/* ============================================================
   Wolaita Sodo Hospital — api.js
   Fetch wrapper. Every read and write goes to the API, which stores
   rows in Supabase. There is no local mock library.
   ============================================================ */

// ---------- Core fetch wrapper ----------
async function apiFetch(endpoint, method = "GET", body = null, opts = {}) {
  const headers = { "Content-Type": "application/json" };
  const session = getSession();
  if (!opts.skipAuth && session && session.token) {
    headers["Authorization"] = "Bearer " + session.token;
  }

  try {
    const res = await fetch(CONFIG.API_BASE_URL + endpoint, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined
    });
    // 401 on an auth request (login/signup/reset) = wrong credentials,
    // not an expired session — let the form display the server's message.
    if (res.status === 401 && !opts.skipAuth) {
      showToast("Your session has expired. Please log in again.", "warning");
      clearSession();
      if (window.SPA && window.SPA.mode) {
        setTimeout(() => window.SPA.showLogin(), 1200);
      } else {
        setTimeout(() => { window.location.href = basePath() + "index.html"; }, 1200);
      }
      return { ok: false, status: 401, error: "Unauthorized" };
    }
    if (res.status === 401 && opts.skipAuth) {
      const d401 = await res.json().catch(() => ({}));
      return { ok: false, status: 401, error: d401.detail || "Invalid email or password" };
    }
    if (res.status === 500) {
      showToast("Server error. Please try again.", "error");
      return { ok: false, status: 500, error: "Server error" };
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, status: res.status, error: data.detail || "Request failed" };
    return { ok: true, data };
  } catch (err) {
    showToast("Network error — cannot reach the server.", "error");
    return { ok: false, error: "Network error" };
  }
}

// Standard AI call pattern with loading state
async function callAI(endpoint, payload, onSuccess) {
  showLoading();
  try {
    await delay(700); // slight delay so the loading state is visible
    const result = await apiFetch(endpoint, "POST", payload);
    if (result.ok) onSuccess(result.data);
    else showToast(result.error || "AI service unavailable. Please try again.", "error");
  } catch (err) {
    showToast("AI service unavailable. Please try again.", "error");
  } finally {
    hideLoading();
  }
}

// ---------- Named AI module functions ----------
const predictDisease     = (payload, cb) => callAI(CONFIG.ENDPOINTS.PREDICT_DISEASE, payload, cb);
const checkDrugInteraction = (payload, cb) => callAI(CONFIG.ENDPOINTS.CHECK_INTERACTION, payload, cb);
const analyzeLabResult   = (payload, cb) => callAI(CONFIG.ENDPOINTS.ANALYZE_LAB, payload, cb);
const checkVitals        = (payload, cb) => callAI(CONFIG.ENDPOINTS.CHECK_VITALS, payload, cb);
const forecastInventory  = (payload, cb) => callAI(CONFIG.ENDPOINTS.FORECAST_INVENTORY, payload, cb);
const predictAppointment = (payload, cb) => callAI(CONFIG.ENDPOINTS.PREDICT_APPOINTMENT, payload, cb);
const symptomChat        = (payload, cb) => callAI(CONFIG.ENDPOINTS.SYMPTOM_CHAT, payload, cb);

// ---------- Helpers ----------
const delay = (ms) => new Promise(r => setTimeout(r, ms));
// ---------- Live YouTube search ----------
// The hospital API searches YouTube and returns playable health videos.
// A browser YouTube key is optional and only used if the API search fails.
const YT_HEALTH_KEYWORDS = ["health", "medical", "doctor", "medicine", "disease", "patient", "care", "treatment", "symptom", "hospital", "clinic", "nutrition", "diet", "wellness", "exercis", "prevent", "hypertension", "diabetes", "asthma", "cancer", "heart", "kidney", "thyroid", "anemia", "pregnancy", "stress", "mental", "tuberculosis", "malaria", "infection", "fever", "cough", "blood", "pain", "weight", "sleep", "vaccin", "therapy", "depression", "anxiety", "smoking", "alcohol", "hygiene", "sanitation", "first aid"];
const YT_BLOCK_KEYWORDS = ["music video", "lyrics", "gameplay", "gaming", "let's play", "trailer", "movie", "prank", "comedy", "stand-up", "sports highlights", "highlights", "reaction", "vlog", "unboxing", "fifa", "minecraft", "dance", "karaoke", "review of phone", "test drive"];
const YT_TRUSTED_CHANNELS = ["mayo clinic", "cleveland clinic", "osmosis", "mass general", "johns hopkins", "nhs", "webmd", "medlineplus", "healthline", "nucleus medical", "medscape", "harvard health", "stanford health", "ted-ed", "med school insiders"];
function isHealthVideo(v) {
  const hay = (v.title + " " + (v.description || "") + " " + v.channel).toLowerCase();
  if (YT_BLOCK_KEYWORDS.some(b => hay.includes(b))) return false;
  if (YT_TRUSTED_CHANNELS.some(t => hay.includes(t))) return true;
  return YT_HEALTH_KEYWORDS.some(k => hay.includes(k));
}
async function searchYouTube(query, maxResults = 12) {
  const q = String(query || "").trim();
  if (!q) return [];
  const viaApi = await apiFetch(CONFIG.ENDPOINTS.VIDEO_SEARCH, "POST", { query: q, max_results: maxResults });
  if (viaApi.ok && viaApi.data && Array.isArray(viaApi.data.items)) return viaApi.data.items;
  if (!CONFIG.YOUTUBE_API_KEY) throw new Error((viaApi && viaApi.error) || "youtube-search-failed");
  const search = q.toLowerCase().includes("health") ? q : q + " health";
  const url = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=" + maxResults +
              "&q=" + encodeURIComponent(search) + "&type=video&videoEmbeddable=true&safeSearch=strict&relevanceLanguage=en&key=" + CONFIG.YOUTUBE_API_KEY;
  const res = await fetch(url);
  if (!res.ok) throw new Error("youtube-api-error");
  const data = await res.json();
  return (data.items || []).map((it, i) => ({
    id: it.id.videoId,
    title: it.snippet.title,
    channel: it.snippet.channelTitle,
    video_id: it.id.videoId,
    url: "https://www.youtube.com/watch?v=" + it.id.videoId,
    search: q,
    conditions: [],
    duration: "—",
    views: "—",
    category: "YouTube",
    description: it.snippet.description || "",
    thumb: it.snippet.thumbnails && it.snippet.thumbnails.high ? it.snippet.thumbnails.high.url : null,
    live: true,
    embeddable: true
  })).filter(isHealthVideo).slice(0, maxResults);
}

function clone(obj) { return JSON.parse(JSON.stringify(obj)); }


let idSeq = 0;
function uid(prefix) {
  idSeq += 1;
  return (prefix || "ID") + "-" + Date.now().toString(36) + idSeq.toString(36);
}

function _saveError(res, action) {
  const msg = (res && res.error) || ("Could not " + action + " in Supabase");
  showToast(msg, "error");
}

function persistInsert(endpoint, row) {
  if (!endpoint || !row) return Promise.resolve({ ok: false, error: "Nothing to save" });
  return apiFetch(endpoint, "POST", row).then(function (res) {
    if (!res.ok) _saveError(res, "save");
    else if (res.data && res.data.row && res.data.row.id) row.id = res.data.row.id;
    return res;
  });
}

function persistUpdate(endpoint, id, row) {
  if (!endpoint || !id) return persistInsert(endpoint, row);
  return apiFetch(endpoint + "/" + encodeURIComponent(id), "PUT", row).then(function (res) {
    if (!res.ok) _saveError(res, "update");
    return res;
  });
}

function persistDelete(endpoint, id) {
  if (!endpoint || !id) return Promise.resolve({ ok: false });
  return apiFetch(endpoint + "/" + encodeURIComponent(id), "DELETE").then(function (res) {
    if (!res.ok) _saveError(res, "delete");
    return res;
  });
}

// Save a row the screen already changed. Shows okMsg only after Supabase accepts it.
function saveRow(endpoint, row, okMsg) {
  if (!endpoint || !row || row.id == null || row.id === "") {
    showToast("This record has no id, so it cannot be saved.", "error");
    return Promise.resolve({ ok: false });
  }
  return persistUpdate(endpoint, row.id, row).then(function (res) {
    if (res && res.ok && okMsg) showToast(okMsg, "success");
    return res;
  });
}

const _known = {};
function persistUpsert(endpoint, row) {
  if (!row) return Promise.resolve({ ok: false });
  const key = endpoint + ":" + row.id;
  if (row.id && _known[key]) return persistUpdate(endpoint, row.id, row);
  if (row.id) _known[key] = true;
  return persistInsert(endpoint, row);
}
function markKnown(endpoint, rows) {
  (rows || []).forEach(function (row) {
    if (row && row.id) _known[endpoint + ":" + row.id] = true;
  });
}

// ---------- Files stored in Supabase ----------
function readUploadFile(file, maxBytes) {
  maxBytes = maxBytes || 1200000;
  return new Promise(function (resolve, reject) {
    if (!file) { resolve(null); return; }
    if (file.size > maxBytes) { reject(new Error("File is too large. Use a file under 1.2 MB.")); return; }
    const reader = new FileReader();
    reader.onload = function () { resolve({ name: file.name, mime: file.type || "application/octet-stream", data: reader.result, size: file.size }); };
    reader.onerror = function () { reject(new Error("Could not read the file")); };
    reader.readAsDataURL(file);
  });
}
function formatFileSize(bytes) {
  const n = Number(bytes) || 0;
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return Math.round(n / 1024) + " KB";
  return (n / (1024 * 1024)).toFixed(1) + " MB";
}
function _errText(data, fallback) {
  const detail = data && (data.detail || data.error);
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map(function (item) { return item.msg || item.message || "Invalid upload"; }).join("; ");
  return fallback;
}
function saveUploadedDocumentJson(row, file) {
  return readUploadFile(file).then(function (packed) {
    if (!packed) throw new Error("Choose a file to upload");
    row.file_name = packed.name;
    row.file_mime = packed.mime;
    row.file_data = packed.data;
    row.size = formatFileSize(packed.size);
    row.has_file = true;
    return persistInsert(CONFIG.ENDPOINTS.DOCUMENTS, row).then(function (res) {
      row.file_data = "";
      return res;
    });
  });
}
function saveUploadedDocument(row, file) {
  if (!file) return Promise.reject(new Error("Choose a file to upload"));
  if (file.size > 1200000) return Promise.reject(new Error("File is too large. Use a file under 1.2 MB."));
  const body = new FormData();
  body.append("file", file, file.name);
  body.append("title", row.title || file.name || "Uploaded document");
  body.append("patient", row.patient || "");
  body.append("patient_id", row.patient_id || "");
  body.append("doc_type", row.type || "Other");
  body.append("summary", row.summary || "");
  const headers = {};
  const session = getSession();
  if (session && session.token) headers.Authorization = "Bearer " + session.token;
  return fetch(CONFIG.API_BASE_URL + "/documents/upload", { method: "POST", headers: headers, body: body }).then(function (res) {
    return res.json().catch(function () { return {}; }).then(function (data) {
      if (res.status === 404 || res.status === 405) return saveUploadedDocumentJson(row, file);
      if (!res.ok) {
        const msg = _errText(data, "Could not upload the file");
        showToast(msg, "error");
        return { ok: false, error: msg, status: res.status };
      }
      if (data.row && data.row.id) row.id = data.row.id;
      row.has_file = true;
      row.file_data = "";
      return { ok: true, data: data };
    });
  }).catch(function () {
    showToast("Network error — cannot reach the server.", "error");
    return { ok: false, error: "Network error" };
  });
}
function submitInlineUpload() {
  const titleEl = document.getElementById("upTitle");
  const fileEl = document.getElementById("upFile");
  const nameEl = document.getElementById("upPatient");
  const typeEl = document.getElementById("upType");
  const sumEl = document.getElementById("upSum");
  const status = document.getElementById("upStatus");
  const title = titleEl ? titleEl.value.trim() : "";
  const file = fileEl && fileEl.files ? fileEl.files[0] : null;
  const patient = nameEl ? nameEl.value.trim() : "";
  if (!patient) { showToast("Enter the patient name", "error"); return; }
  if (!title) { showToast("Title is required", "error"); return; }
  if (!file) { showToast("Choose a file to upload", "error"); return; }
  const row = {
    id: uid("DOC"),
    patient: patient,
    patient_id: "",
    type: typeEl ? typeEl.value : "Other",
    title: title,
    date: typeof todayStr === "function" ? todayStr() : new Date().toISOString().slice(0, 10),
    uploaded_by: getUserName(),
    summary: sumEl ? sumEl.value.trim() : ""
  };
  const btn = document.getElementById("btnUploadSave");
  if (btn) btn.disabled = true;
  if (status) status.textContent = "Saving the file to Supabase…";
  saveUploadedDocument(row, file).then(function (res) {
    if (btn) btn.disabled = false;
    if (!res || !res.ok) {
      if (status) status.textContent = (res && res.error) || "Upload failed.";
      return;
    }
    if (typeof DOCS !== "undefined" && Array.isArray(DOCS)) DOCS.unshift(row);
    if (typeof renderDocs === "function") renderDocs();
    if (titleEl) titleEl.value = "";
    if (sumEl) sumEl.value = "";
    if (fileEl) fileEl.value = "";
    if (status) status.textContent = "Saved. The file is in the list below.";
    showToast("Document uploaded", "success");
  }).catch(function (err) {
    if (btn) btn.disabled = false;
    if (status) status.textContent = err.message || "Upload failed.";
    showToast(err.message || "Could not upload the file", "error");
  });
}
function saveDoctorPatientFile() {
  const firstEl = document.getElementById("fileFirst");
  if (!firstEl) return;
  const first = firstEl.value.trim();
  const last = (document.getElementById("fileLast").value || "").trim();
  if (!first || !last) { showToast("First and last name are required", "error"); return; }
  const existing = (document.getElementById("fileId").value || "").trim();
  const row = {
    id: existing || uid("P"),
    first_name: first,
    last_name: last,
    age: Number(document.getElementById("fileAge").value) || null,
    gender: document.getElementById("fileGender").value,
    phone: document.getElementById("filePhone").value.trim(),
    email: document.getElementById("fileEmail").value.trim(),
    blood: document.getElementById("fileBlood").value,
    address: document.getElementById("fileAddr").value.trim(),
    emergency: document.getElementById("fileEc").value.trim(),
    condition: document.getElementById("fileCond").value.trim(),
    last_visit: typeof todayStr === "function" ? todayStr() : "",
    status: "active",
    notes: document.getElementById("fileNotes").value.trim(),
    filed_by: getUserName()
  };
  const done = function (res) {
    if (!res || !res.ok) return;
    if (typeof PATIENTS !== "undefined" && Array.isArray(PATIENTS)) {
      const found = PATIENTS.find(function (p) { return p.id === row.id; });
      if (found) Object.assign(found, row);
      else PATIENTS.unshift(row);
    }
    if (typeof renderPatients === "function") renderPatients();
    ["fileId", "fileFirst", "fileLast", "fileAge", "filePhone", "fileEmail", "fileAddr", "fileEc", "fileCond", "fileNotes"].forEach(function (id) {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });
    showToast("Patient file saved", "success");
  };
  if (existing) persistUpdate(CONFIG.ENDPOINTS.PATIENTS, existing, row).then(done);
  else persistInsert(CONFIG.ENDPOINTS.PATIENTS, row).then(done);
}
function ensureHealthCard() {
  const session = getSession();
  if (!session || session.role !== "patient" || !CONFIG.ENDPOINTS.HEALTH_CARD) return;
  if (!window.__cardPromise) {
    window.__cardPromise = apiFetch(CONFIG.ENDPOINTS.HEALTH_CARD).then(function (res) {
      const card = res.ok && res.data && res.data.card;
      if (!card || !card.id) return null;
      session.health_card = card.id;
      saveSession(session);
      window.__healthCard = card;
      return card;
    });
  }
  window.__cardPromise.then(function (card) {
    if (card) showHealthCardStrip(card);
  });
}
function showHealthCardStrip(card) {
  const host = document.querySelector(".page-body") || document.getElementById("spaBody");
  if (!host || document.getElementById("autoHealthCard")) return;
  const el = document.createElement("a");
  el.id = "autoHealthCard";
  el.href = "health-card.html";
  el.className = "card mb-4";
  el.style.cssText = "display:block;text-decoration:none;color:inherit";
  el.innerHTML = '<div class="flex-between wrap" style="gap:8px"><div><div class="text-sm" style="color:#6B7280">Health card</div><strong>' +
    esc(card.id) + '</strong><div class="text-sm" style="color:#6B7280">Issued automatically for this patient account.</div></div><span class="badge badge-success">Active</span></div>';
  host.insertBefore(el, host.firstChild);
}
function fillDoctorPatientFile(id) {
  const form = document.getElementById("patientFileForm");
  if (!form) return;
  const p = (id && typeof PATIENTS !== "undefined" && Array.isArray(PATIENTS)) ? PATIENTS.find(function (row) { return row.id === id; }) : null;
  document.getElementById("fileId").value = p ? p.id : "";
  document.getElementById("fileFirst").value = p ? (p.first_name || "") : "";
  document.getElementById("fileLast").value = p ? (p.last_name || "") : "";
  document.getElementById("fileAge").value = p && p.age != null ? p.age : "";
  document.getElementById("fileGender").value = p && p.gender ? p.gender : "Male";
  document.getElementById("filePhone").value = p ? (p.phone || "") : "";
  document.getElementById("fileEmail").value = p ? (p.email || "") : "";
  document.getElementById("fileBlood").value = p && p.blood ? p.blood : "Unknown";
  document.getElementById("fileAddr").value = p ? (p.address || "") : "";
  document.getElementById("fileEc").value = p ? (p.emergency || "") : "";
  document.getElementById("fileCond").value = p ? (p.condition || "") : "";
  document.getElementById("fileNotes").value = p && p.details && p.details.notes ? p.details.notes : (p && p.notes ? p.notes : "");
  const title = document.getElementById("patientFileTitle");
  if (title) title.textContent = p ? "Update patient file" : "File patient information";
}
document.addEventListener("click", function (e) {
  const open = e.target && e.target.closest && e.target.closest("#btnUpload");
  if (open) {
    const panel = document.getElementById("uploadPanel");
    if (panel) {
      e.preventDefault();
      panel.scrollIntoView({ behavior: "smooth", block: "center" });
      const file = document.getElementById("upFile");
      if (file) file.focus();
    }
  }
  const save = e.target && e.target.closest && e.target.closest("#btnUploadSave");
  if (save) {
    e.preventDefault();
    submitInlineUpload();
  }
  const fileSave = e.target && e.target.closest && e.target.closest("#btnSavePatientFile");
  if (fileSave) {
    e.preventDefault();
    saveDoctorPatientFile();
  }
  const fileOpen = e.target && e.target.closest && e.target.closest("#btnFilePatient");
  if (fileOpen && document.getElementById("patientFileForm")) {
    e.preventDefault();
    fillDoctorPatientFile("");
    document.getElementById("patientFileForm").scrollIntoView({ behavior: "smooth", block: "start" });
  }
});
function downloadStoredFile(doc) {
  if (!doc) return;
  const finish = function (packed) {
    if (!packed || !packed.file_data) { showToast("No file is stored for this document", "error"); return; }
    const a = document.createElement("a");
    a.href = packed.file_data;
    a.download = packed.file_name || doc.title || "document";
    document.body.appendChild(a);
    a.click();
    a.remove();
    showToast("Downloaded " + (doc.title || packed.file_name), "success");
  };
  if (doc.file_data) { finish(doc); return; }
  apiFetch(CONFIG.ENDPOINTS.DOCUMENTS + "/" + encodeURIComponent(doc.id) + "/file").then(function (res) {
    if (!res.ok) { showToast(res.error || "Could not download the file", "error"); return; }
    finish(res.data);
  });
}

// ---------- Messages ----------
let _directory = [];
function loadMessageDirectory() {
  return apiFetch(CONFIG.ENDPOINTS.MESSAGE_DIRECTORY).then(function (res) {
    _directory = (res.ok && res.data && res.data.items) || [];
    return _directory;
  });
}
function messageGroups() {
  return [
    { id: "", name: "All Staff", email: "Every staff account", role: "staff", group: "All Staff" },
    { id: "", name: "All Doctors", email: "Every doctor", role: "doctor", group: "All Doctors" },
    { id: "", name: "All Nurses", email: "Every nurse", role: "nurse", group: "All Nurses" },
    { id: "", name: "All Pharmacists", email: "Every pharmacist", role: "pharmacist", group: "All Pharmacists" },
    { id: "", name: "All Laboratory", email: "Laboratory team", role: "laboratory", group: "All Laboratory" },
    { id: "", name: "All Reception", email: "Front desk", role: "reception", group: "All Reception" },
    { id: "", name: "All Patients", email: "Every patient", role: "patient", group: "All Patients" }
  ];
}
function attachRecipientPicker(input, hint) {
  const box = document.createElement("div");
  box.style.position = "relative";
  input.parentNode.insertBefore(box, input);
  box.appendChild(input);
  const list = document.createElement("div");
  list.style.cssText = "display:none;position:absolute;z-index:20;left:0;right:0;top:100%;background:#fff;border:1px solid #E5E7EB;border-radius:12px;max-height:240px;overflow:auto;box-shadow:0 10px 28px rgba(15,23,42,.12)";
  box.appendChild(list);
  let picked = null;
  function choices() {
    const q = input.value.trim().toLowerCase();
    const people = messageGroups().concat(_directory.filter(function (p) { return p.id !== (getSession() || {}).user_id; }));
    return people.filter(function (p) {
      if (!q) return true;
      return (p.name || "").toLowerCase().indexOf(q) >= 0 || (p.email || "").toLowerCase().indexOf(q) >= 0 || (p.role || "").toLowerCase().indexOf(q) >= 0;
    }).slice(0, 8);
  }
  function paint() {
    const hits = choices();
    if (!hits.length) { list.style.display = "none"; list.innerHTML = ""; return; }
    list.style.display = "block";
    list.innerHTML = hits.map(function (p, i) {
      const role = p.group ? "Group" : (typeof getRoleLabel === "function" ? getRoleLabel(p.role) : p.role);
      const initials = (typeof initialsOf === "function" ? initialsOf(p.name) : (p.name || "?").slice(0, 2));
      return '<button type="button" data-i="' + i + '" style="display:flex;gap:10px;align-items:center;width:100%;text-align:left;padding:8px 10px;border:0;background:#fff;cursor:pointer">' +
        '<span style="width:34px;height:34px;border-radius:50%;background:#0B3A5E;color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;flex:none">' + esc(initials) + '</span>' +
        '<span><strong style="display:block">' + esc(p.name) + '</strong><span style="color:#6B7280;font-size:12px">' + esc(role) + ' · ' + esc(p.email || "No email") + '</span></span></button>';
    }).join("");
    list.querySelectorAll("button").forEach(function (btn) {
      btn.onmouseenter = function () { btn.style.background = "#F3F4F6"; };
      btn.onmouseleave = function () { btn.style.background = "#fff"; };
      btn.onclick = function () {
        const p = hits[Number(btn.getAttribute("data-i"))];
        picked = p;
        input.value = p.name;
        input.dataset.email = p.email || "";
        input.dataset.uid = p.id || "";
        input.dataset.role = p.role || "";
        input.dataset.group = p.group || "";
        if (hint) hint.textContent = p.name + " · " + (p.group ? "group" : (typeof getRoleLabel === "function" ? getRoleLabel(p.role) : p.role)) + " · " + (p.email || "");
        list.style.display = "none";
      };
    });
  }
  input.addEventListener("input", function () { picked = null; input.dataset.email = ""; input.dataset.uid = ""; input.dataset.group = ""; paint(); });
  input.addEventListener("focus", paint);
  document.addEventListener("click", function (e) { if (!box.contains(e.target)) list.style.display = "none"; });
  loadMessageDirectory().then(paint);
  return {
    selected: function () {
      if (picked) return picked;
      const typed = input.value.trim().toLowerCase();
      return _directory.find(function (p) { return (p.name || "").toLowerCase() === typed || (p.email || "").toLowerCase() === typed; }) || null;
    }
  };
}
function sendHospitalMessage(fields) {
  const person = fields.person;
  const row = {
    id: uid("MSG"),
    from: getUserName(),
    from_role: getUserRole(),
    from_email: (getSession() || {}).email || "",
    to: person ? person.name : fields.to,
    to_email: person && !person.group ? person.email : "",
    to_id: person && !person.group ? person.id : "",
    to_role: person ? person.role : "",
    subject: fields.subject,
    body: fields.body,
    date: new Date().toISOString(),
    read: false,
    priority: fields.priority || "normal",
    replies: fields.replies || []
  };
  return persistInsert(CONFIG.ENDPOINTS.MESSAGES, row).then(function (res) {
    if (res && res.ok) row.id = (res.data && res.data.row && res.data.row.id) || row.id;
    return { res: res, row: row };
  });
}

