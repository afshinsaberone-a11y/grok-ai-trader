from pathlib import Path

import numpy as np
import pandas as pd

import research.optimization.v51_hybrid_regime as v51


ROOT = Path(__file__).resolve().parents[1]


def test_mql5_trace_identity_uses_the_same_shift_two_signal_bar_as_v51_rules():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    assert "BuildTraceTradeId(true, iTime(_Symbol, PERIOD_CURRENT, 2))" in source
    assert "BuildTraceTradeId(false, iTime(_Symbol, PERIOD_CURRENT, 2))" in source
    assert "int signal_shift = shift + 2;" in source
    assert "BuildTraceTradeId(true, iTime(_Symbol, PERIOD_CURRENT, 1))" not in source
    assert "BuildTraceTradeId(false, iTime(_Symbol, PERIOD_CURRENT, 1))" not in source
    assert "int signal_shift = shift + 1;" not in source


def test_python_signal_log_binds_trace_time_to_shift_two_source_bar(monkeypatch):
    server_index = pd.date_range("2026-01-05 10:00:00", periods=4, freq="15min")
    utc_index = (server_index - pd.Timedelta(hours=2)).tz_localize("UTC")
    features = pd.DataFrame(
        {
            "Open": [1.10] * 4,
            "High": [1.1001] * 4,
            "Low": [1.0999] * 4,
            "Close": [1.10] * 4,
            "utc_timestamp": utc_index,
            "DECISION_ATR": [0.001] * 4,
            "DECISION_ADX": [25.0] * 4,
            "DECISION_DI_PLUS": [20.0] * 4,
            "DECISION_DI_MINUS": [10.0] * 4,
            "DECISION_CLOSE": [0.0, 0.0, 0.0, 1.0],
            "DECISION_SMA200": [1.0] * 4,
            "HTF_CLOSE_SHIFT2": [1.1] * 4,
            "HTF_SMA200_SHIFT2": [1.0] * 4,
            "DECISION_BB_UPPER": [1.101] * 4,
            "DECISION_BB_LOWER": [1.099] * 4,
            "DECISION_BB_MID": [1.10] * 4,
            "SQUEEZE_OLDER_ATR_MEAN": [0.001] * 4,
            "SQUEEZE_OLD_ATR": [0.001] * 4,
            "SQUEEZE_PREV_CLOSE": [1.1] * 4,
            "SQUEEZE_PREV_BB_UPPER": [1.101] * 4,
            "SQUEEZE_PREV_BB_LOWER": [1.099] * 4,
            "DECISION_ADX_PREV": [20.0] * 4,
            "DECISION_HIGH": [1.1001] * 4,
            "DECISION_LOW": [1.0999] * 4,
        },
        index=server_index,
    )

    monkeypatch.setattr(v51, "_regime_raw", lambda row, config: 1)
    monkeypatch.setattr(v51, "_spread_ok", lambda row, config: True)
    monkeypatch.setattr(v51, "_session_ok", lambda timestamp, config: True)
    monkeypatch.setattr(v51, "_news_ok", lambda timestamp, config: True)
    monkeypatch.setattr(
        v51,
        "evaluate_v51_signal",
        lambda row, **kwargs: (
            v51.V51Signal(1, "A-trend", 0.001, 1.095, 1.110)
            if float(row["DECISION_CLOSE"]) == 1.0
            else None
        ),
    )

    report = v51.backtest_v51(features, v51.V51Config(regime_confirm_bars=1))
    assert len(report["signal_log"]) == 1
    signal = report["signal_log"][0]
    assert signal["signal_bar_shift"] == 2
    assert signal["signal_bar_timestamp_server"] == server_index[1].isoformat()
    assert "+00:00" not in signal["signal_bar_timestamp_server"]
    assert signal["signal_bar_timestamp_utc"] == utc_index[1].isoformat()
