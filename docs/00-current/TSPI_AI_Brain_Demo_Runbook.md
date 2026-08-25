# TSPI AI Brain — Demo Runbook

*End-to-end demo: bring up the AI brain, then walk a patient from input → final treatment plan.
All commands assume the `ai-engine` service on `http://localhost:8000`.*

---

## Part 1 — Bring up the stack (pre-flight checklist)

The AI brain needs three things running: **FastAPI app**, **PostgreSQL (pgvector)**, and **Ollama**
(only if you want live LLM prose + real embeddings; the engine runs fully without it too).

### Option A — Docker (recommended for the demo)
From the repo root (`C:\workspace\tspi_new`):

```bash
# 1. one-time: put your secrets in place
cp apps/ai-engine/.env.example apps/ai-engine/.env    # add DEEPSEEK_API_KEY etc. (optional)

# 2. build + start db + ollama + api together
docker compose up -d --build

# 3. (once) pull the local models used by Ollama
docker compose exec ollama ollama pull qwen2.5vl        # vision, for /extract
docker compose exec ollama ollama pull bge-m3           # embeddings (optional)

# 4. (once) build the vector index so RAG/network search works
docker compose exec tspi-api python -m scripts.embed_knowledge
```

### Pre-flight: confirm each service is UP

```bash
# (a) FastAPI app is alive
curl -s http://localhost:8000/health
# expect: {"status":"ok", ...}

# (b) Postgres (pgvector) is healthy
docker compose exec tspi-db pg_isready -U tspi -d tspi
# expect: "... accepting connections"

# (c) Ollama is up and has the models
docker compose exec ollama ollama list
# expect: qwen2.5vl (and bge-m3) listed

# (d) knowledge base loaded + governance flags
curl -s http://localhost:8000/knowledge/health
# expect deidentification_enforced=true, doctor_validation_required=true

# (e) interactive API explorer (great for a live demo)
open http://localhost:8000/docs
```

### Option B — Local (no Docker), for a laptop demo
```bash
cd apps/ai-engine
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m scripts.seed_db          # load axes/domains/keys + registry into the DB
python -m alembic upgrade head     # apply schema migrations (0001..0003)
uvicorn app.main:app --reload --port 8000
# Postgres optional locally: without DATABASE_URL it uses a zero-config SQLite dev DB.
# Ollama optional: without it, the report uses the deterministic prose fallback.
```

**What runs on startup (entrypoint):** waits for DB → `seed_db` (idempotent) →
`alembic upgrade head` → (optional) `embed_knowledge` → `uvicorn` on port 8000.

---

## Part 2 — The demo flow (input → treatment plan)

The clinical path is a single sequence of API calls. Use one `case_id` throughout (de-identified —
**no patient name/DOB ever goes to the engine**).

### Step 0 — (optional) Read a report/scan into structured labs — `POST /extract`
Turns an uploaded lab PDF / photo into candidate labs locally (Ollama vision). Skip if you type labs.

```bash
curl -s -X POST http://localhost:8000/extract \
  -F "file=@/path/to/lab_report.pdf" \
  -F "doc_type=lab"
```

### Step 1 — Safety first: Red-Flag screening — `POST /screen`
Runs BEFORE any reasoning. Demo two patients to show the gate.

```bash
# 1a. a SAFE patient -> no red flags, plan allowed
curl -s -X POST http://localhost:8000/screen \
  -H 'Content-Type: application/json' \
  -d '{
    "case_id": "DEMO-001",
    "age_band": "mid-40s",
    "sex": "female",
    "symptoms": "fibroid, body inflammation, fatigue, stress, bloating after meals",
    "labs": [{"analyte":"CRP","value":21.57,"unit":"mg/L","ref_high":5.0}],
    "consent": {"ai_analysis": true}
  }'
# expect: red_flags=[], module_plan_allowed=true

# 1b. an EMERGENCY patient -> plan blocked
curl -s -X POST http://localhost:8000/screen \
  -H 'Content-Type: application/json' \
  -d '{"case_id":"DEMO-ER","symptoms":"sudden slurred speech and limb weakness","consent":{"ai_analysis":true}}'
# expect: action_class=CLASS_1_EMERGENCY, release_block=true, module_plan_allowed=false
```

### Step 2 — Biological analysis (39 axes, NSS, phenotype) — `POST /analyze`
The heart of the engine: symptoms + labs → assessed axes with the 4 evidence dimensions, NSS, SPS,
red-flag screen, and clinical phenotype.

```bash
curl -s -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "case_id": "DEMO-001",
    "age_band": "mid-40s",
    "sex": "female",
    "symptoms": "fibroid, hypertension, body inflammation, fatigue, stress, bloating after meals, early satiety",
    "labs": [
      {"analyte":"CRP","value":21.57,"unit":"mg/L","ref_high":5.0},
      {"analyte":"HbA1c","value":6.5,"unit":"%","ref_high":5.6},
      {"analyte":"Hemoglobin","value":10.8,"unit":"g/dL","ref_low":12.0},
      {"analyte":"TSH","value":0.416,"unit":"uIU/mL","ref_low":0.54}
    ],
    "medications": ["antihypertensive"],
    "conditions": [],
    "consent": {"ai_analysis": true}
  }'
```
**Point out in the demo:** each `axis_scores[]` has `evidence_status`, `confidence`,
`data_completeness`, `biological_uncertainty`, `status`; `not_assessed[]` lists the axes with no
data (never shown as "normal"); `nss_detail` shows the explainable NSS v0.1; `phenotype` shows the
symptom clusters + differential.

### Step 3 — Full treatment plan — `POST /report`
Same body as `/analyze`. Produces the de-identified draft plan: selected modules (with dosing),
`considered_modules[]` with reasons, safety alerts, and the version stamps.

```bash
curl -s -X POST http://localhost:8000/report \
  -H 'Content-Type: application/json' \
  -d '{
    "case_id": "DEMO-001",
    "age_band": "mid-40s",
    "sex": "female",
    "symptoms": "fibroid, hypertension, body inflammation, fatigue, stress, bloating after meals, early satiety",
    "labs": [
      {"analyte":"CRP","value":21.57,"unit":"mg/L","ref_high":5.0},
      {"analyte":"HbA1c","value":6.5,"unit":"%","ref_high":5.6},
      {"analyte":"Hemoglobin","value":10.8,"unit":"g/dL","ref_low":12.0},
      {"analyte":"TSH","value":0.416,"unit":"uIU/mL","ref_low":0.54}
    ],
    "medications": ["antihypertensive"],
    "consent": {"ai_analysis": true}
  }'
```
**Point out:** `modules[]` capped at ~6 (core + supporting) each with `module_match_score`,
`dose`, `dose_type`; `module_selection.counts` shows *matched vs selected* ("matching ≠
prescribing"); `deliverable=false` + `status=draft` — nothing reaches a patient until a doctor
approves. **Save the `report_id` from the response for the next steps.**

### Step 4 — Fetch the stored report — `GET /reports/{report_id}`
```bash
curl -s http://localhost:8000/reports/REPORT_ID_FROM_STEP_3
```

### Step 5 — Doctor validation gate — `POST /validate`
This is what makes the plan deliverable to the patient.

```bash
curl -s -X POST http://localhost:8000/validate \
  -H 'Content-Type: application/json' \
  -d '{
    "report_id": "REPORT_ID_FROM_STEP_3",
    "doctor_id": "dr.samutthan",
    "decision": "approve",
    "edits": null
  }'
# expect: status=validated, deliverable=true
```

### Step 6 — Follow-up outcome (closing the loop) — `POST /outcome`
```bash
curl -s -X POST http://localhost:8000/outcome \
  -H 'Content-Type: application/json' \
  -d '{"report_id":"REPORT_ID_FROM_STEP_3","marker":"CRP","baseline":21.57,"followup":6.0}'
# expect: delta=-15.57 (improving)
```

### Step 7 — Learning loop (patient-specific, bounded, propose-only) — optional
```bash
# patient-specific axis adaptation (bounded +-5%/cycle)
curl -s -X POST http://localhost:8000/learning/adapt/DEMO-001

# network behaviour learning
curl -s -X POST http://localhost:8000/learning/networks/DEMO-001

# versioned patient biological model (history never deleted)
curl -s http://localhost:8000/patient-model/DEMO-001

# population learning is PROPOSE-ONLY (never auto-changes the global model)
curl -s -X POST http://localhost:8000/learning/recalibrate
curl -s http://localhost:8000/learning/proposals
# a clinician must approve before it applies:
curl -s -X POST "http://localhost:8000/learning/proposals/1/decide?reviewer=dr.samutthan&approve=true"

# temporal trajectory of a marker
curl -s http://localhost:8000/temporal/DEMO-001
```

### Suggested 5-minute demo narrative
1. `/health` + `/knowledge/health` — "the brain is up and de-identification is enforced."
2. `/screen` on the emergency case — "safety runs first and can block everything."
3. `/analyze` on DEMO-001 — "39 axes, each with confidence + uncertainty; unknown stays unknown."
4. `/report` — "a realistic 6-module plan, every rejected module has a reason, draft until a doctor signs."
5. `/validate` — "doctor approves → deliverable." → `/outcome` + `/learning/adapt` — "it learns, safely."

---

## Part 3 — What we've built vs what's pending

### ✅ Done and tested (54/54 tests passing)
- **Framework frozen on the official master** — 39 Axes v2.0 (A35–A39 corrected, A10 sub-axes),
  12 Domains, 3 Keys, Domain→Key map. Everything version-stamped.
- **Phase 0–4 engine:** de-identified pipeline (normalize → axes → root-cause → step → modules →
  dose → report), DB catalog, RAG scaffolding, persistence, consent + append-only audit,
  doctor-validation gate.
- **Local lab/imaging extraction** (`/extract`) — Ollama vision reads PDFs/scans on-prem; PHI never leaves.
- **Phase 6 — Evidence model:** every conclusion carries Evidence Status + Grade, Confidence,
  Data Completeness (weighted), Biological Uncertainty; HYPOTHESIS never scores; **no data is ever
  "normal"** (explicit `NOT_ASSESSED`); no default-50.
- **Phase 7 — Red-Flag screening:** deterministic, runs first; 3 action classes; critical-value
  layer survives a low NSS; unit-aware.
- **Phase 8 — Clinical Phenotype Engine:** symptoms are first-class evidence — a symptoms-only
  patient is now assessable; probabilistic differential (never 1 symptom = 1 axis); clusters;
  negative-test interpretation; adaptive questions.
- **Phase 10 — NSS v0.1 + Module Match v1.0:** confidence-weighted NSS with NetworkFactor
  (explainable); safety as a hard **gate**; **module ceiling ~6** (fixed the 64-module output);
  `reason_not_selected` on every unselected module; mechanism de-dup.
- **Phase 12 — Learning rework (compliance fix):** 3 levels — patient-specific (bounded), network
  behaviour, versioned patient model; population learning is **propose-only** (was non-compliant
  auto-update).
- **Ops:** Docker Compose (FastAPI + pgvector + Ollama), Alembic migrations 0001–0003,
  `build_registry` + `validate_master`, deterministic scoring (the LLM never invents a score/module).

### 🟡 Provisional (seeded from the experts' own examples — needs clinical ratification)
- Red-Flag list, Symptom→Axis dictionary, negative-test rules, NSS coefficients — all labelled
  `authoritative: false`; swap in the official versions when supplied.
- Module→axis map is **quarantined** (`production_allowed: false`) — see blockers.

### 🔴 Blocked / pending (need client data or decisions)
- **Blocker 1 — Module Registry:** the module file still uses **legacy axis numbering**; module→axis
  recommendations are quarantined until a registry with current A1–A39 codes arrives. (~19 axis
  numbers need expert sign-off; comparison sheet already prepared.)
- **Blocker 2 — 180 Networks:** CSV now **verified by client** (`networks_180.csv`); Phase 9 (load +
  crosswalk + embeddings + `network_match`) is planned but not yet built. Network *propagation* still
  needs upstream/downstream edges (not in the CSV).
- **5 open questions** (Ferritin axis, exact NSS formula, phenotype-layer definition, contraindication
  storage, direction rules) — the 17-Jul response answered a different document; still unresolved.
- **Not yet built:** Phase 9 network layer, Phase 11 registry remap, Phase 13 report presentation
  (bilingual, Network Harmonization sections), the report **PII toggle**, and the **knowledge CRUD
  API + auto-embeddings** (all three planned in `TSPI_Implementation_Plan_Networks_PII_CRUD.md`).
- **Master data still awaited:** Marker Registry, lab cut-off table, evidence grades per module,
  module→network links, network→axis crosswalk confirmation.

---

## Quick reference — all endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | app alive |
| GET | `/knowledge/health` | KB loaded + governance flags |
| POST | `/extract` | read a lab/scan file → candidate labs (local vision) |
| POST | `/screen` | red-flag safety screen (runs first) |
| POST | `/analyze` | 39-axis analysis + NSS + phenotype |
| POST | `/report` | full de-identified treatment plan (draft) |
| GET | `/reports/{id}` | fetch a stored report |
| POST | `/validate` | doctor approve/edit/reject → deliverable |
| POST | `/outcome` | record a follow-up marker |
| POST | `/learning/adapt/{case_id}` | patient-specific learning (bounded) |
| POST | `/learning/networks/{case_id}` | network-behaviour learning |
| GET | `/patient-model/{case_id}` | versioned patient biological model |
| POST | `/patient-model/{case_id}/rebuild` | new model version |
| POST | `/learning/recalibrate` | population learning → proposals only |
| GET | `/learning/proposals` | pending model-update proposals |
| POST | `/learning/proposals/{id}/decide` | clinician approves/rejects a proposal |
| GET | `/learning/weights` | current global axis weights |
| GET | `/temporal/{case_id}` | marker trajectory over time |
```
Base URL: http://localhost:8000   ·   Interactive docs: http://localhost:8000/docs
```
