import os
import fitz  # PyMuPDF
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.text import WD_BREAK


class ExtractionError(Exception):
    pass


def extract_text(file_path):
    """
    Extract text and detailed metadata from supported documents.

    Supported:
    - DOCX
    - PDF
    - JPG / JPEG / PNG

    Returns:
        {
            "text": str,
            "lines": list[str],
            "formatting": dict
        }
    """

    if not os.path.exists(file_path):
        raise ExtractionError("File does not exist.")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".docx":
        return _extract_docx(file_path)

    elif ext == ".pdf":
        return _extract_pdf(file_path)

    elif ext in [".jpg", ".jpeg", ".png"]:
        return {
            "text": "",
            "lines": [],
            "formatting": {
                "document_type": "image",
                "image_detected": True,
                "fonts_detected": [],
                "runs": [],
                "paragraphs": [],
                "images_count": 1
            }
        }

    else:
        raise ExtractionError(f"Unsupported file format: {ext}")


# ============================================================
# DOCX EXTRACTION
# ============================================================

def _extract_docx(file_path):
    try:
        doc = docx.Document(file_path)
    except Exception as e:
        raise ExtractionError(
            f"Failed to open DOCX file: {str(e)}"
        )

    lines = []

    formatting_info = {
        "document_type": "docx",
        "paragraphs_count": len(doc.paragraphs),
        "tables_count": len(doc.tables),
        "styles_detected": [],
        "fonts_detected": [],
        "runs": [],
        "paragraphs": [],
        "images_count": 0
    }

    styles = set()
    fonts = set()

    # --------------------------------------------------------
    # Normal paragraphs
    # --------------------------------------------------------

    for paragraph_index, para in enumerate(doc.paragraphs):

        text = para.text.strip()

        if para.style and para.style.name:
            styles.add(para.style.name)

        alignment = _get_alignment_name(para.alignment)

        paragraph_data = {
            "paragraph_index": paragraph_index,
            "text": para.text,
            "style": para.style.name if para.style else "",
            "alignment": alignment,
            "runs": []
        }

        for run_index, run in enumerate(para.runs):

            run_text = run.text

            font_name = run.font.name
            font_size = None

            if run.font.size:
                font_size = round(run.font.size.pt, 2)

            bold = bool(run.bold) if run.bold is not None else False
            italic = bool(run.italic) if run.italic is not None else False
            underline = bool(run.underline) if run.underline is not None else False
            strike = bool(run.font.strike) if run.font.strike is not None else False

            color = None
            if run.font.color and run.font.color.rgb:
                color = str(run.font.color.rgb)

            highlight = None

            try:
                if run.font.highlight_color:
                    highlight = str(run.font.highlight_color)
            except Exception:
                highlight = None

            if font_name:
                fonts.add(font_name)

            run_data = {
                "paragraph_index": paragraph_index,
                "run_index": run_index,
                "text": run_text,
                "font_name": font_name,
                "font_size": font_size,
                "bold": bold,
                "italic": italic,
                "underline": underline,
                "strike": strike,
                "color": color,
                "highlight": highlight
            }

            paragraph_data["runs"].append(run_data)

            formatting_info["runs"].append(run_data)

        formatting_info["paragraphs"].append(paragraph_data)

        if text:
            lines.append(text)

    # --------------------------------------------------------
    # Tables
    # --------------------------------------------------------

    table_start_index = len(lines)

    for table_index, table in enumerate(doc.tables):

        for row_index, row in enumerate(table.rows):

            row_cells = []

            for cell in row.cells:
                cell_text = cell.text.strip()

                if cell_text:
                    row_cells.append(cell_text)

            if row_cells:
                table_line = " | ".join(row_cells)
                lines.append(table_line)

    # --------------------------------------------------------
    # Images inside DOCX
    # --------------------------------------------------------

    try:
        relationships = doc.part.rels.values()

        for relationship in relationships:
            if relationship.reltype.endswith("/image"):
                formatting_info["images_count"] += 1

    except Exception:
        pass

    full_text = "\n".join(lines)

    if not full_text.strip():
        raise ExtractionError(
            "The DOCX document is empty."
        )

    formatting_info["styles_detected"] = sorted(styles)
    formatting_info["fonts_detected"] = sorted(fonts)

    formatting_info["table_lines_start"] = table_start_index

    return {
        "text": full_text,
        "lines": lines,
        "formatting": formatting_info
    }


# ============================================================
# PDF EXTRACTION
# ============================================================

def _extract_pdf(file_path):
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ExtractionError(
            f"Failed to open PDF file: {str(e)}"
        )

    lines = []

    formatting_info = {
        "document_type": "pdf",
        "pages_count": len(doc),
        "fonts_detected": [],
        "runs": [],
        "paragraphs": [],
        "images_count": 0
    }

    fonts = set()
    total_images = 0

    for page_number, page in enumerate(doc):

        # ----------------------------------------------------
        # Text extraction
        # ----------------------------------------------------

        text = page.get_text()

        if text.strip():

            page_lines = [
                line.strip()
                for line in text.split("\n")
                if line.strip()
            ]

            lines.extend(page_lines)

        # ----------------------------------------------------
        # Detailed PDF formatting
        # ----------------------------------------------------

        try:

            page_dict = page.get_text("dict")

            for block in page_dict.get("blocks", []):

                # Text block
                if "lines" in block:

                    for line in block.get("lines", []):

                        for span in line.get("spans", []):

                            font_name = span.get("font", "")
                            font_size = span.get("size")

                            if font_name:
                                fonts.add(font_name)

                            formatting_info["runs"].append({
                                "page": page_number + 1,
                                "text": span.get("text", ""),
                                "font_name": font_name,
                                "font_size": round(font_size, 2)
                                if font_size is not None
                                else None,
                                "bold": False,
                                "italic": False,
                                "underline": False
                            })

                # Image block
                if block.get("type") == 1:
                    total_images += 1

        except Exception:
            pass

        # ----------------------------------------------------
        # Count embedded images
        # ----------------------------------------------------

        try:
            total_images += len(page.get_images(full=True))
        except Exception:
            pass

    formatting_info["fonts_detected"] = sorted(fonts)
    formatting_info["images_count"] = total_images

    full_text = "\n".join(lines)

    # Empty text usually means scanned/image-only PDF.
    if not full_text.strip():

        formatting_info["document_type"] = "scanned_pdf"
        formatting_info["image_detected"] = True

    return {
        "text": full_text,
        "lines": lines,
        "formatting": formatting_info
    }


# ============================================================
# HELPERS
# ============================================================

def _get_alignment_name(alignment):

    if alignment is None:
        return "None"

    mapping = {
        WD_ALIGN_PARAGRAPH.LEFT: "LEFT",
        WD_ALIGN_PARAGRAPH.CENTER: "CENTER",
        WD_ALIGN_PARAGRAPH.RIGHT: "RIGHT",
        WD_ALIGN_PARAGRAPH.JUSTIFY: "JUSTIFY",
        WD_ALIGN_PARAGRAPH.DISTRIBUTE: "DISTRIBUTE"
    }

    return mapping.get(alignment, str(alignment))