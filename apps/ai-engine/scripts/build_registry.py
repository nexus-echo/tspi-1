"""Compile the official module registry + axis->module map from source data.

INPUT  (dev/offline): knowledge-sources/200-modules/modules_consolidated.json (draft) or, once
       delivered, the official master file (same field spec — see docs/Module_Registry_Spec.md).
OUTPUT (shipped in the image): data/module_registry.json  +  data/axis_module_official.json

Rules (domain-expert answers): 1 module = 1 product (keyed by H-Code), map to 39 axes with a
primary/secondary role, dose_type severity|bowel, contraindications per module, status active/…,
A37 interim support = KS/Kerra/VitalPlus. Deterministic + re-runnable.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # apps/ai-engine
DATA = ROOT / "data"
CONSOLIDATED = ROOT.parent.parent / "knowledge-sources" / "200-modules" / "modules_consolidated.json"
REGISTRY = DATA / "product_registry.json"

REGISTRY_VERSION = "0.1.0-draft"      # bumped when the official master file lands
FRAMEWORK_VERSION = "39-axis-v3.0"

BOWEL = ["ks", "blax", "belax", "cathartic", "lypholax", "venta"]         # dose_type = bowel
A37_SUPPORT = ["ks", "kerra", "vitalplus"]                                # interim A37 modules


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def is_bowel(name: str) -> bool:
    n = norm(name)
    return any(b in n for b in BOWEL)


def a(nums):
    return [f"A{n}" for n in sorted(nums, key=int)]


def axnum(codes):
    return {int(c[1:]) for c in codes if c and c.startswith("A")}


def main() -> None:
    consolidated = json.loads(CONSOLIDATED.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    # canonical -> {primary, secondary, all, contra} from the merged sources
    canon = {}
    for rec in consolidated.values():
        c = rec.get("canonical_product")
        if not c:
            continue
        e = canon.setdefault(c, {"primary": set(), "secondary": set(), "all": set(), "contra": ""})
        md = rec.get("md_data") or {}
        e["primary"] |= axnum(md.get("axis_primary", []))
        e["secondary"] |= axnum(md.get("axis_secondary", []))
        e["all"] |= axnum(rec.get("mismatches", {}).get("suggested_union", []))
        if not e["contra"]:
            e["contra"] = (rec.get("excel_data") or {}).get("Drug-Herb Interaction", "") or ""

    # 1 module = 1 product: dedupe registry rows by canonical name (prefer an H-Code)
    best: dict[str, dict] = {}
    for p in registry:
        code = str(p.get("kept_product_id", "")).strip()
        name = p.get("canonical_name", "")
        if not code or not name:
            continue
        key = norm(name)
        cur = best.get(key)
        if cur is None or (code.upper().startswith("H-") and not str(cur.get("kept_product_id","")).upper().startswith("H-")):
            best[key] = p
    used_codes: set[str] = set()

    modules = []
    for p in best.values():
        code = str(p.get("kept_product_id", "")).strip()
        name = p.get("canonical_name", "")
        if not code or code in used_codes:
            continue
        used_codes.add(code)
        info = canon.get(name, {"primary": set(), "secondary": set(), "all": set(), "contra": ""})
        prim, sec, alln = set(info["primary"]), set(info["secondary"]), set(info["all"])
        alln |= prim | sec
        sec = alln - prim                                    # secondary = everything not primary
        # A37 interim support
        if is_bowel(name) or any(k in norm(name) for k in A37_SUPPORT):
            if any(k in norm(name) for k in A37_SUPPORT):
                prim.add(37); alln.add(37); sec = alln - prim
        raw = (info["contra"] or "").strip()
        contra = [raw] if raw and raw.lower() != "none" else []      # raw note; master file will structure these
        modules.append({
            "module_code": code,
            "phytocore_code": p.get("phytocore_code", ""),
            "name_en": name,
            "name_th": None,
            "product_id": code,
            "target_axes": a(alln),
            "primary_axes": a(prim),
            "secondary_axes": a(sec),
            "dose_type": "bowel" if is_bowel(name) else "severity",
            "contraindications": contra,
            "status": "active" if alln else "draft",
        })

    reg_out = {
        "registry_version": REGISTRY_VERSION,
        "framework_version": FRAMEWORK_VERSION,
        "source": "compiled DRAFT from modules_consolidated.json — replace with official master file",
        "module_count": len(modules),
        "modules": modules,
    }
    (DATA / "module_registry.json").write_text(json.dumps(reg_out, ensure_ascii=False, indent=2), encoding="utf-8")

    # inverted axis -> modules (with per-axis role)
    amap: dict[str, list] = {f"A{n}": [] for n in range(1, 40)}
    for m in modules:
        if m["status"] != "active":
            continue
        prim = set(m["primary_axes"])
        for ax in m["target_axes"]:
            amap[ax].append({
                "code": m["module_code"], "name": m["name_en"], "phytocore": m["phytocore_code"],
                "dose_type": m["dose_type"], "status": m["status"],
                "role": "primary" if ax in prim else "secondary",
            })
    amap = {k: v for k, v in amap.items() if v}
    map_out = {
        "registry_version": REGISTRY_VERSION,
        "framework_version": FRAMEWORK_VERSION,
        "map": amap,
    }
    (DATA / "axis_module_official.json").write_text(json.dumps(map_out, ensure_ascii=False, indent=2), encoding="utf-8")

    covered = sorted(amap, key=lambda x: int(x[1:]))
    missing = [f"A{n}" for n in range(1, 40) if f"A{n}" not in amap]
    bowel = [m["module_code"] for m in modules if m["dose_type"] == "bowel"]
    print(f"modules: {len(modules)} | axes covered: {len(covered)}/39 | missing: {missing or 'none'}")
    print(f"bowel-dosing modules: {bowel}")
    print(f"A37 modules: {[x['code'] for x in amap.get('A37', [])]}")
    print("wrote data/module_registry.json + data/axis_module_official.json")


if __name__ == "__main__":
    main()
