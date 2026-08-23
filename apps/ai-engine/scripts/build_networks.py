#!/usr/bin/env python3
"""
build_networks.py — compile the client-verified 180-network CSV into the engine's
Network master, and auto-generate a DRAFT network->axis / network->domain crosswalk.

Inputs
  ../../docs/latest-data/networks_180.csv        (client-verified, Thai verbatim)
  data/tspi_axes_39.json                          (canonical 39 axes + 12 domains)
Outputs
  data/tspi_networks_180.json                     (Network master)
  ../../docs/latest-data/network_axis_crosswalk_DRAFT.csv   (for clinical sign-off)
  prints a coverage report

The CSV's `biological_axis` and `domain` columns are FREE-TEXT LABELS, not codes.
This script maps them to canonical A1-A39 / domain_num where the name matches; anything
unmatched is flagged needs_review=true for the client to confirm. Nothing is guessed.
"""
import csv, json, re, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
CSV_IN = ENGINE.parent.parent / "docs" / "latest-data" / "networks_180.csv"
AXES_IN = ENGINE / "data" / "tspi_axes_39.json"
JSON_OUT = ENGINE / "data" / "tspi_networks_180.json"
CROSSWALK_OUT = ENGINE.parent.parent / "docs" / "latest-data" / "network_axis_crosswalk_DRAFT.csv"

FRAMEWORK_VERSION = "39-axis-master-260715"

# Client ruling: CELA is network #120 under A34 (not an axis).
NETWORK_OVERRIDES = {120: {"primary_axis_code": "A34", "note": "CELA — client ruling: network under A34"}}

def norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = s.replace("&", " and ")
    s = re.sub(r"[‐-―\-/]", " ", s)   # dashes & slashes -> space
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main():
    axes_doc = json.load(open(AXES_IN, encoding="utf-8"))
    axes = axes_doc["axes"]
    axis_by_norm = {norm(a["name"]): a["axis_id"] for a in axes}
    STOP = {"and","the","of","amp"}
    def toks(x): return {t for t in norm(x).split() if t and t not in STOP}
    axis_tokens = [(a["axis_id"], a["name"], toks(a["name"])) for a in axes]
    def suggest_axis(label):
        lt = toks(label)
        if not lt: return ("", "", 0.0)
        best=None; best_s=0.0
        for code,name,at in axis_tokens:
            inter=len(lt & at); union=len(lt | at) or 1
            s=inter/union
            if inter and s>best_s: best_s=s; best=(code,name)
        if best: return (best[0], best[1], round(best_s,2))
        return ("", "", 0.0)
    # domain lookups
    dom_by_num = {}
    dom_norm = {}
    axis_domain = {}                       # axis_code -> domain_num (for DERIVING network domain)
    for a in axes:
        dom_by_num[a["domain_num"]] = a["domain"]
        dom_norm.setdefault(norm(a["domain"]), a["domain_num"])
        axis_domain[a["axis_id"]] = a["domain_num"]

    rows = list(csv.DictReader(open(CSV_IN, encoding="utf-8-sig")))
    networks = []
    axis_matched = axis_unmatched = 0
    dom_matched = dom_unmatched = 0
    unmatched_axis_labels = {}
    unmatched_dom_labels = {}

    for r in rows:
        num = int(r["network_number"])
        axis_label = (r["biological_axis"] or "").strip()
        dom_label = (r["domain"] or "").strip()

        # --- axis mapping ---
        override = NETWORK_OVERRIDES.get(num)
        if override:
            axis_code = override["primary_axis_code"]; axis_src = "client_override"
        else:
            axis_code = axis_by_norm.get(norm(axis_label)); axis_src = "exact_name" if axis_code else None
        if axis_code:
            axis_matched += 1
        else:
            axis_unmatched += 1
            unmatched_axis_labels[axis_label] = unmatched_axis_labels.get(axis_label, 0) + 1

        # --- domain: DERIVED from the (confirmed) primary axis, never authored from the CSV label
        #     (31 Jul §4.3 + Directive 11). The CSV domain label is kept for reference only.
        dnum = axis_domain.get(axis_code) if axis_code else None
        if dnum:
            dom_matched += 1
        else:
            dom_unmatched += 1
            unmatched_dom_labels[dom_label] = unmatched_dom_labels.get(dom_label, 0) + 1

        networks.append({
            # 31 Jul §4.2 + Directive 10: three SEPARATE identity fields.
            "network_code": f"LBN-{num:03d}",          # permanent stable identity (CANDIDATE seed)
            "network_code_status": "CANDIDATE",         # official permanent code assigned at approval
            "network_number": num,                      # human-readable display order 1..180
            "legacy_display_id": f"N{num:03d}",         # legacy/display id
            "network_name_en": (r["living_biological_network_system"] or "").strip(),
            "biological_axis_label": axis_label,        # free-text label from source (reference)
            "primary_axis_code": axis_code,
            "secondary_axis_codes": [],                 # populated at expert review
            "primary_domain_code": (f"D{dnum}" if dnum else None),   # DERIVED from primary axis
            "domain_derivation": "AxisRegistry[primary_axis_code].domain_code",
            "domain_group_label_from_file": dom_label,  # reference only, not a source of truth
            "axis_map_source": axis_src,
            "mapping_confidence": (1.0 if axis_src in ("client_override",) else
                                   0.9 if axis_src == "exact_name" else 0.0),
            "mapping_status": ("APPROVED" if axis_src == "client_override" else "CANDIDATE"),
            "needs_axis_review": axis_code is None,
            "scope": (r["scope"] or "").strip(),
            "status": "active",
            "framework_version": FRAMEWORK_VERSION,
            "axis_master_version": FRAMEWORK_VERSION,
        })

    master = {
        "dataset_name": "tspi_networks_180",
        "dataset_version": "1.0.0",
        "framework_version": FRAMEWORK_VERSION,
        "source": "docs/latest-data/networks_180.csv (client-verified, Thai verbatim, CELA=#120)",
        "record_count": len(networks),
        "networks": networks,
    }
    json.dump(master, open(JSON_OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # --- DRAFT crosswalk: one row per DISTINCT axis label for clinical sign-off ---
    label_rows = {}
    for n in networks:
        lab = n["biological_axis_label"]
        d = label_rows.setdefault(lab, {"label": lab, "count": 0,
                                        "auto_axis_code": n["primary_axis_code"] if n["axis_map_source"]=="exact_name" else "",
                                        "example_networks": []})
        d["count"] += 1
        if len(d["example_networks"]) < 2:
            d["example_networks"].append(f'{n["legacy_display_id"]} {n["network_name_en"]}')
    with open(CROSSWALK_OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["biological_axis_label","networks_using_label","auto_mapped_axis_code",
                    "suggested_axis_code","suggested_axis_name","suggestion_confidence",
                    "CONFIRM_axis_code","status","example_networks"])
        for lab in sorted(label_rows, key=lambda x: (-label_rows[x]["count"], x)):
            d = label_rows[lab]
            if d["auto_axis_code"]:
                sug_code, sug_name, conf, confirm, status = d["auto_axis_code"], "", 1.0, d["auto_axis_code"], "AUTO_MATCHED"
            else:
                sug_code, sug_name, conf = suggest_axis(lab)
                confirm = ""  # never pre-fill CONFIRM for non-exact — clinician decides
                status = "NEEDS_REVIEW"
            w.writerow([lab, d["count"], d["auto_axis_code"], sug_code, sug_name, conf,
                        confirm, status, " | ".join(d["example_networks"])])


    # --- FULL per-network crosswalk: one row per network (all 180) ---  PER-NETWORK
    # 31 Jul §4.3: the expert confirms only the AXIS. The Domain is DERIVED from that axis, so
    # the sheet SHOWS the derived domain (read-only) rather than asking the expert to author it.
    dom_name_by_num = {a["domain_num"]: a["domain"] for a in axes}
    axis_domain = {a["axis_id"]: a["domain_num"] for a in axes}
    axis_name = {a["axis_id"]: a["name"] for a in axes}

    def derived_domain(axis_code):
        dn = axis_domain.get(axis_code)
        return (f"D{dn}", dom_name_by_num.get(dn)) if dn else ("", "")

    PERNET_OUT = ENGINE.parent.parent / "docs" / "latest-data" / "network_crosswalk_FULL_DRAFT.csv"
    with open(PERNET_OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["legacy_display_id","network_number","network_code_candidate","network_name_en",
                    "axis_label_from_file","suggested_axis_code","suggested_axis_name","axis_confidence",
                    "CONFIRM_axis_code",
                    "derived_domain_code","derived_domain_name","(domain auto-derives from CONFIRM_axis)",
                    "scope"])
        for n in sorted(networks, key=lambda x: x["network_number"]):
            if n["axis_map_source"] == "exact_name":
                sug_code, sug_name, conf = n["primary_axis_code"], axis_name.get(n["primary_axis_code"], ""), 1.0
            elif n["axis_map_source"] == "client_override":
                sug_code, sug_name, conf = n["primary_axis_code"], "CELA ruling", 1.0
            else:
                sug_code, sug_name, conf = suggest_axis(n["biological_axis_label"])
            ddom_code, ddom_name = derived_domain(sug_code)
            w.writerow([n["legacy_display_id"], n["network_number"], n["network_code"], n["network_name_en"],
                        n["biological_axis_label"], sug_code, sug_name, conf, "",
                        ddom_code, ddom_name, "derived",
                        n["scope"]])
    print(f"Per-network crosswalk: {PERNET_OUT.name} ({len(networks)} rows)")

    # --- report ---
    print(f"Networks written : {len(networks)} -> {JSON_OUT.name}")
    print(f"Axis mapping     : {axis_matched}/{len(networks)} rows auto-mapped, {axis_unmatched} need review")
    print(f"Distinct axis labels: {len(label_rows)}  "
          f"({sum(1 for l in label_rows.values() if l['auto_axis_code'])} matched, "
          f"{sum(1 for l in label_rows.values() if not l['auto_axis_code'])} need review)")
    print(f"Domain mapping   : {dom_matched}/{len(networks)} rows auto-mapped, {dom_unmatched} need review")
    print(f"Crosswalk draft  : {CROSSWALK_OUT.name} ({len(label_rows)} distinct labels)")
    if unmatched_axis_labels:
        print("\nTop unmatched AXIS labels (label x networks):")
        for lab, c in sorted(unmatched_axis_labels.items(), key=lambda x:-x[1])[:15]:
            print(f"  {c:>3}  {lab}")
    if unmatched_dom_labels:
        print("\nUnmatched DOMAIN labels:")
        for lab, c in sorted(unmatched_dom_labels.items(), key=lambda x:-x[1]):
            print(f"  {c:>3}  {lab}")

if __name__ == "__main__":
    main()
