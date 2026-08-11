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
│   ├── admin/              ← 6 pages
│   ├── manager/            ← 5 pages
│   ├── doctor/             ← 6 pages (incl. AI Diagnosis)
│   ├── nurse/              ← 4 pages (incl. Vitals AI)
│   ├── pharmacist/         ← 5 pages (incl. AI Interaction & Forecast)
│   ├── laboratory/         ← 4 pages (incl. AI Analyzer)
│   ├── reception/          ← 4 pages (incl. Appointment AI)
│   └── patient/            ← 6 pages (incl. AI Chatbot)
│
├── models/                 ← (coming) your trained .pkl models
├── backend/                ← (coming) FastAPI app serving the models
└── tools/build_frontend.py ← dev-only page generator (not needed to run)
```

**41 pages · 4 CSS · 4 JS · 0 frameworks** — pure HTML5 / CSS3 / Vanilla JavaScript.

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
