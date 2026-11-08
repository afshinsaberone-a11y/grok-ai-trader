import hashlib
import json

import pandas as pd
import pytest

import research.optimization.xauusd_intraday_preregistered_discovery_v1 as discovery

from research.optimization.xauusd_intraday_preregistered_discovery_v1 import (
    CANDIDATES,
    build_features,
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
    assert len(CANDIDATES) == 11
    assert len({candidate["id"] for candidate in CANDIDATES}) == 11
    assert {candidate["family"] for candidate in CANDIDATES} == {
        "trend_pullback",
        "donchian_breakout",
        "bollinger_mean_reversion",
        "opening_range_breakout",
        "robust_regime_momentum",
        "pullback_structure_break",
    }


def test_london_failed_breakout_is_exact_inverse_of_original_breakout():
    timestamps = pd.to_datetime([
        "2021-01-04T07:55:00Z",
        "2021-01-04T08:00:00Z",
        "2021-01-04T08:05:00Z",
        "2021-01-05T07:55:00Z",
        "2021-01-05T08:00:00Z",
        "2021-01-05T08:05:00Z",
    ], utc=True)
    features = pd.DataFrame({
        "timestamp": timestamps,
        "mid_close": [100.0, 100.0, 101.0, 100.0, 100.0, 89.0],
        "OPENING_RANGE_HIGH": [100.0] * 6,
        "OPENING_RANGE_LOW": [90.0] * 6,
        "ADX": [20.0] * 6,
        "RSI": [50.0] * 6,
    })
    breakout = next(
        candidate for candidate in CANDIDATES
        if candidate["id"] == "london_opening_range_breakout"
    )
    failed_breakout = next(
        candidate for candidate in CANDIDATES
        if candidate["id"] == "london_opening_range_failed_breakout"
    )
    assert build_signals(features, breakout).tolist() == [0, 0, 1, 0, 0, -1]
    assert build_signals(features, failed_breakout).tolist() == [0, 0, -1, 0, 0, 1]


def test_robust_regime_momentum_requires_confirmed_m5_h1_regimes_and_pullback():
    timestamps = pd.date_range("2021-01-04T08:00:00Z", periods=5, freq="5min")
    features = pd.DataFrame({
        "timestamp": timestamps,
        "mid_open": [100.0, 100.3, 100.2, 101.0, 101.0],
        "mid_close": [100.1, 100.2, 100.8, 100.9, 100.2],
        "mid_low": [99.9, 99.7, 100.1, 100.8, 100.0],
        "mid_high": [100.2, 100.4, 100.9, 101.2, 101.1],
        "EMA20": [100.0, 100.0, 100.0, 101.0, 101.0],
        "EMA50": [99.0, 99.0, 99.0, 102.0, 102.0],
        "ATR": [1.0] * 5,
        "ATR_RATIO": [1.0] * 5,
        "ADX": [25.0] * 5,
        "RSI": [50.0] * 5,
        "H1_TREND_UP": [True, True, True, False, False],
        "H1_TREND_DOWN": [False, False, False, False, True],
    })
    candidate = next(
        item for item in CANDIDATES
        if item["id"] == "robust_regime_momentum_v1"
    )
    assert build_signals(features, candidate).tolist() == [0, 0, 1, 0, -1]


def test_h1_regime_uses_only_complete_previous_utc_hour():
    periods = 203 * 12
    timestamps = pd.date_range(
        "2021-01-01T00:00:00Z", periods=periods, freq="5min"
    )
    # Remove the final M5 bar of hour 201; that hour must not be consumed
    # as a completed H1 candle by the next hour's M5 signals.
    remove_index = 201 * 12 + 11
    timestamps = timestamps.delete(remove_index)
    rows = []
    for i, timestamp in enumerate(timestamps):
        mid = 2000.0 + i * 0.01
        rows.append({
            "timestamp": timestamp,
            "bid_open": mid - 0.05,
            "bid_high": mid + 0.20,
            "bid_low": mid - 0.20,
            "bid_close": mid,
            "ask_open": mid + 0.05,
            "ask_high": mid + 0.30,
            "ask_low": mid - 0.10,
            "ask_close": mid + 0.10,
            "spread_open": 0.10,
            "spread_close": 0.10,
        })
    features = build_features(pd.DataFrame(rows))
    before_incomplete = features.loc[
        features["timestamp"].eq(pd.Timestamp("2021-01-09T09:00:00Z")),
        "H1_TREND_UP",
    ].iloc[0]
    after_incomplete = features.loc[
        features["timestamp"].eq(pd.Timestamp("2021-01-09T10:00:00Z")),
        "H1_TREND_UP",
    ].iloc[0]
    assert before_incomplete == True
    assert pd.isna(after_incomplete)


def test_opening_range_breakout_takes_only_first_cross_per_utc_day():
    timestamps = pd.to_datetime([
        "2021-01-04T07:55:00Z",
        "2021-01-04T08:00:00Z",
        "2021-01-04T08:05:00Z",
        "2021-01-04T08:10:00Z",
        "2021-01-04T08:15:00Z",
        "2021-01-04T08:20:00Z",
        "2021-01-05T07:55:00Z",
        "2021-01-05T08:00:00Z",
        "2021-01-05T08:05:00Z",
    ], utc=True)
    features = pd.DataFrame({
        "timestamp": timestamps,
        "mid_close": [101.0, 101.0, 103.0, 104.0, 97.0, 97.0, 101.0, 101.0, 97.0],
        "OPENING_RANGE_HIGH": [102.0] * 9,
        "OPENING_RANGE_LOW": [98.0] * 9,
        "ADX": [20.0] * 9,
        "RSI": [50.0] * 9,
    })
    candidate = {
        "family": "opening_range_breakout",
        "atr_stop_mult": 1.5,
        "reward_risk": 2.0,
        "max_holding_bars": 36,
    }
    signals = build_signals(features, candidate).tolist()
    assert signals == [0, 0, 1, 0, 0, 0, 0, 0, -1]


def test_opening_range_features_require_all_twelve_m5_bars():
    timestamps = list(pd.date_range("2021-01-04T07:00:00Z", periods=12, freq="5min"))
    timestamps += [pd.Timestamp("2021-01-04T08:00:00Z")]
    timestamps += [
        ts for ts in pd.date_range("2021-01-05T07:00:00Z", periods=12, freq="5min")
        if ts.minute != 55
    ]
    timestamps += [pd.Timestamp("2021-01-05T08:00:00Z")]
    rows = []
    for i, timestamp in enumerate(timestamps):
        bid = 2000.0 + i * 0.01
        rows.append({
            "timestamp": timestamp,
            "bid_open": bid,
            "bid_high": bid + 0.5,
            "bid_low": bid - 0.5,
            "bid_close": bid + 0.1,
            "ask_open": bid + 0.1,
            "ask_high": bid + 0.6,
            "ask_low": bid - 0.4,
            "ask_close": bid + 0.2,
            "spread_open": 0.1,
            "spread_close": 0.1,
        })
    features = build_features(pd.DataFrame(rows))
    day1 = features.loc[features["timestamp"].eq(pd.Timestamp("2021-01-04T08:00:00Z"))].iloc[0]
    day2 = features.loc[features["timestamp"].eq(pd.Timestamp("2021-01-05T08:00:00Z"))].iloc[0]
    assert pd.notna(day1["OPENING_RANGE_HIGH"])
    assert pd.notna(day1["OPENING_RANGE_LOW"])
    assert pd.isna(day2["OPENING_RANGE_HIGH"])
    assert pd.isna(day2["OPENING_RANGE_LOW"])


def test_donchian_55_exit_only_variant_changes_only_reward_risk():
    baseline = next(
        candidate for candidate in CANDIDATES
        if candidate["id"] == "donchian_55_trend"
    )
    variant = next(
        candidate for candidate in CANDIDATES
        if candidate["id"] == "donchian_55_trend_rr15_exit_only"
    )
    baseline_without_id = {k: v for k, v in baseline.items() if k != "id"}
    variant_without_id_or_rr = {
        k: v for k, v in variant.items() if k not in {"id", "reward_risk"}
    }
    baseline_without_rr = {
        k: v for k, v in baseline_without_id.items() if k != "reward_risk"
    }
    assert variant_without_id_or_rr == baseline_without_rr
    assert baseline["reward_risk"] == 2.5
    assert variant["reward_risk"] == 1.5


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


def test_training_years_reject_2024_leakage():
    train_with_2024 = pd.DataFrame({
        "timestamp": pd.to_datetime([
            "2021-01-04T00:00:00Z",
            "2022-01-04T00:00:00Z",
            "2023-01-04T00:00:00Z",
            "2024-01-04T00:00:00Z",
        ], utc=True)
    })
    with pytest.raises(ValueError, match="TRAINING_YEARS_MUST_BE_2021_2023"):
        run_discovery(
            train_with_2024,
            None,
            commission_usd_per_oz=0.08,
            slippage_usd_per_oz_per_side=0.10,
        )


def test_training_only_cli_never_calls_2025_loader(tmp_path, monkeypatch):
    train = pd.DataFrame({
        "timestamp": pd.to_datetime([
            "2021-01-04T00:00:00Z",
            "2022-01-04T00:00:00Z",
            "2023-01-04T00:00:00Z",
        ], utc=True)
    })
    report = {
        "status": "NO_TRAIN_CANDIDATE_PASSED_BASE_AND_STRESS_GATES",
        "candidate_count": len(CANDIDATES),
        "training_summary": {
            "all_gates_passed": False,
            "qualified_candidate_count": 0,
        },
        "selected_on_training_only": None,
        "validation": None,
        "data_policy": {
            "2024_loaded": False,
            "2025_loaded": False,
            "2026_loaded": False,
        },
        "promotion": {"demo_authorized": False, "orders_submitted": False},
    }
    monkeypatch.setattr(discovery, "load_training", lambda _root: (train, []))

    def fail_if_validation_is_loaded(_root):
        pytest.fail("2025 validation loader must not be called in training-only mode")

    monkeypatch.setattr(discovery, "load_validation", fail_if_validation_is_loaded)
    monkeypatch.setattr(discovery, "run_discovery", lambda *_args, **_kwargs: report)
    output = tmp_path / "training-only.json"
    exit_code = discovery.main([
        "--train-root", str(tmp_path),
        "--training-only",
        "--commission-usd-per-oz-round-turn", "0.08",
        "--slippage-usd-per-oz-per-side", "0.10",
        "--output", str(output),
    ])
    assert exit_code == 0
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["validation"] is None
    assert saved["data_policy"]["2025_loaded"] is False

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



def test_pullback_structure_break_requires_prior_pullback_and_breaks_prior_three_bar_structure():
    timestamps = pd.date_range("2021-01-04T08:00:00Z", periods=8, freq="5min")
    features = pd.DataFrame({
        "timestamp": timestamps,
        "mid_open": [100.0] * 8,
        "mid_close": [100.0, 100.2, 99.8, 100.1, 100.0, 101.0, 100.0, 98.0],
        "mid_low": [99.8, 99.9, 99.0, 99.7, 99.6, 99.8, 99.7, 98.0],
        "mid_high": [100.2, 100.4, 100.1, 100.3, 100.2, 101.2, 100.1, 100.0],
        "EMA20": [100.0] * 8,
        "EMA50": [99.0, 99.0, 99.0, 99.0, 99.0, 99.0, 99.0, 101.0],
        "ATR": [1.0] * 8,
        "ADX": [25.0] * 8,
        "H1_TREND_UP": [True] * 7 + [False],
        "H1_TREND_DOWN": [False] * 7 + [True],
    })
    candidate = next(
        item for item in CANDIDATES
        if item["id"] == "h1_m5_pullback_structure_break_v1"
    )
    signals = build_signals(features, candidate).tolist()
    # Bar 5 breaks the prior three-bar high after a prior pullback.
    # Bar 7 is a valid short structure break with completed H1 down regime.
    assert signals[5] == 1
    assert signals[7] == -1


def test_pullback_structure_break_does_not_use_current_bar_in_structure_reference():
    timestamps = pd.date_range("2021-01-04T08:00:00Z", periods=5, freq="5min")
    features = pd.DataFrame({
        "timestamp": timestamps,
        "mid_open": [100.0] * 5,
        "mid_close": [100.0, 100.0, 99.8, 100.0, 100.3],
        "mid_low": [99.8, 99.7, 99.0, 99.8, 99.9],
        "mid_high": [100.2, 100.1, 100.0, 100.2, 105.0],
        "EMA20": [100.0] * 5,
        "EMA50": [99.0] * 5,
        "ATR": [1.0] * 5,
        "ADX": [25.0] * 5,
        "H1_TREND_UP": [True] * 5,
        "H1_TREND_DOWN": [False] * 5,
    })
    candidate = next(
        item for item in CANDIDATES
        if item["id"] == "h1_m5_pullback_structure_break_v1"
    )
    signals = build_signals(features, candidate)
    # A large current-bar high cannot raise its own prior swing-high threshold.
    assert signals.iloc[4] == 1
