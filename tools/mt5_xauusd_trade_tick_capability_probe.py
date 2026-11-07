"""Read-only MT5 XAUUSD tick capability audit.

Requests COPY_TICKS_ALL and aggregates broker-supplied tick flags. It distinguishes
actual BUY/SELL trade flags from BID/ASK quote updates; it never infers aggressor
side from price direction and never exports individual ticks or account identifiers.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SEGMENT_DAYS = 7


def _array(ticks, name: str, default=None):
    names = getattr(getattr(ticks, "dtype", None), "names", None) or ()
    if name not in names:
        if default is not None:
            return default
        raise RuntimeError(f"MT5_TICK_FIELD_MISSING:{name}")
    return ticks[name]


def summarize_tick_capabilities(
    ticks,
    *,
    start_ms: int,
    end_ms: int,
    flag_bid: int = 2,
    flag_ask: int = 4,
    flag_last: int = 8,
    flag_volume: int = 16,
    flag_buy: int = 32,
    flag_sell: int = 64,
) -> dict[str, Any]:
    """Summarize one COPY_TICKS_ALL segment without retaining raw tick records."""
    import numpy as np

    if ticks is None or len(ticks) == 0:
        return {
            "ticks_returned": 0,
            "ticks_in_segment": 0,
            "ticks_outside_segment_filtered": 0,
            "valid_two_sided_quote_ticks": 0,
            "crossed_or_empty_quote_ticks": 0,
            "bid_update_ticks": 0,
            "ask_update_ticks": 0,
            "both_quote_update_ticks": 0,
            "last_update_ticks": 0,
            "volume_update_ticks": 0,
            "buy_side_flag_ticks": 0,
            "sell_side_flag_ticks": 0,
            "ambiguous_buy_and_sell_flag_ticks": 0,
            "side_flags_without_last_or_volume_update": 0,
            "buy_volume_update_ticks": 0,
            "sell_volume_update_ticks": 0,
            "buy_volume_real_sum": 0.0,
            "sell_volume_real_sum": 0.0,
            "buy_volume_real_positive_ticks": 0,
            "sell_volume_real_positive_ticks": 0,
            "timestamps_monotonic_non_decreasing": True,
            "first_tick_utc": None,
            "last_tick_utc": None,
        }

    timestamps = np.asarray(_array(ticks, "time_msc"), dtype="int64")
    flags = np.asarray(_array(ticks, "flags"), dtype="uint64")
    if len(timestamps) != len(flags):
        raise RuntimeError("MT5_TICK_TIMESTAMP_FLAG_LENGTH_MISMATCH")

    in_range = (
        (timestamps > 0)
        & (timestamps >= int(start_ms))
        & (timestamps < int(end_ms))
    )
    ts = timestamps[in_range]
    f = flags[in_range]
    bid = np.asarray(_array(ticks, "bid", np.zeros(len(ticks))), dtype="float64")[in_range]
    ask = np.asarray(_array(ticks, "ask", np.zeros(len(ticks))), dtype="float64")[in_range]

    bid_changed = (f & int(flag_bid)) != 0
    ask_changed = (f & int(flag_ask)) != 0
    last_changed = (f & int(flag_last)) != 0
    volume_changed = (f & int(flag_volume)) != 0
    buy_flag = (f & int(flag_buy)) != 0
    sell_flag = (f & int(flag_sell)) != 0
    both_sides = buy_flag & sell_flag
    buy_only = buy_flag & ~sell_flag
    sell_only = sell_flag & ~buy_flag
    trade_field_changed = last_changed | volume_changed
    buy_volume_update = buy_only & volume_changed
    sell_volume_update = sell_only & volume_changed

    volume_real_name = "volume_real"
    volume_name = "volume"
    names = getattr(getattr(ticks, "dtype", None), "names", None) or ()
    if volume_real_name in names:
        volumes = np.asarray(ticks[volume_real_name], dtype="float64")[in_range]
        volume_basis = "volume_real"
    elif volume_name in names:
        volumes = np.asarray(ticks[volume_name], dtype="float64")[in_range]
        volume_basis = "volume"
    else:
        volumes = np.zeros(len(ts), dtype="float64")
        volume_basis = "unavailable"

    finite_positive_volume = np.isfinite(volumes) & (volumes > 0)
    buy_volume_valid = buy_volume_update & finite_positive_volume
    sell_volume_valid = sell_volume_update & finite_positive_volume

    valid_quote = (
        np.isfinite(bid)
        & np.isfinite(ask)
        & (bid > 0)
        & (ask > 0)
        & (ask >= bid)
    )
    empty_or_crossed = (
        (~np.isfinite(bid))
        | (~np.isfinite(ask))
        | (bid <= 0)
        | (ask <= 0)
        | (ask < bid)
    )

    def vol_sum(mask) -> float:
        return round(float(np.sum(volumes[mask], dtype="float64")), 10)

    first_ms = int(ts.min()) if len(ts) else None
    last_ms = int(ts.max()) if len(ts) else None

    def iso(ms):
        return datetime.fromtimestamp(ms / 1000.0, timezone.utc).isoformat() if ms else None

    return {
        "ticks_returned": int(len(ticks)),
        "ticks_in_segment": int(len(ts)),
        "ticks_outside_segment_filtered": int(len(ticks) - len(ts)),
        "valid_two_sided_quote_ticks": int(valid_quote.sum()),
        "crossed_or_empty_quote_ticks": int(empty_or_crossed.sum()),
        "bid_update_ticks": int(bid_changed.sum()),
        "ask_update_ticks": int(ask_changed.sum()),
        "both_quote_update_ticks": int((bid_changed & ask_changed).sum()),
        "last_update_ticks": int(last_changed.sum()),
        "volume_update_ticks": int(volume_changed.sum()),
        "buy_side_flag_ticks": int(buy_only.sum()),
        "sell_side_flag_ticks": int(sell_only.sum()),
        "ambiguous_buy_and_sell_flag_ticks": int(both_sides.sum()),
        "side_flags_without_last_or_volume_update": int((buy_flag | sell_flag)[~trade_field_changed].sum()),
        "buy_volume_update_ticks": int(buy_volume_update.sum()),
        "sell_volume_update_ticks": int(sell_volume_update.sum()),
        "buy_volume_real_sum": vol_sum(buy_volume_valid),
        "sell_volume_real_sum": vol_sum(sell_volume_valid),
        "buy_volume_real_positive_ticks": int(buy_volume_valid.sum()),
        "sell_volume_real_positive_ticks": int(sell_volume_valid.sum()),
        "volume_basis": volume_basis,
        "timestamps_monotonic_non_decreasing": bool(
            len(ts) < 2 or np.all(ts[1:] >= ts[:-1])
        ),
        "first_tick_utc": iso(first_ms),
        "last_tick_utc": iso(last_ms),
    }



def summarize_market_book_snapshot(
    entries,
    *,
    sell_type: int = 1,
    buy_type: int = 2,
    sell_market_type: int = 3,
    buy_market_type: int = 4,
) -> dict[str, Any]:
    """Aggregate one MT5 DOM snapshot; never retain or export individual levels."""
    result = {
        "snapshot_returned": entries is not None,
        "levels_returned": 0 if entries is None else len(entries),
        "buy_limit_levels": 0,
        "sell_limit_levels": 0,
        "buy_market_levels": 0,
        "sell_market_levels": 0,
        "unknown_type_levels": 0,
        "invalid_price_or_volume_levels": 0,
        "buy_limit_volume": 0.0,
        "sell_limit_volume": 0.0,
        "buy_market_volume": 0.0,
        "sell_market_volume": 0.0,
        "best_bid_price": None,
        "best_ask_price": None,
        "displayed_limit_depth_imbalance": None,
    }
    if entries is None or len(entries) == 0:
        return result

    volumes_by_type = {
        "buy_limit": [],
        "sell_limit": [],
        "buy_market": [],
        "sell_market": [],
    }
    prices_by_type = {"buy_limit": [], "sell_limit": []}
    type_map = {
        int(buy_type): "buy_limit",
        int(sell_type): "sell_limit",
        int(buy_market_type): "buy_market",
        int(sell_market_type): "sell_market",
    }
    if len(type_map) != 4:
        raise ValueError("MT5_BOOK_TYPE_CODES_NOT_DISTINCT")

    for entry in entries:
        if hasattr(entry, "_asdict"):
            row = entry._asdict()
        elif isinstance(entry, dict):
            row = entry
        else:
            row = {
                "type": getattr(entry, "type", None),
                "price": getattr(entry, "price", None),
                "volume_dbl": getattr(entry, "volume_dbl", None),
                "volume": getattr(entry, "volume", None),
            }
        try:
            entry_type = int(row["type"])
        except (KeyError, TypeError, ValueError, OverflowError):
            result["unknown_type_levels"] += 1
            continue
        category = type_map.get(entry_type)
        if category is None:
            result["unknown_type_levels"] += 1
            continue
        try:
            price = float(row.get("price"))
            raw_volume = row.get("volume_dbl")
            if raw_volume is None:
                raw_volume = row.get("volume")
            volume = float(raw_volume)
        except (TypeError, ValueError, OverflowError):
            result["invalid_price_or_volume_levels"] += 1
            continue
        if (
            not math.isfinite(price)
            or price <= 0
            or not math.isfinite(volume)
            or volume <= 0
        ):
            result["invalid_price_or_volume_levels"] += 1
            continue

        result[category + "_levels"] += 1
        volumes_by_type[category].append(volume)
        if category in prices_by_type:
            prices_by_type[category].append(price)

    for category, values in volumes_by_type.items():
        result[category + "_volume"] = round(sum(values), 10)
    if prices_by_type["buy_limit"]:
        result["best_bid_price"] = max(prices_by_type["buy_limit"])
    if prices_by_type["sell_limit"]:
        result["best_ask_price"] = min(prices_by_type["sell_limit"])

    buy_volume = result["buy_limit_volume"]
    sell_volume = result["sell_limit_volume"]
    total_limit_volume = buy_volume + sell_volume
    if total_limit_volume > 0:
        result["displayed_limit_depth_imbalance"] = round(
            (buy_volume - sell_volume) / total_limit_volume,
            8,
        )
    return result


def collect_market_depth(
    mt5,
    symbol: str,
    *,
    sample_count: int = 8,
    interval_seconds: float = 0.5,
) -> dict[str, Any]:
    """Collect a short live DOM capability sample and export aggregate metrics only."""
    if sample_count < 1 or sample_count > 30:
        raise ValueError("DOM_SAMPLE_COUNT_MUST_BE_IN_1_TO_30")
    if not math.isfinite(interval_seconds) or interval_seconds < 0 or interval_seconds > 5:
        raise ValueError("DOM_INTERVAL_SECONDS_INVALID")

    add = getattr(mt5, "market_book_add", None)
    get = getattr(mt5, "market_book_get", None)
    release = getattr(mt5, "market_book_release", None)
    if not callable(add) or not callable(get) or not callable(release):
        return {
            "status": "DOM_API_UNAVAILABLE",
            "subscription_succeeded": False,
            "market_book_release_succeeded": None,
            "samples_requested": sample_count,
            "nonempty_snapshots": 0,
            "empty_snapshots": 0,
            "snapshot_errors": 0,
        }

    book_types = {
        "sell_limit": int(getattr(mt5, "BOOK_TYPE_SELL", 1)),
        "buy_limit": int(getattr(mt5, "BOOK_TYPE_BUY", 2)),
        "sell_market": int(getattr(mt5, "BOOK_TYPE_SELL_MARKET", 3)),
        "buy_market": int(getattr(mt5, "BOOK_TYPE_BUY_MARKET", 4)),
    }
    if len(set(book_types.values())) != 4:
        return {
            "status": "DOM_BOOK_TYPE_CONSTANTS_INVALID",
            "subscription_succeeded": False,
            "market_book_release_succeeded": None,
            "samples_requested": sample_count,
            "book_type_values": book_types,
            "nonempty_snapshots": 0,
            "empty_snapshots": 0,
            "snapshot_errors": 0,
        }

    subscribed = bool(add(symbol))
    if not subscribed:
        return {
            "status": "DOM_SUBSCRIPTION_UNAVAILABLE",
            "subscription_succeeded": False,
            "subscription_error": str(getattr(mt5, "last_error", lambda: None)()),
            "market_book_release_succeeded": None,
            "samples_requested": sample_count,
            "book_type_values": book_types,
            "nonempty_snapshots": 0,
            "empty_snapshots": 0,
            "snapshot_errors": 0,
        }

    snapshots = []
    snapshot_errors = 0
    release_ok = None
    try:
        for index in range(sample_count):
            entries = get(symbol)
            if entries is None:
                snapshot_errors += 1
            else:
                snapshot = summarize_market_book_snapshot(
                    entries,
                    sell_type=book_types["sell_limit"],
                    buy_type=book_types["buy_limit"],
                    sell_market_type=book_types["sell_market"],
                    buy_market_type=book_types["buy_market"],
                )
                snapshots.append(snapshot)
            if index + 1 < sample_count and interval_seconds:
                time.sleep(interval_seconds)
    finally:
        try:
            release_ok = bool(release(symbol))
        except Exception:
            release_ok = False

    nonempty = [row for row in snapshots if row["levels_returned"] > 0]
    empty = len(snapshots) - len(nonempty)

    def average(key: str) -> float | None:
        values = [float(row[key]) for row in nonempty]
        return round(sum(values) / len(values), 10) if values else None

    imbalance_values = [
        float(row["displayed_limit_depth_imbalance"])
        for row in nonempty
        if row["displayed_limit_depth_imbalance"] is not None
    ]
    result = {
        "status": (
            "DOM_LEVELS_CAPTURED"
            if nonempty
            else "DOM_SUBSCRIBED_NO_LEVELS"
            if snapshot_errors == 0
            else "DOM_SUBSCRIPTION_WITH_SNAPSHOT_ERRORS_NO_LEVELS"
        ),
        "subscription_succeeded": True,
        "market_book_release_succeeded": release_ok,
        "samples_requested": sample_count,
        "snapshots_returned": len(snapshots),
        "nonempty_snapshots": len(nonempty),
        "empty_snapshots": empty,
        "snapshot_errors": snapshot_errors,
        "book_type_values": book_types,
        "average_levels_per_nonempty_snapshot": average("levels_returned"),
        "average_buy_limit_levels": average("buy_limit_levels"),
        "average_sell_limit_levels": average("sell_limit_levels"),
        "average_buy_limit_volume": average("buy_limit_volume"),
        "average_sell_limit_volume": average("sell_limit_volume"),
        "average_buy_market_volume": average("buy_market_volume"),
        "average_sell_market_volume": average("sell_market_volume"),
        "average_displayed_limit_depth_imbalance": (
            round(sum(imbalance_values) / len(imbalance_values), 8)
            if imbalance_values else None
        ),
        "quote_only_book_is_not_executed_trade_flow": True,
        "sampled_live_snapshots_are_not_historical_depth": True,
    }
    return result



def collect(mt5, symbol: str, days: int) -> dict[str, Any]:
    if days < 1 or days > 365:
        raise ValueError("DAYS_MUST_BE_IN_1_TO_365")

    if not mt5.initialize():
        raise RuntimeError(f"MT5_INITIALIZE_FAILED:{mt5.last_error()}")
    try:
        terminal = mt5.terminal_info()
        info = mt5.symbol_info(symbol)
        if terminal is None or info is None:
            raise RuntimeError(f"MT5_TERMINAL_OR_SYMBOL_UNAVAILABLE:{mt5.last_error()}")
        if not bool(getattr(terminal, "connected", False)):
            raise RuntimeError("MT5_TERMINAL_NOT_CONNECTED")

        flag_names = (
            "TICK_FLAG_BID",
            "TICK_FLAG_ASK",
            "TICK_FLAG_LAST",
            "TICK_FLAG_VOLUME",
            "TICK_FLAG_BUY",
            "TICK_FLAG_SELL",
            "COPY_TICKS_ALL",
        )
        missing = [name for name in flag_names if not hasattr(mt5, name)]
        if missing:
            raise RuntimeError("MT5_TICK_CONSTANTS_MISSING:" + ",".join(missing))

        end_utc = datetime.now(timezone.utc)
        start_utc = end_utc - timedelta(days=days)
        cursor = start_utc
        segments = []
        errors = []
        totals = {
            key: 0
            for key in (
                "ticks_returned",
                "ticks_in_segment",
                "ticks_outside_segment_filtered",
                "valid_two_sided_quote_ticks",
                "crossed_or_empty_quote_ticks",
                "bid_update_ticks",
                "ask_update_ticks",
                "both_quote_update_ticks",
                "last_update_ticks",
                "volume_update_ticks",
                "buy_side_flag_ticks",
                "sell_side_flag_ticks",
                "ambiguous_buy_and_sell_flag_ticks",
                "side_flags_without_last_or_volume_update",
                "buy_volume_update_ticks",
                "sell_volume_update_ticks",
                "buy_volume_real_positive_ticks",
                "sell_volume_real_positive_ticks",
            )
        }
        buy_volume_sum = 0.0
        sell_volume_sum = 0.0
        volume_basis_counts: dict[str, int] = {}
        monotonic = True
        first_tick_utc = None
        last_tick_utc = None

        flags = {
            "flag_bid": int(mt5.TICK_FLAG_BID),
            "flag_ask": int(mt5.TICK_FLAG_ASK),
            "flag_last": int(mt5.TICK_FLAG_LAST),
            "flag_volume": int(mt5.TICK_FLAG_VOLUME),
            "flag_buy": int(mt5.TICK_FLAG_BUY),
            "flag_sell": int(mt5.TICK_FLAG_SELL),
        }

        while cursor < end_utc:
            segment_end = min(cursor + timedelta(days=SEGMENT_DAYS), end_utc)
            row = {
                "start_utc": cursor.isoformat(),
                "end_utc": segment_end.isoformat(),
                "status": "NO_TICKS_RETURNED",
            }
            ticks = mt5.copy_ticks_range(
                symbol,
                cursor,
                segment_end,
                mt5.COPY_TICKS_ALL,
            )
            if ticks is None:
                error = str(mt5.last_error())
                row["status"] = "MT5_COPY_TICKS_RANGE_ERROR"
                row["error"] = error
                errors.append({
                    "start_utc": cursor.isoformat(),
                    "end_utc": segment_end.isoformat(),
                    "error": error,
                })
            else:
                start_ms = math.ceil(cursor.timestamp() * 1000)
                end_ms = math.ceil(segment_end.timestamp() * 1000)
                metrics = summarize_tick_capabilities(
                    ticks,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    **flags,
                )
                row.update(metrics)
                row["status"] = (
                    "TICKS_CAPTURED"
                    if metrics["ticks_in_segment"]
                    else "NO_TICKS_IN_SEGMENT"
                )
                for key in totals:
                    totals[key] += int(metrics[key])
                buy_volume_sum += float(metrics["buy_volume_real_sum"])
                sell_volume_sum += float(metrics["sell_volume_real_sum"])
                basis = str(metrics["volume_basis"])
                volume_basis_counts[basis] = volume_basis_counts.get(basis, 0) + 1
                monotonic = monotonic and bool(
                    metrics["timestamps_monotonic_non_decreasing"]
                )
                if metrics["first_tick_utc"]:
                    first_tick_utc = (
                        metrics["first_tick_utc"]
                        if first_tick_utc is None
                        else min(first_tick_utc, metrics["first_tick_utc"])
                    )
                if metrics["last_tick_utc"]:
                    last_tick_utc = (
                        metrics["last_tick_utc"]
                        if last_tick_utc is None
                        else max(last_tick_utc, metrics["last_tick_utc"])
                    )
            segments.append(row)
            cursor = segment_end

        trade_side_count = (
            totals["buy_side_flag_ticks"] + totals["sell_side_flag_ticks"]
        )
        trade_side_available = trade_side_count > 0
        trade_volume_available = (
            totals["buy_volume_real_positive_ticks"]
            + totals["sell_volume_real_positive_ticks"]
        ) > 0
        if totals["ticks_in_segment"] == 0 and errors:
            status = "TICK_HISTORY_UNAVAILABLE"
        elif totals["ticks_in_segment"] == 0:
            status = "NO_TICK_HISTORY_RETURNED"
        elif trade_side_available and trade_volume_available:
            status = "TRADE_SIDE_AND_VOLUME_FLAGS_CAPTURED"
        elif trade_side_available:
            status = "TRADE_SIDE_FLAGS_CAPTURED_VOLUME_UNAVAILABLE"
        else:
            status = "QUOTE_TICKS_ONLY_NO_TRADE_SIDE_FLAGS"

        market_depth = collect_market_depth(mt5, symbol)
        return {
            "schema": "forexai.mt5.xauusd_trade_tick_capability.v1",
            "status": status,
            "symbol": str(info.name),
            "captured_at_utc": end_utc.isoformat(),
            "requested_days": int(days),
            "history_start_utc": start_utc.isoformat(),
            "history_end_utc": end_utc.isoformat(),
            "tick_source": "MetaTrader5.copy_ticks_range(COPY_TICKS_ALL)",
            "tick_flag_values": flags,
            "coverage": {
                **totals,
                "segment_days": SEGMENT_DAYS,
                "segment_count": len(segments),
                "segments_with_tick_data": sum(
                    1 for item in segments if item.get("ticks_in_segment", 0) > 0
                ),
                "query_errors": errors,
                "first_tick_utc": first_tick_utc,
                "last_tick_utc": last_tick_utc,
                "timestamps_monotonic_non_decreasing": monotonic,
                "volume_basis_by_segment": volume_basis_counts,
            },
            "trade_side_capability": {
                "trade_side_flags_available": trade_side_available,
                "trade_side_tick_count": trade_side_count,
                "buy_side_flag_ticks": totals["buy_side_flag_ticks"],
                "sell_side_flag_ticks": totals["sell_side_flag_ticks"],
                "ambiguous_buy_and_sell_flag_ticks": totals["ambiguous_buy_and_sell_flag_ticks"],
                "trade_side_volume_available": trade_volume_available,
                "buy_volume_real_sum": round(buy_volume_sum, 10),
                "sell_volume_real_sum": round(sell_volume_sum, 10),
                "interpretation": (
                    "Broker supplied directional trade ticks; suitable for a separately "
                    "validated trade-side research feature, not automatic strategy approval."
                    if trade_side_available
                    else "No directional trade ticks were exposed in the requested history. "
                    "Do not label BID/ASK quote changes as buyer/seller order flow."
                ),
            },
            "market_depth_capability": market_depth,
            "quote_data": {
                "valid_two_sided_quote_ticks": totals["valid_two_sided_quote_ticks"],
                "bid_update_ticks": totals["bid_update_ticks"],
                "ask_update_ticks": totals["ask_update_ticks"],
                "both_quote_update_ticks": totals["both_quote_update_ticks"],
                "quote_only_is_not_aggressor_flow": True,
            },
            "limitations": [
                "BUY/SELL tick flags are reported only when supplied by the connected broker terminal.",
                "BID/ASK quote updates are not classified as buyer- or seller-initiated trades.",
                "No individual tick records, account identifiers, broker server names, or account currency are exported.",
                "This is a capability/coverage audit, not a trading signal, backtest, or profitability claim.",
                "Market Depth results are broker-supplied displayed liquidity snapshots, not executed trades or necessarily market-wide exchange depth.",
                "The Market Depth sample is live/current only; no historical order-book series is available from this probe.",
            ],
            "no_orders_submitted": True,
            "no_positions_modified": True,
            "no_terminal_settings_modified": True,
        }
    finally:
        mt5.shutdown()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only audit of XAUUSD trade-side tick availability in MT5"
    )
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument(
        "--output",
        default="artifacts/xauusd-trade-tick-capability.json",
    )
    args = parser.parse_args(argv)
    if args.days < 1 or args.days > 365:
        raise SystemExit("--days must be in [1,365]")

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit("Install requirements-mt5.txt before running this probe") from exc

    report = collect(mt5, args.symbol, args.days)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report["status"],
        "symbol": report["symbol"],
        "requested_days": report["requested_days"],
        "ticks_in_segment": report["coverage"]["ticks_in_segment"],
        "buy_side_flag_ticks": report["coverage"]["buy_side_flag_ticks"],
        "sell_side_flag_ticks": report["coverage"]["sell_side_flag_ticks"],
        "trade_side_flags_available": report["trade_side_capability"]["trade_side_flags_available"],
        "trade_side_volume_available": report["trade_side_capability"]["trade_side_volume_available"],
        "no_orders_submitted": report["no_orders_submitted"],
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
