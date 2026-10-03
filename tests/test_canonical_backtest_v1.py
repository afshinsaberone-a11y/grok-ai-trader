"""Contract tests for the canonical execution kernel.

These fixtures validate software semantics only. They are not market-data
performance evidence and are never used by research or promotion workflows.
"""
import pandas as pd

from research.optimization.canonical_backtest_v1 import run_canonical_backtest


def _provider(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ATR"] = 1.0
    out["signal"] = 0
    return out


def test_entry_bar_is_evaluated_and_stop_is_anchored_to_actual_fill():
    idx = pd.date_range("2025-01-01", periods=4, freq="min", tz="UTC")
    df = pd.DataFrame(
        {
            "Open": [100.0, 100.0, 100.0, 100.0],
            "High": [100.1, 100.1, 100.1, 100.1],
            "Low": [99.9, 98.0, 100.0, 100.0],
            "Close": [100.0, 100.0, 100.0, 100.0],
        },
        index=idx,
    )

    def provider(value):
        out = _provider(value)
        out.loc[idx[0], "signal"] = 1
        return out

    metrics, rs = run_canonical_backtest(
        df,
        {"atr_mult": 1.0, "rr": 2.0},
        provider,
        risk_fraction=0.005,
    )
    assert metrics["trades"] == 1
    assert metrics["entries_equal_exits"] is True
    assert rs[0] < 0


def test_same_bar_sl_first_is_deterministic():
    idx = pd.date_range("2025-01-01", periods=3, freq="min", tz="UTC")
    df = pd.DataFrame(
        {
            "Open": [100.0, 100.0, 100.0],
            "High": [100.1, 102.0, 100.1],
            "Low": [99.9, 98.0, 99.9],
            "Close": [100.0, 100.0, 100.0],
        },
        index=idx,
    )

    def provider(value):
        out = _provider(value)
        out.loc[idx[0], "signal"] = 1
        return out

    metrics, rs = run_canonical_backtest(df, {"atr_mult": 1.0, "rr": 2.0}, provider)
    assert metrics["trades"] == 1
    assert rs[0] < 0


def test_no_trade_without_a_valid_signal_or_atr():
    idx = pd.date_range("2025-01-01", periods=2, freq="min", tz="UTC")
    df = pd.DataFrame(
        {
            "Open": [100.0, 100.0],
            "High": [100.0, 100.0],
            "Low": [100.0, 100.0],
            "Close": [100.0, 100.0],
        },
        index=idx,
    )
    metrics, rs = run_canonical_backtest(df, {"atr_mult": 1.0, "rr": 2.0}, _provider)
    assert metrics["trades"] == 0
    assert rs == []
