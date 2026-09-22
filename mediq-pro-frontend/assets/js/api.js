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
// ---------- Live YouTube search (free YouTube Data API v3) ----------
// Used by the Health Videos feature when CONFIG.YOUTUBE_API_KEY is set.
// Throws on failure so callers can degrade to the curated library.
// Results are filtered to HEALTH content only (no music/gaming/entertainment).
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
  if (!CONFIG.YOUTUBE_API_KEY) throw new Error("no-youtube-key");
  const q = query.toLowerCase().includes("health") ? query : query + " health";
  const url = "https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=" + maxResults +
              "&q=" + encodeURIComponent(q) + "&type=video&videoEmbeddable=true&safeSearch=strict&relevanceLanguage=en&key=" + CONFIG.YOUTUBE_API_KEY;
  const res = await fetch(url);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const reason = (err.error && err.error.errors && err.error.errors[0] && err.error.errors[0].reason) || ("HTTP " + res.status);
    throw new Error(reason || "youtube-api-error");
  }
  const data = await res.json();
  return (data.items || []).map((it, i) => ({
    id: "YT-" + it.id.videoId + "-" + i,
    title: it.snippet.title,
    channel: it.snippet.channelTitle,
    video_id: it.id.videoId,
    search: "",
    conditions: [],
    duration: "—",
    views: "—",
    category: "Live results",
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

function persistInsert(endpoint, row) {
  if (!endpoint || !row) return;
  apiFetch(endpoint, "POST", row).then(function (res) {
    if (!res.ok) showToast(res.error || "Could not save to Supabase", "error");
    else if (res.data && res.data.row && res.data.row.id) row.id = res.data.row.id;
  });
}

function persistUpdate(endpoint, id, row) {
  if (!endpoint || !id) return persistInsert(endpoint, row);
  apiFetch(endpoint + "/" + encodeURIComponent(id), "PUT", row).then(function (res) {
    if (!res.ok) showToast(res.error || "Could not update Supabase", "error");
  });
}

function persistDelete(endpoint, id) {
  if (!endpoint || !id) return;
  apiFetch(endpoint + "/" + encodeURIComponent(id), "DELETE").then(function (res) {
    if (!res.ok) showToast(res.error || "Could not delete from Supabase", "error");
  });
}

const _known = {};
function persistUpsert(endpoint, row) {
  if (!row) return;
  const key = endpoint + ":" + row.id;
  if (row.id && _known[key]) persistUpdate(endpoint, row.id, row);
  else {
    persistInsert(endpoint, row);
    if (row.id) _known[key] = true;
  }
}
function markKnown(endpoint, rows) {
  (rows || []).forEach(function (row) {
    if (row && row.id) _known[endpoint + ":" + row.id] = true;
  });
}
