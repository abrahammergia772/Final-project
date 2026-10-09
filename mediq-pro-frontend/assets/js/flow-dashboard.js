(function () {
  var I = {
    hospital: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18"/><path d="M5 21V7l7-4 7 4v14"/><path d="M12 7v4"/><path d="M10 9h4"/></svg>',
    spark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/></svg>',
    ok: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>',
    warn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="m10.3 4.3-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-2.7l-8-14a2 2 0 0 0-3.4 0z"/></svg>',
    heart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4 3 5.5l7 7z"/></svg>',
    flask: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3h6"/><path d="M10 3v6.2L4.6 19a2 2 0 0 0 1.8 3h11.2a2 2 0 0 0 1.8-3L14 9.2V3"/></svg>',
    pill: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7z"/><path d="m8.5 8.5 7 7"/></svg>',
    cal: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
    users: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/></svg>',
    box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/></svg>'
  };

  var ROLES = {
    doctor: {
      role: "Doctor",
      flowLabel: "Today's patient flow",
      flow: [
        { n: 8, name: "Triage", cls: "done", prompt: "Show Triage patients", href: "patients.html" },
        { n: 14, name: "Waiting", cls: "active", prompt: "Show Waiting patients", href: "appointments.html" },
        { n: 3, name: "In consult", cls: "active", prompt: "Show In consult patients", href: "consultation.html" },
        { n: 2, name: "Urgent", cls: "urgent", badge: 2, prompt: "Show Urgent patients", href: "patients.html" },
        { n: 5, name: "Lab", cls: "wait", prompt: "Show Lab patients", href: "patients.html" },
        { n: 28, name: "Discharged", cls: "done", prompt: "Show Discharged patients", href: "patients.html" }
      ],
      stats: [
        { val: "47", label: "Patients today", delta: "↑ 12% vs yesterday", up: true },
        { val: "18m", label: "Avg wait time", delta: "↑ 4m vs yesterday", up: false }
      ],
      timeline: [
        { kind: "ai", title: "AI flagged high-risk", text: "Abebe Bekele · BP 160/95 · flagged for review", chip: "Urgent", chipCls: "urgent", time: "2m ago" },
        { kind: "ok", title: "Lab result ready", text: "Tigist Alemu · CBC complete", chip: "Normal", chipCls: "normal", time: "8m ago" },
        { kind: "warn", title: "Appointment no-show", text: "Dawit Haile · 09:30 slot missed", chip: "Follow up", chipCls: "ai", time: "14m ago" }
      ],
      ai: [
        { name: "Clinical decision", pct: 91, runs: 34, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "clinical-decision.html" },
        { name: "Lab analyzer", pct: 88, runs: 21, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "flask", prompt: "Show Lab analyzer details", href: "ai-diagnosis.html" },
        { name: "Vitals alert", pct: 84, runs: 18, color: "#E24B4A", bg: "#FCEBEB", ink: "#A32D2D", icon: "heart", prompt: "Show Vitals alert details", href: "patients.html" }
      ]
    },
    nurse: {
      role: "Nurse",
      flowLabel: "Ward flow",
      flow: [
        { n: 11, name: "Vitals", cls: "active", prompt: "Show Vitals patients", href: "vitals.html" },
        { n: 6, name: "Observations", cls: "wait", prompt: "Show Observations patients", href: "observations.html" },
        { n: 4, name: "Meds due", cls: "urgent", badge: 4, prompt: "Show Meds due patients", href: "medications.html" },
        { n: 9, name: "Handover", cls: "done", prompt: "Show Handover patients", href: "care-plans.html" }
      ],
      stats: [
        { val: "18", label: "Assigned patients", delta: "↑ 2 today", up: true },
        { val: "4", label: "Meds due", delta: "Needs this hour", up: false }
      ],
      timeline: [
        { kind: "alert", title: "Vitals overdue", text: "Bed 12 · BP not recorded this hour", chip: "Urgent", chipCls: "urgent", time: "3m ago" },
        { kind: "ok", title: "Medication given", text: "Hana Tadesse · morning dose recorded", chip: "Done", chipCls: "normal", time: "11m ago" },
        { kind: "ai", title: "AI vitals check", text: "Rising pulse flagged on ward B", chip: "Review", chipCls: "ai", time: "19m ago" }
      ],
      ai: [
        { name: "Vitals alert", pct: 84, runs: 18, color: "#E24B4A", bg: "#FCEBEB", ink: "#A32D2D", icon: "heart", prompt: "Show Vitals alert details", href: "vitals.html" },
        { name: "Clinical decision", pct: 91, runs: 12, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "vitals.html" }
      ]
    },
    pharmacist: {
      role: "Pharmacist",
      flowLabel: "Dispensing flow",
      flow: [
        { n: 7, name: "Orders", cls: "active", prompt: "Show Orders patients", href: "prescriptions.html" },
        { n: 3, name: "Review", cls: "wait", prompt: "Show Review patients", href: "ai-interaction.html" },
        { n: 19, name: "Dispensed", cls: "done", prompt: "Show Dispensed patients", href: "prescriptions.html" },
        { n: 2, name: "Stock alert", cls: "urgent", badge: 2, prompt: "Show Stock alert patients", href: "inventory.html" }
      ],
      stats: [
        { val: "26", label: "Orders today", delta: "↑ 5 vs yesterday", up: true },
        { val: "2", label: "Low-stock items", delta: "Needs reorder", up: false }
      ],
      timeline: [
        { kind: "warn", title: "Interaction warning", text: "Warfarin + ibuprofen held for review", chip: "Review", chipCls: "urgent", time: "4m ago" },
        { kind: "ok", title: "Prescription dispensed", text: "Amoxicillin 500mg · counter 2", chip: "Done", chipCls: "normal", time: "9m ago" },
        { kind: "ai", title: "Inventory forecast", text: "Paracetamol may run low this week", chip: "AI", chipCls: "ai", time: "22m ago" }
      ],
      ai: [
        { name: "Drug interaction", pct: 96, runs: 15, color: "#BA7517", bg: "#FAEEDA", ink: "#633806", icon: "pill", prompt: "Show Drug interaction details", href: "ai-interaction.html" },
        { name: "Inventory forecast", pct: 79, runs: 9, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "box", prompt: "Show Inventory forecast details", href: "inventory.html" }
      ]
    },
    reception: {
      role: "Reception",
      flowLabel: "Front desk flow",
      flow: [
        { n: 12, name: "Walk-in", cls: "active", prompt: "Show Walk-in patients", href: "queue.html" },
        { n: 9, name: "Queue", cls: "wait", prompt: "Show Queue patients", href: "queue.html" },
        { n: 21, name: "Registered", cls: "done", prompt: "Show Registered patients", href: "patients.html" },
        { n: 3, name: "Referred", cls: "urgent", badge: 3, prompt: "Show Referred patients", href: "admissions.html" }
      ],
      stats: [
        { val: "33", label: "Arrivals today", delta: "↑ 6 vs yesterday", up: true },
        { val: "2", label: "No-shows", delta: "Follow up needed", up: false }
      ],
      timeline: [
        { kind: "ok", title: "Patient registered", text: "New invoice opened at the front desk", chip: "Done", chipCls: "normal", time: "1m ago" },
        { kind: "warn", title: "Queue waiting", text: "9 people still in the morning queue", chip: "Queue", chipCls: "urgent", time: "6m ago" },
        { kind: "ai", title: "No-show prediction", text: "Two afternoon slots look at risk", chip: "AI", chipCls: "ai", time: "18m ago" }
      ],
      ai: [
        { name: "Appointment AI", pct: 86, runs: 27, color: "#185FA5", bg: "#E6F1FB", ink: "#0C447C", icon: "cal", prompt: "Show Appointment AI details", href: "appointments.html" },
        { name: "Symptom chatbot", pct: 90, runs: 11, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Symptom chatbot details", href: "queue.html" }
      ]
    },
    admin: {
      role: "Admin",
      flowLabel: "Hospital operations",
      flow: [
        { n: 42, name: "Users", cls: "done", prompt: "Show Users patients", href: "users.html" },
        { n: 8, name: "Shifts", cls: "active", prompt: "Show Shifts patients", href: "shifts.html" },
        { n: 3, name: "Notices", cls: "wait", prompt: "Show Notices patients", href: "announcements.html" },
        { n: 1, name: "Audit", cls: "urgent", badge: 1, prompt: "Show Audit patients", href: "audit-logs.html" }
      ],
      stats: [
        { val: "42", label: "Staff accounts", delta: "All roles active", up: true },
        { val: "1", label: "Audit flags", delta: "Needs review", up: false }
      ],
      timeline: [
        { kind: "warn", title: "Shift gap", text: "Evening pharmacy cover is still open", chip: "Shift", chipCls: "urgent", time: "5m ago" },
        { kind: "ok", title: "User approved", text: "New nurse account is active", chip: "Done", chipCls: "normal", time: "16m ago" },
        { kind: "ai", title: "Module health", text: "All seven AI modules responded", chip: "AI", chipCls: "ai", time: "28m ago" }
      ],
      ai: [
        { name: "Clinical decision", pct: 91, runs: 34, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "ai-config.html" },
        { name: "Drug interaction", pct: 96, runs: 15, color: "#BA7517", bg: "#FAEEDA", ink: "#633806", icon: "pill", prompt: "Show Drug interaction details", href: "ai-config.html" },
        { name: "Lab analyzer", pct: 88, runs: 21, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "flask", prompt: "Show Lab analyzer details", href: "ai-config.html" },
        { name: "Vitals alert", pct: 84, runs: 18, color: "#E24B4A", bg: "#FCEBEB", ink: "#A32D2D", icon: "heart", prompt: "Show Vitals alert details", href: "ai-config.html" }
      ]
    },
    manager: {
      role: "Manager",
      flowLabel: "Hospital day",
      flow: [
        { n: 6, name: "Departments", cls: "done", prompt: "Show Departments patients", href: "departments.html" },
        { n: 14, name: "Finance", cls: "active", prompt: "Show Finance patients", href: "finance.html" },
        { n: 2, name: "Complaints", cls: "urgent", badge: 2, prompt: "Show Complaints patients", href: "complaints.html" },
        { n: 4, name: "Reports", cls: "wait", prompt: "Show Reports patients", href: "reports.html" }
      ],
      stats: [
        { val: "ETB 48k", label: "Collections today", delta: "↑ 8% vs yesterday", up: true },
        { val: "2", label: "Open complaints", delta: "Waiting on reply", up: false }
      ],
      timeline: [
        { kind: "warn", title: "Complaint opened", text: "Waiting time at reception · ticket 214", chip: "Open", chipCls: "urgent", time: "7m ago" },
        { kind: "ok", title: "Morning report", text: "Department summary is ready", chip: "Done", chipCls: "normal", time: "20m ago" },
        { kind: "ai", title: "Appointment forecast", text: "Afternoon clinic may run over", chip: "AI", chipCls: "ai", time: "31m ago" }
      ],
      ai: [
        { name: "Appointment AI", pct: 86, runs: 27, color: "#185FA5", bg: "#E6F1FB", ink: "#0C447C", icon: "cal", prompt: "Show Appointment AI details", href: "reports.html" },
        { name: "Inventory forecast", pct: 79, runs: 9, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "box", prompt: "Show Inventory forecast details", href: "finance.html" }
      ]
    },
    laboratory: {
      role: "Laboratory",
      flowLabel: "Sample flow",
      flow: [
        { n: 9, name: "Received", cls: "active", prompt: "Show Received patients", href: "test-requests.html" },
        { n: 5, name: "Processing", cls: "wait", prompt: "Show Processing patients", href: "test-requests.html" },
        { n: 4, name: "Result", cls: "urgent", badge: 4, prompt: "Show Result patients", href: "results.html" },
        { n: 16, name: "Delivered", cls: "done", prompt: "Show Delivered patients", href: "results.html" }
      ],
      stats: [
        { val: "30", label: "Samples today", delta: "↑ 4 vs yesterday", up: true },
        { val: "42m", label: "Avg turnaround", delta: "↑ 6m vs yesterday", up: false }
      ],
      timeline: [
        { kind: "ok", title: "CBC delivered", text: "Tigist Alemu · result sent to the doctor", chip: "Done", chipCls: "normal", time: "8m ago" },
        { kind: "ai", title: "Lab analyzer", text: "Abnormal range suggested on sample 118", chip: "Review", chipCls: "ai", time: "12m ago" },
        { kind: "warn", title: "Sample waiting", text: "4 results still need a sign-off", chip: "Pending", chipCls: "urgent", time: "17m ago" }
      ],
      ai: [
        { name: "Lab analyzer", pct: 88, runs: 21, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "flask", prompt: "Show Lab analyzer details", href: "ai-analyzer.html" },
        { name: "Clinical decision", pct: 91, runs: 6, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "test-requests.html" }
      ]
    },
    patient: {
      role: "Patient",
      flowLabel: "Your care path",
      flow: [
        { n: 1, name: "Appointment", cls: "active", prompt: "Show Appointment patients", href: "appointments.html" },
        { n: 1, name: "Consult", cls: "wait", prompt: "Show Consult patients", href: "appointments.html" },
        { n: 1, name: "Lab", cls: "done", prompt: "Show Lab patients", href: "records.html" },
        { n: 1, name: "Prescription", cls: "wait", prompt: "Show Prescription patients", href: "records.html" }
      ],
      stats: [
        { val: "1", label: "Upcoming visit", delta: "This morning", up: true },
        { val: "1", label: "Open result", delta: "Ready to view", up: true }
      ],
      timeline: [
        { kind: "ok", title: "Lab result ready", text: "Your latest result is available to view", chip: "Ready", chipCls: "normal", time: "8m ago" },
        { kind: "ai", title: "Symptom chatbot", text: "A suggestion is waiting if you want it", chip: "AI", chipCls: "ai", time: "1h ago" },
        { kind: "warn", title: "Bill open", text: "One invoice is still unpaid", chip: "Bill", chipCls: "urgent", time: "Yesterday" }
      ],
      ai: [
        { name: "Symptom chatbot", pct: 90, runs: 4, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Symptom chatbot details", href: "ai-chatbot.html" },
        { name: "Appointment AI", pct: 86, runs: 2, color: "#185FA5", bg: "#E6F1FB", ink: "#0C447C", icon: "cal", prompt: "Show Appointment AI details", href: "appointments.html" }
      ]
    }
  };

  var SHIFT = [
    { cls: "seg-doctor", label: "Doctors", n: 3, flex: 3 },
    { cls: "seg-nurse", label: "Nurses", n: 2, flex: 2 },
    { cls: "seg-pharm", label: "Pharm", n: 2, flex: 2 },
    { cls: "seg-off", label: "Off", n: 1, flex: 1 }
  ];

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function sendPrompt(text) {
    if (typeof showToast === "function") showToast(text, "info");
  }
  window.sendPrompt = sendPrompt;

  function shiftName(hour) {
    if (hour >= 8 && hour < 16) return { name: "Morning shift", time: "08:00 – 16:00" };
    if (hour >= 16) return { name: "Evening shift", time: "16:00 – 00:00" };
    return { name: "Night shift", time: "00:00 – 08:00" };
  }

  function dateLine() {
    var d = new Date();
    var day = d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short", year: "numeric" });
    return day;
  }

  function mount(root) {
    if (!root) return;
    var role = root.getAttribute("data-flow-role") || "doctor";
    var cfg = ROLES[role] || ROLES.doctor;
    var shift = shiftName(new Date().getHours());
    var flow = cfg.flow.map(function (item) {
      var badge = item.badge ? '<span class="flow-badge">' + item.badge + "</span>" : "";
      return '<button type="button" class="flow-node ' + item.cls + '" role="listitem" data-prompt="' + esc(item.prompt) + '" data-href="' + esc(item.href) + '">' +
        '<span class="flow-dot">' + item.n + badge + "</span>" +
        '<span class="flow-name" data-i18n="' + esc(item.name) + '">' + esc(item.name) + "</span></button>";
    }).join("");
    var stats = cfg.stats.map(function (s) {
      return '<div class="stat-tile"><div class="stat-val">' + esc(s.val) + '</div><div class="stat-lbl" data-i18n="' + esc(s.label) + '">' + esc(s.label) +
        '</div><div class="stat-delta ' + (s.up ? "up" : "dn") + '" data-i18n="' + esc(s.delta) + '">' + esc(s.delta) + "</div></div>";
    }).join("");
    var timeline = cfg.timeline.map(function (t) {
      return '<article class="tl-item"><div class="tl-dot ' + t.kind + '">' + (I[t.kind === "ai" ? "spark" : t.kind === "ok" ? "ok" : "warn"]) +
        '</div><div class="tl-body"><div class="tl-top"><div class="tl-title" data-i18n="' + esc(t.title) + '">' + esc(t.title) +
        '</div><time class="tl-time">' + esc(t.time) + '</time></div><p class="tl-text">' + esc(t.text) +
        '</p><span class="tl-chip ' + t.chipCls + '" data-i18n="' + esc(t.chip) + '">' + esc(t.chip) + "</span></div></article>";
    }).join("");
    var segs = SHIFT.map(function (s) {
      return '<div class="seg ' + s.cls + '" style="flex:' + s.flex + '">' + s.n + " " + s.label + "</div>";
    }).join("");
    var legend = SHIFT.map(function (s) {
      return "<span><i class=\"" + s.cls + "\"></i>" + s.n + " " + s.label + "</span>";
    }).join("");
    var ai = cfg.ai.map(function (m) {
      return '<button type="button" class="ai-card" role="button" tabindex="0" data-prompt="' + esc(m.prompt) + '" data-href="' + esc(m.href) + '">' +
        '<div class="ai-top"><span class="ai-ico" style="background:' + m.bg + ";color:" + m.ink + '">' + I[m.icon] + "</span>" +
        '<span class="ai-name" data-i18n="' + esc(m.name) + '">' + esc(m.name) + '</span><span class="ai-meta"><span class="ai-pct">' + m.pct +
        '%</span><div class="ai-runs">' + m.runs + ' runs</div></span></div><div class="ai-bar-track"><div class="ai-bar-fill" style="width:' +
        m.pct + "%;background:" + m.color + '"></div></div></button>';
    }).join("");

    root.innerHTML =
      '<div class="flow-dash" data-flow-dash="1">' +
      '<header class="identity-bar"><div><p class="hosp-name">' + I.hospital + '<span data-i18n="Wolaita Sodo Hospital">Wolaita Sodo Hospital</span></p>' +
      '<p class="hosp-sub"><span data-i18n="' + esc(cfg.role) + '">' + esc(cfg.role) + "</span> · " + esc(dateLine()) + " · <span data-i18n=\"" + esc(shift.name) + "\">" + esc(shift.name) + "</span></p></div>" +
      '<span class="live-pill"><span class="live-dot" aria-hidden="true"></span><span data-i18n="Live">Live</span></span></header>' +
      '<section aria-label="Today\'s patient flow"><p class="section-label" data-i18n="' + esc(cfg.flowLabel) + '">' + esc(cfg.flowLabel) +
      '</p><div class="flow-strip" role="list">' + flow + "</div></section>" +
      '<div class="stat-row">' + stats + "</div>" +
      '<section class="timeline-section" aria-label="Live activity"><p class="section-label" data-i18n="Live activity">Live activity</p><div class="timeline" role="feed">' + timeline + "</div></section>" +
      '<section class="shift-card" aria-label="Shift coverage"><div class="shift-header"><span data-i18n="Shift coverage">Shift coverage</span><span class="shift-time">' + esc(shift.time) +
      '</span></div><div class="shift-track" role="img" aria-label="Shift coverage ' + SHIFT.map(function (s) { return s.n + " " + s.label; }).join(", ") + '">' + segs +
      '</div><div class="shift-legend">' + legend + "</div></section>" +
      '<section aria-label="AI module health"><p class="section-label" data-i18n="AI module health">AI module health</p><div class="ai-grid">' + ai + "</div></section></div>";

    root.querySelectorAll("[data-prompt]").forEach(function (el) {
      el.addEventListener("click", function () {
        sendPrompt(el.getAttribute("data-prompt"));
      });
    });
    }

  window.FlowDash = { mount: mount, sendPrompt: sendPrompt };
})();
