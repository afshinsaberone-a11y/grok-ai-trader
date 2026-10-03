#!/usr/bin/env python3
"""Fail-closed validator for the ForexAI Quant Constitution v1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "principles",
    "capabilities",
    "hard_boundaries",
    "required_trade_proof",
    "required_trade_states",
    "forbidden_direct_transitions",
    "invariants",
}

REQUIRED_CAPABILITIES = {"research", "validation", "risk", "execution"}
REQUIRED_INVARIANTS = {
    "unauthorized_exposure == 0",
    "actual_risk <= authorized_risk",
    "executed_trade.authorization_exists == true",
    "executed_trade.authorization_not_expired == true",
    "invalid_model_output_cannot_be_executable_direction == true",
    "unresolved_reconciliation_blocks_new_risk == true",
    "research_process_oos_access == false",
    "production_cannot_mutate_frozen_evidence == true",
    "duplicate_request_cannot_create_duplicate_exposure == true",
    "restart_does_not_clear_safety_state == true",
    "mql5_execution_semantic_parity_audit == PASS",
    "deterministic_replay_digest_stable == true",
    "mql5_runtime_trace_cannot_grant_authority == true",
    "runtime_evidence_gate_requires_trace_replay_reconciliation_pass == true",
    "restart_uncertain_state_blocks_new_risk == true",
    "nonfinite_risk_input_must_be_rejected == true",
    "aggregate_authorized_risk <= global_cap == true",
    "mql5_new_order_requires_runtime_authorization_record == true",
    "runtime_authorization_record_cannot_increase_authorized_risk == true",
    "mql5_authorization_record_materialization_must_verify_current_firewall == true",
    "mql5_authorization_record_must_be_fresh_within_10_seconds == true",
    "broker_submission_requires_current_execution_admission == true",
    "execution_admission_rejects_stale_or_revoked_authority == true",
    "execution_admission_cannot_grant_capital_authority == true",
}


class ConstitutionError(RuntimeError):
    """A constitution invariant is missing or contradictory."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ConstitutionError(message)


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConstitutionError(f"CONSTITUTION_LOAD_FAIL:{path}:{exc}") from exc
    _require(isinstance(value, dict), "CONSTITUTION_ROOT_MUST_BE_OBJECT")
    return value


def validate(value: dict[str, Any]) -> dict[str, Any]:
    _require(value.get("schema_version") == "forexai.quant_constitution.v1", "CONSTITUTION_SCHEMA_MISMATCH")
    missing = sorted(REQUIRED_TOP_LEVEL - set(value))
    _require(not missing, f"CONSTITUTION_MISSING_TOP_LEVEL:{missing}")

    capabilities = value["capabilities"]
    _require(set(capabilities) == REQUIRED_CAPABILITIES, "CONSTITUTION_CAPABILITY_SET_MISMATCH")
    for name, capability in capabilities.items():
        _require(isinstance(capability, dict), f"CONSTITUTION_CAPABILITY_NOT_OBJECT:{name}")
        allow = capability.get("allow")
        deny = capability.get("deny")
        _require(isinstance(allow, list) and isinstance(deny, list), f"CONSTITUTION_CAPABILITY_LISTS_REQUIRED:{name}")
        overlap = sorted(set(map(str, allow)) & set(map(str, deny)))
        _require(not overlap, f"CONSTITUTION_CAPABILITY_ALLOW_DENY_OVERLAP:{name}:{overlap}")

    oos = value["hard_boundaries"]["oos"]
    _require(oos["discovery_read"] is False, "OOS_DISCOVERY_MUST_BE_DENIED")
    _require(oos["optimization_read"] is False, "OOS_OPTIMIZATION_MUST_BE_DENIED")
    _require(oos["validation_read"] is False, "OOS_VALIDATION_MUST_BE_DENIED")
    _require(oos["final_evaluation_read"] is True, "OOS_FINAL_EVALUATION_MUST_BE_ALLOWED")
    _require(oos["production_write"] is False, "OOS_PRODUCTION_WRITE_MUST_BE_DENIED")

    capital = value["hard_boundaries"]["capital"]
    _require(capital["default_authorized_risk"] == 0, "CAPITAL_DEFAULT_AUTHORIZATION_MUST_BE_ZERO")
    _require(capital["unauthorized_exposure_must_equal"] == 0, "UNAUTHORIZED_EXPOSURE_MUST_EQUAL_ZERO")
    _require(capital.get("risk_unit") == "equity_fraction", "CAPITAL_RISK_UNIT_MUST_BE_EQUITY_FRACTION")
    _require(capital.get("max_authorized_risk") == 0.006, "CAPITAL_MAX_AUTHORIZED_RISK_MUST_BE_0_006")
    _require(capital["risk_must_not_exceed_authorization"] is True, "RISK_CAP_INVARIANT_REQUIRED")
    _require(capital["expired_authorization_must_not_execute"] is True, "AUTH_EXPIRY_INVARIANT_REQUIRED")

    frozen = value["hard_boundaries"]["evidence"]
    _require(frozen["frozen_history_is_append_only"] is True, "FROZEN_EVIDENCE_MUST_BE_APPEND_ONLY")
    _require(
        frozen["dependency_change_invalidates_downstream_evidence"] is True,
        "DEPENDENCY_CHANGE_MUST_INVALIDATE_EVIDENCE",
    )

    proof = value["required_trade_proof"]
    required_proof = {
        "snapshot_id",
        "decision_id",
        "strategy_id",
        "model_id",
        "policy_version",
        "risk_authorization_id",
        "authorization_expiry",
        "input_hash",
        "execution_contract_version",
    }
    _require(set(proof) == required_proof, "TRADE_PROOF_FIELDS_MISMATCH")

    transitions = value["forbidden_direct_transitions"]
    _require(isinstance(transitions, list) and transitions, "FORBIDDEN_TRANSITIONS_MISSING")
    for transition in transitions:
        _require(isinstance(transition, list) and len(transition) == 2, f"INVALID_FORBIDDEN_TRANSITION:{transition}")

    states = value["required_trade_states"]
    _require(len(states) == len(set(states)), "TRADE_STATES_MUST_BE_UNIQUE")
    _require({"PROPOSED", "AUTHORIZED", "FILLED", "CLOSED", "RECONCILED"} <= set(states), "TRADE_STATE_CORE_MISSING")

    invariants = set(map(str, value["invariants"]))
    _require(REQUIRED_INVARIANTS <= invariants, "CONSTITUTION_REQUIRED_INVARIANTS_MISSING")

    research_deny = set(value["capabilities"]["research"]["deny"])
    validation_deny = set(value["capabilities"]["validation"]["deny"])
    execution_deny = set(value["capabilities"]["execution"]["deny"])
    _require("authorize_capital" in research_deny, "RESEARCH_MUST_NOT_AUTHORIZE_CAPITAL")
    _require("send_order" in research_deny, "RESEARCH_MUST_NOT_SEND_ORDERS")
    _require("authorize_capital" in validation_deny, "VALIDATION_MUST_NOT_AUTHORIZE_CAPITAL")
    _require("send_order" in validation_deny, "VALIDATION_MUST_NOT_SEND_ORDERS")
    _require("increase_authorized_risk" in execution_deny, "EXECUTION_MUST_NOT_INCREASE_RISK")

    return {
        "schema_version": value["schema_version"],
        "status": "PASS",
        "capability_domains": sorted(capabilities),
        "invariant_count": len(invariants),
        "forbidden_transition_count": len(transitions),
        "oos": oos,
        "capital_default_authorized_risk": capital["default_authorized_risk"],
        "capital_max_authorized_risk": capital["max_authorized_risk"],
        "capital_risk_unit": capital["risk_unit"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default="config/forexai_quant_constitution_v1.json")
    args = parser.parse_args()

    result = validate(load(Path(args.path)))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConstitutionError as exc:
        print(f"CONSTITUTION_FAIL_CLOSED:{exc}")
        raise SystemExit(2)
