# TSPI — Follow-up Questions for the Domain Experts (Round 3)

*Thank you for the very detailed feedback — it changed our design in important ways, and we have
already corrected several things. After studying all four documents in full, these are the questions
we still need answered. Each one says what we need, why it matters, an example, and the easiest
format to send it in.*

> **One question (Q1) is blocking everything else.** Two of your documents give **different**
> definitions for Axes 35–39, and we cannot proceed until we know which is correct.

---

## Source documents we are referring to

| Ref | File name | Pages | Date |
|---|---|---|---|
| **[A]** | `tspi comment for phase3 developer _260713_104231.pdf` | 36 | **13 Jul 2026, 10:42** |
| **[B]** | `tspi comment for phase3 developer .pdf` | 55 | **13 Jul 2026** (received 11:17) |
| **[C]** | `TSPI AI Engine — Domain Expert Answers for the Dev_260713_095402.pdf` | 22 | **13 Jul 2026, 09:54** |
| **[D]** | `tspi developer answer.pdf` | 3 | **9 Jul 2026** |

*Note: **[B]** contains everything in **[A]** (pages 1–47 are identical) plus a new closing section,
"Part 6 of 6 — The Fundamental Philosophy", on pages 48–55.*

---

# PART 1 — Blocking questions (we cannot code correctly until these are answered)

## Q1. 🔴 Which 39-Axis dictionary is the official one? *(Sources [A]/[B] vs [C])*

**What we need:** confirmation of the **one correct** name for Axes **35, 36, 37, 38, 39** — and
therefore what Domain 12 contains.

**Why it matters:** this is the single most important question. Every calculation — axis scoring,
NSS, module selection, dosing, reports — flows from the axis dictionary. We must not guess.

**The conflict — your two documents say different things:**

| Axis | **[C]** *Domain Expert Answers* (Q4A, pp. 7–9) | **[A]/[B]** *Phase-3 Comment* — Master Dictionary (pp. 29–30 / 39) |
|---|---|---|
| 35 | *(not stated)* | Visceral Organ Functional Reserve |
| 36 | *(not stated)* | Local Organ & Tissue Interface |
| **37** | **Protein Quality Control System** | **Oncologic Cell Fate** |
| **38** | **Protein Clearance & Proteotoxic Stress** | **Tumor Microenvironment & Metastatic Dynamics** |
| **39** | **Cognitive-Emotional Loop Axis (CELA)** | **Genomic Regulation Homeostasis** |
| **Domain 12** | "Proteostasis, Cellular Integrity **and Conscious Regulation**" | "**Oncology** & System-Level Regulation" |

[A]/[B] also says **proteostasis/autophagy belongs to Axis 10**, and explicitly forbids inferring
Axis 37 from it. [C] says Protein Quality Control **is** Axis 37. These cannot both be true.

**Also please confirm:** if the [A]/[B] Master is correct, **where do CELA and Proteostasis go?**
(Axis 10 is *Proteostasis–Autophagy–Lysosome* — but CELA then has no axis number at all.)

**What a good answer looks like:** *"Use the Master Dictionary in [A]/[B]. Axes 37–39 are the
oncology axes. CELA is handled as ___."* — or the reverse. A single confirmed list of all 39 axis
names is ideal.

**Easiest format:** one CSV/table — `axis_no, official_name_en, official_name_th, domain_no`.

---

## Q2. 🔴 Is there an official **old → new axis number conversion table**?

**What we need:** the mapping that converts the **old axis numbers** used in the product files into
the **new Master** numbers.

**Why it matters:** you told us (in [A]/[B], section 7) *"Do not take the Axis Mapping column from
the product file directly into production — remap every product first."* You are right, and we found
we had done exactly that. **We cannot remap without the conversion rule.**

**Example (your own, from [A]/[B]) — H-001 Curcuma:**

| Product file says (old) | Master says (new) |
|---|---|
| 16 = Liver detoxification | **15** = Detoxification Capacity |
| 17 = Digestive function | **16** = Digestive–Absorptive Function |
| 18 = Microbiome ecology | **17** = Microbiome Ecology |
| 19 = Gut barrier | **18** = Gut Barrier |
| 21 = Endothelial function | **20** = Endothelial Function |
| 25 = Tissue repair | **24** = Wound Healing |
| 27 = Metabolic balance | **27** = Glycation *(meaning changed entirely)* |

**What a good answer looks like:** *"Old 16 → New 15, old 17 → New 16 …"* for the full list — **or**
*"Do not convert; the new module registry will carry the correct new axis numbers directly."*
(If the latter, we will simply wait for the new registry — please confirm.)

**Easiest format:** CSV — `old_axis_no, new_axis_no` — or a note saying the new registry supersedes it.

---

## Q3. 🔴 Does the **180 Networks master table** exist in a file we can load?

**What we need:** the official list of the **180 Living Biological Networks**.

**Why it matters:** Part 6 in **[B]** makes this essential — you wrote that TSPI must reason
*from networks toward symptoms and disease*, and that the AI must never invent a network. **Today we
have no network layer at all** (we go straight from axes to modules). We cannot build the reasoning
you describe without this table.

**Easiest format:** CSV/Excel with the fields you specified in [A]/[B] §8.2 —
`network_code, network_name, axis_code, network_type (signaling/metabolic/structural/transport/
immune/clearance/repair/regulatory), upstream_networks[], downstream_networks[], markers[],
clinical_outputs[], evidence_level`.

**If it does not exist yet:** please tell us, and we will build the loader with a placeholder so the
table drops straight in when ready.

---

## Q4. 🔴 Is there a **Symptom → Axis** (and **Symptom → Network**) dictionary?

**What we need:** the official table linking each symptom to the axes/networks it may indicate,
**with a weight**, and how co-symptoms change that weight.

**Why it matters:** you were very clear that **symptoms are core biological evidence**, not
secondary. Our engine today treats symptoms as free text and scores axes mostly from lab values —
exactly the mistake you identified. We need your clinical mapping to fix it properly; we must not
invent it ourselves.

**Example (your own, from [A]/[B] §11):**
- bloating + early satiety + belching after meals → **Axis 16 weight high**
- bloating + constipation + abnormal stool → **Axes 16, 17, 19 increase**
- bloating worse with stress → **Axis 34** + autonomic digestive network increase

**Easiest format:** CSV — `symptom_code, symptom_name_en, symptom_name_th, axis_code,
weight (high/medium/low), network_code(optional), required_co_symptoms(optional)`.

---

## Q5. 🔴 What is the official **Red-Flag list**?

**What we need:** the list of danger signs that must trigger **standard medical referral first**,
before any network/module reasoning.

**Why it matters:** you require the workflow *Symptoms → Red-flag screening → Standard medical
differential → Network mapping → Axis → Module*. We have **no red-flag layer today**, and this is a
patient-safety issue we do not want to guess at.

**Example (your own):** GI — unexplained weight loss, persistent vomiting, difficulty swallowing,
black or bloody stool, severe anemia, severe abdominal pain, fever, abdominal mass, new symptoms in
the elderly, family history of cancer. Dizziness — limb weakness, slurred speech, sudden ataxia,
worst-ever headache, fainting, chest pain, arrhythmia, very low BP, bleeding, high fever/stiff neck.

**Easiest format:** CSV — `symptom_area, red_flag, action (urgent referral / standard workup first)`.

---

## Q6. 🔴 The **3 Keys**: correct order, and which Domain belongs to which Key?

**What we need:** two things —
1. **The official order/numbering of the 3 Keys.** You noted in [A]/[B] §10 that the latest Master
   lists **Biological Dynamics before Metabolic Energy**, while older data used **Metabolic Energy as
   Key 1**. Please confirm one standard.
2. **The full list of which of the 12 Domains maps to which Key** (primary Key + optional secondary
   Keys, per your model in [C] Q4B). This is still outstanding.

**Why it matters:** the 3 Keys are the top of the whole framework and currently blank in our system.

**Easiest format:** a short table — `domain_no, domain_name, primary_key (A/B/C), secondary_keys[]`
— plus a line confirming which Key is Key 1 (we will keep the key **code** separate from the display
order, as you advised).

---

# PART 2 — Design clarifications (so we implement your rules exactly)

## Q7. How do we calculate the **four dimensions** you require?

In Part 6 of **[B]** you require that **every conclusion** always shows four things:
**Evidence Level · Confidence Level · Data Completeness · Biological Uncertainty**.

**What we need:** a definition and scale for each. Specifically:
- **Evidence Level** — is this the A/B/C/D research grade, or the `MEASURED / DERIVED /
  CLINICAL_INFERENCE / HYPOTHESIS / NOT_AVAILABLE` status from [A]/[B] §6? (They appear to be two
  different things — please confirm.)
- **Confidence Level** — the 0–1 scale from [C] Q3 (1.0 / 0.75 / 0.5 / 0.25 / 0)?
- **Data Completeness** — is this simply *"markers present ÷ markers expected for that axis"* (%)?
- **Biological Uncertainty** — **this is new to us.** How is it different from Confidence, and how
  should it be calculated?

**Easiest format:** one short paragraph per dimension, with the scale.

---

## Q8. **Sub-axes** — are they used for scoring or not?

There appears to be a small conflict:
- In **[C]** (Q3a) you said: *"Modules should map directly to the 39 Axes. Sub-axis mapping is not
  required."*
- In **[A]/[B]** (§2) you scored the sample patient using **sub-axes 26A / 26B / 26C**.

**Please confirm:** sub-axes are **not** needed for **module mapping**, but **are** used for
**axis scoring/evidence**? That is our assumption — we would like it confirmed.

---

## Q9. The **Axis Master** fields — will you supply them?

In [A]/[B] §8.1 you specified the Axis Master should include `accepted_markers[]`,
`accepted_clinical_features[]`, **`exclusion_rules[]`** and **`minimum_evidence`**.

The Master Dictionary in [A]/[B] already gives us, for each axis, the *"data used to score"* and the
*"must NOT infer from"* columns — which look exactly like `accepted_markers` and `exclusion_rules`.

**Please confirm:** may we load the Master Dictionary table directly as the Axis Master
(accepted_markers + exclusion_rules), and what should **`minimum_evidence`** be per axis?

---

## Q10. Confirm the **Module Match scoring formula**

From [A]/[B] §11 we will implement:
`30% Axis match + 25% Network match + 15% Evidence grade + 10% Patient phenotype fit + 10% Safety +
5% Treatment-step compatibility + 5% Historical response`, with deductions for missing critical test,
uncertain diagnosis, contraindication, duplicate mechanism, and **excessive module burden**.

**Please confirm and clarify:**
1. Are these weights final for v1?
2. **What is "excessive module burden"?** Is there a **maximum number of modules** per plan
   (e.g. no more than 5–8)? *(This matters: with your broad axis mappings, a severe patient can
   currently match 60+ modules, which is clearly too many to prescribe.)*
3. **Evidence grade A/B/C/D** — what defines each grade, and will it come with the module registry?

---

## Q11. The **Adaptive Biological Intelligence Loop** — what exactly should the AI learn?

In Part 6 of **[B]** you wrote that the AI must learn **"the behaviour of biological networks"**, not
disease — and you described a loop ending in a **Biological Model Update**.

**What we need to know:**
1. Does this **replace** the axis-weight learning rule you approved in **[C]** (Q5), or sit **on top**
   of it?
2. **What is stored** as "network behaviour"? For example: *"when Network X improves, Network Y
   improves after N weeks"* — is that the kind of relationship we should be recording?
3. Should the patient's biological model be a **living record that is rebuilt on every new result**
   (versioned over time)? Today each report is a one-off snapshot.

---

## Q12. **Network Harmonization** — what should the plan actually contain?

You said the report must stop saying *treat / correct / reduce / improve* and instead speak of
**Network Harmonization, Adaptive Compensation, Biological Resilience, Network Plasticity**.

**What we need:** what should a "Network Harmonization Plan" **contain**, in sections? For example:
root driver network → networks to harmonise first → supporting networks → modules → expected network
response → what to re-check and when.

**Easiest format:** a one-page example of a correct Network Harmonization Plan (even a rough one) —
that would be extremely valuable and would remove all ambiguity.

---

## Q13. Patient report — confirm the **4 communication levels**

From [A]/[B] §5 we will structure every patient report as:
1. **Confirmed:** e.g. *"CBC shows a microcytic hypochromic pattern"*
2. **Probable:** e.g. *"thalassemia trait or iron deficiency"*
3. **Not yet known:** the definite cause
4. **Suggested next tests:** iron profile, Hb typing

**Please confirm** this is the required structure, and confirm the rule: **no module/supplement may
be shown as a main recommendation until the cause is confirmed** (your iron-module example).

---

# PART 3 — Already promised: we only need format & timing

We know these are being prepared and are **not** re-asking them — we would just like to know the
**expected format and rough timing**, so we can prepare the loaders:

| Item | Source | Status |
|---|---|---|
| **Official Module Registry** (final active counts, dedup, cleanup rows) | [D] / [C] Q1e | In progress by your team |
| **Marker Registry** (marker → primary/secondary axis + direction rule) | [C] Q1 | Table pending |
| **Laboratory cut-off table** (optimal/subclinical/functional/pathological + critical values) | [C] Q2 | Table pending |
| **12 Domains → 3 Keys list** | [C] Q4B | Pending *(also asked in Q6 above)* |
| **NSS coefficients** after clinical validation | [C] Q3 | After validation |

---

## What your answers unlock

| Question | Unlocks |
|---|---|
| **Q1** Axis dictionary | **Everything.** Nothing downstream can be trusted until this is fixed |
| **Q2** Axis remap | Correct module→axis mapping (currently wrong in our data) |
| **Q3** 180 Networks | The network reasoning layer required by Part 6 |
| **Q4** Symptom→Axis | Symptoms become real evidence (fixes our biggest weakness) |
| **Q5** Red flags | Patient safety screening before any network reasoning |
| **Q6** 3 Keys / Domains | The top of the framework; the 3-Keys dashboard |
| **Q7–Q13** | Correct scoring, correct module ranking, correct reports, correct learning |

**How to send:** CSV/Excel is ideal for Q1–Q6 (the column names above); a short note or one-page
example is perfect for Q7–Q13. We load them directly — **most require no software changes.**

---

### What we have already fixed from your feedback

So you know the feedback landed: we have **already** stopped the AI from inventing module names (it
can only select real `product_id`s from the registry, or the module is flagged), we compute all axis
scores in a **deterministic engine — never the LLM**, we **never** use a default score of 50, we
enforce **physician approval before any patient release**, and we version-stamp every report with the
registry and framework versions. The remaining gaps are the ones above.
