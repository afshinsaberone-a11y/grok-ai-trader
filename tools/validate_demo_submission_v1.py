"""Fail-closed validator for one real MT5 Demo execution submission receipt."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA = "forexai.mt5_demo_execution_submission.v1"
SHA40 = re.compile(r"^[0-9a-fA-F]{40}$")

REQUIRED = {
    "schema","status","account_mode","terminal_connected","order_submission_performed",
    "execution_status","full_fill","trade_id","strategy_id","symbol","timeframe","side",
    "volume","filled_volume","remaining_volume","broker_order_id","broker_deal_id",
    "broker_retcode","live_enabled",
}


class DemoSubmissionError(RuntimeError):
    pass


def validate_submission(payload: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED - set(payload))
    if missing:
        raise DemoSubmissionError("DEMO_SUBMISSION_REQUIRED_FIELD_MISSING:" + ",".join(missing))
    if payload["schema"] != SCHEMA:
        raise DemoSubmissionError("DEMO_SUBMISSION_SCHEMA_MISMATCH")
    for field, expected, code in (
        ("status","PASS","STATUS_NOT_PASS"),
        ("account_mode","DEMO","ACCOUNT_NOT_DEMO"),
        ("terminal_connected",True,"TERMINAL_NOT_CONNECTED"),
        ("order_submission_performed",True,"NO_ORDER_SUBMISSION"),
        ("execution_status","ACCEPTED","EXECUTION_NOT_ACCEPTED"),
        ("full_fill",True,"FILL_NOT_COMPLETE"),
        ("live_enabled",False,"LIVE_MUST_REMAIN_DISABLED"),
    ):
        if payload[field] != expected:
            raise DemoSubmissionError("DEMO_SUBMISSION_" + code)
    for field in ("trade_id","strategy_id","symbol","timeframe","side","broker_order_id","broker_deal_id","broker_retcode"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise DemoSubmissionError(f"DEMO_SUBMISSION_{field.upper()}_INVALID")
    if payload["side"] not in {"BUY","SELL"}:
        raise DemoSubmissionError("DEMO_SUBMISSION_SIDE_INVALID")
    for field in ("volume","filled_volume","remaining_volume"):
        try:
            x=float(payload[field])
        except (TypeError,ValueError,OverflowError) as exc:
            raise DemoSubmissionError(f"DEMO_SUBMISSION_{field.upper()}_INVALID") from exc
        if not math.isfinite(x) or x < 0:
            raise DemoSubmissionError(f"DEMO_SUBMISSION_{field.upper()}_INVALID")
    volume=float(payload["volume"]); filled=float(payload["filled_volume"]); remaining=float(payload["remaining_volume"])
    if volume <= 0 or not math.isclose(filled, volume, rel_tol=0.0, abs_tol=1e-9) or remaining != 0.0:
        raise DemoSubmissionError("DEMO_SUBMISSION_NOT_FULLY_FILLED")
    return {
        "schema": SCHEMA, "status":"PASS", "account_mode":"DEMO", "trade_id":payload["trade_id"],
        "strategy_id":payload["strategy_id"], "symbol":payload["symbol"], "timeframe":payload["timeframe"],
        "side":payload["side"], "volume":volume, "filled_volume":filled, "remaining_volume":remaining,
        "broker_order_id":payload["broker_order_id"], "broker_deal_id":payload["broker_deal_id"],
        "broker_retcode":payload["broker_retcode"], "live_enabled":False,
    }


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args=parser.parse_args()
    try:
        data=json.loads(args.path.read_text(encoding="utf-8"))
        print(json.dumps(validate_submission(data), ensure_ascii=False, indent=2, sort_keys=True))
    except (OSError,UnicodeError,json.JSONDecodeError,DemoSubmissionError) as exc:
        print(f"DEMO_SUBMISSION_FAIL_CLOSED:{exc}")
        raise SystemExit(2)
