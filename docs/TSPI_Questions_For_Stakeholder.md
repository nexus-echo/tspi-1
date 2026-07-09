# TSPI — Questions We Need Answered Before Building the Knowledge Base (Phase 0)

*Plain-language questions for the TSPI medical/product team. Each one explains what we need,
why it matters, and shows a real example from your own files.*

> ## ✅ ANSWERED by the domain experts (`docs/tspi developer answer.pdf`)
> The blocking questions are resolved. Per-question answers are in-line below (green ✅ boxes), and
> the full module-registry breakdown is in `TSPI_Module_Registry_Questions_For_Experts.md` and
> `TSPI_Phase0_Answers_Resolution.md`.
>
> **Key rulings:** duplicates = same product (dedupe to one canonical record) · **1 module = 1
> product** · the **39-axis `.md` list is the master** (legacy sheet numbering is wrong) · each
> module carries its own **39-axis** list · **severity-level dosing** (bowel group excepted) ·
> contraindications live **in each module entry** · key by **H-Code**, English canonical.
> **Still coming:** the updated master registry file with final active counts + a few cleanups.

> **Already settled (no action needed):**
> ✅ The 39 axes are confirmed and consistent across all files.
> ✅ Domain 11 = an "overlay" domain (it re-uses axes 24–26) — we keep "12 domains".
> ✅ Domain → 3-Keys mapping = left empty for now, you'll provide later.

---

## PART A — Must answer before we start

### Q1. The same product name appears many times. Which one is the official version?
**What we need:** For each product/module name, tell us the **one official ID** to use (or confirm
they really are different products).
**Why it matters:** If "KS" exists 5 times, the computer doesn't know which one to pick.
**Example (from your `products/` folder):**
- "KS" appears as **5 separate files**: IDs `103`, `128`, `14` (YA KS CAPSULE), `159`, `H-026`.
- "Nourishing Blood" appears **5 times**: IDs `40`, `51`, `61`, `6`, `H-016`.
**What a good answer looks like:** *"KS = use ID 103. The others are duplicates / old versions."*
(A simple list of name → official ID is perfect.)

> ✅ **Answered:** Duplicates are the **same** product (from legacy exports). Keep **one canonical
> record** per product, keyed by **H-Code**; archive the rest. (We found 61 such duplicate code-sets.)

---

### Q2. How many modules are there really — and what is a "module" vs a "product"?
**What we need:** The official **count**, and a one-line **definition** of "module".
**Why it matters:** Different files say very different numbers, so we don't know what "complete"
looks like.
**Example (your own files disagree):**
- The folder is named **"200 modules"**.
- The data file `tspi_200_modules_v1.json` has **65 entries**.
- The `products/` folder has **276 files**.
- A poster says **"200 Phytochemical Modules"**.
**The key question:** Is a "module" **one herb** (e.g. just "KS"), or a **combination** (e.g.
"KS + Kerra + IM6" used together)? 
**What a good answer looks like:** *"There are ~200 single products. A 'module' is a named
combination of products for one purpose. There are about X modules."*

> ✅ **Answered (corrects the guess above):** A module is **NOT** a combination — **1 module = 1
> product** (no bundles, no sub-modules). Official target is **~200 phytochemical modules**. The
> exact active count arrives with the updated master file.

---

### Q3. ⚠️ The axis numbers don't match between two of your files. Which numbering is correct?
**What we need:** Confirm **which axis-numbering is the official one**, and how the old numbers
translate to it.
**Why it matters:** This is the most important one. The product data points herbs to the **wrong
axes** if we trust the numbers blindly — meaning wrong treatment suggestions.
**Example:** The official 39-axis list (your `.md` files) and the module data file use the **same
numbers for different things**:

| Axis # | Official 39-axis list (`.md` files) | Module data file (`tspi_200_modules` / product sheets) |
|---|---|---|
| Axis 16 | Digestive–Absorptive | "Liver Detoxification" |
| Axis 17 | Microbiome Ecology | "Digestive Function" |
| Axis 18 | Gut Barrier & Mucosal Integrity | "Microbiome Ecology" |
| Axis 21 | Vascular Remodeling | "Endothelial Function" |
| Axis 25 | Fibrosis & ECM Remodeling | "Tissue Repair" |
| Axis 27 | Glycation / AGE | "Metabolic Balance" / "Hormonal balance" |

So "Axis 17" in one file means **microbiome**, but in the other file it means **digestion** —
two different things with the same number.
**What a good answer looks like:** *"The `.md` 39-axis list is the correct/official one. The
product sheets use an older draft numbering — please re-map them to the official axes."* (Or the
reverse — we just need to know which is the master.)

> ✅ **Answered:** The **official 39-axis framework is the only authority**; legacy sheet numbering
> is a draft — **do not use it**. Modules map to the **39 axes** (parent axes; sub-axes not required).

---

### Q4. Which herbs treat which axis — please confirm ONE master list.
**What we need:** One agreed source for the **axis → herbs/modules** links.
**Why it matters:** Two of your files give different herb-to-axis links, so we need to know which
to trust.
**Example:**
- The **summary PDF** lists herbs under each axis (e.g. *Axis 37 → KS, Beta X, Merdana, Im1, Reshimuno, Renax, Im5, Im6, Kerra, Minoza, Plumax, Vitalplus*).
- The **module data file** instead tags each herb with its own axis list (using the mismatched
numbers from Q3).
**What a good answer looks like:** *"Use the summary PDF's per-axis herb lists as the master."*
(Plus confirmation that the short names — KS, IM6, Beta X — match the product IDs from Q1.)

> ✅ **Answered:** **Each module carries its own axis list** — map modules to the 39 axes from that.
> During a patient's analysis the AI flags **primary vs secondary** axes; the **physician decides**
> whether to prescribe primary-only or primary+secondary modules, and the AI **learns** from those
> choices over time. (Decision support, not autonomous prescribing.)

---

### Q5. What is the standard dose and safety note for each module?
**What we need:** A standard **dose**, **safety/contraindication**, and any **drug interaction**
note per module — or confirmation that the doctor decides this case-by-case.
**Why it matters:** The system should not suggest a dose it cannot back up, and must avoid unsafe
combinations.
**Example:** Your sample case report says *"KS — 1–2 capsules before breakfast and before sleep."*
Is that the **standard KS dose for everyone**, or just for that patient?
**What a good answer looks like:** *"Each product sheet already has the standard dose + safety —
use that,"* **or** *"Doses are decided per patient by the doctor; the AI should only suggest a
range."*

> ✅ **Answered:** Dose follows the **Network Severity Level (0–3)** by default. **Exception — bowel
> modules** (**KS, Be Lax, Cathartic, Lypholax, Venta**) use their own dosing: 1–4 capsules before
> bed and again on waking, per the patient's bowel condition. **Contraindications/safety live inside
> each module entry** (not a separate database). Physician has final authority.

---

## PART B — Nice to have soon (not blocking Phase 0)

### Q6. Two module names in the example report — please confirm the exact product.
- **"ZAMINZYME"** → we found exactly one file: `product_191_ZAMINZYME`. ✅ (please confirm)
- **"Blood Nourishing Module"** → matches **5** "Nourishing Blood" files (see Q1). Which one?

### Q7. What language should the final patient report be in?
English, Thai, or both? (Your data is bilingual; the example report is in English.)

> ✅ **Answered:** **English** is the canonical language for module names/identity; Thai stays as a
> **localized display name** only. (Patient-report display language can still be chosen separately.)

> ℹ️ **Q6 and Q8 not covered** by the module-registry expert answers. Q6 (ZAMINZYME / "Blood
> Nourishing" canonical IDs) is re-asked in `TSPI_Phase0_Answers_Resolution.md §D`; Q8 (validating
> clinic — Samutthan) is still open.

### Q8. Who is the validating doctor / clinic in the workflow?
The documents mention **Samutthan Clinic**. Is that the clinical team who reviews and approves
every AI report before it reaches the patient?

---

## How your answers will be used
Once Q1–Q4 are answered, we can load a **clean, correct knowledge base** (39 axes, 12 domains,
the real module catalog, and the axis→module links). After that the AI's suggestions stop being
"sample/placeholder" and start being based on **your real medical data**.
