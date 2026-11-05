"""Read-only XAUUSD order/deal timestamp audit for quote-to-fill interpretation.

This diagnostic complements mt5_xauusd_slippage_history_probe.py. It does not
send orders. It checks whether historical Deal execution timestamps occur
before, at, or after the order setup timestamp used as the quote reference.
Only aggregate counts/statistics are exported; no tickets or raw prices.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.mt5_xauusd_slippage_history_probe import capture_pre_order_quotes


def _num(value):
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _ms(record, ms_field: str, seconds_field: str) -> int | None:
    value = getattr(record, ms_field, None)
    try:
        stamp = int(value or 0)
    except (TypeError, ValueError, OverflowError):
        stamp = 0
    if stamp > 0:
        return stamp
    value = getattr(record, seconds_field, None)
    try:
        stamp = int(value or 0)
    except (TypeError, ValueError, OverflowError):
        stamp = 0
    return stamp * 1000 if stamp > 0 else None


def _stats(values: list[float]) -> dict:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return {
            "count": 0, "min": None, "median": None,
            "p95": None, "max": None, "mean": None,
        }

    def quantile(probability: float) -> float:
        position = (len(clean) - 1) * probability
        low = math.floor(position)
        high = math.ceil(position)
        if low == high:
            return clean[low]
        weight = position - low
        return clean[low] * (1.0 - weight) + clean[high] * weight

    return {
        "count": len(clean),
        "min": round(clean[0], 3),
        "median": round(quantile(0.50), 3),
        "p95": round(quantile(0.95), 3),
        "max": round(clean[-1], 3),
        "mean": round(sum(clean) / len(clean), 3),
    }


def audit(mt5, symbol: str, days: int, max_quote_age_ms: int) -> dict:
    if not mt5.initialize():
        raise RuntimeError(f"MT5_INITIALIZE_FAILED:{mt5.last_error()}")
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        info = mt5.symbol_info(symbol)
        if terminal is None or account is None or info is None:
            raise RuntimeError(f"MT5_CONTEXT_UNAVAILABLE:{mt5.last_error()}")
        if not bool(getattr(terminal, "connected", False)):
            raise RuntimeError("MT5_TERMINAL_NOT_CONNECTED")

        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        group = f"*{symbol}*"
        orders = mt5.history_orders_get(start, end, group=group)
        if orders is None:
            raise RuntimeError(f"MT5_HISTORY_ORDERS_FAILED:{mt5.last_error()}")
        deals = mt5.history_deals_get(start, end, group=group)
        if deals is None:
            raise RuntimeError(f"MT5_HISTORY_DEALS_FAILED:{mt5.last_error()}")

        quotes = capture_pre_order_quotes(
            mt5, symbol, orders, max_quote_age_ms=max_quote_age_ms
        )
        deals_by_order = {}
        for deal in deals:
            if getattr(deal, "symbol", None) != symbol:
                continue
            ticket = int(getattr(deal, "order", 0) or 0)
            deal_type = int(getattr(deal, "type", -1))
            volume = _num(getattr(deal, "volume", None))
            price = _num(getattr(deal, "price", None))
            deal_ms = _ms(deal, "time_msc", "time")
            if ticket <= 0 or volume is None or volume <= 0 or price is None or price <= 0:
                continue
            deals_by_order.setdefault(ticket, []).append(
                (deal_type, volume, price, deal_ms)
            )

        counters = {
            "market_orders_seen": 0,
            "duplicate_order_records_ignored": 0,
            "orders_missing_setup_timestamp": 0,
            "orders_missing_quote_reference": 0,
            "orders_without_compatible_fill_deal": 0,
            "matched_orders": 0,
            "deals_missing_execution_timestamp": 0,
            "deals_before_order_setup": 0,
            "deals_at_order_setup_millisecond": 0,
            "deals_after_order_setup": 0,
            "deals_before_order_done": 0,
            "deals_at_or_after_order_done": 0,
            "fills_exactly_equal_to_reference_price": 0,
            "fills_different_from_reference_price": 0,
        }
        seen = set()
        setup_to_first_fill_ms = []
        setup_to_last_fill_ms = []
        quote_to_first_fill_ms = []
        quote_to_last_fill_ms = []
        done_to_last_fill_ms = []
        adverse_points = []
        signed_points = []
        quote_age_ms = []
        exact_match_orders = 0
        different_match_orders = 0

        for order in orders:
            if getattr(order, "symbol", None) != symbol:
                continue
            order_type = int(getattr(order, "type", -1))
            if order_type not in (int(mt5.ORDER_TYPE_BUY), int(mt5.ORDER_TYPE_SELL)):
                continue
            counters["market_orders_seen"] += 1

            ticket = int(getattr(order, "ticket", 0) or 0)
            if ticket <= 0 or ticket in seen:
                counters["duplicate_order_records_ignored"] += 1
                continue
            seen.add(ticket)

            setup_ms = _ms(order, "time_setup_msc", "time_setup")
            if setup_ms is None:
                counters["orders_missing_setup_timestamp"] += 1
                continue
            quote = quotes["quotes_by_order_ticket"].get(ticket)
            if not isinstance(quote, dict):
                counters["orders_missing_quote_reference"] += 1
                continue

            expected_type = (
                int(mt5.DEAL_TYPE_BUY)
                if order_type == int(mt5.ORDER_TYPE_BUY)
                else int(mt5.DEAL_TYPE_SELL)
            )
            compatible = [
                row for row in deals_by_order.get(ticket, [])
                if row[0] == expected_type
            ]
            if not compatible:
                counters["orders_without_compatible_fill_deal"] += 1
                continue

            valid_times = [row[3] for row in compatible if row[3] is not None]
            counters["deals_missing_execution_timestamp"] += (
                len(compatible) - len(valid_times)
            )
            if not valid_times:
                continue

            fill_volume = sum(row[1] for row in compatible)
            fill_vwap = sum(row[1] * row[2] for row in compatible) / fill_volume
            first_fill_ms = min(valid_times)
            last_fill_ms = max(valid_times)
            quote_ms = int(quote["timestamp_ms"])
            reference = float(
                quote["ask"] if order_type == int(mt5.ORDER_TYPE_BUY)
                else quote["bid"]
            )
            signed = (
                fill_vwap - reference
                if order_type == int(mt5.ORDER_TYPE_BUY)
                else reference - fill_vwap
            )

            for deal_ms in valid_times:
                if deal_ms < setup_ms:
                    counters["deals_before_order_setup"] += 1
                elif deal_ms == setup_ms:
                    counters["deals_at_order_setup_millisecond"] += 1
                else:
                    counters["deals_after_order_setup"] += 1

            done_ms = _ms(order, "time_done_msc", "time_done")
            if done_ms is not None:
                for deal_ms in valid_times:
                    if deal_ms < done_ms:
                        counters["deals_before_order_done"] += 1
                    else:
                        counters["deals_at_or_after_order_done"] += 1
                done_to_last_fill_ms.append(float(last_fill_ms - done_ms))

            setup_to_first_fill_ms.append(float(first_fill_ms - setup_ms))
            setup_to_last_fill_ms.append(float(last_fill_ms - setup_ms))
            quote_to_first_fill_ms.append(float(first_fill_ms - quote_ms))
            quote_to_last_fill_ms.append(float(last_fill_ms - quote_ms))
            quote_age_ms.append(float(quote["age_ms"]))
            signed_points.append(signed / float(info.point))
            adverse_points.append(max(0.0, signed) / float(info.point))

            if math.isclose(fill_vwap, reference, rel_tol=0.0, abs_tol=1e-9):
                exact_match_orders += 1
                counters["fills_exactly_equal_to_reference_price"] += len(compatible)
            else:
                different_match_orders += 1
                counters["fills_different_from_reference_price"] += len(compatible)
            counters["matched_orders"] += 1

        matched = counters["matched_orders"]
        return {
            "schema": "forexai.mt5.xauusd_quote_fill_timing_audit.v1",
            "status": "QUOTE_FILL_TIMING_AUDIT_CAPTURED",
            "symbol": symbol,
            "captured_at_utc": end.isoformat(),
            "lookback_days": days,
            "account_currency": str(account.currency),
            "matched_orders": matched,
            "counters": counters,
            "timing_ms": {
                "setup_to_first_fill": _stats(setup_to_first_fill_ms),
                "setup_to_last_fill": _stats(setup_to_last_fill_ms),
                "reference_quote_to_first_fill": _stats(quote_to_first_fill_ms),
                "reference_quote_to_last_fill": _stats(quote_to_last_fill_ms),
                "order_done_to_last_fill": _stats(done_to_last_fill_ms),
                "quote_age_at_order_setup": _stats(quote_age_ms),
            },
            "price_check": {
                "orders_with_vwap_exactly_equal_to_reference": exact_match_orders,
                "orders_with_vwap_different_from_reference": different_match_orders,
                "all_matched_vwaps_equal_reference": (
                    matched > 0 and exact_match_orders == matched
                ),
                "signed_deviation_points": _stats(signed_points),
                "adverse_deviation_points": _stats(adverse_points),
            },
            "interpretation": (
                "TIMESTAMP_REVIEW_REQUIRED"
                if matched and (
                    counters["deals_before_order_setup"] > 0
                    or counters["deals_missing_execution_timestamp"] > 0
                    or exact_match_orders == matched
                )
                else "TIMING_DIAGNOSTICS_AVAILABLE"
            ),
            "privacy": {
                "raw_order_tickets_exported": False,
                "raw_deal_tickets_exported": False,
                "raw_prices_exported": False,
            },
            "no_orders_submitted": True,
            "no_positions_modified": True,
            "no_terminal_settings_modified": True,
        }
    finally:
        mt5.shutdown()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only XAUUSD order/deal timestamp and quote-fill audit"
    )
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--max-quote-age-ms", type=int, default=3000)
    parser.add_argument(
        "--output",
        default="artifacts/xauusd-quote-fill-timing-audit.json",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.days <= 3650:
        raise SystemExit("--days must be in [1,3650]")
    if not 1 <= args.max_quote_age_ms <= 60_000:
        raise SystemExit("--max-quote-age-ms must be in [1,60000]")

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit(
            "Install the Windows MetaTrader5 package: py -3 -m pip install MetaTrader5"
        ) from exc

    report = audit(
        mt5, args.symbol, args.days, args.max_quote_age_ms
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "symbol": report["symbol"],
        "matched_orders": report["matched_orders"],
        "interpretation": report["interpretation"],
        "counters": report["counters"],
        "timing_ms": report["timing_ms"],
        "price_check": report["price_check"],
        "no_orders_submitted": report["no_orders_submitted"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
