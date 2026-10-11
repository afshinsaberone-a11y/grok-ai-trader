from __future__ import annotations

import lzma
import struct
from datetime import date

import pandas as pd
import pytest

from research.real_data.dukascopy_xauusd_ingest import (
    PRICE_SCALE,
    XAUUSDIngestError,
    decode_bi5,
    merge_bid_ask,
)


def _bi5(*records: tuple[int, int, int, int, int, float]) -> bytes:
    # Record fields: seconds, open, close, low, high, volume.
    return lzma.compress(b"".join(struct.pack(">IIIIIf", *r) for r in records), format=lzma.FORMAT_ALONE)


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


def test_decoder_fails_closed_if_price_scale_is_wrong_or_prices_implausible() -> None:
    payload = _bi5((60, 40_628, 40_629, 40_627, 40_630, 1.0))
    with pytest.raises(XAUUSDIngestError, match="PRICE_SCALE_OR_RANGE_INVALID"):
        decode_bi5(payload, date(2026, 9, 4), side="BID")


def test_merge_bid_ask_preserves_real_side_prices_and_computes_bar_spread() -> None:
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
