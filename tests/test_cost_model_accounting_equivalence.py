from __future__ import annotations

import pandas as pd
import pytest

from research.optimization.cost_aware_discovery import (
    backtest_cost_aware,
    round_trip_cost_price,
)


def _bars() -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=80, freq="5min", tz="UTC")
    close = [1.1000 + 0.0001 * (i % 10) for i in range(len(idx))]
    return pd.DataFrame(
        {
            "Open": close,
            "High": [x + 0.0005 for x in close],
            "Low": [x - 0.0005 for x in close],
            "Close": close,
            "Volume": [1000] * len(idx),
        },
        index=idx,
    )


def test_round_trip_cost_is_two_sided():
    assert round_trip_cost_price(0.5, 0.2) == pytest.approx(0.00014)


def test_zero_cost_cannot_be_worse_due_to_execution_costs():
    df = _bars()
    params = {"atr_period": 14, "atr_stop": 1.5, "rr": 2.0}
    free = backtest_cost_aware(df, "momentum_breakout", params, spread_pips=0.0, slippage_pips=0.0)
    costly = backtest_cost_aware(df, "momentum_breakout", params, spread_pips=0.5, slippage_pips=0.2)
    assert costly["trades"] == free["trades"]
    assert costly["total_R"] <= free["total_R"] + 1e-9
    assert costly["final_equity"] <= free["final_equity"] + 1e-9


def test_negative_execution_costs_fail_closed():
    with pytest.raises(ValueError, match="execution costs cannot be negative"):
        backtest_cost_aware(_bars(), "momentum_breakout", {"atr_period": 14, "atr_stop": 1.5, "rr": 2.0}, spread_pips=-0.1, slippage_pips=0.0)
