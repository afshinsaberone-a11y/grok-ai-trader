from __future__ import annotations

import pandas as pd
import pytest

from research.optimization import xauusd_opening_range_g20 as g20


def fixture_bars(times, *, high=None, low=None, close=None):
    n = len(times)
    bid_open = [2000.0] * n
    ask_open = [2000.2] * n
    bid_high = [2001.0] * n if high is None else high
    ask_high = [value + 0.2 for value in bid_high]
    bid_low = [1999.0] * n if low is None else low
    ask_low = [value + 0.2 for value in bid_low]
    bid_close = [2000.0] * n if close is None else close
    ask_close = [value + 0.2 for value in bid_close]
    return pd.DataFrame({
        "timestamp": pd.DatetimeIndex(times),
        "bid_open": bid_open, "ask_open": ask_open,
        "bid_high": bid_high, "ask_high": ask_high,
        "bid_low": bid_low, "ask_low": ask_low,
        "bid_close": bid_close, "ask_close": ask_close,
        "spread_open": [0.2] * n, "spread_close": [0.2] * n,
    })


def test_only_complete_contiguous_opening_range_is_accepted():
    # 00:00–06:00 server time maps to 22:00–04:00 UTC in winter.
    times = pd.date_range("2024-01-01T22:00:00Z", periods=9, freq="h")
    bars = fixture_bars(times)
    prepared = g20.prepare_ranges(bars)
    assert prepared.loc[7, "range_high"] == pytest.approx(2001.1)
    assert prepared.loc[7, "range_low"] == pytest.approx(1999.1)


def test_missing_opening_range_hour_disables_that_day():
    times = pd.date_range("2024-01-01T22:00:00Z", periods=9, freq="h").delete(3)
    bars = fixture_bars(times)
    prepared = g20.prepare_ranges(bars)
    assert prepared["range_high"].isna().all()
    assert prepared["range_low"].isna().all()


def test_long_breakout_uses_ask_entry_and_charges_roundturn_cost():
    times = pd.date_range("2024-01-01T22:00:00Z", periods=11, freq="h")
    high = [2001.0] * 11
    low = [1999.0] * 11
    close = [2000.0] * 11
    close[7] = 2002.0  # 07:00 server bar closes above range.
    high[8] = 2006.0
    low[8] = 2000.5
    bars = fixture_bars(times, high=high, low=low, close=close)
    report = g20.run_scenario(bars, slippage_usd_per_oz_per_side=0.05)
    assert len(report["trades"]) == 1
    trade = report["trades"][0]
    assert trade["side"] == "LONG"
    assert trade["entry_server_hour"] == 8
    assert trade["entry_fill"] == pytest.approx(2000.25)
    assert trade["exit_reason"] == "entry_bar_target"
    assert trade["financing_usd_per_oz"] == 0.0
    assert trade["commission_fee_usd_per_oz_round_turn"] == 0.08
    assert trade["spread_double_charged"] is False


def test_same_bar_stop_and_target_resolves_stop_first():
    times = pd.date_range("2024-01-01T22:00:00Z", periods=11, freq="h")
    high = [2001.0] * 11
    low = [1999.0] * 11
    close = [2000.0] * 11
    close[7] = 2002.0
    high[8] = 2006.0
    low[8] = 1990.0
    bars = fixture_bars(times, high=high, low=low, close=close)
    report = g20.run_scenario(bars, slippage_usd_per_oz_per_side=0.05)
    assert len(report["trades"]) == 1
    assert report["trades"][0]["exit_reason"] == "entry_bar_same_bar_stop_first"
    assert report["trades"][0]["net_r"] < 0


def test_trades_never_cross_rollover_or_server_date():
    times = pd.date_range("2024-01-01T22:00:00Z", periods=26, freq="h")
    high = [2001.0] * len(times)
    low = [1999.0] * len(times)
    close = [2000.0] * len(times)
    close[7] = 2002.0
    bars = fixture_bars(times, high=high, low=low, close=close)
    report = g20.run_scenario(bars, slippage_usd_per_oz_per_side=0.05)
    for trade in report["trades"]:
        assert trade["entry_server_date"] == trade["exit_server_date"]
        assert trade["exit_server_hour"] <= 23
        assert trade["intraday_no_rollover_rule_satisfied"]


def test_invalid_cost_inputs_fail_closed():
    with pytest.raises(g20.G20Error, match="SLIPPAGE_INVALID"):
        g20.run_scenario(pd.DataFrame(), slippage_usd_per_oz_per_side=-0.1)
