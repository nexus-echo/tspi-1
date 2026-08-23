"""Tests for the de-identification gate — the guarantee that PII never leaves this layer."""
import pytest

from tspi_mcp.deident import ALLOWED_FIELDS, PIIError, deidentify


def test_forbidden_identity_field_is_rejected():
    with pytest.raises(PIIError):
        deidentify({"case_id": "C1", "name": "John Smith"}, strict=True)


def test_unknown_fields_are_dropped():
    clean, _ = deidentify({"case_id": "C1", "sex": "female", "bogus": "x", "symptoms": "fatigue"},
                          strict=False)
    assert set(clean) <= ALLOWED_FIELDS
    assert "bogus" not in clean and clean["case_id"] == "C1"


def test_strict_mode_rejects_embedded_pii():
    with pytest.raises(PIIError):
        deidentify({"case_id": "C1", "symptoms": "fatigue, email john@doe.com"}, strict=True)


def test_lenient_mode_redacts_and_reports():
    clean, findings = deidentify(
        {"case_id": "C1", "symptoms": "call 090-123-4567, dob 1980-05-01, id 12345678"},
        strict=False)
    assert "email" not in findings
    assert {"phone", "date_of_birth", "identifier"} <= set(findings)
    assert "REDACTED" in clean["symptoms"]


def test_clean_input_passes_untouched():
    payload = {"case_id": "CASE-0912", "age_band": "40s", "sex": "female",
               "symptoms": "bloating after meals, fatigue",
               "labs": [{"analyte": "CRP", "value": 21.5, "unit": "mg/L"}],
               "consent": {"ai_analysis": True}}
    clean, findings = deidentify(payload, strict=True)
    assert findings == []
    assert clean["labs"][0]["analyte"] == "CRP"
