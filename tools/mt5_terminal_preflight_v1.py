"""Read-only MetaTrader 5 terminal preflight.

This command proves terminal connectivity and broker/account context without
creating, checking, or sending a trading order.
"""
from __future__ import annotations

import argparse
import json
from typing import Any

from tools.mt5_terminal_gateway_v1 import MT5GatewayError, MT5TerminalGateway


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--path")
    args = parser.parse_args()

    from tools.mt5_terminal_gateway_v1 import MT5GatewayConfig

    config = MT5GatewayConfig(terminal_path=args.path, shutdown_after_request=True)
    gateway = MT5TerminalGateway(config)

    mt5 = gateway.mt5
    gateway._initialize()
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        info = mt5.symbol_info(args.symbol)
        tick = mt5.symbol_info_tick(args.symbol)
        if terminal is None:
            raise MT5GatewayError("MT5_PREFLIGHT_TERMINAL_INFO_UNAVAILABLE")
        if account is None:
            raise MT5GatewayError("MT5_PREFLIGHT_ACCOUNT_INFO_UNAVAILABLE")
        if info is None:
            raise MT5GatewayError("MT5_PREFLIGHT_SYMBOL_NOT_FOUND")
        if tick is None:
            raise MT5GatewayError("MT5_PREFLIGHT_TICK_UNAVAILABLE")

        print(
            json.dumps(
                {
                    "schema": "forexai.mt5_terminal_preflight.v1",
                    "status": "PASS",
                    "symbol": args.symbol,
                    "terminal_connected": True,
                    "account_login": int(getattr(account, "login", 0)),
                    "account_server": str(getattr(account, "server", "")),
                    "account_trade_allowed": bool(getattr(account, "trade_allowed", False)),
                    "symbol_visible": bool(getattr(info, "visible", False)),
                    "symbol_trade_mode": int(getattr(info, "trade_mode", -1)),
                    "bid": float(getattr(tick, "bid", 0.0)),
                    "ask": float(getattr(tick, "ask", 0.0)),
                    "terminal_version": str(getattr(terminal, "build", "")),
                    "order_submission_performed": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    finally:
        gateway._shutdown()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MT5GatewayError, ImportError) as exc:
        print(f"MT5_PREFLIGHT_FAIL_CLOSED:{exc}")
        raise SystemExit(2)
