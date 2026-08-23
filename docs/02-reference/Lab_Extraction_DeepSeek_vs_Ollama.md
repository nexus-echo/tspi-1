# Lab / Imaging Extraction — DeepSeek vs Ollama (local) models

**Task:** read an uploaded patient report (photo of a lab sheet, a scanned PDF, or a sonography
report) and turn it into structured, reviewable data (labs + imaging findings) for MiHealth.

**Decision (chosen):** run extraction **locally with Ollama** — a **vision** model reads the
images, and a **local text** model structures text-PDF content. No patient data leaves the server.
DeepSeek is **not** used in this pipeline. This document explains why.

---

## The one fact that decides it: DeepSeek's API can't read images

DeepSeek's first-party API is **text-only**. Image/vision understanding exists in their chat *app*
and newer V4 models, but there is **no programmatic image input** on the API today. So "send the
sonography image to DeepSeek and let it read the pixels" is simply **not possible via the API**.
DeepSeek could only help *after* text has already been pulled off the file by something else.

To "read the image with an LLM," you need a **vision** model. The only question is *where it runs*.

## The second fact: PHI governance

A raw lab/sonography file contains the patient's **name, DOB, ID, address**. TSPI's rule is that
only de-identified data (case_id + age band + sex) ever reaches an LLM. Sending raw report files to
**any cloud** LLM breaks that rule. Independently, the hosted DeepSeek service is **not
HIPAA-compliant**, offers **no BAA/DPA**, and routes/stores data on **servers in China** — a
non-starter for regulated health data. Open-weight models run **inside your own infrastructure**
keep the data within your boundary, which is the compliant pattern.

---

## Side-by-side

| Dimension | DeepSeek (hosted API) | Ollama local vision (Qwen2.5-VL / MiniCPM-V / Llama-3.2-Vision) |
|---|---|---|
| **Reads images / scans directly** | ❌ No image input on the API (text-only) | ✅ Yes — native multimodal, reads photos, scans, ultrasound reports |
| **Reads text PDFs / structures text** | ✅ Strong | ✅ Good (e.g. Qwen2.5 14B) |
| **PHI leaves your server?** | ❌ Yes → cloud (servers in China) | ✅ No — 100% on-prem |
| **HIPAA / BAA / data residency** | ❌ No BAA, no residency option | ✅ Compliant pattern (data stays in your boundary) |
| **Per-request cost** | Pay per token | Free after hardware (electricity only) |
| **Works offline** | ❌ Needs internet + their uptime | ✅ Fully offline |
| **Hardware needed** | None (their servers) | A GPU (≈6–12 GB VRAM) for good speed |
| **Document-OCR quality** | N/A for images | ✅ Trained on dense docs/tables/forms |
| **Latency** | Low (their infra) | Depends on your GPU |
| **Governance fit for TSPI** | ✗ Conflicts with de-ID rule | ✅ Aligns with de-ID rule |

**Verdict:** for *reading report images*, DeepSeek is disqualified twice over — it can't take
images on the API, and it wouldn't be PHI-safe if it could. A **local Ollama vision model** is the
correct engine. (DeepSeek remains a fine choice elsewhere — e.g. writing narrative prose from
*already de-identified* facts, which is how the report composer can optionally use it.)

---

## Which local model to pull

All are one `ollama pull` away; the app default is `qwen2.5vl` (override via `VISION_MODEL`).

| Model (Ollama tag) | Size / VRAM | Best for | Notes |
|---|---|---|---|
| **`qwen2.5vl`** *(default)* | 7B ≈ 6–8 GB | Documents, tables, forms, structured JSON output | Strong all-rounder for lab sheets; good multilingual |
| **`minicpm-v`** | 8B ≈ 6 GB | Dense document OCR, tables, invoices | Often the most accurate on scanned docs at low VRAM |
| **`qwen3-vl`** | 8B+ | CJK / multilingual OCR, latest gen | Best when reports mix scripts (e.g. Thai + English) |
| **`llama3.2-vision`** | 11B ≈ 8–10 GB | General vision; widely available | Solid, slightly behind Qwen/MiniCPM on pure OCR |

Text structuring (text PDFs) uses your existing `ollama_model` (default `qwen2.5:14b`); override
via `EXTRACTION_TEXT_MODEL`.

**Practical recommendation:** start with **`qwen2.5vl`** (default). If scanned lab sheets or
handwriting are common, also try **`minicpm-v`** and keep whichever reads your reports best. For
reports containing Thai/CJK, prefer **`qwen3-vl`**.

---

## How it's wired (this repo)

- **Engine:** `apps/ai-engine` → `POST /extract` (`app/pipeline/extraction.py`).
  - Image → local vision model → JSON `{labs, imaging, narrative}`.
  - Text PDF → `pdfplumber` text → local text model → same JSON.
  - Scanned PDF → PyMuPDF rasterizes pages → vision model.
  - **Regex fallback** if models are offline, so it never hard-fails.
  - Always `confirmed=false` → a human confirms before it feeds diagnosis.
- **Portal:** `apps/mihealth-backend` upload → background task calls the engine's `/extract`
  first (smart), falls back to the old local OCR if the engine is unreachable. Raw files stay in
  MiHealth; only confirmed, de-identified labs go to TSPI later. Frontend is unchanged — it still
  reviews the same candidate-labs, now much more accurate.
- **Config:** `VISION_MODEL`, `EXTRACTION_TEXT_MODEL`, `EXTRACTION_BACKEND` (`ollama`|`heuristic`),
  `EXTRACTION_MAX_PAGES`, `PDF_TEXT_MIN_CHARS`.

## Setup
```bash
docker compose up -d --build
docker compose exec ollama ollama pull qwen2.5vl      # vision (reads images/scans)
docker compose exec ollama ollama pull qwen2.5:14b    # text structuring (if not present)
```
