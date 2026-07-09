"""OCR / report parsing: file -> text -> structured labs.

Pipeline (per the plan): extract text (PDF text layer or image OCR), then structure into
labs. Structuring is local-first: if OCR_USE_LLM is on and a local Ollama is reachable we ask
it for strict JSON; otherwise a deterministic heuristic parser runs so the prototype always
works offline. Either way the output is *candidate* labs (confirmed=False) for human review.
"""
from __future__ import annotations

import json
import re

from app.config import settings

# ---- 1. text extraction --------------------------------------------------

def extract_text(path: str, mime: str, filename: str) -> tuple[str, str]:
    """Return (text, note). Degrades gracefully when OCR libs/binaries are absent."""
    name = (filename or path).lower()
    try:
        if name.endswith(".pdf") or "pdf" in mime:
            try:
                import pdfplumber  # optional dep
                with pdfplumber.open(path) as pdf:
                    return "\n".join((pg.extract_text() or "") for pg in pdf.pages), "pdf:pdfplumber"
            except Exception as e:
                return "", f"pdf-extract-unavailable:{type(e).__name__}"
        if any(name.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff")) or "image" in mime:
            try:
                import pytesseract
                from PIL import Image
                if settings.tesseract_cmd:
                    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
                return pytesseract.image_to_string(Image.open(path)), "image:tesseract"
            except Exception as e:
                return "", f"image-ocr-unavailable:{type(e).__name__}"
        # text/csv or unknown -> read as utf-8
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(), "text:direct"
    except Exception as e:  # pragma: no cover
        return "", f"extract-failed:{type(e).__name__}"


# ---- 2. structuring ------------------------------------------------------

# matches: "CRP 21.57 mg/L (ref < 5.0)", "HbA1c: 6.5 % (4.0-5.6)", "Hemoglobin 10.8 g/dL (12-16)"
_LINE = re.compile(
    r"^\s*(?P<analyte>[A-Za-z][A-Za-z0-9 \-/().]{1,40}?)\s*[:\-]?\s+"
    r"(?P<value>-?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>%|[A-Za-zµ/%\^0-9\.\-]{1,12})?\s*"
    r"(?P<ref>\(?\s*(?:ref\.?\s*)?(?:(?P<op><|>)\s*(?P<bound>\d+(?:\.\d+)?)|"
    r"(?P<low>\d+(?:\.\d+)?)\s*[-–]\s*(?P<high>\d+(?:\.\d+)?))\s*\)?)?\s*$",
    re.IGNORECASE,
)

_STOPWORDS = {"name", "date", "patient", "report", "page", "address", "phone", "dob", "age", "sex"}


def _heuristic(text: str) -> list[dict]:
    out: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) > 80:
            continue
        m = _LINE.match(line)
        if not m:
            continue
        analyte = m.group("analyte").strip(" :-").strip()
        if not analyte or analyte.lower() in _STOPWORDS or len(analyte) < 2:
            continue
        ref_low = ref_high = None
        if m.group("op") == "<":
            ref_high = float(m.group("bound"))
        elif m.group("op") == ">":
            ref_low = float(m.group("bound"))
        elif m.group("low"):
            ref_low, ref_high = float(m.group("low")), float(m.group("high"))
        out.append({
            "analyte": analyte,
            "value": m.group("value"),
            "unit": (m.group("unit") or None),
            "ref_low": ref_low,
            "ref_high": ref_high,
        })
    return out


def _llm(text: str) -> list[dict] | None:
    """Optional local-first structuring via Ollama. Returns None if unavailable."""
    if not settings.ocr_use_llm:
        return None
    try:
        import httpx
        prompt = (
            "Extract lab results from the text as a strict JSON array of objects with keys "
            "analyte, value, unit, ref_low, ref_high. Numbers as numbers; null when unknown. "
            "Return ONLY the JSON.\n\nTEXT:\n" + text[:6000]
        )
        r = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={"model": settings.ollama_model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60,
        )
        r.raise_for_status()
        data = json.loads(r.json()["response"])
        rows = data if isinstance(data, list) else data.get("labs", [])
        return [
            {"analyte": str(x.get("analyte", "")).strip(), "value": str(x.get("value", "")),
             "unit": x.get("unit"), "ref_low": x.get("ref_low"), "ref_high": x.get("ref_high")}
            for x in rows if x.get("analyte")
        ] or None
    except Exception:
        return None


def parse_labs(text: str) -> list[dict]:
    """Structure text into candidate labs. LLM first (if enabled), else heuristic."""
    if not text.strip():
        return []
    return _llm(text) or _heuristic(text)
