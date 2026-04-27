/* ================================================================
   Nexus HR — Internal Employee Portal
   script.js  |  Frontend application logic
================================================================ */

'use strict';

/* ── state ───────────────────────────────────────────────────── */
let session = null;   // { emp_id, name, role, dept, avatar }


/* ── currency formatter ──────────────────────────────────────── */
function inr(n) {
  return '₹' + Number(n).toLocaleString('en-IN');
}

function fmtDate(d) {
  if (!d) return '—';
  const [y, m, day] = d.split('-');
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${parseInt(day)} ${months[parseInt(m)-1]} ${y}`;
}


/* ── api helper ──────────────────────────────────────────────── */
async function api(method, path, body) {
  const opts = { method, headers: {'Content-Type':'application/json'}, credentials:'same-origin' };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(path, opts);
  const d = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data: d };
}


/* ── toast ───────────────────────────────────────────────────── */
function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}


/* ================================================================
   AUTH
================================================================ */

async function doLogin() {
  const username = document.getElementById('f-username').value.trim();
  const password = document.getElementById('f-password').value.trim();
  const errEl    = document.getElementById('login-error');

  errEl.style.display = 'none';
  if (!username || !password) {
    errEl.textContent   = 'Please enter your username and password.';
    errEl.style.display = 'block';
    return;
  }

  const btn = document.getElementById('btn-login');
  btn.textContent = 'Signing in…';
  btn.disabled    = true;

  const { ok, data } = await api('POST', '/api/auth/login', { username, password });

  btn.textContent = 'Sign In';
  btn.disabled    = false;

  if (!ok) {
    errEl.textContent   = data.error || 'Login failed. Please try again.';
    errEl.style.display = 'block';
    return;
  }

  session = data;
  document.getElementById('login-page').style.display = 'none';
  document.getElementById('app').style.display        = 'block';
  bootApp();
}

async function doLogout() {
  await api('POST', '/api/auth/logout');
  session = null;
  document.getElementById('app').style.display        = 'none';
  document.getElementById('login-page').style.display = 'flex';
  document.getElementById('f-username').value = '';
  document.getElementById('f-password').value = '';
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('f-password')
    ?.addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });
});


/* ================================================================
   BOOT
================================================================ */

function bootApp() {
  const initials = session.name.split(' ').map(w => w[0]).join('');

  document.getElementById('topbar-avatar').textContent = initials;
  document.getElementById('topbar-name').textContent   = session.name;
  document.getElementById('topbar-role').textContent   = session.role;
  document.getElementById('topbar-greeting').textContent =
    `Good ${hour()}, ${session.name.split(' ')[0]}`;

  showPanel('dashboard', document.querySelector('.nav-item[data-panel="dashboard"]'));
}

function hour() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}


/* ================================================================
   NAVIGATION
================================================================ */

function showPanel(name, el) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const panel = document.getElementById('panel-' + name);
  if (panel) panel.classList.add('active');
  if (el)    el.classList.add('active');

  const loaders = {
    dashboard: loadDashboard,
    profile:   () => loadProfile(session.emp_id),
    payslip:   loadPayslip,
    documents: () => loadDocuments(session.emp_id),
    leave:     () => loadLeave(session.emp_id),
    directory: loadDirectory,
  };
  if (loaders[name]) loaders[name]();
}

function navClick(el) {
  const name = el.getAttribute('data-panel');
  showPanel(name, el);
}


/* ================================================================
   DASHBOARD
================================================================ */

async function loadDashboard() {
  const { ok, data } = await api('GET', '/api/dashboard');
  if (!ok) return;

  document.getElementById('dash-pay').textContent =
    data.latest_pay ? inr(data.latest_pay.net_pay) : '—';
  document.getElementById('dash-pay-period').textContent =
    data.latest_pay ? `${data.latest_pay.month} ${data.latest_pay.year}` : '';
  document.getElementById('dash-leaves').textContent  = data.pending_leaves;
  document.getElementById('dash-docs').textContent    = data.doc_count;

  const ann = document.getElementById('announcements-list');
  ann.innerHTML = data.announcements.map(a => `
    <div class="announcement">
      <div class="announcement-header">
        <div>
          <div class="announcement-title">${a.title}</div>
          <div class="announcement-meta">
            Posted by ${a.posted_by} &nbsp;·&nbsp; ${fmtDate(a.posted_on)}
            &nbsp;·&nbsp; <span class="badge badge-blue" style="font-size:10px">${a.category}</span>
          </div>
        </div>
      </div>
      <div class="announcement-body">${a.body}</div>
    </div>`).join('');
}


/* ================================================================
   PROFILE
================================================================ */

async function loadProfile(empId) {
  const box = document.getElementById('profile-box');
  box.innerHTML = '<div class="loading-state">Loading…</div>';

  const { ok, data } = await api('GET', `/api/employees/${empId}/profile`);
  if (!ok) { box.innerHTML = '<div class="loading-state">Could not load profile.</div>'; return; }

  const roleLabel = { employee:'Employee', manager:'Manager', director:'Director', ceo:'Chief Executive' };

  box.innerHTML = `
    <div class="card" style="overflow:hidden">
      <div class="profile-hero">
        <div class="profile-hero-avatar">${data.avatar_initials}</div>
        <div>
          <div class="profile-hero-name">${data.name}</div>
          <div class="profile-hero-title">${data.designation} &nbsp;·&nbsp; ${data.dept}</div>
          <div class="profile-hero-meta">
            <span class="profile-hero-badge">${data.emp_id}</span>
            <span class="profile-hero-badge">${roleLabel[data.role] || data.role}</span>
            <span class="profile-hero-badge">Joined ${fmtDate(data.joining_date)}</span>
          </div>
        </div>
      </div>

      <div style="padding:0">
        <div style="padding:16px 20px; border-bottom:1px solid var(--border)">
          <div class="section-label">Contact Information</div>
          <div class="profile-fields">
            <div class="profile-field">
              <div class="profile-field-label">Work Email</div>
              <div class="profile-field-value">${data.email}</div>
            </div>
            <div class="profile-field">
              <div class="profile-field-label">Personal Email</div>
              <div class="profile-field-value">${data.personal_email || '—'}</div>
            </div>
            <div class="profile-field">
              <div class="profile-field-label">Mobile</div>
              <div class="profile-field-value">${data.phone || '—'}</div>
            </div>
            <div class="profile-field">
              <div class="profile-field-label">Phone Extension</div>
              <div class="profile-field-value mono">${data.phone_ext || '—'}</div>
            </div>
          </div>
        </div>

        <div style="padding:16px 20px; border-bottom:1px solid var(--border)">
          <div class="section-label">Personal Details</div>
          <div class="profile-fields">
            <div class="profile-field">
              <div class="profile-field-label">Date of Birth</div>
              <div class="profile-field-value">${fmtDate(data.dob)}</div>
            </div>
            <div class="profile-field">
              <div class="profile-field-label">Blood Group</div>
              <div class="profile-field-value">${data.blood_group || '—'}</div>
            </div>
            <div class="profile-field" style="grid-column:1/-1">
              <div class="profile-field-label">Home Address</div>
              <div class="profile-field-value">${data.address ? `${data.address}, ${data.city}, ${data.state}` : '—'}</div>
            </div>
          </div>
        </div>

        <div style="padding:16px 20px">
          <div class="section-label">Emergency Contact</div>
          <div class="profile-fields">
            <div class="profile-field">
              <div class="profile-field-label">Name</div>
              <div class="profile-field-value">${data.emergency_contact || '—'}</div>
            </div>
            <div class="profile-field">
              <div class="profile-field-label">Phone</div>
              <div class="profile-field-value">${data.emergency_phone || '—'}</div>
            </div>
          </div>
        </div>
      </div>
    </div>`;
}


/* ================================================================
   PAYSLIP
================================================================ */

let allPayslips = [];

async function loadPayslip() {
  const box = document.getElementById('payslip-box');
  box.innerHTML = '<div class="loading-state">Loading payslips…</div>';

  const { ok, data } = await api('GET', `/api/employees/${session.emp_id}/payslips`);
  if (!ok) { box.innerHTML = '<div class="loading-state">No payslip records found.</div>'; return; }

  allPayslips = data;

  // Populate month selector
  const sel = document.getElementById('payslip-selector');
  sel.innerHTML = data.map((p, i) =>
    `<option value="${i}">${p.month} ${p.year}</option>`
  ).join('');
  sel.style.display = 'block';

  renderPayslip(data[0]);
}

function onPayslipChange(sel) {
  renderPayslip(allPayslips[sel.value]);
}

function renderPayslip(p) {
  const box = document.getElementById('payslip-box');
  box.innerHTML = `
    <div class="card" style="overflow:hidden">
      <div class="payslip-header">
        <div>
          <div class="payslip-company">Nexus Corporation Pvt. Ltd.</div>
          <div class="payslip-emp-info">${session.name} &nbsp;·&nbsp; ${session.emp_id} &nbsp;·&nbsp; ${session.dept}</div>
        </div>
        <div class="payslip-period">
          <div class="payslip-period-label">Pay Period</div>
          <div class="payslip-period-value">${p.month} ${p.year}</div>
          <div class="text-xs text-muted mt-4">${p.working_days} working days${p.lop_days ? ` · ${p.lop_days} LOP` : ''}</div>
        </div>
      </div>
      <div class="payslip-divider"></div>

      <div class="payslip-grid">
        <div class="payslip-col">
          <div class="payslip-col-title">Earnings</div>
          <div class="payslip-row"><span class="payslip-row-label">Basic Salary</span><span class="payslip-row-amount credit">${inr(p.basic)}</span></div>
          <div class="payslip-row"><span class="payslip-row-label">House Rent Allowance</span><span class="payslip-row-amount credit">${inr(p.hra)}</span></div>
          <div class="payslip-row"><span class="payslip-row-label">Conveyance Allowance</span><span class="payslip-row-amount credit">${inr(p.conveyance)}</span></div>
          <div class="payslip-row"><span class="payslip-row-label">Medical Allowance</span><span class="payslip-row-amount credit">${inr(p.medical)}</span></div>
          <div class="payslip-row"><span class="payslip-row-label">Special Allowance</span><span class="payslip-row-amount credit">${inr(p.special)}</span></div>
          <div class="payslip-row" style="border-top:2px solid var(--border); margin-top:6px; padding-top:10px">
            <span class="payslip-row-label text-bold">Gross Earnings</span>
            <span class="payslip-row-amount text-bold">${inr(p.gross)}</span>
          </div>
        </div>

        <div class="payslip-col">
          <div class="payslip-col-title">Deductions</div>
          <div class="payslip-row"><span class="payslip-row-label">Provident Fund (Employee)</span><span class="payslip-row-amount debit">${inr(p.pf_emp)}</span></div>
          <div class="payslip-row"><span class="payslip-row-label">Provident Fund (Employer)</span><span class="payslip-row-amount debit">${inr(p.pf_employer)}</span></div>
          <div class="payslip-row"><span class="payslip-row-label">Income Tax (TDS)</span><span class="payslip-row-amount debit">${inr(p.income_tax)}</span></div>
          <div class="payslip-row"><span class="payslip-row-label">Professional Tax</span><span class="payslip-row-amount debit">${inr(p.professional_tax)}</span></div>
          <div class="payslip-row" style="border-top:2px solid var(--border); margin-top:6px; padding-top:10px">
            <span class="payslip-row-label text-bold">Total Deductions</span>
            <span class="payslip-row-amount debit text-bold">${inr(p.total_deductions)}</span>
          </div>
        </div>
      </div>

      <div class="payslip-net">
        <div>
          <div class="payslip-net-label">Net Pay for ${p.month} ${p.year}</div>
          <div class="text-xs text-muted mt-4">Credited to ${p.bank_name} &nbsp;·&nbsp; A/C ${p.bank_account}</div>
        </div>
        <div class="payslip-net-amount">${inr(p.net_pay)}</div>
      </div>
    </div>`;
}


/* ================================================================
   DOCUMENTS
================================================================ */

async function loadDocuments(empId) {
  const box = document.getElementById('documents-box');
  box.innerHTML = '<div class="loading-state">Loading documents…</div>';

  const { ok, data } = await api('GET', `/api/employees/${empId}/documents`);
  if (!ok || !data.length) {
    box.innerHTML = `<div class="empty-state"><p>No documents found.</p></div>`;
    return;
  }

  const catIcon = {
    'Offer Letter':'📄', 'Appointment':'📋', 'ID Proof':'🪪',
    'Appraisal':'⭐', 'Salary Revision':'💰', 'Promotion':'🏅',
    'Medical':'🏥', 'Background':'🔍', 'ESOP':'📈',
    'Salary Structure':'💼', 'Legal Agreement':'⚖️',
    'Contract':'📝', 'Board Document':'🏛️', 'HR Document':'📂',
  };

  const rows = data.map(d => `
    <tr>
      <td>
        <div class="flex gap-8">
          <span style="font-size:18px">${catIcon[d.category] || '📄'}</span>
          <div>
            <div style="font-weight:500;color:var(--text)">${d.title}</div>
            <div class="text-xs text-muted">${d.file_name}</div>
          </div>
        </div>
      </td>
      <td><span class="badge badge-gray">${d.category}</span></td>
      <td class="text-muted">${fmtDate(d.uploaded_on)}</td>
      <td class="text-muted">${d.file_size}</td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="toast('Download feature is restricted in this environment.')">
          Download
        </button>
      </td>
    </tr>`).join('');

  box.innerHTML = `
    <div class="card">
      <div class="card-header">
        <span class="card-title">My Documents (${data.length})</span>
        <span class="text-xs text-muted">Managed by HR — Nexus Corp</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Document</th><th>Category</th><th>Uploaded</th><th>Size</th><th></th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}


/* ================================================================
   LEAVE
================================================================ */

async function loadLeave(empId) {
  const box = document.getElementById('leave-box');

  const { ok, data } = await api('GET', `/api/employees/${empId}/leaves`);
  if (!ok) { box.innerHTML = '<div class="loading-state">Could not load records.</div>'; return; }

  const approved = data.filter(l => l.status === 'Approved').reduce((s, l) => s + l.days, 0);
  const pending  = data.filter(l => l.status === 'Pending').length;

  const statusBadge = s => ({
    Approved:'<span class="badge badge-green">Approved</span>',
    Pending: '<span class="badge badge-yellow">Pending</span>',
    Rejected:'<span class="badge badge-red">Rejected</span>',
  }[s] || s);

  const rows = data.map(l => `
    <tr>
      <td><span class="badge badge-blue">${l.leave_type}</span></td>
      <td>${fmtDate(l.from_date)}</td>
      <td>${fmtDate(l.to_date)}</td>
      <td style="text-align:center"><strong>${l.days}</strong></td>
      <td class="text-muted">${l.reason || '—'}</td>
      <td>${statusBadge(l.status)}</td>
      <td class="text-muted text-xs">${fmtDate(l.applied_on)}</td>
    </tr>`).join('');

  box.innerHTML = `
    <div class="card mb-24">
      <div class="leave-balance-row">
        <div class="leave-balance-item">
          <div class="leave-balance-count">${data.length}</div>
          <div class="leave-balance-type">Total Applications</div>
          <div class="leave-balance-avail">This financial year</div>
        </div>
        <div class="leave-balance-item">
          <div class="leave-balance-count" style="color:var(--success)">${approved}</div>
          <div class="leave-balance-type">Days Taken</div>
          <div class="leave-balance-avail">Approved leaves</div>
        </div>
        <div class="leave-balance-item">
          <div class="leave-balance-count" style="color:var(--warning)">${pending}</div>
          <div class="leave-balance-type">Pending</div>
          <div class="leave-balance-avail">Awaiting approval</div>
        </div>
        <div class="leave-balance-item">
          <div class="leave-balance-count">21</div>
          <div class="leave-balance-type">Annual Balance</div>
          <div class="leave-balance-avail">FY 2024-25</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-title">Leave History</span>
        <button class="btn btn-primary btn-sm" onclick="openLeaveModal()">
          Apply for Leave
        </button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Type</th><th>From</th><th>To</th><th style="text-align:center">Days</th><th>Reason</th><th>Status</th><th>Applied</th></tr>
          </thead>
          <tbody>${rows.length ? rows : '<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--text-3)">No leave records found</td></tr>'}</tbody>
        </table>
      </div>
    </div>`;
}

function openLeaveModal()  { document.getElementById('leave-modal').classList.add('open'); }
function closeLeaveModal() { document.getElementById('leave-modal').classList.remove('open'); }

async function submitLeave() {
  const leave_type = document.getElementById('lv-type').value;
  const from_date  = document.getElementById('lv-from').value;
  const to_date    = document.getElementById('lv-to').value;
  const reason     = document.getElementById('lv-reason').value.trim();

  if (!from_date || !to_date || !reason) {
    toast('Please fill all required fields.');
    return;
  }

  const from = new Date(from_date), to = new Date(to_date);
  const days = Math.max(1, Math.round((to - from) / 86400000) + 1);

  const { ok } = await api('POST', `/api/employees/${session.emp_id}/leaves`, {
    leave_type, from_date, to_date, days, reason
  });

  if (ok) {
    closeLeaveModal();
    toast('Leave application submitted successfully.');
    loadLeave(session.emp_id);
  }
}


/* ================================================================
   EMPLOYEE DIRECTORY
================================================================ */

async function loadDirectory() {
  const box = document.getElementById('directory-box');
  box.innerHTML = '<div class="loading-state">Loading directory…</div>';

  const { ok, data } = await api('GET', '/api/directory');
  if (!ok) return;

  const rows = data.map(e => `
    <tr>
      <td>
        <div class="flex gap-12">
          <div class="emp-row-avatar">${e.emp_id.replace('EMP','').replace('0','')}</div>
          <div>
            <div style="font-weight:600;color:var(--text)">${e.name}</div>
            <div class="text-xs text-muted">${e.email}</div>
          </div>
        </div>
      </td>
      <td class="text-mono text-xs text-muted">${e.emp_id}</td>
      <td>${e.dept}</td>
      <td><span class="badge badge-gray" style="text-transform:capitalize">${e.role}</span></td>
      <td class="text-muted">${e.phone_ext || '—'}</td>
    </tr>`).join('');

  box.innerHTML = `
    <div class="card">
      <div class="card-header">
        <span class="card-title">Employee Directory (${data.length})</span>
        <span class="text-xs text-muted">All active employees — Nexus Corporation</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Employee</th><th>Employee ID</th><th>Department</th><th>Role</th><th>Ext.</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>`;
}
