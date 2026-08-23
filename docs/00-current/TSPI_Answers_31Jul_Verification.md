# Verification — Final Domain-Expert Response of 31 Jul 2026

*Source: `TSPI AI Engine answer 31.07.2026.pdf` (34 pages). This is the **complete official response**
to `TSPI — Data Request to Complete Project`. Verified line-by-line against the frozen axis master
(`39-axis-master-260715`), the 25 Jul answers, and the current engine code.*

---

## 1. Headline

**Every remaining open question is now answered, and all five code changes we shipped after 25 Jul are
explicitly confirmed correct.** The document goes further: it is a full *constitutional spec* — 25
non-negotiable directives plus a mandatory pre-production acceptance-test list. Nothing in it
contradicts our architecture; it **tightens several data models** and **adds new registries** needed to
finish the project.

| | Item | Status |
|---|---|---|
| ✅ | All 5 decision changes (NSS, marker model, ferritin, Phase 11, phenotype) | **confirmed correct** |
| 🟡 | 8 data-model refinements to what we built | small, listed in §3 |
| ⬜ | ~12 new registries / controls to build | listed in §4 |
| ⚠ | 1 subtle tension to reconcile (completeness-weighting vs "severity must not drop") | §5 |
| ◆ | Both blockers | rules fully specified; **data/approval still pending** |

---

## 2. What is confirmed correct (no change needed)

**NSS is a weighted average, not a product.** Directive 7 restates it forcefully: *"A severe abnormality
with incomplete evidence remains severe, but uncertain… data quality affects the reliability of the
assessment, not the biological direction."* Our **NSS v0.2** matches the confirmed formula. *(One
nuance to double-check — see §5.)*

**Marker model.** `value_source_type` (MEASURED/DERIVED) is confirmed **separate** from `direction_rule`
(§6.1). Direction rules are exactly the four we used; **U-shape is a `curve_type` under TARGET_RANGE,
not a top-level rule** (§6.2). Both match `app/markers.py` and `data/marker_registry.json`.

**Phase 11 converter.** The seven conversion types are **identical** to ours, and only
`EXACT_SEMANTIC_MAPPING` + `RENAMED_REFINED` may be batch-approved — which is exactly our
`AUTO_TYPES` set. The legacy-A27 "Metabolic Balance vs Glycation" trap is called out as the canonical
`SAME_NUMBER_DIFFERENT_MEANING` case, which our converter already quarantines.

**Phenotype Registry — Option A confirmed.** Named, versioned, `status=CANDIDATE`, dev-proposed; fields
match ours exactly. (Scope note in §3.)

**Retained safeguards are now permanent regression requirements.** Deterministic engine, no LLM axis
scores, official-registry-only resolution, **no default 50**, explicit `NOT_ASSESSED`, separate Evidence
Status vs Grade, weighted completeness, red-flag-first, safety-as-a-gate, propose-only learning, version
stamping — all named and locked. Our build already implements every one of these.

---

## 3. Refinements required to what we already built

These are small, surgical changes — the architecture is right, the data shapes tighten.

**3.1 Ferritin — set a primary axis.** The official mapping is **Primary = A26 (Stem Cell &
Hematopoiesis)**, **Secondary = A1** when an inflammatory context is present. We currently set
`primary_axis: null` and route entirely by context. *Change:* set `primary_axis: "A26"`, keep A1 as the
inflammatory-context secondary, keep "high ferritin alone → assert nothing." The A34-typo correction is
reconfirmed.

**3.2 HOMA-IR is unit-specific.** The formula differs by glucose unit: `÷ 405` for mg/dL, `÷ 22.5` for
mmol/L, and **units must be validated before calculation** (§6.1). Our registry has only the mg/dL form.
*Change:* store both formula variants + a unit-validation guard.

**3.3 Network `network_code` must be a stable identity, not a padded number.** Directive 10 + §4.2:
keep **three** fields — `network_code` (permanent, e.g. `LBN-DET-PHASE1`), `network_number` (display
order 1–180), `legacy_display_id` (`N033`). Our `build_networks.py` currently sets
`network_code = f"N{num:03d}"`, which the ruling explicitly forbids. *Change:* rename our `N###` to
`legacy_display_id`, add a stable `network_code`.

**3.4 Network Domain is derived from the primary axis, not authored.** §4.3 + Directive 11:
`primary_domain_code = AxisRegistry[primary_axis_code].domain_code`. Our builder currently maps domain
from the CSV's free-text domain label independently. *Change:* drop the independent domain mapping;
derive domain from the confirmed primary axis. **This simplifies Blocker 2b** — the
`CONFIRM_domain_num` column becomes review-only, not a source of truth.

**3.5 The 25% network component is *validation coverage*, not candidate generation.** §5 + Directive 9:
the pipeline is Axis → Axis-to-Module candidates → Safety → **Network mechanistic validation** →
research → ranking. Networks must never generate module candidates. When network data are incomplete,
emit `network_validation_status = NOT_ASSESSED` and show a **Validated Score Coverage %** — do **not**
enter 0 and do **not** renormalise. *Change:* reframe `module_match`'s network term as
`network_validation_status` + coverage, confirm it isn't a candidate source.

**3.6 Axis assessment states.** The official five states are `NOT_ASSESSED`, `AXIS_CANDIDATE`,
`PROVISIONALLY_ASSESSED`, `ASSESSED`, `HIGH_CONFIDENCE_ASSESSED` (§10). Our `AxisStatus` enum uses
`HIGH_CONFIDENCE / PROBABLE / POSSIBLE / NOT_ASSESSED`. *Change:* align the enum to the official five.

**3.7 Evidence Grade is per Module+Claim+Target+Source, and "not graded" ≠ D.** §8 + Directive 13: do
**not** default ungraded modules to D — use a distinct `EVIDENCE_NOT_GRADED` value. Grade attaches to a
claim, not a whole module. *Change:* add `EVIDENCE_NOT_GRADED`; model grading at claim/target level
(a Research Claim Registry, see §4).

**3.8 Safety is categorical, not a score.** Directive 8: use `PASS / PASS_WITH_MONITORING / HOLD /
CONTRAINDICATED / INSUFFICIENT_SAFETY_DATA`, evaluated before ranking. Our safety is already a hard
exclusion gate; *change:* surface these five categorical outcomes rather than a boolean/score.

---

## 4. New deliverables the response requires

Schemas are specified in the PDF; we build loaders + candidate data, expert approves.

- **Module Registry (Blocker 1)** — expanded fields: `legacy_axis_number/name`,
  `candidate_current_axis_codes[]`, `conversion_type/confidence`, `mapping_reason/status`,
  `primary_restoration_step` + `secondary_restoration_steps[]`, `contraindications[]`,
  `drug_herb_interactions[]`, `evidence_status/grade`, `axis_master_version`, `reviewed_by/date`.
  Production gate: `mapping_status=APPROVED` ∧ `axis_master_version=39-axis-master-260715` ∧
  `production_allowed=true`; else display "PROVISIONAL CANDIDATE — NOT FOR CLINICAL USE."
- **Network Registry** — `primary_axis_code` (exactly one), `secondary_axis_codes[]`, `network_name_th`,
  `mapping_reason/confidence/status`, `axis_master_version`, plus the stable-code fields (§3.3).
- **Network Edge Registry (Blocker 2c)** — `source/target_network_code`, `edge_type`
  (ACTIVATES/INHIBITS/REQUIRES/COMPENSATES/PROPAGATES_TO/RESTORES/FAILURE_PRECEDES/ASSOCIATED_WITH),
  `direction`, `biological_effect`, `context`, `evidence_status/grade`, `source_reference`,
  `confidence`, `mapping_status`, `version`. AI may propose edges, never publish them.
- **Laboratory Cut-off Registry** — population/sex/age/pregnancy/fasting/assay-specific bands
  (OPTIMAL/SUBCLINICAL/FUNCTIONAL_DISTURBANCE/PATHOLOGICAL/CRITICAL). No universal global cut-off.
- **Per-Axis Minimum-Evidence Registry** — `core/supporting/optional_evidence[]`, `minimum_core_count`,
  `minimum_total_weight`, `required_modalities[]`, `exclusion_rules[]`, `allow_provisional_assessment`;
  weights CORE=3/SUPPORTING=2/OPTIONAL=1; all 39 as `CANDIDATE_FOR_EXPERT_REVIEW`.
- **Phenotype Registry — ~30 core phenotypes** (we scaffolded 4; expand to ≈30 candidates).
- **Nine Restoration Steps (official names, locked):** Detoxification · Microbiome Restoration ·
  Immune–Inflammatory Regulation · Redox Homeostasis · Metabolic and Mitochondrial Restoration ·
  Autophagy and Cellular Clearance · Genomic Stability · Genomic Regulation Homeostasis · Prakati.
- **Reports (Phase 13):** Thai-first bilingual; Physician / Patient / Multi-Omics reports all read from
  **one immutable Analysis Object** carrying `analysis_run_id` + every registry/calculation version; a
  **Cross-Report Consistency Validator** runs before release; draft watermark until physician e-approval.
- **Supporting registries/controls named in §5.4 + directives:** Axis Registry version lock,
  Research Claim Registry, Clinical Outcome Definition Registry, Imaging Evidence Registry,
  Medication/Exposure Registry, Drug–Herb Interaction Evidence Registry, Unit/Assay Normalisation
  Registry, Data Provenance IDs, Patient Identity & Data-Integrity Gate, Temporal/Longitudinal Patient
  Model, Reasoning Ledger, Contradiction Engine, Biological Truth Validation Layer, Physician Electronic
  Approval.
- **Entity reconciliation:** explicitly separate **Biological Module** (≈200) vs **Commercial
  Product / H-Code** (242) vs **Phytocore** — and note the template's 145 pre-listed entries are none of
  those three counts. Our ontology must model the three as distinct entities.

---

## 5. ⚠ One tension to reconcile

The 25 Jul answer defined `AxisWeight = Confidence × Data Completeness × Evidence Quality` **inside** the
NSS weighted average (which we implemented). Directive 7 (31 Jul) states that **low confidence or
completeness must never make a severe axis look biologically mild** — data quality changes *reliability*,
not *severity*.

For a *single axis* these agree (we keep severity and report confidence separately). For the *aggregate
NSS*, using completeness as a weight means a poorly-evidenced severe axis contributes less to the mean,
which **can lower the aggregate** relative to an unweighted severity mean. That is arguably what
Directive 7 warns against.

**Our reading:** the weighting governs each axis's *contribution to the aggregate*, while per-axis
severity is preserved and surfaced with its own confidence — consistent with both documents. But because
this is the single subtlest point where the two expert documents can be read differently, **we should
confirm with the expert** whether NSS should (a) weight by completeness as today, or (b) compute severity
on an unweighted/confidence-annotated basis and express completeness only as "coverage." A one-line
answer settles it; until then NSS v0.2 stays behind its version flag.

---

## 6. Confirmed completion order (from §17)

1. Freeze Axis Master → 2. Generate candidate Module remap → 3. Approve Module Registry →
4. Review all 180 network rows → 5. Confirm each network's primary/secondary axes →
6. **Derive** domains from approved axes → 7. Build & approve Network Edge Registry →
8. Marker Registry → 9. Lab Cut-off Registry → 10. Grade evidence at claim+target level →
11. Map Modules to the 9 Steps → 12. Minimum-Evidence for all 39 axes →
13. Review red flags / symptoms / negative tests / thresholds → 14. Review first 30 phenotypes →
15. Deterministic validation + regression → 16. Physician-only pilot → 17. Patient reports only after
validation.

---

## 7. What we will do next (pending your confirmation)

**Implement now (unambiguous refinements from §3):** ferritin primary=A26; HOMA-IR unit-specific formula
+ unit guard; network `network_code`/`legacy_display_id` split; domain derived from primary axis;
`AxisStatus` → official five states; `EVIDENCE_NOT_GRADED`; categorical safety outcomes; reframe network
term as `network_validation_status` + coverage.

**Build as candidate registries (§4):** expanded Module Registry converter output; Network + Edge
Registry schemas; Lab Cut-off + Minimum-Evidence templates; expand phenotypes toward ~30; lock the 9
official step names.

**Hold for one expert confirmation:** the NSS completeness-weighting question in §5.

**Still blocked on data/approval:** the APPROVED Module Registry; the confirmed network primary/secondary
axes; the network edge list; and all clinical cut-off / evidence-grade content.
