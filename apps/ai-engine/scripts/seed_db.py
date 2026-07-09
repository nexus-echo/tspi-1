"""Phase 0 loader: official framework + 39 axes + product registry -> the database.

Idempotent: clears and reloads the reference tables. Run:
    python -m scripts.seed_db
"""
from __future__ import annotations

import json
from pathlib import Path

from app.knowledge.db import get_session, init_db
from app.knowledge.models import (
    Axis, Domain, Key, Module, Product, Step, SubAxis,
)

DATA = Path(__file__).resolve().parent.parent / "data"


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def seed_all() -> dict:
    init_db()
    fw = _load("tspi_framework.json")
    axes = _load("tspi_axes_39.json")
    try:
        registry = _load("product_registry.json")
    except FileNotFoundError:
        registry = []

    s = get_session()
    # wipe reference tables for a clean reload
    for model in (SubAxis, Axis, Domain, Step, Key, Module, Product):
        s.query(model).delete()
    s.commit()

    for k in fw["keys_3"]:
        s.add(Key(code=k["code"], name=k["name"]))
    for st in fw["steps_9"]:
        s.add(Step(order=st["order"], name=st["name"]))
    for d in fw["domains_12_official"]:
        s.add(Domain(code=f"D{d['num']}", name=d["name"]))
    # provisional meta-domain for axes 37-39 (pending owner confirmation)
    s.add(Domain(code="D12M", name="Proteostasis & Cellular Integrity (meta, provisional)"))
    s.commit()

    # map axis-num -> domain code from the official framework
    axis_to_domain = {}
    for d in fw["domains_12_official"]:
        for ax in d["axes"]:
            axis_to_domain[ax] = f"D{d['num']}"
    for ax in fw.get("axes_37_39_pending", {}).get("axes", []):
        axis_to_domain[ax["code"]] = "D12M"  # provisional Proteostasis/meta group

    dom_ids = {d.code: d.id for d in s.query(Domain).all()}
    for a in axes:
        code = a["axis_id"]
        dcode = axis_to_domain.get(code, "D12M")
        axis = Axis(code=code, name=a["name"] or code, domain_id=dom_ids.get(dcode))
        s.add(axis)
        s.flush()
        for sub in a.get("sub_axes", []):
            s.add(SubAxis(axis_id=axis.id, letter=sub["code"][-1], description=sub.get("name", "")))
    s.commit()

    for p in registry:
        s.add(Product(tspi_id=str(p.get("kept_product_id", "")), name=p.get("canonical_name", "")))
    s.commit()

    counts = {
        "keys": s.query(Key).count(), "steps": s.query(Step).count(),
        "domains": s.query(Domain).count(), "axes": s.query(Axis).count(),
        "sub_axes": s.query(SubAxis).count(), "products": s.query(Product).count(),
    }
    s.close()
    return counts


if __name__ == "__main__":
    print("seeded:", seed_all())
