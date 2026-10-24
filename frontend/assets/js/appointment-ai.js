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

  function mount() {
    if (!root.document) return;
    var old = root.document.getElementById("apptAi");
    if (old && old.parentNode) old.parentNode.removeChild(old);
  }

  root.AppointmentAI = { mount: mount };
})(typeof window !== "undefined" ? window : globalThis);
