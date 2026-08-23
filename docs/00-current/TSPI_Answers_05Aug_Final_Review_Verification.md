# Verification — Final Review of 5 Aug 2026

*Source: `inbound/tspi 05.08.2026 Final Review of the Project Status, Canonical Architecture, Remaining
Blockers, and Required Corrections.pdf` (31 pages + "Additional Development Requirements" appendix).
This is the expert team's **direct review of our `PROJECT_STATUS.md`**. Verified against the frozen
axis master, the engine code, and the 25 Jul / 31 Jul answers.*

---

## 1. Headline

The review **endorses our foundation** ("the software does not need to be rebuilt from zero… the
development team is now working on the correct foundation"), **resolves the one decision we were
holding**, formally **approves several items**, and **adds a large set of governance requirements** for
the road to a physician pilot. It also makes one important **correction to an assumption** in our status
report (the 25% network match).

**Does it resolve open issues? Yes — three concrete resolutions, plus approvals:**

| Open item | Resolution (5 Aug) |
|---|---|
| **NSS / incomplete-evidence decision** (our §4c, held for expert) | **RESOLVED & FINAL** — completeness must **not** reduce severity (see §2). |
| **CELA** | **APPROVED** — `TSPI-NET-0120`, Network 120, primary axis **A34**, primary domain **D10**, `mapping_status=APPROVED`. |
| **A10 sub-axes** | **Canonical** — A10A/B/C/D confirmed; modules map to parent A10, sub-axes are tags only (no duplicate module records). |
| **9 Restoration Steps** | **Canonical numbered list** S1–S9 given (S9 = Prakati / Bioelectrical & Physiological Coherence; ignore narrative "Step 8" drift). |
| 6 of our refinements | **Explicitly approved** (§4). |

**Still pending (process/schema approved, data not delivered):** Module Registry row approval (Blocker
1), full network-to-axis crosswalk (Blocker 2a), Network Edge Registry (2c), and the clinical reference
registries. These remain on the critical path.

---

## 2. The one change this forces in our code — NSS

**Final ruling (§14 + Final Lock):** *"Data Completeness must not numerically reduce the severity of an
observed abnormality… `Final Severity = Severity × Data Completeness` is prohibited."* Confidence and
completeness describe **reliability and coverage**, reported **separately** — never severity multipliers.

**Impact:** our current **NSS v0.2** computes `AxisWeight = Confidence × DataCompleteness ×
EvidenceQuality` *inside* the weighted mean, so completeness **does** influence the aggregate severity.
That is now explicitly disallowed. **NSS must be reworked to:**

1. Compute severity only from axes that meet the required **assessment state**, with these inclusion
   rules: `NOT_ASSESSED` → excluded · `AXIS_CANDIDATE` → excluded from final NSS · `PROVISIONALLY_
   ASSESSED` → only a **labelled Provisional NSS** · `ASSESSED` / `HIGH_CONFIDENCE_ASSESSED` → included.
2. **Not** use completeness/confidence as severity multipliers — report them alongside.
3. Emit a full result object: **Observed NSS · Assessment Coverage · Overall Confidence · Biological
   Uncertainty · Assessment Status · Algorithm Version**. Critical alerts still override NSS.

This is the single code item that changes because of this document. (It was already flagged as the open
§4c decision; it is now decided.)

## 3. One assumption corrected — the 25% Network Match

Our status said confirming the network-to-axis crosswalk would *activate* the 25% network-match
component. **§12 + appendix §5 correct this:** network match must **not** be inferred from a module and a
network sharing an axis (that would just duplicate axis match). It requires a **new approved
Module-to-Network Claim Registry** (module → network → claim → mechanism → evidence). Until that registry
exists: `network_match_status = NOT_ASSESSED`, `network_match_score = null`. *We already emit
NOT_ASSESSED, so no regression — but the activation path is a new registry, not just the crosswalk.*

## 4. What it explicitly approves (our design validated)

Ferritin (A26 primary / A1 contextual, CONTEXT_DEPENDENT) · HOMA-IR unit-guarded calculation · the
three-identifier network model (permanent code / display number / legacy N-id) · `NOT_YET_GRADED`
(ungraded ≠ D) · the five categorical safety outcomes · network match `NOT_ASSESSED` (never 0, never
reweighted) · propose-only learning · NOT_ASSESSED never 0/50 · hypothesis never scores · physician
approval before release. One small adjustment: the **official permanent-code format is `TSPI-NET-####`**
(we seeded `LBN-###`), and **CELA's record should be marked APPROVED**.

## 5. What is new — added requirements (road to pilot)

None conflict with the engine; they extend governance, scoring integrity, and clinical safety. Grouped:

**Scoring integrity**
- **Module-to-Network Claim Registry** (new) — the real basis for network match (see §3).
- **Evidence de-duplication** — one item (e.g. ferritin) must not contribute full weight to A26+A1+A15+A35;
  needs `primary_scoring_target` / `secondary_supporting_targets[]` / `duplicate_scoring_block` /
  `independence_rule_id`. Secondary mappings inform interpretation/confidence, not extra severity.
- **Score contract** — every score carries formula id/version, inputs used, missing components, coverage,
  confidence, uncertainty, provisional/final.
- **Root-Driver confidence grading** — CONFIRMED / PROBABLE / POSSIBLE_ROOT_DRIVER / COMPENSATORY /
  DOWNSTREAM / PROTECTIVE / NOT_YET_ASSESSABLE, with supporting/contradicting/missing evidence.

**Data-model correctness**
- **Ontology vs patient-assessment separation** — different tables/schemas; CELA→A34 (ontology) ≠ CELA
  active in *this* patient (assessment).
- **null ≠ 0 ≠ false ≠ NOT_APPLICABLE ≠ NOT_ASSESSED** — enforced at DB / API / scoring / UI / report.
- **Persistent, versioned Patient Biological Model** alongside immutable analysis runs, with explicit
  transition reasons (NEW_EVIDENCE / CLINICIAN_OVERRIDE / REGISTRY_UPDATE / DATA_CORRECTION /
  OUTCOME_RESPONSE / CONTRADICTING_FINDING / ALGORITHM_UPDATE).
- **Mapping-status ladder** — AUTO_SUGGESTED → CANDIDATE → CLINICALLY_REVIEWED → APPROVED → REJECTED;
  string/embedding/LLM matches may only *suggest*, never authoritative.
- **Source-priority rule** — corrected 39-axis list > key correction > 9-step list > final architecture >
  N1–N180 atlas > older narratives > legacy module lists (label those `MIGRATION_REFERENCE_ONLY`); 180
  networks is canonical (an old infographic's "160" is superseded).

**Safety & pipeline**
- **Two-stage safety** — preliminary eligibility gate *before* ranking (we have this) **+ a new
  regimen-level combination review** *after* selection (ingredient/mechanism duplication, additive
  bleeding/glucose/BP, hepatic/renal burden, pill burden). Contraindicated modules never get a visible rank.
- **Network edges with context + time** — expanded schema (clinical/population/tissue context, temporal
  pattern, time-lag, reversibility, dose dependency) and 10 edge types; only causal/regulatory/activating/
  inhibitory/compensatory edges may affect scoring; associative/hypothetical display only.

**Reporting & release**
- **Statement-level provenance** + an **unsupported-statement detector** that removes or labels
  `HYPOTHESIS — NOT USED FOR SCORING` before release.
- **Report content specs** for Physician / Patient / Multi-Omics; **no simulated omics** — when omics are
  absent, produce an "Omics Data Readiness Report."
- **Release-state ladder** (INTERNAL_TEST … APPROVED_FOR_PATIENT_RELEASE / REJECTED / WITHDRAWN),
  fail-closed; nothing from a provisional/unapproved registry may reach patient release.
- **Cross-report consistency validator** at the structured-data level (not just wording).

**Operations & validation**
- **Registry dependency graph** — every report linked to all registry+algorithm versions; identify all
  affected analyses/reports/patients if a registry is withdrawn.
- **Rollback / withdrawal / clinical incident management** — required before the pilot.
- **Separate technical vs clinical monitoring** metrics.
- **Clinician-authored gold-standard regression suite** (thalassemia vs iron deficiency, critical result
  with low NSS, pregnancy, renal/hepatic impairment, contraindicated module, legacy-axis conflict, etc.) —
  our 71 technical tests are necessary but do **not** establish clinical validity.
- **Physician shadow pilot** — clinician-facing, no auto-prescribe/release, with defined agreement/miss-rate
  metrics; **patient release only after formal approval**.
- **Clinician UI** must show Severity / Confidence / Completeness / Coverage / Uncertainty / Evidence
  Status / Grade separately; **structured clinician overrides** with reason codes and `eligible_for_learning`.

## 6. Bottom line & impact on our plan

- **Resolves** the NSS/completeness decision (now final) → one **code change** to NSS (drop completeness
  as a severity weight; add state-based inclusion + the full NSS output object).
- **Approves** CELA and six refinements → small updates (adopt `TSPI-NET-####`, mark CELA APPROVED).
- **Canonicalises** A10 sub-axes and the S1–S9 step list → build those two small registries.
- **Corrects** the network-match path → add a **Module-to-Network Claim Registry** to the plan; the
  crosswalk alone does not activate the 25%.
- **Adds** a substantial governance/validation layer (evidence de-dup, two-stage safety, provenance +
  unsupported-statement detector, release states, dependency graph, incident management, clinician
  gold-standard tests, shadow pilot). These become the **pre-production checklist** — they don't change
  what's built, they define what must exist before a pilot.
- **Does not deliver** the still-pending approved data (Module rows, full crosswalk, edges, clinical
  registries). Fastest route (their §Final): approve Module remap → complete crosswalk → edge registry →
  Module-to-Network claims → clinical registries → lock NSS → gold-standard tests → shadow pilot.

*Action for us next: rework NSS per §2, adopt the CELA/A10/9-step canonical records, and fold the new
requirements into the implementation plan and PROJECT_STATUS (the §4c decision is now closed).*
