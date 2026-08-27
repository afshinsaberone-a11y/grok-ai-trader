from __future__ import annotations

import numpy as np
import pandas as pd

from research.optimization.cost_aware_discovery import backtest_cost_aware


def _bars(n: int = 240) -> pd.DataFrame:
    ts = pd.date_range("2022-01-01", periods=n, freq="5min", tz="UTC")
    # Deterministic real-shape test fixture: monotonic OHLC is only used to test
    # accounting invariants, never as research/backtest market data.
    close = 1.1000 + np.arange(n, dtype=float) * 0.00001
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 0.00005,
            "Low": close - 0.00005,
            "Close": close,
            "Volume": np.ones(n),
        },
        index=ts,
    )


def _params() -> dict[str, float]:
    return {"atr_period": 14, "atr_stop": 1.5, "rr": 2.0}


def test_round_trip_cost_formula_is_two_sides():
    df = _bars()
    zero = backtest_cost_aware(df, "trend_ema_rsi", _params(), spread_pips=0, slippage_pips=0)
    paid = backtest_cost_aware(df, "trend_ema_rsi", _params(), spread_pips=0.5, slippage_pips=0.2)
    assert zero["round_trip_cost_pips"] == 0.0
    assert paid["round_trip_cost_pips"] == 1.4


def test_execution_cost_cannot_improve_total_r():
    df = _bars()
    free = backtest_cost_aware(df, "trend_ema_rsi", _params(), spread_pips=0, slippage_pips=0)
    paid = backtest_cost_aware(df, "trend_ema_rsi", _params(), spread_pips=0.5, slippage_pips=0.2)
    assert paid["total_R"] <= free["total_R"]
    assert paid["final_equity"] <= free["final_equity"]


def test_negative_execution_cost_is_rejected():
    df = _bars()
    try:
        backtest_cost_aware(df, "trend_ema_rsi", _params(), spread_pips=-0.1, slippage_pips=0)
    except ValueError as exc:
        assert "costs cannot be negative" in str(exc)
    else:
        raise AssertionError("negative execution cost must fail closed")
