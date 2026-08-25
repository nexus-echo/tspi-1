# TSPI Phase B — Authentication, RBAC & Audit (Plan)

*Plan only — no code yet. Adds identity, role-based access, and a hardened audit trail so the AI
Brain can be used by more than one clinician, over remote connectors, and eventually with real
patient data. **Additive and backward-compatible:** existing endpoints keep working; MiHealth and
the local Claude Desktop pilot are not broken.*

---

## 1. Why now / what it gates

Phase A proved the workflow locally for a single clinician. Before **multiple doctors**, **remote
chat clients** (Claude.ai / ChatGPT), or **any real patient data**, we need:

- **Authentication** — know *who* is calling (a verified `clinician_id`), so the physician-approval
  signature and audit trail actually mean something.
- **RBAC** — a clinician can only do clinician things and see their own cases; only the Clinical
  Review Board can touch the learning model.
- **Audit** — an append-only record of every clinically meaningful action (5 Aug directives: audit
  trail, physician e-approval, fail-closed).

Today the engine has **no auth** and MiHealth calls it directly; `store.audit()` + the `AuditLog`
table already exist and are a good base.

## 2. Trust boundaries

```
Doctor ─chat─► AI client ──►  MCP server  ──►  TSPI engine  ──►  DB
                  (cloud)     (enforces:      (enforces:        (audit_log,
                              client auth,     service auth,      owner_id)
                              tool RBAC,       role RBAC,
                              de-id)           tenant isolation)
```

Two auth layers, because there are two hops:
1. **Client → MCP** — authenticate the human clinician (token for local; OAuth for remote).
2. **MCP (or MiHealth) → engine** — authenticate the *service*, and carry the verified
   `clinician_id` + role so the engine can enforce RBAC and stamp ownership/audit.

The chat provider still sees the conversation, so **the MCP + engine remain the enforcement points**;
we never trust role/identity asserted by the LLM itself.

---

## 3. Authentication design

### 3.1 Engine (service auth) — the foundation (do first)
- Add a FastAPI dependency that requires a **service bearer token** (`Authorization: Bearer …`) on
  all clinical endpoints, plus a verified caller identity header **`X-TSPI-Clinician-Id`** and
  **`X-TSPI-Role`** (set by the trusted caller — MCP or MiHealth — never by the browser/LLM).
- New settings (mirroring the existing `require_doctor_validation` / `enforce_deidentification`
  pattern): `auth_enabled: bool = False`, `service_tokens: dict[token→{service,roles}]` (or a signed
  JWT verify key). **Default `auth_enabled=False`** so the current local pilot and MiHealth keep
  working until we flip it on per environment.
- `/health` stays open; everything clinical requires auth when enabled. **Fail-closed:** missing/invalid
  token → 401; valid token but insufficient role → 403 (audited).

### 3.2 Client → MCP
- **Local (Claude Desktop, stdio):** the MCP server is spawned on the clinician's machine; identity
  comes from `TSPI_CLINICIAN_ID` + a per-clinician token in the launch env, which the MCP server then
  presents to the engine. Trust boundary = the machine. Good enough for a single-site pilot.
- **Remote (Claude.ai / ChatGPT connectors):** the MCP server becomes an **OAuth 2.1 resource
  server**; the clinician signs in via an identity provider (MiHealth as IdP, or an external one).
  The access token carries `clinician_id` + role/scopes. *(Deferred to sub-phase B4 — only needed
  when we go remote.)*

### 3.3 MiHealth → engine
- MiHealth already owns patient identity + its own JWT/roles. It calls the engine with a **service
  token** and forwards its authenticated `clinician_id`/role in the same headers. No change to
  MiHealth's own login; it just adds the header + token on its engine calls.

---

## 4. RBAC design

### 4.1 Roles
| Role | Who | Can |
|---|---|---|
| `patient` | the patient (self-service, via MiHealth portal) | self-register, upload own lab reports, submit own symptoms; **view ONLY their own APPROVED treatment plan** (never a draft) |
| `clinic_staff` | front-desk / coordinator (non-clinical) | everything `patient` can, **plus** trigger report generation for a patient, view live case status, and view all patients' reports **within their clinic** — but **no clinical approval, override, or reject** |
| `clinician` | treating doctor | screen, analyze, generate, get, **update (override)**, approve/reject **their own** cases; record outcomes |
| `reviewer` (Clinical Review Board) | governance | everything a clinician can, **plus** decide learning proposals, rebuild patient model, (later) approve registries |
| `auditor` | compliance | **read-only**: fetch reports + audit log; no writes |
| `service` | MiHealth / MCP | machine caller identity; always acts *on behalf of* a user with that person's role |

> **Governance note on the two new roles.** `patient` and `clinic_staff` are **MiHealth-portal roles**,
> not chat/MCP roles. All patient **identity and PII live in MiHealth**; the engine still only ever
> receives a de-identified `case_id` + clinical data. Two hard rules: (1) a `patient` sees a plan
> **only after a physician approves it** (`deliverable=true`) — never a draft, and never another
> patient's data; (2) neither `patient` nor `clinic_staff` can perform any **clinical** action
> (approve / override / reject / learning) — those stay clinician/reviewer-only. Generation triggered
> by `clinic_staff` still produces a **draft** that a clinician must approve before the patient can see it.

### 4.2 Permission matrix (engine endpoints)
| Endpoint | patient | clinic_staff | clinician | reviewer | auditor |
|---|---|---|---|---|---|
| `/extract` (upload own lab report) | ✅ (own) | ✅ (clinic) | ✅ | ✅ | ❌ |
| `/screen`, `/analyze`, `/report` (generate) | ❌ | ✅ (trigger) | ✅ (own) | ✅ | ❌ |
| `GET /reports/{id}` | ✅ **own + APPROVED only** | ✅ (clinic) | ✅ (own) | ✅ | ✅ |
| `/reports/{id}/override`, `/validate` | ❌ | ❌ | ✅ (own) | ✅ | ❌ |
| `/outcome` | ❌ | ❌ | ✅ (own) | ✅ | ❌ |
| `/learning/recalibrate`, `/learning/proposals/*/decide`, `/patient-model/*/rebuild` | ❌ | ❌ | ❌ | ✅ | ❌ |
| `/learning/weights`, `/temporal/*` | ❌ | ❌ | ✅ | ✅ | ✅ |
| `/knowledge/health`, `/health` | ✅ | ✅ | ✅ | ✅ | ✅ |

### 4.2b MiHealth portal capabilities (patient/staff act here; MiHealth calls the engine as `service`)
| Capability | patient | clinic_staff |
|---|---|---|
| Self-register / register a patient | ✅ (self) | ✅ (patients in clinic) |
| Upload lab reports · submit symptoms (intake) | ✅ (own) | ✅ (clinic) |
| Trigger "generate treatment plan" | ❌ | ✅ |
| View live case status | own only | all in clinic |
| View a treatment plan | **own + approved only** | all in clinic |
| Approve / edit / reject a plan | ❌ | ❌ (clinician only) |

*MiHealth holds identity and de-identifies before every engine call; the engine enforces the same
rules server-side (defense in depth) using the forwarded role + `owner`/`clinic` scope.*

### 4.3 Tenant / case isolation
Two scopes, both stamped on each `Report`: **`owner_case_subject`** (the patient the case belongs to)
and **`clinic_id`** (the clinic), plus **`owner_clinician_id`** (the treating doctor).

- **`patient`** — may read a report only when it is **theirs AND approved** (`deliverable=true`).
  Drafts, other patients, and any write are denied (403).
- **`clinic_staff`** — may read all reports **within their `clinic_id`** and trigger generation there;
  no clinical writes. Denied outside their clinic.
- **`clinician`** — read/modify their **own** cases; `reviewer`/`auditor` read across.
- Enforce in `store` queries (filter by owner/clinic + approved-state for patients) **and** a
  dependency that re-checks scope before every read/write. Cross-tenant or draft-to-patient access →
  403 + audit. The patient "approved-only" filter is enforced **server-side**, not just in the UI.

### 4.4 Enforcement points
- **Engine:** a `require_role(...)` / `require_owner(...)` dependency per route (single source of truth).
- **MCP:** filter the advertised tool set by the clinician's role (e.g. hide learning-admin tools) —
  defense in depth, but the engine remains the authority.

---

## 5. Audit design (harden the existing `AuditLog`)

Current `AuditLog(action, case_id, report_id, actor, allowed, detail)` is a solid base. Extend to:
- Add fields: `role`, `source` (`mcp`|`mihealth`|`system`), `request_id` / `analysis_run_id`
  (correlation), `client` (chat client if known), `ip` (remote only), and keep `detail` for
  before/after.
- **Append-only:** no update/delete paths; a periodic export/verify job. (Optional later:
  hash-chain each row for tamper-evidence.)
- **Events to guarantee are audited:** auth success/failure, consent grant/deny, analyze, report,
  **override (with reason codes + before/after)**, approve/reject (the e-signature event),
  learning-proposal decisions, PII-scrub/redaction events, safety overrides, and any 403.
- Every clinical response already carries registry/algorithm versions — record them on the audit row
  so an action is fully reconstructable (ties to the 5 Aug "registry dependency graph").
- **Read API:** `GET /audit` (auditor/reviewer only) with filters (case, clinician, action, date).

---

## 6. Data-model changes (+ one migration)

- `Clinician` table: `clinician_id`, `name`, `role`, `status(active|disabled)`, `created_at`.
  *(Or, if MiHealth is the identity source, treat clinicians as external and store only role
  claims from the token — decision in §9.)*
- `Report`: add `owner_clinician_id`, **`owner_case_subject`** (the patient the case belongs to, a
  de-identified subject key — not PII), and **`clinic_id`** (all nullable for legacy rows). These
  drive the patient/clinic_staff isolation in §4.3.
- `AuditLog`: add the fields in §5.
- Optional `ServiceToken`/credential table (if not using signed JWTs).
- **Alembic `0004_auth_audit`**, additive columns with safe defaults so existing rows/behaviour are intact.

## 7. Config & secrets

- New engine settings: `auth_enabled` (default false), `service_token(s)` or `jwt_public_key`,
  `oauth_issuer`/`audience` (B4). MCP: `TSPI_ENGINE_TOKEN` (already stubbed), `TSPI_CLINICIAN_ID`,
  and OAuth client settings (B4).
- Secrets via env/secret store only; **never logged**; `.env` stays git-ignored (already is).

---

## 8. Sub-phases (delivery order)

| Sub-phase | Scope | Breaks anything? |
|---|---|---|
| **B1 — Engine service auth + identity** | bearer-token dependency, `X-TSPI-Clinician-Id`/`X-TSPI-Role`, `auth_enabled` flag (default off), owner stamping on reports | No — off by default; MCP + MiHealth add a token |
| **B2 — RBAC enforcement** | roles, permission matrix dependency, tenant isolation, MCP tool gating | No — enforced only when auth on |
| **B3 — Audit hardening** | extend AuditLog, correlation ids, guaranteed events, `GET /audit`, append-only | No — additive |
| **B4 — Remote OAuth (optional)** | MCP as OAuth resource server for Claude.ai/ChatGPT | Only when going remote |

Recommended: **B1 → B2 → B3 now**; **B4 when/if you need web chat clients.**

## 9. Testing

- **AuthN:** no token → 401; bad token → 401; valid service token + clinician header → 200.
- **AuthZ:** clinician cannot hit learning-admin (403); auditor cannot write (403); reviewer can.
- **Tenant isolation:** clinician A cannot read/override clinician B's report (403).
- **Audit completeness:** each of the guaranteed events writes exactly one audit row with actor+role+
  correlation id; overrides capture before/after + reason.
- **Backward-compat:** with `auth_enabled=false`, the existing 76 tests still pass unchanged.
- **Fail-closed:** auth error stops the action; nothing partially executes.

## 10. Backward compatibility (important)

- `auth_enabled` defaults **off** → today's local Claude Desktop pilot and MiHealth keep working with
  zero changes. Turn it **on per environment** (staging/prod) once tokens are issued.
- All new DB columns are nullable/defaulted; the migration is additive.
- The standalone engine, MiHealth, and any REST client continue to work; they simply start sending a
  token + identity header once auth is enabled.

## 11. Open decisions (confirm before B1)

1. **Identity source:** is **MiHealth the identity provider** (engine trusts its clinician_id + role
   claims), or does the engine keep its own `Clinician` table? *Recommend: MiHealth is the IdP; engine
   stores role claims + owner_id only — avoids duplicate user management.*
2. **Token type:** **signed JWT** (stateless, carries clinician_id+role) vs **opaque service tokens**
   (simple, table-backed). *Recommend: JWT for MiHealth-issued clinician identity; a static service
   token for the local pilot.*
3. **Do B4 (remote OAuth) now or later?** *Recommend: later — only when a web chat client is needed;
   the pilot runs local.*
4. **Tamper-evident audit (hash-chain)** now or a later hardening pass? *Recommend: later; start with
   append-only + export.*
5. **Does `clinic_staff` see full clinical drafts, or only status + approved plans?** They can view all
   patients' reports in the clinic — but should an unapproved *draft's* clinical detail be visible to
   non-clinical staff, or only its status until a clinician approves? *Recommend: staff see **status**
   for any case but full clinical content only once **approved**; drafts show status + safety flags
   only.* Confirm.
6. **Patient identity & self-registration live entirely in MiHealth** (the engine stays
   de-identified). Confirm patient/clinic_staff auth is via MiHealth's login (not the MCP/chat path),
   and that the patient's "view approved plan" re-attaches PII in MiHealth after approval (per the
   existing Report-PII-toggle plan).

---

### One-line summary
Add a token-based auth layer + role/owner checks on the engine (off by default, so nothing breaks),
gate MCP tools by role, and extend the existing audit log into a complete, append-only trail — then
turn it on per environment before multi-doctor or real-patient use. Build order: **B1 → B2 → B3**,
with remote OAuth (**B4**) only when web chat clients are needed.
