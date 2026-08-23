# TSPI — Round-3 Answers + New Masters: Analysis, KB Update & Remaining Blockers

*Analysis of the three documents received 15 Jul 2026, what we changed in the knowledge base, and
what is still open.*

## Documents analysed

| Ref | File | Type | Verdict |
|---|---|---|---|
| **[E]** | `TSPI 3 — Complete Domain Expert Response for the Development Team.pdf` (30 pp) | Round-3 answers | ✅ **All 13 questions answered.** Ends with a "Final Developer Lock" |
| **[F]** | `data/last 39 แกน 12 โดเมน กุญแจ 3 ดอก (1)_260715_110654.pdf` (81 pp) | Framework master | ✅ **Canonical.** Contains the corrected 39 axes (pp.36–41) **and the 180-Network table (pp.61–81)** |
| **[G]** | `data/200 module tspi 2 (10-7-69).th.en(1).th.en(4) แก้ไข.xlsx` (966 rows / 242 codes) | Module registry | 🔴 **Still legacy.** Does not carry current axis codes — see Blocker 1 |

---

## 1. Headline: the critical blocker is RESOLVED

**[E] declares the axis dictionary conflict settled.** The file *"last 39 Axes, 12 Domains, 3 Keys"*
**[F]** is now the **sole canonical framework**. The Round-3 doc's *Final Developer Lock* states:

- **A10** = Proteostasis–Autophagy–Lysosome *(absorbs Protein Quality Control + Protein Clearance)*
- **A37** = Oncologic Cell Fate · **A38** = Tumor Microenvironment & Metastatic Dynamics ·
  **A39** = Genomic Regulation Homeostasis
- **CELA is a Living Biological Network, NOT A39** — it is network **#120**, parent axis **A34**
- Earlier A37–A39 definitions (Protein Quality Control / Protein Clearance / CELA) are
  **DEPRECATED / SUPERSEDED_BY_LATEST_AXIS_MASTER**
- **Key 1 = Metabolic Energy · Key 2 = Biological Dynamics · Key 3 = Biointegrity**

**[F] independently confirms this** — p.41 carries an explicit *"Key Correction"* explaining that
old A37/A38 duplicated A10 and were re-assigned to oncology. The two sources now agree.

## 2. All 13 Round-3 questions — answered

| Q | Answer |
|---|---|
| **Q1** Axis dictionary | ✅ **[F] is canonical.** A37–39 = oncology; CELA → Network #120 |
| **Q2** Legacy→new remap | ✅ **Do NOT use numerical conversion.** The updated Module Registry must carry current codes directly. A conversion table is for *migration/audit only*, never to auto-override. Legacy Product-file axis column is **not** a production source |
| **Q3** 180-Network master | ✅ **Mandatory architecture, build the loader now.** Labelled placeholders allowed but never clinically authoritative; AI must never invent a network |
| **Q4** Symptom→Axis dict | ✅ **Required.** Probabilistic, never 1:1. Base weights 0.25/0.50/0.75/1.00 adjusted by co-symptoms, timing, triggers, negatives. Full schema given |
| **Q5** Red-Flag list | ✅ **Mandatory before any network/module reasoning.** 3 classes: Emergency referral (block release), Urgent assessment (block + override), Standard work-up first. Must be **deterministic, not LLM-driven** |
| **Q6** 3 Keys + Domains | ✅ Key order confirmed; **Domain→Key Master v1.0** supplied (primary + 0–2 secondary) |
| **Q7** Four dimensions | ✅ **Evidence splits into TWO fields:** Evidence *Status* (MEASURED/DERIVED/CLINICAL_INFERENCE/HYPOTHESIS/NOT_AVAILABLE) **and** Evidence *Grade* (A–D). Confidence 0–1. **Data Completeness = weighted** (CORE=3/SUPPORTING=2/OPTIONAL=1), not a raw ratio. **Biological Uncertainty** = how many alternative models remain plausible |
| **Q8** Sub-axes | ✅ Used for **evidence/scoring within** a parent axis; modules map to **parent axes**; optional `sub_axis_tags` may refine ranking |
| **Q9** Axis Master | ✅ Use [F] as the canonical skeleton, transformed into a structured Axis Master. **minimum_evidence differs per axis**. Axis status: POSSIBLE / PROBABLE / HIGH_CONFIDENCE / **NOT_ASSESSED** |
| **Q10** Module Match | ✅ **Approved as "TSPI Module Match v1.0"** (30/25/15/10/10/5/5). **Safety is a GATE, not a −10**: absolute contraindication ⇒ `EXCLUDED`, score not calculated. **Ceiling: 1–3 core + 0–3 supporting, max ~6; 7–8 needs senior approval; >8 needs justification.** Full `reason_not_selected` enum |
| **Q11** Learning | ✅ **Three levels:** patient-specific axis adaptation → **network behaviour learning** (which network moved first, time-to-response, repeatability) → versioned **Patient Biological Model** (v1→v2→v3, never delete). Population learning = **PROPOSE_MODEL_UPDATE only** |
| **Q12** Harmonization Plan | ✅ **13-section structure** specified (context → red flags → phenotype → differential networks → root drivers → compensatory → axis integration → priorities → modules → lifestyle → expected response → monitoring → model update) |
| **Q13** Patient comms | ✅ 4 levels confirmed. **Nuanced rule:** cause-specific modules blocked until cause confirmed, but *low-risk supportive network harmonization* may show with explicit uncertainty + physician approval |

---

## 3. Knowledge base — what we changed

| File | Change | Status |
|---|---|---|
| `data/tspi_axes_39.json` | **REPLACED** with official master v2.0.0 (`framework_version: 39-axis-master-260715`). A35–A39 corrected; A10 now carries its 4 sub-axes; every axis stamped with `key_primary`/`key_secondary` | ✅ Installed |
| `data/tspi_axes_39.LEGACY-v1.json.bak` | Previous (wrong) dictionary retained for audit/lineage | ✅ Archived |
| `data/domain_key_master.json` | **NEW** — Domain→Key Master v1.0, stable `key_code` separate from `display_order` | ✅ Installed |
| `data/axis_module_official.json` | **QUARANTINED** — `approval_status: UNREVIEWED`, `authoritative: false`, `production_allowed: false`, `framework_version: LEGACY-AXIS-NUMBERING`, with `quarantine_reason` | ⛔ Blocked from production |

**Regression: 22/22 tests still pass** on the new axis master.

**What changed materially:** our A35–A39 were wrong (we had Protein Quality Control / Protein
Clearance / CELA, and A36 = Oncology). A1–A34 were already correct. The engine's deterministic
pipeline, module resolution, approval gate and versioning are retained — as [E] explicitly endorses.

---

## 4. 🔴 REMAINING BLOCKER — the updated module file is still legacy

**This is the one blocker that did not clear, and it is the same one as before.**

[E] Q2 states: *"The updated Official Module Registry will directly contain the correct current Axis
codes for every module."* **The delivered file [G] does not.** Verified programmatically:

| Check | Result |
|---|---|
| Rows using **legacy** axis numbering | **54** |
| Rows using **new** axis numbering | **29** |
| Rows **mixing both** | **2** |
| Indeterminate | 154 |
| Axis numbers whose name disagrees with the official master | **20 of 39** |
| Rows still containing **DEPRECATED** "Protein Quality Control" | **21** |
| Rows still containing **DEPRECATED** "Protein Clearance / Proteotoxic Stress" | **22** |
| Rows still containing **DEPRECATED** "Cognitive-Emotional Loop" as an axis | **14** |

**Example — H-001 Curcuma** (the expert's own example) still reads:
`Axis 16 – Liver Detoxification, Axis 17 – Digestive Function, Axis 18 – Microbiome Ecology,
Axis 19 – Gut Barrier, Axis 21 – Endothelial Function, Axis 25 – Tissue Repair, Axis 27 – Metabolic Balance`
— i.e. exactly the legacy mapping [E] forbids. Under the master these should be A15/A16/A17/A18/A20/A24/A27.

**Example — H-006 BENCHAKUL** still contains
`AXIS 37 Protein Quality Control System … AXIS 38 Protein Clearance & Proteotoxic Stress …
Axis 39 Cognitive-Emotional Loop` — the definitions [E] just deprecated.

**Consequence:** per [E]'s own rule, this file **cannot enter production**. Our
`axis_module_official.json` is therefore quarantined, and **module→axis recommendations remain
clinically unusable** until a registry with current axis codes (`mapping_status = APPROVED`) arrives.

> **The engine is now blocked only on data, not on decisions.** Everything else is unblocked.

---

## 5. Open questions for the client

**Q-A (blocking). The updated module file still uses legacy axis numbering.**
[E] said the updated registry would carry current axis codes; file [G] does not (evidence above).
Is a further-corrected registry coming, or should we run the semantic re-review ourselves and return
it for clinical sign-off? *(Per [E], each legacy mapping must be reviewed semantically — not
converted numerically — so we cannot fix this unilaterally.)*

**Q-B. Please supply the 180-Network master as structured CSV/Excel.**
Good news: we found the full table inside **[F] pp.61–81** (No | Domain | Axis | Living Network |
Scope), and confirmed **CELA = #120**. However it is a **visual/prose table with interleaved Thai and
English**, and does not extract reliably — our best automated pass recovered only **102 of 180** rows
with garbled columns. Rather than load corrupt data we have **not** installed it. A structured export
of the same table (the fields in [E] Q3) would unblock the network layer immediately.

**Q-C. Sub-axis codes for A10.** [E] lists A10A–A10D (Protein Folding / ER Stress–UPR / Autophagy–
Lysosome / Proteotoxic Burden) and [F] lists 4 sub-axes for A10. Confirm the official **codes** so we
key them identically.

**Q-D. `minimum_evidence` per axis.** [E] Q9 says this must differ per axis but does not enumerate it.
Will it come with the Axis Master, or should we propose defaults for clinical review?

**Q-E. Marker Registry / Lab cut-off table.** Still pending from Round 2 ([C] Q1/Q2). We can build the
schema + loader now; we need the clinical values.

---

## 6. What we can build now (no further input needed)

Per [E]'s "Master Datasets" list and Final Developer Lock, all of these are unblocked:

1. **Axis Master v2** — ✅ done.
2. **Domain→Key Master** — ✅ done.
3. **Network loader + graph schema** — build now (data pending Q-B).
4. **Clinical Phenotype Engine** — structured symptoms + clusters (dictionary pending Q4 data).
5. **Red-Flag engine** — deterministic, 3 action classes, runs before network/module reasoning.
6. **Four-dimension scoring** — Evidence Status + Evidence Grade + Confidence + Data Completeness
   (weighted) + Biological Uncertainty; `NOT_ASSESSED` instead of absent axes.
7. **Module Match v1.0** — with the safety **gate**, module-count ceiling and `reason_not_selected`.
8. **Learning rework** — 3 levels; global learning becomes propose-only (fixes our current
   non-compliant auto-recalibration).
9. **Patient Biological Model** — versioned, never deleted.
10. **Bilingual output** — Thai default patient-facing, English canonical.

**Recommended order:** the *engine-correctness* items first — 6 (four dimensions), 5 (red flags),
8 (learning compliance) — since they are pure code and unblock clinical safety, while the module
registry (Q-A) and network master (Q-B) data are prepared in parallel.
