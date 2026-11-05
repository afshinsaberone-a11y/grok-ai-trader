from __future__ import annotations

import pandas as pd
import pytest

from research.optimization.xauusd_execution_contract_v1 import (
    XAUUSDExecutionConfig,
    XAUUSDExecutionError,
    run_xauusd_backtest,
)


def bars_fixture() -> pd.DataFrame:
    # Small deterministic execution fixture only; not market-performance data.
    return pd.DataFrame({
        "timestamp": pd.date_range("2024-01-08T10:00:00Z", periods=4, freq="h"),
        "bid_open":  [2000.0, 2000.0, 2001.0, 2003.0],
        "bid_high":  [2001.0, 2002.0, 2008.0, 2004.0],
        "bid_low":   [1999.0, 1999.0, 2000.0, 2002.0],
        "bid_close": [2000.5, 2001.0, 2006.0, 2003.5],
        "ask_open":  [2000.3, 2000.3, 2001.3, 2003.3],
        "ask_high":  [2001.3, 2002.3, 2008.3, 2004.3],
        "ask_low":   [1999.3, 1999.3, 2000.3, 2002.3],
        "ask_close": [2000.8, 2001.3, 2006.3, 2003.8],
        "signal":    [1, 0, 0, 0],
        "ATR":       [2.0, 2.0, 2.0, 2.0],
        "financing_long_usd_per_oz": [0.0, 0.02, 0.03, 0.0],
        "financing_short_usd_per_oz": [0.0, -0.01, -0.02, 0.0],
    })


def config() -> XAUUSDExecutionConfig:
    return XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        atr_stop_mult=1.5,
        reward_risk=2.5,
        risk_fraction=0.0025,
        max_holding_bars=30,
    )


def test_long_uses_ask_entry_bid_exit_and_charges_explicit_costs_once() -> None:
    metrics, trades = run_xauusd_backtest(bars_fixture(), config())

    assert metrics["trades"] == 1
    assert metrics["entries_equal_exits"] is True
    assert trades[0]["side"] == "LONG"
    assert trades[0]["entry_time"] == "2024-01-08T11:00:00+00:00"
    assert trades[0]["entry_fill"] == pytest.approx(2000.35)
    assert trades[0]["exit_reason"] == "target"
    assert trades[0]["exit_price_field"] == "target_limit"
    assert trades[0]["exit_fill"] == pytest.approx(2007.80)
    assert trades[0]["financing_usd_per_oz"] == pytest.approx(0.05)
    assert trades[0]["net_R"] == pytest.approx(2.43333333)
    assert trades[0]["financing_schedule_side"] == "LONG"
    assert trades[0]["spread_double_charged"] is False
    assert metrics["spread_double_charged"] is False


def test_short_uses_bid_entry_and_ask_exit() -> None:
    bars = bars_fixture()
    bars["signal"] = [-1, 0, 0, 0]
    # Ensure the ASK low triggers the short target on the third bar.
    bars.loc[2, "bid_low"] = 1992.0
    bars.loc[2, "bid_close"] = 1993.8
    bars.loc[2, "ask_high"] = 2002.5
    bars.loc[2, "ask_low"] = 1992.0
    bars.loc[2, "ask_close"] = 1994.0

    metrics, trades = run_xauusd_backtest(bars, config())

    assert metrics["trades"] == 1
    assert trades[0]["side"] == "SHORT"
    assert trades[0]["entry_fill"] == pytest.approx(1999.95)
    assert trades[0]["exit_reason"] == "target"
    assert trades[0]["exit_fill"] == pytest.approx(1992.50)
    assert trades[0]["financing_usd_per_oz"] == pytest.approx(-0.03)
    assert trades[0]["financing_schedule_side"] == "SHORT"
    # A verified broker credit lowers total trading costs for the short.
    assert trades[0]["net_R"] == pytest.approx(2.46)


def test_same_bar_stop_and_target_resolves_stop_first() -> None:
    bars = bars_fixture()
    bars.loc[1, "bid_high"] = 2010.0
    bars.loc[1, "bid_low"] = 1990.0

    metrics, trades = run_xauusd_backtest(bars, config())

    assert metrics["trades"] == 1
    assert trades[0]["exit_reason"] == "same_bar_stop_first"
    assert trades[0]["exit_price_field"] == "stop"
    assert trades[0]["net_R"] < 0


def test_missing_broker_financing_schedule_fails_closed() -> None:
    bars = bars_fixture().drop(columns=["financing_long_usd_per_oz"])

    with pytest.raises(XAUUSDExecutionError, match="REQUIRED_COLUMNS_MISSING"):
        run_xauusd_backtest(bars, config())


def test_crossed_open_quote_fails_closed() -> None:
    bars = bars_fixture()
    bars.loc[1, "ask_open"] = bars.loc[1, "bid_open"] - 0.01

    with pytest.raises(XAUUSDExecutionError, match="CROSSED_OPEN_QUOTES"):
        run_xauusd_backtest(bars, config())


def test_timestamp_duplicate_fails_closed() -> None:
    bars = bars_fixture()
    bars.loc[2, "timestamp"] = bars.loc[1, "timestamp"]

    with pytest.raises(XAUUSDExecutionError, match="DUPLICATE_TIMESTAMPS"):
        run_xauusd_backtest(bars, config())

def test_utc_hour_filter_suppresses_new_entry_at_blocked_bar_open() -> None:
    bars = bars_fixture()
    bars["timestamp"] = pd.to_datetime([
        "2024-01-08T00:00:00Z",
        "2024-01-08T01:00:00Z",
        "2024-01-08T02:00:00Z",
        "2024-01-08T03:00:00Z",
    ], utc=True)
    bars["signal"] = [1, 1, 0, 0]
    filtered = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        atr_stop_mult=1.5,
        reward_risk=2.5,
        risk_fraction=0.0025,
        max_holding_bars=30,
        blocked_entry_utc_hours=(1,),
    )

    metrics, trades = run_xauusd_backtest(bars, filtered)

    assert metrics["blocked_entry_utc_hours"] == [1]
    assert metrics["entry_signals_suppressed_by_utc_hour_filter"] == 1
    assert metrics["entries"] == metrics["trades"] == 1
    assert trades[0]["entry_time"] == "2024-01-08T02:00:00+00:00"


def test_utc_hour_filter_does_not_block_exit_of_existing_position() -> None:
    bars = bars_fixture()
    bars["timestamp"] = pd.to_datetime([
        "2024-01-07T23:00:00Z",
        "2024-01-08T00:00:00Z",
        "2024-01-08T01:00:00Z",
        "2024-01-08T02:00:00Z",
    ], utc=True)
    bars["signal"] = [1, 0, 0, 0]
    filtered = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        atr_stop_mult=1.5,
        reward_risk=2.5,
        risk_fraction=0.0025,
        max_holding_bars=30,
        blocked_entry_utc_hours=(1,),
    )

    metrics, trades = run_xauusd_backtest(bars, filtered)

    assert metrics["entries"] == metrics["trades"] == 1
    assert metrics["entry_signals_suppressed_by_utc_hour_filter"] == 0
    assert trades[0]["exit_reason"] == "target"
    assert trades[0]["exit_time"] == "2024-01-08T01:00:00+00:00"


def test_invalid_blocked_utc_hours_fail_closed() -> None:
    bad = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        blocked_entry_utc_hours=(1, 24),
    )
    with pytest.raises(XAUUSDExecutionError, match="BLOCKED_ENTRY_UTC_HOURS_INVALID"):
        run_xauusd_backtest(bars_fixture(), bad)



def test_daily_flat_guard_closes_open_position_before_utc_cutoff() -> None:
    bars = bars_fixture()
    bars["timestamp"] = pd.to_datetime([
        "2024-01-08T10:00:00Z",
        "2024-01-08T10:05:00Z",
        "2024-01-08T10:10:00Z",
        "2024-01-08T10:15:00Z",
    ], utc=True)
    # Keep the cutoff bar inside the trade's stop/target range.
    bars.loc[2, ["bid_high", "bid_low", "bid_close"]] = [2002.5, 1999.5, 2001.5]
    bars.loc[2, ["ask_high", "ask_low", "ask_close"]] = [2002.8, 1999.8, 2001.8]
    guarded = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        atr_stop_mult=1.5,
        reward_risk=2.5,
        risk_fraction=0.0025,
        max_holding_bars=30,
        force_flat_utc_time="10:15",
        force_flat_bar_interval_minutes=5,
    )

    metrics, trades = run_xauusd_backtest(bars, guarded)

    assert metrics["daily_force_flat_guard_enabled"] is True
    assert metrics["daily_force_flat_utc_time"] == "10:15"
    assert metrics["forced_session_liquidations"] == 1
    assert metrics["forced_end_of_data_liquidation"] is False
    assert metrics["entries"] == metrics["trades"] == 1
    assert trades[0]["exit_reason"] == "forced_daily_flat_before_rollover"
    assert trades[0]["exit_price_field"] == "bid_close"
    assert trades[0]["exit_time"] == "2024-01-08T10:15:00+00:00"
    assert trades[0]["exit_fill"] == pytest.approx(2001.45)


def test_daily_flat_guard_suppresses_entry_on_flatten_bar() -> None:
    bars = bars_fixture()
    bars["timestamp"] = pd.to_datetime([
        "2024-01-08T10:00:00Z",
        "2024-01-08T10:05:00Z",
        "2024-01-08T10:10:00Z",
        "2024-01-08T10:15:00Z",
    ], utc=True)
    bars["signal"] = [0, 1, 0, 0]
    guarded = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        force_flat_utc_time="10:15",
        force_flat_bar_interval_minutes=5,
    )

    metrics, trades = run_xauusd_backtest(bars, guarded)

    assert metrics["entries"] == metrics["trades"] == 0
    assert metrics["entry_signals_suppressed_by_force_flat_bar"] == 1
    assert trades == []


def test_daily_flat_guard_uses_earlier_bar_when_cutoff_bar_is_missing() -> None:
    bars = bars_fixture()
    bars = bars.iloc[[0, 1, 2, 3]].copy()
    bars["timestamp"] = pd.to_datetime([
        "2024-01-08T09:55:00Z",
        "2024-01-08T10:00:00Z",
        "2024-01-08T10:05:00Z",
        "2024-01-08T10:15:00Z",
    ], utc=True)
    bars.loc[2, ["bid_high", "bid_low", "bid_close"]] = [2002.5, 1999.5, 2001.5]
    bars.loc[2, ["ask_high", "ask_low", "ask_close"]] = [2002.8, 1999.8, 2001.8]
    guarded = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        force_flat_utc_time="10:15",
        force_flat_bar_interval_minutes=5,
    )

    metrics, trades = run_xauusd_backtest(bars, guarded)

    # 10:10 is absent, so the 10:05 bar is used and exits early at 10:10.
    assert metrics["forced_session_liquidations"] == 1
    assert trades[0]["exit_reason"] == "forced_daily_flat_before_rollover"
    assert trades[0]["exit_time"] == "2024-01-08T10:10:00+00:00"


def test_daily_flat_guard_rejects_invalid_utc_cutoff() -> None:
    bad = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        force_flat_utc_time="24:00",
    )
    with pytest.raises(XAUUSDExecutionError, match="FORCE_FLAT_UTC_TIME_INVALID"):
        run_xauusd_backtest(bars_fixture(), bad)


def test_daily_flat_guard_blocks_reentry_after_cutoff_until_next_utc_day() -> None:
    bars = bars_fixture()
    bars["timestamp"] = pd.to_datetime([
        "2024-01-08T10:00:00Z",
        "2024-01-08T10:05:00Z",
        "2024-01-08T10:10:00Z",
        "2024-01-08T10:15:00Z",
    ], utc=True)
    # A fresh signal on the last pre-cutoff bar must not open at 10:15.
    bars["signal"] = [0, 0, 1, 0]
    guarded = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.05,
        commission_usd_per_oz_round_turn=0.10,
        force_flat_utc_time="10:15",
        force_flat_bar_interval_minutes=5,
    )

    metrics, trades = run_xauusd_backtest(bars, guarded)

    assert metrics["entries"] == metrics["trades"] == 0
    assert metrics["entry_signals_suppressed_after_flat_cutoff"] == 1
    assert metrics["forced_session_liquidations"] == 0
    assert trades == []
