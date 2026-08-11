# -*- coding: utf-8 -*-
"""MedIQ Pro page bodies — Part A2: manager (executive oversight + AI insights)."""
from frontend_lib import icon, stat_card, panel, badge, pagination, empty_row

M = {"manager": {}}

# =====================================================================
# MANAGER — dashboard
# =====================================================================
M["manager"]["dashboard.html"] = {
"title": "Executive Dashboard",
"body": """
<div class="stat-grid">
  {s1}{s2}{s3}{s4}
</div>
<div class="panel-grid cols-2">
  {p_admissions}{p_revenue}
</div>
<div class="panel-grid">
  {p_distribution}{p_alerts}
</div>
""".format(
    s1=stat_card("dollar", "ETB 84,350", "Revenue Today", "+12% vs yesterday", "up"),
    s2=stat_card("users", "127", "Patients Today", "+18 vs last Monday", "up", "color-success"),
    s3=stat_card("bed", "82%", "Bed Occupancy", "256 of 312 beds", "up", "color-warning"),
    s4=stat_card("user-check", "87", "Staff Present", "of 96 scheduled", "up", "color-info"),
    p_admissions=panel("Patient Admissions — Last 30 Days",
        '<div class="chart-box" id="admChart"></div>',
        sub='<div class="sub">Daily inpatient admissions</div>'),
    p_revenue=panel("Revenue by Department",
        '<div class="chart-box" id="revChart"></div>',
        sub='<div class="sub">ETB (thousands) this month</div>'),
    p_distribution=panel("Patient Distribution by Department",
        '<div class="flex wrap" style="gap:20px;align-items:center"><div class="chart-box" id="distChart" style="max-width:230px"></div><div class="chart-legend" id="distLegend" style="flex-direction:column;margin:0"></div></div>'),
    p_alerts=panel("Recent Alerts",
        '<div id="mgrAlerts"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="ai-insights.html">AI Insights</a>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("manager"); initLayout(); loadPageData();
});
function loadPageData() {
  const admissions = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    admissions.push({ label: d.getDate() + "/" + (d.getMonth() + 1), value: 20 + Math.round(14 * Math.sin(i / 3.1) + Math.random() * 8) });
  }
  document.getElementById("admChart").innerHTML = lineChart(admissions, { height: 250 });
  const rev = [{label:"Medicine",value:32.4},{label:"Surgery",value:24.1},{label:"Cardiology",value:18.7},{label:"Maternity",value:16.2},{label:"Pediatrics",value:12.8},{label:"Pharmacy",value:21.5},{label:"Lab",value:9.6}];
  document.getElementById("revChart").innerHTML = barChart(rev, { height: 250, color: ["#1A56DB","#10B981","#D97706","#7C3AED","#0891B2","#65A30D","#DB2777"] });
  const dist = [{label:"Internal Medicine",value:34},{label:"Pediatrics",value:21},{label:"Maternity",value:18},{label:"Cardiology",value:13},{label:"Surgery",value:9},{label:"Other",value:5}];
  document.getElementById("distChart").innerHTML = donutChart(dist);
  document.getElementById("distLegend").innerHTML = dist.map((d, i) =>
    `<span class="lg-item"><span class="lg-swatch" style="background:${["#1A56DB","#10B981","#D97706","#7C3AED","#0891B2","#DB2778"][i]}"></span>${esc(d.label)} (${d.value}%)</span>`).join("");
  const alerts = [
    { sev: "danger", icon: "package", title: "Amoxicillin 250mg out of stock", sub: "Pharmacy — restock immediately" },
    { sev: "warning", icon: "users", title: "Maternity ward at 92% capacity", sub: "High patient load detected" },
    { sev: "warning", icon: "user-check", title: "3 staff absent today", sub: "Pediatrics & Surgery shifts affected" },
    { sev: "success", icon: "check", title: "AI modules healthy", sub: "All 7 modules passing checks" }
  ];
  document.getElementById("mgrAlerts").innerHTML = alerts.map(a => `
    <div class="feed-item"><div class="feed-icon" style="background:${a.sev==="danger"?"#FEF2F2":a.sev==="warning"?"#FFFBEB":"#ECFDF5"};color:${a.sev==="danger"?"#DC2626":a.sev==="warning"?"#D97706":"#065F46"}">${ICONS[a.icon]}</div>
    <div class="feed-text"><strong>${esc(a.title)}</strong><div class="feed-time">${esc(a.sub)}</div></div>
    <span class="badge badge-${a.sev}">${a.sev}</span></div>`).join("");
}
""",
}

# =====================================================================
# MANAGER — departments
# =====================================================================
M["manager"]["departments.html"] = {
"title": "Departments",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="search-box">%s<input class="form-control" id="depSearch" placeholder="Search department…"></div>
    <button class="btn btn-primary" id="btnAddDep">%s Add Department</button>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="depTable">
      <thead><tr><th class="sortable">Department</th><th class="sortable">Head</th><th class="sortable">Staff</th><th class="sortable">Beds</th><th class="sortable">Occupied</th><th class="sortable">Occupancy</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="depBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), icon("plus"), pagination("depPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("manager"); initLayout(); loadPageData();
});
let DEPTS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.DEPARTMENTS).then(r => {
    if (!r.ok) return; DEPTS = r.data.items; renderDepts();
    attachDataTable(document.getElementById("depTable"), { searchInput: document.getElementById("depSearch"), pagerEl: document.getElementById("depPager"), pageSize: 8 });
  });
  document.getElementById("btnAddDep").addEventListener("click", () => depModal(null));
}
function renderDepts() {
  document.getElementById("depBody").innerHTML = DEPTS.length ? DEPTS.map(d => {
    const occ = d.beds ? Math.round(d.occupied / d.beds * 100) : 0;
    const occCls = occ >= 90 ? "danger" : occ >= 70 ? "warning" : "success";
    return `<tr><td><strong>${esc(d.name)}</strong></td><td>${esc(d.head)}</td><td>${d.staff}</td><td>${d.beds}</td>
      <td>${d.occupied}</td>
      <td><div class="ai-confidence"><div class="progress" style="min-width:90px"><div class="progress-bar ${occCls}" style="width:${occ}%"></div></div><span class="pct" style="min-width:36px">${occ}%</span></div></td>
      <td>${d.status === "active" ? badge("Active","success") : badge("Inactive","neutral")}</td>
      <td><div class="actions"><button class="btn-icon primary" title="Edit" onclick="depModal('${d.id}')">${ICONS.edit}</button>
      <button class="btn-icon danger" title="Delete" onclick="delDep('${d.id}')">${ICONS.trash}</button></div></td></tr>`;
  }).join("") : emptyRow(8);
}
function depModal(id) {
  const d = id ? DEPTS.find(x => x.id === id) : null;
  openModal({
    title: d ? "Edit Department" : "Add Department",
    body: `<div class="form-group"><label>Department Name <span class="req">*</span></label><input class="form-control" id="dName" value="${d ? esc(d.name) : ""}"></div>
      <div class="form-group"><label>Department Head</label><input class="form-control" id="dHead" value="${d ? esc(d.head) : ""}"></div>
      <div class="form-row"><div class="form-group"><label>Beds</label><input class="form-control" type="number" id="dBeds" value="${d ? d.beds : 0}"></div>
      <div class="form-group"><label>Occupied Beds</label><input class="form-control" type="number" id="dOcc" value="${d ? d.occupied : 0}"></div></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveDep">${d ? "Save" : "Add"}</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveDep").onclick = () => {
      const name = ov.querySelector("#dName").value.trim();
      if (!name) { showToast("Department name required","error"); return; }
      if (d) { d.name = name; d.head = ov.querySelector("#dHead").value || "—"; d.beds = +ov.querySelector("#dBeds").value; d.occupied = +ov.querySelector("#dOcc").value; showToast("Department updated","success"); }
      else { DEPTS.unshift({ id: uid("D"), name, head: ov.querySelector("#dHead").value || "—", staff: 0, beds: +ov.querySelector("#dBeds").value, occupied: +ov.querySelector("#dOcc").value, status: "active" }); showToast("Department added","success"); }
      renderDepts(); ov.remove();
    };
  }});
}
async function delDep(id) {
  const ok = await confirmDialog("Delete this department?");
  if (!ok) return;
  DEPTS = DEPTS.filter(d => d.id !== id); renderDepts(); showToast("Department deleted","success");
}
""",
}

# =====================================================================
# MANAGER — staff
# =====================================================================
M["manager"]["staff.html"] = {
"title": "Staff Management",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="search-box">%s<input class="form-control" id="stSearch" placeholder="Search staff…"></div>
    <div class="filters">
      <select class="form-control" id="stStatus" style="width:150px"><option value="">All status</option><option>present</option><option>absent</option><option>on-leave</option></select>
      <button class="btn btn-primary" id="btnAddStaff">%s Add Staff</button>
    </div>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="stTable">
      <thead><tr><th class="sortable">Name</th><th class="sortable">Role</th><th class="sortable">Department</th><th class="sortable">Shift</th><th class="sortable">Status</th><th class="sortable">Contact</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="stBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), icon("plus"), pagination("stPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("manager"); initLayout(); loadPageData();
});
let STAFF = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.STAFF).then(r => {
    if (!r.ok) return; STAFF = r.data.items; renderStaff();
    attachDataTable(document.getElementById("stTable"), {
      searchInput: document.getElementById("stSearch"), pagerEl: document.getElementById("stPager"), pageSize: 8,
      filterFn: row => { const s = document.getElementById("stStatus").value; return !s || row.cells[4].textContent.includes(s); }
    });
  });
  document.getElementById("btnAddStaff").addEventListener("click", () => staffModal(null));
}
function renderStaff() {
  document.getElementById("stBody").innerHTML = STAFF.length ? STAFF.map(s => `<tr>
    <td><div class="flex" style="gap:10px"><span class="avatar-sm">${initialsOf(s.name)}</span><strong>${esc(s.name)}</strong></div></td>
    <td>${esc(s.role)}</td><td>${esc(s.dept)}</td><td><span class="badge badge-info">${esc(s.shift)}</span></td>
    <td>${s.status === "present" ? badge("Present","success") : s.status === "absent" ? badge("Absent","danger") : badge("On leave","warning")}</td>
    <td class="text-sm text-gray" style="color:#6B7280">${esc(s.contact)}</td>
    <td><div class="actions"><button class="btn-icon primary" title="Edit" onclick="staffModal('${s.id}')">${ICONS.edit}</button>
    <button class="btn-icon danger" title="Delete" onclick="delStaff('${s.id}')">${ICONS.trash}</button></div></td></tr>`).join("") : emptyRow(7);
}
function staffModal(id) {
  const s = id ? STAFF.find(x => x.id === id) : null;
  openModal({
    title: s ? "Edit Staff" : "Add Staff",
    body: `<div class="form-group"><label>Full Name <span class="req">*</span></label><input class="form-control" id="sName" value="${s ? esc(s.name) : ""}"></div>
      <div class="form-row"><div class="form-group"><label>Role</label><input class="form-control" id="sRole" value="${s ? esc(s.role) : ""}" placeholder="Doctor, Nurse…"></div>
      <div class="form-group"><label>Department</label><input class="form-control" id="sDept" value="${s ? esc(s.dept) : ""}"></div></div>
      <div class="form-row"><div class="form-group"><label>Shift</label><select class="form-control" id="sShift"><option ${!s||s.shift==="Morning"?"selected":""}>Morning</option><option ${s&&s.shift==="Evening"?"selected":""}>Evening</option><option ${s&&s.shift==="Night"?"selected":""}>Night</option></select></div>
      <div class="form-group"><label>Status</label><select class="form-control" id="sStatus"><option ${!s||s.status==="present"?"selected":""}>present</option><option ${s&&s.status==="absent"?"selected":""}>absent</option><option ${s&&s.status==="on-leave"?"selected":""}>on-leave</option></select></div></div>
      <div class="form-group"><label>Contact</label><input class="form-control" id="sContact" value="${s ? esc(s.contact) : ""}"></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveSt">${s ? "Save" : "Add"}</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveSt").onclick = () => {
      const name = ov.querySelector("#sName").value.trim();
      if (!name) { showToast("Name required","error"); return; }
      if (s) { s.name = name; s.role = ov.querySelector("#sRole").value; s.dept = ov.querySelector("#sDept").value; s.shift = ov.querySelector("#sShift").value; s.status = ov.querySelector("#sStatus").value; s.contact = ov.querySelector("#sContact").value; showToast("Staff updated","success"); }
      else { STAFF.unshift({ id: uid("S"), name, role: ov.querySelector("#sRole").value || "Staff", dept: ov.querySelector("#sDept").value || "—", shift: ov.querySelector("#sShift").value, status: ov.querySelector("#sStatus").value, contact: ov.querySelector("#sContact").value }); showToast("Staff added","success"); }
      renderStaff(); ov.remove();
    };
  }});
}
async function delStaff(id) {
  const ok = await confirmDialog("Remove this staff member?");
  if (!ok) return;
  STAFF = STAFF.filter(s => s.id !== id); renderStaff(); showToast("Staff removed","success");
}
""",
}

# =====================================================================
# MANAGER — reports
# =====================================================================
M["manager"]["reports.html"] = {
"title": "Reports",
"body": """
<div class="flex-between mb-4"><p class="page-intro" style="margin:0">Generate and download executive reports.</p>
  <button class="btn btn-primary" id="btnGenReport">%s Generate Report</button></div>
<div class="card" style="padding:0">
  <div class="table-toolbar"><h3 style="font-size:16px">Generated Reports</h3>
    <span class="badge badge-info" id="repCount">0 reports</span></div>
  <div class="table-wrap">
    <table class="data-table">
      <thead><tr><th>Report</th><th>Period</th><th>Generated</th><th>Format</th><th>Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="repBody"></tbody>
    </table>
  </div>
</div>
""" % icon("chart"),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("manager"); initLayout(); loadPageData();
});
let REPORTS = [
  { id:"R-1", name:"Monthly Revenue Summary", period:"July 2026", generated:"01/08/2026", format:"PDF", status:"ready" },
  { id:"R-2", name:"Patient Admissions Report", period:"30 days", generated:"10/08/2026", format:"CSV", status:"ready" },
  { id:"R-3", name:"Inventory Consumption", period:"Q3 2026", generated:"05/08/2026", format:"PDF", status:"ready" },
  { id:"R-4", name:"AI Module Usage", period:"July 2026", generated:"02/08/2026", format:"CSV", status:"ready" }
];
function loadPageData() {
  renderReps();
  document.getElementById("btnGenReport").addEventListener("click", genModal);
}
function renderReps() {
  document.getElementById("repCount").textContent = REPORTS.length + " reports";
  document.getElementById("repBody").innerHTML = REPORTS.length ? REPORTS.map(r => `<tr>
    <td><strong>${esc(r.name)}</strong></td><td>${esc(r.period)}</td><td>${esc(r.generated)}</td>
    <td><span class="badge badge-primary">${esc(r.format)}</span></td>
    <td>${r.status === "ready" ? badge("Ready","success") : badge("Generating","warning")}</td>
    <td><div class="actions"><button class="btn-icon primary" title="Download" onclick="showToast('Downloading ' + '${r.name}','info')">${ICONS.download}</button>
    <button class="btn-icon" title="Print" onclick="showToast('Sending to printer','info')">${ICONS.printer}</button></div></td></tr>`).join("") : emptyRow(6);
}
function genModal() {
  openModal({
    title: "Generate Report",
    body: `<div class="form-group"><label>Report Type</label><select class="form-control" id="gType">
      <option>Revenue Summary</option><option>Patient Admissions</option><option>Staff Attendance</option><option>Inventory Consumption</option><option>AI Module Usage</option><option>Department Performance</option></select></div>
      <div class="form-group"><label>Period</label><select class="form-control" id="gPeriod"><option>Last 7 days</option><option selected>Last 30 days</option><option>Last 90 days</option><option>This year</option></select></div>
      <div class="form-group"><label>Format</label><select class="form-control" id="gFormat"><option>PDF</option><option>CSV</option><option>Excel</option></select></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="gGo">Generate</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#gGo").onclick = () => {
      const name = ov.querySelector("#gType").value, fmt = ov.querySelector("#gFormat").value;
      showLoading("Generating report…");
      setTimeout(() => {
        hideLoading();
        REPORTS.unshift({ id: uid("R"), name, period: ov.querySelector("#gPeriod").value, generated: formatDate(todayStr()), format: fmt, status: "ready" });
        renderReps(); ov.remove();
        showToast(name + " generated successfully", "success");
      }, 1400);
    };
  }});
}
""",
}

# =====================================================================
# MANAGER — ai-insights
# =====================================================================
M["manager"]["ai-insights.html"] = {
"title": "AI Insights",
"body": """
<div class="alert alert-info mb-4"><span>%s</span>
  <div class="alert-body"><span class="alert-title">AI-powered operations</span> — forecasts and recommendations generated by the AI modules (Inventory, Vitals, Appointment AI).</div></div>
<div class="panel-grid cols-2">
  {p_forecast}{p_heatmap}
</div>
<div class="panel-grid">
  {p_workload}{p_recs}
</div>
""".format(
    p_forecast=panel("Inventory Demand Forecast — 30 Days",
        '<div class="chart-box" id="insForecastChart"></div>',
        sub='<div class="sub">Top drugs combined daily demand (Module 5)</div>'),
    p_heatmap=panel("Patient Load Prediction — Next 7 Days",
        '<div class="chart-box" id="loadHeatmap"></div>',
        sub='<div class="sub">Predicted busy hours by day (Module 6)</div>'),
    p_workload=panel("Department Workload Comparison",
        '<div class="chart-box" id="workloadChart"></div>',
        sub='<div class="sub">Patients per department this week</div>'),
    p_recs=panel("AI Recommendations",
        '<div id="aiRecs"></div>',
        sub='<div class="sub">Auto-generated action items</div>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("manager"); initLayout(); loadPageData();
});
function loadPageData() {
  // Forecast: historical + predicted for one drug
  const hist = [82, 90, 78, 95, 88, 102, 84, 97, 91, 108, 86, 99].map((v, i) => ({ label: "D-" + (12 - i), value: v }));
  const pred = [];
  for (let i = 1; i <= 30; i++) pred.push({ label: "D+" + i, value: Math.round(8 + i * 0.4 + 5 * Math.sin(i / 5)) });
  document.getElementById("insForecastChart").innerHTML = lineChart([...hist, ...pred], { height: 250, valueFmt: v => v });
  // Heatmap: 7 days x 8 hours (08:00–20:00 every 2h)
  const rows = ["OPD","Emergency","Maternity","Pediatrics","Cardiology"].map((label, r) => {
    const cells = [];
    const days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
    days.forEach((d, i) => {
      const v = Math.round(15 + 60 * Math.exp(-Math.pow((i - 2.5) / 2.2, 2)) * (1 + 0.4 * Math.sin((r + i) * 1.7)) + 10 * Math.random());
      cells.push({ label: d, v: Math.min(99, v) });
    });
    return { label, cells };
  });
  document.getElementById("loadHeatmap").innerHTML = heatmapChart(rows);
  const wl = [{label:"Medicine",value:34},{label:"Pediatrics",value:21},{label:"Maternity",value:18},{label:"Cardiology",value:13},{label:"Surgery",value:9},{label:"Emergency",value:26}];
  document.getElementById("workloadChart").innerHTML = barChart(wl, { height: 250, color: "#0891B2" });
  const recs = [
    { sev: "high", icon: "package", title: "Reorder Amoxicillin 250mg", sub: "Stock-out expected within 5 days. Suggested order: 1,200 capsules (Module 5)." },
    { sev: "high", icon: "users", title: "Maternity staff shortage risk", sub: "Forecasted load 92% for the next 3 days — consider extra shift (Module 6)." },
    { sev: "med", icon: "heart", title: "Monitor Selam Tadesse (Ward 3)", sub: "Vitals AI flagged elevated BP 3× today (Module 4)." },
    { sev: "med", icon: "calendar", title: "Reduce Saturday no-shows", sub: "No-show AI predicts 24% on weekends — send SMS reminders (Module 6)." },
    { sev: "low", icon: "truck", title: "Stock up on IV Dextrose 5%", sub: "Consumption trend +8%/week — order 60 bottles (Module 5)." }
  ];
  const sevMap = { high: ["danger","High priority"], med: ["warning","Medium priority"], low: ["success","Low priority"] };
  document.getElementById("aiRecs").innerHTML = recs.map(r => {
    const m = sevMap[r.sev];
    return `<div class="feed-item"><div class="feed-icon" style="background:${r.sev==="high"?"#FEF2F2":r.sev==="med"?"#FFFBEB":"#ECFDF5"};color:${r.sev==="high"?"#DC2626":r.sev==="med"?"#D97706":"#065F46"}">${ICONS[r.icon]}</div>
      <div class="feed-text"><strong>${esc(r.title)}</strong><div class="feed-time">${esc(r.sub)}</div></div>
      <span class="badge badge-${m[0]}">${m[1]}</span></div>`;
  }).join("");
}
""",
}
