# TSPI — Report-Generation Methodology

*How to turn raw patient inputs into a full, de-identified **TSPI Case Report** for **any
patient and any condition**. TSPI is the back-end brain behind **MiHealth** (the front end);
MiHealth captures/parses the data, TSPI does the diagnosis and writes the report. Use this with
`TSPI_Master_Prompt.md` (reasoning rules) and `TSPI_Project_Requirements_Summary.md` (framework +
data). The fibroid case is an **illustrative example only** — adapt the procedure to whatever the
real patient presents.*

> **Generic-by-design & PII rules**
> - Accept **any** lab types/parameters/units, plus imaging, medications, wearables, and
>   multi-omics — never assume a fixed panel or a specific disease.
> - Produce **de-identified** output: reference the patient by a case ID + minimal demographics
>   (age band, sex). Never include name, address, phone, email, ID numbers, exact DOB, or
>   facility identifiers in the report or in any reusable template.

---

## A. Inputs the generator needs

**Required (whatever exists for this patient)**
- Minimal demographics for clinical reasoning only: **age band + sex** (no identifying details).
- Presenting problems / symptoms (free text).
- Lab report(s) of **any type** — routine chemistry, CBC, inflammatory markers, metabolic
  (glucose/HbA1c/insulin), hormones, thyroid, tumor markers, immunology, vitamins, functional
  labs, etc. Parse whatever parameters are present; do not expect a fixed set.
- Imaging/scan findings; current medications; lifestyle (diet, sleep, stress, activity, water);
  and where available wearables and multi-omics (genome, PGx, microbiome, proteomics,
  metabolomics, epigenetics).

**Reference data (attach the catalog)**
- 39-axes definitions — canonical source: the Thai summary PDFs in `39-axes/` and the clean
  `39-axes/axes/*.md` files (ignore the malformed JSON).
- Module/product catalog (`200 modules/*.json`, `products/*.md`).
- The de-identified reference case report — used for **structure/voice only**.

**If something is missing:** state the gap, note how it would change the mapping, and proceed
with clearly-labeled assumptions (inferring axes from limited data is acceptable — but label
inferences, and recommend the confirmatory test).

---

## B. The 7-stage generation procedure

### Stage 1 — Normalize inputs → biological signals
Convert each symptom and lab into its biological meaning. Build the table from **this patient's
actual findings** (any parameters). The rows below are illustrative (from the fibroid example)
— not a fixed checklist:

| Finding | Value/Status | Biological signal |
|---|---|---|
| CRP | high | systemic inflammation (IL-6, TNF-α, NF-κB) |
| HbA1c | diabetic range | insulin resistance / glucose dysregulation |
| Hb, MCV | low / microcytic | iron-deficiency / inflammatory anemia |
| TSH↓ / T3↑ | suppressed/elevated | thyroid overactivation (compensatory) |
| IgE | elevated | immune hypersensitivity / barrier dysfunction |
| Vitamin D | low | immune + metabolic + bone impact |
| Post-menopausal bleeding under stress | — | estrogen/endometrial instability + sympathetic drive |

### Stage 2 — Map signals to the 39 axes (with severity)
For each signal, assign one or more axes and rate **Optimal / Subclinical / Functional
impairment / Pathological**. Then split into:
- **Core / driver axes** (the hubs) — e.g. Inflammatory, Microbiome–Barrier, Metabolic-Energy,
  Hematopoietic, Endocrine, Vascular, Autonomic.
- **Secondary / amplifier axes** — e.g. Oxidative stress, Nutrient sensing, Immune
  hypersensitivity, Cellular repair, Gene regulation.

### Stage 3 — Build the root-cause chain
Write the cascade explicitly, upstream → downstream. Pattern from the reference case:
`Vegetarian low-diversity diet → microbiome dysbiosis → gut-barrier breakdown → LPS
translocation → chronic inflammation (↑CRP) → {insulin resistance, endothelial dysfunction
(HTN), estrogen dysregulation, hepcidin-driven anemia, thyroid/autonomic destabilization} →
fibroid growth + bleeding.`
Name the **upstream hub** (typically microbiome/nutrient-sensing + inflammation). Locate the
patient on the **9 Steps of Wellness** and state the **Prakati gap**.

### Stage 4 — Select modules (axis → module matching)
For each core axis, pull modules from the catalog whose `target_axes` include it. Prefer modules
that cover multiple core axes (synergy). Record for each chosen module: name, target axes,
mechanism, dose, clinical role, safety. Apply contraindication filtering. **Module selection must
be driven by *this* patient's dysfunctional axes** — do not reuse a prior case's module set.
The archetypes below are illustrative (from the fibroid example) of how axis-clusters map to
module roles; your actual selection depends on which axes this patient lights up:
- **Foundation/Gut–Neuro–Immune** (e.g. KS) → microbiome, gut barrier, autonomic, neurotransmitters
- **Anti-Inflammatory Network** (e.g. Kerra + Minoza + IM6) → NF-κB, cytokines, gut permeability
- **Nutrient & Hormonal Support** (e.g. ZAMINZYME) → nutrient sensing, iron, hormone support
- **Hematopoietic Restoration** (Blood Nourishing) → marrow, RBC, oxygen transport

> Whatever the condition (cardiometabolic, autoimmune, gut, oncologic, neuro, renal, etc.), the
> same procedure applies: map findings → axes → catalog modules whose target axes cover them.

### Stage 5 — Sequence into phases (the non-negotiable principle)
Always **foundation before manifestation**, regardless of condition. Map to the 9 Steps of
Wellness and the patient's specific manifestation:
- **Step 1 — Foundation Reset (0–8/12 wks):** reduce inflammation, repair microbiome/gut,
  improve absorption, restore energy/redox, rebuild blood, calm sympathetic drive. **Do NOT**
  target the manifestation or aggressively act on the affected organ system yet.
- **Step 2 — Targeted correction (≈3–6 mo):** address the structural/endocrine/organ
  manifestation once the terrain is stable.
- **Step 3 — Fine-tuning & integration (6+ mo):** normalize higher-order regulators
  (endocrine/neuroendocrine/autonomic synchronization) → **Prakati**.

*Example (fibroid case):* Step 1 = reset; Step 2 = cautiously restore pelvic circulation + shift
fibroid microenvironment + rebalance estrogen; Step 3 = thyroid/autonomic normalization. A
different patient (e.g. metabolic, autoimmune, renal) keeps the same Step-1-first logic with a
different Step-2/3 target. State the risks of acting out of order for the specific case.

### Stage 6 — Lifestyle prescription
Exercise (multiple short sessions), breathing/meditation (parasympathetic activation), sunlight
(vitamin D), high-diversity plant nutrition (+mushrooms, plant protein), iron-supportive carbs
(e.g. black rice), low-TDS mineral water. Tie each to the axes it supports.

### Stage 7 — Monitoring & success definition
Define per-phase biomarker targets, functional indicators, and imaging cadence; state that
recovery is **non-linear** and functional recovery precedes structural change. Success =
restoration of system-level balance (Prakati), not just normalized labs.

| Domain | Markers | Target trajectory |
|---|---|---|
| Inflammatory | CRP (±ESR, cytokines) | Step 1 sharp ↓, then stay low |
| Metabolic | HbA1c, fasting glucose, HOMA-IR | progressive ↓ toward non-diabetic |
| Hematologic | Hb, MCV, ferritin, transferrin sat | gradual normalization |
| Hormonal | TSH/FT3/FT4 (±estrogen/prog.) | gradual, no abrupt suppression |
| Immune | IgE | gradual ↓ |
| Structural | pelvic ultrasound q3–6mo | stabilize → gradual regression |
| Functional | sleep, energy, digestion, mood, bleeding | improve before labs |

---

## C. The output template (section order — de-identified)

A full **TSPI Case Report** should contain, in order. Header carries a **case ID + age band +
sex only** (no PII):

1. **Short Clinical Protocol (front matter)** — Step-1 plan: objective, modules + exact doses,
   lifestyle, expected outcomes (4–12 wks), and a bold **clinical cautions** box.
2. **Introduction** — "from multiple diagnoses to a single network disorder."
3. **Chapter 1 — Clinical Overview** — each condition described, then a unified summary table
   (structural/inflammatory/cardiovascular/metabolic/hematologic/endocrine/immune/neurological).
4. **Chapter 2 — Network Disease** — inflammation as central hub; microbiome/nutrient sensing as
   upstream origin; network pharmacology rationale.
5. **Chapter 3 — 39-Axis Mapping** — core axes, secondary/amplifier axes, network-collapse
   interpretation, hierarchy of dysfunction.
6. **Chapter 4 — Therapeutic Architecture** — Step 1 foundation modules → Step 2 structural/
   hormonal → Step 3 thyroid/neuroendocrine; rationale + risks of premature intervention.
7. **Chapter 5 — Monitoring, Outcomes & Prakati** — biomarkers, phase-specific monitoring,
   non-linear recovery, relapse warning signs, long-term maintenance, definition of Prakati.

> Style note: the reference report is written as a clinician-facing *article* (prose + short
> structured lists), bilingual-friendly, network-first, with explicit safety gates. Keep that
> voice.

---

## D. Ready-to-use generation prompt (paste after the Master Prompt)

```
TASK: Generate a FULL, DE-IDENTIFIED TSPI CASE REPORT for the attached patient.

This patient may have ANY condition and ANY mix of lab/imaging/omics inputs — do not assume a
fibroid-type case or a fixed lab panel. Reference the patient only by a case ID + age band + sex;
include NO name, address, phone, email, ID number, exact DOB, or facility identifiers anywhere.

Use the TSPI Master Prompt rules and the attached 39-axes (Thai summary PDFs / axes/*.md) +
module catalog as ground truth. Follow the 7-stage procedure and produce the report in this exact
section order:
1) Short Clinical Protocol (Step-1 plan with module names, exact doses, lifestyle, expected
   outcomes, and a bold clinical-cautions box)
2) Introduction (network-disorder framing)
3) Clinical Overview (+ unified summary table)
4) Network Disease (inflammation hub + microbiome/nutrient upstream origin)
5) 39-Axis Mapping (core + secondary axes, with a 4-level severity for each; root-cause chain;
   position on the 9 Steps of Wellness)
6) Therapeutic Architecture (Step 1 → Step 2 → Step 3 modules, with dose, target axes,
   mechanism, clinical role; state risks of premature structural/endocrine intervention)
7) Monitoring, Outcomes & Prakati (per-phase biomarker targets + functional indicators +
   imaging cadence; non-linear recovery; relapse signs; maintenance)

CONSTRAINTS:
- Only recommend modules that exist in the attached catalog; cite each module's target axes,
  mechanism, dose, and safety from the data. If a module in the template (e.g. ZAMINZYME,
  Blood Nourishing) cannot be resolved in the catalog, flag it instead of inventing details.
- Respect therapeutic sequencing: foundation before manifestation.
- Label any axis assignment that is inferred (not directly supported by a lab) as an assumption.
- End with a "For clinician review and approval" disclaimer.

First output a compact reasoning table (Finding → Biological signal → Axis → Severity), then
write the full report.
```

---

## E. Quality checklist before delivering a report
- [ ] Every presenting condition appears in the network chain (nothing treated in isolation).
- [ ] Each core axis has a severity rating and ≥1 matched module from the catalog.
- [ ] Module names, doses, target axes, and safety are grounded in the data (no invented items).
- [ ] Sequencing respected; premature-intervention risks stated.
- [ ] Monitoring has phase-specific targets and an explicit Prakati definition.
- [ ] Inferred (lab-unsupported) axis calls are labeled as assumptions.
- [ ] "For clinician review" disclaimer present.
