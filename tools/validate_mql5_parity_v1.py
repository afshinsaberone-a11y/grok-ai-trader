"""Static fail-closed parity audit for the canonical ForexAI MQL5 execution adapter."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


class ParityError(RuntimeError):
    pass


def load_contract(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ParityError(f"PARITY_CONTRACT_LOAD_FAIL:{exc}") from exc
    if value.get("schema_version") != "forexai.execution_parity.v1":
        raise ParityError("PARITY_CONTRACT_SCHEMA_MISMATCH")
    return value


def audit_source(source: str, contract: dict[str, Any]) -> dict[str, Any]:
    if not source.strip():
        raise ParityError("MQL5_SOURCE_EMPTY")

    checks: dict[str, bool] = {}
    checks["mql5_trace_string_literal_sanity"] = not bool(re.search(r'StringFormat\(\s*""', source)) and not bool(re.search(r'^\s+""[A-Za-z_]', source, re.MULTILINE))
    checks["mql5_trace_full_write_verified"] = "written != StringLen(row)" in source
    checks["risk_guard_060_percent"] = bool(re.search(r"if\s*\(\s*RiskPercent\s*>\s*0\.6\s*\)\s*return\s+INIT_FAILED", source))
    checks["max_positions_one"] = bool(re.search(r"input\s+int\s+MaxPositions\s*=\s*1\s*;", source)) and bool(re.search(r"if\s*\(\s*MaxPositions\s*!=\s*1\s*\)\s*return\s+INIT_FAILED", source))
    checks["max_hold_bars_30"] = bool(re.search(r"input\s+int\s+MaxHoldBars\s*=\s*30\s*;", source))
    checks["closed_bar_signal"] = "iTime(_Symbol, PERIOD_CURRENT, 0)" in source and "static datetime last_bar" in source
    checks["next_bar_runtime_boundary"] = "datetime t = iTime(_Symbol, PERIOD_CURRENT, 0);" in source and "if(t == last_bar) return;" in source
    checks["time_stop_contains_open_bar"] = bool(re.search(r"iBarShift\(\s*_Symbol\s*,\s*PERIOD_CURRENT\s*,\s*opened\s*,\s*false\s*\)", source))
    checks["native_symbol_filling"] = "trade.SetTypeFillingBySymbol(_Symbol);" in source
    checks["retcode_verified"] = "trade.ResultRetcode()" in source and "TRADE_RETCODE_DONE" in source
    checks["deal_ticket_verified"] = "trade.ResultDeal()" in source
    checks["order_ticket_verified"] = "trade.ResultOrder()" in source
    checks["partial_fill_not_accepted_as_success"] = (
        "TRADE_RETCODE_DONE_PARTIAL" in source
        and "return (rc == TRADE_RETCODE_DONE) && deal > 0;" in source
    )
    checks["consumption_failure_blocks_new_orders"] = (
        "if(!MarkRuntimeAuthorizationConsumed(trace_trade_id))" in source
    )
    checks["runtime_trace_outcome_observation_contract"] = (
        "TraceOutcomeObservation" in source
        and "BROKER_OUTCOME_UNKNOWN" in source
        and "BROKER_PARTIAL_EXECUTION_OBSERVED" in source
        and "ORDER_SUBMITTED" in source
    )
    checks["failed_submission_not_counted"] = all((
        re.search(r"bool\s+submitted\s*=\s*trade\.(?:Buy|Sell)\(", source),
        re.search(r"if\(!submitted\)\s*\{[\s\S]*?return\s+false;\s*\}", source),
        re.search(r"if\(!TradeExecutionAccepted\(\)\)\s*\{[\s\S]*?return\s+false;\s*\}", source),
        "trades_today++;" in source,
    ))
    checks["freeze_level_checked"] = "SYMBOL_TRADE_FREEZE_LEVEL" in source and "MathMax(stops, freeze)" in source
    checks["trade_mode_permission_checked"] = "SYMBOL_TRADE_MODE" in source and "SYMBOL_ORDER_MODE" in source and "TradeModeAllows" in source
    checks["close_retcode_verified"] = "trade.PositionClose(ticket)" in source and "TRADE_RETCODE_DONE" in source and "Protective closes are counted only after broker ResultRetcode confirmation." in source
    checks["broker_clock_explicit"] = "TimeCurrent()" in source and "broker_timestamp" in source and "TimeGMT()" in source
    checks["restart_state_persistence"] = "GlobalVariableSet" in source and "GlobalVariableGet" in source and "LoadSafetyState" in source and "PersistSafetyState" in source
    checks["runtime_trace_schema"] = "forexai.runtime_trace.v1" in source and "FOREXAI-RUNTIME-TRACE-V1" in source
    checks["runtime_trace_common_file_write"] = "FileOpen(" in source and "FILE_COMMON" in source and "FileWriteString" in source and "FileFlush" in source
    checks["runtime_trace_utc_timestamp"] = "TimeGMT()" in source and "timestamp_utc" in source
    checks["runtime_trace_broker_timestamp"] = "TimeCurrent()" in source and "broker_timestamp" in source
    checks["runtime_trace_broker_offset_evidence"] = "broker_utc_offset_seconds" in source and "TimeCurrent() - TimeGMT()" in source
    checks["runtime_trace_lifecycle"] = all(token in source for token in (
        '"ORDER_SUBMITTED"', '"ACCEPTED"', '"FILLED"', '"OPEN"', '"MANAGED"', '"CLOSED"'
    ))
    checks["runtime_trace_observational_only"] = (
        "CAPITAL_AUTHORIZATION_ISSUED" not in source
        and "CAPITAL_AUTHORIZATION_REVOKED" not in source
        and "TRADE_AUTHORIZED" not in source
        and "CAPITAL_RESERVATION_CREATED" not in source
    )
    checks["runtime_trace_fail_closed"] = "runtime_trace_healthy" in source and "if(!runtime_trace_healthy) return;" in source and "EnsureRuntimeTraceReady" in source
    checks["runtime_authorization_record_schema"] = "forexai.mql5_authorization_record.v1" in source and "FOREXAI-AUTH-V1" in source
    checks["runtime_authorization_symbol_binding"] = "parts[5] != _Symbol" in source and "parts[5]" in source
    checks["runtime_authorization_timeframe_binding"] = "parts[6] != current_timeframe" in source and "EnumToString(_Period)" in source
    checks["runtime_authorization_sha256"] = "CRYPT_HASH_SHA256" in source and "Sha256Hex" in source
    checks["runtime_authorization_common_file"] = "FILE_COMMON" in source and "AuthorizationFile()" in source and "FileReadString" in source
    checks["runtime_authorization_fail_closed"] = (
        "RequireRuntimeAuthorization" in source
        and "VerifyRuntimeAuthorization" in source
        and "if(!VerifyRuntimeAuthorization(trace_trade_id" in source
        and "if(!RequireRuntimeAuthorization) return INIT_FAILED;" in source
    )
    checks["runtime_authorization_risk_cap"] = "authorized > 0.006" in source and "risk_fraction = MathMin(risk_fraction, runtime_reserved_risk)" in source
    checks["runtime_authorization_execution_contract_version"] = '"forexai.execution.v1"' in source
    checks["runtime_authorization_expiry"] = "TimeGMT()" in source and "expiry_epoch" in source and "runtime_authorization_expiry_epoch" in source
    checks["runtime_authorization_freshness"] = (
        "RuntimeAuthorizationMaxAgeSeconds = 10" in source
        and "issued_epoch > now_epoch" in source
        and "now_epoch - issued_epoch > RuntimeAuthorizationMaxAgeSeconds" in source
    )
    checks["runtime_authorization_consumed"] = (
        "AuthorizationConsumedKey" in source
        and "MarkRuntimeAuthorizationConsumed" in source
        and "GlobalVariablesFlush()" in source
    )
    checks["runtime_authorization_single_attempt"] = (
        "AuthorizationAttemptKey" in source
        and "BeginRuntimeAuthorizationAttempt" in source
        and "GlobalVariableSetOnCondition" in source
        and "if(!BeginRuntimeAuthorizationAttempt(trace_trade_id" in source
    )
    checks["runtime_authorization_state_key_bounded"] = (
        "AuthorizationIdentityDigest" in source
        and "StringSubstr(digest, 0, 32)" in source
        and '"ForexAI.v1.a.c."' in source
        and '"ForexAI.v1.a.t."' in source
    )

    expected = {
        "max_positions_one": contract["live_mql5"]["max_positions"] == 1,
        "max_hold_bars_30": contract["live_mql5"]["max_hold_bars"] == 30,
        "native_symbol_filling": contract["live_mql5"]["filling_mode"] == "symbol_native",
        "semantic_execution_identity": contract["parity_policy"]["semantic_execution_identity_required"] is True,
        "restart_safety_state_required": contract["parity_policy"]["restart_safety_state_required"] is True,
        "runtime_trace_emission_required": contract["parity_policy"]["runtime_trace_emission_required"] is True
            and contract["live_mql5"]["runtime_trace"]["enabled"] is True,
        "runtime_trace_cannot_grant_authority": contract["parity_policy"]["runtime_trace_cannot_grant_authority"] is True
            and contract["live_mql5"]["runtime_trace"]["capital_authority_events_forbidden"] is True,
        "runtime_trace_failure_blocks_new_orders": contract["parity_policy"]["runtime_trace_failure_blocks_new_orders"] is True
            and contract["live_mql5"]["runtime_trace"]["failure_policy"] == "BLOCK_NEW_ORDERS"
            and contract["live_mql5"]["runtime_trace"]["existing_position_management"] == "CONTINUE_PROTECTIVE_CLOSES",
        "runtime_authorization_required": contract["parity_policy"]["runtime_authorization_required"] is True
            and contract["live_mql5"]["runtime_authorization"]["enabled"] is True
            and contract["live_mql5"]["runtime_authorization"]["missing_record_policy"] == "BLOCK_NEW_ORDERS",
        "runtime_authorization_fail_closed": contract["parity_policy"]["runtime_authorization_fail_closed"] is True
            and contract["live_mql5"]["runtime_authorization"]["expired_record_policy"] == "BLOCK_NEW_ORDERS"
            and contract["live_mql5"]["runtime_authorization"]["trade_id_mismatch_policy"] == "BLOCK_NEW_ORDERS",
        "runtime_authorization_risk_cap_enforced": contract["parity_policy"]["runtime_authorization_risk_cap_enforced"] is True
            and contract["live_mql5"]["runtime_authorization"]["risk_cap"] == 0.006,
        "runtime_authorization_execution_contract_version": (
            contract["live_mql5"]["runtime_authorization"]["required_execution_contract_version"]
            == "forexai.execution.v1"
        ),
        "runtime_authorization_execution_identity": (
            contract["live_mql5"]["runtime_authorization"]["execution_identity_fields"] == ["symbol", "timeframe"]
        ),
        "runtime_authorization_freshness": (
            contract["live_mql5"]["runtime_authorization"]["max_record_age_seconds"] == 10
        ),
        "runtime_authorization_single_attempt": (
            contract["live_mql5"]["runtime_authorization"]["single_attempt_lock_before_submission"] is True
            and contract["live_mql5"]["runtime_authorization"]["single_attempt_lock_uses_atomic_terminal_global_variable"] is True
            and contract["live_mql5"]["runtime_authorization"]["consumption_persistence_is_fail_closed"] is True
        ),
        "runtime_authorization_state_key_bounded": (
            contract["live_mql5"]["runtime_authorization"]["terminal_global_variable_name_max_length"] == 63
            and contract["live_mql5"]["runtime_authorization"]["state_key_digest_algorithm"] == "SHA-256"
            and contract["live_mql5"]["runtime_authorization"]["state_key_digest_characters"] == 32
        ),
    }
    for key, value in expected.items():
        checks[f"contract_{key}"] = bool(value)

    failed = sorted(name for name, ok in checks.items() if not ok)
    if failed:
        raise ParityError("MQL5_PARITY_FAIL_CLOSED:" + ",".join(failed))

    return {
        "schema": "forexai.mql5_execution_parity_audit.v1",
        "status": "PASS",
        "checks": checks,
        "market_price_identity": "not_required",
        "semantic_execution_identity": "required",
    }


def run(ea_path: str | Path, contract_path: str | Path, output: str | Path | None = None) -> dict[str, Any]:
    ea = Path(ea_path)
    contract = load_contract(Path(contract_path))
    try:
        source = ea.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ParityError(f"MQL5_SOURCE_READ_FAIL:{exc}") from exc
    result = audit_source(source, contract)
    result["ea_path"] = str(ea)
    result["contract_path"] = str(contract_path)
    if output:
        p = Path(output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ea", default="ea/GRK_Hybrid_Regime_EA.mq5")
    parser.add_argument("--contract", default="config/forexai_execution_parity_v1.json")
    parser.add_argument("--output")
    args = parser.parse_args()
    run(args.ea, args.contract, args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ParityError as exc:
        print(f"PARITY_FAIL_CLOSED:{exc}")
        raise SystemExit(2)
