import os
import json
import re
import time

from google import genai

PRIMARY_MODEL = "gemini-3.6-flash"
FALLBACK_MODEL = "gemini-3.8-flash"
MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return genai.Client(api_key=api_key)


def _parse_json_response(text):
    if not text:
        raise ValueError("Gemini returned an empty response.")
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError("Gemini returned a response that could not be parsed as JSON.")


def _is_retryable_error(error):
    message = str(error).lower()
    return any(word in message for word in [
        "503", "unavailable", "service unavailable", "high demand",
        "overloaded", "429", "resource exhausted", "rate limit",
        "500", "502", "504", "internal server error",
        "deadline exceeded", "temporarily"
    ])


def _generate_with_retry(client, models, contents):
    last_error = None

    for model in models:
        for attempt in range(MAX_RETRIES + 1):
            try:
                print(f"[GEMINI] Trying {model} (attempt {attempt + 1}/{MAX_RETRIES + 1})...")
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config={"response_mime_type": "application/json"}
                )
                print(f"[GEMINI] {model} succeeded.")
                return response
            except Exception as error:
                last_error = error
                if not _is_retryable_error(error):
                    raise
                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAYS[attempt]
                    print(f"[GEMINI] Temporary error from {model}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"[GEMINI] {model} failed after {MAX_RETRIES + 1} attempts.")

    raise last_error


def _text_prompt(text_a, text_b):
    return f"""
You are an expert contract comparison assistant.

Compare the ORIGINAL contract and the MODIFIED contract carefully.

Identify meaningful differences in:
1. TEXTUAL: added, removed, or changed wording, clauses, numbers,
   obligations, rights, payment terms, notice periods, penalties, etc.
2. GRAMMAR: grammar, spelling, punctuation, wording, sentence structure.
3. DATES: changed dates, deadlines, commencement, expiry, notice or payment dates.
4. FORMATTING: formatting differences that can be determined from the content.
5. VISUAL: meaningful visual elements when available.

Focus especially on changes affecting legal or contractual meaning.

Return ONLY valid JSON:
{{
  "executive_summary": "Short overall assessment",
  "overall_severity": "Low|Medium|High|Critical",
  "changes": [
    {{
      "category": "Textual|Grammar|Formatting|Dates|Visual",
      "severity": "Low|Medium|High|Critical",
      "location": "Clause or section",
      "original": "Original wording or value",
      "modified": "Modified wording or value",
      "description": "What changed and why it matters",
      "impact": "Legal or contractual impact"
    }}
  ]
}}

Do not invent differences or report unchanged content.

ORIGINAL CONTRACT:
{text_a}

MODIFIED CONTRACT:
{text_b}
"""


def _multimodal_prompt():
    return """
You are an expert contract comparison assistant performing a detailed multimodal comparison of TWO uploaded contract documents.

The first file is the ORIGINAL contract.
The second file is the MODIFIED contract.

Inspect both document content and visual appearance.

Identify meaningful differences in:
1. TEXTUAL: added, removed, or changed words, phrases, sentences, clauses,
   numbers, obligations, rights, payment terms, notice periods, penalties, etc.
2. GRAMMAR: grammar, spelling, punctuation, wording and sentence structure.
3. DATES: every changed date, deadline, commencement, expiry, notice or payment date.
4. FORMATTING: font size/style, bold/italic/underline, alignment, spacing,
   headings, tables, layout, highlighting and other visible formatting.
5. VISUAL: signatures, seals, stamps, logos, initials, handwritten marks,
   highlighting, images and other meaningful visual elements.

OCR REQUIREMENT:
These may be scanned/image-only documents. Read visible text using OCR and compare it.
Do not treat a scanned document as empty just because normal text extraction returns little or no text.

Pay special attention to dates, monetary amounts, percentages, payment periods,
notice periods, termination, obligations, rights, liability, confidentiality,
governing law, signatures and approval marks.

Return ONLY valid JSON:
{
  "executive_summary": "Short overall assessment",
  "overall_severity": "Low|Medium|High|Critical",
  "changes": [
    {
      "category": "Textual|Grammar|Formatting|Dates|Visual",
      "severity": "Low|Medium|High|Critical",
      "location": "Clause, section, page, or visual location",
      "original": "Original wording/value/visual description",
      "modified": "Modified wording/value/visual description",
      "description": "What changed and why it matters",
      "impact": "Legal or contractual impact"
    }
  ]
}

Do not invent differences. If a visual difference cannot be read exactly,
describe it rather than inventing wording. If there are no meaningful differences,
return an empty changes array.
"""


def _compare_text_only(text_a, text_b):
    client = _get_client()
    response = _generate_with_retry(
        client,
        [PRIMARY_MODEL, FALLBACK_MODEL],
        _text_prompt(text_a or "", text_b or "")
    )
    return _parse_json_response(response.text)


def _compare_multimodal(path_a, path_b):
    client = _get_client()
    file_a = None
    file_b = None

    try:
        print("[GEMINI] Uploading files for multimodal/OCR analysis...")
        file_a = client.files.upload(file=path_a)
        file_b = client.files.upload(file=path_b)
        print("[GEMINI] Files uploaded. Starting OCR/visual comparison...")

        response = _generate_with_retry(
            client,
            [PRIMARY_MODEL, FALLBACK_MODEL],
            [file_a, file_b, _multimodal_prompt()]
        )
        return _parse_json_response(response.text)

    finally:
        for uploaded_file in (file_a, file_b):
            if uploaded_file is not None:
                try:
                    client.files.delete(name=uploaded_file.name)
                    print(f"[GEMINI] Deleted uploaded file: {uploaded_file.name}")
                except Exception as cleanup_error:
                    print(f"[GEMINI] Could not delete uploaded file: {cleanup_error}")


def compare_with_ai(path_a, path_b, text_a, text_b):
    ext_a = os.path.splitext(path_a)[1].lower()
    ext_b = os.path.splitext(path_b)[1].lower()

    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    is_image_a = ext_a in image_extensions
    is_image_b = ext_b in image_extensions
    is_scanned_a = ext_a == ".pdf" and len((text_a or "").strip()) < 50
    is_scanned_b = ext_b == ".pdf" and len((text_b or "").strip()) < 50

    if is_image_a or is_image_b or is_scanned_a or is_scanned_b:
        print("[GEMINI] Multimodal/OCR analysis required.")
        return _compare_multimodal(path_a, path_b)

    print("[GEMINI] Text-based contract analysis required.")
    return _compare_text_only(text_a or "", text_b or "")
