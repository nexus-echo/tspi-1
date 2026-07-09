# MiHealth ↔ TSPI — API Contract & Governance Flow (Phase 3)

*How the MiHealth front end talks to the `tspi_ai_brain` back end. TSPI is internal — only
MiHealth (and the validating clinician) call it. All payloads are **de-identified** (case_id +
age band + sex only); every action is **consent-gated and audited**; a report is only deliverable
to the patient **after a doctor validates it**.*

---

## Governance flow (the rule the contract enforces)
```
MiHealth (consent captured)
   │  POST /report  (de-identified inputs + consent flags)
   ▼
TSPI brain: analyze → NSS/SPS/Level → dosed modules → SAFETY flags → compose
   │  persists report (status=draft, deliverable=false) + audit
   ▼
Doctor reviews in MiHealth → POST /validate (approve/edit/reject)
   │  status=validated, deliverable=true + audit
   ▼
MiHealth delivers report to patient   (only if deliverable=true)
   │  later: POST /outcome (follow-up markers) + audit → learning loop
```
**Non-negotiables:** no PII in any payload; `ai_analysis` consent required before processing;
nothing reaches the patient until `deliverable=true`; TSPI is decision-support — the physician
holds final authority.

---

## Endpoints

### `POST /report` — generate a de-identified TSPI Case Report
**Request (MiHealth → TSPI):**
```json
{
  "case_id": "TSPI-2026-000123",
  "age_band": "mid-40s",
  "sex": "female",
  "symptoms": "fibroid, hypertension, inflammation, stress",
  "labs": [{"analyte": "CRP", "value": 21.57, "unit": "mg/L", "ref_high": 5.0}],
  "imaging": ["pelvic ultrasound: 4cm intramural fibroid"],
  "medications": ["amlodipine"],
  "conditions": ["hypertension"],
  "lifestyle": {"diet": "vegetarian", "sleep": "poor"},
  "consent": {"ai_analysis": true, "doctor_sharing": true}
}
```
**Response:** a `CaseReport` — key fields:
```json
{
  "case_id": "TSPI-2026-000123",
  "report_id": "e088de1c...",
  "status": "draft",
  "deliverable": false,
  "analysis": { "nss": 93, "severity_level": 3, "severity_name": "...",
                "axis_scores": [...], "system_priority": [...], "root_cause_chain": [...] },
  "modules": [{"module_code": "KS", "phase": "step_1", "dose": "...", "resolved": true}],
  "monitoring": [{"reassess_every_days": [14, 30]}],
  "safety_alerts": [{"module": "Kerra", "reason": "...", "severity": "review"}],
  "report_markdown": "# TSPI Case Report — ...",
  "disclaimer": "For clinician review and approval — not a substitute for medical judgment."
}
```
`403` if `ai_analysis` consent is not granted (logged as `consent_denied`).

### `GET /reports/{report_id}` — fetch a stored report + its deliverable state
Returns `{id, case_id, status, nss, severity_level, payload, safety_alerts, deliverable}` or `404`.

### `POST /validate` — doctor validation (the gate to patient delivery)
```json
{ "report_id": "e088de1c...", "doctor_id": "dr.lee", "decision": "approve", "edits": null }
```
`decision` ∈ `approve | edit | reject`. Response: `{report_id, status, deliverable}`.
`approve`/`edit` → `validated` (deliverable); `reject` → `rejected`. `404` if unknown id.

### `POST /outcome` — follow-up markers (learning loop)
```json
{ "report_id": "e088de1c...", "marker": "CRP", "baseline": 21.57, "followup": 6.0 }
```
Response: `{report_id, marker, delta}`. Stored for outcome learning (Phase 4).

### `POST /analyze` — structured analysis only (no prose) · `GET /health`, `/knowledge/health`
`/analyze` returns the machine-readable `AnalysisResult` (axes + NSS/SPS) without the narrative.

---

## Consent scopes (granular, each independently required where relevant)
| Scope | Gates |
|---|---|
| `ai_analysis` | `/analyze`, `/report` (required) |
| `doctor_sharing` | sharing the validated report with a clinician |
| `tspi_connection` | connecting to TSPI intervention programs / Samutthan Clinic |
| `research` | use of de-identified outcomes for model learning |
Denied scopes return `403` and write a `consent_denied` audit row.

---

## Audit trail
Every call writes an append-only `audit_log` row: `action` (analyze/report/validate/outcome/
consent_denied), `case_id`, `report_id`, `actor` (`mihealth` | doctor_id | `system`), `allowed`,
`detail`, `created_at`. No PII is stored.

---

## Safety
`safety_alerts` flag possible contraindications (vs the patient's `medications`/`conditions`).
Modules are **flagged for clinician review, never auto-removed**. The official contraindication
dataset is pending; the current rules are a seed (`data/safety_rules.json`).

---

## Integration notes for MiHealth
1. **De-identify before calling** — strip name/DOB/phone/email/IDs; send `case_id` + age band + sex.
2. **Pass consent flags** every call; handle `403` by prompting the user for consent.
3. **Do not show the report to the patient until `deliverable=true`** (post-validation).
4. **Async friendly** — `/report` can be called as a background job; poll `GET /reports/{id}`.
5. Full live schema is at TSPI's **`/docs`** (OpenAPI) when the service is running.
