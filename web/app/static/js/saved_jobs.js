/**
 * saved_jobs.js - Application Tracker & Sankey Conversion Chart Logic
 */

let sankeyChart = null;
let currentSankeyData = [];
let toastInstance = null;
let notesModalInstance = null;

// Read Initial Sankey Data from JSON script tag
const rawDataEl = document.getElementById('sankey-raw-data');
if (rawDataEl) {
    try {
        currentSankeyData = JSON.parse(rawDataEl.textContent.trim());
    } catch (e) {
        currentSankeyData = [];
    }
}

let currentFilter = 'All';

function applyTableFilter(category) {
    currentFilter = category;

    // Update active tab buttons
    const filterBtns = document.querySelectorAll('#stageFilterGroup .btn-stage-filter');
    filterBtns.forEach(btn => {
        if (btn.getAttribute('data-filter') === category) {
            btn.classList.add('btn-stage-active');
        } else {
            btn.classList.remove('btn-stage-active');
        }
    });

    // Filter table rows
    const rows = document.querySelectorAll('.saved-job-row');
    let visibleCount = 0;

    rows.forEach(row => {
        const rowCategory = row.getAttribute('data-filter-category') || '';
        const shouldShow = (category === 'All' || rowCategory === category);

        if (shouldShow) {
            row.style.display = '';
            row.classList.remove('row-fade-in');
            void row.offsetWidth; // trigger reflow for smooth animation
            row.classList.add('row-fade-in');
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Update displayed count text
    const countDisplay = document.getElementById('displayedJobCount');
    if (countDisplay) {
        countDisplay.textContent = `${visibleCount} lowongan ditampilkan`;
    }

    // Toggle empty state row
    const noResultsRow = document.getElementById('noFilterResultsRow');
    if (noResultsRow) {
        noResultsRow.style.display = (visibleCount === 0) ? '' : 'none';
    }

    // Update URL query string without reloading page
    const newUrl = category === 'All' 
        ? window.location.pathname 
        : `${window.location.pathname}?status=${encodeURIComponent(category)}`;
    window.history.replaceState(null, '', newUrl);
}

function initSavedJobs() {
    drawSankeyChart();
    // Safety delay to capture container width after CSS layout
    setTimeout(drawSankeyChart, 50);

    // Toast setup
    const toastEl = document.getElementById('trackerToast');
    if (toastEl && typeof bootstrap !== 'undefined') {
        toastInstance = new bootstrap.Toast(toastEl, { delay: 2500 });
    }

    // Notes modal setup (Moved to document.body to prevent stacking context backdrop trap)
    const modalEl = document.getElementById('notesModal');
    if (modalEl) {
        if (modalEl.parentNode !== document.body) {
            document.body.appendChild(modalEl);
        }
        if (typeof bootstrap !== 'undefined') {
            notesModalInstance = new bootstrap.Modal(modalEl, {
                backdrop: true,
                keyboard: true,
                focus: true
            });
        }
        // Fail-safe manual close triggers
        modalEl.querySelectorAll('[data-bs-dismiss="modal"]').forEach(btn => {
            btn.addEventListener('click', () => {
                if (notesModalInstance) {
                    notesModalInstance.hide();
                }
            });
        });
    }

    // Stage Filter Buttons Event Listener (Smooth in-memory filtering)
    const filterGroup = document.getElementById('stageFilterGroup');
    if (filterGroup) {
        filterGroup.addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-filter]');
            if (btn) {
                const filter = btn.getAttribute('data-filter');
                applyTableFilter(filter);
            }
        });
    }

    // Check URL params on initial load
    const urlParams = new URLSearchParams(window.location.search);
    const initialStatus = urlParams.get('status');
    if (initialStatus && initialStatus !== 'All') {
        applyTableFilter(initialStatus);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSavedJobs);
} else {
    initSavedJobs();
}
window.addEventListener('load', () => {
    setTimeout(drawSankeyChart, 50);
});

    // Event Delegation for Stage and Test Dropdown Changes
    document.addEventListener('change', (e) => {
        const stageSelect = e.target.closest('.stage-dropdown');
        if (stageSelect) {
            const jobId = stageSelect.getAttribute('data-job-id');
            const newStage = stageSelect.value;
            if (jobId && newStage) {
                updateJobStage(jobId, newStage);
            }
            return;
        }

        const testSelect = e.target.closest('.test-dropdown');
        if (testSelect) {
            const jobId = testSelect.getAttribute('data-job-id');
            const newTest = testSelect.value;
            if (jobId) {
                updateJobTestType(jobId, newTest);
            }
            return;
        }
    });

    // Event Delegation for Notes Modal Triggers
    document.addEventListener('click', (e) => {
        const notesTrigger = e.target.closest('.trigger-notes-modal');
        if (notesTrigger) {
            const jobId = notesTrigger.getAttribute('data-job-id');
            const jobTitle = notesTrigger.getAttribute('data-job-title') || 'Lowongan';
            const company = notesTrigger.getAttribute('data-company') || '';
            openNotesModal(jobId, jobTitle, company);
            return;
        }

        const deleteBtn = e.target.closest('.btn-delete-saved-job');
        if (deleteBtn) {
            const jobId = deleteBtn.getAttribute('data-job-id');
            const jobTitle = deleteBtn.getAttribute('data-job-title') || 'Lowongan';
            deleteSavedJob(jobId, jobTitle);
            return;
        }
    });

    // Redraw Sankey on window resize with debouncing & ResizeObserver
    let sankeyResizeTimer = null;
    function triggerSankeyResize() {
        clearTimeout(sankeyResizeTimer);
        sankeyResizeTimer = setTimeout(() => {
            if (currentSankeyData && currentSankeyData.length > 0) {
                drawSankeyChart(false);
            }
        }, 100);
    }

    window.addEventListener('resize', triggerSankeyResize);

    if (typeof ResizeObserver !== 'undefined') {
        const wrapperEl = document.getElementById('sankeyWrapper');
        if (wrapperEl) {
            const ro = new ResizeObserver(() => triggerSankeyResize());
            ro.observe(wrapperEl);
        }
    }

    // Redraw Sankey on theme change
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            setTimeout(() => drawSankeyChart(false), 100);
        });
    }

/**
 * Render Sankey Funnel Chart using Native Vector SVG
 * Deterministic left-to-right recruitment flow:
 * Col 0: Semua Loker Tersimpan
 * Col 1: Belum Apply (stops at Col 1!) & Applied
 * Col 2: Interview HR
 * Col 3: Interview User 1
 * Col 4: Interview User 2
 * Col 5: Tahap Offering
 * Col 6: Diterima, Ghosted, Ditolak (Terminal Sinks)
 */
function drawSankeyChart(isLiveUpdate = false) {
    const container = document.getElementById('sankey_chart');
    if (!container) return;

    // Visual feedback on Live Funnel badge & wrapper
    const liveBadge = document.getElementById('sankeyLiveBadge');
    const wrapper = document.getElementById('sankeyWrapper');
    if (isLiveUpdate) {
        if (liveBadge) {
            liveBadge.innerHTML = '<i class="bi bi-arrow-repeat me-1 spin-pulse"></i> Mengupdate Funnel...';
            liveBadge.style.borderColor = 'rgba(52, 211, 153, 0.6)';
            liveBadge.style.color = '#34d399';
        }
        if (wrapper) {
            wrapper.classList.remove('sankey-live-updated');
            void wrapper.offsetWidth;
            wrapper.classList.add('sankey-live-updated');
        }
    }

    container.innerHTML = '';
    if (!currentSankeyData || currentSankeyData.length === 0) {
        container.innerHTML = '<div class="text-center py-5"><i class="bi bi-diagram-3 fs-1 text-secondary mb-2 d-block"></i><div class="text-white fw-bold mb-1">Belum Ada Cukup Data Konversi</div><p class="text-secondary small mb-3">Simpan lowongan dan update status tahapan untuk melihat diagram alur lamaran.</p><a href="/jobs" class="btn btn-sm btn-studio-outline">Cari Lowongan Sekarang</a></div>';
        return;
    }

    const containerRect = container.getBoundingClientRect();
    const availableWidth = containerRect.width || container.clientWidth || 920;
    const width = Math.max(Math.floor(availableWidth), 780);
    const height = 370;
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';

    function getNodeColor(name) {
        if (name.includes('Ghosted')) return '#94a3b8';
        if (name.includes('Ditolak')) return '#f87171';
        if (name.includes('Diterima')) return '#10b981';
        if (name.includes('Semua Loker')) return '#0284c7';
        if (name.includes('Belum Apply') || name.includes('Wishlist')) return '#f59e0b';
        if (name.includes('Applied')) return '#38bdf8';
        if (name.includes('HR')) return '#f97316';
        if (name.includes('User 1')) return '#8b5cf6';
        if (name.includes('User 2')) return '#a855f7';
        if (name.includes('Offering')) return '#14b8a6';
        return '#64748b';
    }

    function getNodeAccentColor(name) {
        if (name.includes('Semua Loker') || name.includes('Applied')) return '#0284c7';
        if (name.includes('HR')) return '#ea580c';
        if (name.includes('User 1')) return '#7c3aed';
        if (name.includes('User 2')) return '#9333ea';
        if (name.includes('Offering')) return '#0d9488';
        if (name.includes('Diterima')) return '#059669';
        if (name.includes('Ditolak')) return '#dc2626';
        if (name.includes('Ghosted')) return '#64748b';
        if (name.includes('Belum Apply')) return '#d97706';
        return '#475569';
    }

    function getNodeColumn(name) {
        if (name === "Semua Loker Tersimpan") return 0;
        if (name === "Belum Apply" || name === "Applied") return 1;
        if (name.includes("Interview HR") || name.endsWith("(CV)")) return 2;
        if (name.includes("Interview User 1") || name.endsWith("(HR)")) return 3;
        if (name.includes("Interview User 2") || name.endsWith("(User 1)")) return 4;
        if (name.includes("Tahap Offering") || name.includes("Offering") || name.endsWith("(User 2)")) return 5;
        if (name.includes("Diterima") || name.endsWith("(Offer)")) return 6;
        return 1;
    }

    function getNodePriority(name) {
        if (name === "Semua Loker Tersimpan") return 0;
        if (name === "Applied") return 0;
        if (name.startsWith("Interview")) return 0;
        if (name.includes("Offering")) return 0;
        if (name.includes("Diterima")) return 0;
        if (name.includes("Belum Apply")) return 1;
        if (name.includes("Ghosted")) return 2;
        if (name.includes("Ditolak")) return 3;
        return 5;
    }

    // Calculate node totals from links
    const nodeTotals = {};
    currentSankeyData.forEach(([src, tgt, val]) => {
        nodeTotals[src] = nodeTotals[src] || { in: 0, out: 0 };
        nodeTotals[tgt] = nodeTotals[tgt] || { in: 0, out: 0 };
        nodeTotals[src].out += val;
        nodeTotals[tgt].in += val;
    });

    // Group nodes by column
    const columns = [[], [], [], [], [], [], []];
    const uniqueNodeNames = Object.keys(nodeTotals);

    uniqueNodeNames.forEach(name => {
        const colIdx = getNodeColumn(name);
        const val = Math.max(nodeTotals[name].in, nodeTotals[name].out);
        columns[colIdx].push({ name, value: val, in: nodeTotals[name].in, out: nodeTotals[name].out });
    });

    // Sort nodes in each column: Positive progression at top, drop-offs at bottom
    columns.forEach(colNodes => {
        colNodes.sort((a, b) => getNodePriority(a.name) - getNodePriority(b.name));
    });

    // Layout coordinates
    const padX = 35;
    const padY = 22;
    const chartHeight = height - 55; // reserve bottom space for timeline
    const nodeWidth = 14;
    const colSpacing = (width - padX * 2 - nodeWidth) / 6;

    const nodeCoords = {};
    columns.forEach((colNodes, colIdx) => {
        if (colNodes.length === 0) return;
        const colX = padX + colIdx * colSpacing;
        const totalVal = colNodes.reduce((sum, n) => sum + n.value, 0);

        const totalGap = (colNodes.length - 1) * 16;
        const maxH = chartHeight - padY * 2 - totalGap;
        const scaleY = Math.min(maxH / Math.max(totalVal, 1), 24);

        let currY = padY + 8; // align progression stream to upper boundary
        colNodes.forEach(node => {
            const h = Math.max(node.value * scaleY, 18);
            nodeCoords[node.name] = {
                x: colX,
                y: currY,
                width: nodeWidth,
                height: h,
                value: node.value,
                sourceOffset: 0,
                targetOffset: 0,
                colIdx: colIdx
            };
            currY += h + (getNodePriority(node.name) > 0 ? 14 : 20);
        });
    });

    // Create SVG container
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", "100%");
    svg.setAttribute("height", height);
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    svg.style.display = "block";
    svg.style.maxWidth = "100%";
    svg.style.overflow = "visible";

    // Defs for smooth gradients and arrow markers
    const defs = document.createElementNS(svgNS, "defs");
    svg.appendChild(defs);

    // Timeline arrow marker
    const marker = document.createElementNS(svgNS, "marker");
    marker.setAttribute("id", "timelineArrow");
    marker.setAttribute("viewBox", "0 0 10 10");
    marker.setAttribute("refX", "5");
    marker.setAttribute("refY", "5");
    marker.setAttribute("markerWidth", "6");
    marker.setAttribute("markerHeight", "6");
    marker.setAttribute("orient", "auto-start-reverse");
    const markerPath = document.createElementNS(svgNS, "path");
    markerPath.setAttribute("d", "M 0 1.5 L 8 5 L 0 8.5 z");
    markerPath.setAttribute("fill", isDark ? "#64748b" : "#94a3b8");
    marker.appendChild(markerPath);
    defs.appendChild(marker);

    // Group for links
    const linkGroup = document.createElementNS(svgNS, "g");
    svg.appendChild(linkGroup);

    // Sort links so top flows leave from the top and bottom flows leave from the bottom
    const sortedLinks = [...currentSankeyData].sort((a, b) => {
        const srcColA = getNodeColumn(a[0]);
        const srcColB = getNodeColumn(b[0]);
        if (srcColA !== srcColB) return srcColA - srcColB;

        const srcNodeA = nodeCoords[a[0]];
        const srcNodeB = nodeCoords[b[0]];
        if (srcNodeA && srcNodeB && srcNodeA.y !== srcNodeB.y) {
            return srcNodeA.y - srcNodeB.y;
        }

        const tgtNodeA = nodeCoords[a[1]];
        const tgtNodeB = nodeCoords[b[1]];
        if (tgtNodeA && tgtNodeB) {
            return tgtNodeA.y - tgtNodeB.y;
        }
        return 0;
    });

    // Draw Links
    sortedLinks.forEach(([srcName, tgtName, val], i) => {
        const src = nodeCoords[srcName];
        const tgt = nodeCoords[tgtName];
        if (!src || !tgt) return;

        const srcH = (val / src.value) * src.height;
        const tgtH = (val / tgt.value) * tgt.height;

        const sy = src.y + src.sourceOffset;
        const ty = tgt.y + tgt.targetOffset;

        src.sourceOffset += srcH;
        tgt.targetOffset += tgtH;

        const sx = src.x + src.width;
        const tx = tgt.x;
        const mx = (sx + tx) / 2;

        const gradId = `linkGrad_${i}_${Date.now()}`;
        const grad = document.createElementNS(svgNS, "linearGradient");
        grad.setAttribute("id", gradId);
        grad.setAttribute("gradientUnits", "userSpaceOnUse");
        grad.setAttribute("x1", sx);
        grad.setAttribute("x2", tx);

        const stop1 = document.createElementNS(svgNS, "stop");
        stop1.setAttribute("offset", "0%");
        stop1.setAttribute("stop-color", getNodeColor(srcName));
        stop1.setAttribute("stop-opacity", isDark ? "0.60" : "0.40");

        const stop2 = document.createElementNS(svgNS, "stop");
        stop2.setAttribute("offset", "100%");
        stop2.setAttribute("stop-color", getNodeColor(tgtName));
        stop2.setAttribute("stop-opacity", isDark ? "0.60" : "0.40");

        grad.appendChild(stop1);
        grad.appendChild(stop2);
        defs.appendChild(grad);

        const path = document.createElementNS(svgNS, "path");
        const d = `
            M ${sx} ${sy}
            C ${mx} ${sy}, ${mx} ${ty}, ${tx} ${ty}
            L ${tx} ${ty + tgtH}
            C ${mx} ${ty + tgtH}, ${mx} ${sy + srcH}, ${sx} ${sy + srcH}
            Z
        `;
        path.setAttribute("d", d);
        path.setAttribute("fill", `url(#${gradId})`);
        path.classList.add("sankey-link-ribbon");

        // Staggered animated flow entrance
        const srcCol = getNodeColumn(srcName);
        const delayMs = srcCol * 60 + (i % 4) * 15;
        const targetOpacity = isDark ? 0.75 : 0.65;
        path.style.opacity = targetOpacity;
        path.style.cursor = "pointer";

        if (isLiveUpdate && typeof path.animate === 'function') {
            path.animate([
                { opacity: 0.15, transform: 'scaleX(0.75)' },
                { opacity: targetOpacity, transform: 'scaleX(1)' }
            ], {
                duration: 420,
                delay: delayMs,
                easing: 'cubic-bezier(0.16, 1, 0.3, 1)',
                fill: 'backwards'
            });
        }

        const title = document.createElementNS(svgNS, "title");
        title.textContent = `${srcName} → ${tgtName}: ${val} lowongan`;
        path.appendChild(title);

        path.addEventListener("mouseenter", () => {
            path.style.opacity = "0.98";
            path.style.filter = "drop-shadow(0 0 6px rgba(255, 110, 64, 0.45))";
        });
        path.addEventListener("mouseleave", () => {
            path.style.opacity = isDark ? "0.75" : "0.65";
            path.style.filter = "none";
        });

        linkGroup.appendChild(path);
    });

    // Group for nodes
    const nodeGroup = document.createElementNS(svgNS, "g");
    svg.appendChild(nodeGroup);

    uniqueNodeNames.forEach(name => {
        const node = nodeCoords[name];
        if (!node) return;

        const g = document.createElementNS(svgNS, "g");

        // Base Rect with animated pop
        const rect = document.createElementNS(svgNS, "rect");
        rect.setAttribute("x", node.x);
        rect.setAttribute("y", node.y);
        rect.setAttribute("width", node.width);
        rect.setAttribute("height", node.height);
        rect.setAttribute("rx", "2.5");
        rect.setAttribute("ry", "2.5");
        rect.setAttribute("fill", getNodeColor(name));
        rect.classList.add("sankey-node-rect");

        const nodeDelay = node.colIdx * 60 + 25;
        rect.style.opacity = "1";
        rect.style.cursor = "pointer";
        rect.style.filter = "drop-shadow(0 2px 4px rgba(0,0,0,0.18))";

        // Vertical Accent Bar
        const accentBar = document.createElementNS(svgNS, "rect");
        accentBar.setAttribute("x", node.x);
        accentBar.setAttribute("y", node.y);
        accentBar.setAttribute("width", "3.5");
        accentBar.setAttribute("height", node.height);
        accentBar.setAttribute("rx", "1.5");
        accentBar.setAttribute("fill", getNodeAccentColor(name));
        accentBar.style.opacity = "1";

        const title = document.createElementNS(svgNS, "title");
        title.textContent = `${name}: ${node.value} lowongan`;
        rect.appendChild(title);
        g.appendChild(rect);
        g.appendChild(accentBar);

        // Label text with slide-in animation
        const text = document.createElementNS(svgNS, "text");
        const isRightSink = node.colIdx >= 5 || node.x > width - 130;
        text.setAttribute("x", isRightSink ? node.x - 8 : node.x + node.width + 8);
        text.setAttribute("y", node.y + node.height / 2);
        text.setAttribute("dy", "0.35em");
        text.setAttribute("text-anchor", isRightSink ? "end" : "start");
        text.setAttribute("font-size", "11px");
        text.setAttribute("font-family", "Plus Jakarta Sans, sans-serif");
        text.setAttribute("font-weight", "600");
        text.setAttribute("fill", isDark ? "#f1f5f9" : "#0f172a");
        text.style.pointerEvents = "none";
        text.style.opacity = "1";
        text.textContent = `${name}: ${node.value}`;

        if (isLiveUpdate && typeof rect.animate === 'function') {
            rect.animate([
                { opacity: 0.2, transform: 'scale(0.5)' },
                { opacity: 1, transform: 'scale(1)' }
            ], {
                duration: 380,
                delay: nodeDelay,
                easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
                fill: 'backwards'
            });
            accentBar.animate([
                { opacity: 0.2, transform: 'scaleY(0.5)' },
                { opacity: 1, transform: 'scaleY(1)' }
            ], {
                duration: 380,
                delay: nodeDelay,
                easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
                fill: 'backwards'
            });
            text.animate([
                { opacity: 0, transform: 'translateY(4px)' },
                { opacity: 1, transform: 'translateY(0)' }
            ], {
                duration: 320,
                delay: nodeDelay + 40,
                easing: 'ease-out',
                fill: 'backwards'
            });
        }

        g.appendChild(text);
        nodeGroup.appendChild(g);
    });

    // TIMELINE AXIS FOOTER (Inspired by reference "5 Weeks" axis)
    const timelineGroup = document.createElementNS(svgNS, "g");
    const timelineY = height - 16;

    const timelineLine = document.createElementNS(svgNS, "line");
    timelineLine.setAttribute("x1", padX);
    timelineLine.setAttribute("y1", timelineY);
    timelineLine.setAttribute("x2", width - padX);
    timelineLine.setAttribute("y2", timelineY);
    timelineLine.setAttribute("stroke", isDark ? "#334155" : "#cbd5e1");
    timelineLine.setAttribute("stroke-width", "1.5");
    timelineLine.setAttribute("marker-start", "url(#timelineArrow)");
    timelineLine.setAttribute("marker-end", "url(#timelineArrow)");
    timelineGroup.appendChild(timelineLine);

    // Timeline Phase Badges / Labels
    const phases = [
        { x: padX + colSpacing * 0.5, text: "Fase 1: Aplikasi & Screening", color: "#38bdf8" },
        { x: padX + colSpacing * 3.0, text: "Fase 2: Wawancara & Evaluasi Teknis", color: "#f97316" },
        { x: padX + colSpacing * 5.5, text: "Fase 3: Offering & Keputusan", color: "#10b981" }
    ];

    phases.forEach(p => {
        const pText = document.createElementNS(svgNS, "text");
        pText.setAttribute("x", p.x);
        pText.setAttribute("y", timelineY - 6);
        pText.setAttribute("text-anchor", "middle");
        pText.setAttribute("font-size", "10px");
        pText.setAttribute("font-family", "Plus Jakarta Sans, sans-serif");
        pText.setAttribute("font-weight", "700");
        pText.setAttribute("letter-spacing", "0.04em");
        pText.setAttribute("fill", p.color);
        pText.textContent = p.text.toUpperCase();
        timelineGroup.appendChild(pText);
    });

    svg.appendChild(timelineGroup);
    container.appendChild(svg);

    if (liveBadge && isLiveUpdate) {
        setTimeout(() => {
            liveBadge.innerHTML = '<i class="bi bi-check-circle-fill text-success me-1"></i> Funnel Terupdate';
            setTimeout(() => {
                liveBadge.innerHTML = '<i class="bi bi-broadcast text-success me-1"></i> Live Funnel';
                liveBadge.style.borderColor = '';
                liveBadge.style.color = '';
            }, 1800);
        }, 500);
    }
}

/**
 * Update Job Status (Saved, Applied, HR Interview, etc.)
 */
async function updateJobStage(jobId, newStage) {
    const selectEl = document.querySelector(`.stage-dropdown[data-job-id="${jobId}"]`);
    if (selectEl) {
        selectEl.disabled = true;
    }

    try {
        const res = await fetch('/api/saved-jobs/update-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: jobId, status: newStage })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast(`Status lowongan berhasil diubah ke: ${newStage}`);

            // Update dropdown color class while strictly preserving 'stage-dropdown'
            if (selectEl) {
                const classesToRemove = [];
                selectEl.classList.forEach(cls => {
                    if (cls.startsWith('stage-') && cls !== 'stage-dropdown') {
                        classesToRemove.push(cls);
                    }
                });
                classesToRemove.forEach(cls => selectEl.classList.remove(cls));
                const formattedClass = `stage-${newStage.toLowerCase().replace(/\s+/g, '-').replace(/[()]/g, '')}`;
                selectEl.classList.add(formattedClass);
            }

            // Update row data attributes and re-evaluate filter
            const row = document.getElementById(`jobRow-${jobId}`);
            if (row) {
                let newCat = 'Other';
                if (newStage === 'Wishlist') newCat = 'Wishlist';
                else if (['Applied', 'Interview HR', 'Interview User 1', 'Interview User 2', 'Offering'].includes(newStage)) newCat = 'Active';
                else if (newStage === 'Diterima') newCat = 'Success';
                else if (newStage.startsWith('Ghosted')) newCat = 'Ghosted';
                else if (newStage.startsWith('Ditolak')) newCat = 'Rejected';

                row.setAttribute('data-status', newStage);
                row.setAttribute('data-filter-category', newCat);

                if (currentFilter !== 'All' && newCat !== currentFilter) {
                    applyTableFilter(currentFilter);
                }
            }

            // Update Scorecards & Live Animated Sankey
            if (data.stats) {
                updateScorecards(data.stats.scorecards);
                const freshSankey = data.sankey_data || (data.stats && data.stats.sankey_data);
                if (freshSankey && Array.isArray(freshSankey)) {
                    currentSankeyData = freshSankey;
                    drawSankeyChart(true);
                }
            }
        } else {
            showToast(data.message || 'Gagal mengubah status', true);
        }
    } catch (err) {
        showToast('Terjadi kesalahan jaringan saat update status.', true);
    } finally {
        if (selectEl) {
            selectEl.disabled = false;
        }
    }
}

/**
 * Update Assessment / Test Type
 */
async function updateJobTestType(jobId, newTest) {
    const selectEl = document.querySelector(`.test-dropdown[data-job-id="${jobId}"]`);
    if (selectEl) {
        selectEl.disabled = true;
    }

    try {
        const res = await fetch('/api/saved-jobs/update-test-type', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: jobId, test_type: newTest })
        });
        const data = await res.json();

        if (data.status === 'success') {
            showToast(`Keterangan tes diupdate: ${newTest}`);

            // Update Scorecards (tests count)
            if (data.stats) {
                updateScorecards(data.stats.scorecards);
            }
        } else {
            showToast(data.message || 'Gagal mengubah jenis tes', true);
        }
    } catch (err) {
        showToast('Terjadi kesalahan jaringan saat update tes.', true);
    } finally {
        if (selectEl) {
            selectEl.disabled = false;
        }
    }
}

/**
 * Open Notes Modal
 */
function openNotesModal(jobId, jobTitle, companyName) {
    const modalEl = document.getElementById('notesModal');
    if (!modalEl) return;

    if (!notesModalInstance && typeof bootstrap !== 'undefined') {
        if (modalEl.parentNode !== document.body) {
            document.body.appendChild(modalEl);
        }
        notesModalInstance = new bootstrap.Modal(modalEl, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
    }

    const modalTitle = document.getElementById('notesModalTitle');
    const modalSubtitle = document.getElementById('notesModalSubtitle');
    const notesJobId = document.getElementById('notesJobId');
    const notesContent = document.getElementById('notesContent');

    if (notesJobId) notesJobId.value = jobId;
    if (modalTitle) modalTitle.textContent = `Catatan: ${jobTitle}`;
    if (modalSubtitle) modalSubtitle.textContent = companyName;

    // Get current preview text if exists
    const previewBox = document.getElementById(`notesPreview-${jobId}`);
    let existingText = '';
    if (previewBox) {
        existingText = previewBox.getAttribute('data-full-notes');
        if (existingText === null || existingText === undefined) {
            existingText = previewBox.innerText.trim();
        }
    }
    if (notesContent) {
        notesContent.value = existingText.startsWith('+ Tambah catatan') ? '' : existingText;
    }

    if (notesModalInstance) {
        notesModalInstance.show();
    }
}

/**
 * Save Notes via API
 */
async function saveNotes() {
    const jobId = document.getElementById('notesJobId').value;
    const notes = document.getElementById('notesContent').value.trim();
    const saveBtn = document.getElementById('saveNotesBtn');

    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Menyimpan...';
    }

    try {
        const res = await fetch('/api/saved-jobs/update-notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: jobId, notes: notes })
        });
        const data = await res.json();

        if (data.status === 'success') {
            const previewBox = document.getElementById(`notesPreview-${jobId}`);
            if (previewBox) {
                previewBox.setAttribute('data-full-notes', notes);
                if (notes) {
                    const truncated = notes.length > 50 ? notes.substring(0, 48) + '...' : notes;
                    previewBox.innerHTML = `
                        <span class="small text-secondary">${escapeHtml(truncated)}</span>
                        <i class="bi bi-pencil-square ms-1 text-warning" style="font-size: 0.8rem;"></i>
                    `;
                } else {
                    previewBox.innerHTML = `<span class="small text-muted fst-italic">+ Tambah catatan interview/persiapan...</span>`;
                }
            }
            if (notesModalInstance) notesModalInstance.hide();
            showToast('Catatan lamaran berhasil disimpan.');
        } else {
            showToast('Gagal menyimpan catatan.', true);
        }
    } catch (err) {
        showToast('Terjadi kesalahan jaringan.', true);
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Simpan Catatan';
        }
    }
}

/**
 * Delete Saved Job
 */
async function deleteSavedJob(jobId, jobTitle) {
    if (!confirm(`Hapus "${jobTitle}" dari daftar simpan?`)) return;

    try {
        const res = await fetch(`/api/saved-jobs/${jobId}`, {
            method: 'DELETE'
        });
        const data = await res.json();

        if (data.status === 'success') {
            const row = document.getElementById(`jobRow-${jobId}`);
            if (row) {
                row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                row.style.opacity = '0';
                row.style.transform = 'translateX(20px)';
                setTimeout(() => {
                    row.remove();
                    applyTableFilter(currentFilter);
                }, 300);
            }

            if (data.stats) {
                updateScorecards(data.stats.scorecards);
                const freshSankey = data.sankey_data || data.stats.sankey_data;
                if (freshSankey) {
                    currentSankeyData = freshSankey;
                    drawSankeyChart(true);
                }
            }
            showToast('Lowongan dihapus dari daftar simpan.');
        } else {
            showToast('Gagal menghapus lowongan.', true);
        }
    } catch (err) {
        showToast('Terjadi kesalahan jaringan.', true);
    }
}

/**
 * Update Scorecard DOM elements and Filter Counters
 */
function updateScorecards(scorecards) {
    if (!scorecards) return;
    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setVal('statTotal', scorecards.total_saved);
    setVal('statApplied', scorecards.applied);
    setVal('statInterviews', scorecards.interviews);
    setVal('statOffering', (scorecards.offering || 0) + (scorecards.accepted || 0));
    setVal('statGhosted', scorecards.ghosted);
    setVal('statRejected', scorecards.rejected);
    setVal('statRate', `${scorecards.response_rate}%`);

    // Update filter badge counters
    const activeCount = Math.max(0, (scorecards.applied || 0) - (scorecards.ghosted || 0) - (scorecards.rejected || 0) - (scorecards.accepted || 0));
    const setFilterCount = (cls, val) => {
        const el = document.querySelector(cls);
        if (el) el.textContent = val;
    };
    setFilterCount('.filter-count-all', scorecards.total_saved);
    setFilterCount('.filter-count-wishlist', scorecards.wishlist);
    setFilterCount('.filter-count-active', activeCount);
    setFilterCount('.filter-count-success', scorecards.accepted);
    setFilterCount('.filter-count-ghosted', scorecards.ghosted);
    setFilterCount('.filter-count-rejected', scorecards.rejected);
}

/**
 * Toast Helper
 */
function showToast(message, isError = false) {
    const msgEl = document.getElementById('toastMessage');
    const toastEl = document.getElementById('trackerToast');
    if (!msgEl || !toastEl) return;

    msgEl.textContent = message;
    const icon = toastEl.querySelector('i');
    if (icon) {
        if (isError) {
            icon.className = 'bi bi-exclamation-circle-fill text-danger fs-5';
        } else {
            icon.className = 'bi bi-check-circle-fill text-success fs-5';
        }
    }

    if (toastInstance) {
        toastInstance.show();
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
