# TSPI — Official Master File Update & Versioning Plan

**Goal:** maintain the official TSPI knowledge (products/modules, module→axis map, dosing, safety)
as a **living system** — supporting **versioning, future module additions, and ongoing refinement
without changing the core TSPI framework or the engine code.**

This directly answers the domain experts' design principle: *"The module registry should be
designed for continuous expansion as new phytochemical modules, biological mechanisms, and clinical
evidence emerge… support versioning, future additions, and ongoing refinement without requiring
changes to the core TSPI framework."*

---

## 1. Principle: the framework is fixed, the data is versioned

Two layers, deliberately separated:

| Layer | Contents | Changes how often | Owned by |
|---|---|---|---|
| **Core framework** (stable) | 3 Keys · 9 Steps · 12 Domains · 39 Axes · 180 Networks · NSS/SPS model · severity levels | Rarely (a governance change) | TSPI scientific board |
| **Registry data** (living) | Products/modules, module→axis map, dosing, contraindications, product↔code aliases | Continuously | Domain experts |

The engine already **loads all registry data from files** (`ai-engine/data/*.json`) — so new
modules or corrected mappings ship as **data**, never code. Adding a module = adding a row.

---

## 2. Canonical master files (single source of truth)

Keep a small set of versioned master files under `knowledge-sources/official/` (the authoritative
inputs) which compile into the engine's `data/*.json` (the runtime artifacts):

| Master file (authoritative) | Purpose | Compiles to (runtime) |
|---|---|---|
| `modules_master.csv/xlsx` | one row per module (H-Code, PhytoCore, name, target_axes, dose_type, contraindications, status) | `data/module_registry.json` + `data/axis_module_official.json` |
| `axes_39_master.*` | the fixed 39 axes + sub-axes + domains | `data/tspi_axes_39.json` |
| `dosing_master.*` | severity-level table + bowel-group overrides | `data/tspi_severity_dosing.json` |
| `safety_master.*` | contraindication rules (or embedded in modules_master) | `data/safety_rules.json` |

Field spec for `modules_master`: see `Module_Registry_Spec.md` (already aligned to the confirmed
rules: 1 module = 1 product, H-Code key, 39-axis mapping, contraindications in-row, active/archived).

---

## 3. Versioning scheme

**Semantic versioning per master file** — `MAJOR.MINOR.PATCH`:

- **PATCH** (1.0.0 → 1.0.1): fix a typo, a wrong axis on one module, a dose correction. No new modules.
- **MINOR** (1.0.1 → 1.1.0): **add new modules**, add axes to existing modules, add contraindications.
- **MAJOR** (1.1.0 → 2.0.0): a change that alters meaning at scale (e.g. re-issuing IDs, a framework
  change). Requires scientific-board sign-off.

Each master file carries a header block:

```yaml
# registry_version: 1.3.0
# effective_date: 2026-07-15
# author: <domain expert>
# framework_version: 39-axis v3.0        # which core framework it targets
# changelog: added 4 modules (H-201..204); fixed A17 on H-015; deprecated H-026
```

Every compiled `data/*.json` embeds the same `registry_version` and `framework_version`, and every
generated **case report** stamps them — so any plan is traceable to the exact data that produced it.

**Storage:** the `knowledge-sources/official/` folder is git-tracked, so full history/diff/rollback
come for free. Tag releases (`registry-v1.3.0`). Keep a top-level `CHANGELOG.md`.

---

## 4. Lifecycle of a module (never hard-delete)

Every module row has a **`status`**: `active` · `deprecated` · `archived` · `draft`.

- **Add:** new row, `status: active`, next free H-Code, MINOR bump. No code change.
- **Correct:** edit the row (axes/dose/safety), PATCH bump, changelog entry.
- **Retire:** set `status: deprecated` (still readable for old reports) → later `archived`.
  **Never delete** — historical reports must remain reproducible.
- **Supersede:** `replaced_by: <H-Code>` pointer so the engine can suggest the successor.

The engine only *selects* `active` modules but can still *resolve/display* deprecated ones cited by
past reports.

---

## 5. Update workflow (each release)

```
Domain expert edits  →  modules_master.xlsx  (bump version + changelog)
        │
        ▼
Validation script    →  scripts/validate_master.py   (see §6) — blocks bad data
        │  (pass)
        ▼
Compile              →  scripts/build_registry.py → data/module_registry.json
                                                    data/axis_module_official.json
        │
        ▼
Re-embed (if modules changed)  →  scripts/embed_knowledge.py  (pgvector)
        │
        ▼
Tests + review       →  pytest (mapping/coverage tests) → merge → tag registry-vX.Y.Z → deploy
```

Deploy = drop the new `data/*.json` in and restart; **no application code changes**. (Same pattern
the engine already uses for seeding.)

---

## 6. Automated validation gate (before any release ships)

`scripts/validate_master.py` must pass — it enforces the confirmed rules:

- **IDs:** every `module_code` (H-Code) unique; `phytocore_code` present; no duplicate canonical
  products (the 1:1 rule) — flag any product appearing under two active codes.
- **Axes:** every `target_axes` value ∈ `A1…A39` (sub-axes rolled up); each active module has ≥1 axis.
- **Coverage:** report which of the 39 axes have **no active module** (today: A37 — expected to be
  KS/Kerra/VitalPlus).
- **Catalogue:** each module resolves to a product record (name/alias/PhytoCore) — unresolved = fail.
- **Dosing:** `dose_type` ∈ {`severity`, `bowel`}; bowel group limited to the approved list.
- **Framework pin:** `framework_version` matches the installed 39-axis framework.

This is the same validation already prototyped while reconciling the three sources — it becomes the
CI gate on the master file.

---

## 7. Onboarding the *first* official master file (immediate next step)

When the domain expert delivers the updated master registry:

1. Drop it in `knowledge-sources/official/modules_master.*` with `registry_version: 1.0.0`.
2. Run `validate_master.py` → fix any flags with the expert (counts, 213–215, NARIS, 188/190, A37).
3. `build_registry.py` → `data/axis_module_official.json`; point the engine's repository at it and
   retire the provisional map.
4. `embed_knowledge.py` → module vectors for RAG.
5. `pytest` + a spot-check report → tag `registry-v1.0.0`.

Until it arrives, the engine runs on the **merged draft** (`docs/module_axis_mapping_DRAFT.csv` →
`suggested_union`) so development continues; swapping to the official file is a data change only.

---

## 8. Ongoing refinement (built-in, no framework change)

- **Outcome learning loop (Phase 4)** already nudges per-axis weights from follow-up outcomes —
  refinement without touching modules.
- **Physician-choice learning:** as experts said, capture whether physicians prescribe primary-only
  vs primary+secondary and feed it back — a data/model signal, not a code change.
- **New science → new modules:** just a MINOR release. New axes or a hierarchy change would be a
  framework `MAJOR` (rare, board-governed) — the only case that touches the core, and even then the
  engine reads it from `data/tspi_axes_39.json`.

---

## Summary

Fixed framework + versioned, status-tracked, validated data files = a registry that grows and
self-corrects indefinitely, with every change traceable and every past report reproducible, and
**zero engine code changes** for routine additions and refinements.
