# Contract Comparison AI

## 1. Project Title

Contract Comparison AI

## 2. Overview

This project is a full-stack contract comparison and audit application designed to help users compare two versions of a contract and identify meaningful differences between them. The system combines local document processing, formatting checks, and Gemini AI analysis to detect likely contractual changes across text, grammar, dates, layout, and visual elements.

The application is intended for reviewing contract revisions in a practical and structured way. It supports document upload from the browser, analyzes the content on the backend, compares both files, and presents the result in a dashboard with a side-by-side diff, summary statistics, and a searchable change log.

The project is suitable for an internship or academic software project because it combines:

- frontend interaction and dashboard presentation,
- backend API development in Flask,
- document extraction from DOCX and PDF files,
- OCR and visual analysis for images and scanned documents,
- AI-assisted comparison using Gemini,
- local history tracking and report generation.

## 3. Key Features

- Upload and compare two contract files from the browser
- Support for DOCX, PDF, JPG, JPEG, and PNG files
- Side-by-side document diff rendering using Python’s difflib output
- Local detection of five implemented change categories:
  - Textual
  - Grammar
  - Formatting
  - Dates
  - Visual
- Gemini-based comparison for deeper semantic review and OCR/visual inspection
- Summary dashboard with severity counts and executive verdict
- Persistent local comparison history using SQLite
- Downloadable comparison reports in DOCX and PDF format
- Demo mode using preloaded sample contract data
- UI control to view a sample comparison using the current feature name: “View Sample Comparison”

## 4. Supported File Formats

The application supports the following file types:

| Format | Supported | Notes |
| --- | --- | --- |
| DOCX | Yes | Extracts text and document formatting metadata |
| PDF | Yes | Supported for text extraction and scanned-document handling |
| JPG | Yes | Supported for image comparison and OCR-based review |
| JPEG | Yes | Supported for image comparison and OCR-based review |
| PNG | Yes | Supported for image comparison and OCR-based review |

The app is designed to handle both:

- normal digital documents, such as DOCX and text-based PDFs, and
- scanned or image-based documents, including PDFs with little extracted text and uploaded JPG/JPEG/PNG files.

## 5. Types of Differences Detected

The project implements the following comparison categories:

### Textual changes

- Added, removed, or revised wording
- Clause or sentence substitutions
- Changes in obligations, rights, payment terms, and notice periods
- Contract wording differences detected by the local diff engine and Gemini analysis

### Grammar changes

- Spelling corrections
- Grammar and wording improvements
- Sentence structure adjustments
- Punctuation or phrasing corrections that affect readability and clarity

### Formatting changes

- Changes in paragraph structure or layout
- Font differences or formatting metadata changes
- Paragraph alignment or run-level changes detected from DOCX metadata
- Differences in document length or visible formatting structure

### Date changes

- Revised contract dates
- Changed commencement dates
- Updated expiry, notice, or payment dates
- Deadline and schedule modifications

### Visual changes

- Signatures or approval markings
- Seals, stamps, logos, or page-level visual differences
- Image-based or scanned document visual changes identified during Gemini multimodal analysis

## 6. OCR and Scanned Document Analysis

The application includes OCR and scanned-document analysis support for:

- image uploads in JPG/JPEG/PNG format
- PDF files with low extracted text content
- scanned or image-based contract pages that may not contain machine-readable text

When a file is image-based or a PDF appears to be scanned, the backend triggers Gemini multimodal analysis. The app uploads the files through the Gemini Files API and asks the model to review both the document content and visual layout. This helps identify text that may be present only as an image, plus visible elements such as signatures, seals, stamps, and other markings.

This is especially important for scanned contracts where the text cannot be reliably extracted using standard PDF parsing alone.

## 7. System Architecture

The application architecture follows the actual flow of the project:

1. Frontend layer
   - The user interacts with the dashboard in the browser.
   - Files are selected or dragged into the upload area.
   - The UI triggers comparison requests and displays summaries, diff results, history, and reports.

2. Flask backend
   - The Flask app in backend/app.py receives requests from the frontend.
   - It validates file type and size, saves uploads to the temporary uploads folder, and routes requests to the appropriate processing functions.
   - It exposes REST endpoints for comparison, history, demo data, and report download.

3. Document extraction and preprocessing
   - The backend calls extractor.py to read DOCX, PDF, and image files.
   - Text and formatting metadata are extracted for comparison.
   - For scanned PDFs or image files, low text output triggers OCR-ready multimodal analysis.

4. Gemini AI analysis
   - If a valid Gemini API key is configured, the project calls gemini.py for deeper contract review.
   - The AI evaluates changes in textual meaning, grammar, dates, formatting, and visual elements.
   - Gemini is used for semantic analysis, OCR, and document-level review when needed.

5. Comparison and result assembly
   - The project combines local diff results and formatting analysis with AI findings.
   - Summary metrics, severities, verdicts, and change items are assembled into a results object.
   - The UI renders a side-by-side diff and a structured change log.

6. Results dashboard and history
   - Comparison results are displayed in the browser dashboard.
   - The comparison is saved in an SQLite database for later review.
   - The history drawer allows users to inspect previous comparisons and delete saved entries.

7. Reporting and export
   - The application generates DOCX and PDF reports from saved comparison results.
   - Reports are created through reporter.py and returned to users as downloadable files.

## 8. Technology Stack

| Layer | Technologies |
| --- | --- |
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Document extraction | PyMuPDF, python-docx |
| AI analysis | Google Gemini API via google-genai |
| Local diffing | Python difflib |
| Database | SQLite |
| PDF generation | ReportLab |
| DOCX report generation | python-docx |
| Environment setup | python-dotenv |

The project dependencies are listed in requirements.txt and include:

- Flask
- pymupdf
- python-docx
- python-dotenv
- google-genai
- reportlab

## 9. Project Structure

```text
contract/
├── backend/
│   ├── app.py
│   ├── compare.py
│   ├── database.py
│   ├── extractor.py
│   ├── gemini.py
│   ├── mock_data.py
│   ├── reporter.py
│   └── uploads/
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── README.md
├── requirements.txt
└── .env   (to be created locally for Gemini configuration)
```

Notes:

- backend/app.py contains the main Flask server and API routes.
- backend/extractor.py handles document parsing and metadata extraction.
- backend/compare.py compares text and formatting between files.
- backend/gemini.py performs Gemini API requests and multimodal OCR logic.
- backend/database.py stores comparison history in SQLite.
- backend/reporter.py generates Word and PDF report files.
- backend/uploads is used for temporary upload storage and is cleaned up after each comparison run.

## 10. How It Works

1. The user uploads two contract files through the dashboard.
2. The Flask backend validates the files and saves them temporarily.
3. The extractor reads the documents and collects text plus formatting metadata.
4. The comparison logic creates a side-by-side diff and identifies local textual and formatting differences.
5. If a Gemini API key is available, the app performs deeper semantic review and OCR/visual analysis.
6. The backend assembles all found changes into a unified result set.
7. The results are shown in the UI as summary cards, a diff table, and a change log.
8. The comparison is saved in the SQLite history database.
9. Users can download a report as DOCX or PDF.

## 11. Severity Levels

The application uses severity levels to rank the impact of contract changes. The implemented levels in the dashboard and change records are:

- High
- Medium
- Low

The Gemini API can return a value such as "Critical", but the application maps that to High for display consistency in the summary logic.

Typical usage:

- High: major changes in payment terms, termination clauses, rights, or dates
- Medium: notable but less critical changes
- Low: wording fixes, grammar corrections, or minor formatting updates

## 12. API Endpoints

The backend exposes the following endpoints:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | / | Serves the frontend dashboard |
| GET | /api/history | Returns saved comparison history |
| GET | /api/history/<int:comp_id> | Retrieves one previous comparison record |
| DELETE | /api/history/<int:comp_id> | Deletes a saved comparison record |
| GET | /api/demo | Returns preloaded demo comparison data |
| POST | /api/compare | Uploads and compares two contract documents |
| GET | /api/report/<int:comp_id>/pdf | Downloads a PDF comparison report |
| GET | /api/report/<int:comp_id>/docx | Downloads a DOCX comparison report |

## 13. Installation

### Prerequisites

- Python 3.8 or above
- A local terminal or command prompt
- Access to the project folder

### Install dependencies

From the project root, run:

```bash
python -m pip install -r requirements.txt
```

This installs the libraries required for Flask, PDF and DOCX processing, AI integration, and report generation.

## 14. How to Configure the Gemini API

1. Create a file named .env in the project root.
2. Add your Gemini API key in the following format:

```env
GEMINI_API_KEY=your_api_key_here
```

3. Save the file.
4. Restart the application after adding the key.

Important notes:

- The app loads environment variables using python-dotenv.
- If no Gemini API key is present, the app can still run local comparison logic for many documents.
- Image and scanned-document reviews require a valid Gemini API key, because the AI layer is used for OCR and multimodal analysis.

## 15. How to Run the Application

From the project root, start the Flask server:

```bash
python backend/app.py
```

Then open the application in a browser:

```text
http://127.0.0.1:5000
```

From the dashboard, you can:

- upload two contract versions,
- run a comparison,
- view the diff and change log,
- open the history panel,
- download reports,
- use the demo mode by selecting “View Sample Comparison”.

## 16. Example Comparison

A sample comparison in the project demo includes the following kinds of differences:

| Category | Example change |
| --- | --- |
| Textual | Payment term reduced from 30 days to 15 days |
| Dates | Agreement commencement date changed from June 1 to July 1 |
| Grammar | Subject-verb agreement corrected |
| Formatting | Document formatting or font metadata revised |
| Visual | Signature or seal-related visual element noted |

This is based on the sample data included in the project and is designed to demonstrate how the app classifies and reports contract revisions.

## 17. View Sample Comparison / Demo Mode

The project includes a demo mode that loads sample comparison data without requiring the user to upload files manually. In the current frontend, this is labeled as:

- “View Sample Comparison”

This feature is useful for:

- testing the interface,
- understanding how changes are categorized,
- verifying the results dashboard and diff view,
- validating report generation and summary output without needing real contracts.

## 18. Security Considerations

The project includes basic handling for sensitive values and temporary files:

- the API key is stored in a local .env file instead of being hardcoded in source files,
- uploaded files are saved to a local temporary folder inside backend/uploads,
- temporary files are removed after the comparison completes in the Flask finally block.

However, this is not production-grade security. The current project is a local or internship-style application and does not include enterprise-level safeguards such as:

- user authentication and authorization,
- encrypted storage for uploaded documents,
- robust secret management in a production environment,
- malware scanning for uploaded files,
- rate limiting and abuse protection,
- HTTPS enforcement and secure deployment controls,
- enterprise logging and audit trails.

For production-level security, additional measures would be required before deploying this system with real legal or confidential documents.

## 19. Limitations

This project has several practical limitations that should be understood before using it for legal review:

- It is not a legal decision engine and should not be treated as legal advice.
- Local diffing can miss context-dependent semantic changes.
- OCR accuracy depends on image quality, scan quality, and document formatting.
- Gemini analysis depends on API availability and the quality of the uploaded documents.
- Formatting comparisons are limited by what metadata can be extracted from the file type.
- The app stores historical comparison records locally in SQLite and is not built for multi-user enterprise deployment.
- The system does not provide full production security controls.

## 20. Future Improvements

Potential improvements for a future version include:

- stronger contract clause classification and clause-level mapping,
- user authentication and secure multi-user access,
- support for additional file formats such as DOC and XLSX if needed,
- more advanced OCR and visual validation for complex scanned documents,
- improved AI prompt tuning for legal-risk interpretation,
- better export formatting for executive summaries and legal review reports,
- cloud-based storage and deployment for production use,
- a more robust audit trail and role-based workflow.

## 21. Project Objective

The objective of this project is to provide a simple but effective tool for comparing contract versions and highlighting meaningful differences between them. It aims to make contract review more structured by identifying changes in language, grammar, dates, formatting, and visual elements while also supporting quick report generation and history tracking.

The project is especially useful for:

- comparing revised contract drafts,
- identifying critical changes in legal wording,
- reducing manual review workload,
- reviewing scanned and image-based documents more efficiently,
- supporting internship-level full-stack development work with AI and document processing.

## 22. Conclusion

Contract Comparison AI is a practical document-audit application that demonstrates how a full-stack system can compare two contract versions, detect changes across multiple categories, and surface those differences in a clear, usable dashboard. It combines document extraction, diff generation, Gemini-powered analysis, and reporting into a single workflow that is easy to run locally and suitable for demonstration, testing, and further development.

The project successfully implements the major features visible in the current application: comparison of DOCX, PDF, JPG, JPEG, and PNG files; detection of Textual, Grammar, Formatting, Dates, and Visual differences; OCR support for scanned or image-based documents; SQLite history tracking; and downloadable DOCX/PDF reports.

This README reflects the current state of the project and avoids claiming features that are not implemented in the codebase.
