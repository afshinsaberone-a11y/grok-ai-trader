from __future__ import annotations

import pandas as pd
import pytest

from research.optimization.xauusd_execution_contract_v1 import XAUUSDExecutionConfig
from research.optimization.xauusd_intraday_execution_adapter_v1 import (
    XAUUSDIntradayAdapterError,
    run_xauusd_intraday,
)


def bars_fixture() -> pd.DataFrame:
    timestamps = list(pd.date_range('2025-01-06T20:30:00Z', periods=5, freq='5min'))
    timestamps += list(pd.date_range('2025-01-07T20:30:00Z', periods=5, freq='5min'))
    rows = []
    for day_start in range(0, 10, 5):
        for offset in range(5):
            price = 2000.0 + offset * 0.1
            rows.append({
                'timestamp': timestamps[day_start + offset],
                'bid_open': price,
                'bid_high': price + 0.5,
                'bid_low': price - 0.5,
                'bid_close': price + 0.1,
                'ask_open': price + 0.3,
                'ask_high': price + 0.8,
                'ask_low': price - 0.2,
                'ask_close': price + 0.4,
                'signal': 1 if offset == 0 else 0,
                'ATR': 2.0,
            })
    return pd.DataFrame(rows)


def config() -> XAUUSDExecutionConfig:
    return XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=0.02,
        commission_usd_per_oz_round_turn=0.08,
        atr_stop_mult=1.5,
        reward_risk=2.5,
        risk_fraction=0.0025,
        max_holding_bars=30,
    )


def test_intraday_adapter_liquidates_each_day_before_rollover() -> None:
    metrics, trades = run_xauusd_intraday(bars_fixture(), config())

    assert metrics['utc_sessions_executed'] == 2
    assert metrics['trades'] == metrics['entries'] == 2
    assert metrics['entries_equal_exits'] is True
    assert metrics['positions_carry_through_rollover'] is False
    assert metrics['financing_model'] == 'ZERO_NO_OVERNIGHT_CARRY'
    assert metrics['financing_is_historical_broker_schedule'] is False
    assert all(t['exit_reason'] == 'end_of_data_liquidation' for t in trades)
    assert all(t['entry_time'][:10] == t['exit_time'][:10] for t in trades)
    assert all(t['financing_usd_per_oz'] == 0.0 for t in trades)
    assert all(t['spread_double_charged'] is False for t in trades)
    pre_commission = [
        t['price_R_after_quote_and_slippage_before_commission_financing']
        for t in trades
    ]
    net = [t['net_R'] for t in trades]
    assert metrics['pre_commission_expectancy_R'] == pytest.approx(
        sum(pre_commission) / len(pre_commission)
    )
    assert metrics['commission_financing_drag_expectancy_R'] == pytest.approx(
        sum(before - after for before, after in zip(pre_commission, net))
        / len(net)
    )
    assert metrics['pre_commission_profit_factor'] > 0


def test_bar_opening_at_2050_is_excluded_and_last_bar_closes_by_cutoff() -> None:
    metrics, trades = run_xauusd_intraday(bars_fixture(), config())

    # Five bars/day are supplied, but 20:50 opens after the 20:50 close cutoff.
    assert metrics['rows_before_cutoff'] == 8
    assert len(trades) == 2
    assert all(t['exit_time'].endswith('20:45:00+00:00') for t in trades)


def test_cutoff_must_precede_earliest_rollover() -> None:
    with pytest.raises(XAUUSDIntradayAdapterError, match='NOT_BEFORE_ROLLOVER'):
        run_xauusd_intraday(
            bars_fixture(), config(), flatten_by_utc='21:00',
            earliest_rollover_utc='20:59',
        )


def test_adapter_rejects_non_m5_aligned_timestamps() -> None:
    bars = bars_fixture()
    bars.loc[0, 'timestamp'] += pd.Timedelta(minutes=1)
    with pytest.raises(XAUUSDIntradayAdapterError, match='M5_TIMESTAMP_ALIGNMENT_INVALID'):
        run_xauusd_intraday(bars, config())


def test_adapter_requires_real_bid_ask_signal_columns() -> None:
    bars = bars_fixture().drop(columns=['ask_open'])
    with pytest.raises(XAUUSDIntradayAdapterError, match='REQUIRED_COLUMNS_MISSING'):
        run_xauusd_intraday(bars, config())


def gap_bars_fixture() -> pd.DataFrame:
    timestamps = pd.to_datetime([
        "2025-01-06T10:00:00Z",
        "2025-01-06T10:05:00Z",
        "2025-01-06T10:10:00Z",
        "2025-01-06T10:20:00Z",
        "2025-01-06T10:25:00Z",
        "2025-01-06T10:30:00Z",
        "2025-01-06T10:35:00Z",
    ], utc=True)
    rows = []
    signals = [1, 0, 0, 1, 1, 0, 0]
    for timestamp, signal in zip(timestamps, signals):
        rows.append({
            "timestamp": timestamp,
            "bid_open": 2000.0,
            "bid_high": 2000.4,
            "bid_low": 1999.6,
            "bid_close": 2000.1,
            "ask_open": 2000.3,
            "ask_high": 2000.7,
            "ask_low": 1999.9,
            "ask_close": 2000.4,
            "signal": signal,
            "ATR": 2.0,
        })
    return pd.DataFrame(rows)


def test_intraday_gap_requires_explicit_indicator_warmup() -> None:
    with pytest.raises(
        XAUUSDIntradayAdapterError,
        match="GAP_INDICATOR_WARMUP_REQUIRED",
    ):
        run_xauusd_intraday(
            gap_bars_fixture(), config(),
            flatten_by_utc="10:40", earliest_rollover_utc="10:59",
        )


def test_intraday_gap_splits_positions_and_suppresses_post_gap_warmup() -> None:
    metrics, trades = run_xauusd_intraday(
        gap_bars_fixture(),
        config(),
        flatten_by_utc="10:40",
        earliest_rollover_utc="10:59",
        indicator_warmup_bars_after_gap=1,
    )

    assert metrics["utc_sessions_executed"] == 1
    assert metrics["utc_segments_executed"] == 2
    assert metrics["intraday_data_gaps_detected"] == 1
    assert metrics["gap_split_segments_with_open_position"] == 1
    assert metrics["gap_exit_assumption_trades"] == 1
    assert metrics["backtest_qualification_status"] == (
        "GAP_EXIT_ASSUMPTIONS_PRESENT_REVIEW_REQUIRED"
    )
    assert metrics["post_gap_signal_rows_suppressed"] == 1
    assert metrics["gap_handling_policy"] == (
        "SPLIT_FLATTEN_REQUIRE_WARMUP_AND_AUDIT_CUTOFF_COVERAGE"
    )
    assert metrics["positions_carry_through_intraday_data_gaps"] is False
    assert metrics["entries"] == metrics["trades"] == 2
    assert metrics["entries_equal_exits"] is True
    assert trades[0]["exit_time"] == "2025-01-06T10:10:00+00:00"
    assert trades[0]["exit_reason"] == "pre_gap_last_observed_close_assumption"
    assert trades[0]["gap_exit_assumption"] is True
    assert trades[1]["gap_exit_assumption"] is False
    assert trades[1]["entry_time"] == "2025-01-06T10:30:00+00:00"
    assert trades[1]["utc_segment_number"] == 2
    assert all(t["entry_time"][:10] == t["exit_time"][:10] for t in trades)


def test_intraday_gap_warmup_must_be_a_nonnegative_integer() -> None:
    for invalid in (0, -1, True, 1.5):
        with pytest.raises(
            XAUUSDIntradayAdapterError,
            match="GAP_INDICATOR_WARMUP_INVALID",
        ):
            run_xauusd_intraday(
                bars_fixture(),
                config(),
                indicator_warmup_bars_after_gap=invalid,
            )


def test_gap_after_cutoff_does_not_hide_pre_cutoff_session_truncation() -> None:
    bars = gap_bars_fixture().iloc[:2].copy()
    bars["timestamp"] = pd.to_datetime([
        "2025-01-06T10:00:00Z",
        "2025-01-06T10:05:00Z",
    ], utc=True)
    # The next observation is after the cutoff and must not hide the missing
    # interval between the last eligible M5 close and the requested cutoff.
    late_row = bars.iloc[-1].copy()
    late_row["timestamp"] = pd.Timestamp("2025-01-06T11:00:00Z")
    late_row["signal"] = 0
    bars = pd.concat([bars, late_row.to_frame().T], ignore_index=True)
    bars["timestamp"] = pd.to_datetime(bars["timestamp"], utc=True)

    metrics, trades = run_xauusd_intraday(
        bars,
        config(),
        flatten_by_utc="10:15",
        earliest_rollover_utc="10:59",
    )

    assert metrics["utc_sessions_truncated_before_cutoff"] == 1
    assert metrics["cutoff_truncated_gap_exit_segments_with_open_position"] == 1
    assert metrics["gap_exit_assumption_trades"] == 1
    assert metrics["backtest_qualification_status"] == (
        "GAP_EXIT_ASSUMPTIONS_PRESENT_REVIEW_REQUIRED"
    )
    assert metrics["entries"] == metrics["trades"] == 1
    assert trades[0]["exit_reason"] == "pre_gap_last_observed_close_assumption"
    assert trades[0]["gap_exit_assumption"] is True
    assert trades[0]["exit_time"] == "2025-01-06T10:05:00+00:00"
