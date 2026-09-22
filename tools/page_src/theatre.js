const KEY = "wsh_ot_v1";
function seedOT() {
  return [
    { id: "OT-104", theatre: "OT-1", time: "08:30", patient: "Selamawit Tadesse", proc: "C-section", surgeon: "Dr. Daniel Alemu", anaesth: "Dr. Hanna", status: "done" },
    { id: "OT-105", theatre: "OT-1", time: "11:00", patient: "Yonas Girma", proc: "Appendectomy", surgeon: "Dr. Daniel Alemu", anaesth: "Dr. Hanna", status: "in-progress" },
    { id: "OT-106", theatre: "OT-2", time: "09:15", patient: "Samuel Getachew", proc: "Inguinal hernia", surgeon: "Dr. Mekdes", anaesth: "Dr. Abel", status: "scheduled" },
    { id: "OT-107", theatre: "OT-2", time: "13:30", patient: "Bereket Wolde", proc: "ORIF tibia", surgeon: "Dr. Mekdes", anaesth: "Dr. Abel", status: "scheduled" },
    { id: "OT-108", theatre: "Maternity OT", time: "15:00", patient: "Meron Desta", proc: "Emergency C-section", surgeon: "Dr. Sara", anaesth: "Dr. Hanna", status: "scheduled" }
  ];
}
let cases = [];
function loadT() { try { const r = sessionStorage.getItem(KEY); if (r) { cases = JSON.parse(r); return; } } catch (e) {} cases = seedOT(); }
function saveT() { try { sessionStorage.setItem(KEY, JSON.stringify(cases)); } catch (e) {} }
function otBadge(s) {
  return badge(s.replace("-", " "), s === "done" ? "success" : s === "in-progress" ? "warning" : s === "cancelled" ? "neutral" : "info");
}
function renderOT() {
  const rooms = ["OT-1", "OT-2", "Maternity OT"];
  document.getElementById("otGrid").innerHTML = rooms.map(r => {
    const live = cases.find(c => c.theatre === r && c.status === "in-progress");
    const next = cases.find(c => c.theatre === r && c.status === "scheduled");
    return `<article class="ot-card"><h3>${esc(r)}</h3>
      <div class="text-sm text-gray">${live ? "In theatre now" : "No case in progress"}</div>
      <div class="mt-2"><strong>${esc(live ? live.patient + " — " + live.proc : "Idle")}</strong></div>
      <div class="text-sm mt-1">Next: ${esc(next ? next.time + " " + next.proc : "—")}</div></article>`;
  }).join("");
  document.querySelector("#otTable tbody").innerHTML = cases.map(c => `<tr>
    <td>${esc(c.time)}</td><td>${esc(c.theatre)}</td><td>${esc(c.patient)}</td><td>${esc(c.proc)}</td>
    <td>${esc(c.surgeon)}</td><td>${otBadge(c.status)}</td>
    <td class="actions">${c.status === "scheduled" ? `<button class="btn btn-primary btn-sm" data-start="${esc(c.id)}">Start</button>` : ""}
      ${c.status === "in-progress" ? `<button class="btn btn-success btn-sm" data-done="${esc(c.id)}">Complete</button>` : ""}
      ${c.status === "scheduled" ? `<button class="btn btn-secondary btn-sm" data-cancel="${esc(c.id)}">Cancel</button>` : ""}</td>
  </tr>`).join("");
  document.querySelectorAll("[data-start]").forEach(b => b.onclick = () => setStatus(b.dataset.start, "in-progress", "Case started"));
  document.querySelectorAll("[data-done]").forEach(b => b.onclick = () => setStatus(b.dataset.done, "done", "Patient to recovery"));
  document.querySelectorAll("[data-cancel]").forEach(b => b.onclick = () => setStatus(b.dataset.cancel, "cancelled", "Case cancelled"));
}
function setStatus(id, status, msg) {
  const c = cases.find(x => x.id === id);
  if (status === "in-progress" && cases.some(x => x.theatre === c.theatre && x.status === "in-progress")) {
    showToast(c.theatre + " already has a case in progress", "error"); return;
  }
  c.status = status; saveT(); renderOT(); showToast(msg, status === "cancelled" ? "warning" : "success");
}
function bootPage() {
  const ICONS = window.ICONS || {};
  window.ICONS = ICONS;
  loadT();
  document.getElementById("otForm").onsubmit = (e) => {
    e.preventDefault();
    const patient = document.getElementById("otPatient").value.trim();
    const proc = document.getElementById("otProc").value.trim();
    const time = document.getElementById("otTime").value;
    if (!patient || !proc || !time) { showToast("Patient, procedure and time are required", "warning"); return; }
    cases.push({
      id: "OT-" + (200 + cases.length),
      theatre: document.getElementById("otRoom").value,
      time, patient, proc,
      surgeon: document.getElementById("otSurg").value.trim() || "Dr. on call",
      anaesth: "Dr. on call",
      status: "scheduled"
    });
    saveT(); renderOT(); showToast("Theatre slot booked", "success");
    e.target.reset();
  };
  renderOT();
}
