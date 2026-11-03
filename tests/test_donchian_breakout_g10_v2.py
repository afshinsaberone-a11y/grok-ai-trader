import json
from pathlib import Path

import pandas as pd
import pytest

from research.optimization.donchian_breakout_g10_v2 import (
    _canonical_sha256,
    _is_gate,
    _stress_gate,
    _validation_gate,
    _verify_input,
)


def good_metrics():
    return {
        "trades": 120,
        "profit_factor": 1.25,
        "expectancy_R": 0.03,
        "total_R": 3.6,
        "max_dd_pct": 12.0,
        "final_equity": 10180.0,
    }


def test_g10_v2_is_gate_requires_all_three_discovery_years():
    good = good_metrics()
    assert _is_gate({"2022": good, "2023": good, "2024": good})
    assert not _is_gate({"2022": good, "2023": good})
    weak = {**good, "profit_factor": 1.049}
    assert not _is_gate({"2022": good, "2023": weak, "2024": good})


def test_g10_v2_validation_is_pass_fail_and_requires_positive_equity():
    assert _validation_gate(good_metrics()) == (True, [])
    negative = {**good_metrics(), "final_equity": 9990.0}
    ok, reasons = _validation_gate(negative)
    assert not ok
    assert "final_equity<=initial_equity" in reasons


def test_g10_v2_stress_gate_requires_all_four_years():
    good = good_metrics()
    passed, rejected = _stress_gate({
        "2022": good, "2023": good, "2024": good, "2025": good
    })
    assert passed and not rejected
    weak = {**good, "expectancy_R": 0.0}
    passed, rejected = _stress_gate({
        "2022": good, "2023": good, "2024": weak, "2025": good
    })
    assert not passed
    assert "2024" in rejected


def test_g10_v2_canonical_config_hash_is_order_independent():
    assert _canonical_sha256({"a": 1, "b": 2}) == _canonical_sha256({"b": 2, "a": 1})


def test_g10_v2_rejects_oos_timestamp_even_when_manifest_hash_matches(tmp_path: Path):
    dataset = tmp_path / "EURUSD_M5.csv"
    manifest_path = tmp_path / "EURUSD_M5.manifest.json"
    frame = pd.DataFrame({
        "timestamp": pd.to_datetime(["2022-01-03T00:00:00Z", "2026-01-02T00:00:00Z"]),
        "open": [1.1, 1.1],
        "high": [1.101, 1.101],
        "low": [1.099, 1.099],
        "close": [1.1001, 1.1001],
        "volume": [10.0, 10.0],
        "spread": [float("nan"), float("nan")],
    })
    frame.to_csv(dataset, index=False)
    import hashlib
    data_sha = hashlib.sha256(dataset.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps({
        "dataset_id": "fixture",
        "symbol": "EURUSD",
        "timeframe": "M5",
        "source": "HistData.com Generic ASCII M1 resampled to M5",
        "quality_status": "PASS",
        "rows": 2,
        "data_sha256": data_sha,
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="G10_OOS_POLICY_VIOLATION_2026_DATA_PRESENT"):
        _verify_input(dataset, manifest_path)


def test_g10_v2_rejects_modified_dataset_against_manifest(tmp_path: Path):
    dataset = tmp_path / "EURUSD_M5.csv"
    manifest_path = tmp_path / "EURUSD_M5.manifest.json"
    frame = pd.DataFrame({
        "timestamp": pd.date_range("2022-01-03T00:00:00Z", periods=2, freq="5min"),
        "open": [1.1, 1.1],
        "high": [1.101, 1.101],
        "low": [1.099, 1.099],
        "close": [1.1001, 1.1001],
        "volume": [10.0, 10.0],
        "spread": [float("nan"), float("nan")],
    })
    frame.to_csv(dataset, index=False)
    manifest_path.write_text(json.dumps({
        "symbol": "EURUSD",
        "timeframe": "M5",
        "source": "HistData.com",
        "quality_status": "PASS",
        "rows": 2,
        "data_sha256": "0" * 64,
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="G10_V2_DATASET_SHA256_MISMATCH"):
        _verify_input(dataset, manifest_path)
