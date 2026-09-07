import os
import json
import re
import traceback

from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory
)

from werkzeug.utils import secure_filename
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PROJECT MODULES
# ============================================================

import database
import extractor
import compare
import mock_data


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)


# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "uploads"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    16 * 1024 * 1024
)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".jpg",
    ".jpeg",
    ".png"
}


# ============================================================
# FILE VALIDATION
# ============================================================

def allowed_file(filename):

    ext = os.path.splitext(
        filename
    )[1].lower()

    return ext in SUPPORTED_EXTENSIONS


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return app.send_static_file(
        "index.html"
    )


# ============================================================
# HISTORY
# ============================================================

@app.route(
    "/api/history",
    methods=["GET"]
)
def get_history():

    try:

        history = database.get_history()

        return jsonify(history)

    except Exception:

        app.logger.error(
            f"Failed to fetch history:\n"
            f"{traceback.format_exc()}"
        )

        return jsonify({
            "error":
                "Failed to fetch comparison history."
        }), 500


@app.route(
    "/api/history/<int:comp_id>",
    methods=["GET"]
)
def get_comparison_detail(comp_id):

    try:

        record = database.get_comparison(
            comp_id
        )

        if not record:

            return jsonify({
                "error":
                    "Comparison record not found."
            }), 404

        return jsonify(record)

    except Exception:

        app.logger.error(
            f"Failed to fetch comparison "
            f"{comp_id}:\n"
            f"{traceback.format_exc()}"
        )

        return jsonify({
            "error":
                "Failed to load comparison details."
        }), 500


@app.route(
    "/api/history/<int:comp_id>",
    methods=["DELETE"]
)
def delete_comparison(comp_id):

    try:

        success = database.delete_comparison(
            comp_id
        )

        if success:

            return jsonify({
                "message":
                    "Comparison deleted successfully."
            })

        return jsonify({
            "error":
                "Failed to delete comparison record."
        }), 400

    except Exception:

        app.logger.error(
            f"Failed to delete comparison "
            f"{comp_id}:\n"
            f"{traceback.format_exc()}"
        )

        return jsonify({
            "error":
                "An error occurred while deleting "
                "the record."
        }), 500


# ============================================================
# DEMO
# ============================================================

@app.route(
    "/api/demo",
    methods=["GET"]
)
def get_demo():

    return jsonify(
        mock_data.DEMO_RESULTS
    )


# ============================================================
# SUMMARY BUILDER
# ============================================================

def build_local_summary(
    text_changes,
    formatting_changes
):

    all_changes = (
        text_changes +
        formatting_changes
    )

    category_counts = {
        "Textual": 0,
        "Grammar": 0,
        "Formatting": 0,
        "Visual": 0,
        "Dates": 0
    }

    for change in all_changes:

        category = change.get(
            "category",
            "Textual"
        )

        if category in category_counts:

            category_counts[category] += 1

    severity_high = len([
        c for c in all_changes
        if c.get("severity") == "High"
    ])

    severity_medium = len([
        c for c in all_changes
        if c.get("severity") == "Medium"
    ])

    severity_low = len([
        c for c in all_changes
        if c.get("severity") == "Low"
    ])

    # --------------------------------------------------------
    # Verdict
    # --------------------------------------------------------

    if severity_high > 0:

        verdict = (
            "Local analysis detected "
            f"{len(all_changes)} change(s), including "
            f"{severity_high} high-severity "
            "contractual change(s). "
            "A Gemini AI audit can provide deeper "
            "semantic and legal analysis."
        )

    elif len(all_changes) > 0:

        verdict = (
            f"Local analysis detected "
            f"{len(all_changes)} change(s) "
            "between the contracts. "
            "A Gemini AI audit can provide deeper "
            "grammar, semantic, date, and visual analysis."
        )

    else:

        verdict = (
            "No differences were detected by "
            "the local comparison engine."
        )

    return {

        "totalChanges":
            len(all_changes),

        "textualChanges":
            category_counts["Textual"],

        "grammarChanges":
            category_counts["Grammar"],

        "formattingChanges":
            category_counts["Formatting"],

        "visualChanges":
            category_counts["Visual"],

        "dateChanges":
            category_counts["Dates"],

        "severityHigh":
            severity_high,

        "severityMedium":
            severity_medium,

        "severityLow":
            severity_low,

        "verdict":
            verdict
    }


# ============================================================
# AI VERDICT BUILDER
# ============================================================

def build_ai_verdict(
    ai_text,
    changes
):

    if not ai_text:

        return ""

    # Gemini is responsible for semantic,
    # textual, grammar, date and visual analysis.
    #
    # Local comparison remains authoritative for
    # directly verified document differences,
    # especially DOCX formatting.

    if not changes:

        return (
            "Gemini AI: "
            + ai_text.strip()
        )

    cleaned = ai_text.strip()

    # --------------------------------------------------------
    # Prevent contradictory verdicts
    # --------------------------------------------------------
    #
    # Example:
    # Gemini says:
    # "No changes were identified."
    #
    # But local comparison found:
    # 5 formatting changes.
    #
    # We must not display a contradictory result.
    # --------------------------------------------------------

    no_change_pattern = re.compile(
        r"\b(no|none|zero)\b"
        r".{0,80}"
        r"\b(changes?|differences?)\b",
        re.IGNORECASE | re.DOTALL
    )

    if no_change_pattern.search(cleaned):

        cleaned = (
            "No textual or semantic changes "
            "were identified by Gemini AI."
        )

    return (
        "Gemini AI: "
        + cleaned
        + " Local document analysis confirmed "
        + f"{len(changes)} detected change(s)."
    )


# ============================================================
# MAIN COMPARISON
# ============================================================

@app.route(
    "/api/compare",
    methods=["POST"]
)
def compare_contracts():

    if (
        "file_a" not in request.files
        or
        "file_b" not in request.files
    ):

        return jsonify({
            "error":
                "Please provide both Original "
                "and Modified contract files."
        }), 400

    file_a = request.files["file_a"]
    file_b = request.files["file_b"]

    if (
        file_a.filename == ""
        or
        file_b.filename == ""
    ):

        return jsonify({
            "error":
                "One or both selected files "
                "are empty/invalid."
        }), 400

    if (
        not allowed_file(file_a.filename)
        or
        not allowed_file(file_b.filename)
    ):

        return jsonify({
            "error":
                "Unsupported file format. "
                "Supported: PDF, DOCX, JPG, "
                "JPEG, PNG."
        }), 400

    path_a = None
    path_b = None

    try:

        # ----------------------------------------------------
        # Save temporary files
        # ----------------------------------------------------

        filename_a = secure_filename(
            file_a.filename
        )

        filename_b = secure_filename(
            file_b.filename
        )

        path_a = os.path.join(
            app.config["UPLOAD_FOLDER"],
            f"a_{filename_a}"
        )

        path_b = os.path.join(
            app.config["UPLOAD_FOLDER"],
            f"b_{filename_b}"
        )

        file_a.save(path_a)
        file_b.save(path_b)

        # ----------------------------------------------------
        # Empty file check
        # ----------------------------------------------------

        if (
            os.path.getsize(path_a) == 0
            or
            os.path.getsize(path_b) == 0
        ):

            return jsonify({
                "error":
                    "One or both uploaded documents "
                    "are empty files (0 bytes)."
            }), 400

        # ----------------------------------------------------
        # EXTRACTION
        # ----------------------------------------------------

        try:

            data_a = extractor.extract_text(
                path_a
            )

            data_b = extractor.extract_text(
                path_b
            )

        except extractor.ExtractionError as error:

            return jsonify({
                "error": str(error)
            }), 400

        except Exception as error:

            app.logger.error(
                "Extraction failed:\n"
                + traceback.format_exc()
            )

            return jsonify({
                "error":
                    "Failed to extract text "
                    f"from documents: {str(error)}"
            }), 500

        # ----------------------------------------------------
        # TEXT DIFF + FORMATTING
        # ----------------------------------------------------

        try:

            diff_html = compare.generate_text_diff(
                data_a["lines"],
                data_b["lines"]
            )

            formatting_changes = (
                compare.compare_formatting(
                    data_a["formatting"],
                    data_b["formatting"]
                )
            )

            local_text_changes = (
                compare.get_textual_changes(
                    data_a["lines"],
                    data_b["lines"]
                )
            )

        except Exception as error:

            app.logger.error(
                "Diff generation failed:\n"
                + traceback.format_exc()
            )

            return jsonify({
                "error":
                    "Failed to generate difference "
                    f"map: {str(error)}"
            }), 500

        # ----------------------------------------------------
        # API KEY
        # ----------------------------------------------------

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if (
            not api_key
            or
            api_key == "YOUR_GEMINI_API_KEY_HERE"
        ):

            api_key = None

        # ----------------------------------------------------
        # Detect image/scanned documents
        # ----------------------------------------------------

        ext_a = os.path.splitext(
            file_a.filename
        )[1].lower()

        ext_b = os.path.splitext(
            file_b.filename
        )[1].lower()

        is_multimodal_a = (
            ext_a in [
                ".jpg",
                ".jpeg",
                ".png"
            ]
            or
            len(
                data_a["text"].strip()
            ) < 50
        )

        is_multimodal_b = (
            ext_b in [
                ".jpg",
                ".jpeg",
                ".png"
            ]
            or
            len(
                data_b["text"].strip()
            ) < 50
        )

        # ----------------------------------------------------
        # Image/scanned documents require Gemini
        # ----------------------------------------------------

        if (
            is_multimodal_a
            or
            is_multimodal_b
        ) and not api_key:

            return jsonify({
                "error":
                    "Gemini API key is required "
                    "for OCR and visual comparison "
                    "of image formats or scanned PDFs. "
                    "Please add GEMINI_API_KEY to "
                    "the backend .env file."
            }), 400

        # ----------------------------------------------------
        # LOCAL SUMMARY
        # ----------------------------------------------------

        summary = build_local_summary(
            local_text_changes,
            formatting_changes
        )

        # ----------------------------------------------------
        # CHANGE LIST
        # ----------------------------------------------------

        changes = []

        changes.extend(
            local_text_changes
        )

        changes.extend(
            formatting_changes
        )

        # ----------------------------------------------------
        # GEMINI
        # ----------------------------------------------------

        if api_key:

            try:

                import gemini

                ai_result = (
                    gemini.compare_with_ai(
                        path_a,
                        path_b,
                        data_a["text"],
                        data_b["text"]
                    )
                )

                if ai_result:

                    ai_changes = (
                        ai_result.get(
                            "changes",
                            []
                        )
                    )

                    # ------------------------------------------------
                    # Local formatting remains useful
                    # because Gemini text-only mode cannot
                    # reliably inspect DOCX run formatting.
                    # ------------------------------------------------

                    changes = (
                        ai_changes
                        + formatting_changes
                    )

                    # ------------------------------------------------
                    # Recalculate summary from final change list.
                    # ------------------------------------------------

                    summary = build_local_summary(
                        [
                            c for c in changes
                            if c.get("category")
                            not in [
                                "Formatting",
                                "Visual"
                            ]
                        ],
                        [
                            c for c in changes
                            if c.get("category")
                            in [
                                "Formatting",
                                "Visual"
                            ]
                        ]
                    )

                    ai_summary = (
                        ai_result.get(
                            "summary",
                            {}
                        )
                    )

                    # ------------------------------------------------
                    # FIX:
                    # Do NOT blindly replace the local verdict
                    # with Gemini's verdict.
                    #
                    # Gemini may say "no changes" because it is
                    # primarily analyzing text/semantics, while the
                    # local engine has correctly detected formatting.
                    # ------------------------------------------------

                    ai_executive_summary = (
                        ai_result.get(
                            "executive_summary",
                            ""
                        )
                    )

                    ai_old_verdict = (
                        ai_summary.get(
                            "verdict",
                            ""
                        )
                    )

                    if ai_executive_summary:

                        summary["verdict"] = (
                            build_ai_verdict(
                                ai_executive_summary,
                                changes
                            )
                        )

                    elif ai_old_verdict:

                        summary["verdict"] = (
                            build_ai_verdict(
                                ai_old_verdict,
                                changes
                            )
                        )

                    # ------------------------------------------------
                    # Preserve AI severity when available.
                    # ------------------------------------------------

                    ai_overall_severity = (
                        ai_result.get(
                            "overall_severity",
                            ""
                        )
                    )

                    if not ai_overall_severity:

                        ai_overall_severity = (
                            ai_summary.get(
                                "overallSeverity",
                                ""
                            )
                        )

                    if ai_overall_severity:

                        severity_map = {
                            "High": "High",
                            "Medium": "Medium",
                            "Low": "Low",
                            "Critical": "High"
                        }

                        mapped_severity = (
                            severity_map.get(
                                str(
                                    ai_overall_severity
                                ).strip(),
                                None
                            )
                        )

                        if mapped_severity:

                            summary[
                                "overallSeverity"
                            ] = mapped_severity

            except Exception as error:

                app.logger.error(
                    "Gemini API analysis failed:\n"
                    + traceback.format_exc()
                )

                summary["verdict"] += (
                    " Gemini analysis was unavailable: "
                    + str(error)
                )

        # ----------------------------------------------------
        # Ensure IDs exist
        # ----------------------------------------------------

        for index, change in enumerate(
            changes
        ):

            if not change.get("id"):

                change["id"] = (
                    f"change-{index + 1}"
                )

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        results = {

            "file_a_name":
                file_a.filename,

            "file_b_name":
                file_b.filename,

            "diff_html":
                diff_html,

            "changes":
                changes
        }

        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

        comp_id = (
            database.save_comparison(
                file_a_name=file_a.filename,
                file_b_name=file_b.filename,
                summary=summary,
                results=results
            )
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "id":
                comp_id,

            "file_a_name":
                file_a.filename,

            "file_b_name":
                file_b.filename,

            "summary":
                summary,

            "changes":
                changes,

            "diff_html":
                diff_html
        })

    except Exception as error:

        app.logger.error(
            "Upload comparison error:\n"
            + traceback.format_exc()
        )

        return jsonify({
            "error":
                f"Internal server error: {str(error)}"
        }), 500

    finally:

        # ----------------------------------------------------
        # Delete temporary uploads
        # ----------------------------------------------------

        if (
            path_a
            and
            os.path.exists(path_a)
        ):

            os.remove(path_a)

        if (
            path_b
            and
            os.path.exists(path_b)
        ):

            os.remove(path_b)


# ============================================================
# REPORTS
# ============================================================

@app.route(
    "/api/report/<int:comp_id>/<string:format_type>",
    methods=["GET"]
)
def download_report(
    comp_id,
    format_type
):

    try:

        record = database.get_comparison(
            comp_id
        )

        if not record:

            return jsonify({
                "error":
                    "Comparison record not found."
            }), 404

        import reporter

        if format_type.lower() == "pdf":

            pdf_path = (
                reporter.generate_pdf_report(
                    record
                )
            )

            directory = os.path.dirname(
                pdf_path
            )

            filename = os.path.basename(
                pdf_path
            )

            return send_from_directory(
                directory,
                filename,
                as_attachment=True
            )

        elif format_type.lower() == "docx":

            docx_path = (
                reporter.generate_docx_report(
                    record
                )
            )

            directory = os.path.dirname(
                docx_path
            )

            filename = os.path.basename(
                docx_path
            )

            return send_from_directory(
                directory,
                filename,
                as_attachment=True
            )

        else:

            return jsonify({
                "error":
                    "Unsupported report format. "
                    "Supported: pdf, docx."
            }), 400

    except Exception:

        app.logger.error(
            "Failed to generate report:\n"
            + traceback.format_exc()
        )

        return jsonify({
            "error":
                "Failed to generate report."
        }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )