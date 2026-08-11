/* ============================================================
   MedIQ Pro — config.js
   API base URL, Supabase keys, app settings, demo mode
   ============================================================ */

const CONFIG = {
  APP_NAME: "MedIQ Pro",
  VERSION: "1.0.0",

  // Optional free YouTube Data API v3 key (Google). If left empty, the Health
  // Videos feature uses the built-in curated library + targeted YouTube search
  // links (100% free, no key). Add a key to enable live AI video search:
  //   https://console.cloud.google.com/apis/library/youtube.googleapis.com
  YOUTUBE_API_KEY: "",

  // Backend (FastAPI) — replace with your Render URL before deploy
  API_BASE_URL: "https://your-backend.onrender.com",

  // Supabase (PostgreSQL) — replace with your project values before deploy
  SUPABASE_URL: "https://your-project.supabase.co",
  SUPABASE_KEY: "your-anon-key-here",

  // DEMO_MODE = true → the app runs with realistic mock data so the whole
  // frontend is fully testable BEFORE the FastAPI backend + .pkl models are ready.
  // Set to false once your backend is live.
  DEMO_MODE: true,

  // Demo accounts used when DEMO_MODE is true (also reachable from the login page)
  DEMO_ACCOUNTS: {
    admin:      { password: "admin123",      name: "Solomon Tadesse",  role: "admin" },
    manager:    { password: "manager123",    name: "Hanna Bekele",     role: "manager" },
    doctor:     { password: "doctor123",     name: "Dr. Daniel Alemu", role: "doctor" },
    nurse:      { password: "nurse123",      name: "Marta Tesfaye",    role: "nurse" },
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
    DOCTORS:        "/doctors",
    DEPARTMENTS:    "/departments",
    STAFF:          "/staff",
    APPOINTMENTS:   "/appointments",
    PRESCRIPTIONS:  "/prescriptions",
    INVENTORY:      "/inventory",
    LAB_REQUESTS:   "/lab-requests",
    LAB_RESULTS:    "/lab-results",
    VITALS:         "/vitals",
    MEDICATIONS:    "/medications",
    CARE_PLANS:     "/care-plans",
    BILLS:          "/bills",
    AUDIT_LOGS:     "/audit-logs",
    QUEUE:          "/queue",

    // Professional feature modules
    ANNOUNCEMENTS:  "/announcements",
    FINANCE:        "/finance",
    REFERRALS:      "/referrals",
    OBSERVATIONS:   "/observations",
    SUPPLIERS:      "/suppliers",
    PURCHASE_ORDERS:"/purchase-orders",
    SAMPLES:        "/samples",
    INSURANCE:      "/insurance",
    MESSAGES:       "/messages",
    SENT_MESSAGES:  "/messages/sent",
    NOTIFICATIONS:  "/notifications",
    COMPLAINTS:     "/complaints",
    SHIFTS:         "/shifts",
    ROSTER:         "/roster",
    ATTENDANCE:     "/attendance",
    FINGERPRINT_DEVICES: "/fingerprint-devices",
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
    patient:    { appointments: 1, records: 1, bills: 1, complaints: 1, documents: 1, healthcard: 1, videos: 1, messages: 1, ai: 1, settings: 1 }
  }
};

// Global storage key
const STORAGE_KEY = "mediq_pro_session";
