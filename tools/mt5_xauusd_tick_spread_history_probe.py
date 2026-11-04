"""Read-only historical XAUUSD tick-spread sampler for an open MT5 terminal.

The tool reads broker-provided BID/ASK quote ticks only. It never submits,
checks, changes, or closes orders and does not export account identifiers.
Sampling is deterministic and bounded per weekly segment.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median


MAX_SAMPLE_PER_SEGMENT = 12_000
SEGMENT_DAYS = 7


def _quantile(sorted_values: list[float], probability: float) -> float | None:
    if not sorted_values:
        return None
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


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
        "mean": round(mean(ordered), 10),
        "median": round(median(ordered), 10),
        "p95": round(_quantile(ordered, 0.95), 10),
        "p99": round(_quantile(ordered, 0.99), 10),
        "min": round(ordered[0], 10),
        "max": round(ordered[-1], 10),
    }


def _weighted_quantile(values: list[float], weights: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(zip(values, weights), key=lambda item: item[0])
    total_weight = sum(weight for _, weight in ordered)
    if total_weight <= 0:
        return None
    threshold = probability * total_weight
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


def _weighted_stats(values: list[float], weights: list[float]) -> dict:
    if not values:
        return {
            "count": 0,
            "represented_tick_weight": 0.0,
            "mean": None,
            "median": None,
            "p95": None,
            "p99": None,
            "min": None,
            "max": None,
        }
    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError("SAMPLE_WEIGHTS_INVALID")
    return {
        "count": len(values),
        "represented_tick_weight": round(total_weight, 6),
        "mean": round(sum(v * w for v, w in zip(values, weights)) / total_weight, 10),
        "median": round(_weighted_quantile(values, weights, 0.50), 10),
        "p95": round(_weighted_quantile(values, weights, 0.95), 10),
        "p99": round(_weighted_quantile(values, weights, 0.99), 10),
        "min": round(min(values), 10),
        "max": round(max(values), 10),
    }


def summarize_spread_points(
    spread_points,
    *,
    point: float,
    tick_size: float,
    tick_value: float,
    weights=None,
) -> dict:
    """Summarize spread samples, optionally weighting each sample by represented ticks."""
    if not math.isfinite(float(point)) or point <= 0:
        raise ValueError("POINT_INVALID")
    if not math.isfinite(float(tick_size)) or tick_size <= 0:
        raise ValueError("TICK_SIZE_INVALID")
    if not math.isfinite(float(tick_value)) or tick_value < 0:
        raise ValueError("TICK_VALUE_INVALID")

    raw_values = list(spread_points)
    raw_weights = [1.0] * len(raw_values) if weights is None else list(weights)
    if len(raw_weights) != len(raw_values):
        raise ValueError("SAMPLE_WEIGHTS_LENGTH_MISMATCH")

    clean = []
    clean_weights = []
    for value, weight in zip(raw_values, raw_weights):
        try:
            number = float(value)
            sample_weight = float(weight)
        except (TypeError, ValueError):
            continue
        if (
            math.isfinite(number)
            and number >= 0
            and math.isfinite(sample_weight)
            and sample_weight > 0
        ):
            clean.append(number)
            clean_weights.append(sample_weight)

    spread_prices = [value * point for value in clean]
    costs_per_lot = [
        (price / tick_size) * tick_value for price in spread_prices
    ]
    stats = (
        _stats(clean)
        if weights is None
        else _weighted_stats(clean, clean_weights)
    )
    price_stats = (
        _stats(spread_prices)
        if weights is None
        else _weighted_stats(spread_prices, clean_weights)
    )
    cost_stats = (
        _stats(costs_per_lot)
        if weights is None
        else _weighted_stats(costs_per_lot, clean_weights)
    )
    return {
        "spread_points": stats,
        "spread_price_per_oz_quote_currency": price_stats,
        "spread_cost_per_standard_lot_account_currency": cost_stats,
        "statistical_weighting": (
            "unweighted_sample"
            if weights is None
            else "represented_quote_tick_count"
        ),
    }


def _extract_spreads_and_times(
    ticks,
    point: float,
    *,
    start_ms: int,
    end_ms: int,
):
    """Return valid BID/ASK spreads whose quote timestamps are inside [start_ms, end_ms)."""
    import numpy as np

    if ticks is None or len(ticks) == 0:
        return np.asarray([], dtype=float), np.asarray([], dtype="int64"), 0

    names = getattr(getattr(ticks, "dtype", None), "names", None) or ()
    if "bid" not in names or "ask" not in names:
        raise RuntimeError("MT5_TICK_FIELDS_MISSING_BID_ASK")
    if "time_msc" in names:
        timestamps_ms = np.asarray(ticks["time_msc"], dtype="int64")
    elif "time" in names:
        timestamps_ms = np.asarray(ticks["time"], dtype="int64") * 1000
    else:
        raise RuntimeError("MT5_TICK_TIMESTAMP_FIELDS_MISSING")

    bids = np.asarray(ticks["bid"], dtype=float)
    asks = np.asarray(ticks["ask"], dtype=float)
    valid_quote = (
        np.isfinite(bids)
        & np.isfinite(asks)
        & (bids > 0)
        & (asks >= bids)
    )
    valid_time = (
        (timestamps_ms > 0)
        & (timestamps_ms >= int(start_ms))
        & (timestamps_ms < int(end_ms))
    )
    outside_segment_quotes = int((valid_quote & ~valid_time).sum())
    valid = valid_quote & valid_time
    spreads = (asks[valid] - bids[valid]) / point
    valid_times = timestamps_ms[valid]
    return spreads, valid_times, outside_segment_quotes


def collect(mt5, symbol: str, days: int) -> dict:
    import numpy as np

    if not mt5.initialize():
        raise RuntimeError(f"MT5_INITIALIZE_FAILED:{mt5.last_error()}")
    try:
        terminal = mt5.terminal_info()
        account = mt5.account_info()
        info = mt5.symbol_info(symbol)
        if terminal is None or account is None or info is None:
            raise RuntimeError(f"MT5_TERMINAL_ACCOUNT_OR_SYMBOL_UNAVAILABLE:{mt5.last_error()}")
        if not bool(getattr(terminal, "connected", False)):
            raise RuntimeError("MT5_TERMINAL_NOT_CONNECTED")

        point = float(info.point)
        tick_size = float(info.trade_tick_size)
        tick_value = float(info.trade_tick_value)
        if not math.isfinite(point) or point <= 0:
            raise RuntimeError("XAUUSD_POINT_INVALID")
        if not math.isfinite(tick_size) or tick_size <= 0:
            raise RuntimeError("XAUUSD_TICK_SIZE_INVALID")
        if not math.isfinite(tick_value) or tick_value < 0:
            raise RuntimeError("XAUUSD_TICK_VALUE_INVALID")

        end_utc = datetime.now(timezone.utc)
        start_utc = end_utc - timedelta(days=days)
        cursor = start_utc
        sampled_spreads = []
        sampled_weights = []
        top_sampled_spreads = []
        total_ticks = 0
        total_valid_quotes = 0
        total_out_of_segment_quotes = 0
        chunks_with_ticks = 0
        chunks_with_valid_quotes = 0
        errors = []
        segments = []
        first_tick_ms = None
        last_tick_ms = None

        while cursor < end_utc:
            segment_end = min(cursor + timedelta(days=SEGMENT_DAYS), end_utc)
            ticks = mt5.copy_ticks_range(
                symbol,
                cursor,
                segment_end,
                mt5.COPY_TICKS_INFO,
            )
            segment = {
                "start_utc": cursor.isoformat(),
                "end_utc": segment_end.isoformat(),
                "ticks_returned": 0,
                "valid_two_sided_quote_ticks": 0,
                "sampled_quote_ticks": 0,
                "status": "NO_TICKS_RETURNED",
            }
            if ticks is None:
                error = str(mt5.last_error())
                segment["status"] = "MT5_COPY_TICKS_RANGE_ERROR"
                segment["error"] = error
                errors.append({
                    "start_utc": cursor.isoformat(),
                    "end_utc": segment_end.isoformat(),
                    "error": error,
                })
            else:
                tick_count = int(len(ticks))
                segment["ticks_returned"] = tick_count
                total_ticks += tick_count
                if tick_count:
                    chunks_with_ticks += 1
                    segment_start_ms = int(cursor.timestamp() * 1000)
                    segment_end_ms = int(segment_end.timestamp() * 1000)
                    spreads, times_ms, outside_count = _extract_spreads_and_times(
                        ticks,
                        point,
                        start_ms=segment_start_ms,
                        end_ms=segment_end_ms,
                    )
                    total_out_of_segment_quotes += outside_count
                    valid_count = int(len(spreads))
                    segment["valid_two_sided_quote_ticks"] = valid_count
                    segment["valid_two_sided_quotes_outside_segment_filtered"] = outside_count
                    total_valid_quotes += valid_count
                    if valid_count:
                        chunks_with_valid_quotes += 1
                        take = min(valid_count, MAX_SAMPLE_PER_SEGMENT)
                        if take == valid_count:
                            indices = np.arange(valid_count, dtype="int64")
                        else:
                            indices = np.linspace(
                                0, valid_count - 1, num=take, dtype="int64"
                            )
                        sample = spreads[indices]
                        sample_times = times_ms[indices]
                        segment_weight = valid_count / float(take)
                        sample_weights = [segment_weight] * take
                        sampled_spreads.extend(float(value) for value in sample)
                        sampled_weights.extend(sample_weights)
                        segment["sampled_quote_ticks"] = int(len(sample))
                        segment["represented_tick_weight"] = round(valid_count, 6)
                        segment["sampled_spread_points"] = _weighted_stats(
                            [float(value) for value in sample],
                            sample_weights,
                        )
                        segment["status"] = "QUOTE_SAMPLE_CAPTURED"

                        chunk_first = int(times_ms.min())
                        chunk_last = int(times_ms.max())
                        first_tick_ms = (
                            chunk_first if first_tick_ms is None
                            else min(first_tick_ms, chunk_first)
                        )
                        last_tick_ms = (
                            chunk_last if last_tick_ms is None
                            else max(last_tick_ms, chunk_last)
                        )

                        top_sampled_spreads.extend(
                            {
                                "timestamp_utc": datetime.fromtimestamp(
                                    int(sample_times[index]) / 1000,
                                    timezone.utc,
                                ).isoformat(),
                                "spread_points": round(float(sample[index]), 6),
                                "segment_start_utc": cursor.isoformat(),
                            }
                            for index in range(len(sample))
                        )
                        top_sampled_spreads = sorted(
                            top_sampled_spreads,
                            key=lambda item: item["spread_points"],
                            reverse=True,
                        )[:20]
                    else:
                        segment["status"] = "NO_VALID_TWO_SIDED_QUOTES"
            segments.append(segment)
            cursor = segment_end

        distribution = summarize_spread_points(
            sampled_spreads,
            point=point,
            tick_size=tick_size,
            tick_value=tick_value,
            weights=sampled_weights,
        )
        if sampled_spreads and errors:
            status = "PARTIAL_TICK_SPREAD_HISTORY"
        elif sampled_spreads:
            status = "TICK_SPREAD_HISTORY_CAPTURED"
        elif errors:
            status = "TICK_SPREAD_HISTORY_UNAVAILABLE"
        elif total_ticks:
            status = "NO_VALID_TWO_SIDED_QUOTES"
        else:
            status = "NO_TICK_SPREAD_HISTORY_RETURNED"

        return {
            "schema": "forexai.mt5.xauusd_tick_spread_history_probe.v1",
            "status": status,
            "symbol": str(info.name),
            "captured_at_utc": end_utc.isoformat(),
            "requested_days": int(days),
            "history_start_utc": start_utc.isoformat(),
            "history_end_utc": end_utc.isoformat(),
            "quote_source": "MetaTrader5.copy_ticks_range(COPY_TICKS_INFO)",
            "account_currency": str(account.currency),
            "symbol_units": {
                "digits": int(info.digits),
                "point": point,
                "tick_size": tick_size,
                "tick_value_account_currency_per_tick_per_lot": tick_value,
                "contract_size": float(info.trade_contract_size),
                "current_spread_points_snapshot": int(info.spread),
            },
            "coverage": {
                "segment_days": SEGMENT_DAYS,
                "segment_count": len(segments),
                "segments_with_ticks": chunks_with_ticks,
                "segments_with_valid_two_sided_quotes": chunks_with_valid_quotes,
                "ticks_returned": total_ticks,
                "valid_two_sided_quote_ticks": total_valid_quotes,
                "valid_two_sided_quotes_outside_segments_filtered": total_out_of_segment_quotes,
                "sampled_quote_ticks": len(sampled_spreads),
                "represented_tick_weight": round(sum(sampled_weights), 6),
                "sample_fraction_of_valid_ticks": (
                    round(len(sampled_spreads) / total_valid_quotes, 8)
                    if total_valid_quotes else 0.0
                ),
                "first_valid_tick_utc": (
                    datetime.fromtimestamp(first_tick_ms / 1000, timezone.utc).isoformat()
                    if first_tick_ms is not None else None
                ),
                "last_valid_tick_utc": (
                    datetime.fromtimestamp(last_tick_ms / 1000, timezone.utc).isoformat()
                    if last_tick_ms is not None else None
                ),
                "query_errors": errors,
                "segments": segments,
            },
            "sampling": {
                "method": "deterministic evenly spaced tick-index sample within each seven-day segment",
                "max_sampled_ticks_per_segment": MAX_SAMPLE_PER_SEGMENT,
                "global_distribution_weighting": "each sampled quote is weighted by valid in-range quote ticks in its segment divided by sampled quote ticks in that segment",
                "equal_segment_weighting": False,
                "quantiles_describe_weighted_sample_not_every_returned_tick": True,
                "time_weighted_spread_estimate": False,
            },
            "spread_distribution": distribution,
            "top_20_sampled_spread_events": top_sampled_spreads,
            "limitations": [
                "Coverage depends on tick history supplied by the connected broker terminal.",
                "A missing segment is reported; no quote ticks or spreads are synthesized.",
                "Ticks outside the exact UTC half-open segment interval are excluded before sampling.",
                "Global statistics use segment tick-count weights to avoid giving low-volume and partial weeks the same weight as high-volume full weeks.",
                "Statistics are weighted samples of quote events, not time-weighted spread estimates.",
                "The spread history is not combined with Dukascopy prices and does not establish historical slippage.",
                "Current tick value and contract settings are used only for the account-currency-per-lot conversion.",
            ],
            "no_orders_submitted": True,
            "no_positions_modified": True,
            "no_terminal_settings_modified": True,
            "account_login_exported": False,
            "broker_company_or_server_exported": False,
        }
    finally:
        mt5.shutdown()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only MT5 XAUUSD historical BID/ASK tick-spread sampler"
    )
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument(
        "--output",
        default="artifacts/xauusd-tick-spread-history-probe.json",
    )
    args = parser.parse_args(argv)
    if args.days < 1 or args.days > 3650:
        raise SystemExit("--days must be in [1,3650]")

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        raise SystemExit(
            "Install the Windows MetaTrader5 package: py -m pip install MetaTrader5"
        ) from exc

    report = collect(mt5, args.symbol, args.days)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "status": report["status"],
        "symbol": report["symbol"],
        "requested_days": report["requested_days"],
        "ticks_returned": report["coverage"]["ticks_returned"],
        "valid_two_sided_quote_ticks": report["coverage"]["valid_two_sided_quote_ticks"],
        "sampled_quote_ticks": report["coverage"]["sampled_quote_ticks"],
        "spread_points": report["spread_distribution"]["spread_points"],
        "spread_cost_per_standard_lot_account_currency": report["spread_distribution"][
            "spread_cost_per_standard_lot_account_currency"
        ],
        "no_orders_submitted": report["no_orders_submitted"],
        "output": str(output),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
