/* Wolaita Sodo Hospital — Groq appointment page.
   Uses saved doctors, saved visits, and the live /ai/appointment endpoints.
   An SMS is reported only when Africa's Talking accepts it. */
(function (root) {
  function endpoint(name, fallback) {
    var map = (root.CONFIG && root.CONFIG.ENDPOINTS) || {};
    return map[name] || fallback;
  }

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[ch];
    });
  }

  function value(id) {
    var node = root.document.getElementById(id);
    return node ? node.value.trim() : "";
  }

  function box(id) {
    return root.document.getElementById(id);
  }

  function spin(id, on) {
    var node = box(id);
    if (!node) return;
    if (on) node.innerHTML = "<p class=\"appt-wait\">Waiting for Groq…</p>";
  }

  function warnGroq(data) {
    if (data && (data.explained_by === "missing-key" || data.groq === false)) {
      return "<p class=\"appt-warn\">Groq is not configured, so this answer uses saved hospital records only.</p>";
    }
    return "";
  }

  function payload() {
    return {
      patient: value("aiPatient"),
      department: value("aiDept"),
      doctor: value("aiDoc"),
      reason: value("aiReason"),
      urgency: value("aiUrgency")
    };
  }

  function needPatient() {
    if (!value("aiPatient")) {
      showSection("aiScreen", "<p class=\"appt-warn\">Type the patient name first.</p>");
      return false;
    }
    return true;
  }

  function needDoctor() {
    var doctor = value("aiDoc");
    if (!doctor || doctor === "No doctor is registered" || doctor === "Loading doctors…") {
      showSection("aiSlots", "<p class=\"appt-warn\">Choose a saved doctor. No doctor name is invented.</p>");
      return false;
    }
    return true;
  }

  function showSection(id, html) {
    var node = box(id);
    if (node) node.innerHTML = html;
  }

  function call(path, body, target, draw) {
    spin(target, true);
    if (typeof apiFetch !== "function") {
      showSection(target, "<p class=\"appt-warn\">The hospital connection is not ready.</p>");
      return;
    }
    apiFetch(path, "POST", body || {}, { quiet: true }).then(function (res) {
      if (!res || !res.ok) {
        showSection(target, "<p class=\"appt-warn\">" + esc((res && res.error) || "The appointment assistant could not finish.") + "</p>");
        return;
      }
      draw(res.data || {});
    });
  }

  function riskBadge(data) {
    var level = String((data && (data.risk_level || (data.risk && data.risk.risk_level))) || "Unknown");
    var pct = data.no_show_percent;
    if (pct == null && data.risk) pct = data.risk.no_show_percent;
    var kind = level === "High" ? "high" : level === "Medium" ? "medium" : level === "Low" ? "low" : "unknown";
    var score = pct == null ? "not scored" : pct + "%";
    var timing = data.best_reminder_timing || data.explanation || (data.risk && data.risk.best_reminder_timing) || "";
    return "<p><span class=\"risk-badge risk-" + kind + "\">" + esc(level) + " · " + esc(score) + "</span></p>"
      + (timing ? "<p>" + esc(timing) + "</p>" : "")
      + "<p class=\"appt-note\">Risk comes from saved visits. No history means no percent.</p>";
  }

  function drawSlots(data) {
    var html = warnGroq(data);
    if (data.summary) html += "<p>" + esc(data.summary) + "</p>";
    if (data.booked) html += "<p>Saved a visit on " + esc(data.booked.date) + " at " + esc(data.booked.time) + " with " + esc(data.booked.doctor) + ".</p>";
    var slots = data.slots || [];
    if (!slots.length && !data.booked) html += "<p>No open slot was returned. Nothing was invented.</p>";
    html += slots.map(function (slot) {
      return "<div class=\"slot-row\"><div><strong>" + esc(slot.date) + "</strong> · " + esc(slot.time) + "<br><span>" + esc(slot.doctor) + "</span></div>"
        + "<button type=\"button\" class=\"btn btn-primary\" data-slot=\"" + esc(slot.id) + "\">Book This Slot</button></div>";
    }).join("");
    showSection("aiSlots", html);
    var rootBox = box("aiSlots");
    if (!rootBox) return;
    rootBox.querySelectorAll("[data-slot]").forEach(function (button) {
      button.onclick = function () { bookSlot(button.getAttribute("data-slot")); };
    });
    if (data.risk) showSection("aiRisk", riskBadge(data.risk));
  }

  function bookSlot(slotId) {
    if (!needPatient() || !needDoctor()) return;
    var body = payload();
    body.book = true;
    body.slot_id = slotId;
    call(endpoint("APPOINTMENT_SCHEDULE", "/ai/appointment/schedule"), body, "aiSlots", function (data) {
      drawSlots(data);
      if (data.booked && typeof loadPageData === "function") loadPageData();
    });
  }

  function checkSlots() {
    if (!needPatient() || !needDoctor()) return;
    call(endpoint("APPOINTMENT_SCHEDULE", "/ai/appointment/schedule"), payload(), "aiSlots", drawSlots);
  }

  function loadScreen() {
    if (!needPatient()) return;
    call(endpoint("APPOINTMENT_PRESCREEN", "/ai/appointment/prescreen"), payload(), "aiScreen", function (data) {
      var known = data.prefilled || {};
      var keys = Object.keys(known);
      var html = warnGroq(data);
      html += "<p>" + esc(data.summary || "Intake questions are ready.") + "</p>";
      html += "<div class=\"prefill\">" + (keys.length ? keys.map(function (key) {
        return "<span><strong>" + esc(key.replace(/_/g, " ")) + "</strong> " + esc(known[key]) + "</span>";
      }).join("") : "<span>No age, condition, or last visit is saved for this name.</span>") + "</div>";
      html += (data.questions || []).map(function (item, index) {
        return "<label class=\"check-line\"><input type=\"checkbox\"> <span>" + esc(item) + "</span></label><input class=\"form-control\" data-answer=\"" + index + "\" placeholder=\"Answer, if known\">";
      }).join("");
      html += "<p class=\"appt-note\">Answers stay on this page. They are not saved as a diagnosis.</p>";
      showSection("aiScreen", html);
    });
  }

  function loadRisk() {
    if (!needPatient()) return;
    call(endpoint("PREDICT_APPOINTMENT", "/ai/predict-appointment"), { patient: value("aiPatient"), department: value("aiDept") }, "aiRisk", function (data) {
      showSection("aiRisk", warnGroq(data) + riskBadge(data));
    });
  }

  function loadBrief() {
    if (!needPatient()) return;
    call(endpoint("APPOINTMENT_BRIEF", "/ai/appointment/doctor-brief"), payload(), "aiBrief", function (data) {
      var html = warnGroq(data) + "<p>" + esc(data.summary || "No summary was returned.") + "</p>";
      (data.flags || []).forEach(function (item) { html += "<p>Flag: " + esc(item) + "</p>"; });
      html += "<h4>Visits</h4>" + ((data.visits || []).length ? (data.visits || []).map(function (row) {
        return "<p>" + esc(row.date) + " " + esc(row.time || "") + " · " + esc(row.dept || "") + " · " + esc(row.status || "") + "</p>";
      }).join("") : "<p>No saved visits.</p>");
      html += "<h4>Medicines</h4>" + ((data.medicines || []).length ? (data.medicines || []).map(function (row) {
        return "<p>" + esc(row.drug || row.name || "Medicine") + " · " + esc(row.status || "") + "</p>";
      }).join("") : "<p>No saved medicines.</p>");
      html += "<h4>Labs</h4>" + ((data.labs || []).length ? (data.labs || []).map(function (row) {
        return "<p>" + esc(row.test || "Lab") + " · " + esc(row.status || "") + (row.ai_flag ? " · " + esc(row.ai_flag) : "") + "</p>";
      }).join("") : "<p>No saved lab results.</p>");
      showSection("aiBrief", html);
    });
  }

  function sendReminders() {
    call(endpoint("APPOINTMENT_REMINDERS", "/ai/appointment/reminders"), { all_upcoming: true, days: 30 }, "aiRemind", function (data) {
      var html = "<p>" + esc(data.summary || "No reminder was sent.") + "</p>";
      if (data.sms === "not-sent") html += "<p class=\"appt-warn\">Africa's Talking did not accept an SMS. A saved inbox message is not delivery.</p>";
      (data.sent || []).forEach(function (item) {
        html += "<p><strong>" + esc(item.patient) + "</strong> · " + esc(item.date || "") + " " + esc(item.time || "")
          + "<br>Patient SMS: " + esc(item.patient_sms || item.sms || "not reported")
          + "<br>Staff SMS: " + esc(item.staff_sms || "not reported") + "</p>";
      });
      if (!(data.sent || []).length) html += "<p>No upcoming visit needed a new reminder.</p>";
      showSection("aiRemind", html);
    });
  }

  function mount(role) {
    if (!root.document || root.document.getElementById("apptAi")) return;
    var body = root.document.querySelector(".page-body");
    if (!body) return;
    var clinician = role === "doctor" || role === "nurse";
    if (!root.document.getElementById("appt-ai-style")) {
      var style = root.document.createElement("style");
      style.id = "appt-ai-style";
      style.textContent = "#apptAi,#apptAi .appt-panel{background:#fff;color:#06141B;border:1px solid #9AA6AC;border-radius:12px}#apptAi h3,#apptAi h4,#apptAi p,#apptAi label,#apptAi span{color:#06141B}#apptAi .appt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}#apptAi .appt-panel{padding:14px}#apptAi .form-row{display:flex;gap:8px;flex-wrap:wrap}#apptAi .form-control{min-width:0}#apptAi .slot-row{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:8px 0;border-top:1px solid #D5DDE1}#apptAi .risk-badge{display:inline-block;padding:4px 10px;border-radius:999px;font-weight:700}#apptAi .risk-low{background:#DCFCE7;color:#166534}#apptAi .risk-medium{background:#FEF3C7;color:#92400E}#apptAi .risk-high{background:#FEE2E2;color:#991B1B}#apptAi .risk-unknown{background:#E5E7EB;color:#06141B}#apptAi .appt-warn{color:#991B1B}#apptAi .appt-note{font-size:13px}#apptAi .prefill{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}#apptAi .prefill span{border:1px solid #9AA6AC;border-radius:8px;padding:4px 8px}#apptAi .check-line{display:flex;gap:8px;align-items:flex-start;margin-top:8px}html[data-theme=\"dark\"] #apptAi,html[data-theme=\"dark\"] #apptAi .appt-panel{background:#11212D;color:#F4F7F8}html[data-theme=\"dark\"] #apptAi h3,html[data-theme=\"dark\"] #apptAi h4,html[data-theme=\"dark\"] #apptAi p,html[data-theme=\"dark\"] #apptAi label,html[data-theme=\"dark\"] #apptAi span{color:#F4F7F8}";
      root.document.head.appendChild(style);
    }
    var card = root.document.createElement("div");
    card.id = "apptAi";
    card.style.marginBottom = "16px";
    card.innerHTML = ""
      + "<div class=\"appt-grid\">"
      + "<section class=\"appt-panel\"><h3>Book appointment</h3><p>Groq suggests open slots from the hospital calendar. It does not invent a doctor or a time.</p>"
      + "<div class=\"form-row\"><input class=\"form-control\" id=\"aiPatient\" placeholder=\"Patient name\"><select class=\"form-control\" id=\"aiDept\"><option>Internal Medicine</option><option>Pediatrics</option><option>Cardiology</option><option>Maternity</option><option>Orthopedics</option></select></div>"
      + "<div class=\"form-row\" style=\"margin-top:8px\"><select class=\"form-control\" id=\"aiDoc\"><option>Loading doctors…</option></select><select class=\"form-control\" id=\"aiUrgency\"><option value=\"Routine\">Routine</option><option value=\"Urgent\">Urgent</option><option value=\"Emergency\">Emergency</option></select></div>"
      + "<input class=\"form-control\" id=\"aiReason\" placeholder=\"Reason for visit\" style=\"margin-top:8px\">"
      + "<button type=\"button\" class=\"btn btn-primary\" id=\"aiSchedule\" style=\"margin-top:8px\">Check Available Slots</button><div id=\"aiSlots\"></div></section>"
      + "<section class=\"appt-panel\"><h3>AI pre-screening</h3><p>Questions come from Groq. Known fields come only from the saved record.</p><div id=\"aiScreen\"><p class=\"appt-note\">Enter a patient name to load the intake questions.</p></div></section>"
      + "<section class=\"appt-panel\"><h3>No-show risk</h3><div id=\"aiRisk\"><p class=\"appt-note\">Enter a patient name to score saved visits.</p></div></section>"
      + (clinician ? "<section class=\"appt-panel\"><h3>Doctor brief</h3><button type=\"button\" class=\"btn\" id=\"aiBriefBtn\">Open doctor brief</button><div id=\"aiBrief\"></div></section>" : "")
      + "<section class=\"appt-panel\"><h3>Send reminder</h3><p>Africa's Talking must accept an SMS before it is counted. Sandbox does not reach a real phone.</p><button type=\"button\" class=\"btn btn-primary\" id=\"aiRemindBtn\">Send reminders</button><div id=\"aiRemind\"></div></section>"
      + "</div>";
    body.insertBefore(card, body.firstChild);
    if (typeof loadDoctorList === "function") {
      loadDoctorList().then(function (result) {
        var select = box("aiDoc");
        if (!select) return;
        if (!result || !result.ok || !result.items.length) {
          select.innerHTML = "<option>No doctor is registered</option>";
          return;
        }
        select.innerHTML = result.items.map(function (doctor) {
          return "<option>" + esc(doctor.name) + "</option>";
        }).join("");
      });
    }
    var name = box("aiPatient");
    var timer = 0;
    if (name) name.addEventListener("input", function () {
      root.clearTimeout(timer);
      timer = root.setTimeout(function () {
        if (value("aiPatient").length < 3) return;
        loadScreen();
        loadRisk();
      }, 500);
    });
    box("aiSchedule").onclick = checkSlots;
    box("aiRemindBtn").onclick = sendReminders;
    var brief = box("aiBriefBtn");
    if (brief) brief.onclick = loadBrief;
    apiFetch("/health", "GET", null, { quiet: true, skipAuth: true }).then(function (res) {
      if (res && res.ok && res.data && res.data.sms_live === false) {
        showSection("aiRemind", "<p class=\"appt-warn\">Africa's Talking username is sandbox. An accepted SMS stays in the simulator and does not reach a phone.</p>");
      }
    });
  }

  root.AppointmentAI = { mount: mount };
})(typeof window !== "undefined" ? window : globalThis);
