from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from research.real_data.dukascopy_ingest import DukascopyIngestError, DukascopyM1Ingestor
from research.real_data.manifest import build_manifest, sha256_file
from research.real_data.normalizer import canonicalize_ohlcv, resample_ohlcv
from research.real_data.validator import validate_ohlcv


def fixture_m1(rows: int = 15) -> pd.DataFrame:
    ts = pd.date_range("2026-01-05T00:00:00Z", periods=rows, freq="min")
    close = [1.1000 + i * 0.00001 for i in range(rows)]
    return pd.DataFrame({
        "timestamp": ts,
        "open": close,
        "high": [p + 0.00002 for p in close],
        "low": [p - 0.00002 for p in close],
        "close": close,
        "volume": [1.0] * rows,
        "spread": [float("nan")] * rows,
    })


def test_valid_ohlc():
    report = validate_ohlcv(fixture_m1(), symbol="EURUSD", timeframe="M1")
    assert report.status == "PASS"
    assert report.invalid_ohlc == 0


def test_invalid_ohlc():
    df = fixture_m1()
    df.loc[0, "high"] = df.loc[0, "low"] - 0.0001
    report = validate_ohlcv(df)
    assert report.status == "FAIL"
    assert report.invalid_ohlc == 1


def test_duplicate_timestamps():
    df = fixture_m1()
    df.loc[1, "timestamp"] = df.loc[0, "timestamp"]
    report = validate_ohlcv(df)
    assert report.status == "FAIL"
    assert report.duplicates == 1


def test_unsorted_timestamps():
    df = fixture_m1().iloc[[1, 0] + list(range(2, 15))].reset_index(drop=True)
    report = validate_ohlcv(df)
    assert report.status == "FAIL"
    assert report.unsorted_timestamps == 1


def test_timezone_normalization():
    df = fixture_m1().copy()
    df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/London")
    canonical = canonicalize_ohlcv(df)
    assert str(canonical["timestamp"].dt.tz) == "UTC"


def test_missing_bars():
    df = fixture_m1()
    df = df.drop(index=[5]).reset_index(drop=True)
    report = validate_ohlcv(df)
    assert report.missing_bars == 1


def test_m1_to_m5():
    result = resample_ohlcv(fixture_m1(15), "5min")
    assert len(result) == 3
    assert result.loc[0, "open"] == pytest.approx(1.1000)
    assert result.loc[0, "close"] == pytest.approx(1.10004)
    assert result.loc[0, "high"] == pytest.approx(1.10006)
    assert result.loc[0, "low"] == pytest.approx(1.09998)


def test_m1_to_m15():
    result = resample_ohlcv(fixture_m1(15), "15min")
    assert len(result) == 1
    assert result.loc[0, "open"] == pytest.approx(1.1000)
    assert result.loc[0, "close"] == pytest.approx(1.10014)


def test_manifest_and_sha256(tmp_path: Path):
    raw = tmp_path / "raw.bi5"
    raw.write_bytes(b"real-source-fixture")
    digest = sha256_file(raw)
    assert len(digest) == 64
    manifest = build_manifest(
        fixture_m1(), dataset_id="fixture", symbol="EURUSD", timeframe="M1",
        source="Dukascopy", source_hash=digest, quality_status="PASS",
    )
    assert manifest["source_hash"] == digest
    assert manifest["timezone"] == "UTC"


def test_missing_real_dataset_fails(tmp_path: Path):
    ingestor = DukascopyM1Ingestor(tmp_path)
    with pytest.raises(DukascopyIngestError, match="REAL_DATA_REQUIRED"):
        ingestor.build_m1([])


def test_synthetic_fallback_rejected():
    import inspect
    from research.real_data import dukascopy_ingest

    source = inspect.getsource(dukascopy_ingest)
    assert "np.random" not in source
    assert "synthetic" not in source.lower()
