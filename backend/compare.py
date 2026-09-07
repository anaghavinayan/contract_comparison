import difflib
import re


# ============================================================
# SIDE-BY-SIDE TEXT DIFF
# ============================================================

def generate_text_diff(lines_a, lines_b):
    """
    Generate the HTML side-by-side difference view.
    """

    html_diff = difflib.HtmlDiff(tabsize=4)

    return html_diff.make_table(
        lines_a,
        lines_b,
        fromdesc="Original Document",
        todesc="Modified Document",
        context=False
    )


# ============================================================
# DATE DETECTION
# ============================================================

DATE_PATTERNS = [

    # June 1, 2026
    r"\b(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},\s+\d{4}\b",

    # 1 June 2026
    r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|"
    r"August|September|October|November|December)\s+\d{4}\b",

    # 2026-06-01
    r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",

    # 06/01/2026
    r"\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b"
]


def extract_dates(text):
    """
    Extract recognizable date references from text.
    """

    dates = []

    for pattern in DATE_PATTERNS:

        matches = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        for match in matches:

            if match not in dates:
                dates.append(match)

    return dates


# ============================================================
# GRAMMAR DETECTION
# ============================================================

# Common grammatical corrections.
# These are deliberately conservative so that ordinary
# contractual number/value changes are not classified as grammar.

GRAMMAR_PAIRS = {
    "agree": {"agrees"},
    "agrees": {"agree"},

    "is": {"are"},
    "are": {"is"},

    "was": {"were"},
    "were": {"was"},

    "has": {"have"},
    "have": {"has"},

    "does": {"do"},
    "do": {"does"},

    "this": {"these"},
    "these": {"this"},

    "that": {"those"},
    "those": {"that"},

    "its": {"their"},
    "their": {"its"},

    "a": {"an"},
    "an": {"a"}
}


def _tokenize_words(text):
    """
    Convert text into word tokens while preserving
    simple contractions and hyphenated words.
    """

    return re.findall(
        r"\b[\w'-]+\b",
        text.lower()
    )


def _grammar_token_change(original, modified):
    """
    Check whether a sentence contains a small grammatical
    correction.

    Example:

        The Consultant agree to...
        The Consultant agrees to...

    Only one token changed:

        agree -> agrees

    Therefore this is classified as Grammar.
    """

    original_words = _tokenize_words(original)
    modified_words = _tokenize_words(modified)

    if not original_words or not modified_words:
        return False

    matcher = difflib.SequenceMatcher(
        None,
        original_words,
        modified_words
    )

    replacements = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "equal":
            continue

        # We only want very small grammatical replacements.
        if tag == "replace":

            old_words = original_words[i1:i2]
            new_words = modified_words[j1:j2]

            replacements.append(
                (old_words, new_words)
            )

        else:
            # Insertions/deletions can be grammatical, but
            # we keep the local detector conservative.
            return False

    # Exactly one small replacement
    if len(replacements) != 1:
        return False

    old_words, new_words = replacements[0]

    # --------------------------------------------------------
    # Single-word grammar correction
    # --------------------------------------------------------

    if len(old_words) == 1 and len(new_words) == 1:

        old_word = old_words[0]
        new_word = new_words[0]

        if (
            old_word in GRAMMAR_PAIRS
            and
            new_word in GRAMMAR_PAIRS[old_word]
        ):
            return True

        # Simple subject-verb agreement patterns
        if (
            len(old_word) >= 3
            and
            len(new_word) >= 3
            and
            (
                old_word + "s" == new_word
                or
                new_word + "s" == old_word
            )
        ):
            return True

    # --------------------------------------------------------
    # Two-word grammar correction
    # --------------------------------------------------------

    if len(old_words) <= 2 and len(new_words) <= 2:

        for old_word in old_words:

            for new_word in new_words:

                if (
                    old_word in GRAMMAR_PAIRS
                    and
                    new_word in GRAMMAR_PAIRS[old_word]
                ):
                    return True

    # --------------------------------------------------------
    # Punctuation correction
    # --------------------------------------------------------

    original_without_punctuation = re.sub(
        r"[^\w\s]",
        "",
        original.lower()
    )

    modified_without_punctuation = re.sub(
        r"[^\w\s]",
        "",
        modified.lower()
    )

    if (
        original_without_punctuation
        ==
        modified_without_punctuation
    ):
        return True

    return False


# ============================================================
# TEXTUAL / GRAMMAR / DATE CHANGES
# ============================================================

def get_textual_changes(lines_a, lines_b):
    """
    Compare document lines and classify detected changes
    as Textual, Grammar, or Dates.
    """

    changes = []

    matcher = difflib.SequenceMatcher(
        None,
        lines_a,
        lines_b
    )

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        # ====================================================
        # REPLACEMENT
        # ====================================================

        if tag == "replace":

            max_range = max(
                i2 - i1,
                j2 - j1
            )

            for idx in range(max_range):

                orig_idx = i1 + idx
                mod_idx = j1 + idx

                original_text = (
                    lines_a[orig_idx]
                    if orig_idx < i2
                    else ""
                )

                modified_text = (
                    lines_b[mod_idx]
                    if mod_idx < j2
                    else ""
                )

                if (
                    not original_text.strip()
                    and
                    not modified_text.strip()
                ):
                    continue

                # ------------------------------------------------
                # Default classification
                # ------------------------------------------------

                category = "Textual"
                description = "Clause text modified."
                severity = "Medium"

                # =================================================
                # DATE CHANGE
                # =================================================

                original_dates = extract_dates(
                    original_text
                )

                modified_dates = extract_dates(
                    modified_text
                )

                if (
                    original_dates
                    or
                    modified_dates
                ) and (
                    original_dates
                    !=
                    modified_dates
                ):

                    category = "Dates"

                    description = (
                        "Date reference changed from "
                        f"{', '.join(original_dates) or 'none'} "
                        "to "
                        f"{', '.join(modified_dates) or 'none'}."
                    )

                    severity = "Medium"

                # =================================================
                # GRAMMAR CHANGE
                # =================================================

                elif _grammar_token_change(
                    original_text,
                    modified_text
                ):

                    category = "Grammar"

                    description = (
                        "Grammar or language correction detected."
                    )

                    severity = "Low"

                # =================================================
                # CONTRACTUAL NUMBER / VALUE CHANGE
                # =================================================

                elif (
                    re.search(
                        r"\b\d+\b",
                        original_text
                    )
                    and
                    re.search(
                        r"\b\d+\b",
                        modified_text
                    )
                ):

                    category = "Textual"

                    description = (
                        "Contract value or term modified."
                    )

                    severity = "High"

                # =================================================
                # STORE CHANGE
                # =================================================

                changes.append({

                    "category":
                        category,

                    "description":
                        description,

                    "severity":
                        severity,

                    "section":
                        (
                            f"Line {orig_idx + 1}"
                            if orig_idx < i2
                            else
                            f"Line {i1 + 1}"
                        ),

                    "originalText":
                        original_text,

                    "modifiedText":
                        modified_text
                })

        # ====================================================
        # DELETION
        # ====================================================

        elif tag == "delete":

            for idx in range(i1, i2):

                original_text = lines_a[idx]

                if not original_text.strip():
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
                        original_text,

                    "modifiedText":
                        ""
                })

        # ====================================================
        # INSERTION
        # ====================================================

        elif tag == "insert":

            for idx in range(j1, j2):

                modified_text = lines_b[idx]

                if not modified_text.strip():
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
                        modified_text
                })

    # ========================================================
    # ADD UNIQUE IDs
    # ========================================================

    for index, change in enumerate(changes):

        change["id"] = (
            f"local-change-{index + 1}"
        )

    return changes


# ============================================================
# FORMATTING COMPARISON
# ============================================================

def compare_formatting(meta_a, meta_b):

    differences = []

    # ========================================================
    # PARAGRAPH COUNT
    # ========================================================

    paragraphs_a = meta_a.get(
        "paragraphs_count"
    )

    paragraphs_b = meta_b.get(
        "paragraphs_count"
    )

    if (
        paragraphs_a is not None
        and
        paragraphs_b is not None
        and
        paragraphs_a != paragraphs_b
    ):

        differences.append({

            "category":
                "Formatting",

            "description":
                (
                    "Paragraph count changed from "
                    f"{paragraphs_a} to {paragraphs_b}."
                ),

            "severity":
                "Low",

            "section":
                "Document Structure",

            "originalText":
                str(paragraphs_a),

            "modifiedText":
                str(paragraphs_b)
        })

    # ========================================================
    # PAGE COUNT
    # ========================================================

    pages_a = meta_a.get(
        "pages_count"
    )

    pages_b = meta_b.get(
        "pages_count"
    )

    if (
        pages_a is not None
        and
        pages_b is not None
        and
        pages_a != pages_b
    ):

        differences.append({

            "category":
                "Formatting",

            "description":
                (
                    "Page count changed from "
                    f"{pages_a} to {pages_b}."
                ),

            "severity":
                "Low",

            "section":
                "Document Layout",

            "originalText":
                str(pages_a),

            "modifiedText":
                str(pages_b)
        })

    # ========================================================
    # FONT FAMILIES
    # ========================================================

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

    added_fonts = fonts_b - fonts_a
    removed_fonts = fonts_a - fonts_b

    if added_fonts:

        differences.append({

            "category":
                "Formatting",

            "description":
                (
                    "New font(s) detected: "
                    +
                    ", ".join(
                        sorted(added_fonts)
                    )
                ),

            "severity":
                "Low",

            "section":
                "Font",

            "originalText":
                "",

            "modifiedText":
                ", ".join(
                    sorted(added_fonts)
                )
        })

    if removed_fonts:

        differences.append({

            "category":
                "Formatting",

            "description":
                (
                    "Font(s) removed: "
                    +
                    ", ".join(
                        sorted(removed_fonts)
                    )
                ),

            "severity":
                "Low",

            "section":
                "Font",

            "originalText":
                ", ".join(
                    sorted(removed_fonts)
                ),

            "modifiedText":
                ""
        })

    # ========================================================
    # PARAGRAPH STYLES
    # ========================================================

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

    added_styles = styles_b - styles_a
    removed_styles = styles_a - styles_b

    if added_styles:

        differences.append({

            "category":
                "Formatting",

            "description":
                (
                    "New paragraph style(s) detected: "
                    +
                    ", ".join(
                        sorted(added_styles)
                    )
                ),

            "severity":
                "Low",

            "section":
                "Paragraph Style",

            "originalText":
                "",

            "modifiedText":
                ", ".join(
                    sorted(added_styles)
                )
        })

    if removed_styles:

        differences.append({

            "category":
                "Formatting",

            "description":
                (
                    "Paragraph style(s) removed: "
                    +
                    ", ".join(
                        sorted(removed_styles)
                    )
                ),

            "severity":
                "Low",

            "section":
                "Paragraph Style",

            "originalText":
                ", ".join(
                    sorted(removed_styles)
                ),

            "modifiedText":
                ""
        })

    # ========================================================
    # RUN-LEVEL FORMATTING
    # ========================================================

    runs_a = meta_a.get(
        "runs",
        []
    )

    runs_b = meta_b.get(
        "runs",
        []
    )

    max_runs = max(
        len(runs_a),
        len(runs_b)
    )

    for index in range(max_runs):

        run_a = (
            runs_a[index]
            if index < len(runs_a)
            else None
        )

        run_b = (
            runs_b[index]
            if index < len(runs_b)
            else None
        )

        if not run_a or not run_b:
            continue

        formatting_properties = [

            (
                "font_name",
                "font"
            ),

            (
                "font_size",
                "font size"
            ),

            (
                "bold",
                "bold"
            ),

            (
                "italic",
                "italic"
            ),

            (
                "underline",
                "underline"
            ),

            (
                "strike",
                "strikethrough"
            ),

            (
                "color",
                "font color"
            ),

            (
                "highlight",
                "highlight"
            )
        ]

        for property_name, display_name in (
            formatting_properties
        ):

            value_a = run_a.get(
                property_name
            )

            value_b = run_b.get(
                property_name
            )

            if value_a == value_b:
                continue

            if (
                value_a is None
                and
                value_b is None
            ):
                continue

            original_display = (
                str(value_a)
                if value_a is not None
                else
                "default"
            )

            modified_display = (
                str(value_b)
                if value_b is not None
                else
                "default"
            )

            differences.append({

                "category":
                    "Formatting",

                "description":
                    (
                        f"{display_name.capitalize()} "
                        f"changed from "
                        f"{original_display} "
                        f"to "
                        f"{modified_display}."
                    ),

                "severity":
                    "Low",

                "section":
                    (
                        "Paragraph "
                        +
                        str(
                            run_a.get(
                                "paragraph_index",
                                0
                            ) + 1
                        )
                    ),

                "originalText":
                    original_display,

                "modifiedText":
                    modified_display
            })

    # ========================================================
    # VISUAL / IMAGE COUNT
    # ========================================================

    images_a = meta_a.get(
        "images_count",
        0
    )

    images_b = meta_b.get(
        "images_count",
        0
    )

    if images_a != images_b:

        differences.append({

            "category":
                "Visual",

            "description":
                (
                    "Embedded image count changed "
                    f"from {images_a} to {images_b}."
                ),

            "severity":
                "Medium",

            "section":
                "Visual Elements",

            "originalText":
                str(images_a),

            "modifiedText":
                str(images_b)
        })

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    unique = []
    seen = set()

    for difference in differences:

        key = (

            difference["category"],

            difference["description"],

            difference["section"],

            difference["originalText"],

            difference["modifiedText"]
        )

        if key not in seen:

            seen.add(key)
            unique.append(
                difference
            )

    # ========================================================
    # IDS
    # ========================================================

    for index, difference in enumerate(
        unique
    ):

        difference["id"] = (
            f"local-format-{index + 1}"
        )

    return unique