from __future__ import annotations

import io
import lzma
import struct
from datetime import date

import pandas as pd
import pytest

import research.real_data.dukascopy_xauusd_ingest as ingest_module
from research.real_data.dukascopy_xauusd_ingest import (
    PRICE_SCALE,
    XAUUSDIngestError,
    _download,
    _source_url,
    decode_bi5,
    merge_bid_ask,
)


def _bi5(*records: tuple[int, int, int, int, int, float]) -> bytes:
    # Record fields: seconds, open, close, low, high, volume.
    raw = b"".join(struct.pack(">IIIIIf", *record) for record in records)
    return lzma.compress(raw, format=lzma.FORMAT_ALONE)


def test_xauusd_decoder_uses_instrument_specific_price_scale() -> None:
    day = date(2026, 9, 4)
    payload = _bi5((60, 4_062_800, 4_062_900, 4_062_700, 4_063_000, 12.5))
    bars = decode_bi5(payload, day, side="BID")

    assert PRICE_SCALE == 1000.0
    assert bars.loc[0, "timestamp"] == pd.Timestamp("2026-09-04T00:01:00Z")
    assert bars.loc[0, "open"] == pytest.approx(4062.8)
    assert bars.loc[0, "close"] == pytest.approx(4062.9)
    assert bars.loc[0, "low"] == pytest.approx(4062.7)
    assert bars.loc[0, "high"] == pytest.approx(4063.0)


def test_h1_monthly_source_uses_month_start_for_timestamps() -> None:
    payload = _bi5((3600, 2_040_800, 2_040_900, 2_040_700, 2_041_000, 12.5))
    bars = decode_bi5(payload, date(2024, 1, 1), side="BID", timeframe="H1")

    assert bars.loc[0, "timestamp"] == pd.Timestamp("2024-01-01T01:00:00Z")
    assert bars.loc[0, "open"] == pytest.approx(2040.8)


def test_source_urls_use_zero_based_month_and_correct_resolution() -> None:
    day = date(2024, 1, 8)
    assert _source_url(day, "BID", "M1").endswith(
        "/XAUUSD/2024/00/08/BID_candles_min_1.bi5"
    )
    assert _source_url(date(2024, 1, 1), "ASK", "H1").endswith(
        "/XAUUSD/2024/00/ASK_candles_hour_1.bi5"
    )


def test_decoder_fails_closed_when_price_scale_is_wrong_or_prices_implausible() -> None:
    payload = _bi5((60, 40_628, 40_629, 40_627, 40_630, 1.0))
    with pytest.raises(XAUUSDIngestError, match="PRICE_SCALE_OR_RANGE_INVALID"):
        decode_bi5(payload, date(2026, 9, 4), side="BID")


def test_merge_bid_ask_preserves_side_prices_and_computes_bar_spread() -> None:
    day = date(2026, 9, 4)
    bid = decode_bi5(
        _bi5((60, 4_062_800, 4_062_900, 4_062_700, 4_063_000, 12.5)),
        day, side="BID",
    )
    ask = decode_bi5(
        _bi5((60, 4_063_100, 4_063_200, 4_063_000, 4_063_300, 14.5)),
        day, side="ASK",
    )

    merged = merge_bid_ask(bid, ask)
    assert merged.loc[0, "bid_open"] == pytest.approx(4062.8)
    assert merged.loc[0, "ask_open"] == pytest.approx(4063.1)
    assert merged.loc[0, "spread_open"] == pytest.approx(0.3)
    assert merged.loc[0, "spread_close"] == pytest.approx(0.3)


def test_provider_flat_zero_volume_fillers_are_removed() -> None:
    day = date(2026, 9, 4)
    active = (60, 4_062_800, 4_062_900, 4_062_700, 4_063_000, 12.5)
    filler = (120, 4_062_900, 4_062_900, 4_062_900, 4_062_900, 0.0)
    bid = decode_bi5(_bi5(active, filler), day, side="BID")
    ask = decode_bi5(_bi5(
        (60, 4_063_100, 4_063_200, 4_063_000, 4_063_300, 14.5),
        (120, 4_063_200, 4_063_200, 4_063_200, 4_063_200, 0.0),
    ), day, side="ASK")

    merged = merge_bid_ask(bid, ask)
    assert len(merged) == 1
    assert merged.loc[0, "timestamp"] == pd.Timestamp("2026-09-04T00:01:00Z")


def test_merge_refuses_timestamp_mismatch_instead_of_filling_bars() -> None:
    day = date(2026, 9, 4)
    bid = decode_bi5(
        _bi5((60, 4_062_800, 4_062_900, 4_062_700, 4_063_000, 12.5)),
        day, side="BID",
    )
    ask = decode_bi5(
        _bi5((120, 4_063_100, 4_063_200, 4_063_000, 4_063_300, 14.5)),
        day, side="ASK",
    )
    with pytest.raises(XAUUSDIngestError, match="TIMESTAMP_MISMATCH"):
        merge_bid_ask(bid, ask)


def test_merge_refuses_negative_spread() -> None:
    day = date(2026, 9, 4)
    bid = decode_bi5(
        _bi5((60, 4_063_100, 4_063_200, 4_063_000, 4_063_300, 12.5)),
        day, side="BID",
    )
    ask = decode_bi5(
        _bi5((60, 4_062_800, 4_062_900, 4_062_700, 4_063_000, 14.5)),
        day, side="ASK",
    )
    with pytest.raises(XAUUSDIngestError, match="NEGATIVE_OPEN_SPREAD"):
        merge_bid_ask(bid, ask)


def test_decoder_refuses_malformed_bi5_payload() -> None:
    with pytest.raises(XAUUSDIngestError, match="DECOMPRESSION_FAILED"):
        decode_bi5(b"not-lzma", date(2026, 9, 4), side="BID")


def test_download_retries_http_503_with_backoff(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    day = date(2024, 1, 8)
    payload = _bi5((60, 2_040_800, 2_040_900, 2_040_700, 2_041_000, 12.5))
    calls = {"count": 0}

    def fake_urlopen(request, timeout=30):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ingest_module.HTTPError(
                request.full_url, 503, "Service Unavailable", {"Retry-After": "0"}, None
            )
        return io.BytesIO(payload)

    monkeypatch.setattr(ingest_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(ingest_module.time, "sleep", lambda _: None)
    result = _download(
        _source_url(day, "BID", "M1"),
        tmp_path / "cached.bi5",
        timeout=1,
        retries=1,
        throttle_retries=2,
    )
    assert result == payload
    assert calls["count"] == 2



@pytest.mark.parametrize("status", [500, 502, 504])
def test_download_retries_transient_server_http_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path, status: int
) -> None:
    day = date(2024, 1, 8)
    payload = _bi5((60, 2_040_800, 2_040_900, 2_040_700, 2_041_000, 12.5))
    calls = {"count": 0}

    def fake_urlopen(request, timeout=30):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ingest_module.HTTPError(
                request.full_url, status, "Temporary upstream failure", {"Retry-After": "0"}, None
            )
        return io.BytesIO(payload)

    monkeypatch.setattr(ingest_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(ingest_module.time, "sleep", lambda _: None)
    result = _download(
        _source_url(day, "ASK", "M1"),
        tmp_path / f"transient-http-{status}.bi5",
        timeout=1,
        retries=1,
        throttle_retries=1,
    )

    assert result == payload
    assert calls["count"] == 2
    assert (tmp_path / f"transient-http-{status}.bi5").is_file()


def test_download_retries_transient_connection_resets(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from urllib.error import URLError

    day = date(2024, 1, 8)
    payload = _bi5((60, 2_040_800, 2_040_900, 2_040_700, 2_041_000, 12.5))
    calls = {"count": 0}

    def fake_urlopen(request, timeout=30):
        calls["count"] += 1
        if calls["count"] <= 2:
            raise URLError(ConnectionResetError("peer reset TLS connection"))
        return io.BytesIO(payload)

    monkeypatch.setattr(ingest_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(ingest_module.time, "sleep", lambda _: None)
    result = _download(
        _source_url(day, "ASK", "H1"),
        tmp_path / "connection-reset-cache.bi5",
        timeout=1,
        retries=3,
        throttle_retries=2,
    )

    assert result == payload
    assert calls["count"] == 3
    assert (tmp_path / "connection-reset-cache.bi5").is_file()



def _m1_frame(start: str = "2024-01-08T00:00:00Z", count: int = 10) -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=count, freq="min", tz="UTC")
    bid_open = [2040.0 + i * 0.1 for i in range(count)]
    ask_open = [x + 0.2 for x in bid_open]
    return pd.DataFrame({
        "timestamp": timestamps,
        "bid_open": bid_open,
        "bid_high": [x + 0.3 for x in bid_open],
        "bid_low": [x - 0.2 for x in bid_open],
        "bid_close": [x + 0.1 for x in bid_open],
        "bid_volume": [1.0] * count,
        "ask_open": ask_open,
        "ask_high": [x + 0.3 for x in ask_open],
        "ask_low": [x - 0.2 for x in ask_open],
        "ask_close": [x + 0.1 for x in ask_open],
        "ask_volume": [2.0] * count,
        "spread_open": [0.2] * count,
        "spread_close": [0.2] * count,
    })


def test_m1_to_m5_resamples_only_complete_groups_and_preserves_bid_ask_ohlc() -> None:
    from research.real_data.dukascopy_xauusd_ingest import resample_m1_to_m5

    m1 = _m1_frame()
    m5, audit = resample_m1_to_m5(m1)

    assert len(m5) == 2
    assert m5["timestamp"].tolist() == [
        pd.Timestamp("2024-01-08T00:00:00Z"),
        pd.Timestamp("2024-01-08T00:05:00Z"),
    ]
    assert m5.loc[0, "bid_open"] == pytest.approx(2040.0)
    assert m5.loc[0, "bid_high"] == pytest.approx(2040.7)
    assert m5.loc[0, "bid_low"] == pytest.approx(2039.8)
    assert m5.loc[0, "bid_close"] == pytest.approx(2040.5)
    assert m5.loc[0, "ask_open"] == pytest.approx(2040.2)
    assert m5.loc[0, "ask_close"] == pytest.approx(2040.7)
    assert m5.loc[0, "spread_open"] == pytest.approx(0.2)
    assert m5.loc[0, "spread_close"] == pytest.approx(0.2)
    assert m5.loc[0, "bid_volume"] == pytest.approx(5.0)
    assert m5.loc[0, "ask_volume"] == pytest.approx(10.0)
    assert audit["input_m1_rows"] == 10
    assert audit["complete_five_minute_buckets"] == 2
    assert audit["incomplete_five_minute_buckets"] == 0
    assert audit["filled_bars"] == 0
    assert audit["synthetic_data"] is False


def test_m1_to_m5_drops_incomplete_bucket_without_filling_missing_minutes() -> None:
    from research.real_data.dukascopy_xauusd_ingest import resample_m1_to_m5

    m1 = _m1_frame(count=10).drop(index=2).reset_index(drop=True)
    m5, audit = resample_m1_to_m5(m1)

    assert len(m5) == 1
    assert m5.loc[0, "timestamp"] == pd.Timestamp("2024-01-08T00:05:00Z")
    assert audit["candidate_five_minute_buckets"] == 2
    assert audit["complete_five_minute_buckets"] == 1
    assert audit["incomplete_five_minute_buckets"] == 1
    assert audit["m1_rows_excluded_with_incomplete_buckets"] == 4
    assert audit["filled_bars"] == 0


def test_m1_to_m5_rejects_duplicate_or_unsorted_timestamps() -> None:
    from research.real_data.dukascopy_xauusd_ingest import resample_m1_to_m5

    duplicate = _m1_frame()
    duplicate.loc[1, "timestamp"] = duplicate.loc[0, "timestamp"]
    with pytest.raises(XAUUSDIngestError, match="TIMESTAMP_ORDER_INVALID"):
        resample_m1_to_m5(duplicate)

    unsorted = _m1_frame().iloc[::-1].reset_index(drop=True)
    with pytest.raises(XAUUSDIngestError, match="TIMESTAMP_ORDER_INVALID"):
        resample_m1_to_m5(unsorted)


def test_m1_to_m5_rejects_non_minute_aligned_timestamps() -> None:
    from research.real_data.dukascopy_xauusd_ingest import resample_m1_to_m5

    m1 = _m1_frame()
    m1.loc[0, "timestamp"] += pd.Timedelta(seconds=1)
    with pytest.raises(XAUUSDIngestError, match="NOT_MINUTE_ALIGNED"):
        resample_m1_to_m5(m1)


def test_m1_to_m5_rejects_negative_resampled_spread() -> None:
    from research.real_data.dukascopy_xauusd_ingest import resample_m1_to_m5

    m1 = _m1_frame()
    m1.loc[4, "ask_close"] = m1.loc[4, "bid_close"] - 0.1
    with pytest.raises(XAUUSDIngestError, match="NEGATIVE_CLOSE_SPREAD"):
        resample_m1_to_m5(m1)


def test_m1_to_m5_fails_when_no_complete_bucket_exists() -> None:
    from research.real_data.dukascopy_xauusd_ingest import resample_m1_to_m5

    m1 = _m1_frame(count=4)
    with pytest.raises(XAUUSDIngestError, match="NO_COMPLETE_FIVE_MINUTE_BUCKETS"):
        resample_m1_to_m5(m1)


def test_m1_period_starts_include_sunday_open_and_skip_saturday() -> None:
    from research.real_data.dukascopy_xauusd_ingest import _period_starts

    days = _period_starts(date(2024, 6, 29), date(2024, 7, 2), "M1")

    assert days == [date(2024, 6, 30), date(2024, 7, 1)]
