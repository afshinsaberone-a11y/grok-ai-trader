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
