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
function saveUploadedDocument(row, file) {
  return readUploadFile(file).then(function (packed) {
    if (!packed) throw new Error("Choose a file to upload");
    row.file_name = packed.name;
    row.file_mime = packed.mime;
    row.file_data = packed.data;
    row.size = formatFileSize(packed.size);
    row.has_file = true;
    return persistInsert(CONFIG.ENDPOINTS.DOCUMENTS, row);
  });
}
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

