import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from research.optimization.efficiency_ratio_momentum_g17 import (
    _entry_fill, _exit_fill, _features, _gate, _round_trip_cost_pips,
    _signal, _stop_hit, _verified_load, backtest, catalog,
)


def synthetic_frame(rows=2400):
    idx = pd.date_range("2022-01-03T00:00:00Z", periods=rows, freq="5min")
    x = np.arange(rows, dtype=float)
    close = 1.10 + 0.000002 * x + 0.00015 * np.sin(2 * np.pi * x / 90)
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({"Open": open_, "High": np.maximum(open_, close) + 0.00004,
                         "Low": np.minimum(open_, close) - 0.00004, "Close": close}, index=idx)


def _write_fixture(tmp_path, timestamps):
    data, manifest = tmp_path / "EURUSD_M5.csv", tmp_path / "EURUSD_M5.manifest.json"
    rows = pd.DataFrame({
        "timestamp": pd.to_datetime(timestamps, utc=True),
        "open": [1.1] * len(timestamps), "high": [1.1002] * len(timestamps),
        "low": [1.0998] * len(timestamps), "close": [1.1001] * len(timestamps),
        "volume": [10.0] * len(timestamps),
    })
    rows.to_csv(data, index=False)
    doc = {"dataset_id": "g17-fixture", "symbol": "EURUSD", "timeframe": "M5",
           "source": "HistData.com Generic ASCII M1 resampled to M5",
           "source_hash": "fixture-source-hash", "rows": len(rows),
           "start": rows.timestamp.min().isoformat(), "end": rows.timestamp.max().isoformat(),
           "quality_status": "PASS", "data_sha256": hashlib.sha256(data.read_bytes()).hexdigest()}
    manifest.write_text(json.dumps(doc), encoding="utf-8")
    return data, manifest


def test_catalog_is_fixed_and_unique():
    values = catalog()
    assert len(values) == 108
    assert len({tuple(sorted(item.items())) for item in values}) == 108


def test_signal_requires_fresh_threshold_cross_and_efficiency():
    p = {"entry_momentum": 1.0, "efficiency_min": 0.3}
    assert _signal(1.1, 0.9, 0.4, p) == 1
    assert _signal(-1.1, -0.9, 0.4, p) == -1
    assert _signal(1.1, 1.05, 0.4, p) == 0
    assert _signal(1.1, 0.9, 0.2, p) == 0


def test_bid_ask_round_trip_cost_and_fills():
    assert _round_trip_cost_pips(0.5, 0.2) == pytest.approx(0.9)
    assert _entry_fill(1.1, 1, 0.5, 0.2) == pytest.approx(1.10007)
    assert _exit_fill(1.1, 1, 0.2) == pytest.approx(1.09998)
    assert _entry_fill(1.1, -1, 0.5, 0.2) == pytest.approx(1.09998)
    assert _exit_fill(1.10005, -1, 0.2) == pytest.approx(1.10007)


def test_short_stop_uses_reconstructed_ask():
    assert _stop_hit(-1, 1.10000, 1.09980, 1.10005, 0.5)
    assert not _stop_hit(-1, 1.09990, 1.09980, 1.10005, 0.5)


def test_features_reject_bad_chronology_and_ohlc():
    frame = synthetic_frame(200)
    with pytest.raises(ValueError, match="G17_BAD_CHRONOLOGICAL_INDEX"):
        _features(frame.iloc[::-1], 24)
    bad = frame.copy()
    bad.iloc[50, bad.columns.get_loc("High")] = bad.iloc[50]["Low"] - 0.001
    with pytest.raises(ValueError, match="G17_OHLC_INVARIANT_FAIL"):
        _features(bad, 24)


def test_backtest_closes_positions_and_reconciles_equity():
    p = {"lookback": 24, "entry_momentum": 0.75, "efficiency_min": 0.25,
         "atr_stop": 2.0, "max_hold_bars": 24, "exit_momentum": 0.0}
    result = backtest(synthetic_frame(), p)
    assert result["entries"] == result["exits"] == result["trades"]
    assert result["open_position_end"] is False
    assert result["round_trip_cost_pips"] == pytest.approx(0.9)
    assert result["drawdown_basis"] == "CLOSED_EQUITY_PEAK_PLUS_ADVERSE_INTRABAR_MARK"
    assert np.isfinite(result["final_equity"])


def test_nonfinite_cost_is_rejected():
    p = {"lookback": 24}
    with pytest.raises(ValueError, match="G17_INVALID_COST_ASSUMPTION"):
        backtest(synthetic_frame(100), p, (float("nan"), 0.2))


def test_gate_rejects_negative_edge():
    m = {"trades": 300, "profit_factor": 0.95, "expectancy_R": -0.01,
         "total_R": -3.0, "final_equity": 9850.0, "max_adverse_dd_pct": 10.0}
    assert "profit_factor<1.05" in _gate(m, 100, 1.05, 35.0)
    assert "expectancy_R<=0" in _gate(m, 100, 1.05, 35.0)


def test_empty_backtest_is_not_a_pass():
    p = {"lookback": 24, "entry_momentum": 0.75, "efficiency_min": 0.25,
         "atr_stop": 2.0, "max_hold_bars": 24, "exit_momentum": 0.0}
    result = backtest(synthetic_frame(1).iloc[0:0], p)
    assert result["trades"] == 0
    assert result["final_equity"] == 10000.0


def test_loader_accepts_manifest_verified_m5(tmp_path):
    times = ["2022-01-03T00:00:00Z", "2023-01-03T00:00:00Z",
             "2024-01-03T00:00:00Z", "2025-01-03T00:00:00Z"]
    data, manifest = _write_fixture(tmp_path, times)
    frame, doc, data_hash, manifest_hash = _verified_load(data, manifest)
    assert len(frame) == 4 and doc["quality_status"] == "PASS"
    assert len(data_hash) == len(manifest_hash) == 64


def test_loader_rejects_any_2026_row(tmp_path):
    times = ["2022-01-03T00:00:00Z", "2023-01-03T00:00:00Z",
             "2024-01-03T00:00:00Z", "2025-01-03T00:00:00Z",
             "2026-01-01T00:00:00Z"]
    data, manifest = _write_fixture(tmp_path, times)
    with pytest.raises(ValueError, match="G17_OOS_POLICY_VIOLATION_2026_DATA_PRESENT"):
        _verified_load(data, manifest)


def test_loader_rejects_data_hash_mismatch(tmp_path):
    times = ["2022-01-03T00:00:00Z", "2023-01-03T00:00:00Z",
             "2024-01-03T00:00:00Z", "2025-01-03T00:00:00Z"]
    data, manifest = _write_fixture(tmp_path, times)
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    doc["data_sha256"] = "0" * 64
    manifest.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ValueError, match="G17_DATA_SHA256_MISMATCH"):
        _verified_load(data, manifest)
