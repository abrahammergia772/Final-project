/* ============================================================
   MedIQ Pro — utils.js
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
function confirmDialog(message, { title = "Confirm Action", confirmText = "Delete", danger = true } = {}) {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal sm">
        <div class="modal-header"><h3>${escapeHtml(title)}</h3></div>
        <div class="modal-body"><p style="color:#374151">${escapeHtml(message)}</p></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" data-cancel>Cancel</button>
          <button class="btn ${danger ? "btn-danger" : "btn-primary"}" data-ok>${escapeHtml(confirmText)}</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    overlay.querySelector("[data-cancel]").onclick = () => { overlay.remove(); resolve(false); };
    overlay.querySelector("[data-ok]").onclick = () => { overlay.remove(); resolve(true); };
    overlay.addEventListener("click", (e) => { if (e.target === overlay) { overlay.remove(); resolve(false); } });
  });
}

// ---------- Generic modal helper ----------
function openModal(html, { size = "", onMount = null } = {}) {
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
  document.body.appendChild(overlay);
  overlay.querySelector("[data-close]").onclick = () => overlay.remove();
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
  if (onMount) onMount(overlay);
  return overlay;
}

function closeModal(overlay) { if (overlay) overlay.remove(); }

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
  return '<tr class="empty-row"><td colspan="' + colspan + '" style="text-align:center;color:#6B7280;padding:32px">' +
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
const CHART_COLORS = ["#1A56DB", "#10B981", "#D97706", "#7C3AED", "#DC2626", "#0891B2", "#65A30D", "#DB2777"];

function chartSvg(width, height, inner) {
  return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" role="img" preserveAspectRatio="xMidYMid meet">${inner}</svg>`;
}

// Bar chart: data = [{label, value}]
function barChart(data, { height = 240, color = "#1A56DB", valueFmt = (v) => v } = {}) {
  const padL = 44, padB = 34, padT = 14, padR = 10;
  const max = Math.max(...data.map(d => d.value), 1);
  const innerW = 620, innerH = height;
  const plotW = innerW - padL - padR, plotH = innerH - padT - padB;
  const step = plotW / data.length;
  const barW = Math.min(46, step * 0.58);
  let bars = "", labels = "", grid = "";
  for (let i = 0; i <= 4; i++) {
    const y = padT + (plotH / 4) * i;
    grid += `<line x1="${padL}" y1="${y}" x2="${innerW - padR}" y2="${y}" stroke="#E5E7EB" stroke-width="1"/>`;
    grid += `<text x="${padL - 8}" y="${y + 4}" font-size="11" fill="#6B7280" text-anchor="end">${valueFmt(Math.round(max - (max / 4) * i))}</text>`;
  }
  data.forEach((d, i) => {
    const h = Math.max(2, (d.value / max) * plotH);
    const x = padL + step * i + (step - barW) / 2;
    const y = padT + plotH - h;
    bars += `<rect x="${x}" y="${y}" width="${barW}" height="${h}" rx="5" fill="${Array.isArray(color) ? color[i % color.length] : color}" opacity="0.92"/>`;
    bars += `<text x="${x + barW / 2}" y="${y - 5}" font-size="10" fill="#374151" text-anchor="middle" font-weight="600">${valueFmt(d.value)}</text>`;
    labels += `<text x="${x + barW / 2}" y="${innerH - 10}" font-size="10" fill="#6B7280" text-anchor="middle">${d.label}</text>`;
  });
  return chartSvg(innerW, innerH, grid + bars + labels);
}

// Line/area chart: data = [{label, value}]  (opts.area → fill)
function lineChart(data, { height = 240, color = "#1A56DB", area = true, valueFmt = (v) => v, showPoints = true } = {}) {
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
    grid += `<line x1="${padL}" y1="${y}" x2="${innerW - padR}" y2="${y}" stroke="#E5E7EB" stroke-width="1"/>`;
    const val = min + (range / 4) * (4 - i);
    grid += `<text x="${padL - 8}" y="${y + 4}" font-size="11" fill="#6B7280" text-anchor="end">${valueFmt(Math.round(val))}</text>`;
  }
  const pts = data.map((d, i) => X(i) + "," + Y(d.value)).join(" ");
  const poly = `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;
  const fill = area ? `<polygon points="${padL},${padT + plotH} ${pts} ${X(data.length - 1)},${padT + plotH}" fill="${color}" opacity="0.10"/>` : "";
  const dots = showPoints ? data.map((d, i) => `<circle cx="${X(i)}" cy="${Y(d.value)}" r="3.4" fill="#fff" stroke="${color}" stroke-width="2"/>`).join("") : "";
  const labels = data.map((d, i) => {
    if (data.length > 12 && i % Math.ceil(data.length / 8) !== 0) return "";
    return `<text x="${X(i)}" y="${innerH - 10}" font-size="10" fill="#6B7280" text-anchor="middle">${d.label}</text>`;
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
    `<text x="${cx}" y="${cy - 4}" font-size="24" font-weight="700" fill="#111827" text-anchor="middle">${centerPct}%</text>` +
    `<text x="${cx}" y="${cy + 16}" font-size="10" fill="#6B7280" text-anchor="middle">${escapeHtml(data[0] ? data[0].label : "")}</text>`);
}
function polar(cx, cy, r, deg) {
  const rad = (deg - 90) * Math.PI / 180;
  return { x: +(cx + r * Math.cos(rad)).toFixed(2), y: +(cy + r * Math.sin(rad)).toFixed(2) };
}

// Sparkline: values = [numbers]
function sparkline(values, { width = 140, height = 40, color = "#1A56DB" } = {}) {
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
    s += `<text x="${padL + i * cellW + cellW / 2}" y="${18}" font-size="11" fill="#6B7280" text-anchor="middle">${d}</text>`;
  });
  rows.forEach((row, r) => {
    const y = colH + r * cellH;
    s += `<text x="${padL - 10}" y="${y + cellH / 2 + 4}" font-size="11" fill="#374151" text-anchor="end" font-weight="600">${escapeHtml(row.label)}</text>`;
    row.cells.forEach((c, i) => {
      const x = padL + i * cellW;
      const color = c.v >= 75 ? "#DC2626" : c.v >= 50 ? "#D97706" : c.v >= 25 ? "#FACC15" : "#E7F0E9";
      s += `<rect x="${x}" y="${y}" width="${cellW - 8}" height="${cellH - 10}" rx="8" fill="${color}" opacity="0.85"/>`;
      s += `<text x="${x + (cellW - 8) / 2}" y="${y + (cellH - 10) / 2 + 5}" font-size="13" font-weight="700" fill="${c.v >= 25 ? "#111827" : "#fff"}" text-anchor="middle">${c.v}</text>`;
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
let _layoutDelegationDone = false;
function _bindLayoutDelegation() {
  if (_layoutDelegationDone) return;
  _layoutDelegationDone = true;

  // Hamburger → open mobile menu
  document.addEventListener("click", (e) => {
    const ham = e.target.closest("#hamburger");
    if (ham) {
      e.stopPropagation();
      document.body.classList.add("mobile-menu-open");
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
      document.body.classList.remove("mobile-menu-open");
      return;
    }
    // Any link marked [data-close-menu] (e.g. sidebar nav items) → close mobile menu
    const closer = e.target.closest("[data-close-menu]");
    if (closer) {
      document.body.classList.remove("mobile-menu-open");
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
        document.body.classList.remove("mobile-menu-open");
      }
    }, { passive: true });
  } catch (e) { /* ignore on browsers without touch */ }

  // Esc closes dropdowns + mobile menu
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".dropdown-menu.show").forEach(m => m.classList.remove("show"));
      document.body.classList.remove("mobile-menu-open");
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
  // Live notifications bell (safe to call; only runs if #notifMenu exists).
  // Guard so we don't refetch on every SPA page swap.
  if (!window.__notifsBound) {
    initNotifications();
    window.__notifsBound = true;
  }
}

// ---------- Permission-based tabs ----------
// Nav links tagged data-perm are hidden unless the current role has that
// permission (granted/revoked by the admin from Roles & Permissions).
function applyPermissions() {
  const role = getUserRole();
  if (!role) return;
  seedPermissions();
  document.querySelectorAll(".nav-link[data-perm]").forEach(a => {
    if (!canAccess(role, a.dataset.perm)) a.classList.add("hidden");
  });
}

// ---------- Live notifications (topbar bell) ----------
// Fills the notifications dropdown with real data: low stock, abnormal
// results, today's appointments — instead of static placeholders.
// Clicking a notification opens a full-detail popup.
function initNotifications() {
  const menu = document.getElementById("notifMenu");
  if (!menu) return;
  const items = [];
  const now = new Date().toTimeString().slice(0, 5);
  Promise.all([
    apiFetch(CONFIG.ENDPOINTS.INVENTORY),
    apiFetch(CONFIG.ENDPOINTS.LAB_RESULTS),
    apiFetch(CONFIG.ENDPOINTS.APPOINTMENTS)
  ]).then(([inv, lab, appt]) => {
    if (inv.ok) {
      inv.data.items.filter(i => i.status === "low-stock" || i.status === "out-of-stock")
        .slice(0, 2).forEach(i => items.push({
          icon: "package", tint: "#FFFBEB", color: "#D97706",
          category: "Inventory", time: now,
          title: i.name + " — " + i.status.replace("-", " "),
          sub: i.stock + " " + i.unit + " remaining",
          detail: i.name + " has only " + i.stock + " " + i.unit + " left (" + i.status.replace("-", " ") + "). Recommended action: create a purchase order for at least " + (i.stock * 3) + " " + i.unit + " to cover the next 30 days.",
          link: "pharmacist/inventory.html"
        }));
    }
    if (lab.ok) {
      lab.data.items.filter(r => r.ai_flag === "abnormal").slice(0, 1).forEach(r => items.push({
        icon: "alert", tint: "#FEF2F2", color: "#DC2626",
        category: "Laboratory", time: formatDateTime(r.date),
        title: "Abnormal result: " + r.test,
        sub: r.patient + " · AI flagged",
        detail: "The AI analyzer flagged the " + r.test + " result for " + r.patient + " as abnormal. Please review the values and confirm the interpretation before releasing.",
        link: "laboratory/results.html"
      }));
    }
    if (appt.ok) {
      const today = appt.data.items.filter(a => a.date === todayStr() && a.status === "confirmed").length;
      if (today) items.push({
        icon: "calendar", tint: "#EFF6FF", color: "#1A56DB",
        category: "Appointments", time: todayStr(),
        title: today + " confirmed appointment" + (today > 1 ? "s" : "") + " today",
        sub: "Review today's schedule",
        detail: "There " + (today > 1 ? "are" : "is") + " " + today + " confirmed appointment" + (today > 1 ? "s" : "") + " scheduled for today. Ensure patients are checked in on time and doctors are aware of their queue.",
        link: getUserRole() === "patient" ? "patient/appointments.html" : "reception/appointments.html"
      });
    }
    renderNotifItems(menu, items);
  });
}
function renderNotifItems(menu, items) {
  menu.innerHTML = '<div class="dd-header">Notifications</div>' +
    (items.length
      ? items.map((i, idx) => `<div class="dd-item" data-notif="${idx}"><div class="feed-icon" style="background:${i.tint};color:${i.color}">${ICONS[i.icon]}</div><div class="feed-text"><div class="dd-title">${esc(i.title)}</div><div class="dd-sub">${esc(i.sub)}</div></div></div>`).join("")
      : '<div class="empty-state" style="padding:22px;color:#6B7280">You\'re all caught up ✅</div>') +
    '<div class="dd-footer"><a href="#" onclick="event.preventDefault();showToast(\'All notifications shown\',\'info\')">View all</a></div>';
  menu.querySelectorAll("[data-notif]").forEach(el => {
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      openNotificationDetail(items[+el.dataset.notif]);
      const dot = document.querySelector(".notif-dot");
      if (dot) dot.style.display = "none";
    });
  });
}

// ---------- Notification detail popup ----------
function openNotificationDetail(n) {
  openModal({
    title: n.title,
    body: `<div class="detail-list">
      <div class="detail-item"><span class="k">Category</span><span class="v">${esc(n.category || "System")}</span></div>
      <div class="detail-item"><span class="k">Time</span><span class="v">${esc(n.time || "Just now")}</span></div>
      <div class="detail-item"><span class="k">Status</span><span class="v"><span class="badge badge-warning">Active</span></span></div>
    </div>
    <div class="alert alert-info mt-4 mb-0"><span>${ICONS[n.icon]}</span>
      <div class="alert-body"><strong>${esc(n.title)}</strong><div class="mt-2" style="font-size:13px;color:#374151">${esc(n.detail || n.sub || "")}</div></div>
    </div>
    ${n.link ? `<div class="form-actions mt-4"><a class="btn btn-primary" href="${esc(n.link)}">${ICONS.eye} Open related page</a></div>` : ""}`,
    size: "lg"
  });
}

// Auto-close alerts
document.addEventListener("click", (e) => {
  if (e.target.closest(".alert-close")) e.target.closest(".alert").remove();
});
