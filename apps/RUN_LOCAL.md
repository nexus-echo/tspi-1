# Running the TSPI AI Platform locally (without Docker)

Paths are relative to `apps/` (`C:\workspace\tspi_new\apps` on Windows). This repo is the AI
platform: the **engine** and the **MCP server**. The **MiHealth portal** now lives in its own repo —
its local-run guide moved there too.

Two processes:
- **TSPI engine** — FastAPI on **:8000** (`apps/ai-engine`) — the brain; everything depends on it.
- *(optional)* **TSPI MCP server** (`apps/tspi-mcp`) — only to drive the engine from an AI chat client.

By default the engine uses **SQLite** (a file DB) — no Postgres required. A Postgres option is in §4.

---

## 0. Prerequisites
- **Python 3.11–3.13** — `python --version` (Windows: also `py --version`).
- *(optional)* **Ollama** for local embeddings + lab/imaging extraction (`ollama pull bge-m3`, `ollama pull qwen2.5vl`).

---

## 1. Start the engine (Terminal 1)

### Windows (PowerShell)
```powershell
cd C:\workspace\tspi_new\apps\ai-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # add DEEPSEEK_API_KEY etc. (optional for core use)
python -m scripts.seed_db       # bootstrap the knowledge tables
uvicorn app.main:app --reload --port 8000
```

### macOS / Linux (bash)
```bash
cd apps/ai-engine
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed_db
uvicorn app.main:app --reload --port 8000
```

**Verify:** http://localhost:8000/health → `{"status":"ok",...}` · API explorer at
http://localhost:8000/docs. Leave it running.

---

## 2. (Optional) Connect an AI chat client via the MCP server

See `apps/tspi-mcp/README.md`. In short:
```powershell
cd C:\workspace\tspi_new\apps\tspi-mcp
python -m venv .venv ; .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
Then add the `tspi-ai-brain` block from `claude_desktop_config.example.json` to Claude Desktop
(Settings → Developer → Edit Config) and restart it. The MCP server calls the engine at
`TSPI_ENGINE_URL` (default `http://localhost:8000`).

---

## 3. Run the tests
```bash
cd apps/ai-engine && pytest        # engine (82 tests)
cd apps/tspi-mcp  && pytest        # MCP de-identification gate
```

---

## 4. (Optional) PostgreSQL instead of SQLite
1. Install Postgres 15+ with pgvector and create the DB/user.
2. In `ai-engine/.env` set `DATABASE_URL=postgresql+psycopg://tspi:tspi@localhost:5432/tspi`.
3. Apply migrations: `alembic upgrade head`, then re-run `python -m scripts.seed_db`.

> To run the engine + Postgres in one command, use `docker compose up -d --build` from the repo root
> (see the top-level `README.md`). The MiHealth portal is a separate repo and reaches this engine over
> HTTP via `TSPI_BASE_URL`.

---

## Troubleshooting
- **`uvicorn: command not found`** — the venv isn't activated, or deps didn't install. Re-activate and
  `pip install -r requirements.txt`.
- **Port already in use** — change it: `uvicorn app.main:app --port 8010` (update the MCP's
  `TSPI_ENGINE_URL` to match).
- **`seed_db` TypeError / empty tables** — delete `apps/ai-engine/data/tspi.db*` and re-run
  `python -m scripts.seed_db`.
- **Embeddings/extraction do nothing** — those need Ollama running (`OLLAMA_BASE_URL`) with the models
  pulled; the default `hash` embedding backend needs no models and is fine for dev.
