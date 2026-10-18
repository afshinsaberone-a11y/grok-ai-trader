"""Tests for the G13 robustness run-local return cache.

This verifies memoization only; it creates no market metrics, strategy evidence,
candidate ranking or trading artifacts.
"""
from __future__ import annotations

import pandas as pd

import research.optimization.g13_robustness_m15 as robustness


def test_returns_cache_reuses_exact_year_and_canonical_parameters(monkeypatch):
    calls = []

    def fake_trade_returns(frame: pd.DataFrame, params: dict) -> list[float]:
        year = int(frame.iloc[0]["year"])
        calls.append((year, robustness.canonical_hash(params)))
        return [float(year), float(params["pivot"])]

    monkeypatch.setattr(robustness, "trade_returns", fake_trade_returns)
    years_data = {
        2022: pd.DataFrame({"year": [2022]}),
        2023: pd.DataFrame({"year": [2023]}),
    }
    cached_returns, cache = robustness._make_returns_cache(years_data)

    p_a = {"pivot": 3, "side": "short"}
    p_a_reordered = {"side": "short", "pivot": 3}
    p_b = {"pivot": 5, "side": "short"}

    first = cached_returns(2022, p_a)
    repeated = cached_returns(2022, p_a_reordered)
    other_year = cached_returns(2023, p_a)
    other_params = cached_returns(2022, p_b)

    assert first == repeated == [2022.0, 3.0]
    assert other_year == [2023.0, 3.0]
    assert other_params == [2022.0, 5.0]
    assert len(calls) == 3
    assert len(cache) == 3
