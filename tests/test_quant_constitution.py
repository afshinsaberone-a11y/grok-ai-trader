from pathlib import Path

import pytest

from tools.validate_quant_constitution import ConstitutionError, load, validate


ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / "config" / "forexai_quant_constitution_v1.json"


def test_constitution_passes():
    result = validate(load(CONSTITUTION))
    assert result["status"] == "PASS"
    assert result["capital_default_authorized_risk"] == 0
    assert result["capital_max_authorized_risk"] == 0.006
    assert result["capital_risk_unit"] == "equity_fraction"
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


def test_constitution_requires_nonfinite_risk_invariant():
    value = load(CONSTITUTION)
    value["invariants"] = [
        item for item in value["invariants"]
        if item != "nonfinite_risk_input_must_be_rejected == true"
    ]
    with pytest.raises(ConstitutionError, match="CONSTITUTION_REQUIRED_INVARIANTS_MISSING"):
        validate(value)



def test_constitution_rejects_capital_authority_overlap():
    value = load(CONSTITUTION)
    value["capabilities"]["research"]["allow"].append("authorize_capital")
    try:
        validate(value)
    except ConstitutionError as exc:
        assert "CAPABILITY_ALLOW_DENY_OVERLAP:research" in str(exc)
    else:
        raise AssertionError("research capital capability must be denied")


def test_constitution_rejects_higher_authorization_cap():
    value = load(CONSTITUTION)
    value["hard_boundaries"]["capital"]["max_authorized_risk"] = 0.01
    try:
        validate(value)
    except ConstitutionError as exc:
        assert "CAPITAL_MAX_AUTHORIZED_RISK_MUST_BE_0_006" in str(exc)
    else:
        raise AssertionError("capital authorization ceiling must fail closed")


def test_constitution_requires_mql5_runtime_authorization_invariants():
    value = load(CONSTITUTION)
    required = {
        "mql5_new_order_requires_runtime_authorization_record == true",
        "runtime_authorization_record_cannot_increase_authorized_risk == true",
    }
    value["invariants"] = [
        item for item in value["invariants"] if item not in required
    ]
    with pytest.raises(ConstitutionError, match="CONSTITUTION_REQUIRED_INVARIANTS_MISSING"):
        validate(value)


def test_constitution_requires_current_firewall_materialization_and_fresh_record():
    value = load(CONSTITUTION)
    required = {
        "mql5_authorization_record_materialization_must_verify_current_firewall == true",
        "mql5_authorization_record_must_be_fresh_within_10_seconds == true",
    }
    value["invariants"] = [
        item for item in value["invariants"] if item not in required
    ]
    with pytest.raises(ConstitutionError, match="CONSTITUTION_REQUIRED_INVARIANTS_MISSING"):
        validate(value)


def test_constitution_requires_current_execution_admission_invariants():
    value = load(CONSTITUTION)
    required = {
        "broker_submission_requires_current_execution_admission == true",
        "execution_admission_rejects_stale_or_revoked_authority == true",
        "execution_admission_cannot_grant_capital_authority == true",
    }
    value["invariants"] = [
        item for item in value["invariants"] if item not in required
    ]
    with pytest.raises(ConstitutionError, match="CONSTITUTION_REQUIRED_INVARIANTS_MISSING"):
        validate(value)


def test_constitution_requires_bounded_mql5_authorization_state_keys():
    value = load(CONSTITUTION)
    required = "mql5_authorization_state_keys_must_fit_terminal_global_variable_limit == true"
    value["invariants"] = [item for item in value["invariants"] if item != required]
    with pytest.raises(ConstitutionError, match="CONSTITUTION_REQUIRED_INVARIANTS_MISSING"):
        validate(value)


def test_constitution_requires_24_hour_authorization_lifetime_cap():
    value = load(CONSTITUTION)
    value["hard_boundaries"]["capital"]["max_authorization_lifetime_seconds"] = 172800
    with pytest.raises(ConstitutionError, match="CAPITAL_MAX_AUTHORIZATION_LIFETIME_MUST_BE_86400"):
        validate(value)


def test_constitution_requires_broker_submission_safety_invariants():
    value = load(CONSTITUTION)
    required = {
        "broker_submit_requires_durable_order_submitted_intent == true",
        "broker_unknown_outcome_requires_reconciliation == true",
        "broker_unknown_outcome_must_not_be_retried_automatically == true",
        "broker_acceptance_must_match_execution_identity == true",
    }
    value["invariants"] = [
        item for item in value["invariants"] if item not in required
    ]
    with pytest.raises(ConstitutionError, match="CONSTITUTION_REQUIRED_INVARIANTS_MISSING"):
        validate(value)


def test_constitution_requires_safe_pre_execution_reservation_release_boundary():
    value = load(CONSTITUTION)
    invariant = "pre_execution_reservation_release_requires_revocation_and_no_order_submission == true"
    value["invariants"] = [item for item in value["invariants"] if item != invariant]
    with pytest.raises(ConstitutionError, match="CONSTITUTION_REQUIRED_INVARIANTS_MISSING"):
        validate(value)
