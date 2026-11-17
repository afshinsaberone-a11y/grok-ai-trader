from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from research.real_data.xauusd_h1_coverage_audit_g18 import audit


def write_fixture(tmp_path, *, years=(2021, 2022, 2023, 2024), bad_spread=False):
    data = tmp_path / "XAUUSD_H1_BIDASK_fixture.csv"
    manifest_path = tmp_path / "XAUUSD_H1_BIDASK_fixture.manifest.json"
    rows = []
    for year in years:
        for month in range(1, 11):
            start = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
            for hour in range(350):
                ts = start + pd.Timedelta(hours=hour)
                bid = 2000.0 + len(rows) * 0.001
                spread = -0.1 if bad_spread and len(rows) == 0 else 0.3
                rows.append({
                    "timestamp": ts.isoformat(),
                    "bid_open": bid, "bid_high": bid + 0.5,
                    "bid_low": bid - 0.5, "bid_close": bid + 0.1,
                    "ask_open": bid + spread, "ask_high": bid + 0.5 + spread,
                    "ask_low": bid - 0.5 + spread, "ask_close": bid + 0.1 + spread,
                    "bid_volume": 1.0, "ask_volume": 1.1,
                    "spread_open": spread, "spread_close": spread,
                })
    frame = pd.DataFrame(rows)
    frame.to_csv(data, index=False)

    timestamps = pd.to_datetime(frame.timestamp, utc=True)
    gap_count = int((timestamps.diff() > pd.Timedelta(hours=1)).sum())
    files = [{"period_start": "2021-01-01", "side": "BID", "sha256": "fixture"}]
    source_hash = hashlib.sha256(json.dumps(files, sort_keys=True).encode("utf-8")).hexdigest()
    record = {
        "schema": "forexai.real_data.xauusd_bidask_h1.v1",
        "status": "INGESTION_ONLY_COVERAGE_REVIEW_REQUIRED",
        "symbol": "XAUUSD", "timeframe": "H1",
        "source": "Dukascopy historical BID/ASK BI5 bars",
        "requested_start_utc": f"{min(years)}-01-01",
        "requested_end_exclusive_utc": pd.Timestamp(
            year=max(years)+1, month=1, day=1, tz="UTC"
        ).isoformat(),
        "start_inclusive_utc": timestamps.min().isoformat(),
        "end_inclusive_observed_utc": timestamps.max().isoformat(),
        "rows": len(frame), "source_files": files,
        "source_hash_sha256": source_hash,
        "data_sha256": hashlib.sha256(data.read_bytes()).hexdigest(),
        "gap_audit": {"gap_count": gap_count},
        "synthetic_data": False, "backtest_run": False,
    }
    manifest_path.write_text(json.dumps(record), encoding="utf-8")
    return data, manifest_path


def test_audit_accepts_hash_verified_bidask_data_for_all_discovery_years(tmp_path):
    data, manifest = write_fixture(tmp_path)
    result = audit(data, manifest)

    assert result["status"] == "REAL_DATA_COVERAGE_AUDIT_PASS"
    assert result["symbol"] == "XAUUSD"
    assert result["timeframe"] == "H1"
    assert result["data_policy"]["real_bid_ask_bars"] is True
    assert result["data_policy"]["2025_loaded"] is False
    assert result["data_policy"]["2026_plus_loaded"] is False
    assert result["data_policy"]["backtest_run"] is False
    assert result["years"]["2021"]["month_count"] == 10
    assert result["spread_open"]["median_usd_per_oz"] == pytest.approx(0.3)


def test_audit_rejects_dataset_hash_mismatch(tmp_path):
    data, manifest = write_fixture(tmp_path)
    record = json.loads(manifest.read_text())
    record["data_sha256"] = "0" * 64
    manifest.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="G18_DATA_SHA256_MISMATCH"):
        audit(data, manifest)


def test_audit_rejects_negative_spread(tmp_path):
    data, manifest = write_fixture(tmp_path, bad_spread=True)
    with pytest.raises(ValueError, match="G18_NEGATIVE_SPREAD"):
        audit(data, manifest)


def test_audit_rejects_missing_discovery_year(tmp_path):
    data, manifest = write_fixture(tmp_path, years=(2021, 2022, 2023))
    with pytest.raises(ValueError, match="G18_YEAR_SET_MISMATCH"):
        audit(data, manifest)


def test_audit_rejects_spread_manifest_reconciliation_mismatch(tmp_path):
    data, manifest = write_fixture(tmp_path)
    frame = pd.read_csv(data)
    frame.loc[0, "spread_open"] = 0.25
    frame.to_csv(data, index=False)
    record = json.loads(manifest.read_text())
    record["data_sha256"] = hashlib.sha256(data.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="G18_OPEN_SPREAD_RECONCILIATION_FAIL"):
        audit(data, manifest)
