"""Validation gate for the module registry (run before shipping any registry version).

Enforces the domain-expert rules: unique H-Codes, 1 module = 1 product, axes in A1..A39,
>=1 axis per active module, dose_type in {severity,bowel}, catalogue resolution, and a coverage
report (which axes have no active module). Exit code 1 on any hard failure.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def main() -> int:
    reg = json.loads((DATA / "module_registry.json").read_text(encoding="utf-8"))
    mods = reg["modules"]
    prod = json.loads((DATA / "product_registry.json").read_text(encoding="utf-8"))
    prod_ids = {str(p.get("kept_product_id", "")).strip() for p in prod}
    prod_names = {norm(p.get("canonical_name", "")) for p in prod}

    errors: list[str] = []
    warns: list[str] = []
    seen_codes: set[str] = set()
    seen_products: dict[str, str] = {}
    axis_ok = re.compile(r"^A([1-9]|[12]\d|3\d)$")   # A1..A39

    for m in mods:
        code = m["module_code"]
        if code in seen_codes:
            errors.append(f"duplicate module_code: {code}")
        seen_codes.add(code)
        active = m.get("status") == "active"
        # 1 module = 1 product: no product under two active codes
        pid = norm(m.get("name_en", ""))
        if active and pid in seen_products:
            errors.append(f"product '{m['name_en']}' active under two codes: {seen_products[pid]} & {code}")
        elif active:
            seen_products[pid] = code
        # axes
        for ax in m.get("target_axes", []):
            if not axis_ok.match(ax):
                errors.append(f"{code}: bad axis '{ax}' (must be A1..A39)")
        if active and not m.get("target_axes"):
            warns.append(f"{code}: active module has NO axes")
        # dose_type
        if m.get("dose_type") not in ("severity", "bowel"):
            errors.append(f"{code}: dose_type '{m.get('dose_type')}' invalid")
        # catalogue resolution
        if code not in prod_ids and norm(m.get("name_en", "")) not in prod_names:
            warns.append(f"{code} ({m['name_en']}): not resolved to product registry")

    covered = {ax for m in mods if m.get("status") == "active" for ax in m.get("target_axes", [])}
    missing = [f"A{n}" for n in range(1, 40) if f"A{n}" not in covered]

    print(f"modules: {len(mods)} | unique codes: {len(seen_codes)} | axes covered: {len(covered)}/39")
    print(f"registry_version: {reg.get('registry_version')} | framework: {reg.get('framework_version')}")
    if missing:
        warns.append(f"axes with NO active module: {missing}")
    for w in warns:
        print("  WARN:", w)
    for e in errors:
        print("  ERROR:", e)
    if errors:
        print(f"\nFAILED with {len(errors)} error(s).")
        return 1
    print(f"\nPASSED ({len(warns)} warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
