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
    box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/></svg>',
    bed: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 18V8"/><path d="M2 14h20v4"/><path d="M6 14V9h7v5"/><path d="M22 18V8"/></svg>',
    clip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/></svg>'
  };

  function rolePhoto(role) {
    var base = (typeof basePath === "function") ? basePath() : "";
    var alt = {
      doctor: "A doctor speaking with a patient",
      nurse: "A nurse checking a patient's blood pressure",
      pharmacist: "A pharmacist at the dispensing counter",
      laboratory: "A laboratory scientist with a sample",
      reception: "A receptionist at the hospital desk",
      admin: "A hospital administrator at a desk",
      manager: "A hospital manager in the corridor",
      patient: "A patient waiting calmly with a card"
    }[role] || "Hospital staff";
    return '<img class="role-photo" src="' + base + "assets/images/roles/" + role + '.jpg" alt="' + esc(alt) + '">';
  }

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
      timeline: [],
      ai: [
        { name: "Clinical decision", pct: 91, runs: 34, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "clinical-decision.html" },
        { name: "Lab analyzer", pct: 88, runs: 21, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "flask", prompt: "Show Lab analyzer details", href: "ai-diagnosis.html" },
        { name: "Vitals alert", pct: 84, runs: 18, color: "#E24B4A", bg: "#FCEBEB", ink: "#A32D2D", icon: "heart", prompt: "Show Vitals alert details", href: "patients.html" }
      ],
      must: [
        { name: "Patients", note: "Who is in your care", href: "patients.html" },
        { name: "Consultation", note: "Start a visit", href: "consultation.html" },
        { name: "Appointments", note: "Today's visits", href: "appointments.html" },
        { name: "Prescriptions", note: "Write or review", href: "prescriptions.html" },
        { name: "Bed requests", note: "Request a bed", href: "beds.html" },
        { name: "Clinical decision", note: "Decision support", href: "clinical-decision.html" }
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
      timeline: [],
      ai: [
        { name: "Vitals alert", pct: 84, runs: 18, color: "#E24B4A", bg: "#FCEBEB", ink: "#A32D2D", icon: "heart", prompt: "Show Vitals alert details", href: "vitals.html" },
        { name: "Clinical decision", pct: 91, runs: 12, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "vitals.html" }
      ],
      must: [
        { name: "Vitals", note: "Record vitals", href: "vitals.html" },
        { name: "Medications", note: "Give medication", href: "medications.html" },
        { name: "Observations", note: "Ward notes", href: "observations.html" },
        { name: "Care Plans", note: "Care plan", href: "care-plans.html" },
        { name: "Beds", note: "Ward beds", href: "beds.html" },
        { name: "Patients", note: "Assigned patients", href: "patients.html" }
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
      timeline: [],
      ai: [
        { name: "Drug interaction", pct: 96, runs: 15, color: "#BA7517", bg: "#FAEEDA", ink: "#633806", icon: "pill", prompt: "Show Drug interaction details", href: "ai-interaction.html" },
        { name: "Inventory forecast", pct: 79, runs: 9, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "box", prompt: "Show Inventory forecast details", href: "inventory.html" }
      ],
      must: [
        { name: "Prescriptions", note: "Dispense orders", href: "prescriptions.html" },
        { name: "Inventory", note: "Stock levels", href: "inventory.html" },
        { name: "Drug interaction", note: "Check interactions", href: "ai-interaction.html" },
        { name: "Inventory forecast", note: "Forecast stock", href: "ai-forecast.html" },
        { name: "Suppliers", note: "Suppliers", href: "suppliers.html" },
        { name: "Patients", note: "Find a patient", href: "patients.html" }
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
      timeline: [],
      ai: [
        { name: "Appointment AI", pct: 86, runs: 27, color: "#185FA5", bg: "#E6F1FB", ink: "#0C447C", icon: "cal", prompt: "Show Appointment AI details", href: "appointments.html" },
        { name: "Symptom chatbot", pct: 90, runs: 11, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Symptom chatbot details", href: "queue.html" }
      ],
      must: [
        { name: "Registration", note: "Register a patient", href: "registration.html" },
        { name: "Queue", note: "Waiting line", href: "queue.html" },
        { name: "Appointments", note: "Book a visit", href: "appointments.html" },
        { name: "Cashier", note: "Take payment", href: "billing.html" },
        { name: "Admissions", note: "Admit a patient", href: "admissions.html" },
        { name: "Patients", note: "Find a patient", href: "patients.html" }
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
      timeline: [],
      ai: [
        { name: "Clinical decision", pct: 91, runs: 34, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "ai-config.html" },
        { name: "Drug interaction", pct: 96, runs: 15, color: "#BA7517", bg: "#FAEEDA", ink: "#633806", icon: "pill", prompt: "Show Drug interaction details", href: "ai-config.html" },
        { name: "Lab analyzer", pct: 88, runs: 21, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "flask", prompt: "Show Lab analyzer details", href: "ai-config.html" },
        { name: "Vitals alert", pct: 84, runs: 18, color: "#E24B4A", bg: "#FCEBEB", ink: "#A32D2D", icon: "heart", prompt: "Show Vitals alert details", href: "ai-config.html" }
      ],
      must: [
        { name: "Users", note: "Staff accounts", href: "users.html" },
        { name: "Roles", note: "Access control", href: "roles.html" },
        { name: "Wards", note: "Wards and beds", href: "wards.html" },
        { name: "Announcements", note: "Hospital notices", href: "announcements.html" },
        { name: "Audit Logs", note: "Review activity", href: "audit-logs.html" },
        { name: "Shifts", note: "Who is on duty", href: "shifts.html" }
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
      timeline: [],
      ai: [
        { name: "Appointment AI", pct: 86, runs: 27, color: "#185FA5", bg: "#E6F1FB", ink: "#0C447C", icon: "cal", prompt: "Show Appointment AI details", href: "reports.html" },
        { name: "Inventory forecast", pct: 79, runs: 9, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "box", prompt: "Show Inventory forecast details", href: "finance.html" }
      ],
      must: [
        { name: "Departments", note: "Hospital units", href: "departments.html" },
        { name: "Staff", note: "Staff roster", href: "staff.html" },
        { name: "Finance", note: "Today's money", href: "finance.html" },
        { name: "Complaints", note: "Open complaints", href: "complaints.html" },
        { name: "Reports", note: "Hospital reports", href: "reports.html" },
        { name: "Wards", note: "Wards and beds", href: "wards.html" }
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
      timeline: [],
      ai: [
        { name: "Lab analyzer", pct: 88, runs: 21, color: "#1D9E75", bg: "#E1F5EE", ink: "#085041", icon: "flask", prompt: "Show Lab analyzer details", href: "ai-analyzer.html" },
        { name: "Clinical decision", pct: 91, runs: 6, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Clinical decision details", href: "test-requests.html" }
      ],
      must: [
        { name: "Test Requests", note: "Incoming tests", href: "test-requests.html" },
        { name: "Samples", note: "Track samples", href: "samples.html" },
        { name: "Results", note: "Sign results", href: "results.html" },
        { name: "Blood Bank", note: "Blood stock", href: "blood-bank.html" },
        { name: "Lab analyzer", note: "Read a result", href: "ai-analyzer.html" },
        { name: "Patients", note: "Find a patient", href: "patients.html" }
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
      timeline: [],
      ai: [
        { name: "Symptom chatbot", pct: 90, runs: 4, color: "#7F77DD", bg: "#EEEDFE", ink: "#3C3489", icon: "spark", prompt: "Show Symptom chatbot details", href: "ai-chatbot.html" },
        { name: "Appointment AI", pct: 86, runs: 2, color: "#185FA5", bg: "#E6F1FB", ink: "#0C447C", icon: "cal", prompt: "Show Appointment AI details", href: "appointments.html" }
      ],
      hideShift: true,
      must: [
        { name: "Appointments", note: "Your visits", href: "appointments.html" },
        { name: "Medical Records", note: "Your records", href: "records.html" },
        { name: "Bills", note: "Your invoices", href: "bills.html" },
        { name: "Health Card", note: "Your card", href: "health-card.html" },
        { name: "Complaints", note: "Raise a complaint", href: "complaints.html" },
        { name: "Messages", note: "Your messages", href: "messages.html" }
      ]
    }
  };

  var CONCEPT = {
    doctor: {
      title: "Today's care, in one place",
      sub: "See who is waiting, who is with you, and what needs a decision.",
      cta: "Open the list", href: "patients.html", prompt: "Show Waiting patients",
      cards: [
        { name: "Patients", note: "See who is in your care today.", href: "patients.html", icon: "users" },
        { name: "Consultation", note: "Start the visit that is waiting.", href: "consultation.html", icon: "heart" },
        { name: "Appointments", note: "Open today's visits.", href: "appointments.html", icon: "cal" }
      ]
    },
    nurse: {
      title: "The ward, hour by hour",
      sub: "Vitals, medicines, and the beds that need you now.",
      cta: "Open vitals", href: "vitals.html", prompt: "Show Vitals patients",
      cards: [
        { name: "Vitals", note: "Record the next set of vitals.", href: "vitals.html", icon: "heart" },
        { name: "Medications", note: "Give the doses that are due.", href: "medications.html", icon: "pill" },
        { name: "Beds", note: "See the ward beds.", href: "beds.html", icon: "bed" }
      ]
    },
    pharmacist: {
      title: "Orders ready to check",
      sub: "Review the prescription, the interaction, and the shelf.",
      cta: "Open prescriptions", href: "prescriptions.html", prompt: "Show Orders patients",
      cards: [
        { name: "Prescriptions", note: "Dispense the orders waiting.", href: "prescriptions.html", icon: "pill" },
        { name: "Inventory", note: "Check what is on the shelf.", href: "inventory.html", icon: "box" },
        { name: "Drug interaction", note: "Check a combination before you dispense.", href: "ai-interaction.html", icon: "spark" }
      ]
    },
    reception: {
      title: "The desk, in order",
      sub: "Register, queue, and book the next visit.",
      cta: "Open the queue", href: "queue.html", prompt: "Show Queue patients",
      cards: [
        { name: "Queue", note: "See who is waiting at the desk.", href: "queue.html", icon: "users" },
        { name: "Registration", note: "Register a patient and open an invoice.", href: "registration.html", icon: "clip" },
        { name: "Appointments", note: "Book a visit with a saved doctor.", href: "appointments.html", icon: "cal" }
      ]
    },
    admin: {
      title: "The hospital account",
      sub: "People, wards, and the notices that keep the day moving.",
      cta: "Open users", href: "users.html", prompt: "Show Users patients",
      cards: [
        { name: "Users", note: "Open staff accounts.", href: "users.html", icon: "users" },
        { name: "Wards", note: "See wards and beds.", href: "wards.html", icon: "bed" },
        { name: "Announcements", note: "Post a hospital notice.", href: "announcements.html", icon: "spark" }
      ]
    },
    manager: {
      title: "The day across units",
      sub: "Departments, collections, and complaints still open.",
      cta: "Open reports", href: "reports.html", prompt: "Show Reports patients",
      cards: [
        { name: "Reports", note: "Read the hospital day.", href: "reports.html", icon: "spark" },
        { name: "Finance", note: "See today's collections.", href: "finance.html", icon: "box" },
        { name: "Departments", note: "Open each hospital unit.", href: "departments.html", icon: "hospital" }
      ]
    },
    laboratory: {
      title: "The bench, in sequence",
      sub: "Requests in, samples moving, results ready to sign.",
      cta: "Open test requests", href: "test-requests.html", prompt: "Show Received patients",
      cards: [
        { name: "Test Requests", note: "See tests that just arrived.", href: "test-requests.html", icon: "flask" },
        { name: "Samples", note: "Track a sample through the bench.", href: "samples.html", icon: "box" },
        { name: "Results", note: "Sign the results that are ready.", href: "results.html", icon: "ok" }
      ]
    },
    patient: {
      title: "Your visit, clearly",
      sub: "The appointment, the record, and the bill that is still open.",
      cta: "Open appointments", href: "appointments.html", prompt: "Show Appointment patients",
      cards: [
        { name: "Appointments", note: "See your visits.", href: "appointments.html", icon: "cal" },
        { name: "Medical Records", note: "Open your records.", href: "records.html", icon: "clip" },
        { name: "Bills", note: "See an invoice that is still open.", href: "bills.html", icon: "box" }
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

  function showResponse(text, href) {
    var host = document.querySelector("#flowDashboard .flow-dash") || document.querySelector(".flow-dash");
    if (!host) return;
    var box = host.querySelector(".flow-response");
    if (!box) {
      box = document.createElement("section");
      box.className = "flow-response";
      box.setAttribute("role", "status");
      box.setAttribute("aria-live", "polite");
      box.setAttribute("aria-label", "Response");
      host.insertBefore(box, host.children[1] || null);
    }
    var open = href ? '<a class="flow-response-open" href="' + esc(href) + '" data-i18n="Open page">Open page</a>' : "";
    box.innerHTML = '<p class="section-label" data-i18n="Response">Response</p><p class="flow-response-text"></p>' + open;
    box.querySelector(".flow-response-text").textContent = text;
    if (box.scrollIntoView) box.scrollIntoView({ block: "nearest" });
  }

  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-prompt]");
    if (!el || !el.closest(".flow-dash")) return;
    var answer = el.getAttribute("data-answer") || el.getAttribute("data-prompt");
    var href = el.getAttribute("data-href") || "";
    showResponse(answer, href);
    sendPrompt(el.getAttribute("data-prompt") || answer);
    document.querySelectorAll(".flow-dash .is-picked").forEach(function (n) { n.classList.remove("is-picked"); });
    el.classList.add("is-picked");
  }, true);

  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    var el = e.target.closest("[data-prompt]");
    if (!el || el.closest("a, button") || !el.closest(".flow-dash")) return;
    e.preventDefault();
    el.click();
  });

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


  function todayIso() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function rowsOf(res) {
    var data = res && res.data;
    var items = data && (data.items || data);
    return Array.isArray(items) ? items : [];
  }
  function canRead(path) {
    if (!path) return false;
    if (typeof endpointAllowed === "function" && !endpointAllowed(path)) return false;
    return typeof apiFetch === "function";
  }
  function getList(name) {
    var map = (window.CONFIG && CONFIG.ENDPOINTS) || {};
    var path = map[name] || "";
    if (!canRead(path)) return Promise.resolve([]);
    return apiFetch(path, "GET", null, { quiet: true }).then(rowsOf, function () { return []; });
  }
  function sameDay(value) { return String(value || "").slice(0, 10) === todayIso(); }
  function nameTokens(value) {
    return String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").split(" ").filter(function (part) {
      return part && ["dr", "doctor", "prof", "mr", "mrs", "ms", "md"].indexOf(part) < 0;
    });
  }
  function namesMatch(left, right) {
    var a = nameTokens(left), b = nameTokens(right);
    if (!a.length || !b.length) return false;
    var short = a.join(" ").length <= b.join(" ").length ? a : b;
    var long = short === a ? b : a;
    function hit(token, words) {
      if (token.length === 1) return words.some(function (word) { return word.indexOf(token) === 0; });
      return words.some(function (word) { return word.length >= 2 && (word === token || word.indexOf(token) === 0 || token.indexOf(word) === 0); });
    }
    var needed = short.filter(function (token) { return token.length >= 2; });
    return (needed.length ? needed : short).every(function (token) { return hit(token, long); });
  }
  function statusOf(row) { return String((row && (row.status || row.stage)) || "").toLowerCase(); }
  function countWhere(rows, test) { return (rows || []).filter(test).length; }
  function setFlowCount(root, name, n) {
    var nodes = root.querySelectorAll(".flow-node");
    Array.prototype.forEach.call(nodes, function (node) {
      var label = node.querySelector(".flow-name");
      if (!label || label.textContent !== name) return;
      var dot = node.querySelector(".flow-dot");
      if (dot) dot.textContent = String(n);
      node.setAttribute("data-answer", n + " saved records are in " + name + ".");
      node.classList.remove("done", "active", "wait", "urgent");
      node.classList.add(n ? "active" : "done");
    });
  }
  function setStat(root, index, val, delta) {
    var tile = root.querySelectorAll(".stat-tile")[index];
    if (!tile) return;
    var value = tile.querySelector(".stat-val");
    var note = tile.querySelector(".stat-delta");
    var label = tile.querySelector(".stat-lbl");
    if (value) value.textContent = val;
    if (note) {
      note.removeAttribute("data-i18n");
      note.textContent = delta;
      note.classList.remove("up", "dn");
    }
    tile.setAttribute("data-answer", (label ? label.textContent : "This") + " is " + val + ". " + delta + ".");
  }
  function paintTimeline(root, rows) {
    var feed = root.querySelector(".timeline");
    if (!feed) return;
    if (!rows.length) {
      feed.innerHTML = '<div class="tl-item"><div class="tl-dot ok">' + I.ok + '</div><div class="tl-body"><div class="tl-top"><div class="tl-title">No saved activity</div><time class="tl-time">Now</time></div><p class="tl-text">Saved hospital records will appear here.</p></div></div>';
      return;
    }
    feed.innerHTML = rows.slice(0, 4).map(function (item) {
      var kind = item.kind === "warn" ? "warn" : "ok";
      return '<button type="button" class="tl-item" data-prompt="Show ' + esc(item.title) + '" data-answer="' + esc(item.title + ". " + item.text) + '" data-href="' + esc(item.href || "") + '"><div class="tl-dot ' + kind + '">' + (kind === "warn" ? I.warn : I.ok) + '</div><div class="tl-body"><div class="tl-top"><div class="tl-title">' + esc(item.title) + '</div><time class="tl-time">' + esc(item.time || "Saved") + '</time></div><p class="tl-text">' + esc(item.text) + "</p></div></button>";
    }).join("");
  }
  function stamp(row) {
    return String(row.date || row.ts || row.time || row.arrived || row.publish_date || "Saved").replace("T", " ").slice(0, 16);
  }
  function applyHealth(root, health) {
    var models = (health && health.models) || {};
    var map = {
      "Clinical decision": !!models.clinical,
      "Lab analyzer": !!models.lab,
      "Vitals alert": !!models.vitals,
      "Drug interaction": !!models.drug,
      "Inventory forecast": !!models.inventory,
      "Appointment AI": !!(health && health.groq),
      "Symptom chatbot": !!(health && health.groq)
    };
    Array.prototype.forEach.call(root.querySelectorAll(".ai-card"), function (card) {
      var nameEl = card.querySelector(".ai-name");
      if (!nameEl || !Object.prototype.hasOwnProperty.call(map, nameEl.textContent)) return;
      var on = map[nameEl.textContent];
      var pct = card.querySelector(".ai-pct");
      var runs = card.querySelector(".ai-runs");
      var bar = card.querySelector(".ai-bar-fill");
      if (pct) pct.textContent = on ? "On" : "Off";
      if (runs) runs.textContent = on ? "Loaded" : "Not loaded";
      if (bar) bar.style.width = on ? "100%" : "0%";
      card.setAttribute("data-answer", nameEl.textContent + (on ? " is loaded." : " is not loaded."));
    });
  }
  function setShift(root, counts) {
    var keys = ["Doctors", "Nurses", "Pharm", "Off"];
    var segs = root.querySelectorAll(".shift-track .seg");
    var legend = root.querySelectorAll(".shift-legend span");
    keys.forEach(function (key, i) {
      var n = counts[key] || 0;
      if (segs[i]) {
        segs[i].textContent = n + " " + key;
        segs[i].setAttribute("data-answer", n + " saved " + key + " accounts. This is the staff list, not a timed attendance roster.");
      }
      if (legend[i]) {
        var mark = legend[i].querySelector("i");
        var cls = mark ? mark.className : "";
        legend[i].innerHTML = '<i class="' + cls + '"></i>' + n + " " + key;
      }
    });
  }
  function refreshLive(root, role) {
    var jobs = {
      doctor: function () {
        return Promise.all([getList("APPOINTMENTS"), getList("LAB_REQUESTS"), getList("LAB_RESULTS"), getList("PATIENTS")]).then(function (all) {
          var appt = all[0], requests = all[1], results = all[2];
          var today = appt.filter(function (row) { return sameDay(row.date); });
          var open = appt.filter(function (row) { return !/cancel|complete|attended|discharg/i.test(statusOf(row)); });
          var who = typeof getUserName === "function" ? getUserName() : "";
          var mine = who ? appt.filter(function (row) { return namesMatch(who, row.doctor); }) : [];
          var consult = appt.filter(function (row) { return /consult|in-service|in service/i.test(statusOf(row)); });
          var urgent = appt.filter(function (row) { return /urgent|emergency/i.test(statusOf(row) + " " + (row.priority || "")); });
          var done = appt.filter(function (row) { return /complete|attended|discharg/i.test(statusOf(row)) && sameDay(row.date); });
          var labOpen = requests.filter(function (row) { return !/complete|result|deliver/i.test(statusOf(row)); });
          setFlowCount(root, "Triage", 0);
          setFlowCount(root, "Waiting", open.length);
          setFlowCount(root, "In consult", consult.length);
          setFlowCount(root, "Urgent", urgent.length);
          setFlowCount(root, "Lab", labOpen.length);
          setFlowCount(root, "Discharged", done.length);
          setStat(root, 0, String(mine.length || today.length), mine.length ? "Saved visits for " + who : "Saved appointments today");
          setStat(root, 1, "—", "Wait time is not recorded");
          var shown = (mine.length ? mine : today).concat(mine.length ? [] : results);
          paintTimeline(root, shown.slice(0, 4).map(function (row) {
            return { title: row.patient || row.test || row.type || "Saved visit", text: [row.type || row.test, row.doctor, row.date, row.status || row.time].filter(Boolean).join(" · "), time: stamp(row), href: row.test ? "patients.html" : "appointments.html" };
          }));
        });
      },
      nurse: function () {
        return Promise.all([getList("VITALS"), getList("OBSERVATIONS"), getList("MEDICATIONS"), getList("PATIENTS"), getList("MESSAGES")]).then(function (all) {
          var vitals = all[0], obs = all[1], meds = all[2], patients = all[3], messages = all[4];
          var due = meds.filter(function (row) { return /pending|due/i.test(statusOf(row)); });
          var notes = messages.filter(function (row) { return /handover/i.test(row.subject || ""); });
          setFlowCount(root, "Vitals", vitals.length);
          setFlowCount(root, "Observations", obs.length);
          setFlowCount(root, "Meds due", due.length);
          setFlowCount(root, "Handover", notes.length);
          setStat(root, 0, String(patients.length), "Saved patients");
          setStat(root, 1, String(due.length), due.length ? "Marked pending" : "None marked pending");
          var rows = due.slice(0, 2).map(function (row) {
            return { title: "Medication pending", text: [row.patient, row.drug, row.dose, row.due].filter(Boolean).join(" · "), time: row.due || "Saved", href: "medications.html", kind: "warn" };
          }).concat(obs.slice(0, 2).map(function (row) {
            return { title: "Observation saved", text: [row.patient, row.notes].filter(Boolean).join(" · "), time: row.time || "Saved", href: "observations.html" };
          }));
          paintTimeline(root, rows);
        });
      },
      pharmacist: function () {
        return Promise.all([getList("PRESCRIPTIONS"), getList("INVENTORY")]).then(function (all) {
          var rx = all[0], stock = all[1];
          var open = rx.filter(function (row) { return !/dispens|complete|cancel/i.test(statusOf(row)); });
          var done = rx.filter(function (row) { return /dispens/i.test(statusOf(row)); });
          var low = stock.filter(function (row) { return /low|out/i.test(statusOf(row)); });
          setFlowCount(root, "Orders", open.length);
          setFlowCount(root, "Review", 0);
          setFlowCount(root, "Dispensed", done.length);
          setFlowCount(root, "Stock alert", low.length);
          setStat(root, 0, String(rx.filter(function (row) { return sameDay(row.date); }).length), "Saved prescriptions today");
          setStat(root, 1, String(low.length), low.length ? "Marked low or out" : "No low-stock mark");
          paintTimeline(root, low.slice(0, 3).map(function (row) {
            return { title: row.name || "Stock item", text: [row.status, row.stock, row.unit].filter(function (part) { return part !== undefined && part !== ""; }).join(" · "), time: "Saved", href: "inventory.html", kind: "warn" };
          }));
        });
      },
      reception: function () {
        return Promise.all([getList("QUEUE"), getList("APPOINTMENTS"), getList("PATIENTS"), getList("REFERRALS")]).then(function (all) {
          var queue = all[0], appt = all[1], patients = all[2], referrals = all[3];
          var waiting = countWhere(queue, function (row) { return statusOf(row) === "waiting"; });
          var serving = countWhere(queue, function (row) { return statusOf(row) === "in-service"; });
          var today = appt.filter(function (row) { return sameDay(row.date); });
          var missed = today.filter(function (row) { return /no-?show|missed/i.test(statusOf(row)); });
          setFlowCount(root, "Walk-in", waiting + serving);
          setFlowCount(root, "Queue", waiting);
          setFlowCount(root, "Registered", patients.length);
          setFlowCount(root, "Referred", referrals.length);
          setStat(root, 0, String(today.length), "Saved appointments today");
          setStat(root, 1, String(missed.length), missed.length ? "Marked no-show" : "No saved no-show today");
          paintTimeline(root, queue.slice(0, 4).map(function (row) {
            return { title: row.status === "in-service" ? "Now serving" : "Queue", text: [row.name, row.dept, row.status].filter(Boolean).join(" · "), time: row.arrived || "Saved", href: "queue.html", kind: row.status === "held" ? "warn" : "ok" };
          }));
        });
      },
      admin: function () {
        return Promise.all([getList("USERS"), getList("SHIFTS"), getList("ANNOUNCEMENTS"), getList("AUDIT_LOGS")]).then(function (all) {
          var users = all[0], shifts = all[1], notes = all[2], logs = all[3];
          setFlowCount(root, "Users", users.length);
          setFlowCount(root, "Shifts", shifts.length);
          setFlowCount(root, "Notices", notes.length);
          setFlowCount(root, "Audit", logs.length);
          setStat(root, 0, String(users.length), "Saved accounts");
          setStat(root, 1, String(logs.length), logs.length ? "Saved audit rows" : "No saved audit rows");
          paintTimeline(root, logs.slice(0, 4).map(function (row) {
            return { title: row.action || "Audit", text: [row.user, row.detail].filter(Boolean).join(" · "), time: stamp(row), href: "audit-logs.html", kind: /fail|deny/i.test(row.status || "") ? "warn" : "ok" };
          }));
        });
      },
      manager: function () {
        return Promise.all([getList("DEPARTMENTS"), getList("BILLS"), getList("COMPLAINTS"), getList("FINANCE")]).then(function (all) {
          var depts = all[0], bills = all[1], complaints = all[2], finance = all[3];
          var open = complaints.filter(function (row) { return !/resolv|clos/i.test(statusOf(row)); });
          var paid = bills.filter(function (row) { return /paid|settled/i.test(statusOf(row)) && sameDay(row.date); });
          var sum = paid.reduce(function (total, row) { return total + (Number(row.paid || row.amount) || 0); }, 0);
          setFlowCount(root, "Departments", depts.length);
          setFlowCount(root, "Finance", bills.length + finance.length);
          setFlowCount(root, "Complaints", open.length);
          setFlowCount(root, "Reports", finance.length);
          setStat(root, 0, "ETB " + Math.round(sum).toLocaleString("en-US"), paid.length ? "Paid bills saved today" : "No paid bill saved today");
          setStat(root, 1, String(open.length), open.length ? "Still open" : "No open complaint");
          paintTimeline(root, open.slice(0, 4).map(function (row) {
            return { title: row.subject || "Complaint", text: [row.reporter, row.status].filter(Boolean).join(" · "), time: stamp(row), href: "complaints.html", kind: "warn" };
          }));
        });
      },
      laboratory: function () {
        return Promise.all([getList("SAMPLES"), getList("LAB_RESULTS")]).then(function (all) {
          var samples = all[0], results = all[1];
          function stage(name) { return countWhere(samples, function (row) { return statusOf(row) === name; }); }
          var tats = samples.map(function (row) { return Number(row.tat); }).filter(function (n) { return isFinite(n) && n > 0; });
          var avg = tats.length ? Math.round(tats.reduce(function (s, n) { return s + n; }, 0) / tats.length) : null;
          setFlowCount(root, "Received", stage("received") + stage("collected"));
          setFlowCount(root, "Processing", stage("processing"));
          setFlowCount(root, "Result", stage("result-ready") + results.filter(function (row) { return !/complete|deliver/i.test(statusOf(row)); }).length);
          setFlowCount(root, "Delivered", stage("completed") + countWhere(results, function (row) { return /complete|deliver/i.test(statusOf(row)); }));
          setStat(root, 0, String(samples.filter(function (row) { return sameDay(row.collected || row.date); }).length), "Samples dated today");
          setStat(root, 1, avg == null ? "—" : String(avg), avg == null ? "Turnaround is not recorded" : "Average of saved turnaround values");
          paintTimeline(root, samples.slice(0, 4).map(function (row) {
            return { title: row.test || "Sample", text: [row.patient, row.stage].filter(Boolean).join(" · "), time: row.collected || "Saved", href: "samples.html" };
          }));
        });
      },
      patient: function () {
        return Promise.all([getList("APPOINTMENTS"), getList("PRESCRIPTIONS"), getList("LAB_RESULTS"), getList("BILLS")]).then(function (all) {
          var appt = all[0], rx = all[1], labs = all[2], bills = all[3];
          var upcoming = appt.filter(function (row) { return !/cancel|complete|attended/i.test(statusOf(row)); });
          var unpaid = bills.filter(function (row) { return !/paid|settled/i.test(statusOf(row)); });
          setFlowCount(root, "Appointment", upcoming.length);
          setFlowCount(root, "Consult", countWhere(appt, function (row) { return /consult/i.test(statusOf(row)); }));
          setFlowCount(root, "Lab", labs.length);
          setFlowCount(root, "Prescription", rx.length);
          setStat(root, 0, String(upcoming.length), upcoming.length ? "Saved upcoming visits" : "No upcoming visit saved");
          setStat(root, 1, String(labs.length), labs.length ? "Saved lab results" : "No lab result saved");
          var rows = upcoming.slice(0, 2).map(function (row) {
            return { title: row.type || "Appointment", text: [row.date, row.time, row.doctor, row.dept].filter(Boolean).join(" · "), time: stamp(row), href: "appointments.html" };
          }).concat(unpaid.slice(0, 2).map(function (row) {
            return { title: "Bill open", text: [row.service || row.description, row.amount].filter(Boolean).join(" · "), time: stamp(row), href: "bills.html", kind: "warn" };
          }));
          paintTimeline(root, rows);
        });
      }
    };
    var run = jobs[role];
    if (run) run();
    if (role !== "patient") {
      getList("STAFF").then(function (staff) {
        var counts = { Doctors: 0, Nurses: 0, Pharm: 0, Off: 0 };
        (staff || []).forEach(function (row) {
          var name = String(row.role || "").toLowerCase();
          var off = /off|leave|inactive/i.test(String(row.status || "") + " " + String(row.shift || ""));
          if (off) counts.Off += 1;
          else if (name.indexOf("doctor") >= 0) counts.Doctors += 1;
          else if (name.indexOf("nurse") >= 0) counts.Nurses += 1;
          else if (name.indexOf("pharm") >= 0) counts.Pharm += 1;
        });
        setShift(root, counts);
      });
    }
    if (window.CONFIG && CONFIG.API_BASE_URL) {
      fetch(CONFIG.API_BASE_URL + "/health", { cache: "no-store" }).then(function (res) {
        return res.json();
      }).then(function (health) {
        applyHealth(root, health);
      }).catch(function () {});
    }
  }

  function mount(root) {
    if (!root) return;
    var role = root.getAttribute("data-flow-role") || "doctor";
    var cfg = ROLES[role] || ROLES.doctor;
    var shift = shiftName(new Date().getHours());
    var statPages = {
      doctor: ["patients.html", "appointments.html"],
      nurse: ["patients.html", "medications.html"],
      pharmacist: ["prescriptions.html", "inventory.html"],
      reception: ["queue.html", "appointments.html"],
      admin: ["users.html", "audit-logs.html"],
      manager: ["finance.html", "complaints.html"],
      laboratory: ["samples.html", "results.html"],
      patient: ["appointments.html", "records.html"]
    };
    var timePage = {
      doctor: "patients.html", nurse: "vitals.html", pharmacist: "prescriptions.html",
      reception: "queue.html", admin: "audit-logs.html", manager: "complaints.html",
      laboratory: "results.html", patient: "records.html"
    }[role] || "dashboard.html";
    var flow = cfg.flow.map(function (item) {
      var answer = "Saved records for " + item.name + " are loading.";
      return '<button type="button" class="flow-node ' + item.cls + '" role="listitem" data-flow-name="' + esc(item.name) + '" data-prompt="' + esc(item.prompt) + '" data-answer="' + esc(answer) + '" data-href="' + esc(item.href) + '">' +
        '<span class="flow-dot">…</span>' +
        '<span class="flow-name" data-i18n="' + esc(item.name) + '">' + esc(item.name) + "</span></button>";
    }).join("");
    var stats = cfg.stats.map(function (s, i) {
      var href = (statPages[role] || [])[i] || "dashboard.html";
      var answer = s.label + " is loading from saved records.";
      return '<button type="button" class="stat-tile" data-prompt="Show ' + esc(s.label) + '" data-answer="' + esc(answer) + '" data-href="' + esc(href) + '"><div class="stat-val">…</div><div class="stat-lbl" data-i18n="' + esc(s.label) + '">' + esc(s.label) +
        '</div><div class="stat-delta">Loading saved records</div></button>';
    }).join("");
    var timeline = '<div class="tl-item"><div class="tl-dot ok">' + I.ok + '</div><div class="tl-body"><div class="tl-top"><div class="tl-title">Loading saved activity</div><time class="tl-time">Now</time></div><p class="tl-text">Only saved hospital records are shown here.</p></div></div>';
    var segs = SHIFT.map(function (s) {
      var answer = "Saved " + s.label + " accounts are loading. This is not a timed attendance roster.";
      return '<button type="button" class="seg ' + s.cls + '" style="flex:' + s.flex + '" data-prompt="Show ' + esc(s.label) + ' shift" data-answer="' + esc(answer) + '" data-href="shifts.html">… ' + s.label + "</button>";
    }).join("");
    var legend = SHIFT.map(function (s) {
      return "<span><i class=\"" + s.cls + "\"></i>… " + s.label + "</span>";
    }).join("");
    var ai = cfg.ai.map(function (m) {
      var aiAnswer = m.name + " is being checked against the loaded model files.";
      return '<button type="button" class="ai-card" role="button" tabindex="0" data-prompt="' + esc(m.prompt) + '" data-answer="' + esc(aiAnswer) + '" data-href="' + esc(m.href) + '">' +
        '<div class="ai-top"><span class="ai-ico" style="background:' + m.bg + ";color:" + m.ink + '">' + I[m.icon] + "</span>" +
        '<span class="ai-name" data-i18n="' + esc(m.name) + '">' + esc(m.name) + '</span><span class="ai-meta"><span class="ai-pct">…</span><div class="ai-runs">Checking</div></span></div><div class="ai-bar-track"><div class="ai-bar-fill" style="width:0%;background:' +
        m.color + '"></div></div></button>';
    }).join("");
    var must = (cfg.must || []).map(function (item) {
      var mustAnswer = "Opening " + item.name + ". " + item.note + ".";
      return '<a class="must-card" href="' + esc(item.href) + '" data-prompt="Show ' + esc(item.name) + '" data-answer="' + esc(mustAnswer) + '" data-href="' + esc(item.href) + '"><strong data-i18n="' + esc(item.name) + '">' + esc(item.name) +
        '</strong><span data-i18n="' + esc(item.note) + '">' + esc(item.note) + "</span></a>";
    }).join("");
    var identity = '<span data-i18n="' + esc(cfg.role) + '">' + esc(cfg.role) + "</span> · " + esc(dateLine());
    if (!cfg.hideShift) identity += ' · <span data-i18n="' + esc(shift.name) + '">' + esc(shift.name) + "</span>";
    var statusAnswer = "Wolaita Sodo Hospital is live. " + cfg.role + " · " + dateLine() + (cfg.hideShift ? "." : " · " + shift.name + ".");
    var concept = CONCEPT[role] || CONCEPT.doctor;
    var cards = (concept.cards || []).map(function (item) {
      var answer = "Opening " + item.name + ". " + item.note;
      return '<a class="care-card" href="' + esc(item.href) + '" data-prompt="Show ' + esc(item.name) + '" data-answer="' + esc(answer) + '" data-href="' + esc(item.href) + '">' +
        '<span class="care-ico">' + (I[item.icon] || I.hospital) + "</span>" +
        '<strong data-i18n="' + esc(item.name) + '">' + esc(item.name) + "</strong>" +
        '<span data-i18n="' + esc(item.note) + '">' + esc(item.note) + "</span>" +
        '<span class="care-btn" data-i18n="View">View</span></a>';
    }).join("");
    var hero = '<section class="care-hero"><div class="care-copy">' +
      '<button type="button" class="care-kicker" data-prompt="Show hospital status" data-answer="' + esc(statusAnswer) + '">' +
      I.hospital + '<span data-i18n="Wolaita Sodo Hospital">Wolaita Sodo Hospital</span></button>' +
      '<p class="care-id">' + identity + "</p>" +
      '<h2 data-i18n="' + esc(concept.title) + '">' + esc(concept.title) + "</h2>" +
      '<p class="care-sub" data-i18n="' + esc(concept.sub) + '">' + esc(concept.sub) + "</p>" +
      '<div class="care-actions"><a class="care-cta" href="' + esc(concept.href) + '" data-prompt="' + esc(concept.prompt) + '" data-answer="' + esc("Opening " + concept.cta + ".") + '" data-href="' + esc(concept.href) + '"><span data-i18n="' + esc(concept.cta) + '">' + esc(concept.cta) + "</span></a>" +
      '<button type="button" class="live-pill" data-prompt="Show live updates" data-answer="Live updates are on for this board."><span class="live-dot" aria-hidden="true"></span><span data-i18n="Live">Live</span></button></div></div>' +
      '<div class="care-art">' + rolePhoto(role) + "</div></section>" +
      '<section class="care-row" aria-label="Start here">' + cards + "</section>";
    var shiftCard = cfg.hideShift ? "" :
      '<section class="shift-card" aria-label="Shift coverage"><div class="shift-header"><span data-i18n="Shift coverage">Shift coverage</span><span class="shift-time">' + esc(shift.time) +
      '</span></div><div class="shift-track" role="group" aria-label="Shift coverage ' + SHIFT.map(function (s) { return s.n + " " + s.label; }).join(", ") + '">' + segs +
      '</div><div class="shift-legend">' + legend + "</div></section>";

    root.innerHTML =
      '<div class="flow-dash" data-flow-dash="1" data-role="' + esc(role) + '">' +
      hero +
      '<section aria-label="Today\'s patient flow"><p class="section-label" data-i18n="' + esc(cfg.flowLabel) + '">' + esc(cfg.flowLabel) +
      '</p><div class="flow-strip" role="list">' + flow + "</div></section>" +
      '<div class="stat-row">' + stats + "</div>" +
      '<section aria-label="Must have"><p class="section-label" data-i18n="Must have">Must have</p><div class="must-grid">' + must + "</div></section>" +
      '<section class="timeline-section" aria-label="Live activity"><p class="section-label" data-i18n="Live activity">Live activity</p><div class="timeline" role="feed">' + timeline + "</div></section>" +
      shiftCard +
      '<section aria-label="AI module health"><p class="section-label" data-i18n="AI module health">AI module health</p><div class="ai-grid">' + ai + "</div></section></div>";
    refreshLive(root, role);
    }

  window.FlowDash = {
    mount: mount,
    sendPrompt: sendPrompt,
    html: function (role) {
      var el = {
        getAttribute: function (name) { return name === "data-flow-role" ? role : ""; },
        innerHTML: "",
        querySelectorAll: function () { return []; }
      };
      mount(el);
      return el.innerHTML;
    }
  };
})();
