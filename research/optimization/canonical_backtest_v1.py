"""Canonical backtest execution kernel v1.

This module is the single Python execution implementation for research-time
trade simulation. It consumes strategy signals but owns entry, exit, cost,
holding-period, and accounting semantics.

It does not download, synthesize, or repair market data.
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd

from research.optimization.execution_contract_v1 import (
    ExecutionConfig,
    apply_entry_cost,
    apply_exit_cost,
    validate_ohlc,
)


SignalProvider = Callable[[pd.DataFrame], pd.DataFrame]


def run_canonical_backtest(
    df: pd.DataFrame,
    params: dict[str, float],
    signal_provider: SignalProvider,
    *,
    symbol: str = "EURUSD",
    risk_fraction: float = 0.005,
    trade_start: pd.Timestamp | None = None,
    config: ExecutionConfig | None = None,
) -> tuple[dict[str, Any], list[float]]:
    """Run one deterministic, cost-aware execution simulation.

    Signal on bar i is generated from the fully closed bar i. The order is
    filled at bar i+1 raw open with adverse entry cost. SL/TP are anchored to
    that actual entry price. The entry bar itself is evaluated for SL/TP.
    """
    if set(params) != {"atr_mult", "rr"}:
        raise ValueError("CANONICAL_PARAMS_INVALID")
    if not all(np.isfinite(float(v)) and float(v) > 0 for v in params.values()):
        raise ValueError("CANONICAL_PARAMS_INVALID")
    if not np.isfinite(risk_fraction) or risk_fraction <= 0 or risk_fraction > 0.006:
        raise ValueError("CANONICAL_RISK_FRACTION_INVALID")

    cfg = config or ExecutionConfig(risk_pct=risk_fraction)
    validate_ohlc(df)
    if df.empty or len(df) < 2:
        return (
            {
                "symbol": symbol,
                "trades": 0,
                "win_rate_pct": 0.0,
                "expectancy_R": 0.0,
                "total_R": 0.0,
                "profit_factor": 0.0,
                "final_equity": 10000.0,
                "max_dd_pct": 0.0,
                "avg_hold_bars": 0.0,
                "round_trip_cost_pips": cfg.round_trip_cost_pips,
                "entries_equal_exits": True,
                "next_bar_open_entry": True,
                "actual_entry_price_for_stops": True,
                "adverse_exit_cost_applied": True,
                "same_bar_sl_first": True,
                "one_position_at_a_time": True,
                "open_position_at_end": False,
            },
            [],
        )

    d = signal_provider(df.copy())
    required = {"Open", "High", "Low", "Close", "signal", "ATR"}
    missing = required.difference(d.columns)
    if missing:
        raise ValueError(f"CANONICAL_SIGNAL_PROVIDER_INVALID:{sorted(missing)}")
    d = d.copy()
    d.index = pd.to_datetime(d.index, utc=True)
    d = d.sort_index()
    validate_ohlc(d)

    open_px = d["Open"].to_numpy(float)
    high = d["High"].to_numpy(float)
    low = d["Low"].to_numpy(float)
    signal = d["signal"].fillna(0).to_numpy(int)
    atr = d["ATR"].to_numpy(float)

    equity = 10000.0
    peak = equity
    max_dd = 0.0
    wins = losses = 0
    gross_profit = gross_loss = total_r = 0.0
    holds: list[int] = []
    rs: list[float] = []
    position = 0
    entry_i = -1
    entry_price = stop = target = risk_distance = 0.0

    for i in range(len(d) - 1):
        if position == 0:
            if trade_start is not None and d.index[i] < trade_start:
                continue
            if signal[i] not in (-1, 1) or not np.isfinite(atr[i]) or atr[i] <= 0:
                continue

            # Signal is read from the fully closed bar i; fill is bar i+1 open.
            position = int(signal[i])
            entry_i = i + 1
            risk_distance = float(params["atr_mult"]) * float(atr[i])
            entry_price = apply_entry_cost(open_px[entry_i], position, cfg)
            stop = entry_price - position * risk_distance
            target = entry_price + position * float(params["rr"]) * risk_distance
            # The first holding bar is the actual fill bar, evaluated on the
            # next loop iteration (i == entry_i).
            continue

        # Once a position exists, i is the actual holding bar. This includes
        # the fill bar itself and never evaluates pre-entry candles.
        if i < entry_i:
            continue

        age = i - entry_i + 1
        hit_sl = (low[i] <= stop) if position == 1 else (high[i] >= stop)
        hit_tp = (high[i] >= target) if position == 1 else (low[i] <= target)

        reason: str | None = None
        exit_raw: float | None = None

        if hit_sl and hit_tp:
            exit_raw = stop
            reason = "same_bar_sl_first"
        elif hit_sl:
            exit_raw = stop
            reason = "sl"
        elif hit_tp:
            exit_raw = target
            reason = "tp"
        elif signal[i] == -position:
            if i + 1 >= len(d):
                continue
            exit_raw = open_px[i + 1]
            reason = "opposite_next_open"
        elif age >= cfg.expiry_bars:
            if i + 1 >= len(d):
                continue
            exit_raw = open_px[i + 1]
            reason = "expiry_next_open"

        if reason is None or exit_raw is None:
            continue

        exit_price = apply_exit_cost(exit_raw, position, cfg)
        r = float(position * (exit_price - entry_price) / risk_distance)
        rs.append(r)
        total_r += r
        holds.append(age)

        if r > 0:
            wins += 1
            gross_profit += r
        else:
            losses += 1
            gross_loss += abs(r)

        equity *= 1.0 + r * risk_fraction
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
        position = 0
        entry_i = -1

    n_trades = wins + losses
    pf = gross_profit / gross_loss if gross_loss else (3.0 if n_trades else 0.0)
    metrics = {
        "symbol": symbol,
        "trades": n_trades,
        "win_rate_pct": round(100.0 * wins / n_trades, 3) if n_trades else 0.0,
        "expectancy_R": round(total_r / n_trades, 5) if n_trades else 0.0,
        "total_R": round(total_r, 3),
        "profit_factor": round(pf, 4),
        "final_equity": round(equity, 2),
        "max_dd_pct": round(100.0 * max_dd, 3),
        "avg_hold_bars": round(float(np.mean(holds)), 3) if holds else 0.0,
        "round_trip_cost_pips": cfg.round_trip_cost_pips,
        "entries_equal_exits": position == 0,
        "next_bar_open_entry": True,
        "actual_entry_price_for_stops": True,
        "adverse_exit_cost_applied": True,
        "same_bar_sl_first": True,
        "one_position_at_a_time": True,
        "open_position_at_end": position != 0,
    }
    return metrics, rs
