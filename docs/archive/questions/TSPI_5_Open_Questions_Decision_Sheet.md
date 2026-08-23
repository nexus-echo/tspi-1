# TSPI — 5 Open Questions: Decision Sheet

**To:** TSPI Domain-Expert team
**From:** the development team
**Date:** 17 July 2026

> ## ✅ RESOLVED — 25 July 2026 (`answer tspi 25.07.2026.pdf`)
> **All five questions are answered. No open items remain on this sheet.**
>
> | # | Question | Ruling (25 Jul) |
> |---|---|---|
> | **1** | Ferritin secondary axis | **A1 (inflammation). A34 was a typo.** Ferritin is context-dependent: low→A26, high+CRP→A1, alone→no axis. |
> | **2** | NSS formula | **Weighted average — NOT literal multiply.** `AxisWeight = Confidence × Data Completeness × Evidence Quality`; `BaseNSS = Σ(Severity×AxisWeight)/Σ(AxisWeight)`; then `× NetworkFactor` (1.00/1.05/1.10). Confirms our v0.1 reading → now **NSS v0.2**. |
> | **3** | What is a "Phenotype"? | **Option A — named, versioned patterns.** Structure is Symptom→Phenotype→Axis. **Dev team proposes the registry** (status=CANDIDATE) for clinical review. |
> | **4** | Contraindications | **Author inside the module**; the separate Contraindication / Drug-Herb registries are **auto-generated views.** No double entry. |
> | **5a** | `derived_rule` | **Keep it**, but model it as a separate `value_source_type: MEASURED\|DERIVED` field (with calculation_rule) — distinct from the direction rule. |
> | **5b** | Optimal Range vs U-shape | **Same TARGET_RANGE family.** U-shape is a `curve_type`, not a separate direction. |
>
> Plan updated in `TSPI_Implementation_Plan_Phases_5_to_12.md` (NSS v0.2 in 10.1, Phenotype Registry 8.3b, Marker Registry 6.9, Phase 11 now actionable).
>
> *The original open questions are preserved below for the record.*

---

Thank you for the answers of 16 July — they resolved most of our questions. **Five points remain.**

These are **not** the two blockers (the Module Registry file and the 180-Network CSV — handled
separately). These five are small decisions, and **each can be answered in one line.**

Three of them exist because two of your documents say different things. We do not want to guess and
silently build the wrong thing, so we are asking you to pick.

---

## Question 1 — Ferritin: is it A1 or A34?

**What you wrote** *(answer tspi16.07.2026.pdf, Q1)*:

> Ferritin — Primary: A26 Hematopoiesis · Secondary: A16 Gut, A18 Barrier, **A34 Inflammation**

**The problem:** in your own official master, A34 is not inflammation.

| Your answer says | Your master says |
|---|---|
| A34 = Inflammation | **A34 = Neuro–Sleep–Stress–Brain Clearance** |
| | **A1 = Systemic Inflammatory Load**  <- this is inflammation |

**Why it matters:** ferritin does rise with inflammation, so the idea is right — it is only pointing
at the wrong number. Taken literally, a high ferritin would make the AI think the patient has a
**brain / sleep / stress** problem.

### Please choose

    [  ]  Ferritin secondary axis = A1 (inflammation).  A34 was a typo.
    [  ]  A34 is correct - keep it.  (please explain why)
    [  ]  Other: ______________________________________________

---

## Question 2 — Which NSS formula is correct?

You have given us two different formulas:

| Document | Formula |
|---|---|
| **15 Jul** — *TSPI 3 Complete Domain Expert Response*, Q3 | An **average**: for each axis add (Severity x Confidence), divide by the total, then x Network Factor |
| **16 Jul** — *answer tspi16.07.2026*, Q6 | A **multiplication**: Severity x Confidence x Data Completeness x Evidence Quality x Network Factor — *"not a plain average"* |

**The problem:** if we multiply literally, the score collapses. A genuinely severe patient:

> Severity 100 x Confidence 0.5 x Completeness 0.5 x Evidence 0.5 = **12.5** -> *"Level 0 — healthy"*

A very sick patient would look healthy simply because we had not yet run every test. That cannot be
the intention.

**Our reading:** the new items (Data Completeness, Evidence Quality) are meant to **weight each axis
inside the average** — not multiply the final score.

### Please choose

    [  ]  Correct - Completeness and Evidence Quality are per-axis weights inside the average.
    [  ]  No - multiply literally.  (then please give one worked example patient + expected NSS)
    [  ]  Other: ______________________________________________

---

## Question 3 — What exactly is a "Phenotype"?

**What you wrote** *(answer tspi16.07.2026.pdf, Q3)*:

> Symptom -> Phenotype -> Axis -> Network.  **Not** Symptom -> Axis directly.

**What we built today:** symptom -> (phenotype step) -> **axis**. We go straight to the axis.

**The problem:** we do not know what a "Phenotype" is meant to be as a *thing*. You also list a
**"Phenotype Registry"** among the 8 registries, which suggests it is a real, named list.

**Example of what we mean.** For a patient with bloating + early satiety + belching:

| Option A — phenotype is a NAMED pattern | Option B — phenotype is just the collected symptoms |
|---|---|
| bloating + early satiety + belching | bloating + early satiety + belching |
| -> phenotype: **"Upper-digestive dysfunction"** | -> (no named layer) |
| -> Axis A16 | -> Axis A16 |

We cannot build the layer until we know which one you mean.

### Please choose

    [  ]  Option A - phenotypes are named patterns.  You will send the Phenotype Registry.
    [  ]  Option A - named patterns, but the DEV TEAM should propose the list for your review.
    [  ]  Option B - what we already do is fine.
    [  ]  Other: ______________________________________________

---

## Question 4 — Where do contraindications live?

You have told us both:

| Document | What it says |
|---|---|
| **13 Jul** — *Domain Expert Answers for the Dev*, Q3c | *"Contraindications should be stored **within each module registry entry**… **not** a completely separate database."* |
| **16 Jul** — *answer tspi16.07.2026* | Proposes a separate **"Contraindication Registry"** and **"Drug-Herb Interaction Registry"** |

**What we built:** the 13 Jul version — contraindications sit inside each module.

**Why it matters:** it decides where the doctor types the information, and where we read it from.
Either is fine — but it must be one.

**Our suggestion:** keep writing them **inside the module** (one place to edit), and we will
**generate** the separate Contraindication / Drug-Herb registries automatically as a view. That gives
you both, with no double entry.

### Please choose

    [  ]  Agreed - author inside the module; generate the separate registries automatically.
    [  ]  No - contraindications must be authored in their own separate registry file.
    [  ]  Other: ______________________________________________

---

## Question 5 — Did "derived_rule" get removed on purpose?

Every lab marker needs a rule saying which direction is bad. You have given five types, twice, and
the two lists do not match:

| **13 Jul** — *Domain Expert Answers*, Q1 | **16 Jul** — *answer tspi16.07.2026*, Q1 |
|---|---|
| lower_better | Increase = worse |
| higher_better | Decrease = worse |
| toward_range | Optimal Range |
| context_dependent | Context dependent |
| **derived_rule**  <- missing on 16 Jul | **U shape**  <- new on 16 Jul |

**Problem 1 — `derived_rule` has disappeared.** It covered markers that must be **calculated**, not
read directly: **HOMA-IR, AST/ALT ratio, NLR, TG/HDL ratio, eGFR, corrected calcium**. Those were
**your own examples** on 13 Jul. Without this rule the engine has no way to handle them.

**Problem 2 — "Optimal Range" and "U shape" look like the same thing.** Both appear to mean
"too low is bad AND too high is bad" (TSH, sodium, potassium). Are they two different rules, or one
rule with two names?

### Please choose

**5a — derived_rule:**

    [  ]  Keep derived_rule - calculated markers (HOMA-IR, eGFR, ratios) still need it.
    [  ]  Remove it - handle calculated markers another way: ______________________

**5b — Optimal Range vs U shape:**

    [  ]  They are the SAME - use one rule.
    [  ]  They are DIFFERENT.  The difference is: ______________________________

---

## Summary

| # | Question | What we need |
|---|---|---|
| **1** | Ferritin secondary axis | A1 or A34? |
| **2** | NSS formula | weighted average, or literal multiply? |
| **3** | What is a "Phenotype"? | named list, or current approach? |
| **4** | Contraindications | inside the module, or separate registry? |
| **5** | Direction rules | keep derived_rule? is U-shape = Optimal Range? |

**Questions 1, 4 and 5 are one-line answers.**
**Questions 2 and 3 are the two that change how the engine calculates and reasons** — those are the
most important.

You can reply directly on this sheet, or simply answer "1: A1, 2: yes, 3: option A…" in a message.
Nothing else is needed.

---

### For reference — what is already agreed and built

Red-Flag screening runs before everything · no data is ever treated as "normal" · HYPOTHESIS never
affects a score · Evidence Status and Evidence Grade kept separate · module plan limited to ~6 ·
safety works as a hard exclusion gate · the AI can only *propose* model changes (minimum 100 cases,
Clinical Review Board approves) · A10A-A10D sub-axis codes adopted · pages 42-60 of the axis master
treated as deprecated · Network Match marked "Not Assessed" while we wait for the Network Registry.
