# TSPI AI Brain — MCP Integration Plan (Doctor's chat ↔ AI Brain)

*Plan only — no code yet. Goal: let a clinician drive the TSPI AI Brain from inside their own AI chat
client (Claude Desktop / Claude.ai, or ChatGPT) via an **MCP server** that wraps the existing engine
APIs, while preserving every TSPI governance rule (de-identification, physician-approval gate,
registry-only authority, audit, fail-closed).*

---

## 1. What the doctor should be able to do

1. **Connect** the TSPI AI Brain to their AI chat once (add an MCP connector).
2. **Submit a case** — patient context (de-identified), symptoms, and lab reports — in natural language
   or by attaching a lab PDF.
3. **Generate a treatment plan** — the chat calls the engine and returns the structured plan (axes,
   networks, module recommendations, safety, NSS) as an **AI-generated draft**.
4. **Approve or update** the plan — the doctor edits (change/remove modules, adjust dose, override
   safety with justification) and approves; only then is it marked deliverable.

The chat is the **conversation and presentation layer only**. All clinical conclusions come from the
deterministic engine — the LLM must never invent an axis score, network, module, dose, or outcome.

---

## 2. Architecture

```
   Doctor  ──chat──►  AI Chat Client              ──MCP──►   TSPI MCP Server        ──HTTPS──►  TSPI AI Engine (FastAPI)
                     (Claude Desktop / Claude.ai /          (new; thin governance             (existing: /screen /analyze
                      ChatGPT — MCP connector)               + adapter layer)                   /report /validate /extract …)
                                                                   │
                                                                   ├─ Auth (per-doctor token / OAuth)
                                                                   ├─ De-identification gate (PII never forwarded)
                                                                   ├─ Case/session mapping (case_id ↔ local identity, kept OUTSIDE the engine)
                                                                   ├─ Release-state + approval enforcement
                                                                   └─ Audit log (who / when / case / action)
```

**Key point:** the MCP server is a **new, small governance + adapter layer**. It does not re-implement
any clinical logic — it exposes the engine's endpoints as well-described MCP tools and enforces the
boundaries the chat client cannot.

---

## 3. Governance & safety boundaries (non-negotiable)

These are the rules that make the integration safe; they shape every design choice below.

| Rule | How the MCP layer enforces it |
|---|---|
| **PII must never reach the engine or the LLM.** | Tools accept only `case_id` + `age_band` + `sex` + clinical data. The server **strips/【rejects】** name, DOB, MRN, phone, email, ID before any forward. Identity ↔ `case_id` mapping (if needed) lives in the doctor's MiHealth/local vault, never in the engine. *(See §6 — the doctor must also be guided to type de-identified input, because whatever they type is seen by the chat provider.)* |
| **Physician-approval gate.** | `generate_treatment_plan` always returns a **DRAFT** watermarked `AI-GENERATED CLINICAL DRAFT — PENDING PHYSICIAN REVIEW — NOT FOR PATIENT RELEASE`. `deliverable=false` until `approve_treatment_plan` is called by an authenticated clinician. |
| **Registry-only authority / deterministic.** | Tool outputs are the engine's structured results. Tool descriptions instruct the model to **relay, not invent**. The LLM may summarise/translate; it may not add axis scores, modules, doses, or evidence. |
| **Fail-closed.** | While the Module Registry is unapproved (Blocker 1), module output is returned as `PROVISIONAL CANDIDATE / NOT FOR CLINICAL USE`; patient-release states are blocked. Missing data → `NOT_ASSESSED`, never invented. |
| **Full audit.** | Every tool call logs clinician id, case_id, action, timestamp, engine version set, and (for approvals) the before/after and reason codes. |
| **Consent.** | `submit_patient_case` requires an explicit `consent.ai_analysis=true`; without it the engine already returns 403 and the tool surfaces that. |

---

## 4. MCP server — technology & transport

- **Language:** Python + **FastMCP** (matches the FastAPI engine; can even be mounted in the same app or
  run as a sidecar that calls the engine over HTTP). *(TypeScript SDK is the general MCP default, but
  Python keeps us in one stack and lets us reuse the engine's Pydantic schemas.)*
- **Transport:**
  - **Streamable HTTP (remote)** — required for **ChatGPT** and **Claude.ai** web connectors, and the
    recommended default (stateless JSON, easy to host and scale, per-doctor auth).
  - **stdio (local)** — for **Claude Desktop** running against a locally hosted engine (clinic on-prem).
- **Hosting:** one small service (container) alongside the engine, behind TLS. Same network as the
  engine so PII/clinical data never traverses the public internet beyond the chat provider's transport.

---

## 5. MCP tool catalog

Tools map onto existing engine endpoints (a few need new endpoints — flagged 🆕). Names use a `tspi_`
prefix for discoverability; each carries input/output Pydantic schemas and annotations.

| MCP tool | Wraps | Purpose | Annotations |
|---|---|---|---|
| `tspi_screen_red_flags` | `POST /screen` | Run safety / critical-value screening FIRST; returns emergency actions. | readOnly, non-destructive |
| `tspi_extract_lab_report` | `POST /extract` | Turn an attached lab PDF/image into structured, de-identified lab values (local vision model). | non-destructive |
| `tspi_submit_patient_case` | *(server-side)* | Validate + de-identify intake (age band, sex, symptoms, labs, meds, conditions, consent); returns a `case_id` handle. | non-destructive |
| `tspi_generate_treatment_plan` | `POST /report` | Produce the full draft: axis assessment, differential networks, module plan, safety, NSS, disclaimer. Returns `report_id`, `deliverable=false`. | non-destructive, **not** idempotent |
| `tspi_get_treatment_plan` | `GET /reports/{id}` | Re-fetch a plan by id (for review/continuation). | readOnly, idempotent |
| `tspi_update_treatment_plan` 🆕 | `POST /reports/{id}/override` (new) | Apply structured physician edits: change/remove module, adjust dose, add/remove secondary axis, override safety **with justification**. Records reason codes. | **destructive**, auditable |
| `tspi_approve_treatment_plan` | `POST /validate` | Physician approves/rejects; sets `deliverable=true` and the release state. Records signature. | **destructive**, auditable |
| `tspi_record_outcome` | `POST /outcome` | Log follow-up marker change for the propose-only learning loop. | non-destructive |
| `tspi_patient_timeline` | `GET /temporal/{case_id}` | Show the longitudinal biological model across runs. | readOnly |
| `tspi_engine_health` | `GET /health`, `/knowledge/health` | Report engine + registry status (and which blockers gate clinical use). | readOnly |

**Deliberately NOT exposed to the doctor's chat:** the learning-admin endpoints
(`/learning/recalibrate`, `/learning/proposals/*/decide`, `/patient-model/*/rebuild`) — these are
model-governance actions for the Clinical Review Board, not per-consultation tools. They stay on a
separate admin surface.

---

## 6. Case model & the de-identification gate (the hard part)

**The challenge:** anything the doctor types into ChatGPT/Claude is seen by that chat provider. So
de-identification can't only happen at the engine — it must be designed into the *intake pattern*.

**Recommended pattern (defense in depth):**

1. **Structured intake tool.** `tspi_submit_patient_case` takes explicit de-identified fields
   (`age_band`, `sex`, `symptoms`, `labs[]`, `medications[]`, `conditions[]`, `consent`). Its schema has
   **no name/DOB/MRN/contact fields at all**, so the model is steered to collect only what's allowed.
2. **Server-side PII scrub.** The MCP server runs a PII detector on every free-text field and **refuses
   or redacts** anything that looks like a name/ID/DOB/phone/email before forwarding to the engine, and
   returns a warning telling the doctor to remove it.
3. **Identity stays local.** If a human-readable identity is needed on the final document, the doctor's
   **MiHealth / local vault** maps `case_id → patient` *after* approval, outside the engine and outside
   the chat. The engine and LLM only ever see the `case_id`.
4. **Doctor guidance + onboarding.** The connector's welcome text and the tool descriptions instruct:
   *"Enter de-identified data only — use a case code, an age band, and sex. Do not type patient names or
   identifiers."* Optionally provide a thin local intake form (or a lab-drop that runs `tspi_extract_lab_report`
   locally) so PII never enters the chat box in the first place.

> **Strongest option (recommended for production):** run a **local pre-processor / MiHealth intake screen**
> where the doctor selects the patient; MiHealth de-identifies and hands the chat only a `case_id` +
> clinical payload. This keeps PII out of the chat provider entirely. The pure-chat path (typing into
> ChatGPT) is acceptable for a shadow pilot **only** with the scrub + explicit de-identified-input policy.

---

## 7. Authentication & multi-doctor

- **Per-clinician credential.** Each doctor authenticates to the MCP server (OAuth 2.1 for hosted /
  Claude.ai + ChatGPT connectors; signed API token for Claude Desktop). The engine currently has **no
  auth** — the MCP layer adds it and passes a verified `clinician_id` to the engine for audit and the
  approval signature.
- **Scopes/roles.** `clinician` (submit/generate/approve own cases) vs `admin` (learning governance).
- **Session isolation.** A doctor sees only their own cases; `case_id`s are namespaced per clinician.
- **Rate limiting + audit** on every call.

---

## 8. Client integration (per chat platform)

**Claude Desktop (local / on-prem clinic):** add the MCP server to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "tspi-ai-brain": {
      "command": "python",
      "args": ["-m", "tspi_mcp.server"],
      "env": { "TSPI_ENGINE_URL": "http://localhost:8000", "TSPI_CLINICIAN_TOKEN": "..." }
    }
  }
}
```

**Claude.ai (web / Teams-Enterprise):** add a **Custom Connector** pointing at the remote MCP server URL;
authorize via OAuth. Appears as tools the doctor can call in chat.

**ChatGPT:** add the remote MCP server as a **connector / custom action** (ChatGPT supports MCP for
tool use). Same OAuth flow; same tool set.

In all three the doctor then simply talks: *"Screen this case for red flags,"* *"Generate a treatment
plan,"* *"Remove module H-012 and approve."* The client calls the matching `tspi_*` tool.

---

## 9. Engine changes required (small)

Most tools wrap endpoints that already exist. New work on the engine side:

- 🆕 **`POST /reports/{id}/override`** — structured physician edits with reason codes (change/remove
  module, dose override, axis add/remove, `OVERRIDE_SAFETY_WITH_JUSTIFICATION`). Persist old→new +
  rationale (this also satisfies the 5 Aug "structured clinician overrides" requirement).
- 🆕 **Release-state field** on the report (`INTERNAL_TEST … CLINICIAN_DRAFT … APPROVED_FOR_SHADOW_PILOT
  … APPROVED_FOR_PATIENT_RELEASE`), fail-closed on unapproved registries.
- 🆕 **Auth hook** — accept a verified `clinician_id` (the MCP server authenticates; the engine trusts
  the internal call and records the id).
- ♻ **`/validate`** already sets deliverable — extend to record signature + release-state transition.

No change to the deterministic pipeline, scoring, or safety logic.

---

## 10. Phased delivery

| Phase | Scope | Outcome |
|---|---|---|
| **A. Read-only spike** | MCP server skeleton (FastMCP); wrap `/health`, `/screen`, `/analyze`, `/get report`; local stdio + Claude Desktop. | Doctor can screen + analyze a de-identified case in chat. |
| **B. Governance layer** | Auth (token), de-identification scrub, audit log, consent enforcement. | Safe to expose beyond a single dev machine. |
| **C. Plan lifecycle** | `generate_treatment_plan` (draft + watermark), `approve_treatment_plan`, `update_treatment_plan` (+ new engine endpoints), release states. | Full submit → generate → approve/update loop. |
| **D. Remote + clients** | Streamable-HTTP hosting + OAuth; Claude.ai connector + ChatGPT connector; lab-PDF `extract`. | Doctors connect from web chat clients. |
| **E. Pilot hardening** | Eval suite (MCP Inspector + clinician gold-standard cases), rate limits, monitoring, incident/rollback hooks. | Ready for a **clinician shadow pilot** (no auto-prescribe, no patient release). |

---

## 11. Testing & evaluation

- **MCP Inspector** for tool schema/round-trip testing during build.
- **Contract tests** — each tool against a live engine (happy path + error/fail-closed paths).
- **Governance tests** — assert PII is never forwarded; assert a plan is non-deliverable until approved;
  assert unapproved-registry output is watermarked and blocked from patient release.
- **Clinician gold-standard scenarios** (reuse the 5 Aug list: symptoms-only, critical result + low NSS,
  pregnancy, contraindicated module, thalassemia vs iron deficiency…) run end-to-end through the chat.
- **Eval questions** (per mcp-builder Phase 4) to verify the model uses the tools correctly.

---

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Doctor types PII into the chat (provider sees it) | De-identified-only intake schema + server scrub + onboarding policy; recommended MiHealth local pre-processor for production. |
| LLM paraphrases/embellishes clinical output | Tools return structured data; descriptions forbid invention; report carries the deterministic values + provenance; unsupported-statement detector (roadmap). |
| Module output not yet clinically valid (Blocker 1 open) | Fail-closed: modules returned as `PROVISIONAL CANDIDATE / NOT FOR CLINICAL USE`; patient release blocked until the Module Registry is approved. |
| Auth/tenant leakage | Per-clinician OAuth, namespaced case_ids, audit, rate limits. |
| Chat client outage / tool errors | Actionable error messages; `tspi_engine_health` surfaces status; graceful degradation. |

---

## 13. Dependencies & open decisions

**Depends on:** the engine's existing endpoints (ready) + the three small engine additions in §9. It does
**not** depend on Blocker 1/2 being resolved — the integration is buildable now, but its **clinical output
stays provisional** until the Module Registry and network mappings are approved (fail-closed by design).

**Decisions to confirm before Phase D:**
1. **Deployment model** — hosted remote MCP (web ChatGPT/Claude.ai) vs on-prem stdio (Claude Desktop in
   clinic). *Recommend: on-prem/local for the pilot (keeps PII off the public chat path), remote later.*
2. **Primary chat client for the pilot** — Claude Desktop, Claude.ai, or ChatGPT. *Recommend: Claude
   Desktop first (local, simplest, native MCP).*
3. **Identity handling** — pure-chat de-identified input vs a MiHealth local intake pre-processor.
   *Recommend the pre-processor for any real patient data.*
4. **Auth** — OAuth 2.1 (web) and/or signed tokens (desktop).

---

### One-line summary
Build a thin **FastMCP governance+adapter server** in front of the existing engine that exposes
`tspi_*` tools for screen → submit → generate → approve/update; the doctor's chat becomes the
conversational front-end while the engine remains the sole deterministic clinical authority, PII stays
out, and nothing reaches a patient without physician approval.
