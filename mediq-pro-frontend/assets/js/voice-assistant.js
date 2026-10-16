/* Wolaita Sodo Hospital — voice assistant for the patient chatbot.
   Speech in, speech out, and the same hospital actions the patient can do
   on the appointments, bills, complaints, and messages pages. */
(function (root) {
  var DOCTORS = ["Dr. Daniel Alemu", "Dr. Fikru Debebe", "Dr. Meron Assefa", "Dr. Tsehay Mengistu"];
  var DEPTS = [
    ["Internal Medicine", ["internal medicine", "የውስጥ"]],
    ["Pediatrics", ["pediatric", "paediatric", "children", "child", "ሕፃናት", "ህፃናት"]],
    ["Cardiology", ["cardio", "heart", "የልብ"]],
    ["Maternity", ["maternity", "pregnancy", "obstetric", "ወሊድ"]],
    ["Orthopedics", ["orthop", "bone", "joint", "አጥንት"]]
  ];
  var MONTHS = {
    january: 1, february: 2, march: 3, april: 4, may: 5, june: 6,
    july: 7, august: 8, september: 9, october: 10, november: 11, december: 12,
    jan: 1, feb: 2, mar: 3, apr: 4, jun: 6, jul: 7, aug: 8, sep: 9, sept: 9, oct: 10, nov: 11, dec: 12
  };
  var MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var pending = null;
  var soundOn = true;
  var recognition = null;
  var listening = false;
  var suppressSend = false;
  var spokenAnswer = "";

  function tr(en, am) {
    try {
      if (root.I18N && root.I18N.getLang && root.I18N.getLang() === "am") return am;
    } catch (e) { /* keep English */ }
    return en;
  }

  function clean(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
  }

  function lower(text) {
    return clean(text).toLowerCase();
  }

  function isoDate(d) {
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, "0");
    var day = String(d.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + day;
  }

  function addDays(d, n) {
    var next = new Date(d.getTime());
    next.setDate(next.getDate() + n);
    return next;
  }

  function wordToNum(word) {
    var map = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };
    if (map[word]) return map[word];
    var n = Number(word);
    return isFinite(n) ? n : 0;
  }

  function speakDate(iso) {
    var p = String(iso || "").split("-");
    if (p.length < 3) return iso || "";
    return Number(p[2]) + " " + (MONTH_NAMES[Number(p[1]) - 1] || p[1]) + " " + p[0];
  }

  function speakTime(hhmm) {
    var p = String(hhmm || "").split(":");
    var h = Number(p[0]);
    var m = p[1] || "00";
    if (!isFinite(h)) return hhmm || "";
    if (h === 0) return "12:" + m + " at night";
    if (h === 12) return "12:" + m + " noon";
    var suffix = h >= 17 ? "in the evening" : (h >= 12 ? "in the afternoon" : "in the morning");
    var h12 = h > 12 ? h - 12 : h;
    return h12 + ":" + m + " " + suffix;
  }

  function finishTime(hour, minute, hint) {
    var h = Number(hour);
    var min = String(minute || "00").padStart(2, "0");
    if (!isFinite(h) || h < 0 || h > 23) return "";
    if (Number(min) > 59) return "";
    var mark = String(hint || "");
    if (/\bpm\b/.test(mark) && h < 12) h += 12;
    if (/\bam\b/.test(mark) && h === 12) h = 0;
    if (!/\bam\b/.test(mark) && !/\bpm\b/.test(mark) && h >= 1 && h <= 7) h += 12;
    return String(h).padStart(2, "0") + ":" + min;
  }

  function parseTime(text, loose) {
    var t = lower(text).replace(/\./g, "");
    if (/\bnoon\b/.test(t)) return "12:00";
    if (/\bmidnight\b/.test(t)) return "00:00";
    var clock = t.match(/\b(\d{1,2}):(\d{2})\b/);
    if (clock) return finishTime(clock[1], clock[2], t);
    var ampm = t.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/);
    if (ampm) return finishTime(ampm[1], ampm[2] || "00", ampm[3]);
    var at = t.match(/\bat\s+(\d{1,2})(?::(\d{2}))?\b/);
    if (at) return finishTime(at[1], at[2] || "00", t);
    if (loose) {
      var only = t.match(/^\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*$/);
      if (only) return finishTime(only[1], only[2] || "00", only[3] || "");
    }
    return "";
  }

  function parseDate(text, loose, now) {
    var t = lower(text);
    var today = now ? new Date(now) : new Date();
    today.setHours(0, 0, 0, 0);
    if (/\btoday\b/.test(t) || t.indexOf("ዛሬ") >= 0) return isoDate(today);
    if (/\btomorrow\b/.test(t) || t.indexOf("ነገ") >= 0) return isoDate(addDays(today, 1));
    var ahead = t.match(/\bin\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\b/);
    if (ahead) return isoDate(addDays(today, wordToNum(ahead[1])));
    if (/\bnext week\b/.test(t)) return isoDate(addDays(today, 7));
    var days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
    for (var i = 0; i < days.length; i++) {
      if (t.indexOf(days[i]) >= 0) {
        var diff = (i - today.getDay() + 7) % 7;
        if (diff === 0) diff = 7;
        return isoDate(addDays(today, diff));
      }
    }
    var iso = t.match(/\b(20\d{2})-(\d{1,2})-(\d{1,2})\b/);
    if (iso) return iso[1] + "-" + String(iso[2]).padStart(2, "0") + "-" + String(iso[3]).padStart(2, "0");
    var dmy = t.match(/\b(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b/);
    var mdy = t.match(/\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?\b/);
    if (dmy || mdy) {
      var day = dmy ? Number(dmy[1]) : Number(mdy[2]);
      var month = dmy ? MONTHS[dmy[2]] : MONTHS[mdy[1]];
      var year = today.getFullYear();
      var candidate = new Date(year, month - 1, day);
      candidate.setHours(0, 0, 0, 0);
      if (candidate < today) candidate = new Date(year + 1, month - 1, day);
      return isoDate(candidate);
    }
    var dayWord = t.match(/\b(?:the\s+)?(\d{1,2})(?:st|nd|rd|th)\b/);
    var looseDay = loose ? t.match(/^\s*(\d{1,2})(?:st|nd|rd|th)?\s*$/) : null;
    var picked = dayWord || looseDay;
    if (picked) {
      var n = Number(picked[1]);
      if (n >= 1 && n <= 31) {
        var chosen = new Date(today.getFullYear(), today.getMonth(), n);
        chosen.setHours(0, 0, 0, 0);
        if (chosen < today) chosen = new Date(today.getFullYear(), today.getMonth() + 1, n);
        return isoDate(chosen);
      }
    }
    return "";
  }

  function extractDept(text) {
    var t = lower(text);
    for (var i = 0; i < DEPTS.length; i++) {
      var names = DEPTS[i][1];
      for (var j = 0; j < names.length; j++) {
        if (t.indexOf(names[j]) >= 0) return DEPTS[i][0];
      }
    }
    return "";
  }

  function extractDoctor(text) {
    var t = lower(text);
    for (var i = 0; i < DOCTORS.length; i++) {
      var parts = DOCTORS[i].toLowerCase().replace("dr. ", "").split(" ");
      if (parts.some(function (part) { return part.length > 2 && t.indexOf(part) >= 0; })) return DOCTORS[i];
    }
    return "";
  }

  function unknownDoctor(text) {
    var m = lower(text).match(/\b(?:dr|doctor)\s+([a-z]+)\b/);
    if (!m) return false;
    var skip = { tomorrow: 1, today: 1, please: 1, for: 1, on: 1, at: 1, appointment: 1, the: 1 };
    if (skip[m[1]]) return false;
    return !extractDoctor(text);
  }

  function extractReason(text) {
    var m = String(text || "").match(/\b(?:because|reason is)\s+(.+)$/i);
    if (!m) return "";
    var reason = clean(m[1]);
    if (!reason || parseDate(reason) || extractDept(reason)) return "";
    return reason.slice(0, 180);
  }

  function wantsBook(text) {
    var t = lower(text);
    if (/ቀጠሮ/.test(text) && /(ያዝ|ይያዙ|እፈልጋለሁ|መያዝ|አስይዝ)/.test(text)) return true;
    if (/\bhow do i book\b/.test(t) || (/\b(can you|could you)\b/.test(t) && /\bbook\b/.test(t))) return true;
    if (/\b(book|schedule)\b/.test(t) && /\b(appointment|doctor|visit)\b/.test(t)) return true;
    if (/\b(make|request)\b/.test(t) && /\bappointment\b/.test(t)) return true;
    if (/\b(see|need)\b/.test(t) && /\ba doctor\b/.test(t) && !/\b(said|told)\b/.test(t)) return true;
    return false;
  }

  function wantsCancel(text) {
    var t = lower(text);
    if (/\bhow do i cancel\b/.test(t)) return true;
    if (/(ሰርዝ|ሰርዙ|መሰረዝ)/.test(text) && /ቀጠሮ/.test(text)) return true;
    return /\b(cancel|call off)\b/.test(t) && /\b(appointment|booking)\b/.test(t);
  }

  function wantsReschedule(text) {
    var t = lower(text);
    return /\b(reschedule|move|change)\b/.test(t) && /\bappointment\b/.test(t);
  }

  function wantsList(text) {
    var t = lower(text);
    if (/\b(open|go to)\b/.test(t)) return false;
    if (/ቀጠሮዎቼ/.test(text)) return true;
    return /\b(my appointments|upcoming appointment|what appointments|which appointments|list appointments|show appointments|show my appointment)\b/.test(t);
  }

  function wantsBills(text) {
    var t = lower(text);
    if (/\b(open|go to)\b/.test(t) && /\bbills?\b/.test(t)) return false;
    return /\b(my bills?|what do i owe|outstanding|invoice|unpaid)\b/.test(t) || (/\bbills?\b/.test(t) && /\b(show|check|read|what|how much)\b/.test(t));
  }

  function wantsComplaint(text) {
    var t = lower(text);
    if (/\b(what is|how do i|how to)\b/.test(t)) return false;
    return /\bcomplaint\b/.test(t) && /\b(file|submit|make|send|lodge|about)\b/.test(t);
  }

  function wantsMessages(text) {
    var t = lower(text);
    if (/\b(how do i|how to|what is)\b/.test(t)) return false;
    return /\b(my messages|inbox)\b/.test(t) || (/\bmessages\b/.test(t) && /\b(read|show|check|any)\b/.test(t));
  }

  function pageTarget(text) {
    var t = lower(text);
    if (!/\b(open|go to|take me to|show me the)\b/.test(t)) return null;
    var pages = [
      ["health card", "patient/health-card.html", "health card"],
      ["record", "patient/records.html", "medical records"],
      ["complaint", "patient/complaints.html", "complaints"],
      ["message", "patient/messages.html", "messages"],
      ["setting", "patient/settings.html", "settings"],
      ["profile", "patient/settings.html", "settings"],
      ["video", "patient/videos.html", "health videos"],
      ["appointment", "patient/appointments.html", "appointments"],
      ["bill", "patient/bills.html", "bills"]
    ];
    for (var i = 0; i < pages.length; i++) {
      if (t.indexOf(pages[i][0]) >= 0) return { path: pages[i][1], label: pages[i][2] };
    }
    return null;
  }

  function isSpeechRefusal(text) {
    return /cannot speak|can't speak|can not speak|unable to (speak|talk)|do not have (a )?voice|don't have (a )?voice|cannot produce audio|can't produce audio|cannot generate audio|no audio capability|text-only|text only/i.test(String(text || ""));
  }

  function prepare(text) {
    var raw = clean(text);
    var t = lower(raw);
    var asks = (
      /\b(respond|reply|answer|speak|talk|tell|read|say)\b[\s\S]{0,48}\b(voice|audio|aloud|out loud)\b/.test(t) ||
      /\b(voice|audio)\b[\s\S]{0,32}\b(respond|reply|answer|response)\b/.test(t) ||
      /\b(speak to me|read (it|this|that|the answer)( to me)?|say it out loud)\b/.test(t) ||
      /በድምፅ|በድምጽ/.test(raw)
    );
    if (!asks) return { speak: false, question: raw, repeat: false };
    var question = raw
      .replace(/\b(?:please\s+)?(?:can you\s+|could you\s+|i ask(?:ed)?(?: you)? to\s+)?(?:respond|reply|answer|speak|talk|tell me|read(?:\s+(?:it|this|that|the answer))?|say(?:\s+it)?)\s+(?:to me\s+|me\s+|the answer\s+)?(?:by|with|in|using|via)\s+(?:a\s+)?(?:voice|audio|speech)\b/ig, " ")
      .replace(/\b(?:by|with|in|using)\s+(?:a\s+)?(?:voice|audio|speech)\b/ig, " ")
      .replace(/\bvoice\s+(?:response|reply|answer)\b/ig, " ")
      .replace(/\b(?:speak to me|read (?:it|this|that|the answer)(?: to me)?|say it out loud|out loud|aloud)\b/ig, " ")
      .replace(/በድምፅ(?:\s*መልስልኝ|\s*መልስ)?|በድምጽ(?:\s*ንገረኝ)?/g, " ")
      .replace(/\b(?:and|also|then|but)\b\s*$/i, " ")
      .replace(/\s+/g, " ")
      .replace(/^[\s,.;:?!-]+|[\s,.;:?!-]+$/g, "")
      .trim();
    return { speak: true, question: question, repeat: question.length < 8 };
  }

  function detectIntent(text) {
    if (wantsCancel(text)) return "cancel";
    if (wantsReschedule(text)) return "reschedule";
    if (wantsBook(text)) return "book";
    if (wantsList(text)) return "list";
    if (wantsBills(text)) return "bills";
    if (wantsComplaint(text)) return "complaint";
    if (wantsMessages(text)) return "messages";
    if (pageTarget(text)) return "open";
    if (/^(hi|hello|hey|good morning|good afternoon|good evening)\b/.test(lower(text)) && clean(text).length < 40) return "hello";
    return "";
  }

  function answered(text, askMore) {
    return { handled: true, reply: text, askMore: !!askMore };
  }

  function missed() {
    return { handled: false };
  }

  function deptQuestion() {
    return tr(
      "Which department? You can say Internal Medicine, Pediatrics, Cardiology, Maternity, or Orthopedics.",
      "የትኛው ክፍል? የውስጥ ሕክምና፣ የሕፃናት፣ የልብ፣ የወሊድ፣ ወይም የአጥንት ይበሉ።"
    );
  }

  function dateQuestion() {
    return tr("What date should I book? You can say tomorrow, a weekday, or a date.", "የትኛው ቀን ልይዝልዎ? ነገ፣ የሳምንቱ ቀን፣ ወይም ቀን ይበሉ።");
  }

  function timeQuestion() {
    return tr("What time? For example, 9 in the morning or 2 in the afternoon.", "ስንት ሰዓት? ለምሳሌ ጧት 9 ወይም ከሰዓት 2።");
  }

  function doctorQuestion() {
    return "I can book with " + DOCTORS.join(", ") + ". Which doctor?";
  }

  function emergencyNote(text) {
    var t = lower(text);
    var red = ["chest pain", "can't breathe", "cannot breathe", "unconscious", "seizure", "heavy bleeding", "stroke"];
    for (var i = 0; i < red.length; i++) {
      if (t.indexOf(red[i]) >= 0) return "If this is an emergency, go to the Emergency Department or call 907. ";
    }
    return "";
  }

  function slotsFrom(text, base, looseTime, looseDate) {
    var slots = {
      dept: base && base.dept || "",
      date: base && base.date || "",
      time: base && base.time || "",
      doctor: base && base.doctor || "",
      reason: base && base.reason || ""
    };
    var dept = extractDept(text);
    var date = parseDate(text, !!looseDate);
    var time = parseTime(text, !!looseTime);
    var doctor = extractDoctor(text);
    var reason = extractReason(text);
    if (dept) slots.dept = dept;
    if (date) slots.date = date;
    if (time) slots.time = time;
    if (doctor) {
      slots.doctor = doctor;
      slots.doctorChosen = true;
    }
    if (reason) slots.reason = reason;
    return slots;
  }

  function describe(row) {
    return (row.dept || "Appointment") + " with " + (row.doctor || "the hospital doctor") + " on " + speakDate(row.date) + " at " + speakTime(row.time);
  }

  function isOpen(row) {
    var status = lower(row && row.status);
    return status !== "cancelled" && status !== "completed" && status !== "attended";
  }

  function itemsOf(res) {
    if (!res || !res.ok || !res.data) return null;
    return res.data.items || [];
  }

  function call(endpoint, method, body) {
    if (typeof apiFetch !== "function") return Promise.resolve({ ok: false, error: "The hospital connection is not ready." });
    return apiFetch(endpoint, method || "GET", body || null, { quiet: true });
  }

  function endpoint(name) {
    var map = (root.CONFIG && root.CONFIG.ENDPOINTS) || {};
    return map[name] || ("/" + name.toLowerCase());
  }

  function saveFailed() {
    return tr("I could not save that. The hospital database did not accept it. Nothing was changed.", "ማስቀመጥ አልተቻለም። የሆስፒታሉ መረጃ አልተቀበለውም። ምንም አልተቀየረም።");
  }

  function saveBook(slots, original) {
    return call(endpoint("APPOINTMENTS")).then(function (res) {
      if (!res || !res.ok) return answered("I could not read your appointments, so I did not book a new one.");
      var items = itemsOf(res) || [];
      var same = items.filter(isOpen).filter(function (row) {
        return lower(row.dept) === lower(slots.dept) && String(row.date || "").slice(0, 10) === slots.date && String(row.time || "").slice(0, 5) === slots.time;
      });
      if (same.length) {
        pending = null;
        return answered("That appointment is already booked: " + describe(same[0]) + ".");
      }
      var row = {
        id: typeof uid === "function" ? uid("A") : ("A-" + Date.now().toString(36)),
        patient: typeof getUserName === "function" ? getUserName() : "",
        doctor: slots.doctor || DOCTORS[0],
        dept: slots.dept,
        date: slots.date,
        time: slots.time,
        type: "Consultation",
        status: "confirmed",
        reason: slots.reason || ""
      };
      return call(endpoint("APPOINTMENTS"), "POST", row).then(function (saved) {
        if (!saved || !saved.ok) return answered(saveFailed());
        pending = null;
        var assigned = row.doctor === DOCTORS[0] && !(original && extractDoctor(original)) ? " I assigned " + row.doctor + "." : "";
        return answered(emergencyNote(original || "") + "I booked " + describe(row) + "." + assigned + " It is saved in your appointments.");
      });
    });
  }

  function continueBook(text) {
    if (unknownDoctor(text)) {
      pending.slots = slotsFrom(text, pending.slots, pending.ask === "time", pending.ask === "date");
      pending.ask = "doctor";
      return Promise.resolve(answered(doctorQuestion(), true));
    }
    var slots = slotsFrom(text, pending.slots, pending.ask === "time", pending.ask === "date");
    pending.slots = slots;
    if (!slots.dept) {
      pending.ask = "dept";
      return Promise.resolve(answered(deptQuestion(), true));
    }
    if (!slots.date) {
      pending.ask = "date";
      return Promise.resolve(answered(dateQuestion(), true));
    }
    if (!slots.time) {
      pending.ask = "time";
      return Promise.resolve(answered(timeQuestion(), true));
    }
    if (!slots.doctor) slots.doctor = DOCTORS[0];
    return saveBook(slots, text);
  }

  function chooseIndex(text, count) {
    var words = ["first", "second", "third", "fourth", "fifth"];
    var t = lower(text);
    for (var i = 0; i < words.length && i < count; i++) {
      if (t.indexOf(words[i]) >= 0) return i;
    }
    var m = t.match(/^\s*(?:number|no|#)?\s*(\d+)\s*$/);
    if (m) {
      var n = Number(m[1]);
      if (n >= 1 && n <= count) return n - 1;
    }
    return -1;
  }

  function narrow(items, text) {
    var dept = extractDept(text);
    var doctor = extractDoctor(text);
    var date = parseDate(text, false);
    var time = parseTime(text, false);
    return items.filter(function (row) {
      if (dept && lower(row.dept) !== lower(dept)) return false;
      if (doctor && lower(row.doctor) !== lower(doctor)) return false;
      if (date && String(row.date || "").slice(0, 10) !== date) return false;
      if (time && String(row.time || "").slice(0, 5) !== time) return false;
      return !!(dept || doctor || date || time);
    });
  }

  function listText(items) {
    if (!items.length) return tr("You have no open appointments.", "ክፍት ቀጠሮ የለዎትም።");
    var lines = items.slice(0, 5).map(function (row, i) { return (i + 1) + ". " + describe(row); });
    var more = items.length > 5 ? " I am showing the first 5 of " + items.length + "." : "";
    return "You have " + items.length + " open appointment" + (items.length === 1 ? "" : "s") + ". " + lines.join(" ") + more;
  }

  function loadOpen() {
    return call(endpoint("APPOINTMENTS")).then(function (res) {
      var items = itemsOf(res);
      if (items === null) return { error: saveFailed().replace("Nothing was changed.", "I could not read your appointments.") };
      return { items: items.filter(isOpen) };
    });
  }

  function cancelRow(row) {
    var next = {};
    Object.keys(row || {}).forEach(function (key) { next[key] = row[key]; });
    next.status = "cancelled";
    return call(endpoint("APPOINTMENTS") + "/" + encodeURIComponent(row.id), "PUT", next).then(function (saved) {
      if (!saved || !saved.ok) return answered(saveFailed());
      pending = null;
      return answered("I cancelled " + describe(row) + ". It is saved as cancelled.");
    });
  }

  function startCancel(text) {
    return loadOpen().then(function (found) {
      if (found.error) return answered(found.error);
      var open = found.items;
      if (!open.length) {
        pending = null;
        return answered(tr("You have no open appointment to cancel.", "የሚሰረዝ ክፍት ቀጠሮ የለም።"));
      }
      var picked = narrow(open, text);
      var index = pending && pending.choices ? chooseIndex(text, pending.choices.length) : -1;
      var row = null;
      if (index >= 0 && pending && pending.choices) row = pending.choices[index];
      else if (picked.length === 1) row = picked[0];
      else if (!picked.length && open.length === 1 && !extractDept(text) && !parseDate(text, false)) row = open[0];
      if (!row) {
        var choices = picked.length > 1 ? picked : open;
        pending = { kind: "cancel", choices: choices };
        return answered(listText(choices) + " Say the number to cancel, for example number 1.", true);
      }
      return cancelRow(row);
    });
  }

  function rescheduleRow(row, date, time) {
    var next = {};
    Object.keys(row || {}).forEach(function (key) { next[key] = row[key]; });
    if (date) next.date = date;
    if (time) next.time = time;
    return call(endpoint("APPOINTMENTS") + "/" + encodeURIComponent(row.id), "PUT", next).then(function (saved) {
      if (!saved || !saved.ok) return answered(saveFailed());
      pending = null;
      return answered("I rescheduled it to " + describe(next) + ". The change is saved.");
    });
  }

  function startReschedule(text) {
    return loadOpen().then(function (found) {
      if (found.error) return answered(found.error);
      var open = found.items;
      if (!open.length) return answered("You have no open appointment to reschedule.");
      var choices = pending && pending.kind === "reschedule" && pending.choices ? pending.choices : open;
      var index = chooseIndex(text, choices.length);
      var picked = narrow(open, text);
      var row = pending && pending.row ? pending.row : null;
      if (!row && index >= 0) row = choices[index];
      if (!row && picked.length === 1) row = picked[0];
      if (!row && open.length === 1) row = open[0];
      if (!row) {
        pending = { kind: "reschedule", choices: picked.length ? picked : open };
        return answered(listText(pending.choices) + " Say the number, then the new date and time.", true);
      }
      var date = parseDate(text, pending && pending.ask === "when") || (pending && pending.date) || "";
      var time = parseTime(text, pending && pending.ask === "when") || (pending && pending.time) || "";
      if (!date && !time) {
        pending = { kind: "reschedule", row: row, ask: "when" };
        return answered("What date and time should I move " + describe(row) + " to?", true);
      }
      return rescheduleRow(row, date || String(row.date || "").slice(0, 10), time || String(row.time || "").slice(0, 5));
    });
  }

  function readBills() {
    return call(endpoint("BILLS")).then(function (res) {
      var items = itemsOf(res);
      if (items === null) return answered("I could not read your bills. Nothing was changed.");
      if (!items.length) return answered("You have no bills on file.");
      var unpaid = items.filter(function (row) {
        var status = lower(row.status);
        return status !== "paid" && status !== "void";
      });
      if (!unpaid.length) return answered("Your bills are marked paid. I found " + items.length + " bill" + (items.length === 1 ? "" : "s") + ".");
      var total = 0;
      var known = true;
      var lines = unpaid.slice(0, 4).map(function (row) {
        var amount = Number(row.amount);
        if (!isFinite(amount)) known = false;
        else total += amount;
        var label = row.description || row.service || "Bill";
        return label + " for " + (isFinite(amount) ? amount : "an unstated amount") + ", status " + (row.status || "open");
      });
      var sum = known ? " The unpaid total is " + total + "." : "";
      return answered("You have " + unpaid.length + " unpaid bill" + (unpaid.length === 1 ? "" : "s") + "." + sum + " " + lines.join(". ") + ". To pay, say open bills and choose a bank or wallet. I will not ask for a PIN or card number.");
    });
  }

  function complaintCategory(text) {
    var t = lower(text);
    if (/\bbill/.test(t)) return "Billing";
    if (/\b(staff|rude|nurse|doctor)\b/.test(t)) return "Staff Conduct";
    if (/\b(clean|dirt|toilet|facility)\b/.test(t)) return "Facility / Cleanliness";
    if (/\b(treatment|care|pain)\b/.test(t)) return "Treatment / Care";
    if (/\b(wait|queue|appointment)\b/.test(t)) return "Appointment";
    if (/\b(service|slow)\b/.test(t)) return "Service Quality";
    return "Other";
  }

  function saveComplaint(text) {
    var subject = clean(text).replace(/^(please\s+)?(file|submit|make|send|lodge)\s+(a\s+)?complaint\s*(about)?\s*/i, "");
    subject = clean(subject) || clean(text);
    if (subject.length < 8) {
      pending = { kind: "complaint" };
      return Promise.resolve(answered("What is the complaint about? Say it in one sentence.", true));
    }
    var row = {
      id: typeof uid === "function" ? uid("C") : ("C-" + Date.now().toString(36)),
      category: complaintCategory(text),
      subject: subject.slice(0, 80),
      description: clean(text).slice(0, 500),
      priority: "normal",
      date: isoDate(new Date()),
      status: "pending"
    };
    return call(endpoint("COMPLAINTS"), "POST", row).then(function (saved) {
      if (!saved || !saved.ok) return answered(saveFailed());
      pending = null;
      return answered("I filed your complaint under " + row.category + ": " + row.subject + ". It is saved as pending for the General Manager.");
    });
  }

  function readMessages() {
    return call(endpoint("MESSAGES")).then(function (res) {
      var items = itemsOf(res);
      if (items === null) return answered("I could not read your messages.");
      if (!items.length) return answered("You have no messages.");
      var lines = items.slice(0, 3).map(function (row) {
        return (row.from || "Someone") + " sent " + (row.subject || "a message") + (row.date ? " on " + row.date : "");
      });
      return answered("You have " + items.length + " message" + (items.length === 1 ? "" : "s") + ". " + lines.join(". ") + ".");
    });
  }

  function openHospitalPage(text) {
    var target = pageTarget(text);
    if (!target) return missed();
    var reply = "Opening your " + target.label + ".";
    setTimeout(function () {
      if (root.document && root.document.getElementById("spaBody")) root.location.hash = target.path;
      else root.location.href = target.path.split("/").pop();
    }, 700);
    return answered(reply);
  }

  function tryAction(text) {
    var said = clean(text);
    var t = lower(said);
    if (!said) return Promise.resolve(missed());
    if (pending && /^(cancel|stop|never mind|forget it|start over)$/.test(t)) {
      pending = null;
      return Promise.resolve(answered("Stopped. Nothing was changed."));
    }
    var intent = detectIntent(said);
    if (intent === "hello" && !pending) {
      return Promise.resolve(answered(tr(
        "Hello. I can book an appointment, cancel an appointment, read your bills, file a complaint, or explain the hospital system. What should I do?",
        "ሰላም። ቀጠሮ መያዝ፣ ቀጠሮ መሰረዝ፣ ሂሳብ ማንበብ፣ ቅሬታ ማቅረብ፣ ወይም ስለ ሆስፒታሉ ማብራራት እችላለሁ። ምን ላድርግ?"
      ), true));
    }
    if (intent && intent !== "hello" && !(pending && !intent)) {
      if (intent === "book") {
        pending = { kind: "book", slots: {}, ask: "" };
        return continueBook(said);
      }
      if (intent === "cancel") return startCancel(said);
      if (intent === "reschedule") {
        pending = { kind: "reschedule" };
        return startReschedule(said);
      }
      if (intent === "list") {
        pending = null;
        return loadOpen().then(function (found) {
          return answered(found.error || listText(found.items));
        });
      }
      if (intent === "bills") {
        pending = null;
        return readBills();
      }
      if (intent === "complaint") return saveComplaint(said);
      if (intent === "messages") {
        pending = null;
        return readMessages();
      }
      if (intent === "open") {
        pending = null;
        return Promise.resolve(openHospitalPage(said));
      }
    }
    if (pending && pending.kind === "book") return continueBook(said);
    if (pending && pending.kind === "cancel") return startCancel(said);
    if (pending && pending.kind === "reschedule") return startReschedule(said);
    if (pending && pending.kind === "complaint") return saveComplaint(said);
    return Promise.resolve(missed());
  }

  function stripSpeak(text) {
    return clean(String(text || "").replace(/<[^>]+>/g, " ")).slice(0, 500);
  }

  function remember(text) {
    var line = stripSpeak(text);
    if (!line || isSpeechRefusal(line)) return;
    spokenAnswer = line;
  }

  function speak(text, thenListen) {
    var line = stripSpeak(text);
    if (!line || isSpeechRefusal(line)) line = spokenAnswer;
    if (!soundOn || !line) {
      if (thenListen) setTimeout(startListen, 300);
      return false;
    }
    if (!root.speechSynthesis || !root.SpeechSynthesisUtterance) {
      if (typeof showToast === "function") showToast("This browser cannot play speech. The answer is written in the chat.", "info");
      return false;
    }
    try { root.speechSynthesis.resume(); } catch (e) { /* ignore */ }
    try { root.speechSynthesis.cancel(); } catch (e) { /* ignore */ }
    var voice = new root.SpeechSynthesisUtterance(line);
    voice.lang = tr("en-US", "am-ET");
    voice.rate = 1;
    var voices = [];
    try { voices = root.speechSynthesis.getVoices() || []; } catch (e) { voices = []; }
    var wanted = tr("en", "am");
    var picked = voices.filter(function (item) { return String(item.lang || "").toLowerCase().indexOf(wanted) === 0; })[0];
    if (picked) voice.voice = picked;
    voice.onend = function () { if (thenListen) startListen(); };
    voice.onerror = function () {
      if (typeof showToast === "function") showToast("Turn the device volume up, tap Sound on, and ask again.", "info");
    };
    setTimeout(function () {
      try { root.speechSynthesis.resume(); } catch (e) { /* ignore */ }
      root.speechSynthesis.speak(voice);
    }, 80);
    return true;
  }

  function prime(force) {
    if (force) soundOn = true;
    if (!soundOn || !root.speechSynthesis || !root.SpeechSynthesisUtterance) return;
    try { root.speechSynthesis.resume(); } catch (e) { /* ignore */ }
    try {
      var unlock = new root.SpeechSynthesisUtterance(" ");
      unlock.volume = 0.01;
      unlock.rate = 2;
      root.speechSynthesis.speak(unlock);
    } catch (e) { /* ignore */ }
  }

  var MIC_ICON = "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><path d=\"M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z\"/><path d=\"M19 10v2a7 7 0 0 1-14 0v-2\"/><path d=\"M12 19v3\"/></svg>";
  var STOP_ICON = "<svg viewBox=\"0 0 24 24\" fill=\"currentColor\" aria-hidden=\"true\"><rect x=\"6\" y=\"6\" width=\"12\" height=\"12\" rx=\"2\"/></svg>";
  var PLAY_ICON = "<svg viewBox=\"0 0 24 24\" fill=\"currentColor\" aria-hidden=\"true\"><polygon points=\"7 4 20 12 7 20 7 4\"/></svg>";
  var SOUND_ON_ICON = "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><polygon points=\"11 5 6 9 2 9 2 15 6 15 11 19 11 5\"/><path d=\"M15.54 8.46a5 5 0 0 1 0 7.07\"/><path d=\"M19.07 4.93a10 10 0 0 1 0 14.14\"/></svg>";
  var SOUND_OFF_ICON = "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\"><polygon points=\"11 5 6 9 2 9 2 15 6 15 11 19 11 5\"/><line x1=\"22\" y1=\"9\" x2=\"16\" y2=\"15\"/><line x1=\"16\" y1=\"9\" x2=\"22\" y2=\"15\"/></svg>";
  var playingButton = null;

  function setSpeakLabel() {
    var btn = root.document && root.document.getElementById("btnSpeak");
    if (!btn) return;
    btn.innerHTML = listening ? STOP_ICON : MIC_ICON;
    btn.classList.toggle("listening", listening);
    btn.setAttribute("aria-label", listening ? tr("Stop listening", "ማዳመጥ አቁም") : tr("Speak", "ተናገር"));
    btn.setAttribute("aria-pressed", listening ? "true" : "false");
  }

  function setSoundLabel() {
    var btn = root.document && root.document.getElementById("btnVoiceSound");
    if (!btn) return;
    btn.innerHTML = soundOn ? SOUND_ON_ICON : SOUND_OFF_ICON;
    btn.setAttribute("aria-label", soundOn ? tr("Sound on", "ድምፅ በርቷል") : tr("Sound off", "ድምፅ ጠፍቷል"));
    btn.setAttribute("aria-pressed", soundOn ? "true" : "false");
  }

  function clearPlaying() {
    if (!playingButton) return;
    playingButton.classList.remove("playing");
    playingButton.innerHTML = PLAY_ICON;
    playingButton = null;
  }

  function playThis(source, btn) {
    var line = source;
    if (source && source.cloneNode) {
      var copy = source.cloneNode(true);
      var times = copy.querySelectorAll ? copy.querySelectorAll(".msg-time") : [];
      for (var i = 0; i < times.length; i++) times[i].remove();
      line = copy.textContent;
    }
    line = stripSpeak(line);
    if (!line) return false;
    if (btn && btn.classList.contains("playing")) {
      if (root.speechSynthesis) root.speechSynthesis.cancel();
      clearPlaying();
      return false;
    }
    if (!root.speechSynthesis || !root.SpeechSynthesisUtterance) {
      if (typeof showToast === "function") showToast("This browser cannot play speech. The answer is written in the chat.", "info");
      return false;
    }
    clearPlaying();
    try { root.speechSynthesis.resume(); } catch (e) { /* ignore */ }
    try { root.speechSynthesis.cancel(); } catch (e) { /* ignore */ }
    var voice = new root.SpeechSynthesisUtterance(line);
    voice.lang = tr("en-US", "am-ET");
    voice.rate = 1;
    var voices = [];
    try { voices = root.speechSynthesis.getVoices() || []; } catch (e) { voices = []; }
    var wanted = tr("en", "am");
    var picked = voices.filter(function (item) { return String(item.lang || "").toLowerCase().indexOf(wanted) === 0; })[0];
    if (picked) voice.voice = picked;
    voice.onend = function () { if (playingButton === btn) clearPlaying(); };
    voice.onerror = function () {
      clearPlaying();
      if (typeof showToast === "function") showToast("Turn the device volume up and tap play again.", "info");
    };
    if (btn) {
      playingButton = btn;
      btn.classList.add("playing");
      btn.innerHTML = STOP_ICON;
    }
    setTimeout(function () {
      try { root.speechSynthesis.resume(); } catch (e) { /* ignore */ }
      root.speechSynthesis.speak(voice);
    }, 60);
    return true;
  }

  function playButton(source) {
    var btn = root.document.createElement("button");
    btn.type = "button";
    btn.className = "voice-play";
    btn.setAttribute("aria-label", tr("Play response", "መልሱን አጫውት"));
    btn.innerHTML = PLAY_ICON;
    btn.onclick = function () { playThis(source, btn); };
    return btn;
  }

  function stopListen() {
    suppressSend = true;
    if (recognition && listening) {
      try { recognition.stop(); } catch (e) { /* ignore */ }
    }
  }

  function startListen() {
    var Rec = root.SpeechRecognition || root.webkitSpeechRecognition;
    var input = root.document && root.document.getElementById("chatInput");
    if (!Rec) {
      if (typeof showToast === "function") showToast("This browser cannot hear speech. Type the request, or open the page in Chrome.", "info");
      return;
    }
    if (listening && recognition) {
      suppressSend = false;
      try { recognition.stop(); } catch (e) { /* ignore */ }
      return;
    }
    recognition = new Rec();
    recognition.lang = tr("en-US", "am-ET");
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    suppressSend = false;
    recognition.onresult = function (event) {
      var said = "";
      for (var i = event.resultIndex; i < event.results.length; i++) said += event.results[i][0].transcript;
      if (input) input.value = clean(said);
    };
    recognition.onerror = function (event) {
      var code = event && event.error;
      if (code === "not-allowed" && typeof showToast === "function") showToast("Allow the microphone, then tap Speak again.", "error");
      else if (code === "network" && typeof showToast === "function") showToast("Speech recognition needs a network connection.", "info");
    };
    recognition.onend = function () {
      listening = false;
      setSpeakLabel();
      var said = input ? clean(input.value) : "";
      if (!suppressSend && said && typeof root.sendMsg === "function") root.sendMsg(true);
    };
    try {
      recognition.start();
      listening = true;
      soundOn = true;
      setSpeakLabel();
      setSoundLabel();
    } catch (e) {
      listening = false;
      setSpeakLabel();
    }
  }

  function mount() {
    if (!root.document || root.document.getElementById("btnSpeak")) return;
    var input = root.document.getElementById("chatInput");
    if (!input || !input.parentNode) return;
    if (!root.document.getElementById("voice-assistant-style")) {
      var style = root.document.createElement("style");
      style.id = "voice-assistant-style";
      style.textContent = "#btnSpeak,#btnVoiceSound,.voice-play{width:42px;height:42px;min-width:42px;padding:0;display:inline-flex;align-items:center;justify-content:center;border-radius:10px;background:#fff !important;color:#06141B !important;border:1px solid #9AA6AC !important}#btnSpeak svg,#btnVoiceSound svg,.voice-play svg{width:20px;height:20px;display:block}#btnSpeak.listening,.voice-play.playing{background:#1A6FA8 !important;color:#fff !important;border-color:#1A6FA8 !important}.chat-msg.ai.has-play{display:flex;align-items:flex-start;gap:8px}.chat-msg.ai.has-play .voice-msg-body{flex:1;min-width:0}.voice-chip{background:#fff !important;color:#06141B !important;border:1px solid #9AA6AC !important;font-weight:700;border-radius:999px;padding:6px 10px;cursor:pointer}.voice-subtitle{color:#06141B}html[data-theme=\"dark\"] .voice-subtitle{color:#F4F7F8}";
      root.document.head.appendChild(style);
    }
    var speak = root.document.createElement("button");
    speak.type = "button";
    speak.className = "btn";
    speak.id = "btnSpeak";
    speak.onclick = startListen;
    var sound = root.document.createElement("button");
    sound.type = "button";
    sound.className = "btn";
    sound.id = "btnVoiceSound";
    sound.onclick = function () {
      soundOn = !soundOn;
      if (!soundOn && root.speechSynthesis) root.speechSynthesis.cancel();
      setSoundLabel();
    };
    input.parentNode.style.flexWrap = "wrap";
    input.style.flex = "1";
    input.style.minWidth = "160px";
    input.parentNode.insertBefore(speak, input);
    input.parentNode.insertBefore(sound, input);
    input.placeholder = "Type a question, or use the microphone";
    var hints = root.document.createElement("div");
    hints.id = "voiceHints";
    hints.style.cssText = "display:flex;gap:8px;flex-wrap:wrap;padding:8px 12px 0";
    ["Book an appointment", "Cancel my appointment", "Show my appointments", "What are my bills?"].forEach(function (label) {
      var chip = root.document.createElement("button");
      chip.type = "button";
      chip.className = "voice-chip";
      chip.textContent = label;
      chip.onclick = function () {
        input.value = label;
        if (typeof root.sendMsg === "function") root.sendMsg(false);
      };
      hints.appendChild(chip);
    });
    var area = root.document.getElementById("chatArea");
    if (area && area.parentNode) area.parentNode.insertBefore(hints, area.nextSibling);
    setSpeakLabel();
    setSoundLabel();
  }

  function reset() {
    pending = null;
    suppressSend = true;
    listening = false;
    if (recognition) {
      try { recognition.stop(); } catch (e) { /* ignore */ }
    }
    if (root.speechSynthesis) {
      try { root.speechSynthesis.cancel(); } catch (e) { /* ignore */ }
    }
  }

  function afterReply(text, fromVoice, askMore) {
    if (fromVoice) soundOn = true;
    remember(text);
    setSoundLabel();
    var said = speak(text, !!(askMore && fromVoice));
    if (fromVoice && !said && isSpeechRefusal(text)) {
      if (typeof showToast === "function") showToast("I will read the answer aloud. Ask the question again if nothing plays.", "info");
    }
  }

  var api = {
    tryAction: tryAction,
    playButton: playButton,
    prepare: prepare,
    remember: remember,
    lastAnswer: function () { return spokenAnswer; },
    prime: prime,
    mount: mount,
    reset: reset,
    stopListen: stopListen,
    afterReply: afterReply,
    parseDate: parseDate,
    parseTime: parseTime,
    extractDept: extractDept,
    extractDoctor: extractDoctor,
    detectIntent: detectIntent,
    doctors: DOCTORS
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root && root.document) root.VoiceAssistant = api;
})(typeof window !== "undefined" ? window : globalThis);
