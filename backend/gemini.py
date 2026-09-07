import os
import json
import time
import google.generativeai as genai

def compare_with_ai(path_a, path_b, text_a, text_b):
    """
    Main function to run AI comparative analysis. Decides whether to use fast text-based
    prompting or multimodal upload-based comparison based on file types.
    
    :param path_a: Path to original file
    :param path_b: Path to modified file
    :param text_a: Extracted text of original file (may be empty for scanned documents)
    :param text_b: Extracted text of modified file (may be empty for scanned documents)
    :return: Dictionary containing 'summary' and 'changes' lists
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing in backend.")
        
    genai.configure(api_key=api_key)
    
    # Detect if we need to do multimodal comparison
    ext_a = os.path.splitext(path_a)[1].lower()
    ext_b = os.path.splitext(path_b)[1].lower()
    
    is_image_a = ext_a in ['.jpg', '.jpeg', '.png']
    is_image_b = ext_b in ['.jpg', '.jpeg', '.png']
    
    # If it has no text, it's probably scanned PDF
    is_scanned_a = ext_a == '.pdf' and len(text_a.strip()) < 50
    is_scanned_b = ext_b == '.pdf' and len(text_b.strip()) < 50
    
    multimodal_required = is_image_a or is_image_b or is_scanned_a or is_scanned_b
    
    if multimodal_required:
        return _compare_multimodal(path_a, path_b)
    else:
        return _compare_text_only(text_a, text_b)

def _compare_text_only(text_a, text_b):
    """Executes comparison using text-only inputs for fast response times."""
    prompt = f"""
You are an expert legal counsel and contract auditor. Compare the following two contracts in detail.
Original Contract (Document A):
\"\"\"
{text_a}
\"\"\"

Modified Contract (Document B):
\"\"\"
{text_b}
\"\"\"

Perform a rigorous audit comparing Document A to Document B. Identify:
1. Textual changes: missing characters, words, sentences, or added/removed clauses.
2. Grammar changes: syntax corrections, spelling modifications.
3. Formatting changes: font style/size modifications, paragraph alignment, header adjustments (where text indicates layouts).
4. Date references: deadlines, milestones, start/end dates.

For each change, assign:
- Category: "Textual" | "Grammar" | "Formatting" | "Dates"
- Severity: "High" (impacts liabilities, payment terms, termination, indemnity, IP), "Medium" (operational shifts, notice timelines, minor definitions), "Low" (grammar, formatting, typos)

You MUST return your response in a strict JSON format matching the following structure:
{{
  "summary": {{
    "totalChanges": number,
    "textualChanges": number,
    "grammarChanges": number,
    "formattingChanges": number,
    "visualChanges": 0,
    "dateChanges": number,
    "severityHigh": number,
    "severityMedium": number,
    "severityLow": number,
    "verdict": "Provide a detailed executive verdict of the modifications and contract risks."
  }},
  "changes": [
    {{
      "id": "change-unique-id",
      "category": "Textual" | "Grammar" | "Formatting" | "Dates",
      "severity": "High" | "Medium" | "Low",
      "section": "Name of section / paragraph heading",
      "description": "Clear explanation of the change",
      "originalText": "Matching text snippet from Document A (blank if new)",
      "modifiedText": "Matching text snippet from Document B (blank if deleted)"
    }}
  ]
}}
Do NOT include markdown wrapping (like ```json). Output raw JSON only.
"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)

def _compare_multimodal(path_a, path_b):
    """Uploads documents to Gemini Files API to do multimodal OCR, layout, and visual analysis."""
    uploaded_files = []
    try:
        # Upload file A
        file_a_ref = genai.upload_file(path=path_a)
        uploaded_files.append(file_a_ref)
        
        # Upload file B
        file_b_ref = genai.upload_file(path=path_b)
        uploaded_files.append(file_b_ref)
        
        # Wait briefly for files to process in Google backend if they are large PDFs
        # For small images/PDFs, processing is almost instantaneous.
        for f in uploaded_files:
            while f.state.name == "PROCESSING":
                time.sleep(1)
                f = genai.get_file(f.name)
            if f.state.name == "FAILED":
                raise ValueError(f"Failed to process file {f.display_name} in Gemini API.")
                
        prompt_instruction = """
You are an expert contract comparison AI. Analyze the two uploaded files in detail. 
The first file is Document A (Original Contract). The second file is Document B (Modified Contract).

Perform OCR and visual analysis on both files to identify all differences. Inspect:
1. Textual changes (words, sentences, clauses).
2. Grammar and syntax modifications.
3. Formatting changes (font style, size, alignment, margins).
4. Date references (deadlines, term milestones, effective dates).
5. Visual elements (signatures, stamps, seals, hand-drawn marks, highlights).

For each difference:
- Category: "Textual" | "Grammar" | "Formatting" | "Visual" | "Dates"
- Severity: "High" | "Medium" | "Low"

You MUST return your response in a strict JSON format matching this structure:
{
  "summary": {
    "totalChanges": number,
    "textualChanges": number,
    "grammarChanges": number,
    "formattingChanges": number,
    "visualChanges": number,
    "dateChanges": number,
    "severityHigh": number,
    "severityMedium": number,
    "severityLow": number,
    "verdict": "Provide an audit verdict summarizing the differences, missing visual items like signatures, and overall legal impacts."
  },
  "changes": [
    {
      "id": "change-unique-id",
      "category": "Textual" | "Grammar" | "Formatting" | "Visual" | "Dates",
      "severity": "High" | "Medium" | "Low",
      "section": "Section name/page location",
      "description": "Explanation of change",
      "originalText": "Text in original Document A (or visual status)",
      "modifiedText": "Text in modified Document B (or visual status)"
    }
  ]
}
Do NOT include markdown wrapping. Output raw JSON only.
"""
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            "Compare the two uploaded files.",
            file_a_ref,
            file_b_ref,
            prompt_instruction
        ], generation_config={"response_mime_type": "application/json"})
        
        return json.loads(response.text)
        
    finally:
        # Clean up files from Gemini API storage immediately to preserve privacy
        for f in uploaded_files:
            try:
                genai.delete_file(f.name)
            except Exception:
                pass
