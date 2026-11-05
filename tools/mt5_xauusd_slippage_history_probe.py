"""Read-only MT5 requested-price versus executed-fill slippage audit for XAUUSD.

Uses historical market orders and their associated deal fills only. Orders with
no valid positive specified price are excluded rather than assigned zero
slippage. No order is submitted, modified, checked, or closed.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _number(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _quantile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _stats(values: list[float]) -> dict:
    if not values:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "p95": None,
            "p99": None,
            "min": None,
            "max": None,
        }
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "mean": round(sum(ordered) / len(ordered), 10),
        "median": round(_quantile(ordered, 0.50), 10),
        "p95": round(_quantile(ordered, 0.95), 10),
        "p99": round(_quantile(ordered, 0.99), 10),
        "min": round(ordered[0], 10),
        "max": round(ordered[-1], 10),
    }


def aggregate_requested_to_fill_slippage(
    orders,
    deals,
    *,
    symbol: str,
    point: float,
    tick_size: float,
    tick_value: float,
    buy_order_type: int,
    sell_order_type: int,
    buy_deal_type: int,
    sell_deal_type: int,
) -> dict:
    """Aggregate signed adverse price deviation by filled market order.

    BUY adverse deviation = volume-weighted deal fill price - specified order price.
    SELL adverse deviation = specified order price - volume-weighted deal fill price.
    Positive values are adverse; negative values are favorable price improvement.
    """
    for name, value, allow_zero in (
        ("POINT", point, False),
        ("TICK_SIZE", tick_size, False),
        ("TICK_VALUE", tick_value, True),
    ):
        number = _number(value)
        if number is None or (number < 0 if allow_zero else number <= 0):
            raise ValueError(f"XAUUSD_{name}_INVALID")
    if buy_order_type == sell_order_type or buy_deal_type == sell_deal_type:
        raise ValueError("XAUUSD_ORDER_OR_DEAL_SIDE_CODES_INVALID")

    fills_by_order = {}
    for deal in deals or ():
        if getattr(deal, "symbol", None) != symbol:
            continue
        order_ticket = int(getattr(deal, "order", 0) or 0)
        deal_type = int(getattr(deal, "type", -1))
        volume = _number(getattr(deal, "volume", None))
        price = _number(getattr(deal, "price", None))
        if order_ticket <= 0 or volume is None or volume <= 0 or price is None or price <= 0:
            continue
        fills_by_order.setdefault(order_ticket, []).append(
            (deal_type, volume, price)
        )

    seen_tickets = set()
    matched_rows = []
    counters = {
        "market_orders_seen": 0,
        "missing_or_invalid_specified_price_orders": 0,
        "orders_without_matching_fill_deals": 0,
        "duplicate_order_records_ignored": 0,
        "fill_deals_with_side_mismatch_ignored": 0,
        "matched_filled_orders": 0,
        "multi_deal_fill_orders": 0,
        "partial_fill_orders": 0,
    }

    for order in orders or ():
        if getattr(order, "symbol", None) != symbol:
            continue
        order_type = int(getattr(order, "type", -1))
        if order_type not in (buy_order_type, sell_order_type):
            continue
        counters["market_orders_seen"] += 1

        ticket = int(getattr(order, "ticket", 0) or 0)
        if ticket <= 0:
            counters["orders_without_matching_fill_deals"] += 1
            continue
        if ticket in seen_tickets:
            counters["duplicate_order_records_ignored"] += 1
            continue
        seen_tickets.add(ticket)

        requested = _number(getattr(order, "price_open", None))
        if requested is None or requested <= 0:
            counters["missing_or_invalid_specified_price_orders"] += 1
            continue

        candidates = fills_by_order.get(ticket, [])
        expected_deal_type = buy_deal_type if order_type == buy_order_type else sell_deal_type
        compatible = []
        for deal_type, volume, price in candidates:
            if deal_type != expected_deal_type:
                counters["fill_deals_with_side_mismatch_ignored"] += 1
                continue
            compatible.append((volume, price))
        if not compatible:
            counters["orders_without_matching_fill_deals"] += 1
            continue

        filled_volume = sum(volume for volume, _ in compatible)
        if not math.isfinite(filled_volume) or filled_volume <= 0:
            counters["orders_without_matching_fill_deals"] += 1
            continue
        fill_price = sum(volume * price for volume, price in compatible) / filled_volume
        signed_deviation = (
            fill_price - requested
            if order_type == buy_order_type
            else requested - fill_price
        )
        initial_volume = _number(getattr(order, "volume_initial", None))
        if initial_volume is not None and initial_volume > 0:
            if filled_volume + max(1e-8, initial_volume * 1e-6) < initial_volume:
                counters["partial_fill_orders"] += 1
        if len(compatible) > 1:
            counters["multi_deal_fill_orders"] += 1

        matched_rows.append({
            "side": "BUY" if order_type == buy_order_type else "SELL",
            "signed_deviation": signed_deviation,
            "adverse_deviation": max(0.0, signed_deviation),
            "favorable_improvement": max(0.0, -signed_deviation),
            "filled_volume": filled_volume,
        })
        counters["matched_filled_orders"] += 1

    by_side = {}
    for side in ("BUY", "SELL"):
        rows = [row for row in matched_rows if row["side"] == side]
        signed = [row["signed_deviation"] for row in rows]
        adverse = [row["adverse_deviation"] for row in rows]
        favorable = [row["favorable_improvement"] for row in rows]
        points = [value / point for value in signed]
        adverse_points = [value / point for value in adverse]
        adverse_cost_per_lot = [
            (value / tick_size) * tick_value for value in adverse
        ]
        total_volume = sum(row["filled_volume"] for row in rows)
        volume_weighted_signed = (
            sum(row["signed_deviation"] * row["filled_volume"] for row in rows) / total_volume
            if total_volume else None
        )
        volume_weighted_adverse = (
            sum(row["adverse_deviation"] * row["filled_volume"] for row in rows) / total_volume
            if total_volume else None
        )
        by_side[side] = {
            "matched_order_count": len(rows),
            "filled_volume_lots": round(total_volume, 8),
            "signed_deviation_usd_per_oz": _stats(signed),
            "signed_deviation_points": _stats(points),
            "adverse_slippage_usd_per_oz": _stats(adverse),
            "adverse_slippage_points": _stats(adverse_points),
            "favorable_price_improvement_usd_per_oz": _stats(favorable),
            "adverse_slippage_cost_per_standard_lot_account_currency": _stats(adverse_cost_per_lot),
            "volume_weighted_signed_deviation_usd_per_oz": (
                round(volume_weighted_signed, 10) if volume_weighted_signed is not None else None
            ),
            "volume_weighted_adverse_slippage_usd_per_oz": (
                round(volume_weighted_adverse, 10) if volume_weighted_adverse is not None else None
            ),
            "volume_weighted_adverse_slippage_cost_per_standard_lot_account_currency": (
                round((volume_weighted_adverse / tick_size) * tick_value, 10)
                if volume_weighted_adverse is not None else None
            ),
        }

    return {
        "matched_filled_order_count": counters["matched_filled_orders"],
        "market_order_count": counters["market_orders_seen"],
        "sample_is_adequate_for_review": counters["matched_filled_orders"] >= 10,
        "method": "volume_weighted historical deal fill price compared with the specified historical order price",
        "positive_signed_deviation_means": "adverse_slippage",
        "negative_signed_deviation_means": "favorable_price_improvement",
        "counters": counters,
        "by_order_side": by_side,
        "raw_order_tickets_exported": False,
        "raw_deal_tickets_exported": False,
    }


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
            raise RuntimeError(f"XAUUSD_SYMBOL_NOT_FOUND:{symbol}")

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        group = f"*{symbol}*"
        orders = mt5.history_orders_get(start, now, group=group)
        if orders is None:
            raise RuntimeError(f"MT5_HISTORY_ORDERS_FAILED:{mt5.last_error()}")
        deals = mt5.history_deals_get(start, now, group=group)
        if deals is None:
            raise RuntimeError(f"MT5_HISTORY_DEALS_FAILED:{mt5.last_error()}")

        summary = aggregate_requested_to_fill_slippage(
            orders,
            deals,
            symbol=symbol,
            point=float(info.point),
            tick_size=float(info.trade_tick_size),
            tick_value=float(info.trade_tick_value),
            buy_order_type=int(mt5.ORDER_TYPE_BUY),
            sell_order_type=int(mt5.ORDER_TYPE_SELL),
            buy_deal_type=int(mt5.DEAL_TYPE_BUY),
            sell_deal_type=int(mt5.DEAL_TYPE_SELL),
        )
        matched = summary["matched_filled_order_count"]
        return {
            "schema": "forexai.mt5.xauusd_requested_to_fill_slippage_probe.v1",
            "status": (
                "REQUESTED_TO_FILL_SLIPPAGE_CAPTURED"
                if matched else "NO_USABLE_REQUESTED_PRICE_FILL_PAIRS"
            ),
            "symbol": str(info.name),
            "captured_at_utc": now.isoformat(),
            "lookback_days": int(days),
            "history_start_utc": start.isoformat(),
            "history_end_utc": now.isoformat(),
            "account_currency": str(account.currency),
            "symbol_units": {
                "digits": int(info.digits),
                "point": float(info.point),
                "tick_size": float(info.trade_tick_size),
                "tick_value_account_currency_per_tick_per_lot": float(info.trade_tick_value),
                "contract_size": float(info.trade_contract_size),
            },
            "slippage_sample": summary,
            "limitations": [
                "This is specified-order-price to executed-deal-price deviation, not an arrival-time mid-price benchmark.",
                "Orders without a positive specified order price are excluded; zero is never used as a missing-price substitute.",
                "This measure may include price movement between request construction and execution and is not a pure latency or market-impact decomposition.",
                "Partial fills are consolidated by order using deal-volume-weighted execution prices.",
                "Results are account-history evidence for the connected terminal and lookback only; they are not a historical 2021-2024 slippage schedule.",
                "Costs are converted with current symbol tick-size/value metadata; historical metadata changes are not reconstructed.",
            ],
            "no_orders_submitted": True,
            "no_positions_modified": True,
            "no_terminal_settings_modified": True,
        }
    finally:
        mt5.shutdown()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only MT5 XAUUSD requested-price-to-fill slippage audit"
    )
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument(
        "--output",
        default="artifacts/xauusd-slippage-history-probe.json",
    )
    args = parser.parse_args(argv)
    if args.days < 1 or args.days > 3650:
        raise SystemExit("--days must be in [1,3650]")
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit(
            "Install the Windows MetaTrader5 package: py -3 -m pip install MetaTrader5"
        ) from exc

    report = collect(mt5, args.symbol, args.days)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "symbol": report["symbol"],
        "lookback_days": report["lookback_days"],
        "matched_filled_order_count": report["slippage_sample"]["matched_filled_order_count"],
        "sample_is_adequate_for_review": report["slippage_sample"]["sample_is_adequate_for_review"],
        "no_orders_submitted": report["no_orders_submitted"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
