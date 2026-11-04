from __future__ import annotations

import pandas as pd
import pytest

from research.optimization import xauusd_volatility_momentum_g21 as g21


def execution_frame(times, signals, *, bid_open=None, bid_high=None, bid_low=None, bid_close=None):
    n = len(times)
    bid_open = [2000.0] * n if bid_open is None else bid_open
    bid_high = [2001.0] * n if bid_high is None else bid_high
    bid_low = [1999.0] * n if bid_low is None else bid_low
    bid_close = [2000.0] * n if bid_close is None else bid_close
    ask_open = [v + 0.20 for v in bid_open]
    ask_high = [v + 0.20 for v in bid_high]
    ask_low = [v + 0.20 for v in bid_low]
    ask_close = [v + 0.20 for v in bid_close]
    frame = pd.DataFrame({
        "timestamp": pd.DatetimeIndex(times),
        "bid_open": bid_open, "bid_high": bid_high,
        "bid_low": bid_low, "bid_close": bid_close,
        "ask_open": ask_open, "ask_high": ask_high,
        "ask_low": ask_low, "ask_close": ask_close,
        "signal": signals, "atr": [2.0] * n,
    })
    server = frame["timestamp"].dt.tz_convert(g21.SERVER_TIMEZONE)
    frame["server_time"] = server
    frame["server_date"] = server.dt.date
    frame["server_hour"] = server.dt.hour
    return frame


def run_frame(monkeypatch, frame, slippage=0.05):
    monkeypatch.setattr(g21, "make_signals", lambda bars, spec: frame.copy())
    return g21.run_scenario(
        frame,
        slippage_usd_per_oz_per_side=slippage,
        commission_usd_per_oz_round_turn=0.08,
    )


def test_long_uses_ask_entry_bid_exit_and_roundturn_fee(monkeypatch):
    times = pd.date_range("2024-01-02T06:00:00Z", periods=4, freq="h")
    highs = [2001.0, 2012.0, 2002.0, 2002.0]
    lows = [1999.0, 1999.0, 1999.0, 1999.0]
    frame = execution_frame(times, [1, 0, 0, 0], bid_high=highs, bid_low=lows)
    report = run_frame(monkeypatch, frame)
    assert len(report["trades"]) == 1
    trade = report["trades"][0]
    assert trade["side"] == "LONG"
    assert trade["entry_fill"] == pytest.approx(2000.25)
    assert trade["exit_reason"] == "entry_bar_target"
    assert trade["commission_fee_usd_per_oz_round_turn"] == pytest.approx(0.08)
    assert trade["financing_usd_per_oz"] == 0.0
    assert trade["spread_double_charged"] is False


def test_short_uses_bid_entry_ask_exit(monkeypatch):
    times = pd.date_range("2024-01-02T06:00:00Z", periods=4, freq="h")
    highs = [2001.0, 2001.0, 2001.0, 2001.0]
    lows = [1999.0, 1988.0, 1999.0, 1999.0]
    frame = execution_frame(times, [-1, 0, 0, 0], bid_high=highs, bid_low=lows)
    report = run_frame(monkeypatch, frame)
    assert len(report["trades"]) == 1
    trade = report["trades"][0]
    assert trade["side"] == "SHORT"
    assert trade["entry_fill"] == pytest.approx(1999.95)
    assert trade["exit_reason"] == "entry_bar_target"
    assert trade["spread_double_charged"] is False


def test_same_bar_stop_and_target_resolves_stop_first(monkeypatch):
    times = pd.date_range("2024-01-02T06:00:00Z", periods=4, freq="h")
    frame = execution_frame(
        times, [1, 0, 0, 0],
        bid_high=[2001.0, 2012.0, 2001.0, 2001.0],
        bid_low=[1999.0, 1990.0, 1999.0, 1999.0],
    )
    report = run_frame(monkeypatch, frame)
    assert len(report["trades"]) == 1
    assert report["trades"][0]["exit_reason"] == "entry_bar_same_bar_stop_first"
    assert report["trades"][0]["net_r"] < 0


def test_position_is_flattened_at_22_server_open(monkeypatch):
    # UTC 19:00 is 21:00 server in winter; UTC 20:00 is 22:00 server.
    times = pd.date_range("2024-01-02T17:00:00Z", periods=7, freq="h")
    frame = execution_frame(times, [1, 0, 0, 0, 0, 0, 0])
    report = run_frame(monkeypatch, frame)
    trades = report["trades"]
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "pre_rollover_flatten"
    assert trades[0]["exit_server_hour"] == 22
    assert trades[0]["entry_server_date"] == trades[0]["exit_server_date"]


def test_new_entry_is_not_allowed_at_or_after_flatten_hour(monkeypatch):
    # UTC 20:00 == 22:00 server time in winter.
    times = pd.date_range("2024-01-02T19:00:00Z", periods=3, freq="h")
    frame = execution_frame(times, [1, 0, 0])
    report = run_frame(monkeypatch, frame)
    assert report["trades"] == []


def test_position_flattens_at_last_close_before_data_gap(monkeypatch):
    times = pd.DatetimeIndex([
        "2024-01-02T06:00:00Z",  # 08:00 server
        "2024-01-02T07:00:00Z",  # 09:00 server entry
        "2024-01-02T10:00:00Z",  # gap to 12:00 server
        "2024-01-02T11:00:00Z",
    ])
    frame = execution_frame(times, [1, 0, 0, 0])
    report = run_frame(monkeypatch, frame)
    assert len(report["trades"]) == 1
    trade = report["trades"][0]
    assert trade["exit_reason"] == "data_gap_flatten"
    assert trade["exit_time_precision"] == "h1_bar_close"
    assert trade["entry_server_date"] == trade["exit_server_date"]


def test_indicator_signals_are_causal_and_future_bars_do_not_change_past():
    n = 180
    times = pd.date_range("2024-01-01T00:00:00Z", periods=n, freq="h")
    close = [2000.0 + 0.08 * i + (2.0 if i % 7 < 3 else -1.0) for i in range(n)]
    bid_open = [x - 0.15 for x in close]
    bid_high = [x + 0.8 for x in close]
    bid_low = [x - 0.8 for x in close]
    ask_open = [x + 0.05 for x in bid_open]
    ask_high = [x + 0.2 for x in bid_high]
    ask_low = [x + 0.2 for x in bid_low]
    ask_close = [x + 0.2 for x in close]
    bars = pd.DataFrame({
        "timestamp": times,
        "bid_open": bid_open, "bid_high": bid_high, "bid_low": bid_low, "bid_close": close,
        "ask_open": ask_open, "ask_high": ask_high, "ask_low": ask_low, "ask_close": ask_close,
    })
    full = g21.make_signals(bars)
    cut = 145
    altered = bars.copy()
    altered.loc[cut:, ["bid_open", "bid_high", "bid_low", "bid_close"]] += 500.0
    altered.loc[cut:, ["ask_open", "ask_high", "ask_low", "ask_close"]] += 500.0
    changed = g21.make_signals(altered)
    pd.testing.assert_series_equal(full.loc[:cut-1, "signal"], changed.loc[:cut-1, "signal"])
    pd.testing.assert_series_equal(full.loc[:cut-1, "atr"], changed.loc[:cut-1, "atr"])


def test_invalid_cost_inputs_fail_closed():
    with pytest.raises(g21.G21Error, match="SLIPPAGE_INVALID"):
        g21.run_scenario(pd.DataFrame(), slippage_usd_per_oz_per_side=-0.01)
