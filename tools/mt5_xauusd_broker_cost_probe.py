"""Read-only MetaTrader 5 XAUUSD contract and realized-cost probe.

Run on Windows where the target MT5 terminal is already open and logged in.
This script never sends or modifies orders, never exports the account login ID,
and never exports raw deal tickets or position identifiers.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median


def aggregate_closed_positions(
    deals,
    *,
    symbol: str,
    contract_size: float,
    entry_codes: set[int],
    exit_codes: set[int],
) -> dict:
    """Summarize actual round-turn commissions/fees and swap by closed position.

    Positive output values mean cost/debit; negative values mean credit.
    All results stay in the account's deposit currency per ounce.
    """
    if not math.isfinite(float(contract_size)) or contract_size <= 0:
        raise ValueError("XAUUSD_CONTRACT_SIZE_INVALID")

    groups = defaultdict(lambda: {
        "opened_volume": 0.0,
        "closed_volume": 0.0,
        "commission_fee": 0.0,
        "swap": 0.0,
        "entry_deals": 0,
        "exit_deals": 0,
    })
    for deal in deals:
        if getattr(deal, "symbol", None) != symbol:
            continue
        position_id = int(getattr(deal, "position_id", 0) or 0)
        if position_id <= 0:
            continue
        entry = int(getattr(deal, "entry", -1))
        volume = float(getattr(deal, "volume", 0.0) or 0.0)
        if not math.isfinite(volume) or volume <= 0:
            continue
        item = groups[position_id]
        item["commission_fee"] += float(getattr(deal, "commission", 0.0) or 0.0)
        item["commission_fee"] += float(getattr(deal, "fee", 0.0) or 0.0)
        item["swap"] += float(getattr(deal, "swap", 0.0) or 0.0)
        if entry in entry_codes:
            item["opened_volume"] += volume
            item["entry_deals"] += 1
        if entry in exit_codes:
            item["closed_volume"] += volume
            item["exit_deals"] += 1

    commission_per_oz = []
    financing_per_oz = []
    round_turn_lots = []
    for item in groups.values():
        opened = item["opened_volume"]
        closed = item["closed_volume"]
        tolerance = max(1e-8, opened * 1e-6)
        if opened <= 0 or closed <= 0 or abs(opened - closed) > tolerance:
            continue
        ounces = opened * float(contract_size)
        if ounces <= 0:
            continue
        # Broker deal commission/fee/swap is normally negative for a debit.
        # Convert to positive cost convention used by the research simulator.
        commission_per_oz.append(-item["commission_fee"] / ounces)
        financing_per_oz.append(-item["swap"] / ounces)
        round_turn_lots.append(opened)

    def stats(values: list[float]) -> dict:
        if not values:
            return {"mean": None, "median": None, "min": None, "max": None}
        return {
            "mean": round(mean(values), 10),
            "median": round(median(values), 10),
            "min": round(min(values), 10),
            "max": round(max(values), 10),
        }

    return {
        "closed_position_count": len(commission_per_oz),
        "total_round_turn_lots": round(sum(round_turn_lots), 8),
        "commission_fee_cost_per_oz_account_currency": stats(commission_per_oz),
        "realized_financing_cost_per_oz_account_currency": stats(financing_per_oz),
        "sample_is_adequate_for_cost_review": len(commission_per_oz) >= 5,
        "per_bar_financing_schedule_available": False,
        "raw_deal_ids_exported": False,
    }


def _number(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _read_symbol_info(info) -> dict:
    names = (
        "name", "description", "path", "currency_base", "currency_profit",
        "currency_margin", "digits", "point", "trade_contract_size",
        "trade_tick_size", "trade_tick_value", "trade_tick_value_profit",
        "trade_tick_value_loss", "volume_min", "volume_max", "volume_step",
        "trade_stops_level", "trade_freeze_level", "trade_calc_mode",
        "trade_mode", "trade_exemode", "filling_mode", "order_mode",
        "spread", "spread_float", "swap_mode", "swap_long", "swap_short",
        "swap_rollover3days",
    )
    values = {}
    for name in names:
        value = getattr(info, name, None)
        if isinstance(value, float):
            values[name] = _number(value)
        elif isinstance(value, (int, str, bool)) or value is None:
            values[name] = value
        else:
            values[name] = str(value)
    return values


def collect(mt5, symbol: str, days: int) -> dict:
    if not mt5.initialize():
        raise RuntimeError(f"MT5_INITIALIZE_FAILED:{mt5.last_error()}")
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        if terminal is None or account is None:
            raise RuntimeError(f"MT5_TERMINAL_OR_ACCOUNT_UNAVAILABLE:{mt5.last_error()}")
        if not bool(getattr(terminal, "connected", False)):
            raise RuntimeError("MT5_TERMINAL_NOT_CONNECTED")

        info = mt5.symbol_info(symbol)
        if info is None:
            alternatives = mt5.symbols_get("*XAU*") or ()
            names = sorted({getattr(item, "name", "") for item in alternatives if getattr(item, "name", "")})
            raise RuntimeError("XAUUSD_SYMBOL_NOT_FOUND; available=" + ",".join(names[:30]))

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        deals = mt5.history_deals_get(start, now)
        if deals is None:
            raise RuntimeError(f"MT5_HISTORY_DEALS_FAILED:{mt5.last_error()}")

        entry_codes = {int(mt5.DEAL_ENTRY_IN)}
        exit_codes = {int(mt5.DEAL_ENTRY_OUT), int(mt5.DEAL_ENTRY_OUT_BY)}
        costs = aggregate_closed_positions(
            deals,
            symbol=symbol,
            contract_size=float(info.trade_contract_size),
            entry_codes=entry_codes,
            exit_codes=exit_codes,
        )
        account_currency = str(account.currency)
        terminal_version = mt5.version()

        return {
            "schema": "forexai.mt5.xauusd_broker_cost_probe.v1",
            "status": "READ_ONLY_CONTRACT_SPECS_CAPTURED",
            "captured_at_utc": now.isoformat(),
            "lookback_days": int(days),
            "history_start_utc": start.isoformat(),
            "history_end_utc": now.isoformat(),
            "broker": {
                "company": str(account.company),
                "server": str(account.server),
                "account_currency": account_currency,
                "leverage": int(account.leverage),
            },
            "terminal": {
                "connected": bool(terminal.connected),
                "trade_allowed": bool(getattr(terminal, "trade_allowed", False)),
                "terminal_build": int(getattr(terminal, "build", 0) or 0),
                "python_mt5_version": list(terminal_version) if terminal_version else None,
            },
            "symbol": _read_symbol_info(info),
            "realized_cost_sample": costs | {
                "currency": account_currency,
                "values_are_usd": account_currency == "USD",
                "lookback_is_account_history_only": True,
                "account_login_exported": False,
            },
            "current_swap_terms": {
                "swap_mode": getattr(info, "swap_mode", None),
                "swap_long": _number(getattr(info, "swap_long", None)),
                "swap_short": _number(getattr(info, "swap_short", None)),
                "rollover_three_day": getattr(info, "swap_rollover3days", None),
                "these_are_current_terms_not_a_historical_schedule": True,
            },
            "limitations": [
                "No account login ID, password, raw deal ticket or position ID is exported.",
                "Historical commission/fee and swap are summarized from closed XAUUSD positions only.",
                "Current symbol swap fields do not reconstruct historical daily financing changes.",
                "Per-bar financing schedule is not available from this probe.",
                "Convert account-currency costs to USD only with a sourced FX conversion where needed.",
            ],
            "no_orders_submitted": True,
            "no_positions_modified": True,
            "no_terminal_settings_modified": True,
        }
    finally:
        mt5.shutdown()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only MT5 XAUUSD contract and realized cost probe"
    )
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--output", default="artifacts/xauusd-broker-cost-probe.json")
    args = parser.parse_args(argv)
    if args.days < 1 or args.days > 3650:
        raise SystemExit("--days must be in [1,3650]")

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit("Install the Windows MetaTrader5 package: py -m pip install MetaTrader5") from exc

    report = collect(mt5, args.symbol, args.days)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "symbol": report["symbol"]["name"],
        "account_currency": report["broker"]["account_currency"],
        "contract_size": report["symbol"]["trade_contract_size"],
        "closed_position_sample_count": report["realized_cost_sample"]["closed_position_count"],
        "cost_sample_adequate": report["realized_cost_sample"]["sample_is_adequate_for_cost_review"],
        "per_bar_financing_schedule_available": report["realized_cost_sample"]["per_bar_financing_schedule_available"],
        "no_orders_submitted": report["no_orders_submitted"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
