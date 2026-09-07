import difflib
import re


def generate_text_diff(lines_a, lines_b):
    """
    Generate a clean side-by-side HTML diff without HtmlDiff navigation links.
    """

    html_diff = difflib.HtmlDiff(tabsize=4)

    diff_table = html_diff.make_table(
        lines_a,
        lines_b,
        fromdesc="Original Document",
        todesc="Modified Document",
        context=False
    )

    # Remove HtmlDiff navigation cells such as:
    # f = first difference
    # n = next difference
    # t = top
    diff_table = re.sub(
        r'<td\s+class="diff_next"[^>]*>.*?</td>',
        '',
        diff_table,
        flags=re.DOTALL
    )

    diff_table = re.sub(
        r'<th\s+class="diff_next"[^>]*>.*?</th>',
        '',
        diff_table,
        flags=re.DOTALL
    )

    return diff_table


def _normalise(value):
    if value is None:
        return None

    if isinstance(value, bool):
        return bool(value)

    if isinstance(value, (int, float)):
        return float(value)

    return str(value).strip()


def _get_paragraphs(meta):
    """
    Return paragraph formatting records.

    Supports several possible extractor field names.
    """

    for key in (
        "paragraphs",
        "paragraph_formatting",
        "paragraph_metadata"
    ):

        value = meta.get(key)

        if isinstance(value, list):
            return value

    return []


def _get_runs(paragraph):
    """
    Return run-level formatting records.
    """

    if not isinstance(paragraph, dict):
        return []

    for key in (
        "runs",
        "run_formatting",
        "run_metadata"
    ):

        value = paragraph.get(key)

        if isinstance(value, list):
            return value

    return []


def _run_signature(run):
    """
    Extract formatting properties from a run.
    """

    if not isinstance(run, dict):
        return {}

    return {
        "font_name": _normalise(
            run.get(
                "font_name",
                run.get("font")
            )
        ),

        "font_size": _normalise(
            run.get(
                "font_size",
                run.get("size")
            )
        ),

        "bold": _normalise(
            run.get("bold")
        ),

        "italic": _normalise(
            run.get("italic")
        ),

        "underline": _normalise(
            run.get("underline")
        ),

        "strike": _normalise(
            run.get(
                "strike",
                run.get("strikethrough")
            )
        ),

        "color": _normalise(
            run.get(
                "color",
                run.get("font_color")
            )
        ),

        "highlight": _normalise(
            run.get("highlight")
        )
    }


def _paragraph_signature(paragraph):
    """
    Extract paragraph-level formatting properties.
    """

    if not isinstance(paragraph, dict):
        return {}

    return {
        "alignment": _normalise(
            paragraph.get(
                "alignment",
                paragraph.get("paragraph_alignment")
            )
        ),

        "font_name": _normalise(
            paragraph.get("font_name")
        ),

        "font_size": _normalise(
            paragraph.get("font_size")
        ),

        "bold": _normalise(
            paragraph.get("bold")
        ),

        "italic": _normalise(
            paragraph.get("italic")
        ),

        "underline": _normalise(
            paragraph.get("underline")
        ),

        "highlight": _normalise(
            paragraph.get("highlight")
        )
    }


def _append_change(
    changes,
    paragraph_index,
    description,
    original,
    modified
):

    changes.append({

        "category":
            "Formatting",

        "description":
            description,

        "severity":
            "Low",

        "section":
            f"Paragraph {paragraph_index + 1}",

        "originalText":
            str(original),

        "modifiedText":
            str(modified)
    })


def compare_formatting(meta_a, meta_b):
    """
    Compare document-level and DOCX run-level formatting.
    """

    differences = []

    # =========================================================
    # DOCUMENT STRUCTURE
    # =========================================================

    pages_a = meta_a.get("pages_count")
    pages_b = meta_b.get("pages_count")

    if (
        pages_a is not None
        and pages_b is not None
        and pages_a != pages_b
    ):

        differences.append({

            "category":
                "Formatting",

            "description":
                f"Document length changed from "
                f"{pages_a} pages to {pages_b} pages.",

            "severity":
                "Low"
        })


    paras_a_count = meta_a.get(
        "paragraphs_count"
    )

    paras_b_count = meta_b.get(
        "paragraphs_count"
    )

    if (
        paras_a_count is not None
        and paras_b_count is not None
        and paras_a_count != paras_b_count
    ):

        differences.append({

            "category":
                "Formatting",

            "description":
                f"Total paragraphs changed from "
                f"{paras_a_count} to {paras_b_count}.",

            "severity":
                "Low"
        })


    # =========================================================
    # FONT SETS
    # =========================================================

    fonts_a = set(
        meta_a.get(
            "fonts_detected",
            []
        )
    )

    fonts_b = set(
        meta_b.get(
            "fonts_detected",
            []
        )
    )

    if fonts_a or fonts_b:

        added_fonts = fonts_b - fonts_a
        removed_fonts = fonts_a - fonts_b

        if added_fonts:

            differences.append({

                "category":
                    "Formatting",

                "description":
                    "New fonts/styles introduced: "
                    + ", ".join(
                        sorted(
                            map(
                                str,
                                added_fonts
                            )
                        )
                    )
                    + ".",

                "severity":
                    "Low"
            })

        if removed_fonts:

            differences.append({

                "category":
                    "Formatting",

                "description":
                    "Fonts/styles removed: "
                    + ", ".join(
                        sorted(
                            map(
                                str,
                                removed_fonts
                            )
                        )
                    )
                    + ".",

                "severity":
                    "Low"
            })


    # =========================================================
    # DOCUMENT STYLE SETS
    # =========================================================

    styles_a = set(
        meta_a.get(
            "styles_detected",
            []
        )
    )

    styles_b = set(
        meta_b.get(
            "styles_detected",
            []
        )
    )

    if styles_a or styles_b:

        added_styles = styles_b - styles_a
        removed_styles = styles_a - styles_b

        if added_styles:

            differences.append({

                "category":
                    "Formatting",

                "description":
                    "New document style templates applied: "
                    + ", ".join(
                        sorted(
                            map(
                                str,
                                added_styles
                            )
                        )
                    )
                    + ".",

                "severity":
                    "Low"
            })

        if removed_styles:

            differences.append({

                "category":
                    "Formatting",

                "description":
                    "Style templates removed: "
                    + ", ".join(
                        sorted(
                            map(
                                str,
                                removed_styles
                            )
                        )
                    )
                    + ".",

                "severity":
                    "Low"
            })


    # =========================================================
    # VISUAL / IMAGE COUNT
    # =========================================================

    image_keys = (
        "images_count",
        "image_count",
        "images",
        "pictures_count",
        "visual_elements_count"
    )

    image_a = None
    image_b = None

    for key in image_keys:

        if (
            image_a is None
            and meta_a.get(key) is not None
        ):
            image_a = meta_a.get(key)

        if (
            image_b is None
            and meta_b.get(key) is not None
        ):
            image_b = meta_b.get(key)


    if isinstance(image_a, list):
        image_a = len(image_a)

    if isinstance(image_b, list):
        image_b = len(image_b)


    if (
        image_a is not None
        and image_b is not None
        and image_a != image_b
    ):

        differences.append({

            "category":
                "Visual",

            "description":
                f"Visual/image elements changed "
                f"from {image_a} to {image_b}.",

            "severity":
                "Low"
        })


    # =========================================================
    # PARAGRAPH-LEVEL FORMATTING
    # =========================================================

    paragraphs_a = _get_paragraphs(
        meta_a
    )

    paragraphs_b = _get_paragraphs(
        meta_b
    )


    # Some extractor versions may store
    # runs directly in the metadata.

    if (
        not paragraphs_a
        and isinstance(
            meta_a.get("runs"),
            list
        )
    ):

        paragraphs_a = [
            {
                "runs":
                    meta_a.get(
                        "runs",
                        []
                    )
            }
        ]


    if (
        not paragraphs_b
        and isinstance(
            meta_b.get("runs"),
            list
        )
    ):

        paragraphs_b = [
            {
                "runs":
                    meta_b.get(
                        "runs",
                        []
                    )
            }
        ]


    max_paragraphs = max(
        len(paragraphs_a),
        len(paragraphs_b)
    )


    formatting_fields = [

        (
            "font_size",
            "Font size"
        ),

        (
            "font_name",
            "Font"
        ),

        (
            "bold",
            "Bold"
        ),

        (
            "italic",
            "Italic"
        ),

        (
            "underline",
            "Underline"
        ),

        (
            "strike",
            "Strikethrough"
        ),

        (
            "color",
            "Font color"
        ),

        (
            "highlight",
            "Highlight"
        ),

        (
            "alignment",
            "Alignment"
        )
    ]


    for paragraph_index in range(
        max_paragraphs
    ):

        paragraph_a = (
            paragraphs_a[
                paragraph_index
            ]
            if paragraph_index
            < len(paragraphs_a)
            else {}
        )

        paragraph_b = (
            paragraphs_b[
                paragraph_index
            ]
            if paragraph_index
            < len(paragraphs_b)
            else {}
        )


        # -----------------------------------------------------
        # Paragraph-level formatting
        # -----------------------------------------------------

        sig_a = _paragraph_signature(
            paragraph_a
        )

        sig_b = _paragraph_signature(
            paragraph_b
        )


        for field, label in formatting_fields:

            value_a = sig_a.get(
                field
            )

            value_b = sig_b.get(
                field
            )


            if (
                value_a is None
                and value_b is None
            ):
                continue


            if value_a != value_b:

                _append_change(

                    differences,

                    paragraph_index,

                    f"{label} changed "
                    f"from {value_a} "
                    f"to {value_b}.",

                    value_a,

                    value_b
                )


        # -----------------------------------------------------
        # Run-level formatting
        # -----------------------------------------------------

        runs_a = _get_runs(
            paragraph_a
        )

        runs_b = _get_runs(
            paragraph_b
        )


        max_runs = max(
            len(runs_a),
            len(runs_b)
        )


        for run_index in range(
            max_runs
        ):

            run_a = (
                runs_a[run_index]
                if run_index
                < len(runs_a)
                else {}
            )

            run_b = (
                runs_b[run_index]
                if run_index
                < len(runs_b)
                else {}
            )


            run_sig_a = _run_signature(
                run_a
            )

            run_sig_b = _run_signature(
                run_b
            )


            for field, label in formatting_fields:

                value_a = run_sig_a.get(
                    field
                )

                value_b = run_sig_b.get(
                    field
                )


                if (
                    value_a is None
                    and value_b is None
                ):
                    continue


                if value_a != value_b:

                    description = (
                        f"{label} changed "
                        f"from {value_a} "
                        f"to {value_b}."
                    )


                    # Avoid duplicate formatting
                    # records when the same change
                    # exists at paragraph and run level.

                    duplicate = any(

                        change.get(
                            "section"
                        )
                        == (
                            f"Paragraph "
                            f"{paragraph_index + 1}"
                        )

                        and

                        change.get(
                            "description"
                        )
                        == description

                        for change
                        in differences
                    )


                    if not duplicate:

                        _append_change(

                            differences,

                            paragraph_index,

                            description,

                            value_a,

                            value_b
                        )


    return differences


def get_textual_changes(lines_a, lines_b):
    """
    Compare the textual content of both documents.
    """

    changes = []

    matcher = difflib.SequenceMatcher(
        None,
        lines_a,
        lines_b
    )


    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        # =====================================================
        # REPLACE
        # =====================================================

        if tag == "replace":

            max_range = max(
                i2 - i1,
                j2 - j1
            )


            for idx in range(
                max_range
            ):

                orig_idx = i1 + idx
                mod_idx = j1 + idx


                orig_line = (
                    lines_a[orig_idx]
                    if orig_idx < i2
                    else ""
                )


                mod_line = (
                    lines_b[mod_idx]
                    if mod_idx < j2
                    else ""
                )


                if (
                    not orig_line.strip()
                    and
                    not mod_line.strip()
                ):
                    continue


                changes.append({

                    "category":
                        "Textual",

                    "description":
                        "Clause text modified.",

                    "severity":
                        "Medium",

                    "section": (
                        f"Line {orig_idx + 1}"
                        if orig_idx < i2
                        else f"Line {i1 + 1}"
                    ),

                    "originalText":
                        orig_line,

                    "modifiedText":
                        mod_line
                })


        # =====================================================
        # DELETE
        # =====================================================

        elif tag == "delete":

            for idx in range(
                i1,
                i2
            ):

                orig_line = lines_a[idx]


                if not orig_line.strip():
                    continue


                changes.append({

                    "category":
                        "Textual",

                    "description":
                        "Clause text removed.",

                    "severity":
                        "High",

                    "section":
                        f"Line {idx + 1}",

                    "originalText":
                        orig_line,

                    "modifiedText":
                        ""
                })


        # =====================================================
        # INSERT
        # =====================================================

        elif tag == "insert":

            for idx in range(
                j1,
                j2
            ):

                mod_line = lines_b[idx]


                if not mod_line.strip():
                    continue


                changes.append({

                    "category":
                        "Textual",

                    "description":
                        "New clause text added.",

                    "severity":
                        "Medium",

                    "section":
                        f"Line {i1 + 1}",

                    "originalText":
                        "",

                    "modifiedText":
                        mod_line
                })


    return changes