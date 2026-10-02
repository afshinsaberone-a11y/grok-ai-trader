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
    checks["risk_guard_060_percent"] = bool(re.search(r"if\s*\(\s*RiskPercent\s*>\s*0\.6\s*\)\s*return\s+INIT_FAILED", source))
    checks["max_positions_one"] = bool(re.search(r"input\s+int\s+MaxPositions\s*=\s*1\s*;", source)) and bool(re.search(r"if\s*\(\s*MaxPositions\s*!=\s*1\s*\)\s*return\s+INIT_FAILED", source))
    checks["max_hold_bars_30"] = bool(re.search(r"input\s+int\s+MaxHoldBars\s*=\s*30\s*;", source))
    checks["closed_bar_signal"] = "iTime(_Symbol, PERIOD_CURRENT, 0)" in source and "static datetime last_bar" in source
    checks["next_bar_runtime_boundary"] = "datetime t = iTime(_Symbol, PERIOD_CURRENT, 0);" in source and "if(t == last_bar) return;" in source
    checks["time_stop_contains_open_bar"] = bool(re.search(r"iBarShift\(\s*_Symbol\s*,\s*PERIOD_CURRENT\s*,\s*opened\s*,\s*false\s*\)", source))
    checks["native_symbol_filling"] = "trade.SetTypeFillingBySymbol(_Symbol);" in source
    checks["retcode_verified"] = "trade.ResultRetcode()" in source and "TRADE_RETCODE_DONE" in source
    checks["deal_ticket_verified"] = "trade.ResultDeal()" in source
    checks["failed_submission_not_counted"] = bool(re.search(r"bool\s+submitted\s*=\s*trade\.(?:Buy|Sell)\([\s\S]*?\);[\s\S]*?if\(!submitted\)\s*return\s+false;[\s\S]*?if\(!TradeExecutionAccepted\(\)\)\s*return\s+false;[\s\S]*?trades_today\+\+;", source))
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
