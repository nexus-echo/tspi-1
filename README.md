# TSPI Platform — Monorepo

**TSPI (The Standardized Network Phytochemicals Intelligence Platform)** is the AI diagnostic
"brain" that turns a patient's (de-identified) symptoms + lab/imaging reports into a **TSPI Case
Report**, by mapping data onto the framework: **3 Keys → 9 Steps → 12 Systems → 39 Axes → 180
Living Networks → Modules**. Principle: *treat the network, not the disease*.

**MiHealth** is the patient/doctor/admin portal that consumes the TSPI brain as a service.

## Repository layout
```
tspi_new/
├── docker-compose.yml          Unified stack: TSPI brain + MiHealth (db/api/web) + Ollama
├── apps/
│   ├── ai-engine/              TSPI FastAPI brain            (was: tspi_ai_brain)
│   ├── mihealth-backend/       MiHealth API (FastAPI)        (was: mihealth_portal/backend)
│   ├── mihealth-frontend/      MiHealth web (React/Vite)     (was: mihealth_portal/frontend)
│   ├── mihealth-compose.yml    Portal-only compose (reference)
│   └── RUN_LOCAL.md            Portal local-run guide
├── docs/                       17 TSPI_*.md specs + architecture/ + samples/
└── knowledge-sources/          Raw inputs the engine/knowledge were built from
    ├── 39-axes/  products/  keys-domains/  200-modules/
    ├── new_revised_docs/       Official master files
    ├── mihealth-design/        Portal design docs + business/privacy strategy
    ├── api-demo/               Sample API request(s)
    ├── patient-samples/        De-identified patient case + lab PDFs + vrishali_report_request.json
    └── stakeholder-chat.txt    Requirements thread
```

## Run everything (Docker)
```bash
cp apps/ai-engine/.env.docker.example apps/ai-engine/.env   # add DEEPSEEK_API_KEY etc.
docker compose up -d --build
docker compose exec ollama ollama pull bge-m3               # once (embeddings)
docker compose exec tspi-api python -m scripts.embed_knowledge   # once (build vectors)
```
| Service        | URL                     |
|----------------|-------------------------|
| TSPI brain     | http://localhost:8000/docs |
| MiHealth API   | http://localhost:8001   |
| MiHealth web   | http://localhost:5173   |

### Smart lab/imaging extraction (local, PHI-safe)
Uploaded reports are read by the engine's `POST /extract` using **local Ollama models** — a
vision model for images/scanned PDFs, a text model for text PDFs — so patient files never leave
your server. Pull the vision model once: `docker compose exec ollama ollama pull qwen2.5vl`.
See `docs/Lab_Extraction_DeepSeek_vs_Ollama.md` for why local (not DeepSeek) does the reading.

Run just the brain: `cd apps/ai-engine && docker compose up -d --build` (see its README/DEPLOY.md).

## Engine status — all 5 phases DONE
- **Phase 0** knowledge foundation (3 keys, 9 steps, 13 domains, 39 axes, 119 sub-axes, 153 products).
- **Phase 1** deterministic pipeline (normalize → axes → root-cause graph → step → modules → sequence → report). *Clinical scoring rules still provisional, pending ratification.*
- **Phase 2** embeddings + RAG (3 backends: hash/ollama/api; pgvector), additive & feature-flagged.
- **Phase 3** safety flags, doctor validation gate, consent + append-only audit; nothing reaches a patient until `deliverable=true`.
- **Phase 4** outcome learning loop + temporal trajectory (weight-aware NSS/SPS).

17/17 smoke tests pass: `cd apps/ai-engine && pip install -r requirements.txt && pytest`.

## Governance (must preserve)
- **De-identified** to the LLM: `case_id` + age band + sex only — never name/DOB/phone/email/ID.
- TSPI is **decision-support**; the physician has final authority.
- Every cited module resolves to the product catalog or is **flagged**; outputs carry a clinician-review disclaimer.

> Provenance: consolidated from the prior working tree (`tspi_ai_brain/`, `mihealth_portal/`, and the
> TSPI_*.md docs). Generated caches, `node_modules/`, `.venv/` and dev `*.db` were intentionally excluded
> (regenerate from requirements/package manifests + Alembic migrations).
