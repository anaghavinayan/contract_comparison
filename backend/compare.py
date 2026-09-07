import difflib

def generate_text_diff(lines_a, lines_b):
    """
    Generates a side-by-side HTML diff table using difflib.HtmlDiff.
    
    :param lines_a: List of lines from the original contract
    :param lines_b: List of lines from the modified contract
    :return: HTML string representing the side-by-side comparison table
    """
    # Create HtmlDiff instance
    html_diff = difflib.HtmlDiff(tabsize=4)
    
    # Generate table HTML. context=False means show full documents.
    diff_table = html_diff.make_table(
        lines_a, 
        lines_b, 
        fromdesc='Original Document', 
        todesc='Modified Document',
        context=False
    )
    return diff_table

def compare_formatting(meta_a, meta_b):
    """
    Compares formatting metadata extracted from both documents.
    
    :param meta_a: Formatting dict from original document
    :param meta_b: Formatting dict from modified document
    :return: List of detected formatting differences
    """
    differences = []
    
    # 1. Structure changes
    pages_a = meta_a.get('pages_count')
    pages_b = meta_b.get('pages_count')
    if pages_a is not None and pages_b is not None:
        if pages_a != pages_b:
            differences.append({
                'category': 'Formatting',
                'description': f"Document length changed from {pages_a} pages to {pages_b} pages.",
                'severity': 'Low'
            })
            
    paras_a = meta_a.get('paragraphs_count')
    paras_b = meta_b.get('paragraphs_count')
    if paras_a is not None and paras_b is not None:
        if paras_a != paras_b:
            differences.append({
                'category': 'Formatting',
                'description': f"Total paragraphs changed from {paras_a} to {paras_b}.",
                'severity': 'Low'
            })

    # 2. Font/Styles changes
    fonts_a = set(meta_a.get('fonts_detected', []))
    fonts_b = set(meta_b.get('fonts_detected', []))
    if fonts_a or fonts_b:
        added_fonts = fonts_b - fonts_a
        removed_fonts = fonts_a - fonts_b
        if added_fonts:
            differences.append({
                'category': 'Formatting',
                'description': f"New fonts/styles introduced: {', '.join(added_fonts)}.",
                'severity': 'Low'
            })
        if removed_fonts:
            differences.append({
                'category': 'Formatting',
                'description': f"Fonts/styles removed: {', '.join(removed_fonts)}.",
                'severity': 'Low'
            })
            
    styles_a = set(meta_a.get('styles_detected', []))
    styles_b = set(meta_b.get('styles_detected', []))
    if styles_a or styles_b:
        added_styles = styles_b - styles_a
        removed_styles = styles_a - styles_b
        if added_styles:
            differences.append({
                'category': 'Formatting',
                'description': f"New document style templates applied: {', '.join(added_styles)}.",
                'severity': 'Low'
            })
        if removed_styles:
            differences.append({
                'category': 'Formatting',
                'description': f"Style templates removed: {', '.join(removed_styles)}.",
                'severity': 'Low'
            })
            
    return differences

def get_textual_changes(lines_a, lines_b):
    """
    Computes a list of textual differences locally without Gemini.
    
    :param lines_a: List of lines from the original contract
    :param lines_b: List of lines from the modified contract
    :return: List of textual difference records (dict format)
    """
    changes = []
    matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            max_range = max(i2 - i1, j2 - j1)
            for idx in range(max_range):
                orig_idx = i1 + idx
                mod_idx = j1 + idx
                
                orig_line = lines_a[orig_idx] if orig_idx < i2 else ""
                mod_line = lines_b[mod_idx] if mod_idx < j2 else ""
                
                if not orig_line.strip() and not mod_line.strip():
                    continue
                    
                changes.append({
                    'category': 'Textual',
                    'description': "Clause text modified.",
                    'severity': 'Medium',
                    'section': f"Line {orig_idx + 1 if orig_idx < i2 else i1 + 1}",
                    'originalText': orig_line,
                    'modifiedText': mod_line
                })
        elif tag == 'delete':
            for idx in range(i1, i2):
                orig_line = lines_a[idx]
                if not orig_line.strip():
                    continue
                changes.append({
                    'category': 'Textual',
                    'description': "Clause text removed.",
                    'severity': 'High',
                    'section': f"Line {idx + 1}",
                    'originalText': orig_line,
                    'modifiedText': ""
                })
        elif tag == 'insert':
            for idx in range(j1, j2):
                mod_line = lines_b[idx]
                if not mod_line.strip():
                    continue
                changes.append({
                    'category': 'Textual',
                    'description': "New clause text added.",
                    'severity': 'Medium',
                    'section': f"Line {i1 + 1}",
                    'originalText': "",
                    'modifiedText': mod_line
                })
                
    return changes
