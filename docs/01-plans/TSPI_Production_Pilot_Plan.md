# TSPI — Production Pilot Plan (blockers, PII, bilingual reports, deployment)

*Goal: get an end-to-end, deployable system for a **physician shadow pilot** — clinician-facing, no
automatic patient release — using best-available **provisional** clinical data, then iterate post-deploy.
This is the exact "shadow pilot" the domain experts recommended.*

---

## 0. Reality check + decisions locked (read first)

Target = a **clinician shadow pilot** (clinician-facing, no auto patient release), deployed with
best-available **provisional** data, then iterate. Full clinical validation is a post-pilot step.

**Decisions now locked (26 Aug):**
- ✅ **`PILOT_MODE` — approved.** Candidate datasets are usable for ranking; every report is watermarked
  *PROVISIONAL / NOT CLINICALLY VALIDATED*; physician approval mandatory; no auto patient release.
  Enabled in the pilot environment only.
- ✅ **PII — centralised at the engine API; the LLM stays PII-free** (see §2). One deployable now,
  split-ready into `ai_api` + `brain` pods later.
- ✅ **Report template — done.** Common template distilled from the 3 sample reports →
  `docs/02-reference/TSPI_Report_Template.md`. Bilingual (th/en), two audiences.
- ✅ **Extraction stays in the engine** (already `POST /extract`, local vision/text models).

**Still needed from you:** the default **report language** (th or en; both supported at generation
time). Deployment access (Coolify project, Supabase URLs, Tailscale Ollama IP — you have
`100.121.11.25:11434`).

---

## 1. Open items / blockers — and how we resolve them for the pilot

| # | Item | Pilot resolution |
|---|---|---|
| B1 | **Approved Module Registry** (legacy→current axis) | Apply our candidate remap (`TSPI_Candidate_Module_Remap.xlsx`) under `PILOT_MODE=true`: Tier-A auto-mapped modules become *pilot-eligible*; Tier-B/C stay quarantined. Every recommendation flagged PROVISIONAL. |
| B2a | **Network→axis/domain crosswalk** | Load the auto-suggested crosswalk (`network_crosswalk_FULL_DRAFT.csv`) as `mapping_status=CANDIDATE`; domains derive from axis. |
| B2c | **Network edges** | Not required for the pilot: `network_validation_status=NOT_ASSESSED` (already correct). Root-cause is axis-based. |
| — | **Module-to-Network Claim Registry** | Deferred: 25% network-match stays NOT_ASSESSED (module ranking is axis-based). |
| C1 | **Lab Cut-off Registry** | Seed candidate cut-offs for the common markers (CRP, HbA1c, glucose, Hb, TSH, ferritin, Na, K, creatinine/eGFR…) from standard references; `authoritative=false`. Unknown marker → NOT_CLASSIFIABLE. |
| C2 | **Per-claim Evidence Grades** | Modules stay `EVIDENCE_NOT_GRADED` (neutral, not D) — already implemented. |
| C3 | **Per-Axis Minimum-Evidence** | Seed candidate minimum-evidence for all 39 axes; status `CANDIDATE_FOR_EXPERT_REVIEW`. |
| — | **Marker Registry** | Expand our seeded registry to the common panel; `authoritative=false`. |
| — | **Phenotype Registry** | Expand from 4 → ~20–30 candidate phenotypes; `status=CANDIDATE`. |
| — | **9 Restoration Steps + module→step** | Load the canonical S1–S9 names; seed candidate module→step where inferable, else neutral. |

**1c — governance switch (✅ APPROVED):** engine setting **`PILOT_MODE`** (default **false**; **true**
in the pilot env). When true, candidate datasets are usable for ranking, every report is watermarked
**"PILOT — PROVISIONAL, NOT CLINICALLY VALIDATED"**, patient-release states are blocked, and physician
approval is mandatory. When false, the current fail-closed behaviour stands.

---

## 2. PII architecture (DECIDED — centralised at the engine API, LLM stays PII-free)

**Decision (26 Aug):** With multiple clients (MCP, direct API, future), per-client de-identification is
the wrong design. **PII handling is centralised server-side at the engine API.** The rule that matters —
and that we keep absolutely — is **"PII must never reach the LLM,"** not "PII must never reach the
engine." The engine may hold PHI; the LLM only ever sees placeholders.

**Two layers (one deployable now; splittable into two pods later):**

- **`ai_api` (PHI side — what clients call):** authentication/RBAC · **extraction** of uploaded reports
  (text/image/x-ray/MRI/CT via local models) · store patient data (PHI) in the engine DB (Supabase) ·
  **de-identify** → call the brain → **re-insert PII into the finished report** · hand to the doctor
  *with* identity for validation · deliver the final PDF to the patient.
- **`brain` (internal, de-identified):** domain/axis mapping · scoring · the **LLM step**, which only
  ever receives `case_id` + de-identified fields + **PII placeholders** and returns placeholder text.

Enforced with a hard internal **de-id boundary**: all PII passes through one `deid` module; the `brain`
module is constructed so it can only receive de-identified input. Package as one FastAPI service for the
pilot, structured to split into `ai_api` + `brain` pods later without rework.

**Non-negotiable guardrails (PHI now lives in the engine DB):**
1. **LLM never sees PII** — a prompt-builder that can read only de-identified fields + placeholders,
   with a test that fails if any identifier reaches the prompt. Cloud LLM (DeepSeek, not HIPAA-safe) is
   used **only** on de-identified content; PHI-bearing steps use local Ollama only.
2. **PHI encrypted at rest + column-level encryption for identifiers, strict RBAC, audit** on the engine
   DB. Mandatory.
3. **Re-identification is server-side, after the LLM, before doctor review** — never in the brain.
4. **Chat/MCP caveat:** never render the identified report *into the chat transcript* (the chat provider
   would see PII). The MCP `report` tool returns **de-identified**; the **identified PDF is delivered
   out-of-band** (secure link/download generated server-side).

*MiHealth's role after this change:* the patient/clinic **portal** (accounts, workflow UI). The
de-id/re-id + extraction + report assembly it currently does either moves behind the shared `ai_api`
or calls it — so there is exactly **one** PII-handling implementation, not one per client.

*If you truly want PII to live in the engine and be tokenised only at the LLM call, that's possible but
it makes the engine a PHI system (encryption, BAA, audit, Supabase PHI posture) — I do **not** recommend
it. The recommended design gives you the same user outcome without that exposure.* **Please confirm the
recommended design.**

---

## 3. Report generation — template + bilingual (Thai/English)

- **You provide 2–3 approved TSPI reports** → we reverse-engineer a **report template** (sections,
  ordering, wording, disclaimers) so generated reports match your house style.
- **Template engine:** a structured Analysis Object → rendered report (HTML/PDF), driven by a template
  file — not free LLM prose. The LLM only *translates/explains* pre-computed structured content.
- **Language option:** a `report_language` parameter (`th` | `en`, default your choice). Canonical
  clinical terms (axis codes, module names) stay stable; the narrative + section labels localise. Thai
  is rendered with a Thai-capable font in the PDF.
- **Two audiences** (from the 5 Aug spec): Physician report (full evidence chain) and Patient report
  (Confirmed / Probable / Not-yet-known / next tests / approved plan / safety) — both from the **same
  Analysis Object**, differing only in language/detail. Patient report only after physician approval.

*Blocked on you: the 2–3 sample reports. Everything else can start now with a placeholder template.*

---

## 4. Production deployment — analysis of your stack

**Your stack:** Hostinger VPS + Coolify · Supabase Postgres · local Ollama (GPU) via Tailscale · 4 pods
(MiHealth FE, MiHealth BE, TSPI AI API, TSPI MCP).

**Overall: a sensible, cost-effective pilot topology.** Notes and recommendations:

- **Coolify on a Hostinger VPS** — good self-hosted PaaS (git-driven deploys, per-service containers,
  healthchecks). Watch: it's a **single VPS** — size it (≥ 4 vCPU / 8–16 GB for 4 services + build), set
  **per-container CPU/RAM limits**, enable **auto-deploy from the two git repos** (tspi_new + mihealth),
  and configure **backups**. No HA — fine for a pilot; note it.
- **Supabase Postgres** — good managed choice. Must-dos:
  - **Enable the `pgvector` extension** (the engine needs it) — Supabase supports it.
  - Use **two separate databases/projects**: `tspi` (engine) and `mihealth` (portal), isolated.
  - Use the **connection pooler** (pgBouncer) for FastAPI; set sane pool sizes.
  - **PHI now lives in the engine (`tspi`) DB** (per §2 the engine stores patient data + does re-id):
    enable **encryption at rest**, **column-level encryption for identifiers**, strict RBAC, and audit
    on the `tspi` DB — the same posture MiHealth already applies. The **brain layer** still never reads
    PHI; only the `ai_api`/de-id layer does.
- **Local Ollama via Tailscale** — great for privacy (PHI-bearing OCR/LLM stays on your GPU box) and
  cost. Risks: it's a **single point of failure** for embeddings, extraction, and report LLM; depends on
  home network + Tailscale uptime. Mitigations (mostly already in code): extraction degrades to a clear
  error; embeddings can fall back to `hash`; **report writing that touches PHI must use local Ollama
  only — never DeepSeek/cloud LLM**. Keep the cloud LLM (DeepSeek) for *de-identified* summarisation only.
- **4 pods** — good separation. Two cautions:
  - **TSPI MCP as a public pod needs OAuth (Phase B4).** As-is it has **no incoming auth** — do **not**
    expose it publicly yet. For the pilot, either keep the MCP **internal-only** (reachable over
    Tailscale / not public) with the static clinician token, or implement B4 before public exposure.
  - **MiHealth is a separate repo** now — Coolify deploys FE + BE from that repo; engine + MCP from
    tspi_new. Wire `TSPI_BASE_URL` (MiHealth→engine) and `TSPI_ENGINE_URL` (MCP→engine) to the engine
    pod's internal URL; keep the **engine private** (no public route), expose only MiHealth web (+ MCP
    only if OAuth'd).
- **TLS/HTTPS**: terminate at Coolify's reverse proxy (Traefik) with Let's Encrypt for MiHealth web (and
  MCP if public).
- **Secrets**: Coolify env vars / secrets — `AUTH_ENABLED=true`, `SERVICE_TOKENS`, DB URLs, JWT secret,
  encryption key, DeepSeek key. Never in git.

**Net:** solid for a pilot. The two things to fix before *public* exposure are **MCP OAuth** and
**keeping the engine private**; everything else is standard Coolify wiring.

---

## 5. Phased implementation (small, shippable phases)

Ordered so each phase is independently testable and the pilot can go out after P6.

| Phase | Deliverable | Status / needs you |
|---|---|---|
| **P1** | `PILOT_MODE` flag; candidate datasets usable; reports watermarked; patient-release blocked | ✅ approved — ready to build |
| **P2** | **Candidate clinical data**: lab cut-offs, per-axis minimum-evidence (39), expanded markers, ~20–30 phenotypes, S1–S9 steps — all `authoritative=false` | ready |
| **P3** | Apply candidate Module remap under PILOT_MODE; load network crosswalk (candidate) | ready |
| **P4** | **PII centralised at the engine API**: `deid` boundary, encrypted PHI storage, extraction stays engine-side, **re-id at render only**, LLM-prompt PII guard + test; one deployable, split-ready | ✅ decided — ready |
| **P5** | **Report renderer** — build from `TSPI_Report_Template.md`; Analysis Object → HTML/PDF; bilingual th/en; physician + patient variants | template ✅ done; need **default language** |
| **P6** | Deployment: Coolify configs, Supabase pgvector + pooler + **encrypted `tspi` DB**, Tailscale→Ollama, **engine private**, MiHealth public, `AUTH_ENABLED=true` | need VPS/Supabase access |
| **P7** | **MCP OAuth (Phase B4)** — only if the MCP surface is exposed publicly | decision (else keep MCP internal) |
| **P8** | Clinician gold-standard test cases + shadow-pilot checklist; monitoring | your clinician input |

**Fastest path to pilot: P1 → P2 → P3 → P4 → P5 → P6.** P7 only if chat/MCP is public; P8 runs alongside.

**Suggested build grouping (to move fast):**
- **Batch A (data & governance, no external dep):** P1 + P2 + P3 — one branch, one test pass.
- **Batch B (PII rework):** P4 — the deid boundary + re-id + guard.
- **Batch C (reports):** P5 renderer.
- **Batch D (ship):** P6 deploy; P7/P8 as needed.

---

## 6. What I still need from you

1. **Default report language** — `th` or `en`? (both work at generation time; this sets the default.)
2. **Deployment access for P6** — Coolify project, Supabase project URLs/keys, confirm the Tailscale
   Ollama IP (`100.121.11.25:11434`).
3. **P7 decision** — will the MCP/chat surface be **public** (needs OAuth) or **internal-only** for the
   pilot (no OAuth needed now)?

Everything else is decided. **P1–P5 need nothing further from you** and can start now.
