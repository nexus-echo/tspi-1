"""Production-pilot governance helpers.

When `settings.pilot_mode` is on, the engine may use PROVISIONAL/candidate clinical datasets so the
pipeline runs end-to-end — but every report is clearly watermarked and must never auto-reach a
patient. Physician approval is still required. This is the domain-experts' recommended
"clinician shadow pilot": provisional data is a review aid, not clinical authority.
"""
from __future__ import annotations

from app.config import settings

PILOT_NOTICE = ("PILOT — PROVISIONAL, NOT CLINICALLY VALIDATED. For clinician review only. "
                "NOT FOR PATIENT RELEASE.")


def is_pilot() -> bool:
    return bool(settings.pilot_mode)


def report_language(requested: str | None = None) -> str:
    lang = (requested or settings.report_language_default or "en").strip().lower()
    return lang if lang in {"en", "th"} else "en"
