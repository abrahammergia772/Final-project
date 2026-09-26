# =============================================================================
# Wolaita Sodo Hospital — routers/interaction.py  (Module 2: Drug Interaction)
# POST /ai/check-interaction
#
# Uses the uploaded model in backend/models/drug_interaction/:
#   severity_classifier.pkl      LightGBM, 13 features, 5 classes
#   binary_classifier.pkl        logistic regression, same 13 features
#   label_encoders.pkl           encoders for the categorical columns
#   severity_label_encoder.pkl   Contraindicated / Mild / Moderate / Severe / nan
#   feature_columns.pkl          the training column order
#
# The pharmacist page sends two drug names. Drug identity and drug class are
# encoded from those names. The other training columns describe an interaction
# record the checker does not have, so they stay at the encoder's
# "no significant interaction" values unless the caller supplies them.
# A name-only score is an estimate. Known dangerous pairs are still forced
# to severe so a low model score cannot clear them.
# =============================================================================
import logging
import re
from typing import Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from model_loader import load_module

router = APIRouter(tags=["AI · Drug Interaction"])
log = logging.getLogger("mediq.interaction")

CONFIDENT = 0.50
RANK = {"Contraindicated": 4, "Severe": 3, "Moderate": 2, "Mild": 1}

# Pharmacological class for every name in the uploaded drug encoder.
# Class is a property of the drug, and the model requires it.
DRUG_CLASS = {
    "Acamprosate": "Other", "Acyclovir": "Antiviral/Antifungal", "Alendronate": "Other",
    "Allopurinol": "Other", "Alogliptin": "Antidiabetic", "Alprazolam": "CNS/Psychiatric",
    "Aminophylline": "Respiratory", "Amitriptyline": "CNS/Psychiatric", "Amlodipine": "Cardiovascular",
    "Amoxicillin": "Antibiotic", "Ampicillin": "Antibiotic", "Apixaban": "Anticoagulant",
    "Aripiprazole": "CNS/Psychiatric", "Aspirin": "Analgesic/NSAID", "Atazanavir": "Antiviral/Antifungal",
    "Atenolol": "Cardiovascular", "Atorvastatin": "Cardiovascular", "Azathioprine": "Immunosuppressant",
    "Azithromycin": "Antibiotic", "Bisoprolol": "Cardiovascular", "Budesonide": "Respiratory",
    "Bupropion": "CNS/Psychiatric", "Buspirone": "CNS/Psychiatric", "Calcitriol": "Other",
    "Canagliflozin": "Antidiabetic", "Candesartan": "Cardiovascular", "Capecitabine": "Oncology",
    "Carbamazepine": "CNS/Psychiatric", "Carvedilol": "Cardiovascular", "Ceftriaxone": "Antibiotic",
    "Celecoxib": "Analgesic/NSAID", "Cephalexin": "Antibiotic", "Ciprofloxacin": "Antibiotic",
    "Citalopram": "CNS/Psychiatric", "Clarithromycin": "Antibiotic", "Clindamycin": "Antibiotic",
    "Clomipramine": "CNS/Psychiatric", "Clonazepam": "CNS/Psychiatric", "Clopidogrel": "Anticoagulant",
    "Clozapine": "CNS/Psychiatric", "Codeine": "Analgesic/NSAID", "Colchicine": "Other",
    "Cyclophosphamide": "Oncology", "Cyclosporine": "Immunosuppressant", "Dabigatran": "Anticoagulant",
    "Dapagliflozin": "Antidiabetic", "Desvenlafaxine": "CNS/Psychiatric", "Dexamethasone": "Other",
    "Diazepam": "CNS/Psychiatric", "Diclofenac": "Analgesic/NSAID", "Digoxin": "Cardiovascular",
    "Diltiazem": "Cardiovascular", "Disulfiram": "Other", "Domperidone": "GI",
    "Donepezil": "CNS/Psychiatric", "Doxorubicin": "Oncology", "Doxycycline": "Antibiotic",
    "Duloxetine": "CNS/Psychiatric", "Dutasteride": "Other", "Efavirenz": "Antiviral/Antifungal",
    "Empagliflozin": "Antidiabetic", "Enalapril": "Cardiovascular", "Enoxaparin": "Anticoagulant",
    "Eplerenone": "Cardiovascular", "Erlotinib": "Oncology", "Erythromycin": "Antibiotic",
    "Escitalopram": "CNS/Psychiatric", "Everolimus": "Immunosuppressant", "Exenatide": "Antidiabetic",
    "Felodipine": "Cardiovascular", "Fentanyl": "Analgesic/NSAID", "Ferrous sulfate": "Other",
    "Finasteride": "Other", "Fluconazole": "Antiviral/Antifungal", "Fluorouracil": "Oncology",
    "Fluoxetine": "CNS/Psychiatric", "Fluticasone": "Respiratory", "Folic acid": "Other",
    "Fondaparinux": "Anticoagulant", "Furosemide": "Cardiovascular", "Gabapentin": "CNS/Psychiatric",
    "Ganciclovir": "Antiviral/Antifungal", "Gentamicin": "Antibiotic", "Glibenclamide": "Antidiabetic",
    "Glimepiride": "Antidiabetic", "Glipizide": "Antidiabetic", "Haloperidol": "CNS/Psychiatric",
    "Heparin": "Anticoagulant", "Hydrochlorothiazide": "Cardiovascular", "Hydrocodone": "Analgesic/NSAID",
    "Hydroxychloroquine": "Immunosuppressant", "Ibuprofen": "Analgesic/NSAID", "Imatinib": "Oncology",
    "Indapamide": "Cardiovascular", "Indomethacin": "Analgesic/NSAID", "Insulin": "Antidiabetic",
    "Ipratropium": "Respiratory", "Irbesartan": "Cardiovascular", "Irinotecan": "Oncology",
    "Itraconazole": "Antiviral/Antifungal", "Ketoconazole": "Antiviral/Antifungal", "Ketorolac": "Analgesic/NSAID",
    "Lamivudine": "Antiviral/Antifungal", "Lamotrigine": "CNS/Psychiatric", "Lansoprazole": "GI",
    "Levetiracetam": "CNS/Psychiatric", "Levofloxacin": "Antibiotic", "Levothyroxine": "Other",
    "Liraglutide": "Antidiabetic", "Lisinopril": "Cardiovascular", "Lithium": "CNS/Psychiatric",
    "Loperamide": "GI", "Lopinavir": "Antiviral/Antifungal", "Lorazepam": "CNS/Psychiatric",
    "Losartan": "Cardiovascular", "Melatonin": "CNS/Psychiatric", "Meloxicam": "Analgesic/NSAID",
    "Memantine": "CNS/Psychiatric", "Meropenem": "Antibiotic", "Metformin": "Antidiabetic",
    "Methotrexate": "Immunosuppressant", "Metoclopramide": "GI", "Metoprolol": "Cardiovascular",
    "Metronidazole": "Antibiotic", "Mirtazapine": "CNS/Psychiatric", "Misoprostol": "GI",
    "Montelukast": "Respiratory", "Morphine": "Analgesic/NSAID", "Mycophenolate": "Immunosuppressant",
    "Naloxone": "Other", "Naltrexone": "Other", "Naproxen": "Analgesic/NSAID",
    "Nifedipine": "Cardiovascular", "Nitrofurantoin": "Antibiotic", "Olanzapine": "CNS/Psychiatric",
    "Olmesartan": "Cardiovascular", "Omeprazole": "GI", "Ondansetron": "GI",
    "Oseltamivir": "Antiviral/Antifungal", "Oxycodone": "Analgesic/NSAID", "Pantoprazole": "GI",
    "Paracetamol": "Analgesic/NSAID", "Paroxetine": "CNS/Psychiatric", "Phenobarbital": "CNS/Psychiatric",
    "Phenytoin": "CNS/Psychiatric", "Pioglitazone": "Antidiabetic", "Piperacillin": "Antibiotic",
    "Piroxicam": "Analgesic/NSAID", "Posaconazole": "Antiviral/Antifungal", "Pravastatin": "Cardiovascular",
    "Prednisolone": "Other", "Pregabalin": "CNS/Psychiatric", "Quetiapine": "CNS/Psychiatric",
    "Raloxifene": "Other", "Ramipril": "Cardiovascular", "Ranitidine": "GI",
    "Repaglinide": "Antidiabetic", "Rifampicin": "Antibiotic", "Risperidone": "CNS/Psychiatric",
    "Ritonavir": "Antiviral/Antifungal", "Rivaroxaban": "Anticoagulant", "Roflumilast": "Respiratory",
    "Rosuvastatin": "Cardiovascular", "Salbutamol": "Respiratory", "Salmeterol": "Respiratory",
    "Saxagliptin": "Antidiabetic", "Sertraline": "CNS/Psychiatric", "Sildenafil": "Cardiovascular",
    "Simvastatin": "Cardiovascular", "Sirolimus": "Immunosuppressant", "Sitagliptin": "Antidiabetic",
    "Spironolactone": "Cardiovascular", "Sucralfate": "GI", "Tacrolimus": "Immunosuppressant",
    "Tadalafil": "Cardiovascular", "Tamoxifen": "Oncology", "Telmisartan": "Cardiovascular",
    "Tenofovir": "Antiviral/Antifungal", "Terbinafine": "Antiviral/Antifungal", "Tetracycline": "Antibiotic",
    "Theophylline": "Respiratory", "Ticagrelor": "Anticoagulant", "Tiotropium": "Respiratory",
    "Topiramate": "CNS/Psychiatric", "Torsemide": "Cardiovascular", "Tramadol": "Analgesic/NSAID",
    "Trimethoprim": "Antibiotic", "Valproate": "CNS/Psychiatric", "Valsartan": "Cardiovascular",
    "Vancomycin": "Antibiotic", "Venlafaxine": "CNS/Psychiatric", "Verapamil": "Cardiovascular",
    "Vincristine": "Oncology", "Vitamin K": "Other", "Voriconazole": "Antiviral/Antifungal",
    "Warfarin": "Anticoagulant", "Ziprasidone": "CNS/Psychiatric", "Zolpidem": "CNS/Psychiatric",
}

# Pairs that must not be cleared when the name-only model is unsure.
# Wording is taken from the uploaded encoder where a matching phrase exists.
GUARDRAILS = [
    {
        "left": ("warfarin", "apixaban", "rivaroxaban", "dabigatran", "heparin", "enoxaparin", "fondaparinux", "clopidogrel", "ticagrelor"),
        "right": ("aspirin", "ibuprofen", "diclofenac", "naproxen", "indomethacin", "ketorolac", "meloxicam", "piroxicam", "celecoxib", "clopidogrel", "ticagrelor"),
        "title": "Severe Interaction",
        "mechanism": "Additive anticoagulant effect increases bleeding risk.",
        "effect": "Increased bleeding risk.",
        "action": "Avoid combination unless a doctor has already accepted the bleeding risk.",
    },
    {
        "left": ("sildenafil", "tadalafil"),
        "right": ("nitroglycerin", "isosorbide", "nitrate"),
        "title": "Contraindicated",
        "mechanism": "Additive hypotensive effect leads to clinically significant hypotension.",
        "effect": "Hypotension.",
        "action": "Contraindicated - do not use.",
    },
    {
        "left": ("simvastatin", "atorvastatin"),
        "right": ("clarithromycin", "erythromycin", "itraconazole", "ketoconazole", "ritonavir", "posaconazole", "voriconazole"),
        "title": "Severe Interaction",
        "mechanism": "Inhibits CYP3A4 enzyme increasing plasma concentration of co-drug.",
        "effect": "Rhabdomyolysis.",
        "action": "Avoid combination.",
    },
    {
        "left": ("enalapril", "lisinopril", "ramipril", "losartan", "valsartan", "candesartan", "irbesartan", "olmesartan", "telmisartan"),
        "right": ("spironolactone", "eplerenone", "potassium"),
        "title": "Severe Interaction",
        "mechanism": "Increased potassium retention causing life-threatening hyperkalemia.",
        "effect": "Hyperkalemia.",
        "action": "Monitor electrolytes regularly. Do not combine without a documented plan.",
    },
    {
        "left": ("methotrexate",),
        "right": ("trimethoprim", "ibuprofen", "naproxen", "diclofenac", "indomethacin", "ketorolac"),
        "title": "Severe Interaction",
        "mechanism": "Reduces renal tubular secretion increasing drug half-life.",
        "effect": "Bone marrow suppression.",
        "action": "Avoid combination.",
    },
    {
        "left": ("digoxin",),
        "right": ("furosemide", "verapamil", "clarithromycin", "amiodarone"),
        "title": "Severe Interaction",
        "mechanism": "Combined diuretic effect causes hypokalemia and electrolyte imbalance, which raises digoxin toxicity.",
        "effect": "Increased drug toxicity risk.",
        "action": "Monitor drug plasma levels and electrolytes.",
    },
    {
        "left": ("lithium",),
        "right": ("hydrochlorothiazide", "furosemide", "indapamide", "torsemide", "ibuprofen", "naproxen", "diclofenac"),
        "title": "Severe Interaction",
        "mechanism": "Reduces renal clearance and can raise lithium to a toxic level.",
        "effect": "Increased drug toxicity risk.",
        "action": "Avoid combination or monitor drug plasma levels.",
    },
    {
        "left": ("theophylline", "aminophylline"),
        "right": ("ciprofloxacin", "erythromycin", "clarithromycin"),
        "title": "Severe Interaction",
        "mechanism": "Inhibits CYP1A2 elevating theophylline/clozapine levels.",
        "effect": "Increased drug toxicity risk.",
        "action": "Avoid combination or reduce the theophylline dose and monitor levels.",
    },
    {
        "left": ("sertraline", "fluoxetine", "paroxetine", "citalopram", "escitalopram", "duloxetine", "venlafaxine", "desvenlafaxine"),
        "right": ("tramadol",),
        "title": "Severe Interaction",
        "mechanism": "Serotonin reuptake inhibition from both drugs may cause toxicity.",
        "effect": "Serotonin syndrome.",
        "action": "Avoid combination.",
    },
    {
        "left": ("potassium",),
        "right": ("spironolactone", "eplerenone"),
        "title": "Severe Interaction",
        "mechanism": "Increased potassium retention causing life-threatening hyperkalemia.",
        "effect": "Hyperkalemia.",
        "action": "Contraindicated - do not use.",
    },
    {
        "left": ("metformin",),
        "right": ("iodinated contrast", "contrast"),
        "title": "Severe Interaction",
        "mechanism": "Synergistic nephrotoxic effect damages renal tubular cells.",
        "effect": "Nephrotoxicity.",
        "action": "Hold metformin around iodinated contrast and check renal function.",
    },
]

_DOSE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu|units?|%)\b", re.I)
_FORM = re.compile(r"\b(?:inhaler|tablet|tablets|capsule|capsules|injection|syrup|suspension|cream|ointment|drops|vial|ampoule|ampule)\b", re.I)


class InteractionRequest(BaseModel):
    drug_a: str
    drug_b: str
    drug_a_class: Optional[str] = None
    drug_b_class: Optional[str] = None
    interaction_type: Optional[str] = None
    mechanism: Optional[str] = None
    clinical_effect: Optional[str] = None
    management: Optional[str] = None
    evidence_level: Optional[str] = None
    onset: Optional[str] = None
    documented_cases: Optional[float] = None
    contraindicated: Optional[int] = None
    requires_monitoring: Optional[int] = None


def _normalize(name: str) -> str:
    text = (name or "").lower().replace("µ", "u")
    text = _DOSE.sub(" ", text)
    text = _FORM.sub(" ", text)
    text = re.sub(r"[^a-z0-9/+ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _models():
    loaded = load_module("drug")
    needed = (
        "severity_classifier.pkl",
        "binary_classifier.pkl",
        "label_encoders.pkl",
        "severity_label_encoder.pkl",
        "feature_columns.pkl",
    )
    if any(loaded.get(name) is None for name in needed):
        return None
    return loaded


def _encoder_value(encoder, value, fallback: str):
    classes = [str(item) for item in encoder.classes_]
    chosen = value if value and str(value) in classes else fallback
    if chosen not in classes:
        chosen = classes[0]
    return int(encoder.transform([chosen])[0]), chosen


def _resolve(name: str, encoder):
    index = {_normalize(label): label for label in encoder.classes_}
    text = _normalize(name)
    if text in index:
        return index[text]
    best = None
    padded = f" {text} "
    for key, label in index.items():
        if key and f" {key} " in padded and (best is None or len(key) > len(best[0])):
            best = (key, label)
    return None if best is None else best[1]


def _contains(name: str, stems) -> bool:
    text = _normalize(name)
    return any(stem in text for stem in stems)


def _guardrail(drug_a: str, drug_b: str):
    for rule in GUARDRAILS:
        left_a = _contains(drug_a, rule["left"])
        right_b = _contains(drug_b, rule["right"])
        left_b = _contains(drug_b, rule["left"])
        right_a = _contains(drug_a, rule["right"])
        if (left_a and right_b) or (left_b and right_a):
            return rule
    return None


def _feature_row(bundle, drug_a: str, drug_b: str, class_a: str, class_b: str, supplied: dict):
    encoders = bundle["label_encoders.pkl"]
    columns = list(bundle["feature_columns.pkl"])
    defaults = {
        "interaction_type": "No significant interaction",
        "mechanism": "No clinically significant mechanism identified",
        "clinical_effect": "No clinically significant effect",
        "management": "No action required",
        "evidence_level": "Level D - Theoretical / In vitro data",
        "onset": "Variable",
    }
    used = {}
    values = {}
    for key, fallback in (("drug_1", drug_a), ("drug_2", drug_b), ("drug_1_class", class_a), ("drug_2_class", class_b)):
        code, chosen = _encoder_value(encoders[key], fallback, fallback)
        values[key] = code
        used[key] = chosen
    supplied_any = False
    for key, fallback in defaults.items():
        raw = supplied.get(key)
        code, chosen = _encoder_value(encoders[key], raw, fallback)
        if raw and chosen == str(raw):
            supplied_any = True
        values[key] = code
        used[key] = chosen
    for key, default in (("documented_cases", 0.0), ("contraindicated", 0), ("requires_monitoring", 0)):
        raw = supplied.get(key)
        if raw is None:
            values[key] = default
        else:
            values[key] = float(raw)
            supplied_any = True
        used[key] = values[key]
    row = np.array([[values[column] for column in columns]], dtype=float)
    return row, used, supplied_any


def _label_from_proba(bundle, proba):
    model = bundle["severity_classifier.pkl"]
    encoder = bundle["severity_label_encoder.pkl"]
    scored = []
    for class_id, prob in zip(model.classes_, proba):
        name = str(encoder.inverse_transform([int(class_id)])[0])
        if name == "nan":
            continue
        scored.append((name, float(prob)))
    scored.sort(key=lambda item: item[1], reverse=True)
    if not scored:
        return None, 0.0
    return scored[0]


def _binary_probability(bundle, row, supplied_any: bool):
    if not supplied_any:
        return None
    try:
        import pandas as pd
        frame = pd.DataFrame(row, columns=list(bundle["feature_columns.pkl"]))
        binary = bundle["binary_classifier.pkl"]
        class_list = [int(item) for item in binary.classes_]
        proba = binary.predict_proba(frame)[0]
        return round(float(proba[class_list.index(1)]) * 100, 1) if 1 in class_list else None
    except Exception as exc:  # noqa: BLE001
        log.warning("binary interaction model failed: %s", exc)
        return None


def _best_score(bundle, drug_a: str, drug_b: str, class_a: str, class_b: str, supplied: dict):
    """Average both drug orders. One order alone is not stable enough to alert."""
    severity = bundle["severity_classifier.pkl"]
    forward, _, supplied_any = _feature_row(bundle, drug_a, drug_b, class_a, class_b, supplied)
    reverse, _, reverse_supplied = _feature_row(bundle, drug_b, drug_a, class_b, class_a, supplied)
    averaged = (severity.predict_proba(forward)[0] + severity.predict_proba(reverse)[0]) / 2.0
    label, confidence = _label_from_proba(bundle, averaged)
    return {
        "label": label,
        "confidence": confidence,
        "supplied": supplied_any or reverse_supplied,
        "binary_probability": _binary_probability(bundle, forward, supplied_any or reverse_supplied),
    }


def _copy_for(label: str, firm: bool):
    if not firm or label not in RANK:
        return {
            "level": "uncertain",
            "title": "No high-confidence interaction",
            "mechanism": "The uploaded severity model did not reach a confident result from these drug names.",
            "effect": "A low-confidence estimate is not a safety clearance.",
            "action": "Check a clinical reference before dispensing.",
        }
    copies = {
        "Contraindicated": ("severe", "Contraindicated", "Do not dispense together until a pharmacist or doctor checks a clinical reference."),
        "Severe": ("severe", "Severe Interaction", "Avoid the combination or get a clinical review before dispensing."),
        "Moderate": ("moderate", "Moderate Interaction", "Monitor the patient and confirm the pair in a clinical reference."),
        "Mild": ("mild", "Mild Interaction", "Standard monitoring. Confirm the pair if the patient is high risk."),
    }
    level, title, action = copies[label]
    return {
        "level": level,
        "title": title,
        "mechanism": f"The uploaded severity model classified this pair as {label.lower()} from the trained drug names.",
        "effect": "This is a model estimate, not a documented interaction record.",
        "action": action,
    }


def _unknown_copy():
    return {
        "level": "unknown",
        "title": "Drug not in the uploaded model",
        "mechanism": "One or both names are outside the 198 drugs the uploaded model was trained on.",
        "effect": "The model cannot score this pair.",
        "action": "Check a clinical reference. Known dangerous pairs are still flagged.",
    }


def predict_interaction(drug_a: str, drug_b: str, supplied: Optional[dict] = None) -> dict:
    """Score one pair. Safe to call from tests without the HTTP layer."""
    supplied = supplied or {}
    left = (drug_a or "").strip()
    right = (drug_b or "").strip()
    if not left or not right:
        return {"level": "unknown", "title": "Enter both drug names", "mechanism": "", "effect": "",
                "action": "Enter two drug names.", "drug_a": drug_a, "drug_b": drug_b,
                "confidence": None, "model": "severity_classifier", "model_version": "uploaded",
                "source": "none"}
    if _normalize(left) == _normalize(right):
        return {"level": "uncertain", "title": "Enter two different drugs", "mechanism": "A drug is not checked against itself.",
                "effect": "", "action": "Add the second drug.", "drug_a": left, "drug_b": right,
                "confidence": None, "model": "severity_classifier", "model_version": "uploaded", "source": "none"}

    bundle = _models()
    matched_a = matched_b = class_a = class_b = None
    score = None
    if bundle is not None:
        encoders = bundle["label_encoders.pkl"]
        matched_a = _resolve(left, encoders["drug_1"])
        matched_b = _resolve(right, encoders["drug_2"])
        if matched_a and matched_b:
            class_a = supplied.get("drug_a_class") or DRUG_CLASS.get(matched_a, "Other")
            class_b = supplied.get("drug_b_class") or DRUG_CLASS.get(matched_b, "Other")
            try:
                score = _best_score(bundle, matched_a, matched_b, class_a, class_b, supplied)
            except Exception as exc:  # noqa: BLE001
                log.warning("uploaded drug model failed: %s", exc)
                score = None

    rule = _guardrail(left, right)
    if score is None:
        details = _unknown_copy() if not rule else {
            "level": "severe",
            "title": rule["title"],
            "mechanism": rule["mechanism"],
            "effect": rule["effect"],
            "action": rule["action"],
        }
        source = "guardrail" if rule else "outside-vocabulary"
        confidence = None
        model_label = None
    else:
        firm = score["confidence"] >= CONFIDENT or bool(score["supplied"])
        details = _copy_for(score["label"], firm)
        confidence = round(score["confidence"] * 100, 1)
        model_label = score["label"]
        lean = f"Model estimate: {model_label} at {confidence}%."
        if not firm:
            details["effect"] = lean + " " + details["effect"]
        if rule:
            details = {
                "level": "severe",
                "title": rule["title"],
                "mechanism": rule["mechanism"],
                "effect": rule["effect"] + " " + lean,
                "action": rule["action"],
            }
        source = "uploaded-model+guardrail" if rule else "uploaded-model"
        if matched_a and matched_b:
            details["mechanism"] = (
                f"Matched {matched_a} ({class_a}) and {matched_b} ({class_b}). " + details["mechanism"]
            )

    return {
        "level": details["level"],
        "title": details["title"],
        "mechanism": details["mechanism"],
        "effect": details["effect"],
        "action": details["action"],
        "drug_a": left,
        "drug_b": right,
        "matched_drug_a": matched_a,
        "matched_drug_b": matched_b,
        "drug_a_class": class_a,
        "drug_b_class": class_b,
        "confidence": confidence,
        "model_label": model_label,
        "model": "severity_classifier",
        "model_version": "uploaded",
        "source": source,
        "binary_probability": None if score is None else score.get("binary_probability"),
    }


@router.get("/ai/interaction-drugs")
def interaction_drugs():
    bundle = _models()
    if bundle is None:
        return {"drugs": sorted(DRUG_CLASS), "source": "class-map"}
    drugs = [str(name) for name in bundle["label_encoders.pkl"]["drug_1"].classes_]
    return {"drugs": drugs, "count": len(drugs), "source": "uploaded-model"}


@router.post("/ai/check-interaction")
def check_interaction(req: InteractionRequest):
    supplied = {
        "drug_a_class": req.drug_a_class,
        "drug_b_class": req.drug_b_class,
        "interaction_type": req.interaction_type,
        "mechanism": req.mechanism,
        "clinical_effect": req.clinical_effect,
        "management": req.management,
        "evidence_level": req.evidence_level,
        "onset": req.onset,
        "documented_cases": req.documented_cases,
        "contraindicated": req.contraindicated,
        "requires_monitoring": req.requires_monitoring,
    }
    return predict_interaction(req.drug_a, req.drug_b, supplied)
