document.addEventListener('DOMContentLoaded', () => {
    // State management
    const state = {
        files: {
            'file-a': null,
            'file-b': null
        },
        currentComparisonId: null,
        currentChanges: [],
        historyOpen: false
    };

    // DOM Elements
    const dropzoneA = document.getElementById('dropzone-a');
    const dropzoneB = document.getElementById('dropzone-b');
    const fileInputA = document.getElementById('file-a');
    const fileInputB = document.getElementById('file-b');
    const compareBtn = document.getElementById('compare-btn');
    const demoBtn = document.getElementById('demo-btn');
    const backBtn = document.getElementById('back-to-upload-btn');
    const downloadDocxBtn = document.getElementById('download-docx-btn');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');

    const uploadPanel = document.getElementById('upload-panel');
    const resultsPanel = document.getElementById('results-panel');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingStatus = document.getElementById('loading-status');
    const toastContainer = document.getElementById('toast-container');

    // History Drawer DOM
    const historyDrawer = document.getElementById('history-drawer');
    const toggleHistoryBtn = document.getElementById('toggle-history-btn');
    const closeHistoryBtn = document.getElementById('close-history-btn');
    const historyList = document.getElementById('history-list');

    // Filter Elements
    const filterCategory = document.getElementById('filter-category');
    const filterSeverity = document.getElementById('filter-severity');


    // -------------------------------------------------------------
    // Toast Notification System
    // -------------------------------------------------------------

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        let icon = '';

        if (type === 'success') {
            icon = `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>`;
        } else if (type === 'error') {
            icon = `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2.5" fill="none">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>`;
        }

        toast.innerHTML = `${icon} <span>${message}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 4000);
    }


    // -------------------------------------------------------------
    // Drag & Drop / File Input Event Handlers
    // -------------------------------------------------------------

    function initDropzone(dropzone, inputId) {
        const input = document.getElementById(inputId);
        const promptDiv = dropzone.querySelector('.dropzone-prompt');
        const detailsDiv = dropzone.querySelector('.file-details');
        const clearBtn = detailsDiv.querySelector('.btn-clear');

        // Click on dropzone to trigger input browse
        dropzone.addEventListener('click', (e) => {
            if (e.target.closest('.btn-clear')) return;
            input.click();
        });

        // Drag events
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const file = dt.files[0];

            if (file) {
                handleFileSelection(
                    file,
                    inputId,
                    promptDiv,
                    detailsDiv,
                    dropzone
                );
            }
        });

        input.addEventListener('change', () => {
            const file = input.files[0];

            if (file) {
                handleFileSelection(
                    file,
                    inputId,
                    promptDiv,
                    detailsDiv,
                    dropzone
                );
            }
        });

        clearBtn.addEventListener('click', (e) => {
            e.stopPropagation();

            clearFile(
                inputId,
                promptDiv,
                detailsDiv,
                dropzone
            );
        });
    }


    function handleFileSelection(
        file,
        inputId,
        promptDiv,
        detailsDiv,
        dropzone
    ) {
        // Validation: size check (16MB max)
        if (file.size > 16 * 1024 * 1024) {
            showToast(
                "File is too large. Max limit is 16MB.",
                "error"
            );
            return;
        }

        const ext = file.name
            .split('.')
            .pop()
            .toLowerCase();

        const allowedExts = [
            'pdf',
            'docx',
            'jpg',
            'jpeg',
            'png'
        ];

        if (!allowedExts.includes(ext)) {
            showToast(
                "Unsupported format. Please upload PDF, DOCX, or JPEG/PNG files.",
                "error"
            );
            return;
        }

        // Save file in state
        state.files[inputId] = file;

        // Visual mapping
        let visualType = 'doc';

        if (ext === 'pdf') {
            visualType = 'pdf';
        }

        if (['jpg', 'jpeg', 'png'].includes(ext)) {
            visualType = 'image';
        }

        dropzone.setAttribute(
            'data-file-type',
            visualType
        );

        promptDiv.classList.add('hidden');
        detailsDiv.classList.remove('hidden');

        detailsDiv.querySelector(
            '.file-name'
        ).textContent = file.name;

        detailsDiv.querySelector(
            '.file-size'
        ).textContent = formatBytes(file.size);

        updateCompareButtonState();
    }


    function clearFile(
        inputId,
        promptDiv,
        detailsDiv,
        dropzone
    ) {
        state.files[inputId] = null;

        document.getElementById(
            inputId
        ).value = '';

        dropzone.removeAttribute(
            'data-file-type'
        );

        detailsDiv.classList.add('hidden');
        promptDiv.classList.remove('hidden');

        updateCompareButtonState();
    }


    function updateCompareButtonState() {
        if (
            state.files['file-a'] &&
            state.files['file-b']
        ) {
            compareBtn.removeAttribute('disabled');
        } else {
            compareBtn.setAttribute(
                'disabled',
                'true'
            );
        }
    }


    function formatBytes(
        bytes,
        decimals = 2
    ) {
        if (bytes === 0) {
            return '0 Bytes';
        }

        const k = 1024;
        const dm =
            decimals < 0
                ? 0
                : decimals;

        const sizes = [
            'Bytes',
            'KB',
            'MB',
            'GB'
        ];

        const i = Math.floor(
            Math.log(bytes) /
            Math.log(k)
        );

        return (
            parseFloat(
                (
                    bytes /
                    Math.pow(k, i)
                ).toFixed(dm)
            ) +
            ' ' +
            sizes[i]
        );
    }


    // Initialize Dropzones
    initDropzone(
        dropzoneA,
        'file-a'
    );

    initDropzone(
        dropzoneB,
        'file-b'
    );


    // -------------------------------------------------------------
    // Tab Switching
    // -------------------------------------------------------------

    const tabButtons =
        document.querySelectorAll(
            '.tab-btn'
        );

    const tabPanels =
        document.querySelectorAll(
            '.tab-panel'
        );

    tabButtons.forEach(btn => {
        btn.addEventListener(
            'click',
            () => {
                const targetTab =
                    btn.getAttribute(
                        'data-tab'
                    );

                tabButtons.forEach(b =>
                    b.classList.remove(
                        'active'
                    )
                );

                tabPanels.forEach(p =>
                    p.classList.remove(
                        'active'
                    )
                );

                btn.classList.add(
                    'active'
                );

                document
                    .getElementById(
                        targetTab
                    )
                    .classList.add(
                        'active'
                    );
            }
        );
    });


    // -------------------------------------------------------------
    // Backend API Calls
    // -------------------------------------------------------------

    // Compare Action
    compareBtn.addEventListener(
        'click',
        async () => {

            if (
                !state.files['file-a'] ||
                !state.files['file-b']
            ) {
                return;
            }

            const formData =
                new FormData();

            formData.append(
                'file_a',
                state.files['file-a']
            );

            formData.append(
                'file_b',
                state.files['file-b']
            );

            setLoadingState(
                true,
                "Scanning documents..."
            );

            try {

                // Simulated stages for aesthetic feel
                setTimeout(() => {
                    loadingStatus.textContent =
                        "Extracting text structure...";
                }, 1000);

                setTimeout(() => {
                    loadingStatus.textContent =
                        "Aligning clauses and differences...";
                }, 2200);

                setTimeout(() => {
                    loadingStatus.textContent =
                        "Running AI audits (Gemini)...";
                }, 3500);

                const response =
                    await fetch(
                        '/api/compare',
                        {
                            method: 'POST',
                            body: formData
                        }
                    );

                const data =
                    await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.error ||
                        "Failed to compare documents."
                    );
                }

                // Render Result
                renderComparison(data);

                showToast(
                    "Documents compared successfully!",
                    "success"
                );

                // Switch Panel
                switchPanel(
                    'results-panel'
                );

                loadHistory();

            } catch (err) {

                console.error(err);

                showToast(
                    err.message,
                    "error"
                );

            } finally {

                setLoadingState(
                    false
                );
            }
        }
    );


    // -------------------------------------------------------------
    // Demo Mode Action
    // -------------------------------------------------------------

    demoBtn.addEventListener(
        'click',
        async () => {

            setLoadingState(
                true,
                "Loading demo contracts..."
            );

            try {

                setTimeout(() => {
                    loadingStatus.textContent =
                        "Comparing Demo Agreements...";
                }, 1000);

                const response =
                    await fetch(
                        '/api/demo'
                    );

                if (!response.ok) {
                    throw new Error(
                        "Failed to load demo data."
                    );
                }

                const data =
                    await response.json();

                // Render Result
                renderComparison(data);

                showToast(
                    "Demo Mode loaded successfully!",
                    "success"
                );

                // Switch Panel
                switchPanel(
                    'results-panel'
                );

            } catch (err) {

                showToast(
                    err.message,
                    "error"
                );

            } finally {

                setLoadingState(
                    false
                );
            }
        }
    );


    // -------------------------------------------------------------
    // Back to Upload Panel
    // -------------------------------------------------------------

    backBtn.addEventListener(
        'click',
        () => {
            switchPanel(
                'upload-panel'
            );
        }
    );


    // -------------------------------------------------------------
    // Results Rendering Logic
    // -------------------------------------------------------------

    function renderComparison(data) {

        state.currentComparisonId =
            data.id || null;

        state.currentChanges =
            data.changes || [];


        // Hide/Show Download buttons
        // based on whether we have a saved database ID
        if (state.currentComparisonId) {

            downloadDocxBtn.style.display =
                'inline-flex';

            downloadPdfBtn.style.display =
                'inline-flex';

        } else {

            downloadDocxBtn.style.display =
                'none';

            downloadPdfBtn.style.display =
                'none';
        }


        // Summary Text / Verdict
        document.getElementById(
            'dashboard-verdict'
        ).textContent =
            data.summary?.verdict ||
            "Comparison complete.";

        document.getElementById(
            'label-file-a'
        ).textContent =
            `Original: ${data.file_a_name}`;

        document.getElementById(
            'label-file-b'
        ).textContent =
            `Modified: ${data.file_b_name}`;


        // Setup Statistics Cards
        const counts = {
            Textual: 0,
            Grammar: 0,
            Formatting: 0,
            Dates: 0,
            Visual: 0
        };


        state.currentChanges.forEach(
            c => {

                if (
                    counts[c.category] !==
                    undefined
                ) {
                    counts[c.category]++;
                }

            }
        );


        document.getElementById(
            'stat-textual'
        ).textContent =
            counts.Textual;

        document.getElementById(
            'stat-grammar'
        ).textContent =
            counts.Grammar;

        document.getElementById(
            'stat-formatting'
        ).textContent =
            counts.Formatting;

        document.getElementById(
            'stat-dates'
        ).textContent =
            counts.Dates;


        // ---------------------------------------------------------
        // Visual Changes Statistics Card
        // ---------------------------------------------------------
        // The backend already returns Visual changes.
        // If the HTML does not contain a Visual card,
        // create one dynamically.

        let visualStat =
            document.getElementById(
                'stat-visual'
            );

        if (!visualStat) {

            const datesStat =
                document.getElementById(
                    'stat-dates'
                );

            const statsGrid =
                datesStat?.closest(
                    '.stat-card'
                )?.parentElement;

            if (statsGrid) {

                const visualCard =
                    document.createElement(
                        'div'
                    );

                visualCard.className =
                    'stat-card';

                visualCard.setAttribute(
                    'data-category',
                    'Visual'
                );

                visualCard.innerHTML = `
                    <div
                        class="stat-number"
                        id="stat-visual"
                    >
                        0
                    </div>

                    <div
                        class="stat-label"
                    >
                        Visual Changes
                    </div>
                `;

                statsGrid.appendChild(
                    visualCard
                );

                visualStat =
                    document.getElementById(
                        'stat-visual'
                    );


                // Click Visual card to filter
                // the Changes Log
                visualCard.addEventListener(
                    'click',
                    () => {

                        filterCategory.value =
                            'Visual';

                        document
                            .querySelector(
                                '[data-tab="tab-changes"]'
                            )
                            .click();

                        renderChangesList();
                    }
                );
            }
        }


        // Update Visual count
        if (visualStat) {

            visualStat.textContent =
                counts.Visual;
        }


        // ---------------------------------------------------------
        // Side-by-Side Diff
        // ---------------------------------------------------------

        const diffTableWrapper =
            document.getElementById(
                'diff-table-wrapper'
            );


        // Check whether backend generated
        // a usable normal text diff.
        const hasUsableDiff =
            data.diff_html &&
            !data.diff_html.includes(
                'Empty File'
            );


        // ---------------------------------------------------------
        // NORMAL TEXT DOCUMENTS
        // ---------------------------------------------------------

        if (hasUsableDiff) {

            diffTableWrapper.innerHTML =
                data.diff_html;

        }


        // ---------------------------------------------------------
        // SCANNED / IMAGE DOCUMENTS
        // ---------------------------------------------------------

        else if (
            state.currentChanges.length > 0
        ) {

            const rows =
                state.currentChanges
                    .map(c => {

                        const location =
                            c.location ||
                            c.section ||
                            'General';


                        const original =
                            c.original ??
                            c.originalText ??
                            '-';


                        const modified =
                            c.modified ??
                            c.modifiedText ??
                            '-';


                        const description =
                            c.description ||
                            'Difference detected by Gemini AI.';


                        return `
                            <tr>

                                <td
                                    style="
                                        width:16%;
                                        min-width:150px;
                                        padding:16px;
                                        vertical-align:top;
                                        font-weight:600;
                                        white-space:normal;
                                        overflow-wrap:anywhere;
                                        word-break:normal;
                                        line-height:1.5;
                                    "
                                >
                                    ${escapeHtml(
                                        String(location)
                                    )}
                                </td>


                                <td
                                    style="
                                        width:28%;
                                        padding:16px;
                                        vertical-align:top;
                                    "
                                >

                                    <div
                                        class="cell-code"
                                        style="
                                            width:100%;
                                            box-sizing:border-box;
                                            padding:14px;
                                            white-space:pre-wrap;
                                            overflow-wrap:anywhere;
                                            word-break:normal;
                                            line-height:1.6;
                                            overflow:visible;
                                        "
                                    >
                                        ${escapeHtml(
                                            String(original)
                                        )}
                                    </div>

                                </td>


                                <td
                                    style="
                                        width:28%;
                                        padding:16px;
                                        vertical-align:top;
                                    "
                                >

                                    <div
                                        class="cell-code"
                                        style="
                                            width:100%;
                                            box-sizing:border-box;
                                            padding:14px;
                                            white-space:pre-wrap;
                                            overflow-wrap:anywhere;
                                            word-break:normal;
                                            line-height:1.6;
                                            overflow:visible;
                                            color:var(--color-success);
                                        "
                                    >
                                        ${escapeHtml(
                                            String(modified)
                                        )}
                                    </div>

                                </td>


                                <td
                                    style="
                                        width:28%;
                                        padding:16px;
                                        vertical-align:top;
                                        white-space:normal;
                                        overflow-wrap:anywhere;
                                        word-break:normal;
                                        line-height:1.6;
                                    "
                                >
                                    ${escapeHtml(
                                        String(description)
                                    )}
                                </td>

                            </tr>
                        `;

                    })
                    .join('');


            diffTableWrapper.innerHTML = `

                <div
                    style="
                        padding:14px 18px;
                        color:var(--color-text-secondary);
                        font-size:13px;
                    "
                >

                    <strong
                        style="
                            color:var(--color-primary);
                        "
                    >
                        AI OCR Side-by-Side Differences
                    </strong>

                    <span style="margin-left:8px;">
                        Scanned document text was extracted
                        and compared by Gemini.
                    </span>

                </div>


                <div
                    style="
                        width:100%;
                        overflow-x:auto;
                    "
                >

                    <table
                        class="diff-table"
                        style="
                            width:100%;
                            min-width:1000px;
                            table-layout:fixed;
                            border-collapse:collapse;
                        "
                    >

                        <thead>

                            <tr>

                                <th
                                    style="
                                        width:16%;
                                        padding:14px;
                                    "
                                >
                                    Location
                                </th>


                                <th
                                    style="
                                        width:28%;
                                        padding:14px;
                                    "
                                >
                                    Original Document
                                </th>


                                <th
                                    style="
                                        width:28%;
                                        padding:14px;
                                    "
                                >
                                    Modified Document
                                </th>


                                <th
                                    style="
                                        width:28%;
                                        padding:14px;
                                    "
                                >
                                    Difference
                                </th>

                            </tr>

                        </thead>


                        <tbody>

                            ${rows}

                        </tbody>

                    </table>

                </div>

            `;

        }


        // ---------------------------------------------------------
        // NO DIFFERENCES
        // ---------------------------------------------------------

        else {

            diffTableWrapper.innerHTML =
                "<div class='no-data-msg'>No differences detected.</div>";

        }


        // Render Changes Table Log
        renderChangesList();
    }


    // -------------------------------------------------------------
    // Changes List
    // -------------------------------------------------------------

    function renderChangesList() {

        const tbody =
            document.getElementById(
                'changes-table-body'
            );

        const noChangesMsg =
            document.getElementById(
                'no-changes-msg'
            );


        tbody.innerHTML = '';


        const selectedCat =
            filterCategory.value;

        const selectedSev =
            filterSeverity.value;


        const filtered =
            state.currentChanges.filter(
                c => {

                    const catMatch =
                        selectedCat === 'All' ||
                        c.category ===
                            selectedCat;

                    const sevMatch =
                        selectedSev === 'All' ||
                        c.severity ===
                            selectedSev;

                    return (
                        catMatch &&
                        sevMatch
                    );
                }
            );


        if (filtered.length === 0) {

            noChangesMsg.classList.remove(
                'hidden'
            );

            return;
        }


        noChangesMsg.classList.add(
            'hidden'
        );


        filtered.forEach(c => {

            const tr =
                document.createElement(
                    'tr'
                );


            tr.innerHTML = `

                <td>

                    <span
                        class="badge-category cat-${c.category}"
                    >
                        ${c.category}
                    </span>

                </td>


                <td>

                    <span
                        class="badge-severity sev-${c.severity}"
                    >
                        ${c.severity}
                    </span>

                </td>


                <td
                    style="font-weight:600;"
                >
                    ${c.section ||
                        c.location ||
                        'General'}
                </td>


                <td
                    style="max-width:350px;"
                >
                    ${escapeHtml(
                        c.description
                    )}
                </td>


                <td>

                    <div
                        class="cell-code"
                    >
                        ${escapeHtml(
                            c.originalText ??
                            c.original ??
                            '-'
                        )}
                    </div>

                </td>


                <td>

                    <div
                        class="cell-code"
                        style="
                            color:var(--color-success);
                        "
                    >
                        ${escapeHtml(
                            c.modifiedText ??
                            c.modified ??
                            '-'
                        )}
                    </div>

                </td>

            `;


            tbody.appendChild(tr);
        });
    }


    // -------------------------------------------------------------
    // Filter Event Listeners
    // -------------------------------------------------------------

    filterCategory.addEventListener(
        'change',
        renderChangesList
    );

    filterSeverity.addEventListener(
        'change',
        renderChangesList
    );


    // Click Statistics Card to filter
    // by that Category
    document
        .querySelectorAll(
            '.stat-card'
        )
        .forEach(card => {

            card.addEventListener(
                'click',
                () => {

                    const category =
                        card.getAttribute(
                            'data-category'
                        );


                    filterCategory.value =
                        category;


                    // Switch to list tab
                    document
                        .querySelector(
                            '[data-tab="tab-changes"]'
                        )
                        .click();


                    renderChangesList();
                }
            );

        });


    // -------------------------------------------------------------
    // Report Downloads
    // -------------------------------------------------------------

    downloadDocxBtn.addEventListener(
        'click',
        () => {

            if (
                !state.currentComparisonId
            ) {
                return;
            }


            window.location.href =
                `/api/report/${state.currentComparisonId}/docx`;
        }
    );


    downloadPdfBtn.addEventListener(
        'click',
        () => {

            if (
                !state.currentComparisonId
            ) {
                return;
            }


            window.location.href =
                `/api/report/${state.currentComparisonId}/pdf`;
        }
    );


    // -------------------------------------------------------------
    // History Drawer Logic
    // -------------------------------------------------------------

    toggleHistoryBtn.addEventListener(
        'click',
        () => {
            openHistoryDrawer();
        }
    );


    closeHistoryBtn.addEventListener(
        'click',
        () => {
            closeHistoryDrawer();
        }
    );


    async function openHistoryDrawer() {

        historyDrawer.classList.add(
            'open'
        );

        state.historyOpen = true;

        await loadHistory();
    }


    function closeHistoryDrawer() {

        historyDrawer.classList.remove(
            'open'
        );

        state.historyOpen = false;
    }


    async function loadHistory() {

        try {

            const response =
                await fetch(
                    '/api/history'
                );


            if (!response.ok) {

                throw new Error(
                    "Failed to load history."
                );
            }


            const historyData =
                await response.json();


            renderHistory(
                historyData
            );

        } catch (err) {

            console.error(err);

        }
    }


    function renderHistory(history) {

        historyList.innerHTML = '';


        if (history.length === 0) {

            historyList.innerHTML =
                '<div class="no-history-msg">No historical runs saved.</div>';

            return;
        }


        history.forEach(item => {

            const card =
                document.createElement(
                    'div'
                );


            card.className =
                'history-card';


            card.setAttribute(
                'data-id',
                item.id
            );


            const totalChanges =
                item.summary?.totalChanges ||
                0;


            const dateStr =
                item.comparison_date ||
                '';


            card.innerHTML = `

                <div
                    class="history-card-header"
                >

                    <div
                        class="history-title"
                    >
                        ${escapeHtml(
                            item.file_a_name
                        )}
                        ↔
                        ${escapeHtml(
                            item.file_b_name
                        )}
                    </div>

                </div>


                <span
                    class="history-date"
                >
                    ${dateStr}
                </span>


                <div
                    class="history-stats"
                >

                    <span
                        class="history-stat-tag"
                        style="
                            color:var(--color-primary);
                        "
                    >
                        ${totalChanges}
                        changes
                    </span>


                    <span
                        class="history-stat-tag"
                    >
                        ${item.summary?.severityHigh || 0}
                        Critical
                    </span>

                </div>


                <button
                    class="history-delete-btn"
                    title="Delete run"
                >

                    <svg
                        viewBox="0 0 24 24"
                        width="14"
                        height="14"
                        stroke="currentColor"
                        stroke-width="2"
                        fill="none"
                    >

                        <polyline
                            points="3 6 5 6 21 6"
                        ></polyline>

                        <path
                            d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                        ></path>

                    </svg>

                </button>

            `;


            // Card click to load
            card.addEventListener(
                'click',
                (e) => {

                    if (
                        e.target.closest(
                            '.history-delete-btn'
                        )
                    ) {
                        return;
                    }


                    loadHistoryItem(
                        item.id
                    );
                }
            );


            // Delete click
            card
                .querySelector(
                    '.history-delete-btn'
                )
                .addEventListener(
                    'click',
                    (e) => {

                        e.stopPropagation();

                        deleteHistoryItem(
                            item.id
                        );
                    }
                );


            historyList.appendChild(
                card
            );
        });
    }


    async function loadHistoryItem(id) {

        setLoadingState(
            true,
            "Retrieving logs..."
        );


        closeHistoryDrawer();


        try {

            const response =
                await fetch(
                    `/api/history/${id}`
                );


            if (!response.ok) {

                throw new Error(
                    "Failed to load historical comparison details."
                );
            }


            const data =
                await response.json();


            // The table / payload matches
            // the comparison shape
            renderComparison({

                id:
                    data.id,

                file_a_name:
                    data.file_a_name,

                file_b_name:
                    data.file_b_name,

                summary:
                    data.summary,

                changes:
                    data.results?.changes ||
                    [],

                diff_html:
                    data.results?.diff_html ||
                    ""

            });


            showToast(
                "Comparison history loaded.",
                "success"
            );


            switchPanel(
                'results-panel'
            );


        } catch (err) {

            showToast(
                err.message,
                "error"
            );

        } finally {

            setLoadingState(
                false
            );
        }
    }


    async function deleteHistoryItem(id) {

        if (
            !confirm(
                "Are you sure you want to delete this comparison history?"
            )
        ) {
            return;
        }


        try {

            const response =
                await fetch(
                    `/api/history/${id}`,
                    {
                        method: 'DELETE'
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Failed to delete record."
                );
            }


            showToast(
                "Comparison deleted.",
                "success"
            );


            // If the deleted item is currently viewed,
            // go back to upload
            if (
                state.currentComparisonId ===
                id
            ) {

                switchPanel(
                    'upload-panel'
                );
            }


            loadHistory();


        } catch (err) {

            showToast(
                err.message,
                "error"
            );
        }
    }


    // -------------------------------------------------------------
    // Utility Helpers
    // -------------------------------------------------------------

    function setLoadingState(
        isLoading,
        text = "Processing..."
    ) {

        if (isLoading) {

            loadingStatus.textContent =
                text;

            loadingOverlay.classList.add(
                'active'
            );

        } else {

            loadingOverlay.classList.remove(
                'active'
            );
        }
    }


    function switchPanel(panelId) {

        document
            .querySelectorAll(
                '.panel'
            )
            .forEach(p => {

                p.classList.remove(
                    'active'
                );

            });


        document
            .getElementById(
                panelId
            )
            .classList.add(
                'active'
            );
    }


    function escapeHtml(text) {

        if (!text) {
            return '';
        }


        const map = {

            '&': '&amp;',

            '<': '&lt;',

            '>': '&gt;',

            '"': '&quot;',

            "'": '&#039;'

        };


        return text.replace(
            /[&<>"']/g,
            function(m) {
                return map[m];
            }
        );
    }


    // Load history runs in background on load
    loadHistory();

});