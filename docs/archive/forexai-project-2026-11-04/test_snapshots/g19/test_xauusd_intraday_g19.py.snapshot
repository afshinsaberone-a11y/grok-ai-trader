from __future__ import annotations

import pandas as pd
import pytest

from research.optimization import xauusd_intraday_g19 as g19


def frame_with_signals(timestamps, signals, *, gap_after=None):
    timestamps = pd.DatetimeIndex(timestamps)
    n = len(timestamps)
    bid_open = [2000.0] * n
    ask_open = [2000.2] * n
    bid_high = [2002.0] * n
    ask_high = [2002.2] * n
    bid_low = [1998.0] * n
    ask_low = [1998.2] * n
    bid_close = [2000.0] * n
    ask_close = [2000.2] * n
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "bid_open": bid_open,
        "ask_open": ask_open,
        "bid_high": bid_high,
        "ask_high": ask_high,
        "bid_low": bid_low,
        "ask_low": ask_low,
        "bid_close": bid_close,
        "ask_close": ask_close,
        "signal": signals,
        "ATR": [2.0] * n,
    })
    frame["server_time"] = frame["timestamp"].dt.tz_convert(g19.SERVER_TIMEZONE)
    frame["server_date"] = frame["server_time"].dt.date
    frame["server_hour"] = frame["server_time"].dt.hour
    return frame


def run_with_frame(monkeypatch, frame, *, slippage=0.05):
    monkeypatch.setattr(g19, "make_signals", lambda bars, spec: frame.copy())
    return g19.run_intraday_scenario(
        frame,
        slippage_usd_per_oz_per_side=slippage,
        commission_usd_per_oz_round_turn=0.08,
    )


def test_position_is_force_closed_at_23_server_time_before_rollover(monkeypatch):
    # Winter broker time is UTC+2: 21:00 UTC == 23:00 server time.
    times = pd.date_range("2024-01-02T18:00:00Z", periods=5, freq="h")
    frame = frame_with_signals(times, [1, 0, 0, 0, 0])
    report = run_with_frame(monkeypatch, frame)

    trades = report["trades"]
    assert len(trades) == 1
    assert trades[0]["entry_server_hour"] == 21
    assert trades[0]["exit_server_hour"] == 23
    assert trades[0]["exit_reason"] == "pre_rollover_flatten"
    assert trades[0]["entry_server_date"] == trades[0]["exit_server_date"]
    assert trades[0]["financing_usd_per_oz"] == 0.0
    assert trades[0]["commission_usd_per_oz_round_turn"] == 0.08
    assert trades[0]["intraday_no_rollover_rule_satisfied"] is True


def test_new_position_is_not_opened_at_rollover_flatten_hour(monkeypatch):
    times = pd.date_range("2024-01-02T20:00:00Z", periods=3, freq="h")
    # 21:00 UTC == 23:00 server time in winter.
    frame = frame_with_signals(times, [1, 0, 0])
    report = run_with_frame(monkeypatch, frame)
    assert report["trades"] == []


def test_position_is_closed_at_last_observed_close_before_data_gap(monkeypatch):
    # Entry at 10:00 server, then a two-hour missing interval.
    times = pd.DatetimeIndex([
        "2024-01-02T07:00:00Z",  # 09:00 server
        "2024-01-02T08:00:00Z",  # 10:00 server; entry
        "2024-01-02T10:00:00Z",  # 12:00 server; gap > 1h
        "2024-01-02T11:00:00Z",
    ]).tz_convert("UTC")
    frame = frame_with_signals(times, [1, 0, 0, 0])
    report = run_with_frame(monkeypatch, frame)

    trades = report["trades"]
    assert len(trades) == 1
    assert trades[0]["exit_reason"] == "data_gap_flatten"
    assert trades[0]["exit_time_precision"] == "h1_bar_close"
    assert trades[0]["entry_server_date"] == trades[0]["exit_server_date"]
    assert trades[0]["financing_usd_per_oz"] == 0.0


def test_same_server_date_and_rollover_assertions_are_true_for_empty_sample(monkeypatch):
    times = pd.date_range("2024-01-02T00:00:00Z", periods=4, freq="h")
    frame = frame_with_signals(times, [0, 0, 0, 0])
    report = run_with_frame(monkeypatch, frame)
    stats = report["discovery_2021_2023"]
    assert stats["trades"] == 0
    assert stats["all_trades_same_server_date"] is True
    assert stats["all_trades_flat_before_rollover"] is True


def test_invalid_slippage_is_rejected():
    with pytest.raises(g19.G19Error, match="SLIPPAGE_INPUT_INVALID"):
        g19.run_intraday_scenario(pd.DataFrame(), slippage_usd_per_oz_per_side=-0.01)
