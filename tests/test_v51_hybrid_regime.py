import numpy as np
import pandas as pd
import pytest

from research.optimization.v51_hybrid_regime import (
    V51Config,
    _Position,
    _intrabar_exit,
    _wilder_rma,
    backtest_v51,
    evaluate_v51_signal,
    prepare_v51_features,
)


def _ohlc(rows: int = 1200) -> pd.DataFrame:
    index = pd.date_range("2024-01-01T00:00:00Z", periods=rows, freq="15min")
    close = 1.10 + np.arange(rows, dtype=float) * 0.00001
    return pd.DataFrame(
        {
            "timestamp": index,
            "open": close,
            "high": close + 0.00008,
            "low": close - 0.00008,
            "close": close,
            "volume": np.ones(rows),
            "spread": np.full(rows, np.nan),
        }
    )


def test_wilder_rma_uses_sma_seed_then_recursive_smoothing():
    values = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    result = _wilder_rma(values, 3)
    assert result.iloc[:2].isna().all()
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx((2.0 * 2.0 + 4.0) / 3.0)


def test_mql5_copybuffer_series_index_one_is_reproduced_as_shift_two():
    data = _ohlc(500)
    features = prepare_v51_features(data)
    # The entry-bar row at index i uses MQL5 shift 2, not shift 1.
    assert features["DECISION_CLOSE"].iloc[20] == pytest.approx(features["Close"].iloc[18])
    assert features["DECISION_ATR"].iloc[300] == pytest.approx(features["ATR"].iloc[298])
    assert features["DECISION_ADX"].iloc[300] == pytest.approx(features["ADX"].iloc[298])


def test_h4_shift_two_points_to_second_most_recent_completed_h4_bar():
    data = _ohlc(24 * 4 * 15)
    features = prepare_v51_features(data)
    at_0800 = pd.Timestamp("2024-01-01T08:00:00Z")
    expected_h4_close = (
        data.assign(timestamp=pd.to_datetime(data["timestamp"], utc=True))
        .set_index("timestamp")["close"]
        .resample("4h", label="left", closed="left")
        .last()
        .loc[pd.Timestamp("2024-01-01T00:00:00Z")]
    )
    observed = features.loc[at_0800, "HTF_CLOSE_SHIFT2"]
    assert observed == pytest.approx(expected_h4_close)


def test_trend_branch_uses_shifted_ma_atr_di_and_h4_filters():
    row = pd.Series(
        {
            "DECISION_ATR": 2.0,
            "DECISION_CLOSE": 101.0,
            "DECISION_SMA200": 100.0,
            "DECISION_DI_PLUS": 24.0,
            "DECISION_DI_MINUS": 12.0,
            "HTF_CLOSE_SHIFT2": 105.0,
            "HTF_SMA200_SHIFT2": 100.0,
        }
    )
    signal = evaluate_v51_signal(
        row,
        regime=1,
        current_bid_open=100.0,
        spread_price=0.00005,
        config=V51Config(),
    )
    assert signal is not None
    assert signal.side == 1
    assert signal.setup == "A-trend"
    assert signal.stop == pytest.approx(97.1)
    assert signal.target == pytest.approx(105.51)


def test_range_or_trend_does_not_signal_when_required_indicators_are_missing():
    row = pd.Series(
        {
            "DECISION_ATR": 0.001,
            "DECISION_CLOSE": np.nan,
            "DECISION_SMA200": np.nan,
            "DECISION_DI_PLUS": np.nan,
            "DECISION_DI_MINUS": np.nan,
            "HTF_CLOSE_SHIFT2": np.nan,
            "HTF_SMA200_SHIFT2": np.nan,
        }
    )
    assert evaluate_v51_signal(
        row,
        regime=1,
        current_bid_open=1.1,
        spread_price=0.00005,
    ) is None


def test_same_bar_stop_is_resolved_before_target():
    config = V51Config()
    execution = __import__(
        "research.optimization.execution_contract_v1",
        fromlist=["ExecutionConfig"],
    ).ExecutionConfig()
    position = _Position(
        side=1,
        setup="A-trend",
        entry_time=pd.Timestamp("2024-01-01T00:00:00Z"),
        entry_index=0,
        entry_price=100.0,
        stop=99.0,
        target=101.0,
        risk_distance=1.0,
        risk_fraction=0.005,
        spread_pips=0.5,
    )
    row = pd.Series({"High": 102.0, "Low": 98.0})
    result = _intrabar_exit(
        position,
        row,
        pd.Timestamp("2024-01-01T00:15:00Z"),
        config,
        execution,
    )
    assert result is not None
    assert result["exit_reason"] == "SL"
    assert result["R"] < 0


def test_backtest_requires_prepared_features_and_does_not_invent_trades():
    with pytest.raises(ValueError, match="REAL_DATA_REQUIRED"):
        prepare_v51_features(pd.DataFrame())

    data = _ohlc(400)
    config = V51Config()
    features = prepare_v51_features(data, config)
    # The monotonic fixture does not satisfy the configured ADX regime/pullback
    # combinations with all gates, and no broker/tick prices are invented.
    report = backtest_v51(features.iloc[:100], config)
    assert report["status"] == "PASS_RESEARCH_SIMULATION"
    assert report["trades"] == 0
    assert report["round_trip_cost_pips"] == pytest.approx(1.4)
    assert report["open_position_at_end"] is False
