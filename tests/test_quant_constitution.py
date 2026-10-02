from pathlib import Path

from tools.validate_quant_constitution import ConstitutionError, load, validate


ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / "config" / "forexai_quant_constitution_v1.json"


def test_constitution_passes():
    result = validate(load(CONSTITUTION))
    assert result["status"] == "PASS"
    assert result["capital_default_authorized_risk"] == 0
    assert result["oos"]["discovery_read"] is False
    assert result["oos"]["optimization_read"] is False


def test_constitution_rejects_oos_discovery_access():
    value = load(CONSTITUTION)
    value["hard_boundaries"]["oos"]["discovery_read"] = True
    try:
        validate(value)
    except ConstitutionError as exc:
        assert "OOS_DISCOVERY_MUST_BE_DENIED" in str(exc)
    else:
        raise AssertionError("OOS discovery access must fail closed")


def test_constitution_rejects_capital_authority_overlap():
    value = load(CONSTITUTION)
    value["capabilities"]["research"]["allow"].append("authorize_capital")
    try:
        validate(value)
    except ConstitutionError as exc:
        assert "CAPABILITY_ALLOW_DENY_OVERLAP" not in str(exc)
        raise
    # Research already denies capital authorization, so the overlap must be rejected.
    try:
        validate(value)
    except ConstitutionError as exc:
        assert "CAPABILITY_ALLOW_DENY_OVERLAP:research" in str(exc)
    else:
        raise AssertionError("research capital capability must be denied")
