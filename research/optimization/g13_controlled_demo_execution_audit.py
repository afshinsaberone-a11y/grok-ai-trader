"""Validate G13 controlled-Demo execution evidence without placing trades.

The validator is intentionally offline/read-only. It checks that execution
telemetry is attributable to a frozen promoted candidate, Demo-only context,
and a complete set of execution fields. It never contacts a broker.
"""
from __future__ import annotations


# Gate assertions are part of the fail-closed contract; optimized Python (-O) must never disable them.
if not __debug__:
    raise RuntimeError("G13 gate refuses optimized Python execution; assertions must remain enabled.")

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "forexai.g13.controlled_demo_execution_audit.m15.v1"
PROMOTED_IDS = (2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48)
REQUIRED_COLUMNS = (
    "candidate_id",
    "config_hash",
    "event",
    "timestamp_utc",
    "symbol",
    "timeframe",
    "side",
    "order",
    "deal",
    "requested_volume",
    "executed_volume",
    "requested_price",
    "executed_price",
    "sl",
    "tp",
    "spread_points",
    "slippage_points",
    "retcode",
    "retcode_description",
    "elapsed_ms",
    "comment",
)

def finite(value: str) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False

def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def load_frozen_hashes(handoff: Path) -> dict[int, str]:
    payload = json.loads(handoff.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == "forexai.g13.candidate_handoff.frozen.v1"
    assert payload.get("handoff_policy", {}).get("parameters_are_frozen") is True
    assert payload.get("handoff_policy", {}).get("oos_optimization_disabled") is True
    hashes: dict[int, str] = {}
    for candidate in payload.get("candidates", []):
        cid = int(candidate["candidate_id"])
        if cid in PROMOTED_IDS:
            cfg = candidate["config_hash"]
            assert cfg == canonical_hash(candidate["params"])
            hashes[cid] = cfg
    assert set(hashes) == set(PROMOTED_IDS)
    return hashes

def load_context(path: Path) -> dict[str, Any]:
    p = json.loads(path.read_text(encoding="utf-8"))
    assert p.get("schema") == "forexai.g13.controlled_demo_execution_context.v1"
    assert p.get("account_mode") == "DEMO"
    assert p.get("live_enabled") is False
    assert p.get("explicit_demo_authorization") is True
    assert p.get("kill_switch") == "ALLOW"
    return p

def audit(csv_path: Path, handoff: Path, context: Path) -> dict[str, Any]:
    hashes = load_frozen_hashes(handoff)
    ctx = load_context(context)
    rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8", newline="")))
    assert rows, "execution audit CSV is empty"
    assert tuple(rows[0].keys()) == REQUIRED_COLUMNS, "unexpected execution audit columns"

    events = {"ORDER_ATTEMPT": 0, "TRADE_TRANSACTION": 0, "CLOSE_ATTEMPT": 0}
    candidate_counts: dict[int, int] = {}

    previous_ts = ""
    for idx, row in enumerate(rows, start=1):
        cid = int(row["candidate_id"])
        assert cid in PROMOTED_IDS, f"row {idx}: unknown candidate {cid}"
        assert row["config_hash"] == hashes[cid], f"row {idx}: config hash mismatch for candidate {cid}"
        assert row["symbol"] == "EURUSD", f"row {idx}: wrong symbol {row['symbol']}"
        assert row["timeframe"] == "M15", f"row {idx}: wrong timeframe {row['timeframe']}"
        assert row["event"] in events, f"row {idx}: unknown event {row['event']}"
        assert row["timestamp_utc"], f"row {idx}: missing timestamp"
        assert row["timestamp_utc"] >= previous_ts, f"row {idx}: non-monotonic timestamp"
        previous_ts = row["timestamp_utc"]

        for col in ("requested_volume","executed_volume","requested_price","executed_price",
                    "sl","tp","spread_points","slippage_points","elapsed_ms"):
            assert finite(row[col]), f"row {idx}: non-finite {col}"

        assert float(row["requested_volume"]) >= 0.0
        assert float(row["executed_volume"]) >= 0.0
        assert float(row["spread_points"]) >= 0.0
        assert float(row["elapsed_ms"]) >= 0.0

        events[row["event"]] += 1
        candidate_counts[cid] = candidate_counts.get(cid, 0) + 1

        if row["event"] == "ORDER_ATTEMPT":
            assert row["side"] == "SELL", f"row {idx}: G13 entry must be SELL"
            assert float(row["requested_volume"]) > 0.0
            assert float(row["requested_price"]) > 0.0
            assert float(row["sl"]) > 0.0
            assert float(row["tp"]) > 0.0
            assert int(row["order"]) >= 0
            assert int(row["deal"]) >= 0
        elif row["event"] == "TRADE_TRANSACTION":
            assert int(row["order"]) > 0 or int(row["deal"]) > 0
        elif row["event"] == "CLOSE_ATTEMPT":
            assert row["side"] == "CLOSE"
            assert int(row["order"]) >= 0
            assert int(row["deal"]) >= 0

    order_attempts = [r for r in rows if r["event"] == "ORDER_ATTEMPT"]
    assert order_attempts, "no ORDER_ATTEMPT evidence"
    for row in order_attempts:
        assert int(row["retcode"]) == 10009, "ORDER_ATTEMPT retcode must be TRADE_RETCODE_DONE"
        assert int(row["order"]) > 0, "ORDER_ATTEMPT broker order ticket missing"
        assert int(row["deal"]) > 0, "ORDER_ATTEMPT broker deal ticket missing"
        assert float(row["requested_volume"]) > 0.0
        assert float(row["executed_volume"]) > 0.0
        assert abs(float(row["executed_volume"]) - float(row["requested_volume"])) <= 1e-9

        matching_transactions = [
            r for r in rows
            if r["event"] == "TRADE_TRANSACTION"
            and str(r["order"]) == str(row["order"])
            and str(r["deal"]) == str(row["deal"])
        ]
        assert matching_transactions, "ORDER_ATTEMPT has no matching TRADE_TRANSACTION"

    return {
        "schema": SCHEMA,
        "status": "PASS",
        "policy": {
            "broker_execution_validated": True,
            "demo_only": True,
            "live_enabled": False,
            "trading_performed_by_validator": False,
        },
        "context": {
            "account_mode": ctx["account_mode"],
            "explicit_demo_authorization": ctx["explicit_demo_authorization"],
            "kill_switch": ctx["kill_switch"],
        },
        "scope": {
            "symbol": "EURUSD",
            "timeframe": "M15",
            "candidate_count": len(PROMOTED_IDS),
            "candidate_ids": list(PROMOTED_IDS),
            "row_count": len(rows),
        },
        "events": events,
        "candidate_event_rows": candidate_counts,
        "notes": [
            "This validator checks recorded execution evidence; it does not execute orders.",
            "A PASS does not establish profitability.",
            "Live execution is explicitly out of scope.",
        ],
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execution-csv", type=Path, required=True)
    ap.add_argument("--handoff", type=Path, required=True)
    ap.add_argument("--context", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    result = audit(args.execution_csv, args.handoff, args.context)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "row_count": result["scope"]["row_count"],
        "order_attempts": result["events"]["ORDER_ATTEMPT"],
        "transactions": result["events"]["TRADE_TRANSACTION"],
        "close_attempts": result["events"]["CLOSE_ATTEMPT"],
        "live_enabled": result["policy"]["live_enabled"],
    }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
