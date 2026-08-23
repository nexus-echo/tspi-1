# TSPI AI Engine — What We Need From You to Finish the Project

**Prepared for:** the TSPI domain-expert team
**Prepared by:** the development team
**Date:** 28 July 2026
**Purpose:** one single checklist of **everything still needed from the clinical team** to resolve the
remaining blockers and complete the TSPI AI engine. Nothing here needs software from you — just
clinical answers and data files. **Most items can be answered in one line or one small table.**

---

## How to read this document

Every item below follows the same simple shape, so you can answer quickly:

> **What we have** — what is already built or seeded on our side.
> **What we need from you** — the exact thing missing.
> **Easiest way to send it** — the format that lets us load it with no rework.
> ☐ a box to tick or a blank to fill, where a decision is required.

You do **not** have to answer everything at once. **Section 1 (the two blockers) unblocks the most** —
if you can only do one thing, do that.

---

## Files sent with this document

To make answering as easy as possible, two fill-in files come with this document. You type directly
into them — no need to build anything from scratch.

| File | What it is for | Section here |
|---|---|---|
| **`network_crosswalk_FULL_DRAFT.csv`** | all 180 networks listed, with our suggested axis + domain codes to confirm | Blocker 2 (2a / 2b) |
| **`TSPI_Master_Data_Templates.xlsx`** | one workbook, 5 ready-to-fill tabs (markers, cut-offs, evidence grades, steps, minimum evidence) | Sections 2.1 – 2.5 |

*(The corrected module registry — Blocker 1 — is not attached yet; we will send you a candidate
version to approve, see Section 1.)*

---

## 0. Where the project stands today

| | Item | Status |
|---|---|---|
| ✅ | Engine architecture, scoring, safety, learning | **built & tested** (54/54 passing) |
| ✅ | All decision questions (Ferritin, NSS formula, phenotype, contraindications, direction rules) | **answered 25 Jul — closed** |
| 🟡 | **Blocker 1 — Module Registry** | official axis mapping received; **approved registry file still needed** |
| 🟡 | **Blocker 2 — Network layer** | 180 networks verified; **axis/domain crosswalk + network links still needed** |
| ⬜ | **Clinical master datasets** (markers, cut-offs, evidence grades, steps…) | **schemas built — content still needed** |

**In short: the engine is finished waiting on decisions. It is now waiting on your clinical data.**

---

# 1. ◆ The two blockers (highest priority)

## Blocker 1 — Approved Module Registry with current axis codes

**What we have:** your latest module file still uses the **old axis numbers**, and you told us a blind
number-swap is not allowed. On 25 Jul you sent the official **legacy → current** mapping, so we can now
safely convert the simple cases and hold the risky ones for you.

**What we need from you:** sign-off on the module registry so it can go to production — either
(a) a corrected file, or (b) approval of the **candidate remap we will generate** for you to review.

**Easiest way to send it** — one row per product, these columns:

```
module_code (H-Code), module_name, phytocore_code,
target_axes[] (CURRENT A1–A39 codes), primary_step, secondary_step,
evidence_grade (A/B/C/D), contraindications, dose_type, status
```

☐ We will generate the candidate remap (with confidence flags) → **you review & approve**
☐ You will send a corrected registry file directly
☐ Other: ________________________________________________

---

## Blocker 2 — Connect the 180 networks to axes, domains, and each other

**What we have:** all **180 networks are verified** and loaded. **But** the `axis` and `domain` columns
in the file are **written as words, not codes** — e.g. the file says *"Detoxification"*, but the engine
needs the code **A15**. There are **141 different axis wordings** for the 39 real axes, so we cannot
guess them safely.

We already prepared a fill-in sheet — **`network_crosswalk_FULL_DRAFT.csv`** (attached) — which lists
**all 180 networks**, each with our **best-guess suggestion** and a confidence score, so you only
confirm or correct.

**What we need from you — three things:**

**2a. Confirm the axis code for each network** — in the attached sheet, fill the
**`CONFIRM_axis_code`** column.

> Each row shows the network, the label from your file, and our suggestion. Example:
>
> | network | label (from your file) | our suggestion | you confirm |
> |---|---|---|---|
> | N033 Phase I Detoxification | Detoxification | A15 | ☐ A15  ☐ other: ____ |
> | N048 Base Excision Repair | DNA Repair | A11 | ☐ A11  ☐ other: ____ |
> | N053 DNA Methylation | Epigenetics | *(none)* | ☐ ____ |

**2b. Confirm the domain (1–12) for each network** — same sheet, fill the **`CONFIRM_domain_num`**
column (our suggested domain is already shown beside it).

**2c. Send the network connections (which network feeds which).** Your 17 Jul document already shows
chains like **AXIS27 → N120 → N145 → N173** — we just need that list in full.

> Easiest format: `network_code, upstream_networks[], downstream_networks[]`

**Why this matters:** until 2a/2b are done, 25% of every module's score (the "network match") stays at
zero. Until 2c is done, the AI cannot trace a problem back to its root network.

☐ We send you the fill-in sheet; you confirm the codes
☐ Other: ________________________________________________

---

# 2. Clinical master datasets we still need

*These are the reference tables the AI reads instead of guessing. We built every table structure and a
small placeholder from your own examples — we now need your real content.*

> 📎 **All five tables below are ready-to-fill tabs in the attached `TSPI_Master_Data_Templates.xlsx`.**
> The module list (145) and axis list (39) are already typed in for you; the fixed choices are
> dropdowns. Just fill the white cells. The column names in each section below match the tabs exactly.

### 2.1 Marker Registry — which lab test points to which axis  *(tab "1. Marker Registry")*

**What we need:** for each lab marker, the axis it affects and which direction is bad.

```
marker_name, primary_axis, secondary_axes[],
direction_rule (Lower-better / Higher-better / Target-range / Context-dependent),
value_source_type (Measured / Derived),  calculation_rule (only if Derived),
unit
```

> Example you already gave us: *Ferritin → primary A26, secondary A1 (when inflamed), context-dependent.*
> Derived example: *HOMA-IR = (glucose × insulin) ÷ 405.*

### 2.2 Laboratory Cut-off Registry — the normal/abnormal ranges  *(tab "2. Lab Cut-offs")*

**What we need:** for each marker, the bands — and the **critical** value that triggers a red flag.

```
marker_name, optimal, subclinical, functional, pathological, critical_low, critical_high,
population (male / female / pregnancy / child / older-adult)
```

> You told us "never one global value" — so please send the population variants where they differ.

### 2.3 Evidence Grade Registry — how strong is each module's evidence  *(tab "3. Evidence Grades")*

**What we have:** **every module currently defaults to grade D (weakest)** because no grades exist yet.
**What we need:** the A/B/C/D grade per module (per claim if it varies). *All 145 modules are already
listed in the tab — just add the grade beside each.*

```
module_code, module_name, phytocore_code, evidence_grade (A/B/C/D), reference (optional)
```

### 2.4 Module → 9 Restoration Steps  *(tab "4. Module to 9 Steps")*

**What we need:** which of the 9 steps (Detox … Prakriti) each module belongs to. *All 145 modules are
pre-listed — just pick the step numbers.*

```
module_code, module_name, primary_step (1–9), secondary_step (1–9)
```

### 2.5 Per-axis minimum evidence — what's the least data needed to score an axis  *(tab "5. Axis Minimum Evidence")*

**What we need:** for each axis, the minimum evidence tier (Low / Medium / High) and what counts.
*All 39 axes are pre-listed in the tab — just fill the tier and a short note.*

> Your examples: *A26 needs at least a CBC · A8 needs symptoms OR energy markers · A37 needs cancer
> evidence / imaging / biopsy.* We need this for all 39.

```
axis_code, axis_name, domain, minimum_tier (Low/Medium/High), accepted_inputs (short note)
```

---

# 3. Content to ratify (we drafted it — please confirm or correct)

*We seeded these from your own worked examples so the engine could run. They are marked "not
authoritative" until you approve them. A yes/no per table is enough.*

| Table | What we seeded | Your call |
|---|---|---|
| **Red-flag list** | 24 symptom rules · 3 condition rules · 10 critical-value rules | ☐ approve  ☐ send corrections |
| **Symptom dictionary** | 16 symptoms, weighted (bloating, dizziness, fatigue…) | ☐ approve  ☐ send corrections |
| **Negative-test rules** | 3 rules (gastroscopy, brain MRI, routine bloods) | ☐ approve  ☐ send corrections |
| **Critical thresholds** | K⁺ <2.5/>6.5 · Na⁺ <120/>160 · glucose <54/>450 · Hb <7 · platelets <20 · ALT/AST >1000 · SpO₂ <88% · troponin >0.04 | ☐ approve  ☐ send corrections |

---

# 4. The Phenotype Registry (you asked us to propose it)

On 25 Jul you chose **Option A** — phenotypes are **named patterns** (e.g. *"Upper-digestive
dysfunction"*), and you asked the **dev team to propose the first list** for your review.

**What we will do:** draft a starter Phenotype Registry from your symptom examples and send it to you as
a review sheet (`status = CANDIDATE`). Each phenotype will list its symptoms, the axes it points to, and
any red-flag overrides.

**What we need from you:** confirm this is the right approach, and tell us roughly **how many phenotypes**
you expect (10? 30? 50?), so we scope the first draft correctly.

☐ Yes — propose the list, we will review
☐ Expected number of phenotypes (rough): ____________
☐ Other: ________________________________________________

---

# 5. A few small confirmations

*One-line answers. These fill the last gaps.*

**5.1 A35 / A36 — organ reserve.** The master renamed A35 to *"Visceral Organ Functional Reserve"* and
A36 to *"Local Organ & Tissue Interface."* Please confirm which **organs/markers** belong to each, so we
route liver/kidney/heart reserve correctly.
> Answer: ________________________________________________

**5.2 Historical response data (optional).** Module scoring reserves 5% for "how patients responded
before." Do you have any **past outcome data** we can load, or should this stay neutral until the system
collects its own?
> ☐ stay neutral for now   ☐ we have data: ____________

**5.3 Report language & content (for the patient/doctor report).** When we build the final report, do you
want it **bilingual (Thai + English)**, and is there a **required layout or wording** the clinic uses?
> ☐ bilingual   ☐ Thai only   ☐ English only · layout notes: ____________

**5.4 Anything we missed?** If there is a dataset, rule, or safety check you expect the AI to use that is
**not** listed anywhere above, please add it here:
> ________________________________________________________

---

# 6. What each answer unlocks (so you can prioritise)

| If you send… | …the engine gains |
|---|---|
| **Blocker 1** — approved module registry | clinically usable module recommendations (today they are quarantined) |
| **Blocker 2a/2b** — network axis/domain codes | the 25% network-match score starts working |
| **Blocker 2c** — network connections | root-cause tracing across networks |
| **2.1 / 2.2** — markers + cut-offs | accurate severity from any lab report |
| **2.3** — evidence grades | correct module ranking (all are grade D today) |
| **2.4 / 2.5** — steps + minimum evidence | full module matching + honest "not enough data" handling |
| **Section 3** — ratified content | the safety & symptom engines become authoritative |
| **Section 4** — phenotype approach | the Symptom → Phenotype → Axis reasoning layer |

---

# 7. Suggested order (easiest path to a finished system)

1. **Blocker 2a/2b** — confirm the network codes on the fill-in sheet *(fastest, we did most of it)*.
2. **Blocker 1** — approve the module registry remap.
3. **2.1 + 2.2** — the Marker + Cut-off tables *(these make lab reports work)*.
4. **Section 3** — tick-approve the drafted safety/symptom content.
5. **2.3 – 2.5** — grades, steps, minimum evidence.
6. **Section 4 + Blocker 2c** — phenotype list and network connections.
7. **Section 5** — the small confirmations.

---

## How to send everything

- **Fill the two attached files** — `network_crosswalk_FULL_DRAFT.csv` (Blocker 2) and
  `TSPI_Master_Data_Templates.xlsx` (Sections 2.1–2.5) — and send them back. That covers most of this document.
- **A short note** is perfect for the confirmations in Sections 3–5.
- You can reply **item by item** as answers become ready — nothing has to arrive together.
- For the network sheet, just fill the `CONFIRM_axis_code` and `CONFIRM_domain_num` columns.

**Every dataset you send is versioned and audited on our side, and any change automatically updates the
AI's understanding — you will never have to repeat yourself.**

---

### Quick checklist (tear-off summary)

```
BLOCKERS
  ☐ 1  Module registry — approve remap OR send corrected file
  ☐ 2a Network → axis codes      [file: network_crosswalk_FULL_DRAFT.csv, 180 rows]
  ☐ 2b Network → domain (1–12)   [same file, CONFIRM_domain_num column]
  ☐ 2c Network connections (upstream/downstream)

MASTER DATA  [file: TSPI_Master_Data_Templates.xlsx — 5 tabs]
  ☐ 2.1 Marker Registry (marker → axis + direction)
  ☐ 2.2 Lab cut-offs (+ critical values, per population)
  ☐ 2.3 Evidence grades per module      [145 modules pre-listed]
  ☐ 2.4 Module → 9 steps                 [145 modules pre-listed]
  ☐ 2.5 Per-axis minimum evidence        [39 axes pre-listed]

RATIFY (yes/no)
  ☐ 3  Red flags · symptoms · negative tests · critical thresholds

PROPOSE / CONFIRM
  ☐ 4  Phenotype approach + expected count
  ☐ 5  A35/A36 organs · historical data · report language · anything missed
```
