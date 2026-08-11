# 🏥 MedIQ Pro — AI-Powered Hospital Management System

University thesis project — **Wolaita Sodo University, Ethiopia**
Department of Electrical and Computer Engineering

> AI-integrated Hospital Management System with a pure HTML/CSS/JS frontend,
> FastAPI backend and trained `.pkl` ML models. The frontend is fully functional
> **right now** using built-in demo data — the backend + `models/` folder will be
> added to this repo as they are trained.

---

## 📁 Repo structure

```
Final-project/
│
├── mediq-pro-frontend/     ← THIS IS THE FRONTEND (static, deploy as-is)
│   ├── index.html          ← Login page
│   ├── assets/
│   │   ├── css/            ← global, sidebar, components, dashboard
│   │   ├── js/             ← config, auth, api, utils
│   │   └── images/logo.png
│   ├── admin/              ← 7 pages (incl. Announcements)
│   ├── manager/            ← 6 pages (incl. Finance)
│   ├── doctor/             ← 7 pages (incl. AI Diagnosis, Referrals)
│   ├── nurse/              ← 5 pages (incl. Vitals AI, Observations)
│   ├── pharmacist/         ← 6 pages (incl. AI modules, Suppliers & POs)
│   ├── laboratory/         ← 5 pages (incl. AI Analyzer, Sample Tracking)
│   ├── reception/          ← 5 pages (incl. Appointment AI, Insurance)
│   └── patient/            ← 7 pages (incl. AI Chatbot, Messages)
│
├── models/                 ← (coming) your trained .pkl models
├── backend/                ← (coming) FastAPI app serving the models
└── tools/build_frontend.py ← dev-only page generator (not needed to run)
```

**95 pages · 8 roles · 7 AI modules · 0 frameworks** — pure HTML5 / CSS3 / Vanilla JavaScript.

### Messaging, accounts & access control

- **📬 Messages inbox for every role** — received-message list with unread badges; **single-click** a message to open it in a popup with full detail, **double-click** to minimize (collapse) it; compose/send with simulated replies; Sent tab.
- **📝 Sign-up page** (`signup.html`) — full registration: account, personal info (DOB, gender, phone, blood type, region), emergency contact, role (patient or staff), insurance, terms consent. Patient accounts activate instantly; staff accounts await admin approval.
- **🔑 Forgot password** (`forgot-password.html`) — email → 6-digit reset code → set new password (3-step flow).
- **🔔 Notifications open full detail** — clicking any notification in the topbar bell opens a popup with category, time, status and full message, plus a link to the related page.
- **🛡️ Permission-controlled tabs** — the admin can grant/revoke every tab per role on the **Roles & Permissions** page; changes apply **automatically** — a granted tab appears in that role's sidebar on their next load, a revoked one disappears.
- **📢 Complaints** — patients submit complaints (category, priority, description) and track status; only the **General Manager** can read every complaint and give a solution, which the patient then sees in their portal. The patient's old **Lab Results** tab was removed.
- **🕐 Shifts & Attendance (all hospital workers)** — every worker (admin, manager, doctor, nurse, pharmacist, laboratory, reception) has a **fingerprint check-in panel** with an animated scanner: attendance is captured **automatically by fingerprint devices** when staff enter the facility (demo-simulated; touch to scan/check out), plus their shift roster for the week and attendance history with a 7-day sparkline.
  - **Admin** additionally manages **shift templates** (create/edit/delete), the **shift roster** (assign staff), **all workers' attendance** (filterable, CSV export) and **fingerprint devices** (status, enrolled staff, sync).
  - **Manager** additionally sees **department attendance** with **manual override** for absent staff and the department roster.
- **📄 Documents (role-based access)** — every staff role has **role-scoped access**: each role sees only the document types it handles (laboratory → lab reports, pharmacist → prescriptions, reception → consent/insurance, nurse → clinical view-only, etc.) and each role gets only the actions it's allowed (upload / edit / delete / view / download per role). Patients **no longer have a Documents tab**.
- **🪪 Patient Information & Card system** — staff roles get a **card-grid patient directory** (name, ID, blood type, condition, status) with a full **Patient Information** popup (emergency contact, insurance, chronic conditions…) and one-click **printable Patient ID card** with barcode. Patients get their own **Health Card** page (gradient hospital card with photo, blood type, emergency contact, barcode) that can be printed or emailed.
- **📊 Reports for all staff roles** — admin, manager, doctor, nurse, pharmacist, laboratory and reception each get role-appropriate **report generation** (templates, date range, print/CSV, generated-report history). The **doctor can compose an individual health report and send it to a specific patient** — it lands in that patient's Messages inbox as a 📄 Health Report.
- **🎬 Health Videos (free YouTube AI suggestions)** — patients get **video suggestions matched to their conditions** (e.g. hypertension → Mayo Clinic's "Explains Hypertension") with embedded players, thumbnails and "Open on YouTube" links; an AI search box finds educational videos for any topic. Doctors get a condition-driven video library to share with patients. **100% free**: verified videos are embedded/thumbnailed; a **live YouTube Data API key** is configured in `config.js` to upgrade the search to real, always-fresh results (graceful fallback to the curated library if the API is unreachable). Every suggestion shows an "educational only — not medical advice" disclaimer.

### Professional features (added per role)

| Role | Feature page | What it does |
|------|--------------|--------------|
| Admin | `announcements.html` | Broadcast announcements to all staff or a role — publish now / schedule / draft, urgent flag, view counts |
| Manager | `finance.html` | Financial analytics — revenue vs expenses (12 months), budget vs actual, revenue by department, top revenue services, CSV export |
| Doctor | `referrals.html` | Refer patients to specialists/hospitals with priority (routine/urgent/emergency) and full status tracking |
| Nurse | `observations.html` | Nursing observations — pain score (0–10), fluid intake/output, fluid-balance chart, observation log |
| Pharmacist | `suppliers.html` | Supplier management + purchase orders, "receive PO" workflow, restock suggestions from the AI forecast |
| Laboratory | `samples.html` | Sample tracking pipeline (Collected → Received → Processing → Result → Completed) with TAT per sample |
| Reception | `insurance.html` | Insurance coverage verification (EHBPA, Nyala, GIB…), policy validity, coverage % |
| Patient | `messages.html` | Secure messaging with Front Desk / Doctor / Pharmacy — conversations, auto-replies |

Plus: the **topbar bell now shows live notifications** (low-stock items, AI-flagged abnormal lab results, today's appointments) and the **doctor consultation page can schedule follow-ups**.

---

## 🚀 Quick start (no backend needed)

The frontend ships with **DEMO_MODE = true**, so every page, table and AI module
runs on realistic mock data. Open `mediq-pro-frontend/index.html` in any browser
(or serve the folder) and log in with any demo account:

| Role       | Email              | Password      |
|------------|--------------------|---------------|
| Admin      | `admin@mediq.pro`  | `admin123`    |
| Manager    | `manager@mediq.pro`| `manager123`  |
| Doctor     | `doctor@mediq.pro` | `doctor123`   |
| Nurse      | `nurse@mediq.pro`  | `nurse123`    |
| Pharmacist | `pharmacist@mediq.pro` | `pharmacist123` |
| Laboratory | `lab@mediq.pro`    | `lab123`      |
| Reception  | `reception@mediq.pro` | `reception123` |
| Patient    | `patient@mediq.pro`| `patient123`  |

The login page also has **one-click demo buttons** for every role.

Run locally:

```bash
cd mediq-pro-frontend
python3 -m http.server 8000      # or: npx serve .
# open http://localhost:8000
```

---

## 🤖 The 7 AI modules (integrated in the UI)

All AI calls go through `assets/js/api.js`. In demo mode they return realistic
mock predictions; point `CONFIG.API_BASE_URL` at your FastAPI backend to go live.

| # | Module | Endpoint (POST) | Page |
|---|--------|-----------------|------|
| 1 | Clinical Decision Support | `/ai/predict-disease` | `doctor/ai-diagnosis.html` |
| 2 | Drug Interaction Checker | `/ai/check-interaction` | `pharmacist/ai-interaction.html` |
| 3 | Lab Result Analyzer | `/ai/analyze-lab` | `laboratory/ai-analyzer.html` |
| 4 | Vitals Alert System | `/ai/check-vitals` | `nurse/vitals.html` |
| 5 | Inventory Forecasting | `/ai/forecast-inventory` | `pharmacist/ai-forecast.html` |
| 6 | Appointment / No-show AI | `/ai/predict-appointment` | `reception/appointments.html` |
| 7 | Symptom Checker Chatbot | `/ai/symptom-chat` | `patient/ai-chatbot.html` |

Every AI output shows a clinical disclaimer, confidence bars and error/loading states.

---

## 🔌 Going live (when your backend + models are ready)

1. **Frontend**: deploy `mediq-pro-frontend/` to Netlify (build command: *none*,
   publish directory: `mediq-pro-frontend/`).
2. **Backend**: deploy your FastAPI app to Render, upload `.pkl` files to
   `models/`, endpoints as in the table above.
3. In `mediq-pro-frontend/assets/js/config.js` set:
   ```js
   API_BASE_URL: "https://your-backend.onrender.com",
   DEMO_MODE: false,
   ```
4. **Supabase**: put your URL + anon key into `config.js`. Never commit secret keys.

## 📝 Notes

- All money shown in **ETB**, dates in **DD/MM/YYYY** (Ethiopian standard).
- Responsive: sidebar collapses to a hamburger menu below 768px.
- `tools/build_frontend.py` regenerates the 40 role pages from shared templates —
  edit the `bodies_*.py` files and re-run `python3 tools/build_frontend.py` if you
  want to change the shell/layout everywhere at once. The static pages in
  `mediq-pro-frontend/` are the deployable output.
