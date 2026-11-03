import hashlib
import json

import pandas as pd
import pytest

from research.optimization.session_range_breakout_g15 import (
    _canonical_sha256,
    _is_reasons,
    _stress_reasons,
    _validation_reasons,
    backtest_session_range,
    _load_verified_data,
)


def _good():
    return {
        "trades": 150,
        "profit_factor": 1.25,
        "expectancy_R": 0.02,
        "total_R": 3.0,
        "final_equity": 10150.0,
        "max_dd_pct": 15.0,
    }


def test_g15_is_gate_fails_closed_for_any_bad_discovery_year():
    good = _good()
    assert _is_reasons({"2022": good, "2023": good, "2024": good}) == {}
    bad = {**good, "final_equity": 9999.0}
    assert "2023" in _is_reasons({"2022": good, "2023": bad, "2024": good})


def test_g15_validation_gate_requires_positive_net_and_compounded_equity():
    assert _validation_reasons(_good()) == []
    assert "final_equity<=initial_equity" in _validation_reasons(_good() | {"final_equity": 9999.0})
    assert "expectancy_R<=0" in _validation_reasons(_good() | {"expectancy_R": 0.0})
    assert "total_R<=0" in _validation_reasons(_good() | {"total_R": -1.0})
    assert "profit_factor<1.1" in _validation_reasons(_good() | {"profit_factor": 1.09})
    assert "max_dd_pct>35.0" in _validation_reasons(_good() | {"max_dd_pct": 35.01})


def test_g15_moderate_stress_gate_rejects_negative_edge():
    assert _stress_reasons(_good()) == []
    assert "profit_factor<1.0" in _stress_reasons(_good() | {"profit_factor": 0.99})
    assert "total_R<=0" in _stress_reasons(_good() | {"total_R": 0.0})


def test_g15_canonical_hash_is_independent_of_dict_insertion_order():
    assert _canonical_sha256({"a": 1, "b": 2}) == _canonical_sha256({"b": 2, "a": 1})


def test_g15_backtest_checks_entry_bar_and_resolves_ambiguous_hit_sl_first():
    index = pd.date_range("2022-01-03T06:30:00Z", periods=80, freq="5min")
    opens = [1.1000] * 80
    highs = [1.1001] * 80
    lows = [1.0999] * 80
    closes = [1.1000] * 80

    # Pre-session high is established immediately before 07:00 UTC.
    highs[5] = 1.1010
    closes[5] = 1.1005
    # This closed candle breaks the retained morning range.
    highs[6] = 1.1013
    closes[6] = 1.1012
    # The next candle is the executable entry bar and touches both SL and TP.
    opens[7] = 1.1000
    highs[7] = 1.1013
    lows[7] = 1.0990
    closes[7] = 1.1000

    frame = pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes},
        index=index,
    )
    params = {
        "atr": 14, "bb": 20, "fast": 13, "slow": 89, "rsi": 14,
        "don": 20, "trend": 200, "atr_stop": 1.0, "rr": 1.5,
        "session_start_hour": 7, "breakout_buffer_pips": 0.0,
    }
    metrics = backtest_session_range(frame, params)
    assert metrics["entries"] == metrics["exits"]
    assert metrics["trades"] >= 1
    assert metrics["open_position_end"] is False
    assert metrics["same_bar_stop_first_count"] >= 1
    assert metrics["final_equity"] < 10000.0


def test_g15_input_verification_rejects_2026_rows(tmp_path):
    dataset = tmp_path / "EURUSD_M5.csv"
    manifest = tmp_path / "EURUSD_M5.manifest.json"
    frame = pd.DataFrame({
        "timestamp": pd.to_datetime(["2022-01-03T00:00:00Z", "2026-01-01T00:00:00Z"]),
        "open": [1.1, 1.1], "high": [1.101, 1.101],
        "low": [1.099, 1.099], "close": [1.1001, 1.1001],
        "volume": [10.0, 10.0],
    })
    frame.to_csv(dataset, index=False)
    manifest.write_text(json.dumps({
        "dataset_id": "fixture",
        "symbol": "EURUSD",
        "timeframe": "M5",
        "source": "HistData.com Generic ASCII M1 resampled to M5",
        "source_hash": "source-hash",
        "rows": 2,
        "quality_status": "PASS",
        "data_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="G15_OOS_POLICY_VIOLATION_2026_DATA_PRESENT"):
        _load_verified_data(dataset, manifest)


def test_g15_input_verification_rejects_modified_dataset_sha(tmp_path):
    dataset = tmp_path / "EURUSD_M5.csv"
    manifest = tmp_path / "EURUSD_M5.manifest.json"
    frame = pd.DataFrame({
        "timestamp": pd.date_range("2022-01-03T00:00:00Z", periods=2, freq="5min"),
        "open": [1.1, 1.1], "high": [1.101, 1.101],
        "low": [1.099, 1.099], "close": [1.1001, 1.1001],
        "volume": [10.0, 10.0],
    })
    frame.to_csv(dataset, index=False)
    manifest.write_text(json.dumps({
        "symbol": "EURUSD",
        "timeframe": "M5",
        "source": "HistData",
        "source_hash": "source-hash",
        "rows": 2,
        "quality_status": "PASS",
        "data_sha256": "0" * 64,
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="G15_DATA_SHA256_MISMATCH"):
        _load_verified_data(dataset, manifest)
