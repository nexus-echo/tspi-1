#!/usr/bin/env python3
"""CLI: apply the Phase 11 legacy->current axis converter to a module registry JSON.

Usage:
  python3 scripts/convert_registry.py <legacy_modules.json> [out_prefix]

Writes:
  <out_prefix>_converted.json         converted modules (production_allowed per module)
  <out_prefix>_axis_review.csv        quarantine sheet for domain-expert sign-off
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.registry_convert import convert_registry  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src = Path(sys.argv[1])
    prefix = sys.argv[2] if len(sys.argv) > 2 else str(src.with_suffix(""))
    doc = json.loads(src.read_text(encoding="utf-8"))
    modules = doc.get("modules", doc) if isinstance(doc, dict) else doc
    result = convert_registry(modules)

    Path(f"{prefix}_converted.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(f"{prefix}_axis_review.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["module_code", "module_name", "legacy_ref", "candidate_code",
                    "conversion_type", "tier", "network_code", "CONFIRM_current_code", "note"])
        for r in result["review_sheet"]:
            w.writerow([r.get("module_code"), r.get("module_name"), r.get("legacy_ref"),
                        r.get("candidate_code"), r.get("conversion_type"), r.get("tier"),
                        r.get("network_code"), "", r.get("note")])
    s = result["summary"]
    print(f"Converted {s['modules_total']} modules — "
          f"{s['modules_fully_resolved']} auto-resolved, {s['modules_needing_review']} need review "
          f"({s['quarantined_refs']} quarantined refs). production_allowed={result['production_allowed']}")


if __name__ == "__main__":
    main()
