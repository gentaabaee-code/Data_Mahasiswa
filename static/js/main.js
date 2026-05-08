/* =============================================================================
   Student Data Management System – main.js
   Single-page application logic: CRUD, Search, Sort, UI helpers.
   ============================================================================= */

'use strict';

let allStudents = [];
let displayedStudents = [];
let editingId = null;
let deleteTargetId = null;
let currentSection = 'dashboard';

const dashboardCharts = {};

const SECTION_META = {
    dashboard: {
        kicker: 'Panel Analitik',
        title: 'Dashboard',
        subtitle: 'Pantau performa akademik mahasiswa dari satu tampilan ringkas sebelum masuk ke data lengkap.',
    },
    students: {
        kicker: 'Pusat Data',
        title: 'Data Mahasiswa',
        subtitle: 'Lihat seluruh mahasiswa beserta fitur pencarian, pengurutan, ekspor, dan pengelolaan data seperti sebelumnya.',
    },
};

const CHART_COLORS = ['#4F46E5', '#38C999', '#F4B740', '#66758F', '#66A8FF', '#F26D7D'];

const studentModal = new bootstrap.Modal(document.getElementById('studentModal'));
const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
const viewModal = new bootstrap.Modal(document.getElementById('viewModal'));

async function apiFetch(url, options = {}) {
    const resp = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });

    const data = await resp.json();

    if (!resp.ok) {
        const msg = Array.isArray(data.errors)
            ? data.errors.join('\n')
            : (data.errors || 'Request failed');
        throw new Error(msg);
    }

    return data;
}

async function loadStudents() {
    showLoading(true);

    try {
        const result = await apiFetch('/api/students');
        allStudents = Array.isArray(result.data) ? result.data : [];
        updateTopbarCount(allStudents);
        renderDashboard(allStudents);
        showStudentsHome({ resetForms: false, closePanels: false });
    } catch (err) {
        showToast('Gagal memuat data: ' + err.message, 'danger');
        showLoading(false);
    }
}

function switchSection(section) {
    currentSection = section;

    const dashboardSection = document.getElementById('dashboard-section');
    const studentsSection = document.getElementById('students-section');
    const dashboardNav = document.getElementById('nav-dashboard');
    const studentsNav = document.getElementById('nav-students');

    const isDashboard = section === 'dashboard';

    dashboardSection.classList.remove('section-reveal');
    studentsSection.classList.remove('section-reveal');

    dashboardSection.classList.toggle('d-none', !isDashboard);
    studentsSection.classList.toggle('d-none', isDashboard);
    dashboardNav.classList.toggle('is-active', isDashboard);
    studentsNav.classList.toggle('is-active', !isDashboard);

    const activeSection = isDashboard ? dashboardSection : studentsSection;
    void activeSection.offsetWidth;
    activeSection.classList.add('section-reveal');

    const meta = SECTION_META[section] || SECTION_META.dashboard;
    document.getElementById('section-kicker').textContent = meta.kicker;
    document.getElementById('section-title').textContent = meta.title;
    document.getElementById('section-subtitle').textContent = meta.subtitle;

    if (!isDashboard) {
        showStudentsHome();
    }
}

function renderTable(students) {
    const tbody = document.getElementById('students-tbody');
    const tableWrap = document.getElementById('table-wrapper');
    const emptyState = document.getElementById('empty-state');
    const badge = document.getElementById('table-badge');
    const isAdmin = window.IS_ADMIN === true || window.IS_ADMIN === 'true';

    showLoading(false);
    badge.textContent = students.length;

    if (students.length === 0) {
        tableWrap.classList.add('d-none');
        emptyState.classList.remove('d-none');
        tbody.innerHTML = '';
        return;
    }

    emptyState.classList.add('d-none');
    tableWrap.classList.remove('d-none');

    tbody.innerHTML = students.map((student, index) => {
        const gpa = Number(student.gpa || 0);
        const safeName = esc(student.name || 'Mahasiswa');
        const safeStatus = esc(student.status || 'Status belum tersedia');
        const initial = esc((student.name || '?').trim().charAt(0).toUpperCase() || '?');
        const actions = isAdmin ? `
            <td class="text-center" style="white-space: nowrap;">
                <button class="btn btn-sm btn-outline-primary action-icon me-1" title="Lihat detail" onclick="openViewModal('${student.student_id}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-warning action-icon me-1" title="Edit" onclick="openEditModal('${student.student_id}')">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger action-icon" title="Hapus" onclick="openDeleteModal('${student.student_id}', '${safeName}')">
                    <i class="bi bi-trash3"></i>
                </button>
            </td>
        ` : '';

        return `
            <tr>
                <td class="text-muted small">${index + 1}</td>
                <td><span class="student-code">${esc(student.student_id)}</span></td>
                <td>
                    <div class="student-identity">
                        <span class="student-avatar-mini">${initial}</span>
                        <div>
                            <div class="student-name">${safeName}</div>
                            <div class="student-subline">${safeStatus}</div>
                        </div>
                    </div>
                </td>
                <td>${formatBirthDate(student.birth_date)}</td>
                <td class="text-muted small">${esc(student.email)}</td>
                <td class="small">${esc(student.education_level || '—')}</td>
                <td><span class="table-chip">${esc(student.major)}</span></td>
                <td><span class="gpa-badge ${gpaClass(gpa)}">${gpa.toFixed(2)}</span></td>
                <td><span class="grade-pill">${student.semester ?? '—'}</span></td>
                ${actions}
            </tr>
        `;
    }).join('');
}

function updateTopbarCount(students) {
    document.getElementById('nav-count').textContent = `${students.length} mahasiswa`;
}

function renderDashboard(students) {
    const total = students.length;
    const averageGpa = total
        ? students.reduce((sum, student) => sum + Number(student.gpa || 0), 0) / total
        : 0;
    const deansCount = students.filter(student => Number(student.gpa || 0) >= 3.5).length;

    const majorGroups = groupBy(students, student => normalizeLabel(student.major, 'Belum diisi'));
    const sortedMajors = [...majorGroups.entries()].sort((left, right) => right[1].length - left[1].length);
    const topMajor = sortedMajors[0];

    document.getElementById('dashboard-total').textContent = String(total);
    document.getElementById('dashboard-average-gpa').textContent = averageGpa.toFixed(2);
    document.getElementById('dashboard-average-gpa-meta').textContent = total
        ? `Nilai rerata seluruh mahasiswa pada ${majorGroups.size || 0} jurusan.`
        : 'Belum ada data untuk diringkas.';
    document.getElementById('dashboard-deans-count').textContent = String(deansCount);
    document.getElementById('dashboard-deans-meta').textContent = total
        ? `${percentage(deansCount, total)}% dari total mahasiswa berada di Dean's List.`
        : 'Mahasiswa dengan IPK minimal 3.50 akan muncul di sini.';
    document.getElementById('dashboard-top-major').textContent = topMajor ? topMajor[0] : 'Belum ada';
    document.getElementById('dashboard-top-major-meta').textContent = topMajor
        ? `${topMajor[1].length} mahasiswa paling dominan di jurusan ini.`
        : 'Jurusan dengan populasi terbanyak akan tampil di sini.';

    renderGpaDistribution(students);
    renderMajorRadar(sortedMajors);
    renderSemesterChart(students);
    renderMajorComposition(sortedMajors, total);
}

function renderGpaDistribution(students) {
    const ranges = [
        { label: '<2.5', min: 0, max: 2.5 },
        { label: '2.5 - 2.99', min: 2.5, max: 3.0 },
        { label: '3.0 - 3.49', min: 3.0, max: 3.5 },
        { label: '3.5 - 3.74', min: 3.5, max: 3.75 },
        { label: '3.75 - 4.0', min: 3.75, max: 4.01 },
    ];

    const counts = ranges.map(range => students.filter(student => {
        const gpa = Number(student.gpa || 0);
        return gpa >= range.min && gpa < range.max;
    }).length);

    renderChart('gpaDistribution', 'gpa-distribution-chart', {
        type: 'bar',
        data: {
            labels: ranges.map(range => range.label),
            datasets: [{
                data: counts,
                backgroundColor: ['#cfd7ff', '#b7d3ff', '#8ac0ff', '#69a9ff', '#4f7fff'],
                borderRadius: 18,
                borderSkipped: false,
                maxBarThickness: 40,
            }],
        },
        options: buildChartOptions({
            yTicksPrecision: 0,
            yMin: 0,
            yMax: 11,
            yStepSize: 1,
            showLegend: false,
        }),
    });

    const gpaBandList = document.getElementById('gpa-band-list');
    if (gpaBandList) {
        gpaBandList.innerHTML = ranges.map((range, index) => `
            <span class="dashboard-chip">
                <strong>${range.label}</strong>
                <span>${counts[index]} mahasiswa</span>
            </span>
        `).join('');
    }
}

function renderMajorRadar(sortedMajors) {
    const labels = sortedMajors.map(([major]) => major);
    const averages = sortedMajors.map(([, students]) => averageOf(students.map(student => Number(student.gpa || 0))));

    renderChart('majorRadar', 'major-radar-chart', {
        type: 'radar',
        data: {
            labels,
            datasets: [{
                label: 'Rata-rata IPK',
                data: averages,
                backgroundColor: 'rgba(102, 168, 255, 0.18)',
                borderColor: '#4F8CFF',
                pointBackgroundColor: '#4F8CFF',
                pointBorderColor: '#ffffff',
                pointHoverBackgroundColor: '#ffffff',
                pointHoverBorderColor: '#4F8CFF',
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
            },
            scales: {
                r: {
                    suggestedMin: 0,
                    suggestedMax: 4,
                    angleLines: { color: 'rgba(104, 132, 255, 0.14)' },
                    grid: { color: 'rgba(104, 132, 255, 0.16)' },
                    pointLabels: { color: '#5D6883', font: { size: 11, weight: 700 } },
                    ticks: {
                        backdropColor: 'transparent',
                        color: '#74809B',
                        stepSize: 1,
                    },
                },
            },
        },
    });

    document.getElementById('major-average-list').innerHTML = sortedMajors.length
        ? sortedMajors.map((entry, index) => {
            const [major, students] = entry;
            return `
                <div class="dashboard-list-row">
                    <span class="dashboard-list-label">${esc(major)}</span>
                    <span class="dashboard-list-value" style="color: ${CHART_COLORS[index % CHART_COLORS.length]};">${averageOf(students.map(student => Number(student.gpa || 0))).toFixed(2)}</span>
                </div>
            `;
        }).join('')
        : emptyDashboardState('Belum ada jurusan untuk dibandingkan.');
}

function renderSemesterChart(students) {
    const semesterCounts = groupBy(
        students.filter(student => Number.isFinite(Number(student.semester)) && Number(student.semester) > 0),
        student => Number(student.semester)
    );

    const sortedSemesters = [...semesterCounts.entries()].sort((left, right) => left[0] - right[0]);
    const labels = sortedSemesters.map(([semester]) => `Sem ${semester}`);
    const counts = sortedSemesters.map(([, entries]) => entries.length);

    renderChart('semesterBar', 'semester-chart', {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                data: counts,
                backgroundColor: ['#A7E8CF', '#7EDCB9', '#57D0A4', '#38C999', '#2DB78A', '#239D75'],
                borderRadius: 18,
                borderSkipped: false,
                maxBarThickness: 36,
            }],
        },
        options: buildChartOptions({ yTicksPrecision: 0, showLegend: false }),
    });
}

function renderMajorComposition(sortedMajors, total) {
    const labels = sortedMajors.map(([major]) => major);
    const counts = sortedMajors.map(([, students]) => students.length);
    const colors = labels.map((_, index) => CHART_COLORS[index % CHART_COLORS.length]);

    renderChart('majorDoughnut', 'major-doughnut-chart', {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: counts,
                backgroundColor: colors,
                borderWidth: 0,
                hoverOffset: 6,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: { display: false },
            },
        },
    });

    document.getElementById('major-total-count').textContent = String(total);
    document.getElementById('major-share-list').innerHTML = sortedMajors.length
        ? sortedMajors.map((entry, index) => {
            const [major, students] = entry;
            const percent = percentage(students.length, total);
            const color = colors[index];
            return `
                <div class="progress-row">
                    <div class="progress-row-head">
                        <span class="progress-label">
                            <span class="progress-dot" style="background: ${color};"></span>
                            <span>${esc(major)}</span>
                        </span>
                        <span class="progress-value">${percent}%</span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-bar" style="width: ${percent}%; background: ${color};"></div>
                    </div>
                </div>
            `;
        }).join('')
        : emptyDashboardState('Belum ada komposisi jurusan.');
}

function renderChart(key, canvasId, config) {
    if (typeof Chart === 'undefined') {
        return;
    }

    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        return;
    }

    if (dashboardCharts[key]) {
        dashboardCharts[key].destroy();
    }

    dashboardCharts[key] = new Chart(canvas, config);
}

function buildChartOptions({ yTicksPrecision = null, yMin = null, yMax = null, yStepSize = null, showLegend = false } = {}) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: showLegend },
            tooltip: {
                backgroundColor: 'rgba(26, 36, 64, 0.92)',
                titleFont: { family: 'Plus Jakarta Sans', weight: 700 },
                bodyFont: { family: 'Plus Jakarta Sans' },
                padding: 12,
            },
        },
        scales: {
            x: {
                grid: { display: false },
                border: { display: false },
                ticks: { color: '#69758E', font: { family: 'Plus Jakarta Sans', weight: 700 } },
            },
            y: {
                beginAtZero: true,
                min: yMin,
                max: yMax,
                grid: { color: 'rgba(104, 132, 255, 0.12)' },
                border: { display: false },
                ticks: {
                    color: '#7A86A2',
                    precision: yTicksPrecision,
                    stepSize: yStepSize,
                    font: { family: 'Plus Jakarta Sans', weight: 700 },
                },
            },
        },
    };
}

function showStudentsHome({ resetForms = true, closePanels = true } = {}) {
    if (resetForms) {
        document.getElementById('search-form').reset();
        document.getElementById('sort-form').reset();
        updateAlgoHint();
    }

    hideResultInfo();

    if (closePanels) {
        ['searchPanel', 'sortPanel'].forEach(id => {
            const element = document.getElementById(id);
            bootstrap.Collapse.getOrCreateInstance(element, { toggle: false }).hide();
        });
    }

    displayedStudents = [...allStudents];
    renderTable(displayedStudents);
    setViewLabel('Semua Mahasiswa', 'primary');
}

function openAddModal() {
    editingId = null;

    document.getElementById('modal-title').innerHTML =
        '<i class="bi bi-person-plus me-1"></i> Tambah Mahasiswa';
    document.getElementById('submit-btn').innerHTML =
        '<i class="bi bi-floppy me-1"></i> Simpan';
    document.getElementById('student-form').reset();
    document.getElementById('f-student_id').disabled = false;
    hideFormErrors();

    studentModal.show();
}

function openEditModal(student_id) {
    const student = findStudent(student_id);
    if (!student) return;

    editingId = student_id;

    document.getElementById('modal-title').innerHTML =
        '<i class="bi bi-pencil me-1"></i> Edit Mahasiswa';
    document.getElementById('submit-btn').innerHTML =
        '<i class="bi bi-floppy me-1"></i> Simpan Perubahan';
    hideFormErrors();

    document.getElementById('f-student_id').value = student.student_id;
    document.getElementById('f-student_id').disabled = true;
    document.getElementById('f-name').value = student.name;
    document.getElementById('f-birth_date').value = student.birth_date || '';
    document.getElementById('f-email').value = student.email;
    document.getElementById('f-phone').value = student.phone;
    document.getElementById('f-education_level').value = student.education_level || '';
    document.getElementById('f-major').value = student.major;
    document.getElementById('f-gpa').value = student.gpa;
    document.getElementById('f-semester').value = student.semester ?? '';

    studentModal.show();
}

async function submitStudentForm(e) {
    e.preventDefault();
    hideFormErrors();

    const semesterValue = document.getElementById('f-semester').value.trim();

    const payload = {
        student_id: document.getElementById('f-student_id').value.trim(),
        name: document.getElementById('f-name').value.trim(),
        birth_date: document.getElementById('f-birth_date').value,
        email: document.getElementById('f-email').value.trim(),
        phone: document.getElementById('f-phone').value.trim(),
        education_level: document.getElementById('f-education_level').value,
        major: document.getElementById('f-major').value.trim(),
        gpa: parseFloat(document.getElementById('f-gpa').value),
        semester: semesterValue === '' ? null : parseInt(semesterValue, 10),
    };

    const btn = document.getElementById('submit-btn');
    setButtonLoading(btn, true, 'Menyimpan…');

    try {
        if (editingId) {
            await apiFetch(`/api/students/${editingId}`, {
                method: 'PUT',
                body: JSON.stringify(payload),
            });
            showToast(`Mahasiswa "${payload.name}" berhasil diperbarui.`, 'success');
        } else {
            await apiFetch('/api/students', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            showToast(`Mahasiswa "${payload.name}" berhasil ditambahkan.`, 'success');
        }

        studentModal.hide();
        await loadStudents();
    } catch (err) {
        showFormErrors(err.message.split('\n'));
    } finally {
        const label = editingId ? 'Simpan Perubahan' : 'Simpan';
        setButtonLoading(btn, false, `<i class="bi bi-floppy me-1"></i> ${label}`);
    }
}

function openDeleteModal(student_id, name) {
    deleteTargetId = student_id;
    document.getElementById('delete-student-name').textContent = name;
    deleteModal.show();
}

async function confirmDelete() {
    if (!deleteTargetId) return;

    const btn = document.getElementById('confirm-delete-btn');
    setButtonLoading(btn, true, 'Menghapus…');

    try {
        await apiFetch(`/api/students/${deleteTargetId}`, { method: 'DELETE' });
        showToast('Mahasiswa berhasil dihapus.', 'success');
        deleteModal.hide();
        await loadStudents();
    } catch (err) {
        showToast('Gagal menghapus: ' + err.message, 'danger');
    } finally {
        setButtonLoading(btn, false, '<i class="bi bi-trash3 me-1"></i> Hapus');
        deleteTargetId = null;
    }
}

function openViewModal(student_id) {
    const student = findStudent(student_id);
    if (!student) return;

    const gpa = Number(student.gpa || 0);
    const rows = [
        ['Tanggal Lahir', formatBirthDate(student.birth_date)],
        ['Email', esc(student.email)],
        ['Telepon', esc(student.phone)],
        ['Jenjang Pendidikan', esc(student.education_level || '—')],
        ['Jurusan', esc(student.major)],
        ['IPK', `<span class="gpa-badge ${gpaClass(gpa)}">${gpa.toFixed(2)}</span>`],
        ['Semester', student.semester ?? '<span class="text-muted">—</span>'],
        ['Status', `<span class="status-pill ${statusClass(student.status)}">${esc(student.status || '—')}</span>`],
        ['Terdaftar', student.created_at ? formatTimestamp(student.created_at) : '—'],
    ].map(([label, value]) => `
        <div class="detail-row">
            <span class="detail-label">${label}</span>
            <span class="detail-value">${value}</span>
        </div>
    `).join('');

    document.getElementById('view-modal-body').innerHTML = `
        <div class="d-flex align-items-center gap-3 mb-4">
            <div class="avatar-circle">${esc((student.name || '?').charAt(0).toUpperCase())}</div>
            <div>
                <h5 class="mb-0 fw-bold">${esc(student.name)}</h5>
                <small class="text-muted"><code>${esc(student.student_id)}</code></small>
            </div>
        </div>
        ${rows}
    `;

    viewModal.show();
}

async function doSearch(e) {
    e.preventDefault();

    const query = document.getElementById('search-query').value.trim();
    const field = document.getElementById('search-field').value;
    const algo = document.getElementById('search-algorithm').value;

    if (!query) return;

    showLoading(true);

    try {
        const url = `/api/students/search?query=${encodeURIComponent(query)}&field=${field}&algorithm=${algo}`;
        const result = await apiFetch(url);

        displayedStudents = result.data;
        renderTable(displayedStudents);
        setViewLabel(`Pencarian: "${query}"`, 'info');

        const matchType = algo === 'binary' ? 'prefiks (diawali dengan)' : 'substring (mengandung)';
        const info = document.getElementById('search-result-info');
        info.innerHTML = `
            <i class="bi bi-info-circle me-1"></i>
            Algoritma: <strong>${result.algorithm}</strong> | 
            Kecocokan: <strong>${matchType}</strong> | 
            Terbaik: <code>${result.complexity.best}</code>
            Rata-rata: <code>${result.complexity.avg}</code>
            Terburuk: <code>${result.complexity.worst}</code> | 
            Waktu: <strong>${result.elapsed_ms} ms</strong> | 
            Ditemukan: <strong>${result.count}</strong> hasil
        `;
        info.classList.remove('d-none');
    } catch (err) {
        showToast('Pencarian gagal: ' + err.message, 'danger');
        showLoading(false);
    }
}

function updateAlgoHint() {
    const algo = document.getElementById('search-algorithm').value;
    const hint = document.getElementById('algo-hint');

    if (algo === 'binary') {
        hint.innerHTML = 'Mencocokkan data yang <strong>diawali dengan</strong> kata kunci (prefiks saja).';
    } else {
        hint.innerHTML = 'Mencocokkan data yang <strong>mengandung</strong> kata kunci di mana saja.';
    }
}

function clearSearch() {
    document.getElementById('search-form').reset();
    document.getElementById('search-result-info').classList.add('d-none');
    updateAlgoHint();
    displayedStudents = [...allStudents];
    renderTable(displayedStudents);
    setViewLabel('Semua Mahasiswa', 'primary');
}

async function doSort(e) {
    e.preventDefault();

    const field = document.getElementById('sort-field').value;
    const algo = document.getElementById('sort-algorithm').value;
    const order = document.getElementById('sort-order').value;

    showLoading(true);

    try {
        const url = `/api/students/sort?algorithm=${algo}&field=${field}&order=${order}`;
        const result = await apiFetch(url);

        displayedStudents = result.data;
        renderTable(displayedStudents);
        setViewLabel(`Diurutkan: ${humanizeField(field)} ${order === 'asc' ? '↑' : '↓'} (${algo})`, 'warning');

        const info = document.getElementById('sort-result-info');
        info.innerHTML = `
            <i class="bi bi-info-circle me-1"></i>
            Algoritma: <strong>${result.algorithm}</strong> | 
            Waktu: <code>${result.time_complexity}</code>
            Ruang: <code>${result.space_complexity}</code> | 
            Durasi: <strong>${result.elapsed_ms} ms</strong>
        `;
        info.classList.remove('d-none');
    } catch (err) {
        showToast('Pengurutan gagal: ' + err.message, 'danger');
        showLoading(false);
    }
}

function clearSort() {
    document.getElementById('sort-form').reset();
    document.getElementById('sort-result-info').classList.add('d-none');
    displayedStudents = [...allStudents];
    renderTable(displayedStudents);
    setViewLabel('Semua Mahasiswa', 'primary');
}

function showLoading(show) {
    document.getElementById('loading-state').classList.toggle('d-none', !show);
    if (show) {
        document.getElementById('table-wrapper').classList.add('d-none');
        document.getElementById('empty-state').classList.add('d-none');
    }
}

function setViewLabel(text, variant) {
    const el = document.getElementById('view-mode-label');
    el.className = `view-chip view-chip-${variant}`;
    el.textContent = text;
}

function setButtonLoading(btn, loading, label) {
    if (loading) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>…';
    } else {
        btn.disabled = false;
        btn.innerHTML = label;
    }
}

function showFormErrors(messages) {
    const el = document.getElementById('form-errors');
    el.innerHTML = messages.map(message => `<div>• ${esc(message)}</div>`).join('');
    el.classList.remove('d-none');
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideFormErrors() {
    document.getElementById('form-errors').classList.add('d-none');
}

function hideResultInfo() {
    document.getElementById('search-result-info').classList.add('d-none');
    document.getElementById('sort-result-info').classList.add('d-none');
}

function findStudent(student_id) {
    return allStudents.find(student => student.student_id === student_id)
        || displayedStudents.find(student => student.student_id === student_id);
}

function gpaClass(gpa) {
    if (gpa >= 3.0) return 'gpa-a';
    if (gpa >= 2.5) return 'gpa-b';
    if (gpa >= 2.0) return 'gpa-c';
    return 'gpa-d';
}

function statusClass(status) {
    const map = {
        "Dean's List": 'status-deans',
        'Good Standing': 'status-good',
        'Academic Probation': 'status-probation',
        'Academic Suspension': 'status-suspension',
    };

    return map[status] || 'status-good';
}

function formatTimestamp(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime())
        ? '—'
        : new Intl.DateTimeFormat('id-ID', {
            dateStyle: 'medium',
            timeStyle: 'short',
        }).format(date);
}

function formatBirthDate(value) {
    if (!value) {
        return '—';
    }

    const [year, month, day] = String(value).split('-');
    if (!year || !month || !day) {
        return esc(value);
    }

    return `${day}/${month}/${year}`;
}

function humanizeField(field) {
    const map = {
        name: 'nama',
        student_id: 'NIM',
        gpa: 'IPK',
        age: 'usia',
        birth_date: 'tanggal lahir',
        education_level: 'jenjang pendidikan',
        major: 'jurusan',
        email: 'email',
    };

    return map[field] || field;
}

function groupBy(items, keyFn) {
    const map = new Map();

    items.forEach(item => {
        const key = keyFn(item);
        const bucket = map.get(key) || [];
        bucket.push(item);
        map.set(key, bucket);
    });

    return map;
}

function normalizeLabel(value, fallback = 'Tidak diketahui') {
    return value && String(value).trim() ? String(value).trim() : fallback;
}

function averageOf(values) {
    if (!values.length) {
        return 0;
    }

    return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function percentage(value, total) {
    if (!total) {
        return 0;
    }

    return Math.round((value / total) * 100);
}

function emptyDashboardState(message) {
    return `<div class="dashboard-list-row"><span class="dashboard-list-label">${esc(message)}</span></div>`;
}

function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

const _TOAST_ICONS = {
    success: 'bi-check-circle-fill',
    danger: 'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info: 'bi-info-circle-fill',
};

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const id = `toast-${Date.now()}`;
    const icon = _TOAST_ICONS[type] || 'bi-info-circle-fill';

    container.insertAdjacentHTML('beforeend', `
        <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert" aria-live="assertive">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="bi ${icon}"></i>
                    ${esc(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `);

    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 3500 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

document.addEventListener('DOMContentLoaded', () => {
    switchSection('dashboard');
    updateAlgoHint();
    loadStudents();
});
