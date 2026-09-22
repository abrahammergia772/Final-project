const KEY = "wsh_img_v1";
function seedImg() {
  return [
    { id: "IMG-331", patient: "Liya Hailu", study: "Chest X-ray", priority: "Urgent", status: "reported", note: "No acute infiltrate" },
    { id: "IMG-332", patient: "Marta Tesfaye", study: "ECG + chest X-ray", priority: "Emergency", status: "in-progress", note: "" },
    { id: "IMG-333", patient: "Abel Mekonnen", study: "Abdominal ultrasound", priority: "Routine", status: "scheduled", note: "" },
    { id: "IMG-334", patient: "Samuel Getachew", study: "Pelvis X-ray", priority: "Urgent", status: "scheduled", note: "" },
    { id: "IMG-335", patient: "Frehiwot Assefa", study: "CT head", priority: "Emergency", status: "scheduled", note: "" },
    { id: "IMG-336", patient: "Kidus Haile", study: "Chest X-ray", priority: "Routine", status: "reported", note: "Hyperinflation, no focal consolidation" }
  ];
}
let studies = [];
function loadI() { try { const r = sessionStorage.getItem(KEY); if (r) { studies = JSON.parse(r); return; } } catch (e) {} studies = seedImg(); }
function saveI() { try { sessionStorage.setItem(KEY, JSON.stringify(studies)); } catch (e) {} }
function imgBadge(s) { return badge(s.replace("-", " "), s === "reported" ? "success" : s === "in-progress" ? "warning" : "info"); }
function priBadge(p) { return badge(p, p === "Emergency" ? "danger" : p === "Urgent" ? "warning" : "neutral"); }
function renderImg() {
  const waiting = studies.filter(s => s.status !== "reported").length;
  document.getElementById("imgStats").innerHTML = `
    <div class="stat-card"><div class="stat-icon tile-info">${ICONS.eye}</div><div><div class="stat-value">${studies.length}</div><div class="stat-label">Studies today</div></div></div>
    <div class="stat-card color-warning"><div class="stat-icon">${ICONS.clock}</div><div><div class="stat-value">${waiting}</div><div class="stat-label">Not yet reported</div></div></div>
    <div class="stat-card color-danger"><div class="stat-icon">${ICONS.alert}</div><div><div class="stat-value">${studies.filter(s => s.priority === "Emergency" && s.status !== "reported").length}</div><div class="stat-label">Emergency queue</div></div></div>
    <div class="stat-card color-success"><div class="stat-icon">${ICONS.check}</div><div><div class="stat-value">${studies.filter(s => s.status === "reported").length}</div><div class="stat-label">Reports released</div></div></div>`;
  const f = document.getElementById("imgFilter").value;
  const rows = studies.filter(s => !f || s.status === f || s.study.toLowerCase().includes(f));
  document.querySelector("#imgTable tbody").innerHTML = rows.map(s => `<tr class="${s.priority === "Emergency" && s.status !== "reported" ? "row-danger" : ""}">
    <td>${esc(s.id)}</td><td>${esc(s.patient)}</td><td>${esc(s.study)}</td><td>${priBadge(s.priority)}</td>
    <td>${imgBadge(s.status)}</td><td>${esc(s.note || "—")}</td>
    <td class="actions">
      ${s.status === "scheduled" ? `<button class="btn btn-primary btn-sm" data-go="${esc(s.id)}">Start</button>` : ""}
      ${s.status !== "reported" ? `<button class="btn btn-secondary btn-sm" data-rep="${esc(s.id)}">Report</button>` : `<button class="btn btn-secondary btn-sm" data-view="${esc(s.id)}">View</button>`}
    </td></tr>`).join("") || emptyRow(7, "No studies.");
  document.querySelectorAll("[data-go]").forEach(b => b.onclick = () => {
    studies.find(x => x.id === b.dataset.go).status = "in-progress"; saveI(); renderImg(); showToast("Study started", "info");
  });
  document.querySelectorAll("[data-rep]").forEach(b => b.onclick = () => reportStudy(b.dataset.rep));
  document.querySelectorAll("[data-view]").forEach(b => b.onclick = () => reportStudy(b.dataset.view, true));
}
function reportStudy(id, viewOnly) {
  const s = studies.find(x => x.id === id);
  openModal({
    title: s.study + " · " + s.patient,
    body: `<div class="detail-list mb-3">
      <div class="detail-item"><span class="k">Priority</span><span class="v">${priBadge(s.priority)}</span></div>
      <div class="detail-item"><span class="k">Status</span><span class="v">${imgBadge(s.status)}</span></div>
    </div>
    <div class="form-group"><label>Report note</label><textarea class="form-control" id="imgNote" ${viewOnly ? "readonly" : ""}>${esc(s.note || "")}</textarea></div>
    <p class="module-note">Educational demo only — not a diagnostic report.</p>`,
    footer: viewOnly ? `<button class="btn btn-secondary" data-close>Close</button>` : `<button class="btn btn-secondary" data-close>Cancel</button><button class="btn btn-primary" id="imgSave">Release report</button>`
  }, { onMount(ov) {
    const btn = ov.querySelector("#imgSave");
    if (!btn) return;
    btn.onclick = () => {
      s.note = ov.querySelector("#imgNote").value.trim() || "Reported — see clinical note";
      s.status = "reported"; saveI(); closeModal(ov); renderImg(); showToast("Report released to the chart", "success");
    };
  }});
}
function bootPage() {
  const ICONS = window.ICONS || {};
  window.ICONS = ICONS;
  loadI();
  document.getElementById("imgFilter").onchange = renderImg;
  document.getElementById("imgForm").onsubmit = (e) => {
    e.preventDefault();
    const patient = document.getElementById("imgPatient").value.trim();
    const study = document.getElementById("imgStudy").value;
    if (!patient) { showToast("Patient name is required", "warning"); return; }
    studies.unshift({ id: "IMG-" + (400 + studies.length), patient, study, priority: document.getElementById("imgPri").value, status: "scheduled", note: "" });
    saveI(); renderImg(); showToast("Imaging request sent", "success");
    e.target.reset();
  };
  renderImg();
}
