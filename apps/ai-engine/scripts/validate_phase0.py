"""Phase 0 validation — runs every invariant and prints PASS/FAIL.

Usage:  python -m scripts.validate_phase0
Exit code 0 = all passed, 1 = something failed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from app.knowledge.db import get_session
from app.knowledge.models import Axis, Domain, Key, Product, Step, SubAxis
from scripts.seed_db import seed_all

DATA = Path(__file__).resolve().parent.parent / "data"
checks: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append((name, bool(ok), detail))


# 1. data files exist
for f in ["tspi_axes_39.json", "tspi_framework.json", "tspi_severity_dosing.json",
          "product_registry.json", "axis_module_provisional.json"]:
    check(f"data file present: {f}", (DATA / f).exists())

# 2. reproducible seed -> expected counts
counts = seed_all()
expected = {"keys": 3, "steps": 9, "domains": 13, "axes": 39, "sub_axes": 119, "products": 153}
for k, v in expected.items():
    check(f"count {k} == {v}", counts.get(k) == v, f"got {counts.get(k)}")

# 3. structural integrity in the DB
s = get_session()
try:
    axes = s.query(Axis).all()
    codes = {a.code for a in axes}
    check("all 39 axis codes A1..A39", codes == {f"A{i}" for i in range(1, 40)},
          f"missing {sorted({f'A{i}' for i in range(1,40)} - codes)}")
    check("every axis has a domain", all(a.domain_id is not None for a in axes))
    check("every axis has >=1 sub-axis",
          all(s.query(SubAxis).filter_by(axis_id=a.id).count() >= 1 for a in axes))
    # spot-check official domain grouping (A16/A17 in D5, A36 in D12)
    dom = {a.code: s.get(Domain, a.domain_id).code for a in axes}
    check("A17 -> D5 (official Digestive-Gut grouping)", dom.get("A17") == "D5", dom.get("A17"))
    check("A36 -> D12 (Oncology)", dom.get("A36") == "D12", dom.get("A36"))
    check("A1 name == 'Systemic Inflammatory Load'",
          s.query(Axis).filter_by(code="A1").first().name == "Systemic Inflammatory Load")
finally:
    s.close()

# 4. dedup invariants
reg = json.loads((DATA / "product_registry.json").read_text(encoding="utf-8"))
check("registry has 153 canonical products", len(reg) == 153, f"got {len(reg)}")
check("every registry row has a kept_product_id", all(r.get("kept_product_id") for r in reg))
check("no duplicate norm_keys in registry",
      len({r["norm_key"] for r in reg}) == len(reg))

# 5. engine reads DB + resolves modules
from app.knowledge.repository import KnowledgeRepo  # noqa: E402
repo = KnowledgeRepo()
check("repo.axis('A17') name from DB", repo.axis("A17").get("name") == "Microbiome Ecology")
ks = [m for m in repo.modules_for_axis("A1") if m["code"] == "KS"]
check("KS resolves against registry", bool(ks) and ks[0]["resolved"])

# 6. end-to-end API: severity + dosing + de-identification + consent gate
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
c = TestClient(app)
P = {"case_id": "VAL-1", "sex": "female", "symptoms": "inflammation, stress",
     "labs": [{"analyte": "CRP", "value": 21.57, "ref_high": 5.0}],
     "consent": {"ai_analysis": True}}
r = c.post("/report", json=P).json()
check("report case_id echoes (de-identified, no PII)", r["case_id"] == "VAL-1")
check("NSS in 0..100", 0 <= r["analysis"]["nss"] <= 100)
check("severity level 0..3", r["analysis"]["severity_level"] in (0, 1, 2, 3))
check("every module has a dose", all(m["dose"] for m in r["modules"]))
check("consent gate returns 403",
      c.post("/analyze", json={**P, "consent": {"ai_analysis": False}}).status_code == 403)

# ---- report ----
passed = sum(1 for _, ok, _ in checks if ok)
print(f"\nPHASE 0 VALIDATION — {passed}/{len(checks)} checks passed\n" + "-" * 48)
for name, ok, detail in checks:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if not ok and detail else ""))
sys.exit(0 if passed == len(checks) else 1)
