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


# ---- P7: OAuth wiring (env-driven) ----
def test_auth_none_by_default_and_static_identity():
    import os
    os.environ.pop("TSPI_MCP_AUTH", None)
    from importlib import reload
    from tspi_mcp import config as c, identity as idn
    reload(c); reload(idn)
    assert idn.build_auth() is None                       # local stdio: no incoming auth
    user, role, clinic = idn.current_identity()           # falls back to static pilot identity
    assert role == c.settings.clinician_role

def test_auth_jwt_requires_config_else_fail_closed():
    import os, pytest
    from importlib import reload
    from tspi_mcp import config as c, identity as idn
    os.environ["TSPI_MCP_AUTH"] = "jwt"                    # but no JWKS/issuer -> must fail closed
    os.environ.pop("TSPI_JWT_JWKS_URI", None); os.environ.pop("TSPI_JWT_ISSUER", None)
    reload(c); reload(idn)
    with pytest.raises(RuntimeError):
        idn.build_auth()
    os.environ.pop("TSPI_MCP_AUTH", None); reload(c); reload(idn)

def test_auth_jwt_builds_verifier_when_configured():
    import os
    from importlib import reload
    from tspi_mcp import config as c, identity as idn
    os.environ.update({"TSPI_MCP_AUTH": "jwt",
                       "TSPI_JWT_JWKS_URI": "https://idp.example/.well-known/jwks.json",
                       "TSPI_JWT_ISSUER": "https://idp.example", "TSPI_JWT_AUDIENCE": "tspi-mcp"})
    reload(c); reload(idn)
    auth = idn.build_auth()
    assert auth is not None and auth.__class__.__name__ == "JWTVerifier"
    for k in ("TSPI_MCP_AUTH", "TSPI_JWT_JWKS_URI", "TSPI_JWT_ISSUER", "TSPI_JWT_AUDIENCE"):
        os.environ.pop(k, None)
    reload(c); reload(idn)
