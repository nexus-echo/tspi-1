# TSPI — Remaining Questions for the Domain Experts

*One simple list of everything still needed from the medical team to finish the AI engine — in
plain language, with an example and the easiest format for each. The software is built and tested;
these are **medical sign-off items**, not code.*

> **Not included here:** anything about the **module registry** (what a module is, module IDs,
> which axes each module treats, per-module dosing/contraindications). You've already answered those
> and are preparing the updated master registry file — so we've left them out on purpose. This
> document is **only** the questions that do **not** depend on that file.

Everything below currently runs on a **clearly-labelled placeholder** so the system works end to
end — but it is not clinically authoritative until you confirm these.

---

## Part 1 — Must-have (needed for accurate scoring)

These four decide how a patient's lab values become an axis score and an overall severity. They are
about **lab results and the framework**, not about modules.

### Q1. Which lab marker points to which axis — and which direction is "good"?
- **What we need:** a simple table saying, for each common lab marker, **which of the 39 axes** it
  belongs to, and whether **higher, lower, or in-range** is the healthy direction.
- **Why it matters:** this is how any lab report gets turned into axis scores, trend arrows
  (improving/worsening), and learning over time. We currently seeded ~12 common markers ourselves.
- **Example:** *CRP → Axis 1 (inflammation), lower is better. Hemoglobin → Axis (blood), higher is
  better. HbA1c → Axis (glucose), lower is better. TSH → Axis (thyroid), toward range.*
- **Easiest format:** CSV — `marker, axis_code (A1–A39), direction (lower_better / higher_better / toward_range)`.

### Q2. What lab values count as mild / moderate / severe on each axis?
- **What we need:** for each axis (or key marker), the **cut-off numbers** that turn a lab value
  into a severity band: **Optimal → Subclinical → Functional impairment → Pathological.**
- **Why it matters:** axis severity is the foundation of the whole score; right now the cut-offs are
  our best-guess placeholders.
- **Example:** *CRP: under 1 = optimal, 1–3 = subclinical, 3–10 = functional impairment, over 10 =
  pathological.*
- **Easiest format:** CSV — `marker, axis_code, optimal_max, subclinical_max, functional_max`
  (anything above the last number = pathological), or a short one-line rule per axis.

### Q3. How is the overall severity number (NSS 0–100) calculated?
- **What we need:** the exact **formula** that combines the individual axis scores into the single
  **Network Severity Score (0–100)** — including any axis weights, how inflammation amplifies the
  score, and any maximum caps.
- **Why it matters:** NSS drives the severity level and therefore the dosing. The level bands are
  already set (0–15 = Level 0, 16–30 = Level 1, 31–60 = Level 2, 61–100 = Level 3); we just need the
  calculation that produces the 0–100 number. Ours is a documented placeholder isolated in one place.
- **Example:** *"NSS = weighted average of active axis scores, ×1.3 if inflammatory axes are high,
  capped at 100."* (Any worked examples we can match to are perfect.)
- **Easiest format:** a **one-page formula** or a few worked examples (patient values → the NSS you'd
  expect).

### Q4. Where do Axes 37, 38, 39 belong — and which domains map to the 3 Keys?
Two small structure confirmations that finalise the framework:
- **Axes 37–39 domain:** the official master groups Axes **1–36** into the 12 domains and lists
  **37 (Proteostasis), 38 (Protein Clearance), 39 (Cognitive-Emotional / CELA)** *after* Domain 12.
  **Which domain do 37–39 belong to** — an existing domain, or a new 13th group? *(We've provisionally
  grouped them as "Proteostasis & Cellular Integrity.")*
- **Domain → 3 Keys:** which of the 12 domains roll up to **Key A – Metabolic Energy**, **Key B –
  Biological Dynamics**, and **Key C – Biointegrity**? *(Currently left blank.)*
- **Easiest format:** two short lists — `axis 37/38/39 → domain`, and `each domain → A / B / C`.

---

## Part 2 — Good to have (refinements, not blocking)

### Q5. Is the learning rule for improving/worsening patients OK as-is?
- **What we need:** a yes/no (or your preferred rule) on how the system nudges an axis's importance
  based on patient outcomes — **worsening → give it more weight, improving → relax** — including how
  fast it adjusts and its limits.
- **Why it matters:** the mechanism is built and safely bounded; the *policy* is a clinical choice.
- **Easiest format:** one line — "keep as-is," or your preferred adjustment rule.

### Q6. Who is the approving clinician / clinic?
- **What we need:** confirm that **Samutthan Clinic** (and which **doctor roles**) are the team that
  **reviews and approves every AI report** before it reaches a patient.
- **Why it matters:** nothing reaches a patient until a named clinician approves it; we need to know
  who that is in the workflow.
- **Easiest format:** a sentence — clinic name + which roles can approve.

### Q7. What language should the patient report be in?
- **What we need:** should the **patient-facing report** be **English, Thai, or both**? *(Module and
  data names are already standardised to English; this is only about the report the patient reads.)*
- **Easiest format:** one word — English / Thai / both.

---

## What your answers unlock

| Question | Unlocks |
|---|---|
| Q1 Marker → axis + direction | turning any lab report into axis scores + correct trend arrows |
| Q2 Severity thresholds | accurate per-axis scoring |
| Q3 NSS formula | the correct overall severity level → correct dosing |
| Q4 Axes 37–39 + Domain→Keys | a fully finalised framework structure |
| Q5 Learning rule | valid long-term outcome learning |
| Q6 Approving clinician | a complete, safe review workflow |
| Q7 Report language | the right patient-facing output |

**How to send:** simple CSV/Excel for Q1 and Q2; a short note or one-pager for Q3–Q7. We load each
one, replace the matching placeholder, and re-run our checks — **no software changes needed.**
