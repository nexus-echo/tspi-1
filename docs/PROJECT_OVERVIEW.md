# TSPI AI Platform — Project Overview (understand & explain)

## 1. What it is (one line)
A **registry-driven, deterministic clinical-AI engine** that turns a patient's de-identified symptoms
and lab reports into a **network-based treatment plan** — reasoning over a fixed biological ontology,
with the LLM used only to explain (never to decide), gated by physician approval.

## 2. The problem it solves
Conventional AI health tools reason *disease → drug* and hallucinate. TSPI reasons
**evidence → biological state → plan → disease interpretation**. The organising idea is
*"treat the network, not the disease"*: one patient is a **multi-system network disorder**, so the
system maps them onto a stable framework instead of a single diagnosis.

The framework (fixed ontology):
**3 Keys → 9 Restoration Steps → 12 Domains → 39 Biological Axes → 180 Living Networks → ~200 Modules.**
The **39 axes** are the central assessment + module-matching layer; networks *explain* the axes.

## 3. Architecture (three deployables + two clients)
- **ai-engine** (FastAPI) — the deterministic "brain": the whole reasoning pipeline + the PII boundary.
- **tspi-mcp** (FastMCP) — lets a clinician drive the engine from an **AI chat client** (Claude/ChatGPT)
  over MCP; OAuth-protected when public.
- **mihealth** (separate repo: React + FastAPI) — the patient/clinic **portal** that consumes the engine.

Both clients speak the same **de-identified REST contract** to the engine. The engine is the single
source of clinical truth; everything else is a client of it.

## 4. The request lifecycle (what happens to one case)
1. **Intake + de-identify** — PII is stripped and stored **encrypted** (Fernet), keyed by a de-identified
   `case_id`. The pipeline and LLM never see PII.
2. **Red-flag safety screen** — deterministic; runs first; can only escalate care.
3. **Normalise + extract** — lab values classified against a **cut-off registry**; uploaded PDFs/images
   read by a **local vision model** (PHI-safe).
4. **Map 39 axes** — deterministic marker/symptom → axis mapping, a named **phenotype** layer
   (symptom → phenotype → axis), and a **vector-RAG** fallback for unknown labs (marked HYPOTHESIS,
   never scores).
5. **NSS (severity)** — Network Severity Score v0.3: a weighted mean where **data completeness never
   reduces severity** (severe stays severe; reliability reported separately).
6. **Module match** — ranks phytochemical modules against axes; **safety is a hard gate** (contraindicated
   modules are excluded, not low-scored); "matching is not prescribing".
7. **Compose report** — deterministic structure; optional LLM narrative that receives **placeholders
   only** (a guard fails closed if any identifier reaches the prompt).
8. **Physician review + approve** — nothing is deliverable until a clinician validates it.
9. **Re-identify + render** — PII re-attached only in the final rendered report (**bilingual en/th**,
   physician + patient variants); never streamed into a chat transcript.

## 5. Governance (the non-negotiables, all enforced in code + tests)
- **Deterministic**: the LLM never invents an axis score, network, module, or outcome.
- **PII → the LLM never sees it**; PHI stored encrypted; re-identification only at render, never over chat.
- **Missing data → NOT_ASSESSED**, never 0 and never a default of 50; a hypothesis never scores.
- **Safety is a categorical gate**, not a number. **Learning is propose-only** (a clinician approves).
- **Physician approval** before any patient release; every clinical claim is traceable + audited.
- **RBAC + tenant isolation** (patient / clinic-staff / clinician / reviewer / auditor).
- **PILOT_MODE**: provisional/candidate data is usable but every report is watermarked and gated.

## 6. Tech stack
Python · FastAPI · Pydantic v2 · SQLAlchemy 2 + Alembic · PostgreSQL + **pgvector** (vector RAG) ·
FastMCP (MCP server) with **OAuth (JWT / WorkOS AuthKit)** · local **Ollama** (embeddings, vision OCR,
private LLM) · **Fernet** encryption · Docker · Coolify · Supabase · Tailscale · ~100 automated tests.

## 7. RAG design (brief)
**Vector RAG (pgvector cosine similarity), not hybrid.** The knowledge catalog (axis definitions,
products) is embedded into a `kb_embeddings` table. At request time it adds two things only: a semantic
**fallback** to suggest an axis for an unknown lab (as a non-scoring HYPOTHESIS), and **grounding
snippets** for the report narrative. It is additive and fail-safe — the pipeline is fully deterministic
without it, and it's off in the default SQLite dev setup.

## 8. Engineering highlights (what's notable)
- Worked from **ambiguous, conflicting domain-expert PDFs** to a frozen, versioned ontology; encoded a
  legacy→current axis **converter** that auto-applies safe mappings and quarantines risky ones.
- A **de-identification boundary** that lets the engine own PII while guaranteeing the LLM only sees
  placeholders — verified by a fail-closed prompt guard.
- Clean **service boundaries**: split the portal into its own repo behind a versioned REST contract;
  two-layer auth (OAuth for users, service-token + RBAC for services).
- A **candidate-data pilot mode** that ships an end-to-end shadow pilot without over-claiming clinical
  authority — every provisional output is watermarked and physician-gated.
