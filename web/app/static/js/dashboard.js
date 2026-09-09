/**
 * KarirLake Dashboard - Chart.js & Reactive Role Filtering
 */

let skillsChart = null;
let salaryChart = null;
let workArrangementChart = null;
let employmentTypeChart = null;
let experienceTierChart = null;
let educationChart = null;
let locationChart = null;

function getChartColors() {
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    return {
        text: isDark ? '#cbd5e1' : '#334155',
        grid: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
        tooltipBg: isDark ? '#181820' : '#ffffff',
        tooltipText: isDark ? '#ffffff' : '#0f172a',
        tooltipBorder: isDark ? 'rgba(255, 255, 255, 0.22)' : '#94a3b8',
    };
}

function formatRupiah(num) {
    if (!num) return "Rp 0";
    return "Rp " + Math.round(num).toLocaleString('id-ID');
}

// 1. Inisialisasi Skills Chart (Horizontal Bar)
function renderSkillsChart(skillsData) {
    const canvas = document.getElementById('skillsChart');
    const ctx = canvas.getContext('2d');
    const labels = skillsData.map(s => s.name);
    const data = skillsData.map(s => s.demand);

    const colors = getChartColors();

    if (skillsChart) skillsChart.destroy();

    // Solid horizontal gradient: Fiery Orange -> Warm Gold
    const skillsGradient = ctx.createLinearGradient(0, 0, 450, 0);
    skillsGradient.addColorStop(0, '#ff4500');
    skillsGradient.addColorStop(1, '#ff9100');

    skillsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Jumlah Lowongan Mensyaratkan',
                data: data,
                backgroundColor: skillsGradient,
                hoverBackgroundColor: '#ffa726',
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.raw} Loker Membutuhkan`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: colors.grid, drawBorder: false },
                    ticks: { color: colors.text, font: { family: 'JetBrains Mono', size: 11 } }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: colors.text, font: { weight: '600' } }
                }
            }
        }
    });
}

// 2. Inisialisasi Salary Chart (Grouped Bars)
function renderSalaryChart(salaryData) {
    const canvas = document.getElementById('salaryChart');
    const ctx = canvas.getContext('2d');
    const labels = salaryData.map(s => s.city || "Kota Lain");
    const minSalaries = salaryData.map(s => s.min);
    const midSalaries = salaryData.map(s => s.mid);
    const maxSalaries = salaryData.map(s => s.max);

    const colors = getChartColors();

    if (salaryChart) salaryChart.destroy();

    // Solid vertical gradients (no transparent wash)
    const minGradient = ctx.createLinearGradient(0, 0, 0, 300);
    minGradient.addColorStop(0, '#64748b');
    minGradient.addColorStop(1, '#475569');

    const midGradient = ctx.createLinearGradient(0, 0, 0, 300);
    midGradient.addColorStop(0, '#10b981');
    midGradient.addColorStop(1, '#059669');

    const maxGradient = ctx.createLinearGradient(0, 0, 0, 300);
    maxGradient.addColorStop(0, '#34d399');
    maxGradient.addColorStop(1, '#10b981');

    salaryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Min Gaji',
                    data: minSalaries,
                    backgroundColor: minGradient,
                    hoverBackgroundColor: '#94a3b8',
                    borderRadius: 4,
                },
                {
                    label: 'Rata-Rata (Mid)',
                    data: midSalaries,
                    backgroundColor: midGradient,
                    hoverBackgroundColor: '#34d399',
                    borderRadius: 4,
                },
                {
                    label: 'Max Gaji',
                    data: maxSalaries,
                    backgroundColor: maxGradient,
                    hoverBackgroundColor: '#6ee7b7',
                    borderRadius: 4,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: colors.text, font: { size: 11, weight: '600' } }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.dataset.label}: ${formatRupiah(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.text, font: { size: 11 } }
                },
                y: {
                    grid: { color: colors.grid, drawBorder: false },
                    ticks: {
                        color: colors.text,
                        font: { family: 'JetBrains Mono', size: 10 },
                        callback: function(val) {
                            return (val / 1000000).toFixed(0) + " Jt";
                        }
                    }
                }
            }
        }
    });
}

// 3. Inisialisasi Work Arrangement Donut Chart
function renderWorkArrangementChart(workData) {
    const canvas = document.getElementById('workArrangementChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const labels = (workData || []).map(w => w.type || "Other");
    const data = (workData || []).map(w => w.count || 0);

    const colors = getChartColors();
    if (workArrangementChart) workArrangementChart.destroy();

    const colorMap = {
        'Onsite': '#3b82f6',
        'Hybrid': '#8b5cf6',
        'Remote': '#10b981',
        'Not Specified': '#64748b'
    };
    const bgColors = labels.map(l => colorMap[l] || '#0ea5e9');

    workArrangementChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderWidth: 2,
                borderColor: colors.tooltipBg,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: colors.text, font: { size: 11, weight: '500' }, boxWidth: 12, padding: 12 }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw} Loker`;
                        }
                    }
                }
            }
        }
    });
}

// 4. Inisialisasi Employment Type Donut Chart
function renderEmploymentTypeChart(empData) {
    const canvas = document.getElementById('employmentTypeChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const labels = (empData || []).map(e => e.type || "Other");
    const data = (empData || []).map(e => e.count || 0);

    const colors = getChartColors();
    if (employmentTypeChart) employmentTypeChart.destroy();

    const colorMap = {
        'Full-time': '#10b981',
        'Contractual': '#f59e0b',
        'Internship': '#06b6d4',
        'Part-time': '#ec4899',
        'Freelance': '#8b5cf6',
        'Not Specified': '#64748b'
    };
    const bgColors = labels.map(l => colorMap[l] || '#6366f1');

    employmentTypeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderWidth: 2,
                borderColor: colors.tooltipBg,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: colors.text, font: { size: 11, weight: '500' }, boxWidth: 12, padding: 12 }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.label}: ${context.raw} Loker`;
                        }
                    }
                }
            }
        }
    });
}

// 5. Inisialisasi Experience Seniority Tiers (Bar Chart)
function renderExperienceTierChart(expData) {
    const canvas = document.getElementById('experienceTierChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const labels = (expData || []).map(e => e.tier || "Other");
    const data = (expData || []).map(e => e.count || 0);

    const colors = getChartColors();
    if (experienceTierChart) experienceTierChart.destroy();

    const colorMap = {
        'Entry Level': '#10b981',
        'Junior': '#06b6d4',
        'Mid-Level': '#3b82f6',
        'Senior': '#8b5cf6',
        'Lead / Principal': '#f59e0b',
        'Not Specified': '#64748b'
    };
    const bgColors = labels.map(l => colorMap[l] || '#6366f1');

    experienceTierChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(l => l.replace(' / Principal', '').replace(' Level', '')),
            datasets: [{
                label: 'Jumlah Lowongan',
                data: data,
                backgroundColor: bgColors,
                borderRadius: 4,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        title: function(context) {
                            return labels[context[0].dataIndex] || context[0].label;
                        },
                        label: function(context) {
                            return ` ${context.raw} Loker`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.text, font: { size: 10, weight: '600' } }
                },
                y: {
                    grid: { color: colors.grid, drawBorder: false },
                    ticks: { color: colors.text, font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}

// 4. Inisialisasi Education Chart (Doughnut)
function renderEducationChart(eduData) {
    const ctx = document.getElementById('educationChart').getContext('2d');
    const labels = eduData.map(e => e.level);
    const data = eduData.map(e => e.count);

    const colors = getChartColors();

    if (educationChart) educationChart.destroy();

    educationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#6366f1',
                    '#a855f7',
                    '#ec4899',
                    '#06b6d4'
                ],
                borderWidth: 2,
                borderColor: colors.tooltipBg,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: colors.text, font: { size: 11 } }
                },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    padding: 10
                }
            }
        }
    });
}

// 5. Inisialisasi Location Hubs Chart (Bar)
function renderLocationChart(locationData) {
    const canvas = document.getElementById('locationChart');
    const ctx = canvas.getContext('2d');
    const labels = locationData.map(l => l.city);
    const data = locationData.map(l => l.count);

    const colors = getChartColors();

    if (locationChart) locationChart.destroy();

    // Solid vertical gradient: Electric Indigo -> Deep Indigo (no transparency)
    const locGradient = ctx.createLinearGradient(0, 0, 0, 220);
    locGradient.addColorStop(0, '#818cf8');
    locGradient.addColorStop(1, '#4f46e5');

    locationChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: locGradient,
                hoverBackgroundColor: '#a5b4fc',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: colors.tooltipBg,
                    titleColor: colors.tooltipText,
                    bodyColor: colors.tooltipText,
                    borderColor: colors.tooltipBorder,
                    borderWidth: 1,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: colors.text, font: { size: 10 } }
                },
                y: {
                    grid: { color: colors.grid, drawBorder: false },
                    ticks: { color: colors.text, font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}

// Render Top Hiring Companies Cards
function renderTopCompanies(companies) {
    const container = document.getElementById('topCompaniesContainer');
    if (!container) return;

    if (!companies || companies.length === 0) {
        container.innerHTML = `<div class="col-12 text-center text-muted py-4">Data perusahaan belum tersedia untuk role ini.</div>`;
        return;
    }

    let html = "";
    companies.forEach(comp => {
        const industry = comp.industry || 'Tech / General';
        html += `
            <div class="col-12 col-sm-6 col-lg-3">
                <div class="p-3 rounded-3 d-flex flex-column justify-content-between h-100" style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle);">
                    <div>
                        <div class="d-flex justify-content-between align-items-center gap-2 mb-2">
                            <span class="badge mono-tag text-truncate employer-industry-badge" style="max-width: 60%;" title="${industry}">
                                ${industry}
                            </span>
                            <span class="badge mono-tag flex-shrink-0 employer-openings-badge">
                                ${comp.openings} Loker
                            </span>
                        </div>
                        <div class="fw-bold text-truncate" style="color: var(--text-primary); font-size: 0.95rem;" title="${comp.name}">
                            ${comp.name}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    container.innerHTML = html;
}

// Reactive Fetch saat User Mengklik Role Pill
function setupRolePills() {
    const pills = document.querySelectorAll('.role-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', async () => {
            const role = pill.getAttribute('data-role');

            // Set active class
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

            // Update badges label
            document.querySelectorAll('.current-role-badge').forEach(b => b.textContent = role);

            // Fetch AJAX to API
            try {
                const response = await fetch(`/api/role-insights/${encodeURIComponent(role)}`);
                const result = await response.json();

                if (result.status === 'success') {
                    const d = result.data;

                    // Update 4 Pulse KPI Scorecards
                    if (d.kpis) {
                        const elTotal = document.getElementById('kpiTotalJobs');
                        const elSalary = document.getElementById('kpiAvgSalary');
                        const elRemote = document.getElementById('kpiRemotePct');
                        const elComp = document.getElementById('kpiTotalCompanies');

                        if (elTotal) elTotal.textContent = Number(d.kpis.total_jobs).toLocaleString('en-US');
                        if (elSalary) {
                            elSalary.textContent = d.kpis.avg_salary > 0 
                                ? "Rp " + Math.round(d.kpis.avg_salary / 1000000).toLocaleString('id-ID') + " Jt" 
                                : "N/A";
                        }
                        if (elRemote) elRemote.textContent = d.kpis.remote_pct + "%";
                        if (elComp) elComp.textContent = Number(d.kpis.total_companies).toLocaleString('en-US');
                    }

                    // Update all charts
                    renderSkillsChart(d.top_skills);
                    renderSalaryChart(d.salaries);
                    renderWorkArrangementChart(d.work_arrangements);
                    renderEmploymentTypeChart(d.employment_types);
                    renderExperienceTierChart(d.experience_tiers);
                    renderEducationChart(d.education_reqs);
                    renderLocationChart(d.locations);
                    renderTopCompanies(d.top_companies);
                }
            } catch (err) {
                console.error("Gagal mengambil data role:", err);
            }
        });
    });
}

// Callback saat tema di-toggle
function updateChartsTheme(theme) {
    const colors = getChartColors();
    [skillsChart, salaryChart, workArrangementChart, employmentTypeChart, experienceTierChart, educationChart, locationChart].forEach(chart => {
        if (!chart) return;
        if (chart.options.scales) {
            Object.values(chart.options.scales).forEach(scale => {
                if (scale.ticks) scale.ticks.color = colors.text;
                if (scale.grid) scale.grid.color = colors.grid;
            });
        }
        if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
            chart.options.plugins.legend.labels.color = colors.text;
        }
        chart.update();
    });
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    if (typeof INITIAL_INSIGHTS !== 'undefined') {
        renderSkillsChart(INITIAL_INSIGHTS.top_skills);
        renderSalaryChart(INITIAL_INSIGHTS.salaries);
        renderWorkArrangementChart(INITIAL_INSIGHTS.work_arrangements);
        renderEmploymentTypeChart(INITIAL_INSIGHTS.employment_types);
        renderExperienceTierChart(INITIAL_INSIGHTS.experience_tiers);
        renderEducationChart(INITIAL_INSIGHTS.education_reqs);
        renderLocationChart(INITIAL_INSIGHTS.locations);
    }
    setupRolePills();
});
