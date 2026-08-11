# -*- coding: utf-8 -*-
"""MedIQ Pro page bodies — Part A: admin + manager."""
from frontend_lib import icon, stat_card, panel, badge, pagination, empty_row

A = {"admin": {}, "manager": {}}

# =====================================================================
# ADMIN — dashboard
# =====================================================================
A["admin"]["dashboard.html"] = {
"title": "Admin Dashboard",
"body": """
<div class="stat-grid">
  {s1}{s2}{s3}{s4}
</div>
<div class="panel-grid">
  <div>
    {panel_health}
    <div class="mt-5">{panel_activity}</div>
  </div>
  <div>
    {panel_quick}
    <div class="mt-5">{panel_signups}</div>
  </div>
</div>
""".format(
    s1=stat_card("users", '<span id="statUsers">–</span>', "Total Users", "+2 this week", "up"),
    s2=stat_card("activity", "34", "Active Sessions", "12 in last hour", "up", "color-success"),
    s3=stat_card("zap", "99.9%", "System Uptime", "30 days", "up", "color-info"),
    s4=stat_card("alert", "3", "Errors (24h)", "2 resolved", "down", "color-danger"),
    panel_health=panel("System Health",
        '<div id="healthList"></div>',
        sub='<div class="sub">Live status of core services</div>'),
    panel_activity=panel("Recent Activity",
        '<div id="activityFeed"><div class="empty-state">Loading activity…</div></div>',
        actions='<a class="btn btn-secondary btn-sm" href="audit-logs.html">View all</a>'),
    panel_quick=panel("Quick Actions",
        '<div class="quick-actions" style="grid-template-columns:1fr;margin:0">'
        '<a class="quick-action" href="users.html"><div class="qa-icon" style="background:#EFF6FF;color:#1A56DB">' + icon("users") + '</div><div><div class="qa-title">Add User</div><div class="qa-sub">Create a new account</div></div></a>'
        '<a class="quick-action" href="audit-logs.html"><div class="qa-icon" style="background:#F0F9FF;color:#0369A1">' + icon("list") + '</div><div><div class="qa-title">View Logs</div><div class="qa-sub">Audit trail &amp; events</div></div></a>'
        '<a class="quick-action" href="settings.html"><div class="qa-icon" style="background:#FFFBEB;color:#D97706">' + icon("settings") + '</div><div><div class="qa-title">System Settings</div><div class="qa-sub">Configure the hospital</div></div></a>'
        '<a class="quick-action" href="ai-config.html"><div class="qa-icon" style="background:#F5F3FF;color:#7C3AED">' + icon("cpu") + '</div><div><div class="qa-title">AI Configuration</div><div class="qa-sub">Manage AI modules</div></div></a>'
        '</div>'),
    panel_signups=panel("New Signups — Last 7 Days",
        '<div class="chart-box" id="signupsChart"></div>')
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("admin"); initLayout(); loadPageData();
});
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.USERS).then(r => {
    if (r.ok) document.getElementById("statUsers").textContent = r.data.items.length;
  });
  // System health panel
  const health = [
    { name: "FastAPI backend", icon: "server", ok: true, detail: "All endpoints responding" },
    { name: "Supabase database", icon: "database", ok: true, detail: "Connection pool healthy" },
    { name: "AI modules (7)", icon: "cpu", ok: true, detail: "7/7 models loaded & online" }
  ];
  document.getElementById("healthList").innerHTML = health.map(h => `
    <div class="feed-item"><div class="feed-icon" style="background:#F3F4F6;color:#6B7280">${ICONS[h.icon]}</div>
    <div class="feed-text"><strong>${h.name}</strong><div class="feed-time">${h.detail}</div></div>
    <span class="health-dot ${h.ok ? "ok" : "bad"}"></span></div>`).join("");
  apiFetch(CONFIG.ENDPOINTS.AUDIT_LOGS).then(r => {
    if (!r.ok) return;
    const feed = document.getElementById("activityFeed");
    const icons = { login: ["key","info"], create: ["plus","success"], update: ["edit","warning"], delete: ["trash","danger"], backup: ["database","info"] };
    const colors = { login: "#EFF6FF", create: "#ECFDF5", update: "#FFFBEB", delete: "#FEF2F2", backup: "#F0F9FF" };
    const tints = { login: "#1A56DB", create: "#065F46", update: "#D97706", delete: "#DC2626", backup: "#0369A1" };
    feed.innerHTML = r.data.items.slice(0, 8).map(l => {
      const c = icons[l.action] || ["info","neutral"];
      return `<div class="feed-item">
        <div class="feed-icon" style="background:${colors[l.action]||"#F3F4F6"};color:${tints[l.action]||"#6B7280"}">${ICONS[l.action]||ICONS.info}</div>
        <div class="feed-text"><strong>${esc(l.user)}</strong> · ${esc(l.detail || l.action)}
          <div class="feed-time">${formatDateTime(l.ts)} · ${esc(l.ip)}</div></div>
        <span class="badge badge-${l.status==="success"?"success":"danger"}">${l.status}</span>
      </div>`;
    }).join("");
  });
  document.getElementById("signupsChart").innerHTML = barChart(
    [{label:"Mon",value:9},{label:"Tue",value:14},{label:"Wed",value:11},{label:"Thu",value:17},{label:"Fri",value:13},{label:"Sat",value:6},{label:"Sun",value:5}]
  );
}
""",
}

# =====================================================================
# ADMIN — users
# =====================================================================
A["admin"]["users.html"] = {
"title": "User Management",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="search-box">%s<input class="form-control" id="userSearch" placeholder="Search name, email…"></div>
    <div class="filters">
      <select class="form-control" id="filterRole" style="width:150px"><option value="">All roles</option><option>admin</option><option>manager</option><option>doctor</option><option>nurse</option><option>pharmacist</option><option>laboratory</option><option>reception</option><option>patient</option></select>
      <select class="form-control" id="filterStatus" style="width:140px"><option value="">All status</option><option>active</option><option>inactive</option></select>
      <button class="btn btn-secondary" id="btnExport"><span>%s</span> Export CSV</button>
      <button class="btn btn-primary" id="btnAddUser"><span>%s</span> Add User</button>
    </div>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="usersTable">
      <thead><tr>
        <th class="sortable">Name</th><th class="sortable">Email</th><th class="sortable">Role</th>
        <th class="sortable">Department</th><th class="sortable">Status</th><th class="sortable">Last Login</th>
        <th style="text-align:right">Actions</th>
      </tr></thead>
      <tbody id="usersBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), icon("download"), icon("plus"), pagination("usersPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("admin"); initLayout(); loadPageData();
});
let USERS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.USERS).then(r => {
    if (!r.ok) return;
    USERS = r.data.items;
    renderUsers();
    attachDataTable(document.getElementById("usersTable"), {
      searchInput: document.getElementById("userSearch"),
      pagerEl: document.getElementById("usersPager"),
      pageSize: 8,
      filterFn: (row) => {
        const role = document.getElementById("filterRole").value;
        const st = document.getElementById("filterStatus").value;
        if (role && !row.cells[2].textContent.includes(role)) return false;
        if (st && !row.cells[4].textContent.includes(st)) return false;
        return true;
      }
    });
  });
}
function renderUsers() {
  const body = document.getElementById("usersBody");
  if (!USERS.length) { body.innerHTML = emptyRow(7); return; }
  body.innerHTML = USERS.map(u => `<tr>
    <td><div class="flex" style="gap:10px"><span class="avatar-sm">${initialsOf(u.name)}</span><strong>${esc(u.name)}</strong></div></td>
    <td>${esc(u.email)}</td>
    <td><span class="badge badge-primary">${esc(u.role)}</span></td>
    <td>${esc(u.department)}</td>
    <td>${u.status === "active" ? badge("Active","success") : badge("Inactive","neutral")}</td>
    <td>${formatDateTime(u.last_login)}</td>
    <td><div class="actions">
      <button class="btn-icon primary" title="Edit" onclick="editUser('${u.id}')">${ICONS.edit}</button>
      <button class="btn-icon danger" title="Delete" onclick="deleteUser('${u.id}')">${ICONS.trash}</button>
    </div></td></tr>`).join("");
}
function userModal(u) {
  const isEdit = !!u;
  const roles = ["admin","manager","doctor","nurse","pharmacist","laboratory","reception","patient"].map(r =>
    `<option ${u && u.role===r ? "selected":""}>${r}</option>`).join("");
  openModal({
    title: isEdit ? "Edit User" : "Add New User",
    body: `
      <div class="form-row">
        <div class="form-group"><label>Full Name <span class="req">*</span></label><input class="form-control" id="mName" value="${u?esc(u.name):""}" required></div>
        <div class="form-group"><label>Email <span class="req">*</span></label><input class="form-control" type="email" id="mEmail" value="${u?esc(u.email):""}" required></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Password ${isEdit?"(leave blank to keep)":"<span class='req'>*</span>"}</label><input class="form-control" type="password" id="mPass" ${isEdit?"":"required"} placeholder="••••••••"></div>
        <div class="form-group"><label>Role <span class="req">*</span></label><select class="form-control" id="mRole">${roles}</select></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Department</label><input class="form-control" id="mDept" value="${u?esc(u.department):""}" placeholder="e.g. Internal Medicine"></div>
        <div class="form-group"><label>Status</label><select class="form-control" id="mStatus"><option ${!u||u.status==="active"?"selected":""}>active</option><option ${u&&u.status==="inactive"?"selected":""}>inactive</option></select></div>
      </div>`,
    footer: `<button class="btn btn-secondary" data-close2>Cancel</button><button class="btn btn-primary" id="saveUser">${isEdit?"Save Changes":"Create User"}</button>`
  }, {
    onMount: (ov) => {
      ov.querySelector("[data-close2]").onclick = () => ov.remove();
      ov.querySelector("#saveUser").onclick = () => {
        const name = ov.querySelector("#mName").value.trim();
        const email = ov.querySelector("#mEmail").value.trim();
        const role = ov.querySelector("#mRole").value;
        if (!name || !email) { showToast("Name and email are required","error"); return; }
        if (!isEdit && !ov.querySelector("#mPass").value) { showToast("Password is required","error"); return; }
        if (isEdit) {
          const target = USERS.find(x => x.id === u.id);
          target.name = name; target.email = email; target.role = role;
          target.department = ov.querySelector("#mDept").value; target.status = ov.querySelector("#mStatus").value;
          showToast("User updated successfully","success");
        } else {
          USERS.unshift({ id: uid("U"), name, email, role, department: ov.querySelector("#mDept").value || "—", status: ov.querySelector("#mStatus").value, last_login: "—" });
          showToast("User created successfully","success");
        }
        renderUsers(); ov.remove();
      };
    }
  });
}
function editUser(id) { userModal(USERS.find(u => u.id === id)); }
document.getElementById("btnAddUser").addEventListener("click", () => userModal(null));
document.getElementById("btnExport").addEventListener("click", () => {
  exportCSV("users.csv", ["Name","Email","Role","Department","Status","Last Login"],
    USERS.map(u => [u.name,u.email,u.role,u.department,u.status,u.last_login]));
  showToast("Users exported to CSV","success");
});
async function deleteUser(id) {
  const ok = await confirmDialog("Are you sure you want to delete this user? This action cannot be undone.");
  if (!ok) return;
  USERS = USERS.filter(u => u.id !== id);
  renderUsers();
  showToast("User deleted","success");
}
""",
}

# =====================================================================
# ADMIN — roles
# =====================================================================
A["admin"]["roles.html"] = {
"title": "Roles & Permissions",
"body": """
<div class="flex-between mb-4"><p class="page-intro" style="margin:0">Define what each role can access across the system.</p>
  <button class="btn btn-primary" id="btnAddRole"><span>%s</span> Add Role</button></div>
<div id="rolesGrid"></div>
""" % icon("plus"),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("admin"); initLayout(); loadPageData();
});
const ROLES = [
  { name: "admin", label: "Administrator", desc: "Full system control — users, settings, logs, AI config", icon: "shield", perms: {dashboard:1,users:1,patients:1,appointments:1,ai:1,settings:1} },
  { name: "manager", label: "General Manager", desc: "Executive oversight — analytics, reports, AI insights", icon: "chart", perms: {dashboard:1,users:0,patients:0,appointments:0,ai:1,settings:0} },
  { name: "doctor", label: "Doctor", desc: "Clinical care — consultations, prescriptions, AI diagnosis", icon: "stethoscope", perms: {dashboard:1,users:0,patients:1,appointments:1,ai:1,settings:0} },
  { name: "nurse", label: "Nurse", desc: "Patient care — vitals, medications, care plans", icon: "heart", perms: {dashboard:1,users:0,patients:1,appointments:0,ai:1,settings:0} },
  { name: "pharmacist", label: "Pharmacist", desc: "Medication & inventory — dispensing, forecasting", icon: "pill", perms: {dashboard:1,users:0,patients:0,appointments:0,ai:1,settings:0} },
  { name: "laboratory", label: "Laboratory", desc: "Test processing & AI result analysis", icon: "flask", perms: {dashboard:1,users:0,patients:0,appointments:0,ai:1,settings:0} },
  { name: "reception", label: "Receptionist", desc: "Front desk — registration, appointments, queue", icon: "users", perms: {dashboard:1,users:0,patients:1,appointments:1,ai:0,settings:0} },
  { name: "patient", label: "Patient", desc: "Self-service portal — records, results, bills, chatbot", icon: "user-check", perms: {dashboard:1,users:0,patients:0,appointments:1,ai:1,settings:0} }
];
const PERM_LABELS = { dashboard: "Dashboard", users: "User Management", patients: "Patient Records", appointments: "Appointments", ai: "AI Modules", settings: "Settings" };
function loadPageData() { renderRoles(); }
function renderRoles() {
  document.getElementById("rolesGrid").innerHTML = `<div class="stat-grid" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr))">
    ${ROLES.map(r => `<div class="card" style="display:flex;flex-direction:column;gap:12px">
      <div class="flex-between"><div class="flex" style="gap:12px"><div class="stat-icon">${ICONS[r.icon]}</div>
        <div><div style="font-weight:700;font-size:15px">${r.label}</div><div class="text-sm text-gray" style="color:#6B7280">${esc(r.desc)}</div></div></div>
        <span class="badge badge-neutral">${esc(r.name)}</span></div>
      <div class="flex wrap" style="gap:6px">${Object.entries(r.perms).map(([k,v]) => `<span class="badge badge-${v?"success":"default"}">${PERM_LABELS[k]}</span>`).join("")}</div>
      <div style="display:flex;gap:8px"><button class="btn btn-secondary btn-sm" onclick="editRole('${r.name}')">${ICONS.edit} Edit Permissions</button></div>
    </div>`).join("")}
  </div>`;
}
function editRole(name) {
  const r = ROLES.find(x => x.name === name);
  openModal({
    title: "Edit Permissions — " + r.label,
    body: `<p class="text-sm text-gray mb-3">Grant or revoke access for the <strong>${esc(r.name)}</strong> role.</p>
      ${Object.entries(r.perms).map(([k,v]) => `<div class="flex-between" style="padding:10px 0;border-bottom:1px solid #E5E7EB">
        <div><div style="font-weight:600">${PERM_LABELS[k]}</div><div class="text-sm text-gray" style="color:#6B7280">Access to ${PERM_LABELS[k].toLowerCase()} module</div></div>
        <label class="toggle"><input type="checkbox" data-perm="${k}" ${v?"checked":""}><span class="track"></span></label></div>`).join("")}`,
    footer: `<button class="btn btn-secondary" data-cancel2>Cancel</button><button class="btn btn-primary" id="savePerms">Save Permissions</button>`
  }, {
    onMount: (ov) => {
      ov.querySelector("[data-cancel2]").onclick = () => ov.remove();
      ov.querySelector("#savePerms").onclick = () => {
        ov.querySelectorAll("[data-perm]").forEach(cb => { r.perms[cb.dataset.perm] = cb.checked ? 1 : 0; });
        renderRoles(); ov.remove(); showToast("Permissions updated","success");
      };
    }
  });
}
document.getElementById("btnAddRole").addEventListener("click", () => {
  openModal({
    title: "Add Custom Role",
    body: `<div class="form-group"><label>Role Name <span class="req">*</span></label><input class="form-control" id="nrName" placeholder="e.g. radiologist"></div>
      <div class="form-group"><label>Description</label><input class="form-control" id="nrDesc" placeholder="Short description"></div>`,
    footer: `<button class="btn btn-secondary" data-c2>Cancel</button><button class="btn btn-primary" id="saveRole">Create Role</button>`
  }, {
    onMount: (ov) => {
      ov.querySelector("[data-c2]").onclick = () => ov.remove();
      ov.querySelector("#saveRole").onclick = () => {
        const n = ov.querySelector("#nrName").value.trim().toLowerCase();
        if (!n) { showToast("Role name required","error"); return; }
        ROLES.push({ name: n, label: n, desc: ov.querySelector("#nrDesc").value || "Custom role", icon: "shield", perms: {dashboard:1,users:0,patients:0,appointments:0,ai:0,settings:0} });
        renderRoles(); ov.remove(); showToast("Role created","success");
      };
    }
  });
});
""",
}

# =====================================================================
# ADMIN — AI config
# =====================================================================
A["admin"]["ai-config.html"] = {
"title": "AI Module Configuration",
"body": """
<div class="alert alert-info mb-4"><span>%s</span>
  <div class="alert-body"><span class="alert-title">AI services</span> — manage the 7 AI modules. When disabled, the frontend will show "AI unavailable" for that feature.</div>
  <button class="alert-close">×</button></div>
<div id="aiConfigList"></div>
""" % icon("info"),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("admin"); initLayout(); loadPageData();
});
const MODULES = [
  { id:"m1", name:"Clinical Decision Support", ep:"/ai/predict-disease", page:"doctor/ai-diagnosis.html", icon:"brain", on:true, conf:75, model:"rf_clinical_v1.2" },
  { id:"m2", name:"Drug Interaction Checker", ep:"/ai/check-interaction", page:"pharmacist/ai-interaction.html", icon:"pill", on:true, conf:85, model:"drug_int_v1.1" },
  { id:"m3", name:"Lab Result Analyzer", ep:"/ai/analyze-lab", page:"laboratory/ai-analyzer.html", icon:"flask", on:true, conf:80, model:"lab_analyzer_v2.0" },
  { id:"m4", name:"Vitals Alert System", ep:"/ai/check-vitals", page:"nurse/vitals.html", icon:"heart-pulse", on:true, conf:88, model:"vitals_alert_v1.3" },
  { id:"m5", name:"Inventory Forecasting", ep:"/ai/forecast-inventory", page:"pharmacist/ai-forecast.html", icon:"truck", on:true, conf:70, model:"inventory_forecast_v1.4" },
  { id:"m6", name:"Appointment / No-show AI", ep:"/ai/predict-appointment", page:"reception/appointments.html", icon:"calendar", on:true, conf:65, model:"appointment_ai_v1.1" },
  { id:"m7", name:"Symptom Checker Chatbot", ep:"/ai/symptom-chat", page:"patient/ai-chatbot.html", icon:"chat", on:true, conf:60, model:"symptom_chat_v1.5", hasKey:true }
];
function loadPageData() { renderModules(); }
function renderModules() {
  document.getElementById("aiConfigList").innerHTML = MODULES.map((m,i) => `
    <section class="card mb-4" data-module="${m.id}">
      <div class="flex-between wrap" style="gap:12px">
        <div class="flex" style="gap:12px"><div class="stat-icon">${ICONS[m.icon]}</div>
          <div><div style="font-weight:700;font-size:15px">${i+1}. ${m.name}</div>
          <div class="text-sm text-gray" style="color:#6B7280">Endpoint: <code style="background:#F3F4F6;padding:2px 6px;border-radius:4px;font-size:12px">${m.ep}</code></div></div></div>
        <div class="flex" style="gap:14px">
          <span class="badge badge-${m.on?"success":"neutral"}" id="st-${m.id}">${m.on?"Active":"Disabled"}</span>
          <label class="toggle"><input type="checkbox" data-on="${m.id}" ${m.on?"checked":""}><span class="track"></span></label>
        </div>
      </div>
      <div class="divider"></div>
      <div class="form-row-3" style="align-items:end">
        <div class="form-group"><label>Confidence Threshold</label>
          <div class="flex" style="gap:10px"><input type="range" min="0" max="100" value="${m.conf}" data-conf="${m.id}">
          <span class="range-label" id="conf-${m.id}">${m.conf}%</span></div></div>
        <div class="form-group"><label>Model Version</label><input class="form-control" value="${m.model}" disabled style="background:#F9FAFB"></div>
        ${m.hasKey ? '<div class="form-group"><label>Claude API Key</label><input class="form-control" type="password" value="sk-ant-••••••••••••••••" placeholder="sk-ant-…"></div>' : '<div class="form-group"><label>Usage</label><input class="form-control" value="~' + (120 + i*37) + ' calls / day" disabled style="background:#F9FAFB"></div>'}
        <div class="form-group"><button class="btn btn-outline" data-test="${m.id}">${ICONS.zap} Test Module</button></div>
      </div>
    </section>`).join("");
  document.querySelectorAll("[data-on]").forEach(cb => cb.addEventListener("change", () => {
    const m = MODULES.find(x => x.id === cb.dataset.on); m.on = cb.checked;
    const st = document.getElementById("st-" + m.id);
    st.className = "badge badge-" + (m.on ? "success" : "neutral"); st.textContent = m.on ? "Active" : "Disabled";
    showToast(m.name + (m.on ? " enabled" : " disabled"), m.on ? "success" : "warning");
  }));
  document.querySelectorAll("[data-conf]").forEach(r => r.addEventListener("input", () => {
    const m = MODULES.find(x => x.id === r.dataset.conf); m.conf = r.value;
    document.getElementById("conf-" + m.id).textContent = r.value + "%";
  }));
  document.querySelectorAll("[data-test]").forEach(b => b.addEventListener("click", async () => {
    const m = MODULES.find(x => x.id === b.dataset.test);
    b.disabled = true; b.innerHTML = '<span class="spinner sm" style="border-color:#C7DBFE;border-top-color:#1A56DB"></span> Testing…';
    await new Promise(r => setTimeout(r, 900));
    showToast(m.name + " — connection OK (model " + m.model + ")", "success");
    b.innerHTML = ICONS.zap + " Test Module"; b.disabled = false;
  }));
}
""",
}

# =====================================================================
# ADMIN — audit logs
# =====================================================================
A["admin"]["audit-logs.html"] = {
"title": "Audit Logs",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="filters">
      <input type="date" class="form-control" id="fFrom" style="width:160px">
      <input type="date" class="form-control" id="fTo" style="width:160px">
      <select class="form-control" id="fRole" style="width:140px"><option value="">All roles</option><option>admin</option><option>doctor</option><option>nurse</option><option>pharmacist</option><option>laboratory</option><option>reception</option><option>patient</option></select>
      <select class="form-control" id="fAction" style="width:140px"><option value="">All actions</option><option>login</option><option>create</option><option>update</option><option>delete</option><option>backup</option></select>
      <button class="btn btn-secondary" id="btnExp">%s Export CSV</button>
    </div>
    <span class="badge badge-info" id="logCount">0 events</span>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="logsTable">
      <thead><tr><th class="sortable">Timestamp</th><th class="sortable">User</th><th class="sortable">Role</th><th class="sortable">Action</th><th class="sortable">Detail</th><th class="sortable">IP Address</th><th class="sortable">Status</th></tr></thead>
      <tbody id="logsBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("download"), pagination("logsPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("admin"); initLayout(); loadPageData();
});
let LOGS = [];
const ACTION_BADGE = { login:["info","Login"], create:["success","Create"], update:["warning","Update"], delete:["danger","Delete"], backup:["primary","Backup"] };
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.AUDIT_LOGS).then(r => {
    if (!r.ok) return; LOGS = r.data.items; renderLogs();
    attachDataTable(document.getElementById("logsTable"), {
      pagerEl: document.getElementById("logsPager"), pageSize: 10,
      filterFn: (row) => {
        const role = document.getElementById("fRole").value;
        const act = document.getElementById("fAction").value;
        if (role && !row.cells[2].textContent.includes(role)) return false;
        if (act && !row.cells[3].textContent.includes(act)) return false;
        const from = document.getElementById("fFrom").value, to = document.getElementById("fTo").value;
        if (from || to) {
          const d = row.cells[0].dataset.ts;
          if (from && d < from) return false;
          if (to && d > to) return false;
        }
        return true;
      },
      onRender: (n) => document.getElementById("logCount").textContent = n + " events"
    });
  });
}
function renderLogs() {
  document.getElementById("logsBody").innerHTML = LOGS.length ? LOGS.map(l => {
    const ab = ACTION_BADGE[l.action] || ["neutral", l.action];
    return `<tr data-ts="${l.ts}"><td>${formatDateTime(l.ts)}</td><td><strong>${esc(l.user)}</strong></td>
      <td>${esc(l.role)}</td><td><span class="badge badge-${ab[0]}">${ab[1]}</span></td>
      <td class="text-gray">${esc(l.detail || "—")}</td><td style="font-family:monospace;font-size:12px">${esc(l.ip)}</td>
      <td>${l.status === "success" ? badge("Success","success") : badge("Failed","danger")}</td></tr>`;
  }).join("") : emptyRow(7);
  document.querySelectorAll("#logsTable tbody tr").forEach(tr => {
    if (tr.dataset.ts) tr.dataset.ts = tr.dataset.ts;
  });
}
document.getElementById("btnExp").addEventListener("click", () => {
  exportCSV("audit-logs.csv", ["Timestamp","User","Role","Action","Detail","IP","Status"],
    LOGS.map(l => [l.ts,l.user,l.role,l.action,l.detail||"",l.ip,l.status]));
  showToast("Audit logs exported","success");
});
""",
}

# =====================================================================
# ADMIN — settings
# =====================================================================
A["admin"]["settings.html"] = {
"title": "System Settings",
"body": """
<div class="panel-grid cols-2">
  <div>
    <section class="card mb-4"><h3 class="mb-3">General Information</h3>
      <div class="form-row">
        <div class="form-group"><label>Hospital Name</label><input class="form-control" id="sName" value="Wolaita Sodo University Hospital"></div>
        <div class="form-group"><label>Phone</label><input class="form-control" value="+251 46 551 2345"></div>
      </div>
      <div class="form-group"><label>Address</label><input class="form-control" value="Sodo, Wolaita Zone, SNNPR, Ethiopia"></div>
      <div class="form-row">
        <div class="form-group"><label>Email</label><input class="form-control" type="email" value="info@mediqpro.et"></div>
        <div class="form-group"><label>Hospital Logo</label><input class="form-control" type="file" accept="image/*"></div>
      </div>
      <div class="form-actions"><button class="btn btn-primary" onclick="saveSection('General settings saved')">Save General</button></div>
    </section>
    <section class="card"><h3 class="mb-3">Security</h3>
      <div class="form-row">
        <div class="form-group"><label>New Password</label><input class="form-control" type="password" placeholder="••••••••"></div>
        <div class="form-group"><label>Confirm Password</label><input class="form-control" type="password" placeholder="••••••••"></div>
      </div>
      <div class="flex-between" style="padding:10px 0;border-bottom:1px solid #E5E7EB"><div><div style="font-weight:600">Two-Factor Authentication</div><div class="text-sm text-gray" style="color:#6B7280">Require OTP at login</div></div><label class="toggle"><input type="checkbox" checked><span class="track"></span></label></div>
      <div class="flex-between" style="padding:10px 0;border-bottom:1px solid #E5E7EB"><div><div style="font-weight:600">Session Timeout</div><div class="text-sm text-gray" style="color:#6B7280">Auto-logout after inactivity</div></div>
        <select class="form-control" style="width:150px"><option>30 minutes</option><option selected>1 hour</option><option>4 hours</option><option>8 hours</option></select></div>
      <div class="form-actions"><button class="btn btn-primary" onclick="saveSection('Security settings saved')">Save Security</button></div>
    </section>
  </div>
  <div>
    <section class="card mb-4"><h3 class="mb-3">Notifications</h3>
      ${["Email alerts","SMS alerts","System alerts","AI module alerts","Low stock alerts"].map((n,i) =>
        `<div class="flex-between" style="padding:10px 0;border-bottom:1px solid #E5E7EB"><div style="font-weight:500">${n}</div><label class="toggle"><input type="checkbox" ${i<3?"checked":""}><span class="track"></span></label></div>`).join("")}
      <div class="form-actions"><button class="btn btn-primary" onclick="saveSection('Notification settings saved')">Save Notifications</button></div>
    </section>
    <section class="card"><h3 class="mb-3">Data & Backup</h3>
      <div class="detail-list">
        <div class="detail-item"><span class="k">Last backup</span><span class="v">10/08/2026 23:50</span></div>
        <div class="detail-item"><span class="k">Backup size</span><span class="v">184 MB</span></div>
        <div class="detail-item"><span class="k">Schedule</span><span class="v">Daily (23:00 EAT)</span></div>
        <div class="detail-item"><span class="k">Database</span><span class="v">Supabase (PostgreSQL)</span></div>
      </div>
      <div class="flex wrap gap-3 mt-4">
        <button class="btn btn-primary" onclick="saveSection('Backup started — you will be notified when ready')">%s Run Backup Now</button>
        <button class="btn btn-secondary" onclick="saveSection('Database export downloaded')">%s Export Database</button>
      </div>
      <div class="disclaimer mt-4"><span>%s</span><div>Backups are stored securely. Never commit API keys or database credentials to GitHub.</div></div>
    </section>
  </div>
</div>
""" % (icon("refresh"), icon("download"), icon("info")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("admin"); initLayout();
});
function saveSection(msg) { showToast(msg, "success"); }
""",
}
