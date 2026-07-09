# TSPI-AI — Official Inputs Needed from the Domain Owner

*One consolidated checklist of every **clinical/data input** the engineering team is waiting on,
across Phases 0–4. The software (`tspi_ai_brain`) is built and tested end-to-end; these are
**medical-data and sign-off items**, not code. Each row says what we need, why, the format that's
easiest for us to load, and what it unblocks.*

> Status today: engine runs on real data for axes/domains/keys/steps; everything below currently
> uses a **clearly-labelled provisional placeholder** so the system works, but it is **not
> clinically authoritative** until these official inputs replace the placeholders.

---

## 🔴 PART A — Blockers (highest priority; several phases depend on these)

### A1. Official **Module Registry**  *(Phases 0, 1, 2)* — *rules RESOLVED; final data pending*
- **✅ Resolved by domain experts** (`docs/tspi developer answer.pdf`): **1 module = 1 product**
  (no bundles), keyed by **H-Code**, mapped to the **39 axes**; contraindications live in each
  module entry; ~200 target modules. See `TSPI_Module_Registry_Questions_For_Experts.md`.
- **What we still need:** the **updated master registry file** with the **final active module/product
  counts**, dedup of the 61 duplicate code-sets, and the ~11 cleanup rows (no-axis 213–215,
  conflicts NARIS/30/54/64/97/201, unmatched 188/190, A37 support).
- **Easiest format:** a spreadsheet/CSV — `module_code(H-Code), module_name, phytocore_code,
  target_axes[], dose_type, contraindications, status(active/archived)`. (Template + spec:
  `docs/Module_Registry_Spec.md`.)
- **Unblocks:** the real module catalog, module embeddings (Phase 2), correct module selection.

### A2. Official **Module → Axis mapping**  *(Phases 0, 1)*
- **What we need:** which of the **39 axes** each module targets (the owner said this "already
  exists" in the TSPI framework).
- **Why:** we currently use a **small provisional map**; module recommendations are only as right
  as this table.
- **Easiest format:** CSV — `module_code, axis_code (A1..A39), relevance(optional 0–1)`.
- **Unblocks:** clinically-correct module-to-axis recommendations.

### A3. Official **39-Axis severity thresholds**  *(Phase 1)*
- **What we need:** for each axis (and key markers), the rules that turn a **lab value → severity
  level** (Optimal / Subclinical / Functional impairment / Pathological). E.g. *CRP < 1 = optimal,
  1–3 = subclinical, 3–10 = functional, > 10 = pathological.*
- **Why:** axis severity is currently a **placeholder heuristic**.
- **Easiest format:** CSV — `marker, axis_code, optimal_max, subclinical_max, functional_max` (or
  a short rules doc per axis).
- **Unblocks:** accurate per-axis scoring (the basis of NSS/SPS).

### A4. Official **NSS formula**  *(Phase 1)*
- **What we need:** the exact way the **Network Severity Score (0–100)** is computed from the axis
  scores (weights, how inflammation amplifies, any caps). The level bands (0–15/16–30/31–60/61–100)
  are already implemented.
- **Why:** our NSS is a **documented heuristic** isolated in one function, ready to swap.
- **Easiest format:** a one-page formula/spec (or worked examples we can fit to).
- **Unblocks:** the official severity → dosing decision.

---

## 🟠 PART B — Important (each unblocks a specific capability)

### B5. Official **Contraindication / Safety dataset**  *(Phase 3)*
- **What we need:** per module/ingredient: which **medications** and **conditions** to avoid or
  use with caution, plus the warning text. (e.g. anticoagulants + blood-movers; pregnancy cautions;
  estrogen-sensitive conditions + phytoestrogens.)
- **Why:** safety currently uses **3 seed rules** demonstrating the mechanism.
- **Easiest format:** CSV — `module_or_ingredient, avoid_with_meds[], avoid_with_conditions[],
  severity(review/avoid), note`.
- **Unblocks:** real contraindication flagging for the doctor.

### B6. Official **dose details per module** (confirm)  *(Phase 1/3)*
- **What we need:** confirm the **severity-level dosing** (L0 2×2 → L3 3×5/day) and the **KS bowel
  protocol** are final, and whether any module has **module-specific** dosing/overrides.
- **Why:** we implemented the v3.0 protocol exactly; just need confirmation + any exceptions.
- **Easiest format:** confirmation + a short list of exceptions if any.

### B7. **Marker → Axis dictionary** for monitoring & learning  *(Phases 1, 4)*
- **What we need:** the canonical map of **lab markers → axis**, and for each marker whether
  **lower or higher is "better."** (e.g. CRP↓ good, Hb↑ good, HbA1c↓ good, TSH/FT3 = toward range.)
- **Why:** drives axis mapping for any lab, the temporal trend ("improving/worsening"), and the
  learning loop. We seeded ~12 common markers.
- **Easiest format:** CSV — `marker, axis_code, direction(lower_better/higher_better/toward_range)`.
- **Unblocks:** generic lab handling + correct outcome learning.

### B8. **Learning-loop update rule** ratification  *(Phase 4)*
- **What we need:** sign-off on (or replacement of) the rule that adjusts **axis weights** from
  outcomes (worsening → more emphasis, improving → relax), including the learning rate and bounds.
- **Why:** the mechanism is built and bounded [0.5–2.0]; the *policy* is a clinical decision.
- **Easiest format:** a short note: keep-as-is, or your preferred update rule.

---

## 🟡 PART C — Clarifications (small but blocking final structure)

### C9. **Axes 37–39 domain placement**  *(Phase 0)*
- The official master groups axes **1–36** into 12 domains and lists **37 (Proteostasis), 38
  (Protein Clearance), 39 (CELA)** *after* Domain 12 (Oncology). **Which domain do 37–39 belong to?**
  (We provisionally grouped them as "Proteostasis & Cellular Integrity (meta)".)

### C10. **Domain → 3-Keys mapping**  *(Phase 0)*
- Which of the 12 domains rolls up to **Metabolic Energy / Biological Dynamics / Biointegrity**?
  (Currently left null.)

### C11. **Duplicate "keep" rule** confirmation  *(Phase 0)*
- When the same product had several files, we kept the **most complete** record (e.g. KS → ID 159).
  Confirm this, or tell us to prefer the official **`H-xxx` TSPI-coded** records. *(See
  `product_dedup_report.json` for all groups.)*

### C12. **Report language**  *(output)*
- Patient report in **English, Thai, or both**? (Currently English; data is bilingual.)

### C13. **Validating clinician / clinic**  *(Phase 3)*
- Confirm **Samutthan Clinic** (and which doctor roles) are the team that reviews/approves every
  AI report before patient delivery.

---

## How to deliver
- **Best:** simple **CSV/Excel** files for A1, A2, A3, B5, B7 (the column hints above) — we load
  these directly. Short docs are fine for A4, B6, B8, and Part C.
- We'll load each one, replace the matching placeholder, and re-run the verification suite — no
  code changes needed for most of these.

## What each unlocks (summary)
| Input | Unblocks |
|---|---|
| A1 Module registry | real module catalog + Phase 2 module embeddings |
| A2 Module→axis map | correct module recommendations |
| A3 Severity thresholds + A4 NSS formula | clinically-accurate scoring & severity level |
| B5 Contraindications | real safety flags |
| B7 Marker→axis + B8 learning rule | generic lab handling + valid outcome learning |
| C9–C13 | finalised domain structure, keys, dedup, language, validation owner |

*Reference: full per-phase detail in `TSPI_AI_Brain_Build_Plan.md`; this checklist consolidates
every pending item in one place.*
