# TSPI AI Brain (`tspi_ai_brain`) — Build Plan (Revised)

*Revised with the official master files in `new_revised_docs/` (the 39-Axis/12-Domain/3-Keys
master, the **TSPI-AI Clinical Decision Engine v3.0**, and the owner's `question_answers.txt`).
This is the back-end "brain" behind **MiHealth**; it turns a patient's symptoms + health reports
into a de-identified **TSPI Case Report**.*

> **What changed in this revision:** official product/architecture names; the **NSS / SPS /
> severity-level / dosing** engine is now specified *and implemented*; the official **12-domain**
> structure replaces the earlier draft; data files are loaded; roadmap updated to reflect what is
> already built vs pending the official module registry.

---

## 0. What TSPI is (names locked)

- **TSPI** = **The Standardized Network Phytochemicals Intelligence Platform** — an **AI Diagnostic
  Intelligence Platform** (the "brain").
- **MiHealth** = the patient/doctor/admin **front end** (the "face"): data capture, health
  timeline, AI advisor, doctor sharing. Users never touch TSPI directly; it runs behind MiHealth
  and only with explicit consent.
- **Core principle:** *Treat the Network, Not the Disease.* Intervention intensity follows
  **biological network severity**, not the disease label. Goal = restore/preserve **Prakati**
  (biological homeostasis).

**Official architecture (memorize):**
`3 Keys → 9 Steps → 12 Systems(Domains) → 39 Axes → 180 Living Biological Networks → Modules`

**Master authority order** (owner's rule — higher wins on any conflict):
1) Official Product Registry → 2) Official Module Registry → 3) Official 39-Axis Framework →
4) Official Module-to-Axis Mapping → 5) Official Dosing Protocol. *Any conflicting file = legacy.*

---

## 1. What the brain does (the official decision flow)

From the Clinical Decision Engine v3.0:

```
Collect data → Evaluate 12 Systems → Evaluate 39 Axes → Compute NSS → Compute SPS →
Determine Severity Level → Select Modules → Apply Severity-Based Dosing → Apply KS Protocol →
Generate Personalized Intervention Plan → Reassess every 14–30 days
```

Input: symptoms + **any** lab/imaging/omics + meds + lifestyle (already OCR'd/parsed by MiHealth).
Output: a de-identified TSPI Case Report (axis map → root cause → NSS/level → SPS → dosed,
sequenced module plan → monitoring) + the machine-readable analysis behind it.

### The two scores that drive everything
- **NSS — Network Severity Score (0–100):** overall biological-network dysfunction, **driven by
  inflammatory activity** (NF-κB, IL-6, TNF-α, COX-2, NLRP3, ROS).

  | NSS | Level | State |
  |---|---|---|
  | 0–15 | 0 | Preventive Longevity & Network Optimization |
  | 16–30 | 1 | Functional Imbalance |
  | 31–60 | 2 | Systemic Dysfunction |
  | 61–100 | 3 | Advanced Network Failure |

- **SPS — System Priority Score:** ranks dysfunction across the **12 Systems** → drives module
  selection, priority, sequencing, and intensity.

### Severity-based dosing (all assigned modules)
| Level | Dose | Daily total |
|---|---|---|
| 0 | 2 caps × 2/day (AM+PM) | 4 |
| 1 | 2 caps × 3/day | 6 |
| 2 | 3 caps × 3/day | 9 |
| 3 | 3 caps × 5/day | 15 |

**KS (special):** dosed by **bowel performance**, not level (goal ≥2 comfortable BMs/day; start
2 caps before bed, titrate +2 every 3–7 days, practical max 12/day).
**Safety:** TSPI-AI is a **Clinical Decision Support System** — it recommends modules/dose ranges/
priorities; the **physician** holds final prescribing authority.

---

## 2. Framework: FastAPI (decided)

`tspi_ai_brain` is built in **FastAPI** (confirmed). It is I/O-bound AI orchestration (LLM, vector,
DB calls), needs typed/validated structured output (Pydantic), high concurrency, streaming, and
auto OpenAPI docs for MiHealth integration. A small **Django** companion remains *optional* later
for EMR/admin/master-data + the doctor-validation UI, sharing one Postgres.

---

## 3. The official biological framework (loaded)

### 3 Keys
A = **Metabolic Energy** (Pitta) · B = **Biological Dynamics** (Vata) · C = **Biointegrity** (Kapha).

### 9 Steps of Wellness (the therapeutic ladder)
1 Detoxification → 2 Microbiome Restoration → 3 Immune Regulation → 4 Redox Balance →
5 Metabolic & Mitochondrial Recovery → 6 Autophagy & Cellular Clearance →
7 Genomic Stability & Proteostasis → 8 Genomic Regulation → 9 **PRAKATI**.

### 12 Systems / Domains (OFFICIAL master — axes 1–36)
D1 Immune–Infection (A1–A4) · D2 Metabolic–Energy (A5–A10) · D3 Genomic Programming (A11–A14) ·
D4 Detoxification (A15) · D5 Digestive–Gut Ecosystem (A16–A19) · D6 Vascular–Circulation (A20–A23) ·
D7 Repair–Regeneration (A24–A27) · D8 Musculoskeletal (A28–A30) · D9 Endocrine (A31–A33) ·
D10 Neurological (A34) · D11 Organ Axis (A35) · D12 Oncology (A36).
**Axes 37 (Proteostasis), 38 (Protein Clearance), 39 (CELA)** are listed after D12 — provisionally
grouped "Proteostasis & Cellular Integrity (meta)" **pending owner confirmation**.

### 39 Axes
All 39 axis names + 119 sub-axes are extracted and stored (see §6). Names are authoritative from
the `.md` files; domain grouping follows the official master above.

---

## 4. Internal architecture of `tspi_ai_brain`

```
                ┌─────────────────────────────────────────────────────────┐
  MiHealth ───▶ │  FastAPI app (tspi_ai_brain)                            │
 (parsed data) │  /analyze  /report  /validate  /outcome  /knowledge      │
               │      │                                                    │
               │      ▼   Pipeline orchestrator (async)                   │
               │   1 Normalizer       → biological signals (any lab)      │
               │   2 Axis Mapper      → 39-axis scores (4-level)          │
               │   3 Graph Engine     → root-cause chain (NetworkX+PageRank)│
               │   3b Severity        → NSS (0-100) + SPS (12 systems)    │
               │   4 Step Locator     → 9-steps + Prakati gap             │
               │   5 Module Matcher   → axis→module (+ safety filter)     │
               │   6 Sequencer        → foundation→manifestation phases   │
               │   6b Dosing          → severity-based dose + KS protocol │
               │   7 Report Composer  → LLM prose from grounded facts     │
               └──────┬───────────────┬───────────────┬──────────────────┘
                      ▼               ▼               ▼
               PostgreSQL        Vector DB        LLM layer
            (knowledge+EMR)   (pgvector/Chroma)  (Ollama local +
                                                  Claude/DeepSeek cloud)
```

### API surface (implemented)
| Endpoint | Purpose |
|---|---|
| `POST /analyze` | inputs → axis scores + **NSS/level + SPS** + root-cause (structured, no prose) |
| `POST /report` | full de-identified TSPI Case Report (JSON + Markdown) with **dosed** module plan |
| `POST /validate` | doctor approve/edit/reject *(stub — persistence TODO)* |
| `POST /outcome` | outcome markers for the learning loop *(stub — recalibration TODO)* |
| `GET /knowledge/health`, `/health` | status checks |

---

## 5. Tech stack
FastAPI + Uvicorn (ASGI) · Pydantic v2 · PostgreSQL 15 + **pgvector** (one DB for facts + vectors;
or ChromaDB) · NetworkX (axis graph + PageRank) · sentence-embeddings (local or API) · LLM via
Ollama (`qwen2.5:14b`) + Claude/DeepSeek/Groq fallback behind one provider module · task queue
(RQ/Celery/Arq) for embedding sync + longitudinal jobs · Docker · pytest golden-case tests.

---

## 6. How knowledge is stored (plain-English + data files)

- **PostgreSQL = the exact catalog.** Keys, Steps, Systems, Axes (+ sub-axes), Products, Modules,
  and the **axis↔module map**. Exact lookups + safety rules.
- **Vector DB (pgvector/Chroma) = the "meaning" search.** Embeddings of axis/module/product text
  for fuzzy retrieval (RAG) when input is messy; each vector points back to a relational id.
- **LLM = the writer.** Composes the report from exact facts + retrieved context; doesn't store
  knowledge. Keeps output grounded and auditable.
- **Patient data + reports** = separate, consent-gated tables.

**Data already produced (ready to load):**
- `data/tspi_axes_39.json` — 39 axes, names, primary domain, **119 sub-axes** (from the `.md` files).
- `data/tspi_framework.json` — official 12 domains, 3 Keys, 9 Steps, architecture, decisions.
- `data/tspi_severity_dosing.json` — NSS bands, Level 0–3 dosing, KS protocol, reassessment days.

Relational sketch (unchanged core + dosing): `keys, steps, domains, axes, sub_axes, products,
modules, module_products, axis_module_map(relevance), patients(uuid,age_band,sex,consent),
intake, lab_results, axis_scores, reports, outcomes`. **No PII as a key** (UUID + phone/email).

---

## 7. Current build status (what's real today)

**Implemented & tested (5/5 tests pass; runs end-to-end with seed knowledge):**
- FastAPI app + all endpoints; Pydantic contracts for every stage.
- 7-stage pipeline wired (`normalizer → axis_mapper → graph_engine → severity → step_locator →
  module_matcher → sequencer → report_composer`).
- **Official decision engine: NSS, severity Level 0–3, SPS over 12 systems, severity-based dosing,
  KS bowel protocol, 14–30 day reassessment.**
- Governance: consent gate (403 without consent), de-identification, unresolved-module flagging,
  "for clinician review" disclaimer.
- Live example: NSS 97 → Level 3; modules dosed 3×5/day; KS on its own protocol.

**Still placeholder / TODO (clearly marked in code):**
- Knowledge is an **in-memory seed** (~14 axes, ~9 modules), not the full catalog.
- Axis severity scoring + the **NSS formula** are documented **heuristics** (official formula not
  yet published — isolated in `severity.py` for a clean swap).
- Axis→module map is seed; LLM + vector RAG not wired; validation/outcome endpoints don't persist.

---

## 8. Roadmap (revised)

**Phase 0 — Knowledge foundation (in progress).**
- ✅ Official axes/domains/keys/steps + severity/dosing extracted to `data/*.json`.
- ⏭ Load these into PostgreSQL; replace the seed repository (same interface).
- ✅ **Module-registry rules decided (domain experts):** **1 module = 1 product** (no bundles),
  keyed by **H-Code**, mapped to the **39 axes** (each module's own list). See
  `TSPI_Module_Registry_Questions_For_Experts.md` + `TSPI_Phase0_Answers_Resolution.md §F`.
- ⏳ **Remaining blocked item = data only:** the updated **master registry file** (final active
  counts, ~200 modules, plus ~11 cleanup rows). We can build the loader + merged draft map now and
  re-ingest cleanly when it lands — no code changes (data-driven). Maintenance plan:
  `TSPI_Master_File_Update_Plan.md`.

**Phase 1 — Deterministic core (mostly done).**
- ✅ Pipeline + NSS/SPS/level/dosing live.
- ⏭ Replace heuristic axis-scoring + NSS with the clinically-reviewed rules/formula; load the
  curated axis-dependency graph.

**Phase 2 — RAG + report composer.**
- pgvector + embeddings; wire RAG into the axis mapper and the LLM report writer (Pydantic-schema'd).

**Phase 3 — Safety, validation, MiHealth integration.**
- Real contraindication rules; persist `/validate` + audit log; consent/audit layer; the MiHealth
  API contract; route every report through doctor validation (Samutthan Clinic).

**Phase 4 — Learning loop + digital twin.**
- Persist outcomes; recalibrate axis weights / NSS; longitudinal analysis; future omics + wearable
  (CGM/HRV) inputs continuously update NSS/SPS (digital-twin ready).

---

## 9. Open items to unblock full accuracy
1. **Official module registry + module→axis map** (the #1 blocker for real output).
2. **Axes 37–39 domain placement** (provisional "Proteostasis & Cellular Integrity (meta)").
3. **Q6 product IDs:** canonical ID for "ZAMINZYME" (191?) and "Blood Nourishing" (40/51/61/6/H-016?).
4. **Official NSS formula + per-axis severity thresholds** (to replace the documented heuristics).
5. **Domain → 3-Keys mapping** (still null).

> Net: the engine's *logic and structure are now official and built*; remaining work is loading the
> official **content** (modules + exact scoring) as the master files land.
