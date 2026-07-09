"""DB-backed knowledge repository (Phase 0).

Reads the official catalog (39 axes, 12+meta domains, keys, steps, 153 products) from the
relational DB (SQLite dev / PostgreSQL prod). Same method signatures as the old in-memory seed,
so nothing upstream changes. The axis->module map is still PROVISIONAL (official map pending);
module names are resolved against the product registry and unresolved ones are flagged.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.knowledge.db import get_session, init_db
from app.knowledge.models import Axis, Domain, Product

_DATA = Path(__file__).resolve().parent.parent.parent / "data"


def _norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


@lru_cache
def _provisional_axis_modules() -> dict:
    return json.loads((_DATA / "axis_module_provisional.json").read_text(encoding="utf-8"))["map"]


@lru_cache
def _registry_norms() -> frozenset:
    try:
        reg = json.loads((_DATA / "product_registry.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return frozenset()
    names: set[str] = set()
    for r in reg:
        names.add(_norm(r.get("norm_key", "")))
        names.add(_norm(r.get("canonical_name", "")))
    return frozenset(n for n in names if n)


class KnowledgeRepo:
    """Stable interface over the knowledge DB."""

    def __init__(self) -> None:
        init_db()
        self._ensure_seeded()

    def _ensure_seeded(self) -> None:
        s = get_session()
        try:
            empty = s.query(Axis).count() == 0
        finally:
            s.close()
        if empty:
            try:
                from scripts.seed_db import seed_all
                seed_all()
            except Exception:  # noqa: BLE001 — DB stays empty; axis() degrades gracefully
                pass

    def axis(self, code: str) -> dict:
        s = get_session()
        try:
            a = s.query(Axis).filter_by(code=code).first()
            if not a:
                return {"name": code}
            dom = s.get(Domain, a.domain_id) if a.domain_id else None
            return {"name": a.name, "domain_code": dom.code if dom else None}
        finally:
            s.close()

    def modules_for_axis(self, axis_code: str) -> list[dict]:
        reg = _registry_norms()
        out: list[dict] = []
        for code in _provisional_axis_modules().get(axis_code, []):
            out.append({
                "code": code,
                "name": code,
                "resolved": _norm(code) in reg,
                "provisional": True,
            })
        return out

    def is_contraindicated(self, module_code: str, medications: list[str]) -> bool:
        return False  # TODO(Phase 3): real contraindication rules vs meds.

    # --- convenience for diagnostics ---
    def counts(self) -> dict:
        s = get_session()
        try:
            return {
                "axes": s.query(Axis).count(),
                "domains": s.query(Domain).count(),
                "products": s.query(Product).count(),
            }
        finally:
            s.close()
