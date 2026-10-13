from __future__ import annotations

import numpy as np
import pandas as pd

from research.optimization.cost_aware_adaptive_regime_switch_v25 import bt


def _daily_bars(*, touch_both_on_final_bar: bool = False) -> pd.DataFrame:
    index = pd.date_range("2024-03-04 00:00:00", periods=70, freq="5min", tz="UTC", name="Timestamp")
    data = pd.DataFrame(
        {
            "Open": np.full(len(index), 1.0),
            "High": np.full(len(index), 1.0002),
            "Low": np.full(len(index), 0.9998),
            "Close": np.full(len(index), 1.0),
            "ATR": np.full(len(index), 0.001),
            "ADX": np.full(len(index), 10.0),
            "RSI": np.full(len(index), 20.0),
            "EMA20": np.full(len(index), 1.001),
            "EMA50": np.full(len(index), 1.002),
        },
        index=index,
    )
    data["day"] = data.index.date
    if touch_both_on_final_bar:
        data.iloc[-1, data.columns.get_loc("High")] = 1.002
        data.iloc[-1, data.columns.get_loc("Low")] = 0.998
    return data


PARAMS = {
    "lookback": 12,
    "adx_threshold": 18,
    "atr_stop": 1.0,
    "rr": 1.5,
    "rsi_low": 25,
    "rsi_high": 70,
    "mode": "adaptive",
}


def test_open_trade_is_realized_at_daily_boundary_and_counts_match() -> None:
    result = bt(_daily_bars(), PARAMS)

    assert result["entries"] == 1
    assert result["exits"] == 1
    assert result["trades"] == 1
    assert result["entries_equal_exits"] is True
    # At day close: raw close=1.0, then one adverse exit cost of 0.7 pip.
    assert result["total_R"] == -0.14


def test_final_bar_both_sl_and_tp_touched_resolves_sl_first() -> None:
    result = bt(_daily_bars(touch_both_on_final_bar=True), PARAMS)

    assert result["entries"] == 1
    assert result["exits"] == 1
    assert result["entries_equal_exits"] is True
    # Long stop is 0.99907; exit cost moves the stop fill to 0.99900.
    assert result["total_R"] == -1.07
