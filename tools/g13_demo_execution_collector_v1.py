"""Collect real G13 M15 Demo execution telemetry without placing orders."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

from tools.mt5_terminal_gateway_v1 import MT5GatewayConfig, MT5GatewayError, MT5TerminalGateway

CONFIRMATION = "DEMO_EXECUTION_CONFIRMED"
AUDIT_NAME = "g13_demo_execution_audit.csv"
CONTEXT_SCHEMA = "forexai.g13.controlled_demo_execution_context.v1"


def _common_files_path(mt5: Any) -> Path:
    terminal = mt5.terminal_info()
    if terminal is None:
        raise MT5GatewayError("DEMO_COLLECTOR_TERMINAL_INFO_UNAVAILABLE")
    common = getattr(terminal, "commondata_path", None)
    if not common:
        raise MT5GatewayError("DEMO_COLLECTOR_COMMONDATA_PATH_UNAVAILABLE")
    return Path(str(common)) / "Files"


def _assert_demo(mt5: Any, symbol: str) -> dict[str, Any]:
    account = mt5.account_info()
    terminal = mt5.terminal_info()
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if account is None:
        raise MT5GatewayError("DEMO_COLLECTOR_ACCOUNT_INFO_UNAVAILABLE")
    if terminal is None:
        raise MT5GatewayError("DEMO_COLLECTOR_TERMINAL_INFO_UNAVAILABLE")
    if info is None:
        raise MT5GatewayError("DEMO_COLLECTOR_SYMBOL_NOT_FOUND")
    if tick is None:
        raise MT5GatewayError("DEMO_COLLECTOR_TICK_UNAVAILABLE")
    demo = int(getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0))
    if int(getattr(account, "trade_mode", -1)) != demo:
        raise MT5GatewayError("DEMO_COLLECTOR_REAL_ACCOUNT_BLOCKED")
    bid = float(getattr(tick, "bid", 0.0))
    ask = float(getattr(tick, "ask", 0.0))
    if bid <= 0.0 or ask <= 0.0:
        raise MT5GatewayError("DEMO_COLLECTOR_INVALID_TICK")
    if not bool(getattr(terminal, "connected", True)):
        raise MT5GatewayError("DEMO_COLLECTOR_TERMINAL_NOT_CONNECTED")
    return {
        "account_login": int(getattr(account, "login", 0)),
        "account_server": str(getattr(account, "server", "")),
        "account_mode": "DEMO",
        "terminal_connected": True,
        "account_trade_allowed": bool(getattr(account, "trade_allowed", False)),
        "account_trade_expert": bool(getattr(account, "trade_expert", False)),
        "symbol_visible": bool(getattr(info, "visible", False)),
        "symbol_trade_mode": int(getattr(info, "trade_mode", -1)),
        "bid": bid,
        "ask": ask,
        "terminal_build": str(getattr(terminal, "build", "")),
    }


def _kill_switch_state(common_files: Path) -> str:
    path = common_files / "g13_demo_kill_switch.txt"
    if not path.is_file():
        raise MT5GatewayError("DEMO_COLLECTOR_KILL_SWITCH_MISSING")
    state = path.read_text(encoding="utf-8", errors="strict").strip()
    if state != "ALLOW":
        raise MT5GatewayError(f"DEMO_COLLECTOR_KILL_SWITCH_NOT_ALLOW:{state!r}")
    return state


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _wait_for_candidate(
    path: Path,
    *,
    candidate_id: int,
    baseline_rows: int,
    timeout_seconds: int,
    poll_seconds: float,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() <= deadline:
        if path.is_file():
            rows = _read_rows(path)
            if len(rows) > baseline_rows:
                new_rows = rows[baseline_rows:]
                matches = [r for r in new_rows if r.get("candidate_id") == str(candidate_id)]
                attempts = [r for r in matches if r.get("event") == "ORDER_ATTEMPT"]
                if len(attempts) > 1:
                    raise MT5GatewayError("DEMO_COLLECTOR_MULTIPLE_ORDER_ATTEMPTS")
                if attempts:
                    row = attempts[0]
                    try:
                        retcode = int(row["retcode"])
                        order_id = int(row["order"])
                        deal_id = int(row["deal"])
                        requested = float(row["requested_volume"])
                        executed = float(row["executed_volume"])
                    except (KeyError, TypeError, ValueError) as exc:
                        raise MT5GatewayError("DEMO_COLLECTOR_ORDER_ATTEMPT_MALFORMED") from exc
                    if row.get("side") != "SELL":
                        raise MT5GatewayError("DEMO_COLLECTOR_ORDER_SIDE_NOT_SELL")
                    if retcode != 10009:
                        raise MT5GatewayError(f"DEMO_COLLECTOR_BROKER_NOT_DONE:{retcode}")
                    if order_id <= 0 or deal_id <= 0:
                        raise MT5GatewayError("DEMO_COLLECTOR_MISSING_ORDER_OR_DEAL")
                    if requested <= 0.0 or executed <= 0.0 or abs(executed - requested) > 1e-9:
                        raise MT5GatewayError("DEMO_COLLECTOR_NOT_FULL_FILL")
                    return rows, new_rows
        time.sleep(max(0.2, poll_seconds))
    raise MT5GatewayError(
        f"DEMO_COLLECTOR_NO_ACCEPTED_FULL_FILL:{candidate_id}:timeout={timeout_seconds}s"
    )


def build_context(
    *,
    mt5_snapshot: dict[str, Any],
    candidate_id: int,
    confirmation: str,
    kill_switch: str,
    terminal_path: str | None,
    audit_path: Path,
) -> dict[str, Any]:
    if confirmation != CONFIRMATION:
        raise MT5GatewayError("DEMO_COLLECTOR_EXPLICIT_CONFIRMATION_REQUIRED")
    if kill_switch != "ALLOW":
        raise MT5GatewayError("DEMO_COLLECTOR_KILL_SWITCH_NOT_ALLOW")
    if mt5_snapshot.get("account_mode") != "DEMO":
        raise MT5GatewayError("DEMO_COLLECTOR_CONTEXT_NOT_DEMO")
    return {
        "schema": CONTEXT_SCHEMA,
        "status": "PASS",
        "account_mode": "DEMO",
        "live_enabled": False,
        "explicit_demo_authorization": True,
        "kill_switch": "ALLOW",
        "candidate_id": candidate_id,
        "symbol": "EURUSD",
        "timeframe": "M15",
        "terminal_path": terminal_path or "",
        "audit_path": str(audit_path),
        "mt5": mt5_snapshot,
        "collector_policy": {
            "order_submission_performed": False,
            "retry_performed": False,
            "capital_authority_granted": False,
            "kill_switch_modified": False,
            "ea_inputs_modified": False,
            "python_order_send_used": False,
        },
        "operator_confirmation": {
            "value": CONFIRMATION,
            "meaning": "Human-confirmed Demo execution window for the frozen EA.",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate-id", type=int, required=True)
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--terminal-path")
    ap.add_argument("--audit-csv", type=Path)
    ap.add_argument("--context-out", type=Path, required=True)
    ap.add_argument("--report-out", type=Path, required=True)
    ap.add_argument("--confirmation", required=True)
    ap.add_argument("--timeout-seconds", type=int, default=900)
    ap.add_argument("--poll-seconds", type=float, default=2.0)
    ap.add_argument("--evidence-csv-out", type=Path, required=True)
    args = ap.parse_args()

    if args.confirmation != CONFIRMATION:
        print("DEMO_COLLECTOR_FAIL_CLOSED:EXPLICIT_CONFIRMATION_REQUIRED")
        return 2

    gateway = MT5TerminalGateway(
        MT5GatewayConfig(terminal_path=args.terminal_path, shutdown_after_request=True)
    )
    mt5 = gateway.mt5
    gateway._initialize()
    try:
        snapshot = _assert_demo(mt5, args.symbol)
        common_files = _common_files_path(mt5)
        kill_switch = _kill_switch_state(common_files)
        audit_path = args.audit_csv or (common_files / AUDIT_NAME)
        baseline_rows = len(_read_rows(audit_path)) if audit_path.is_file() else 0
        rows, new_rows = _wait_for_candidate(
            audit_path,
            candidate_id=args.candidate_id,
            baseline_rows=baseline_rows,
            timeout_seconds=args.timeout_seconds,
            poll_seconds=args.poll_seconds,
        )
        args.evidence_csv_out.parent.mkdir(parents=True, exist_ok=True)
        if not new_rows:
            raise MT5GatewayError("DEMO_COLLECTOR_NO_NEW_EVIDENCE_ROWS")
        fieldnames = list(new_rows[0].keys())
        with args.evidence_csv_out.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_rows)
        context = build_context(
            mt5_snapshot=snapshot,
            candidate_id=args.candidate_id,
            confirmation=args.confirmation,
            kill_switch=kill_switch,
            terminal_path=args.terminal_path,
            audit_path=audit_path,
        )
        args.context_out.parent.mkdir(parents=True, exist_ok=True)
        args.context_out.write_text(json.dumps(context, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report = {
            "schema": "forexai.g13.controlled_demo_execution_collector.v1",
            "status": "PASS",
            "account_mode": "DEMO",
            "symbol": args.symbol,
            "timeframe": "M15",
            "candidate_id": args.candidate_id,
            "audit_path": str(audit_path),
            "rows_collected": len(new_rows),
            "baseline_rows": baseline_rows,
            "broker_full_fill_detected": True,
            "order_attempt_detected": True,
            "accepted_full_fill": True,
            "collector_policy": context["collector_policy"],
            "notes": [
                "Collector is read-only with respect to trade execution.",
                "The frozen MQL5 EA is the only component allowed to place the Demo order.",
                "This artifact is not a profitability claim and not Live authorization.",
            ],
        }
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        return 0
    finally:
        gateway._shutdown()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MT5GatewayError, ImportError, OSError) as exc:
        print(f"DEMO_COLLECTOR_FAIL_CLOSED:{exc}")
        raise SystemExit(2)
