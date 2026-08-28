#!/usr/bin/env python3
"""End-to-end test of all 7 AI modules via the running FastAPI server."""
import json, time, urllib.request

BASE = "http://localhost:8090"

def call(method, path, payload=None, token=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token: req.add_header("Authorization", "Bearer " + token)
    data = json.dumps(payload).encode() if payload is not None else None
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, data, timeout=120) as r:
            body = json.loads(r.read())
            return r.status, body, (time.time() - t0) * 1000
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}"), (time.time() - t0) * 1000

results = []
def record(module, endpoint, status, ms, note):
    ok = status == 200
    results.append((module, endpoint, status, ms, note))
    print(f"{'✓' if ok else '✗'} [{module}] {endpoint} → {status} ({ms:.0f} ms) {note}")

# ---- auth ----
st, body, ms = call("POST", "/auth/login", {"email": "doctor@wsh.et", "password": "doctor123"})
assert st == 200, f"login failed: {body}"
TOKEN = body["token"]
print(f"✓ [auth] login as doctor@wsh.et → role={body['role']}, token issued ({ms:.0f} ms)\n")

# ---- Module 1: Clinical Decision Support ----
st, b, ms = call("POST", "/ai/predict-disease", {
    "symptoms": "fever, sore throat, runny nose, headache and mild cough",
    "vitals": {"temp": 37.9, "hr": 92}, "history": ["no chronic illness"]}, TOKEN)
top = ", ".join(f"{p['disease']} {p['confidence']}%" for p in (b.get("predictions") or b.get("top3") or [])[:3])
record("clinical", "/ai/predict-disease", st, ms, f"top: {top or b}")

# ---- Module 2: Drug Interaction ----
for a, d in [("warfarin", "ibuprofen"), ("amoxicillin", "paracetamol")]:
    st, b, ms = call("POST", "/ai/check-interaction", {"drug_a": a, "drug_b": d}, TOKEN)
    sev = b.get("severity") or b.get("level") or b.get("classification") or "?"
    record("drug", "/ai/check-interaction", st, ms, f"{a} + {d} → {sev}")

# ---- Module 3: Lab Result Analyzer ----
st, b, ms = call("POST", "/ai/analyze-lab", {
    "test_type": "blood", "patient": "P-001",
    "values": {"hemoglobin": 8.1, "mcv": 72, "wbc": 6.5, "rbc": 3.9, "age": 34}}, TOKEN)
pred = b.get("prediction") or b.get("condition") or b.get("predictions") or b
record("lab", "/ai/analyze-lab", st, ms, f"anemia-like panel → {json.dumps(pred)[:160]}")

# ---- Module 4: Vitals Alert ----
st, b, ms = call("POST", "/ai/check-vitals",
    {"hr": 128, "sys": 85, "dia": 52, "temp": 39.4, "spo2": 89, "rr": 27, "age": 67}, TOKEN)
record("vitals", "/ai/check-vitals", st, ms, f"critical inputs → {json.dumps({k: b[k] for k in list(b)[:5]})[:170]}")
st, b, ms = call("POST", "/ai/check-vitals",
    {"hr": 74, "sys": 118, "dia": 76, "temp": 36.7, "spo2": 98, "rr": 14, "age": 30}, TOKEN)
record("vitals", "/ai/check-vitals", st, ms, f"normal inputs → {json.dumps({k: b[k] for k in list(b)[:5]})[:170]}")

# ---- Module 5: Inventory Forecast ----
for drug in ["Paracetamol", "Amoxicillin"]:
    st, b, ms = call("POST", "/ai/forecast-inventory", {"drug_name": drug, "days": 14}, TOKEN)
    s = json.dumps(b)
    key = next((k for k in ["forecast", "total_predicted", "total", "summary"] if k in b), "?")
    record("inventory", "/ai/forecast-inventory", st, ms, f"{drug}/14d → {key}: {json.dumps(b.get(key))[:120]}")

# ---- Module 6: Appointment No-Show ----
st, b, ms = call("POST", "/ai/predict-appointment", {
    "patient_age": 34, "appointment_date": "2026-09-04", "appointment_time": "09:00",
    "department": "Internal Medicine", "doctor_id": "Dr. Daniel Alemu",
    "appointment_type": "Scheduled", "gender": "Male",
    "insurance_type": "EHBPA", "reminder_channel": "SMS"}, TOKEN)
s = json.dumps(b)
risk = b.get("risk") or b.get("no_show_probability") or b.get("probability") or s[:120]
record("appointment", "/ai/predict-appointment", st, ms, f"no-show risk → {json.dumps(risk)[:150] if not isinstance(risk,str) else risk}")

# ---- Module 7: Symptom Chatbot ----
st, b, ms = call("POST", "/ai/symptom-chat", {"message": "I have chest pain and difficulty breathing"}, TOKEN)
ur = b.get("urgency") or b.get("triage") or "?"
record("symptom", "/ai/symptom-chat", st, ms, f"emergency text → urgency={ur}")
st, b, ms = call("POST", "/ai/symptom-chat", {"message": "mild headache and tired for two days"}, TOKEN)
ur = b.get("urgency") or b.get("triage") or "?"
dx = (b.get("predictions") or [{}])[0].get("disease", "")
record("symptom", "/ai/symptom-chat", st, ms, f"routine text → urgency={ur}, top={dx}")

# ---- health ----
st, b, ms = call("GET", "/health")
record("system", "/health", st, ms, f"models: {b.get('models')}")

print("\n" + "=" * 74)
fails = [r for r in results if r[2] != 200]
print(f"RESULT: {len(results)-len(fails)}/{len(results)} checks passed" + (f" — FAILURES: {[r[0]+' '+r[1] for r in fails]}" if fails else " 🎉"))
