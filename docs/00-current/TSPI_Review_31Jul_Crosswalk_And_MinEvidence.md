# Verification — Expert Review of our Crosswalk + Minimum-Evidence deliverables (31 Jul 2026, doc 2)

*Source: `inbound/tspi answer for developing 31.07.2026(2).pdf` (12 pages). This is a **QA review of
two artefacts we produced** — `latest-data/network_crosswalk_FULL_DRAFT.csv` and the "Axis Minimum
Evidence" tab of `latest-data/TSPI_Master_Data_Templates.xlsx` — reviewed from screenshots. It is
**not** a new set of answers to open questions.*

---

## 1. Does it resolve any open issue?

**No blocker is fully resolved — but it advances Blocker 2.**

- **Blocker 2 (Networks): partial progress, still open.** The review keeps every mapping
  `status = CANDIDATE` and explicitly says a full row-by-row approval "requires the complete
  `network_crosswalk_FULL_DRAFT.csv`" (they reviewed screenshots, not the file). It does, however,
  **confirm three mappings** (N033→A15, N048→A11, N053→A12) and gives **semantic correction rules**
  for the ambiguous categories (§7 below), which materially improves our candidate suggestions.
- **Blocker 1 (Module Registry):** untouched — still pending the APPROVED file.
- **Network Edge Registry:** reaffirmed as *still required* before the network layer is operational.
- **Clinical content** (minimum-evidence rules, cut-offs, grades): still to be authored.

So: a useful **review gate + correction set**, not a resolution.

## 2. What it confirms about our current design ✅

Everything we built to the 31 Jul spec is validated by this review:

- **Network identity split** — `network_code` (permanent, e.g. `LBN-DET-PHASE1`) separate from
  `network_number` and `legacy_display_id`. *We implemented exactly this (our seed uses `LBN-###`).*
- **Domain derived from the approved Primary Axis**, not authored. *We implemented this.*
- **The five axis states** (NOT_ASSESSED / AXIS_CANDIDATE / PROVISIONALLY_ASSESSED / ASSESSED /
  HIGH_CONFIDENCE_ASSESSED). *Implemented.*
- **CANDIDATE status, mapping_confidence as a review aid (never a clinical score), NOT_ASSESSED never
  0/50, 39 Axes stay central, networks explain not replace.** *All already in our design.*
- Our A1–A39 min-evidence list is "structurally correct" and correctly drops CELA as an axis.

## 3. What is new — actionable for us

Five concrete items, all small-to-medium and none conflicting with the engine:

**3.1 Delete the `A0 — example — delete` row (and the other tab example rows).** They call this out
specifically: it must be **physically removed**, not just marked, because a loader could ingest it as
a real axis. *Fix our template generator to omit example rows (or place them on a separate,
non-ingested legend).* Applies to all 5 tabs, not just Min-Evidence.

**3.2 Enrich the network crosswalk schema.** Our FULL draft is missing fields they require. Add:
`network_name_th`, `network_scope`, explicit `secondary_axis_codes[]`, `mapping_reason`,
`reviewed_by`, `review_date`, `network_registry_version`, and keep **one clear Primary / Secondary**
(no ambiguous "Axis 1 / Axis 2" columns).

**3.3 Formalise the confidence scale** with their named bands (embed as a legend):
`1.00 exact · 0.67 strong · 0.50 plausible · 0.33 ambiguous · 0.17 weak · 0.00 no safe mapping`.
Our current token-overlap numbers should be bucketed to these bands.

**3.4 Bake in the §7 semantic corrections** (these fix wrong auto-suggestions and pre-fill better
candidates for review):

| Network pattern | Primary Axis | Notes |
|---|---|---|
| Glucose Variability | **A5** | secondary A8/A9/A27 by scope (not DNA-repair) |
| DNA Damage Sensing | **A11** | not connective tissue/structural |
| Fatty-Acid / Beta-Oxidation | **A8** | secondary A6; A6 primary only if scope is systemic lipid burden |
| Cardiac networks | **by mechanism** | organ reserve→A35 · endothelial→A20/A21 · hemodynamic→A23 · energy→A8 · autonomic→A34 (not all A20) |
| Brain / cognition / synaptic | **A34** | secondary A12/A20/A21/A9 |
| Sensory (vision/hearing/smell/taste) | **A36** | A34 secondary only if central processing |
| Reproductive | **A31 / A32 / A36** by mechanism | not A20 just for vascularization |
| Liver Repair | **by scope** | regeneration→A24 · fibrosis→A25 · reserve→A35 · detox→A15 · DNA repair→A11 (not auto DNA-repair) |

**3.5 Expand the Minimum-Evidence template to the structured schema** (`core/supporting/optional_
evidence[]`, `minimum_core_count`, `minimum_total_weight`, `required_modalities[]`, `accepted_inputs[]`,
`exclusion_rules[]`, `allow_provisional_assessment`), weights CORE=3/SUPPORTING=2/OPTIONAL=1; status
`TEMPLATE`, authoritative=false. (Examples given: A26 needs CBC; A37 needs verified oncology evidence;
A19 needs colon-specific evidence, not constipation alone.)

Also reaffirmed (already on our roadmap): **Network Edge Registry** with the full edge schema, and
**production gates** (unapproved mapping → NOT_ASSESSED; undefined min-evidence → axis cannot score;
confidence never used in patient scoring).

## 4. Bottom line

This is an **approval-workflow review**, not an unblock. It confirms our architecture is on track,
corrects ~8 candidate-mapping categories, and hands us a clean punch-list (delete example rows, enrich
the crosswalk, define the confidence bands, apply the §7 corrections, expand the min-evidence schema).
None of it changes the engine; it sharpens the two review spreadsheets and the still-pending network
edge + min-evidence registries. Blocker 2 stays open pending the expert's row-by-row sign-off of the
enriched crosswalk.
