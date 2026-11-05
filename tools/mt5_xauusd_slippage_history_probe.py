"""Read-only MT5 pre-order quote versus executed-fill audit for XAUUSD.

Market Execution requests do not require a request price. For each historical
market order, this probe therefore uses the latest valid two-sided quote at or
before the server order-setup timestamp, subject to a strict maximum quote age.
The metric is quote-to-fill price deterioration, not pure broker slippage or
an arrival-time benchmark. No trade operation is performed.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path


MIN_REVIEW_ORDERS = 30
MIN_REVIEW_ORDERS_PER_SIDE = 10


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


def order_setup_time_ms(order) -> int | None:
    value = getattr(order, "time_setup_msc", None)
    try:
        stamp = int(value or 0)
    except (TypeError, ValueError, OverflowError):
        stamp = 0
    if stamp > 0:
        return stamp
    seconds = getattr(order, "time_setup", None)
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError, OverflowError):
        seconds = 0
    return seconds * 1000 if seconds > 0 else None


def capture_pre_order_quotes(mt5, symbol: str, orders, *, max_quote_age_ms: int) -> dict:
    """Map order tickets to latest valid BID/ASK at or before order setup time."""
    if type(max_quote_age_ms) is not int or max_quote_age_ms < 1 or max_quote_age_ms > 60_000:
        raise ValueError("XAUUSD_MAX_QUOTE_AGE_INVALID")

    references = {}
    unique_orders = {}
    for order in orders or ():
        if getattr(order, "symbol", None) != symbol:
            continue
        ticket = int(getattr(order, "ticket", 0) or 0)
        if ticket > 0:
            unique_orders.setdefault(ticket, order)

    counters = {
        "market_orders_considered_for_quote_reference": 0,
        "orders_missing_setup_timestamp": 0,
        "tick_history_query_errors": 0,
        "orders_without_valid_quote_within_age": 0,
        "orders_with_valid_pre_order_quote": 0,
    }
    errors = []

    for ticket, order in unique_orders.items():
        setup_ms = order_setup_time_ms(order)
        if setup_ms is None:
            counters["orders_missing_setup_timestamp"] += 1
            continue
        counters["market_orders_considered_for_quote_reference"] += 1

        # Query the setup second and adjacent second because MT5's Python
        # datetime interface is second-oriented on some builds. Strictly
        # filter returned time_msc values below, using the exact millisecond.
        window_start_ms = max(1, setup_ms - max_quote_age_ms)
        start_dt = datetime.fromtimestamp(window_start_ms / 1000, timezone.utc)
        end_dt = datetime.fromtimestamp((setup_ms + 999) / 1000, timezone.utc)
        ticks = mt5.copy_ticks_range(
            symbol,
            start_dt,
            end_dt,
            mt5.COPY_TICKS_INFO,
        )
        if ticks is None:
            counters["tick_history_query_errors"] += 1
            errors.append({
                "order_setup_utc": datetime.fromtimestamp(
                    setup_ms / 1000, timezone.utc
                ).isoformat(),
                "error": str(mt5.last_error()),
            })
            continue
        if len(ticks) == 0:
            counters["orders_without_valid_quote_within_age"] += 1
            continue

        names = getattr(getattr(ticks, "dtype", None), "names", None) or ()
        if "bid" not in names or "ask" not in names:
            raise RuntimeError("MT5_TICK_FIELDS_MISSING_BID_ASK")
        if "time_msc" in names:
            timestamps = ticks["time_msc"]
        elif "time" in names:
            timestamps = ticks["time"] * 1000
        else:
            raise RuntimeError("MT5_TICK_TIMESTAMP_FIELDS_MISSING")

        best = None
        for index in range(len(ticks)):
            timestamp_ms = int(timestamps[index])
            bid = _number(ticks["bid"][index])
            ask = _number(ticks["ask"][index])
            if (
                timestamp_ms <= 0
                or timestamp_ms > setup_ms
                or setup_ms - timestamp_ms > max_quote_age_ms
                or bid is None
                or ask is None
                or bid <= 0
                or ask < bid
            ):
                continue
            if best is None or timestamp_ms >= best["timestamp_ms"]:
                best = {
                    "bid": bid,
                    "ask": ask,
                    "timestamp_ms": timestamp_ms,
                    "age_ms": setup_ms - timestamp_ms,
                }

        if best is None:
            counters["orders_without_valid_quote_within_age"] += 1
            continue
        references[ticket] = best
        counters["orders_with_valid_pre_order_quote"] += 1

    return {
        "quotes_by_order_ticket": references,
        "counters": counters,
        "query_errors": errors,
        "max_quote_age_ms": max_quote_age_ms,
    }


def aggregate_quote_to_fill_slippage(
    orders,
    deals,
    reference_quotes: dict,
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
    """Compare fill VWAP to pre-order executable side (ASK for BUY, BID for SELL).

    BUY adverse deviation = fill VWAP - pre-order ASK.
    SELL adverse deviation = pre-order BID - fill VWAP.
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
        fills_by_order.setdefault(order_ticket, []).append((deal_type, volume, price))

    seen_tickets = set()
    matched_rows = []
    counters = {
        "market_orders_seen": 0,
        "orders_missing_valid_pre_order_quote": 0,
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
            counters["orders_missing_valid_pre_order_quote"] += 1
            continue
        if ticket in seen_tickets:
            counters["duplicate_order_records_ignored"] += 1
            continue
        seen_tickets.add(ticket)

        reference = reference_quotes.get(ticket)
        if not isinstance(reference, dict):
            counters["orders_missing_valid_pre_order_quote"] += 1
            continue
        bid = _number(reference.get("bid"))
        ask = _number(reference.get("ask"))
        quote_age_ms = _number(reference.get("age_ms"))
        if (
            bid is None or ask is None or bid <= 0 or ask < bid
            or quote_age_ms is None or quote_age_ms < 0
        ):
            counters["orders_missing_valid_pre_order_quote"] += 1
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
        reference_price = ask if order_type == buy_order_type else bid
        signed_deviation = (
            fill_price - reference_price
            if order_type == buy_order_type
            else reference_price - fill_price
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
            "quote_age_ms": quote_age_ms,
            "reference_spread": ask - bid,
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
        adverse_cost_per_lot = [(value / tick_size) * tick_value for value in adverse]
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
            "signed_quote_to_fill_deviation_usd_per_oz": _stats(signed),
            "signed_quote_to_fill_deviation_points": _stats(points),
            "adverse_quote_to_fill_deviation_usd_per_oz": _stats(adverse),
            "adverse_quote_to_fill_deviation_points": _stats(adverse_points),
            "favorable_price_improvement_usd_per_oz": _stats(favorable),
            "quote_age_at_order_setup_ms": _stats([row["quote_age_ms"] for row in rows]),
            "reference_spread_usd_per_oz": _stats([row["reference_spread"] for row in rows]),
            "adverse_quote_to_fill_cost_per_standard_lot_account_currency": _stats(adverse_cost_per_lot),
            "volume_weighted_signed_quote_to_fill_deviation_usd_per_oz": (
                round(volume_weighted_signed, 10) if volume_weighted_signed is not None else None
            ),
            "volume_weighted_adverse_quote_to_fill_deviation_usd_per_oz": (
                round(volume_weighted_adverse, 10) if volume_weighted_adverse is not None else None
            ),
            "volume_weighted_adverse_quote_to_fill_cost_per_standard_lot_account_currency": (
                round((volume_weighted_adverse / tick_size) * tick_value, 10)
                if volume_weighted_adverse is not None else None
            ),
        }

    by_counts = {side: by_side[side]["matched_order_count"] for side in ("BUY", "SELL")}
    matched = counters["matched_filled_orders"]
    return {
        "matched_filled_order_count": matched,
        "market_order_count": counters["market_orders_seen"],
        "minimum_orders_for_review": MIN_REVIEW_ORDERS,
        "minimum_orders_per_side_for_review": MIN_REVIEW_ORDERS_PER_SIDE,
        "sample_is_adequate_for_review": (
            matched >= MIN_REVIEW_ORDERS
            and all(by_counts[side] >= MIN_REVIEW_ORDERS_PER_SIDE for side in ("BUY", "SELL"))
        ),
        "method": "volume-weighted fill price versus latest valid pre-setup executable quote (ASK for BUY, BID for SELL)",
        "positive_signed_deviation_means": "adverse_quote_to_fill_price_movement",
        "negative_signed_deviation_means": "favorable_price_improvement",
        "counters": counters,
        "by_order_side": by_side,
        "raw_order_tickets_exported": False,
        "raw_deal_tickets_exported": False,
    }


def collect(mt5, symbol: str, days: int, *, max_quote_age_ms: int) -> dict:
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

        quote_capture = capture_pre_order_quotes(
            mt5, symbol, orders, max_quote_age_ms=max_quote_age_ms
        )
        summary = aggregate_quote_to_fill_slippage(
            orders,
            deals,
            quote_capture["quotes_by_order_ticket"],
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
        adequate = summary["sample_is_adequate_for_review"]
        return {
            "schema": "forexai.mt5.xauusd_pre_order_quote_to_fill_probe.v1",
            "status": (
                "PRE_ORDER_QUOTE_TO_FILL_CAPTURED"
                if matched else "NO_USABLE_PRE_ORDER_QUOTE_FILL_PAIRS"
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
            "pre_order_quote_capture": {
                "reference": "latest valid two-sided quote at or before server order-setup timestamp",
                "executable_side": {"BUY": "ASK", "SELL": "BID"},
                "max_quote_age_ms": quote_capture["max_quote_age_ms"],
                "counters": quote_capture["counters"],
                "query_error_count": len(quote_capture["query_errors"]),
                "query_errors": quote_capture["query_errors"],
            },
            "slippage_sample": summary,
            "limitations": [
                "This measures movement from the latest observable executable-side quote at or before server order setup to the volume-weighted fill; it is not a pure broker slippage, client-arrival benchmark, latency decomposition, or market-impact estimate.",
                "Market Execution orders need not carry a request price. Missing historical order price_open is therefore not treated as zero and is not required for this quote-based method.",
                "Only quotes no older than max_quote_age_ms and timestamped at or before order setup are used; orders without such a quote are excluded.",
                "The broker may not retain complete tick history for every order timestamp. Query errors and missing references are reported; no prices are synthesized.",
                "Partial fills are consolidated by order using deal-volume-weighted execution prices.",
                "Results are connected-account history evidence for the lookback only, not a historical 2021–2024 slippage schedule.",
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
        description="Read-only MT5 XAUUSD pre-order quote-to-fill slippage audit"
    )
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--max-quote-age-ms", type=int, default=3000)
    parser.add_argument(
        "--output",
        default="artifacts/xauusd-pre-order-quote-to-fill-probe.json",
    )
    args = parser.parse_args(argv)
    if args.days < 1 or args.days > 3650:
        raise SystemExit("--days must be in [1,3650]")
    if args.max_quote_age_ms < 1 or args.max_quote_age_ms > 60_000:
        raise SystemExit("--max-quote-age-ms must be in [1,60000]")
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit(
            "Install the Windows MetaTrader5 package: py -3 -m pip install MetaTrader5"
        ) from exc

    report = collect(
        mt5,
        args.symbol,
        args.days,
        max_quote_age_ms=args.max_quote_age_ms,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "symbol": report["symbol"],
        "lookback_days": report["lookback_days"],
        "matched_filled_order_count": report["slippage_sample"]["matched_filled_order_count"],
        "buy_matched": report["slippage_sample"]["by_order_side"]["BUY"]["matched_order_count"],
        "sell_matched": report["slippage_sample"]["by_order_side"]["SELL"]["matched_order_count"],
        "sample_is_adequate_for_review": report["slippage_sample"]["sample_is_adequate_for_review"],
        "quote_reference_query_errors": report["pre_order_quote_capture"]["query_error_count"],
        "no_orders_submitted": report["no_orders_submitted"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
