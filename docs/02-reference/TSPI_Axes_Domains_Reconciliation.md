# TSPI — 39 Axes & 12 Domains: Extraction + Source Comparison

*Authoritative axis data fetched from `39-axes/axes/axis_01..39.md` (39 files). Domain/keys/
steps cross-checked against the summary PDF (`…สรุป…_260530_141459.pdf`) and the two
`last … กุญแจ 3 ดอก` PDFs. Structured output saved to `tspi_ai_brain/data/tspi_axes_39.json`
(axes + 119 sub-axes) and `tspi_ai_brain/data/tspi_framework.json` (domains/keys/steps).*

---

## 1. What each source actually is

| File | Role | Contents |
|---|---|---|
| `39-axes/axes/*.md` (39 files) | **Authoritative per-axis source** | Axis ID, name, primary domain, sub-axes (A/B/C…) + mechanism text. **No module lists.** |
| `…สรุป…_260530_141459.pdf` (18 pp) | Domain summary | 12 domains, 39 axes, **per-axis module lists**, Domain 11 & 12 detail. |
| `last … กุญแจ 3 ดอก.pdf` (68 pp) | **Master theory book** | The *same* 12-domain/39-axis summary **plus** the 3 Keys (กุญแจ 3 ดอก) and the 9 Stairs (บันได 9 ขั้น). |
| `last … กุญแจ 3 ดอก2.pdf` (72 pp) | Duplicate of the above | Same content; **degraded Thai text encoding** (a re-export). Treat as a copy of v1. |

**Bottom line:** the markdown files and all three PDFs describe **the same 39 axes** with the
same names and domain placement. They are consistent — *except* for how Domains 10–12 are
counted (see §3).

---

## 2. The authoritative 39-axis → domain map (from the .md files)

| Domain | Axes | Domain name |
|---|---|---|
| 1 | A1–A4 | Immune–Infection Governance |
| 2 | A5–A10 | Metabolic–Energy Core |
| 3 | A11–A14 | Genomic–Longevity Programming |
| 4 | A15–A19 | Detox–Digestive–Gut Ecosystem |
| 5 | A20–A23 | Vascular–Circulation–Stroke Prevention |
| 6 | A24–A27 | Repair–Fibrosis–Regeneration |
| 7 | A28–A30 | Musculoskeletal & Structural Integrity |
| 8 | A31–A33 | Endocrine Network |
| 9 | A34 | Neuro–Sleep–Stress |
| 10 | A35–A36 | Organ Axis + Oncology |
| **(11)** | *(reuses A24–A26)* | Regeneration & Repair System — see §3 |
| 12 | A37–A39 | Proteostasis & Cellular Integrity |

39 unique axes · 119 sub-axes · every axis has sub-axes. Full names + sub-axes are in
`tspi_axes_39.json`.

---

## 3. The one real discrepancy: Domain 11

The framework is branded "**12 Domains**", but the 39 markdown files physically define axes in
only **11 distinct domains (1–10, 12)** — there is **no Domain 11 axis file**.

The PDFs explain why. Domain 11 ("Regeneration & Repair System") is a **deliberate overlay
domain**: the summary/theory PDFs state it *"ใช้แกนซ้ำ แต่แยกโดเมนออกมา"* — **"reuses the same
axes but is split out as its own domain."** It re-groups **A24, A25, A26** (which physically live
in **Domain 6**) to highlight the regeneration "decision node," and notes it depends on Domains
1, 3, 6, 7 and 12.

**Consequence for the data model:** axis→domain is **not strictly one-to-one**. Two clean options:
- **(Recommended) Many-to-many "view":** keep 39 axes each in one *primary* domain (1–10, 12),
  and model Domain 11 as a **logical view/grouping** that references A24–A26. Preserves "12
  domains" branding without duplicating axes.
- **Physical 11 domains:** drop Domain 11 as a domain and treat it as a note on Domain 6 (then
  the product is "11 domains, 39 axes").

### Minor name variants (same axes, cosmetic)
| Axis | Primary (.md / Domain 6) | Domain 11 overlay (PDF) |
|---|---|---|
| A24 | Wound Healing (Internal + External) | Wound Healing & Repair Dynamics |
| A26 | Stem Cell & Hematopoiesis | Stem Cell & Regenerative Capacity |

Use the `.md` names as canonical; keep the overlay names as aliases.

---

## 4. 3 Keys & 9 Steps (from the theory PDFs)

**3 Keys (กุญแจ 3 ดอก)** — mapped to Ayurvedic tridosha:
- **Metabolic Energy** = Pitta — energy/biochemical transformation
- **Biological Dynamics** = Vata — movement, regulation, nervous/hormonal/circadian
- **Biointegrity** = Kapha — structural/cellular/microbiome integrity

**9 Stairs (บันได 9 ขั้น — "Nine Stair Steps of Biological Restoration")**, in order:
1 Detoxification → 2 Microbiome Restoration → 3 Immune Regulation → 4 Redox Balance →
5 Metabolic & Mitochondrial Recovery → 6 Autophagy & Cellular Clearance → 7 Genomic Stability →
8 Genomic Regulation → 9 **PRAKATI**.

---

## 5. Data gaps that still need a source / your input
1. **Domain 11 modeling** — overlay view vs physical (see §3). *Needs your decision.*
2. **Domain → Key mapping** — the 3 Keys are defined, but I did **not** find an explicit table
   saying which of the 12 domains rolls up to which Key. *Needs confirmation or a source.*
3. **Module lists** — present in the summary PDF *per axis* (e.g. Axis 37 → KS, Beta X, Merdana,
   Im1, ImO, Reshimuno, Renax, Im5, Im6, Kerra, Minoza, Plumax, Vitalplus) but **not** in the
   .md files. The axis→module map should be built from the summary PDF + the JSON + `products/`.

---

## 6. Output files produced
- `tspi_ai_brain/data/tspi_axes_39.json` — 39 axes, names, primary domain, 119 sub-axes (from .md).
- `tspi_ai_brain/data/tspi_framework.json` — 12 domains (incl. Domain 11 overlay flag), 3 keys, 9 steps, open questions.
