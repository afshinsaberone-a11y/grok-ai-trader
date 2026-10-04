"""Read-only MetaTrader 5 Demo broker observation CLI v1.

Connects to an existing MT5 terminal, observes one existing broker order,
and writes a JSON observation artifact. It never calls order_send/order_check
and never retries or grants capital authority.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.mt5_broker_observation_v1 import observe_order


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--broker-order-id", required=True)
    p.add_argument("--side", required=True, choices=("BUY", "SELL"))
    p.add_argument("--requested-volume", required=True, type=float)
    p.add_argument("--trade-id", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--terminal-path", default=None)
    return p.parse_args()


def _connect(terminal_path: str | None) -> Any:
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise RuntimeError("MT5_PYTHON_PACKAGE_NOT_INSTALLED") from exc

    ok = mt5.initialize(terminal_path) if terminal_path else mt5.initialize()
    if not ok:
        raise RuntimeError(f"MT5_INITIALIZE_FAILED:{mt5.last_error()}")
    return mt5


def main() -> int:
    args = _parse_args()
    mt5 = _connect(args.terminal_path)
    try:
        account = mt5.account_info()
        if account is None:
            raise RuntimeError("MT5_ACCOUNT_INFO_UNAVAILABLE")
        demo_mode = int(getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0))
        trade_mode = int(getattr(account, "trade_mode", -1))
        if trade_mode != demo_mode:
            raise RuntimeError("MT5_REAL_ACCOUNT_BLOCKED_BY_READ_ONLY_DEMO_OBSERVER")

        observation = observe_order(
            mt5,
            broker_order_id=args.broker_order_id,
            symbol=args.symbol,
            side=args.side,
            requested_volume=args.requested_volume,
        )
        payload = {
            "schema": "forexai.mt5_demo_broker_observation.v1",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS",
            "trade_id": args.trade_id,
            "account_mode": "DEMO",
            "terminal_connected": True,
            "order_submission_performed": False,
            "retry_performed": False,
            "capital_authority_granted": False,
            "observation": observation,
        }
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass

    Path(args.output).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
