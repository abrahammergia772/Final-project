# -*- coding: utf-8 -*-
"""MedIQ Pro page bodies — Part D: reception + patient."""
from frontend_lib import icon, stat_card, panel, badge, pagination, empty_row

D = {"reception": {}, "patient": {}}

# =====================================================================
# RECEPTION — dashboard
# =====================================================================
D["reception"]["dashboard.html"] = {
"title": "Front Desk Dashboard",
"body": """
<div class="panel-grid">
  <div>
    {p_appts}
  </div>
  <div>{p_queue}{p_docs}</div>
</div>
""" .format(
    p_appts=panel("Today's Appointments",
        '<div class="table-wrap" style="max-height:460px;overflow-y:auto"><table class="data-table"><thead><tr><th>Time</th><th>Patient</th><th>Doctor</th><th>Status</th></tr></thead><tbody id="recApptsBody"></tbody></table></div>',
        actions='<a class="btn btn-secondary btn-sm" href="appointments.html">Manage</a>'),
    p_queue=panel("Walk-in Queue",
        '<div id="recQueueList"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="queue.html">Queue Board</a>'),
    p_docs=panel("Doctor Availability",
        '<div id="docAvail"></div>',
        sub='<div class="sub">Real-time status</div>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("reception"); initLayout(); loadPageData();
});
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.APPOINTMENTS).then(r => {
    if (!r.ok) return;
    document.getElementById("recApptsBody").innerHTML = r.data.items.filter(a => a.status !== "cancelled").map(a => `<tr>
      <td><span class="time-pill">${a.time}</span></td><td><strong>${esc(a.patient)}</strong></td><td>${esc(a.doctor)}</td>
      <td>${a.status === "checked-in" ? badge("Checked in","info") : badge(a.status,"success")}</td></tr>`).join("") || emptyRow(4);
  });
  apiFetch(CONFIG.ENDPOINTS.QUEUE).then(r => {
    if (!r.ok) return;
    const q = r.data.items;
    document.getElementById("recQueueList").innerHTML = q.slice(0, 5).map(x => `
      <div class="feed-item"><div class="feed-icon" style="background:${x.status === "in-service" ? "#ECFDF5" : "#EFF6FF"};color:${x.status === "in-service" ? "#065F46" : "#1A56DB"}">${ICONS.users}</div>
      <div class="feed-text"><strong>${esc(x.name)}</strong> · ${esc(x.dept)}<div class="feed-time">Arrived ${x.arrived} · ${x.status}</div></div>
      <span class="badge badge-${x.status === "in-service" ? "success" : "neutral"}">${x.status === "in-service" ? "Now" : "Wait"}</span></div>`).join("");
  });
  const docs = [["Dr. Daniel Alemu","Internal Medicine","available"],["Dr. Fikru Debebe","Pediatrics","busy"],["Dr. Meron Assefa","Cardiology","busy"],["Dr. Tsehay Mengistu","Maternity","off"],["Dr. Natnael Fekadu","Emergency","available"]];
  document.getElementById("docAvail").innerHTML = docs.map(d => `
    <div class="avail-item"><span class="health-dot ${d[2] === "available" ? "ok" : d[2] === "busy" ? "warn" : "bad"}"></span>
    <div style="flex:1"><strong>${d[0]}</strong><div class="text-sm text-gray" style="color:#6B7280">${d[1]}</div></div>
    <span class="badge badge-${d[2] === "available" ? "success" : d[2] === "busy" ? "warning" : "neutral"}">${d[2]}</span></div>`).join("");
}
""",
}

# =====================================================================
# RECEPTION — registration
# =====================================================================
D["reception"]["registration.html"] = {
"title": "Patient Registration",
"body": """
<section class="card mb-4">
  <div class="flex-between wrap" style="gap:12px"><div><h3 style="font-size:16px">Returning Patient?</h3>
    <p class="text-sm text-gray" style="color:#6B7280">Search by name or ID to pull up an existing record.</p></div>
    <div class="search-box"><span>%s</span><input class="form-control" id="retSearch" placeholder="Search…"></div></div>
  <div id="retResult" class="mt-3"></div>
</section>
<section class="card">
  <div class="flex-between wrap" style="gap:10px"><h3 style="font-size:16px">New Patient Registration</h3><span class="badge badge-info">Auto ID on submit</span></div>
  <div class="form-row mt-4">
    <div class="form-group"><label>First Name <span class="req">*</span></label><input class="form-control" id="rF"></div>
    <div class="form-group"><label>Last Name <span class="req">*</span></label><input class="form-control" id="rL"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>Date of Birth <span class="req">*</span></label><input class="form-control" type="date" id="rDob"></div>
    <div class="form-group"><label>Gender</label><select class="form-control" id="rG"><option>Male</option><option>Female</option></select></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>Phone <span class="req">*</span></label><input class="form-control" id="rP" placeholder="+251 9xx xxx xxx"></div>
    <div class="form-group"><label>Email</label><input class="form-control" type="email" id="rE" placeholder="name@mail.com"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>Address</label><input class="form-control" id="rA" placeholder="City, Sub-city"></div>
    <div class="form-group"><label>Blood Type</label><select class="form-control" id="rB"><option>O+</option><option>O−</option><option>A+</option><option>A−</option><option>B+</option><option>B−</option><option>AB+</option><option>AB−</option><option>Unknown</option></select></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>Emergency Contact <span class="req">*</span></label><input class="form-control" id="rEc" placeholder="Name & phone"></div>
    <div class="form-group"><label>Photo</label><input class="form-control" type="file" accept="image/*"></div>
  </div>
  <div class="divider"></div>
  <h3 style="font-size:15px" class="mb-3">Insurance Information</h3>
  <div class="form-row">
    <div class="form-group"><label>Insurance Provider</label><input class="form-control" id="rIns" placeholder="e.g. EHBPA, Nyala Insurance…"></div>
    <div class="form-group"><label>Policy / Member No.</label><input class="form-control" id="rPol"></div>
  </div>
  <div class="form-actions">
    <button class="btn btn-secondary" onclick="resetForm()">Clear</button>
    <button class="btn btn-primary btn-lg" id="btnReg">%s Register Patient</button>
  </div>
</section>
<div id="regResult"></div>
""" % (icon("search"), icon("check")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("reception"); initLayout(); loadPageData();
});
const EXISTING = ["Abel Mekonnen (P-1001)","Hana Wolde (P-1002)","Dawit Kebede (P-1003)","Selam Tadesse (P-1004)","Biruk Ayele (P-1005)","Ruth Gebre (P-1006)","Tewodros Haile (P-1007)","Mahlet Shiferaw (P-1008)","Yohannes Mamo (P-1009)","Kidist Assefa (P-1010)"];
function loadPageData() {
  document.getElementById("retSearch").addEventListener("input", debounce(e => {
    const q = e.target.value.trim().toLowerCase();
    const box = document.getElementById("retResult");
    if (!q) { box.innerHTML = ""; return; }
    const hits = EXISTING.filter(n => n.toLowerCase().includes(q));
    box.innerHTML = hits.length ? `<div class="feed">${hits.map(h => `<div class="feed-item"><div class="feed-icon" style="background:#EFF6FF;color:#1A56DB">${ICONS.users}</div>
      <div class="feed-text"><strong>${esc(h)}</strong> — returning patient record found<div class="feed-time"><a href="#" onclick="event.preventDefault();showToast('Opened existing record','info')">View record</a></div></div></div>`).join("")}</div>`
      : '<div class="alert alert-warning mb-0">No existing record — complete the form to register a new patient.</div>';
  }, 250));
  document.getElementById("btnReg").addEventListener("click", register);
}
function register() {
  const f = document.getElementById("rF").value.trim(), l = document.getElementById("rL").value.trim();
  const dob = document.getElementById("rDob").value, ph = document.getElementById("rP").value.trim();
  if (!f || !l) { showToast("First and last name are required","error"); return; }
  if (!dob) { showToast("Date of birth is required","error"); return; }
  if (!ph) { showToast("Phone number is required","error"); return; }
  const id = "P-" + (1011 + Math.floor(Math.random() * 900));
  document.getElementById("regResult").innerHTML = `<section class="card mt-4">
    <div class="severity-card severity-safe"><div class="flex" style="gap:10px"><span>${ICONS.check}</span>
      <div><strong style="font-size:16px">Patient registered successfully!</strong></div></div></div>
    <div class="receipt mt-4">
      <div class="r-row"><span>Patient ID</span><strong>${id}</strong></div>
      <div class="r-row"><span>Name</span><strong>${esc(f + " " + l)}</strong></div>
      <div class="r-row"><span>Date of Birth</span><span>${formatDate(dob)}</span></div>
      <div class="r-row"><span>Gender</span><span>${document.getElementById("rG").value}</span></div>
      <div class="r-row"><span>Phone</span><span>${esc(ph)}</span></div>
      <div class="r-row"><span>Blood Type</span><span>${document.getElementById("rB").value}</span></div>
      <div class="r-row"><span>Insurance</span><span>${esc(document.getElementById("rIns").value || "None")}</span></div>
    </div>
    <div class="form-actions"><button class="btn btn-secondary" onclick="document.getElementById('regResult').innerHTML=''">Dismiss</button>
    <button class="btn btn-primary" onclick="window.print()">${ICONS.printer} Print ID Card</button></div>
  </section>`;
  showToast("Patient registered — ID " + id, "success");
  resetForm();
}
function resetForm() {
  ["rF","rL","rP","rE","rA","rEc","rIns","rPol"].forEach(i => document.getElementById(i).value = "");
  document.getElementById("rDob").value = "";
}
""",
}

# =====================================================================
# RECEPTION — appointments (with AI no-show, Module 6)
# =====================================================================
D["reception"]["appointments.html"] = {
"title": "Appointments",
"body": """
<div class="flex-between mb-4"><div class="chip-group" id="viewToggle">
    <span class="chip selected" data-view="list">%s List View</span>
    <span class="chip" data-view="cal">%s Calendar View</span>
  </div>
  <button class="btn btn-primary" id="btnBook">%s Book Appointment</button></div>
<div id="calView" class="card mb-4 hidden"><div id="calGrid"></div></div>
<div class="card" style="padding:0" id="listView">
  <div class="table-toolbar"><div class="search-box">%s<input class="form-control" id="apptSearch" placeholder="Search patient…"></div>
    <span class="badge badge-info" id="apptCount">0 appointments</span></div>
  <div class="table-wrap">
    <table class="data-table" id="apptTable">
      <thead><tr><th class="sortable">Time</th><th class="sortable">Patient</th><th class="sortable">Doctor</th><th class="sortable">Department</th><th class="sortable">Type</th><th class="sortable">No-show Risk</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="apptBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % (icon("list"), icon("calendar"), icon("plus"), icon("search"), pagination("apptPager")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("reception"); initLayout(); loadPageData();
});
let APPT = [];
const PATIENTS = ["Abel Mekonnen","Hana Wolde","Dawit Kebede","Selam Tadesse","Biruk Ayele","Ruth Gebre","Tewodros Haile","Mahlet Shiferaw","Yohannes Mamo","Kidist Assefa"];
const DOCTORS = ["Dr. Daniel Alemu","Dr. Fikru Debebe","Dr. Meron Assefa","Dr. Tsehay Mengistu","Dr. Natnael Fekadu"];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.APPOINTMENTS).then(r => {
    if (!r.ok) return; APPT = r.data.items; renderAppts();
    attachDataTable(document.getElementById("apptTable"), {
      searchInput: document.getElementById("apptSearch"), pagerEl: document.getElementById("apptPager"), pageSize: 8,
      onRender: n => document.getElementById("apptCount").textContent = n + " appointments"
    });
  });
  document.getElementById("btnBook").addEventListener("click", bookModal);
  document.querySelectorAll("[data-view]").forEach(c => c.addEventListener("click", () => {
    document.querySelectorAll("[data-view]").forEach(x => x.classList.remove("selected"));
    c.classList.add("selected");
    document.getElementById("calView").classList.toggle("hidden", c.dataset.view === "list");
    document.getElementById("listView").classList.toggle("hidden", c.dataset.view === "cal");
    if (c.dataset.view === "cal") renderCalendar();
  }));
}
function noShowBadge(a) {
  const p = a.no_show;
  return p >= 30 ? `<span class="badge badge-danger" title="AI predicted no-show">High · ${p}%</span>`
    : p >= 15 ? `<span class="badge badge-warning" title="AI predicted no-show">Med · ${p}%</span>`
    : `<span class="badge badge-success" title="AI predicted no-show">Low · ${p}%</span>`;
}
function renderAppts() {
  document.getElementById("apptBody").innerHTML = APPT.length ? APPT.map(a => `<tr>
    <td><span class="time-pill">${a.time}</span></td><td><strong>${esc(a.patient)}</strong></td><td>${esc(a.doctor)}</td>
    <td>${esc(a.dept)}</td><td>${esc(a.type)}</td><td>${noShowBadge(a)}</td>
    <td>${apptBadge(a.status)}</td>
    <td><div class="actions">
      <button class="btn-icon success" title="Mark attended" onclick="setA('${a.id}','attended')">${ICONS.check}</button>
      <button class="btn-icon warning" title="Reschedule" onclick="setA('${a.id}','rescheduled')">${ICONS.refresh}</button>
      <button class="btn-icon danger" title="Cancel" onclick="setA('${a.id}','cancelled')">${ICONS.x}</button>
    </div></td></tr>`).join("") : emptyRow(8);
}
function apptBadge(s) {
  const m = { confirmed:["success","Confirmed"], "checked-in":["info","Checked in"], completed:["neutral","Completed"], cancelled:["danger","Cancelled"], attended:["success","Attended"], rescheduled:["warning","Rescheduled"] };
  const b = m[s] || ["neutral", s]; return `<span class="badge badge-${b[0]}">${b[1]}</span>`;
}
function setA(id, s) { const a = APPT.find(x => x.id === id); a.status = s; renderAppts(); showToast("Appointment " + s,"success"); }
function bookModal() {
  openModal({
    title: "Book Appointment",
    body: `<div class="form-group"><label>Patient <span class="req">*</span></label><input class="form-control" id="bPat" list="bPats"><datalist id="bPats">${PATIENTS.map(n=>`<option value="${n}">`).join("")}</datalist></div>
      <div class="form-group"><label>Doctor</label><select class="form-control" id="bDoc">${DOCTORS.map(d=>`<option>${d}</option>`).join("")}</select></div>
      <div class="form-row">
        <div class="form-group"><label>Date</label><input class="form-control" type="date" id="bDate" value="${todayStr()}"></div>
        <div class="form-group"><label>Time</label><input class="form-control" type="time" id="bTime" value="09:00"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Type</label><select class="form-control" id="bType"><option>Consultation</option><option>Follow-up</option><option>New patient</option></select></div>
        <div class="form-group"><label>Department</label><select class="form-control" id="bDept"><option>Internal Medicine</option><option>Pediatrics</option><option>Cardiology</option><option>Maternity</option><option>Orthopedics</option></select></div>
      </div>
      <div class="form-group"><label>Notes</label><textarea class="form-control" rows="2" id="bNotes"></textarea></div>
      <div class="alert alert-info mb-0"><span>${ICONS.brain}</span><div class="alert-body">On booking, the AI will predict the no-show probability (Module 6).</div></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveB">Book Appointment</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveB").onclick = () => {
      const pat = ov.querySelector("#bPat").value.trim();
      if (!pat) { showToast("Patient is required","error"); return; }
      showLoading("AI predicting no-show risk…");
      predictAppointment({ patient: pat, day: "Monday", type: ov.querySelector("#bType").value, dept: ov.querySelector("#bDept").value }, res => {
        hideLoading();
        APPT.unshift({ id: uid("A"), patient: pat, doctor: ov.querySelector("#bDoc").value, dept: ov.querySelector("#bDept").value,
          date: ov.querySelector("#bDate").value, time: ov.querySelector("#bTime").value,
          type: ov.querySelector("#bType").value, status: "confirmed", no_show: res.no_show_percent });
        renderAppts(); ov.remove();
        showToast("Appointment booked — AI no-show risk " + res.no_show_percent + "%", "success");
      });
    };
  }});
}
function renderCalendar() {
  const now = new Date();
  const y = now.getFullYear(), m = now.getMonth();
  const first = new Date(y, m, 1), startDow = first.getDay();
  const daysInMonth = new Date(y, m + 1, 0).getDate();
  const today = now.getDate();
  let cells = "";
  const days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
  days.forEach(d => cells += `<div style="font-weight:700;text-align:center;color:#6B7280;font-size:12px;padding:8px">${d}</div>`);
  for (let i = 0; i < startDow; i++) cells += `<div></div>`;
  for (let d = 1; d <= daysInMonth; d++) {
    const count = APPT.filter(a => +a.date.split("-")[2] === d).length;
    const isToday = d === today;
    cells += `<div style="border:1px solid #E5E7EB;border-radius:8px;min-height:64px;padding:6px;background:${isToday ? "#EFF6FF" : "#fff"}">
      <strong style="color:${isToday ? "var(--primary)" : "#111827"}">${d}</strong>
      ${count ? `<div style="font-size:11px;color:#1A56DB;font-weight:600;margin-top:4px">${count} appt${count>1?"s":""}</div>` : ""}</div>`;
  }
  document.getElementById("calGrid").innerHTML = `<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:6px">${cells}</div>
    <p class="text-sm text-gray mt-3" style="color:#6B7280">Showing ${APPT.length} appointments for ${first.toLocaleString("en",{month:"long",year:"numeric"})}.</p>`;
}
""",
}

# =====================================================================
# RECEPTION — queue
# =====================================================================
D["reception"]["queue.html"] = {
"title": "Walk-in Queue",
"body": """
<div class="queue-board">
  <div>
    <section class="card">
      <h3 class="mb-3">Now Serving</h3>
      <div class="queue-now" id="nowServing"><div class="qn-label">Currently in service</div>
        <div class="qn-name">—</div><div class="qn-sub">No patient in service</div></div>
      <div class="flex gap-3"><button class="btn btn-primary btn-block" id="btnCallNext">%s Call Next</button>
        <button class="btn btn-secondary" id="btnPause">%s Hold</button></div>
    </section>
    <section class="card mt-4">
      <h3 class="mb-3">Add to Queue</h3>
      <div class="form-group"><input class="form-control" id="qName" placeholder="Patient name…"></div>
      <div class="form-group"><select class="form-control" id="qDept"><option>Internal Medicine</option><option>Pediatrics</option><option>Cardiology</option><option>Maternity</option><option>Orthopedics</option><option>Emergency</option></select></div>
      <button class="btn btn-success btn-block" id="btnAddQ">%s Add to Queue</button>
    </section>
  </div>
  <section class="card" style="padding:0">
    <div class="table-toolbar"><h3 style="font-size:16px">Waiting List</h3><span class="badge badge-warning" id="qCount">0 waiting</span></div>
    <div class="table-wrap">
      <table class="data-table"><thead><tr><th>#</th><th>Patient</th><th>Department</th><th>Arrived</th><th>Est. Wait</th><th style="text-align:right">Action</th></tr></thead>
      <tbody id="qBody"></tbody></table>
    </div>
  </section>
</div>
""" % (icon("chevron-right"), icon("clock"), icon("plus")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("reception"); initLayout(); loadPageData();
});
let QUEUE = [
  { id:"Q-1", name:"Mahlet Shiferaw", dept:"Internal Medicine", arrived:"08:10", status:"in-service" },
  { id:"Q-2", name:"Kidist Assefa", dept:"Cardiology", arrived:"08:15", status:"waiting" },
  { id:"Q-3", name:"Biruk Ayele", dept:"Pediatrics", arrived:"08:22", status:"waiting" },
  { id:"Q-4", name:"Tewodros Haile", dept:"Cardiology", arrived:"08:30", status:"waiting" },
  { id:"Q-5", name:"Ruth Gebre", dept:"Internal Medicine", arrived:"08:41", status:"waiting" },
  { id:"Q-6", name:"Yohannes Mamo", dept:"Internal Medicine", arrived:"08:47", status:"waiting" }
];
function loadPageData() {
  renderQueue();
  document.getElementById("btnCallNext").addEventListener("click", callNext);
  document.getElementById("btnAddQ").addEventListener("click", addToQueue);
  document.getElementById("btnPause").addEventListener("click", () => showToast("Queue paused for 10 minutes","info"));
}
function renderQueue() {
  const waiting = QUEUE.filter(q => q.status === "waiting");
  const serving = QUEUE.find(q => q.status === "in-service");
  document.getElementById("qCount").textContent = waiting.length + " waiting";
  document.getElementById("nowServing").innerHTML = serving
    ? `<div class="qn-label">Currently in service</div><div class="qn-name">${esc(serving.name)}</div><div class="qn-sub">${esc(serving.dept)} · since ${serving.arrived}</div>`
    : `<div class="qn-label">Currently in service</div><div class="qn-name">—</div><div class="qn-sub">No patient in service</div>`;
  document.getElementById("qBody").innerHTML = waiting.length ? waiting.map((q, i) => `
    <tr><td><span class="badge badge-neutral">${i + 1}</span></td><td><strong>${esc(q.name)}</strong></td>
    <td>${esc(q.dept)}</td><td><span class="time-pill">${q.arrived}</span></td>
    <td class="text-sm text-gray" style="color:#6B7280">~${10 + i * 8} min</td>
    <td style="text-align:right"><button class="btn-icon danger" title="Remove" onclick="removeQ('${q.id}')">${ICONS.trash}</button></td></tr>`).join("") : '<tr><td colspan="6" style="text-align:center;color:#6B7280;padding:32px">Queue is empty 🎉</td></tr>';
}
function callNext() {
  const next = QUEUE.find(q => q.status === "waiting");
  if (!next) { showToast("No patients waiting","info"); return; }
  QUEUE.forEach(q => { if (q.status === "in-service") q.status = "waiting"; });
  next.status = "in-service";
  renderQueue();
  showToast("Now serving: " + next.name, "success");
}
function addToQueue() {
  const name = document.getElementById("qName").value.trim();
  if (!name) { showToast("Enter a patient name","error"); return; }
  const t = new Date().toTimeString().slice(0, 5);
  QUEUE.push({ id: uid("Q"), name, dept: document.getElementById("qDept").value, arrived: t, status: "waiting" });
  document.getElementById("qName").value = "";
  renderQueue();
  showToast(name + " added to queue","success");
}
function removeQ(id) { QUEUE = QUEUE.filter(q => q.id !== id); renderQueue(); }
""",
}

# =====================================================================
# PATIENT — dashboard
# =====================================================================
D["patient"]["dashboard.html"] = {
"title": "Patient Portal",
"body": """
<div class="welcome-banner">
  <div><h2>Welcome back, <span data-user-name>Patient</span> 👋</h2>
    <p>You have <strong>1 appointment</strong> this week and <strong>3 active prescriptions</strong>.</p></div>
  <div class="wb-actions">
    <a class="btn" href="appointments.html">%s Book Appointment</a>
    <a class="btn btn-ghost" href="ai-chatbot.html">%s Chat with AI</a>
  </div>
</div>
<div class="stat-grid">
  {s1}{s2}{s3}{s4}
</div>
<div class="panel-grid">
  <div>{p_appts}</div>
  <div>{p_results}</div>
</div>
""" .format(
    icon("calendar"), icon("chat"),
    s1=stat_card("calendar", "11/08/2026<br><span style='font-size:14px'>09:00</span>", "Next Appointment", "Internal Medicine", "up"),
    s2=stat_card("file-text", "3", "Active Prescriptions", "2 renew soon", "up", "color-info"),
    s3=stat_card("flask", "5", "Lab Results", "1 abnormal", "down", "color-warning"),
    s4=stat_card("wallet", '<span id="outBill">–</span>', "Outstanding Bill", "due in 5 days", "down", "color-danger"),
    p_appts=panel("Upcoming Appointments",
        '<div id="patAppts"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="appointments.html">All</a>'),
    p_results=panel("Recent Lab Results",
        '<div id="patResults"></div>',
        actions='<a class="btn btn-secondary btn-sm" href="results.html">All</a>'),
),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("patient"); initLayout(); loadPageData();
});
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.BILLS).then(r => {
    if (!r.ok) return;
    const total = r.data.items.filter(b => b.status !== "paid").reduce((s, b) => s + b.amount, 0);
    document.getElementById("outBill").textContent = formatCurrency(total);
  });
  apiFetch(CONFIG.ENDPOINTS.APPOINTMENTS).then(r => {
    if (!r.ok) return;
    document.getElementById("patAppts").innerHTML = r.data.items.slice(0, 3).map(a => `
      <div class="feed-item"><div class="feed-icon" style="background:#EFF6FF;color:#1A56DB">${ICONS.calendar}</div>
      <div class="feed-text"><strong>${esc(a.type)}</strong> · ${esc(a.dept)}<div class="feed-time">${formatDate(a.date)} at ${a.time} · ${esc(a.doctor)}</div></div>
      <span class="badge badge-${a.status === "confirmed" ? "success" : "neutral"}">${esc(a.status)}</span></div>`).join("") || '<div class="empty-state">No upcoming appointments.</div>';
  });
  apiFetch(CONFIG.ENDPOINTS.LAB_RESULTS).then(r => {
    if (!r.ok) return;
    document.getElementById("patResults").innerHTML = r.data.items.slice(0, 3).map(res => `
      <div class="feed-item"><div class="feed-icon" style="background:${res.ai_flag === "abnormal" ? "#FEF2F2" : "#ECFDF5"};color:${res.ai_flag === "abnormal" ? "#DC2626" : "#065F46"}">${ICONS.flask}</div>
      <div class="feed-text"><strong>${esc(res.test)}</strong><div class="feed-time">${formatDate(res.date)}</div></div>
      <span class="badge badge-${res.ai_flag === "abnormal" ? "danger" : "success"}">${res.ai_flag}</span></div>`).join("");
  });
}
""",
}

# =====================================================================
# PATIENT — appointments
# =====================================================================
D["patient"]["appointments.html"] = {
"title": "My Appointments",
"body": """
<div class="flex-between mb-4"><p class="page-intro" style="margin:0">Manage your visits.</p>
  <button class="btn btn-primary" id="btnBook">%s Book Appointment</button></div>
<div class="card" style="padding:0">
  <div class="table-wrap">
    <table class="data-table">
      <thead><tr><th>Date</th><th>Time</th><th>Doctor</th><th>Department</th><th>Type</th><th>Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="pApptBody"></tbody>
    </table>
  </div>
</div>
""" % icon("plus"),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("patient"); initLayout(); loadPageData();
});
let MYAPPT = [];
const DOCS = ["Dr. Daniel Alemu","Dr. Fikru Debebe","Dr. Meron Assefa","Dr. Tsehay Mengistu"];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.APPOINTMENTS).then(r => {
    if (!r.ok) return; MYAPPT = r.data.items; renderMy();
  });
  document.getElementById("btnBook").addEventListener("click", bookModal);
}
function renderMy() {
  document.getElementById("pApptBody").innerHTML = MYAPPT.length ? MYAPPT.map(a => `<tr>
    <td><strong>${formatDate(a.date)}</strong></td><td><span class="time-pill">${a.time}</span></td>
    <td>${esc(a.doctor)}</td><td>${esc(a.dept)}</td><td>${esc(a.type)}</td>
    <td>${a.status === "cancelled" ? badge("Cancelled","danger") : a.status === "completed" ? badge("Completed","neutral") : badge("Confirmed","success")}</td>
    <td><div class="actions">
      ${a.status === "confirmed" ? `<button class="btn-icon warning" title="Reschedule" onclick="resched('${a.id}')">${ICONS.refresh}</button>
      <button class="btn-icon danger" title="Cancel" onclick="cancelA('${a.id}')">${ICONS.x}</button>` : ""}
    </div></td></tr>`).join("") : emptyRow(7);
}
function cancelA(id) {
  const a = MYAPPT.find(x => x.id === id); a.status = "cancelled"; renderMy();
  showToast("Appointment cancelled","success");
}
function resched(id) {
  const a = MYAPPT.find(x => x.id === id);
  openModal({
    title: "Reschedule Appointment",
    body: `<div class="form-group"><label>New Date</label><input class="form-control" type="date" id="rDate" value="${a.date}"></div>
      <div class="form-group"><label>New Time</label><input class="form-control" type="time" id="rTime" value="${a.time}"></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveR">Confirm</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveR").onclick = () => {
      a.date = ov.querySelector("#rDate").value; a.time = ov.querySelector("#rTime").value; a.status = "rescheduled";
      renderMy(); ov.remove(); showToast("Appointment rescheduled","success");
    };
  }});
}
function bookModal() {
  openModal({
    title: "Book Appointment",
    body: `<div class="form-group"><label>Department</label><select class="form-control" id="pDept"><option>Internal Medicine</option><option>Pediatrics</option><option>Cardiology</option><option>Maternity</option><option>Orthopedics</option></select></div>
      <div class="form-group"><label>Doctor</label><select class="form-control" id="pDoc">${DOCS.map(d=>`<option>${d}</option>`).join("")}</select></div>
      <div class="form-row"><div class="form-group"><label>Date</label><input class="form-control" type="date" id="pDate" value="${todayStr()}"></div>
      <div class="form-group"><label>Time</label><input class="form-control" type="time" id="pTime" value="09:00"></div></div>
      <div class="form-group"><label>Reason</label><textarea class="form-control" rows="2" placeholder="Briefly describe your concern…"></textarea></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="saveBk">Request Booking</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    ov.querySelector("#saveBk").onclick = () => {
      MYAPPT.unshift({ id: uid("A"), patient: getUserName(), doctor: ov.querySelector("#pDoc").value, dept: ov.querySelector("#pDept").value, date: ov.querySelector("#pDate").value, time: ov.querySelector("#pTime").value, type: "Consultation", status: "confirmed" });
      renderMy(); ov.remove(); showToast("Appointment requested — you will be notified","success");
    };
  }});
}
""",
}

# =====================================================================
# PATIENT — records
# =====================================================================
D["patient"]["records.html"] = {
"title": "Medical Records",
"body": """
<section class="card mb-4">
  <h3 class="mb-1">Record Timeline</h3>
  <p class="text-sm text-gray" style="color:#6B7280">Your complete medical history at the hospital.</p>
</section>
<div id="recordsTimeline"></div>
""" ,
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("patient"); initLayout(); loadPageData();
});
const RECORDS = [
  { date: "2026-08-11", type: "visit", title: "Follow-up Consultation", by: "Dr. Daniel Alemu", note: "Blood pressure stable at 132/84. Continue current medication." },
  { date: "2026-08-11", type: "prescription", title: "Prescription RX-2201", by: "Dr. Daniel Alemu", note: "Amlodipine 5mg once daily × 30 days" },
  { date: "2026-08-10", type: "lab", title: "HbA1c Result — 8.2%", by: "Laboratory", note: "Above target (4.0 – 5.6%). Diet review recommended." },
  { date: "2026-08-06", type: "visit", title: "ECG — Cardiology", by: "Dr. Meron Assefa", note: "Sinus rhythm, no acute ischemia." },
  { date: "2026-08-05", type: "prescription", title: "Prescription RX-2109", by: "Dr. Daniel Alemu", note: "Aspirin 81mg once daily × 30 days" },
  { date: "2026-07-28", type: "lab", title: "Complete Blood Count", by: "Laboratory", note: "All values within normal range." }
];
const IC = { visit: ["stethoscope","#EFF6FF","#1A56DB"], prescription: ["file-text","#ECFDF5","#065F46"], lab: ["flask","#F0F9FF","#0369A1"] };
function loadPageData() {
  document.getElementById("recordsTimeline").innerHTML = RECORDS.map((r, i) => {
    const c = IC[r.type];
    return `<div class="card mb-4" style="border-left:4px solid ${c[2]}">
      <div class="flex-between wrap" style="gap:10px">
        <div class="flex" style="gap:12px"><div class="stat-icon" style="background:${c[1]};color:${c[2]}">${ICONS[r.type === "prescription" ? "file-text" : r.type === "lab" ? "flask" : "stethoscope"]}</div>
        <div><div style="font-weight:700;font-size:15px">${esc(r.title)}</div>
        <div class="text-sm text-gray" style="color:#6B7280">${formatDate(r.date)} · ${esc(r.by)}</div></div></div>
        <span class="badge badge-${r.type === "visit" ? "primary" : r.type === "lab" ? "info" : "success"}">${r.type}</span></div>
      <p class="mt-3" style="color:#374151">${esc(r.note)}</p>
    </div>`;
  }).join("");
}
""",
}

# =====================================================================
# PATIENT — results
# =====================================================================
D["patient"]["results.html"] = {
"title": "Lab Results",
"body": """
<div class="card" style="padding:0">
  <div class="table-toolbar"><h3 style="font-size:16px">Your Lab Results</h3>
    <span class="badge badge-info" id="resCount">0 results</span></div>
  <div class="table-wrap">
    <table class="data-table" id="resTable">
      <thead><tr><th class="sortable">Test</th><th class="sortable">Date</th><th class="sortable">Status</th><th class="sortable">AI Flag</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="resBody"></tbody>
    </table>
  </div>
  %s
</div>
""" % pagination("resPager"),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("patient"); initLayout(); loadPageData();
});
let RESULTS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.LAB_RESULTS).then(r => {
    if (!r.ok) return; RESULTS = r.data.items; render();
    attachDataTable(document.getElementById("resTable"), { pagerEl: document.getElementById("resPager"), pageSize: 8,
      onRender: n => document.getElementById("resCount").textContent = n + " results" });
  });
}
function render() {
  document.getElementById("resBody").innerHTML = RESULTS.length ? RESULTS.map(r => `<tr>
    <td><strong>${esc(r.test)}</strong></td><td>${formatDate(r.date)}</td>
    <td>${r.status === "normal" ? badge("Normal","success") : badge("Abnormal","danger")}</td>
    <td>${r.ai_flag === "abnormal" ? badge("AI: Abnormal","danger") : badge("AI: Normal","success")}</td>
    <td><div class="actions"><button class="btn-icon primary" title="View" onclick="viewRes('${r.id}')">${ICONS.eye}</button>
    <button class="btn-icon" title="Print" onclick="printRes('${r.id}')">${ICONS.printer}</button></div></td></tr>`).join("") : emptyRow(5);
}
function viewRes(id) {
  const r = RESULTS.find(x => x.id === id);
  openModal({
    title: "Lab Report — " + r.test,
    body: `<div class="detail-list"><div class="detail-item"><span class="k">Date</span><span class="v">${formatDate(r.date)}</span></div>
      <div class="detail-item"><span class="k">Overall</span><span class="v">${esc(r.status)}</span></div></div>
      <h3 class="mt-4 mb-2" style="font-size:15px">Values</h3>
      <table class="data-table"><thead><tr><th>Parameter</th><th>Normal Range</th><th>Value</th><th>Status</th></tr></thead><tbody>
      ${r.values.map(v => `<tr><td>${esc(v.name)}</td><td class="text-sm text-gray" style="color:#6B7280">${esc(v.range)}</td><td><strong>${esc(v.value)}</strong></td>
      <td>${v.status === "normal" ? badge("Normal","success") : badge("Abnormal","danger")}</td></tr>`).join("")}</tbody></table>
      <div class="disclaimer"><span>${ICONS.info}</span><div>Questions about your results? Ask your doctor or use the AI Chatbot.</div></div>
      <div class="flex gap-3 mt-4"><a class="btn btn-primary" href="ai-chatbot.html">${ICONS.chat} Ask AI</a></div>`,
    size: "lg"
  });
}
function printRes(id) {
  const r = RESULTS.find(x => x.id === id);
  const w = window.open("", "_blank");
  w.document.write(`<html><head><title>Lab Report</title><style>body{font-family:monospace;padding:40px}.h{text-align:center;border-bottom:2px solid #000;padding-bottom:10px;margin-bottom:20px}</style></head><body>
    <div class="h"><h2>Wolaita Sodo University Hospital</h2><p>Laboratory Report — ${r.test}</p></div>
    <p><strong>Date:</strong> ${formatDate(r.date)}</p>
    <table width="100%" border="1" cellpadding="8" style="border-collapse:collapse;margin-top:16px">
    <tr><th align="left">Parameter</th><th align="left">Normal Range</th><th align="left">Value</th><th align="left">Status</th></tr>
    ${r.values.map(v => `<tr><td>${v.name}</td><td>${v.range}</td><td>${v.value}</td><td>${v.status}</td></tr>`).join("")}</table></body></html>`);
  w.document.close(); w.print();
}
""",
}

# =====================================================================
# PATIENT — bills
# =====================================================================
D["patient"]["bills.html"] = {
"title": "Bills & Payments",
"body": """
<div class="alert alert-warning mb-4" id="outstandingBanner"><span>%s</span>
  <div class="alert-body"><span class="alert-title">Outstanding balance: </span><strong id="outTotal" style="font-size:16px">ETB 0.00</strong> — please settle to continue receiving services.</div></div>
<div class="card" style="padding:0">
  <div class="table-toolbar"><h3 style="font-size:16px">Billing History</h3>
    <button class="btn btn-secondary" onclick="printAll()">%s Print Receipts</button></div>
  <div class="table-wrap">
    <table class="data-table">
      <thead><tr><th class="sortable">Date</th><th class="sortable">Description</th><th class="sortable">Amount (ETB)</th><th class="sortable">Status</th><th style="text-align:right">Actions</th></tr></thead>
      <tbody id="billBody"></tbody>
    </table>
  </div>
</div>
""" % (icon("wallet"), icon("printer")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("patient"); initLayout(); loadPageData();
});
let BILLS = [];
function loadPageData() {
  apiFetch(CONFIG.ENDPOINTS.BILLS).then(r => {
    if (!r.ok) return; BILLS = r.data.items; renderBills();
  });
}
function renderBills() {
  const out = BILLS.filter(b => b.status !== "paid").reduce((s, b) => s + b.amount, 0);
  document.getElementById("outTotal").textContent = formatCurrency(out);
  document.getElementById("billBody").innerHTML = BILLS.map(b => `<tr>
    <td>${formatDate(b.date)}</td><td>${esc(b.description)}</td>
    <td><strong>${formatCurrency(b.amount)}</strong></td>
    <td>${b.status === "paid" ? badge("Paid","success") : b.status === "pending" ? badge("Pending","warning") : badge("Overdue","danger")}</td>
    <td><div class="actions"><button class="btn-icon primary" title="View detail" onclick="viewBill('${b.id}')">${ICONS.eye}</button>
    ${b.status === "paid" ? `<button class="btn-icon" title="Print receipt" onclick="printBill('${b.id}')">${ICONS.printer}</button>` : ""}</div></td></tr>`).join("") || emptyRow(5);
}
function viewBill(id) {
  const b = BILLS.find(x => x.id === id);
  openModal({
    title: "Bill Detail — " + b.id,
    body: `<div class="detail-list">
      <div class="detail-item"><span class="k">Date</span><span class="v">${formatDate(b.date)}</span></div>
      <div class="detail-item"><span class="k">Description</span><span class="v">${esc(b.description)}</span></div>
      <div class="detail-item"><span class="k">Status</span><span class="v">${esc(b.status)}</span></div></div>
      <h3 class="mt-4 mb-2" style="font-size:15px">Itemized Breakdown</h3>
      <div class="receipt">
        <div class="r-row"><span>Service charge</span><span>${formatCurrency(b.amount * 0.7)}</span></div>
        <div class="r-row"><span>Pharmacy / consumables</span><span>${formatCurrency(b.amount * 0.25)}</span></div>
        <div class="r-row"><span>Administrative fee</span><span>${formatCurrency(b.amount * 0.05)}</span></div>
        <div class="r-row r-total"><span>Total</span><span>${formatCurrency(b.amount)}</span></div>
      </div>`
  });
}
function printBill(id) {
  const b = BILLS.find(x => x.id === id);
  const w = window.open("", "_blank");
  w.document.write(`<html><head><title>Receipt ${b.id}</title><style>body{font-family:monospace;padding:40px}.h{text-align:center;border-bottom:2px solid #000;padding-bottom:10px;margin-bottom:20px}</style></head><body>
    <div class="h"><h2>Wolaita Sodo University Hospital</h2><p>Official Receipt</p></div>
    <p><strong>Receipt No:</strong> ${b.id}</p><p><strong>Date:</strong> ${formatDate(b.date)}</p>
    <p><strong>Description:</strong> ${b.description}</p><p><strong>Amount Paid:</strong> ${formatCurrency(b.amount)}</p>
    <p><strong>Status:</strong> PAID ✓</p><p style="margin-top:24px">Thank you! ______</p></body></html>`);
  w.document.close(); w.print();
}
function printAll() { showToast("Select a paid bill to print its receipt","info"); }
""",
}

# =====================================================================
# PATIENT — ai-chatbot (Module 7)
# =====================================================================
D["patient"]["ai-chatbot.html"] = {
"title": "AI Health Assistant",
"body": """
<div class="card" style="display:flex;flex-direction:column;height:calc(100vh - 140px);min-height:520px;padding:0">
  <div class="panel-header">
    <div class="flex" style="gap:12px"><div class="stat-icon" style="background:#F5F3FF;color:#7C3AED;width:40px;height:40px">%s</div>
      <div><h3 style="font-size:16px">MedIQ AI Assistant</h3><div class="text-sm" style="color:#6B7280">Symptom checker · always on</div></div></div>
    <div class="flex" style="gap:8px">
      <button class="btn btn-secondary btn-sm" id="btnClear">%s Clear</button>
      <button class="btn btn-secondary btn-sm" id="btnSave">%s Save</button>
    </div>
  </div>
  <div id="chatArea" class="chat-area" style="flex:1;overflow-y:auto;background:#F9FAFB"></div>
  <div class="panel-header" style="border-top:1px solid #E5E7EB;border-bottom:none">
    <div class="flex" style="gap:10px;width:100%%">
      <input class="form-control" id="chatInput" placeholder="Describe your symptoms… (e.g. I have fever and chills)">
      <button class="btn btn-primary" id="btnSend">%s Send</button>
    </div>
  </div>
</div>
""" % (icon("bot") if False else icon("brain"), icon("x"), icon("download"), icon("send")),
"script": """
document.addEventListener("DOMContentLoaded", () => {
  checkSession(); checkRoleAccess("patient"); initLayout(); loadPageData();
});
function loadPageData() {
  document.getElementById("btnSend").addEventListener("click", sendMsg);
  document.getElementById("chatInput").addEventListener("keydown", e => { if (e.key === "Enter") sendMsg(); });
  document.getElementById("btnClear").addEventListener("click", () => {
    document.getElementById("chatArea").innerHTML = "";
    addMsg("ai", "Hello! I'm your MedIQ health assistant. Describe your symptoms and I'll suggest possible conditions, urgency and next steps. Remember — this is not a diagnosis.");
  });
  document.getElementById("btnSave").addEventListener("click", () => showToast("Conversation saved to your records","success"));
  // Intro message
  addMsg("ai", "Hello! I'm your MedIQ health assistant. Describe your symptoms and I'll suggest possible conditions, urgency and next steps. Remember — this is not a diagnosis.");
}
function sendMsg() {
  const input = document.getElementById("chatInput");
  const text = input.value.trim();
  if (!text) return;
  addMsg("user", text);
  input.value = "";
  const typing = document.createElement("div");
  typing.className = "chat-msg ai"; typing.id = "typing";
  typing.innerHTML = '<div class="flex" style="gap:6px"><span class="spinner sm" style="border-color:#C7DBFE;border-top-color:#1A56DB"></span> AI is thinking…</div>';
  document.getElementById("chatArea").appendChild(typing);
  document.getElementById("chatArea").scrollTop = document.getElementById("chatArea").scrollHeight;
  symptomChat({ message: text, session_id: getUserRole() }, res => {
    typing.remove();
    renderAIResponse(res);
  });
}
function renderAIResponse(res) {
  const urg = res.urgency; // green | orange | red
  const cfg = {
    green: ["success","Self-care","You can manage this at home. Monitor symptoms and rest."],
    orange: ["warning","See a doctor","Book an appointment within 24–48 hours."],
    red: ["danger","Emergency","Seek immediate emergency care — do not wait."]
  }[urg] || ["neutral","Follow up",""];
  const conds = res.conditions.map(c => `<span class="badge badge-primary">${esc(c)}</span>`).join(" ");
  addMsg("ai", `
    <strong>Possible conditions:</strong><br><div class="mt-2 mb-2">${conds}</div>
    <span class="badge badge-${cfg[0]}"><span class="dot"></span> Urgency: ${cfg[1]}</span>
    <div class="mt-2" style="font-size:13px">${esc(res.action || "")}</div>
    <div class="mt-2 text-sm" style="opacity:.85">${esc(res.reply)}</div>
    <div class="mt-2 text-sm" style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:8px;color:#92400E">💬 ${esc(res.follow_up || "")}</div>
    <div class="disclaimer" style="margin-top:10px">${ICONS.info} <div>${esc(res.disclaimer || "AI suggestions only. Final diagnosis by doctor.")}</div></div>`);
  if (urg === "red") {
    addMsg("ai", "🚨 Based on your description this may be urgent. Please go to the <strong>Emergency Department</strong> or call 907 (emergency services in Ethiopia) right away.");
  }
}
function addMsg(who, html) {
  const area = document.getElementById("chatArea");
  const div = document.createElement("div");
  div.className = "chat-msg " + who;
  div.innerHTML = html + `<span class="msg-time">${new Date().toTimeString().slice(0, 5)}</span>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}
""",
}
