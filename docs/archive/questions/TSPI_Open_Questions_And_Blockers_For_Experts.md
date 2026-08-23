# TSPI AI Engine — Open Questions, Blockers & Feedback on the Latest Files

**Prepared for:** the TSPI domain-expert team
**Status:** 1 hard blocker (now *partially* unblocked) · 1 data blocker (data verified — **axis/domain crosswalk still open**) · decision questions all resolved
**Purpose:** everything still needed from the clinical team, plus our feedback on the three files received 15 Jul 2026.

---

> ## ✅ UPDATE — 25 July 2026 (`answer tspi 25.07.2026.pdf`)
> **All open *decision* questions are now resolved. The two blockers have moved forward.**
>
> | Item | Before | After 25 Jul |
> |---|---|---|
> | **Blocker 1 — Module registry legacy numbering** | 🔴 hard-blocked | 🟡 **partially unblocked** — the **official legacy→current axis mapping** was delivered. We can now auto-convert the **Tier A** (safe, exact-semantic) set and **quarantine Tier B/C** for clinical sign-off. Full production still needs the `mapping_status=APPROVED` registry file. |
> | **Blocker 2 — 180-Network master** | 🔴 not machine-readable | 🟡 **data resolved, crosswalk open** — all **180 rows** extracted and **client-verified** (`networks_180.csv`); loaded into `data/tspi_networks_180.json`. **But** the CSV's `biological_axis`/`domain` columns are **free-text labels, not codes** (141 distinct axis labels vs 39 canonical axes; 29 domain labels vs 12). A **network→axis/domain crosswalk** is still needed before the network layer connects to the engine. *(Also: no upstream/downstream edges → propagation still deferred.)* |
> | **Ferritin axis** (was §4.1 error) | A34 (wrong) | ✅ **A1** — A34 was a typo; ferritin is context-dependent (low→A26, high+CRP→A1, alone→no axis). |
> | **NSS formula** (§4.2) | ambiguous | ✅ **Weighted average, NOT multiply.** `AxisWeight = Confidence × Data Completeness × Evidence Quality`; then `× NetworkFactor`. → engine on **NSS v0.2**. |
> | **Direction rules** (§4.3) | `derived_rule` dropped? | ✅ **Keep** — modeled as separate `value_source_type: MEASURED\|DERIVED`. **Optimal Range = U-shape** (one TARGET_RANGE family; U-shape is a `curve_type`). |
> | **Contraindications** (§4.4) | inside vs separate | ✅ **Author inside the module**; separate registries are **auto-generated views.** |
> | **Phenotype** (Q3) | undefined | ✅ **Option A — named, versioned patterns**; dev team proposes the registry (status=CANDIDATE) for review. |
>
> Plans updated accordingly: `TSPI_Implementation_Plan_Phases_5_to_12.md` (NSS v0.2 §10.1, Phenotype Registry §8.3b, Marker Registry §6.9, Phase 11 now actionable) and `TSPI_5_Open_Questions_Decision_Sheet.md` (all 5 marked RESOLVED).
>
> **Still outstanding:** the `APPROVED` module-registry file (to lift the Tier A/B/C quarantine), plus network **upstream/downstream edge data** (for propagation). The master-dataset content in §5 (marker cut-offs, evidence grades, per-axis minimum-evidence) is also still pending. *The original questions are preserved below for the record.*

---

## 1. Summary — where we are

Your Round-3 response resolved the **critical axis-dictionary conflict**, and we have already
re-based the engine on the new master. Five phases of engine work are complete and tested
(54/54 passing). **The engine is now blocked on data, not on decisions.**

| | Count | |
|---|---|---|
| ✔ | **13 of 13** Round-3 questions | answered and implemented |
| ◆ | **1** hard blocker | the updated module file still uses **legacy** axis numbering |
| ◆ | **1** data blocker | the 180-Network master is not machine-readable |
| ! | **12** open questions | mostly master datasets + confirmations |

---

## 2. Documents received (all read in full)

| Ref | File | Pages | Date |
|---|---|---|---|
| **[D]** | `tspi developer answer.pdf` | 3 | 9 Jul 2026 |
| **[C]** | `TSPI AI Engine — Domain Expert Answers for the Dev_260713_095402.pdf` | 22 | 13 Jul 2026, 09:54 |
| **[A]** | `tspi comment for phase3 developer _260713_104231.pdf` | 36 | 13 Jul 2026, 10:42 |
| **[B]** | `tspi comment for phase3 developer .pdf` | 55 | 13 Jul 2026, 11:17 |
| **[E]** | `TSPI 3 — Complete Domain Expert Response for the Development Team.pdf` | 30 | **15 Jul 2026** |
| **[F]** | `last 39 แกน 12 โดเมน กุญแจ 3 ดอก (1)_260715_110654.pdf` | 81 | **15 Jul 2026** |
| **[G]** | `200 module tspi 2 (10-7-69).th.en(1).th.en(4) แก้ไข.xlsx` | 966 rows | **15 Jul 2026** |

---

## 3. Feedback on the three latest files

### [E] Round-3 Complete Response — ✔ excellent, no issues

All 13 questions answered, and the **Final Developer Lock** gave us exactly what we needed to
proceed. Particularly valuable corrections we would not have arrived at ourselves:

- **Safety is a GATE, not a score** — we would have wrongly subtracted 10 points instead of excluding.
- **Data Completeness must be weighted** (CORE=3 / SUPPORTING=2 / OPTIONAL=1) — you explicitly
  rejected our `present ÷ expected` assumption. Correct: a missing CORE marker must not look "nearly complete".
- **Evidence splits into two fields** (Status *and* Grade) — we had conflated them.
- **Module ceiling ~6** — this resolved our 64-module output. "Matching is not prescribing" is now enforced in code.
- **Learning must be propose-only** — our Phase-4 loop was auto-updating the global model from single
  patients. That was a genuine compliance violation; it is now fixed.

**All of the above are implemented.** Nothing in [E] is disputed.

### [F] 39 Axes / 12 Domains / 3 Keys master — ✔ canonical, 2 observations

This is now our **frozen ontology** (`framework_version: 39-axis-master-260715`). The *"Key
Correction"* on p.41 independently confirms [E] — the two agree, which resolved the conflict.

Two things to be aware of:

1. **The file contains two different axis lists.** Pages **36–41** carry the corrected list
   (A35 = Visceral Organ Functional Reserve, A37 = Oncologic Cell Fate…). Pages **42–60** carry an
   **older detailed section** (A35 = "Organ Resilience & Functional Reserve"; A36–A39 absent) —
   *this older section is the one that contains the per-axis `Module:` lists*. **We used pp.36–41
   only.** → see **Q13**.
2. **The 180-Network table is in there** (pp.61–81) — genuinely good news, and we confirmed
   **CELA = network #120**. But it is a visual Thai/English prose table: our best automated
   extraction recovered only **102 of 180** rows with mixed-up columns, so we did **not** load it.
   → see **Blocker 2**.

### [G] Updated 200-module xlsx — ◆ **this is the blocker**

[E] Q2 states: *"The updated Official Module Registry will directly contain the correct current Axis
codes for every module."* **This file does not.** Verified programmatically across all 242 product codes:

| Check | Result |
|---|---|
| Rows using **legacy** axis numbering | **54** |
| Rows using **new** axis numbering | **29** |
| Rows **mixing both** | **2** |
| Axis numbers whose name disagrees with the master | **20 of 39** |
| Rows still containing deprecated **"Protein Quality Control"** | **21** |
| Rows still containing deprecated **"Protein Clearance / Proteotoxic Stress"** | **22** |
| Rows still containing deprecated **"Cognitive-Emotional Loop"** as an axis | **14** |

**Your own example, H-001 Curcuma, still reads:**
`Axis 16 – Liver Detoxification · Axis 17 – Digestive Function · Axis 18 – Microbiome Ecology ·
Axis 19 – Gut Barrier · Axis 21 – Endothelial Function · Axis 25 – Tissue Repair · Axis 27 – Metabolic Balance`
Under the master these should be **A15 · A16 · A17 · A18 · A20 · A24 · A27** *(and A27 changes meaning
entirely — legacy "Metabolic Balance" vs current "Glycation / Carbonyl Stress")*.

**H-006 BENCHAKUL still contains** `AXIS 37 Protein Quality Control System`,
`AXIS 38 Protein Clearance & Proteotoxic Stress`, `Axis 39 Cognitive-Emotional Loop` — the three
definitions [E] just deprecated.

Per your own rule, this file **cannot enter production**, so we have quarantined our module→axis map
(`production_allowed: false`). Module recommendations are therefore **not clinically usable** today.

---

# 4. ◆ BLOCKERS

## Blocker 1 — The module registry still carries legacy axis numbering  🟡 *partially unblocked (25 Jul)*

> **25 Jul update:** the official **legacy→current axis mapping** has now been delivered. We are
> building `data/legacy_axis_map.json` + a converter that **auto-applies the Tier A** exact-semantic
> mappings and **quarantines Tier B/C** (renamed/split/context-dependent) for your sign-off. This
> unblocks the *safe* subset. **A production-ready registry with `mapping_status=APPROVED` is still
> required** to lift the remaining quarantine.

**What we need:** an Official Module Registry where `target_axes` already contains **current**
A1–A39 codes, with `mapping_status = APPROVED`.

**Why we cannot fix it ourselves:** [E] Q2 is explicit — *"Do not use a blind numerical conversion
as the Production source of truth… Each legacy mapping must be reviewed semantically."* A numeric
shift would silently produce clinically wrong mappings (A27 is the proof: same number, different meaning).

**Question:** is a further-corrected registry coming — or would you like us to produce a
**candidate remap** (legacy → current, with `conversion_type` and confidence flags) for your team to
review and sign off? We can generate that within a day; it would still need clinical approval before use.

**Easiest format:** `module_code(H-Code), module_name, phytocore_code, target_axes[] (current codes),
dose_type, contraindications, evidence_grade, status, axis_master_version`.

## Blocker 2 — The 180-Network master  🟡 *data resolved · crosswalk + edges still open*

> **Data resolved:** all **180 rows** transcribed and **client-verified** (`networks_180.csv`,
> CELA=#120), now compiled into `data/tspi_networks_180.json` via `scripts/build_networks.py`.
>
> **Still open — the network↔axis/domain crosswalk.** The CSV's `biological_axis` and `domain`
> columns are **descriptive text labels, not codes.** There are **141 distinct axis labels** for the
> 39 canonical axes, and **29 domain labels** for the 12 domains. Until each label carries a
> canonical `A1–A39` (and `D1–D12`) code, the networks load as an isolated list and **Module Match's
> 25% network component still cannot score.**
>
> To speed sign-off we auto-generated **`network_axis_crosswalk_DRAFT.csv`** — one row per distinct
> label with a name-match suggestion + confidence for the clinician to confirm/correct:
>
> | Bucket | Distinct labels |
> |---|---|
> | Exact auto-match (high confidence) | **8** |
> | Strong suggestion (token overlap ≥ 0.5) | 15 |
> | Moderate suggestion (0.3–0.5) | 25 |
> | Weak suggestion (< 0.3) | 41 |
> | No suggestion — needs clinician from scratch | 52 |
> | **Total distinct axis labels** | **141** |
>
> Suggestions are **advisory only** — none is written as authoritative; the `CONFIRM_axis_code`
> column is left for the domain expert. **CELA (#120) → A34** is pre-set per the client ruling.
>
> **Second gap:** the CSV has **no upstream/downstream columns**, so network *propagation* stays
> deferred — the 17-Jul doc shows chains like `AXIS27 → N120 → N145 → N173`, so the edges exist
> somewhere and should be requested.

**What we still need:** (1) the domain expert to confirm/correct `network_axis_crosswalk_DRAFT.csv`
(label → A1–A39 / D1–D12); (2) network upstream/downstream edges for propagation.

**Why it matters:** [E] Q3 makes the network layer **mandatory architecture**, and Part 6 of [B]
states TSPI must reason *from networks toward symptoms*. Our Module Match v1.0 allocates **25% to
network match** — until the master lands, **every module scores 0 on that component**.

**Easiest format** (your own schema from [E] Q3): `network_code, network_number, network_name_en,
network_name_th, primary_axis_code, secondary_axis_codes[], domain_code, network_type,
upstream_network_codes[], downstream_network_codes[], accepted_symptoms[], accepted_markers[],
evidence_grade, status`.

---

# 5. Master datasets still required

*(You listed these yourself in [E] Part 3. We have built the schemas + loaders; we need the clinical content.)*

| # | Dataset | Blocks | Our status |
|---|---|---|---|
| **Q1** | **Marker Registry** — marker → primary/secondary axis + direction rule (5 types) | generic lab handling | ~12 markers seeded by us |
| **Q2** | **Laboratory Cut-off Registry** — optimal/subclinical/functional/pathological + critical values | accurate axis severity | thresholds are placeholders |
| **Q3** | **Symptom→Axis / Symptom→Network Dictionary** | the phenotype engine | **16 symptoms seeded from your examples** — needs ratification |
| **Q4** | **Red-Flag Registry** | patient safety screening | **24 symptom + 3 condition + 10 critical-value rules seeded from your examples** — needs ratification |
| **Q5** | **Evidence Grade Registry** (A–D per module + claim + target) | module ranking | **no grades exist in the registry — every module currently defaults to D (weakest)** |
| **Q6** | **NSS Coefficients** after clinical validation | final scoring | v0.1 implemented behind a version flag |

---

# 6. Clarifications & confirmations

**Q7 — What are the official sub-axis codes for A10?**
[E] lists A10A–A10D (Protein Folding / ER Stress–UPR / Autophagy–Lysosome / Proteotoxic Burden) and
[F] shows 4 sub-axes for A10. Please confirm the exact **codes** so we key them identically.

**Q8 — What is `minimum_evidence` for each axis?**
[E] Q9 says this must differ per axis but does not enumerate it. Will it come with the Axis Master,
or shall we propose defaults for your review?

**Q9 — Treatment-step compatibility (5% of Module Match).**
We need the mapping of **modules → the 9 Restoration Steps** to score this. Does it exist? Until
then this component is neutral for every module.

**Q10 — Historical response (5% of Module Match).**
This requires past outcome data per module. Should it stay neutral until enough outcomes accumulate,
or do you have historical response data we can load?

**Q11 — Population-learning minimum sample size.**
[E] Q11 requires a "minimum sample size" but does not give a number. **We used 30** as a placeholder.
Please confirm or replace.

**Q12 — Domain→Key relationship weights.**
[E] Q6 gives primary/secondary keys per domain and says weights *"may remain descriptive until
clinically validated"*. We have stored them as descriptive only — please confirm that is right.

**Q13 — The older axis section inside [F] (pp.42–60).**
That section uses the **old** A35 name and omits A36–A39 — but it is also the section carrying the
per-axis `Module:` lists. **We ignored it entirely.** Please confirm it is superseded, and tell us
whether those per-axis module lists should be used (re-mapped) or discarded.

**Q14 — Interim handling of the 25% network-match weight.**
Until the Network master arrives, every module scores 0 on network match, so all scores sit ~25%
lower (ranking is unaffected, since it is uniform). Prefer we (a) leave it, or (b) temporarily
re-normalise the remaining weights to sum to 1.0? We recommend **(a) leave it** — it keeps the
approved formula intact and honestly shows the data gap.

---

# 7. What we built in the meantime — please ratify

To keep moving, we seeded provisional datasets **verbatim from your own worked examples**. Each is
labelled `authoritative: false` and is excluded from clinical authority. **These need your review:**

| File | Contents | Source |
|---|---|---|
| `red_flag_rules.json` | 24 symptom rules · 3 condition rules · 10 critical-value rules | your Q5 examples + section 10 of [A]/[B] |
| `symptom_dictionary.json` | 16 symptoms · 3 clusters · weights 0.25/0.50/0.75/1.00 | your Q4 examples (bloating, dizziness, fatigue) |
| `negative_test_rules.json` | 3 rules (gastroscopy, brain MRI, routine bloods) | your section 8 examples |
| `nss_config.json` | NSS v0.1 coefficients + NetworkFactor bands | your Q3 formula |
| `module_match_config.json` | the approved 30/25/15/10/10/5/5 weights + ceiling | your Q10 |

**Specific ratification requests:**
- Are the **critical-value thresholds** acceptable as an interim? (K⁺ <2.5 / >6.5 · Na⁺ <120 / >160 ·
  glucose <54 / >450 mg/dL · Hb <7 · platelets <20 · ALT/AST >1000 · SpO₂ <88% · troponin >0.04)
- Is the **symptom weighting** faithful to your intent? *(bloating alone = nonspecific; + early
  satiety + belching → A16 high; + constipation → A17/A19 rise; worse with stress → A34 + CELA)*

---

# 8. What your answers unlock

| Input | Unlocks |
|---|---|
| **Blocker 1** — corrected module registry | clinically usable module recommendations (currently quarantined) |
| **Blocker 2** — 180-Network CSV | the mandatory network reasoning layer + the 25% network-match component |
| **Q1/Q2** Marker + cut-offs | accurate per-axis severity from any lab |
| **Q3/Q4** Symptom dictionary + red flags | ratified clinical content behind the phenotype and safety engines |
| **Q5** Evidence grades | correct module ranking (all modules are currently graded D) |
| **Q7–Q14** | final structural details + confirmation of our interim choices |

**How to send:** CSV/Excel is ideal for the registries; a short note is perfect for Q7–Q14. We load
them directly — **most require no software changes**, because every dataset is versioned and loaded
from file.

---

## 9. For reference — what is already implemented from your feedback

Deterministic engine (**the LLM never assigns an axis score, network identity or module name**) ·
official-registry-only module resolution · physician approval gate · de-identification + audit ·
**no default-50** · explicit `NOT_ASSESSED` (no data is never "normal") · the four dimensions
(Evidence Status, Evidence Grade, Confidence, Data Completeness) **+ Biological Uncertainty** ·
HYPOTHESIS never scores · **red-flag screening runs first** · critical alerts survive a low NSS ·
**NSS v0.1** (confidence-weighted, NetworkFactor, no universal inflammation multiplier) ·
**Module Match v1.0** (safety gate, mechanism de-dup, ~6 ceiling, `reason_not_selected`) ·
**symptoms as first-class evidence** (a symptoms-only patient is now assessable) ·
**propose-only population learning** with clinician approval · everything version-stamped.
