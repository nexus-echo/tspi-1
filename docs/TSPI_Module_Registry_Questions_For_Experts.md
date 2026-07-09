# TSPI — Official Module Registry: Questions for Domain Experts

> ## ✅ ANSWERED — domain-expert responses received (`docs/tspi developer answer.pdf`)
> **12 of 17 questions are resolved; the remaining 5 are data cleanups the expert will deliver in
> an updated master registry file.** Resolution summary is in the next section; the original
> questions are kept below for reference. Full analysis: this file's companion answers PDF.
>
> **Headline decisions:** 1 module = 1 product · key by **H-Code** now (PhytoCore later) ·
> map to **39 axes** (use each module's full axis list) · **severity-level dosing** except a
> **bowel-dosing group** · contraindications **inside each module entry** · English canonical name.

**Blocker:** Part A · A1 — Official Module Registry & module→axis map
**Purpose:** get clinical/domain sign-off so the AI engine can map each *axis* to the correct
*module(s)*. Right now the engine runs on a provisional placeholder; the real mapping exists in
your source files but the three sources disagree and use inconsistent IDs.

---

## Resolution summary (from the domain-expert answers)

| # | Question | Status | Resolution |
|---|---|---|---|
| Source | Excel(282) / JSON(65) / MD(276) — which? | ⏳ Master file | Merge to one canonical record; authoritative list comes in the updated master file |
| 1a | Module = product or bundle? | ✅ | **1 module = 1 product**; no bundles, no sub-modules |
| 1b | Duplicate codes | ✅ | Same product; legacy-export duplicates → one canonical record each |
| 1c | Authoritative ID | ✅ | **H-Code** primary key now; PhytoCore becomes permanent scientific ID later |
| 1d | Position in hierarchy | ✅ | Lowest layer: 3 Keys→9 Steps→12 Domains→39 Axes→**180 Biological Networks→200 Modules**; each module names its axes |
| 1e | Active module/product counts | ⏳ Master file | Provided in the forthcoming master file |
| 2a | A37 has no module | ✅ (interim) | Assign **KS, Kerra, VitalPlus** to A37; design for continuous expansion |
| 2b | 3 modules with no axes (213–215) | ⏳ Master file | Resolved in the registry update |
| 2c | Axis conflicts (NARIS, 30/54/64/97/201) | ⏳ Master file | Corrected in the registry update |
| 2d | 2 unmatched to registry (188, 190) | ⏳ Master file | Folded into the registry cleanup |
| 2e | Primary vs secondary scope | ✅ | Module carries its **full** axis list; AI flags primary/secondary per patient; **physician decides**; AI **learns** from prescribing |
| 3a | Axis vs sub-axis | ✅ | Map to **39 axes only**; sub-axis not required |
| 3b | Dosing source of truth | ✅ | **Severity-level** dosing; exceptions = bowel modules **KS, Be Lax, Cathartic, Lypholax, Venta** (own dosing: 1–4 caps at bedtime + waking) |
| 3c | Contraindications/safety | ✅ | Stored **inside each module entry**, not a separate DB |
| 3d | Canonical identifier | ✅ | **PhytoCore Code** is the long-term canonical scientific ID |
| 3e | Language | ✅ | **English** canonical; Thai = localized display only |
| 3f | 180 Networks layer | ✅ | Modules attach **directly to 39 axes**; networks are an intermediate knowledge layer |

**Design principle (expert):** build the registry as a *living* system — support **versioning,
future module additions, and ongoing refinement without changing the core TSPI framework**.
(Verified against catalogue: KS, KERRA, VitalPlus, B-LAX, Cathartic, LYPHOLAX, Ya Venta all
resolve.) See `docs/TSPI_Master_File_Update_Plan.md` for how we maintain the master files.

---

## Original questions (for reference — see resolution above)

## Which source should we build on?

For TSPI modules we have **3 different sources**, and they don't agree on how many modules exist:

1. **Excel file** — 282 modules
2. **JSON file** — 65 modules
3. **MD files** — 276 modules

**Please tell us which of these three should be treated as the authoritative source for design and
development** — or whether they should be reconciled/merged into one master list. Everything below
helps you make that call.

---

## 1. Module ↔ Product — the core question

**What we need to know:** *Is one "module" exactly one product, or a group of products?*

**What the data currently shows** (this is the key evidence): the **same product appears under
several different module codes**. Examples from `modules_consolidated.json`:

| Product (canonical) | Module codes it appears under |
|---|---|
| HO REN YIN MIXTURE | `H-009`, `H-027`, `17`, `31`, `105` |
| BUTEA SUPERBA CAPSULE | `H-006`, `60`, `70` |
| STOMMA CAPSULE | `H-013`, `3`, `56`, `66` |
| B-LAX CAPSULE | `H-015`, `5`, `58`, `68` |

Overall: **61 products** are mapped by **more than one** module code, and **166 modules** are
backed by **more than one** source `.md` file. The headline counts also don't line up:

| Source | Count |
|---|---|
| Canonical products (deduped registry) | **153** |
| "200 modules" (the name of the sheet) | ~200 |
| Rows in the xlsx (with a code) | **271** |
| Product `.md` files | **276** |
| Consolidated entries | **274** |

**Questions for you:**

1a. Is a **module = one product** (1:1), or is a module a **protocol/bundle of several products**?

1b. When the same product shows up under codes like `H-009`, `17`, `31`, `105` — are those
**duplicate records of one product** (different exports that we should merge), or **genuinely
different modules** that happen to reuse the same product?

1c. What is the **authoritative ID scheme** and **authoritative count**? Should we key modules by
the `H-…` codes, the plain numbers, or the PhytoCore code? How many modules should exist —
~153, ~200, or ~271?

1d. Where does a "module" sit in the framework hierarchy
(3 Keys → 9 Steps → 12 Systems → 39 Axes → **180 Living Networks** → Modules)? Is a module the
same thing as a Living Network, or a level below it?

1e. **How many currently ACTIVE modules and ACTIVE products does the TSPI system have today?**
This is the single number we most need. Our sources give conflicting totals (153 / ~200 / 271 /
276 — see the table above), and some entries look like duplicates or legacy records. Please
confirm:
- the count of **active products** (the actual catalogue items in use), and
- the count of **active modules** (as you define a module in 1a),
- and whether any of the entries above are **archived / deprecated / not in production** and should
be excluded.

---

## 2. Missing / conflicting axis details

**2a. One axis has NO module at all — A37.**
`A37 = "Protein Quality Control System"` (Domain 12 – Proteostasis & Cellular Integrity; sub-axes:
protein folding/chaperones, ER-stress/UPR, etc.). No product in any of the three sources maps to it.
→ *Is there a module that addresses A37, or is it intentionally not covered by a phytochemical
module (e.g. handled by lifestyle/other means)?*

**2b. Three modules have NO axis mapping in any source** — codes `213`, `214`, `215`.
→ *Are these real modules whose axis mapping is simply missing, or blank/spacer rows to delete?*

**2c. Five modules where the sources share NO common axis** (worst conflicts) — codes
`30`, `54`, `64`, `97`, `201`, plus **NARIS** flagged earlier.
→ *For these, which source's axis list is correct?* (See their rows in the CSV for the exact lists.)

**2d. Two modules don't match the 153-product registry** — codes `188`, `190`.
→ *Are these products missing from the catalogue, or renamed/merged?*

**2e. The primary-vs-secondary scope decision (affects every module).**
The xlsx lists a **narrow/primary** axis set; each product's `.md` lists **primary + many
secondary** axes (in 87% of cases the xlsx is a strict subset of the `.md`).
→ *Should the engine treat a module as relevant to its **primary axes only** (more selective
treatment plans) or **primary + secondary** (broader plans)?* And should secondary axes be
**weighted lower** than primary?

---

## 3. Other open questions

3a. **Axis vs sub-axis granularity.** Each axis has sub-axes (e.g. A37 → 37A, 37B). Should modules
map to the **parent axis** (A1–A39) only, or down to **sub-axes** where the source specifies them?

3b. **Dosing source of truth.** Is the recommended dose defined **per module**, or purely by the
severity table (Level 0–3)? When a module has its own dose (e.g. "2–4 capsules, 3–4×/day") *and*
a severity level applies, which wins?

3c. **Contraindications / safety.** Should the module registry carry each module's
contraindications (conditions/meds), or is that a separate official safety table? Several `.md`
files have "Drug-Herb Interaction: None" — is that "verified none" or "not yet filled"?

3d. **PhytoCore code meaning.** Some PhytoCore codes are structured (`TSPI-CURCUMA-01`), others are
descriptive names (`Absorn Women's Internal Harmony Module`). Which is the canonical module
identifier we should standardise on?

3e. **Language.** Product/module names appear in Thai and English. Which language string is the
canonical name for matching and display?

3f. **The "180 Living Networks" layer.** Do modules attach to axes directly (current assumption),
or should they attach to Living Networks, which then roll up to axes?

---

## What your answers unblock

Once we have (1) the module↔product definition + authoritative IDs, (2) the confirmed axis scope
(primary vs primary+secondary), and (3) resolution of the ~11 problem modules + A37, we can:
build the official `axis_module_official.json`, switch the engine off the provisional map, embed
the modules for semantic search, and turn on accurate, catalogue-resolved treatment
recommendations. Everything else on the engine side is already built and tested.

*Fastest way to answer Section 2: open the flat spreadsheet view of the merged sources, filter the
`needs_review` column, and edit those rows — that alone clears most of the blocker.*
