# TSPI AI Brain — MCP Server (Phase A)

A thin **governance + adapter** layer that lets a clinician drive the TSPI AI Brain from an AI
chat client (Claude Desktop / Claude.ai / ChatGPT) via the Model Context Protocol.

**It contains no clinical logic.** It is an HTTP client of the existing FastAPI engine, exactly
like MiHealth or any other REST client. The engine stays standalone and unchanged; MiHealth and
other clients are unaffected.

```
Doctor ─chat─► AI client ─MCP─► THIS server ─REST─► TSPI FastAPI engine (unchanged)
                                    │
                                    ├─ de-identification gate (PII never forwarded)
                                    ├─ draft / physician-approval framing
                                    └─ actionable errors
```

## Phase A tools (existing endpoints only — zero engine changes)

| Tool | Engine endpoint | Purpose |
|---|---|---|
| `tspi_engine_health` | `GET /health`, `/knowledge/health` | Is the engine up? registry/governance status |
| `tspi_screen_red_flags` | `POST /screen` | Safety screening — run first |
| `tspi_analyze_case` | `POST /analyze` | 39-axis analysis + NSS (no plan) |
| `tspi_generate_treatment_plan` | `POST /report` | Full draft plan (deliverable=false) |
| `tspi_get_treatment_plan` | `GET /reports/{id}` | Re-fetch a plan |
| `tspi_approve_treatment_plan` | `POST /validate` | Physician approve / edit / reject |
| `tspi_update_treatment_plan` | `POST /reports/{id}/override` | Structured physician edits (remove/reject module, change dose, override safety, add/remove secondary axis, note) — non-destructive; resets plan to draft for re-approval |
| `tspi_record_outcome` | `POST /outcome` | Follow-up marker for propose-only learning |

Later phases add `tspi_extract_lab_report` (`/extract`), remote transport + OAuth, and RBAC.

## Run locally (Claude Desktop)

1. Start the engine (from `apps/ai-engine`): `uvicorn app.main:app --port 8000`.
2. Install deps here: `pip install -r requirements.txt`.
3. Copy the `tspi-ai-brain` block from `claude_desktop_config.example.json` into your Claude
   Desktop config and restart Claude Desktop.
4. In chat: *"Screen case CASE-0912 for red flags: female, 40s, CRP 21.5 mg/L, bloating."*

No public IP is required for this local/stdio setup — everything runs on the machine.

## Configuration (env)

| Var | Default | Meaning |
|---|---|---|
| `TSPI_ENGINE_URL` | `http://localhost:8000` | Where the engine is |
| `TSPI_ENGINE_TOKEN` | *(none)* | Bearer token to the engine (Phase B auth) |
| `TSPI_CLINICIAN_ID` | `unknown-clinician` | Recorded on approvals + audit |
| `TSPI_STRICT_DEIDENT` | `true` | Strict = reject on any detected PII; else redact + warn |
| `TSPI_MCP_TRANSPORT` | `stdio` | `stdio` (local) or `streamable-http` (remote) |

## Governance invariants

- **PII never leaves this layer.** Tool schemas have no identity fields; the de-id gate drops
  unknown fields, rejects identity fields, and scrubs identifiers from free text.
- **Physician-approval gate.** Plans are AI drafts, watermarked, `deliverable=false` until approved.
- **Deterministic authority.** The engine computes everything; the chat only presents it.
- **Fail-closed.** Module output is provisional until the Module Registry is approved.

## Test

```
pip install -r requirements.txt pytest
python -m pytest tests -q
```
