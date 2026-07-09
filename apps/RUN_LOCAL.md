# Running the TSPI Platform locally (without Docker)

This guide lives in `apps/` inside the monorepo. All paths below are relative to it
(`C:\workspace\tspi_new\apps` on Windows).

Three processes:
- **MiHealth backend** — FastAPI on **:8001** (`apps/mihealth-backend`)
- **MiHealth frontend** — Vite dev server on **:5173** (`apps/mihealth-frontend`)
- *(optional)* **TSPI brain** — FastAPI on **:8000** (`apps/ai-engine`), needed for plan generation

The frontend proxies `/api` → `http://localhost:8001`, so you only browse to :5173.
By default MiHealth uses **SQLite** (a file DB) — **no Postgres install required**. A Postgres
option is in section 5.

---

## Current directory structure
```
tspi_new/
├── docker-compose.yml          Unified stack (all services) — see repo README
├── README.md
├── apps/
│   ├── ai-engine/              TSPI brain — FastAPI :8000   (was: tspi_ai_brain)
│   │   ├── app/  scripts/  alembic/  data/  tests/
│   │   ├── requirements.txt  Dockerfile  docker-compose.yml
│   │   └── .env               (your secrets — DEEPSEEK_API_KEY, EMBEDDING_*)
│   ├── mihealth-backend/       MiHealth API — FastAPI :8001 (was: mihealth_portal/backend)
│   │   ├── app/  uploads/
│   │   ├── requirements.txt  requirements-ocr.txt  requirements-postgres.txt
│   │   ├── Dockerfile
│   │   └── .env               (local SQLite by default)
│   ├── mihealth-frontend/      MiHealth web — React/Vite :5173 (was: mihealth_portal/frontend)
│   │   ├── src/  index.html  vite.config.ts  package.json
│   │   └── Dockerfile
│   ├── mihealth-compose.yml    Portal-only compose (reference)
│   └── RUN_LOCAL.md            ← this file
├── docs/                       17 TSPI_*.md + architecture/ + samples/
└── knowledge-sources/          39-axes/ products/ keys-domains/ 200-modules/
                                new_revised_docs/ mihealth-design/ api-demo/ patient-samples/
```

---

## 0. Prerequisites (install once)

- **Python 3.11–3.13 recommended** — check: `python --version` (Windows: also try `py --version`).
  Python **3.14** also works for the core app, but some optional OCR packages may lack 3.14
  wheels yet; see step 1 and Troubleshooting. If you have multiple Pythons, you can target one
  explicitly, e.g. `py -3.12 -m venv .venv` on Windows.
- **Node.js 18+ and npm** — check: `node --version` and `npm --version`
- *(Optional)* **Tesseract OCR** — only needed to OCR **image** lab reports (.png/.jpg). PDF text
  and .txt/.csv work without it.
  - Windows: install "Tesseract at UB Mannheim" build, or `winget install UB-Mannheim.TesseractOCR`
  - macOS: `brew install tesseract`   ·   Linux: `sudo apt install tesseract-ocr`
- *(Optional)* The **TSPI brain** running on `http://localhost:8000` — only needed for the
  "Generate plan" / validate / learning steps. Everything else (register, profile, consent,
  upload, OCR, confirm labs) works without it. See section 6.

---

## 1. Start the MiHealth backend (Terminal 1)

The repo already includes a local `mihealth-backend/.env` (SQLite).

### Windows (PowerShell)
```powershell
cd C:\workspace\tspi_new\apps\mihealth-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```
> **Optional extras** (install only if you need them):
> - Image OCR (.png/.jpg) + PDF text parsing: `pip install -r requirements-ocr.txt`
>   (text/.csv reports work without this; you can always type lab values manually).
> - PostgreSQL instead of SQLite: `pip install -r requirements-postgres.txt` (see section 5).
>
> If PowerShell blocks the activate script, run once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` then re-run Activate.
> Or use cmd.exe: `.venv\Scripts\activate.bat`

### macOS / Linux (bash)
```bash
cd apps/mihealth-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**Success looks like:** `Uvicorn running on http://127.0.0.1:8001`. On first start it creates
`mihealth.db` and seeds the admin account.

**Verify:** open http://localhost:8001/health → `{"status":"ok",...}` and
http://localhost:8001/docs for the API explorer.

Leave this terminal running.

---

## 2. Start the MiHealth frontend (Terminal 2 — a new window)

### Windows (PowerShell)
```powershell
cd C:\workspace\tspi_new\apps\mihealth-frontend
npm install
npm run dev
```

### macOS / Linux
```bash
cd apps/mihealth-frontend
npm install
npm run dev
```

**Success looks like:** `Local: http://localhost:5173/`.

---

## 3. Use the app

Open **http://localhost:5173**.

Seeded admin login:  **admin@mihealth.app**  /  **admin12345**

Suggested walkthrough:
1. **Register** a new patient account (Create an account) → fill profile → grant `ai_analysis`
   consent → save symptoms → upload a lab report.
   - A quick test file: create `labs.txt` containing lines like
     `CRP 21.57 mg/L (ref < 5.0)` and `HbA1c: 6.5 % (4.0-5.6)`.
2. Log out → sign in as **admin** → **Patients** → open the patient → **Review & confirm labs** →
   assign a **doctor** (create one first via the Users page if needed).
3. *(Needs the TSPI brain on :8000)* As admin/doctor → **Generate plan** → review NSS / modules / safety.
4. Sign in as the **assigned doctor** → **Approve / Suggest changes / Reject**.
5. Sign back in as the **patient** → the approved plan shows under *My treatment plan*.
6. As staff record **follow-up outcomes**; as **admin** click **Recalibrate now**.

---

## 4. Stopping / restarting

- Stop either server with **Ctrl+C** in its terminal.
- To restart later: backend → re-activate the venv and run the `uvicorn …` line again;
  frontend → `npm run dev` (no need to reinstall).
- **Reset all data:** stop the backend and delete `mihealth-backend/mihealth.db` (and the
  `mihealth-backend/uploads/` folder). It will re-seed the admin on next start.

---

## 5. (Optional) Use PostgreSQL instead of SQLite

1. Install Postgres 15+ and create a database/user:
   ```sql
   CREATE USER mihealth WITH PASSWORD 'mihealth';
   CREATE DATABASE mihealth OWNER mihealth;
   ```
2. Edit `mihealth-backend/.env` and set:
   ```
   DATABASE_URL=postgresql+psycopg2://mihealth:mihealth@localhost:5432/mihealth
   ```
3. Restart the backend. Tables are created automatically on startup.

---

## 6. (Optional) Run the TSPI brain for plan generation

In a third terminal, start the TSPI brain so it listens on `http://localhost:8000`:
```bash
cd apps/ai-engine          # Windows: cd C:\workspace\tspi_new\apps\ai-engine
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
MiHealth's `.env` already points `TSPI_BASE_URL` at `http://localhost:8000`. If the brain is not
running, plan generation returns a clear "engine unreachable" message; all other features still work.

> **Tip:** to run *everything* (both apps + Postgres + Ollama) in one command, use the unified
> `docker compose up -d --build` from the repo root instead — see the top-level `README.md`.

---

## Troubleshooting

- **`uvicorn: command not found`** — the venv isn't activated, or deps didn't install. Re-activate
  and re-run `pip install -r requirements.txt`.
- **Port already in use** — change the port: backend `--port 8002`; if you change the backend port,
  set `VITE_API_TARGET=http://localhost:8002` before `npm run dev` (PowerShell:
  `$env:VITE_API_TARGET="http://localhost:8002"; npm run dev`).
- **Login fails for the seeded admin** — make sure the email is exactly `admin@mihealth.app`
  (`.local` TLDs are rejected by email validation).
- **CORS errors in the browser console** — confirm the backend is on :8001 and `CORS_ORIGINS`
  includes `http://localhost:5173` (it does by default).
- **Image OCR shows "could not auto-read"** — install Tesseract (step 0) or just type the lab
  values manually in *Review & confirm labs* (PDF text and .txt always work).
- **`Pillow x.y does not support Python 3.14` / a package fails to build a wheel** — that package
  is an *optional* one and is no longer in core `requirements.txt`. Install the core set (which
  has no such pins) and skip the extra, or install the extra only when needed:
  `pip install -r requirements-ocr.txt`. If an OCR package still won't install on 3.14, either
  upload **text/PDF** reports (no Pillow needed) and type any image-only values manually, or use
  Python 3.12 for the backend venv (`py -3.12 -m venv .venv`).
- **bcrypt/psycopg2 build errors on install** — ensure you're on Python 3.11+ and have a recent
  `pip` (`python -m pip install --upgrade pip`), then retry.
- **Tesseract install fails with `0x800704c7` (winget) / nothing installs** — the installer
  needs admin rights and the UAC prompt was cancelled. Open **PowerShell as Administrator**
  and re-run `winget install UB-Mannheim.TesseractOCR`, clicking **Yes** on the UAC dialog —
  or download the UB-Mannheim `tesseract-ocr-w64-setup-*.exe` and right-click → **Run as
  administrator**. Then open a **new** terminal and check `tesseract --version`. If Tesseract
  installed but isn't found, set `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe`
  in `mihealth-backend/.env` and restart the backend. (Tesseract is only for image OCR — PDF/text
  reports and manual entry work without it.)
- **`ValueError: password cannot be longer than 72 bytes` on startup** — caused by an old
  passlib + bcrypt 5.x mismatch. This is fixed: the app now uses the `bcrypt` library
  directly. Update your venv: `pip install -r requirements.txt` (installs `bcrypt`), then
  restart the backend. If the first run left an empty DB, you can also delete
  `mihealth-backend/mihealth.db` to re-seed cleanly.
