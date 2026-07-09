# TSPI Phase 0 — Status: COMPLETE (knowledge foundation)

Phase 0 of `tspi_ai_brain` is built, run, and tested. The engine no longer uses a hand-typed seed
— it now reads the **official knowledge base** from a real database.

## What was built
1. **Product dedup tool** (`scripts/build_product_registry.py`) — executes the owner's rule
   *one module = one record*: parses all **276** `products/*.md`, groups duplicates by normalized
   name, keeps the most complete, archives the rest. Output:
   - `data/product_registry.json` — **153 canonical products** (+ aliases + archived IDs)
   - `data/product_dedup_report.json` — every group, for clinical review
   - Result: **276 → 153** products · 65 duplicate groups · 123 files archived
     (e.g. KS ×5 → keep 1, NOURISHING BLOOD ×5 → keep 1).
2. **Database layer** (`app/knowledge/db.py`) — SQLAlchemy engine; **SQLite** for dev/tests,
   **PostgreSQL** in prod via `DATABASE_URL` (same models).
3. **Loader** (`scripts/seed_db.py`) — loads the official framework + 39 axes + registry:
   **3 keys · 9 steps · 13 domains (12 official + 1 provisional meta) · 39 axes · 119 sub-axes ·
   153 products**. Idempotent and reproducible.
4. **DB-backed repository** (`app/knowledge/repository.py`) — same interface as before, now queries
   the DB. Axis names/domains come from the official data; modules resolve against the registry
   (unresolved ones are flagged, not invented). Self-bootstraps if the DB is empty.

## Verified
- `python -m scripts.seed_db` → `{keys:3, steps:9, domains:13, axes:39, sub_axes:119, products:153}`
- Engine reads real axis data, e.g. `A17 → Microbiome Ecology (D5)`, `A36 → Oncology (D12)` —
  confirming the **official 12-domain grouping** (A16/A17 in D5 Digestive–Gut, not the old draft).
- All **5/5 tests pass**; `/report` runs end-to-end on the DB-backed catalog with NSS/SPS/dosing.

## Still provisional (awaiting the updated master registry file)
- The **module registry** — rules now **decided** (domain experts): **1 module = 1 product**,
  keyed by **H-Code**, ~200 target modules. Awaiting the master file for **final active counts** +
  dedup of the 61 duplicate code-sets. (Modules are 1:1 with products, *not* groupings.)
- The **module→axis map** — rules decided (map to **39 axes**, each module's own list); a merged
  draft (`docs/module_axis_mapping_DRAFT.csv`) is ready; official values land with the master file.
- **Axes 37–39** domain placement (loaded under a provisional meta-domain `D12M`) — still to confirm;
  expert confirmed A37 = *Protein Quality Control* with interim support KS/Kerra/VitalPlus.

## How to run
```bash
cd tspi_ai_brain
pip install -r requirements.txt
python -m scripts.build_product_registry /path/to/products data
python -m scripts.seed_db
uvicorn app.main:app --reload     # POST /report now uses the official DB-backed knowledge
```
