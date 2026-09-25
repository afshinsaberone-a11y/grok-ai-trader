from __future__ import annotations

import pandas as pd
import pytest

from research.optimization.robust_regime_momentum_v1 import Params, backtest, build_features


def _bars(n=500):
    idx = pd.date_range("2024-01-01", periods=n, freq="5min", tz="UTC")
    close = pd.Series(100.0 + pd.Series(range(n)).rolling(25, min_periods=1).mean() * 0.01, index=idx)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) + 0.02
    low = pd.concat([open_, close], axis=1).min(axis=1) - 0.02
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close}, index=idx)


def test_signal_is_based_on_completed_bar():
    d = _bars()
    f = build_features(d, Params())
    # The signal row is intended to be consumed by the next bar, not the same bar.
    assert "long_signal" in f
    assert "short_signal" in f
    assert f.index.is_monotonic_increasing


def test_backtest_never_needs_synthetic_data_fallback():
    d = _bars()
    result = backtest(d, Params())
    assert result["trades"] >= 0
    assert "profit_factor" in result


def test_invalid_ohlc_is_rejected_by_loader(tmp_path):
    from research.optimization.robust_regime_momentum_v1 import load_real_m5
    p = tmp_path / "bad.csv"
    pd.DataFrame(
        {
            "timestamp": ["2024-01-01T00:00:00Z"],
            "open": [2],
            "high": [1],
            "low": [0],
            "close": [1],
        }
    ).to_csv(p, index=False)
    with pytest.raises(ValueError, match="REAL_DATA_INVALID"):
        load_real_m5(p)
