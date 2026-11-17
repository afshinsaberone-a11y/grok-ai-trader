import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from research.optimization.trend_pullback_continuation_g17 import (
    _entry_fill, _exit_fill, _features, _gate, _load, _round_trip_cost_pips,
    _signal, _stop_hit, _target_hit, backtest, catalog,
)


def good_metrics():
    return {
        "trades": 80, "profit_factor": 1.20, "expectancy_R": 0.03,
        "total_R": 2.4, "final_equity": 10120.0, "max_dd_pct": 12.0,
    }


def test_catalog_has_64_unique_predeclared_candidates():
    rows = catalog()
    assert len(rows) == 64
    assert len({json.dumps(item, sort_keys=True) for item in rows}) == 64
    assert {item["pullback_ema"] for item in rows} == {20, 30}
    assert {item["rsi_trigger"] for item in rows} == {45.0, 50.0}
    assert {item["reward_risk"] for item in rows} == {1.5, 2.0}


def test_bid_ask_fills_charge_spread_once_and_slippage_each_side():
    bid = 1.10000
    long_entry = _entry_fill(bid, 1, 0.5, 0.2)
    long_exit = _exit_fill(bid, 1, 0.2)
    assert long_entry == pytest.approx(1.10007)
    assert long_exit == pytest.approx(1.09998)
    assert (long_entry - long_exit) / 0.0001 == pytest.approx(0.9)

    short_entry = _entry_fill(bid, -1, 0.5, 0.2)
    short_exit = _exit_fill(bid + 0.5 * 0.0001, -1, 0.2)
    assert short_entry == pytest.approx(1.09998)
    assert short_exit == pytest.approx(1.10007)
    assert (short_exit - short_entry) / 0.0001 == pytest.approx(0.9)
    assert _round_trip_cost_pips(0.75, 0.30) == pytest.approx(1.35)
    assert _round_trip_cost_pips(1.0, 0.5) == pytest.approx(2.0)


def test_long_signal_requires_trend_pullback_and_rsi_reclaim():
    frame = pd.DataFrame([
        {"Open":1.12,"High":1.13,"Low":1.11,"Close":1.12,"atr":0.001,
         "ema_pullback":1.115,"ema50":1.12,"ema200":1.10,"adx":22,"pdi":30,"mdi":12,"rsi":40},
        {"Open":1.12,"High":1.13,"Low":1.114,"Close":1.118,"atr":0.001,
         "ema_pullback":1.116,"ema50":1.125,"ema200":1.105,"adx":23,"pdi":32,"mdi":11,"rsi":47},
    ])
    p = {"rsi_trigger":45.0,"adx_min":20.0}
    assert _signal(frame, 1, p) == 1
    frame.loc[1,"Low"] = 1.117
    assert _signal(frame, 1, p) == 0  # no pullback into the EMA


def test_short_signal_requires_downtrend_pullback_and_rsi_rejection():
    frame = pd.DataFrame([
        {"Open":1.10,"High":1.11,"Low":1.09,"Close":1.10,"atr":0.001,
         "ema_pullback":1.105,"ema50":1.12,"ema200":1.13,"adx":22,"pdi":12,"mdi":30,"rsi":60},
        {"Open":1.10,"High":1.106,"Low":1.094,"Close":1.100,"atr":0.001,
         "ema_pullback":1.102,"ema50":1.115,"ema200":1.125,"adx":23,"pdi":11,"mdi":32,"rsi":53},
    ])
    assert _signal(frame, 1, {"rsi_trigger":45.0,"adx_min":20.0}) == -1


def test_short_stops_and_targets_use_reconstructed_ask():
    assert _stop_hit(-1, 1.10046, 1.10000, 1.10050, 0.5) is True
    assert _stop_hit(-1, 1.10040, 1.10000, 1.10050, 0.5) is False
    assert _target_hit(-1, 1.10050, 1.09990, 1.10000, 0.5) is True


def test_gate_is_fail_closed_for_each_required_year():
    assert _gate(good_metrics()) == []
    assert "trades<50" in _gate(good_metrics() | {"trades":49})
    assert "profit_factor<1.05" in _gate(good_metrics() | {"profit_factor":1.04})
    assert "expectancy_R<=0" in _gate(good_metrics() | {"expectancy_R":0.0})
    assert "max_dd_pct>35.0" in _gate(good_metrics() | {"max_dd_pct":35.01})


def test_feature_builder_emits_only_causal_indicator_columns():
    n = 800
    idx = pd.date_range("2022-01-03T00:00:00Z", periods=n, freq="5min")
    close = 1.10 + np.arange(n) * 0.00001 + 0.0003 * np.sin(np.arange(n) / 9.0)
    op = np.roll(close, 1)
    op[0] = close[0]
    frame = pd.DataFrame({
        "Open":op, "High":np.maximum(op,close)+0.00005,
        "Low":np.minimum(op,close)-0.00005, "Close":close,
    }, index=idx)
    features = _features(frame, 20)
    assert {"ema_pullback","ema50","ema200","atr","adx","pdi","mdi","rsi"}.issubset(features.columns)
    assert np.isfinite(features.loc[features.index[-1], ["ema_pullback","ema50","ema200","atr","adx","pdi","mdi","rsi"]].to_numpy(float)).all()


def test_same_bar_stop_and_target_collision_resolves_stop_first():
    rows = [
        {"Open":1.12,"High":1.13,"Low":1.11,"Close":1.12,"atr":0.001,
         "ema_pullback":1.115,"ema50":1.12,"ema200":1.10,"adx":22,"pdi":30,"mdi":12,"rsi":40},
        {"Open":1.12,"High":1.13,"Low":1.114,"Close":1.118,"atr":0.001,
         "ema_pullback":1.116,"ema50":1.125,"ema200":1.105,"adx":23,"pdi":32,"mdi":11,"rsi":47},
        {"Open":1.10,"High":1.103,"Low":1.098,"Close":1.100,"atr":0.001,
         "ema_pullback":1.1,"ema50":1.13,"ema200":1.11,"adx":22,"pdi":30,"mdi":12,"rsi":50},
    ]
    prepared = pd.DataFrame(rows)
    frame = prepared[["Open","High","Low","Close"]].copy()
    p = {"pullback_ema":20,"rsi_trigger":45.0,"adx_min":20.0,
         "atr_stop":1.5,"reward_risk":1.5,"max_hold_bars":48}
    result = backtest(frame, p, prepared=prepared)
    assert result["trades"] == result["entries"] == result["exits"] == 1
    assert result["stop_exits"] == 1
    assert result["target_exits"] == 0
    assert result["open_position_end"] is False
    assert result["expectancy_R"] < 0


def write_dataset(tmp_path, timestamps):
    data = tmp_path / "EURUSD_M5.csv"
    manifest = tmp_path / "EURUSD_M5.manifest.json"
    ts = pd.to_datetime(timestamps, utc=True)
    raw = pd.DataFrame({
        "timestamp": ts, "open":[1.1000]*len(ts), "high":[1.1002]*len(ts),
        "low":[1.0998]*len(ts), "close":[1.1001]*len(ts), "volume":[10.0]*len(ts),
    })
    raw.to_csv(data, index=False)
    record = {
        "dataset_id":"test-fixture", "symbol":"EURUSD", "timeframe":"M5",
        "source":"HistData.com Generic ASCII M1 resampled to M5",
        "source_hash":"test-source-hash", "rows":len(raw),
        "start":ts.min().isoformat(), "end":ts.max().isoformat(),
        "quality_status":"PASS",
        "data_sha256":hashlib.sha256(data.read_bytes()).hexdigest(),
    }
    manifest.write_text(json.dumps(record), encoding="utf-8")
    return data, manifest


def test_loader_accepts_only_hash_verified_2022_to_2024_real_data(tmp_path):
    data, manifest = write_dataset(tmp_path, [
        "2022-01-03T00:00:00Z","2023-01-03T00:00:00Z","2024-01-03T00:00:00Z",
    ])
    frame, doc, data_hash, manifest_hash = _load(data, manifest)
    assert len(frame) == 3
    assert isinstance(frame.index, pd.DatetimeIndex)
    assert str(frame.index.tz) == "UTC"
    assert doc["quality_status"] == "PASS"
    assert len(data_hash) == len(manifest_hash) == 64


def test_loader_rejects_2025_row_instead_of_reusing_old_validation(tmp_path):
    data, manifest = write_dataset(tmp_path, [
        "2022-01-03T00:00:00Z","2023-01-03T00:00:00Z","2024-01-03T00:00:00Z",
        "2025-01-01T00:00:00Z",
    ])
    with pytest.raises(ValueError, match="G17_DATA_WINDOW_VIOLATION_2025_OR_OUT_OF_RANGE_ROW"):
        _load(data, manifest)


def test_loader_rejects_manifest_hash_mismatch(tmp_path):
    data, manifest = write_dataset(tmp_path, [
        "2022-01-03T00:00:00Z","2023-01-03T00:00:00Z","2024-01-03T00:00:00Z",
    ])
    record = json.loads(manifest.read_text(encoding="utf-8"))
    record["data_sha256"] = "0" * 64
    manifest.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="G17_DATA_SHA256_MISMATCH"):
        _load(data, manifest)
