# Contract Comparison AI - Audit Dashboard

A professional, full-stack web application designed to help legal teams and auditors compare two versions of a contract. The application identifies textual differences, grammatical fixes, formatting updates, date discrepancies, and missing visual elements (like signatures or seals) using a combination of local python diffing algorithms and Gemini AI.

---

## Features

1. **Document Upload**
   - Supports dragging and dropping or browsing files.
   - Acceptable formats: `.docx`, `.pdf`, and `.jpg`/`.jpeg`/`.png`.

2. **Side-by-Side Diff Workspace**
   - Renders a clean, scroll-synchronized side-by-side textual diff table (using Python `difflib.HtmlDiff`).
   - High-contrast color indicators: Green highlights for additions, red for deletions, and yellow for inline modifications.

3. **AI-Powered Contract Audit**
   - Leverages **Gemini AI** to perform semantic comparison.
   - Categorizes modifications into: **Textual**, **Grammar**, **Formatting**, **Dates**, and **Visual Elements**.
   - Assigns a severity level (**High**, **Medium**, **Low**) to each change to highlight risk areas.
   - Generates an executive verdict detailing the legal implications of the modifications.

4. **Lightweight SQLite History Tracking**
   - Every comparison run is persisted locally in an SQLite database.
   - History panel allows loading previous runs, auditing past verdicts, and generating reports.
   - Users can delete individual records from the history list.

5. **Multi-Format Report Generation**
   - Export comparison results dynamically into:
     - **Microsoft Word (`.docx`)** using `python-docx`.
     - **Adobe PDF (`.pdf`)** using `reportlab`.
   - Reports include executive summaries, color-coded severity badges, and detailed comparison tables.

6. **Hybrid OCR & Image Audit**
   - Scanned PDFs or images are uploaded directly to the Gemini Files API.
   - Handles text extraction (OCR) and layout styling checks natively with state-of-the-art accuracy.

7. **Demo Mode**
   - A zero-configuration test environment pre-loaded with mock agreement files and differences. Test all features instantly without requiring an API key.

---

## Project Structure

```
ContractComparisonAI/
├── backend/
│   ├── app.py              # Flask server and API endpoints
│   ├── extractor.py        # Local text extraction logic (PyMuPDF, python-docx)
│   ├── compare.py          # Local diff compilation and formatting analyzer
│   ├── gemini.py           # Gemini API SDK integration and prompts
│   ├── database.py         # SQLite history tracker manager
│   ├── reporter.py         # Dynamic DOCX/PDF report compilers
│   ├── uploads/            # Temporary upload directory (auto-cleaned)
│   └── history.db          # SQLite local database (generated automatically)
│
├── frontend/
│   ├── index.html          # Dashboard page markup
│   ├── style.css           # Custom dark theme and styled diff tables
│   └── script.js           # Client-side form handlers, routing, and filters
│
├── requirements.txt        # Backend python dependencies
├── .env                    # Environment variables (API Key)
└── README.md               # Operation manual
```

---

## Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Install Dependencies
Open your command prompt or terminal in the project root folder and execute:
```bash
python -m pip install -r requirements.txt
```

This installs:
- `Flask` (Backend web server)
- `pymupdf` (PDF parser)
- `python-docx` (Word parser and DOCX exporter)
- `python-dotenv` (Load environment keys)
- `google-generativeai` (Gemini SDK)
- `reportlab` (PDF exporter)

### 3. Configure API Key
1. Locate the `.env` file in the root directory.
2. Replace `YOUR_GEMINI_API_KEY_HERE` with your actual Google AI Studio API key.
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
   *Note: If no API key is specified, the application will run in local-fallback mode, rendering local text differences, and will suggest setting up the API key for deep audits.*

---

## Running the Application

1. In the project root, start the Flask web server:
   ```bash
   python backend/app.py
   ```
2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
3. Click **"Try Demo Mode"** to see sample results immediately, or upload your own files to compare!
