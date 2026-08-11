# -*- coding: utf-8 -*-
"""MedIQ Pro page bodies — Part C: pharmacist + laboratory."""
from frontend_lib import icon, stat_card, panel, badge, pagination, empty_row

C = {"pharmacist": {}, "laboratory": {}}

# =====================================================================
# PHARMACIST — dashboard
# =====================================================================
C["pharmacist"]["dashboard.html"] = {
"title": "Pharmacy Dashboard",
"body": """
<div class="stat-grid">
  {s1}{s2}{s3}{s4}
</div>
<div class="panel-grid">
  <div>{p_alerts}{p_disp}</div>
  <div>{p_quick}{p_low}</div>
</div>
""".format(
    s1=stat_card("file-text", "34", "Prescriptions Today", "+8 vs yesterday", "up"),
    s2=stat_card("check", "28", "Dispensed", "82% fill rate", "up", "color-success"),
    s3=stat_card("package", '<span id="lowStockCount">–</span>', "Low Stock Items", "reorder soon", "down", "color-warning"),
    s4=stat_card("clock", "4", "Expiring Soon", "within 30 days", "down", "color-danger"),
    p_alerts=panel("Inventory Alerts",
        '<div id="invAlerts"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="inventory.html">Inventory</a>'),
    p_disp=panel("Recent Dispensations",
        '<div class="table-wrap" style="max-height:320px;overflow-y:auto"><table class="data-table"><thead><tr><th>Patient</th><th>Items</th><th>Status</th></tr></thead><tbody id="dispBody"></tbody></table></div>',
        actions='<a class="btn btn-secondary btn-sm" href="prescriptions.html">Queue</a>'),
    p_quick=panel("Quick Actions",
        '<div class="quick-actions" style="grid-template-columns:1fr;margin:0">'
        '<a class="quick-action" href="ai-interaction.html"><div class="qa-icon" style="background:#F5F3FF;color:#7C3AED">' + icon("zap") + '</div><div><div class="qa-title">AI Interaction Check</div><div class="qa-sub">Module 2</div></div></a>'
        '<a class="quick-action" href="ai-forecast.html"><div class="qa-icon" style="background:#EFF6FF;color:#1A56DB">' + icon("truck") + '</div><div><div class="qa-title">Inventory Forecast</div><div class="qa-sub">Module 5</div></div></a>'
        '<a class="quick-action" href="inventory.html"><div class="qa-icon" style="background:#ECFDF5;color:#065F46">' + icon("package") + '</div><div><div class="qa-title">Manage Stock</div><div class="qa-sub">Add or update drugs</div></div></a>'
        '</div>'),
    p_low=panel("Stock Levels",
        '<div class="chart-box" id="stockChart"></div>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("pharmacist"); initLayout(); loadPageData();
});
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.INVENTORY).then(r => {
    if (!r.ok) return;
    const items = r.data.items;
    const low = items.filter(i => i.status === "low-stock" || i.status === "out-of-stock");
    const exp = items.filter(i => i.status === "expiring-soon");
    document.getElementById("lowStockCount").textContent = low.length;
    document.getElementById("invAlerts").innerHTML = low.slice(0, 5).map(i => `
      <div class="feed-item"><div class="feed-icon" style="background:${i.status==="out-of-stock"?"#FEF2F2":"#FFFBEB"};color:${i.status==="out-of-stock"?"#DC2626":"#D97706"}">${ICONS.package}</div>
      <div class="feed-text"><strong>${esc(i.name)}</strong> · ${i.stock} ${esc(i.unit)} left<div class="feed-time">${i.status === "out-of-stock" ? "Out of stock!" : "Below reorder point"}</div></div>
      <span class="badge badge-${i.status==="out-of-stock"?"danger":"warning"}">${i.status==="out-of-stock"?"Out":"Low"}</span></div>`).join("") ||
      '<div class="empty-state">All stock levels healthy ✅</div>';
    // Stock bar chart (top 6 by stock)
    const top = [...items].sort((a, b) => b.stock - a.stock).slice(0, 6);
    document.getElementById("stockChart").innerHTML = barChart(top.map(i => ({ label: i.name.split(" ")[0], value: i.stock })), { height: 220 });
    const colors = top.map(i => i.status === "in-stock" ? "#10B981" : i.status === "low-stock" ? "#D97706" : "#DC2626");
    document.getElementById("stockChart").innerHTML = barChart(top.map(i => ({ label: i.name.split(" ")[0], value: i.stock })), { height: 220, color: colors });
    if (exp.length) showToast(exp.length + " item(s) expiring within 30 days", "warning");
  });
  apiFetch(CONFIG.ENDPOINTS.PRESCRIPTIONS).then(r => {
    if (!r.ok) return;
    document.getElementById("dispBody").innerHTML = r.data.items.slice(0, 6).map(p => `<tr>
      <td><strong>${esc(p.patient)}</strong><div class="text-sm text-gray" style="color:#6B7280">${formatDate(p.date)}</div></td>
      <td><span class="badge badge-primary">${p.drugs.length} item${p.drugs.length>1?"s":""}</span></td>
      <td>${p.status === "active" ? badge("Pending","warning") : badge("Dispensed","success")}</td></tr>`).join("") || emptyRow(3);
  });
}
""",
}

# =====================================================================
# PHARMACIST — prescriptions (dispensing queue)
# =====================================================================
C["pharmacist"]["prescriptions.html"] = {
"title": "Prescription Queue",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar"><h3 style="font-size:16px">Pending Dispensing</h3>
    <span class="badge badge-warning" id="pendCount">0 pending</span></div>
  <div class="table-wrap">
    <table class="data-table" id="phRxTable">
      <thead><tr><th class="sortable">ID</th><th class="sortable">Patient</th><th>Medications</th><th class="sortable">Prescribed By</th><th class="sortable">Date</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="phRxBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % pagination("phRxPager"),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("pharmacist"); initLayout(); loadPageData();
});
let PHRX = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.PRESCRIPTIONS).then(r => {
    if (!r.ok) return; PHRX = r.data.items; render();
    attachDataTable(document.getElementById("phRxTable"), { pagerEl: document.getElementById("phRxPager"), pageSize: 8 });
  });
}
function render() {
  document.getElementById("pendCount").textContent = PHRX.filter(p => p.status === "active").length + " pending";
  document.getElementById("phRxBody").innerHTML = PHRX.map(p => `<tr>
    <td><span class="badge badge-neutral">${esc(p.id)}</span></td><td><strong>${esc(p.patient)}</strong></td>
    <td>${p.drugs.map(d => `<span class="badge badge-primary" style="margin:1px">${esc(d.name)}</span>`).join("")}</td>
    <td>${esc(p.doctor)}</td><td>${formatDate(p.date)}</td>
    <td>${p.status === "dispensed" ? badge("Dispensed","success") : badge("Pending","warning")}</td>
    <td><div class="actions">
      <button class="btn-icon primary" title="View" onclick="viewPhRx('${p.id}')">${ICONS.eye}</button>
      ${p.status !== "dispensed" ? `<button class="btn btn-success btn-sm" onclick="dispense('${p.id}')">${ICONS.check} Dispense</button>` : ""}
    </div></td></tr>`).join("") || emptyRow(7);
}
function dispense(id) {
  const p = PHRX.find(x => x.id === id);
  p.status = "dispensed"; render();
  showToast("Dispensed " + p.drugs.length + " item(s) to " + p.patient, "success");
}
function viewPhRx(id) {
  const p = PHRX.find(x => x.id === id);
  openModal({
    title: "Prescription " + p.id,
    body: `<div class="detail-list"><div class="detail-item"><span class="k">Patient</span><span class="v">${esc(p.patient)}</span></div>
      <div class="detail-item"><span class="k">Doctor</span><span class="v">${esc(p.doctor)}</span></div>
      <div class="detail-item"><span class="k">Date</span><span class="v">${formatDate(p.date)}</span></div></div>
      <h3 class="mt-4 mb-2" style="font-size:15px">Medications</h3>
      <table class="data-table"><thead><tr><th>Drug</th><th>Dosage</th><th>Frequency</th><th>Duration</th></tr></thead><tbody>
      ${p.drugs.map(d => `<tr><td>${esc(d.name)}</td><td>${esc(d.dose)}</td><td>${esc(d.freq)}</td><td>${esc(d.duration)}</td></tr>`).join("")}</tbody></table>`,
    size: "lg"
  });
}
""",
}

# =====================================================================
# PHARMACIST — inventory
# =====================================================================
C["pharmacist"]["inventory.html"] = {
"title": "Drug Inventory",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="search-box">%s<input class="form-control" id="invSearch" placeholder="Search drug…"></div>
    <div class="filters">
      <select class="form-control" id="invCat" style="width:160px"><option value="">All categories</option><option>Analgesic</option><option>Cardiovascular</option><option>Antidiabetic</option><option>Antibiotic</option><option>Respiratory</option><option>Antimalarial</option><option>IV Fluids</option><option>Steroid</option><option>Gastro</option></select>
      <select class="form-control" id="invStatus" style="width:150px"><option value="">All status</option><option>in-stock</option><option>low-stock</option><option>out-of-stock</option><option>expiring-soon</option></select>
      <button class="btn btn-secondary" id="invExp">%s Export CSV</button>
      <button class="btn btn-primary" id="invAdd">%s Add Stock</button>
    </div>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="invTable">
      <thead><tr><th class="sortable">Drug Name</th><th class="sortable">Category</th><th class="sortable">Stock</th><th class="sortable">Unit</th><th class="sortable">Expiry</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="invBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), icon("download"), icon("plus"), pagination("invPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("pharmacist"); initLayout(); loadPageData();
});
let INV = [];
const STATUS_BADGE = { "in-stock":["success","In Stock"], "low-stock":["warning","Low Stock"], "out-of-stock":["danger","Out of Stock"], "expiring-soon":["default","Expiring Soon"] };
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.INVENTORY).then(r => {
    if (!r.ok) return; INV = r.data.items; renderInv();
    attachDataTable(document.getElementById("invTable"), {
      searchInput: document.getElementById("invSearch"), pagerEl: document.getElementById("invPager"), pageSize: 8,
      filterFn: row => {
        const cat = document.getElementById("invCat").value, st = document.getElementById("invStatus").value;
        if (cat && !row.cells[1].textContent.includes(cat)) return false;
        if (st && !row.cells[5].textContent.includes(st.replace("-", " "))) return false;
        return true;
      }
    });
  });
  document.getElementById("invAdd").addEventListener("click", () => invModal(null));
  document.getElementById("invExp").addEventListener("click", () => {
    exportCSV("inventory.csv", ["Drug","Category","Stock","Unit","Expiry","Status"],
      INV.map(i => [i.name, i.category, i.stock, i.unit, i.expiry, i.status]));
    showToast("Inventory exported to CSV","success");
  });
}
function renderInv() {
  document.getElementById("invBody").innerHTML = INV.length ? INV.map(i => {
    const b = STATUS_BADGE[i.status] || ["neutral", i.status];
    const low = i.status === "low-stock" || i.status === "out-of-stock";
    return `<tr><td><strong>${esc(i.name)}</strong></td><td>${esc(i.category)}</td>
      <td><strong style="color:${low ? "var(--danger)" : "var(--success)"}">${i.stock}</strong> <span class="text-sm text-gray" style="color:#6B7280">${esc(i.unit)}</span></td>
      <td>${esc(i.unit)}</td><td>${formatDate(i.expiry)}</td>
      <td><span class="badge badge-${b[0]}">${b[1]}</span></td>
      <td><div class="actions">
        <button class="btn-icon primary" title="Edit" onclick="invModal('${i.id}')">${ICONS.edit}</button>
        <button class="btn-icon danger" title="Delete" onclick="delInv('${i.id}')">${ICONS.trash}</button></div></td></tr>`;
  }).join("") : emptyRow(7);
}
function invModal(id) {
  const i = id ? INV.find(x => x.id === id) : null;
  openModal({
    title: i ? "Edit Stock — " + i.name : "Add New Drug",
    body: `<div class="form-row">
      <div class="form-group"><label>Drug Name <span class="req">*</span></label><input class="form-control" id="iName" value="${i ? esc(i.name) : ""}"></div>
      <div class="form-group"><label>Category</label><select class="form-control" id="iCat">${["Analgesic","Cardiovascular","Antidiabetic","Antibiotic","Respiratory","Antimalarial","IV Fluids","Steroid","Gastro"].map(c => `<option ${i && i.category === c ? "selected" : ""}>${c}</option>`).join("")}</select></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Stock <span class="req">*</span></label><input class="form-control" type="number" id="iStock" value="${i ? i.stock : ""}"></div>
      <div class="form-group"><label>Unit</label><input class="form-control" id="iUnit" value="${i ? esc(i.unit) : "tablets"}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Expiry Date</label><input class="form-control" type="date" id="iExp" value="${i ? i.expiry : ""}"></div>
      <div class="form-group"><label>Status</label><select class="form-control" id="iStatus">${Object.keys(STATUS_BADGE).map(s => `<option ${i && i.status === s ? "selected" : ""}>${s}</option>`).join("")}</select></div>
    </div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveInv">${i ? "Save Changes" : "Add Drug"}</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveInv").onclick = () => {
      const name = ov.querySelector("#iName").value.trim();
      if (!name) { showToast("Drug name required","error"); return; }
      if (i) {
        i.name = name; i.category = ov.querySelector("#iCat").value; i.stock = +ov.querySelector("#iStock").value || 0;
        i.unit = ov.querySelector("#iUnit").value; i.expiry = ov.querySelector("#iExp").value; i.status = ov.querySelector("#iStatus").value;
        showToast("Stock updated","success");
      } else {
        INV.unshift({ id: uid("I"), name, category: ov.querySelector("#iCat").value, stock: +ov.querySelector("#iStock").value || 0, unit: ov.querySelector("#iUnit").value, expiry: ov.querySelector("#iExp").value || "2027-01-01", status: "in-stock" });
        showToast("Drug added to inventory","success");
      }
      renderInv(); ov.remove();
    };
  }});
}
async function delInv(id) {
  const ok = await confirmDialog("Delete this drug from inventory?");
  if (!ok) return;
  INV = INV.filter(i => i.id !== id); renderInv(); showToast("Drug removed","success");
}
""",
}

# =====================================================================
# PHARMACIST — ai-interaction (Module 2)
# =====================================================================
C["pharmacist"]["ai-interaction.html"] = {
"title": "AI Drug Interaction Checker",
"body": """
<div class="alert alert-info mb-4"><span>%s</span>
  <div class="alert-body"><span class="alert-title">Module 2 — Drug Interaction</span> — check two drugs or up to five drugs for all pairwise combinations.</div></div>
<div class="panel-grid cols-2">
  <section class="card">
    <h3 class="mb-3">Check Two Drugs</h3>
    <div class="form-group"><label>Drug A</label><input class="form-control" id="drugA" list="drugList" placeholder="Type to search…"></div>
    <div class="form-group"><label>Drug B</label><input class="form-control" id="drugB" list="drugList" placeholder="Type to search…"></div>
    <button class="btn btn-primary btn-block" id="btnCheckPair">%s Check Interaction</button>
    <div class="disclaimer mt-4"><span>%s</span><div>AI suggestions only. Final decisions by the pharmacist or doctor.</div></div>
  </section>
  <div>
    <div id="pairResult"></div>
    <section class="card mt-4">
      <h3 class="mb-3">Multi-Drug Check (up to 5)</h3>
      <div id="multiInputs"></div>
      <div class="flex gap-3 mt-3">
        <button class="btn btn-secondary" id="btnAddDrug">%s Add Drug</button>
        <button class="btn btn-primary" id="btnCheckAll">%s Check All Combinations</button>
      </div>
      <div id="multiResult" class="mt-4"></div>
    </section>
  </div>
</div>
<datalist id="drugList"></datalist>
""" % (icon("info"), icon("zap"), icon("info"), icon("plus"), icon("layers")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("pharmacist"); initLayout(); loadPageData();
});
const CATALOG = ["Paracetamol 500mg","Amlodipine 5mg","Metformin 500mg","Insulin Glargine","Amoxicillin 250mg","Salbutamol Inhaler","Atorvastatin 20mg","Bisoprolol 2.5mg","Enalapril 10mg","Aspirin 81mg","Furosemide 40mg","Warfarin 5mg","Digoxin 0.25mg","Ceftriaxone 1g","Hydrocortisone 100mg","Artemether/Lumefantrine"];
let multiDrugs = [];
function loadPageData() {
  document.getElementById("drugList").innerHTML = CATALOG.map(d => `<option value="${d}">`).join("");
  addMultiInput();
  document.getElementById("btnCheckPair").addEventListener("click", checkPair);
  document.getElementById("btnAddDrug").addEventListener("click", () => {
    if (multiDrugs.length >= 5) { showToast("Maximum 5 drugs","warning"); return; }
    addMultiInput();
  });
  document.getElementById("btnCheckAll").addEventListener("click", checkAll);
}
function addMultiInput() {
  const wrap = document.getElementById("multiInputs");
  const div = document.createElement("div");
  div.className = "form-group";
  div.innerHTML = `<div class="flex" style="gap:10px"><input class="form-control" list="drugList" placeholder="Drug ${multiDrugs.length + 1}…">
    <button class="btn-icon danger" title="Remove">${ICONS.x}</button></div>`;
  div.querySelector("button").onclick = () => { div.remove(); multiDrugs = Array.from(wrap.querySelectorAll("input")).map(i => i.value.trim()).filter(Boolean); };
  wrap.appendChild(div);
  multiDrugs = Array.from(wrap.querySelectorAll("input")).map(i => i.value.trim()).filter(Boolean);
  wrap.querySelectorAll("input").forEach(inp => inp.addEventListener("input", () => { multiDrugs = Array.from(wrap.querySelectorAll("input")).map(i => i.value.trim()).filter(Boolean); }));
}
function checkPair() {
  const a = document.getElementById("drugA").value.trim(), b = document.getElementById("drugB").value.trim();
  if (!a || !b) { showToast("Enter both drug names","error"); return; }
  document.getElementById("pairResult").innerHTML = `<section class="card"><div class="loading-area"><div class="spinner"></div><div>Checking interaction…</div></div></section>`;
  checkDrugInteraction({ drug_a: a, drug_b: b }, res => {
    const cls = res.level === "severe" ? "severity-severe" : res.level === "moderate" ? "severity-moderate" : "severity-safe";
    const ico = res.level === "severe" ? ICONS.alert : res.level === "moderate" ? ICONS.info : ICONS.check;
    const title = res.level === "severe" ? "danger" : res.level === "moderate" ? "warning" : "success";
    document.getElementById("pairResult").innerHTML = `<section class="card">
      <div class="severity-card ${cls}"><div class="flex" style="gap:10px;align-items:flex-start"><span>${ico}</span>
        <div><strong style="font-size:16px">${res.title}</strong><div style="font-size:13px;margin-top:2px">${esc(res.drug_a)} + ${esc(res.drug_b)}</div></div></div></div>
      <div class="detail-list mt-4">
        <div class="detail-item"><span class="k">Mechanism</span><span class="v" style="max-width:340px">${esc(res.mechanism)}</span></div>
        <div class="detail-item"><span class="k">Clinical Effect</span><span class="v" style="max-width:340px">${esc(res.effect)}</span></div>
        <div class="detail-item"><span class="k">Recommended Action</span><span class="v" style="max-width:340px">${esc(res.action)}</span></div>
      </div>
      <div class="disclaimer"><span>${ICONS.info}</span><div>AI suggestions only — model ${esc(res.model || "v1.1")}. Verify with a clinical reference.</div></div>
    </section>`;
  });
}
function checkAll() {
  if (multiDrugs.length < 2) { showToast("Add at least 2 drugs","warning"); return; }
  showLoading("Checking all combinations…");
  const pairs = [];
  for (let i = 0; i < multiDrugs.length; i++) for (let j = i + 1; j < multiDrugs.length; j++) pairs.push([multiDrugs[i], multiDrugs[j]]);
  let results = [], done = 0;
  setTimeout(() => {
    pairs.forEach(([a, b]) => {
      checkDrugInteraction({ drug_a: a, drug_b: b }, res => {
        results.push({ a, b, res }); done++;
        if (done === pairs.length) {
          hideLoading();
          const rows = results.map(r => {
            const ico = r.res.level === "severe" ? "danger" : r.res.level === "moderate" ? "warning" : "success";
            return `<tr><td><strong>${esc(r.a)}</strong> + <strong>${esc(r.b)}</strong></td>
              <td><span class="badge badge-${ico}">${r.res.title}</span></td><td class="text-sm text-gray" style="color:#6B7280">${esc(r.res.action)}</td></tr>`;
          }).join("");
          document.getElementById("multiResult").innerHTML = `<table class="data-table"><thead><tr><th>Combination</th><th>Result</th><th>Recommended Action</th></tr></thead><tbody>${rows}</tbody></table>`;
          showToast("Checked " + pairs.length + " combinations","success");
        }
      });
    });
  }, 500);
}
""",
}

# =====================================================================
# PHARMACIST — ai-forecast (Module 5)
# =====================================================================
C["pharmacist"]["ai-forecast.html"] = {
"title": "AI Inventory Forecast",
"body": """
<div class="alert alert-info mb-4"><span>%s</span>
  <div class="alert-body"><span class="alert-title">Module 5 — Inventory Forecasting</span> — predicts future drug demand so you can reorder before stock runs out.</div></div>
<section class="card mb-4">
  <div class="form-row" style="align-items:end">
    <div class="form-group"><label>Drug</label><input class="form-control" id="fcDrug" list="fcDrugs" placeholder="Search drug…"></div>
    <div class="form-group"><label>Forecast Period</label>
      <div class="chip-group" id="fcPeriods">
        <span class="chip selected" data-days="7">7 days</span><span class="chip" data-days="14">14 days</span>
        <span class="chip" data-days="30">30 days</span><span class="chip" data-days="60">60 days</span>
      </div></div>
    <div class="form-group"><button class="btn btn-primary btn-lg" id="btnForecast">%s Run Forecast</button></div>
  </div>
</section>
<div id="fcResult"></div>
<datalist id="fcDrugs"></datalist>
""" % (icon("info"), icon("truck")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("pharmacist"); initLayout(); loadPageData();
});
let days = 30, fcDrug = "Paracetamol 500mg";
function loadPageData() {
  const drugs = ["Paracetamol 500mg","Amlodipine 5mg","Metformin 500mg","Insulin Glargine","Amoxicillin 250mg","Salbutamol Inhaler","Atorvastatin 20mg","Ceftriaxone 1g","Artemether/Lumefantrine","ORS Sachets"];
  document.getElementById("fcDrugs").innerHTML = drugs.map(d => `<option value="${d}">`).join("");
  document.getElementById("fcPeriods").querySelectorAll(".chip").forEach(c => c.addEventListener("click", () => {
    document.querySelectorAll("#fcPeriods .chip").forEach(x => x.classList.remove("selected"));
    c.classList.add("selected"); days = +c.dataset.days;
  }));
  document.getElementById("fcDrug").addEventListener("input", e => { if (e.target.value) fcDrug = e.target.value; });
  document.getElementById("btnForecast").addEventListener("click", runForecast);
}
function runForecast() {
  const drug = document.getElementById("fcDrug").value.trim() || fcDrug;
  if (!drug) { showToast("Select a drug first","error"); return; }
  document.getElementById("fcResult").innerHTML = `<section class="card"><div class="loading-area"><div class="spinner"></div><div>Running demand forecast…</div></div></section>`;
  forecastInventory({ drug_name: drug, days }, renderForecast);
}
function renderForecast(res) {
  const hist = res.historical.map(h => ({ label: h.label, value: h.value }));
  const fc = res.forecast.map(f => ({ label: f.day, value: f.value }));
  const all = [...hist, ...fc];
  const chart = lineChart(all, { height: 260, valueFmt: v => v });
  const runsOut = res.runs_out_in_days;
  document.getElementById("fcResult").innerHTML = `<div class="stat-grid" style="grid-template-columns:repeat(auto-fit,minmax(180px,1fr))">
    ${statCardHtml(res.current_stock + "", "Current Stock", "package", "in-stock")}
    ${statCardHtml(res.daily_use + " /day", "Avg Daily Demand", "activity", "info")}
    ${statCardHtml(runsOut ? "Day " + runsOut : "OK", runsOut ? "Est. Stock-Out" : "Stock Adequate", "alert", runsOut ? "danger" : "success")}
    ${statCardHtml(res.suggested_order_qty + " units", "Suggested Order", "truck", "success")}
  </div>
  <section class="card mt-4">
    ${runsOut ? `<div class="alert alert-danger mb-4"><span>${ICONS.alert}</span><div class="alert-body"><span class="alert-title">Reorder alert</span> — ${esc(res.drug_name)} will run out in approximately ${runsOut} days at the current consumption rate.</div></div>` : ""}
    <h3 class="mb-3">Demand Forecast — ${esc(res.drug_name)} (next ${res.days} days)</h3>
    <div class="chart-box">${chart}</div>
    <div class="chart-legend">
      <span class="lg-item"><span class="lg-swatch" style="background:#1A56DB"></span> Historical + predicted demand (units/day)</span>
    </div>
    <div class="disclaimer"><span>${ICONS.info}</span><div>AI forecast — model ${esc(res.model || "v1.4")}. Actual demand may vary with season, supply and prescriber behaviour.</div></div>
  </section>`;
}
function statCardHtml(value, label, ic, color) {
  return `<div class="stat-card color-${color}"><div class="stat-icon">${ICONS[ic]}</div>
    <div><div class="stat-value">${value}</div><div class="stat-label">${label}</div></div></div>`;
}
""",
}

# =====================================================================
# LABORATORY — dashboard
# =====================================================================
C["laboratory"]["dashboard.html"] = {
"title": "Laboratory Dashboard",
"body": """
<div class="stat-grid">
  {s1}{s2}{s3}{s4}
</div>
<div class="panel-grid">
  <div>{p_pending}</div>
  <div>{p_recent}{p_quick}</div>
</div>
""".format(
    s1=stat_card("flask", "38", "Tests Today", "+6 vs yesterday", "up"),
    s2=stat_card("clock", "7", "Pending", "3 urgent", "down", "color-warning"),
    s3=stat_card("check", "26", "Completed", "68% done", "up", "color-success"),
    s4=stat_card("alert", "4", "Abnormal Results", "AI flagged", "down", "color-danger"),
    p_pending=panel("Pending Test Requests",
        '<div class="table-wrap" style="max-height:420px;overflow-y:auto"><table class="data-table"><thead><tr><th>Patient</th><th>Test</th><th>Requested By</th><th>Priority</th><th>Status</th></tr></thead><tbody id="labPendingBody"></tbody></table></div>',
        actions='<a class="btn btn-secondary btn-sm" href="test-requests.html">All Requests</a>'),
    p_recent=panel("Recent Results",
        '<div id="labRecentList"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="results.html">Results</a>'),
    p_quick=panel("Quick Actions",
        '<div class="quick-actions" style="grid-template-columns:1fr;margin:0">'
        '<a class="quick-action" href="ai-analyzer.html"><div class="qa-icon" style="background:#F5F3FF;color:#7C3AED">' + icon("brain") + '</div><div><div class="qa-title">AI Analyzer</div><div class="qa-sub">Analyze lab values</div></div></a>'
        '<a class="quick-action" href="test-requests.html"><div class="qa-icon" style="background:#EFF6FF;color:#1A56DB">' + icon("flask") + '</div><div><div class="qa-title">Test Requests</div><div class="qa-sub">Process new tests</div></div></a>'
        '</div>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("laboratory"); initLayout(); loadPageData();
});
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.LAB_REQUESTS).then(r => {
    if (!r.ok) return;
    const pend = r.data.items.filter(l => l.status !== "completed");
    document.getElementById("labPendingBody").innerHTML = pend.length ? pend.map(l => `<tr>
      <td><strong>${esc(l.patient)}</strong></td><td>${esc(l.test)}</td><td>${esc(l.doctor)}</td>
      <td><span class="badge badge-${l.priority === "Urgent" ? "danger" : "neutral"}">${esc(l.priority)}</span></td>
      <td>${l.status === "pending" ? badge("Pending","warning") : badge("In progress","info")}</td></tr>`).join("") : emptyRow(5);
  });
  apiFetch(CONFIG.ENDPOINTS.LAB_RESULTS).then(r => {
    if (!r.ok) return;
    document.getElementById("labRecentList").innerHTML = r.data.items.slice(0, 5).map(res => `
      <div class="feed-item"><div class="feed-icon" style="background:${res.ai_flag === "abnormal" ? "#FEF2F2" : "#ECFDF5"};color:${res.ai_flag === "abnormal" ? "#DC2626" : "#065F46"}">${ICONS.flask}</div>
      <div class="feed-text"><strong>${esc(res.patient)}</strong> · ${esc(res.test)}<div class="feed-time">${formatDate(res.date)}</div></div>
      <span class="badge badge-${res.ai_flag === "abnormal" ? "danger" : "success"}">${res.ai_flag}</span></div>`).join("");
  });
}
""",
}

# =====================================================================
# LABORATORY — test requests
# =====================================================================
C["laboratory"]["test-requests.html"] = {
"title": "Test Requests",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="search-box">%s<input class="form-control" id="trSearch" placeholder="Search patient…"></div>
    <div class="filters">
      <select class="form-control" id="trStatus" style="width:150px"><option value="">All status</option><option>pending</option><option>in-progress</option><option>completed</option></select>
      <select class="form-control" id="trPriority" style="width:140px"><option value="">All priority</option><option>Routine</option><option>Urgent</option></select>
    </div>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="trTable">
      <thead><tr><th class="sortable">ID</th><th class="sortable">Patient</th><th class="sortable">Test</th><th class="sortable">Requested By</th><th class="sortable">Date</th><th class="sortable">Priority</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="trBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), pagination("trPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("laboratory"); initLayout(); loadPageData();
});
let REQS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.LAB_REQUESTS).then(r => {
    if (!r.ok) return; REQS = r.data.items; renderReqs();
    attachDataTable(document.getElementById("trTable"), {
      searchInput: document.getElementById("trSearch"), pagerEl: document.getElementById("trPager"), pageSize: 8,
      filterFn: row => {
        const st = document.getElementById("trStatus").value, pr = document.getElementById("trPriority").value;
        if (st && !row.cells[6].textContent.includes(st)) return false;
        if (pr && !row.cells[5].textContent.includes(pr)) return false;
        return true;
      }
    });
  });
}
function renderReqs() {
  document.getElementById("trBody").innerHTML = REQS.length ? REQS.map(l => `<tr>
    <td><span class="badge badge-neutral">${esc(l.id)}</span></td><td><strong>${esc(l.patient)}</strong></td><td>${esc(l.test)}</td>
    <td>${esc(l.doctor)}</td><td>${formatDate(l.date)}</td>
    <td><span class="badge badge-${l.priority === "Urgent" ? "danger" : "neutral"}">${esc(l.priority)}</span></td>
    <td>${l.status === "completed" ? badge("Completed","success") : l.status === "in-progress" ? badge("In progress","info") : badge("Pending","warning")}</td>
    <td><div class="actions">
      ${l.status === "pending" ? `<button class="btn btn-secondary btn-sm" onclick="startTest('${l.id}')">Start</button>` : ""}
      ${l.status !== "completed" ? `<button class="btn btn-success btn-sm" onclick="completeTest('${l.id}')">${ICONS.check} Complete</button>` : ""}
    </div></td></tr>`).join("") : emptyRow(8);
}
function startTest(id) { const l = REQS.find(x => x.id === id); l.status = "in-progress"; renderReqs(); showToast("Test started","info"); }
function completeTest(id) {
  const l = REQS.find(x => x.id === id);
  l.status = "completed"; renderReqs();
  showToast(l.test + " completed — you can now enter results","success");
}
""",
}

# =====================================================================
# LABORATORY — results
# =====================================================================
C["laboratory"]["results.html"] = {
"title": "Lab Results",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="search-box">%s<input class="form-control" id="lrSearch" placeholder="Search patient…"></div>
    <div class="filters"><select class="form-control" id="lrFlag" style="width:160px"><option value="">All AI flags</option><option>normal</option><option>abnormal</option></select></div>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="lrTable">
      <thead><tr><th class="sortable">Patient</th><th class="sortable">Test Type</th><th class="sortable">Date</th><th class="sortable">Status</th><th class="sortable">AI Flag</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="lrBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), pagination("lrPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("laboratory"); initLayout(); loadPageData();
});
let RESULTS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.LAB_RESULTS).then(r => {
    if (!r.ok) return; RESULTS = r.data.items; renderResults();
    attachDataTable(document.getElementById("lrTable"), {
      searchInput: document.getElementById("lrSearch"), pagerEl: document.getElementById("lrPager"), pageSize: 8,
      filterFn: row => { const f = document.getElementById("lrFlag").value; return !f || row.cells[4].textContent.includes(f); }
    });
  });
}
function renderResults() {
  document.getElementById("lrBody").innerHTML = RESULTS.length ? RESULTS.map(r => `<tr>
    <td><strong>${esc(r.patient)}</strong></td><td>${esc(r.test)}</td><td>${formatDate(r.date)}</td>
    <td>${r.status === "normal" ? badge("Normal","success") : badge("Abnormal","danger")}</td>
    <td>${r.ai_flag === "abnormal" ? badge("AI: Abnormal","danger") : badge("AI: Normal","success")}</td>
    <td><div class="actions">
      <button class="btn-icon primary" title="View" onclick="viewResult('${r.id}')">${ICONS.eye}</button>
      <button class="btn-icon success" title="Send to doctor" onclick="sendToDoctor('${r.id}')">${ICONS.send}</button>
      <button class="btn-icon" title="Print" onclick="printResult('${r.id}')">${ICONS.printer}</button>
    </div></td></tr>`).join("") : emptyRow(6);
}
function viewResult(id) {
  const r = RESULTS.find(x => x.id === id);
  openModal({
    title: "Lab Report — " + r.test,
    body: `<div class="detail-list">
      <div class="detail-item"><span class="k">Patient</span><span class="v">${esc(r.patient)}</span></div>
      <div class="detail-item"><span class="k">Test</span><span class="v">${esc(r.test)}</span></div>
      <div class="detail-item"><span class="k">Date</span><span class="v">${formatDate(r.date)}</span></div></div>
      <h3 class="mt-4 mb-2" style="font-size:15px">Values</h3>
      <table class="data-table"><thead><tr><th>Parameter</th><th>Normal Range</th><th>Value</th><th>Status</th></tr></thead><tbody>
      ${r.values.map(v => `<tr><td>${esc(v.name)}</td><td class="text-sm text-gray" style="color:#6B7280">${esc(v.range)}</td><td><strong>${esc(v.value)}</strong></td>
      <td>${v.status === "normal" ? badge("Normal","success") : badge("Abnormal","danger")}</td></tr>`).join("")}</tbody></table>
      <div class="flex gap-3 mt-4"><button class="btn btn-success" onclick="sendToDoctor('${r.id}')">${ICONS.send} Send to Doctor</button>
      <button class="btn btn-secondary" onclick="printResult('${r.id}')">${ICONS.printer} Print</button></div>`,
    size: "lg"
  });
}
function sendToDoctor(id) { showToast("Result sent to the requesting doctor","success"); }
function printResult(id) {
  const r = RESULTS.find(x => x.id === id);
  const w = window.open("", "_blank");
  w.document.write(`<html><head><title>Lab Report</title><style>body{font-family:monospace;padding:40px}.h{text-align:center;border-bottom:2px solid #000;padding-bottom:10px;margin-bottom:20px}</style></head><body>
    <div class="h"><h2>Wolaita Sodo University Hospital</h2><p>Laboratory Report — ${r.test}</p></div>
    <p><strong>Patient:</strong> ${r.patient} &nbsp; <strong>Date:</strong> ${formatDate(r.date)}</p>
    <table width="100%" border="1" cellpadding="8" style="border-collapse:collapse;margin-top:16px">
    <tr><th align="left">Parameter</th><th align="left">Normal Range</th><th align="left">Value</th><th align="left">Status</th></tr>
    ${r.values.map(v => `<tr><td>${v.name}</td><td>${v.range}</td><td>${v.value}</td><td>${v.status}</td></tr>`).join("")}</table>
    <p style="margin-top:24px">Signed: ______________________</p></body></html>`);
  w.document.close(); w.print();
}
""",
}

# =====================================================================
# LABORATORY — ai-analyzer (Module 3)
# =====================================================================
C["laboratory"]["ai-analyzer.html"] = {
"title": "AI Lab Result Analyzer",
"body": """
<div class="alert alert-info mb-4"><span>%s</span>
  <div class="alert-body"><span class="alert-title">Module 3 — Lab Analyzer</span> — enter patient values and the AI compares them to reference ranges, flags abnormalities and suggests conditions.</div></div>
<div class="panel-grid cols-2">
  <section class="card">
    <h3 class="mb-3">1. Select Test Type</h3>
    <div class="chip-group" id="testTypes">
      <span class="chip selected" data-type="blood">Blood Count</span>
      <span class="chip" data-type="liver">Liver Function</span>
      <span class="chip" data-type="kidney">Kidney Function</span>
      <span class="chip" data-type="thyroid">Thyroid</span>
      <span class="chip" data-type="diabetes">Diabetes</span>
    </div>
    <div class="form-group mt-4"><label>Patient</label><select class="form-control" id="anPatient"><option>Abel Mekonnen (P-1001)</option><option>Hana Wolde (P-1002)</option><option>Selam Tadesse (P-1004)</option><option>Ruth Gebre (P-1006)</option><option>Yohannes Mamo (P-1009)</option></select></div>
    <h3 class="mb-3">2. Enter Values</h3>
    <div id="labForm"></div>
    <button class="btn btn-primary btn-lg btn-block" id="btnAnalyze">%s Analyze Results</button>
  </section>
  <div>
    <div id="labResult"></div>
  </div>
</div>
""" % (icon("info"), icon("brain")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("laboratory"); initLayout(); loadPageData();
});
const FIELDS = {
  blood: [["hemoglobin","Hemoglobin (g/dL)","14.2"],["wbc","WBC (×10³/µL)","6.8"],["rbc","RBC (×10⁶/µL)","4.6"],["platelets","Platelets (×10³/µL)","240"]],
  liver: [["alt","ALT (U/L)","45"],["ast","AST (U/L)","38"]],
  kidney: [["creatinine","Creatinine (mg/dL)","1.1"]],
  thyroid: [["tsh","TSH (mIU/L)","3.2"]],
  diabetes: [["glucose","Glucose Fasting (mg/dL)","95"]]
};
let currentType = "blood";
function loadPageData() {
  document.querySelectorAll("#testTypes .chip").forEach(c => c.addEventListener("click", () => {
    document.querySelectorAll("#testTypes .chip").forEach(x => x.classList.remove("selected"));
    c.classList.add("selected"); currentType = c.dataset.type; renderLabForm();
  }));
  document.getElementById("btnAnalyze").addEventListener("click", analyze);
  renderLabForm();
}
function renderLabForm() {
  document.getElementById("labForm").innerHTML = `<div class="form-row-3">${FIELDS[currentType].map(f =>
    `<div class="form-group"><label class="text-sm">${f[1]}</label><input class="form-control" data-key="${f[0]}" value="${f[2]}"></div>`).join("")}</div>`;
}
function analyze() {
  const values = {};
  document.querySelectorAll("#labForm input").forEach(i => { values[i.dataset.key] = i.value; });
  document.getElementById("labResult").innerHTML = `<section class="card"><div class="loading-area"><div class="spinner"></div><div>AI analyzing lab values…</div></div></section>`;
  analyzeLabResult({ test_type: currentType, patient: document.getElementById("anPatient").value, values }, renderLabResult);
}
function renderLabResult(res) {
  const overall = res.overall === "abnormal";
  document.getElementById("labResult").innerHTML = `<section class="card">
    <div class="flex-between wrap" style="gap:10px"><h3>Analysis Result</h3>
      ${overall ? badge("Overall: Abnormal","danger") : badge("Overall: Normal","success")}</div>
    <table class="data-table mt-4"><thead><tr><th>Parameter</th><th>Normal Range</th><th>Patient Value</th><th>Status</th><th>Deviation</th></tr></thead><tbody>
    ${res.rows.map(r => `<tr><td>${esc(r.name)}</td><td class="text-sm text-gray" style="color:#6B7280">${esc(r.range)}</td>
      <td><strong>${esc(r.value)}</strong></td>
      <td>${r.status === "normal" ? badge("Normal","success") : r.status === "high" ? badge("High","danger") : badge("Low","warning")}</td>
      <td class="text-sm">${esc(r.deviation)}</td></tr>`).join("")}</tbody></table>
    <h3 class="mt-4 mb-2" style="font-size:15px">Suspected Conditions</h3>
    <div class="feed">${res.conditions.map(c => `<div class="feed-item"><div class="feed-icon" style="background:${overall ? "#FEF2F2" : "#ECFDF5"};color:${overall ? "#DC2626" : "#065F46"}">${overall ? ICONS.alert : ICONS.check}</div>
      <div class="feed-text">${esc(c)}</div></div>`).join("")}</div>
    <div class="disclaimer"><span>${ICONS.info}</span><div>AI suggestions only — model ${esc(res.model || "v2.0")}. Final interpretation by the laboratory technician or doctor.</div></div>
    <div class="form-actions mt-4"><button class="btn btn-primary" onclick="generateReport()">${ICONS["file-text"]} Generate Report</button></div>
  </section>`;
}
function generateReport() {
  const w = window.open("", "_blank");
  w.document.write(`<html><head><title>AI Lab Report</title><style>body{font-family:monospace;padding:40px}.h{text-align:center;border-bottom:2px solid #000;padding-bottom:10px;margin-bottom:20px}</style></head><body>
    <div class="h"><h2>Wolaita Sodo University Hospital</h2><p>AI-Assisted Laboratory Report</p></div>
    <p><strong>Patient:</strong> ${document.getElementById("anPatient").value}</p>
    <p><strong>Date:</strong> ${formatDateTime(new Date().toISOString())}</p>
    <p><strong>Generated by:</strong> MedIQ Pro AI Analyzer (Module 3)</p>
    <p style="margin-top:16px">This report was auto-generated. Please verify with clinical judgment.</p></body></html>`);
  w.document.close(); w.print();
  showToast("Report generated","success");
}
""",
}
