# -*- coding: utf-8 -*-
"""MedIQ Pro page bodies — Part B: doctor + nurse."""
from frontend_lib import icon, stat_card, panel, badge, pagination, empty_row

B = {"doctor": {}, "nurse": {}}

# =====================================================================
# DOCTOR — dashboard
# =====================================================================
B["doctor"]["dashboard.html"] = {
"title": "Doctor Dashboard",
"body": """
<div class="stat-grid">
  {s1}{s2}{s3}{s4}
</div>
<div class="panel-grid">
  <div>
    {p_appts}
    <div class="mt-5">{p_lab}</div>
  </div>
  <div>{p_ai}{p_quick}</div>
</div>
""".format(
    s1=stat_card("users", "14", "Patients Today", "+3 vs yesterday", "up"),
    s2=stat_card("clock", "18 min", "Avg Consultation", "−2 min", "up", "color-info"),
    s3=stat_card("file-text", "22", "Prescriptions Written", "+5 this week", "up", "color-success"),
    s4=stat_card("alert", "3", "Critical AI Alerts", "1 urgent", "down", "color-danger"),
    p_appts=panel("Today's Appointments",
        '<div class="table-wrap" style="max-height:360px;overflow-y:auto"><table class="data-table" id="docApptsTable"><thead><tr><th>Time</th><th>Patient</th><th>Type</th><th>Status</th></tr></thead><tbody id="docApptsBody"></tbody></table></div>',
        actions='<a class="btn btn-secondary btn-sm" href="appointments.html">Manage</a>'),
    p_lab=panel("Pending Lab Results",
        '<div id="docLabList"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="patients.html">Patients</a>'),
    p_ai=panel("AI Alerts — Critical Patients",
        '<div id="docAiAlerts"></div>',
        sub='<div class="sub">Flagged by vitals AI (Module 4)</div>'),
    p_quick=panel("Quick Actions",
        '<div class="quick-actions" style="grid-template-columns:1fr;margin:0">'
        '<a class="quick-action" href="ai-diagnosis.html"><div class="qa-icon" style="background:#F5F3FF;color:#7C3AED">' + icon("brain") + '</div><div><div class="qa-title">AI Diagnosis</div><div class="qa-sub">Clinical decision support</div></div></a>'
        '<a class="quick-action" href="consultation.html"><div class="qa-icon" style="background:#EFF6FF;color:#1A56DB">' + icon("stethoscope") + '</div><div><div class="qa-title">New Consultation</div><div class="qa-sub">Start a patient visit</div></div></a>'
        '<a class="quick-action" href="prescriptions.html"><div class="qa-icon" style="background:#ECFDF5;color:#065F46">' + icon("file-text") + '</div><div><div class="qa-title">Prescriptions</div><div class="qa-sub">Write &amp; manage</div></div></a>'
        '</div>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("doctor"); initLayout(); loadPageData();
});
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.APPOINTMENTS).then(r => {
    if (!r.ok) return;
    const rows = r.data.items.filter(a => a.status !== "cancelled").slice(0, 8);
    document.getElementById("docApptsBody").innerHTML = rows.map(a => `<tr>
      <td><span class="time-pill">${a.time}</span></td><td><strong>${esc(a.patient)}</strong><div class="text-sm text-gray" style="color:#6B7280">${esc(a.dept)}</div></td>
      <td>${esc(a.type)}</td><td>${statusBadge(a.status)}</td></tr>`).join("") || emptyRow(4);
  });
  apiFetch(CONFIG.ENDPOINTS.LAB_REQUESTS).then(r => {
    if (!r.ok) return;
    const pend = r.data.items.filter(l => l.status === "pending");
    document.getElementById("docLabList").innerHTML = pend.length ? pend.map(l => `
      <div class="feed-item"><div class="feed-icon" style="background:#F0F9FF;color:#0369A1">${ICONS.flask}</div>
      <div class="feed-text"><strong>${esc(l.patient)}</strong> · ${esc(l.test)}
      <div class="feed-time">Requested by ${esc(l.doctor)}</div></div>
      <span class="badge badge-warning">${esc(l.priority)}</span></div>`).join("")
      : '<div class="empty-state">No pending lab results 🎉</div>';
  });
  const alerts = [
    { patient: "Selam Tadesse", vital: "BP 158/98 mmHg", sev: "critical", note: "Hypertensive crisis risk" },
    { patient: "Ruth Gebre", vital: "Creatinine ↑ 2.1", sev: "critical", note: "Renal function declining" },
    { patient: "Yohannes Mamo", vital: "Glucose 312 mg/dL", sev: "warning", note: "Uncontrolled diabetes" }
  ];
  document.getElementById("docAiAlerts").innerHTML = alerts.map(a => `
    <div class="feed-item"><div class="feed-icon" style="background:${a.sev==="critical"?"#FEF2F2":"#FFFBEB"};color:${a.sev==="critical"?"#DC2626":"#D97706"}">${ICONS.alert}</div>
    <div class="feed-text"><strong>${esc(a.patient)}</strong><div>${esc(a.vital)}</div>
    <div class="feed-time">${esc(a.note)}</div></div>
    <span class="badge badge-${a.sev==="critical"?"danger":"warning"}">${a.sev}</span></div>`).join("");
}
function statusBadge(s) {
  const m = { confirmed:["success","Confirmed"], "checked-in":["info","Checked in"], completed:["neutral","Completed"], cancelled:["danger","Cancelled"] };
  const b = m[s] || ["neutral", s];
  return `<span class="badge badge-${b[0]}">${b[1]}</span>`;
}
""",
}

# =====================================================================
# DOCTOR — patients
# =====================================================================
B["doctor"]["patients.html"] = {
"title": "My Patients",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar">
    <div class="search-box">%s<input class="form-control" id="ptSearch" placeholder="Search name or ID…"></div>
    <div class="filters">
      <select class="form-control" id="ptFilter" style="width:170px"><option value="">All conditions</option><option>Hypertension</option><option>Diabetes Type 2</option><option>Asthma</option><option>Heart Disease</option><option>Chronic Kidney Disease</option><option>Thyroid Disorder</option></select>
      <span class="badge badge-info" id="ptCount">0 patients</span>
    </div>
  </div>
  <div class="table-wrap">
    <table class="data-table" id="patientsTable">
      <thead><tr><th class="sortable">Patient ID</th><th class="sortable">Name</th><th class="sortable">Age</th><th class="sortable">Gender</th><th class="sortable">Blood</th><th class="sortable">Condition</th><th class="sortable">Last Visit</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="patientsBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), pagination("ptPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("doctor"); initLayout(); loadPageData();
});
let PATIENTS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.PATIENTS).then(r => {
    if (!r.ok) return;
    PATIENTS = r.data.items;
    renderPatients();
    attachDataTable(document.getElementById("patientsTable"), {
      searchInput: document.getElementById("ptSearch"), pagerEl: document.getElementById("ptPager"), pageSize: 8,
      filterFn: (row) => {
        const c = document.getElementById("ptFilter").value;
        return !c || row.cells[5].textContent.includes(c);
      },
      onRender: (n) => document.getElementById("ptCount").textContent = n + " patients"
    });
  });
}
function renderPatients() {
  document.getElementById("patientsBody").innerHTML = PATIENTS.length ? PATIENTS.map(p => `<tr>
    <td><span class="badge badge-neutral">${esc(p.id)}</span></td>
    <td><div class="flex" style="gap:10px"><span class="avatar-sm">${initialsOf(p.first_name + " " + p.last_name)}</span><strong>${esc(p.first_name + " " + p.last_name)}</strong></div></td>
    <td>${p.age}</td><td>${esc(p.gender)}</td><td><span class="badge badge-primary">${esc(p.blood)}</span></td>
    <td>${esc(p.condition || "—")}</td><td>${formatDate(p.last_visit)}</td>
    <td><div class="actions"><button class="btn-icon primary" title="View" onclick="viewPatient('${p.id}')">${ICONS.eye}</button>
    <a class="btn-icon success" title="Consult" href="consultation.html?patient=${p.id}">${ICONS.stethoscope}</a></div></td></tr>`).join("") : emptyRow(8);
}
function viewPatient(id) {
  const p = PATIENTS.find(x => x.id === id);
  openModal({
    title: "Patient Record — " + p.id,
    body: `<div class="flex" style="gap:14px;margin-bottom:16px"><span class="avatar" style="width:52px;height:52px;font-size:20px">${initialsOf(p.first_name + " " + p.last_name)}</span>
      <div><div style="font-size:18px;font-weight:700">${esc(p.first_name + " " + p.last_name)}</div>
      <div class="text-sm text-gray" style="color:#6B7280">${p.age} yrs · ${esc(p.gender)} · Blood ${esc(p.blood)}</div></div></div>
      <div class="detail-list">
        <div class="detail-item"><span class="k">Phone</span><span class="v">${esc(p.phone)}</span></div>
        <div class="detail-item"><span class="k">Address</span><span class="v">${esc(p.address)}</span></div>
        <div class="detail-item"><span class="k">Emergency Contact</span><span class="v">${esc(p.emergency)}</span></div>
        <div class="detail-item"><span class="k">Chronic Condition</span><span class="v">${esc(p.condition || "None")}</span></div>
        <div class="detail-item"><span class="k">Last Visit</span><span class="v">${formatDate(p.last_visit)}</span></div>
      </div>
      <h3 class="mt-4 mb-2" style="font-size:15px">Recent Encounters</h3>
      ${encounters(p.id)}
      <div class="flex gap-3 mt-4"><a class="btn btn-primary" href="consultation.html?patient=${p.id}">${ICONS.stethoscope} Start Consultation</a></div>`,
    size: "lg"
  });
}
function encounters(id) {
  const data = {
    "P-1001": [["11/08/2026","Follow-up — hypertension review","Dr. Daniel Alemu"],["05/08/2026","Prescribed Amlodipine 5mg","Dr. Daniel Alemu"]],
    "P-1004": [["09/08/2026","ECG + cardiac consultation","Dr. Meron Assefa"],["02/08/2026","Lipid profile ordered","Dr. Meron Assefa"]]
  };
  const list = data[id];
  if (!list) return '<div class="empty-state" style="padding:20px">No prior encounters.</div>';
  return `<div class="feed">${list.map(e => `<div class="feed-item"><div class="feed-icon" style="background:#EFF6FF;color:#1A56DB">${ICONS["file-text"]}</div>
    <div class="feed-text"><strong>${e[1]}</strong><div class="feed-time">${e[0]} · ${e[2]}</div></div></div>`).join("")}</div>`;
}
""",
}

# =====================================================================
# DOCTOR — consultation
# =====================================================================
B["doctor"]["consultation.html"] = {
"title": "Patient Consultation",
"body": """
<div class="card mb-4">
  <div class="flex-between wrap" style="gap:12px">
    <div><h3 style="font-size:16px">Select Patient</h3><p class="text-sm text-gray" style="color:#6B7280">Search by name or patient ID</p></div>
    <select class="form-control" id="patientSelect" style="width:320px"><option value="">— Choose a patient —</option></select>
  </div>
  <div id="patientSummary" class="mt-4"></div>
</div>
<div class="panel-grid cols-2">
  <section class="card">
    <h3 class="mb-3">Diagnosis & Plan</h3>
    <div class="form-group"><label>Diagnosis (free text)</label><textarea class="form-control" id="diagText" rows="3" placeholder="e.g. Essential hypertension, stage 2…"></textarea></div>
    <div class="form-group"><label>AI Suggestions</label><div class="chip-group" id="aiSuggestChips"></div>
      <div class="hint">Click a suggestion to insert it into the diagnosis field.</div></div>
    <div class="form-group"><label>Clinical Notes</label><textarea class="form-control" id="clinNotes" rows="4" placeholder="Examination findings, plan, follow-up…"></textarea></div>
    <div class="form-group"><label>Order Lab Tests</label>
      <div class="chip-group" id="labChips">
        <span class="chip" data-lab="Complete Blood Count">Complete Blood Count</span>
        <span class="chip" data-lab="Fasting Blood Sugar">Fasting Blood Sugar</span>
        <span class="chip" data-lab="Liver Function">Liver Function</span>
        <span class="chip" data-lab="Kidney Function">Kidney Function</span>
        <span class="chip" data-lab="Lipid Profile">Lipid Profile</span>
        <span class="chip" data-lab="Thyroid Panel">Thyroid Panel</span>
        <span class="chip" data-lab="Urinalysis">Urinalysis</span>
        <span class="chip" data-lab="Malaria Test">Malaria Test</span>
      </div></div>
    <div class="form-actions"><button class="btn btn-primary btn-lg" id="submitConsult" style="width:100%%">%s Submit Consultation</button></div>
  </section>
  <div>
    <section class="card mb-4">
      <h3 class="mb-3">Prescription Builder</h3>
      <div class="form-row">
        <div class="form-group"><label>Drug</label><input class="form-control" id="rxDrug" list="drugList" placeholder="Search drug…">
          <datalist id="drugList"></datalist></div>
        <div class="form-group"><label>Dosage</label><select class="form-control" id="rxDose"><option>1 tablet</option><option>½ tablet</option><option>2 tablets</option><option>5 ml</option><option>10 ml</option><option>2 puffs</option><option>20 units</option></select></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Frequency</label><select class="form-control" id="rxFreq"><option>Once daily</option><option>Twice daily</option><option>Three times daily</option><option>Every 6 hours</option><option>As needed</option><option>At bedtime</option></select></div>
        <div class="form-group"><label>Duration</label><select class="form-control" id="rxDur"><option>3 days</option><option>5 days</option><option>7 days</option><option>14 days</option><option>30 days</option><option>60 days</option><option>90 days</option></select></div>
      </div>
      <button class="btn btn-outline btn-block" id="addRx">%s Add to Prescription</button>
      <div id="rxList" class="mt-4"></div>
      <button class="btn btn-secondary btn-block mt-4" id="checkInteract">%s Check Drug Interactions</button>
      <div id="interactResult" class="mt-3"></div>
    </section>
    <section class="card">
      <h3 class="mb-3">Drug Interaction — Module 2</h3>
      <p class="text-sm text-gray" style="color:#6B7280">The AI checks every pair of drugs added to this prescription and flags any interaction before you submit.</p>
      <div class="disclaimer mt-3"><span>%s</span><div>AI suggestions only. Final prescribing decisions by the clinician.</div></div>
    </section>
  </div>
</div>
""" % (icon("check"), icon("plus"), icon("zap"), icon("info")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("doctor"); initLayout(); loadPageData();
});
let PATIENTS = [], DRUGS = [], rxItems = [], labs = new Set(), selPatient = null;
const DRUG_CATALOG = ["Paracetamol 500mg","Amlodipine 5mg","Metformin 500mg","Insulin Glargine","Amoxicillin 250mg","Salbutamol Inhaler","Atorvastatin 20mg","Bisoprolol 2.5mg","Enalapril 10mg","Aspirin 81mg","Furosemide 40mg","Artemether/Lumefantrine","Ceftriaxone 1g","Hydrocortisone 100mg","ORS Sachets","Warfarin 5mg","Digoxin 0.25mg"];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.PATIENTS).then(r => {
    if (!r.ok) return;
    PATIENTS = r.data.items;
    document.getElementById("patientSelect").innerHTML = '<option value="">— Choose a patient —</option>' +
      PATIENTS.map(p => `<option value="${p.id}">${esc(p.id)} — ${esc(p.first_name + " " + p.last_name)}</option>`).join("");
    const qp = new URLSearchParams(location.search).get("patient");
    if (qp) { document.getElementById("patientSelect").value = qp; showPatient(qp); }
  });
  document.getElementById("drugList").innerHTML = DRUG_CATALOG.map(d => `<option value="${d}">`).join("");
  document.getElementById("aiSuggestChips").innerHTML = [
    "Essential hypertension","Type 2 diabetes mellitus","Acute upper respiratory infection","Gastroenteritis","Malaria (unconfirmed)","Asthma exacerbation"
  ].map(s => `<span class="chip" onclick="insertDiag('${s}')">${s}</span>`).join("");
  document.querySelectorAll("[data-lab]").forEach(c => c.addEventListener("click", () => {
    c.classList.toggle("selected");
    if (c.classList.contains("selected")) labs.add(c.dataset.lab); else labs.delete(c.dataset.lab);
  }));
  document.getElementById("patientSelect").addEventListener("change", e => showPatient(e.target.value));
}
function showPatient(id) {
  selPatient = PATIENTS.find(p => p.id === id);
  if (!selPatient) { document.getElementById("patientSummary").innerHTML = ""; return; }
  const p = selPatient;
  document.getElementById("patientSummary").innerHTML = `<div class="flex-between wrap" style="gap:14px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:12px;padding:16px">
    <div class="flex" style="gap:14px"><span class="avatar">${initialsOf(p.first_name + " " + p.last_name)}</span>
      <div><div style="font-weight:700;font-size:16px">${esc(p.first_name + " " + p.last_name)}</div>
      <div class="text-sm text-gray" style="color:#6B7280">${p.age} yrs · ${esc(p.gender)} · ${esc(p.id)}</div></div></div>
    <div class="flex wrap" style="gap:14px">
      <div><div class="text-sm text-gray" style="color:#6B7280">Blood Type</div><strong>${esc(p.blood)}</strong></div>
      <div><div class="text-sm text-gray" style="color:#6B7280">Phone</div><strong>${esc(p.phone)}</strong></div>
      <div><div class="text-sm text-gray" style="color:#6B7280">Chronic</div><span class="badge badge-${p.condition ? "warning" : "success"}">${esc(p.condition || "None")}</span></div>
    </div></div>`;
}
function insertDiag(s) {
  const t = document.getElementById("diagText");
  t.value = t.value ? t.value + "; " + s : s;
}
document.getElementById("addRx").addEventListener("click", () => {
  const drug = document.getElementById("rxDrug").value.trim();
  if (!drug) { showToast("Enter a drug name first", "error"); return; }
  const item = { drug, dose: document.getElementById("rxDose").value, freq: document.getElementById("rxFreq").value, dur: document.getElementById("rxDur").value };
  if (rxItems.some(r => r.drug.toLowerCase() === drug.toLowerCase())) { showToast("Drug already in prescription", "warning"); return; }
  rxItems.push(item);
  document.getElementById("rxDrug").value = "";
  renderRx();
});
function renderRx() {
  document.getElementById("rxList").innerHTML = rxItems.length ? `<table class="data-table"><thead><tr><th>Drug</th><th>Dosage</th><th>Frequency</th><th>Duration</th><th></th></tr></thead><tbody>
    ${rxItems.map((r, i) => `<tr><td><strong>${esc(r.drug)}</strong></td><td>${esc(r.dose)}</td><td>${esc(r.freq)}</td><td>${esc(r.dur)}</td>
    <td style="text-align:right"><button class="btn-icon danger" onclick="rxItems.splice(${i},1);renderRx()">${ICONS.trash}</button></td></tr>`).join("")}</tbody></table>` : '<p class="text-gray" style="color:#6B7280">No drugs added yet.</p>';
}
document.getElementById("checkInteract").addEventListener("click", () => {
  if (rxItems.length < 2) { showToast("Add at least 2 drugs to check interactions", "warning"); return; }
  showLoading("Checking drug interactions…");
  const pairs = [];
  for (let i = 0; i < rxItems.length; i++) for (let j = i + 1; j < rxItems.length; j++) pairs.push([rxItems[i].drug, rxItems[j].drug]);
  setTimeout(() => {
    hideLoading();
    let html = "";
    pairs.forEach(([a, b]) => {
      checkDrugInteraction({ drug_a: a, drug_b: b }, res => {
        const lv = res.level;
        const cls = lv === "severe" ? "severity-severe" : lv === "moderate" ? "severity-moderate" : "severity-safe";
        const ico = lv === "severe" ? ICONS.alert : lv === "moderate" ? ICONS.info : ICONS.check;
        html += `<div class="severity-card ${cls} mb-3"><div class="flex" style="gap:10px"><span>${ico}</span>
          <div><strong>${esc(a)}</strong> + <strong>${esc(b)}</strong> → <strong>${res.title}</strong><br>
          <span style="font-size:13px">${esc(res.mechanism)}</span></div></div></div>`;
        document.getElementById("interactResult").innerHTML = html;
      });
    });
    showToast("Interaction check complete", "success");
  }, 700);
});
document.getElementById("submitConsult").addEventListener("click", () => {
  if (!selPatient) { showToast("Select a patient first", "error"); return; }
  if (!document.getElementById("diagText").value.trim() && !rxItems.length) { showToast("Add a diagnosis or prescription", "warning"); return; }
  showLoading("Submitting consultation…");
  setTimeout(() => {
    hideLoading();
    showToast("Consultation saved to patient record", "success");
    rxItems = []; labs.clear(); renderRx();
    document.getElementById("diagText").value = ""; document.getElementById("clinNotes").value = "";
    document.querySelectorAll("[data-lab].selected").forEach(c => c.classList.remove("selected"));
    document.getElementById("interactResult").innerHTML = "";
  }, 900);
});
""",
}

# =====================================================================
# DOCTOR — ai-diagnosis
# =====================================================================
B["doctor"]["ai-diagnosis.html"] = {
"title": "AI Diagnosis",
"body": """
<div class="alert alert-warning mb-4"><span>%s</span>
  <div class="alert-body"><span class="alert-title">Disclaimer</span> — AI suggestions only. Final diagnosis is made by the doctor. Always verify AI output with clinical judgment.</div></div>
<div class="panel-grid cols-2">
  <section class="card">
    <h3 class="mb-1">Symptoms</h3>
    <p class="text-sm text-gray mb-3" style="color:#6B7280">Describe symptoms or tap common ones to add them.</p>
    <div class="form-group"><textarea class="form-control" id="symText" rows="4" placeholder="e.g. Fever for 3 days, chills, headache, muscle ache…"></textarea></div>
    <div class="form-group"><label>Common Symptoms</label><div class="chip-group" id="symChips"></div></div>
    <div class="form-group"><label>Patient Vitals</label>
      <div class="form-row-3">
        <div class="form-group"><label class="text-sm">Heart Rate</label><input class="form-control" type="number" id="vHr" placeholder="bpm" value="88"></div>
        <div class="form-group"><label class="text-sm">BP Systolic</label><input class="form-control" type="number" id="vSys" placeholder="mmHg" value="132"></div>
        <div class="form-group"><label class="text-sm">BP Diastolic</label><input class="form-control" type="number" id="vDia" placeholder="mmHg" value="86"></div>
        <div class="form-group"><label class="text-sm">Temperature</label><input class="form-control" type="number" id="vTemp" placeholder="°C" value="37.4"></div>
        <div class="form-group"><label class="text-sm">SpO2</label><input class="form-control" type="number" id="vSpo2" placeholder="%%" value="97"></div>
        <div class="form-group"><label class="text-sm">Resp. Rate</label><input class="form-control" type="number" id="vRr" placeholder="/min" value="18"></div>
      </div></div>
    <div class="form-group"><label>Patient History</label>
      <div class="chip-group" id="histChips"></div></div>
    <button class="btn btn-primary btn-lg btn-block" id="btnAnalyze">%s Analyze with AI</button>
  </section>
  <div>
    <div id="aiResultPanel"></div>
  </div>
</div>
""" % (icon("info"), icon("brain")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("doctor"); initLayout(); loadPageData();
});
const SYMPTOMS = ["Fever","Chills","Headache","Cough","Sore throat","Fatigue","Nausea","Diarrhea","Chest pain","Shortness of breath","Joint pain","Night sweats","Loss of appetite","Abdominal pain"];
const HISTORY = ["Diabetic","Hypertensive","Asthmatic","Anemic","Smoker","Allergies","Heart Disease","Kidney Disease","Pregnant","TB History"];
function loadPageData() {
  document.getElementById("symChips").innerHTML = SYMPTOMS.map(s => `<span class="chip" data-sym="${s}" onclick="toggleChip(this,'symText')">${s}</span>`).join("");
  document.getElementById("histChips").innerHTML = HISTORY.map(h => `<span class="chip" data-sym="${h}" onclick="this.classList.toggle('selected')">${h}</span>`).join("");
  document.getElementById("btnAnalyze").addEventListener("click", analyze);
}
function toggleChip(chip, fieldId) {
  chip.classList.toggle("selected");
  const t = document.getElementById(fieldId);
  const sym = chip.dataset.sym;
  const cur = t.value.split(",").map(s => s.trim()).filter(Boolean);
  if (chip.classList.contains("selected") && !cur.includes(sym)) cur.push(sym);
  else if (!chip.classList.contains("selected")) t.value = cur.filter(s => s !== sym).join(", ");
  if (chip.classList.contains("selected")) t.value = cur.join(", ");
}
function analyze() {
  const symptoms = document.getElementById("symText").value.trim();
  if (!symptoms) { showToast("Please describe the symptoms first", "error"); return; }
  const history = Array.from(document.querySelectorAll("#histChips .selected")).map(c => c.dataset.sym);
  document.getElementById("aiResultPanel").innerHTML = `<section class="card">
    <h3 class="mb-3">Analyzing…</h3>
    <div class="skeleton skeleton-line" style="width:80%"></div><div class="skeleton skeleton-line" style="width:60%"></div>
    <div class="skeleton skeleton-line" style="width:90%"></div><div class="skeleton skeleton-line" style="width:45%"></div></section>`;
  predictDisease({ symptoms, vitals: {
      hr: document.getElementById("vHr").value, sys: document.getElementById("vSys").value,
      dia: document.getElementById("vDia").value, temp: document.getElementById("vTemp").value,
      spo2: document.getElementById("vSpo2").value, rr: document.getElementById("vRr").value
    }, history }, renderResult);
}
function renderResult(res) {
  const panel = document.getElementById("aiResultPanel");
  const cards = res.predictions.map(p => {
    const cls = confidenceColor(p.confidence);
    return `<div class="ai-result-card mb-3">
      <div class="flex-between wrap" style="gap:10px"><div><div style="font-weight:700;font-size:16px">${esc(p.disease)}</div>
      <div class="text-sm text-gray" style="color:#6B7280;margin-top:2px">${esc(p.description)}</div></div>
      <span class="badge badge-${p.urgency === "Emergency" ? "danger" : "warning"}">${esc(p.urgency)}</span></div>
      <div class="ai-confidence"><span class="pct" style="color:var(--primary)">${p.confidence}%</span>
      <div class="progress"><div class="progress-bar ${cls}" style="width:${p.confidence}%"></div></div></div>
    </div>`;
  }).join("");
  panel.innerHTML = `<section class="card">
    <div class="flex-between wrap" style="gap:10px"><h3>Prediction Results</h3>
      <span class="badge badge-neutral">Model ${esc(res.model || "v1")}</span></div>
    <p class="text-sm text-gray mb-4" style="color:#6B7280">Top ${res.predictions.length} conditions ranked by confidence.</p>
    ${cards}
    <div class="disclaimer"><span>${ICONS.info}</span><div>AI suggestions only. Final diagnosis by doctor. This output should not replace clinical judgment.</div></div>
    <div class="form-actions mt-4"><button class="btn btn-secondary" id="saveDx">${ICONS.download} Save to Patient Record</button>
    <button class="btn btn-primary" onclick="analyze()">${ICONS.refresh} Re-run</button></div></section>`;
  document.getElementById("saveDx").addEventListener("click", () => showToast("Prediction saved to patient record", "success"));
}
""",
}

# =====================================================================
# DOCTOR — prescriptions
# =====================================================================
B["doctor"]["prescriptions.html"] = {
"title": "Prescriptions",
"body": """
<div class="flex-between mb-4"><p class="page-intro" style="margin:0">Prescriptions you have written.</p>
  <button class="btn btn-primary" id="btnNewRx">%s New Prescription</button></div>
<div class="card" style="padding:0">
  <div class="table-toolbar"><div class="search-box">%s<input class="form-control" id="rxSearch" placeholder="Search patient…"></div>
    <span class="badge badge-info" id="rxCount">0 prescriptions</span></div>
  <div class="table-wrap">
    <table class="data-table" id="rxTable">
      <thead><tr><th class="sortable">ID</th><th class="sortable">Patient</th><th class="sortable">Date</th><th>Medications</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="rxBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("plus"), icon("search"), pagination("rxPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("doctor"); initLayout(); loadPageData();
});
let RX = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.PRESCRIPTIONS).then(r => {
    if (!r.ok) return;
    RX = r.data.items; renderRx();
    attachDataTable(document.getElementById("rxTable"), {
      searchInput: document.getElementById("rxSearch"), pagerEl: document.getElementById("rxPager"), pageSize: 8,
      onRender: n => document.getElementById("rxCount").textContent = n + " prescriptions"
    });
  });
  document.getElementById("btnNewRx").addEventListener("click", newRxModal);
}
function renderRx() {
  document.getElementById("rxBody").innerHTML = RX.length ? RX.map(r => `<tr>
    <td><span class="badge badge-neutral">${esc(r.id)}</span></td><td><strong>${esc(r.patient)}</strong><div class="text-sm text-gray" style="color:#6B7280">Dr. ${esc(r.doctor.split(" ").slice(-1)[0])}</div></td>
    <td>${formatDate(r.date)}</td><td><span class="badge badge-primary">${r.drugs.length} drug${r.drugs.length>1?"s":""}</span> <span class="text-sm text-gray" style="color:#6B7280">${esc(r.drugs.map(d=>d.name).join(", ").slice(0,40))}…</span></td>
    <td>${r.status === "active" ? badge("Active","success") : r.status === "dispensed" ? badge("Dispensed","info") : badge(r.status,"neutral")}</td>
    <td><div class="actions"><button class="btn-icon primary" title="View" onclick="viewRx('${r.id}')">${ICONS.eye}</button>
    <button class="btn-icon" title="Print" onclick="printRx('${r.id}')">${ICONS.printer}</button></div></td></tr>`).join("") : emptyRow(6);
}
function newRxModal() {
  openModal({
    title: "New Prescription",
    body: `<div class="form-group"><label>Patient <span class="req">*</span></label><input class="form-control" id="rxPat" list="rxPats" placeholder="Search patient…"><datalist id="rxPats">${PATIENT_OPTS()}</datalist></div>
      <div class="form-group"><label>Medication <span class="req">*</span></label><input class="form-control" id="rxMed" placeholder="e.g. Amoxicillin 250mg"></div>
      <div class="form-row">
        <div class="form-group"><label>Dosage</label><input class="form-control" id="rxD1" value="1 tablet"></div>
        <div class="form-group"><label>Frequency</label><input class="form-control" id="rxF1" value="Twice daily"></div>
      </div>
      <div class="form-group"><label>Duration</label><input class="form-control" id="rxDur1" value="7 days"></div>
      <div class="form-group"><label>Notes</label><textarea class="form-control" rows="2" id="rxNote" placeholder="e.g. Take after meals"></textarea></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveRx">Save Prescription</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveRx").onclick = () => {
      const pat = ov.querySelector("#rxPat").value.trim();
      if (!pat) { showToast("Patient is required","error"); return; }
      RX.unshift({ id: uid("RX"), patient: pat, doctor: getUserName(), date: todayStr(), status: "active",
        drugs: [{ name: ov.querySelector("#rxMed").value || "Medication", dose: ov.querySelector("#rxD1").value, freq: ov.querySelector("#rxF1").value, duration: ov.querySelector("#rxDur1").value }] });
      renderRx(); ov.remove(); showToast("Prescription created","success");
    };
  }});
}
function PATIENT_OPTS() {
  const names = ["Abel Mekonnen","Hana Wolde","Dawit Kebede","Selam Tadesse","Biruk Ayele","Ruth Gebre","Tewodros Haile","Mahlet Shiferaw","Yohannes Mamo","Kidist Assefa"];
  return names.map(n => `<option value="${n}">`).join("");
}
function viewRx(id) {
  const r = RX.find(x => x.id === id);
  openModal({
    title: "Prescription " + r.id,
    body: `<div class="detail-list"><div class="detail-item"><span class="k">Patient</span><span class="v">${esc(r.patient)}</span></div>
      <div class="detail-item"><span class="k">Doctor</span><span class="v">${esc(r.doctor)}</span></div>
      <div class="detail-item"><span class="k">Date</span><span class="v">${formatDate(r.date)}</span></div>
      <div class="detail-item"><span class="k">Status</span><span class="v">${esc(r.status)}</span></div></div>
      <h3 class="mt-4 mb-2" style="font-size:15px">Medications</h3>
      <table class="data-table"><thead><tr><th>Drug</th><th>Dosage</th><th>Frequency</th><th>Duration</th></tr></thead><tbody>
      ${r.drugs.map(d => `<tr><td>${esc(d.name)}</td><td>${esc(d.dose)}</td><td>${esc(d.freq)}</td><td>${esc(d.duration)}</td></tr>`).join("")}</tbody></table>`,
    size: "lg"
  });
}
function printRx(id) {
  const r = RX.find(x => x.id === id);
  const w = window.open("", "_blank");
  w.document.write(`<html><head><title>Prescription ${r.id}</title><style>body{font-family:monospace;padding:40px}.h{text-align:center;border-bottom:2px solid #000;padding-bottom:10px;margin-bottom:20px}</style></head><body>
    <div class="h"><h2>Wolaita Sodo University Hospital</h2><p>MedIQ Pro Prescription</p></div>
    <p><strong>Patient:</strong> ${r.patient} &nbsp; <strong>Date:</strong> ${formatDate(r.date)}</p><p><strong>Doctor:</strong> ${r.doctor}</p>
    <table width="100%" border="1" cellpadding="8" style="border-collapse:collapse;margin-top:16px">
    <tr><th align="left">Medication</th><th align="left">Dosage</th><th align="left">Frequency</th><th align="left">Duration</th></tr>
    ${r.drugs.map(d => `<tr><td>${d.name}</td><td>${d.dose}</td><td>${d.freq}</td><td>${d.duration}</td></tr>`).join("")}</table>
    <p style="margin-top:24px">Signature: ______________________</p></body></html>`);
  w.document.close(); w.print();
}
""",
}

# =====================================================================
# DOCTOR — appointments
# =====================================================================
B["doctor"]["appointments.html"] = {
"title": "Appointments",
"body": """
<div class="card mb-4" id="weekStrip"><div class="flex wrap" style="gap:8px" id="weekDays"></div></div>
<div class="card" style="padding:0">
  <div class="table-toolbar"><h3 style="font-size:16px">Upcoming Appointments</h3>
    <button class="btn btn-primary" id="btnBook">%s Book Appointment</button></div>
  <div class="table-wrap">
    <table class="data-table" id="apptTable">
      <thead><tr><th class="sortable">Time</th><th class="sortable">Patient</th><th class="sortable">Type</th><th class="sortable">Department</th><th class="sortable">Status</th><th class="sortable">No-show Risk</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="apptBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("plus"), pagination("apptPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("doctor"); initLayout(); loadPageData();
});
let APPT = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.APPOINTMENTS).then(r => {
    if (!r.ok) return; APPT = r.data.items; renderAppts();
    attachDataTable(document.getElementById("apptTable"), { pagerEl: document.getElementById("apptPager"), pageSize: 8 });
  });
  document.getElementById("btnBook").addEventListener("click", bookModal);
  // week strip
  const today = new Date();
  document.getElementById("weekDays").innerHTML = Array.from({length: 7}).map((_, i) => {
    const d = new Date(today); d.setDate(today.getDate() + i);
    const sel = i === 0 ? "selected" : "";
    return `<span class="chip ${sel}" style="flex-direction:column;gap:2px;padding:8px 14px"><strong style="font-size:14px">${d.getDate()}</strong><span style="font-size:11px;opacity:.8">${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][d.getDay()]}</span></span>`;
  }).join("");
}
function renderAppts() {
  document.getElementById("apptBody").innerHTML = APPT.length ? APPT.map(a => `<tr>
    <td><span class="time-pill">${a.time}</span></td><td><strong>${esc(a.patient)}</strong></td><td>${esc(a.type)}</td>
    <td>${esc(a.dept)}</td><td>${apptBadge(a.status)}</td>
    <td>${a.no_show >= 30 ? `<span class="badge badge-danger">High (${a.no_show}%)</span>` : a.no_show >= 15 ? `<span class="badge badge-warning">Medium (${a.no_show}%)</span>` : `<span class="badge badge-success">Low (${a.no_show}%)</span>`}</td>
    <td><div class="actions">
      <button class="btn-icon success" title="Mark attended" onclick="setStatus('${a.id}','attended')">${ICONS.check}</button>
      <button class="btn-icon warning" title="Reschedule" onclick="setStatus('${a.id}','rescheduled')">${ICONS.refresh}</button>
      <button class="btn-icon danger" title="Cancel" onclick="setStatus('${a.id}','cancelled')">${ICONS.x}</button>
    </div></td></tr>`).join("") : emptyRow(7);
}
function apptBadge(s) {
  const m = { confirmed:["success","Confirmed"], "checked-in":["info","Checked in"], completed:["neutral","Completed"], cancelled:["danger","Cancelled"], attended:["success","Attended"], rescheduled:["warning","Rescheduled"] };
  const b = m[s] || ["neutral", s]; return `<span class="badge badge-${b[0]}">${b[1]}</span>`;
}
function setStatus(id, s) {
  const a = APPT.find(x => x.id === id);
  a.status = s === "rescheduled" ? "rescheduled" : s;
  showToast("Appointment " + (s === "rescheduled" ? "rescheduled" : s), "success");
  renderAppts();
}
function bookModal() {
  openModal({
    title: "Book Appointment",
    body: `<div class="form-group"><label>Patient</label><input class="form-control" id="bkPat" list="rxPats2" placeholder="Search…"><datalist id="rxPats2">${["Abel Mekonnen","Hana Wolde","Dawit Kebede","Selam Tadesse","Biruk Ayele","Ruth Gebre","Tewodros Haile","Mahlet Shiferaw","Yohannes Mamo","Kidist Assefa"].map(n=>`<option value="${n}">`).join("")}</datalist></div>
      <div class="form-row"><div class="form-group"><label>Date</label><input class="form-control" type="date" id="bkDate" value="${todayStr()}"></div>
      <div class="form-group"><label>Time</label><input class="form-control" type="time" id="bkTime" value="09:00"></div></div>
      <div class="form-row"><div class="form-group"><label>Type</label><select class="form-control" id="bkType"><option>Consultation</option><option>Follow-up</option><option>New patient</option></select></div>
      <div class="form-group"><label>Department</label><select class="form-control" id="bkDept"><option>Internal Medicine</option><option>Pediatrics</option><option>Cardiology</option><option>Maternity</option><option>Orthopedics</option></select></div></div>
      <div class="form-group"><label>Notes</label><textarea class="form-control" rows="2" id="bkNotes"></textarea></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveBk">Book</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveBk").onclick = () => {
      const pat = ov.querySelector("#bkPat").value.trim();
      if (!pat) { showToast("Patient is required","error"); return; }
      const noShow = Math.round(5 + Math.random() * 30);
      APPT.unshift({ id: uid("A"), patient: pat, doctor: getUserName(), dept: ov.querySelector("#bkDept").value,
        date: ov.querySelector("#bkDate").value, time: ov.querySelector("#bkTime").value,
        type: ov.querySelector("#bkType").value, status: "confirmed", no_show: noShow });
      renderAppts(); ov.remove(); showToast("Appointment booked (no-show risk " + noShow + "%)","success");
    };
  }});
}
""",
}

# =====================================================================
# NURSE — dashboard
# =====================================================================
B["nurse"]["dashboard.html"] = {
"title": "Nurse Dashboard",
"body": """
<div class="stat-grid">
  {s1}{s2}{s3}{s4}
</div>
<div class="panel-grid">
  <div>{p_vitals}{p_meds}</div>
  <div>{p_alerts}{p_quick}</div>
</div>
""".format(
    s1=stat_card("users", "18", "Assigned Patients", "+2 today", "up"),
    s2=stat_card("thermometer", "5", "Vitals Due", "next 2 hrs", "up", "color-warning"),
    s3=stat_card("pill", "9", "Medications Due", "1 missed", "down", "color-danger"),
    s4=stat_card("alert", "2", "Critical Alerts", "1 high priority", "down", "color-danger"),
    p_vitals=panel("Vitals Due",
        '<div id="nurseVitalsList"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="vitals.html">Record Vitals</a>'),
    p_meds=panel("Medication Queue",
        '<div class="table-wrap" style="max-height:300px;overflow-y:auto"><table class="data-table"><thead><tr><th>Patient</th><th>Drug</th><th>Due</th><th>Status</th></tr></thead><tbody id="nurseMedsBody"></tbody></table></div>',
        actions='<a class="btn btn-secondary btn-sm" href="medications.html">All Meds</a>'),
    p_alerts=panel("Patient Alerts",
        '<div id="nurseAlerts"></div>',
        sub='<div class="sub">Flagged by vitals AI (Module 4)</div>'),
    p_quick=panel("Quick Actions",
        '<div class="quick-actions" style="grid-template-columns:1fr;margin:0">'
        '<a class="quick-action" href="vitals.html"><div class="qa-icon" style="background:#EFF6FF;color:#1A56DB">' + icon("thermometer") + '</div><div><div class="qa-title">Record Vitals</div><div class="qa-sub">With AI alert check</div></div></a>'
        '<a class="quick-action" href="medications.html"><div class="qa-icon" style="background:#ECFDF5;color:#065F46">' + icon("pill") + '</div><div><div class="qa-title">Medication Admin</div><div class="qa-sub">Mark doses given</div></div></a>'
        '<a class="quick-action" href="care-plans.html"><div class="qa-icon" style="background:#FFFBEB;color:#D97706">' + icon("clipboard") + '</div><div><div class="qa-title">Care Plans</div><div class="qa-sub">Review patient plans</div></div></a>'
        '</div>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("nurse"); initLayout(); loadPageData();
});
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.MEDICATIONS).then(r => {
    if (!r.ok) return;
    const due = r.data.items.filter(m => m.status === "pending");
    document.getElementById("nurseMedsBody").innerHTML = due.length ? due.map(m => `<tr>
      <td><strong>${esc(m.patient)}</strong></td><td>${esc(m.drug)}<div class="text-sm text-gray" style="color:#6B7280">${esc(m.dose)}</div></td>
      <td><span class="time-pill">${m.due}</span></td><td>${badge("Pending","warning")}</td></tr>`).join("") : emptyRow(4);
  });
  apiFetch(CONFIG.ENDPOINTS.CARE_PLANS).then(r => {
    if (!r.ok) return;
    document.getElementById("nurseVitalsList").innerHTML = r.data.items.slice(0, 4).map(c => `
      <div class="feed-item"><div class="feed-icon" style="background:#F0F9FF;color:#0369A1">${ICONS.clipboard}</div>
      <div class="feed-text"><strong>${esc(c.patient)}</strong> · ${esc(c.plan)}<div class="feed-time">Updated ${formatDate(c.updated)}</div></div>
      <span class="badge badge-${c.status === "completed" ? "success" : "warning"}">${esc(c.status)}</span></div>`).join("");
  });
  const alerts = [
    { patient: "Selam Tadesse", msg: "BP 158/98 — above target", sev: "critical" },
    { patient: "Biruk Ayele", msg: "SpO2 89% on room air", sev: "critical" },
    { patient: "Dawit Kebede", msg: "Missed morning inhaler", sev: "warning" }
  ];
  document.getElementById("nurseAlerts").innerHTML = alerts.map(a => `
    <div class="feed-item"><div class="feed-icon" style="background:${a.sev==="critical"?"#FEF2F2":"#FFFBEB"};color:${a.sev==="critical"?"#DC2626":"#D97706"}">${ICONS.alert}</div>
    <div class="feed-text"><strong>${esc(a.patient)}</strong><div>${esc(a.msg)}</div></div>
    <span class="badge badge-${a.sev}">${a.sev}</span></div>`).join("");
}
""",
}

# =====================================================================
# NURSE — vitals (AI module 4)
# =====================================================================
B["nurse"]["vitals.html"] = {
"title": "Patient Vitals",
"body": """
<div class="panel-grid cols-2">
  <section class="card">
    <h3 class="mb-3">Record Vitals</h3>
    <div class="form-group"><label>Patient</label>
      <select class="form-control" id="vtPatient"><option value="">— Select patient —</option></select></div>
    <div class="form-row-3">
      <div class="form-group"><label>Heart Rate (bpm)</label><input class="form-control" type="number" id="vtHr" value="90"></div>
      <div class="form-group"><label>BP Systolic</label><input class="form-control" type="number" id="vtSys" value="150"></div>
      <div class="form-group"><label>BP Diastolic</label><input class="form-control" type="number" id="vtDia" value="94"></div>
      <div class="form-group"><label>Temperature (°C)</label><input class="form-control" type="number" step="0.1" id="vtTemp" value="37.0"></div>
      <div class="form-group"><label>SpO2 (%%)</label><input class="form-control" type="number" id="vtSpo2" value="95"></div>
      <div class="form-group"><label>Resp. Rate (/min)</label><input class="form-control" type="number" id="vtRr" value="19"></div>
    </div>
    <button class="btn btn-primary btn-block" id="btnCheckVitals">%s Check Alerts (AI)</button>
    <button class="btn btn-secondary btn-block mt-3" id="btnSaveVitals">%s Save Vitals</button>
  </section>
  <div>
    <div id="vitalsResult"></div>
    <section class="card mt-4">
      <h3 class="mb-3">Vitals History — 24h (Heart Rate)</h3>
      <div class="chart-box" id="vitalsChart"></div>
      <div class="chart-legend">
        <span class="lg-item"><span class="lg-swatch" style="background:#1A56DB"></span> Heart rate (bpm)</span>
        <span class="lg-item"><span class="lg-swatch" style="background:#DC2626"></span> Critical</span>
        <span class="lg-item"><span class="lg-swatch" style="background:#D97706"></span> Warning</span>
      </div>
    </section>
  </div>
</div>
""" % (icon("zap"), icon("check")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("nurse"); initLayout(); loadPageData();
});
const HISTORY = [
  { t: "06:00", hr: 88, sys: 148, dia: 92, temp: 36.8, spo2: 96, rr: 18 },
  { t: "08:00", hr: 92, sys: 152, dia: 94, temp: 36.9, spo2: 95, rr: 19 },
  { t: "10:00", hr: 90, sys: 145, dia: 90, temp: 36.7, spo2: 96, rr: 18 },
  { t: "12:00", hr: 95, sys: 158, dia: 98, temp: 37.0, spo2: 94, rr: 20 },
  { t: "14:00", hr: 91, sys: 150, dia: 93, temp: 36.9, spo2: 95, rr: 18 },
  { t: "16:00", hr: 89, sys: 146, dia: 91, temp: 36.8, spo2: 96, rr: 18 },
  { t: "18:00", hr: 93, sys: 154, dia: 95, temp: 37.0, spo2: 95, rr: 19 },
  { t: "20:00", hr: 90, sys: 149, dia: 92, temp: 36.9, spo2: 96, rr: 18 }
];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.PATIENTS).then(r => {
    if (!r.ok) return;
    document.getElementById("vtPatient").innerHTML = '<option value="">— Select patient —</option>' +
      r.data.items.map(p => `<option value="${p.id}">${esc(p.id)} — ${esc(p.first_name + " " + p.last_name)}</option>`).join("");
  });
  document.getElementById("btnCheckVitals").addEventListener("click", runVitalsCheck);
  document.getElementById("btnSaveVitals").addEventListener("click", () => {
    if (!document.getElementById("vtPatient").value) { showToast("Select a patient first","error"); return; }
    showToast("Vitals saved to patient record","success");
  });
  renderHistory();
}
function runVitalsCheck() {
  if (!document.getElementById("vtPatient").value) { showToast("Select a patient first","error"); return; }
  document.getElementById("vitalsResult").innerHTML = `<section class="card"><div class="loading-area"><div class="spinner"></div><div>Running vitals AI alert check…</div></div></section>`;
  checkVitalsAI({
    hr: document.getElementById("vtHr").value, sys: document.getElementById("vtSys").value,
    dia: document.getElementById("vtDia").value, temp: document.getElementById("vtTemp").value,
    spo2: document.getElementById("vtSpo2").value, rr: document.getElementById("vtRr").value
  });
}
function checkVitalsAI(payload) {
  apiFetch(CONFIG.ENDPOINTS.CHECK_VITALS, "POST", payload).then(r => {
    if (!r.ok) { document.getElementById("vitalsResult").innerHTML = `<div class="alert alert-danger">${ICONS.alert} <div class="alert-body">AI service unavailable.</div></div>`; return; }
    renderVitalsResult(r.data);
  });
}
function renderVitalsResult(res) {
  const cfg = { normal: ["severity-safe","success","Normal","All vitals within normal ranges."], warning: ["severity-moderate","warning","Warning","Some vitals are out of range — monitor closely."], critical: ["severity-severe","danger","Critical","Immediate medical attention required!"] };
  const c = cfg[res.level];
  let rows = res.flags.length ? res.flags.map(f => `<tr><td>${esc(f.vital)}</td><td><strong>${esc(f.value)}</strong></td><td>${esc(f.range)}</td><td><span class="badge badge-${f.severity}">${f.severity}</span></td><td>${esc(f.by)}</td></tr>`).join("") : `<tr><td colspan="5" style="text-align:center;color:#6B7280;padding:16px">All vitals within range</td></tr>`;
  document.getElementById("vitalsResult").innerHTML = `<section class="card">
    <div class="severity-card ${c[0]}"><div class="flex" style="gap:10px;align-items:flex-start"><span>${ICONS[c[1]]}</span>
      <div><strong style="font-size:16px">${c[2]} Alert</strong><div style="font-size:13px;margin-top:2px">${c[3]}</div></div></div></div>
    ${res.flags.length ? `<table class="data-table mt-4"><thead><tr><th>Vital</th><th>Value</th><th>Normal Range</th><th>Severity</th><th>Deviation</th></tr></thead><tbody>${rows}</tbody></table>` : ""}
    <h3 class="mt-4 mb-2" style="font-size:15px">Recommended Actions</h3>
    <ul style="list-style:disc;padding-left:20px;color:#374151">${res.actions.map(a => `<li style="margin-bottom:6px">${esc(a)}</li>`).join("")}</ul>
    <div class="disclaimer"><span>${ICONS.info}</span><div>AI suggestions only. Clinical decisions are made by the responsible nurse or doctor.</div></div>
  </section>`;
}
function renderHistory() {
  document.getElementById("vitalsChart").innerHTML = lineChart(HISTORY.map(h => ({ label: h.t, value: h.hr })), { height: 220 });
}
""",
}

# =====================================================================
# NURSE — medications
# =====================================================================
B["nurse"]["medications.html"] = {
"title": "Medication Administration",
"body": """
<div class="card mb-4" style="padding:0">
  <div class="table-toolbar"><h3 style="font-size:16px">Administration Queue</h3>
    <span class="badge badge-warning" id="medCount">0 pending</span></div>
  <div class="table-wrap">
    <table class="data-table" id="medTable">
      <thead><tr><th class="sortable">Patient</th><th class="sortable">Drug</th><th>Dose</th><th class="sortable">Due</th><th class="sortable">Status</th><th>Administered</th><th style="text-align:right">Action</th></tr></thead>
      <tbody id="medBody"></tbody>
    </table>
  </div>
</div>
<div class="card">
  <h3 class="mb-3">Shift Handover Notes</h3>
  <textarea class="form-control" id="handover" rows="4" placeholder="Summarize the shift: critical patients, pending tasks, incidents…">Ward 3: Selam T. BP still elevated — cardiology notified. Biruk A. improving on antibiotics. Please re-check Yohannes M. glucose at 12:00.</textarea>
  <div class="form-actions"><button class="btn btn-primary" onclick="saveHandover()">%s Save Handover</button></div>
</div>
""" % icon("check"),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("nurse"); initLayout(); loadPageData();
});
let MEDS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.MEDICATIONS).then(r => {
    if (!r.ok) return; MEDS = r.data.items; renderMeds();
  });
}
function renderMeds() {
  const body = document.getElementById("medBody");
  const pend = MEDS.filter(m => m.status === "pending").length;
  document.getElementById("medCount").textContent = pend + " pending";
  body.innerHTML = MEDS.map(m => {
    const missed = m.status === "missed";
    return `<tr class="${missed ? "row-danger" : ""}">
      <td><strong>${esc(m.patient)}</strong></td><td>${esc(m.drug)}</td><td>${esc(m.dose)}</td>
      <td><span class="time-pill">${m.due}</span></td>
      <td>${m.status === "administered" ? badge("Administered","success") : m.status === "missed" ? badge("Missed","danger") : badge("Pending","warning")}</td>
      <td class="text-sm text-gray" style="color:#6B7280">${m.time || "—"}</td>
      <td style="text-align:right">${m.status !== "administered" ? `<button class="btn btn-success btn-sm" onclick="administer('${m.id}')">${ICONS.check} ${m.status === "missed" ? "Record" : "Mark Administered"}</button>` : '<span class="text-success text-sm" style="font-weight:600">✓ Done</span>'}</td></tr>`;
  }).join("") || emptyRow(7);
}
function administer(id) {
  const m = MEDS.find(x => x.id === id);
  m.status = "administered";
  m.time = new Date().toTimeString().slice(0, 5);
  renderMeds();
  showToast(m.drug + " administered to " + m.patient + " at " + m.time, "success");
}
function saveHandover() {
  const t = document.getElementById("handover").value.trim();
  if (!t) { showToast("Notes are empty","warning"); return; }
  showToast("Shift handover notes saved","success");
}
""",
}

# =====================================================================
# NURSE — care plans
# =====================================================================
B["nurse"]["care-plans.html"] = {
"title": "Care Plans",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar"><div class="search-box">%s<input class="form-control" id="cpSearch" placeholder="Search patient…"></div>
    <button class="btn btn-primary" id="btnNewCp">%s New Care Plan</button></div>
  <div class="table-wrap">
    <table class="data-table" id="cpTable">
      <thead><tr><th class="sortable">Patient</th><th class="sortable">Plan</th><th class="sortable">Created</th><th class="sortable">Updated</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="cpBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("search"), icon("plus"), pagination("cpPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("nurse"); initLayout(); loadPageData();
});
let PLANS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.CARE_PLANS).then(r => {
    if (!r.ok) return; PLANS = r.data.items; renderPlans();
    attachDataTable(document.getElementById("cpTable"), { searchInput: document.getElementById("cpSearch"), pagerEl: document.getElementById("cpPager"), pageSize: 8 });
  });
  document.getElementById("btnNewCp").addEventListener("click", newPlan);
}
function renderPlans() {
  document.getElementById("cpBody").innerHTML = PLANS.length ? PLANS.map(p => `<tr>
    <td><strong>${esc(p.patient)}</strong></td><td>${esc(p.plan)}</td><td>${formatDate(p.created)}</td><td>${formatDate(p.updated)}</td>
    <td>${p.status === "completed" ? badge("Completed","success") : badge("In progress","warning")}</td>
    <td><div class="actions"><button class="btn-icon primary" title="View" onclick="viewPlan('${p.id}')">${ICONS.eye}</button>
    <button class="btn-icon" title="Update" onclick="updatePlan('${p.id}')">${ICONS.edit}</button></div></td></tr>`).join("") : emptyRow(6);
}
function viewPlan(id) {
  const p = PLANS.find(x => x.id === id);
  openModal({
    title: "Care Plan — " + p.patient,
    body: `<div class="detail-list">
      <div class="detail-item"><span class="k">Patient</span><span class="v">${esc(p.patient)}</span></div>
      <div class="detail-item"><span class="k">Plan</span><span class="v">${esc(p.plan)}</span></div>
      <div class="detail-item"><span class="k">Status</span><span class="v">${esc(p.status)}</span></div></div>
      <h3 class="mt-4 mb-2" style="font-size:15px">Care Steps</h3>
      ${p.steps.map((s, i) => `<div class="flex-between" style="padding:9px 0;border-bottom:1px dashed #E5E7EB">
        <span>${i+1}. ${esc(s)}</span><span class="badge badge-${i < 3 ? "success" : "neutral"}">${i < 3 ? "Done" : "Pending"}</span></div>`).join("")}`,
    size: "lg"
  });
}
function updatePlan(id) {
  const p = PLANS.find(x => x.id === id);
  openModal({
    title: "Update Care Plan",
    body: `<div class="form-group"><label>Status</label><select class="form-control" id="cpStatus"><option ${p.status==="in-progress"?"selected":""}>in-progress</option><option ${p.status==="completed"?"selected":""}>completed</option></select></div>
      <div class="form-group"><label>Notes</label><textarea class="form-control" rows="3" placeholder="Progress notes…"></textarea></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveCp">Save Update</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveCp").onclick = () => {
      p.status = ov.querySelector("#cpStatus").value; p.updated = todayStr();
      renderPlans(); ov.remove(); showToast("Care plan updated","success");
    };
  }});
}
function newPlan() {
  openModal({
    title: "New Care Plan",
    body: `<div class="form-group"><label>Patient</label><input class="form-control" list="cpPats" placeholder="Search…"><datalist id="cpPats">${["Selam Tadesse","Yohannes Mamo","Ruth Gebre","Biruk Ayele"].map(n=>`<option value="${n}">`).join("")}</datalist></div>
      <div class="form-group"><label>Plan Title</label><input class="form-control" placeholder="e.g. Post-op recovery"></div>
      <div class="form-group"><label>Steps (one per line)</label><textarea class="form-control" rows="4" placeholder="Daily wound care&#10;Physiotherapy 20 min&#10;Pain assessment q4h"></textarea></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveNew">Create Plan</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveNew").onclick = () => {
      PLANS.unshift({ id: uid("CP"), patient: "New Patient", plan: "New care plan", created: todayStr(), updated: todayStr(), status: "in-progress", steps: ["Step 1"] });
      renderPlans(); ov.remove(); showToast("Care plan created","success");
    };
  }});
}
""",
}
