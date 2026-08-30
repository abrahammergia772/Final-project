/* ============================================================
   Wolaita Sodo Hospital — api.js
   Fetch wrapper + AI module functions + demo mock data
   All calls to FastAPI go through apiFetch(). When CONFIG.DEMO_MODE
   is true, requests are answered with realistic mock data so every
   page is testable before the backend/.pkl models are ready.
   ============================================================ */

// ---------- Core fetch wrapper ----------
async function apiFetch(endpoint, method = "GET", body = null, opts = {}) {
  const headers = { "Content-Type": "application/json" };
  const session = getSession();
  if (!opts.skipAuth && session && session.token) {
    headers["Authorization"] = "Bearer " + session.token;
  }

  // DEMO MODE — answer from mock data (no network needed)
  if (CONFIG.DEMO_MODE && !opts.skipDemo) {
    return mockResponse(endpoint, method, body);
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
let mockSeq = 0;
const uid = (p) => (p || "ID") + "-" + (1000 + (mockSeq++ % 9000));

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

// ============================================================
// DEMO MOCK DATA
// ============================================================
const MOCK = {
  users: [
    { id: "U-001", name: "Solomon Tadesse", email: "admin@wsh.et", role: "admin", department: "Administration", status: "active", last_login: "2026-08-11T08:12:00" },
    { id: "U-002", name: "Hanna Bekele", email: "manager@wsh.et", role: "manager", department: "Management", status: "active", last_login: "2026-08-11T07:55:00" },
    { id: "U-003", name: "Dr. Daniel Alemu", email: "doctor@wsh.et", role: "doctor", department: "Internal Medicine", status: "active", last_login: "2026-08-11T07:40:00" },
    { id: "U-004", name: "Marta Tesfaye", email: "nurse@wsh.et", role: "nurse", department: "General Ward", status: "active", last_login: "2026-08-11T06:58:00" },
    { id: "U-005", name: "Yonas Girma", email: "pharmacist@wsh.et", role: "pharmacist", department: "Pharmacy", status: "active", last_login: "2026-08-11T07:20:00" },
    { id: "U-006", name: "Sara Worku", email: "lab@wsh.et", role: "laboratory", department: "Laboratory", status: "active", last_login: "2026-08-11T07:10:00" },
    { id: "U-007", name: "Liya Hailu", email: "reception@wsh.et", role: "reception", department: "Front Desk", status: "active", last_login: "2026-08-11T06:45:00" },
    { id: "U-008", name: "Abel Mekonnen", email: "patient@wsh.et", role: "patient", department: "—", status: "active", last_login: "2026-08-10T18:30:00" },
    { id: "U-009", name: "Dr. Fikru Debebe", email: "fikru.d@wsh.et", role: "doctor", department: "Pediatrics", status: "active", last_login: "2026-08-10T16:12:00" },
    { id: "U-010", name: "Bethelehem Girma", email: "beti.g@wsh.et", role: "nurse", department: "Pediatrics", status: "inactive", last_login: "2026-08-04T13:02:00" },
    { id: "U-011", name: "Dr. Meron Assefa", email: "meron.a@wsh.et", role: "doctor", department: "Cardiology", status: "active", last_login: "2026-08-10T15:44:00" },
    { id: "U-012", name: "Kaleb Teshome", email: "kaleb.t@wsh.et", role: "pharmacist", department: "Pharmacy", status: "active", last_login: "2026-08-10T17:20:00" }
  ],

  patients: [
    { id: "P-1001", first_name: "Abel", last_name: "Mekonnen", age: 34, gender: "Male", phone: "+251 911 223 344", email: "abel.m@mail.com", blood: "O+", address: "Sodo, Wolaita", emergency: "+251 911 223 355", condition: "Hypertension", last_visit: "2026-08-05", status: "active" },
    { id: "P-1002", first_name: "Hana", last_name: "Wolde", age: 28, gender: "Female", phone: "+251 912 334 455", email: "hana.w@mail.com", blood: "A+", address: "Sodo, Wolaita", emergency: "+251 912 334 466", condition: "Diabetes Type 2", last_visit: "2026-08-02", status: "active" },
    { id: "P-1003", first_name: "Dawit", last_name: "Kebede", age: 45, gender: "Male", phone: "+251 913 445 566", email: "dawit.k@mail.com", blood: "B+", address: "Boditi", emergency: "+251 913 445 577", condition: "Asthma", last_visit: "2026-07-28", status: "active" },
    { id: "P-1004", first_name: "Selam", last_name: "Tadesse", age: 62, gender: "Female", phone: "+251 914 556 677", email: "selam.t@mail.com", blood: "AB+", address: "Areka", emergency: "+251 914 556 688", condition: "Heart Disease", last_visit: "2026-08-09", status: "active" },
    { id: "P-1005", first_name: "Biruk", last_name: "Ayele", age: 8, gender: "Male", phone: "+251 915 667 788", email: "—", blood: "O-", address: "Sodo, Wolaita", emergency: "+251 915 667 799", condition: "Pneumonia (recovering)", last_visit: "2026-08-07", status: "active" },
    { id: "P-1006", first_name: "Ruth", last_name: "Gebre", age: 51, gender: "Female", phone: "+251 916 778 899", email: "ruth.g@mail.com", blood: "A-", address: "Humbo", emergency: "+251 916 778 800", condition: "Chronic Kidney Disease", last_visit: "2026-08-08", status: "active" },
    { id: "P-1007", first_name: "Tewodros", last_name: "Haile", age: 39, gender: "Male", phone: "+251 917 889 900", email: "tewodros.h@mail.com", blood: "B-", address: "Sodo, Wolaita", emergency: "+251 917 889 911", condition: "Thyroid Disorder", last_visit: "2026-08-01", status: "active" },
    { id: "P-1008", first_name: "Mahlet", last_name: "Shiferaw", age: 22, gender: "Female", phone: "+251 918 990 011", email: "mahlet.s@mail.com", blood: "O+", address: "Sodo, Wolaita", emergency: "+251 918 990 022", condition: "—", last_visit: "2026-07-30", status: "active" },
    { id: "P-1009", first_name: "Yohannes", last_name: "Mamo", age: 58, gender: "Male", phone: "+251 919 001 122", email: "yohannes.m@mail.com", blood: "A+", address: "Bilate", emergency: "+251 919 001 133", condition: "Diabetes + Hypertension", last_visit: "2026-08-10", status: "active" },
    { id: "P-1010", first_name: "Kidist", last_name: "Assefa", age: 30, gender: "Female", phone: "+251 910 112 233", email: "kidist.a@mail.com", blood: "B+", address: "Sodo, Wolaita", emergency: "+251 910 112 244", condition: "Malaria (treated)", last_visit: "2026-08-06", status: "active" }
  ],

  departments: [
    { id: "D-01", name: "Internal Medicine", head: "Dr. Daniel Alemu", staff: 18, beds: 42, occupied: 35, status: "active" },
    { id: "D-02", name: "Pediatrics", head: "Dr. Fikru Debebe", staff: 14, beds: 30, occupied: 21, status: "active" },
    { id: "D-03", name: "Cardiology", head: "Dr. Meron Assefa", staff: 10, beds: 20, occupied: 17, status: "active" },
    { id: "D-04", name: "Maternity", head: "Dr. Tsehay Mengistu", staff: 22, beds: 26, occupied: 24, status: "active" },
    { id: "D-05", name: "Emergency", head: "Dr. Natnael Fekadu", staff: 16, beds: 14, occupied: 12, status: "active" },
    { id: "D-06", name: "Surgery", head: "Dr. Amanuel Bekele", staff: 12, beds: 24, occupied: 13, status: "active" },
    { id: "D-07", name: "Orthopedics", head: "Dr. Girma Tola", staff: 8, beds: 16, occupied: 6, status: "active" },
    { id: "D-08", name: "Outpatient (OPD)", head: "Dr. Daniel Alemu", staff: 20, beds: 0, occupied: 0, status: "active" }
  ],

  staff: [
    { id: "S-001", name: "Dr. Daniel Alemu", role: "Doctor", dept: "Internal Medicine", shift: "Morning", status: "present", contact: "+251 911 100 001" },
    { id: "S-002", name: "Dr. Fikru Debebe", role: "Doctor", dept: "Pediatrics", shift: "Morning", status: "present", contact: "+251 911 100 002" },
    { id: "S-003", name: "Dr. Meron Assefa", role: "Doctor", dept: "Cardiology", shift: "Evening", status: "present", contact: "+251 911 100 003" },
    { id: "S-004", name: "Marta Tesfaye", role: "Nurse", dept: "General Ward", shift: "Morning", status: "present", contact: "+251 911 100 004" },
    { id: "S-005", name: "Bethelehem Girma", role: "Nurse", dept: "Pediatrics", shift: "Morning", status: "absent", contact: "+251 911 100 005" },
    { id: "S-006", name: "Yonas Girma", role: "Pharmacist", dept: "Pharmacy", shift: "Morning", status: "present", contact: "+251 911 100 006" },
    { id: "S-007", name: "Sara Worku", role: "Lab Technician", dept: "Laboratory", shift: "Morning", status: "present", contact: "+251 911 100 007" },
    { id: "S-008", name: "Liya Hailu", role: "Receptionist", dept: "Front Desk", shift: "Morning", status: "present", contact: "+251 911 100 008" },
    { id: "S-009", name: "Dr. Tsehay Mengistu", role: "Doctor", dept: "Maternity", shift: "Night", status: "on-leave", contact: "+251 911 100 009" },
    { id: "S-010", name: "Kaleb Teshome", role: "Pharmacist", dept: "Pharmacy", shift: "Evening", status: "present", contact: "+251 911 100 010" }
  ],

  appointments: [
    { id: "A-501", patient: "Abel Mekonnen", patient_id: "P-1001", doctor: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-11", time: "09:00", type: "Follow-up", status: "confirmed", no_show: 12 },
    { id: "A-502", patient: "Hana Wolde", patient_id: "P-1002", doctor: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-11", time: "09:30", type: "Consultation", status: "confirmed", no_show: 22 },
    { id: "A-503", patient: "Dawit Kebede", patient_id: "P-1003", doctor: "Dr. Fikru Debebe", dept: "Pediatrics", date: "2026-08-11", time: "10:00", type: "Consultation", status: "checked-in", no_show: 8 },
    { id: "A-504", patient: "Selam Tadesse", patient_id: "P-1004", doctor: "Dr. Meron Assefa", dept: "Cardiology", date: "2026-08-11", time: "10:30", type: "Follow-up", status: "confirmed", no_show: 18 },
    { id: "A-505", patient: "Biruk Ayele", patient_id: "P-1005", doctor: "Dr. Fikru Debebe", dept: "Pediatrics", date: "2026-08-11", time: "11:00", type: "Consultation", status: "completed", no_show: 5 },
    { id: "A-506", patient: "Ruth Gebre", patient_id: "P-1006", doctor: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-11", time: "11:30", type: "Follow-up", status: "confirmed", no_show: 31 },
    { id: "A-507", patient: "Tewodros Haile", patient_id: "P-1007", doctor: "Dr. Meron Assefa", dept: "Cardiology", date: "2026-08-11", time: "14:00", type: "New patient", status: "confirmed", no_show: 15 },
    { id: "A-508", patient: "Yohannes Mamo", patient_id: "P-1009", doctor: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-11", time: "14:30", type: "Follow-up", status: "confirmed", no_show: 9 },
    { id: "A-509", patient: "Mahlet Shiferaw", patient_id: "P-1008", doctor: "Dr. Fikru Debebe", dept: "Pediatrics", date: "2026-08-11", time: "15:00", type: "Consultation", status: "cancelled", no_show: 40 },
    { id: "A-510", patient: "Kidist Assefa", patient_id: "P-1010", doctor: "Dr. Meron Assefa", dept: "Cardiology", date: "2026-08-11", time: "15:30", type: "Consultation", status: "confirmed", no_show: 6 }
  ],

  prescriptions: [
    { id: "RX-2201", patient: "Abel Mekonnen", doctor: "Dr. Daniel Alemu", date: "2026-08-11", drugs: [{ name: "Amlodipine 5mg", dose: "1 tablet", freq: "Once daily", duration: "30 days" }, { name: "Aspirin 81mg", dose: "1 tablet", freq: "Once daily", duration: "30 days" }], status: "active" },
    { id: "RX-2202", patient: "Hana Wolde", doctor: "Dr. Daniel Alemu", date: "2026-08-11", drugs: [{ name: "Metformin 500mg", dose: "1 tablet", freq: "Twice daily", duration: "60 days" }], status: "active" },
    { id: "RX-2203", patient: "Dawit Kebede", doctor: "Dr. Fikru Debebe", date: "2026-08-10", drugs: [{ name: "Salbutamol Inhaler", dose: "2 puffs", freq: "As needed", duration: "30 days" }], status: "active" },
    { id: "RX-2204", patient: "Selam Tadesse", doctor: "Dr. Meron Assefa", date: "2026-08-09", drugs: [{ name: "Atorvastatin 20mg", dose: "1 tablet", freq: "Once daily at night", duration: "90 days" }, { name: "Bisoprolol 2.5mg", dose: "1 tablet", freq: "Once daily", duration: "90 days" }], status: "active" },
    { id: "RX-2205", patient: "Yohannes Mamo", doctor: "Dr. Daniel Alemu", date: "2026-08-10", drugs: [{ name: "Insulin Glargine", dose: "20 units", freq: "Once daily", duration: "30 days" }, { name: "Enalapril 10mg", dose: "1 tablet", freq: "Once daily", duration: "30 days" }], status: "active" }
  ],

  inventory: [
    { id: "I-001", name: "Paracetamol 500mg", category: "Analgesic", stock: 850, unit: "tablets", expiry: "2027-02-15", status: "in-stock" },
    { id: "I-002", name: "Amlodipine 5mg", category: "Cardiovascular", stock: 210, unit: "tablets", expiry: "2026-11-20", status: "in-stock" },
    { id: "I-003", name: "Metformin 500mg", category: "Antidiabetic", stock: 74, unit: "tablets", expiry: "2026-12-01", status: "low-stock" },
    { id: "I-004", name: "Insulin Glargine", category: "Antidiabetic", stock: 22, unit: "vials", expiry: "2026-09-30", status: "low-stock" },
    { id: "I-005", name: "Amoxicillin 250mg", category: "Antibiotic", stock: 0, unit: "capsules", expiry: "2026-10-10", status: "out-of-stock" },
    { id: "I-006", name: "Salbutamol Inhaler", category: "Respiratory", stock: 48, unit: "units", expiry: "2026-12-18", status: "in-stock" },
    { id: "I-007", name: "ORS Sachets", category: "Gastro", stock: 430, unit: "sachets", expiry: "2027-01-25", status: "in-stock" },
    { id: "I-008", name: "Atorvastatin 20mg", category: "Cardiovascular", stock: 63, unit: "tablets", expiry: "2026-08-25", status: "expiring-soon" },
    { id: "I-009", name: "Artemether/Lumefantrine", category: "Antimalarial", stock: 150, unit: "blisters", expiry: "2027-03-05", status: "in-stock" },
    { id: "I-010", name: "Ceftriaxone 1g", category: "Antibiotic", stock: 38, unit: "vials", expiry: "2026-09-14", status: "low-stock" },
    { id: "I-011", name: "IV Dextrose 5%", category: "IV Fluids", stock: 120, unit: "bottles", expiry: "2027-04-10", status: "in-stock" },
    { id: "I-012", name: "Hydrocortisone 100mg", category: "Steroid", stock: 29, unit: "vials", expiry: "2026-08-19", status: "expiring-soon" }
  ],

  lab_requests: [
    { id: "LR-331", patient: "Abel Mekonnen", test: "Complete Blood Count", doctor: "Dr. Daniel Alemu", date: "2026-08-11", priority: "Routine", status: "pending" },
    { id: "LR-332", patient: "Hana Wolde", test: "Fasting Blood Sugar", doctor: "Dr. Daniel Alemu", date: "2026-08-11", priority: "Urgent", status: "pending" },
    { id: "LR-333", patient: "Selam Tadesse", test: "Lipid Profile", doctor: "Dr. Meron Assefa", date: "2026-08-11", priority: "Routine", status: "in-progress" },
    { id: "LR-334", patient: "Ruth Gebre", test: "Kidney Function", doctor: "Dr. Daniel Alemu", date: "2026-08-11", priority: "Urgent", status: "pending" },
    { id: "LR-335", patient: "Biruk Ayele", test: "Malaria Test", doctor: "Dr. Fikru Debebe", date: "2026-08-10", priority: "Routine", status: "completed" },
    { id: "LR-336", patient: "Yohannes Mamo", test: "HbA1c", doctor: "Dr. Daniel Alemu", date: "2026-08-10", priority: "Routine", status: "completed" }
  ],

  lab_results: [
    { id: "R-901", patient: "Biruk Ayele", test: "Malaria Test", date: "2026-08-10", status: "normal", ai_flag: "normal", values: [{ name: "Malaria Antigen", range: "Negative", value: "Negative", status: "normal" }] },
    { id: "R-902", patient: "Yohannes Mamo", test: "HbA1c", date: "2026-08-10", status: "abnormal", ai_flag: "abnormal", values: [{ name: "HbA1c", range: "4.0 – 5.6 %", value: "8.2 %", status: "abnormal" }] },
    { id: "R-903", patient: "Selam Tadesse", test: "Lipid Profile", date: "2026-08-09", status: "abnormal", ai_flag: "abnormal", values: [{ name: "Total Cholesterol", range: "< 200 mg/dL", value: "248 mg/dL", status: "abnormal" }, { name: "LDL", range: "< 100 mg/dL", value: "168 mg/dL", status: "abnormal" }, { name: "HDL", range: "> 40 mg/dL", value: "38 mg/dL", status: "abnormal" }] },
    { id: "R-904", patient: "Mahlet Shiferaw", test: "Complete Blood Count", date: "2026-08-08", status: "normal", ai_flag: "normal", values: [{ name: "Hemoglobin", range: "13.5–17.5 g/dL", value: "14.2 g/dL", status: "normal" }, { name: "WBC", range: "4.0–11.0 ×10³/µL", value: "6.8 ×10³/µL", status: "normal" }] },
    { id: "R-905", patient: "Kidist Assefa", test: "Malaria Test", date: "2026-08-06", status: "normal", ai_flag: "normal", values: [{ name: "Malaria Antigen", range: "Negative", value: "Negative", status: "normal" }] }
  ],

  medications: [
    { id: "M-01", patient: "Selam Tadesse", drug: "Atorvastatin 20mg", dose: "1 tablet", due: "08:00", status: "administered", time: "07:58" },
    { id: "M-02", patient: "Abel Mekonnen", drug: "Amlodipine 5mg", dose: "1 tablet", due: "08:00", status: "administered", time: "08:05" },
    { id: "M-03", patient: "Yohannes Mamo", drug: "Insulin Glargine", dose: "20 units", due: "09:00", status: "pending", time: "" },
    { id: "M-04", patient: "Hana Wolde", drug: "Metformin 500mg", dose: "1 tablet", due: "09:00", status: "pending", time: "" },
    { id: "M-05", patient: "Dawit Kebede", drug: "Salbutamol Inhaler", dose: "2 puffs", due: "09:00", status: "missed", time: "" },
    { id: "M-06", patient: "Ruth Gebre", drug: "Furosemide 40mg", dose: "1 tablet", due: "10:00", status: "pending", time: "" },
    { id: "M-07", patient: "Biruk Ayele", drug: "Paracetamol Syrup", dose: "5 ml", due: "10:00", status: "pending", time: "" }
  ],

  care_plans: [
    { id: "CP-1", patient: "Selam Tadesse", plan: "Post-MI cardiac rehab", created: "2026-08-02", updated: "2026-08-10", status: "in-progress", steps: ["Daily ECG monitoring", "Physiotherapy: 30 min/day", "Diet: low-sodium", "Medication adherence"] },
    { id: "CP-2", patient: "Yohannes Mamo", plan: "Diabetes management", created: "2026-07-20", updated: "2026-08-10", status: "in-progress", steps: ["Blood glucose monitoring ×4/day", "Dietitian consult weekly", "Foot examination"] },
    { id: "CP-3", patient: "Ruth Gebre", plan: "CKD stage 3 care", created: "2026-07-15", updated: "2026-08-08", status: "in-progress", steps: ["Fluid intake monitoring", "Monthly creatinine", "Low-protein diet"] },
    { id: "CP-4", patient: "Biruk Ayele", plan: "Pneumonia recovery", created: "2026-08-07", updated: "2026-08-09", status: "completed", steps: ["IV antibiotics 7 days", "Chest physio", "Follow-up X-ray"] }
  ],

  bills: [
    { id: "B-701", date: "2026-08-05", description: "Consultation — Internal Medicine", amount: 350, status: "paid" },
    { id: "B-702", date: "2026-08-05", description: "Complete Blood Count", amount: 250, status: "paid" },
    { id: "B-703", date: "2026-08-06", description: "Amlodipine 5mg ×30 tablets", amount: 180, status: "pending" },
    { id: "B-704", date: "2026-08-08", description: "ECG — Cardiology", amount: 500, status: "pending" },
    { id: "B-705", date: "2026-08-09", description: "Inpatient ward — 2 nights (General)", amount: 1600, status: "overdue" },
    { id: "B-706", date: "2026-08-10", description: "Physiotherapy session", amount: 300, status: "pending" }
  ],

  audit_logs: [
    { id: "AL-1", ts: "2026-08-11T08:12:00", user: "Solomon Tadesse", role: "admin", action: "login", ip: "196.188.24.10", status: "success" },
    { id: "AL-2", ts: "2026-08-11T08:05:00", user: "Dr. Daniel Alemu", role: "doctor", action: "create", ip: "196.188.24.45", status: "success", detail: "Created prescription RX-2201" },
    { id: "AL-3", ts: "2026-08-11T07:58:00", user: "Marta Tesfaye", role: "nurse", action: "update", ip: "196.188.24.67", status: "success", detail: "Recorded vitals for P-1004" },
    { id: "AL-4", ts: "2026-08-11T07:45:00", user: "Sara Worku", role: "laboratory", action: "create", ip: "196.188.24.88", status: "success", detail: "Uploaded lab result R-902" },
    { id: "AL-5", ts: "2026-08-11T07:30:00", user: "unknown", role: "—", action: "login", ip: "41.223.88.12", status: "failed" },
    { id: "AL-6", ts: "2026-08-11T07:20:00", user: "Yonas Girma", role: "pharmacist", action: "update", ip: "196.188.24.100", status: "success", detail: "Updated stock for I-003" },
    { id: "AL-7", ts: "2026-08-11T07:05:00", user: "Liya Hailu", role: "reception", action: "create", ip: "196.188.24.23", status: "success", detail: "Registered patient P-1010" },
    { id: "AL-8", ts: "2026-08-10T23:50:00", user: "system", role: "system", action: "backup", ip: "internal", status: "success", detail: "Daily database backup completed" },
    { id: "AL-9", ts: "2026-08-10T21:15:00", user: "Solomon Tadesse", role: "admin", action: "delete", ip: "196.188.24.10", status: "success", detail: "Deleted inactive user U-014" },
    { id: "AL-10", ts: "2026-08-10T18:40:00", user: "Abel Mekonnen", role: "patient", action: "login", ip: "196.188.30.5", status: "success" }
  ],

  queue: [
    { id: "Q-1", name: "Mahlet Shiferaw", dept: "Internal Medicine", arrived: "08:10", status: "in-service" },
    { id: "Q-2", name: "Kidist Assefa", dept: "Cardiology", arrived: "08:15", status: "waiting" },
    { id: "Q-3", name: "Biruk Ayele", dept: "Pediatrics", arrived: "08:22", status: "waiting" },
    { id: "Q-4", name: "Tewodros Haile", dept: "Cardiology", arrived: "08:30", status: "waiting" },
    { id: "Q-5", name: "Ruth Gebre", dept: "Internal Medicine", arrived: "08:41", status: "waiting" },
    { id: "Q-6", name: "Yohannes Mamo", dept: "Internal Medicine", arrived: "08:47", status: "waiting" }
  ],

  announcements: [
    { id: "AN-1", title: "Emergency: Generator maintenance Friday 22:00", message: "Hospital generator will be serviced on Friday from 22:00 to 23:30. Critical care units will remain on UPS power. Please conserve where possible.", audience: "All staff", author: "Solomon Tadesse", publish_date: "2026-08-11T08:00:00", priority: "urgent", status: "published", views: 132 },
    { id: "AN-2", title: "New blood pressure monitors delivered", message: "10 new digital BP monitors are now available on Ward 2. Sign-out sheet is on the nurses' station.", audience: "Nurses", author: "Marta Tesfaye", publish_date: "2026-08-10T14:30:00", priority: "normal", status: "published", views: 87 },
    { id: "AN-3", title: "Pharmacy stock update: Amoxicillin restocked", message: "Amoxicillin 250mg is back in stock as of this morning. Prescriptions can be filled normally.", audience: "All staff", author: "Yonas Girma", publish_date: "2026-08-10T09:15:00", priority: "important", status: "published", views: 214 },
    { id: "AN-4", title: "Staff training: AI diagnosis tools", message: "Mandatory 1-hour training session on the new AI diagnosis module. Two sessions available: Tuesday 10:00 and Thursday 14:00 in the conference room.", audience: "Doctors", author: "Solomon Tadesse", publish_date: "2026-08-13T10:00:00", priority: "important", status: "scheduled", views: 0 },
    { id: "AN-5", title: "Draft: Q3 staff performance reviews", message: "Q3 performance review cycle starts next month. Please update your self-assessments.", audience: "Managers", author: "Hanna Bekele", publish_date: "2026-08-20T09:00:00", priority: "normal", status: "draft", views: 0 },
    { id: "AN-6", title: "Outpatient clinic closed Sunday", message: "The OPD will be closed this Sunday for fumigation. Emergency department remains open 24/7.", audience: "Patients", author: "Liya Hailu", publish_date: "2026-08-15T08:00:00", priority: "normal", status: "scheduled", views: 0 }
  ],

  referrals: [
    { id: "RF-401", patient: "Selam Tadesse", to: "Dr. Meron Assefa", specialty: "Cardiology", reason: "Recurrent chest pain with abnormal ECG — needs stress test.", priority: "urgent", date: "2026-08-11", status: "pending" },
    { id: "RF-402", patient: "Ruth Gebre", to: "Dr. Girma Tola", specialty: "Nephrology", reason: "Creatinine rising — CKD stage 3, requires specialist review.", priority: "urgent", date: "2026-08-11", status: "accepted" },
    { id: "RF-403", patient: "Dawit Kebede", to: "Dr. Fikru Debebe", specialty: "Pulmonology", reason: "Persistent wheezing despite inhaler therapy.", priority: "routine", date: "2026-08-10", status: "completed" },
    { id: "RF-404", patient: "Tewodros Haile", to: "Dr. Meron Assefa", specialty: "Endocrinology", reason: "Thyroid panel abnormal — suspected subclinical hypothyroidism.", priority: "routine", date: "2026-08-09", status: "pending" },
    { id: "RF-405", patient: "Biruk Ayele", to: "St. Mary's Hospital", specialty: "Pediatric ICU", reason: "Oxygen saturation dropping — transfer for ICU-level care.", priority: "emergency", date: "2026-08-08", status: "completed" },
    { id: "RF-406", patient: "Hana Wolde", to: "Dr. Girma Tola", specialty: "Ophthalmology", reason: "Blurred vision — possible diabetic retinopathy.", priority: "routine", date: "2026-08-07", status: "declined" }
  ],

  purchase_orders: [
    { id: "PO-501", supplier: "PharmaLink Ethiopia", items: ["Paracetamol 500mg — 1000", "ORS Sachets — 500"], total: 18200, date: "2026-08-10", status: "ordered" },
    { id: "PO-502", supplier: "Addis Medical Supply", items: ["Amoxicillin 250mg — 2000"], total: 24500, date: "2026-08-09", status: "ordered" },
    { id: "PO-503", supplier: "United Pharma PLC", items: ["Insulin Glargine — 60", "Ceftriaxone 1g — 300"], total: 38900, date: "2026-08-05", status: "received" },
    { id: "PO-504", supplier: "PharmaLink Ethiopia", items: ["Atorvastatin 20mg — 800"], total: 12400, date: "2026-08-02", status: "received" },
    { id: "PO-505", supplier: "Geda Medical", items: ["IV Dextrose 5% — 200"], total: 9600, date: "2026-07-28", status: "cancelled" }
  ],

  suppliers: [
    { id: "SP-1", name: "PharmaLink Ethiopia", contact: "Mr. Dawit Getachew", phone: "+251 911 000 101", categories: "Analgesics, ORS, Statins", lead_time: 4, rating: 4.6 },
    { id: "SP-2", name: "Addis Medical Supply", contact: "Ms. Tigist Alemu", phone: "+251 911 000 102", categories: "Antibiotics", lead_time: 5, rating: 4.2 },
    { id: "SP-3", name: "United Pharma PLC", contact: "Mr. Samuel Bekele", phone: "+251 911 000 103", categories: "Insulin, IV fluids", lead_time: 7, rating: 4.8 },
    { id: "SP-4", name: "Geda Medical", contact: "Mr. Henok Tesfaye", phone: "+251 911 000 104", categories: "IV fluids, disposables", lead_time: 6, rating: 3.9 },
    { id: "SP-5", name: "Nile Pharma", contact: "Ms. Rahel Abebe", phone: "+251 911 000 105", categories: "Cardiovascular", lead_time: 8, rating: 4.1 },
    { id: "SP-6", name: "Hawassa Medical Center", contact: "Dr. Kalkidan Fikre", phone: "+251 911 000 106", categories: "Respiratory, steroids", lead_time: 5, rating: 4.4 }
  ],

  samples: [
    { id: "S-801", patient: "Abel Mekonnen", test: "Complete Blood Count", type: "Whole blood", collected: "08:10", stage: "completed", tat: "2.8 h" },
    { id: "S-802", patient: "Hana Wolde", test: "Fasting Blood Sugar", type: "Serum", collected: "08:25", stage: "result-ready", tat: "—" },
    { id: "S-803", patient: "Selam Tadesse", test: "Lipid Profile", type: "Serum", collected: "08:40", stage: "processing", tat: "—" },
    { id: "S-804", patient: "Ruth Gebre", test: "Kidney Function", type: "Serum", collected: "08:55", stage: "received", tat: "—" },
    { id: "S-805", patient: "Biruk Ayele", test: "Malaria Test", type: "Whole blood", collected: "09:05", stage: "collected", tat: "—" },
    { id: "S-806", patient: "Yohannes Mamo", test: "HbA1c", type: "Whole blood", collected: "09:15", stage: "processing", tat: "—" },
    { id: "S-807", patient: "Mahlet Shiferaw", test: "Urinalysis", type: "Urine", collected: "09:30", stage: "collected", tat: "—" },
    { id: "S-808", patient: "Tewodros Haile", test: "Thyroid Panel", type: "Serum", collected: "09:45", stage: "result-ready", tat: "—" },
    { id: "S-809", patient: "Kidist Assefa", test: "Complete Blood Count", type: "Whole blood", collected: "10:00", stage: "completed", tat: "3.5 h" },
    { id: "S-810", patient: "Dawit Kebede", test: "Liver Function", type: "Serum", collected: "10:15", stage: "received", tat: "—" }
  ],

  insurance: [
    { id: "IN-1", patient: "Abel Mekonnen", provider: "EHBPA", policy: "EHB-2026-4412", coverage: 80, valid_until: "2027-03-15", status: "verified" },
    { id: "IN-2", patient: "Hana Wolde", provider: "Nyala Insurance", policy: "NYL-8821", coverage: 75, valid_until: "2026-12-01", status: "verified" },
    { id: "IN-3", patient: "Selam Tadesse", provider: "GIB (Global Insurance)", policy: "GIB-5520", coverage: 90, valid_until: "2027-06-20", status: "pending" },
    { id: "IN-4", patient: "Ruth Gebre", provider: "Awash Insurance", policy: "AWS-1124", coverage: 70, valid_until: "2026-09-30", status: "expired" },
    { id: "IN-5", patient: "Yohannes Mamo", provider: "EHBPA", policy: "EHB-2025-7731", coverage: 80, valid_until: "2026-10-12", status: "pending" },
    { id: "IN-6", patient: "Dawit Kebede", provider: "Private (self-pay)", policy: "—", coverage: 0, valid_until: "—", status: "verified" }
  ],

  messages: [
    { id: "MSG-1001", from: "Dr. Daniel Alemu", from_role: "Doctor", subject: "Lab result follow-up", body: "Dear colleague, the HbA1c result for patient Yohannes Mamo (P-1009) came back at 8.2%. Please ensure a dietary review is scheduled and his insulin dose is re-evaluated at the next visit.", date: "2026-08-11T08:40:00", read: false, priority: "high", replies: [] },
    { id: "MSG-1002", from: "Front Desk (Reception)", from_role: "Reception", subject: "Appointment reminder", body: "Reminder: 3 patients are checked in and waiting in the Internal Medicine queue. Please review the queue board when you are free.", date: "2026-08-11T08:15:00", read: false, priority: "normal", replies: [] },
    { id: "MSG-1003", from: "Yonas Girma", from_role: "Pharmacist", subject: "Prescription ready for pickup", body: "Prescription RX-2201 (Amlodipine 5mg × 30 tablets) is ready for pickup at the pharmacy window. The patient has been notified via SMS.", date: "2026-08-11T07:50:00", read: true, priority: "normal", replies: [{ from: "me", body: "Thank you Yonas — I'll let the patient know.", date: "2026-08-11T08:02:00" }] },
    { id: "MSG-1004", from: "Sara Worku", from_role: "Laboratory", subject: "Sample results pending", body: "Two kidney-function samples are still processing. Expected completion within 1 hour. We will notify you as soon as they are released.", date: "2026-08-11T07:30:00", read: false, priority: "normal", replies: [] },
    { id: "MSG-1005", from: "System Administrator", from_role: "System", subject: "Maintenance notice", body: "The hospital system will undergo scheduled maintenance on Saturday from 23:00 to 23:30. Please log out before maintenance begins to avoid losing unsaved work.", date: "2026-08-10T16:00:00", read: true, priority: "high", replies: [] },
    { id: "MSG-1006", from: "Hanna Bekele", from_role: "Manager", subject: "Quarterly report request", body: "Kindly submit your departmental activity summary for Q3 by Friday. The finance and AI insights teams need this data for the executive report.", date: "2026-08-10T11:20:00", read: false, priority: "normal", replies: [] }
  ],

  sent: [
    { id: "SENT-501", to: "Dr. Daniel Alemu", subject: "Re: Lab result follow-up", body: "Noted — the dietary review is scheduled for the next visit and the insulin dose will be re-evaluated.", date: "2026-08-11T09:05:00" },
    { id: "SENT-502", to: "Front Desk (Reception)", subject: "Queue confirmation", body: "Received, we will start with the patients in the Internal Medicine queue shortly.", date: "2026-08-11T08:20:00" },
    { id: "SENT-503", to: "Pharmacy", subject: "Refill confirmation", body: "Thank you for confirming the refill. The patient has been notified.", date: "2026-08-11T07:55:00" }
  ],

  documents: [
    { id: "DOC-1", patient: "Abel Mekonnen", patient_id: "P-1001", type: "Lab Report", title: "Complete Blood Count — 05/08", date: "2026-08-05", size: "214 KB", uploaded_by: "Sara Worku", summary: "All CBC parameters within normal limits." },
    { id: "DOC-2", patient: "Abel Mekonnen", patient_id: "P-1001", type: "Prescription", title: "Prescription RX-2201 — Amlodipine", date: "2026-08-11", size: "86 KB", uploaded_by: "Dr. Daniel Alemu", summary: "Amlodipine 5mg once daily × 30 days." },
    { id: "DOC-3", patient: "Abel Mekonnen", patient_id: "P-1001", type: "Consent Form", title: "Treatment Consent — 2026", date: "2026-01-12", size: "142 KB", uploaded_by: "Liya Hailu", summary: "Signed general treatment & information consent." },
    { id: "DOC-4", patient: "Abel Mekonnen", patient_id: "P-1001", type: "Insurance", title: "EHBPA Policy — 2026", date: "2026-03-01", size: "310 KB", uploaded_by: "Liya Hailu", summary: "EHBPA insurance policy card & terms." },
    { id: "DOC-5", patient: "Abel Mekonnen", patient_id: "P-1001", type: "Referral Letter", title: "Cardiology referral — Aug", date: "2026-08-09", size: "98 KB", uploaded_by: "Dr. Daniel Alemu", summary: "Referred for stress test evaluation." },
    { id: "DOC-6", patient: "Hana Wolde", patient_id: "P-1002", type: "Lab Report", title: "Fasting Blood Sugar — 02/08", date: "2026-08-02", size: "198 KB", uploaded_by: "Sara Worku", summary: "FBS 168 mg/dL — above target." },
    { id: "DOC-7", patient: "Hana Wolde", patient_id: "P-1002", type: "Prescription", title: "Prescription RX-2202 — Metformin", date: "2026-08-11", size: "92 KB", uploaded_by: "Dr. Daniel Alemu", summary: "Metformin 500mg twice daily × 60 days." },
    { id: "DOC-8", patient: "Selam Tadesse", patient_id: "P-1004", type: "Lab Report", title: "Lipid Profile — 09/08", date: "2026-08-09", size: "224 KB", uploaded_by: "Sara Worku", summary: "Elevated total cholesterol and LDL." },
    { id: "DOC-9", patient: "Selam Tadesse", patient_id: "P-1004", type: "Consent Form", title: "Procedure Consent — ECG", date: "2026-06-20", size: "138 KB", uploaded_by: "Liya Hailu", summary: "Signed consent for ECG procedure." },
    { id: "DOC-10", patient: "Ruth Gebre", patient_id: "P-1006", type: "Lab Report", title: "Kidney Function — 08/08", date: "2026-08-08", size: "208 KB", uploaded_by: "Sara Worku", summary: "Creatinine 2.1 mg/dL — elevated, monitor." }
  ],

  complaints: [
    { id: "CMP-101", reporter: "Abel Mekonnen", reporter_role: "patient", category: "Billing", subject: "Incorrect charge on my invoice", description: "I was charged 500 ETB for an ECG that was not performed during my last visit on 05/08. The cashier said to contact the manager, so here I am.", priority: "high", date: "2026-08-10T09:30:00", status: "resolved", solution: "We reviewed your account and found the ECG charge was added by mistake. The 500 ETB has been refunded and will appear as a credit on your next bill. Apologies for the inconvenience.", resolved_by: "Hanna Bekele", resolved_date: "2026-08-11T08:00:00" },
    { id: "CMP-102", reporter: "Abel Mekonnen", reporter_role: "patient", category: "Service Quality", subject: "Long waiting time at OPD", description: "I waited over 2 hours at the OPD despite having a confirmed 09:00 appointment. This is the second time this month.", priority: "normal", date: "2026-08-09T14:00:00", status: "in-review", solution: "" },
    { id: "CMP-103", reporter: "Hana Wolde", reporter_role: "patient", category: "Facility / Cleanliness", subject: "Broken fan in waiting area", description: "The ceiling fan in the OPD waiting area has been broken for over a week. It is very hot for patients, especially mothers with children.", priority: "normal", date: "2026-08-08T10:00:00", status: "pending", solution: "" },
    { id: "CMP-104", reporter: "Abel Mekonnen", reporter_role: "patient", category: "Staff Conduct", subject: "Unhelpful front desk staff", description: "The receptionist on duty at 08:00 was dismissive when I asked about rescheduling my appointment. I felt unheard.", priority: "high", date: "2026-08-07T11:00:00", status: "pending", solution: "" },
    { id: "CMP-105", reporter: "Selam Tadesse", reporter_role: "patient", category: "Treatment / Care", subject: "Dizziness with new medication", description: "Since starting the new blood pressure medication I have been feeling dizzy in the morning. Should I continue taking it?", priority: "urgent", date: "2026-08-06T16:00:00", status: "resolved", solution: "Reviewed with Dr. Meron Assefa: the dizziness is a known side effect. Your dose has been reduced to half a tablet and we recommend follow-up in 3 days. If dizziness persists or worsens, come to the emergency department.", resolved_by: "Hanna Bekele", resolved_date: "2026-08-07T09:00:00" }
  ],

  shifts: [
    { id: "SH-1", name: "Morning", start: "07:00", end: "15:00", color: "#1A6FA8", css: "morning", workers: 34 },
    { id: "SH-2", name: "Evening", start: "15:00", end: "23:00", color: "#B45309", css: "evening", workers: 22 },
    { id: "SH-3", name: "Night", start: "23:00", end: "07:00", color: "#7C3AED", css: "night", workers: 15 },
    { id: "SH-4", name: "Day (OPD)", start: "08:00", end: "17:00", color: "#0F9D5C", css: "day", workers: 18 },
    { id: "SH-5", name: "Half-day", start: "08:00", end: "13:00", color: "#0891B2", css: "half", workers: 6 }
  ],

  roster: [
    { id: "RO-1", staff: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-11", shift: "Morning", start: "07:00", end: "15:00" },
    { id: "RO-2", staff: "Dr. Fikru Debebe", dept: "Pediatrics", date: "2026-08-11", shift: "Morning", start: "07:00", end: "15:00" },
    { id: "RO-3", staff: "Dr. Meron Assefa", dept: "Cardiology", date: "2026-08-11", shift: "Evening", start: "15:00", end: "23:00" },
    { id: "RO-4", staff: "Marta Tesfaye", dept: "Internal Medicine", date: "2026-08-11", shift: "Morning", start: "07:00", end: "15:00" },
    { id: "RO-5", staff: "Bethelehem Girma", dept: "Pediatrics", date: "2026-08-11", shift: "Morning", start: "07:00", end: "15:00" },
    { id: "RO-6", staff: "Yonas Girma", dept: "Pharmacy", date: "2026-08-11", shift: "Morning", start: "07:00", end: "15:00" },
    { id: "RO-7", staff: "Sara Worku", dept: "Laboratory", date: "2026-08-11", shift: "Morning", start: "07:00", end: "15:00" },
    { id: "RO-8", staff: "Liya Hailu", dept: "Front Desk", date: "2026-08-11", shift: "Morning", start: "07:00", end: "15:00" },
    { id: "RO-9", staff: "Kaleb Teshome", dept: "Pharmacy", date: "2026-08-11", shift: "Evening", start: "15:00", end: "23:00" },
    { id: "RO-10", staff: "Hanna Bekele", dept: "Management", date: "2026-08-11", shift: "Day (OPD)", start: "08:00", end: "17:00" }
  ],

  attendance: [
    { id: "AT-1", staff: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-11", shift: "Morning", check_in: "06:52", check_out: null, status: "present", source: "fingerprint", device: "FP-01" },
    { id: "AT-2", staff: "Dr. Fikru Debebe", dept: "Pediatrics", date: "2026-08-11", shift: "Morning", check_in: "06:58", check_out: null, status: "present", source: "fingerprint", device: "FP-01" },
    { id: "AT-3", staff: "Dr. Meron Assefa", dept: "Cardiology", date: "2026-08-11", shift: "Evening", check_in: "14:52", check_out: null, status: "present", source: "fingerprint", device: "FP-02" },
    { id: "AT-4", staff: "Marta Tesfaye", dept: "Internal Medicine", date: "2026-08-11", shift: "Morning", check_in: "07:05", check_out: null, status: "late", source: "fingerprint", device: "FP-01" },
    { id: "AT-5", staff: "Bethelehem Girma", dept: "Pediatrics", date: "2026-08-11", shift: "Morning", check_in: null, check_out: null, status: "absent", source: "fingerprint", device: "FP-01" },
    { id: "AT-6", staff: "Yonas Girma", dept: "Pharmacy", date: "2026-08-11", shift: "Morning", check_in: "07:12", check_out: null, status: "late", source: "fingerprint", device: "FP-04" },
    { id: "AT-7", staff: "Sara Worku", dept: "Laboratory", date: "2026-08-11", shift: "Morning", check_in: "06:48", check_out: null, status: "present", source: "fingerprint", device: "FP-05" },
    { id: "AT-8", staff: "Liya Hailu", dept: "Front Desk", date: "2026-08-11", shift: "Morning", check_in: "06:45", check_out: null, status: "present", source: "fingerprint", device: "FP-01" },
    { id: "AT-9", staff: "Kaleb Teshome", dept: "Pharmacy", date: "2026-08-11", shift: "Evening", check_in: "15:02", check_out: null, status: "present", source: "fingerprint", device: "FP-04" },
    { id: "AT-10", staff: "Hanna Bekele", dept: "Management", date: "2026-08-11", shift: "Day (OPD)", check_in: "08:10", check_out: null, status: "late", source: "fingerprint", device: "FP-01" },
    { id: "AT-11", staff: "Solomon Tadesse", dept: "Administration", date: "2026-08-11", shift: "Day (OPD)", check_in: "07:55", check_out: null, status: "present", source: "fingerprint", device: "FP-01" },
    // history (past days)
    { id: "AT-21", staff: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-10", shift: "Morning", check_in: "06:55", check_out: "15:05", status: "present", source: "fingerprint", device: "FP-01" },
    { id: "AT-22", staff: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-09", shift: "Morning", check_in: "07:10", check_out: "15:00", status: "late", source: "fingerprint", device: "FP-01" },
    { id: "AT-23", staff: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-08", shift: "Evening", check_in: "14:58", check_out: "23:05", status: "present", source: "fingerprint", device: "FP-02" },
    { id: "AT-24", staff: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-07", shift: "Morning", check_in: "06:50", check_out: "15:02", status: "present", source: "fingerprint", device: "FP-01" },
    { id: "AT-25", staff: "Dr. Daniel Alemu", dept: "Internal Medicine", date: "2026-08-06", shift: "Morning", check_in: null, check_out: null, status: "leave", source: "manual", device: null },
    { id: "AT-26", staff: "Marta Tesfaye", dept: "Internal Medicine", date: "2026-08-10", shift: "Morning", check_in: "07:02", check_out: "15:06", status: "present", source: "fingerprint", device: "FP-01" },
    { id: "AT-27", staff: "Yonas Girma", dept: "Pharmacy", date: "2026-08-10", shift: "Morning", check_in: "07:18", check_out: "15:10", status: "late", source: "fingerprint", device: "FP-04" },
    { id: "AT-28", staff: "Sara Worku", dept: "Laboratory", date: "2026-08-10", shift: "Morning", check_in: "06:44", check_out: "15:00", status: "present", source: "fingerprint", device: "FP-05" },
    { id: "AT-29", staff: "Liya Hailu", dept: "Front Desk", date: "2026-08-10", shift: "Morning", check_in: "06:50", check_out: "15:04", status: "present", source: "fingerprint", device: "FP-01" },
    { id: "AT-30", staff: "Bethelehem Girma", dept: "Pediatrics", date: "2026-08-10", shift: "Morning", check_in: "07:00", check_out: "15:00", status: "present", source: "fingerprint", device: "FP-01" }
  ],

  devices: [
    { id: "FP-01", name: "Main Entrance", model: "ZKTeco MB20", location: "Hospital Main Gate", status: "online", enrolled: 96, last_sync: "2026-08-11T08:05:00", auto: true },
    { id: "FP-02", name: "Staff Wing — Ground", model: "ZKTeco UA760", location: "Staff Block A", status: "online", enrolled: 48, last_sync: "2026-08-11T08:02:00", auto: true },
    { id: "FP-03", name: "Ward 2 Access", model: "ZKTeco F18", location: "Nursing Station Ward 2", status: "online", enrolled: 61, last_sync: "2026-08-11T07:58:00", auto: true },
    { id: "FP-04", name: "Pharmacy Gate", model: "ZKTeco MB20", location: "Pharmacy", status: "warning", enrolled: 12, last_sync: "2026-08-11T07:30:00", auto: true },
    { id: "FP-05", name: "Laboratory Entry", model: "ZKTeco UA760", location: "Lab Block", status: "online", enrolled: 9, last_sync: "2026-08-11T08:00:00", auto: true }
  ],

  videos: [
    // --- Verified YouTube video IDs (public health-education channels) ---
    { id: "V-1", title: "Mayo Clinic Explains Hypertension", channel: "Mayo Clinic", video_id: "r5XTTeP039Q", embeddable: true, search: "", conditions: ["hypertension", "heart disease", "ckd"], duration: "6:12", views: "1.4M", category: "Understanding the condition", description: "Dr. Leslie Thomas walks through what high blood pressure is, its risks, and how to manage it." },
    { id: "V-2", title: "Understanding Type 2 Diabetes — Animated Patient Education", channel: "Animated Diabetes Patient", video_id: "JAjZv41iUJU", search: "", conditions: ["diabetes", "diabetes type 2"], duration: "~5 min", views: "1.2M", category: "Understanding the condition", description: "What happens in the body with type 2 diabetes, and why blood sugar control matters.", embeddable: true },
    { id: "V-3", title: "How to Measure Your Blood Sugar", channel: "Mayo Clinic", video_id: "nxIJeHWlhF4", embeddable: true, search: "", conditions: ["diabetes", "diabetes type 2"], duration: "2:55", views: "720K", category: "Self-care", description: "A certified diabetes educator demonstrates how to check your blood sugar correctly." },
    { id: "V-4", title: "Malaria — Osmosis Study Video", channel: "Osmosis from Elsevier", video_id: "3_2TnCqBFcY", embeddable: true, search: "", conditions: ["malaria", "fever"], duration: "9:12", views: "2.1M", category: "Understanding the condition", description: "How malaria spreads through mosquitoes, its symptoms, and prevention." },
    { id: "V-5", title: "Coronary Artery Disease — Signs, Causes, Prevention", channel: "Cleveland Clinic", video_id: "xSx3F9sswyE", embeddable: true, search: "", conditions: ["heart disease", "cad"], duration: "8:40", views: "1.1M", category: "Understanding the condition", description: "Learn about coronary artery disease, its risk factors, and how to prevent it." },
    { id: "V-6", title: "Coronary Artery Disease: Symptoms, Causes, Treatments", channel: "Mass General Brigham", video_id: "5YZPM8F-A9A", embeddable: true, search: "", conditions: ["heart disease", "cad", "chest pain"], duration: "5:30", views: "640K", category: "Understanding the condition", description: "Dr. Farouc Jaffer explains CAD symptoms, causes, and treatment options." },
    { id: "V-7", title: "Tuberculosis (TB) Symptoms Animation", channel: "Health Animations", video_id: "VnF47GGAU8g", embeddable: true, search: "", conditions: ["tb", "tuberculosis", "cough"], duration: "2:20", views: "810K", category: "Understanding the condition", description: "A visual guide to the common symptoms of TB and when to see a doctor." },
    { id: "V-8", title: "How the Body Reacts to Tuberculosis", channel: "Health Animations", video_id: "hTscEEWD5Ho", embeddable: true, search: "", conditions: ["tb", "tuberculosis"], duration: "3:05", views: "450K", category: "Understanding the condition", description: "How the TB bacterium spreads and how your body fights it." },

    // --- Search-linked suggestions (open targeted YouTube search — always free, no key) ---
    { id: "V-9", title: "What is Asthma? — Patient Education", channel: "YouTube Health Education", video_id: null, search: "what is asthma patient education video", conditions: ["asthma"], duration: "~4 min", views: "—", category: "Understanding the condition", description: "Understand asthma triggers, inhaler use, and when to seek urgent care." },
    { id: "V-10", title: "Chronic Kidney Disease Explained", channel: "YouTube Health Education", video_id: null, search: "chronic kidney disease patient education video", conditions: ["ckd", "kidney disease"], duration: "~6 min", views: "—", category: "Understanding the condition", description: "How CKD develops, diet advice, and protecting your kidneys." },
    { id: "V-11", title: "Understanding Hypothyroidism / Thyroid Disorders", channel: "YouTube Health Education", video_id: null, search: "hypothyroidism patient education video", conditions: ["thyroid", "thyroid disorder", "hypothyroidism"], duration: "~5 min", views: "—", category: "Understanding the condition", description: "Symptoms of an underactive thyroid and how treatment works." },
    { id: "V-12", title: "Anemia — Symptoms and Diet", channel: "YouTube Health Education", video_id: null, search: "anemia symptoms iron rich diet patient education", conditions: ["anemia", "fatigue"], duration: "~4 min", views: "—", category: "Self-care", description: "Recognize anemia, iron-rich foods, and when to see a doctor." },
    { id: "V-13", title: "Typhoid Fever — Prevention", channel: "YouTube Health Education", video_id: null, search: "typhoid fever prevention clean water patient education", conditions: ["typhoid", "fever"], duration: "~3 min", views: "—", category: "Prevention", description: "How typhoid spreads, safe water and food habits, and vaccination." },
    { id: "V-14", title: "Eating Healthy with Diabetes", channel: "YouTube Health Education", video_id: null, search: "healthy eating diet for diabetes patient education", conditions: ["diabetes", "diabetes type 2", "healthy diet"], duration: "~6 min", views: "—", category: "Diet & lifestyle", description: "Practical food choices to keep blood sugar stable." },
    { id: "V-15", title: "How to Use an Inhaler Correctly", channel: "YouTube Health Education", video_id: null, search: "how to use metered dose inhaler correctly", conditions: ["asthma"], duration: "~2 min", views: "—", category: "Self-care", description: "Step-by-step inhaler technique for better asthma control." },
    { id: "V-16", title: "Medication Adherence — Why It Matters", channel: "YouTube Health Education", video_id: null, search: "why medication adherence matters patient education", conditions: ["hypertension", "diabetes", "thyroid", "heart disease"], duration: "~3 min", views: "—", category: "Self-care", description: "Simple routines to never miss your medicines." },
    { id: "V-17", title: "Healthy Pregnancy & Nutrition", channel: "YouTube Health Education", video_id: null, search: "healthy pregnancy nutrition patient education", conditions: ["pregnancy", "maternity"], duration: "~7 min", views: "—", category: "Diet & lifestyle", description: "Nutrition and care advice for a healthy pregnancy." },
    { id: "V-18", title: "Managing Stress & Mental Health", channel: "YouTube Health Education", video_id: null, search: "managing stress mental health self care", conditions: ["stress", "mental health", "anxiety"], duration: "~5 min", views: "—", category: "Wellness", description: "Simple daily habits to reduce stress and protect mental health." }
  ],

  extra_videos: [
    { id: "V-19", title: "Fatty Liver Disease — Causes, Diagnosis and Treatment", channel: "The Ottawa Hospital", video_id: "re4yEU8UGWo", search: "", conditions: ["liver", "liver disease", "fatty liver", "liver problem"], duration: "~4 min", views: "1.5M", category: "Understanding the condition", description: "A hepatologist explains fatty liver disease (MASLD) — causes, symptoms and how it is managed.", embeddable: true },
    { id: "V-20", title: "Liver Disease — Mayo Clinic", channel: "Mayo Clinic", video_id: "SUAugMHDnOw", search: "", conditions: ["liver", "liver disease", "hepatitis", "cirrhosis", "liver cancer", "jaundice"], duration: "5:10", views: "1.2M", category: "Understanding the condition", description: "A Mayo Clinic hepatologist discusses liver disease — including the most common forms and warning signs.", embeddable: true },
    { id: "V-21", title: "The ABCs of Hepatitis — Causes, Symptoms & Treatment", channel: "Health Education", video_id: "TtfJmux3aiM", search: "", conditions: ["hepatitis", "liver", "liver disease", "jaundice", "yellow eyes"], duration: "4:20", views: "680K", category: "Understanding the condition", description: "Hepatitis causes liver inflammation — often silent but serious. Learn the A, B, C types and how they spread.", embeddable: true },
    { id: "V-22", title: "What is Diarrhea? — Causes, Signs, Symptoms & Treatment", channel: "Medical Centric", video_id: "EGtihfAhd_c", search: "", conditions: ["diarrhea", "diarrhoea", "loose stool", "gastroenteritis", "food poisoning", "stomach", "dehydration", "vomiting"], duration: "3:15", views: "2.4M", category: "Understanding the condition", description: "What causes diarrhea, when it is dangerous, and how to prevent dehydration — especially for children.", embeddable: true },
    { id: "V-23", title: "Pneumonia: Causes, Symptoms, Diagnosis & Treatments", channel: "Level Up RN (Ask A Nurse)", video_id: "vp8FXgcunfE", search: "", conditions: ["pneumonia", "cough", "breathing", "chest infection", "lungs", "fever"], duration: "7:10", views: "890K", category: "Understanding the condition", description: "What pneumonia is, its signs and symptoms, and when you need urgent care.", embeddable: true },
    { id: "V-24", title: "Pneumonia — Overview", channel: "Ninja Nerd", video_id: "lzyUVVOqyS0", search: "", conditions: ["pneumonia", "lungs", "cough", "breathing", "chest pain"], duration: "~6 min", views: "1.1M", category: "Understanding the condition", description: "A detailed but clear overview of pneumonia and how it affects the lungs.", embeddable: true },
    { id: "V-25", title: "Stroke Education — Causes and Effects", channel: "Health Education", video_id: "DrPXM-LFATA", search: "", conditions: ["stroke", "brain", "paralysis", "numbness", "weakness", "face drooping"], duration: "5:30", views: "1.8M", category: "Understanding the condition", description: "What happens during a stroke, the FAST warning signs, and how to prevent one.", embeddable: true },
    { id: "V-26", title: "What is a Migraine? — Osmosis", channel: "Osmosis from Elsevier", video_id: "DMhKBUgizO8", search: "", conditions: ["migraine", "headache", "head pain", "nausea"], duration: "6:20", views: "950K", category: "Understanding the condition", description: "Why migraines happen and what is different about them compared to normal headaches.", embeddable: true },
    { id: "V-27", title: "Rheumatoid Arthritis — Disease Overview", channel: "Johns Hopkins Rheumatology", video_id: "7PRe46JE3sE", search: "", conditions: ["arthritis", "rheumatoid", "joint pain", "joints", "swelling"], duration: "~4 min", views: "760K", category: "Understanding the condition", description: "What happens in the joints with rheumatoid arthritis and how treatment works.", embeddable: true },
    { id: "V-28", title: "Rheumatoid Arthritis — Signs & Symptoms", channel: "Johns Hopkins Rheumatology", video_id: "iBV6dhEUdpc", search: "", conditions: ["arthritis", "rheumatoid", "joint pain", "morning stiffness"], duration: "~3 min", views: "540K", category: "Understanding the condition", description: "Recognize the early signs of rheumatoid arthritis — swelling, stiffness and fatigue.", embeddable: true },
    { id: "V-29", title: "Understanding Cholesterol", channel: "Patient Education Animation", video_id: "_qzT246x8DE", search: "", conditions: ["cholesterol", "heart", "heart disease", "blood pressure", "fats", "lipid"], duration: "3:45", views: "1.3M", category: "Understanding the condition", description: "What high cholesterol means for your heart and how it is caused.", embeddable: true },
    { id: "V-30", title: "Understanding Kidney Stones", channel: "Zero To Finals", video_id: "DK9AkAVDoho", search: "", conditions: ["kidney stones", "kidney", "stones", "urine", "back pain", "flank pain", "uti"], duration: "6:10", views: "1.6M", category: "Understanding the condition", description: "How kidney stones form, the pain they cause, and how they are treated.", embeddable: true }
  ],

  vitals_history: {
    "P-1004": [
      { t: "06:00", hr: 88, sys: 148, dia: 92, temp: 36.8, spo2: 96, rr: 18 },
      { t: "08:00", hr: 92, sys: 152, dia: 94, temp: 36.9, spo2: 95, rr: 19 },
      { t: "10:00", hr: 90, sys: 145, dia: 90, temp: 36.7, spo2: 96, rr: 18 },
      { t: "12:00", hr: 95, sys: 158, dia: 98, temp: 37.0, spo2: 94, rr: 20 },
      { t: "14:00", hr: 91, sys: 150, dia: 93, temp: 36.9, spo2: 95, rr: 18 },
      { t: "16:00", hr: 89, sys: 146, dia: 91, temp: 36.8, spo2: 96, rr: 18 },
      { t: "18:00", hr: 93, sys: 154, dia: 95, temp: 37.0, spo2: 95, rr: 19 },
      { t: "20:00", hr: 90, sys: 149, dia: 92, temp: 36.9, spo2: 96, rr: 18 }
    ]
  }
};

// ============================================================
// DEMO DATA SEED — relative to "today", so every page always
// looks alive (today's appointments, recent lab results, fresh
// messages, this week's roster, last month's attendance…).
// Deterministic (seeded) so demo screenshots stay consistent.
// ============================================================
(function seedDemoData() {
  var __s = 20260830;
  function rnd() { __s = (__s * 1103515245 + 12345) % 2147483648; return __s / 2147483648; }
  function ri(n) { return Math.floor(rnd() * n); }
  function pick(a) { return a[ri(a.length)]; }
  function iso(d) { return d.toISOString().slice(0, 10); }
  function D(off) { var d = new Date(); d.setDate(d.getDate() + off); return iso(d); }
  function DT(off, hhmm) { return D(off) + "T" + (hhmm || "09:00") + ":00"; }

  var TIMES = ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "14:00", "14:30", "15:00", "15:30", "16:00"];
  var DOCS = [
    { n: "Dr. Daniel Alemu", dept: "Internal Medicine" },
    { n: "Dr. Fikru Debebe", dept: "Pediatrics" },
    { n: "Dr. Meron Assefa", dept: "Cardiology" },
    { n: "Dr. Girma Tola", dept: "Orthopedics" },
    { n: "Dr. Natnael Fekadu", dept: "Emergency" },
    { n: "Dr. Tsehay Mengistu", dept: "Maternity" }
  ];
  var NURSES = ["Marta Tesfaye", "Bethelehem Girma", "Rahel Demissie"];

  // ---------- 6 extra patients (full directory) ----------
  var EXTRA_P = [
    { id: "P-1011", first_name: "Meron", last_name: "Getachew", age: 41, gender: "Female", phone: "+251 912 222 111", email: "meron.g@mail.com", blood: "O+", address: "Sodo, Wolaita", emergency: "+251 912 222 122", condition: "Anemia", status: "active" },
    { id: "P-1012", first_name: "Sileshi", last_name: "Berta", age: 52, gender: "Male", phone: "+251 913 333 222", email: "sileshi.b@mail.com", blood: "B+", address: "Damot, Wolaita", emergency: "+251 913 333 233", condition: "Tuberculosis", status: "active" },
    { id: "P-1013", first_name: "Amina", last_name: "Mohammed", age: 26, gender: "Female", phone: "+251 914 444 333", email: "amina.m@mail.com", blood: "A-", address: "Humbo, Wolaita", emergency: "+251 914 444 344", condition: "Malaria (recovering)", status: "active" },
    { id: "P-1014", first_name: "Chala", last_name: "Desta", age: 35, gender: "Male", phone: "+251 915 555 444", email: "chala.d@mail.com", blood: "AB+", address: "Boditi, Wolaita", emergency: "+251 915 555 455", condition: "Typhoid Fever", status: "active" },
    { id: "P-1015", first_name: "Tigist", last_name: "Woldu", age: 29, gender: "Female", phone: "+251 916 666 555", email: "tigist.w@mail.com", blood: "O-", address: "Sodo, Wolaita", emergency: "+251 916 666 566", condition: "Maternity (prenatal)", status: "active" },
    { id: "P-1016", first_name: "Meseret", last_name: "Fikru", age: 63, gender: "Female", phone: "+251 917 777 666", email: "meseret.f@mail.com", blood: "B-", address: "Areka, Wolaita", emergency: "+251 917 777 677", condition: "Osteoarthritis", status: "active" }
  ];
  EXTRA_P.forEach(function (p) { p.last_visit = D(-ri(9)); MOCK.patients.push(p); });
  var ALLP = MOCK.patients;
  function pIdx() { return ri(ALLP.length); }

  // ---------- appointments: today (+8), next days, past (with no-shows) ----------
  var apptTypes = ["Consultation", "Follow-up", "New patient", "Teleconsult", "Walk-in"];
  var apptStatus = ["confirmed", "confirmed", "checked-in", "completed", "cancelled"];
  var nAppt = 0;
  function mkAppt(dayOff, forceStatus) {
    var p = ALLP[pIdx()];
    var d = DOCS[ri(DOCS.length)];
    var st = forceStatus || apptStatus[ri(apptStatus.length)];
    MOCK.appointments.push({
      id: "A-60" + (nAppt++),
      patient: p.first_name + " " + p.last_name, patient_id: p.id,
      doctor: d.n, dept: d.dept, date: D(dayOff), time: TIMES[ri(TIMES.length)],
      type: apptTypes[ri(apptTypes.length)], status: st,
      no_show: st === "cancelled" ? ri(45) : 3 + ri(38)
    });
  }
  for (var i = 0; i < 9; i++) mkAppt(0);            // today
  for (i = 0; i < 6; i++) mkAppt(1 + ri(2));        // next days
  for (i = 0; i < 8; i++) mkAppt(6 + ri(4));        // next week
  for (i = 0; i < 7; i++) mkAppt(-(1 + ri(6)));     // past

  // ---------- prescriptions ----------
  var drugLib = [
    ["Amoxicillin 500mg", "1 capsule", "Three times daily", "7 days"],
    ["Ibuprofen 400mg", "1 tablet", "Twice daily", "5 days"],
    ["Omeprazole 20mg", "1 capsule", "Once daily before breakfast", "14 days"],
    ["Doxycycline 100mg", "1 tablet", "Once daily", "10 days"],
    ["Azithromycin 500mg", "1 tablet", "Once daily", "3 days"],
    ["Metronidazole 400mg", "1 tablet", "Three times daily", "7 days"],
    ["Vitamin B12 1000mcg", "1 tablet", "Once daily", "30 days"],
    ["Ferrous Sulfate 200mg", "1 tablet", "Twice daily with food", "60 days"],
    ["Paracetamol 500mg", "1 tablet", "Up to 3 times daily", "5 days"],
    ["Amlodipine 10mg", "1 tablet", "Once daily", "30 days"]
  ];
  for (i = 0; i < 8; i++) {
    var rp = ALLP[pIdx()];
    var rd = DOCS[ri(DOCS.length)];
    var drugs = [];
    var nDrugs = 1 + ri(2);
    for (var d2 = 0; d2 < nDrugs; d2++) {
      var dl = drugLib[ri(drugLib.length)];
      drugs.push({ name: dl[0], dose: dl[1], freq: dl[2], duration: dl[3] });
    }
    MOCK.prescriptions.push({ id: "RX-22" + (11 + i), patient: rp.first_name + " " + rp.last_name, doctor: rd.n, date: D(-ri(3)), drugs: drugs, status: "active" });
  }

  // ---------- inventory (round out to the Prophet-forecasted drugs) ----------
  [
    { id: "I-013", name: "Ibuprofen 400mg", category: "Analgesic", stock: 190, unit: "tablets", expiry: D(120), status: "in-stock" },
    { id: "I-014", name: "Omeprazole 20mg", category: "Gastro", stock: 58, unit: "capsules", expiry: D(45), status: "low-stock" },
    { id: "I-015", name: "Doxycycline 100mg", category: "Antibiotic", stock: 96, unit: "capsules", expiry: D(90), status: "in-stock" },
    { id: "I-016", name: "Metronidazole 400mg", category: "Antibiotic", stock: 12, unit: "tablets", expiry: D(25), status: "low-stock" },
    { id: "I-017", name: "Azithromycin 500mg", category: "Antibiotic", stock: 0, unit: "tablets", expiry: D(15), status: "out-of-stock" },
    { id: "I-018", name: "Ferrous Sulfate 200mg", category: "Supplement", stock: 240, unit: "tablets", expiry: D(200), status: "in-stock" },
    { id: "I-019", name: "Vitamin B12 1000mcg", category: "Supplement", stock: 141, unit: "tablets", expiry: D(160), status: "in-stock" }
  ].forEach(function (x) { MOCK.inventory.push(x); });

  // ---------- lab requests & results (recent) ----------
  var tests = ["Complete Blood Count", "Fasting Blood Sugar", "Lipid Profile", "Thyroid Panel", "Urinalysis", "Malaria Test", "Liver Function", "Kidney Function", "HbA1c"];
  var prio = ["Routine", "Urgent", "Routine", "Urgent"];
  for (i = 0; i < 8; i++) {
    var lp = ALLP[pIdx()];
    MOCK.lab_requests.push({ id: "LR-34" + i, patient: lp.first_name + " " + lp.last_name, test: tests[ri(tests.length)], doctor: DOCS[ri(DOCS.length)].n, date: D(ri(2) === 0 ? 0 : -1), priority: prio[ri(prio.length)], status: ["pending", "in-progress", "completed"][ri(3)] });
  }
  var valueSets = {
    "Complete Blood Count": [
      { name: "Hemoglobin", range: "13.5 – 17.5 g/dL", value: "11.2 g/dL", status: "low" },
      { name: "WBC", range: "4.0 – 11.0 ×10³/µL", value: "7.1 ×10³/µL", status: "normal" },
      { name: "RBC", range: "4.5 – 5.9 ×10⁶/µL", value: "4.1 ×10⁶/µL", status: "low" }
    ],
    "Fasting Blood Sugar": [{ name: "Glucose (Fasting)", range: "70 – 100 mg/dL", value: "126 mg/dL", status: "high" }],
    "Lipid Profile": [
      { name: "Total Cholesterol", range: "< 200 mg/dL", value: "238 mg/dL", status: "high" },
      { name: "LDL", range: "< 100 mg/dL", value: "151 mg/dL", status: "high" },
      { name: "HDL", range: "> 40 mg/dL", value: "44 mg/dL", status: "normal" }
    ],
    "Thyroid Panel": [{ name: "TSH", range: "0.4 – 4.0 mIU/L", value: "6.2 mIU/L", status: "high" }],
    "Liver Function": [
      { name: "ALT", range: "7 – 56 U/L", value: "72 U/L", status: "high" },
      { name: "AST", range: "10 – 40 U/L", value: "61 U/L", status: "high" }
    ],
    "Kidney Function": [
      { name: "Creatinine", range: "0.7 – 1.3 mg/dL", value: "2.1 mg/dL", status: "high" }
    ],
    "Urinalysis": [{ name: "Protein", range: "Negative", value: "Trace", status: "abnormal" }],
    "Malaria Test": [{ name: "Malaria Antigen", range: "Negative", value: "Positive", status: "abnormal" }],
    "HbA1c": [{ name: "HbA1c", range: "4.0 – 5.6 %", value: "7.9 %", status: "abnormal" }]
  };
  var resN = 0;
  for (i = 0; i < 9; i++) {
    var lt = tests[ri(tests.length)];
    var lv = valueSets[lt];
    var abn = lv.some(function (v) { return v.status !== "normal"; });
    MOCK.lab_results.push({
      id: "R-91" + (resN++), patient: (b => b.first_name + " " + b.last_name)(ALLP[pIdx()]),
      test: lt, date: D(-(1 + ri(4))), status: abn ? "abnormal" : "normal", ai_flag: abn ? "abnormal" : "normal",
      values: lv
    });
  }

  // ---------- medications (today's shift) ----------
  var medState = ["administered", "pending", "pending", "pending", "missed"];
  for (i = 0; i < 9; i++) {
    var mp = ALLP[pIdx()];
    var md = drugLib[ri(drugLib.length)];
    var st2 = medState[ri(medState.length)];
    MOCK.medications.push({ id: "M-" + (10 + i), patient: mp.first_name + " " + mp.last_name, drug: md[0], dose: md[1], due: TIMES[2 + ri(6)], status: st2, time: st2 === "administered" ? "0" + (7 + ri(2)) + ":" + (10 + ri(40)) : "" });
  }

  // ---------- care plans ----------
  [
    { patient: "Meron Getachew", plan: "Iron-deficiency anemia treatment", steps: ["Oral iron twice daily", "Diet: iron-rich foods", "Repeat CBC in 4 weeks"] },
    { patient: "Sileshi Berta", plan: "TB DOTS therapy", steps: ["Daily supervised dose", "Sputum check monthly", "Nutrition support"] },
    { patient: "Meseret Fikru", plan: "Osteoarthritis pain management", steps: ["Physiotherapy 3×/week", "Weight management", "Joint protection advice"] }
  ].forEach(function (cp, ci) { MOCK.care_plans.push({ id: "CP-" + (5 + ci), patient: cp.patient, plan: cp.plan, created: D(-20), updated: D(-ri(3)), status: "in-progress", steps: cp.steps }); });

  // ---------- bills (last 10 days, mixed statuses) ----------
  var billDesc = ["Consultation — Internal Medicine", "Consultation — Pediatrics", "Complete Blood Count", "Chest X-ray", "ECG — Cardiology", "Prescription — Antibiotics", "Inpatient ward — 1 night", "IV fluids & infusion set", "Physiotherapy session", "Surgical dressing pack", "Malaria RDT", "Ultrasound — Abdomen"];
  var billStatus = ["paid", "paid", "pending", "pending", "overdue", "paid", "pending"];
  for (i = 0; i < 12; i++) {
    MOCK.bills.push({ id: "B-71" + (1 + i), date: D(-ri(9)), description: billDesc[ri(billDesc.length)], amount: [250, 350, 500, 800, 180, 1200, 650, 300][ri(8)], status: billStatus[ri(billStatus.length)] });
  }

  // ---------- audit logs (today) ----------
  var auditActs = [
    ["Dr. Daniel Alemu", "doctor", "create", "Created prescription RX-22" + (11 + ri(8))],
    ["Yonas Girma", "pharmacist", "update", "Dispensed medication M-" + (10 + ri(9))],
    ["Sara Worku", "laboratory", "create", "Uploaded lab result R-91" + ri(9)],
    ["Liya Hailu", "reception", "create", "Registered new patient P-101" + (1 + ri(6))],
    ["Marta Tesfaye", "nurse", "update", "Recorded vitals for patient"],
    ["unknown", "—", "login", ""]
  ];
  for (i = 0; i < 8; i++) {
    var aa = auditActs[ri(auditActs.length)];
    MOCK.audit_logs.push({ id: "AL-1" + (1 + i), ts: DT(0, "0" + (6 + ri(3)) + ":" + (10 + ri(45))), user: aa[0], role: aa[1], action: aa[2], ip: "196.188.24." + (10 + ri(200)), status: aa[0] === "unknown" ? "failed" : "success", detail: aa[3] || "" });
  }

  // ---------- queue (today walk-ins) ----------
  var qNames = ALLP.slice(4, 16);
  for (i = 0; i < 6; i++) {
    var qp = qNames[ri(qNames.length)];
    MOCK.queue.push({ id: "Q-" + (7 + i), name: qp.first_name + " " + qp.last_name, dept: DOCS[ri(DOCS.length)].dept, arrived: "0" + (9 + ri(2)) + ":" + (10 + ri(45)), status: i < 2 ? "in-service" : "waiting" });
  }

  // ---------- announcements (fresh) ----------
  [
    { title: "Blood donation drive — this Saturday", message: "The Ethiopian Red Cross will run a blood donation drive at the hospital main hall this Saturday from 08:00 to 14:00. Staff and visitors are encouraged to donate.", audience: "All staff", author: "Solomon Tadesse", priority: "important", status: "published", views: 96 },
    { title: "Water interruption — Ward 2", message: "Water supply to Ward 2 will be interrupted today from 14:00 to 16:00 for maintenance. Emergency water tanks have been filled.", audience: "All staff", author: "Hanna Bekele", priority: "urgent", status: "published", views: 58 },
    { title: "New lab analyzer commissioned", message: "The new hematology analyzer in the laboratory is fully operational. All CBC requests will now be processed same-day.", audience: "Doctors", author: "Sara Worku", priority: "normal", status: "published", views: 41 }
  ].forEach(function (an, ai) { MOCK.announcements.push({ id: "AN-" + (7 + ai), title: an.title, message: an.message, audience: an.audience, author: an.author, publish_date: DT(ai === 2 ? -1 : 0, "0" + (7 + ai) + ":" + (30 + ai * 10)), priority: an.priority, status: an.status, views: an.views }); });

  // ---------- referrals (recent) ----------
  var refSpec = [["Cardiology", "Dr. Meron Assefa"], ["Nephrology", "Dr. Girma Tola"], ["Endocrinology", "Dr. Fikru Debebe"], ["Pediatric ICU", "St. Mary's Hospital"], ["Ophthalmology", "Hawassa Referral"]];
  for (i = 0; i < 5; i++) {
    var fp = ALLP[pIdx()];
    var fs = refSpec[ri(refSpec.length)];
    MOCK.referrals.push({ id: "RF-" + (407 + i), patient: fp.first_name + " " + fp.last_name, to: fs[1], specialty: fs[0], reason: ["Requires specialist assessment and further investigation.", "Disease progression needs specialty review.", "Second opinion requested by attending physician."][ri(3)], priority: ["routine", "urgent", "emergency"][ri(3)], date: D(-ri(3)), status: ["pending", "accepted", "completed"][ri(3)] });
  }

  // ---------- suppliers / POs ----------
  MOCK.suppliers.push(
    { id: "SP-7", name: "Ethio Pharma Distributors", contact: "Mr. Abebe Negash", phone: "+251 911 000 107", categories: "Antibiotics, supplements", lead_time: 4, rating: 4.3 },
    { id: "SP-8", name: "Sodo Medical Trading", contact: "Ms. Birtukan Tadesse", phone: "+251 911 000 108", categories: "Analgesics, IV fluids", lead_time: 3, rating: 4.0 }
  );
  [
    { id: "PO-506", supplier: "Ethio Pharma Distributors", items: ["Azithromycin 500mg — 500", "Ferrous Sulfate — 1000"], total: 14200, status: "ordered" },
    { id: "PO-507", supplier: "Sodo Medical Trading", items: ["Ibuprofen 400mg — 1500"], total: 9800, status: "received" },
    { id: "PO-508", supplier: "United Pharma PLC", items: ["Omeprazole 20mg — 800"], total: 11600, status: "ordered" }
  ].forEach(function (po) { po.date = D(-ri(6)); MOCK.purchase_orders.push(po); });

  // ---------- samples (today pipeline) ----------
  var stages = ["collected", "received", "processing", "result-ready", "completed"];
  var sampleTypes = ["Whole blood", "Serum", "Urine"];
  for (i = 0; i < 6; i++) {
    var sp = ALLP[pIdx()];
    MOCK.samples.push({ id: "S-81" + (1 + i), patient: sp.first_name + " " + sp.last_name, test: tests[ri(tests.length)], type: sampleTypes[ri(sampleTypes.length)], collected: "0" + (8 + ri(4)) + ":" + (10 + ri(40)), stage: stages[ri(stages.length)], tat: "" });
  }

  // ---------- insurance (more coverage checks) ----------
  [
    { patient: "Tigist Woldu", provider: "EHBPA", policy: "EHB-2026-5109", coverage: 80, valid_until: D(200), status: "verified" },
    { patient: "Sileshi Berta", provider: "Nyala Insurance", policy: "NYL-9130", coverage: 75, valid_until: D(90), status: "pending" },
    { patient: "Meseret Fikru", provider: "GIB (Global Insurance)", policy: "GIB-7712", coverage: 85, valid_until: D(40), status: "verified" }
  ].forEach(function (x) { MOCK.insurance.push({ id: "IN-" + (7 + ri(100)), patient: x.patient, provider: x.provider, policy: x.policy, coverage: x.coverage, valid_until: x.valid_until, status: x.status }); });

  // ---------- messages & sent (fresh, some unread) ----------
  var msgs = [
    ["Dr. Daniel Alemu", "Doctor", "Follow-up review — P-1004", "Selam Tadesse's BP is improving on the reduced dose. Please schedule a follow-up ECG before the end of the week.", "high"],
    ["Pharmacy", "Pharmacist", "Amoxicillin stock restored", "Amoxicillin 250mg is back in stock. Outstanding prescriptions can now be dispensed.", "normal"],
    ["Laboratory", "Laboratory", "HbA1c result ready", "Yohannes Mamo's HbA1c is 7.9% — a copy has been sent to the doctor on file.", "normal"],
    ["Front Desk (Reception)", "Reception", "Walk-in queue update", "The OPD walk-in queue currently has 4 patients. Two have been waiting over 40 minutes.", "normal"],
    ["Hanna Bekele", "Manager", "Q3 staff review timeline", "Please submit staff self-assessments by Friday. The review meetings start next Monday.", "high"],
    ["Front Desk (Reception)", "Reception", "Appointment reminder", "Reminder: 5 confirmed appointments and 2 new registrations are scheduled for today.", "normal"]
  ];
  msgs.forEach(function (m, mi) { MOCK.messages.push({ id: "MSG-11" + (1 + mi), from: m[0], from_role: m[1], subject: m[2], body: m[3], date: DT(mi < 3 ? -1 : 0, "0" + (8 + ri(4)) + ":" + (10 + ri(45))), read: mi > 2, priority: m[4], replies: [] }); });
  [
    ["Dr. Daniel Alemu", "Re: HbA1c result", "Noted. Insulin dose re-evaluation is scheduled for the next visit."],
    ["Pharmacy", "Re: Amoxicillin stock", "Great — we will notify the affected patients."],
    ["Hanna Bekele", "Re: Q3 reviews", "Self-assessments will be submitted before Friday as requested."]
  ].forEach(function (s, si) { MOCK.sent.push({ id: "SENT-60" + (1 + si), to: s[0], subject: s[1], body: s[2], date: DT(0, "09:0" + si + ":00") }); });

  // ---------- documents (fresh uploads) ----------
  var docTemplates = [
    ["Lab Report", "Complete Blood Count — ", 214, "Sara Worku", "CBC with low hemoglobin — repeat in 2 weeks."],
    ["Lab Report", "Kidney Function — ", 208, "Sara Worku", "Creatinine mildly elevated — monitor."],
    ["Prescription", "Prescription — ", 86, "Dr. Daniel Alemu", "Antibiotic course 7 days."],
    ["Prescription", "Prescription — ", 92, "Dr. Fikru Debebe", "Bronchodilator as needed."],
    ["Consent Form", "Consent — ", 138, "Liya Hailu", "Signed consent for procedure."],
    ["Insurance", "Insurance Verification — ", 310, "Liya Hailu", "Policy verified with 80% coverage."],
    ["Referral Letter", "Referral — ", 124, "Dr. Meron Assefa", "Referral to specialty clinic."],
    ["ID Copy", "ID Copy — ", 458, "Liya Hailu", "National ID on file."]
  ];
  for (i = 0; i < 8; i++) {
    var tp = ALLP[pIdx()];
    var dt2 = docTemplates[ri(docTemplates.length)];
    MOCK.documents.push({ id: "DOC-" + (11 + i), patient: tp.first_name + " " + tp.last_name, patient_id: tp.id, type: dt2[0], title: dt2[1] + (tp.first_name + " " + tp.last_name), date: D(-ri(4)), size: dt2[2] + " KB", uploaded_by: dt2[3], summary: dt2[4] });
  }

  // ---------- complaints (open + one resolved today) ----------
  [
    ["Hana Wolde", "Billing", "Double charge on lab test", "I was charged twice for the same blood test on my last visit. Please review my account.", "high", "in-review", ""],
    ["Tigist Woldu", "Service Quality", "Maternity waiting area crowd", "The maternity waiting area was overcrowded this morning with no seats for late arrivals.", "normal", "pending", ""],
    ["Merch Awoke", "Treatment / Care", "Pain medication timing", "My mother's pain medication was given 3 hours late on the night shift.", "high", "resolved", "Reviewed with the night supervisor — dosage schedules are now checked at shift handover. Apologies for the delay."]
  ].forEach(function (c, ci) {
    MOCK.complaints.push({ id: "CMP-" + (106 + ci), reporter: c[0], reporter_role: "patient", category: c[1], subject: c[2], description: c[3], priority: c[4], date: DT(-ri(2), "1" + (0 + ri(3)) + ":00"), status: c[5], solution: c[6], resolved_by: c[6] ? "Hanna Bekele" : "", resolved_date: c[6] ? DT(0, "09:00") : "" });
  });

  // ---------- roster: this week (tomorrow → +6) for all 10 staff ----------
  var rosterStaff = [
    ["Dr. Daniel Alemu", "Internal Medicine"], ["Dr. Fikru Debebe", "Pediatrics"], ["Dr. Meron Assefa", "Cardiology"],
    ["Marta Tesfaye", "Internal Medicine"], ["Bethelehem Girma", "Pediatrics"], ["Yonas Girma", "Pharmacy"],
    ["Sara Worku", "Laboratory"], ["Liya Hailu", "Front Desk"], ["Kaleb Teshome", "Pharmacy"], ["Hanna Bekele", "Management"]
  ];
  var shiftsPool = [["Morning", "07:00", "15:00"], ["Evening", "15:00", "23:00"], ["Day (OPD)", "08:00", "17:00"], ["Half-day", "08:00", "13:00"]];
  var roN = 100;
  for (var dayOff = 1; dayOff <= 6; dayOff++) {
    rosterStaff.forEach(function (rs2) {
      var sh = shiftsPool[ri(shiftsPool.length)];
      MOCK.roster.push({ id: "RO-" + (roN++), staff: rs2[0], dept: rs2[1], date: D(dayOff), shift: sh[0], start: sh[1], end: sh[2] });
    });
  }

  // ---------- attendance: today + last 13 days for all 10 staff ----------
  var attStatus = ["present", "present", "present", "present", "late", "present", "present", "absent", "leave", "present"];
  function mkAtt(off, staff, idx) {
    var sh = shiftsPool[ri(shiftsPool.length)];
    var st3 = off === 0 ? (idx % 4 === 3 ? "late" : "present") : attStatus[ri(attStatus.length)];
    var checkIn = st3 === "absent" || st3 === "leave" ? null : "0" + (6 + ri(2)) + ":" + (10 + ri(45));
    var checkOut = off === 0 ? null : (st3 === "absent" || st3 === "leave" ? null : "1" + (4 + ri(2)) + ":" + (5 + ri(50)));
    MOCK.attendance.push({ id: "AT-" + (400 + off * 20 + idx), staff: staff[0], dept: staff[1], date: D(off), shift: sh[0] === "Day (OPD)" ? "Day (OPD)" : (sh[2] === "23:00" ? "Evening" : "Morning"), check_in: checkIn, check_out: checkOut, status: st3, source: st3 === "absent" ? "manual" : "fingerprint", device: st3 === "absent" ? null : "FP-0" + (1 + ri(5)) });
  }
  for (var off = 0; off <= 13; off++) rosterStaff.forEach(function (rs3, idx) { mkAtt(off, rs3, idx); });

  // ---------- observations (nursing, today) ----------
  MOCK.observations = [];
  var obsN = 0;
  for (i = 0; i < 12; i++) {
    var op = ALLP[pIdx()];
    MOCK.observations.push({
      id: "O-" + (obsN++), time: TIMES[ri(TIMES.length)],
      patient: op.first_name + " " + op.last_name,
      pain: ri(9), intake: 100 + ri(7) * 50, output: 80 + ri(7) * 40,
      temp: (36.4 + rnd() * 1.8).toFixed(1),
      nurse: NURSES[ri(NURSES.length)],
      notes: ["Resting comfortably", "Pain after repositioning", "Tolerating oral fluids", "Reduced urine output, monitor", "Good oral intake", "Sleeping", "Arms swollen, elevate", "Vomited once, reviewing fluids"][ri(8)]
    });
  }

  // ---------- notifications (topbar bell) ----------
  MOCK.notifications = [
    { title: "3 critical patient alerts", sub: "Flagged by the vitals AI", icon: "alert", tint: "#FEF2F2", color: "#DC2626", category: "AI", time: "06:40", detail: "Three patients currently monitored in the wards have vitals outside safe ranges. The vitals AI has flagged them for immediate nursing review.", link: getUserRole && getUserRole() === "nurse" ? "nurse/vitals.html" : "doctor/patients.html" },
    { title: "4 items low in stock", sub: "Pharmacy reorder suggested", icon: "package", tint: "#FBF0D3", color: "#B45309", category: "Inventory", time: "07:15", detail: "Metformin 500mg, Insulin Glargine, Ceftriaxone 1g and Metronidazole 400mg are at low stock levels. Suggested reorder quantities are ready on the AI forecast page.", link: "pharmacist/ai-forecast.html" },
    { title: "AI modules online", sub: "All 7 modules passed health check", icon: "check", tint: "#E3F9EF", color: "#0F9D5C", category: "System", time: "08:00", detail: "Clinical diagnosis, drug interaction, lab analyzer, vitals alerts, inventory forecast, appointment no-show and symptom chatbot all passed their health checks.", link: "" },
    { title: "2 lab results flagged abnormal", sub: "Review in the AI analyzer", icon: "flask", tint: "#E0F4FA", color: "#0891B2", category: "Laboratory", time: "08:22", detail: "The lab analyzer flagged two results: elevated creatinine (Kidney Function) and high fasting glucose. Both have been pushed to the requesting doctors.", link: "laboratory/ai-analyzer.html" }
  ];

  // ---------- vitals history (extra monitored patients) ----------
  function vitSeries(sysBase, diaBase, hrBase, spo2Base) {
    var out = [];
    for (var h = 6; h <= 20; h += 2) {
      out.push({
        t: (h < 10 ? "0" + h : h) + ":00",
        hr: hrBase + ri(9) - 4, sys: sysBase + ri(14) - 7, dia: diaBase + ri(10) - 5,
        temp: +(36.4 + rnd() * 1.2).toFixed(1), spo2: Math.min(99, spo2Base + ri(4) - 1), rr: 16 + ri(6) - 2
      });
    }
    return out;
  }
  MOCK.vitals_history["P-1001"] = vitSeries(138, 88, 84, 95);   // Abel — hypertensive
  MOCK.vitals_history["P-1002"] = vitSeries(122, 78, 76, 97);
  MOCK.vitals_history["P-1004"] = vitSeries(150, 92, 90, 95);   // Selam — cardiac (already present)
  MOCK.vitals_history["P-1006"] = vitSeries(128, 82, 80, 96);
  MOCK.vitals_history["P-1009"] = vitSeries(132, 84, 82, 96);
  MOCK.vitals_history["P-1011"] = vitSeries(118, 74, 92, 98);   // Meron — anemia
})();

// ============================================================
// DEMO RESPONSE ROUTER
// ============================================================
function mockResponse(endpoint, method, body) {
  const e = endpoint.replace(/^\//, "");
  let data = null;
  let status = "success";

  const list = (arr) => ({ ok: true, data: { items: clone(arr), total: arr.length } });
  const find = (arr, idKey, id) => arr.find(x => x[idKey] === id) || null;

  switch (e) {

    // ---------- Core lists ----------
    case CONFIG.ENDPOINTS.USERS.replace(/^\//, ""):
      data = list(MOCK.users);
      break;
    case CONFIG.ENDPOINTS.PATIENTS.replace(/^\//, ""):
      data = list(MOCK.patients);
      break;
    case CONFIG.ENDPOINTS.DEPARTMENTS.replace(/^\//, ""):
      data = list(MOCK.departments);
      break;
    case CONFIG.ENDPOINTS.STAFF.replace(/^\//, ""):
      data = list(MOCK.staff);
      break;
    case CONFIG.ENDPOINTS.APPOINTMENTS.replace(/^\//, ""):
      data = list(MOCK.appointments);
      break;
    case CONFIG.ENDPOINTS.PRESCRIPTIONS.replace(/^\//, ""):
      data = list(MOCK.prescriptions);
      break;
    case CONFIG.ENDPOINTS.INVENTORY.replace(/^\//, ""):
      data = list(MOCK.inventory);
      break;
    case CONFIG.ENDPOINTS.LAB_REQUESTS.replace(/^\//, ""):
      data = list(MOCK.lab_requests);
      break;
    case CONFIG.ENDPOINTS.LAB_RESULTS.replace(/^\//, ""):
      data = list(MOCK.lab_results);
      break;
    case CONFIG.ENDPOINTS.MEDICATIONS.replace(/^\//, ""):
      data = list(MOCK.medications);
      break;
    case CONFIG.ENDPOINTS.CARE_PLANS.replace(/^\//, ""):
      data = list(MOCK.care_plans);
      break;
    case CONFIG.ENDPOINTS.BILLS.replace(/^\//, ""):
      data = list(MOCK.bills);
      break;
    case CONFIG.ENDPOINTS.AUDIT_LOGS.replace(/^\//, ""):
      data = list(MOCK.audit_logs);
      break;
    case CONFIG.ENDPOINTS.QUEUE.replace(/^\//, ""):
      data = list(MOCK.queue);
      break;
    case CONFIG.ENDPOINTS.ANNOUNCEMENTS.replace(/^\//, ""):
      data = list(MOCK.announcements);
      break;
    case CONFIG.ENDPOINTS.FINANCE.replace(/^\//, ""):
      data = { ok: true, data: { months: ["Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"], revenue: [640,688,701,745,720,768,790,812,798,826,831,842], expenses: [420,431,448,462,455,470,481,490,486,500,505,513] } };
      break;
    case CONFIG.ENDPOINTS.REFERRALS.replace(/^\//, ""):
      data = list(MOCK.referrals);
      break;
    case CONFIG.ENDPOINTS.OBSERVATIONS.replace(/^\//, ""):
      data = list(MOCK.observations || []);
      break;
    case CONFIG.ENDPOINTS.SUPPLIERS.replace(/^\//, ""):
      data = list(MOCK.suppliers);
      break;
    case CONFIG.ENDPOINTS.PURCHASE_ORDERS.replace(/^\//, ""):
      data = list(MOCK.purchase_orders);
      break;
    case CONFIG.ENDPOINTS.SAMPLES.replace(/^\//, ""):
      data = list(MOCK.samples);
      break;
    case CONFIG.ENDPOINTS.INSURANCE.replace(/^\//, ""):
      data = list(MOCK.insurance);
      break;
    case CONFIG.ENDPOINTS.MESSAGES.replace(/^\//, ""):
      data = list(MOCK.messages);
      break;
    case CONFIG.ENDPOINTS.SENT_MESSAGES.replace(/^\//, ""):
      data = list(MOCK.sent);
      break;
    case CONFIG.ENDPOINTS.NOTIFICATIONS.replace(/^\//, ""):
      data = list(MOCK.notifications || []);
      break;
    case CONFIG.ENDPOINTS.COMPLAINTS.replace(/^\//, ""):
      data = list(MOCK.complaints);
      break;
    case CONFIG.ENDPOINTS.SHIFTS.replace(/^\//, ""):
      data = list(MOCK.shifts);
      break;
    case CONFIG.ENDPOINTS.ROSTER.replace(/^\//, ""):
      data = list(MOCK.roster);
      break;
    case CONFIG.ENDPOINTS.ATTENDANCE.replace(/^\//, ""):
      data = list(MOCK.attendance);
      break;
    case CONFIG.ENDPOINTS.FINGERPRINT_DEVICES.replace(/^\//, ""):
      data = list(MOCK.devices);
      break;
    case CONFIG.ENDPOINTS.DOCUMENTS.replace(/^\//, ""):
      data = list(MOCK.documents);
      break;

    // ============================================================
    // HEALTH VIDEOS — AI video suggestions (YouTube, free)
    // Demo: filters the curated library. With CONFIG.YOUTUBE_API_KEY
    // set (free Google key), the real backend would call the YouTube
    // Data API v3 instead; this demo router returns curated results.
    // ============================================================
    case CONFIG.ENDPOINTS.VIDEOS.replace(/^\//, ""):
      data = list(MOCK.videos.concat(MOCK.extra_videos || []));
      break;
    case CONFIG.ENDPOINTS.VIDEO_SEARCH.replace(/^\//, ""):
      if (method === "POST") {
        const q = String((body && body.query) || "").toLowerCase();
        const conds = (body && body.conditions) || [];
        let list = MOCK.videos.concat(MOCK.extra_videos || []).filter(v => {
          const hay = (v.title + " " + v.channel + " " + v.description + " " + v.conditions.join(" ")).toLowerCase();
          return !q || hay.includes(q);
        });
        if (conds.length) {
          // rank: matches for the patient's own conditions first
          const scored = list.map(v => {
            let s = 0;
            conds.forEach(c => { if (v.conditions.some(t => c.toLowerCase().includes(t) || t.includes(c.toLowerCase()))) s += 2; });
            return { v, s };
          });
          scored.sort((a, b) => b.s - a.s);
          list = scored.map(x => x.v);
        }
        data = { items: clone(list.slice(0, 12)), total: list.length, suggested_for: conds, source: CONFIG.YOUTUBE_API_KEY ? "youtube-api" : "curated" };
      }
      break;

    // ---------- Auth ----------
    case CONFIG.ENDPOINTS.LOGIN.replace(/^\//, ""):
      if (method === "POST") {
        const roleKey = String(body.email || "").toLowerCase().split("@")[0];
        const acc = CONFIG.DEMO_ACCOUNTS[roleKey];
        if (acc && acc.password === body.password) {
          data = { token: "demo-token-" + roleKey, role: acc.role, user_id: roleKey + "-001", name: acc.name };
        } else {
          return { ok: false, error: "Invalid email or password." };
        }
      }
      break;

    // ============================================================
    // AI MODULE 1 — Clinical Decision Support (disease prediction)
    // ============================================================
    case CONFIG.ENDPOINTS.PREDICT_DISEASE.replace(/^\//, ""):
      if (method === "POST") {
        const syms = String((body && body.symptoms) || "").toLowerCase();
        const predictions = [
          { disease: "Malaria", confidence: 82, description: "Common in the region — presents with fever, chills and headache. Confirm with blood film / RDT.", urgency: "See doctor" },
          { disease: "Typhoid Fever", confidence: 61, description: "Prolonged fever with abdominal discomfort. Widal test and blood culture recommended.", urgency: "See doctor" },
          { disease: "Upper Respiratory Infection", confidence: 47, description: "Cough, sore throat and mild fever. Usually viral and self-limiting.", urgency: "Self-care" }
        ];
        // Simple heuristic to shuffle ranking based on input text
        if (syms.includes("cough") || syms.includes("throat")) {
          predictions.unshift({ disease: "Upper Respiratory Infection", confidence: 74, description: "Cough, sore throat and mild fever. Usually viral and self-limiting.", urgency: "Self-care" });
        }
        if (syms.includes("chest") || syms.includes("breath")) {
          predictions.unshift({ disease: "Pneumonia (suspected)", confidence: 79, description: "Fever with productive cough and breathing difficulty. Chest X-ray advised.", urgency: "See doctor" });
        }
        data = { predictions: predictions.slice(0, 3), model: "rf_clinical_v1.2", model_version: "1.2.0" };
      }
      break;

    // ============================================================
    // AI MODULE 2 — Drug Interaction Checker
    // ============================================================
    case CONFIG.ENDPOINTS.CHECK_INTERACTION.replace(/^\//, ""):
      if (method === "POST") {
        const a = String((body && body.drug_a) || "").toLowerCase();
        const b = String((body && body.drug_b) || "").toLowerCase();
        const both = a + "|" + b;
        let result;
        if (both.includes("warfarin") && both.includes("aspirin"))
          result = { level: "severe", title: "Severe Interaction", mechanism: "Both drugs inhibit platelet aggregation and increase bleeding risk.", effect: "Significant risk of gastrointestinal bleeding and hemorrhage.", action: "Avoid combination. Use alternative analgesia or monitor INR closely." };
        else if ((both.includes("metformin") && both.includes("contrast")) || (both.includes("metformin") && both.includes("furosemide")))
          result = { level: "moderate", title: "Moderate Interaction", mechanism: "Additive effect on renal function and lactic acidosis risk.", effect: "Reduced renal clearance may increase metformin levels.", action: "Monitor renal function; adjust doses as needed." };
        else if (both.includes("amlodipine") && both.includes("stat"))
          result = { level: "moderate", title: "Moderate Interaction", mechanism: "CYP3A4 metabolism shared by both drugs.", effect: "Increased exposure to the statin — myopathy risk.", action: "Monitor for muscle pain; consider lower statin dose." };
        else if (both.includes("digoxin") && both.includes("furosemide"))
          result = { level: "severe", title: "Severe Interaction", mechanism: "Diuretic-induced hypokalemia potentiates digoxin toxicity.", effect: "Risk of cardiac arrhythmias.", action: "Monitor serum potassium; correct hypokalemia before dosing." };
        else
          result = { level: "safe", title: "No Significant Interaction", mechanism: "No known pharmacokinetic or pharmacodynamic interaction between these drugs.", effect: "No clinically significant effect expected.", action: "No action required. Standard monitoring applies." };
        data = { ...result, drug_a: body.drug_a, drug_b: body.drug_b, model: "drug_int_v1.1", model_version: "1.1.0" };
      }
      break;

    // ============================================================
    // AI MODULE 3 — Lab Result Analyzer
    // ============================================================
    case CONFIG.ENDPOINTS.ANALYZE_LAB.replace(/^\//, ""):
      if (method === "POST") {
        const values = (body && body.values) || {};
        const refRanges = {
          hemoglobin: { name: "Hemoglobin", range: "13.5 – 17.5 g/dL", low: 13.5, high: 17.5, unit: "g/dL" },
          wbc: { name: "WBC", range: "4.0 – 11.0 ×10³/µL", low: 4.0, high: 11.0, unit: "×10³/µL" },
          rbc: { name: "RBC", range: "4.5 – 5.9 ×10⁶/µL", low: 4.5, high: 5.9, unit: "×10⁶/µL" },
          platelets: { name: "Platelets", range: "150 – 450 ×10³/µL", low: 150, high: 450, unit: "×10³/µL" },
          creatinine: { name: "Creatinine", range: "0.7 – 1.3 mg/dL", low: 0.7, high: 1.3, unit: "mg/dL" },
          alt: { name: "ALT", range: "7 – 56 U/L", low: 7, high: 56, unit: "U/L" },
          ast: { name: "AST", range: "10 – 40 U/L", low: 10, high: 40, unit: "U/L" },
          tsh: { name: "TSH", range: "0.4 – 4.0 mIU/L", low: 0.4, high: 4.0, unit: "mIU/L" },
          glucose: { name: "Glucose (Fasting)", range: "70 – 100 mg/dL", low: 70, high: 100, unit: "mg/dL" }
        };
        const rows = [];
        Object.entries(values).forEach(([key, val]) => {
          const ref = refRanges[key];
          const num = parseFloat(val);
          if (ref && !isNaN(num)) {
            const status = num < ref.low ? "low" : num > ref.high ? "high" : "normal";
            const deviation = status === "normal" ? "—" : ((num - (ref.high + ref.low) / 2) / ((ref.high - ref.low) / 2) * 100).toFixed(0) + "% from range";
            rows.push({ name: ref.name, range: ref.range, value: val + " " + ref.unit, status, deviation });
          }
        });
        if (!rows.length) {
          rows.push({ name: "Hemoglobin", range: "13.5 – 17.5 g/dL", value: values.hemoglobin ? values.hemoglobin + " g/dL" : "—", status: "normal", deviation: "—" });
        }
        const abnormal = rows.filter(r => r.status !== "normal");
        const conditions = abnormal.length
          ? (abnormal.some(r => /creatinine/i.test(r.name)) ? ["Possible renal impairment — monitor eGFR"] : [])
              .concat(abnormal.some(r => /glucose/i.test(r.name)) ? ["Impaired fasting glucose — consider diabetes screening"] : [])
              .concat(abnormal.some(r => /alt|ast/i.test(r.name)) ? ["Hepatic enzyme elevation — evaluate liver function"] : [])
              .concat(abnormal.some(r => /hemoglobin|rbc/i.test(r.name)) ? ["Possible anemia — further workup advised"] : [])
          : [];
        data = {
          overall: abnormal.length ? "abnormal" : "normal",
          rows,
          conditions: conditions.length ? conditions : ["All measured values within reference ranges."],
          model: "lab_analyzer_v2.0", model_version: "2.0.0"
        };
      }
      break;

    // ============================================================
    // AI MODULE 4 — Vitals Alert System
    // ============================================================
    case CONFIG.ENDPOINTS.CHECK_VITALS.replace(/^\//, ""):
      if (method === "POST") {
        const v = body || {};
        const hr = +v.hr, sys = +v.sys, dia = +v.dia, temp = +v.temp, spo2 = +v.spo2, rr = +v.rr;
        const flags = [];
        if (hr > 100 || hr < 60) flags.push({ vital: "Heart Rate", value: hr + " bpm", range: "60 – 100 bpm", severity: hr > 120 || hr < 45 ? "critical" : "warning", by: Math.abs(hr - ((100 + 60) / 2)) + " bpm off" });
        if (sys > 140 || dia > 90 || sys < 90) flags.push({ vital: "Blood Pressure", value: sys + "/" + dia + " mmHg", range: "90–140 / 60–90 mmHg", severity: sys > 180 || dia > 120 ? "critical" : "warning", by: Math.abs(sys - 115) + " mmHg off" });
        if (temp > 38.5) flags.push({ vital: "Temperature", value: temp + " °C", range: "36.1 – 37.8 °C", severity: temp > 40 ? "critical" : "warning", by: (temp - 37.8).toFixed(1) + " °C high" });
        if (spo2 < 94) flags.push({ vital: "SpO2", value: spo2 + " %", range: "94 – 100 %", severity: spo2 < 90 ? "critical" : "warning", by: (94 - spo2) + "% low" });
        if (rr > 22 || rr < 10) flags.push({ vital: "Respiratory Rate", value: rr + " /min", range: "12 – 20 /min", severity: rr > 28 || rr < 8 ? "critical" : "warning", by: Math.abs(rr - 16) + " breaths/min off" });

        let level = "normal", actions = ["Continue routine monitoring."];
        if (flags.some(f => f.severity === "critical")) {
          level = "critical";
          actions = ["Notify the attending doctor immediately.", "Move patient to a monitored bed if admitted.", "Prepare for emergency review — repeat vitals in 15 minutes."];
        } else if (flags.length) {
          level = "warning";
          actions = ["Recheck vitals in 1 hour.", "Inform the nursing supervisor.", "Review medication schedule for possible causes."];
        }
        data = { level, flags, actions, model: "vitals_alert_v1.3", model_version: "1.3.0" };
      }
      break;

    // ============================================================
    // AI MODULE 5 — Inventory Forecasting
    // ============================================================
    case CONFIG.ENDPOINTS.FORECAST_INVENTORY.replace(/^\//, ""):
      if (method === "POST") {
        const drug = String((body && body.drug_name) || "Paracetamol 500mg");
        const days = +(body && body.days) || 30;
        const seed = drug.length;
        const historical = [82, 90, 78, 95, 88, 102, 84, 97, 91, 108, 86, 99];
        const dailyUse = 8 + (seed % 5); // avg daily units
        const forecast = [];
        let projected = 0;
        for (let i = 1; i <= days; i++) {
          const wave = Math.round(dailyUse * (1 + 0.18 * Math.sin(i / 6 + seed)));
          projected += wave;
          forecast.push({ day: "Day " + i, value: wave });
        }
        const currentStock = Math.max(60, (seed * 37) % 500);
        const runsOut = projected >= currentStock;
        const suggested = Math.max(0, projected - currentStock) + Math.round(days * dailyUse * 0.25);
        data = {
          drug_name: drug,
          days,
          current_stock: currentStock,
          historical: historical.map((v, i) => ({ label: "D-" + (30 - historical.length + i + 1), value: v })),
          forecast,
          daily_use: dailyUse,
          runs_out_in_days: runsOut ? Math.max(1, Math.floor(currentStock / dailyUse)) : null,
          suggested_order_qty: suggested,
          model: "inventory_forecast_v1.4", model_version: "1.4.0"
        };
      }
      break;

    // ============================================================
    // AI MODULE 6 — Appointment / No-show Prediction
    // ============================================================
    case CONFIG.ENDPOINTS.PREDICT_APPOINTMENT.replace(/^\//, ""):
      if (method === "POST") {
        const appt = body || {};
        const base = 8 + (String(appt.patient || "").length % 25);
        const dayFactor = /saturday|sunday/.test(String(appt.day || "").toLowerCase()) ? 9 : 0;
        const typeFactor = appt.type === "Follow-up" ? 14 : 5;
        const no_show = Math.min(85, base + dayFactor + typeFactor + (appt.history_no_show || 0));
        data = {
          no_show_percent: Math.round(no_show),
          load_prediction: appt.dept ? "Moderate" : "Moderate",
          busy_hours: [8, 9, 10, 11, 14, 15],
          confidence: 0.9 + ((no_show % 9) / 100),
          model: "appointment_ai_v1.1", model_version: "1.1.0"
        };
      }
      break;

    // ============================================================
    // AI MODULE 7 — Symptom Checker Chatbot
    // ============================================================
    case CONFIG.ENDPOINTS.SYMPTOM_CHAT.replace(/^\//, ""):
      if (method === "POST") {
        const msg = String((body && body.message) || "").toLowerCase();
        let resp;
        if (msg.includes("fever") && (msg.includes("chill") || msg.includes("headache")))
          resp = { conditions: ["Malaria"], urgency: "orange", action: "See a doctor", follow_up: "Have you had any vomiting or difficulty urinating?" };
        else if (msg.includes("chest") || msg.includes("chest pain"))
          resp = { conditions: ["Angina", "Acid reflux"], urgency: "red", action: "Seek emergency care", follow_up: "Is the pain radiating to your arm or jaw?" };
        else if (msg.includes("cough") || msg.includes("throat"))
          resp = { conditions: ["Upper Respiratory Infection"], urgency: "green", action: "Self-care", follow_up: "Do you have a fever above 38°C or shortness of breath?" };
        else if (msg.includes("headache"))
          resp = { conditions: ["Tension Headache", "Migraine"], urgency: "green", action: "Self-care", follow_up: "How long have you had the headache?" };
        else if (msg.includes("breath") || msg.includes("breathing"))
          resp = { conditions: ["Possible Asthma exacerbation", "Pneumonia"], urgency: "orange", action: "See a doctor today", follow_up: "Do you have a wheeze when breathing out?" };
        else if (msg.includes("stomach") || msg.includes("abdominal") || msg.includes("diarrhea"))
          resp = { conditions: ["Gastroenteritis", "Food poisoning"], urgency: "orange", action: "See a doctor", follow_up: "Any blood in your stool or persistent vomiting?" };
        else if (msg.includes("tired") || msg.includes("fatigue") || msg.includes("weak"))
          resp = { conditions: ["Anemia", "Hypothyroidism"], urgency: "green", action: "Book a lab test", follow_up: "Do you feel dizzy or short of breath with exertion?" };
        else
          resp = { conditions: ["General health query"], urgency: "green", action: "Book a consultation", follow_up: "Can you describe when the symptoms started?" };
        data = {
          reply: "Based on the symptoms you described, I found some possible conditions. This is not a medical diagnosis — please consult a clinician.",
          conditions: resp.conditions,
          urgency: resp.urgency,
          action: resp.action,
          follow_up: resp.follow_up,
          disclaimer: "AI suggestions only. Final diagnosis by doctor.",
          model: "symptom_chat_v1.5", model_version: "1.5.0"
        };
      }
      break;

    // ---------- Fallback ----------
    default:
      data = { ok: true, data: { message: "Demo response for " + endpoint } };
      break;
  }

  if (method === "GET" && Array.isArray(data && data.data && data.data.items)) {
    return data;
  }
  if (data && data.data) return { ok: true, data: clone(data.data) };
  if (data) return { ok: true, data: clone(data) };
  return { ok: true, status, data: { items: [] } };
}
