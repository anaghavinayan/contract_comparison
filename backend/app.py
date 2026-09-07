import os
import json
import traceback
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import project modules
import database
import extractor
import compare
import mock_data

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit (mod-6: File size check)

SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.jpg', '.jpeg', '.png'}

def allowed_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_EXTENSIONS

@app.route('/')
def index():
    """Serves the main frontend page."""
    return app.send_static_file('index.html')

@app.route('/api/history', methods=['GET'])
def get_history():
    """Fetches list of past comparisons from the SQLite database."""
    try:
        history = database.get_history()
        return jsonify(history)
    except Exception as e:
        app.logger.error(f"Failed to fetch history: {traceback.format_exc()}")
        return jsonify({"error": "Failed to fetch comparison history."}), 500

@app.route('/api/history/<int:comp_id>', methods=['GET'])
def get_comparison_detail(comp_id):
    """Fetches a specific past comparison with full diff results."""
    try:
        record = database.get_comparison(comp_id)
        if not record:
            return jsonify({"error": "Comparison record not found."}), 404
        return jsonify(record)
    except Exception as e:
        app.logger.error(f"Failed to fetch comparison {comp_id}: {traceback.format_exc()}")
        return jsonify({"error": "Failed to load comparison details."}), 500

@app.route('/api/history/<int:comp_id>', methods=['DELETE'])
def delete_comparison(comp_id):
    """Deletes a comparison record by ID."""
    try:
        success = database.delete_comparison(comp_id)
        if success:
            return jsonify({"message": "Comparison deleted successfully."})
        return jsonify({"error": "Failed to delete comparison record."}), 400
    except Exception as e:
        app.logger.error(f"Failed to delete comparison {comp_id}: {traceback.format_exc()}")
        return jsonify({"error": "An error occurred while deleting the record."}), 500

@app.route('/api/demo', methods=['GET'])
def get_demo():
    """Serves the pre-computed demo comparison data."""
    return jsonify(mock_data.DEMO_RESULTS)

@app.route('/api/compare', methods=['POST'])
def compare_contracts():
    """
    Main endpoint to upload and compare two contract files.
    Extracts text, runs local diffing, runs Gemini analysis (if API key is present),
    saves the record to SQLite, and returns results.
    """
    if 'file_a' not in request.files or 'file_b' not in request.files:
        return jsonify({"error": "Please provide both Original and Modified contract files."}), 400
        
    file_a = request.files['file_a']
    file_b = request.files['file_b']
    
    if file_a.filename == '' or file_b.filename == '':
        return jsonify({"error": "One or both selected files are empty/invalid."}), 400
        
    if not (allowed_file(file_a.filename) and allowed_file(file_b.filename)):
        return jsonify({"error": "Unsupported file format. Supported: PDF, DOCX, JPG, JPEG, PNG."}), 400

    path_a = None
    path_b = None
    
    try:
        # Save files temporarily
        filename_a = secure_filename(file_a.filename)
        filename_b = secure_filename(file_b.filename)
        
        path_a = os.path.join(app.config['UPLOAD_FOLDER'], f"a_{filename_a}")
        path_b = os.path.join(app.config['UPLOAD_FOLDER'], f"b_{filename_b}")
        
        file_a.save(path_a)
        file_b.save(path_b)
        
        # Check file sizes are not 0 (mod-6: empty document checks)
        if os.path.getsize(path_a) == 0 or os.path.getsize(path_b) == 0:
            return jsonify({"error": "One or both uploaded documents are empty files (0 bytes)."}), 400

        # Step 1: Extract text and styles
        try:
            data_a = extractor.extract_text(path_a)
            data_b = extractor.extract_text(path_b)
        except extractor.ExtractionError as ee:
            return jsonify({"error": str(ee)}), 400
        except Exception as e:
            app.logger.error(f"Extraction failed: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to extract text from documents: {str(e)}"}), 500
            
        # Step 2: Compute local text diff (difflib.HtmlDiff)
        try:
            diff_html = compare.generate_text_diff(data_a['lines'], data_b['lines'])
            formatting_changes = compare.compare_formatting(data_a['formatting'], data_b['formatting'])
        except Exception as e:
            app.logger.error(f"Diff generation failed: {traceback.format_exc()}")
            return jsonify({"error": f"Failed to generate difference map: {str(e)}"}), 500

        # Check if Gemini API key is configured and not the default template placeholder
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key == 'YOUR_GEMINI_API_KEY_HERE' or not api_key:
            api_key = None

        # Check if multimodal processing is required
        ext_a = os.path.splitext(file_a.filename)[1].lower()
        ext_b = os.path.splitext(file_b.filename)[1].lower()
        is_multimodal_a = ext_a in ['.jpg', '.jpeg', '.png'] or len(data_a['text'].strip()) < 50
        is_multimodal_b = ext_b in ['.jpg', '.jpeg', '.png'] or len(data_b['text'].strip()) < 50
        
        if (is_multimodal_a or is_multimodal_b) and not api_key:
            return jsonify({
                "error": "Gemini API key is required on the backend to perform OCR and visual comparison on image formats or scanned PDFs. Please add your GEMINI_API_KEY to the backend .env file."
            }), 400

        # Step 3: Local structural and textual difference collection
        local_text_changes = []
        if not api_key:
            try:
                local_text_changes = compare.get_textual_changes(data_a['lines'], data_b['lines'])
            except Exception as e:
                app.logger.error(f"Local text diff parsing failed: {traceback.format_exc()}")

        # Build initial summary based on local checks
        total_formatting = len(formatting_changes)
        total_textual = len(local_text_changes)
        
        summary = {
            "totalChanges": total_formatting + total_textual,
            "textualChanges": total_textual,
            "grammarChanges": 0,
            "formattingChanges": total_formatting,
            "visualChanges": 0,
            "dateChanges": 0,
            "severityHigh": len([c for c in local_text_changes if c['severity'] == 'High']),
            "severityMedium": len([c for c in local_text_changes if c['severity'] == 'Medium']),
            "severityLow": total_formatting,
            "verdict": "Local analysis complete. Configure GEMINI_API_KEY in the backend .env for deep AI audits (text, grammar, dates, visuals)."
        }
        
        changes = []
        # Add local textual changes (fallback when no API key)
        for i, change in enumerate(local_text_changes):
            changes.append({
                "id": f"local-text-{i}",
                "category": change['category'],
                "severity": change['severity'],
                "section": change['section'],
                "description": change['description'],
                "originalText": change['originalText'],
                "modifiedText": change['modifiedText']
            })
            
        # Add formatting changes
        for i, change in enumerate(formatting_changes):
            changes.append({
                "id": f"local-format-{i}",
                "category": change['category'],
                "severity": change['severity'],
                "section": "Document Layout",
                "description": change['description'],
                "originalText": "",
                "modifiedText": ""
            })

        if api_key:
            try:
                import gemini
                ai_result = gemini.compare_with_ai(path_a, path_b, data_a['text'], data_b['text'])
                if ai_result:
                    summary = ai_result.get("summary", summary)
                    # Merge local formatting changes with AI changes
                    ai_changes = ai_result.get("changes", [])
                    changes = ai_changes + changes
                    summary["totalChanges"] = len(changes)
                    summary["formattingChanges"] += len([c for c in changes if c['category'] == 'Formatting'])
            except Exception as e:
                # If Gemini fails, we log it and fallback to local comparison results
                app.logger.error(f"Gemini API analysis failed: {traceback.format_exc()}")
                summary["verdict"] = f"Local analysis completed. AI comparison failed: {str(e)}"

        # Prepare payload to return and save
        results = {
            "file_a_name": file_a.filename,
            "file_b_name": file_b.filename,
            "diff_html": diff_html,
            "changes": changes
        }
        
        # Save to database
        comp_id = database.save_comparison(
            file_a_name=file_a.filename,
            file_b_name=file_b.filename,
            summary=summary,
            results=results
        )
        
        # Return full response
        return jsonify({
            "id": comp_id,
            "file_a_name": file_a.filename,
            "file_b_name": file_b.filename,
            "summary": summary,
            "changes": changes,
            "diff_html": diff_html
        })
        
    except Exception as e:
        app.logger.error(f"Upload comparison error: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
        
    finally:
        # Clean up temporary uploaded files
        if path_a and os.path.exists(path_a):
            os.remove(path_a)
        if path_b and os.path.exists(path_b):
            os.remove(path_b)

@app.route('/api/report/<int:comp_id>/<string:format_type>', methods=['GET'])
def download_report(comp_id, format_type):
    """
    Downloads comparison results as a PDF or DOCX report.
    (Phase 2 implementation in reporter.py)
    """
    try:
        record = database.get_comparison(comp_id)
        if not record:
            return jsonify({"error": "Comparison record not found."}), 404
            
        import reporter
        if format_type.lower() == 'pdf':
            pdf_path = reporter.generate_pdf_report(record)
            directory = os.path.dirname(pdf_path)
            filename = os.path.basename(pdf_path)
            return send_from_directory(directory, filename, as_attachment=True)
            
        elif format_type.lower() == 'docx':
            docx_path = reporter.generate_docx_report(record)
            directory = os.path.dirname(docx_path)
            filename = os.path.basename(docx_path)
            return send_from_directory(directory, filename, as_attachment=True)
            
        else:
            return jsonify({"error": "Unsupported report format. Supported: pdf, docx."}), 400
            
    except Exception as e:
        app.logger.error(f"Failed to generate report: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
