# TSPI — Phase 3 Expert Feedback: Deep Analysis vs. Our Implementation

*Analysis of the domain experts' Phase-3 feedback against the `tspi_ai_brain` engine as currently built.*

## Source documents analysed (all read in full)

| # | File (in `docs/`) | Pages | Contents |
|---|---|---|---|
| **[A]** | `tspi comment for phase3 developer _260713_104231.pdf` | **36** | Part 1 (Clinical Reasoning Core) + Phase-3 report review (13 points) + **canonical 39-Axis Master Dictionary** + Priority 0/1 list |
| **[B]** | `tspi comment for phase3 developer .pdf` | **55** | **Pages 1–47 are identical to [A]**, plus **NEW pages 48–55: "Part 6 of 6 — The Fundamental Philosophy and Intelligence Architecture of TSPI-AI"** (see §6b) |
| **[C]** | `TSPI AI Engine — Domain Expert Answers for the Dev_260713_095402.pdf` | 22 | Answers to our 7 remaining questions (marker→axis, thresholds, NSS formula, Axes 37–39, learning rule, approver, language) |
| **[D]** | `tspi developer answer.pdf` | 3 | Earlier module-registry answers (1 module = 1 product, H-Code, etc.) |

**[B] supersedes [A]** (it contains everything in [A] plus Part 6). Both are cited below because [A]
was the first received. **[C] contradicts [A]/[B]** on Axes 35–39 — see Critical #1.

---

## 0. Scope note — read this first

The review examines **three Phase-3 report documents**: *TSPI Clinic — Clinical Intelligence
Platform* **Physician Edition (48 pp)**, **Patient Edition (25 pp)**, and **Multi-Omics Edition
(51 pp)**. **Our engine did not produce those reports.** They contain things our engine cannot
emit — invented module names ("Iron Recovery Module"), `AXIS_7 = 85/100` generic labels, projected
omics values, and default 50/100 scores.

So the review is of **a different artifact**. However, the **principles** it lays down are binding
on TSPI as a whole, and most of them expose **real gaps in our design**. This document separates:
- criticisms that **do not apply to us** (we already comply), and
- criticisms that **do apply** and require work.

**Two findings are critical and block clinical use. Both are ours.**

---

## 1. 🔴 CRITICAL #1 — Two expert PDFs contradict each other on Axes 35–39

**The two conflicting source files (both dated 260713, ~1 hour apart):**

- **Source [C]** — `TSPI AI Engine — Domain Expert Answers for the Dev_260713_095402.pdf` (22 pp),
  **Q4A "Where do Axes 37–39 belong?"** (pages 7–9)
- **Source [A]/[B]** — `tspi comment for phase3 developer _260713_104231.pdf` (36 pp) **and**
  `tspi comment for phase3 developer .pdf` (55 pp), section **"3. Master Dictionary ที่ Developer
  ต้อง Lock ให้ตรงทั้ง 39 แกน"** — *Domain 12 — Oncology & System-Level Regulation* (pp. 29–30 / 39)

They give **incompatible** definitions of the top of the axis list:

| Axis | **[C]** Domain Expert Answers PDF (Q4A) | **[A]/[B]** Phase-3 Comment PDF (Master Dictionary) | Our engine today |
|---|---|---|---|
| 35 | — | Visceral Organ Functional Reserve | Organ Resilience & Functional Reserve |
| 36 | — | Local Organ & Tissue Interface | **Oncology** |
| 37 | **Protein Quality Control System** | **Oncologic Cell Fate** | Protein Quality Control System |
| 38 | **Protein Clearance & Proteotoxic Stress** | **Tumor Microenvironment & Metastatic Dynamics** | Protein Clearance & Proteotoxic Stress |
| 39 | **Cognitive-Emotional Loop Axis (CELA)** | **Genomic Regulation Homeostasis** | CELA |
| Domain 12 | "Proteostasis, Cellular Integrity **and Conscious Regulation**" | "**Oncology** & System-Level Regulation" | Proteostasis & Cellular Integrity |

Note both Phase-3 files (**[A]** 36 pp and **[B]** 55 pp) carry the **same** Master Dictionary, so this
is a genuine disagreement between documents — **not** a transcription or OCR error on our side.

**[A]/[B]** goes further and states **proteostasis/autophagy lives at Axis 10**
(*Proteostasis–Autophagy–Lysosome*), explicitly listing *"proteostasis/autophagy — เพราะอยู่ Axis 10"*
under **"must NOT infer Axis 37 from"**. That is irreconcilable with **[C]**, which puts *Protein
Quality Control* at Axis 37.

**Our dictionary matches 34/39** of the Phase-3 master. The **only** divergences are axes **35–39** —
precisely the disputed region. Note the good news: the "semantic drift" the expert is angry about
(Axis 7 = inflammation/haematopoiesis, Axis 10 = microbiome, etc.) is **not present in our data** —
our Axis 7 = *Nutrient Sensing* and Axis 10 = *Proteostasis–Autophagy–Lysosome* already match the master.

> **ACTION REQUIRED — cannot be resolved by us.** The client must declare **which of the two axis
> dictionaries is canonical**. Everything downstream (axis scoring, module mapping, reports) depends
> on it. Until then, axes 35–39 must be treated as unstable.

---

## 2. 🔴 CRITICAL #2 — Our module→axis map uses the LEGACY axis numbering

The expert states plainly: *"Do not take the Axis Mapping column from the product file directly into
production. Every product must be remapped to the latest Axis Master first."* The product sheets use
an **old numbering** that is offset in the middle of the range:

| Product file (legacy) | Master (correct) |
|---|---|
| 16 = Liver detoxification | **15** = Detoxification Capacity |
| 17 = Digestive function | **16** = Digestive–Absorptive Function |
| 18 = Microbiome ecology | **17** = Microbiome Ecology |
| 19 = Gut barrier | **18** = Gut Barrier & Mucosal Integrity |
| 21 = Endothelial function | **20** = Endothelial Function |
| 25 = Tissue repair | **24** = Wound Healing |
| 27 = Metabolic balance | **27** = Glycation / Carbonyl Stress *(meaning changed!)* |

**We built `axis_module_official.json` straight from that column.** Verified: our registry maps
**H-001 Curcuma → A1, A9, A16, A17, A18, A19, A21, A25, A27** — the legacy numbers exactly.

**Consequence:** every module→axis link in our registry is **systematically wrong** in the A15–A27
band (roughly an off-by-one), so module selection is clinically incorrect. This also silently
contradicts the earlier owner ruling (*"ignore `target_axes_raw` in the legacy product sheets"*)
which we did not honour when compiling the draft.

> **ACTION REQUIRED.** Build a **legacy→master axis remap table**, apply it in `build_registry.py`,
> and add a validator rule that refuses to compile un-remapped mappings. Blocked on Critical #1 for
> axes 35–39.

---

## 3. The philosophical demand: symptoms are primary evidence

This is the heart of Part 1 of the review, and it is **the biggest design gap we have.**

**What they demand:**
- Patient **symptoms are biological evidence**, not secondary text. An axis must be assessable
  **without** specialist biomarkers.
- **Forbidden:** "no abnormal lab → axis normal"; "no biomarker → axis cannot be assessed"; "normal
  test → normal network".
- A **normal test narrows the differential, it does not erase symptoms** (normal gastroscopy does not
  exclude motility/acid/enteric/microbiome dysfunction).
- Required: a **Clinical Phenotype Engine** with structured symptoms (onset, duration, frequency,
  severity, trigger, relieving factor, meal/sleep/stress/bowel relation, functional impact,
  associated symptoms, red flags), **symptom clusters**, a **Symptom→Axis** and **Symptom→Network**
  dictionary, **adaptive follow-up questioning**, and **probabilistic differential network mapping**
  (never one network from one symptom).
- **Red-flag screening comes first:** Symptoms → Red-flag screening → Standard medical differential
  → Functional network mapping → Axis integration → Module consideration.
- Evidence layers 1–5 (phenotype → exam → routine labs → imaging → omics). **Layer 5 must not be
  required** to analyse.

**What we have:** `PatientInput.symptoms` is a **plain free-text string**. Axis scoring is
**lab-driven**. There is no structured phenotype, no symptom→axis dictionary, no clusters, no
red-flag layer, no adaptive questioning.

This is exactly the failure we already diagnosed ourselves in
`TSPI_Report_Comparison_Diagnosis.md` — a symptoms-only case produced a nearly empty report. The
expert has now told us *why* that is philosophically wrong, not just operationally thin.

> **Verdict: major gap. This is the single largest piece of work implied by the feedback.**

---

## 4. Full gap matrix — demand vs. our engine

| # | Expert requirement | Our engine today | Verdict |
|---|---|---|---|
| 1 | Axis scores computed by a **structured engine, not the LLM** | Deterministic pipeline; LLM only writes prose | ✅ **Comply** |
| 2 | **Only official registry modules** — AI may not invent module names | Registry-backed; unresolved modules flagged | ✅ **Comply** (just built) |
| 3 | **Physician approval** before patient release | `/validate` gate; `deliverable=false` until approved | ✅ **Comply** |
| 4 | **No default 50/100** — use `NOT_ASSESSED` + `INSUFFICIENT_DATA` | We never emit a default 50 | ✅ Comply (but see #6) |
| 5 | **Single versioned severity band** from backend, not per-report | One dosing/severity config; version-stamped | ✅ **Comply** |
| 6 | Explicit **`NOT_ASSESSED` / reason** for unmeasured axes | Unscored axes are simply **absent** — silent, not explicit | ⚠️ **Gap (small)** |
| 7 | Separate **4 scores**: symptom burden, axis probability, **evidence confidence**, **data completeness** | Single axis score only | ❌ **Gap (large)** — *also required by the NSS formula in the other PDF* |
| 8 | **`evidence_status`** on every statement (MEASURED / DERIVED / CLINICAL_INFERENCE / HYPOTHESIS / NOT_AVAILABLE); HYPOTHESIS must never raise a score | Not modelled | ❌ **Gap** |
| 9 | **Symptoms as core evidence** + structured phenotype + clusters | Free-text string; lab-driven | ❌ **Gap (largest)** |
| 10 | **Symptom→Axis** and **Symptom→Network** dictionaries | None | ❌ **Gap** |
| 11 | **Red-flag screening** before network analysis | None (module safety only) | ❌ **Gap (safety-critical)** |
| 12 | **Negative-test interpretation rules** | None | ❌ **Gap** |
| 13 | **Adaptive clinical questioning** | None | ❌ **Gap** |
| 14 | **180 Networks** layer; 39↔180 fixed table; **network propagation** | Absent — we jump axes → modules. Graph engine works over *axes* only | ❌ **Gap (architectural)** |
| 15 | **12 Domains + 3 Keys** rollup in the output; 9-Step restoration map | Domains/keys in DB; **9-step locator exists**; not surfaced as Keys/Domain dashboards | ⚠️ **Partial** |
| 16 | **Module match formula** (30% axis / 25% network / 15% evidence grade / 10% phenotype / 10% safety / 5% step / 5% history) + deductions + **`reason_not_selected`** | Simple axis match, no scoring, no rejection reasons | ❌ **Gap** |
| 17 | **Evidence grades A/B/C/D** linked to research | None | ❌ **Gap** |
| 18 | **Bilingual** (Thai default patient-facing, English canonical) | English only | ❌ **Gap** |
| 19 | **Versioning** of axis / network / product mapping | `registry_version` + `framework_version` stamped | ✅ **Comply** (extend to network/axis) |
| 20 | Learning loop: patient-specific bounded + population **propose-only** | Global auto-recalibration of axis weights | ❌ **Non-compliant** *(per the other PDF)* |
| 21 | **Digital twin / simulation**, TSPI knowledge graph | None | ⚪ **Future (P2)** |
| 22 | Correct **axis dictionary** | 34/39 match; 35–39 disputed | 🔴 **Blocked on Critical #1** |
| 23 | **Remapped** product→axis mapping | Legacy numbering | 🔴 **Critical #2** |

---

## 5. What we already get right (do not rebuild)

The expert scored the reviewed system *Software architecture 90/100, Future scalability 98/100* —
and the things it praised are things our engine already enforces structurally:

- Deterministic, auditable scoring engine — **the LLM never assigns an axis score**.
- Modules resolve to the **official catalogue** or are flagged; nothing invented.
- **Physician-in-the-loop** gate; nothing reaches a patient un-approved.
- De-identification; append-only audit; consent gating.
- Data-driven design — axis/module/dosing all load from versioned files, so fixing the dictionary
  and the remap is a **data change, not a rewrite**.

The expert's own conclusion applies to us too: *"What must be done is not to rebuild the software,
but to freeze the new master ontology and make every calculation flow from real data → axis."*

---

## 6. Recommended priority plan

### P0 — Blocking (no clinical use until done)
1. **Resolve the axis-dictionary conflict** (Critical #1) — client decision required.
2. **Build the legacy→master axis remap table**, apply in `build_registry.py`, and add a validator
   rule that fails on un-remapped input (Critical #2).
3. **Add `confidence` + `data_completeness` + `NOT_ASSESSED`** to axis scoring (also unlocks the
   official NSS formula, which needs `Confidence_i`).
4. **Add `evidence_status`** to every derived statement; forbid HYPOTHESIS from affecting any score.
5. **Red-flag screening layer** before network/module reasoning (safety-critical).
6. **Fix the learning loop** to bounded patient-specific + propose-only population learning.

### P1 — Makes it genuinely TSPI
7. **Clinical Phenotype Engine**: structured symptoms + clusters + Symptom→Axis dictionary
   (turns symptoms into first-class evidence — fixes the thin-report problem at the root).
8. **180 Networks layer**: network master table, 39↔180 mapping, network propagation.
9. **Module match scoring formula** + `reason_not_selected`.
10. **3 Keys / 12 Domains / 9-Step** rollups in the report output.
11. **Negative-test interpretation rules**; adaptive follow-up questioning.
12. **Bilingual** output (Thai default, English canonical).

### P2 — Differentiators
13. Evidence grades A–D; TSPI knowledge graph; digital-twin simulation (module A vs B → predicted
    3-month trajectory).

---

## 6b. ⭐ NEW — "Part 6 of 6: The Fundamental Philosophy" (from the 55-page edition)

Source **[B]** (`tspi comment for phase3 developer .pdf`, 55 pp) contains pages 1–47 identical to
**[A]** (the 36-page file), **plus a new closing section (pp. 48–55)** that the expert calls *"the
final and most important axis."* It is not a feature request — it defines **how every algorithm
inside TSPI-AI must reason.** *"Without this philosophy, TSPI-AI will become another disease-oriented
clinical AI. With it, TSPI-AI becomes a Biological Intelligence Platform."*

### The Final Core Principle (to become the FIRST design principle of the whole engine)

> *"In Fundamental Medicine, symptoms and diseases are not the primary targets of treatment. They are
> biological expressions of dysregulated living biological networks. Therefore, TSPI-AI reasons **from
> biological networks toward symptoms and diseases — not from diseases toward biological networks.**"*

### The causal chain (note the direction)

```
Biological Network Dysregulation → Symptoms → Laboratory Changes → Structural Changes → Disease
```
Disease is a **consequence, not the starting point**. Labs are **downstream events**; imaging/structural
change is **later still**. Hence: *normal labs ≠ normal biology*, and *abnormal labs ≠ the primary driver*.

### Ten principles that bind our engine

1. **Disease is not the treatment target** — diseases (Diabetes, GERD, Migraine) are *clinical labels*,
   useful for communication but **not the reasoning units**. The reasoning units are **living networks**.
2. **Symptoms are biological language** — not noise, not subjective, not secondary. (Constipation may
   express enteric-NS, colonic transit, microbiome, autonomic, thyroid, mitochondrial, hydration…)
3. **Every symptom → multiple candidate networks** → produce a **differential network model**, never a
   single diagnosis.
4. **Evidence ≠ Truth.** Absence of microbiome sequencing does not mean the microbiome is normal — it
   means *insufficient direct evidence*.
5. **Every conclusion must always expose FOUR dimensions** (this extends what we had):
   - **Evidence Level**
   - **Confidence Level**
   - **Data Completeness**
   - **Biological Uncertainty**  ← *new fourth dimension*
6. **Treatment = Network Harmonization** — the vocabulary must change from *treat / correct / reduce /
   improve* to **Network Harmonization, Adaptive Compensation, Biological Resilience, Network Plasticity**.
7. **Reasoning must be dynamic** — every new datum **reconstructs** the patient's biological model.
   New evidence may *confirm, refine, redirect, override or contradict* prior hypotheses. The AI must
   **not preserve a static diagnosis**.
8. **The objective is not normal lab values** — it is restored **resilience, adaptive capacity and
   physiological harmony** of the whole organism.
9. **TSPI-AI is a Biological Intelligence System**, not a lab reader or an auto-prescriber.
10. **Mission:** *"the world's first Biological Intelligence Operating System based on the philosophy of
    Fundamental Medicine"* — explicitly **not** "another clinical decision support system."

### The **Adaptive Biological Intelligence Loop** (new core architecture — distinct from our learning loop)

```
Patient → Symptoms & History → Clinical Phenotype → 39 Biological Axes
       → 180 Living Biological Networks → Root Driver Analysis
       → Network Harmonization Plan → Clinical Outcome → Network Response
       → Biological Model Update → Better Biological Understanding → Next Clinical Decision
```

> **The decisive sentence:** *"What the AI learns is not 'disease' — it is **the behaviour of biological
> networks**."* This is stated as the single most important difference between TSPI-AI and generic clinical AI.

### What this changes for us (beyond §4)

| Part-6 demand | Our engine today | Verdict |
|---|---|---|
| Reason **network → symptom/disease**, not the reverse | We reason **lab/finding → signal → axis → module**. Serviceable as *inference*, but the engine has **no network layer** to reason from, and the report is organised around findings/conditions | ❌ **Architectural gap** |
| **Diseases are labels, not reasoning units** | `conditions[]` is an input that only feeds safety checks — we never reason *from* them, which is accidentally correct, but we also never reason from **networks** | ⚠️ Partial |
| **4th dimension: Biological Uncertainty** on every conclusion | Not modelled (we have none of the four) | ❌ Gap — *extends §4 item 7* |
| **Network Harmonization** vocabulary | Report language is treat/correct/reduce | ❌ Gap (report_composer prompt + templates) |
| **Dynamic model reconstruction** — patient's biological model is rebuilt on every new datum | Each `/report` is a **one-shot, immutable** artifact. `/temporal` only trends raw markers | ❌ **Gap** — needs a persistent, versioned *patient biological model* |
| **Adaptive Biological Intelligence Loop** — learn **network behaviour** | Phase 4 learns **axis weights from marker deltas**. Wrong learning target *and* (per the other PDF) wrong scope (global auto-update) | ❌ **Redesign required** |
| **Root Driver Analysis at network level** | `graph_engine` does PageRank root-cause over **axes** — the closest thing we have, but not over the 180 networks | ⚠️ Partial — good foundation, wrong layer |

**Net effect:** Part 6 promotes several items from "nice to have" to **architectural**. In particular the
**180-Networks layer stops being optional** — it is the layer the entire system is supposed to *reason
in*. Our axis-level graph engine is the right machinery pointed at the wrong layer.

---

## 7. Questions the client must answer before P0 can start

1. **Which axis dictionary is canonical** —
   **[C]** `TSPI AI Engine — Domain Expert Answers for the Dev_260713_095402.pdf` (A37 = Protein
   Quality Control, A38 = Protein Clearance, A39 = CELA), **or**
   **[A]/[B]** `tspi comment for phase3 developer …pdf` Master Dictionary (A37 = Oncologic Cell Fate,
   A38 = Tumor Microenvironment, A39 = Genomic Regulation Homeostasis)?
   **They cannot both be right**, and every downstream calculation depends on the answer.
2. Is there an **official legacy→master axis conversion table**, or should we derive one and have it
   clinically reviewed?
3. The **180 Networks master table** (network_code, name, axis_code, type, upstream/downstream) —
   does it exist in a loadable form?
4. **3 Keys ordering:** the master lists *Biological Dynamics* before *Metabolic Energy*, while older
   data uses Metabolic Energy as Key 1. Confirm one standard (and keep `key_code` separate from
   display order, as the expert advises).
