# TSPI AI Engine — Project Status & Update

*Prepared for the TSPI clinical / domain-expert team · Last updated: 5 Aug 2026*

This document summarises where the TSPI AI Engine stands today: what is built and tested, what remains,
and — most importantly — **what we now need from your team to keep the project moving**. The engine's
core is complete; the remaining timeline depends largely on a few clinical data approvals that only your
team can provide.

> **Update — incorporating your 5 Aug Final Review.** Your final ruling on severity is now implemented:
> **data completeness no longer reduces an axis's severity** (NSS reworked to v0.3 — a severe finding
> stays severe, with reliability shown separately). **CELA is recorded as approved** (`TSPI-NET-0120` →
> A34 / D10), and the A10 sub-axes and the nine Restoration Steps are locked to your canonical lists.
> Your review also added a pre-pilot governance layer (see §7) and corrected one assumption: the 25%
> network match depends on a new **Module-to-Network Claim Registry**, not the axis crosswalk alone.

---

## 1. What TSPI is (one paragraph)

TSPI is the registry-driven, deterministic AI "brain" behind MiHealth. Reasoning flows
**Clinical Evidence → Evidence Integration → 3 Keys → 9 Restoration Steps → 12 Domains →
39 Biological Axes → 180 Living Networks → Module ranking → Physician approval → Reports.**
The **39 Axes are the central diagnostic and module-matching layer**; the 180 Networks *explain and
validate* mechanisms — they never replace axis matching. The AI only summarises and translates; it never
invents an axis score, network identity, module, research result, or outcome. Frozen ontology:
`framework_version = 39-axis-master-260715`.

## 2. Constitutional rules (permanent, always enforced)

Deterministic engine · official-registry-only resolution · **missing data → NOT_ASSESSED, never 0,
never a default of 50** · confidence/completeness affect *reliability, not severity* · Evidence Status ≠
Evidence Grade ≠ Confidence ≠ Completeness · a hypothesis never scores · **safety is a categorical gate,
not a number** · red-flag screening runs first · **learning is propose-only** (a clinician always
approves) · one immutable analysis record per run · the system fails closed when a registry is missing or
unapproved · physician approval before any patient release.

## 3. Built & tested — engine core ✅ (71 automated tests passing)

| Area | State |
|---|---|
| Full pipeline (normalise → axis-map → severity → module-match → safety → compose → validate) | ✅ |
| Evidence model — 4 dimensions + biological uncertainty, explicit NOT_ASSESSED | ✅ |
| Red-flag safety screening — deterministic, runs first, critical-value layer | ✅ |
| Phenotype engine + named Phenotype Registry (Option A, candidate list) | ✅ |
| Network Severity Score **v0.3** (completeness never reduces severity) + Module Match v1.0 | ✅ |
| Legacy → current axis converter (auto-applies safe cases, quarantines the rest) | ✅ |
| Learning — propose-only, versioned patient model | ✅ |
| Marker Registry — value source vs direction rule, curve types, context markers | ✅ |
| Canonical records locked — CELA (`TSPI-NET-0120`→A34/D10), A10 sub-axes, 9 Restoration Steps | ✅ |
| All refinements from your 25 Jul, 31 Jul and 5 Aug guidance | ✅ (see §5) |

---

## 4. Remaining work — and what it depends on

The work still ahead falls into three groups. **Group 4a we can do on our own. Groups 4b and 4c
depend on your team and are on the critical path** — every item there blocks downstream work until it is
provided.

### 4a. What we are building now (no dependency on you)

We continue in parallel while awaiting your approvals:

- **Network layer integration** — loading the 180 networks into the engine and wiring the mechanistic-
  validation step (today the network score is a safe placeholder marked "not assessed").
- **Report layer** — the Physician, Patient, and Multi-Omics reports, **Thai-first bilingual**, all
  reading from one immutable analysis record, with a cross-report consistency check and physician
  e-signature.
- **Minimum-evidence gate, governance controls, and the remaining registry loaders** (lab cut-offs,
  research claims, restoration-step mapping) — ready to receive your clinical content the moment it
  arrives.

### 4b. ⚠ What we need from you — URGENT, on the critical path

These are the items that currently **hold up clinically usable output**. Until they are provided, the
engine can reason and rank internally, but its recommendations **cannot be released for clinical use**.
Each week of delay pushes back the physician pilot and, after it, patient-facing reports.

| # | What we need | Why it blocks everything downstream | If delayed |
|---|---|---|---|
| **1** | **Approved Module Registry** (Blocker 1) — the module list mapped to current A1–A39 axis codes, marked APPROVED | Modules cannot enter clinical ranking until their axis mappings are expert-approved. We have prepared the candidate remap; it needs your sign-off. | **No clinically usable module recommendations at all** — the single biggest blocker. |
| **2** | **Confirm each network's Primary/Secondary Axis** (Blocker 2a) — sign off the crosswalk we sent | The 39-axis engine cannot use the 180 networks until each network's axis is confirmed. This also switches on the network-validation component of module scoring. | Network mechanistic validation stays off; module scores stay provisional. |
| **3** | **Network connections / edges** (Blocker 2c) — which network feeds which | Without edges, the AI cannot trace a problem to its root network or explain propagation. | The "network explanation" layer stays incomplete. |
| **4** | **Clinical reference content** — lab cut-off thresholds, per-claim evidence grades, and the per-axis minimum-evidence rules | These are the tables the engine reads instead of guessing. Without them, axes cannot be scored to a clinical standard and modules cannot be graded. | Axis scoring and module grading remain provisional, not production-grade. |

> **Why this is time-sensitive:** the engine is essentially finished waiting on *decisions* — it is now
> waiting on your *data and approvals*. These four items are sequential dependencies for the physician
> pilot. Starting the expert review now (even a few rows or one registry at a time) directly shortens the
> path to a working pilot. The corresponding fill-in files and the candidate mappings are already in your
> hands.

### 4c. Decision resolved (5 Aug) ✅

- **How the severity score treats incomplete evidence — now decided and implemented.** Your 5 Aug ruling
  is final: **data completeness must not reduce an observed abnormality's severity.** We reworked the
  severity score accordingly (**NSS v0.3**): a severe finding stays severe, and reliability (confidence,
  completeness, coverage, biological uncertainty) is reported alongside it rather than bent into the
  number. Only axes that reach the required assessment state contribute; provisional axes produce a
  clearly-labelled *Provisional* score. This item is closed.

---

## 5. Refinements completed in response to your 31 Jul guidance

We implemented your review points immediately. In plain terms:

1. **Ferritin** now reads as a blood/iron marker first (Axis A26) and only points to inflammation (A1)
   when inflammatory markers confirm it — correcting the earlier A34 typo.
2. **HOMA-IR** is calculated with the correct unit-specific formula and **refuses to compute if the unit
   is unknown**, preventing wrong insulin-resistance values.
3. **Each network now carries three separate identifiers** (a permanent code, a display number, and the
   legacy N-id), so future re-ordering never changes a network's identity.
4. **A network's Domain is derived automatically from its confirmed Axis** — no duplicate or
   contradictory domain data.
5. **Axis assessment uses your five official states** (Not Assessed → Axis Candidate → Provisionally
   Assessed → Assessed → High-Confidence Assessed).
6. **Modules with no graded evidence are marked "not yet graded" (neutral)** — never mislabeled as
   weakest.
7. **Safety is a clear categorical decision** (Pass / Pass-with-Monitoring / Hold / Contraindicated /
   Insufficient-Safety-Data), never a number.
8. **When network data is unavailable, the score shows "not assessed" plus a coverage percentage** — never
   a silent zero, and never quietly re-weighted.

Following your 5 Aug review we also: reworked the **severity score (NSS v0.3)** so completeness never
reduces severity; recorded **CELA as approved** (`TSPI-NET-0120` → A34 / D10); and locked the **A10
sub-axes** and the **nine Restoration Steps** to your canonical numbered lists. Your crosswalk /
minimum-evidence corrections (delete the example row, add the missing fields, define the confidence
scale, apply the semantic mapping fixes) remain queued for those two review spreadsheets.

---

## 6. The two blockers — where they stand and why they matter

**Blocker 1 — Module Registry (🟡 waiting on your approval).**
The official legacy → current axis mapping has been received, and our converter now automatically applies
the clearly-safe mappings and **quarantines the risky ones for your review** (a blind number-swap is
unsafe — e.g. legacy "Metabolic Balance" is *not* today's A27). **What remains is your approval of the
candidate remap.** This is the highest-impact blocker: until it is approved, module recommendations
cannot be used clinically. We can prepare the full candidate file for sign-off on request.

**Blocker 2 — the 180-Network layer (🟡 partially resolved).**
All 180 networks are transcribed and verified, **CELA is now approved** (`TSPI-NET-0120` → A34), and we
have built the axis/domain crosswalk for your review. **Three things remain:** (a) your **row-by-row
confirmation of each network's Primary/Secondary Axis**, (b) the **network-to-network connections
(edges)**, and (c) — per your 5 Aug review — a **Module-to-Network Claim Registry** (which module treats
which network, with evidence). Note: the 25% network-match component depends on (c), not on the axis
crosswalk alone; until it exists the component correctly stays *Not Assessed* rather than defaulting to
zero.

> **In one line:** the fastest path to a physician pilot is **(1) approve the Module Registry remap** and
> **(2) begin confirming the network axis mappings** — even incrementally. Both are ready for your review
> now.

---

## 7. Pre-pilot governance layer (added by your 5 Aug review)

Your final review introduced a set of governance and validation requirements that must exist before a
physician pilot. None of them change what is already built; they define what must be in place before any
clinical use. We are folding them into the implementation plan:

- **Module-to-Network Claim Registry** — the real basis for network match (see §6).
- **Evidence de-duplication** — one result (e.g. ferritin) must not score full weight into several axes
  at once.
- **Two-stage safety** — the pre-ranking eligibility gate we already have, **plus** a new
  regimen-level combination review (ingredient/mechanism duplication, additive effects, pill burden).
- **Statement-level provenance + an unsupported-statement detector** — every clinical sentence must trace
  to data and an approved rule, or be labelled a non-scoring hypothesis.
- **Ontology vs patient-assessment separation** · distinct **null / 0 / false / NOT_ASSESSED** semantics ·
  a **persistent versioned Patient Biological Model** with explicit transition reasons.
- **Release-state ladder** (fail-closed; nothing provisional reaches patient release) · **cross-report
  consistency validator** · **registry dependency graph** · **rollback / incident management**.
- **Clinician-authored gold-standard test cases** and a **physician shadow-pilot** (no auto-prescribing,
  no patient release) — because the 71 automated tests prove technical behaviour, not clinical validity.

**Recommended sequence to a pilot (from your review):** approve the Module remap → complete the network
crosswalk → build the Network Edge Registry → build the Module-to-Network Claim Registry → approve the
pilot clinical registries → lock NSS → run clinician gold-standard tests → physician shadow pilot →
patient release only after formal approval.
