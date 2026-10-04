"""Fail-closed validator for a real MT5 Demo execution evidence package v1.

This validator does not trade, optimize, approve capital, or enable Live trading.
It accepts only a completed Demo evidence package whose runtime/evidence gates
are already independently PASS and whose broker lifecycle is reconciled.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "forexai.demo_execution_evidence.v1"
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")


class DemoEvidenceError(RuntimeError):
    """Demo evidence is incomplete, contradictory, or unsafe."""


REQUIRED = {
    "schema",
    "status",
    "commit_sha",
    "ea_source_sha256",
    "strategy_id",
    "trade_id",
    "symbol",
    "timeframe",
    "account_mode",
    "terminal_connected",
    "broker_order_id",
    "broker_deal_id",
    "execution_status",
    "full_fill",
    "reconciliation_status",
    "unresolved_broker_outcomes",
    "runtime_evidence_gate_status",
    "deterministic_replay_status",
    "live_enabled",
    "order_submission_performed",
}


def validate_demo_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED - set(payload))
    if missing:
        raise DemoEvidenceError("DEMO_EVIDENCE_REQUIRED_FIELD_MISSING:" + ",".join(missing))

    if payload["schema"] != SCHEMA:
        raise DemoEvidenceError("DEMO_EVIDENCE_SCHEMA_MISMATCH")

    if payload["status"] != "PASS":
        raise DemoEvidenceError("DEMO_EVIDENCE_STATUS_NOT_PASS")

    if payload["account_mode"] != "DEMO":
        raise DemoEvidenceError("DEMO_EVIDENCE_ACCOUNT_NOT_DEMO")

    if payload["live_enabled"] is not False:
        raise DemoEvidenceError("DEMO_EVIDENCE_LIVE_MUST_REMAIN_DISABLED")

    if payload["terminal_connected"] is not True:
        raise DemoEvidenceError("DEMO_EVIDENCE_TERMINAL_NOT_CONNECTED")

    if payload["order_submission_performed"] is not True:
        raise DemoEvidenceError("DEMO_EVIDENCE_NO_ORDER_SUBMISSION")

    if payload["execution_status"] != "ACCEPTED":
        raise DemoEvidenceError("DEMO_EVIDENCE_EXECUTION_NOT_ACCEPTED")

    if payload["full_fill"] is not True:
        raise DemoEvidenceError("DEMO_EVIDENCE_FILL_NOT_COMPLETE")

    if not isinstance(payload["broker_order_id"], (str, int)) or not str(payload["broker_order_id"]).strip() or str(payload["broker_order_id"]).lower() in {"none", "null", "0"}:
        raise DemoEvidenceError("DEMO_EVIDENCE_BROKER_ORDER_ID_MISSING")

    if not isinstance(payload["broker_deal_id"], (str, int)) or not str(payload["broker_deal_id"]).strip() or str(payload["broker_deal_id"]).lower() in {"none", "null", "0"}:
        raise DemoEvidenceError("DEMO_EVIDENCE_BROKER_DEAL_ID_MISSING")

    if payload["reconciliation_status"] != "RECONCILED":
        raise DemoEvidenceError("DEMO_EVIDENCE_NOT_RECONCILED")

    if payload["unresolved_broker_outcomes"] is not False:
        raise DemoEvidenceError("DEMO_EVIDENCE_UNRESOLVED_BROKER_OUTCOME")

    if payload["runtime_evidence_gate_status"] != "PASS":
        raise DemoEvidenceError("DEMO_EVIDENCE_RUNTIME_GATE_NOT_PASS")

    if payload["deterministic_replay_status"] != "PASS":
        raise DemoEvidenceError("DEMO_EVIDENCE_REPLAY_NOT_PASS")

    if not isinstance(payload["commit_sha"], str) or not SHA40.fullmatch(payload["commit_sha"]):
        raise DemoEvidenceError("DEMO_EVIDENCE_COMMIT_SHA_INVALID")

    if not isinstance(payload["ea_source_sha256"], str) or not re.fullmatch(r"^[0-9a-fA-F]{64}$", payload["ea_source_sha256"]):
        raise DemoEvidenceError("DEMO_EVIDENCE_EA_SOURCE_SHA256_INVALID")

    for field, error in (
        ("strategy_id", "DEMO_EVIDENCE_STRATEGY_ID_MISSING"),
        ("trade_id", "DEMO_EVIDENCE_TRADE_ID_MISSING"),
        ("symbol", "DEMO_EVIDENCE_SYMBOL_MISSING"),
        ("timeframe", "DEMO_EVIDENCE_TIMEFRAME_MISSING"),
    ):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise DemoEvidenceError(error)

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "account_mode": "DEMO",
        "trade_id": str(payload["trade_id"]),
        "symbol": str(payload["symbol"]),
        "timeframe": str(payload["timeframe"]),
        "broker_order_id": str(payload["broker_order_id"]),
        "broker_deal_id": str(payload["broker_deal_id"]),
        "ea_source_sha256": str(payload["ea_source_sha256"]),
        "reconciliation_status": "RECONCILED",
        "live_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    try:
        payload = json.loads(args.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise DemoEvidenceError("DEMO_EVIDENCE_ROOT_MUST_BE_OBJECT")
        result = validate_demo_evidence(payload)
    except (OSError, json.JSONDecodeError, DemoEvidenceError) as exc:
        print(f"DEMO_EVIDENCE_FAIL_CLOSED:{exc}")
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
