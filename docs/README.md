# TSPI docs — index

Organised so you only need to open a few files to know the current state. **Start with
[`PROJECT_STATUS.md`](./PROJECT_STATUS.md).**

## Folders

| Folder | What's in it | Load for context? |
|---|---|---|
| **`PROJECT_STATUS.md`** | Single source of truth: what's built, what's left, blockers, decisions | **Yes — first** |
| `00-current/` | Active docs: latest expert analysis, the outbound data request, demo runbook | Yes, when relevant |
| `01-plans/` | Current implementation plans (phase plan; networks/PII/CRUD plan) | When planning code |
| `02-reference/` | Stable specs & contracts (API/input contracts, module-registry spec, requirements summary, master prompt, architecture report, deployment/cost, methodology) | Occasionally |
| `inbound/` | **Client-received source docs** — every expert answer/comment PDF + client feedback | Rarely (summarised in verifications) |
| `latest-data/` | Working data outputs — verified networks CSV, network crosswalk, master-data templates | When touching data |
| `data/` · `architecture/` · `samples/` | Original client source files, architecture PDFs, sample report | Rarely |
| `archive/` | **Superseded** — old question rounds, old verifications, old plans/reports, stray files. Normally never load | No |

## `archive/` breakdown

- `archive/questions/` — earlier outbound question rounds + the resolved 5-question sheet and the
  open-questions/blockers tracker (all superseded by `00-current/TSPI_Data_Request_To_Complete_Project.md`
  and the 31 Jul answer).
- `archive/verifications/` — 16 Jul verification, Round-3 KB update, Phase-3 gap analysis, Phase-0 docs.
- `archive/plans/` — early build plan.
- `archive/reports/` — old case reports & sample templates.
- `archive/data/` — superseded module-axis CSVs (replaced by the registry converter + latest-data).
- `archive/misc/` — stray/unrelated files (Windows shortcut, render scratch, unrelated spreadsheet).

## Where things live (internal quick-load map)

*(Moved here from PROJECT_STATUS.md — PROJECT_STATUS is now a client-shareable document and no longer
carries internal file paths.)*

| Need | Load |
|---|---|
| Current state / client update | `PROJECT_STATUS.md` |
| Latest expert analysis (31 Jul answer) | `00-current/TSPI_Answers_31Jul_Verification.md` |
| Review of our crosswalk + min-evidence deliverables | `00-current/TSPI_Review_31Jul_Crosswalk_And_MinEvidence.md` |
| Outbound ask + fill-in templates | `00-current/TSPI_Data_Request_To_Complete_Project.md` |
| Bring-up / demo | `00-current/TSPI_AI_Brain_Demo_Runbook.md` |
| Phase plan (code changes) | `01-plans/TSPI_Implementation_Plan_Phases_5_to_12.md` |
| Networks / PII / CRUD plan | `01-plans/TSPI_Implementation_Plan_Networks_PII_CRUD.md` |
| Stable specs / contracts | `02-reference/` |
| Raw client documents | `inbound/` · source files in `data/`, `architecture/` |
| Working data outputs | `latest-data/` |
| History (superseded) | `archive/` — normally never load |

**Engine code:** `apps/ai-engine/` (see the demo runbook to run it).

## Conventions going forward

- One dated verification per client answer → `00-current/`; the previous one moves to
  `archive/verifications/`.
- Raw client PDFs always land in `inbound/`.
- `PROJECT_STATUS.md` is updated whenever build state or blockers change, so it stays the only file
  needed to resume.
