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


def summarize_spread_points(
    spread_points,
    *,
    point: float,
    tick_size: float,
    tick_value: float,
) -> dict:
    """Summarize sampled spreads in points, quote-price units, and account currency/lot."""
    if not math.isfinite(float(point)) or point <= 0:
        raise ValueError("POINT_INVALID")
    if not math.isfinite(float(tick_size)) or tick_size <= 0:
        raise ValueError("TICK_SIZE_INVALID")
    if not math.isfinite(float(tick_value)) or tick_value < 0:
        raise ValueError("TICK_VALUE_INVALID")

    clean = []
    for value in spread_points:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number) and number >= 0:
            clean.append(number)

    spread_prices = [value * point for value in clean]
    costs_per_lot = [
        (price / tick_size) * tick_value for price in spread_prices
    ]
    return {
        "spread_points": _stats(clean),
        "spread_price_per_oz_quote_currency": _stats(spread_prices),
        "spread_cost_per_standard_lot_account_currency": _stats(costs_per_lot),
    }


def _extract_spreads_and_times(ticks, point: float):
    """Return valid quote spreads in points and their UTC timestamps."""
    import numpy as np

    if ticks is None or len(ticks) == 0:
        return np.asarray([], dtype=float), []

    names = getattr(getattr(ticks, "dtype", None), "names", None) or ()
    if "bid" not in names or "ask" not in names:
        raise RuntimeError("MT5_TICK_FIELDS_MISSING_BID_ASK")

    bids = np.asarray(ticks["bid"], dtype=float)
    asks = np.asarray(ticks["ask"], dtype=float)
    valid = (
        np.isfinite(bids)
        & np.isfinite(asks)
        & (bids > 0)
        & (asks >= bids)
    )
    spreads = (asks[valid] - bids[valid]) / point

    valid_times = []
    if "time_msc" in names:
        raw_times = np.asarray(ticks["time_msc"], dtype="int64")[valid]
        valid_times = [int(value) for value in raw_times if value > 0]
    elif "time" in names:
        raw_times = np.asarray(ticks["time"], dtype="int64")[valid]
        valid_times = [int(value) * 1000 for value in raw_times if value > 0]

    return spreads, valid_times


def collect(mt5, symbol: str, days: int) -> dict:
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
        total_ticks = 0
        total_valid_quotes = 0
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
                    spreads, times_ms = _extract_spreads_and_times(ticks, point)
                    valid_count = int(len(spreads))
                    segment["valid_two_sided_quote_ticks"] = valid_count
                    total_valid_quotes += valid_count
                    if valid_count:
                        chunks_with_valid_quotes += 1
                        take = min(valid_count, MAX_SAMPLE_PER_SEGMENT)
                        if take == valid_count:
                            sample = spreads
                        else:
                            indices = np.linspace(
                                0, valid_count - 1, num=take, dtype="int64"
                            )
                            sample = spreads[indices]
                        sampled_spreads.extend(float(value) for value in sample)
                        segment["sampled_quote_ticks"] = int(len(sample))
                        segment["status"] = "QUOTE_SAMPLE_CAPTURED"
                        if times_ms:
                            chunk_first = min(times_ms)
                            chunk_last = max(times_ms)
                            first_tick_ms = (
                                chunk_first if first_tick_ms is None
                                else min(first_tick_ms, chunk_first)
                            )
                            last_tick_ms = (
                                chunk_last if last_tick_ms is None
                                else max(last_tick_ms, chunk_last)
                            )
                    else:
                        segment["status"] = "NO_VALID_TWO_SIDED_QUOTES"
            segments.append(segment)
            cursor = segment_end

        distribution = summarize_spread_points(
            sampled_spreads,
            point=point,
            tick_size=tick_size,
            tick_value=tick_value,
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
                "sampled_quote_ticks": len(sampled_spreads),
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
                "quantiles_describe_sample_not_every_returned_tick": True,
                "time_weighted_spread_estimate": False,
            },
            "spread_distribution": distribution,
            "limitations": [
                "Coverage depends on tick history supplied by the connected broker terminal.",
                "A missing segment is reported; no quote ticks or spreads are synthesized.",
                "Statistics are deterministic samples of quote events, not time-weighted spread estimates.",
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
