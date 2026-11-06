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
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run signals independently per UTC date and prevent overnight carry.

    M5 timestamps identify bar opens. A bar is retained only when its five
    minutes have fully elapsed by flatten_by_utc. The execution kernel
    liquidates any open position at the final retained bar close.

    The default 20:50 UTC cutoff precedes the currently observed WM Markets
    earliest rollover (20:59 UTC in the UTC+3 season). Reconfirm broker timing
    before use if broker/server terms change.

    Since each UTC date is backtested separately, no trade carries through
    rollover. Zero financing is supplied only under this intraday constraint.
    """
    config.validate()
    cutoff = _parse_hhmm(flatten_by_utc, "FLATTEN_BY_UTC")
    rollover = _parse_hhmm(earliest_rollover_utc, "EARLIEST_ROLLOVER_UTC")
    cutoff_minutes = cutoff.hour * 60 + cutoff.minute
    rollover_minutes = rollover.hour * 60 + rollover.minute
    if cutoff_minutes >= rollover_minutes:
        raise XAUUSDIntradayAdapterError("FLATTEN_CUTOFF_NOT_BEFORE_ROLLOVER")

    missing = REQUIRED_SIGNAL_COLUMNS.difference(bars.columns)
    if missing:
        raise XAUUSDIntradayAdapterError(
            f"REQUIRED_COLUMNS_MISSING:{sorted(missing)}"
        )
    frame = bars.copy()
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
    bar_end_minutes = (
        frame["timestamp"].dt.hour * 60
        + frame["timestamp"].dt.minute
        + 5
    )
    frame = frame.loc[bar_end_minutes <= cutoff_minutes].copy()
    if frame.empty:
        raise XAUUSDIntradayAdapterError("NO_BARS_BEFORE_FLATTEN_CUTOFF")

    trades: list[dict[str, Any]] = []
    daily_runs = 0
    skipped_short_days = 0
    suppressed_entries = 0
    total_entries = 0
    for session_date, session in frame.groupby(
        frame["timestamp"].dt.strftime("%Y-%m-%d"), sort=True
    ):
        session = session.reset_index(drop=True)
        if len(session) < 2:
            skipped_short_days += 1
            continue

        # No position can survive beyond this UTC session. These zeros are
        # not guessed overnight swap values: positions are liquidated before
        # rollover and the historical swap schedule is not modeled.
        session["financing_long_usd_per_oz"] = 0.0
        session["financing_short_usd_per_oz"] = 0.0
        metrics, session_trades = run_xauusd_backtest(session, config)
        daily_runs += 1
        total_entries += int(metrics.get("entries", 0))
        suppressed_entries += int(
            metrics.get("entry_signals_suppressed_by_utc_hour_filter", 0)
        )

        for number, trade in enumerate(session_trades, start=1):
            entry_date = pd.Timestamp(trade["entry_time"]).date().isoformat()
            exit_date = pd.Timestamp(trade["exit_time"]).date().isoformat()
            if entry_date != session_date or exit_date != session_date:
                raise XAUUSDIntradayAdapterError("OVERNIGHT_POSITION_DETECTED")
            if float(trade["financing_usd_per_oz"]) != 0.0:
                raise XAUUSDIntradayAdapterError("UNEXPECTED_FINANCING_CHARGE")
            trades.append({
                **trade,
                "utc_session_date": session_date,
                "session_trade_number": number,
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
