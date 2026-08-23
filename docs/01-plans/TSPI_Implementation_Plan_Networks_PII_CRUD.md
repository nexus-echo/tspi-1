# TSPI — Implementation Plan: Networks (Blocker 2), Report PII Toggle, Knowledge CRUD API

*Plan only — no code changes yet. Three independent workstreams (A, B, C). A must precede C's
network endpoints; B is standalone.*

---

# PART A — Resolve Blocker 2: the 180-Network layer (Phase 9)

> 🟡 **Blocker 2 — data resolved, crosswalk open.** The client verified all 180 rows of
> `docs/latest-data/networks_180.csv`; `scripts/build_networks.py` now compiles them into
> `data/tspi_networks_180.json`. **Two gaps remain before the network layer scores:**
> (1) the `biological_axis`/`domain` columns are free-text labels (141 axis labels vs 39 axes) →
> we generated `network_axis_crosswalk_DRAFT.csv` (name-match suggestion + confidence per label)
> for **clinician sign-off** — see A.2; (2) propagation edges — see A.6.

**Goal:** load the verified `docs/latest-data/networks_180.csv` as the official Network master, wire
it into the engine, and embed it.

**Current state:** the engine has no network layer; `network_match` (25% of Module Match v1.0)
scores 0 for every module; `graph_engine` does root-cause over axes only.

### A.1 Compile the Network master (data)
- New `scripts/build_networks.py`: read `networks_180.csv` → `data/tspi_networks_180.json`.
- Fields per record: `network_code` (N001–N180, zero-padded — *confirm convention with client*),
  `network_number`, `network_name_en`, `domain_group` (the CSV "domain"), `biological_axis_label`
  (the CSV text label), `scope` (verbatim, Thai kept), `status: active`, `dataset_version`,
  `framework_version: 39-axis-master-260715`, `approval_status: APPROVED` (client-verified).

### A.2 Network → 39-Axis crosswalk  ⚠ *needs a decision*
The CSV's `biological_axis` column is a **network-level label** (e.g. "Systemic Inflammatory Load",
"CELA", "Liver Functional Reserve"), **not** an A1–A39 code. To connect networks to the 39-axis
engine we need `primary_axis_code`.
- `build_networks.py` auto-maps the label to A1–A39 where it matches the axis master; unmatched rows
  get `primary_axis_code: null, needs_axis_review: true`.
- Produce `docs/latest-data/network_axis_crosswalk_DRAFT.csv` for the client to confirm the
  unmatched ones (same review pattern we used for modules). **CELA(#120) → A34** is pre-set per their ruling.

### A.3 Schema + migration
- `models.py`: `Network` (code, number, name_en, domain_group, primary_axis_code, biological_axis_label,
  scope, status, version) + optional `NetworkAxis` link table (secondary axes) + `NetworkEdge`
  (upstream/downstream) **left empty for now** (see A.6).
- Alembic `0004_networks`.

### A.4 Repository + reasoning hooks
- `repository.py`: `networks()`, `network(code)`, `networks_for_axis(axis_code)`.
- `module_match.py`: `network_match` becomes computable **once module→network links exist**
  (that data comes with the corrected Module Registry — **Blocker 1, still open**). Until then it
  stays `NOT_ASSESSED`, but the master now exists so it lights up the moment Blocker 1 lands.

### A.5 Embeddings
- Extend `scripts/embed_knowledge.py` to embed the 180 networks (name + scope) into `kb_embeddings`
  (`kind='network'`). No-op on the hash/dev backend, as today.

### A.6 Known gap to flag (do not fake)
The CSV has **no `upstream`/`downstream` columns**, so **network propagation / root-driver-at-network-level
cannot be built from it.** Phase 9 delivers the network *registry* + axis crosswalk + embeddings +
reasoning hooks. Propagation stays deferred until edge data is supplied. (Note: their 17-Jul doc
shows propagation chains like `AXIS27 → N120 → N145 → N173`, so the edges exist somewhere — request them.)

### A.7 Tests
180 rows load; CELA=N120→A34; crosswalk coverage report; networks embedded; existing suite stays green.

**Files:** `scripts/build_networks.py`(new), `data/tspi_networks_180.json`(new), `models.py`,
`alembic/versions/0004_networks.py`(new), `repository.py`, `embed_knowledge.py`, `tests/`.
**Blocked-partial-by:** module→network links (Blocker 1) for full `network_match` scoring.

---

# PART B — Report PII toggle (config-driven)

**Goal:** a config flag that decides whether the treatment report is rendered **with** patient
personal information (PII) or **without** (the current de-identified default).

### B.1 🔴 Governance boundary — read first
The **ai-engine is de-identified by contract**: it must only ever receive `case_id + age_band + sex`,
and **PII must never reach the LLM** (report_composer). This is a hard rule we deliberately built.
Therefore the PII toggle must live in the **MiHealth backend** (the layer that *owns* patient
identity and renders the patient-facing report) — **not** in the ai-engine.

The flow becomes:
```
ai-engine  -> de-identified CaseReport (never any PII)            [unchanged]
MiHealth   -> if SHOW_PII: merge patient identity from its OWN DB into the rendered report
           -> else:        render with case_id + age band + sex only (today's behaviour)
```
PII is attached **after** the LLM, at render time — the engine and its prompts stay PII-free regardless.

### B.2 Config
- `mihealth-backend/app/config.py`: `report_show_patient_pii: bool = False` (env `REPORT_SHOW_PATIENT_PII`).
- Default **false** (safe). Optional per-request override allowed only for staff/clinician roles.

### B.3 Render layer
- A report-assembly function in the MiHealth backend that, when the flag is on, prepends a
  **patient identity block** (name, DOB, MRN, contact — from MiHealth's patient record) to the
  approved plan; when off, uses the de-identified header.
- Applies to whichever output formats the portal produces (screen / PDF / export).

### B.4 Safety + audit
- Guard/test asserting the **ai-engine request payload never contains PII** regardless of the flag.
- Audit every PII-included report (who requested, when, which patient) — showing PII is a
  governance-sensitive action.
- Keep the de-identified `deliverable=true` gate unchanged (physician approval still required).

### B.5 Tests
Flag off → no PII in output; flag on → identity block present; engine payload PII-free in both;
non-staff cannot force the PII version.

**Files:** `mihealth-backend/app/config.py`, the report/render module in `mihealth-backend`, its
audit + tests. **ai-engine: no changes** (that's the point).

*If you specifically want the ai-engine's standalone report object to carry an optional display
block, we can add an optional `patient_display` field that is populated only by MiHealth after the
LLM — but the recommended and safer placement is entirely in MiHealth.*

---

# PART C — Knowledge CRUD REST API + auto-updating embeddings

**Goal:** RESTful CRUD for **Keys, Domains, Axes, Networks, Phytochemical modules/products**, and
whenever any of these change, the affected **embeddings update automatically**.

**Current state:** knowledge loads from `data/*.json` into the DB via `seed_db`; embeddings are built
by a one-shot script. No runtime management API.

### C.1 Decide the source of truth  ⚠ *design decision*
Today the JSON files are the source of truth. CRUD implies the **DB becomes the runtime source of
truth** for these tables. Plan:
- DB = runtime source of truth.
- `scripts/export_masters.py`: on demand (and after each write batch) exports versioned JSON
  snapshots back to `data/` / `knowledge-sources/official/` for git history + audit.
- `seed_db` still bootstraps from JSON on an empty DB.
This keeps our versioning/lineage story intact while allowing live edits.

### C.2 Endpoints (one router per entity, consistent shape)
`app/api/admin_knowledge.py`:
| Entity | Base path | Ops |
|---|---|---|
| Keys | `/admin/keys` | GET list/one, POST, PATCH |
| Domains | `/admin/domains` | GET, POST, PATCH |
| Axes | `/admin/axes` | GET, POST, PATCH |
| Networks | `/admin/networks` | GET, POST, PATCH |
| Modules/Products | `/admin/modules` | GET, POST, PATCH |

- **Soft-delete only** (`PATCH status=archived`) — never hard-delete (expert rule; past reports must
  stay reproducible). No `DELETE` verb, or `DELETE` = soft-archive.
- Pydantic request/response schemas per entity; consistent envelope + error format.

### C.3 Validation gate (per write)
Reuse/extend `validate_master.py` as callable checks: axis codes ∈ A1–A39; network `primary_axis`
valid; module 1:1 (no product under two active codes); `dose_type` valid; framework_version pin
matches the active axis master. **Reject invalid writes before commit.**

### C.4 Versioning + audit
- Every write bumps the entity's `dataset_version` and writes a `change_log` row
  (`entity, ref_code, action, before, after, changed_by, timestamp`).
- New table `knowledge_change_log` + migration `0005_admin_crud`.
- Enforce `framework_version` consistency on axis/network/module writes.

### C.5 🔑 Auto-updating embeddings (the core of the request)
- `app/knowledge/reembed.py`: `reembed(kind, ref_code)` recomputes the embedding for **one** changed
  row (axis / network / module / product) and **upserts** it into `kb_embeddings`; on archive, it
  **removes** the vector.
- CRUD write → fire a **FastAPI BackgroundTask** calling `reembed(...)` (non-blocking) so the API
  returns immediately; the vector updates just after.
- `POST /admin/embeddings/rebuild` for a full deterministic rebuild.
- Behaviour by backend: real update on `ollama`/`api`; **no-op on `hash`/dev** (as today), so tests
  stay hermetic. Keys/Domains typically aren't embedded — embedding applies to axes, networks,
  modules, products.
- Guard the `EMBEDDING_DIM` vs model mismatch (existing rule).

### C.6 Access control ⚠ *decision*
The ai-engine currently has **no auth** (it's an internal service behind MiHealth). These are
clinical master-data endpoints, so they must be gated. Options:
- (a) Require an **internal admin token** on `/admin/*` in the ai-engine (simple), **or**
- (b) Expose CRUD **through the MiHealth backend** (which already has JWT + roles) as a proxy.
Recommendation: (a) admin-token on the ai-engine now + audit, with (b) as the eventual UI path.

### C.7 Tests
CRUD happy paths; validation rejects bad axis/network/module; soft-archive hides from active
selection but keeps history; version bump + change_log written; `reembed` invoked on write (mock on
hash backend); full-rebuild endpoint; auth gate.

**Files:** `app/api/admin_knowledge.py`(new), `app/knowledge/reembed.py`(new),
`scripts/export_masters.py`(new), `models.py` (change_log), `alembic/versions/0005_admin_crud.py`(new),
`schemas.py`, `repository.py`, `validate_master.py`, `app/main.py` (router mount), `tests/`.
**Depends on:** Part A (the `Network` model must exist before network CRUD).

---

## Recommended sequence & dependencies

```
A (Networks) ─────────────► C (CRUD needs the Network model + gives networks an editor)
B (Report PII) ── independent, can go anytime
```

| Order | Workstream | Why first | Blocked? |
|---|---|---|---|
| 1 | **A — Network master + crosswalk + embeddings** | unblocks the network layer; prerequisite for C's network CRUD | 🟡 propagation edges + module→network links still pending |
| 2 | **B — Report PII toggle** | small, isolated, high-value; MiHealth-only | 🟢 no |
| 3 | **C — Knowledge CRUD + auto-embeddings** | biggest; needs A's schema; sets DB as source of truth | 🟢 no (but see decisions C.1/C.6) |

## Decisions I need from you before coding
1. **A.2** — auto-map network→axis and send you the crosswalk to confirm, or wait for an official
   network→axis column?
2. **A.1** — is `network_code` = zero-padded number (N001…N180), or a different scheme?
3. **B** — confirm the PII toggle lives in **MiHealth** (recommended, keeps the engine PII-free), not the ai-engine.
4. **C.1** — agree DB becomes the runtime source of truth, with versioned JSON snapshots exported for git?
5. **C.6** — admin-token on the ai-engine now, or route CRUD through MiHealth's existing auth?

## Cross-cutting notes
- **No hard deletes** anywhere (clinical reproducibility).
- Every master write stays **versioned + audited** (consistent with `TSPI_Master_File_Update_Plan.md`).
- Embedding updates are **incremental + background**; a full rebuild endpoint exists as a fallback.
- Governance invariant preserved: **PII never reaches the ai-engine or the LLM.**
