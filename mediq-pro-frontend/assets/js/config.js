/* ============================================================
   MedIQ Pro — config.js
   API base URL, Supabase keys, app settings, demo mode
   ============================================================ */

// Optional deployment-time override. A host may define
// window.MEDIQ_RUNTIME_CONFIG before loading this file.
const MEDIQ_RUNTIME_CONFIG = window.MEDIQ_RUNTIME_CONFIG || {};
const runtimeBoolean = (value, fallback) => {
  if (value === undefined || value === null || value === "") return fallback;
  return value === true || value === 1 || String(value).toLowerCase() === "true";
};
const runtimeNumber = (value, fallback, min, max) => {
  const number = Number(value);
  return Number.isFinite(number) && number >= min && number <= max ? number : fallback;
};

const CONFIG = {
  APP_NAME: "MedIQ Pro",
  VERSION: "2.1.0",

  // Optional free YouTube Data API v3 key (Google). If left empty, the Health
  // Videos feature uses the built-in curated library + targeted YouTube search
  // links (100% free, no key). Add a key to enable live AI video search:
  //   https://console.cloud.google.com/apis/library/youtube.googleapis.com
  // NOTE: this key is client-side, so restrict it in Google Cloud Console to
  // your domain/referrer (API & Services → Credentials → key → HTTP referrers).
  YOUTUBE_API_KEY: String(MEDIQ_RUNTIME_CONFIG.YOUTUBE_API_KEY || ""), // Use a referrer-restricted key; never commit secrets.

  // Backend (FastAPI). Leave empty to use a same-origin /api gateway, or
  // provide a full HTTPS URL through the runtime override before deployment.
  API_BASE_URL: String(MEDIQ_RUNTIME_CONFIG.API_BASE_URL || "").replace(/\/+$/, ""),
  API_TIMEOUT_MS: runtimeNumber(MEDIQ_RUNTIME_CONFIG.API_TIMEOUT_MS, 15000, 1000, 120000),

  // DEMO_MODE = true → the app runs with realistic mock data. Set it to false
  // only when the backend is reachable and has been configured.
  DEMO_MODE: runtimeBoolean(MEDIQ_RUNTIME_CONFIG.DEMO_MODE, true),

  // Demo accounts used when DEMO_MODE is true (also reachable from the login page)
  DEMO_ACCOUNTS: {
    admin:      { reports: 1, password: "admin123",      name: "Solomon Tadesse",  role: "admin" },
    manager:    { password: "manager123",    name: "Hanna Bekele",     role: "manager" },
    doctor:     { password: "doctor123",     name: "Dr. Daniel Alemu", role: "doctor" },
    nurse:      { reports: 1, password: "nurse123",      name: "Marta Tesfaye",    role: "nurse" },
    pharmacist: { password: "pharmacist123", name: "Yonas Girma",      role: "pharmacist" },
    laboratory: { password: "lab123",        name: "Sara Worku",       role: "laboratory" },
    reception:  { password: "reception123",  name: "Liya Hailu",       role: "reception" },
    patient:    { password: "patient123",    name: "Abel Mekonnen",    role: "patient" }
  },

  // All API endpoints used by the frontend (AI modules + core)
  ENDPOINTS: {
    LOGIN: "/auth/login",

    // AI Modules
    PREDICT_DISEASE:      "/ai/predict-disease",
    CHECK_INTERACTION:    "/ai/check-interaction",
    ANALYZE_LAB:          "/ai/analyze-lab",
    CHECK_VITALS:         "/ai/check-vitals",
    FORECAST_INVENTORY:   "/ai/forecast-inventory",
    PREDICT_APPOINTMENT:  "/ai/predict-appointment",
    SYMPTOM_CHAT:         "/ai/symptom-chat",

    // Core data
    USERS:          "/users",
    PATIENTS:       "/patients",
    DOCTORS:        "/staff",
    DEPARTMENTS:    "/departments",
    STAFF:          "/staff",
    APPOINTMENTS:   "/appointments",
    PRESCRIPTIONS:  "/prescriptions",
    INVENTORY:      "/inventory",
    LAB_REQUESTS:   "/lab_requests",
    LAB_RESULTS:    "/lab_results",
    VITALS:         "/vitals",
    MEDICATIONS:    "/medications",
    CARE_PLANS:     "/care_plans",
    BILLS:          "/bills",
    AUDIT_LOGS:     "/audit_logs",
    QUEUE:          "/queue",

    // Professional feature modules
    ANNOUNCEMENTS:  "/announcements",
    FINANCE:        "/finance",
    REFERRALS:      "/referrals",
    OBSERVATIONS:   "/observations",
    SUPPLIERS:      "/suppliers",
    PURCHASE_ORDERS:"/purchase_orders",
    SAMPLES:        "/samples",
    INSURANCE:      "/insurance",
    MESSAGES:       "/messages",
    SENT_MESSAGES:  "/messages/sent",
    NOTIFICATIONS:  "/notifications",
    COMPLAINTS:     "/complaints",
    SHIFTS:         "/shifts",
    ROSTER:         "/roster",
    ATTENDANCE:     "/attendance",
    FINGERPRINT_DEVICES: "/fingerprint_devices",
    DOCUMENTS:      "/documents",
    VIDEOS:         "/videos",
    VIDEO_SEARCH:   "/videos/search",

    // Auth
    SIGNUP:         "/auth/signup",
    RESET_PASSWORD: "/auth/reset-password"
  },

  // Role → tab permissions. The admin can grant/revoke these from the
  // Roles & Permissions page; changes apply automatically — the granted tab
  // appears (or disappears) in that role's sidebar on their next load.
  PERMISSIONS: {
    admin:      { users: 1, roles: 1, announcements: 1, audit: 1, settings: 1, shifts: 1, documents: 1, patients: 1, ai: 1, messages: 1 },
    manager:    { departments: 1, staff: 1, reports: 1, finance: 1, complaints: 1, shifts: 1, documents: 1, patients: 1, ai: 1, messages: 1, settings: 1 },
    doctor:     { patients: 1, consultation: 1, prescriptions: 1, appointments: 1, referrals: 1, shifts: 1, documents: 1, videos: 1, ai: 1, messages: 1, settings: 1 },
    nurse:      { vitals: 1, observations: 1, medications: 1, careplans: 1, shifts: 1, documents: 1, patients: 1, messages: 1, settings: 1 },
    pharmacist: { prescriptions: 1, inventory: 1, suppliers: 1, shifts: 1, documents: 1, patients: 1, ai: 1, messages: 1, settings: 1 },
    laboratory: { testrequests: 1, samples: 1, results: 1, shifts: 1, documents: 1, patients: 1, ai: 1, messages: 1, settings: 1 },
    reception:  { registration: 1, appointments: 1, insurance: 1, queue: 1, shifts: 1, documents: 1, patients: 1, messages: 1, settings: 1 },
    patient:    { appointments: 1, records: 1, bills: 1, complaints: 1, healthcard: 1, videos: 1, messages: 1, ai: 1, settings: 1 }
  }
};

// Global storage key
const STORAGE_KEY = "mediq_pro_session";
