# TSPI AI Platform

**TSPI (The Standardized Network Phytochemicals Intelligence Platform)** is the deterministic,
registry-driven AI diagnostic **"brain"**. It turns a patient's **de-identified** symptoms + lab/imaging
reports into a **TSPI Case Report**, mapping the data onto the framework
**3 Keys → 9 Restoration Steps → 12 Domains → 39 Biological Axes → 180 Living Networks → Modules**.
Principle: *treat the network, not the disease.* The AI only summarises/translates — it never invents an
axis score, network, module, or outcome.

> **MiHealth** (the patient/doctor/admin portal) now lives in its **own repo** and consumes this engine
> over HTTP as a de-identified service. See `docs/01-plans/TSPI_MiHealth_Repo_Split_Plan.md`.

## Repository layout
```
tspi_new/
├── docker-compose.yml       AI stack: TSPI engine + Postgres/pgvector
├── apps/
│   ├── ai-engine/           TSPI FastAPI engine (the brain)
│   ├── tspi-mcp/            MCP server — drive the engine from an AI chat client (Claude/ChatGPT)
│   └── RUN_LOCAL.md         Local-run guide
├── docs/                    Specs, plans, expert verifications — start with PROJECT_STATUS.md
└── knowledge-sources/       Raw inputs the engine's knowledge was built from
```

## Two clients of one engine
The engine is the single source of clinical conclusions. Everything talks to it over the same
de-identified REST contract (`/report`, `/extract`, `/screen`, …):
- **MiHealth backend** (separate repo) — the PII-owning portal: de-identifies, calls the engine, re-attaches identity.
- **tspi-mcp** (this repo) — lets a clinician run the workflow from their AI chat client.

## Run the engine (Docker)
```bash
cp apps/ai-engine/.env.example apps/ai-engine/.env   # add DEEPSEEK_API_KEY etc.
docker compose up -d --build
docker compose exec tspi-api python -m scripts.embed_knowledge   # once (build vectors)
```
| Service     | URL                          |
|-------------|------------------------------|
| TSPI engine | http://localhost:8002/docs   |

Run the engine directly (no Docker): `cd apps/ai-engine && uvicorn app.main:app --port 8000`
(see its `README.md` / `DEPLOY.md`). Connect the chat client: see `apps/tspi-mcp/README.md`.

### Smart lab/imaging extraction (local, PHI-safe)
Uploaded reports are read by the engine's `POST /extract` using **local Ollama models** (vision for
images/scanned PDFs, text for text PDFs), so patient files never leave your server.
See `docs/02-reference/Lab_Extraction_DeepSeek_vs_Ollama.md`.

## Status & tests
Current state, what's built, and what's blocked are tracked in **`docs/PROJECT_STATUS.md`** (the one
doc to read first). Test suites:
```bash
cd apps/ai-engine && pip install -r requirements.txt && pytest    # engine (82 tests)
cd apps/tspi-mcp  && pip install -r requirements.txt && pytest    # MCP de-identification gate
```

## Governance (must preserve)
- **De-identified** to the engine/LLM: `case_id` + age band + sex only — never name/DOB/phone/email/ID.
- TSPI is **decision-support**; the physician has final authority; nothing reaches a patient until approved.
- **Missing data → NOT_ASSESSED**, never 0 and never a default of 50; a hypothesis never scores.
- Every cited module resolves to the official registry or is **flagged**; learning is **propose-only**.
- Access control (auth + roles + audit) ships **off by default**, enabled per environment
  (see `docs/01-plans/TSPI_Phase_B_Auth_RBAC_Audit_Plan.md`).
