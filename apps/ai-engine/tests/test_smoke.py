"""Smoke tests: the pipeline boots and produces a grounded, de-identified report."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_PATIENT = {
    "case_id": "TSPI-EX-001",
    "age_band": "mid-40s",
    "sex": "female",
    "symptoms": "fibroid, hypertension, body inflammation, stress",
    "labs": [
        {"analyte": "CRP", "value": 21.57, "unit": "mg/L", "ref_high": 5.0},
        {"analyte": "HbA1c", "value": 6.5, "unit": "%", "ref_high": 5.6},
        {"analyte": "Hemoglobin", "value": 10.8, "unit": "g/dL", "ref_low": 12.0},
        {"analyte": "TSH", "value": 0.416, "unit": "uIU/mL", "ref_low": 0.54},
    ],
    "medications": ["antihypertensive"],
    "consent": {"ai_analysis": True},
}


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_analyze_maps_axes():
    r = client.post("/analyze", json=_PATIENT).json()
    codes = {a["axis_code"] for a in r["axis_scores"]}
    assert "A1" in codes            # CRP -> systemic inflammation
    assert r["root_cause_chain"]    # a chain was produced


def test_report_is_grounded_and_deidentified():
    r = client.post("/report", json=_PATIENT).json()
    assert r["case_id"] == "TSPI-EX-001"
    assert "clinician review" in r["disclaimer"].lower()
    # modules are resolved against the real product registry; unresolved ones are FLAGGED
    assert all(isinstance(m["resolved"], bool) for m in r["modules"])
    ks = [m for m in r["modules"] if (m["module_name"] or "").strip().upper() == "KS"]
    assert ks and ks[0]["resolved"]  # core KS module resolves to the catalog


def test_consent_blocks_analysis():
    p = {**_PATIENT, "consent": {"ai_analysis": False}}
    assert client.post("/analyze", json=p).status_code == 403


def test_severity_and_dosing_present():
    r = client.post("/report", json=_PATIENT).json()
    a = r["analysis"]
    assert 0 <= a["nss"] <= 100
    assert a["severity_level"] in (0, 1, 2, 3)
    assert a["severity_name"]
    assert a["system_priority"]                      # SPS ranked systems
    assert all(m["dose"] for m in r["modules"])      # every module got a dose
    ks = [m for m in r["modules"] if (m["module_name"] or "").strip().upper() == "KS"]
    assert ks and "bowel" in ks[0]["dose"].lower()   # KS uses its special protocol
    assert ks[0]["dose_type"] == "bowel"


def test_async_embed_matches_sync():
    import asyncio
    from app.knowledge.embeddings import EmbeddingProvider
    e = EmbeddingProvider()                       # hash backend in tests
    assert e.embed("chronic inflammation") == asyncio.run(e.aembed("chronic inflammation"))


def test_retrieval_cache_helpers():
    from app.knowledge import retrieval as R
    R.clear_cache()
    R._cache_put(("k",), [1.0, 2.0])
    assert R._cache_get(("k",)) == [1.0, 2.0]
    R.clear_cache()
    assert R._cache_get(("k",)) is None


def test_retrieve_noop_on_sqlite():
    import asyncio
    from app.knowledge import retrieval as R
    assert R.retrieve("x") == []                  # sync no-op
    assert asyncio.run(R.aretrieve("x")) == []    # async no-op


# ---- Phase 3: validation, persistence, consent/audit, safety ----
def test_report_persisted_not_deliverable():
    r = client.post("/report", json=_PATIENT).json()
    assert r["report_id"]                         # persisted
    assert r["status"] == "draft"
    assert r["deliverable"] is False              # needs doctor validation first


def test_doctor_validation_makes_deliverable():
    rid = client.post("/report", json=_PATIENT).json()["report_id"]
    v = client.post("/validate", json={"report_id": rid, "doctor_id": "dr.smith",
                                       "decision": "approve"}).json()
    assert v["status"] == "validated" and v["deliverable"] is True
    fetched = client.get(f"/reports/{rid}").json()
    assert fetched["deliverable"] is True


def test_validate_unknown_report_404():
    assert client.post("/validate", json={"report_id": "nope", "doctor_id": "d",
                                          "decision": "approve"}).status_code == 404


def test_outcome_recorded():
    rid = client.post("/report", json=_PATIENT).json()["report_id"]
    o = client.post("/outcome", json={"report_id": rid, "marker": "CRP",
                                      "baseline": 21.5, "followup": 6.0}).json()
    assert round(o["delta"], 1) == -15.5


def test_safety_flags_for_condition():
    p = {**_PATIENT, "conditions": ["pregnancy"]}   # KERRA rule -> flag (not dropped)
    r = client.post("/report", json=p).json()
    # KERRA's business code is now an H-Code; resolve it by name, then confirm it was flagged.
    kerra_codes = {m["module_code"] for m in r["modules"] if "KERRA" in (m["module_name"] or "").upper()}
    assert kerra_codes, "KERRA module expected in the plan for this case"
    flagged = [a for a in r["safety_alerts"] if a.get("module") in kerra_codes]
    assert flagged and all(isinstance(m["resolved"], bool) for m in r["modules"])


def test_safety_med_keyword_alert():
    p = {**_PATIENT, "medications": ["warfarin"]}
    r = client.post("/report", json=p).json()
    assert any("anticoagulant" in a["reason"].lower() or "bleeding" in a["reason"].lower()
               for a in r["safety_alerts"])


# ---- Phase 4: learning loop + temporal ----
def test_weights_default_neutral():
    # no learning yet -> weights empty -> NSS identical to Phase 1-3 behaviour
    assert client.get("/learning/weights").json()["axis_weights"] == {}
    r = client.post("/report", json=_PATIENT).json()
    assert r["analysis"]["nss"] >= 60          # high-CRP case stays high-severity


def test_recalibrate_changes_axis_weight():
    client.post("/learning/recalibrate")                       # drain any prior outcomes
    w0 = client.get("/learning/weights").json()["axis_weights"].get("A1", 1.0)
    rid = client.post("/report", json=_PATIENT).json()["report_id"]
    client.post("/outcome", json={"report_id": rid, "marker": "CRP",
                                  "baseline": 10.0, "followup": 25.0})   # CRP up = worse
    out = client.post("/learning/recalibrate").json()
    assert out["axes_changed"] >= 1
    w1 = client.get("/learning/weights").json()["axis_weights"].get("A1", 1.0)
    assert w1 > w0                                              # worsening -> more emphasis


def test_temporal_trajectory():
    cid = "TEMPORAL-1"
    p = {**_PATIENT, "case_id": cid}
    rid = client.post("/report", json=p).json()["report_id"]
    client.post("/outcome", json={"report_id": rid, "marker": "CRP",
                                  "baseline": 21.0, "followup": 6.0})    # CRP down = improving
    t = client.get(f"/temporal/{cid}").json()
    crp = [m for m in t["markers"] if m["marker"] == "CRP"][0]
    assert crp["trend"] == "improving"


# ---- Extraction: /extract reads an uploaded file into candidate labs ----
def test_extract_endpoint_parses_labs_and_drops_pii():
    content = b"CRP 21.57 mg/L (ref < 5.0)\nHbA1c: 6.5 % (4.0-5.6)\nName: Jane Doe\n"
    files = {"file": ("labs.txt", content, "text/plain")}
    r = client.post("/extract", files=files, data={"doc_type": "lab"}).json()
    analytes = {l["analyte"] for l in r["labs"]}
    assert "CRP" in analytes                 # value extracted
    assert "Name" not in analytes            # PII line not treated as a lab
    assert r["confirmed"] is False           # human-review gate preserved
    assert r["source"] == "text"


# ---- Official module registry (domain-expert answers) ----
def test_report_stamps_registry_versions():
    r = client.post("/report", json=_PATIENT).json()
    assert r["registry_version"] and r["framework_version"]   # traceable to the data that made it


def test_modules_carry_role_and_dose_type():
    r = client.post("/report", json=_PATIENT).json()
    assert r["modules"], "expected modules for a high-severity case"
    m = r["modules"][0]
    assert m["dose_type"] in ("severity", "bowel")
    assert set(m["axis_roles"].values()) <= {"primary", "secondary"}   # per-axis role tagged


def test_bowel_group_uses_bowel_dose():
    r = client.post("/report", json=_PATIENT).json()
    bowel = [m for m in r["modules"] if m["dose_type"] == "bowel"]
    assert bowel and all("bowel" in (m["dose"] or "").lower() for m in bowel)


def test_a37_has_modules():
    # A37 (Protein Quality Control) — interim support assigned by the experts
    from app.knowledge.repository import KnowledgeRepo
    mods = KnowledgeRepo().modules_for_axis("A37")
    names = {(m.get("name") or "").upper() for m in mods}
    assert mods and any(n in names for n in ("KS", "KERRA CAPSULE", "VITALPLUS"))
