# Module Registry — data format to unblock the axis→module map

> **✅ Confirmed rules (domain experts, `docs/tspi developer answer.pdf`):**
> **1 module = 1 product** (no bundles) · primary key = **H-Code** (`module_code`) · **PhytoCore
> Code** is the long-term scientific ID · map to the **39 axes** (sub-axes not required) ·
> **contraindications live in the module row** · **English** canonical name · include an
> **active/archived** status. Dosing = severity-level, except the bowel group (KS, Be Lax,
> Cathartic, Lypholax, Venta). This spec already matches those rules.

Fill **one row per module** and send back as **CSV, XLSX, or JSON** (same field names).
Easiest path: fill the `target_axes` column in your existing `200 module tspi 2 …xlsx` and return it.
A ready-to-fill template is `docs/module_registry_TEMPLATE.csv`.

## Fields

| Field | Req? | Format | Example | Purpose |
|---|---|---|---|---|
| `module_code` | **Required** | UPPERCASE, no spaces, unique | `KS` | Stable ID used everywhere |
| `module_name` | **Required** | text | `KS bowel protocol` | Display name |
| `target_axes` | **Required** | `A1`–`A39`, `;`-separated | `A17;A18` | **The map. Which axis/axes this module treats** |
| `products` | Recommended | `canonical_name` or `phytocore_code`, `;`-sep | `KERRA` | Links module to the 153-product catalogue |
| `key` | Optional | `A` / `B` / `C` | `A` | Which of the 3 Keys |
| `dosing_default` | Recommended | text | `follows severity table` | Base dose |
| `special_protocol` | Optional | `yes`/`no` | `yes` | Non-standard dosing (e.g. KS bowel-based) |
| `contraindications` | Recommended | conditions/meds, `;`-sep | `pregnancy;warfarin` | Feeds the safety layer (flags) |
| `therapeutic_focus` | Optional | text | `systemic inflammation` | Indication summary |
| `safety_notes` | Optional | text | | Free-text cautions |
| `treatment_duration` | Optional | text | `8-12 weeks` | Course length |
| `notes` | Optional | text | | Anything else |

## Rules (validated on ingest)
- `module_code` unique; every module has **≥1** `target_axes`.
- each axis matches `^A([1-9]|[12][0-9]|3[0-9])$` (A1–A39). Sub-axis like `A17.3` is accepted and rolled up to its parent axis.
- `products` are matched (normalized) against `product_registry.json` (153 products); unmatched entries are **flagged, not dropped** — a typo won't silently disappear.
- multiple modules may target the same axis, and one module may target several axes — both are fine.

## What happens after you send it
1. I parse it into `data/axis_module_official.json` and point `repository.modules_for_axis` at it (drops the "provisional" flag).
2. Modules get embedded into pgvector so RAG can suggest modules even for axes the explicit map doesn't list.
3. `resolved` / dosing / contraindication flags become authoritative — no engine/architecture changes needed.

## Minimum vs complete
- **Minimum to unblock the core gap:** just `module_code`, `module_name`, `target_axes` for all ~200 modules (ideally covering all 39 axes).
- **Complete (best):** add `products`, `dosing_default`/`special_protocol`, and `contraindications` — these light up accurate dosing and the safety layer too.
