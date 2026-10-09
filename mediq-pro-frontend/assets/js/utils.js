/* ============================================================
   Wolaita Sodo Hospital — utils.js
   Shared helpers: dates, currency, toasts, modals, loading,
   tables, CSV export, SVG charts (no external libraries)
   ============================================================ */

// ---------- Dates ----------
function pad(n) { return String(n).padStart(2, "0"); }

// ISO or "YYYY-MM-DD" → DD/MM/YYYY (Ethiopian standard)
function formatDate(input) {
  if (!input) return "—";
  const d = new Date(input.includes("T") ? input : input + "T00:00:00");
  if (isNaN(d)) return String(input);
  return pad(d.getDate()) + "/" + pad(d.getMonth() + 1) + "/" + d.getFullYear();
}

function formatDateTime(input) {
  if (!input) return "—";
  const d = new Date(input);
  if (isNaN(d)) return String(input);
  return formatDate(input) + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
}

function todayStr() {
  const d = new Date();
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
}

// ---------- Currency (ETB) ----------
function formatCurrency(amount, withSymbol = true) {
  const n = Number(amount) || 0;
  const s = n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return withSymbol ? "ETB " + s : s;
}

// ---------- Toasts ----------
function showToast(message, type = "info", duration = 4000) {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    document.body.appendChild(container);
  }
  const icons = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>',
    error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/></svg>',
    warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>'
  };
  const toast = document.createElement("div");
  toast.className = "toast toast-" + type;
  toast.innerHTML = (icons[type] || icons.info) + "<div>" + escapeHtml(message) + "</div>";
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("hide");
    setTimeout(() => toast.remove(), 350);
  }, duration);
}

// ---------- Loading overlay ----------
function showLoading(text = "Loading…") {
  let overlay = document.getElementById("loadingOverlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "loadingOverlay";
    overlay.innerHTML = '<div class="spinner"></div><div class="loading-text" id="loadingText"></div>';
    document.body.appendChild(overlay);
  }
  document.getElementById("loadingText").textContent = text;
  overlay.classList.add("show");
}
function hideLoading() {
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) overlay.classList.remove("show");
}

// ---------- Confirm dialog (Promise) ----------
function bindModalKeys(overlay, onClose) {
  const focusables = () => Array.from(overlay.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'))
    .filter(el => !el.disabled && el.offsetParent !== null);
  function onKey(e) {
    if (!overlay.isConnected) { document.removeEventListener("keydown", onKey); return; }
    if (e.key === "Escape") { e.preventDefault(); onClose(); return; }
    if (e.key !== "Tab") return;
    const els = focusables();
    if (!els.length) return;
    const i = els.indexOf(document.activeElement);
    if (e.shiftKey && (i <= 0)) { e.preventDefault(); els[els.length - 1].focus(); }
    else if (!e.shiftKey && (i === -1 || i === els.length - 1)) { e.preventDefault(); els[0].focus(); }
  }
  document.addEventListener("keydown", onKey);
  overlay._unbindKeys = () => document.removeEventListener("keydown", onKey);
  setTimeout(() => { const f = focusables()[0]; if (f) f.focus(); }, 20);
}
function dismissOverlay(overlay) {
  if (overlay && overlay._unbindKeys) overlay._unbindKeys();
  if (overlay) overlay.remove();
}

function confirmDialog(message, { title = "Confirm Action", confirmText = "Delete", danger = true } = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-modal", "true");
    overlay.innerHTML = `
      <div class="modal sm">
        <div class="modal-header"><h3>${escapeHtml(title)}</h3></div>
        <div class="modal-body"><p>${escapeHtml(message)}</p></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-cancel>Cancel</button>
          <button class="btn ${danger ? "btn-danger" : "btn-primary"}" data-ok>${escapeHtml(confirmText)}</button>
        </div>
      </div>`;
    const finish = (val) => { dismissOverlay(overlay); resolve(val); };
    document.body.appendChild(overlay);
    overlay.querySelector("[data-cancel]").onclick = () => finish(false);
    overlay.querySelector("[data-ok]").onclick = () => finish(true);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) finish(false); });
    bindModalKeys(overlay, () => finish(false));
  });
}

// ---------- Generic modal helper ----------
function openModal(html, opts) {
  opts = opts || {};
  if (html && typeof html === "object") {
    if (!opts.size && html.size) opts.size = html.size;
    if (!opts.onMount && html.onMount) opts.onMount = html.onMount;
  }
  const size = opts.size || "";
  const onMount = opts.onMount || null;
  const overlay = document.createElement("div");
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal ${size}">
      <div class="modal-header">
        <h3></h3>
        <button class="btn-icon" data-close title="Close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
      </div>
      <div class="modal-body">${html.body || ""}</div>
      ${html.footer ? '<div class="modal-footer">' + html.footer + "</div>" : ""}
    </div>`;
  overlay.querySelector(".modal-header h3").textContent = html.title || "";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  document.body.appendChild(overlay);
  const close = () => dismissOverlay(overlay);
  overlay.querySelectorAll("[data-close]").forEach(btn => { btn.onclick = close; });
  overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
  bindModalKeys(overlay, close);
  if (onMount) {
    try { onMount(overlay); }
    catch (e) {
      console.error(e);
      showToast("This button could not finish opening. Refresh the page and try again.", "error");
    }
  }
  fillRegisteredPatientSelects(overlay);
  return overlay;
}

function closeModal(overlay) { if (overlay) overlay.remove(); }

function apptTimeValue(value) {
  const match = String(value || "").trim().match(/^(\d{1,2}):(\d{2})/);
  return match ? match[1].padStart(2, "0") + ":" + match[2] : "";
}

function optionList(values, current) {
  const list = values.slice();
  if (current && list.indexOf(current) < 0) list.unshift(current);
  return list.map(value => `<option${value === current ? " selected" : ""}>${esc(value)}</option>`).join("");
}

// Edit an appointment, or move it onto another appointment's date, time, and doctor.
function openAppointmentEditor(opts) {
  opts = opts || {};
  const row = opts.row;
  if (!row) return;
  const mode = opts.mode === "edit" ? "edit" : "reschedule";
  const others = (opts.others || []).filter(item => item && String(item.id) !== String(row.id) && item.status !== "cancelled");
  const doctors = opts.doctors && opts.doctors.length ? opts.doctors : [row.doctor || "Doctor"];
  const departments = opts.departments || ["Internal Medicine", "Pediatrics", "Cardiology", "Maternity", "Orthopedics"];
  const types = opts.types || ["Consultation", "Follow-up", "New patient"];
  const details = row.details && typeof row.details === "object" ? row.details : {};
  const otherOptions = ['<option value="">Keep a custom date and time</option>'].concat(others.map(item => {
    const label = [item.date, item.time, item.doctor, item.dept, item.patient].filter(Boolean).join(" · ");
    return `<option value="${esc(item.id)}">${esc(label)}</option>`;
  })).join("");
  openModal({
    title: mode === "edit" ? "Edit appointment" : "Reschedule to other appointment",
    body: `<div class="alert alert-info mb-3"><div class="alert-body">Current: <strong>${esc(row.patient || "")}</strong> · ${esc(row.date || "")} ${esc(row.time || "")} · ${esc(row.doctor || "")}</div></div>
      ${mode === "reschedule" ? `<div class="form-group"><label>Reschedule to other appointment</label><select class="form-control" id="apptMove">${otherOptions}</select><div class="text-sm" id="apptMoveNote" style="margin-top:6px;color:#6B7280">Choose another appointment to take its date, time, and doctor, or set a new slot below.</div></div>` : ""}
      ${mode === "edit" && opts.canEditPatient !== false ? `<div class="form-group"><label>Patient <span class="req">*</span></label><input class="form-control" id="apptPatient" value="${esc(row.patient || "")}"></div>` : ""}
      <div class="form-group"><label>Doctor</label><select class="form-control" id="apptDoctor">${optionList(doctors, row.doctor || doctors[0])}</select></div>
      <div class="form-row">
        <div class="form-group"><label>Date</label><input class="form-control" type="date" id="apptDate" value="${esc(row.date || "")}"></div>
        <div class="form-group"><label>Time</label><input class="form-control" type="time" id="apptTime" value="${esc(apptTimeValue(row.time))}"></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>Type</label><select class="form-control" id="apptType">${optionList(types, row.type || types[0])}</select></div>
        <div class="form-group"><label>Department</label><select class="form-control" id="apptDept">${optionList(departments, row.dept || departments[0])}</select></div>
      </div>
      <div class="form-group"><label>Notes</label><textarea class="form-control" rows="2" id="apptNotes">${esc(details.notes || "")}</textarea></div>`,
    footer: `<button class="btn btn-secondary" data-c>Cancel</button><button class="btn btn-primary" id="apptSave">${mode === "edit" ? "Save changes" : "Reschedule"}</button>`
  }, { onMount: ov => {
    ov.querySelector("[data-c]").onclick = () => ov.remove();
    const move = ov.querySelector("#apptMove");
    if (move) move.addEventListener("change", () => {
      const picked = others.find(item => String(item.id) === move.value);
      const note = ov.querySelector("#apptMoveNote");
      if (!picked) {
        if (note) note.textContent = "Choose another appointment to take its date, time, and doctor, or set a new slot below.";
        return;
      }
      ov.querySelector("#apptDate").value = picked.date || "";
      ov.querySelector("#apptTime").value = apptTimeValue(picked.time);
      ["apptDoctor", "apptDept"].forEach((id, index) => {
        const value = index === 0 ? picked.doctor : picked.dept;
        const select = ov.querySelector("#" + id);
        if (value && !Array.from(select.options).some(option => option.textContent === value)) {
          select.insertAdjacentHTML("afterbegin", `<option>${esc(value)}</option>`);
        }
        if (value) select.value = value;
      });
      if (note) note.textContent = "This appointment will move to " + (picked.patient || "that slot") + "'s date and time. The other booking is left as it is.";
    });
    ov.querySelector("#apptSave").onclick = () => {
      const date = ov.querySelector("#apptDate").value;
      const time = ov.querySelector("#apptTime").value;
      if (!date || !time) { showToast("Choose a date and time", "error"); return; }
      const patientInput = ov.querySelector("#apptPatient");
      const patient = patientInput ? patientInput.value.trim() : row.patient;
      if (mode === "edit" && !patient) { showToast("Patient is required", "error"); return; }
      const doctor = ov.querySelector("#apptDoctor").value;
      const slotChanged = date !== (row.date || "") || time !== apptTimeValue(row.time) || doctor !== (row.doctor || "");
      const nextDetails = Object.assign({}, details, { notes: ov.querySelector("#apptNotes").value.trim() });
      if (mode === "reschedule" || slotChanged) {
        nextDetails.rescheduled_from = { date: row.date || "", time: row.time || "", doctor: row.doctor || "" };
        if (move && move.value) nextDetails.moved_to_appointment = move.value;
      }
      const updated = Object.assign({}, row, {
        patient: patient || row.patient,
        doctor: doctor,
        dept: ov.querySelector("#apptDept").value,
        date: date,
        time: time,
        type: ov.querySelector("#apptType").value,
        status: (mode === "reschedule" || slotChanged) ? "rescheduled" : (row.status || "confirmed"),
        details: nextDetails
      });
      if (typeof opts.onSave === "function") opts.onSave(updated);
      ov.remove();
    };
  }});
}

// ---------- Escaping ----------
function escapeHtml(str) {
  return String(str == null ? "" : str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
const esc = escapeHtml;

// ---------- Misc small helpers used by page scripts ----------
function initialsOf(name) {
  return String(name || "").split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

function badge(text, kind = "neutral") {
  return '<span class="badge badge-' + kind + '"><span class="dot"></span>' + esc(text) + "</span>";
}

function emptyRow(colspan, msg) {
  return '<tr class="empty-row"><td colspan="' + colspan + '" style="text-align:center;color:#64748B;padding:32px">' +
         (msg || "No records found.") + "</td></tr>";
}

// ---------- Debounce ----------
function debounce(fn, ms = 300) {
  let t;
  return function (...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), ms);
  };
}

// ---------- Confidence color ----------
function confidenceColor(pct) {
  const p = Number(pct) || 0;
  if (p >= 70) return "high";
  if (p >= 40) return "mid";
  return "low";
}

// ---------- CSV export ----------
function exportCSV(filename, headers, rows) {
  const esc = (v) => {
    const s = String(v == null ? "" : v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const lines = [headers.map(esc).join(","), ...rows.map(r => r.map(esc).join(","))];
  const blob = new Blob(["\uFEFF" + lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 500);
}

// ============================================================
// SVG CHART ENGINE (no external libraries)
// ============================================================
const CHART_COLORS = ["#1A6FA8", "#18BF75", "#B45309", "#7C3AED", "#DC2626", "#0891B2", "#65A30D", "#DB2777"];

function chartSvg(width, height, inner) {
  return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" role="img" preserveAspectRatio="xMidYMid meet">${inner}</svg>`;
}

// Bar chart: data = [{label, value}]
function barChart(data, { height = 240, color = "#1A6FA8", valueFmt = (v) => v } = {}) {
  const padL = 44, padB = 34, padT = 14, padR = 10;
  const max = Math.max(...data.map(d => d.value), 1);
  const innerW = 620, innerH = height;
  const plotW = innerW - padL - padR, plotH = innerH - padT - padB;
  const step = plotW / data.length;
  const barW = Math.min(46, step * 0.58);
  let bars = "", labels = "", grid = "";
  for (let i = 0; i <= 4; i++) {
    const y = padT + (plotH / 4) * i;
    grid += `<line x1="${padL}" y1="${y}" x2="${innerW - padR}" y2="${y}" stroke="#E2E8F0" stroke-width="1"/>`;
    grid += `<text x="${padL - 8}" y="${y + 4}" font-size="11" fill="#64748B" text-anchor="end">${valueFmt(Math.round(max - (max / 4) * i))}</text>`;
  }
  data.forEach((d, i) => {
    const h = Math.max(2, (d.value / max) * plotH);
    const x = padL + step * i + (step - barW) / 2;
    const y = padT + plotH - h;
    bars += `<rect x="${x}" y="${y}" width="${barW}" height="${h}" rx="5" fill="${Array.isArray(color) ? color[i % color.length] : color}" opacity="0.92"/>`;
    bars += `<text x="${x + barW / 2}" y="${y - 5}" font-size="10" fill="#374151" text-anchor="middle" font-weight="600">${valueFmt(d.value)}</text>`;
    labels += `<text x="${x + barW / 2}" y="${innerH - 10}" font-size="10" fill="#64748B" text-anchor="middle">${d.label}</text>`;
  });
  return chartSvg(innerW, innerH, grid + bars + labels);
}

// Line/area chart: data = [{label, value}]  (opts.area → fill)
function lineChart(data, { height = 240, color = "#1A6FA8", area = true, valueFmt = (v) => v, showPoints = true } = {}) {
  const padL = 44, padB = 34, padT = 14, padR = 14;
  const values = data.map(d => d.value);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(max - min, 1);
  const innerW = 620, innerH = height;
  const plotW = innerW - padL - padR, plotH = innerH - padT - padB;
  const X = (i) => padL + (plotW * i) / Math.max(data.length - 1, 1);
  const Y = (v) => padT + plotH - ((v - min) / range) * plotH;
  let grid = "";
  for (let i = 0; i <= 4; i++) {
    const y = padT + (plotH / 4) * i;
    grid += `<line x1="${padL}" y1="${y}" x2="${innerW - padR}" y2="${y}" stroke="#E2E8F0" stroke-width="1"/>`;
    const val = min + (range / 4) * (4 - i);
    grid += `<text x="${padL - 8}" y="${y + 4}" font-size="11" fill="#64748B" text-anchor="end">${valueFmt(Math.round(val))}</text>`;
  }
  const pts = data.map((d, i) => X(i) + "," + Y(d.value)).join(" ");
  const poly = `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;
  const fill = area ? `<polygon points="${padL},${padT + plotH} ${pts} ${X(data.length - 1)},${padT + plotH}" fill="${color}" opacity="0.10"/>` : "";
  const dots = showPoints ? data.map((d, i) => `<circle cx="${X(i)}" cy="${Y(d.value)}" r="3.4" fill="#fff" stroke="${color}" stroke-width="2"/>`).join("") : "";
  const labels = data.map((d, i) => {
    if (data.length > 12 && i % Math.ceil(data.length / 8) !== 0) return "";
    return `<text x="${X(i)}" y="${innerH - 10}" font-size="10" fill="#64748B" text-anchor="middle">${d.label}</text>`;
  }).join("");
  return chartSvg(innerW, innerH, grid + fill + poly + dots + labels);
}

// Donut chart: data = [{label, value}]
function donutChart(data, { size = 200 } = {}) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const rOuter = 80, rInner = 52, cx = size / 2, cy = size / 2;
  let angle = -90;
  const arcs = data.map((d, i) => {
    const frac = d.value / total;
    const a0 = angle, a1 = angle + frac * 360;
    angle = a1;
    const large = (a1 - a0) > 180 ? 1 : 0;
    const p0 = polar(cx, cy, rOuter, a0), p1 = polar(cx, cy, rOuter, a1);
    const p2 = polar(cx, cy, rInner, a1), p3 = polar(cx, cy, rInner, a0);
    return `<path d="M ${p0.x} ${p0.y} A ${rOuter} ${rOuter} 0 ${large} 1 ${p1.x} ${p1.y} L ${p2.x} ${p2.y} A ${rInner} ${rInner} 0 ${large} 0 ${p3.x} ${p3.y} Z" fill="${CHART_COLORS[i % CHART_COLORS.length]}"/>`;
  }).join("");
  const centerPct = Math.round((data[0] ? data[0].value : 0) / total * 100);
  return chartSvg(size, size, arcs +
    `<text x="${cx}" y="${cy - 4}" font-size="24" font-weight="700" fill="#1E293B" text-anchor="middle">${centerPct}%</text>` +
    `<text x="${cx}" y="${cy + 16}" font-size="10" fill="#64748B" text-anchor="middle">${escapeHtml(data[0] ? data[0].label : "")}</text>`);
}
function polar(cx, cy, r, deg) {
  const rad = (deg - 90) * Math.PI / 180;
  return { x: +(cx + r * Math.cos(rad)).toFixed(2), y: +(cy + r * Math.sin(rad)).toFixed(2) };
}

// Sparkline: values = [numbers]
function sparkline(values, { width = 140, height = 40, color = "#1A6FA8" } = {}) {
  const max = Math.max(...values, 1), min = Math.min(...values, 0);
  const range = Math.max(max - min, 1);
  const X = (i) => (width * i) / Math.max(values.length - 1, 1);
  const Y = (v) => height - 6 - ((v - min) / range) * (height - 12);
  const pts = values.map((v, i) => X(i) + "," + Y(v)).join(" ");
  return chartSvg(width, height, `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round"/>`);
}

// Heatmap: rows = [{label, cells:[{v,label}]}], 7 columns
function heatmapChart(rows) {
  const cellW = 84, cellH = 52, colH = 28, padL = 76;
  const w = padL + 7 * cellW + 16, h = colH + rows.length * cellH + 12;
  let s = "";
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  days.forEach((d, i) => {
    s += `<text x="${padL + i * cellW + cellW / 2}" y="${18}" font-size="11" fill="#64748B" text-anchor="middle">${d}</text>`;
  });
  rows.forEach((row, r) => {
    const y = colH + r * cellH;
    s += `<text x="${padL - 10}" y="${y + cellH / 2 + 4}" font-size="11" fill="#374151" text-anchor="end" font-weight="600">${escapeHtml(row.label)}</text>`;
    row.cells.forEach((c, i) => {
      const x = padL + i * cellW;
      const color = c.v >= 75 ? "#DC2626" : c.v >= 50 ? "#B45309" : c.v >= 25 ? "#FACC15" : "#E3F9EF";
      s += `<rect x="${x}" y="${y}" width="${cellW - 8}" height="${cellH - 10}" rx="8" fill="${color}" opacity="0.85"/>`;
      s += `<text x="${x + (cellW - 8) / 2}" y="${y + (cellH - 10) / 2 + 5}" font-size="13" font-weight="700" fill="${c.v >= 25 ? "#1E293B" : "#fff"}" text-anchor="middle">${c.v}</text>`;
    });
  });
  return chartSvg(w, h, s);
}

// ============================================================
// DATA TABLE helper — search / sort / pagination
// ============================================================
// Usage: attachDataTable(tableEl, { searchInput, pageSize, filterFn })
function attachDataTable(table, opts = {}) {
  if (!table) return;
  const rows = Array.from(table.tBodies[0].rows);
  const state = { q: "", sortIdx: -1, sortAsc: true, page: 1, pageSize: opts.pageSize || 8, filtered: rows };

  const thead = table.tHead.querySelectorAll("th.sortable");
  thead.forEach((th, idx) => {
    th.addEventListener("click", () => {
      if (state.sortIdx === idx) state.sortAsc = !state.sortAsc;
      else { state.sortIdx = idx; state.sortAsc = true; }
      render();
    });
  });

  function applyFilter() {
    state.filtered = rows.filter(r => {
      if (opts.filterFn && !opts.filterFn(r)) return false;
      if (!state.q) return true;
      return Array.from(r.cells).some(c => c.textContent.toLowerCase().includes(state.q));
    });
    state.page = 1;
  }

  function render() {
    applyFilter();
    let list = [...state.filtered];
    if (state.sortIdx >= 0) {
      list.sort((a, b) => {
        const av = a.cells[state.sortIdx] ? a.cells[state.sortIdx].textContent.trim() : "";
        const bv = b.cells[state.sortIdx] ? b.cells[state.sortIdx].textContent.trim() : "";
        const an = parseFloat(av), bn = parseFloat(bv);
        const cmp = (!isNaN(an) && !isNaN(bn)) ? an - bn : av.localeCompare(bv);
        return state.sortAsc ? cmp : -cmp;
      });
    }
    const total = list.length;
    const pages = Math.max(1, Math.ceil(total / state.pageSize));
    if (state.page > pages) state.page = pages;
    const start = (state.page - 1) * state.pageSize;
    const slice = list.slice(start, start + state.pageSize);

    rows.forEach(r => r.classList.add("hidden"));
    slice.forEach(r => r.classList.remove("hidden"));

    const pager = opts.pagerEl;
    if (pager) {
      pager.innerHTML = `
        <button class="page-btn" data-pg="prev" ${state.page === 1 ? "disabled" : ""}>‹ Prev</button>
        ${pageButtons(state.page, pages)}
        <button class="page-btn" data-pg="next" ${state.page === pages ? "disabled" : ""}>Next ›</button>
        <span class="page-info">Showing ${total ? start + 1 : 0}–${Math.min(start + state.pageSize, total)} of ${total}</span>`;
      pager.querySelectorAll("[data-pg]").forEach(b => {
        b.onclick = () => {
          if (b.dataset.pg === "prev") state.page = Math.max(1, state.page - 1);
          else if (b.dataset.pg === "next") state.page = Math.min(pages, state.page + 1);
          else state.page = +b.dataset.pg;
          render();
        };
      });
    }
    if (opts.onRender) opts.onRender(state.filtered.length);
  }

  function pageButtons(cur, pages) {
    let s = "";
    const range = [];
    const start = Math.max(1, cur - 2), end = Math.min(pages, cur + 2);
    for (let i = start; i <= end; i++) range.push(i);
    if (start > 1) range.unshift(1);
    if (end < pages) range.push(pages);
    let prev = 0;
    range.forEach(p => {
      if (p - prev > 1) s += '<span class="page-info" style="margin:0">…</span>';
      s += `<button class="page-btn ${p === cur ? "active" : ""}" data-pg="${p}">${p}</button>`;
      prev = p;
    });
    return s;
  }

  if (opts.searchInput) {
    opts.searchInput.addEventListener("input", debounce((e) => { state.q = e.target.value.toLowerCase(); render(); }, 250));
  }
  render();
}

// ============================================================
// Sidebar / layout behaviour (used by every role page)
// ============================================================
// Uses event delegation on document so the hamburger, sidebar-collapse
// toggle, mobile-overlay close, and data-close-menu links all continue to
// work after the SPA shell rebuilds the sidebar/topbar on login. Safe to
// call multiple times — the global listeners attach only once per page load.
// Mobile menu open/close — keep body class + hamburger a11y state in sync
function openMobileMenu() {
  document.body.classList.add("mobile-menu-open");
  const h = document.getElementById("hamburger");
  if (h) { h.setAttribute("aria-label", "Close menu"); h.setAttribute("aria-expanded", "true"); }
}
function closeMobileMenu() {
  document.body.classList.remove("mobile-menu-open");
  const h = document.getElementById("hamburger");
  if (h) { h.setAttribute("aria-label", "Open menu"); h.setAttribute("aria-expanded", "false"); }
}

let _layoutDelegationDone = false;
function _bindLayoutDelegation() {
  if (_layoutDelegationDone) return;
  _layoutDelegationDone = true;

  // Hamburger → open mobile menu
  document.addEventListener("click", (e) => {
    const ham = e.target.closest("#hamburger");
    if (ham) {
      e.stopPropagation();
      openMobileMenu();
      return;
    }
    // Collapse toggle (desktop sidebar)
    const collapser = e.target.closest("#sidebarToggle");
    if (collapser) {
      e.stopPropagation();
      document.body.classList.toggle("sidebar-collapsed");
      return;
    }
    // Click on overlay → close mobile menu
    if (e.target && e.target.id === "mobileOverlay") {
      closeMobileMenu();
      return;
    }
    // Any link marked [data-close-menu] (e.g. sidebar nav items) → close mobile menu
    const closer = e.target.closest("[data-close-menu]");
    if (closer) {
      closeMobileMenu();
    }
  });

  // Swipe-left on sidebar to close it (mobile nicety)
  try {
    let touchStartX = 0;
    document.addEventListener("touchstart", (e) => {
      touchStartX = e.changedTouches[0].clientX;
    }, { passive: true });
    document.addEventListener("touchend", (e) => {
      const dx = e.changedTouches[0].clientX - touchStartX;
      if (touchStartX > 40 && dx < -60) {
        closeMobileMenu();
      }
    }, { passive: true });
  } catch (e) { /* ignore on browsers without touch */ }

  // Esc closes dropdowns + mobile menu
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".dropdown-menu.show").forEach(m => m.classList.remove("show"));
      closeMobileMenu();
    }
  });
}

function initLayout() {
  // Wire user name / initials / permission-hidden tabs for whatever DOM is
  // present right now (whether SPA shell or standalone page).
  initAuthUI();
  applyPermissions();
  // Attach global delegated listeners once — they keep working across SPA
  // page swaps and across login/logout shell rebuilds.
  _bindLayoutDelegation();
  // The shell rebuilds the bell, so refresh whenever the layout is ready.
  if (typeof refreshNotifications === "function") refreshNotifications();
  initPatientSuggest();
  fillRegisteredPatientSelects(document);
}

// ---------- Permission-based tabs ----------
// Nav links tagged data-perm are hidden unless the current role has that
// permission (granted/revoked by the admin from Roles & Permissions).
function applyPermissions() {
  const role = getUserRole();
  if (!role) return;
  seedPermissions();
  document.querySelectorAll(".nav-link[data-perm], .taskbar-link[data-perm]").forEach(a => {
    a.classList.toggle("hidden", !canAccess(role, a.dataset.perm));
  });
  document.querySelectorAll(".nav-section-label").forEach(function (label) {
    let sib = label.nextElementSibling;
    let any = false;
    while (sib && !sib.classList.contains("nav-section-label")) {
      if (sib.classList.contains("nav-link") && !sib.classList.contains("hidden")) any = true;
      sib = sib.nextElementSibling;
    }
    label.classList.toggle("hidden", !any);
  });
}

function enforceCurrentPage() {
  if (window.SPA && window.SPA.mode) return;
  if (typeof pageAllowed !== "function" || pageAllowed(location.pathname)) return;
  const body = document.querySelector(".page-body");
  if (body) body.innerHTML = permissionDeniedHtml();
}

// ---------- Live notifications (topbar bell) ----------
// Real rows only: unread messages, upcoming appointments, unpaid bills,
// abnormal results, and low stock. Fake sample alerts are not shown.
var _notifTimer = null;
var _notifGen = 0;
var _notifItems = [];

function notifPrefOn(key) {
  if (typeof _userPrefs === "undefined" || !_userPrefs) return true;
  var value = _userPrefs["notify_" + key];
  if (value == null) return true;
  return value === 1 || value === true || value === "1";
}
function notifSeen() {
  var saved = (typeof _userPrefs !== "undefined" && _userPrefs && _userPrefs.notify_seen) || [];
  var local = window.__notifSeen || [];
  var out = [];
  (Array.isArray(saved) ? saved : []).concat(local).forEach(function (id) {
    if (id && out.indexOf(id) < 0) out.push(String(id));
  });
  return out;
}
function notifIcon(name) {
  var icons = window.ICONS || (typeof ICONS !== "undefined" ? ICONS : {});
  return icons[name] || "";
}
function notifHref(key) {
  var role = typeof getUserRole === "function" ? getUserRole() : "";
  var pages = {
    patient: { appointments: "appointments.html", messages: "messages.html", bills: "bills.html", settings: "settings.html" },
    doctor: { appointments: "appointments.html", messages: "messages.html", settings: "settings.html" },
    nurse: { messages: "messages.html", medications: "medications.html", settings: "settings.html" },
    pharmacist: { inventory: "inventory.html", messages: "messages.html", settings: "settings.html" },
    laboratory: { results: "results.html", messages: "messages.html", settings: "settings.html" },
    reception: { appointments: "appointments.html", queue: "queue.html", messages: "messages.html", settings: "settings.html" },
    manager: { messages: "messages.html", settings: "settings.html" },
    admin: { messages: "messages.html", settings: "settings.html" }
  };
  var file = (pages[role] || {})[key];
  if (!file) return "";
  if (typeof inRoleFolder === "function" && inRoleFolder()) return file;
  return role ? role + "/" + file : file;
}
function quietFetch(endpoint) {
  if (!endpoint) return Promise.resolve({ ok: false, skipped: true });
  if (typeof endpointAllowed === "function" && !endpointAllowed(endpoint)) {
    return Promise.resolve({ ok: false, skipped: true });
  }
  return apiFetch(endpoint, "GET", null, { quiet: true });
}
function notifDate(value) {
  return String(value || "").slice(0, 10);
}
function notifUnread(row) {
  var read = row && row.read;
  return read !== true && read !== 1 && read !== "1" && read !== "true";
}
function nameHits(value, me) {
  var a = String(value || "").trim().toLowerCase();
  var b = String(me || "").trim().toLowerCase();
  if (!a || !b) return false;
  return a === b || a.indexOf(b) >= 0 || b.indexOf(a) >= 0;
}
function setNotifDot(count) {
  document.querySelectorAll(".notif-dot").forEach(function (dot) {
    if (count > 0) {
      dot.hidden = false;
      dot.setAttribute("aria-label", count + " unread");
    } else {
      dot.hidden = true;
      dot.removeAttribute("aria-label");
    }
  });
}
function markNotifRead(id) {
  if (!id) return;
  window.__notifSeen = window.__notifSeen || [];
  if (window.__notifSeen.indexOf(id) < 0) window.__notifSeen.push(id);
  if (typeof _userPrefs !== "undefined" && _userPrefs) {
    var seen = notifSeen().slice(-80);
    _userPrefs.notify_seen = seen;
    if (typeof _userDetails !== "undefined" && _userDetails) _userDetails.prefs = _userPrefs;
    if (typeof apiFetch === "function" && CONFIG.ENDPOINTS.PROFILE) {
      apiFetch(CONFIG.ENDPOINTS.PROFILE, "POST", { details_patch: { prefs: { notify_seen: seen } } }, { quiet: true });
    }
  }
  _notifItems.forEach(function (item) { if (item.id === id) item.read = true; });
  var menu = document.getElementById("notifMenu");
  if (menu) renderNotifItems(menu, _notifItems);
}
function refreshNotifications() {
  clearTimeout(_notifTimer);
  _notifTimer = setTimeout(loadNotifications, 40);
}
window.refreshNotifications = refreshNotifications;
function initNotifications() { refreshNotifications(); }

function loadNotifications() {
  var menu = document.getElementById("notifMenu");
  if (!menu || typeof apiFetch !== "function" || !CONFIG || !CONFIG.ENDPOINTS) return;
  if (!getSession || !getSession()) {
    renderNotifItems(menu, [], "Sign in to see notifications.");
    return;
  }
  if (!notifPrefOn("inapp")) {
    _notifItems = [];
    renderNotifItems(menu, [], "In-app notifications are turned off in Settings.", notifHref("settings"));
    return;
  }
  var gen = ++_notifGen;
  var role = typeof getUserRole === "function" ? getUserRole() : "";
  var me = typeof getUserName === "function" ? getUserName() : "";
  var today = typeof todayStr === "function" ? todayStr() : "";
  Promise.all([
    quietFetch(CONFIG.ENDPOINTS.MESSAGES),
    quietFetch(CONFIG.ENDPOINTS.APPOINTMENTS),
    quietFetch(CONFIG.ENDPOINTS.LAB_RESULTS),
    quietFetch(CONFIG.ENDPOINTS.INVENTORY),
    quietFetch(CONFIG.ENDPOINTS.BILLS)
  ]).then(function (rows) {
    if (gen !== _notifGen) return;
    var live = document.getElementById("notifMenu");
    if (!live) return;
    var items = [];
    var seen = notifSeen();
    function add(item) {
      if (!item || !item.id || items.some(function (x) { return x.id === item.id; })) return;
      item.read = seen.indexOf(item.id) >= 0;
      items.push(item);
    }
    var messages = rows[0];
    if (messages.ok && messages.data && Array.isArray(messages.data.items)) {
      messages.data.items.filter(notifUnread).slice(0, 5).forEach(function (m) {
        add({
          id: "msg:" + (m.id || m.subject || m.date),
          icon: "mail", tint: "#D5DCDF", color: "#253745",
          category: "Message", time: typeof formatDateTime === "function" ? formatDateTime(m.date) : (m.date || ""),
          title: m.subject || "New message",
          sub: "From " + (m.from || "the hospital"),
          detail: m.body || m.subject || "You have an unread message.",
          link: notifHref("messages")
        });
      });
    }
    var appts = rows[1];
    if (appts.ok && appts.data && Array.isArray(appts.data.items)) {
      appts.data.items.filter(function (a) {
        var when = notifDate(a.date);
        var status = String(a.status || "").toLowerCase();
        if (!when || when < today) return false;
        if (status && status !== "confirmed" && status !== "scheduled" && status !== "booked") return false;
        if (role === "doctor") return nameHits(a.doctor, me);
        return true;
      }).slice(0, 4).forEach(function (a) {
        add({
          id: "appt:" + (a.id || a.date + a.time + a.patient),
          icon: "calendar", tint: "#D5DCDF", color: "#253745",
          category: "Appointment", time: (a.date || "") + (a.time ? " " + a.time : ""),
          title: (a.patient || a.doctor || "Appointment") + (a.time ? " at " + a.time : ""),
          sub: (a.dept || a.type || "Appointment") + " · " + (a.status || "scheduled"),
          detail: (a.patient || "A patient") + " has an appointment" + (a.doctor ? " with " + a.doctor : "") + (a.dept ? " in " + a.dept : "") + " on " + (a.date || "the scheduled day") + (a.time ? " at " + a.time : "") + ".",
          link: notifHref("appointments")
        });
      });
    }
    var labs = rows[2];
    if (notifPrefOn("ai") && labs.ok && labs.data && Array.isArray(labs.data.items)) {
      labs.data.items.filter(function (r) {
        return String(r.ai_flag || "").toLowerCase() === "abnormal";
      }).slice(0, 3).forEach(function (r) {
        add({
          id: "lab:" + (r.id || r.test + r.patient + r.date),
          icon: "alert", tint: "#E8DCDC", color: "#9B2C2C",
          category: "Laboratory", time: typeof formatDateTime === "function" ? formatDateTime(r.date) : (r.date || ""),
          title: "Abnormal result: " + (r.test || "lab test"),
          sub: (r.patient || "Patient") + " · AI flagged",
          detail: "The AI analyzer flagged the " + (r.test || "lab") + " result for " + (r.patient || "the patient") + " as abnormal. Review the values before releasing them.",
          link: notifHref("results")
        });
      });
    }
    var stock = rows[3];
    if (stock.ok && stock.data && Array.isArray(stock.data.items)) {
      stock.data.items.filter(function (i) {
        var status = String(i.status || "").toLowerCase();
        return status === "low-stock" || status === "out-of-stock" || status === "low";
      }).slice(0, 3).forEach(function (i) {
        add({
          id: "stock:" + (i.id || i.name),
          icon: "package", tint: "#E7E2D6", color: "#8A5A12",
          category: "Inventory", time: "Now",
          title: (i.name || "Item") + " is " + String(i.status || "low").replace(/-/g, " "),
          sub: (i.stock != null ? i.stock : "0") + " " + (i.unit || "units") + " remaining",
          detail: (i.name || "An item") + " has " + (i.stock != null ? i.stock : "0") + " " + (i.unit || "units") + " left. Reorder before the ward runs out.",
          link: notifHref("inventory")
        });
      });
    }
    var bills = rows[4];
    if (role === "patient" && bills.ok && bills.data && Array.isArray(bills.data.items)) {
      bills.data.items.filter(function (b) {
        var status = String(b.status || "").toLowerCase();
        if (status === "paid" || status === "cancelled" || status === "void") return false;
        if (status === "unpaid" || status === "pending" || status === "due" || status === "outstanding" || status === "partial") return true;
        return (Number(b.amount) || 0) > (Number(b.paid) || 0);
      }).slice(0, 3).forEach(function (b) {
        add({
          id: "bill:" + (b.id || b.date + b.description),
          icon: "alert", tint: "#E8DCDC", color: "#9B2C2C",
          category: "Bill", time: b.date || "",
          title: b.description || b.service || "Unpaid bill",
          sub: (typeof formatCurrency === "function" ? formatCurrency(b.amount) : (b.amount || "")) + " · " + (b.status || "unpaid"),
          detail: "This bill is still open. Open Bills to review the amount and payment status.",
          link: notifHref("bills")
        });
      });
    }
    _notifItems = items;
    renderNotifItems(live, items);
  });
}
function renderNotifItems(menu, items, emptyText, emptyLink) {
  var unread = (items || []).filter(function (i) { return !i.read; }).length;
  setNotifDot(unread);
  var shown = (items || []).slice(0, 6);
  var body = shown.length
    ? '<div class="notif-list">' + shown.map(function (i, idx) {
        return '<div class="dd-item' + (i.read ? " is-read" : "") + '" data-notif="' + idx + '"><div class="feed-icon" style="background:' + i.tint + ";color:" + i.color + '">' + notifIcon(i.icon) + '</div><div class="feed-text"><div class="dd-title">' + esc(i.title) + '</div><div class="dd-sub">' + esc(i.sub) + "</div></div></div>";
      }).join("") + "</div>"
    : '<div class="empty-state" style="padding:22px">' + esc(emptyText || "You're all caught up") + (emptyLink ? ' <a href="' + esc(emptyLink) + '">Open Settings</a>' : "") + "</div>";
  menu.innerHTML = '<div class="dd-header"><span>Notifications</span>' + (unread ? "<span> (" + unread + ")</span>" : "") + "</div>" + body +
    ((items && items.length) ? '<div class="dd-footer"><a href="#" id="notifViewAll">View all</a></div>' : "");
  menu.querySelectorAll("[data-notif]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.stopPropagation();
      var item = shown[+el.getAttribute("data-notif")];
      if (!item) return;
      markNotifRead(item.id);
      openNotificationDetail(item);
    });
  });
  var all = menu.querySelector("#notifViewAll");
  if (all) all.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    openAllNotifications(items);
  });
}
function openAllNotifications(items) {
  var list = items || [];
  var body = list.length
    ? list.map(function (n, idx) {
        return '<button type="button" class="dd-item" data-all="' + idx + '" style="width:100%;background:transparent;border:0;border-bottom:1px solid var(--border);text-align:left"><div class="feed-icon" style="background:' + n.tint + ";color:" + n.color + '">' + notifIcon(n.icon) + '</div><div class="feed-text"><div class="dd-title">' + esc(n.title) + '</div><div class="dd-sub">' + esc(n.sub) + "</div></div></button>";
      }).join("")
    : "<p>You're all caught up</p>";
  openModal({
    title: "All notifications",
    body: body,
    size: "lg",
    onMount: function (ov) {
      ov.querySelectorAll("[data-all]").forEach(function (el) {
        el.onclick = function () {
          var item = list[+el.getAttribute("data-all")];
          if (!item) return;
          markNotifRead(item.id);
          openNotificationDetail(item);
        };
      });
    }
  });
}

// ---------- Notification detail popup ----------
function openNotificationDetail(n) {
  if (!n) return;
  openModal({
    title: n.title,
    body: `<div class="detail-list">
      <div class="detail-item"><span class="k">Category</span><span class="v">${esc(n.category || "System")}</span></div>
      <div class="detail-item"><span class="k">Time</span><span class="v">${esc(n.time || "Just now")}</span></div>
      <div class="detail-item"><span class="k">Status</span><span class="v"><span class="badge ${n.read ? "badge-neutral" : "badge-warning"}">${n.read ? "Read" : "Unread"}</span></span></div>
    </div>
    <div class="alert alert-info mt-4 mb-0"><span>${notifIcon(n.icon)}</span>
      <div class="alert-body"><strong>${esc(n.title)}</strong><div class="mt-2" style="font-size:13px">${esc(n.detail || n.sub || "")}</div></div>
    </div>
    ${n.link ? `<div class="form-actions mt-4"><a class="btn btn-primary" href="${esc(n.link)}">${notifIcon("eye")} Open related page</a></div>` : ""}`,
    size: "lg"
  });
}

function aiExplanationHtml(res) {
  var text = res && res.explanation;
  if (!text) return "";
  var icon = (typeof ICONS !== "undefined" && ICONS.info) ? ICONS.info : "";
  return '<div class="alert alert-info mt-3"><span>' + icon + '</span><div class="alert-body"><strong>Explanation</strong><div class="mt-1" style="font-size:14px;line-height:1.55;white-space:pre-wrap">' + esc(text) + '</div></div></div>';
}

function compactReportRows(rows) {
  return (rows || []).slice(0, 40).map(function (row) {
    var item = row.drug || row.test || row.department || row.category || row.subject || row.type || "record";
    return {
      item: String(item || "record").slice(0, 80),
      detail: String(row.detail || row.subject || row.category || row.type || "").slice(0, 80),
      status: String(row.status || "").slice(0, 30),
      date: String(row.date || "").slice(0, 20)
    };
  });
}

function requestHospitalNarrative(title, period, rows) {
  if (typeof apiFetch !== "function" || !CONFIG.ENDPOINTS.REPORT_GENERATE) {
    return Promise.resolve({ narrative: "", error: "Report writing is not available" });
  }
  return apiFetch(CONFIG.ENDPOINTS.REPORT_GENERATE, "POST", {
    title: title,
    period: period,
    rows: compactReportRows(rows)
  }).then(function (res) {
    if (!res.ok) return { narrative: "", saved: false, error: res.error || "Could not write the report" };
    return res.data || {};
  });
}

function reportNarrativeBlock(text) {
  if (!text) return "";
  return '<div class="alert alert-info mb-4"><div class="alert-body"><strong>Written report</strong><div class="mt-2" style="font-size:14px;line-height:1.6;white-space:pre-wrap">' + esc(text) + '</div></div></div>';
}

function loadSavedHospitalReports(apply) {
  if (typeof apiFetch !== "function") return;
  apiFetch(CONFIG.ENDPOINTS.DOCUMENTS).then(function (res) {
    if (!res.ok || !res.data || !res.data.items) return;
    var saved = res.data.items.filter(function (row) {
      return row && row.type === "Hospital Report";
    }).map(function (row) {
      return {
        id: row.id,
        name: row.title || "Report",
        title: row.title || "Report",
        period: row.period || "",
        date: row.date || "",
        generated: row.date || "",
        by: row.uploaded_by || "",
        narrative: row.narrative || row.summary || "",
        format: row.format || "Narrative",
        status: "ready"
      };
    });
    apply(saved);
  });
}

// Auto-close alerts
document.addEventListener("click", (e) => {
  if (e.target.closest(".alert-close")) e.target.closest(".alert").remove();
});

// ---------- Registered patient name suggestions ----------
// Wherever a patient name is typed, show similar people already saved in Supabase.
var _regPatients = null;
var _regPatientJob = null;
var _suggestEl = null;
var _suggestInput = null;
var _suggestHits = [];
var _suggestIndex = -1;

var _regPatientError = "";
var _regPatientAt = 0;
function patientRowsFrom(res) {
  if (!res || !res.ok || !res.data) return [];
  var items = res.data.items || res.data;
  return Array.isArray(items) ? items : [];
}
function fetchSavedNames(path) {
  if (!window.CONFIG || !CONFIG.API_BASE_URL || typeof fetch !== "function") {
    return Promise.resolve({ ok: false, error: "Could not read names from the hospital database" });
  }
  var headers = { "Accept": "application/json" };
  var session = typeof getSession === "function" ? getSession() : null;
  if (session && session.token) headers.Authorization = "Bearer " + session.token;
  return fetch(CONFIG.API_BASE_URL + path, { method: "GET", headers: headers, cache: "no-store" }).then(function (res) {
    return res.json().catch(function () { return {}; }).then(function (data) {
      return { ok: res.ok, status: res.status, data: data, error: (data && (data.detail || data.error)) || "" };
    });
  }).catch(function () {
    return { ok: false, error: "Could not read names from the hospital database" };
  });
}
function mergePatientRows(lists) {
  var byName = {};
  (lists || []).forEach(function (rows) {
    (rows || []).forEach(function (row) {
      if (!row || typeof row !== "object") return;
      var name = patientFullName(row);
      if (!name) return;
      var key = name.toLowerCase();
      var current = byName[key] || {};
      var mail = patientEmail(row) || current.email || "";
      byName[key] = {
        id: row.id || current.id || "",
        name: name,
        first_name: row.first_name || current.first_name || name.split(" ")[0] || "",
        last_name: row.last_name || current.last_name || name.split(" ").slice(1).join(" "),
        phone: row.phone || current.phone || "",
        email: mail
      };
    });
  });
  return Object.keys(byName).map(function (key) { return byName[key]; });
}
function loadRegisteredPatients() {
  if (typeof getUserRole === "function" && getUserRole() === "patient") return Promise.resolve([]);
  if (_regPatients && (Date.now() - _regPatientAt) < 20000) return Promise.resolve(_regPatients);
  if (_regPatientJob) return _regPatientJob;
  var patientsPath = (window.CONFIG && CONFIG.ENDPOINTS && CONFIG.ENDPOINTS.PATIENTS) || "/patients";
  var lookupPath = (window.CONFIG && CONFIG.ENDPOINTS && CONFIG.ENDPOINTS.PATIENT_LOOKUP) || "/patients/lookup";
  _regPatientJob = Promise.all([
    fetchSavedNames(patientsPath + "?limit=500"),
    fetchSavedNames(lookupPath)
  ]).then(function (results) {
    _regPatientJob = null;
    var rows = mergePatientRows(results.map(patientRowsFrom));
    if (rows.length) {
      _regPatientError = "";
      _regPatients = rows;
      _regPatientAt = Date.now();
      return rows;
    }
    var failed = (results || []).filter(function (res) { return !res || !res.ok; });
    if (failed.length) {
      _regPatients = null;
      _regPatientError = (failed[0] && failed[0].error) || "Could not read names from the hospital database";
      return [];
    }
    _regPatientError = "";
    _regPatients = [];
    _regPatientAt = Date.now();
    return [];
  });
  return _regPatientJob;
}
window.loadRegisteredPatients = loadRegisteredPatients;
window.refreshRegisteredPatients = function () {
  _regPatients = null;
  _regPatientJob = null;
  return loadRegisteredPatients();
};

function patientFullName(p) {
  if (!p) return "";
  var full = [p.first_name, p.last_name].filter(Boolean).join(" ").trim();
  return full || p.name || "";
}
function patientFieldBlob(input) {
  var label = "";
  var group = input.closest && input.closest(".form-group");
  if (group) {
    var lab = group.querySelector("label");
    if (lab) label = lab.textContent || "";
  }
  if (input.id) {
    var linked = document.querySelector('label[for="' + input.id + '"]');
    if (linked) label += " " + (linked.textContent || "");
  }
  return ((input.id || "") + " " + (input.name || "") + " " + (input.placeholder || "") + " " + label + " " + (input.getAttribute("list") || "")).toLowerCase();
}
function isPatientNameField(input) {
  if (!input || input.tagName !== "INPUT" || input.disabled || input.readOnly) return false;
  var type = (input.type || "text").toLowerCase();
  if (type !== "text" && type !== "search") return false;
  if (input.dataset.patientSuggest === "off") return false;
  var id = (input.id || "").toLowerCase();
  if (id === "cmdinput" || id === "cto" || id === "stname" || id === "billsearch" || id === "retsearch") return false;
  if (input.closest(".search-box") || input.closest(".topbar-search")) return false;
  var blob = patientFieldBlob(input);
  if (/hospital name|drug name|department name|role name|shift name|supplier|email|password/.test(blob)) return false;
  if (/surgeon|refer to|dr\. name/.test(blob)) return false;
  if (/patient history|patient vitals/.test(blob)) return false;
  if (/patient|donor name|patient name/.test(blob)) return true;
  if (/^(rf|rl|filefirst|filelast|pffirst|pflast|qname|rqname|bedpatient|invpatient|uppatient|upatname|dxpatient|cdpatient|imgpatient|otpatient|donname)$/.test(id)) return true;
  if (input.getAttribute("list") && /pat/.test(input.getAttribute("list"))) return true;
  return false;
}
function patientEmail(p) {
  return String((p && p.email) || "").trim();
}
function patientMatches(p, query) {
  var q = String(query || "").trim().toLowerCase();
  if (!q) return false;
  var full = patientFullName(p).toLowerCase();
  var id = String(p.id || "").toLowerCase();
  var phone = String(p.phone || "").toLowerCase();
  var mail = patientEmail(p).toLowerCase();
  if (full.indexOf(q) >= 0 || id.indexOf(q) >= 0 || phone.indexOf(q) >= 0 || mail.indexOf(q) >= 0) return true;
  var parts = q.split(/\s+/).filter(Boolean);
  return parts.length > 1 && parts.every(function (part) { return full.indexOf(part) >= 0 || mail.indexOf(part) >= 0; });
}
function rankPatient(p, query) {
  var q = String(query || "").trim().toLowerCase();
  var full = patientFullName(p).toLowerCase();
  var mail = patientEmail(p).toLowerCase();
  if (full === q || mail === q) return 0;
  if (full.indexOf(q) === 0 || mail.indexOf(q) === 0) return 1;
  if (full.indexOf(" " + q) >= 0) return 2;
  if (String(p.id || "").toLowerCase().indexOf(q) >= 0) return 3;
  return 4;
}
function hidePatientSuggest() {
  if (_suggestEl) _suggestEl.hidden = true;
  _suggestInput = null;
  _suggestHits = [];
  _suggestIndex = -1;
}
function placePatientSuggest(input) {
  if (!_suggestEl) return;
  var rect = input.getBoundingClientRect();
  var width = Math.max(rect.width, 220);
  var left = rect.left;
  if (left + width > window.innerWidth - 8) left = Math.max(8, window.innerWidth - width - 8);
  _suggestEl.style.width = width + "px";
  _suggestEl.style.left = left + "px";
  var top = rect.bottom + 4;
  _suggestEl.style.top = top + "px";
  _suggestEl.hidden = false;
  var box = _suggestEl.getBoundingClientRect();
  if (box.bottom > window.innerHeight - 8) {
    _suggestEl.style.top = Math.max(8, rect.top - box.height - 4) + "px";
  }
}
function applyPatientPick(input, patient) {
  var full = patientFullName(patient);
  var first = patient.first_name || full.split(" ")[0] || "";
  var rest = patient.last_name || full.split(" ").slice(1).join(" ");
  var id = (input.id || "").toLowerCase();
  var pair = { rf: "rL", filefirst: "fileLast", pffirst: "pfLast", rl: "rF", filelast: "fileFirst", pflast: "pfFirst" };
  if (pair[id]) {
    input.value = (id === "rl" || id === "filelast" || id === "pflast") ? rest : first;
    var other = document.getElementById(pair[id]);
    if (other) other.value = (id === "rl" || id === "filelast" || id === "pflast") ? first : rest;
  } else {
    input.value = full;
  }
  input.dataset.patientId = patient.id || "";
  input.dataset.patientName = full;
  input.dataset.email = patientEmail(patient);
  ["rE", "fileEmail", "pfEmail", "invEmail"].forEach(function (id) {
    var el = document.getElementById(id);
    if (!el) return;
    if (!el.value || el.dataset.filledFromPatient === "1") {
      el.value = patientEmail(patient);
      el.dataset.filledFromPatient = "1";
    }
  });
  input.dispatchEvent(new Event("input", { bubbles: true }));
  input.dispatchEvent(new Event("change", { bubbles: true }));
  hidePatientSuggest();
}
function paintPatientSuggest(input, hits, note) {
  if (!_suggestEl) {
    _suggestEl = document.createElement("div");
    _suggestEl.className = "patient-suggest";
    _suggestEl.hidden = true;
    _suggestEl.setAttribute("role", "listbox");
    document.body.appendChild(_suggestEl);
  }
  _suggestInput = input;
  _suggestHits = hits || [];
  if (note) {
    _suggestEl.innerHTML = '<div class="ps-empty">' + esc(note) + "</div>";
  } else {
    _suggestEl.innerHTML = hits.map(function (p, i) {
      var name = patientFullName(p);
      var mail = patientEmail(p);
      var initials = typeof initialsOf === "function" ? initialsOf(name) : name.slice(0, 2).toUpperCase();
      return '<button type="button" role="option" data-i="' + i + '" class="' + (i === _suggestIndex ? "is-active" : "") + '">' +
        '<span class="ps-avatar">' + esc(initials) + "</span>" +
        '<span class="ps-copy"><strong>' + esc(name) + '</strong><span class="ps-meta">Patient · ' + esc(mail || "No email") + "</span></span></button>";
    }).join("");
    _suggestEl.querySelectorAll("button").forEach(function (btn) {
      btn.onmousedown = function (e) { e.preventDefault(); };
      btn.onclick = function () {
        var picked = hits[Number(btn.getAttribute("data-i"))];
        if (picked && _suggestInput) applyPatientPick(_suggestInput, picked);
      };
    });
  }
  placePatientSuggest(input);
}
function showPatientSuggest(input) {
  if (!isPatientNameField(input)) return;
  if (input.getAttribute("list")) input.removeAttribute("list");
  var query = input.value.trim();
  if (query.length < 1) { hidePatientSuggest(); return; }
  if (input.dataset.patientName && query === input.dataset.patientName) {
    hidePatientSuggest();
    return;
  }
  if (input.dataset.patientName && query !== input.dataset.patientName) {
    input.dataset.patientId = "";
    input.dataset.patientName = "";
  }
  if (!_regPatients) paintPatientSuggest(input, [], "Loading registered patients…");
  loadRegisteredPatients().then(function (rows) {
    if (_suggestInput !== input || input.value.trim() !== query) return;
    var hits = (rows || []).filter(function (p) { return patientMatches(p, query) && patientFullName(p); });
    hits.sort(function (a, b) { return rankPatient(a, query) - rankPatient(b, query); });
    hits = hits.slice(0, 8);
    _suggestIndex = hits.length ? 0 : -1;
    if (!hits.length) {
      paintPatientSuggest(input, [], _regPatientError || (_regPatients && _regPatients.length ? "No registered patient with that name" : "No registered patients"));
    } else paintPatientSuggest(input, hits);
  });
}
function onPatientSuggestKey(e) {
  if (!_suggestEl || _suggestEl.hidden || !_suggestHits.length) return;
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    _suggestIndex += e.key === "ArrowDown" ? 1 : -1;
    if (_suggestIndex < 0) _suggestIndex = _suggestHits.length - 1;
    if (_suggestIndex >= _suggestHits.length) _suggestIndex = 0;
    paintPatientSuggest(_suggestInput, _suggestHits);
  } else if (e.key === "Enter" && _suggestIndex >= 0) {
    e.preventDefault();
    applyPatientPick(_suggestInput, _suggestHits[_suggestIndex]);
  } else if (e.key === "Escape") {
    hidePatientSuggest();
  }
}
function initPatientSuggest() {
  if (window.__patientSuggestBound) return;
  window.__patientSuggestBound = true;
  document.addEventListener("focusin", function (e) {
    if (e.target && e.target.tagName === "SELECT" && needsPatientNames(e.target)) {
      if ((e.target.textContent || "").indexOf("Could not read names") >= 0) {
        _regPatients = null;
        _regPatientAt = 0;
      }
      fillRegisteredPatientSelects(e.target);
    }
    if (isPatientNameField(e.target)) showPatientSuggest(e.target);
  });
  document.addEventListener("input", function (e) {
    if (isPatientNameField(e.target)) showPatientSuggest(e.target);
  });
  document.addEventListener("keydown", onPatientSuggestKey, true);
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest(".patient-suggest")) return;
    if (isPatientNameField(e.target)) return;
    hidePatientSuggest();
  });
  window.addEventListener("resize", hidePatientSuggest);
  window.addEventListener("scroll", function () {
    if (_suggestInput && _suggestEl && !_suggestEl.hidden) placePatientSuggest(_suggestInput);
  }, true);
}
function needsPatientNames(sel) {
  if (!sel || sel.tagName !== "SELECT") return false;
  if (sel.dataset.patientSelect === "1") return true;
  var text = sel.textContent || "";
  return text.indexOf("Abel Mekonnen") >= 0 || text.indexOf("Could not read names") >= 0 || text.indexOf("No registered patients") >= 0;
}
function fillRegisteredPatientSelects(root) {
  var scope = root && root.tagName === "SELECT" ? null : (root || document);
  var selects = scope ? scope.querySelectorAll("select") : [root];
  Array.prototype.forEach.call(selects, function (sel) {
    if (!needsPatientNames(sel)) return;
    sel.dataset.patientSelect = "1";
    loadRegisteredPatients().then(function (rows) {
      var html = (rows || []).map(function (p) {
        var name = patientFullName(p);
        if (!name) return "";
        var label = name + (patientEmail(p) ? " · " + patientEmail(p) : "");
        return '<option value="' + esc(name) + '">' + esc(label) + "</option>";
      }).filter(Boolean).join("");
      sel.innerHTML = html || '<option value="">' + esc(_regPatientError || "No registered patients") + "</option>";
    });
  });
}
