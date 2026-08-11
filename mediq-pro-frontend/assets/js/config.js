/* ============================================================
   MedIQ Pro — config.js
   API base URL, Supabase keys, app settings, demo mode
   ============================================================ */

const CONFIG = {
  APP_NAME: "MedIQ Pro",
  VERSION: "1.0.0",

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
    MESSAGES:       "/messages"
  }
};

// Global storage key
const STORAGE_KEY = "mediq_pro_session";
