# Mock data for Demo Mode

DEMO_SUMMARY = {
    "totalChanges": 5,
    "textualChanges": 3,
    "grammarChanges": 1,
    "formattingChanges": 1,
    "visualChanges": 0,
    "dateChanges": 1,
    "severityHigh": 1,
    "severityMedium": 2,
    "severityLow": 2,
    "verdict": "CRITICAL: The payment term has been shortened from 30 to 15 days, and termination notice was reduced. The start date was also shifted to July. A grammatical error in Section 3 has been corrected."
}

DEMO_CHANGES = [
    {
        "id": "demo-change-1",
        "category": "Textual",
        "severity": "High",
        "section": "Section 4.1: Payments",
        "description": "Payment term changed from 30 days to 15 days.",
        "originalText": "Payment shall be made within thirty (30) days of receipt of invoice.",
        "modifiedText": "Payment shall be made within fifteen (15) days of receipt of invoice."
    },
    {
        "id": "demo-change-2",
        "category": "Dates",
        "severity": "Medium",
        "section": "Section 1.2: Term",
        "description": "Effective start date shifted by one month.",
        "originalText": "This Agreement shall commence on June 1, 2026.",
        "modifiedText": "This Agreement shall commence on July 1, 2026."
    },
    {
        "id": "demo-change-3",
        "category": "Textual",
        "severity": "Medium",
        "section": "Section 8.2: Termination",
        "description": "Termination notice period reduced from 90 days to 60 days.",
        "originalText": "Either party may terminate this agreement upon ninety (90) days written notice.",
        "modifiedText": "Either party may terminate this agreement upon sixty (60) days written notice."
    },
    {
        "id": "demo-change-4",
        "category": "Grammar",
        "severity": "Low",
        "section": "Section 3.4: Confidentiality",
        "description": "Corrected subject-verb agreement.",
        "originalText": "The Consultant agree to keep all information confidential.",
        "modifiedText": "The Consultant agrees to keep all information confidential."
    },
    {
        "id": "demo-change-5",
        "category": "Formatting",
        "severity": "Low",
        "section": "Document Metadata",
        "description": "Font changes detected between original and modified documents.",
        "originalText": "Font Style: Arial",
        "modifiedText": "Font Style: Times New Roman"
    }
]

# Simulated difflib.HtmlDiff table output
DEMO_DIFF_HTML = """
<table class="diff" id="difflib_chg_to0__cls" cellspacing="0" cellpadding="0" rules="groups">
    <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
    <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
    <thead>
        <tr><th class="diff_header" colspan="2">Original Document (Consulting_Agreement_Original.docx)</th><th class="diff_header" colspan="2">Modified Document (Consulting_Agreement_Revised.docx)</th></tr>
    </thead>
    <tbody>
        <tr><td class="diff_header" id="from0_1">1</td><td nowrap="nowrap">CONSULTING SERVICE AGREEMENT</td><td class="diff_header" id="to0_1">1</td><td nowrap="nowrap">CONSULTING SERVICE AGREEMENT</td></tr>
        <tr><td class="diff_header" id="from0_2">2</td><td nowrap="nowrap"></td><td class="diff_header" id="to0_2">2</td><td nowrap="nowrap"></td></tr>
        <tr><td class="diff_header" id="from0_3">3</td><td nowrap="nowrap">1. TERM OF AGREEMENT</td><td class="diff_header" id="to0_3">3</td><td nowrap="nowrap">1. TERM OF AGREEMENT</td></tr>
        <tr><td class="diff_header" id="from0_4">4</td><td nowrap="nowrap">1.2 <span class="diff_chg">This Agreement shall commence on June 1, 2026.</span></td><td class="diff_header" id="to0_4">4</td><td nowrap="nowrap">1.2 <span class="diff_chg">This Agreement shall commence on July 1, 2026.</span></td></tr>
        <tr><td class="diff_header" id="from0_5">5</td><td nowrap="nowrap"></td><td class="diff_header" id="to0_5">5</td><td nowrap="nowrap"></td></tr>
        <tr><td class="diff_header" id="from0_6">6</td><td nowrap="nowrap">3. CONFIDENTIALITY</td><td class="diff_header" id="to0_6">6</td><td nowrap="nowrap">3. CONFIDENTIALITY</td></tr>
        <tr><td class="diff_header" id="from0_7">7</td><td nowrap="nowrap">3.4 <span class="diff_chg">The Consultant agree to keep all information confidential.</span></td><td class="diff_header" id="to0_7">7</td><td nowrap="nowrap">3.4 <span class="diff_chg">The Consultant agrees to keep all information confidential.</span></td></tr>
        <tr><td class="diff_header" id="from0_8">8</td><td nowrap="nowrap"></td><td class="diff_header" id="to0_8">8</td><td nowrap="nowrap"></td></tr>
        <tr><td class="diff_header" id="from0_9">9</td><td nowrap="nowrap">4. REMUNERATION AND BILLING</td><td class="diff_header" id="to0_9">9</td><td nowrap="nowrap">4. REMUNERATION AND BILLING</td></tr>
        <tr><td class="diff_header" id="from0_10">10</td><td nowrap="nowrap">4.1 <span class="diff_chg">Payment shall be made within thirty (30) days of receipt of invoice.</span></td><td class="diff_header" id="to0_10">10</td><td nowrap="nowrap">4.1 <span class="diff_chg">Payment shall be made within fifteen (15) days of receipt of invoice.</span></td></tr>
        <tr><td class="diff_header" id="from0_11">11</td><td nowrap="nowrap"></td><td class="diff_header" id="to0_11">11</td><td nowrap="nowrap"></td></tr>
        <tr><td class="diff_header" id="from0_12">12</td><td nowrap="nowrap">8. TERMINATION OF AGREEMENT</td><td class="diff_header" id="to0_12">12</td><td nowrap="nowrap">8. TERMINATION OF AGREEMENT</td></tr>
        <tr><td class="diff_header" id="from0_13">13</td><td nowrap="nowrap">8.2 <span class="diff_chg">Either party may terminate this agreement upon ninety (90) days written notice.</span></td><td class="diff_header" id="to0_13">13</td><td nowrap="nowrap">8.2 <span class="diff_chg">Either party may terminate this agreement upon sixty (60) days written notice.</span></td></tr>
    </tbody>
</table>
"""

DEMO_RESULTS = {
    "file_a_name": "Consulting_Agreement_Original.docx",
    "file_b_name": "Consulting_Agreement_Revised.docx",
    "summary": DEMO_SUMMARY,
    "changes": DEMO_CHANGES,
    "diff_html": DEMO_DIFF_HTML
}
