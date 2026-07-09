# MiHealth Portal — Prototype (Phases A–F · complete)

The patient/doctor/admin front end on top of the de-identified `tspi_ai_brain`. A MiHealth
FastAPI service + Postgres holds all PII; a React app provides role-based UI.

```
React SPA (:5173) ──▶ MiHealth API (:8001, Postgres) ──▶ TSPI brain (:8000, run separately)
   roles & UI            PII • auth • patients • consent      de-identified engine
```

## What works
**Phase A — auth & roles**
- Patient self-registration + login (JWT access/refresh, auto-refresh interceptor).
- Admin (seeded on first boot) creates doctor/admin accounts; lists users.
- Role-guarded routing; each role lands on its own dashboard.

**Phase B — patients, consent, intake**
- Patient profiles with **PII encrypted at rest** (Fernet); `case_id` (`TSPI-YYYY-NNNNNN`) and a
  coarse **age band** are derived server-side — only those (never DOB/PII) ever go to TSPI.
- Symptoms & history intake; granular **consent center** (`ai_analysis`, `doctor_sharing`,
  `tspi_connection`, `research`).
- **Role-scoped access:** patients see only their own record; doctors see only assigned patients;
  admins see all and **assign doctors manually**.
- Append-only **audit log** for patient/consent/intake actions.

**Phase C — documents, OCR & labs**
- Upload a health report (PDF / image / text). A background job extracts text (PDF text layer or
  Tesseract OCR) and **auto-parses candidate lab values** (analyte, value, unit, reference range).
  Structuring is local-first (heuristic parser always; optional local Ollama LLM via `OCR_USE_LLM`).
- Every document lands in **review** — staff edit/confirm the extracted labs (or add labs manually);
  only **confirmed** labs become eligible to feed plan generation. Patients may upload but not confirm.
- Raw files stay in MiHealth (local disk / mounted volume); only confirmed, de-identified labs go to TSPI.

**Phase D — treatment-plan generation (TSPI integration)**
- Staff-only **Generate plan**: MiHealth builds a **de-identified payload** (case id + age band +
  sex + confirmed labs + intake — provably no PII, enforced by a guard) and calls the brain's
  `POST /report`. The returned analysis is stored as a **draft** (`deliverable=false`).
- The plan view renders **NSS gauge, severity level/name, root-cause drivers, dosed & sequenced
  modules, and safety alerts** (flagged, never auto-removed), plus the full report markdown.
  Staff (and the patient, for approved plans) can **Download PDF** of the plan (print-to-PDF,
  no extra dependencies).
- **Full payload** per the MiHealth→TSPI input contract: confirmed labs (analyte/value/unit/ref),
  ALL symptoms, imaging findings, medications, conditions, lifestyle. A **pre-flight readiness**
  check shows exactly what will be sent and **blocks generation** if a lab report was uploaded
  but its labs aren't confirmed (prevents the symptom-only, 1-axis report).
- Consent-gated (`ai_analysis` required → 409 if missing) and role-gated (patients can't generate).
  Patients **cannot see a draft** — only approved (deliverable) plans, which arrive in Phase E.

**Phase E — doctor validation (the delivery gate)**
- The patient's **assigned doctor** reviews a draft and **Approves**, **Suggests changes**, or
  **Rejects** it → MiHealth mirrors the decision to TSPI `POST /validate`.
- Locked semantics: approve/edit → `validated` + **deliverable** (a *Suggest changes* edit delivers
  the doctor's edited markdown); reject → `rejected`, **not** delivered. Decisions are recorded in a
  `validations` table and audited.
- Gated: only the **assigned doctor** can validate (patient/admin/other-doctor → 403). Once
  deliverable, the **patient sees the approved plan** on their dashboard.

**Phase F — outcomes & learning loop**
- Staff record follow-up markers (baseline vs follow-up) on a validated plan; MiHealth stores them
  with a computed delta and **mirrors them to TSPI `POST /outcome`** (best-effort, with a synced flag).
- A per-marker **temporal trajectory** (`GET /patients/{id}/temporal`) is built locally so trends
  show even when the brain is offline.
- **Admins** trigger `POST /learning/recalibrate` and inspect axis weights — doctor-approved
  outcomes thus feed the brain's future NSS/SPS scoring (digital-twin loop). Role-gated + audited.

## Run with Docker
Run the TSPI brain on the host at `http://localhost:8000`, then:
```bash
cd mihealth_portal
docker compose up --build
```
Web http://localhost:5173 · API http://localhost:8001/docs · admin `admin@mihealth.app` / `admin12345`

## Run without Docker (dev)
Backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cp .env.example .env && uvicorn app.main:app --reload --port 8001`
(Python 3.11–3.13 recommended. Optional extras: `requirements-ocr.txt` for image OCR, `requirements-postgres.txt` for Postgres. See `RUN_LOCAL.md`.)
Frontend: `cd frontend && npm install && npm run dev`

## Smoke test
1. Register a patient → set up profile (see your `case_id` + age band) → grant `ai_analysis` consent → save symptoms.
2. Sign in as `admin@mihealth.app` → Patients → register/open a patient → assign a doctor.
3. Upload a lab report (a .txt with lines like `CRP 21.57 mg/L (ref < 5.0)` works offline) → as
   admin/doctor open the patient → **Review & confirm labs** → confirmed labs appear for the patient.
4. With the TSPI brain running on :8000 and `ai_analysis` consent granted, open the patient as
   staff → **Generate plan** → review NSS / severity / modules / safety alerts (stored as a draft).
5. Sign in as the **assigned doctor** → open the patient → **Approve / Suggest changes / Reject**.
6. Sign back in as the patient → the **approved plan** now appears under *My treatment plan*.
7. As staff, record follow-up outcomes on the validated plan; as **admin**, click **Recalibrate now** (Learning loop).

## Structure
```
backend/app/  config, database, models (User/Patient/Intake/Consent/Document/LabResult/...),
              encryption (Fernet PII), util (case_id/age_band), ocr, storage, security (JWT),
              deid (PII guard), tspi (brain client), audit,
              routers/{auth,users,patients(+imaging),documents,reports(+readiness),learning}
frontend/src/ api/{client,patients,documents,reports,outcomes}, auth/{AuthContext,RequireRole},
              components/{PatientForm,ConsentCenter,IntakeForm,DocumentUpload,LabReview,ConfirmedLabs,ImagingPanel,PlanView,ReportsPanel,ValidationPanel,OutcomesPanel,LearningPanel}, lib/printReport, pages/*
docker-compose.yml   db + api + web
```

## Security notes (prototype)
Change `JWT_SECRET`, `PII_ENCRYPTION_KEY`, and the seeded admin password before any real use.
TSPI never receives PII — MiHealth sends only `case_id` + age band + sex, enforced by the
de-identification boundary: a guard in `deid.py` rejects any payload that isn't case_id +
age band + sex + clinical facts, and a test asserts no PII keys can appear.
