# Plan — Split MiHealth (frontend + backend) into its own repo

*Goal: move the MiHealth portal (frontend + backend) out of `tspi_new` into a new **`mihealth`** repo.
The current repo keeps the AI platform (`ai-engine` + `tspi-mcp`). The only link between them is the
de-identified REST contract (`/report`, `/extract`) — there is **no code-level coupling** (verified:
MiHealth imports none of the engine's code), so this is a clean network-boundary split.*

> Git is blocked in this workspace, so the commands below are run **on your machine**. History-preserving
> extraction uses `git filter-repo`.

---

## 1. Target layouts

**New `mihealth` repo** (clean, matches the existing `apps/mihealth-compose.yml` which already points at
`./backend`, `./frontend`, and the engine at `host.docker.internal:8000`):
```
mihealth/
├── backend/                 (was apps/mihealth-backend/)
├── frontend/                (was apps/mihealth-frontend/)
├── docker-compose.yml       (was apps/mihealth-compose.yml)
├── docs/
│   ├── MiHealth_Portal_Design_and_Implementation_Plan.md
│   ├── TSPI_MiHealth_API_Contract.md          (copy of the shared contract)
│   └── TSPI_MiHealth_Input_Contract_Spec.md   (copy of the shared contract)
├── README.md
└── .gitignore
```

**Current repo `tspi_new`** after the split (AI platform):
```
tspi_new/
├── apps/
│   ├── ai-engine/
│   ├── tspi-mcp/
│   └── RUN_LOCAL.md         (updated — AI only)
├── docs/                    (engine/project docs stay; contract docs remain here as source of truth)
├── knowledge-sources/
├── docker-compose.yml       (mihealth services removed)
└── README.md               (updated)
```

## 2. What moves / stays / is shared

| Item | Action |
|---|---|
| `apps/mihealth-backend/` | **MOVE** → `backend/` |
| `apps/mihealth-frontend/` | **MOVE** → `frontend/` |
| `apps/mihealth-compose.yml` | **MOVE** → `docker-compose.yml` (new repo root) |
| `docs/02-reference/MiHealth_Portal_Design_and_Implementation_Plan.md` | **MOVE** (portal-only) |
| `docs/02-reference/TSPI_MiHealth_API_Contract.md` | **COPY** (shared contract; engine keeps canonical) |
| `docs/02-reference/TSPI_MiHealth_Input_Contract_Spec.md` | **COPY** (shared contract; engine keeps canonical) |
| `apps/ai-engine/`, `apps/tspi-mcp/` | **STAY** |
| root `docker-compose.yml` | **EDIT** — remove `mihealth-db`, `mihealth-api`, `mihealth-web` + `mihealth_*` volumes |
| root `README.md`, `apps/RUN_LOCAL.md` | **EDIT** — drop MiHealth run steps; link to the new repo |
| `knowledge-sources/`, other `docs/` | **STAY** |

**Contract = source of truth stays in the engine repo.** The two `*Contract*` docs describe the
`/report` + `/extract` interface. Keep them canonical in `tspi_new` and copy into `mihealth`; the
engine's live OpenAPI (`/openapi.json`, `/docs`) is the machine-readable source.

---

## 3. Commands — extract into the new repo (history-preserving)

```bash
# one-time tool install
pip install git-filter-repo

# 1) fresh clone to carve from (never run filter-repo on your working clone)
git clone <CURRENT_REPO_URL> mihealth && cd mihealth

# 2) keep only MiHealth paths AND restructure to the new layout
git filter-repo \
  --path apps/mihealth-backend/ \
  --path apps/mihealth-frontend/ \
  --path apps/mihealth-compose.yml \
  --path docs/02-reference/MiHealth_Portal_Design_and_Implementation_Plan.md \
  --path docs/02-reference/TSPI_MiHealth_API_Contract.md \
  --path docs/02-reference/TSPI_MiHealth_Input_Contract_Spec.md \
  --path-rename apps/mihealth-backend/:backend/ \
  --path-rename apps/mihealth-frontend/:frontend/ \
  --path-rename apps/mihealth-compose.yml:docker-compose.yml \
  --path-rename docs/02-reference/:docs/

# 3) push to the new (empty) GitHub repo   (filter-repo drops the old remote for safety)
git remote add origin <NEW_MIHEALTH_REPO_URL>
git branch -M main
git push -u origin main
```
Result: a `mihealth` repo containing only `backend/`, `frontend/`, `docker-compose.yml`, `docs/` — each
with its **original commit history** for those files.

## 4. Commands — clean the original repo

```bash
cd <path-to>/tspi_new
git checkout -b chore/split-mihealth       # or work on your feature branch

git rm -r apps/mihealth-backend apps/mihealth-frontend apps/mihealth-compose.yml

# EDIT root docker-compose.yml: delete the mihealth-db / mihealth-api / mihealth-web services
#   and the mihealth_pgdata / mihealth_uploads / mihealth-db volumes. Keep tspi-db, tspi-api, ollama.
# EDIT README.md and apps/RUN_LOCAL.md: remove MiHealth bring-up steps; add a link to the new repo.
# (Optional) remove the portal-only doc that was moved:
git rm docs/02-reference/MiHealth_Portal_Design_and_Implementation_Plan.md

git add -A
git commit -m "chore: split MiHealth (frontend+backend) into its own repo"
git push -u origin chore/split-mihealth
```

> Fallback if you don't want `git filter-repo` (loses per-file history): copy `apps/mihealth-backend`,
> `apps/mihealth-frontend`, `apps/mihealth-compose.yml` into a new folder, restructure as §1,
> `git init`, one initial commit, push.

---

## 5. Post-split wiring (do these before it runs)

1. **New repo layout already matches** `docker-compose.yml` (was `mihealth-compose.yml`): it builds
   `./backend` and `./frontend` and sets `TSPI_BASE_URL: http://host.docker.internal:8000`. For a real
   server deployment, change that to the engine's reachable URL (host / VPN / Tailscale IP), since the
   two stacks are now on separate compose networks.
2. **Engine URL in backend config:** `backend/app/config.py` → `tspi_base_url` (env `TSPI_BASE_URL`)
   must point at the running engine.
3. **When engine auth is ON (Phase B):** the MiHealth backend calls the engine **directly**, so its
   engine client (`backend/app/tspi.py`) must present `Authorization: Bearer <one of the engine's
   SERVICE_TOKENS>` and forward `X-TSPI-User-Id / -Role / -Clinic-Id` — the same pattern the MCP client
   already uses. Add a `TSPI_SERVICE_TOKEN` (+ identity) to the backend. *(Small follow-up task.)*
4. **New repo hygiene:** add `README.md`, `.gitignore` (node_modules, `.venv`, `__pycache__`, `.env`,
   `uploads/`), and its own CI. `.env.example` for the backend (DB URL, `TSPI_BASE_URL`, JWT secret,
   encryption key, service token).
5. **Contract governance:** add contract tests in `mihealth` against the engine's OpenAPI so the
   `/report` + `/extract` shapes can't drift silently across repos.

## 6. Verification checklist

- [ ] `mihealth` repo: `docker compose up` builds backend + frontend; frontend loads; login works.
- [ ] Backend reaches the engine (`/report`, `/extract`) at the configured `TSPI_BASE_URL`.
- [ ] `tspi_new`: `docker compose up` starts only tspi-db + tspi-api (+ ollama); engine tests still pass.
- [ ] No dangling `mihealth` references in `tspi_new` (`grep -rIn mihealth` returns only historical/doc mentions).
- [ ] Contract docs present in both repos; engine's OpenAPI is the machine-readable source.

## 7. Trade-off reminder

Splitting simplifies each repo and gives independent CI/versioning/ownership, but the `/report` +
`/extract` **contract now spans two repos** — manage it with the engine's OpenAPI + contract tests to
prevent drift, and expect cross-repo PRs when a change touches both. The de-identification boundary
remains the interface: MiHealth owns PII; the engine only ever receives de-identified cases.
