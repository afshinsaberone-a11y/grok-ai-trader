from pathlib import Path
import inspect
import lzma
import struct

import pandas as pd
import pytest

from research.real_data.dukascopy_ingest import DukascopyIngestError, DukascopyM1Ingestor
from research.real_data.manifest import build_manifest, sha256_file
from research.real_data.normalizer import canonicalize_ohlcv, resample_ohlcv
from research.real_data.validator import validate_ohlcv
from strategies.grok_ai_trader import GrokHybridStrategy, fetch_data


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
    report = validate_ohlcv(df, symbol="EURUSD")
    assert report.status == "FAIL"
    assert report.invalid_ohlc == 1


def test_duplicate_timestamps():
    df = fixture_m1()
    df.loc[1, "timestamp"] = df.loc[0, "timestamp"]
    report = validate_ohlcv(df, symbol="EURUSD")
    assert report.status == "FAIL"
    assert report.duplicates == 1


def test_unsorted_timestamps():
    df = fixture_m1().iloc[[1, 0] + list(range(2, 15))].reset_index(drop=True)
    report = validate_ohlcv(df, symbol="EURUSD")
    assert report.status == "FAIL"
    assert report.unsorted_timestamps == 1


def test_timezone_normalization():
    df = fixture_m1().copy()
    df["timestamp"] = df["timestamp"].dt.tz_convert("Europe/London")
    canonical = canonicalize_ohlcv(df, symbol="EURUSD")
    assert str(canonical["timestamp"].dt.tz) == "UTC"


def test_invalid_timestamp():
    df = fixture_m1().copy()
    df["timestamp"] = df["timestamp"].astype(object)
    df.loc[0, "timestamp"] = "not-a-timestamp"
    report = validate_ohlcv(df, symbol="EURUSD")
    assert report.status == "FAIL"
    assert report.nan_values == 1


def test_missing_bars():
    df = fixture_m1().drop(index=[5]).reset_index(drop=True)
    report = validate_ohlcv(df, symbol="EURUSD")
    assert report.missing_bars == 1


def test_weekend_gap_is_not_reported_as_missing_intraday_bars():
    before = pd.date_range("2026-01-09T23:55:00Z", periods=5, freq="min")
    after = pd.date_range("2026-01-12T00:00:00Z", periods=5, freq="min")
    left = fixture_m1(5)
    right = fixture_m1(5)
    left["timestamp"] = before
    right["timestamp"] = after
    report = validate_ohlcv(pd.concat([left, right], ignore_index=True), symbol="EURUSD")
    assert report.missing_bars == 0
    assert report.status == "PASS"


def test_dukascopy_legacy_url_uses_zero_based_month():
    url = DukascopyM1Ingestor.legacy_url_for(pd.Timestamp("2026-02-14").date())
    assert url.endswith("/EURUSD/2026/01/14/BID_candles_min_1.bi5")


def test_dukascopy_bi5_ohlc_field_order(tmp_path: Path):
    # Dukascopy candle BI5 order is seconds, Open, Close, Low, High, Volume.
    payload = struct.pack(">IIIIIf", 60, 110000, 110200, 109900, 110300, 12.5)
    raw_path = tmp_path / "fixture.bi5"
    raw_path.write_bytes(lzma.compress(payload))

    decoded = DukascopyM1Ingestor.decode_m1(raw_path, pd.Timestamp("2026-01-05").date())
    row = decoded.iloc[0]
    assert row["timestamp"] == pd.Timestamp("2026-01-05T00:01:00Z")
    assert row["open"] == pytest.approx(1.10)
    assert row["close"] == pytest.approx(1.102)
    assert row["low"] == pytest.approx(1.099)
    assert row["high"] == pytest.approx(1.103)
    assert row["volume"] == pytest.approx(12.5)


def test_m1_to_m5():
    result = resample_ohlcv(fixture_m1(15), "5min", symbol="EURUSD")
    assert len(result) == 3
    assert result.loc[0, "open"] == pytest.approx(1.1000)
    assert result.loc[0, "close"] == pytest.approx(1.10004)
    assert result.loc[0, "high"] == pytest.approx(1.10006)
    assert result.loc[0, "low"] == pytest.approx(1.09998)


def test_m1_to_m15():
    result = resample_ohlcv(fixture_m1(15), "15min", symbol="EURUSD")
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

    dataset = tmp_path / "dataset.csv"
    fixture_m1().to_csv(dataset, index=False)
    manifest_with_data_hash = build_manifest(
        fixture_m1(), dataset_id="fixture", symbol="EURUSD", timeframe="M1",
        source="Dukascopy", source_hash=digest, quality_status="PASS",
        dataset_path=dataset,
    )
    assert manifest_with_data_hash["data_sha256"] == sha256_file(dataset)


def test_missing_real_dataset_fails(tmp_path: Path):
    ingestor = DukascopyM1Ingestor(tmp_path)
    with pytest.raises(DukascopyIngestError, match="REAL_DATA_REQUIRED"):
        ingestor.build_m1([])


def test_synthetic_fallback_rejected():
    from research.real_data import dukascopy_ingest
    source = inspect.getsource(dukascopy_ingest)
    strategy_source = inspect.getsource(fetch_data)
    assert "np.random" not in source
    assert "yfinance" not in source.lower()
    assert "random.seed" not in source.lower()
    assert "yfinance" not in strategy_source.lower()
    assert "np.random" not in strategy_source



def test_shared_ohlc_pipeline_rejects_xauusd():
    from research.real_data.normalizer import canonicalize_ohlcv, resample_ohlcv
    from research.real_data.research_pipeline import load_real_dataset

    with pytest.raises(ValueError, match="XAUUSD_REQUIRES_PAIRED_BID_ASK_VALIDATOR"):
        validate_ohlcv(fixture_m1(), symbol="XAUUSD")
    with pytest.raises(ValueError, match="XAUUSD_REQUIRES_PAIRED_BID_ASK_NORMALIZER"):
        canonicalize_ohlcv(fixture_m1(), symbol="XAUUSD")
    with pytest.raises(ValueError, match="XAUUSD_REQUIRES_PAIRED_BID_ASK_RESAMPLER"):
        resample_ohlcv(fixture_m1(), "5min", symbol="XAUUSD")
    with pytest.raises(ValueError, match="SYMBOL_PIPELINE_UNSUPPORTED"):
        load_real_dataset("not-read-because-symbol-is-invalid.csv", symbol="XAUUSD")


def test_common_symbol_arguments_are_explicit():
    with pytest.raises(TypeError):
        validate_ohlcv(fixture_m1())
    with pytest.raises(TypeError):
        canonicalize_ohlcv(fixture_m1())
    with pytest.raises(TypeError):
        resample_ohlcv(fixture_m1(), "5min")


def test_real_dataset_loader_rejects_sidecar_manifest_symbol_mismatch(tmp_path: Path):
    import json
    from research.real_data.research_pipeline import load_real_dataset

    dataset = tmp_path / "EURUSD_M1_fixture.csv"
    fixture_m1().to_csv(dataset, index=False)
    manifest = {
        "symbol": "XAUUSD",
        "timeframe": "M1",
        "quality_status": "PASS",
        "data_sha256": sha256_file(dataset),
    }
    dataset.with_suffix(".manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="DATASET_MANIFEST_SYMBOL_MISMATCH"):
        load_real_dataset(dataset, symbol="EURUSD", timeframe="M1")


def test_strategy_rejects_xauusd_on_eurusd_signal_engine():
    ts = pd.date_range("2026-01-05T07:00:00Z", periods=3, freq="min")
    data = pd.DataFrame(
        {"Open": [2300.0] * 3, "High": [2301.0] * 3,
         "Low": [2299.0] * 3, "Close": [2300.0] * 3},
        index=ts,
    )
    with pytest.raises(ValueError, match="STRATEGY_SYMBOL_UNSUPPORTED"):
        GrokHybridStrategy().backtest_simple(data, symbol="XAUUSD")

def test_strategy_requires_explicit_real_dataset(tmp_path: Path):
    with pytest.raises((FileNotFoundError, ValueError), match="REAL_DATA_REQUIRED"):
        fetch_data(tmp_path / "does-not-exist.csv", symbol="EURUSD")


def test_strategy_does_not_trade_before_atr_warmup():
    ts = pd.date_range("2026-01-05T07:00:00Z", periods=10, freq="min")
    prices = [1.10 + i * 0.0001 for i in range(10)]
    data = pd.DataFrame({
        "Open": prices,
        "High": [p + 0.0002 for p in prices],
        "Low": [p - 0.0002 for p in prices],
        "Close": prices,
    }, index=ts)
    result = GrokHybridStrategy().backtest_simple(data, symbol="EURUSD")
    assert result["trades"] == 0


def test_jetta_empty_response_retries_then_succeeds(tmp_path: Path, monkeypatch):
    from research.real_data import dukascopy_ingest

    class FakeResponse:
        def __init__(self, payload: bytes):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self.payload

    payloads = [b"", b"", b"{}"]
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(timeout)
        return FakeResponse(payloads.pop(0))

    monkeypatch.setattr(dukascopy_ingest, "urlopen", fake_urlopen)
    monkeypatch.setattr(dukascopy_ingest.time, "sleep", lambda _delay: None)
    ingestor = DukascopyM1Ingestor(tmp_path, retries=3)
    day = pd.Timestamp("2026-01-05").date()
    destination = tmp_path / "jetta.json"

    assert ingestor._download("https://example.invalid/day", destination, day=day)
    assert len(calls) == 3
    assert destination.read_bytes() == b"{}"


def test_jetta_empty_response_exhaustion_fails_closed(tmp_path: Path, monkeypatch):
    from research.real_data import dukascopy_ingest

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b""

    calls = []

    def fake_urlopen(request, timeout):
        calls.append(timeout)
        return FakeResponse()

    monkeypatch.setattr(dukascopy_ingest, "urlopen", fake_urlopen)
    monkeypatch.setattr(dukascopy_ingest.time, "sleep", lambda _delay: None)
    ingestor = DukascopyM1Ingestor(tmp_path, retries=2)
    day = pd.Timestamp("2026-01-05").date()

    with pytest.raises(DukascopyIngestError, match="failed to download weekday JETTA data after 2 attempts"):
        ingestor._download("https://example.invalid/day", tmp_path / "empty.json", day=day)
    assert len(calls) == 2
    assert not (tmp_path / "empty.json").exists()
