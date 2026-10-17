/* Wolaita Sodo Hospital — Groq appointment assistant.
   Scheduling, reminders, intake, doctor brief, and follow-up.
   Replies are not spoken. SMS is not connected. */
(function (root) {
  function endpoint(name, fallback) {
    var map = (root.CONFIG && root.CONFIG.ENDPOINTS) || {};
    return map[name] || fallback;
  }

  function show(html) {
    var box = root.document && root.document.getElementById("apptAiResult");
    if (!box) return;
    box.innerHTML = html;
  }

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[ch];
    });
  }

  function call(path, body) {
    show("<p>Working…</p>");
    if (typeof apiFetch !== "function") {
      show("<p>The hospital connection is not ready.</p>");
      return;
    }
    apiFetch(path, "POST", body || {}, { quiet: true }).then(function (res) {
      if (!res || !res.ok) {
        show("<p>" + esc((res && res.error) || "The appointment assistant could not finish.") + "</p>");
        return;
      }
      show(render(res.data || {}));
    });
  }

  function render(data) {
    var lines = [];
    if (data.summary) lines.push("<p>" + esc(data.summary) + "</p>");
    if (data.risk && data.risk.risk_level) {
      var pct = data.risk.no_show_percent == null ? "not scored" : data.risk.no_show_percent + "%";
      lines.push("<p>No-show risk from saved visits: " + esc(data.risk.risk_level) + " (" + esc(pct) + ").</p>");
    }
    (data.slots || []).forEach(function (slot) {
      lines.push("<p>" + esc(slot.date) + " at " + esc(slot.time) + " with " + esc(slot.doctor) + "</p>");
    });
    (data.sent || data.flagged || []).forEach(function (item) {
      lines.push("<p>" + esc(item.patient) + " · " + esc(item.date || "") + " " + esc(item.time || "") + "</p>");
    });
    (data.questions || []).forEach(function (item) {
      lines.push("<p>• " + esc(item) + "</p>");
    });
    if (data.prefilled && Object.keys(data.prefilled).length) {
      lines.push("<p>Prefilled from the record: " + esc(JSON.stringify(data.prefilled)) + "</p>");
    }
    (data.flags || []).forEach(function (item) {
      lines.push("<p>Flag: " + esc(item) + "</p>");
    });
    if (data.booked) lines.push("<p>Saved a visit on " + esc(data.booked.date) + " at " + esc(data.booked.time) + ".</p>");
    if (!lines.length) lines.push("<p>No matching hospital record was found. Nothing was invented.</p>");
    lines.push("<p>SMS is not connected. Email was not sent. Messages, when saved, are in the hospital inbox.</p>");
    return lines.join("");
  }

  function value(id) {
    var node = root.document.getElementById(id);
    return node ? node.value.trim() : "";
  }

  function mount(role) {
    if (!root.document || root.document.getElementById("apptAi")) return;
    var body = root.document.querySelector(".page-body");
    if (!body) return;
    if (!root.document.getElementById("appt-ai-style")) {
      var style = root.document.createElement("style");
      style.id = "appt-ai-style";
      style.textContent = "#apptAi,#apptAiResult{background:#fff;color:#06141B;border:1px solid #9AA6AC}#apptAi button{color:#06141B;background:#fff;border:1px solid #9AA6AC;font-weight:700}#apptAi .btn-primary{background:#1A6FA8;color:#fff;border-color:#1A6FA8}html[data-theme=\"dark\"] #apptAi,html[data-theme=\"dark\"] #apptAiResult{background:#11212D;color:#F4F7F8}";
      root.document.head.appendChild(style);
    }
    var card = root.document.createElement("div");
    card.className = "card mb-4";
    card.id = "apptAi";
    card.style.padding = "14px";
    var clinician = role === "doctor";
    card.innerHTML = ""
      + "<h3 style=\"font-size:16px;margin:0 0 8px\">Appointment assistant</h3>"
      + "<p style=\"margin:0 0 10px\">Groq uses saved visits. It does not use the old trained model. A reply is not read aloud.</p>"
      + "<div style=\"display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px\">"
      + "<input class=\"form-control\" id=\"aiPatient\" placeholder=\"Patient name\" style=\"max-width:220px\">"
      + "<select class=\"form-control\" id=\"aiDept\" style=\"max-width:180px\"><option>Internal Medicine</option><option>Pediatrics</option><option>Cardiology</option><option>Maternity</option><option>Orthopedics</option></select>"
      + "<select class=\"form-control\" id=\"aiDoc\" style=\"max-width:200px\"><option>Dr. Daniel Alemu</option><option>Dr. Fikru Debebe</option><option>Dr. Meron Assefa</option><option>Dr. Tsehay Mengistu</option></select>"
      + "<select class=\"form-control\" id=\"aiUrgency\" style=\"max-width:140px\"><option value=\"routine\">Routine</option><option value=\"soon\">Soon</option><option value=\"urgent\">Urgent</option></select>"
      + "</div>"
      + "<input class=\"form-control\" id=\"aiReason\" placeholder=\"Reason for the visit\" style=\"margin-bottom:10px\">"
      + "<div style=\"display:flex;gap:8px;flex-wrap:wrap\">"
      + "<button type=\"button\" class=\"btn btn-primary\" id=\"aiSchedule\">Suggest slots</button>"
      + "<button type=\"button\" class=\"btn\" id=\"aiBook\">Book first slot</button>"
      + "<button type=\"button\" class=\"btn\" id=\"aiRemind\">Send reminders</button>"
      + "<button type=\"button\" class=\"btn\" id=\"aiForm\">Intake form</button>"
      + (clinician ? "<button type=\"button\" class=\"btn\" id=\"aiBrief\">Doctor brief</button>" : "")
      + "<button type=\"button\" class=\"btn\" id=\"aiFollow\">Follow-up</button>"
      + "</div>"
      + "<div id=\"apptAiResult\" style=\"margin-top:12px;padding:10px;border-radius:8px\"></div>";
    body.insertBefore(card, body.firstChild);
    function payload(book) {
      return {
        patient: value("aiPatient"),
        department: value("aiDept"),
        doctor: value("aiDoc"),
        reason: value("aiReason"),
        urgency: value("aiUrgency"),
        book: !!book
      };
    }
    root.document.getElementById("aiSchedule").onclick = function () {
      call(endpoint("APPOINTMENT_SCHEDULE", "/ai/appointment/schedule"), payload(false));
    };
    root.document.getElementById("aiBook").onclick = function () {
      call(endpoint("APPOINTMENT_SCHEDULE", "/ai/appointment/schedule"), payload(true));
    };
    root.document.getElementById("aiRemind").onclick = function () {
      call(endpoint("APPOINTMENT_REMINDERS", "/ai/appointment/reminders"), { days: 3 });
    };
    root.document.getElementById("aiForm").onclick = function () {
      call(endpoint("APPOINTMENT_PRESCREEN", "/ai/appointment/prescreen"), payload(false));
    };
    var brief = root.document.getElementById("aiBrief");
    if (brief) brief.onclick = function () {
      call(endpoint("APPOINTMENT_BRIEF", "/ai/appointment/doctor-brief"), payload(false));
    };
    root.document.getElementById("aiFollow").onclick = function () {
      call(endpoint("APPOINTMENT_FOLLOWUP", "/ai/appointment/follow-up"), payload(false));
    };
  }

  root.AppointmentAI = { mount: mount };
})(typeof window !== "undefined" ? window : globalThis);
