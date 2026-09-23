/* ============================================================
   Wolaita Sodo Hospital — config.js
   API base URL, Supabase keys, app settings, demo mode
   ============================================================ */

const CONFIG = {
  APP_NAME: "Wolaita Sodo Hospital",
  VERSION: "2.1.0",

  // Optional. Health Videos search YouTube through the hospital API, so this
  // can stay empty. A key is only a fallback if that API search fails.
  YOUTUBE_API_KEY: "",

  // Backend (FastAPI) — replace with your Render URL before deploy
  API_BASE_URL: (function() {
    // Allow override via ?api=... URL param or localStorage for local dev
    var urlParams = new URLSearchParams(window.location.search);
    var saved = null;
    return urlParams.get('api') || "https://final-project-bo4l.onrender.com";
  })(),

  // Supabase (PostgreSQL) — replace with your project values before deploy
  SUPABASE_URL: "",
  SUPABASE_KEY: "",

  // DEMO_MODE = true → the app runs with realistic mock data so the whole
  // frontend is fully testable BEFORE the FastAPI backend + .pkl models are ready.
  // Set to false once your backend is live AND redeployed with matching accounts.
  DEMO_MODE: false,

  DEMO_ACCOUNTS: {},

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
    BEDS:           "/beds",
    BED_REQUESTS:   "/bed_requests",
    BLOOD_UNITS:    "/blood_units",
    AMBULANCES:     "/ambulances",
    AMBULANCE_MISSIONS: "/ambulance_missions",
    THEATRE_CASES:  "/theatre_cases",
    IMAGING_STUDIES:"/imaging_studies",
    CASHIER_INVOICES:"/cashier_invoices",
    CHANGE_PASSWORD:"/auth/change-password",
    ME:             "/auth/me",
    PROFILE:        "/auth/profile",
    MESSAGE_DIRECTORY: "/messages/directory",
    APP_SETTINGS:   "/app_settings",

    // Auth
    SIGNUP:         "/auth/signup",
    RESET_PASSWORD: "/auth/reset-password"
  },

  // Role → tab permissions. The admin can grant/revoke these from the
  // Roles & Permissions page; changes apply automatically — the granted tab
  // appears (or disappears) in that role's sidebar on their next load.
  PERMISSIONS: {
    admin:      { users: 1, roles: 1, announcements: 1, audit: 1, settings: 1, shifts: 1, documents: 1, patients: 1, reports: 1, wards: 1, ai: 1, messages: 1 },
    manager:    { departments: 1, staff: 1, reports: 1, finance: 1, complaints: 1, shifts: 1, documents: 1, patients: 1, wards: 1, ai: 1, messages: 1, settings: 1 },
    doctor:     { patients: 1, bedrequests: 1, consultation: 1, prescriptions: 1, appointments: 1, referrals: 1, theatre: 1, imaging: 1, shifts: 1, documents: 1, videos: 1, ai: 1, messages: 1, settings: 1 },
    nurse:      { beds: 1, vitals: 1, observations: 1, medications: 1, careplans: 1, shifts: 1, documents: 1, patients: 1, reports: 1, messages: 1, settings: 1 },
    pharmacist: { prescriptions: 1, inventory: 1, suppliers: 1, shifts: 1, documents: 1, patients: 1, reports: 1, ai: 1, messages: 1, settings: 1 },
    laboratory: { testrequests: 1, samples: 1, bloodbank: 1, results: 1, shifts: 1, documents: 1, patients: 1, reports: 1, ai: 1, messages: 1, settings: 1 },
    reception:  { registration: 1, admissions: 1, appointments: 1, insurance: 1, queue: 1, ambulance: 1, billing: 1, shifts: 1, documents: 1, patients: 1, reports: 1, messages: 1, settings: 1 },
    patient:    { appointments: 1, records: 1, bills: 1, complaints: 1, healthcard: 1, videos: 1, messages: 1, ai: 1, settings: 1 }
  }
};

// Global storage key
const STORAGE_KEY = "mediq_pro_session";
