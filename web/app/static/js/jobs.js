/**
 * TalentLake - Live Job Explorer JavaScript
 * Features:
 * - Dynamic column sorting (Text, Numeric, Date) with direction toggles & icons
 * - Client-side pagination (15 jobs/page) with smart navigation & counter
 * - All Skills Modal dialog populator
 */

let allJobRows = [];
let currentPage = 1;
const pageSize = 15;
let skillsModalInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initJobExplorer();
});

/**
 * Main initialization
 */
function initJobExplorer() {
    const tbody = document.getElementById('jobsTableBody');
    if (tbody) {
        allJobRows = Array.from(tbody.querySelectorAll('tr.job-row'));
    }

    initTableSorting();
    initPagination();
    initSkillsModal();
    initFilterListeners();
}

/**
 * Filter change event listeners for instant form auto-submission
 */
function initFilterListeners() {
    ['filterRole', 'filterPlatform', 'filterWorkArrangement', 'filterEmploymentType', 'filterExpTier'].forEach(id => {
        const select = document.getElementById(id);
        if (select) {
            select.addEventListener('change', () => {
                const form = document.getElementById('jobFilterForm');
                if (form) form.submit();
            });
        }
    });
}

/**
 * 1. Initialize Clickable Column Sorting for Job Explorer Table
 */
function initTableSorting() {
    const table = document.querySelector('.table-custom');
    if (!table) return;

    const headers = table.querySelectorAll('th.sortable-th');
    const tbody = document.getElementById('jobsTableBody');
    if (!tbody || !headers.length) return;

    let currentSortCol = null;
    let currentSortDir = 'asc';

    headers.forEach(th => {
        th.addEventListener('click', () => {
            const colIndex = parseInt(th.getAttribute('data-col'), 10);
            const sortType = th.getAttribute('data-sort-type') || 'text';

            // Determine direction
            if (currentSortCol === colIndex) {
                currentSortDir = currentSortDir === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortCol = colIndex;
                // For dates & salary, default first click to DESC (latest / highest first)
                currentSortDir = (sortType === 'date' || sortType === 'num') ? 'desc' : 'asc';
            }

            // Update Header UI & Icons
            headers.forEach(header => {
                header.classList.remove('sorted-asc', 'sorted-desc');
                const icon = header.querySelector('.sort-icon');
                if (icon) {
                    icon.className = 'bi bi-arrow-down-up sort-icon';
                }
            });

            th.classList.add(currentSortDir === 'asc' ? 'sorted-asc' : 'sorted-desc');
            const activeIcon = th.querySelector('.sort-icon');
            if (activeIcon) {
                activeIcon.className = currentSortDir === 'asc' 
                    ? 'bi bi-sort-up sort-icon' 
                    : 'bi bi-sort-down sort-icon';
            }

            // Perform sorting on rows
            if (!allJobRows.length) return;

            allJobRows.sort((rowA, rowB) => {
                const cellA = rowA.children[colIndex];
                const cellB = rowB.children[colIndex];
                if (!cellA || !cellB) return 0;

                let valA = cellA.getAttribute('data-sort-val');
                let valB = cellB.getAttribute('data-sort-val');

                if (valA === null || valA === undefined) valA = cellA.innerText.trim();
                if (valB === null || valB === undefined) valB = cellB.innerText.trim();

                let comparison = 0;
                if (sortType === 'num') {
                    const numA = parseFloat(valA) || 0;
                    const numB = parseFloat(valB) || 0;
                    comparison = numA - numB;
                } else if (sortType === 'date') {
                    const timeA = valA ? new Date(valA).getTime() : 0;
                    const timeB = valB ? new Date(valB).getTime() : 0;
                    comparison = timeA - timeB;
                } else {
                    comparison = valA.localeCompare(valB, undefined, { sensitivity: 'base' });
                }

                return currentSortDir === 'asc' ? comparison : -comparison;
            });

            // Re-append sorted rows to tbody
            const fragment = document.createDocumentFragment();
            allJobRows.forEach(row => fragment.appendChild(row));
            tbody.appendChild(fragment);

            // Reset to page 1 after sorting
            goToPage(1);
        });
    });
}

/**
 * 2. Client-side Pagination Logic
 */
function initPagination() {
    goToPage(1);
}

function goToPage(page) {
    if (!allJobRows.length) {
        updatePaginationInfo(0, 0, 0);
        renderPaginationButtons(1, 1);
        return;
    }

    const totalPages = Math.ceil(allJobRows.length / pageSize);
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    currentPage = page;

    const startIdx = (currentPage - 1) * pageSize;
    const endIdx = Math.min(startIdx + pageSize, allJobRows.length);

    // Show/Hide rows
    allJobRows.forEach((row, idx) => {
        if (idx >= startIdx && idx < endIdx) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });

    updatePaginationInfo(startIdx + 1, endIdx, allJobRows.length);
    renderPaginationButtons(currentPage, totalPages);
}

function updatePaginationInfo(start, end, total) {
    const pageStartEl = document.getElementById('pageStart');
    const pageEndEl = document.getElementById('pageEnd');
    const pageTotalEl = document.getElementById('pageTotal');

    if (pageStartEl) pageStartEl.textContent = total > 0 ? start : 0;
    if (pageEndEl) pageEndEl.textContent = end;
    if (pageTotalEl) pageTotalEl.textContent = total;
}

function renderPaginationButtons(current, total) {
    const container = document.getElementById('paginationControls');
    if (!container) return;
    container.innerHTML = '';

    if (total <= 1) return;

    // Previous Button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${current === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<button class="page-link" aria-label="Sebelumnya"><i class="bi bi-chevron-left"></i></button>`;
    if (current > 1) {
        prevLi.querySelector('button').addEventListener('click', () => {
            goToPage(current - 1);
            scrollToTable();
        });
    }
    container.appendChild(prevLi);

    // Page Number Calculation with Ellipsis
    const pageNumbers = getPaginationNumbers(current, total);

    pageNumbers.forEach(p => {
        const li = document.createElement('li');
        if (p === '...') {
            li.className = 'page-item disabled';
            li.innerHTML = `<span class="page-link border-0 text-muted">...</span>`;
        } else {
            li.className = `page-item ${p === current ? 'active' : ''}`;
            li.innerHTML = `<button class="page-link">${p}</button>`;
            li.querySelector('button').addEventListener('click', () => {
                goToPage(p);
                scrollToTable();
            });
        }
        container.appendChild(li);
    });

    // Next Button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${current === total ? 'disabled' : ''}`;
    nextLi.innerHTML = `<button class="page-link" aria-label="Berikutnya"><i class="bi bi-chevron-right"></i></button>`;
    if (current < total) {
        nextLi.querySelector('button').addEventListener('click', () => {
            goToPage(current + 1);
            scrollToTable();
        });
    }
    container.appendChild(nextLi);
}

function getPaginationNumbers(current, total) {
    if (total <= 7) {
        return Array.from({ length: total }, (_, i) => i + 1);
    }

    if (current <= 4) {
        return [1, 2, 3, 4, 5, '...', total];
    } else if (current >= total - 3) {
        return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
    } else {
        return [1, '...', current - 1, current, current + 1, '...', total];
    }
}

function scrollToTable() {
    const table = document.querySelector('.table-custom');
    if (table) {
        const rect = table.getBoundingClientRect();
        if (rect.top < 0) {
            window.scrollTo({ top: window.scrollY + rect.top - 120, behavior: 'smooth' });
        }
    }
}

/**
 * 3. All Skills Modal Handler
 */
function initSkillsModal() {
    const modalEl = document.getElementById('skillsModal');
    if (!modalEl) return;

    // Move modal directly to document.body to avoid stacking context traps from .main-content
    document.body.appendChild(modalEl);

    if (typeof bootstrap !== 'undefined') {
        skillsModalInstance = new bootstrap.Modal(modalEl, {
            backdrop: true,
            keyboard: true,
            focus: true
        });
    }

    // Fail-safe manual close handlers for buttons inside modal
    modalEl.querySelectorAll('[data-bs-dismiss="modal"]').forEach(btn => {
        btn.addEventListener('click', (ev) => {
            ev.preventDefault();
            if (skillsModalInstance) {
                skillsModalInstance.hide();
            }
        });
    });

    // Cleanup backdrop on hide
    modalEl.addEventListener('hidden.bs.modal', () => {
        document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
        document.body.classList.remove('modal-open');
        document.body.style.removeProperty('overflow');
        document.body.style.removeProperty('padding-right');
    });

    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('.trigger-skills-modal');
        if (!trigger) return;

        const row = trigger.closest('tr.job-row');
        if (!row) return;

        const title = row.getAttribute('data-job-title') || 'Untitled';
        const company = row.getAttribute('data-company') || '';
        const role = row.getAttribute('data-role') || 'Tech Role';
        const skillsRaw = row.getAttribute('data-skills') || '';
        const url = row.getAttribute('data-url') || '';
        const city = row.getAttribute('data-city') || 'Kota Tidak Dicantumkan';
        const workArrangement = row.getAttribute('data-work-arrangement') || 'Unspecified';
        const empType = row.getAttribute('data-employment-type') || 'Full-time';
        const education = row.getAttribute('data-education-level') || 'Not Specified';
        const expTier = row.getAttribute('data-exp-tier') || '';
        const expDisplay = row.getAttribute('data-exp-display') || '';
        const salaryMin = parseFloat(row.getAttribute('data-salary-min')) || null;
        const salaryMax = parseFloat(row.getAttribute('data-salary-max')) || null;
        const platform = row.getAttribute('data-platform') || 'Platform';

        const skills = skillsRaw ? skillsRaw.split('||').filter(s => s.trim()) : [];

        // Populate Modal Header & Role
        document.getElementById('skillsModalTitle').textContent = title;
        document.getElementById('skillsModalCompany').textContent = company;
        document.getElementById('skillsModalRole').textContent = role;
        document.getElementById('skillsModalCount').textContent = `${skills.length} Keahlian Terdaftar`;

        // Populate Badges
        const arrEl = document.getElementById('skillsModalArrangement');
        if (arrEl) {
            arrEl.textContent = workArrangement;
            arrEl.className = 'badge mono-tag';
            if (workArrangement === 'Remote') arrEl.classList.add('badge-work-remote');
            else if (workArrangement === 'Hybrid') arrEl.classList.add('badge-work-hybrid');
            else if (workArrangement === 'Onsite') arrEl.classList.add('badge-work-onsite');
            else arrEl.classList.add('badge-work-unspecified');
        }

        const empEl = document.getElementById('skillsModalEmpType');
        if (empEl) empEl.textContent = empType;

        const expEl = document.getElementById('skillsModalExp');
        if (expEl) {
            expEl.textContent = expDisplay || expTier || 'Pengalaman Tidak Ditentukan';
            expEl.className = 'badge mono-tag';
            if (expTier === 'Entry Level') expEl.classList.add('badge-exp-entry');
            else if (expTier === 'Junior') expEl.classList.add('badge-exp-junior');
            else if (expTier === 'Mid-Level') expEl.classList.add('badge-exp-mid');
            else if (expTier === 'Senior') expEl.classList.add('badge-exp-senior');
            else if (expTier === 'Lead / Principal') expEl.classList.add('badge-exp-lead');
            else expEl.classList.add('badge-exp-unspecified');
        }

        const eduEl = document.getElementById('skillsModalEdu');
        if (eduEl) {
            if (education && education !== 'Not Specified') {
                eduEl.style.display = 'inline-flex';
                eduEl.textContent = education;
            } else {
                eduEl.style.display = 'none';
            }
        }

        // Populate Info Grid
        const locEl = document.getElementById('skillsModalLocation');
        if (locEl) locEl.textContent = city;

        const salEl = document.getElementById('skillsModalSalary');
        if (salEl) {
            if (salaryMin && salaryMax) salEl.textContent = `Rp ${(salaryMin/1000000).toFixed(0)} Jt - ${(salaryMax/1000000).toFixed(0)} Jt`;
            else if (salaryMin) salEl.textContent = `Min Rp ${(salaryMin/1000000).toFixed(0)} Jt`;
            else salEl.textContent = 'Disclosed on Interview';
        }

        const platEl = document.getElementById('skillsModalPlatform');
        if (platEl) platEl.textContent = platform;

        // Populate Skills List
        const listContainer = document.getElementById('skillsModalList');
        listContainer.innerHTML = '';

        if (skills.length > 0) {
            skills.forEach(s => {
                const badge = document.createElement('span');
                badge.className = 'badge-skill px-3 py-2';
                badge.style.fontSize = '0.85rem';
                badge.textContent = s;
                listContainer.appendChild(badge);
            });
        } else {
            listContainer.innerHTML = '<span class="text-muted small">Tidak ada keahlian khusus yang dicantumkan pada deskripsi loker ini.</span>';
        }

        const applyBtn = document.getElementById('skillsModalApplyBtn');
        if (applyBtn) {
            if (url) {
                applyBtn.href = url;
                applyBtn.style.display = 'inline-flex';
            } else {
                applyBtn.style.display = 'none';
            }
        }

        // Store currently opened job data for modal save button
        currentModalJobData = {
            job_title: title,
            company_name: company,
            standard_role: role,
            skills: skills,
            job_url: url,
            company_url: row.getAttribute('data-company-url') || '',
            location_city: city,
            work_type: row.getAttribute('data-work-type') || workArrangement,
            work_arrangement: workArrangement,
            employment_type: empType,
            education_level: education,
            min_experience: row.getAttribute('data-min-exp') || '',
            experience_tier: expTier,
            salary_min: row.getAttribute('data-salary-min') || null,
            salary_max: row.getAttribute('data-salary-max') || null,
            source_platform: platform
        };

        const modalSaveBtn = document.getElementById('skillsModalSaveBtn');
        if (modalSaveBtn) {
            const isSaved = row.getAttribute('data-is-saved') === 'true';
            if (isSaved) {
                modalSaveBtn.innerHTML = `<i class="bi bi-bookmark-check-fill text-warning me-1"></i><span>Tersimpan</span>`;
                modalSaveBtn.classList.add('btn-stage-active');
            } else {
                modalSaveBtn.innerHTML = `<i class="bi bi-bookmark-plus me-1"></i><span>Simpan Lowongan</span>`;
                modalSaveBtn.classList.remove('btn-stage-active');
            }
        }

        if (skillsModalInstance) {
            skillsModalInstance.show();
        }
    });

    // Handle Bookmark click from Table Row
    document.addEventListener('click', (e) => {
        const bookmarkBtn = e.target.closest('.btn-bookmark');
        if (!bookmarkBtn) return;

        const row = bookmarkBtn.closest('tr.job-row');
        if (!row) return;

        const jobData = {
            job_title: row.getAttribute('data-job-title'),
            company_name: row.getAttribute('data-company'),
            standard_role: row.getAttribute('data-role'),
            skills: (row.getAttribute('data-skills') || '').split('||').filter(s => s.trim()),
            job_url: row.getAttribute('data-url'),
            company_url: row.getAttribute('data-company-url'),
            location_city: row.getAttribute('data-city'),
            work_type: row.getAttribute('data-work-type'),
            salary_min: row.getAttribute('data-salary-min') || null,
            salary_max: row.getAttribute('data-salary-max') || null,
            source_platform: row.getAttribute('data-platform')
        };

        saveJobToServer(jobData, bookmarkBtn, row);
    });

    // Handle Bookmark click from Modal
    const modalSaveBtn = document.getElementById('skillsModalSaveBtn');
    if (modalSaveBtn) {
        modalSaveBtn.addEventListener('click', () => {
            if (!currentModalJobData) return;
            saveJobToServer(currentModalJobData, modalSaveBtn);
        });
    }

    // Initialize Toast
    const toastEl = document.getElementById('jobActionToast');
    if (toastEl && typeof bootstrap !== 'undefined') {
        jobActionToastInstance = new bootstrap.Toast(toastEl, { delay: 2500 });
    }
}

/**
 * 4. Save Job AJAX Helper
 */
async function saveJobToServer(jobData, triggerBtn, rowEl) {
    if (triggerBtn) triggerBtn.disabled = true;

    try {
        const res = await fetch('/api/jobs/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });

        if (res.status === 401) {
            // Not logged in -> redirect to login
            window.location.href = '/auth/login?next=' + encodeURIComponent(window.location.pathname + window.location.search);
            return;
        }

        const data = await res.json();
        if (data.status === 'success') {
            if (triggerBtn) {
                triggerBtn.classList.add('saved');
                const icon = triggerBtn.querySelector('i');
                if (icon) icon.className = 'bi bi-bookmark-check-fill text-warning';
                triggerBtn.title = 'Tersimpan di Saved Jobs';
                const textSpan = triggerBtn.querySelector('span');
                if (textSpan) textSpan.textContent = 'Tersimpan';
            }
            if (rowEl) {
                rowEl.setAttribute('data-is-saved', 'true');
            }
            showJobToast('Lowongan berhasil disimpan ke Saved Jobs!');
        } else {
            showJobToast(data.message || 'Gagal menyimpan lowongan', true);
        }
    } catch (err) {
        showJobToast('Terjadi kesalahan jaringan saat menyimpan.', true);
    } finally {
        if (triggerBtn) triggerBtn.disabled = false;
    }
}

function showJobToast(message, isError = false) {
    const msgEl = document.getElementById('jobToastMessage');
    const toastEl = document.getElementById('jobActionToast');
    if (!msgEl || !toastEl) return;

    msgEl.textContent = message;
    const icon = toastEl.querySelector('i');
    if (icon) {
        icon.className = isError ? 'bi bi-exclamation-circle-fill text-danger fs-5' : 'bi bi-check-circle-fill text-success fs-5';
    }

    if (jobActionToastInstance) {
        jobActionToastInstance.show();
    }
}
