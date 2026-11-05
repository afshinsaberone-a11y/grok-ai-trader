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

try:
    # Package import for pytest / module execution from the repository root.
    from .mt5_xauusd_slippage_history_probe import capture_pre_order_quotes
except ImportError:
    # Direct script execution: Python places the tools/ directory on sys.path.
    from mt5_xauusd_slippage_history_probe import capture_pre_order_quotes


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


def _quote_at_fill_time(
    mt5,
    symbol: str,
    setup_ms: int,
    fill_ms: int,
    setup_quote: dict,
    executable_side: str,
    max_quote_age_ms: int,
) -> dict:
    """Cross-check the latest valid executable quote at or before the fill time.

    Only ticks strictly after order setup and at/before the last fill are queried.
    The setup quote remains the fallback when no intervening quote update exists.
    """
    if fill_ms < setup_ms:
        return {
            "quote": None,
            "query_error": False,
            "query_empty": False,
            "post_setup_tick_records_seen": 0,
            "post_setup_valid_tick_count": 0,
            "post_setup_executable_price_change_count": 0,
        }

    start_dt = datetime.fromtimestamp(setup_ms / 1000.0, timezone.utc)
    end_dt = datetime.fromtimestamp((fill_ms + 999) / 1000.0, timezone.utc)
    ticks = mt5.copy_ticks_range(
        symbol, start_dt, end_dt, mt5.COPY_TICKS_INFO
    )
    if ticks is None:
        return {
            "quote": None,
            "query_error": True,
            "query_empty": False,
            "post_setup_tick_records_seen": 0,
            "post_setup_valid_tick_count": 0,
            "post_setup_executable_price_change_count": 0,
        }

    names = getattr(getattr(ticks, "dtype", None), "names", None) or ()
    if len(ticks) and ("bid" not in names or "ask" not in names):
        raise RuntimeError("MT5_EXECUTION_TICK_FIELDS_MISSING_BID_ASK")
    if len(ticks) and "time_msc" not in names and "time" not in names:
        raise RuntimeError("MT5_EXECUTION_TICK_TIMESTAMP_FIELDS_MISSING")

    timestamp_values = ticks["time_msc"] if "time_msc" in names else (
        ticks["time"] * 1000 if "time" in names else []
    )
    best = None
    post_setup_tick_records_seen = 0
    post_setup_valid_tick_count = 0
    post_setup_price_changes = 0
    previous_side_price = float(
        setup_quote["ask"] if executable_side == "ASK" else setup_quote["bid"]
    )

    for index in range(len(ticks)):
        tick_ms = int(timestamp_values[index])
        if tick_ms <= setup_ms or tick_ms > fill_ms:
            continue
        post_setup_tick_records_seen += 1
        bid = _num(ticks["bid"][index])
        ask = _num(ticks["ask"][index])
        if (
            tick_ms <= 0 or bid is None or ask is None
            or bid <= 0 or ask < bid
        ):
            continue
        post_setup_valid_tick_count += 1
        side_price = ask if executable_side == "ASK" else bid
        if not math.isclose(
            side_price, previous_side_price, rel_tol=0.0, abs_tol=1e-12
        ):
            post_setup_price_changes += 1
        previous_side_price = side_price
        if best is None or tick_ms >= best["timestamp_ms"]:
            best = {
                "bid": bid,
                "ask": ask,
                "timestamp_ms": tick_ms,
                "age_ms": fill_ms - tick_ms,
            }

    if best is not None:
        selected = best
    elif post_setup_tick_records_seen == 0:
        selected = {
            "bid": float(setup_quote["bid"]),
            "ask": float(setup_quote["ask"]),
            "timestamp_ms": int(setup_quote["timestamp_ms"]),
            "age_ms": fill_ms - int(setup_quote["timestamp_ms"]),
        }
    else:
        # A newer tick record exists but has no usable two-sided quote.
        # Do not silently fall back to an older quote in that case.
        selected = None
    if selected["age_ms"] < 0 or selected["age_ms"] > max_quote_age_ms:
        selected = None

    return {
        "quote": selected,
        "query_error": False,
        "query_empty": len(ticks) == 0,
        "post_setup_tick_records_seen": post_setup_tick_records_seen,
        "post_setup_valid_tick_count": post_setup_valid_tick_count,
        "post_setup_executable_price_change_count": post_setup_price_changes,
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
            "orders_with_vwap_equal_to_reference_price": 0,
            "orders_with_vwap_different_from_reference_price": 0,
            "execution_quote_tick_query_errors": 0,
            "orders_missing_execution_quote_reference": 0,
            "orders_with_post_setup_quote_tick": 0,
            "orders_with_post_setup_executable_price_change": 0,
            "orders_with_vwap_equal_to_execution_quote": 0,
            "orders_with_vwap_different_from_execution_quote": 0,
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
        execution_quote_age_ms = []
        post_setup_tick_counts = []
        setup_to_execution_quote_move_points = []
        execution_quote_signed_points = []
        execution_quote_adverse_points = []
        execution_quote_exact_match_orders = 0
        execution_quote_different_orders = 0

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

            executable_side = "ASK" if order_type == int(mt5.ORDER_TYPE_BUY) else "BID"
            execution_crosscheck = _quote_at_fill_time(
                mt5,
                symbol,
                setup_ms,
                last_fill_ms,
                quote,
                executable_side,
                max_quote_age_ms,
            )
            if execution_crosscheck["query_error"]:
                counters["execution_quote_tick_query_errors"] += 1
                counters["orders_missing_execution_quote_reference"] += 1
            else:
                post_setup_count = execution_crosscheck["post_setup_valid_tick_count"]
                post_setup_tick_counts.append(float(post_setup_count))
                if post_setup_count > 0:
                    counters["orders_with_post_setup_quote_tick"] += 1
                if execution_crosscheck["post_setup_executable_price_change_count"] > 0:
                    counters["orders_with_post_setup_executable_price_change"] += 1

                execution_quote = execution_crosscheck["quote"]
                if execution_quote is None:
                    counters["orders_missing_execution_quote_reference"] += 1
                else:
                    execution_quote_age_ms.append(float(execution_quote["age_ms"]))
                    execution_reference = float(
                        execution_quote["ask"] if order_type == int(mt5.ORDER_TYPE_BUY)
                        else execution_quote["bid"]
                    )
                    execution_signed = (
                        fill_vwap - execution_reference
                        if order_type == int(mt5.ORDER_TYPE_BUY)
                        else execution_reference - fill_vwap
                    )
                    setup_side_move = (
                        execution_reference - reference
                        if order_type == int(mt5.ORDER_TYPE_BUY)
                        else reference - execution_reference
                    )
                    setup_to_execution_quote_move_points.append(
                        setup_side_move / float(info.point)
                    )
                    execution_quote_signed_points.append(
                        execution_signed / float(info.point)
                    )
                    execution_quote_adverse_points.append(
                        max(0.0, execution_signed) / float(info.point)
                    )
                    if math.isclose(
                        fill_vwap, execution_reference, rel_tol=0.0, abs_tol=1e-9
                    ):
                        execution_quote_exact_match_orders += 1
                        counters["orders_with_vwap_equal_to_execution_quote"] += 1
                    else:
                        execution_quote_different_orders += 1
                        counters["orders_with_vwap_different_from_execution_quote"] += 1

            if math.isclose(fill_vwap, reference, rel_tol=0.0, abs_tol=1e-9):
                exact_match_orders += 1
                counters["orders_with_vwap_equal_to_reference_price"] += 1
            else:
                different_match_orders += 1
                counters["orders_with_vwap_different_from_reference_price"] += 1
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
                "orders_with_vwap_exactly_equal_to_setup_reference": exact_match_orders,
                "orders_with_vwap_different_from_setup_reference": different_match_orders,
                "all_matched_vwaps_equal_setup_reference": (
                    matched > 0 and exact_match_orders == matched
                ),
                "signed_deviation_points": _stats(signed_points),
                "adverse_deviation_points": _stats(adverse_points),
            },
            "execution_quote_check": {
                "method": (
                    "latest valid executable-side quote strictly after setup and at/before last fill; "
                    "falls back to the valid setup quote only when no intervening quote update is returned"
                ),
                "orders_with_vwap_equal_to_execution_quote": execution_quote_exact_match_orders,
                "orders_with_vwap_different_from_execution_quote": execution_quote_different_orders,
                "all_matched_vwaps_equal_execution_quote": (
                    matched > 0
                    and counters["orders_missing_execution_quote_reference"] == 0
                    and execution_quote_exact_match_orders == matched
                ),
                "execution_quote_signed_deviation_points": _stats(execution_quote_signed_points),
                "execution_quote_adverse_deviation_points": _stats(execution_quote_adverse_points),
                "setup_to_execution_quote_adverse_move_points": _stats(setup_to_execution_quote_move_points),
                "execution_quote_age_at_last_fill_ms": _stats(execution_quote_age_ms),
                "post_setup_valid_quote_ticks_per_order": _stats(post_setup_tick_counts),
            },
            "interpretation": (
                "TIMESTAMP_ORDER_INCONSISTENCY"
                if matched and (
                    counters["deals_before_order_setup"] > 0
                    or counters["deals_missing_execution_timestamp"] > 0
                )
                else "EXECUTION_QUOTE_CROSSCHECK_INCOMPLETE"
                if matched and (
                    counters["execution_quote_tick_query_errors"] > 0
                    or counters["orders_missing_execution_quote_reference"] > 0
                )
                else "ZERO_DEVIATION_VS_LAST_RECORDED_EXECUTION_QUOTE"
                if matched and execution_quote_exact_match_orders == matched
                else "EXECUTION_QUOTE_CROSSCHECK_AVAILABLE"
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
        "execution_quote_check": report["execution_quote_check"],
        "no_orders_submitted": report["no_orders_submitted"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
