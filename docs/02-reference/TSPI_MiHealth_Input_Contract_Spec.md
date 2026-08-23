# MiHealth → TSPI Input Contract — Fix Spec

*For the MiHealth Portal / Intelligence-Layer team. The recent fibroid case produced a 1-axis
report because the `/report` call carried **only** `symptoms: "stress"` — the patient's labs,
other symptoms, imaging, medications and conditions never reached the engine. This spec defines
exactly what MiHealth must send so TSPI sees the same data the doctor had.*

> Proven impact: with the **full** payload below, the same engine goes from **1 axis → 7 axes**
> (NSS 40→97, 1 module → 8). The fix is the input, not the model.

---

## 1. Where the fix lives (MiHealth's job, not TSPI's)

```
Patient uploads lab PDF / enters symptoms
        │
        ▼
[ MiHealth Intelligence Layer ]   ← THE GAP IS HERE
   • OCR engine        (PDF/image → text)
   • Medical parser    (text → structured labs[], conditions[], meds[])
   • Symptom intake    (free-text → symptoms string)
   • De-identifier     (strip PII → case_id + age band + sex)
        │  builds the full PatientInput
        ▼
POST /report  → TSPI brain  (axes → NSS/SPS → modules → report)
```
TSPI scores whatever it receives. **MiHealth must populate the fields** before calling `/report`.

---

## 2. The contract — full `PatientInput`

| Field | Type | Required | Notes |
|---|---|---|---|
| `case_id` | string | ✅ | de-identified handle (e.g. `TSPI-2026-000123`). **No name/DOB.** |
| `age_band` | string | recommended | e.g. `"mid-40s"` (NOT exact DOB) |
| `sex` | `female`/`male`/`other`/`unknown` | recommended | |
| `symptoms` | string | ✅ | **ALL** presenting symptoms, comma-separated — not just the chief complaint |
| `labs` | array of `LabResult` | ✅ when a report exists | **the critical one** — see §3 |
| `imaging` | string[] | when available | e.g. `["pelvic ultrasound: 4cm intramural fibroid"]` |
| `medications` | string[] | when available | current meds (drives safety flags) |
| `conditions` | string[] | when available | known diagnoses (drives safety flags) |
| `lifestyle` | object | optional | `{"diet":"vegetarian","sleep":"poor","stress":"high"}` |
| `omics` | object | optional | future: genome/microbiome/etc. |
| `consent` | object | ✅ | `{"ai_analysis": true, "doctor_sharing": true}` |

### `LabResult` (each lab row)
| Field | Type | Notes |
|---|---|---|
| `analyte` | string | test name, e.g. `"CRP"`, `"HbA1c"`, `"Hemoglobin"`, `"TSH"` |
| `value` | number or string | the result |
| `unit` | string | e.g. `"mg/L"`, `"%"`, `"g/dL"` |
| `ref_low` | number | reference range low (omit if N/A) |
| `ref_high` | number | reference range high (omit if N/A) |
| `flag` | string | optional `"high"`/`"low"`; TSPI computes it from the range if omitted |

---

## 3. Parsing the lab report into `labs[]` (the key step)

For every result row in the uploaded report, emit one `LabResult`. From this patient's report:

| Report row | → `labs[]` entry |
|---|---|
| CRP 21.57 mg/L (ref < 5) | `{"analyte":"CRP","value":21.57,"unit":"mg/L","ref_high":5.0}` |
| HbA1c 6.5 % (≤5.6) | `{"analyte":"HbA1c","value":6.5,"unit":"%","ref_high":5.6}` |
| Haemoglobin 10.8 g/dL (12–16) | `{"analyte":"Hemoglobin","value":10.8,"unit":"g/dL","ref_low":12.0,"ref_high":16.0}` |
| MCV 67.2 fL (82–101) | `{"analyte":"MCV","value":67.2,"unit":"fL","ref_low":82.0,"ref_high":101.0}` |
| TSH 0.416 µIU/mL (0.54–5.3) | `{"analyte":"TSH","value":0.416,"unit":"uIU/mL","ref_low":0.54,"ref_high":5.3}` |
| Vitamin D 27.6 ng/mL (>30) | `{"analyte":"Vitamin D","value":27.6,"unit":"ng/mL","ref_low":30.0}` |

**Parsing rules**
- Send **every** numeric result, not just abnormal ones (TSPI decides severity).
- Keep the **reference range** — it's how TSPI flags high/low without hard-coding thresholds.
- Use a clean `analyte` name; TSPI normalizes common synonyms, and **unknown analytes are matched
  semantically (RAG)** — so unusual tests still map, just send them.
- One row per result; for panels (CBC, thyroid, lipid) emit each sub-result separately.

---

## 4. Before vs after (this patient)

**❌ What was sent (produced the 2-page report):**
```json
{ "case_id": "TSPI-2026-000001", "symptoms": "stress", "consent": {"ai_analysis": true} }
```

**✅ What SHOULD be sent:**
```json
{
  "case_id": "TSPI-2026-000123",
  "age_band": "mid-40s",
  "sex": "female",
  "symptoms": "uterine fibroid, hypertension, body inflammation, post-menopausal bleeding (stress-triggered), fatigue, stress",
  "labs": [
    {"analyte": "CRP", "value": 21.57, "unit": "mg/L", "ref_high": 5.0},
    {"analyte": "HbA1c", "value": 6.5, "unit": "%", "ref_high": 5.6},
    {"analyte": "Hemoglobin", "value": 10.8, "unit": "g/dL", "ref_low": 12.0, "ref_high": 16.0},
    {"analyte": "MCV", "value": 67.2, "unit": "fL", "ref_low": 82.0, "ref_high": 101.0},
    {"analyte": "TSH", "value": 0.416, "unit": "uIU/mL", "ref_low": 0.54, "ref_high": 5.3},
    {"analyte": "Vitamin D", "value": 27.6, "unit": "ng/mL", "ref_low": 30.0}
  ],
  "imaging": ["pelvic ultrasound: intramural uterine fibroid"],
  "medications": ["amlodipine"],
  "conditions": ["hypertension", "post-menopausal"],
  "lifestyle": {"diet": "vegetarian", "stress": "high"},
  "consent": {"ai_analysis": true, "doctor_sharing": true}
}
```
**Result of the fix:** axes `A1, A5, A26, A33, A8, A15, A34`; NSS 97 / Level 3; 8 sequenced
modules — matching the doctor's network picture.

---

## 5. MiHealth pre-flight checklist (run before calling `/report`)
- [ ] A lab report was uploaded → `labs[]` is **non-empty** (don't call with 0 labs if a report exists).
- [ ] `symptoms` includes **all** complaints, not just the first one.
- [ ] Reference ranges captured where the report shows them.
- [ ] `medications` + `conditions` populated (powers safety flags).
- [ ] PII stripped: `case_id` + `age_band` + `sex` only — no name/DOB/phone/email/ID.
- [ ] Consent flags present (`ai_analysis` at minimum).

## 6. Safety net on the TSPI side (recommended add-on)
We can add a **low-information guard** to `/report`: if `labs` is empty (or only the chief complaint
is present), TSPI returns a visible warning in the response (e.g. `"input_warning": "0 labs
received — report is symptom-only and likely incomplete"`) and audits it — so a near-empty call is
obvious instead of silently yielding a 1-axis report. *(Say the word and I'll wire this in.)*

## 7. Reference
- Full live schema: TSPI `/docs` (OpenAPI) when running.
- API/governance details: `TSPI_MiHealth_API_Contract.md`.
- Root-cause analysis of the thin report: `TSPI_Report_Comparison_Diagnosis.md`.
