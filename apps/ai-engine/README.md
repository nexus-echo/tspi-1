# tspi_ai_brain

FastAPI engine for **TSPI — The Standardized Network Phytochemicals Intelligence Platform**.
It is the back-end "brain" behind **MiHealth**: it takes a patient's (already parsed) symptoms +
health reports and produces a **de-identified TSPI Case Report** by mapping the data onto the
**3 Keys / 9 Steps / 12 Domains / 39 Axes** model.

> Status: **scaffold (Phase 0/1)**. The pipeline runs end-to-end with in-memory *seed* knowledge
> and deterministic logic. Clinical scoring rules, the full module catalog, the vector store, and
> the LLM are stubbed/optional and marked with `TODO`.

## Run it
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# open http://localhost:8000/docs
```

Or Docker:
```bash
docker build -t tspi_ai_brain .
docker run -p 8000:8000 --env-file .env tspi_ai_brain
```

## Try it
```bash
curl -s http://localhost:8000/health

curl -s -X POST http://localhost:8000/report \
  -H 'Content-Type: application/json' \
  -d '{
        "case_id": "TSPI-EX-001",
        "age_band": "mid-40s",
        "sex": "female",
        "symptoms": "fibroid, hypertension, body inflammation, stress",
        "labs": [
          {"analyte": "CRP", "value": 21.57, "unit": "mg/L", "ref_high": 5.0},
          {"analyte": "HbA1c", "value": 6.5, "unit": "%", "ref_high": 5.6},
          {"analyte": "Hemoglobin", "value": 10.8, "unit": "g/dL", "ref_low": 12.0},
          {"analyte": "TSH", "value": 0.416, "unit": "uIU/mL", "ref_low": 0.54}
        ],
        "medications": ["antihypertensive"],
        "consent": {"ai_analysis": true}
      }'
```

## Layout
```
app/
  main.py            FastAPI app + /health
  config.py          settings (.env)
  schemas.py         Pydantic contracts (input -> signals -> axes -> modules -> report)
  api/routes.py      /analyze /report /validate /outcome /knowledge
  pipeline/          the 7 stages:
    normalizer.py      1 findings -> biological signals
    axis_mapper.py     2 signals -> 39-axis scores (rules now, RAG later)
    graph_engine.py    3 NetworkX root-cause chain (driver vs amplifier)
    step_locator.py    4 position on the 9 Steps + Prakati gap
    module_matcher.py  5 axis -> catalog modules (+ safety filter)
    sequencer.py       6 foundation-before-manifestation phasing
    report_composer.py 7 LLM writes prose from grounded facts (+ deterministic fallback)
    orchestrator.py    wires 1..7
  knowledge/         models.py (SQLAlchemy) + repository.py (seed; swap for DB)
  llm/               provider.py (Ollama primary + cloud fallbacks)
```

## Phase 0 — DONE (knowledge foundation)
- `scripts/build_product_registry.py` → dedups 276 product files → **153 canonical products**
  (`data/product_registry.json` + `data/product_dedup_report.json`).
- `scripts/seed_db.py` → loads the official **3 keys, 9 steps, 13 domains (12 + meta), 39 axes,
  119 sub-axes, 153 products** into the DB (`data/tspi.db` for dev; PostgreSQL via `DATABASE_URL`).
- `app/knowledge/db.py` + DB-backed `repository.py` → engine now reads the official catalog.
- Run it: `python -m scripts.build_product_registry <products_dir> data && python -m scripts.seed_db`

## Phase 2 — DONE (embeddings + RAG, additive & feature-flagged)
_Core complete & verified. Optional follow-ups: embed the module registry (waits on the official
module list), and an automated re-embed-on-change job._
- `app/knowledge/embeddings.py` — **three backends** behind one interface: `hash` (no deps, dev),
  `ollama` (local, private), and `api` (OpenAI-compatible, managed). `vectors.py` — `kb_embeddings`
  + cosine search (pgvector). Switch via `EMBEDDING_BACKEND` (+`EMBEDDING_DIM`) and re-run `embed_knowledge`.
- `scripts/embed_knowledge.py` — embeds axes + products into `kb_embeddings` (Postgres only).
- `app/knowledge/retrieval.py` — **async + cached** `aretrieve()` (non-blocking embed + threaded
  DB search + LRU query cache) for request time; sync `retrieve()` for scripts. Returns `[]` unless
  Postgres+pgvector+embeddings are present, so SQLite/dev behaves exactly as Phase 0/1.
- RAG wired **additively**: `axis_mapper` uses it only for labs the rules can't map; `report_composer`
  adds retrieved context to the LLM prompt. Both no-op without vectors.
- Run on Postgres: `python -m scripts.embed_knowledge && python -m scripts.verify_phase2`

## Phase 3 — DONE (safety, doctor validation, consent/audit, MiHealth contract)
- `app/store.py` + models (`Report`, `ReportValidation`, `OutcomeRow`, `AuditLog`) — reports are
  **persisted** (de-identified); `/report` returns `report_id`, `status=draft`, `deliverable=false`.
- `/validate` (doctor approve/edit/reject) flips status -> `validated`/`rejected` and sets
  `deliverable`; `GET /reports/{id}` fetches state; `/outcome` records follow-up markers.
- `app/safety.py` + `data/safety_rules.json` — contraindication **flags** vs meds/conditions
  (never silently drops a module). Seed rules; official data pending.
- **Consent-gated + audited**: every action writes an append-only `audit_log` row; denied consent
  returns 403 + audit. Nothing reaches the patient until `deliverable=true`.
- Contract documented in `TSPI_MiHealth_API_Contract.md`.

## Phase 4 — DONE (outcome learning loop + temporal analysis)
- `AxisWeight` table + weight-aware **NSS/SPS** (`severity.py`): per-axis weights default to 1.0
  (neutral) so behaviour is identical until learning runs.
- `app/learning.py` — `recalibrate()` reads **new** outcomes (incremental `learned` flag), decides
  improved/worsened per marker, and nudges the axis weight (worsening→more emphasis, improving→
  relax), bounded [0.5, 2.0]. `temporal()` returns a per-marker trajectory for a case.
- Endpoints: `POST /learning/recalibrate`, `GET /learning/weights`, `GET /temporal/{case_id}` (audited).
- **Digital-twin ready**: outcomes continuously refine axis weights -> future NSS/SPS.
- _Mechanism complete; the exact update rule + marker→axis map await clinical ratification (like the
  official NSS formula)._

## Next steps (see TSPI_AI_Brain_Build_Plan.md)
1. **Phase 0 follow-ups** — load the OFFICIAL module registry + module→axis map when delivered
   (currently provisional); confirm axes 37–39 domain.
2. **Phase 1** — replace seed heuristics with clinically-reviewed scoring + dependency graph.
3. **Phase 2** — pgvector + RAG + LLM report composer.
4. **Phase 3** — safety rules, doctor validation, MiHealth API contract, consent/audit.
5. **Phase 4** — outcome learning loop.

**Governance:** de-identified output (case_id + age band + sex only); every cited module must
resolve to the catalog or be flagged; outputs carry a "for clinician review" disclaimer.

## Lab/imaging extraction — `POST /extract` (local-only)
Reads ONE uploaded report (image / scanned PDF / text PDF) with **local Ollama** models and
returns candidate labs + imaging narrative (`confirmed=false` — human reviews before it feeds
diagnosis). Vision model for images/scans, text model for text PDFs, regex fallback if models
are offline. Nothing is sent to a cloud LLM. Config: `VISION_MODEL` (default `qwen2.5vl`),
`EXTRACTION_TEXT_MODEL`, `EXTRACTION_BACKEND`. Pull the model once:
`ollama pull qwen2.5vl`. Rationale: `docs/Lab_Extraction_DeepSeek_vs_Ollama.md`.
