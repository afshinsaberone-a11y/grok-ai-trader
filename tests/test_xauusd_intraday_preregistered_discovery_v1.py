import hashlib
import json

import pandas as pd
import pytest

from research.optimization.xauusd_intraday_preregistered_discovery_v1 import (
    CANDIDATES,
    build_signals,
    load_validation,
    read_verified_dataset,
    run_discovery,
    run_passes,
)


def _one_bar_frame(timestamp="2021-01-04T23:00:00Z"):
    return pd.DataFrame([{
        "timestamp": timestamp,
        "bid_open": 2000.0,
        "bid_high": 2001.0,
        "bid_low": 1999.0,
        "bid_close": 2000.5,
        "ask_open": 2000.1,
        "ask_high": 2001.1,
        "ask_low": 1999.1,
        "ask_close": 2000.6,
        "spread_open": 0.1,
        "spread_close": 0.1,
    }])


def _write_verified_pair(tmp_path, *, synthetic=False, filled=0, hash_override=None):
    csv_path = tmp_path / "XAUUSD_M5_BIDASK_20210101_20220101.csv"
    manifest_path = tmp_path / "XAUUSD_M5_BIDASK_20210101_20220101.manifest.json"
    frame = _one_bar_frame()
    frame.to_csv(csv_path, index=False)
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    manifest = {
        "status": "FULL_YEAR_DATASET_ASSEMBLED_GAP_REVIEW_REQUIRED",
        "timeframe": "M5",
        "symbol": None,
        "synthetic_data": synthetic,
        "filled_bars": filled,
        "backtest_run": False,
        "data_sha256": hash_override or digest,
        "rows": 1,
        "first_utc": "2021-01-04T23:00:00+00:00",
        "last_utc": "2021-01-04T23:00:00+00:00",
        "start_inclusive_utc": "2021-01-01T00:00:00+00:00",
        "end_exclusive_utc": "2022-01-01T00:00:00+00:00",
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return csv_path, manifest_path


def test_candidate_hypothesis_set_is_small_and_fixed():
    assert len(CANDIDATES) == 6
    assert len({candidate["id"] for candidate in CANDIDATES}) == 6
    assert {candidate["family"] for candidate in CANDIDATES} == {
        "trend_pullback",
        "donchian_breakout",
        "bollinger_mean_reversion",
    }


def test_training_dataset_hash_scope_and_real_data_are_verified(tmp_path):
    csv_path, manifest_path = _write_verified_pair(tmp_path)
    frame, audit = read_verified_dataset(
        csv_path,
        manifest_path,
        start="2021-01-01",
        end="2022-01-01",
        expected_year=2021,
    )
    assert len(frame) == 1
    assert audit["rows"] == 1
    assert audit["data_sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()


def test_training_dataset_hash_mismatch_is_rejected(tmp_path):
    csv_path, manifest_path = _write_verified_pair(tmp_path, hash_override="0" * 64)
    with pytest.raises(ValueError, match="DATA_HASH_MISMATCH"):
        read_verified_dataset(
            csv_path,
            manifest_path,
            start="2021-01-01",
            end="2022-01-01",
            expected_year=2021,
        )


@pytest.mark.parametrize(
    ("synthetic", "filled"),
    [(True, 0), (False, 1)],
)
def test_synthetic_or_filled_source_is_rejected(tmp_path, synthetic, filled):
    csv_path, manifest_path = _write_verified_pair(
        tmp_path, synthetic=synthetic, filled=filled
    )
    with pytest.raises(ValueError, match="SYNTHETIC_OR_FILLED_DATA_REJECTED"):
        read_verified_dataset(
            csv_path,
            manifest_path,
            start="2021-01-01",
            end="2022-01-01",
            expected_year=2021,
        )


def test_run_gate_rejects_gap_assumptions_and_non_positive_expectancy():
    good = {
        "trades": 100,
        "profit_factor": 1.2,
        "expectancy_R": 0.05,
        "max_dd_pct": 10.0,
        "gap_exit_assumption_trades": 0,
        "entries_equal_exits": True,
    }
    assert run_passes(good, min_trades=50, min_pf=1.05, max_dd_pct=20.0) == (True, [])

    bad = dict(good, gap_exit_assumption_trades=1)
    passed, reasons = run_passes(bad, min_trades=50, min_pf=1.05, max_dd_pct=20.0)
    assert passed is False
    assert "gap_exit_assumptions_present" in reasons

    bad = dict(good, expectancy_R=0.0)
    passed, reasons = run_passes(bad, min_trades=50, min_pf=1.05, max_dd_pct=20.0)
    assert passed is False
    assert "expectancy_not_positive" in reasons


def test_signal_builder_never_emits_entries_outside_day_session():
    features = pd.DataFrame({
        "timestamp": pd.to_datetime([
            "2021-01-04T06:00:00Z",
            "2021-01-04T07:00:00Z",
            "2021-01-04T19:00:00Z",
            "2021-01-04T20:00:00Z",
        ], utc=True),
        "mid_close": [100.0, 101.0, 102.0, 103.0],
        "EMA50": [101.0, 101.0, 101.0, 101.0],
        "EMA200": [100.0, 100.0, 100.0, 100.0],
        "EMA20": [101.0, 100.0, 101.5, 102.5],
        "RSI": [60.0, 60.0, 60.0, 60.0],
        "ADX": [25.0, 25.0, 25.0, 25.0],
    })
    candidate = {
        "family": "trend_pullback",
        "ema_fast": 50,
        "ema_slow": 200,
        "pullback_ema": 20,
        "rsi_min": 50,
        "adx_min": 18,
    }
    signals = build_signals(features, candidate)
    assert signals.iloc[0] == 0
    assert signals.iloc[1] == 1
    assert signals.iloc[3] == 0


def test_train_and_validation_periods_reject_2024_or_2026_leakage():
    train_with_2024 = pd.DataFrame({
        "timestamp": pd.to_datetime([
            "2021-01-04T00:00:00Z",
            "2022-01-04T00:00:00Z",
            "2023-01-04T00:00:00Z",
            "2024-01-04T00:00:00Z",
        ], utc=True)
    })
    validation = pd.DataFrame({
        "timestamp": pd.to_datetime(["2025-01-04T00:00:00Z"], utc=True)
    })
    with pytest.raises(ValueError, match="TRAINING_YEARS_MUST_BE_2021_2023"):
        run_discovery(
            train_with_2024,
            validation,
            commission_usd_per_oz=0.08,
            slippage_usd_per_oz_per_side=0.10,
        )

    train = pd.DataFrame({
        "timestamp": pd.to_datetime([
            "2021-01-04T00:00:00Z",
            "2022-01-04T00:00:00Z",
            "2023-01-04T00:00:00Z",
        ], utc=True)
    })
    validation_with_2026 = pd.DataFrame({
        "timestamp": pd.to_datetime(["2026-01-04T00:00:00Z"], utc=True)
    })
    with pytest.raises(ValueError, match="VALIDATION_MUST_BE_2025_ONLY"):
        run_discovery(
            train,
            validation_with_2026,
            commission_usd_per_oz=0.08,
            slippage_usd_per_oz_per_side=0.10,
        )


def _write_2025_quarter(root, shard, start, end, timestamp):
    base = root / f"artifact-{shard}"
    m1_dir = base / "m1-ingest" / "normalized"
    m5_dir = base / "normalized"
    m1_dir.mkdir(parents=True)
    m5_dir.mkdir(parents=True)

    m1_path = m1_dir / "XAUUSD_M1_source.csv"
    m1_path.write_text("test source payload\n", encoding="utf-8")
    m1_hash = hashlib.sha256(m1_path.read_bytes()).hexdigest()
    m1_manifest_path = m1_dir / "XAUUSD_M1_source.manifest.json"
    m1_manifest = {
        "symbol": "XAUUSD",
        "timeframe": "M1",
        "synthetic_data": False,
        "backtest_run": False,
        "data_sha256": m1_hash,
    }
    m1_manifest_path.write_text(json.dumps(m1_manifest), encoding="utf-8")
    m1_manifest_hash = hashlib.sha256(m1_manifest_path.read_bytes()).hexdigest()

    m5_path = m5_dir / f"{shard}.csv"
    _one_bar_frame(timestamp).to_csv(m5_path, index=False)
    m5_hash = hashlib.sha256(m5_path.read_bytes()).hexdigest()
    m5_manifest_path = m5_dir / f"{shard}.manifest.json"
    m5_manifest = {
        "status": "REAL_M5_SHARD_PASS_GAPS_PRESERVED",
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "shard": shard,
        "requested_start_utc": start,
        "requested_end_exclusive_utc": end,
        "synthetic_data": False,
        "filled_bars": 0,
        "backtest_run": False,
        "rows": 1,
        "data_sha256": m5_hash,
        "source_m1_data_sha256": m1_hash,
        "source_m1_manifest_sha256": m1_manifest_hash,
    }
    m5_manifest_path.write_text(json.dumps(m5_manifest), encoding="utf-8")
    m5_manifest_hash = hashlib.sha256(m5_manifest_path.read_bytes()).hexdigest()

    report = {
        "status": "REAL_XAUUSD_M5_FRESH_OOS_SHARD_PASS",
        "shard": shard,
        "m1_path": str(m1_path.relative_to(base)),
        "m1_manifest_path": str(m1_manifest_path.relative_to(base)),
        "m5_path": str(m5_path.relative_to(base)),
        "m5_manifest_path": str(m5_manifest_path.relative_to(base)),
        "m1_sha256": m1_hash,
        "m1_manifest_sha256": m1_manifest_hash,
        "m5_sha256": m5_hash,
        "m5_manifest_sha256": m5_manifest_hash,
        "m1_rows": 5,
        "m5_rows": 1,
        "synthetic_data": False,
        "filled_bars": 0,
        "backtest_run": False,
        "orders_submitted": False,
        "reconciliation_audit": {
            "compared_bars": 1,
            "max_abs_delta": 0.0,
            "tolerance": 1.1e-5,
        },
    }
    (base / "report.json").write_text(json.dumps(report), encoding="utf-8")


def test_load_validation_verifies_and_assembles_only_four_2025_shards(tmp_path):
    shards = (
        ("2025-Q1", "2025-01-01", "2025-04-01", "2025-01-02T00:00:00Z"),
        ("2025-Q2", "2025-04-01", "2025-07-01", "2025-04-02T00:00:00Z"),
        ("2025-Q3", "2025-07-01", "2025-10-01", "2025-07-02T00:00:00Z"),
        ("2025-Q4", "2025-10-01", "2026-01-01", "2025-10-02T00:00:00Z"),
    )
    for shard, start, end, timestamp in shards:
        _write_2025_quarter(tmp_path, shard, start, end, timestamp)

    frame, audit = load_validation(tmp_path)
    assert len(frame) == 4
    assert set(frame["timestamp"].dt.year.unique()) == {2025}
    assert [item["shard"] for item in audit["source_shards"]] == [
        "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"
    ]
    assert audit["2026_shards_downloaded"] is False


def test_load_validation_fails_closed_when_one_2025_shard_is_missing(tmp_path):
    _write_2025_quarter(
        tmp_path, "2025-Q1", "2025-01-01", "2025-04-01", "2025-01-02T00:00:00Z"
    )
    with pytest.raises(FileNotFoundError, match="2025_SHARDS_MISSING"):
        load_validation(tmp_path)
