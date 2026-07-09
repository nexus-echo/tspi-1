# MiHealth Portal — Design & Implementation Plan (Prototype)

*The patient/doctor/admin front end ("the face") that sits on top of the de-identified
`tspi_ai_brain` engine ("the brain"). This document is the design and build plan for a working
prototype: a **React** SPA + a **MiHealth FastAPI service** + **PostgreSQL**, integrating with the
existing TSPI brain already running on `http://localhost:8000`.*

Status of inputs this plan is built on: TSPI brain is built through Phase 4 and exposes
`/report`, `/analyze`, `/reports/{id}`, `/validate`, `/outcome`, `/learning/recalibrate`,
`/temporal/{case_id}`, `/health`, `/knowledge/health`. It accepts **de-identified** input only
(`case_id` + `age_band` + `sex`), is **consent-gated** (403 without `ai_analysis`), and gates
patient delivery behind a doctor's `/validate` (`deliverable=true`).

---

## 1. Decisions locked for this prototype

These were confirmed before planning and shape everything below:

1. **Backend tier** — Reuse the existing `tspi_ai_brain` (FastAPI + Postgres) running on
   `localhost:8000` as the diagnostic engine. MiHealth gets its **own** FastAPI service +
   PostgreSQL database that holds all PII and calls TSPI over HTTP. This keeps the brain
   de-identified, which is a non-negotiable of the existing system.
2. **Report intake** — Upload a PDF/image, **auto OCR/parse** into structured labs, then a human
   confirms/edits the extracted values before they are sent to TSPI.
3. **Roles** — Three roles: **admin**, **doctor**, **patient**. Patients can self-register, capture
   symptoms, and upload reports. **Treatment-plan generation is staff-only** (admin/doctor).
   Doctors review, approve, or request changes. Patients see a plan only after approval.
4. **Deliverable now** — This plan document. Implementation follows on approval.

---

## 2. Why MiHealth is a separate tier (the de-identification boundary)

The single most important architectural rule: **PII never reaches TSPI.** TSPI only ever sees
`case_id` + age band + sex + clinical facts. Therefore MiHealth must be the system of record for
identity, and it must translate between "Priya Sharma, DOB 12-03-1981, phone …" and
`case_id = TSPI-2026-000123` on every call.

```
  ┌──────────────┐      HTTPS/JWT       ┌────────────────────────┐   de-identified HTTP   ┌──────────────────┐
  │  React SPA   │ ───────────────────▶ │  MiHealth API (FastAPI)│ ─────────────────────▶ │  TSPI brain      │
  │ (admin/doc/  │ ◀─────────────────── │  :8001  +  Postgres    │ ◀───────────────────── │  :8000 (existing)│
  │  patient)    │                      │  (ALL PII lives here)  │   case_id+age+sex only │  de-identified DB │
  └──────────────┘                      └────────────────────────┘                        └──────────────────┘
        UI/UX                            identity • consent • files                         axes • NSS/SPS
                                          OCR • case-id mapping                              modules • dosing
                                          report metadata • audit                            validation • learning
```

What lives where:

| Concern | MiHealth (Postgres, :8001) | TSPI brain (:8000) |
|---|---|---|
| Patient identity / PII | ✅ owns it | ❌ never sees it |
| Login, roles, sessions | ✅ | ❌ |
| Uploaded files + OCR | ✅ stores files + extracted labs | ❌ (receives parsed labs only) |
| Consent capture & display | ✅ source of truth | ✅ enforces via flags on each call |
| case_id ↔ patient mapping | ✅ | ❌ (only knows case_id) |
| Axis scores / NSS / SPS / modules / dosing | mirror for display | ✅ computes |
| Report status / deliverable | mirror + drives UI | ✅ authoritative (`/validate`) |
| Learning loop | triggers via API | ✅ recalibrates weights |

This boundary means a leak or breach of the brain exposes no identities, and MiHealth can be
audited independently. It also matches the existing API contract (`TSPI_MiHealth_API_Contract.md`)
exactly, so no changes to the brain are required for the prototype.

---

## 3. Roles & permissions

| Capability | Patient | Admin | Doctor |
|---|---|---|---|
| Self-register / login | ✅ | ✅ (admin-provisioned) | ✅ (admin-provisioned) |
| Create/edit own patient profile | ✅ (self) | ✅ (any) | view |
| Capture symptoms / intake | ✅ (self) | ✅ (any) | view |
| Upload health report (file) | ✅ (self) | ✅ (any) | view |
| Review/correct OCR-extracted labs | view | ✅ | ✅ |
| Capture/modify consent | ✅ (own) | ✅ (assist) | view |
| **Generate treatment plan (call TSPI `/report`)** | ❌ | ✅ | ✅ |
| View draft (unapproved) plan | ❌ | ✅ | ✅ |
| **Approve / request-changes / reject plan** | ❌ | ❌ | ✅ |
| Record outcome markers / trigger learning | ❌ | ✅ | ✅ |
| View **approved** treatment plan | ✅ (own) | ✅ | ✅ |
| Manage users / assignments | ❌ | ✅ | ❌ |

Two rules worth calling out: only **doctors** can flip a plan to deliverable (mirrors TSPI's
`/validate` being the delivery gate), and the patient UI **never** shows a plan whose
`deliverable=false`.

---

## 4. Data model (MiHealth PostgreSQL)

All identity and workflow state. UUID primary keys; PII isolated to `patients`. Timestamps and
soft-delete (`deleted_at`) on all tables. SQLAlchemy + Alembic migrations.

```
users            id, email(unique), password_hash, role(admin|doctor|patient),
                 full_name, is_active, last_login_at, created_at
                 -- a patient user links to exactly one patients row; staff users do not

patients         id(uuid), case_id(unique, e.g. "TSPI-2026-000123"),
                 owner_user_id(fk users, nullable for staff-created),
                 first_name, last_name, dob, sex(female|male|other|unknown),
                 phone, email, address,                        -- PII (encrypted at rest)
                 age_band(derived from dob, e.g. "mid-40s"),   -- the only age sent to TSPI
                 assigned_doctor_id(fk users), created_at

intake           id, patient_id(fk), symptoms_text, conditions(jsonb[]),
                 medications(jsonb[]), lifestyle(jsonb), captured_by(fk users), created_at

documents        id, patient_id(fk), file_path/blob_key, original_filename,
                 mime_type, size_bytes, doc_type(lab|imaging|other),
                 ocr_status(pending|done|failed|review), uploaded_by(fk users), created_at

lab_results      id, document_id(fk, nullable), patient_id(fk),
                 analyte, value, unit, ref_low, ref_high, flag,
                 source(ocr|manual), confirmed(bool), confirmed_by(fk), created_at

imaging_findings id, document_id(fk), patient_id(fk), text, confirmed(bool)

consents         id, patient_id(fk), scope(ai_analysis|doctor_sharing|
                 tspi_connection|research), granted(bool),
                 captured_by(fk users), captured_at
                 -- one current row per (patient, scope); history retained

reports          id(uuid), patient_id(fk), case_id,
                 tspi_report_id(from brain), status(draft|validated|rejected|changes_requested),
                 deliverable(bool), nss, severity_level, severity_name,
                 analysis(jsonb), modules(jsonb), monitoring(jsonb),
                 safety_alerts(jsonb), report_markdown(text),
                 generated_by(fk users), created_at, updated_at

validations      id, report_id(fk), doctor_id(fk users), decision(approve|edit|reject),
                 edits(jsonb), note, created_at         -- mirrors what we POST to /validate

outcomes         id, report_id(fk), marker, baseline, followup, delta,
                 recorded_by(fk users), created_at

audit_log        id, action, actor_user_id, patient_id, report_id,
                 allowed(bool), detail(jsonb), ip, created_at  -- append-only
```

Notes:
- **`patients.case_id`** is generated by MiHealth at creation (`TSPI-{year}-{seq}`) and is the only
  patient key TSPI ever receives.
- **PII columns** (`first_name`, `last_name`, `dob`, `phone`, `email`, `address`) are encrypted at
  rest (pgcrypto or app-level envelope encryption). `age_band` is derived and stored separately so
  the de-id payload builder never touches raw DOB.
- MiHealth keeps its **own audit_log** in addition to the brain's, so identity-linked actions are
  traceable on the MiHealth side and de-identified actions on the TSPI side.

---

## 5. MiHealth API (FastAPI, `:8001`)

Thin auth + persistence layer in front of TSPI. JWT bearer auth, role dependencies, Pydantic
schemas. Endpoints grouped by concern:

**Auth & users**
- `POST /auth/register` — patient self-registration (role forced to `patient`).
- `POST /auth/login` → JWT (access + refresh). `POST /auth/refresh`, `POST /auth/logout`.
- `GET /me` — current user + (if patient) linked patient profile.
- `POST /admin/users` — admin creates doctor/admin accounts. `GET /admin/users`.

**Patients & intake**
- `POST /patients` — create patient (auto-assign `case_id`, derive `age_band`). Patient role can
  only create/edit self; staff can create anyone.
- `GET /patients`, `GET /patients/{id}` — list/detail (role-scoped: patient sees only self).
- `PUT /patients/{id}` — update profile.
- `POST /patients/{id}/intake` — symptoms, conditions, meds, lifestyle.
- `POST /patients/{id}/consent` — set/update a consent scope.

**Documents & OCR**
- `POST /patients/{id}/documents` — multipart upload; stores file; enqueues OCR job; returns
  `document_id`, `ocr_status=pending`.
- `GET /documents/{id}` — file metadata + OCR status + extracted candidates.
- `POST /documents/{id}/labs/confirm` — staff confirms/edits the OCR-extracted `lab_results`
  (sets `confirmed=true`). This is the gate before a report can be generated.

**Treatment plan (staff-only — these are the TSPI calls)**
- `POST /patients/{id}/reports` *(admin/doctor)* — builds the **de-identified** payload from
  confirmed labs + intake + consent, calls TSPI `POST /report`, stores the returned report
  (`status=draft`, `deliverable=false`), returns it. **403 mapping:** if TSPI returns 403
  (missing `ai_analysis` consent), MiHealth surfaces a "capture consent first" error.
- `GET /patients/{id}/reports`, `GET /reports/{id}` — list/detail (staff: any status; patient:
  only `deliverable=true`).
- `POST /reports/{id}/validate` *(doctor only)* — body `{decision: approve|edit|reject, edits, note}`.
  Calls TSPI `POST /validate`, updates local `reports.status`/`deliverable`, writes `validations`
  row. `approve`/`edit` → validated+deliverable; `reject`/`changes_requested` → not deliverable.
- `POST /reports/{id}/outcomes` *(staff)* — records a follow-up marker, calls TSPI `POST /outcome`.
- `POST /learning/recalibrate` *(admin)* — calls TSPI `/learning/recalibrate`.
- `GET /reports/{id}/temporal` — proxies TSPI `/temporal/{case_id}` for trend charts.

Every MiHealth endpoint writes a MiHealth `audit_log` row. Consent is enforced **twice**: MiHealth
checks its own `consents` table before calling TSPI (fast fail + clear UX), and TSPI re-enforces via
the `consent` flags in the payload (defense in depth).

### 5.1 De-identification payload builder (the critical function)

When generating a report, MiHealth assembles exactly the contract shape and nothing more:

```python
def build_tspi_payload(patient, intake, confirmed_labs, imaging, consents):
    return {
        "case_id":     patient.case_id,          # NOT the uuid, NOT the name
        "age_band":    patient.age_band,          # derived; never DOB
        "sex":         patient.sex,
        "symptoms":    intake.symptoms_text,
        "labs":        [ {analyte, value, unit, ref_low, ref_high, flag}
                          for l in confirmed_labs if l.confirmed ],
        "imaging":     [ f.text for f in imaging if f.confirmed ],
        "medications": intake.medications,
        "conditions":  intake.conditions,
        "lifestyle":   intake.lifestyle,
        "consent":     { scope: c.granted for scope, c in consents },
    }
```

A unit test asserts this dict's keys are a subset of the contract and that no PII field
(`first_name`, `dob`, `phone`, …) can appear — a guardrail against accidental leakage.

---

## 6. OCR / report-parsing pipeline

Upload → extract → human-confirm → ready-for-TSPI. Runs as a background job so uploads return fast.

```
1. Upload      multipart PDF/JPG/PNG → store file (local disk for prototype; S3/MinIO later)
2. Extract     PDF text layer (pdfplumber) OR image/scan → OCR (Tesseract)
3. Structure   LLM extraction (reuse the brain's llm/provider.py: Ollama local / cloud fallback)
               prompt → strict JSON: [{analyte, value, unit, ref_low, ref_high, flag}]
4. Persist     write candidate lab_results (source=ocr, confirmed=false), ocr_status=review
5. Review      staff opens the doc, sees extracted rows side-by-side with the source file,
               edits/confirms → confirmed=true
6. Ready       confirmed labs feed the de-id payload builder
```

Prototype simplifications: local filesystem storage, synchronous fallback if no job queue is wired
(small files), and a manual-entry path so a report can still be produced if OCR confidence is low.
Confidence/`ocr_status=review` always forces human confirmation — we never auto-send unconfirmed
labs to TSPI. Reuse the brain's `app/llm/provider.py` so there is one LLM configuration for the
whole system.

---

## 7. End-to-end workflows

### 7.1 Patient onboarding → plan delivery (the main flow)

```
Patient self-registers → completes profile (MiHealth derives case_id + age_band)
   → captures symptoms/intake → grants consent (ai_analysis required)
   → uploads lab report  ──OCR──▶  extracted labs (status: review)
Admin/Doctor reviews & confirms extracted labs
Admin/Doctor clicks "Generate Plan"
   → MiHealth de-identifies → POST /report (TSPI)
   → TSPI: analyze → NSS/SPS/Level → dosed modules → safety flags → compose
   → MiHealth stores report (draft, deliverable=false)
Doctor opens draft → reviews axes/NSS/modules/dosing/safety alerts
   → Approve            → POST /validate(approve) → validated, deliverable=true
   → Request changes    → POST /validate(edit, edits) → validated w/ edits  (or)
   → Reject             → POST /validate(reject) → rejected, NOT deliverable
Patient logs in → sees approved plan (only because deliverable=true)
Later: staff records outcome markers → POST /outcome → POST /learning/recalibrate
   → TSPI nudges axis weights → future NSS/SPS improve (digital-twin learning loop)
```

### 7.2 Doctor "request changes" semantics

The contract's `/validate` supports `approve | edit | reject`. We map the doctor's "suggest required
changes" to **`edit`** with an `edits` payload + free-text `note`. Per the contract, `edit` results
in `validated`/`deliverable=true` — **the doctor's edited version is the authoritative, deliverable
plan** (decision locked: changes do *not* bounce back to staff for regeneration). `reject` is the
only path that blocks delivery. The patient sees the doctor's edited plan, not the original draft.

### 7.3 The learning loop (doctor approval → brain learns)

"Once a doctor approves, that knowledge feeds AI brain learning." Concretely:
- Approval is captured in `validations` and via TSPI `/validate` (the approved/edited plan is the
  ratified ground truth).
- Real learning in the current brain is **outcome-driven**: `/outcome` markers → `/learning/recalibrate`
  adjusts per-axis weights (bounded 0.5–2.0) which change future NSS/SPS. So MiHealth surfaces an
  **Outcomes** screen (enter baseline vs follow-up labs) and a **Recalibrate** admin action.
- The approved plan itself is retained (status + edits) as the dataset for future supervised
  ratification of the NSS formula/module map (which the brain notes are pending clinical sign-off).

---

## 8. React frontend

**Stack:** React 18 + Vite + TypeScript, React Router, TanStack Query (server state) + a light
client store (Zustand) for auth/session, Tailwind + shadcn/ui for components, React Hook Form + Zod
for forms, Recharts for NSS/SPS/trend visuals, Axios with a JWT interceptor. `react-markdown`
renders the brain's `report_markdown`.

### 8.1 App structure

```
src/
  api/            axios client, typed endpoints, JWT refresh interceptor
  auth/           AuthProvider, useAuth, <RequireRole>, login/register pages
  components/     ui (shadcn), LabTable, ConsentToggles, NSSGauge, SeverityBadge,
                  ModulePlanCard, SafetyAlertList, ReportMarkdown, FileDropzone
  features/
    patients/     list, detail, profile form, intake form
    documents/    upload, OCR review (file viewer + editable lab table)
    reports/      generate, draft review, validation panel, approved view
    outcomes/     marker entry, temporal trend charts
    admin/        user management, learning/recalibrate
  routes.tsx      role-guarded routing
  layouts/        AdminLayout, DoctorLayout, PatientLayout
```

### 8.2 Screens by role

**Patient**
- Register / Login.
- My Profile (name, DOB, sex, contact) and Consent center (toggles per scope with plain-language
  explanations; `ai_analysis` flagged as required to receive a plan).
- Symptoms & history intake form.
- Upload reports (drag-drop) + see OCR status ("processing", "ready for clinician review").
- **My Treatment Plan** — visible only when an approved plan exists; renders the **full clinical
  detail**: NSS gauge + severity level/name, axis scores, the sequenced & dosed module plan,
  monitoring schedule, safety alerts, and the full report markdown (decision locked: patients see
  the complete plan). The "for clinician review" framing is replaced with the doctor-approved
  version (the edited plan if the doctor used "suggest changes").

**Admin**
- Dashboard (patients, pending OCR reviews, drafts awaiting doctor, recent activity).
- Patient registry: create/search patients, assign a doctor.
- OCR review workspace: source file alongside an editable extracted-labs table; confirm values.
- Generate Plan action; view drafts.
- User management (create doctors/admins); trigger learning recalibration.

**Doctor**
- Worklist: patients assigned + plans awaiting validation.
- Patient detail: profile (PII visible to clinician), intake, confirmed labs, imaging.
- **Plan review panel:** NSS gauge + severity badge, axis-score table (drivers highlighted),
  root-cause chain, SPS ranking, sequenced & dosed module plan, **safety alerts** prominently,
  and the full report markdown.
- Validation actions: **Approve**, **Suggest changes** (structured `edits` + note), **Reject**.
- Outcomes entry + temporal trend charts.

### 8.3 Key UI components mapped to brain data

- `NSSGauge` — 0–100 with band coloring (0–15/16–30/31–60/61–100) → Level 0–3.
- `SeverityBadge` — Level + name (e.g., "Level 3 — Advanced Network Failure").
- `ModulePlanCard` — module name/code, target axes, phase (step_1/2/3), **dose string**, clinical
  role; `resolved=false` modules visibly flagged ("not in catalog — clinician review").
- `SafetyAlertList` — contraindication flags vs meds/conditions; **never hidden**, never auto-removed
  (matches brain behavior).
- `AxisTable` — 39-axis severity, `is_driver` highlighted, evidence on expand.

---

## 9. Tech stack summary

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 18 + Vite + TS, Tailwind + shadcn/ui, TanStack Query, RHF+Zod, Recharts | Fast prototype, typed, good DX |
| MiHealth API | FastAPI + Pydantic v2, SQLAlchemy + Alembic, `httpx` async client to TSPI | Same stack/patterns as the brain |
| Auth | JWT (access+refresh), `passlib`/bcrypt, role dependencies | Standard, prototype-appropriate |
| DB | PostgreSQL 15 (separate `mihealth` DB) | PII isolation from TSPI DB |
| OCR | pdfplumber + Tesseract, LLM structuring via brain's `llm/provider.py` | Reuse existing LLM config |
| Files | Local disk (prototype) → S3/MinIO later | Keep prototype simple |
| Jobs | FastAPI BackgroundTasks (prototype) → RQ/Arq later | Async OCR without infra |
| TSPI brain | Existing FastAPI on `:8000` (unchanged) | Consume as-is per contract |
| Dev orchestration | docker-compose: postgres + tspi_brain + mihealth_api + web | One-command local run |

---

## 10. Implementation roadmap (phased)

**Phase A — Foundations (scaffold + auth)**
- docker-compose (Postgres + brain + MiHealth API + React). MiHealth FastAPI skeleton, SQLAlchemy
  models + Alembic initial migration. JWT auth, user roles, `/auth/*`, `/me`. React app shell,
  routing, auth pages, role-guarded layouts. *Exit: a patient can register/log in; an admin can
  create a doctor.*

**Phase B — Patient data capture**
- Patient CRUD with `case_id`/`age_band` derivation + PII encryption. Intake form + consent center
  (UI + persistence). *Exit: a complete, consented patient record exists.*

**Phase C — Documents + OCR**
- Upload endpoint + storage; OCR background job (pdfplumber/Tesseract + LLM structuring); OCR review
  workspace; confirm-labs gate. *Exit: confirmed structured labs attached to a patient.*

**Phase D — Plan generation (TSPI integration)**
- `httpx` client to TSPI; de-id payload builder + leakage guard test; `POST /report` wiring; store
  + render draft (NSS gauge, axis table, module plan, safety alerts, markdown). Map TSPI 403 →
  consent UX. *Exit: staff generate a real draft plan from a patient record.*

**Phase E — Doctor validation**
- Doctor worklist + review panel; Approve/Suggest-changes/Reject → `POST /validate`; status +
  deliverable sync; patient "My Plan" gated on `deliverable=true`. *Exit: full draft→approve→deliver
  flow works end to end.*

**Phase F — Learning loop + polish**
- Outcomes entry → `POST /outcome`; admin recalibrate → `/learning/recalibrate`; temporal trend
  charts via `/temporal`. Audit log views, dashboards, error/empty states. *Exit: outcomes feed the
  brain; trends visible.*

**Phase G — Verification & hardening**
- Seed/demo data + a scripted golden-path walkthrough (register→upload→generate→approve→deliver).
  Tests: payload leakage guard, role-permission matrix, consent gating, status transitions.
  Security pass (see §11).

A thin **vertical slice first** is recommended: one patient, one hardcoded confirmed lab set,
`POST /report`, draft render, doctor approve, patient view — proving the de-id boundary and the TSPI
round-trip before building breadth.

---

## 11. Security, privacy & compliance (prototype-level)

- **PII isolation** — only MiHealth DB holds identity; TSPI receives de-identified payloads only.
  Automated test prevents PII keys in the outbound payload.
- **Encryption** — PII columns encrypted at rest; TLS for all hops in any non-local deployment.
- **AuthZ** — every endpoint behind role dependencies; patients are hard-scoped to their own record.
- **Consent** — enforced in MiHealth before the call and re-enforced by TSPI; denials audited.
- **Audit** — append-only `audit_log` in MiHealth (identity-linked) complementing TSPI's de-identified log.
- **Delivery gate** — patient UI cannot fetch a non-deliverable report (enforced server-side, not just hidden in UI).
- **Disclaimer** — drafts always carry the "for clinician review" disclaimer; it is the doctor, not
  the AI, who authorizes a plan.
- *Out of scope for the prototype (flag for production):* full HIPAA/GDPR controls, BAA-backed
  storage, key management/HSM, pen-testing, rate limiting, MFA.

---

## 12. Open questions — all resolved ✅

1. ✅ **"Suggest changes" semantics (§7.2)** — Resolved: doctor's edited version delivers; no bounce
   back to staff. `reject` is the only delivery-blocking path.
2. ✅ **Patient visibility (§8.2)** — Resolved: patients see the full NSS / severity / module / dosing detail.
3. ✅ **Edit granularity** — Resolved: **free-text / markdown only**. "Suggest changes" sends
   `decision: "edit"` with the doctor's edited markdown/note in `edits`; structured module/dose
   fields remain as AI-generated. Simplest editing UI (a single rich-text/markdown editor); no
   editable module table needed.
4. ✅ **Doctor assignment** — Resolved: **admin assigns manually** (at registration or review).
5. ✅ **OCR LLM backend** — Resolved: **reuse the brain's `llm/provider.py`, local-first** (Ollama
   primary + fallback). Raw report text never leaves the local environment before parsing.
6. ✅ **Run target** — Resolved: the prototype runs **entirely on the local machine** via
   docker-compose (no cloud). Postgres + MiHealth API + React web are Composed; the brain is
   consumed at `localhost:8000`. Files on local disk; OCR via local-first Ollama.

---

*Once you confirm §12 (or accept the defaults), I'll proceed with Phase A scaffolding: docker-compose,
the MiHealth FastAPI service with auth + models, and the React app shell.*
