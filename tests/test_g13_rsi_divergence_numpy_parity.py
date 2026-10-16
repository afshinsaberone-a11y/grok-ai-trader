"""Semantics-only regression tests for the NumPy row-access optimization.

The deterministic generated frame below is a unit-test fixture only. It is not
research evidence, is not used to select candidates, and is never uploaded as
a backtest or trading artifact.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.optimization.execution_contract_v1 import (
    ExecutionConfig,
    apply_entry_cost,
    apply_exit_cost,
)
from research.optimization.rsi_divergence_discovery_g13 import (
    MAX_HOLD,
    pivots,
    prep,
    signals,
    trade_returns,
)


def _fixture() -> pd.DataFrame:
    """Return deterministic OHLC rows used only to compare implementation semantics."""
    rng = np.random.default_rng(13713)
    n = 3600
    timestamps = pd.date_range("2023-01-01", periods=n, freq="15min", tz="UTC")
    close = 1.10 + np.cumsum(rng.normal(0.0, 0.00022, size=n))
    open_ = np.concatenate(([close[0]], close[:-1]))
    upper = rng.uniform(0.00004, 0.00028, size=n)
    lower = rng.uniform(0.00004, 0.00028, size=n)
    high = np.maximum(open_, close) + upper
    low = np.minimum(open_, close) - lower
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    })


def _legacy_signals(d: pd.DataFrame, p: dict) -> pd.Series:
    """Reference implementation using the pre-optimization pandas .iloc access."""
    ph, pl = pivots(d, p["pivot"])
    out = pd.Series(0, index=d.index, dtype=int)
    highs = []
    lows = []
    for i in range(p["pivot"], len(d) - p["pivot"]):
        if not (np.isfinite(d.RSI14.iloc[i]) and np.isfinite(d.ATR14.iloc[i])):
            continue
        pi = i - p["pivot"]
        if ph.iloc[pi]:
            highs.append((pi, float(d.High.iloc[pi]), float(d.RSI14.iloc[pi])))
        if pl.iloc[pi]:
            lows.append((pi, float(d.Low.iloc[pi]), float(d.RSI14.iloc[pi])))
        if p["side"] == "short" and len(highs) >= 2:
            a, b = highs[-2], highs[-1]
            if b[1] > a[1] + p["min_delta"] and b[2] < a[2] and b[2] >= p["rsi_high"]:
                out.iloc[i] = -1
        if p["side"] == "long" and len(lows) >= 2:
            a, b = lows[-2], lows[-1]
            if b[1] < a[1] - p["min_delta"] and b[2] > a[2] and b[2] <= p["rsi_low"]:
                out.iloc[i] = 1
    return out


def _legacy_trade_returns(d: pd.DataFrame, p: dict) -> list[float]:
    """Reference execution loop before replacing pandas row access with arrays."""
    if len(d) < 100:
        return []
    sig = _legacy_signals(d, p)
    cfg = ExecutionConfig()
    returns = []
    pos = None
    for i in range(1, len(d)):
        if pos is not None:
            h, low = float(d.High.iloc[i]), float(d.Low.iloc[i])
            age = i - pos["entry_i"]
            slhit = low <= pos["sl"] if pos["side"] == 1 else h >= pos["sl"]
            tphit = h >= pos["tp"] if pos["side"] == 1 else low <= pos["tp"]
            opposite = bool(sig.iloc[i] == -pos["side"])
            if slhit or tphit or opposite or age >= MAX_HOLD:
                raw = pos["sl"] if slhit else pos["tp"] if tphit else float(d.Close.iloc[i])
                exit_price = apply_exit_cost(raw, pos["side"], cfg)
                returns.append(float(
                    (exit_price - pos["entry"]) / (pos["entry"] - pos["sl"]) * pos["side"]
                ))
                pos = None
        if pos is None and bool(sig.iloc[i - 1]):
            side = int(sig.iloc[i - 1])
            entry = apply_entry_cost(float(d.Open.iloc[i]), side, cfg)
            atr = float(d.ATR14.iloc[i - 1])
            if not np.isfinite(atr) or atr <= 0:
                continue
            risk = p["atr_mult"] * atr
            sl = entry - side * risk
            tp = entry + side * p["rr"] * risk
            pos = {"entry_i": i, "side": side, "entry": entry, "sl": sl, "tp": tp}
    if pos is not None:
        exit_price = apply_exit_cost(float(d.Close.iloc[-1]), pos["side"], cfg)
        returns.append(float(
            (exit_price - pos["entry"]) / (pos["entry"] - pos["sl"]) * pos["side"]
        ))
    return returns


PARAMETERS = (
    {
        "pivot": 3, "rsi_low": 30, "rsi_high": 70, "min_delta": 0.0003,
        "atr_mult": 1.0, "rr": 1.5, "side": "short",
    },
    {
        "pivot": 5, "rsi_low": 35, "rsi_high": 65, "min_delta": 0.0005,
        "atr_mult": 1.5, "rr": 2.0, "side": "long",
    },
    {
        "pivot": 8, "rsi_low": 30, "rsi_high": 70, "min_delta": 0.0003,
        "atr_mult": 1.2, "rr": 1.8, "side": "short",
    },
)


def test_numpy_signal_path_matches_legacy_pandas_path_exactly():
    data = prep(_fixture())
    for params in PARAMETERS:
        actual = signals(data, params)
        expected = _legacy_signals(data, params)
        pd.testing.assert_series_equal(actual, expected, check_exact=True)


def test_numpy_trade_returns_match_legacy_execution_path_exactly():
    data = prep(_fixture())
    for params in PARAMETERS:
        actual = trade_returns(data, params)
        expected = _legacy_trade_returns(data, params)
        assert actual == expected


def test_short_history_still_returns_no_trades():
    data = prep(_fixture().iloc[:80].copy())
    params = PARAMETERS[0]
    assert trade_returns(data, params) == []
    assert _legacy_trade_returns(data, params) == []
