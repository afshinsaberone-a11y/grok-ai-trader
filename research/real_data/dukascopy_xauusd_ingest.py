"""Fail-closed Dukascopy XAUUSD BID/ASK M1 intake.

This module only ingests and validates real source bars. It does not run a
backtest, synthesize candles/spread, or claim that bar-level BID/ASK replaces
tick-level execution. The source's XAUUSD price scale is 1,000, unlike the
EURUSD legacy decoder in dukascopy_ingest.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import lzma
import struct
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

SYMBOL = "XAUUSD"
TIMEFRAME = "M1"
PRICE_SCALE = 1000.0
GOLD_PRICE_MIN = 200.0
GOLD_PRICE_MAX = 20000.0
BASE_URL = "https://datafeed.dukascopy.com/datafeed"
RECORD = struct.Struct(">IIIIIf")
COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class XAUUSDIngestError(RuntimeError):
    """Raised when source data are unavailable or fail strict validation."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_url(day: date, side: str) -> str:
    if side not in {"BID", "ASK"}:
        raise ValueError("XAUUSD_SIDE_INVALID")
    # Dukascopy legacy BI5 paths use a zero-based month.
    return (
        f"{BASE_URL}/{SYMBOL}/{day.year:04d}/{day.month - 1:02d}/"
        f"{day.day:02d}/{side}_candles_min_1.bi5"
    )


def decode_bi5(payload: bytes, day: date, *, side: str) -> pd.DataFrame:
    """Decode one real Dukascopy BI5 M1 side using XAUUSD's 1,000 scale."""
    if side not in {"BID", "ASK"}:
        raise ValueError("XAUUSD_SIDE_INVALID")
    if not payload:
        raise XAUUSDIngestError(f"REAL_DATA_REQUIRED: empty {side} payload for {day}")

    try:
        raw = lzma.decompress(payload)
    except lzma.LZMAError as exc:
        raise XAUUSDIngestError(f"XAUUSD_BI5_DECOMPRESSION_FAILED:{day}:{side}") from exc

    if len(raw) % RECORD.size:
        raise XAUUSDIngestError(
            f"XAUUSD_BI5_RECORD_ALIGNMENT_FAILED:{day}:{side}:{len(raw)}"
        )

    day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    rows: list[tuple[object, float, float, float, float, float]] = []
    for offset in range(0, len(raw), RECORD.size):
        seconds, open_i, close_i, low_i, high_i, volume = RECORD.unpack_from(raw, offset)
        values = [open_i / PRICE_SCALE, high_i / PRICE_SCALE,
                  low_i / PRICE_SCALE, close_i / PRICE_SCALE]
        if not all(GOLD_PRICE_MIN <= value <= GOLD_PRICE_MAX for value in values):
            raise XAUUSDIngestError(
                f"XAUUSD_PRICE_SCALE_OR_RANGE_INVALID:{day}:{side}:{values}"
            )
        open_px, high_px, low_px, close_px = values[0], values[1], values[2], values[3]
        if high_px < max(open_px, close_px, low_px) or low_px > min(open_px, close_px):
            raise XAUUSDIngestError(f"XAUUSD_OHLC_INVARIANT_FAILED:{day}:{side}:{offset}")
        timestamp = day_start + timedelta(seconds=int(seconds))
        rows.append((timestamp, open_px, high_px, low_px, close_px, float(volume)))

    if not rows:
        raise XAUUSDIngestError(f"REAL_DATA_REQUIRED: no {side} bars for weekday {day}")
    return pd.DataFrame(rows, columns=COLUMNS)


def merge_bid_ask(bid: pd.DataFrame, ask: pd.DataFrame) -> pd.DataFrame:
    """Pair real BID/ASK minute bars; refuse timestamp or spread mismatches."""
    for label, frame in (("BID", bid), ("ASK", ask)):
        if frame.empty or frame["timestamp"].duplicated().any():
            raise XAUUSDIngestError(f"XAUUSD_{label}_EMPTY_OR_DUPLICATE")
        ordered = pd.to_datetime(frame["timestamp"], utc=True)
        if not ordered.is_monotonic_increasing:
            raise XAUUSDIngestError(f"XAUUSD_{label}_TIMESTAMPS_UNSORTED")

    if not bid["timestamp"].reset_index(drop=True).equals(
        ask["timestamp"].reset_index(drop=True)
    ):
        raise XAUUSDIngestError("XAUUSD_BID_ASK_TIMESTAMP_MISMATCH")

    out = pd.DataFrame({"timestamp": pd.to_datetime(bid["timestamp"], utc=True)})
    for column in ("open", "high", "low", "close", "volume"):
        out[f"bid_{column}"] = pd.to_numeric(bid[column], errors="raise").to_numpy()
        out[f"ask_{column}"] = pd.to_numeric(ask[column], errors="raise").to_numpy()

    for point in ("open", "close"):
        out[f"spread_{point}"] = out[f"ask_{point}"] - out[f"bid_{point}"]
        if (out[f"spread_{point}"] < 0).any():
            raise XAUUSDIngestError(f"XAUUSD_NEGATIVE_{point.upper()}_SPREAD")
    if (out[["bid_open", "bid_high", "bid_low", "bid_close",
             "ask_open", "ask_high", "ask_low", "ask_close"]] <= 0).any().any():
        raise XAUUSDIngestError("XAUUSD_NONPOSITIVE_PRICE")
    return out


def _download(url: str, path: Path, *, timeout: int, retries: int) -> bytes:
    if path.exists() and path.stat().st_size:
        payload = path.read_bytes()
        # Do not trust a cache file just because it exists.
        try:
            lzma.decompress(payload)
        except lzma.LZMAError:
            path.unlink()
        else:
            return payload

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = Request(url, headers={"User-Agent": "ForexAI-XAUUSD-Research/1.0"})
            with urlopen(request, timeout=timeout) as response:
                payload = response.read()
            # Verify compressed structure before caching.
            lzma.decompress(payload)
            temp = path.with_suffix(path.suffix + ".part")
            temp.write_bytes(payload)
            temp.replace(path)
            return payload
        except HTTPError as exc:
            if exc.code == 404:
                raise XAUUSDIngestError(
                    f"REAL_DATA_REQUIRED: source 404 for {url}; no synthetic fallback"
                ) from exc
            last_error = exc
        except (URLError, TimeoutError, OSError, lzma.LZMAError) as exc:
            last_error = exc
        if attempt < retries:
            time.sleep(min(8, attempt * 2))
    raise XAUUSDIngestError(f"REAL_DATA_REQUIRED: source download failed: {url}: {last_error}")


def ingest(start: date, end: date, output_dir: str | Path, *,
           timeout: int = 30, retries: int = 3) -> dict[str, object]:
    """Download real BID/ASK M1 bars over [start, end); fail closed on gaps/mismatch."""
    if end <= start:
        raise ValueError("XAUUSD_DATE_RANGE_INVALID")

    root = Path(output_dir)
    raw_root = root / "raw" / SYMBOL / "m1"
    normalized_root = root / "normalized"
    raw_root.mkdir(parents=True, exist_ok=True)
    normalized_root.mkdir(parents=True, exist_ok=True)

    paired_days: list[pd.DataFrame] = []
    source_hash_records: list[dict[str, str]] = []
    day = start
    while day < end:
        if day.weekday() < 5:
            sides: dict[str, pd.DataFrame] = {}
            for side in ("BID", "ASK"):
                url = _source_url(day, side)
                path = raw_root / f"{day.isoformat()}_{side}.bi5"
                payload = _download(url, path, timeout=timeout, retries=retries)
                sides[side] = decode_bi5(payload, day, side=side)
                source_hash_records.append({
                    "day": day.isoformat(), "side": side, "url": url,
                    "sha256": _sha256(payload),
                })
            paired = merge_bid_ask(sides["BID"], sides["ASK"])
            paired_days.append(paired)
        day += timedelta(days=1)

    if not paired_days:
        raise XAUUSDIngestError("REAL_DATA_REQUIRED: date range yielded no XAUUSD bars")

    data = pd.concat(paired_days, ignore_index=True).sort_values("timestamp")
    if data["timestamp"].duplicated().any():
        raise XAUUSDIngestError("XAUUSD_DUPLICATE_TIMESTAMP_ACROSS_DAYS")
    data = data.reset_index(drop=True)

    dates = f"{start:%Y%m%d}_{end:%Y%m%d}"
    dataset_path = normalized_root / f"XAUUSD_M1_BIDASK_{dates}.csv"
    data.to_csv(dataset_path, index=False, float_format="%.5f")
    data_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    source_hash = _sha256(json.dumps(source_hash_records, sort_keys=True).encode())
    manifest = {
        "schema": "forexai.real_data.xauusd_bidask_m1.v1",
        "status": "PASS",
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "start_inclusive_utc": data["timestamp"].min().isoformat(),
        "end_inclusive_utc": data["timestamp"].max().isoformat(),
        "requested_start_utc": start.isoformat(),
        "requested_end_exclusive_utc": end.isoformat(),
        "rows": int(len(data)),
        "price_scale": int(PRICE_SCALE),
        "source": "Dukascopy historical BID/ASK M1 BI5",
        "source_hash_sha256": source_hash,
        "data_sha256": data_hash,
        "source_files": source_hash_records,
        "spread_fields": ["spread_open", "spread_close"],
        "spread_semantics": (
            "ask-minus-bid from paired minute-bar open/close values; "
            "not tick-level spread history"
        ),
        "synthetic_data": False,
        "backtest_run": False,
        "promotion_status": "RESEARCH_ONLY",
    }
    manifest_path = dataset_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {"dataset": str(dataset_path), "manifest": str(manifest_path),
            "rows": int(len(data)), "data_sha256": data_hash, "source_sha256": source_hash}


def main() -> int:
    parser = argparse.ArgumentParser(description="Download/validate REAL Dukascopy XAUUSD BID/ASK M1")
    parser.add_argument("--start", required=True, help="UTC date inclusive, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="UTC date exclusive, YYYY-MM-DD")
    parser.add_argument("--output", default="data/real/xauusd")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    result = ingest(date.fromisoformat(args.start), date.fromisoformat(args.end),
                    args.output, timeout=args.timeout, retries=args.retries)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
