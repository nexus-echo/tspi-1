"""Phase 0 — Product dedup + registry builder (executes owner rules Q1/Q2).

Rule: one module = one official record. Where several files share the same (normalized)
product name, keep the MOST COMPLETE one and archive the rest. Produces:
  data/product_registry.json      — one canonical record per product (+ aliases/archived)
  data/product_dedup_report.json  — the full grouping for human review

Conservative normalization: only strip dosage-form / brand words (CAPSULE, MIXTURE, TONIC,
ELIXIR, BRAND, YA-prefix). Distinguishing words (COMPLEX, OIL, SPRAY, SOAP, PLUS, numbers in
name) are kept so genuinely different products are NOT merged. Output is a CANDIDATE registry
for clinical review (owner: 'final number to be confirmed after data cleaning').
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

FORM_WORDS = {"CAPSULE", "CAPSULES", "CAP", "CAPS", "MIXTURE", "TONIC", "ELIXIR",
              "BRAND", "YA", "MEDICINE", "HERBAL"}

FIELD = {
    "id": r"\(Product ID\):\*\*\s*(.+)",
    "name": r"\(Product Name\):\*\*\s*(.+)",
    "phytocore": r"\(PhytoCore Code\):\*\*\s*(.+)",
}


def norm_name(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = re.sub(r"[^A-Za-z0-9 ]", " ", n).upper()
    toks = [t for t in n.split() if t and t not in FORM_WORDS]
    return " ".join(toks).strip()


def parse(p: Path) -> dict:
    txt = p.read_text(encoding="utf-8", errors="ignore")
    rec = {"file": p.name, "chars": len(txt)}
    for k, pat in FIELD.items():
        m = re.search(pat, txt)
        rec[k] = (m.group(1).strip() if m else "") or ""
    # completeness: file length + count of populated meaningful sections
    sections = len(re.findall(r"^#{2,3}\s", txt, flags=re.M))
    has_botanical = "Botanical Composition" in txt or "องค์ประกอบพฤกษเคมี" in txt
    rec["completeness"] = len(txt) + sections * 50 + (200 if has_botanical else 0)
    rec["norm"] = norm_name(rec.get("name") or "")
    return rec


def main(products_dir: str, out_dir: str) -> None:
    pdir, odir = Path(products_dir), Path(out_dir)
    recs = [parse(p) for p in sorted(pdir.glob("product_*.md"))]
    recs = [r for r in recs if r["norm"] and r["norm"] not in {"N A", "NA", ""}]

    groups: dict[str, list[dict]] = {}
    for r in recs:
        groups.setdefault(r["norm"], []).append(r)

    registry, report = [], []
    for norm, members in sorted(groups.items()):
        members.sort(key=lambda r: r["completeness"], reverse=True)
        keep = members[0]
        archived = members[1:]
        registry.append({
            "canonical_name": keep["name"],
            "norm_key": norm,
            "kept_product_id": keep["id"],
            "kept_file": keep["file"],
            "phytocore_code": keep["phytocore"],
            "duplicate_count": len(members),
            "aliases": sorted({m["name"] for m in members if m["name"] != keep["name"]}),
            "archived_ids": [{"id": m["id"], "file": m["file"]} for m in archived],
        })
        report.append({"norm_key": norm, "members": [
            {"id": m["id"], "name": m["name"], "file": m["file"],
             "completeness": m["completeness"], "kept": m is keep} for m in members]})

    odir.mkdir(parents=True, exist_ok=True)
    (odir / "product_registry.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    (odir / "product_dedup_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    dups = [g for g in report if len(g["members"]) > 1]
    print(f"input product files parsed : {len(recs)}")
    print(f"canonical products (registry): {len(registry)}")
    print(f"groups with duplicates     : {len(dups)}")
    print(f"files archived as duplicates: {sum(len(g['members'])-1 for g in dups)}")
    print("\nExample duplicate groups:")
    for g in sorted(dups, key=lambda g: len(g["members"]), reverse=True)[:8]:
        ids = ", ".join(m["id"] for m in g["members"])
        kept = next(m["id"] for m in g["members"] if m["kept"])
        print(f"  {g['norm_key']:<22} x{len(g['members'])}  ids=[{ids}]  -> keep {kept}")


if __name__ == "__main__":
    pdir = sys.argv[1] if len(sys.argv) > 1 else "../products"
    odir = sys.argv[2] if len(sys.argv) > 2 else "data"
    main(pdir, odir)
