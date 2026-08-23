# TSPI — Phase 0 Questions: Official Answers & What They Change

*Resolution of `TSPI_Questions_For_Stakeholder.md` using the owner's `question_answers.txt`, the
official master files in `new_revised_docs/`, and — most recently — the **domain-expert answers**
(`docs/tspi developer answer.pdf`, analysed against `TSPI_Module_Registry_Questions_For_Experts.md`).
Bottom line: **all 5 blocking questions are answered**, the official **decision-engine spec (v3.0)**
is available, and Phase 0 can proceed.*

> ### ⚠️ Update (domain-expert answers supersede the earlier Q2 answer)
> The earlier `question_answers.txt` said "~60–70 modules, a module = a package of one *or more*
> products." The **domain experts have since corrected this**: **1 module = exactly 1 product**
> (no bundles, no sub-modules), target **~200 modules**, keyed by **H-Code**. The Q2 row below is
> updated accordingly; the old wording is struck through. The "separate module/product tables (a
> module can contain several products)" plan is **withdrawn** — module and product are 1:1.

---

## A. Each question → official answer → action

| # | Question | Official answer | What we do |
|---|---|---|---|
| **Q1** | Duplicate product names (e.g. "KS" ×5) | Duplicates from old data collection / legacy exports. **One module = one official record.** Keep the most complete/current; archive the rest. | Build a **dedup/merge** step; keep one canonical record per module (61 duplicate code-sets found). |
| **Q2** | How many modules? Module vs product? | **UPDATED (domain experts):** ~~~60–70 active modules; a module = a package of one *or more* products~~ → **1 module = exactly 1 product** (no bundles/sub-modules); official target **~200 phytochemical modules**. Exact active count comes with the master file. | Model module and product **1:1** (single table). Key by **H-Code**. ~~separate module/product tables~~ **withdrawn**. Await master file for the final count. |
| **Q3** | Which axis numbering is correct? | **The 39-axis framework is the only authority.** Old numberings are **legacy drafts — do not use.** Official architecture: **3 Keys → 9 Steps → 12 Systems → 39 Axes → 180 Living Networks → Modules.** A finalized official 39-axis doc is provided (`new_revised_docs/39 Biological Axes…pdf`). | Use the official 39 axes only. **Ignore** `target_axes_raw` numbers in the legacy product sheets. |
| **Q4** | Which herbs treat which axis? | **Each module carries its own axis list** (the full associated 39-axis set). Map modules to the **39 axes** (not sub-axes, not the 180 networks). AI flags **primary vs secondary** axes per patient; **physician decides** scope; AI **learns** from prescribing. | Build `axis_module_official.json` from the merged sources (`suggested_union`); load the master file when delivered. Sub-axis mapping **not** required. |
| **Q5** | Standard dose & safety? | **Dose = by Network Severity Level (0–3), not by disease.** Exceptions = **bowel-regulation modules** with their own dosing. AI = **Clinical Decision Support**; physician has final authority. **Contraindications live inside each module entry** (not a separate DB). | Implement **severity→dosing** + a **bowel-dosing group**: **KS, Be Lax (B-LAX), Cathartic, Lypholax, Venta (Ya Venta)** → 1–4 caps at bedtime + on waking (done — see §C). |
| **Q6** | Confirm ZAMINZYME / "Blood Nourishing" | Owner asked us to **clarify the question** first. | Re-ask precisely (see §D). |

**Master authority order (owner's rule):** 1) Official Product Registry → 2) Official Module
Registry → 3) Official 39-Axis Framework → 4) Official Module-to-Axis Mapping → 5) Official Dosing
Protocol. Any conflicting file = legacy until reviewed.

---

## B. The big new asset: the official TSPI-AI Decision Engine (v3.0)

`new_revised_docs/TSPI-AI Clinical Decision Engine.pdf` specifies the real algorithm:

**Decision flow:** Collect data → evaluate **12 Systems** → evaluate **39 Axes** → compute **NSS**
→ compute **SPS** → determine **Severity Level** → select modules → apply **severity-based dosing**
→ apply **KS protocol** → generate plan → **reassess every 14–30 days**.

**NSS — Network Severity Score (0–100):**

| NSS | Level | State |
|---|---|---|
| 0–15 | **0** | Preventive Longevity & Network Optimization |
| 16–30 | **1** | Functional Imbalance |
| 31–60 | **2** | Systemic Dysfunction |
| 61–100 | **3** | Advanced Network Failure (driven by inflammatory signal) |

**SPS — System Priority Score:** ranks dysfunction across the 12 Systems → drives module
selection, priority, sequencing, and intensity.

**Severity-based dosing (all assigned modules):**

| Level | Dose | Daily total |
|---|---|---|
| 0 | 2 caps × 2/day (AM+PM) | 4 |
| 1 | 2 caps × 3/day | 6 |
| 2 | 3 caps × 3/day | 9 |
| 3 | 3 caps × 5/day | 15 |

**KS — special:** dosed by **bowel performance** (goal ≥2 comfortable BMs/day). Start 2 caps before
bed (±2 on waking; 4+2 if chronic constipation); titrate +2 every 3–7 days; practical max 12/day,
physician review beyond.

**Severity is driven by inflammatory activity** (NF-κB, IL-6, TNF-α, COX-2, NLRP3, ROS).
**Digital-twin ready:** future omics + wearables (CGM, HRV…) continuously update NSS/SPS.

---

## C. One new item to confirm (introduced by the new master file)

The new official master (`39 Biological Axes…pdf`) **re-groups the 12 domains** differently from
the earlier `.md` files, and its 12-domain grid explicitly covers **axes 1–36**, listing **axes 37
(Proteostasis), 38 (Protein Clearance), 39 (CELA)** *after* Domain 12 (Oncology).

**Official 12 domains (axes 1–36):**
D1 Immune–Infection (1–4) · D2 Metabolic–Energy (5–10) · D3 Genomic Programming (11–14) ·
D4 Detoxification (15) · D5 Digestive–Gut Ecosystem (16–19) · D6 Vascular–Circulation (20–23) ·
D7 Repair–Regeneration (24–27) · D8 Musculoskeletal (28–30) · D9 Endocrine (31–33) ·
D10 Neurological (34) · D11 Organ Axis (35) · D12 Oncology (36).

**❓ Confirm:** which domain do **axes 37, 38, 39** belong to? (Earlier `.md` files put them in a
"Domain 12 – Proteostasis & Cellular Integrity"; the new master ends Domain 12 at Oncology.) We've
provisionally grouped 37–39 as **"Proteostasis & Cellular Integrity (meta)"** pending your word.

---

## D. Re-ask for Q6 (precise)
For the example report's modules, we only need the **canonical Product ID** (post-dedup):
1. **"ZAMINZYME"** — is it product **191**? (one match found)
2. **"Blood Nourishing"** — which single ID is canonical among IDs **40, 51, 61, 6, H-016**?
(We are asking only for *product identity / official ID* — nothing else.)

---

## F. Module registry decisions (domain-expert answers)

From `docs/tspi developer answer.pdf` (full mapping in `TSPI_Module_Registry_Questions_For_Experts.md`):

| Decision | Ruling |
|---|---|
| Module ↔ product | **1 module = 1 product** (no bundles, no sub-modules) |
| Duplicates | Same product; keep **one canonical record**; archive legacy exports |
| Primary key | **H-Code** now; **PhytoCore Code** becomes the permanent scientific ID later |
| Hierarchy | 3 Keys → 9 Steps → 12 Domains → 39 Axes → **180 Biological Networks → 200 Modules** |
| Axis mapping | Map modules to **39 axes** (each module lists its own); **sub-axes not required**; **180 networks** stay an intermediate knowledge layer (not attached in the registry) |
| Primary vs secondary | Module carries its **full** axis list; AI flags primary/secondary per patient; **physician decides**; AI **learns** from prescribing patterns |
| Dosing | **Severity-level** default; **bowel group** (KS, Be Lax, Cathartic, Lypholax, Venta) uses own dosing |
| Contraindications | Stored **inside each module entry** |
| Language | **English** canonical; Thai = display only |
| A37 (Protein Quality Control) | interim support = **KS, Kerra, VitalPlus** |
| Design | **Living system** — versioning + future additions + refinement without core-framework changes |

**Still pending the updated master file:** exact active module/product counts (Q1e), the 3 no-axis
modules (213–215), the axis conflicts (NARIS, 30/54/64/97/201), and the 2 unmatched (188, 190).
Plan for maintaining the master files: `docs/TSPI_Master_File_Update_Plan.md`.

---

## E. Status after these answers
- ✅ Architecture, severity model, and dosing = **locked** and now **implemented** in the engine.
- ✅ Official 12-domain structure adopted (1–36); 37–39 flagged for confirmation.
- ✅ **Module registry rules decided** (see §F): 1:1 module=product, H-Code key, map to 39 axes,
  severity + bowel dosing, contraindications in-entry.
- ⏳ Final **module registry data** (counts + the ~11 cleanup rows) = awaiting the updated master file.
- → Phase 0 proceeds: rules + merged draft map load now; the official catalog re-ingests when the
  master file lands (no code changes — data-driven).
