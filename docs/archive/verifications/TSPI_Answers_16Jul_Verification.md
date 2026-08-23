# Verification — Domain-Expert Answers of 16 Jul 2026

*Source: `answer tspi16.07.2026.pdf` (11 pages, Thai/English), answering our 2 blockers + Q1–Q14.
Verified line-by-line against the frozen axis master (`39-axis-master-260715`), the earlier expert
rulings [C]/[E], and the current engine code.*

---

## 1. Headline

**10 of 14 questions are answered and actionable. Both blockers, however, remain OPEN** — the
response **confirms the rules** for the two blocking datasets but **does not deliver the data**.

| | Item | Status |
|---|---|---|
| ✔ | 8 answers **confirm** decisions we already implemented | no work needed |
| ✔ | 4 answers are **new and actionable now** (A10 codes, sample size 100, Not-Assessed, grades) | small code changes |
| ! | 2 answers imply **design changes** (NSS formula, Symptom→Phenotype→Axis→Network) | need confirmation first |
| ◆ | **Blocker 1** corrected Module Registry | **STILL BLOCKED — data not attached** |
| ◆ | **Blocker 2** 180-Network CSV | **STILL BLOCKED — data not attached** |
| ⚠ | **6 discrepancies found** (1 factual error) | listed in §4 |

---

## 2. Both blockers remain open

### Blocker 1 — Module Registry
**Their answer:** *"Use Current Axis A1–A39 only. Legacy numbering forbidden in Production. No
numeric shift — semantic mapping only. Mapping must be approved by a Domain Expert."* Required
fields listed (module_code, module_name, phytocore_code, target_axes[], mapping_status,
axis_master_version, contraindications, dose_type, evidence_grade, status).

**Verification:** this **restates the rule we already follow** — it does not resolve the blocker.
The delivered file `200 module tspi 2 (10-7-69)…xlsx` **still contains legacy numbering** (54 legacy
rows, 20/39 axis-name mismatches, deprecated A37–A39 concepts in 14–22 rows). Our map stays
**quarantined**. Module recommendations remain clinically unusable.

> **Still needed:** the registry **file** with current A1–A39 codes and `mapping_status=APPROVED`.
> Our standing offer: we generate a **candidate semantic remap** (with `conversion_type` +
> confidence) for your clinical sign-off. We cannot approve it ourselves — you were explicit that
> mapping requires domain-expert approval.

### Blocker 2 — 180-Network Master
**Their answer:** *"Yes. 180 Networks will be a Master Dataset. Network Master is the Source of
Truth."* Schema given (now **16 fields** — adds `accepted_imaging[]`, `accepted_omics[]`,
`network_name_th`).

**Verification:** format confirmed, **file not attached**. The table exists in the 39-axes PDF
(pp.61–81) but does not extract reliably (102/180, garbled). Phase 9 stays blocked; `network_match`
(25% of Module Match) still scores nothing.

---

## 3. Answers verified as correct — no action needed

| Q | Their answer | Our status |
|---|---|---|
| **Q4** | Red Flag runs before TSPI, every time. `Symptoms → Red Flag → Emergency? → Medical Diagnosis → TSPI`. Never skip | ✔ **Implemented exactly** (Phase 7) |
| **Q10** | Historical response **not used** until enough outcomes; initial weight **Neutral** | ✔ **Matches** — we set neutral 0.5 |
| **Q12** | Domain→Key weights stay **descriptive**, not used in calculation | ✔ **Matches** — stored descriptive only |
| **Q13** | Older axis section (pp.42–60) is **Deprecated**; use only the canonical master; its per-axis module lists must move into the new Registry | ✔ **Confirms our decision** — we ignored pp.42–60 entirely |
| **Q14** | **Agrees with us**: do **not** re-normalize; keep the formula; mark Network Match as **Not Assessed** | ✔ Confirms our recommendation *(one refinement — see §4.6)* |
| **Q5** | Evidence **Grade separate from Status** | ✔ Implemented (Phase 6) *(grade definitions refined — see §4.5)* |
| **Q2** | Cut-offs need Optimal/Subclinical/Functional/Pathological/**Critical** + population variants (male/female/pregnancy/children/older adult); *"never one global value"* | ✔ Architecture matches; **data still pending** |
| **Q9** | Every module needs **Primary + Secondary Step** (Step 1 Detox … Step 9 Prakriti), used in matching | ✔ Mechanism ready; **data comes with the registry** |

---

## 4. ⚠ Discrepancies found — please resolve

### 4.1 🔴 Factual error — the Ferritin example maps to the wrong axis
Their Q1 example reads:
> Ferritin — Primary: **A26 Hematopoiesis** · Secondary: **A16 Gut**, **A18 Barrier**, **A34 Inflammation**

**A34 is not inflammation.** Per the canonical master you froze:
- **A34 = Neuro–Sleep–Stress–Brain Clearance** (Domain 10, Neurological Regulation)
- **Inflammation = A1 — Systemic Inflammatory Load** (Domain 1)

A26/A16/A18 are correct. **Please confirm the intended secondary axis is A1, not A34.** This matters:
ferritin is an acute-phase reactant, so an inflammation link is clinically sensible — but it must
point at A1.

### 4.2 The NSS formula now differs from [E] Q3
- **[E] Q3 (15 Jul):** `RawNSS = Σ(AxisScore × Confidence × Weight) ÷ Σ(Confidence × Weight)`, then
  `× NetworkFactor` — an evidence-adjusted **weighted mean**. *This is what we implemented as
  TSPI-NSS-v0.1.*
- **[H] Q6 (16 Jul):** *"NSS = Axis Severity × Confidence × **Data Completeness** × **Evidence
  Quality** × Network Factor — not a plain average."*

This **adds two multipliers** and appears to drop the normalising denominator. Our reading is that
the per-axis contribution weight becomes
`Confidence × Data Completeness × Evidence Quality`, still inside the weighted mean, then
× NetworkFactor. **Please confirm**, because a literal product across axes (no denominator) would
drive NSS toward 0 as soon as any axis has low completeness — almost certainly not intended.

### 4.3 The five direction rules changed
- **[C] Q1 (13 Jul):** `lower_better`, `higher_better`, `toward_range`, `context_dependent`, **`derived_rule`**
- **[H] Q1 (16 Jul):** `Increase = worse`, `Decrease = worse`, `Optimal Range`, **`U shape`**, `Context dependent`

**`derived_rule` has disappeared** and **`U shape`** is new. Two issues:
1. `derived_rule` covered **HOMA-IR, AST/ALT ratio, NLR, TG/HDL, eGFR, corrected calcium** — your
   own examples. Without it, the engine has no rule type for calculated markers. Was its removal intended?
2. `Optimal Range` and `U shape` look like the same concept (both low and high are abnormal). Are
   they distinct, or should we merge them?

### 4.4 Contraindications: inside the module, or a separate registry?
- **[C] Q3c (13 Jul):** *"Contraindications and safety information should be stored **within each
  module registry entry**… This information **should not be maintained as a completely separate
  database**."*
- **[H] §extra (16 Jul):** proposes **"Contraindication Registry"** and **"Drug–Herb Interaction
  Registry"** as two of the 8 standalone registries.

These conflict. We implemented the former (contraindications carried per module). **Which is
canonical?** *(A workable reconciliation: keep authoring per module, and expose a derived
Contraindication/Interaction Registry as a view. Please confirm.)*

### 4.5 Evidence Grade definitions were refined
- **[E]:** A = strong human clinical (preferably reproduced) · B = human observational/pilot +
  coherent preclinical · C = animal/cell/mechanistic · D = traditional use/expert consensus
- **[H]:** A = **Meta-analysis / RCT** / strong clinical · B = **Controlled / Prospective** ·
  C = **Observational** / in vitro / animal · D = **Expert opinion**

Note **"Observational" moved from B to C**, and "traditional use" is no longer named in D. We will
adopt **[H]** as the later ruling unless told otherwise — but flagging it, since it changes how any
already-graded module should be interpreted.

### 4.6 Network Match: "Not Assessed" vs 0
Q14 says *"Network Match = **Not Assessed**"* while keeping the formula. We currently set it to
numeric **0.0**. Numerically identical, semantically not — and it violates our own Phase-6 rule
(*"no data must never be scored as 0"*). **We will change it to an explicit `NOT_ASSESSED` marker
that contributes nothing**, which we believe is exactly your intent.

### 4.7 Minor — Q8's A39 example
> *"A39 must have Cancer evidence or Imaging or Biopsy"*

**A39 = Genomic Regulation Homeostasis**; the cancer-evidence requirement fits **A37 = Oncologic
Cell Fate**. Both sit in Domain 12, so this may be loose phrasing — please confirm which axis the
minimum-evidence rule applies to.

---

## 5. New answers — actionable immediately

| Q | Ruling | Change required |
|---|---|---|
| **Q7** | **A10A** Protein Folding · **A10B** ER Stress/UPR · **A10C** Autophagy–Lysosome · **A10D** Proteotoxic Burden — *"use these codes only"* | add the 4 official sub-axis codes to the axis master |
| **Q11** | Minimum sample for a rule proposal is **100 cases, not 30**. Production always passes a **Clinical Review Board**. *"AI has no right to update the model itself"* | `MIN_POPULATION_SAMPLE: 30 → 100` |
| **Q14** | Network Match = **Not Assessed**, formula unchanged | replace numeric 0 with an explicit NOT_ASSESSED marker |
| **Q5** | Grade A–D definitions refined | update grade descriptions |
| **Q8** | Minimum evidence is **tiered Low / Medium / High**, differs per axis (A26 needs ≥ CBC; A8 needs symptoms **or** energy markers; A39 needs cancer evidence/imaging/biopsy) | implement the tiering mechanism; **full 39-axis table still needed** |
| **Q3** | **Symptom → Phenotype → Axis → Network** — *"not Symptom → Axis directly"*. Each symptom carries weight, specificity, priority, laterality, duration, severity | **design change** — see §6 |

---

## 6. Design change implied by Q3

Our Phase-8 engine maps **symptom → axis candidates** (via a phenotype step that emits axis weights
directly). Q3 now requires an explicit intermediate:

```
Symptom  →  Phenotype  →  Axis  →  Network        (required)
Symptom  →  Axis                                  (explicitly forbidden)
```

We can restructure so the phenotype layer produces **named phenotype constructs** which then resolve
to axes and networks. Two questions before we build it:

1. **Is there an official Phenotype Registry** (the 8-registry list names one), or do we define the
   phenotype constructs ourselves for your review?
2. Since Axis resolution would then flow **through** Network, and the Network master is not yet
   available — should the phenotype layer land now with a **provisional** phenotype→axis path, and
   the network hop switch on when the Network Registry arrives?

---

## 7. The 8 registries they propose

`Axis` · `Network` · `Module` · `Marker` · **`Contraindication`** · **`Drug–Herb Interaction`** ·
**`Phenotype`** · `Outcome`

Three are new to us (**Contraindication**, **Drug–Herb Interaction**, **Phenotype**). We agree with
the principle — *"the AI does not guess knowledge, it reads standard databases"* — which is already
how the engine is built: every dataset is versioned and loaded from file. Two of the three conflict
or interact with earlier rulings (§4.4, §6), so we need those resolved before adding them.

---

## 8. What we will do next (pending your confirmations)

**Implement now** (unambiguous): A10A–A10D codes · sample size 100 · Network Match = Not Assessed ·
Evidence Grade definitions · minimum-evidence tiering mechanism.

**Hold for confirmation:** the NSS formula (§4.2) · the Symptom→Phenotype→Axis→Network restructure
(§6) · contraindication registry location (§4.4) · direction rules (§4.3).

**Still blocked on data:** corrected Module Registry · 180-Network CSV · Marker Registry · lab
cut-offs · per-axis minimum-evidence table · Symptom/Phenotype Registry · per-module evidence grades
and treatment steps.
