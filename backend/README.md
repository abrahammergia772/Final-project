# Wolaita Sodo Hospital — Backend (FastAPI + Supabase)

All **7 AI modules** served from your **trained models** in `backend/models/`,
plus **Supabase** as the database and a **Render**-ready config.

## 🚀 Deploy on Render (fastest)

**Option A — Blueprint (recommended):**
Render → **New → Blueprint** → select your repo. It reads `render.yaml`
(root dir `backend`, build & start commands) automatically.

**Option B — Manual Web Service:**

| Field | Value |
|---|---|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port 10000` |
| **Plan** | Free |

**Environment variables (Render → Environment):**
```
SUPABASE_URL=…          (from Supabase project settings → API)
SUPABASE_KEY=…          (anon public key)
SUPABASE_SERVICE_KEY=…  (service_role key — required for server-side CRUD; never expose it)

SECRET_KEY=…            (long random value; required in production)
CORS_ORIGINS=https://your-frontend.example (exact comma-separated origins; never use *)
CORS_ALLOW_ALL=0
```

## 🗄️ Set up Supabase (5 minutes)

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** → paste `backend/supabase_schema.sql` → **Run**.
   That file creates every table and turns on row level security. It does not
   insert patients. The split files live in `backend/sql/`:
   - `001_schema.sql` then `002_security.sql` for a new project
   - `004_upgrade_existing.sql` then `002_security.sql` if the old schema already ran
   - `003_seed.sql` only for a training database
3. Copy the project **URL**, **anon key**, and **service_role key** into the Render env vars above.
   The service_role key stays on the server. Leave the frontend `SUPABASE_URL` and `SUPABASE_KEY` empty.
4. For a training database only, run `backend/sql/003_seed.sql`. Those demo passwords are public. Do not use them with real patients.

> **No Supabase configured?** The API uses built-in demo data. Once `SUPABASE_URL` is set, a database error is returned instead of silently switching to the demo passwords.

## 🤖 The 7 AI endpoints (all use your trained models)

| Module | Endpoint | Model files used |
|---|---|---|
| 1 Clinical | `POST /ai/predict-disease` | clinical_decision: TF-IDF + RF + XGB ensemble |
| 2 Drug interaction | `POST /ai/check-interaction` | drug_interaction: TF-IDF + RF/XGB |
| 3 Lab analyzer | `POST /ai/analyze-lab` | lab: 78-feature RF/XGB + scaler |
| 4 Vitals alert | `POST /ai/check-vitals` | vitals: 26-feature RF/XGB + RobustScaler |
| 5 Inventory forecast | `POST /ai/forecast-inventory` | inventory: XGBRegressor + Prophet JSONs |
| 6 Appointment assistant | Groq on saved visits. Reminders also send SMS through Africa's Talking when `AT_API_KEY` and `AT_USERNAME` are set. | no model file |
| 7 Symptom chatbot | `POST /ai/symptom-chat` | clinical_decision: doctor_ai_model |

Plus:
- `POST /auth/login`, `/auth/signup`, `/auth/reset-password` (Supabase `users` table)
- Generic CRUD for every data table: `GET/POST/PUT/DELETE /users`, `/patients`,
  `/appointments`, `/inventory`, `/complaints`, `/messages`, `/attendance`, …

## 🧪 Run locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# docs: http://localhost:8000/docs
```

## 🔌 Point the frontend at this backend

In `frontend/assets/js/config.js`:
```js
API_BASE_URL: "https://your-backend.onrender.com",
DEMO_MODE: false,
```
Then deploy the frontend (Netlify, publish dir `frontend/`).
