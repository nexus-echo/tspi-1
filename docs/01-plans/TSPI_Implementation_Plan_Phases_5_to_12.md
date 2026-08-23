# TSPI AI Engine — Implementation Plan (Phases 5–12)

*All changes required by the domain-expert feedback, grouped into phases with dependencies.
Phases 0–4 (knowledge foundation, deterministic core, RAG, safety/validation, learning) are already
built and tested — this plan covers what the expert rulings now require **on top of** that.*

**Governing principle (expert, Part 6 + Final Developer Lock):**
> *"The engine does not need to be rebuilt from zero. It needs the latest ontology frozen, the legacy
> mappings removed, and the Clinical Phenotype, Red-Flag and 180-Network layers added around the
> existing foundation."*

> ### ✅ Update — 25 Jul 2026 answers (`answer tspi 25.07.2026.pdf`)
> **All 5 open questions are RESOLVED, and the legacy→current axis mapping decisions were delivered
> (partially breaks Blocker 1).** Impact on this plan:
> - **NSS (Phase 10):** per-axis weight = **Confidence × Data Completeness × Evidence Quality** (was
>   Confidence-only) → v0.2. Weighted average, never a literal multiply against the final NSS.
> - **Phenotype (Phase 8):** confirmed **Option A** — named, versioned Phenotype Registry; we may
>   propose it as `CANDIDATE` for expert approval.
> - **Marker Registry (Phase 6):** split `value_source_type` (MEASURED/DERIVED, `calculation_rule`)
>   from `direction_rule` (LOWER_BETTER / HIGHER_BETTER / **TARGET_RANGE** / CONTEXT_DEPENDENT);
>   U-shape becomes a `curve_type`, not a direction. Ferritin inflammatory axis = **A1** (A34 typo).
> - **Contraindications (Phases 10/11):** author **inside the Module**; auto-generate Contraindication
>   + Drug-Herb registries as **views**. Gate outputs PASS / PASS_WITH_MONITORING / HOLD /
>   CONTRAINDICATED / INSUFFICIENT_SAFETY_DATA.
> - **Phase 11:** now actionable — official legacy→current mapping tiers supplied (see Phase 11).

---

## Status legend

| Mark | Meaning |
|---|---|
| 🟢 | Pure code — **no external data needed, can start now** |
| 🟡 | Code now, **data arrives later** (build loader + schema against placeholder) |
| 🔴 | **Blocked** — cannot complete without client data |
| ✅ | Already done |

---

# PHASE 5 — Ontology Freeze & Version Enforcement 🟢

*Foundation. Everything downstream depends on the frozen ontology.*

| # | Change | Notes |
|---|---|---|
| 5.1 | ✅ **Axis Master v2** installed (`39-axis-master-260715`), A35–A39 corrected, A10 sub-axes, key mapping | done |
| 5.2 | ✅ **Domain→Key Master v1.0** installed | done |
| 5.3 | ✅ **Legacy module map quarantined** (`production_allowed: false`) | done |
| 5.4 | **Dataset envelope** on every master file: `dataset_name, dataset_version, framework_version, effective_date, approval_status, reviewed_by, approved_by, change_log, supersedes_version, status` | expert-specified |
| 5.5 | **Version-mismatch rejection**: `if dataset.axis_master_version != active_axis_master.version → reject_dataset(AXIS_MASTER_VERSION_MISMATCH)` | expert gave the rule verbatim |
| 5.6 | **Status gate**: `DRAFT`/`PROVISIONAL` datasets must never silently enter production; allowed = `APPROVED` (or `CLINICALLY_REVIEWED` in controlled testing) | |
| 5.7 | Sub-axis model: sub-axes for **evidence/scoring within** an axis; modules map to **parent axes**; optional `sub_axis_tags` refine ranking only | Q8 |
| 5.8 | Deprecate old axis concepts explicitly (`SUPERSEDED_BY_LATEST_AXIS_MASTER`) rather than deleting | audit/lineage |

**Deliverables:** `dataset_envelope.py`, `version_guard.py`, updated `validate_master.py`.

---

# PHASE 6 — Evidence & Confidence Model 🟢

*The four dimensions the expert requires on **every** conclusion. Also a prerequisite for the
official NSS formula (which needs `Confidence_i`).*

| # | Change | Notes |
|---|---|---|
| 6.1 | **Evidence Status** enum: `MEASURED / DERIVED / CLINICAL_INFERENCE / HYPOTHESIS / NOT_AVAILABLE` | how a statement was produced |
| 6.2 | **Evidence Grade** enum: `A / B / C / D` — **separate field**, stored per *module + claim + target axis/network*, not one global grade | Q7/Q10 |
| 6.3 | **Confidence** 0.00–1.00 (Very High → Very Low) — from evidence consistency, quality, specificity, independent sources, longitudinal consistency, contradictions, confounders. **Not** just a count of data points | |
| 6.4 | **Data Completeness** = *weighted*: `Σ weight(available) ÷ Σ weight(expected)` with `CORE=3, SUPPORTING=2, OPTIONAL=1`. Missing a CORE marker must **not** yield high completeness | expert explicitly rejected the raw ratio |
| 6.5 | **Biological Uncertainty** 0.00–1.00 — how many alternative biological models remain plausible. **Distinct from Confidence** | new 4th dimension |
| 6.6 | **Hard rule:** `HYPOTHESIS` must never raise Axis score, Network score, NSS or Module Match. It may only generate a follow-up question, suggest an investigation, stay in the differential, or display with uncertainty | anti-hallucination |
| 6.7 | **Axis status** enum: `POSSIBLE / PROBABLE / HIGH_CONFIDENCE / NOT_ASSESSED` + `reason` | Q9 |
| 6.8 | **`NOT_ASSESSED` is explicit** — unscored axes must appear with `score=null, status=NOT_ASSESSED, confidence=INSUFFICIENT_DATA, reason=...`. **No data must never be read as normal**, and never defaulted to 50 | fixes our "silently absent" gap |
| 6.9 | **Marker Registry (25 Jul):** each marker carries `value_source_type: MEASURED\|DERIVED` (with `calculation_rule, formula_version, required_inputs[], validation_range` when DERIVED) **separate from** `direction_rule: LOWER_BETTER \| HIGHER_BETTER \| TARGET_RANGE \| CONTEXT_DEPENDENT`. `TARGET_RANGE` carries `lower/upper_optimal_bound` + `curve_type: LINEAR\|U_SHAPE\|J_SHAPE\|ASYMMETRIC` (U-shape is a curve, not a direction). **Ferritin inflammatory axis = A1** (A34 was a typo); ferritin is context-dependent (low→A26, high+CRP→A1, alone→no axis) | new — data pending |

**Touches:** `schemas.py`, `severity.py`, `axis_mapper.py`, `report_composer.py`, new `marker_registry`.

---

# PHASE 7 — Red-Flag Safety Layer 🟡

*Safety-critical. Must run **before** any network/axis/module reasoning.*

| # | Change | Notes |
|---|---|---|
| 7.1 | **Red-Flag Registry** schema + loader (`red_flag_code, symptom_area, action_class, required_action, release_block, module_plan_allowed, override_role, version, status`) | 🔴 needs official list |
| 7.2 | **Deterministic engine** — must **not** rely on the LLM reading free prose | expert explicit |
| 7.3 | **Class 1 Emergency**: `action=EMERGENCY_REFERRAL, release_block=true, module_plan_allowed=false` | |
| 7.4 | **Class 2 Urgent**: `release_block=true, module_plan_requires_clinician_override=true` | |
| 7.5 | **Class 3 Standard work-up first**: cause-specific plan blocked; supportive plan = clinician review only | |
| 7.6 | **Pipeline reorder**: `Symptoms → Red-flag → Standard medical differential → Clinical phenotype → Network → Axis → Module` | architectural |
| 7.7 | **Critical-value rules** as a *separate layer* — a critical alert must never be diluted by averaging (e.g. NSS 28 + critical K⁺ still urgent) | Round-2 Q2 |

---

# PHASE 8 — Clinical Phenotype Engine 🟡

*Our single biggest gap: symptoms are currently free text and scoring is lab-driven.*

| # | Change | Notes |
|---|---|---|
| 8.1 | **Structured symptom schema** (~24 fields: `symptom_code, onset, duration, frequency, severity, progression, location, quality, triggering/relieving factors, meal/bowel/sleep/stress/activity relationships, circadian_pattern, functional_impact, associated_symptoms[], negative_findings[], red_flags[]`) | replaces `symptoms: str` |
| 8.2 | **Symptom clusters** (e.g. upper-digestive cluster, intestinal-motility cluster) | |
| 8.3 | **Symptom→Axis + Symptom→Network dictionary** loader | 🟡 provisional dict built; official pending |
| 8.3b | **Phenotype Registry (Option A — CONFIRMED 25 Jul):** named, versioned patterns. Schema: `phenotype_code, phenotype_name_en/th, required_features[], supporting_features[], exclusion_features[], red_flag_overrides[], candidate_axis_codes[], axis_evidence_weights, minimum_feature_count, confidence_rule, status, version, approved_by`. Restructure engine to **Symptom→Phenotype→Axis**; whole system still enters from **integrated Clinical Evidence**. We may propose the initial registry as `status=CANDIDATE` for expert approval; AI-learned phenotypes may be *proposed*, never published | 🟢 build now |
| 8.4 | **Probabilistic weighting**: base 0.25 / 0.50 / 0.75 / 1.00, adjusted by co-symptoms, timing, triggers, relieving factors, objective findings, negative tests, confounders, longitudinal consistency | never 1 symptom = 1 axis |
| 8.5 | **Adaptive clinical questioning** — ask to discriminate between candidate networks | |
| 8.6 | **Negative-test interpretation rules** — a normal test narrows the differential, never erases a symptom | |
| 8.7 | **Separate symptom burden from attribution confidence** (severity 8/10 ≠ confident mechanism) | |

---

# PHASE 9 — 180 Living Biological Networks 🔴/🟡

*Mandatory architecture per the expert — the layer the system is supposed to reason **in**.*

| # | Change | Notes |
|---|---|---|
| 9.1 | **Network Master** schema + loader (~25 fields incl. `primary_axis_code, upstream/downstream, feedback_relationships, accepted_symptoms, network_type` from a 16-value enum) | 🔴 needs structured CSV (found in PDF pp.61–81 but not reliably extractable) |
| 9.2 | **39↔180 fixed mapping table** | |
| 9.3 | **Network propagation + root-driver analysis at network level** — repoint our existing PageRank `graph_engine` from axes to networks (right machinery, wrong layer today) | reuses existing code |
| 9.4 | **Root driver classes**: `CONFIRMED / PROBABLE / POSSIBLE_ROOT_DRIVER / NOT_YET_ASSESSABLE` | |
| 9.5 | **Compensatory network handling** — must first decide harmful vs protective; do not auto-suppress | |
| 9.6 | **Bidirectional reasoning**: clinical inference (symptoms→networks→axes) **and** biological explanation (network→symptoms→labs→structure→disease) | Part 6 |
| 9.7 | **Anti-hallucination**: `if network_code not in official_registry → evidence_status=HYPOTHESIS, scoring_effect=0, display=UNRESOLVED_NETWORK_HYPOTHESIS` | verbatim rule |
| 9.8 | **CELA as Network #120**, parent axis A34 — never as A39 | |

---

# PHASE 10 — NSS v0.1 & Module Match v1.0 🟢

| # | Change | Notes |
|---|---|---|
| 10.1 | **NSS v0.2 (CANONICAL, 25 Jul):** per-axis `AxisWeight = Confidence × Data Completeness × Evidence Quality`; `BaseNSS = Σ(Severity × AxisWeight) ÷ Σ(AxisWeight)`; `FinalNSS = BaseNSS × NetworkFactor`, capped. **Weighted average — never multiply the factors against the final NSS** (a severe patient with sparse data must stay severe). Extends our shipped v0.1 (which weighted by Confidence only). Safeguards: NOT_ASSESSED excluded from num+denom, missing marker ≠ severity 0, HYPOTHESIS no score, red flags survive low NSS | **update v0.1 → v0.2** |
| 10.2 | **NetworkFactor**: 0–2 abnormal axes ≥50 → 1.00; 3–5 → 1.05; ≥6 → 1.10. `FinalNSS = min(100, Raw × Factor)` | |
| 10.3 | **Version flag** `nss_algorithm_version = "TSPI-NSS-v0.1"`; coefficients configurable, not hard-coded | |
| 10.4 | **No blanket inflammation ×1.3** — allowed as provisional test rule only, never a universal law | expert warning |
| 10.5 | **Missing data ≠ normal**; critical alerts survive independently of NSS | |
| 10.6 | Keep level bands 0–15/16–30/31–60/61–100 (provisionally retained) | |
| 10.7 | **Module Match v1.0**: 30% axis + 25% network + 15% evidence grade + 10% phenotype fit + 10% safety + 5% step compatibility + 5% historical response | approved as v1.0 |
| 10.8 | **Safety = GATE not score**: absolute contraindication/major interaction → `module_status=EXCLUDED`, `module_match_score=not_calculated`. Do **not** merely subtract 10 | important correction |
| 10.9 | **Module-count ceiling**: typical 1–3 core + 0–3 supporting (**max ~6**); 7–8 needs senior approval; >8 needs justification + dedup + interaction review. *Matching ≠ prescribing* | fixes our 64-module output |
| 10.10 | **Mechanism de-duplication** — pick highest-ranked representative | |
| 10.11 | **`reason_not_selected`** enum (10 values incl. `DUPLICATE_MECHANISM`, `EXCESSIVE_MODULE_BURDEN`, `DIAGNOSTIC_WORKUP_REQUIRED_FIRST`) | |
| 10.12 | **Dosing safeguard**: NSS guides default dose but must never override module-specific rules, contraindications, renal/hepatic impairment, age, physician judgment, or the bowel group | |

---

# PHASE 11 — Module Registry Remap 🟡 *(now actionable — official mapping delivered 25 Jul)*

*The 25-Jul answers supply the semantic legacy→current axis mapping. We can **auto-convert the safe
tiers** and **quarantine the rest** with proper provenance — instead of waiting for a fully corrected file.*

| # | Change | Notes |
|---|---|---|
| 11.1 | **New `data/legacy_axis_map.json`** — the official conversion table (below), version-stamped to `39-axis-master-260715` | authoritative reference |
| 11.2 | **`conversion_type` enum:** `EXACT_SEMANTIC_MAPPING / RENAMED_REFINED / SPLIT_REQUIRES_REVIEW / CONTEXT_DEPENDENT / DEPRECATED_TO_NETWORK / NO_DIRECT_EQUIVALENT / SAME_NUMBER_DIFFERENT_MEANING` | expert's exact set |
| 11.3 | **`build_registry.py` converter:** apply legacy→current using `legacy_axis_map.json`. **Bulk-convert ONLY** `EXACT_SEMANTIC_MAPPING` + `RENAMED_REFINED`. Everything else → `mapping_status=REQUIRES_SEMANTIC_REVIEW` (stays quarantined) | expert rule |
| 11.4 | **Per-module provenance (required):** `legacy_axis_number, legacy_axis_name, current_axis_codes[], conversion_type, conversion_confidence, mapping_status, reviewed_by, review_date, axis_master_version` | expert-specified |
| 11.5 | **`mapping_status` gate:** production accepts `APPROVED` only (`CLINICALLY_REVIEWED` in controlled testing) | unchanged |
| 11.6 | **Per-module review sheet** for the quarantined mechanism cases (Metabolic Balance, Cancer Surveillance, Liver, Oncology) → hand to experts, same pattern as before | needs mechanism review |
| 11.7 | Rebuild `axis_module_official.json` from converted+approved rows; **lift quarantine incrementally** as tiers get approved | partial un-block |

### Official legacy → current mapping (from `answer tspi 25.07.2026.pdf`)

**Tier A — bulk-convert now** (`EXACT_SEMANTIC_MAPPING` / `RENAMED_REFINED`):
`16→A15 · 17→A16 · 18→A17 · 19→A18 · 21→A20 · 25→A24 · 29→A28 · 32→A31` ·
`2→A17 · 3→A9 · 5→A1 · 18(Longevity)→A13 · 28→A26 · 33→A34` ·
`37→A10 · 38→A10` (Proteostasis, confirmed) · `35(Organ Resilience)→A35` (RENAMED_REFINED).

**Tier B — QUARANTINE, per-module mechanism review** (`SAME_NUMBER_DIFFERENT_MEANING` / `SPLIT_REQUIRES_REVIEW` / `CONTEXT_DEPENDENT`):
- **27 "Metabolic Balance" → NOT A27** (A27 is now Glycation) → review to A5/A6/A7/A8/A9/A13 ⚠ *the silent-error case*
- **19 "Cancer Surveillance" → NOT A19** → A37 (apoptosis/cell-cycle) or A38 (immune-evasion) by mechanism
- **13 "Liver"** → A35 generic; +A15/A6/A9/A24/A25/A1 by demonstrated mechanism
- **36 "Oncology"** → A37/A38/A39 by mechanism, never auto-defaulted
- **Kidney → A35** candidate (broad organ-reserve; add vascular/fibrosis/detox axes only on evidence)

**Tier C — deprecated to network** (`DEPRECATED_TO_NETWORK`):
- **39 "CELA"** → `target_axis_code=A34` + `supporting_network=CELA #120` (never A39)

**Production rule (verbatim):** *no blind numerical conversion; the current axis's biological meaning —
not the legacy number — determines the mapping. The 39 axes remain the module-matching layer; the
180 networks explain mechanism only.*

---

# PHASE 12 — Learning Rework (compliance fix) 🟢

*Our current global auto-recalibration is **non-compliant** and must change.*

| # | Change | Notes |
|---|---|---|
| 12.1 | **Level 1 — patient-specific axis adaptation**: bounded **±5% per cycle, ±20% cumulative**; require **sustained** improvement (≥2 consecutive) before relaxing; worsening only counts if clinically meaningful, reliable, repeated and unconfounded | |
| 12.2 | **Level 2 — network behaviour learning**: which network moved first, which downstream followed, time-to-response, magnitude, repeatability, confounders. *"What the AI learns is not disease — it is the behaviour of biological networks."* | new learning target |
| 12.3 | **Level 3 — versioned Patient Biological Model** (v1→v2→v3). Every meaningful input reconstructs it; new evidence may `CONFIRM/REFINE/REDIRECT/OVERRIDE/CONTRADICT`. **Old models never deleted** (audit) | replaces one-shot reports |
| 12.4 | **Population learning = `PROPOSE_MODEL_UPDATE` only** — requires sample size, data-quality + confounder review, statistics, clinical review, validation, version approval | **removes our auto-update** |
| 12.5 | Learning record schema (~18 fields incl. adherence, confounders, `learning_approval_status`) | |

---

# PHASE 13 — Reports & Output 🟡

| # | Change | Notes |
|---|---|---|
| 13.1 | **Network Harmonization Plan — 13 sections** (context → red flags → phenotype → differential networks → root drivers → compensatory → axis integration → priorities → modules → lifestyle → expected response → monitoring → model update) | expert-specified |
| 13.2 | **4 communication levels**: Confirmed / Probable / Not Yet Known / Suggested Next Tests — in **both** physician and patient reports | |
| 13.3 | **Nuanced module rule**: cause-specific modules blocked until cause confirmed, **but** low-risk supportive harmonization may show with explicit uncertainty + physician approval + the prescribed disclaimer wording | not an absolute ban |
| 13.4 | **3 Keys / 12 Domains / 9-Step** rollups + dashboards | |
| 13.5 | **Vocabulary shift** → Network Harmonization, Adaptive Compensation, Biological Resilience, Network Plasticity (not treat/correct/reduce) | |
| 13.6 | **Bilingual**: Thai default patient-facing (`locale th-TH`), English canonical internally; `technical_term_mode = Thai + English in parentheses` | |
| 13.7 | Lifestyle/environmental harmonization as **network-level interventions**, not "tips" | |

---

## Dependency map

```
PHASE 5 (ontology freeze) ──┬─> PHASE 6 (evidence model) ──┬─> PHASE 10 (NSS + Module Match)
                            │                              │
                            ├─> PHASE 7 (red flags) ───────┤
                            │                              │
                            ├─> PHASE 8 (phenotype) ───────┤
                            │                              │
                            └─> PHASE 9 (180 networks) ────┴─> PHASE 13 (reports)
                                                            
PHASE 11 (registry remap)  — NOW ACTIONABLE (official legacy→current mapping delivered 25 Jul)
PHASE 12 (learning)        — independent, pure code
```

**Phase 6 is the keystone:** NSS v0.1 needs `Confidence_i`, and Module Match needs Evidence Grade.

---

## Recommended sequence

| Order | Phase | Why | Blocked? |
|---|---|---|---|
| 1 | **6 — Evidence model** | keystone; unblocks NSS + Module Match; kills "no data = normal" | 🟢 no |
| 2 | **12 — Learning rework** | we are currently **non-compliant**; pure code | 🟢 no |
| 3 | **7 — Red flags** (engine) | safety-critical; build engine now, load list when it arrives | 🟡 partial |
| 4 | **10 — NSS + Module Match** | fixes the 64-module problem + heuristic NSS | 🟢 no |
| 5 | **5.4–5.8 — Version guards** | prevents another legacy-data incident | 🟢 no |
| 6 | **8 — Phenotype engine** | biggest clinical gap; schema now, dictionary later | 🟡 partial |
| 7 | **9 — Network layer** | **master verified & loaded** (`networks_180.csv` → `tspi_networks_180.json`); network→axis/domain **crosswalk drafted** (`network_axis_crosswalk_DRAFT.csv`, 141 labels) — **awaiting clinician confirm** before `network_match` scores; propagation edges still pending | 🟡 crosswalk pending |
| 8 | **13 — Reports** | consumes everything above | 🟡 |
| 9 | **11 — Registry remap** | **now actionable** — build `legacy_axis_map.json` + converter; auto-apply Tier A, quarantine Tiers B/C; lift quarantine incrementally | 🟡 partial |

*Post-25-Jul re-prioritisation:* Phase 11 moves up — it now unblocks real module recommendations for
the safe tier. Recommended near-term order: **NSS v0.2 update (10.1) → Phase 11 converter (Tier A) →
Phenotype Registry (8.3b) → Phase 9 networks**.

---

## Data still required from the client

| Item | Blocks |
|---|---|
| Module Registry with **current** axis codes (`mapping_status=APPROVED`) | Phase 11 |
| ~~**180-Network master** as structured CSV~~ ✅ **DELIVERED & VERIFIED** (`networks_180.csv`) | Still pending for Phase 9: **network→axis/domain crosswalk sign-off** (`network_axis_crosswalk_DRAFT.csv`) + **upstream/downstream edges** (propagation) |
| **Symptom→Axis / Symptom→Network dictionary** | Phase 8 |
| **Red-Flag list** | Phase 7 |
| **Marker Registry + lab cut-offs** | Phase 6 thresholds |
| **`minimum_evidence`** per axis | Phase 6 |
| A10 **sub-axis codes** | Phase 5 |

---

## What is explicitly retained (expert endorsed)

Deterministic scoring pipeline · official-registry-only module resolution · physician approval gate ·
de-identification + audit · versioned architecture · data-driven loaders. **No rebuild from zero.**
