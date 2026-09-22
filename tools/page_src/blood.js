const KEY = "wsh_blood_v1";
const TYPES = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"];
function seedUnits() {
  const rows = [];
  const donors = ["Gemechu T.", "Almaz K.", "Tesfaye B.", "Hirut A.", "Mulugeta D.", "Senait W.", "Kebede L.", "Aster G."];
  TYPES.forEach((t, ti) => {
    const n = t.endsWith("-") ? 2 : 4;
    for (let i = 0; i < n; i++) {
      const exp = new Date(); exp.setDate(exp.getDate() + (i === 0 && ti % 3 === 0 ? 3 : 18 + i * 4));
      rows.push({
        id: "BB-" + t.replace("+", "P").replace("-", "N") + "-" + (10 + i),
        type: t, donor: donors[(ti + i) % donors.length],
        collected: "2026-09-" + String(8 + i).padStart(2, "0"),
        expires: exp.toISOString().slice(0, 10),
        status: i === 0 && t === "O-" ? "reserved" : "available",
        for: i === 0 && t === "O-" ? "ICU-02 Frehiwot A." : ""
      });
    }
  });
  return rows;
}
let units = [];
function loadU() {
  try { const r = sessionStorage.getItem(KEY); if (r) { units = JSON.parse(r); return; } } catch (e) {}
  units = seedUnits();
}
function saveU() { try { sessionStorage.setItem(KEY, JSON.stringify(units)); } catch (e) {} }
function daysLeft(iso) {
  return Math.round((new Date(iso + "T00:00:00") - new Date(new Date().toDateString())) / 86400000);
}
function renderBlood() {
  const by = {};
  TYPES.forEach(t => by[t] = units.filter(u => u.type === t && u.status !== "issued"));
  document.getElementById("bloodGrid").innerHTML = TYPES.map(t => {
    const avail = by[t].filter(u => u.status === "available").length;
    const crit = avail <= 1;
    return `<div class="blood-card"><div class="bt ${crit ? "crit" : ""}">${esc(t)}</div>
      <div class="stat-value" style="font-size:28px">${avail}</div>
      <div class="text-sm text-gray">${by[t].length} on shelf · ${crit ? "low stock" : "stable"}</div>
      <div class="occ-meter mt-2"><span style="width:${Math.min(100, avail * 22)}%;background:${crit ? "var(--danger)" : "var(--danger)"}"></span></div></div>`;
  }).join("");
  const expiring = units.filter(u => u.status !== "issued" && daysLeft(u.expires) <= 7).length;
  const reserved = units.filter(u => u.status === "reserved").length;
  document.getElementById("bloodStats").innerHTML = `
    <div class="stat-card"><div class="stat-icon tile-danger">${ICONS.droplet}</div><div><div class="stat-value">${units.filter(u => u.status === "available").length}</div><div class="stat-label">Units available</div></div></div>
    <div class="stat-card color-warning"><div class="stat-icon">${ICONS.clock}</div><div><div class="stat-value">${expiring}</div><div class="stat-label">Expiring in 7 days</div></div></div>
    <div class="stat-card color-info"><div class="stat-icon">${ICONS.clipboard}</div><div><div class="stat-value">${reserved}</div><div class="stat-label">Reserved for surgery</div></div></div>
    <div class="stat-card color-success"><div class="stat-icon">${ICONS.check}</div><div><div class="stat-value">${units.filter(u => u.status === "issued").length}</div><div class="stat-label">Issued this session</div></div></div>`;
  const q = (document.getElementById("bloodSearch").value || "").toLowerCase();
  const typeF = document.getElementById("bloodType").value;
  const rows = units.filter(u => (!typeF || u.type === typeF) && (!q || (u.id + u.donor + u.for + u.status).toLowerCase().includes(q)));
  document.querySelector("#bloodTable tbody").innerHTML = rows.map(u => {
    const d = daysLeft(u.expires);
    const kind = u.status === "issued" ? "neutral" : u.status === "reserved" ? "info" : d <= 7 ? "warning" : "success";
    return `<tr>
      <td>${esc(u.id)}</td><td><strong>${esc(u.type)}</strong></td><td>${esc(u.donor)}</td>
      <td>${formatDate(u.expires)} <span class="text-sm text-gray">(${d}d)</span></td>
      <td>${badge(u.status, kind)}</td><td>${esc(u.for || "—")}</td>
      <td class="actions">
        ${u.status === "available" ? `<button class="btn btn-secondary btn-sm" data-res="${esc(u.id)}">Reserve</button> <button class="btn btn-primary btn-sm" data-iss="${esc(u.id)}">Issue</button>` : ""}
        ${u.status === "reserved" ? `<button class="btn btn-primary btn-sm" data-iss="${esc(u.id)}">Issue</button> <button class="btn btn-secondary btn-sm" data-rel="${esc(u.id)}">Release</button>` : ""}
      </td></tr>`;
  }).join("") || emptyRow(7, "No units match.");
  document.querySelectorAll("[data-res]").forEach(b => b.onclick = () => reserveUnit(b.dataset.res));
  document.querySelectorAll("[data-iss]").forEach(b => b.onclick = () => issueUnit(b.dataset.iss));
  document.querySelectorAll("[data-rel]").forEach(b => b.onclick = () => {
    const u = units.find(x => x.id === b.dataset.rel); u.status = "available"; u.for = ""; saveU(); renderBlood(); showToast("Unit released", "info");
  });
}
function reserveUnit(id) {
  openModal({
    title: "Reserve " + id,
    body: `<div class="form-group"><label>Reserve for</label><input class="form-control" id="resFor" placeholder="Patient or theatre, e.g. OT-1 C-section"></div>
      <p class="module-note">Crossmatch is assumed compatible in this demo. A real bank would hold the unit until the lab confirms.</p>`,
    footer: `<button class="btn btn-secondary" data-close>Cancel</button><button class="btn btn-primary" id="resOk">Reserve</button>`
  }, { onMount(ov) {
    ov.querySelector("#resOk").onclick = () => {
      const forWhom = ov.querySelector("#resFor").value.trim();
      if (!forWhom) { showToast("Who is this reserved for?", "warning"); return; }
      const u = units.find(x => x.id === id);
      u.status = "reserved"; u.for = forWhom; saveU(); closeModal(ov); renderBlood();
      showToast(id + " reserved", "success");
    };
  }});
}
function issueUnit(id) {
  const u = units.find(x => x.id === id);
  u.status = "issued"; if (!u.for) u.for = "Issued at counter";
  saveU(); renderBlood(); showToast(id + " issued from the blood bank", "success");
}
function bootPage() {
  const ICONS = window.ICONS || {};
  window.ICONS = ICONS;
  loadU();
  document.getElementById("bloodType").innerHTML = `<option value="">All groups</option>` + TYPES.map(t => `<option>${t}</option>`).join("");
  document.getElementById("bloodSearch").oninput = debounce(renderBlood, 200);
  document.getElementById("bloodType").onchange = renderBlood;
  document.getElementById("addDonation").onclick = () => {
    const type = document.getElementById("donType").value;
    const donor = document.getElementById("donName").value.trim();
    if (!donor) { showToast("Donor name is required", "warning"); return; }
    const exp = new Date(); exp.setDate(exp.getDate() + 35);
    units.unshift({ id: "BB-NEW-" + (units.length + 20), type, donor, collected: todayStr(), expires: exp.toISOString().slice(0, 10), status: "available", for: "" });
    saveU(); renderBlood(); showToast("Donation logged — " + type, "success");
    document.getElementById("donName").value = "";
  };
  renderBlood();
}
