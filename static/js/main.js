/* =============================================================================
   Student Data Management System – main.js
   Single-page application logic: CRUD, Search, Sort, UI helpers.
   ============================================================================= */

'use strict';

/* ── State ────────────────────────────────────────────────────────────────── */
let allStudents      = [];    // Full list loaded from the server
let displayedStudents = [];   // Currently rendered subset (filtered / sorted)
let editingId        = null;  // student_id being edited; null → add mode
let deleteTargetId   = null;  // student_id queued for deletion

/* ── Bootstrap modal instances ───────────────────────────────────────────── */
const studentModal = new bootstrap.Modal(document.getElementById('studentModal'));
const deleteModal  = new bootstrap.Modal(document.getElementById('deleteModal'));
const viewModal    = new bootstrap.Modal(document.getElementById('viewModal'));

/* ═══════════════════════════════ API Layer ══════════════════════════════════ */

/**
 * Thin fetch wrapper that:
 *  - Always sends/expects JSON
 *  - Throws Error with the server's error messages on non-2xx responses
 *
 * @param {string}  url     - Relative API endpoint
 * @param {object}  options - Fetch options (method, body, …)
 * @returns {Promise<object>} Parsed JSON response body
 */
async function apiFetch(url, options = {}) {
    const resp = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });

    const data = await resp.json();

    if (!resp.ok) {
        // Surface server-side validation messages to the user
        const msg = Array.isArray(data.errors)
            ? data.errors.join('\n')
            : (data.errors || 'Request failed');
        throw new Error(msg);
    }

    return data;
}


/* ═══════════════════════════════ Load / Render ══════════════════════════════ */

/**
 * Fetch all students from the server and refresh the UI.
 * Time Complexity: O(n) – renders every row.
 */
async function loadStudents() {
    showLoading(true);
    try {
        const result = await apiFetch('/api/students');
        allStudents       = result.data;
        displayedStudents = [...allStudents];
        renderTable(displayedStudents);
        updateStats(allStudents);
        setViewLabel('All Students', 'primary');
    } catch (err) {
        showToast('Gagal memuat data: ' + err.message, 'danger');
        showLoading(false);
    }
}

/**
 * Render the students array into the HTML table.
 * Handles empty, loading, and populated states.
 *
 * @param {Array} students - Array of student plain-objects (from to_dict)
 */
function renderTable(students) {
    const tbody      = document.getElementById('students-tbody');
    const tableWrap  = document.getElementById('table-wrapper');
    const emptyState = document.getElementById('empty-state');
    const badge      = document.getElementById('table-badge');

    showLoading(false);
    badge.textContent = students.length;

    if (students.length === 0) {
        tableWrap.classList.add('d-none');
        emptyState.classList.remove('d-none');
        return;
    }

    emptyState.classList.add('d-none');
    tableWrap.classList.remove('d-none');

    const isAdmin = window.IS_ADMIN === true || window.IS_ADMIN === 'true';

    tbody.innerHTML = students.map((s, i) => `
        <tr>
            <td class="text-muted small">${i + 1}</td>
            <td><code class="small">${s.student_id}</code></td>
            <td class="fw-semibold">${esc(s.name)}</td>
            <td>${s.age}</td>
            <td class="small text-muted">${esc(s.email)}</td>
            <td class="small">${esc(s.phone)}</td>
            <td>${esc(s.major)}</td>
            <td><span class="gpa-badge ${gpaClass(s.gpa)}">${s.gpa.toFixed(2)}</span></td>
            <td><span class="badge bg-secondary">${s.grade_letter}</span></td>
            ${isAdmin ? `
            <td class="text-center" style="white-space:nowrap">
                <button class="btn btn-sm btn-outline-primary me-1 py-0 px-1"
                        title="View details" onclick="openViewModal('${s.student_id}')">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-warning me-1 py-0 px-1"
                        title="Edit" onclick="openEditModal('${s.student_id}')">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger py-0 px-1"
                        title="Delete" onclick="openDeleteModal('${s.student_id}', '${esc(s.name)}')">
                    <i class="bi bi-trash3"></i>
                </button>
            </td>
            ` : ''}
        </tr>
    `).join('');
}

/**
 * Recompute and display aggregate statistics.
 * @param {Array} students
 */
function updateStats(students) {
    const total = students.length;
    const navCount = document.getElementById('nav-count');
    navCount.textContent = `${total} mahasiswa`;
}

/* ═══════════════════════════════ Add Modal ══════════════════════════════════ */

/** Open the Add Student modal with a blank form. */
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

/* ═══════════════════════════════ Edit Modal ═════════════════════════════════ */

/**
 * Open the Edit Student modal pre-filled with the student's current data.
 * @param {string} student_id
 */
function openEditModal(student_id) {
    const s = findStudent(student_id);
    if (!s) return;

    editingId = student_id;

    document.getElementById('modal-title').innerHTML =
        '<i class="bi bi-pencil me-1"></i> Edit Mahasiswa';
    document.getElementById('submit-btn').innerHTML =
        '<i class="bi bi-floppy me-1"></i> Simpan Perubahan';
    hideFormErrors();

    // Populate form fields
    document.getElementById('f-student_id').value    = s.student_id;
    document.getElementById('f-student_id').disabled = true;  // ID is immutable
    document.getElementById('f-name').value           = s.name;
    document.getElementById('f-age').value            = s.age;
    document.getElementById('f-email').value          = s.email;
    document.getElementById('f-phone').value          = s.phone;
    document.getElementById('f-major').value          = s.major;
    document.getElementById('f-gpa').value            = s.gpa;
    document.getElementById('f-address').value        = s.address || '';

    studentModal.show();
}

/* ═══════════════════════════════ Form Submit ════════════════════════════════ */

/**
 * Handle Add / Edit form submission.
 * Sends the payload to the server; displays validation errors inline.
 * @param {Event} e - Form submit event
 */
async function submitStudentForm(e) {
    e.preventDefault();
    hideFormErrors();

    const payload = {
        student_id: document.getElementById('f-student_id').value.trim(),
        name:       document.getElementById('f-name').value.trim(),
        age:        parseInt(document.getElementById('f-age').value, 10),
        email:      document.getElementById('f-email').value.trim(),
        phone:      document.getElementById('f-phone').value.trim(),
        major:      document.getElementById('f-major').value.trim(),
        gpa:        parseFloat(document.getElementById('f-gpa').value),
        address:    document.getElementById('f-address').value.trim(),
    };

    const btn = document.getElementById('submit-btn');
setButtonLoading(btn, true, 'Menyimpan…');

    try {
        if (editingId) {
            await apiFetch(`/api/students/${editingId}`, {
                method: 'PUT',
                body:   JSON.stringify(payload),
            });
            showToast(`Mahasiswa "${payload.name}" berhasil diperbarui.`, 'success');
        } else {
            await apiFetch('/api/students', {
                method: 'POST',
                body:   JSON.stringify(payload),
            });
            showToast(`Mahasiswa "${payload.name}" berhasil ditambahkan.`, 'success');
        }
        studentModal.hide();
        await loadStudents();

    } catch (err) {
        // Show server-side validation errors inside the modal
        showFormErrors(err.message.split('\n'));
    } finally {
        const label = editingId ? 'Simpan Perubahan' : 'Simpan';
        setButtonLoading(btn, false, `<i class="bi bi-floppy me-1"></i> ${label}`);
    }
}

/* ═══════════════════════════════ Delete ════════════════════════════════════ */

/**
 * Open the Delete confirmation modal.
 * @param {string} student_id
 * @param {string} name
 */
function openDeleteModal(student_id, name) {
    deleteTargetId = student_id;
    document.getElementById('delete-student-name').textContent = name;
    deleteModal.show();
}

/** Execute the deletion after user confirms. */
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

/* ═══════════════════════════════ View Modal ═════════════════════════════════ */

/**
 * Open the read-only Student Details modal.
 * @param {string} student_id
 */
function openViewModal(student_id) {
    const s = findStudent(student_id);
    if (!s) return;

    const rows = [
        ['Usia',          s.age],
        ['Email',         esc(s.email)],
        ['Telepon',       esc(s.phone)],
        ['Jurusan',       esc(s.major)],
        ['IPK',           `<span class="gpa-badge ${gpaClass(s.gpa)}">${s.gpa.toFixed(2)}</span>`],
        ['Nilai',         `<span class="badge bg-secondary">${s.grade_letter}</span>`],
        ['Alamat',        esc(s.address) || '<span class="text-muted">—</span>'],
        ['Terdaftar',     s.created_at ? new Date(s.created_at).toLocaleString() : '—'],
    ].map(([label, val]) =>
        `<div class="detail-row">
            <span class="detail-label">${label}</span>
            <span class="detail-value">${val}</span>
        </div>`
    ).join('');

    document.getElementById('view-modal-body').innerHTML = `
        <div class="d-flex align-items-center gap-3 mb-4">
            <div class="avatar-circle">${esc(s.name.charAt(0).toUpperCase())}</div>
            <div>
                <h5 class="mb-0 fw-bold">${esc(s.name)}</h5>
                <small class="text-muted"><code>${s.student_id}</code></small>
            </div>
        </div>
        ${rows}
    `;
    viewModal.show();
}

/* ═══════════════════════════════ Search ═════════════════════════════════════ */

/**
 * Execute a search request against the server and render results.
 * @param {Event} e - Form submit event
 */
async function doSearch(e) {
    e.preventDefault();

    const query = document.getElementById('search-query').value.trim();
    const field = document.getElementById('search-field').value;
    const algo  = document.getElementById('search-algorithm').value;

    if (!query) return;

    showLoading(true);
    try {
        const url    = `/api/students/search?query=${encodeURIComponent(query)}&field=${field}&algorithm=${algo}`;
        const result = await apiFetch(url);

        displayedStudents = result.data;
        renderTable(displayedStudents);
        setViewLabel(`Pencarian: "${query}"`, 'info');

        const matchType = algo === 'binary' ? 'prefiks (diawali dengan)' : 'substring (mengandung)';
        const info = document.getElementById('search-result-info');
        info.innerHTML =
            `<i class="bi bi-info-circle me-1"></i>
             Algoritma: <strong>${result.algorithm}</strong>&nbsp;|&nbsp;
             Kecocokan: <strong>${matchType}</strong>&nbsp;|&nbsp;
             Terbaik: <code>${result.complexity.best}</code>&nbsp;
             Rata-rata: <code>${result.complexity.avg}</code>&nbsp;
             Terburuk: <code>${result.complexity.worst}</code>&nbsp;|&nbsp;
             Waktu: <strong>${result.elapsed_ms} ms</strong>&nbsp;|&nbsp;
             Ditemukan: <strong>${result.count}</strong> hasil`;
        info.classList.remove('d-none');

    } catch (err) {
        showToast('Pencarian gagal: ' + err.message, 'danger');
        showLoading(false);
    }
}

/** Update the algorithm hint text based on selected algorithm. */
function updateAlgoHint() {
    const algo = document.getElementById('search-algorithm').value;
    const hint = document.getElementById('algo-hint');
    if (algo === 'binary') {
        hint.innerHTML = 'Mencocokkan data yang <strong>diawali dengan</strong> kata kunci (prefiks saja).';
    } else {
        hint.innerHTML = 'Mencocokkan data yang <strong>mengandung</strong> kata kunci di mana saja.';
    }
}

/** Reset the search UI and show all students. */
function clearSearch() {
    document.getElementById('search-form').reset();
    document.getElementById('search-result-info').classList.add('d-none');
    displayedStudents = [...allStudents];
    renderTable(displayedStudents);
    setViewLabel('Semua Mahasiswa', 'primary');
}

/* ═══════════════════════════════ Sort ═══════════════════════════════════════ */

/**
 * Execute a sort request against the server and render results.
 * @param {Event} e - Form submit event
 */
async function doSort(e) {
    e.preventDefault();

    const field = document.getElementById('sort-field').value;
    const algo  = document.getElementById('sort-algorithm').value;
    const order = document.getElementById('sort-order').value;

    showLoading(true);
    try {
        const url    = `/api/students/sort?algorithm=${algo}&field=${field}&order=${order}`;
        const result = await apiFetch(url);

        displayedStudents = result.data;
        renderTable(displayedStudents);

        const dir = order === 'asc' ? '↑' : '↓';
        setViewLabel(`Diurutkan: ${field} ${dir} (${algo})`, 'warning');

        const info = document.getElementById('sort-result-info');
        info.innerHTML =
            `<i class="bi bi-info-circle me-1"></i>
             Algoritma: <strong>${result.algorithm}</strong>&nbsp;|&nbsp;
             Waktu: <code>${result.time_complexity}</code>&nbsp;
             Ruang: <code>${result.space_complexity}</code>&nbsp;|&nbsp;
             Durasi: <strong>${result.elapsed_ms} ms</strong>`;
        info.classList.remove('d-none');

    } catch (err) {
        showToast('Pengurutan gagal: ' + err.message, 'danger');
        showLoading(false);
    }
}

/** Reset sort UI and restore original order. */
function clearSort() {
    document.getElementById('sort-form').reset();
    document.getElementById('sort-result-info').classList.add('d-none');
    displayedStudents = [...allStudents];
    renderTable(displayedStudents);
    setViewLabel('Semua Mahasiswa', 'primary');
}

/* ═══════════════════════════════ UI Utilities ═══════════════════════════════ */

/**
 * Toggle the loading spinner vs. the data table.
 * @param {boolean} show
 */
function showLoading(show) {
    document.getElementById('loading-state').classList.toggle('d-none', !show);
    if (show) {
        document.getElementById('table-wrapper').classList.add('d-none');
        document.getElementById('empty-state').classList.add('d-none');
    }
}

/**
 * Update the "view mode" badge above the table.
 * @param {string} text    - Label text
 * @param {string} variant - Bootstrap colour variant (primary, info, warning …)
 */
function setViewLabel(text, variant) {
    const el = document.getElementById('view-mode-label');
    el.className  = `badge bg-${variant} px-3`;
    el.textContent = text;
}

/**
 * Disable a button and show a spinner while an async operation runs.
 * @param {HTMLButtonElement} btn
 * @param {boolean}           loading
 * @param {string}            label - HTML string for the restored label
 */
function setButtonLoading(btn, loading, label) {
    if (loading) {
        btn.disabled   = true;
        btn.innerHTML  = '<span class="spinner-border spinner-border-sm me-1"></span>…';
    } else {
        btn.disabled  = false;
        btn.innerHTML = label;
    }
}

/** Show inline validation errors inside the student modal. */
function showFormErrors(messages) {
    const el = document.getElementById('form-errors');
    el.innerHTML = messages.map(m => `<div>• ${esc(m)}</div>`).join('');
    el.classList.remove('d-none');
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/** Hide the inline error block inside the student modal. */
function hideFormErrors() {
    document.getElementById('form-errors').classList.add('d-none');
}

/* ─────────────────────── DOM helpers ──────────────────────────────────────── */

/**
 * Find a student object by ID from either the full or displayed list.
 * @param {string} student_id
 * @returns {object|undefined}
 */
function findStudent(student_id) {
    return (
        allStudents.find(s => s.student_id === student_id) ||
        displayedStudents.find(s => s.student_id === student_id)
    );
}

/**
 * Return the CSS class name for a GPA badge based on the GPA value.
 * @param {number} gpa
 * @returns {string}
 */
function gpaClass(gpa) {
    if (gpa >= 3.0) return 'gpa-a';
    if (gpa >= 2.5) return 'gpa-b';
    if (gpa >= 2.0) return 'gpa-c';
    return 'gpa-d';
}

/**
 * Return the CSS class name for a status badge.
 * @param {string} status
 * @returns {string}
 */
function statusClass(status) {
    const map = {
        "Dean's List":         'status-deans',
        "Good Standing":       'status-good',
        "Academic Probation":  'status-probation',
        "Academic Suspension": 'status-suspension',
    };
    return map[status] || 'bg-secondary text-white';
}

/**
 * Escape HTML special characters to prevent XSS.
 * @param {*} str
 * @returns {string}
 */
function esc(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/* ─────────────────────── Toast notifications ───────────────────────────────── */

const _TOAST_ICONS = {
    success: 'bi-check-circle-fill',
    danger:  'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info:    'bi-info-circle-fill',
};

/**
 * Display a self-dismissing Bootstrap Toast notification.
 * @param {string} message
 * @param {'success'|'danger'|'warning'|'info'} type
 */
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const id        = `toast-${Date.now()}`;
    const icon      = _TOAST_ICONS[type] || 'bi-info-circle-fill';

    container.insertAdjacentHTML('beforeend', `
        <div id="${id}" class="toast align-items-center text-bg-${type} border-0"
             role="alert" aria-live="assertive">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="bi ${icon}"></i>
                    ${esc(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `);

    const toastEl = document.getElementById(id);
    const toast   = new bootstrap.Toast(toastEl, { delay: 3500 });
    toast.show();
    // Clean up DOM after the toast hides
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

/* ═══════════════════════════════ Initialise ═════════════════════════════════ */

document.addEventListener('DOMContentLoaded', loadStudents);
