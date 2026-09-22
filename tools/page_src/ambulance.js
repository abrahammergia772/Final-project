const KEY = "wsh_amb_v1";
const PLACES = ["Merkato", "Gido", "Wadu", "Otona", "Fana", "Damot Gale road", "University campus", "Wolaita Sodo bus station", "Areka junction"];
function seedFleet() {
  return [
    { id: "AMB-01", crew: "Nurse Alma + driver Bekele", status: "available", place: "Hospital bay" },
    { id: "AMB-02", crew: "Nurse Tadesse + driver Getu", status: "en-route", place: "Otona", eta: "8 min", case: "RTA — two casualties" },
    { id: "AMB-03", crew: "Paramedic Selam + driver Hailu", status: "at-scene", place: "Merkato", eta: "on scene", case: "Unconscious adult" },
    { id: "AMB-04", crew: "—", status: "maintenance", place: "Workshop", case: "Brake service" }
  ];
}
let fleet = [], log = [];
function loadA() {
  try { const r = sessionStorage.getItem(KEY); if (r) { const s = JSON.parse(r); fleet = s.fleet; log = s.log; return; } } catch (e) {}
  fleet = seedFleet();
  log = [{ time: "08:12", text: "AMB-02 dispatched to Otona — RTA" }, { time: "07:40", text: "AMB-03 on scene at Merkato" }];
}
function saveA() { try { sessionStorage.setItem(KEY, JSON.stringify({ fleet, log })); } catch (e) {} }
function ambBadge(s) {
  return badge(s.replace("-", " "), s === "available" ? "success" : s === "maintenance" ? "neutral" : s === "at-scene" ? "danger" : "warning");
}
function renderAmb() {
  document.getElementById("fleetGrid").innerHTML = fleet.map(v => `
    <article class="fleet-card">
      <div class="flex-between"><h3>${esc(v.id)}</h3>${ambBadge(v.status)}</div>
      <div class="text-sm text-gray mt-1">${esc(v.crew)}</div>
      <div class="mt-2"><strong>${esc(v.place)}</strong></div>
      <div class="text-sm">${esc(v.case || "Standing by")}${v.eta ? " · ETA " + esc(v.eta) : ""}</div>
      <div class="mt-3">${v.status !== "maintenance" && v.status !== "available" ? `<button class="btn btn-primary btn-sm" data-adv="${esc(v.id)}">Advance status</button>` : ""}
        ${v.status === "available" ? `<button class="btn btn-secondary btn-sm" data-pick="${esc(v.id)}">Dispatch this unit</button>` : ""}</div>
    </article>`).join("");
  document.getElementById("missionLog").innerHTML = log.map(l => `<div class="mission"><div class="feed-icon tile-info">${ICONS.truck}</div><div><div class="text-sm text-gray">${esc(l.time)}</div><div>${esc(l.text)}</div></div></div>`).join("");
  document.querySelectorAll("[data-adv]").forEach(b => b.onclick = () => advance(b.dataset.adv));
  document.querySelectorAll("[data-pick]").forEach(b => b.onclick = () => { document.getElementById("ambUnit").value = b.dataset.pick; document.getElementById("ambForm").scrollIntoView({ behavior: "smooth" }); });
  const free = fleet.filter(v => v.status === "available").length;
  document.getElementById("ambFree").textContent = free;
  document.getElementById("ambActive").textContent = fleet.filter(v => v.status === "en-route" || v.status === "at-scene" || v.status === "transporting").length;
}
function advance(id) {
  const v = fleet.find(x => x.id === id);
  const order = ["en-route", "at-scene", "transporting", "available"];
  const i = order.indexOf(v.status);
  v.status = order[Math.min(order.length - 1, i + 1)] || "available";
  if (v.status === "available") { v.case = ""; v.eta = ""; v.place = "Hospital bay"; }
  if (v.status === "transporting") { v.eta = "12 min"; v.place = "En route to WSUH"; }
  const now = new Date().toTimeString().slice(0, 5);
  log.unshift({ time: now, text: v.id + " → " + v.status.replace("-", " ") });
  saveA(); renderAmb(); showToast(v.id + " is now " + v.status.replace("-", " "), "info");
}
function bootPage() {
  const ICONS = window.ICONS || {};
  window.ICONS = ICONS;
  loadA();
  document.getElementById("ambUnit").innerHTML = fleet.map(v => `<option value="${esc(v.id)}">${esc(v.id)} · ${esc(v.status)}</option>`).join("");
  document.getElementById("ambPlace").innerHTML = PLACES.map(p => `<option>${esc(p)}</option>`).join("");
  document.getElementById("ambForm").onsubmit = (e) => {
    e.preventDefault();
    const id = document.getElementById("ambUnit").value;
    const v = fleet.find(x => x.id === id);
    if (!v || v.status === "maintenance") { showToast("That unit cannot be dispatched", "error"); return; }
    if (v.status !== "available") { showToast(id + " is already on a call", "warning"); return; }
    v.status = "en-route";
    v.place = document.getElementById("ambPlace").value;
    v.case = document.getElementById("ambCase").value.trim() || "Emergency call";
    v.eta = document.getElementById("ambPri").value === "Emergency" ? "6 min" : "14 min";
    const now = new Date().toTimeString().slice(0, 5);
    log.unshift({ time: now, text: id + " dispatched to " + v.place + " — " + v.case });
    saveA(); renderAmb();
    showToast(id + " dispatched to " + v.place, "success");
    e.target.reset();
  };
  renderAmb();
}
