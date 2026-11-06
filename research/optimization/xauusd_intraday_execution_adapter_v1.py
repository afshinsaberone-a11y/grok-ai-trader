"""Intraday-only adapter for the XAUUSD BID/ASK execution contract.

It splits a real M5 signal frame into UTC trading dates and runs each date
independently. Every position is liquidated by the configured UTC cutoff,
before the earliest known broker rollover. Zero financing is supplied only
because no trade can carry through rollover. This is not a historical swap
schedule and must not be used for overnight strategies.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import time
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.xauusd_execution_contract_v1 import (
    XAUUSDExecutionConfig,
    run_xauusd_backtest,
)

REQUIRED_SIGNAL_COLUMNS = {
    "timestamp",
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
    "signal", "ATR",
}


class XAUUSDIntradayAdapterError(ValueError):
    """Raised when bars or cutoff rules cannot prove intraday-only execution."""


def _parse_hhmm(value: str, field: str) -> time:
    try:
        parsed = time.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise XAUUSDIntradayAdapterError(f"{field}_INVALID") from exc
    if parsed.second or parsed.microsecond:
        raise XAUUSDIntradayAdapterError(f"{field}_MUST_BE_HH_MM")
    return parsed


def run_xauusd_intraday(
    bars: pd.DataFrame,
    config: XAUUSDExecutionConfig,
    *,
    flatten_by_utc: str = "20:50",
    earliest_rollover_utc: str = "20:59",
    indicator_warmup_bars_after_gap: int | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run each UTC day and each contiguous M5 segment independently.

    M5 timestamps identify bar opens. A bar is retained only when its five
    minutes have fully elapsed by flatten_by_utc. A position is liquidated at
    the last observed close before every intraday data gap and before the UTC
    session ends, so no position crosses an unknown price interval.

    When an intraday gap exists, callers must explicitly provide the maximum
    indicator warm-up/lookback length. Signals are suppressed for that many
    bars after each gap so rolling features cannot reuse pre-gap observations.
    """
    config.validate()
    cutoff = _parse_hhmm(flatten_by_utc, "FLATTEN_BY_UTC")
    rollover = _parse_hhmm(earliest_rollover_utc, "EARLIEST_ROLLOVER_UTC")
    cutoff_minutes = cutoff.hour * 60 + cutoff.minute
    rollover_minutes = rollover.hour * 60 + rollover.minute
    if cutoff_minutes >= rollover_minutes:
        raise XAUUSDIntradayAdapterError("FLATTEN_CUTOFF_NOT_BEFORE_ROLLOVER")
    if indicator_warmup_bars_after_gap is not None and (
        type(indicator_warmup_bars_after_gap) is not int
        or indicator_warmup_bars_after_gap < 1
    ):
        raise XAUUSDIntradayAdapterError("GAP_INDICATOR_WARMUP_INVALID")

    missing = REQUIRED_SIGNAL_COLUMNS.difference(bars.columns)
    if missing:
        raise XAUUSDIntradayAdapterError(
            f"REQUIRED_COLUMNS_MISSING:{sorted(missing)}"
        )
    frame = bars.copy().reset_index(drop=True)
    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"], utc=True, errors="coerce"
    )
    if frame.empty or frame["timestamp"].isna().any():
        raise XAUUSDIntradayAdapterError("TIMESTAMP_EMPTY_OR_INVALID")
    if frame["timestamp"].duplicated().any():
        raise XAUUSDIntradayAdapterError("DUPLICATE_TIMESTAMPS")
    if not frame["timestamp"].is_monotonic_increasing:
        raise XAUUSDIntradayAdapterError("TIMESTAMPS_NOT_MONOTONIC")
    if (
        frame["timestamp"].dt.second.ne(0).any()
        or frame["timestamp"].dt.microsecond.ne(0).any()
        or frame["timestamp"].dt.minute.mod(5).ne(0).any()
    ):
        raise XAUUSDIntradayAdapterError("M5_TIMESTAMP_ALIGNMENT_INVALID")

    # M5 timestamps are bar OPEN times. A 20:45 bar closes at 20:50 UTC.
    raw_frame = frame.copy()
    bar_end_minutes = (
        raw_frame["timestamp"].dt.hour * 60
        + raw_frame["timestamp"].dt.minute
        + 5
    )
    eligible_mask = bar_end_minutes <= cutoff_minutes

    # Detect truncated sessions BEFORE discarding post-cutoff rows. Otherwise,
    # a gap whose first returning bar is after cutoff disappears from the
    # filtered frame and a forced exit can be mislabeled as normal day-end.
    cutoff_truncated_sessions: set[str] = set()
    for raw_date, raw_session in raw_frame.groupby(
        raw_frame["timestamp"].dt.strftime("%Y-%m-%d"), sort=True
    ):
        session_mask = raw_session.index.isin(raw_frame.index[eligible_mask])
        eligible_session = raw_session.loc[session_mask]
        if eligible_session.empty:
            continue
        last_eligible_close = (
            eligible_session["timestamp"].iloc[-1] + pd.Timedelta(minutes=5)
        )
        cutoff_timestamp = (
            pd.Timestamp(f"{raw_date}T00:00:00Z")
            + pd.Timedelta(minutes=cutoff_minutes)
        )
        if last_eligible_close < cutoff_timestamp:
            cutoff_truncated_sessions.add(raw_date)

    frame = raw_frame.loc[eligible_mask].copy()
    if frame.empty:
        raise XAUUSDIntradayAdapterError("NO_BARS_BEFORE_FLATTEN_CUTOFF")

    trades: list[dict[str, Any]] = []
    daily_runs = 0
    segments_executed = 0
    skipped_short_days = 0
    skipped_short_segments = 0
    intraday_gap_count = 0
    gap_split_segments_with_open_position = 0
    cutoff_truncated_gap_exit_segments_with_open_position = 0
    gap_exit_assumption_trade_count = 0
    post_gap_signal_rows_suppressed = 0
    suppressed_entries = 0
    total_entries = 0

    for session_date, session in frame.groupby(
        frame["timestamp"].dt.strftime("%Y-%m-%d"), sort=True
    ):
        session = session.reset_index(drop=True)
        if len(session) < 2:
            skipped_short_days += 1
            continue
        daily_runs += 1

        # An exact M5 continuation is five minutes. Any longer interval is an
        # unknown price path and becomes a hard execution boundary.
        gap_starts = session.index[
            session["timestamp"].diff().gt(pd.Timedelta(minutes=5))
        ].tolist()
        if gap_starts and indicator_warmup_bars_after_gap is None:
            raise XAUUSDIntradayAdapterError(
                "GAP_INDICATOR_WARMUP_REQUIRED"
            )
        intraday_gap_count += len(gap_starts)
        boundaries = [0, *gap_starts, len(session)]
        session_trade_number = 0

        for segment_number, (left, right) in enumerate(
            zip(boundaries[:-1], boundaries[1:]), start=1
        ):
            segment = session.iloc[left:right].copy().reset_index(drop=True)
            if len(segment) < 2:
                skipped_short_segments += 1
                continue

            # Signals generated from a pre-gap rolling window are unusable
            # until the strategy's full indicator lookback has refilled.
            if segment_number > 1 and indicator_warmup_bars_after_gap:
                warmup_end = min(
                    indicator_warmup_bars_after_gap, len(segment)
                )
                warmup_mask = segment.index < warmup_end
                post_gap_signal_rows_suppressed += int(
                    segment.loc[warmup_mask, "signal"].ne(0).sum()
                )
                segment.loc[warmup_mask, "signal"] = 0

            # No position can survive this contiguous segment. Zero financing
            # is used only because liquidation occurs before its final close.
            segment["financing_long_usd_per_oz"] = 0.0
            segment["financing_short_usd_per_oz"] = 0.0
            metrics, segment_trades = run_xauusd_backtest(segment, config)
            segments_executed += 1
            total_entries += int(metrics.get("entries", 0))
            suppressed_entries += int(
                metrics.get("entry_signals_suppressed_by_utc_hour_filter", 0)
            )
            pre_gap_segment = segment_number < len(boundaries) - 1
            cutoff_truncated_final_segment = (
                segment_number == len(boundaries) - 1
                and session_date in cutoff_truncated_sessions
            )
            gap_boundary_segment = (
                pre_gap_segment or cutoff_truncated_final_segment
            )
            if (
                pre_gap_segment
                and metrics.get("forced_end_of_data_liquidation") is True
            ):
                gap_split_segments_with_open_position += 1
            if (
                cutoff_truncated_final_segment
                and metrics.get("forced_end_of_data_liquidation") is True
            ):
                cutoff_truncated_gap_exit_segments_with_open_position += 1

            for trade in segment_trades:
                entry_date = pd.Timestamp(trade["entry_time"]).date().isoformat()
                exit_date = pd.Timestamp(trade["exit_time"]).date().isoformat()
                if entry_date != session_date or exit_date != session_date:
                    raise XAUUSDIntradayAdapterError("OVERNIGHT_POSITION_DETECTED")
                if float(trade["financing_usd_per_oz"]) != 0.0:
                    raise XAUUSDIntradayAdapterError("UNEXPECTED_FINANCING_CHARGE")
                trade_row = dict(trade)
                gap_exit_assumption = (
                    gap_boundary_segment
                    and trade_row.get("exit_reason") == "end_of_data_liquidation"
                )
                if gap_exit_assumption:
                    # This is a conservative research boundary assumption,
                    # not evidence of an executable broker fill.
                    trade_row["exit_reason"] = "pre_gap_last_observed_close_assumption"
                    gap_exit_assumption_trade_count += 1
                trade_row["gap_exit_assumption"] = bool(gap_exit_assumption)
                session_trade_number += 1
                trades.append({
                    **trade_row,
                    "utc_session_date": session_date,
                    "utc_segment_number": segment_number,
                    "session_trade_number": session_trade_number,
                })

    net_r = [float(item["net_R"]) for item in trades]
    wins = [value for value in net_r if value > 0]
    losses = [value for value in net_r if value < 0]
    gross_profit = float(sum(wins))
    gross_loss = float(abs(sum(losses)))
    if gross_loss > 0:
        profit_factor: float | str = round(gross_profit / gross_loss, 6)
    elif gross_profit > 0:
        profit_factor = "inf"
    else:
        profit_factor = 0.0

    equity = peak = 10_000.0
    max_dd_pct = 0.0
    for value in net_r:
        equity *= max(0.0, 1.0 + value * config.risk_fraction)
        peak = max(peak, equity)
        if peak > 0:
            max_dd_pct = max(max_dd_pct, 100.0 * (peak - equity) / peak)

    result = {
        "schema": "forexai.xauusd_intraday_execution_adapter.v1",
        "status": "INTRADAY_EXECUTION_SIMULATION_ONLY",
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "rows_before_cutoff": int(len(frame)),
        "utc_sessions_executed": daily_runs,
        "utc_sessions_skipped_under_two_bars": skipped_short_days,
        "utc_segments_executed": segments_executed,
        "utc_segments_skipped_under_two_bars": skipped_short_segments,
        "intraday_data_gaps_detected": intraday_gap_count,
        "utc_sessions_truncated_before_cutoff": len(cutoff_truncated_sessions),
        "gap_split_segments_with_open_position": gap_split_segments_with_open_position,
        "cutoff_truncated_gap_exit_segments_with_open_position": cutoff_truncated_gap_exit_segments_with_open_position,
        "gap_exit_assumption_trades": gap_exit_assumption_trade_count,
        "backtest_qualification_status": (
            "GAP_EXIT_ASSUMPTIONS_PRESENT_REVIEW_REQUIRED"
            if gap_exit_assumption_trade_count
            else "NO_GAP_EXIT_ASSUMPTIONS"
        ),
        "post_gap_signal_rows_suppressed": post_gap_signal_rows_suppressed,
        "indicator_warmup_bars_after_gap": indicator_warmup_bars_after_gap,
        "gap_handling_policy": "SPLIT_FLATTEN_REQUIRE_WARMUP_AND_AUDIT_CUTOFF_COVERAGE",
        "trades": len(trades),
        "entries": total_entries,
        "entries_equal_exits": total_entries == len(trades),
        "win_rate_pct": round(100.0 * len(wins) / len(net_r), 4) if net_r else 0.0,
        "expectancy_R": round(float(np.mean(net_r)), 8) if net_r else 0.0,
        "total_R": round(float(np.sum(net_r)), 8) if net_r else 0.0,
        "profit_factor": profit_factor,
        "max_dd_pct": round(max_dd_pct, 6),
        "normalized_equity_index_final": round(equity, 6),
        "risk_fraction": config.risk_fraction,
        "commission_round_turn_usd_per_oz": config.commission_usd_per_oz_round_turn,
        "slippage_per_side_usd_per_oz": config.slippage_usd_per_oz_per_side,
        "financing_model": "ZERO_NO_OVERNIGHT_CARRY",
        "financing_is_historical_broker_schedule": False,
        "positions_carry_through_rollover": False,
        "positions_carry_through_intraday_data_gaps": False,
        "flatten_by_utc": flatten_by_utc,
        "earliest_rollover_utc_assumption": earliest_rollover_utc,
        "entry_signals_suppressed_by_utc_hour_filter": suppressed_entries,
        "execution_config": asdict(config),
        "promotion_status": "RESEARCH_ONLY",
        "demo_authorized": False,
        "live_authorized": False,
        "orders_submitted": False,
    }
    return result, trades
