import numpy as np
import pandas as pd

from research.optimization.cost_aware_discovery import backtest_cost_aware


def _fixture() -> pd.DataFrame:
    n = 240
    idx = pd.date_range("2022-01-01", periods=n, freq="min", tz="UTC")
    close = 1.10 + 0.0002 * np.sin(np.arange(n) / 7.0)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close + 0.0003,
            "Low": close - 0.0003,
            "Close": close,
            "Volume": np.ones(n),
        },
        index=idx,
    )


def test_optimized_backtest_is_deterministic():
    df = _fixture()
    params = {"atr_stop": 1.5, "rr": 2.0}
    first = backtest_cost_aware(df, "trend_ema_rsi", params, spread_pips=0.5, slippage_pips=0.2)
    second = backtest_cost_aware(df, "trend_ema_rsi", params, spread_pips=0.5, slippage_pips=0.2)
    assert first == second


def test_optimized_backtest_output_schema_and_cost_are_stable():
    df = _fixture()
    params = {"atr_stop": 1.5, "rr": 2.0}
    result = backtest_cost_aware(df, "trend_ema_rsi", params, spread_pips=0.5, slippage_pips=0.2)
    assert result["round_trip_cost_pips"] == 1.4
    assert result["spread_pips"] == 0.5
    assert result["slippage_pips"] == 0.2
    assert set(result) >= {
        "trades",
        "win_rate",
        "total_R",
        "expectancy_R",
        "profit_factor",
        "max_dd_pct",
        "final_equity",
        "round_trip_cost_pips",
    }
