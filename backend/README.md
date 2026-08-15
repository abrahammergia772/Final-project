# MedIQ Pro — Backend (FastAPI + Supabase)

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
SUPABASE_SERVICE_KEY=…  (service_role key — recommended for server writes)
MODEL_DOWNLOAD_URLS=…   (only needed for the >25 MB appointment model — see below)
SECRET_KEY=…
CORS_ORIGINS=*          (or your frontend URL, e.g. https://wsh-cpug.netlify.app)
```

## 🗄️ Set up Supabase (5 minutes)

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** → paste the contents of `backend/supabase_schema.sql` → **Run**.
   This creates all tables (users, patients, appointments, prescriptions, inventory,
   lab, bills, complaints, messages, attendance, documents, …) with RLS policies.
3. Copy the project **URL** and **anon key** into the Render env vars above.
4. Optionally seed demo users:
   ```sql
   insert into users (email, password_hash, name, role) values
   ('admin@mediq.pro','<sha256 of admin123>','Solomon Tadesse','admin'),
   ('doctor@mediq.pro','<sha256 of doctor123>','Dr. Daniel Alemu','doctor');
   ```
   (`password_hash` is `sha256(password)` — compute it with
   `python -c "import hashlib; print(hashlib.sha256(b'admin123').hexdigest())"`)

> **No Supabase configured?** The API automatically falls back to built-in demo
> data — the whole system still works end-to-end while you set it up.

## 🤖 The 7 AI endpoints (all use your trained models)

| Module | Endpoint | Model files used |
|---|---|---|
| 1 Clinical | `POST /ai/predict-disease` | clinical_decision: TF-IDF + RF + XGB ensemble |
| 2 Drug interaction | `POST /ai/check-interaction` | drug_interaction: TF-IDF + RF/XGB |
| 3 Lab analyzer | `POST /ai/analyze-lab` | lab: 78-feature RF/XGB + scaler |
| 4 Vitals alert | `POST /ai/check-vitals` | vitals: 26-feature RF/XGB + RobustScaler |
| 5 Inventory forecast | `POST /ai/forecast-inventory` | inventory: XGBRegressor + Prophet JSONs |
| 6 Appointment AI | `POST /ai/predict-appointment` | appointment: XGB (RF optional — see below) |
| 7 Symptom chatbot | `POST /ai/symptom-chat` | symptom-checker: TF-IDF + RF/XGB |

Plus:
- `POST /auth/login`, `/auth/signup`, `/auth/reset-password` (Supabase `users` table)
- Generic CRUD for every data table: `GET/POST/PUT/DELETE /users`, `/patients`,
  `/appointments`, `/inventory`, `/complaints`, `/messages`, `/attendance`, …

## 🔓 SOLUTION: the >25 MB appointment model (GitHub limit)

GitHub blocks files **above 25 MB**. Your `rf_appointment.pkl` (the RandomForest
half of the appointment ensemble) is over the limit, which is why the upload
failed. The backend already **works with the XGB model alone**, but here are
**3 free ways** to get the RF model in and restore the full ensemble:

### Option A — GitHub Release asset (recommended, works on Render free)
1. GitHub → **Releases** → **New release** → tag `v1-models`.
2. Upload `rf_appointment.pkl` as a **Release asset** (assets allow up to **2 GB**).
3. Copy the asset URL, e.g.
   `https://github.com/abrahammergia772/Final-project/releases/download/v1-models/rf_appointment.pkl`
4. In Render add env var:
   ```
   MODEL_DOWNLOAD_URLS=appointment_rf=<that-URL>
   ```
5. On every deploy, `download_models.py` fetches it into
   `backend/models/appointment/rf_appointment.pkl` and the RF+XGB ensemble kicks in.

### Option B — Compress it under 25 MB (no external hosting)
```bash
python -c "import joblib; m=joblib.load('rf_appointment.pkl'); joblib.dump(m,'rf_appointment.pkl',compress=3)"
```
If the result is < 25 MB, commit it normally. (This also makes the repo smaller.)

### Option C — Supabase Storage
Upload the file to a Supabase Storage bucket (free tier objects up to 50 MB) and
set `MODEL_DOWNLOAD_URLS=appointment_rf=<public-bucket-url>`.

> The `a` file in `backend/models/appointment/` was the leftover of the failed
> upload — it has been removed.

## 🧪 Run locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# docs: http://localhost:8000/docs
```

## 🔌 Point the frontend at this backend

In `mediq-pro-frontend/assets/js/config.js`:
```js
API_BASE_URL: "https://your-backend.onrender.com",
DEMO_MODE: false,
```
Then deploy the frontend (Netlify, publish dir `mediq-pro-frontend/`).
