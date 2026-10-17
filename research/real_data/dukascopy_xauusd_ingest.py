"""Fail-closed real Dukascopy XAUUSD BID/ASK intake.

Supports daily M1 or monthly H1 source files. XAUUSD BI5 prices use a 1,000
point scale (not the EURUSD decoder's 100,000 scale). Provider filler candles
(flat range with zero volume) are dropped; timestamps, side pairing, source
hashes, and coverage gaps are recorded. No synthetic market data is created.
This module does not backtest or certify strategy profitability.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import lzma
import random
import struct
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

SYMBOL = "XAUUSD"
PRICE_SCALE = 1000.0
GOLD_PRICE_MIN = 200.0
GOLD_PRICE_MAX = 20000.0
BASE_URL = "https://datafeed.dukascopy.com/datafeed"
RECORD = struct.Struct(">IIIIIf")
COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]
TIMEFRAMES = {"M1", "H1"}


class XAUUSDIngestError(RuntimeError):
    """Raised when source data are unavailable or fail strict validation."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_url(period_start: date, side: str, timeframe: str) -> str:
    timeframe = timeframe.upper()
    if side not in {"BID", "ASK"}:
        raise ValueError("XAUUSD_SIDE_INVALID")
    if timeframe == "M1":
        suffix = f"{period_start.day:02d}/{side}_candles_min_1.bi5"
    elif timeframe == "H1":
        suffix = f"{side}_candles_hour_1.bi5"
    else:
        raise ValueError("XAUUSD_TIMEFRAME_INVALID")
    return (
        f"{BASE_URL}/{SYMBOL}/{period_start.year:04d}/"
        f"{period_start.month - 1:02d}/{suffix}"
    )


def _period_seconds(period_start: date, timeframe: str) -> int:
    if timeframe.upper() == "M1":
        return 86400
    if timeframe.upper() == "H1":
        return calendar.monthrange(period_start.year, period_start.month)[1] * 86400
    raise ValueError("XAUUSD_TIMEFRAME_INVALID")


def decode_bi5(
    payload: bytes,
    period_start: date,
    *,
    side: str,
    timeframe: str = "M1",
) -> pd.DataFrame:
    """Decode one real Dukascopy BI5 period using XAUUSD's instrument-specific scale."""
    timeframe = timeframe.upper()
    if side not in {"BID", "ASK"}:
        raise ValueError("XAUUSD_SIDE_INVALID")
    if timeframe not in TIMEFRAMES:
        raise ValueError("XAUUSD_TIMEFRAME_INVALID")
    if not payload:
        return pd.DataFrame(columns=COLUMNS)

    try:
        raw = lzma.decompress(payload)
    except (lzma.LZMAError, EOFError) as exc:
        raise XAUUSDIngestError(
            f"XAUUSD_BI5_DECOMPRESSION_FAILED:{period_start}:{side}"
        ) from exc
    if len(raw) % RECORD.size:
        raise XAUUSDIngestError(
            f"XAUUSD_BI5_RECORD_ALIGNMENT_FAILED:{period_start}:{side}:{len(raw)}"
        )

    start = datetime.combine(period_start, datetime.min.time(), tzinfo=timezone.utc)
    max_seconds = _period_seconds(period_start, timeframe)
    rows: list[tuple[object, float, float, float, float, float]] = []
    for offset in range(0, len(raw), RECORD.size):
        seconds, open_i, close_i, low_i, high_i, volume = RECORD.unpack_from(raw, offset)
        if not 0 <= int(seconds) < max_seconds:
            raise XAUUSDIngestError(
                f"XAUUSD_TIMESTAMP_OUT_OF_PERIOD:{period_start}:{side}:{seconds}"
            )
        if not pd.notna(volume) or float(volume) < 0:
            raise XAUUSDIngestError(f"XAUUSD_INVALID_VOLUME:{period_start}:{side}:{offset}")

        # Dukascopy record order is O-C-L-H, not O-H-L-C.
        open_px, close_px = open_i / PRICE_SCALE, close_i / PRICE_SCALE
        low_px, high_px = low_i / PRICE_SCALE, high_i / PRICE_SCALE
        values = (open_px, high_px, low_px, close_px)
        if not all(GOLD_PRICE_MIN <= value <= GOLD_PRICE_MAX for value in values):
            raise XAUUSDIngestError(
                f"XAUUSD_PRICE_SCALE_OR_RANGE_INVALID:{period_start}:{side}:{values}"
            )
        if high_px < max(open_px, close_px, low_px) or low_px > min(open_px, close_px):
            raise XAUUSDIngestError(
                f"XAUUSD_OHLC_INVARIANT_FAILED:{period_start}:{side}:{offset}"
            )

        timestamp = start + timedelta(seconds=int(seconds))
        rows.append((timestamp, open_px, high_px, low_px, close_px, float(volume)))

    frame = pd.DataFrame(rows, columns=COLUMNS)
    if not frame.empty:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        if frame["timestamp"].duplicated().any():
            raise XAUUSDIngestError(f"XAUUSD_DUPLICATE_SOURCE_TIMESTAMP:{period_start}:{side}")
        if not frame["timestamp"].is_monotonic_increasing:
            raise XAUUSDIngestError(f"XAUUSD_UNSORTED_SOURCE_TIMESTAMP:{period_start}:{side}")
    return frame


def merge_bid_ask(bid: pd.DataFrame, ask: pd.DataFrame) -> pd.DataFrame:
    """Pair real BID/ASK bars; reject misalignment and remove provider filler bars."""
    for label, frame in (("BID", bid), ("ASK", ask)):
        if frame.empty or frame["timestamp"].duplicated().any():
            raise XAUUSDIngestError(f"XAUUSD_{label}_EMPTY_OR_DUPLICATE")
        ts = pd.to_datetime(frame["timestamp"], utc=True)
        if not ts.is_monotonic_increasing:
            raise XAUUSDIngestError(f"XAUUSD_{label}_TIMESTAMPS_UNSORTED")

    bid_ts = pd.to_datetime(bid["timestamp"], utc=True).reset_index(drop=True)
    ask_ts = pd.to_datetime(ask["timestamp"], utc=True).reset_index(drop=True)
    if not bid_ts.equals(ask_ts):
        raise XAUUSDIngestError("XAUUSD_BID_ASK_TIMESTAMP_MISMATCH")

    out = pd.DataFrame({"timestamp": bid_ts})
    for column in ("open", "high", "low", "close", "volume"):
        out[f"bid_{column}"] = pd.to_numeric(bid[column], errors="raise").to_numpy()
        out[f"ask_{column}"] = pd.to_numeric(ask[column], errors="raise").to_numpy()

    for point in ("open", "close"):
        out[f"spread_{point}"] = out[f"ask_{point}"] - out[f"bid_{point}"]
        if (out[f"spread_{point}"] < 0).any():
            raise XAUUSDIngestError(f"XAUUSD_NEGATIVE_{point.upper()}_SPREAD")

    prices = ["bid_open", "bid_high", "bid_low", "bid_close",
              "ask_open", "ask_high", "ask_low", "ask_close"]
    if (out[prices] <= 0).any().any():
        raise XAUUSDIngestError("XAUUSD_NONPOSITIVE_PRICE")

    # Dukascopy fills some closed periods with flat zero-volume candles. They
    # are source filler, not traded bars; exclude them from research OHLC.
    active = (
        (out["bid_volume"] > 0)
        | (out["ask_volume"] > 0)
        | (out["bid_high"] > out["bid_low"])
        | (out["ask_high"] > out["ask_low"])
    )
    return out.loc[active].reset_index(drop=True)


def _valid_payload(payload: bytes) -> bool:
    if not payload:
        return True
    try:
        raw = lzma.decompress(payload)
    except (lzma.LZMAError, EOFError):
        return False
    return len(raw) % RECORD.size == 0


def _retry_after_seconds(exc: HTTPError) -> float | None:
    value = exc.headers.get("Retry-After") if exc.headers else None
    if value is None:
        return None
    try:
        return max(0.0, min(float(value), 300.0))
    except (TypeError, ValueError):
        return None


def _download(
    url: str,
    path: Path,
    *,
    timeout: int = 30,
    retries: int = 3,
    throttle_retries: int = 8,
) -> bytes:
    """Fetch/cache one source file, respecting 429/503 backoff and Retry-After."""
    if path.exists() and path.stat().st_size:
        cached = path.read_bytes()
        if _valid_payload(cached):
            return cached
        path.unlink()

    errors = throttles = 0
    while True:
        try:
            request = Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ForexAI-XAUUSD-Research/1.0)"},
            )
            with urlopen(request, timeout=timeout) as response:
                payload = response.read()
            if not _valid_payload(payload):
                raise XAUUSDIngestError(f"XAUUSD_INVALID_BI5_PAYLOAD:{url}")
            if payload:
                temp = path.with_suffix(path.suffix + ".part")
                temp.write_bytes(payload)
                temp.replace(path)
            return payload
        except HTTPError as exc:
            if exc.code == 404:
                # Dukascopy uses 404/empty files for unavailable periods. The
                # caller records this and refuses one-sided BID/ASK data.
                return b""
            if exc.code in {429, 503}:
                throttles += 1
                if throttles > throttle_retries:
                    raise XAUUSDIngestError(
                        f"REAL_DATA_REQUIRED: rate limited after {throttles - 1} retries: {url}"
                    ) from exc
                delay = min(30.0, 5.0 * (2 ** min(throttles - 1, 3)))
                retry_after = _retry_after_seconds(exc)
                if retry_after is not None:
                    delay = max(delay, retry_after)
                time.sleep(delay * random.uniform(0.8, 1.2))
                continue
            raise XAUUSDIngestError(
                f"REAL_DATA_REQUIRED: non-retryable HTTP {exc.code}: {url}"
            ) from exc
        except (URLError, TimeoutError, OSError, XAUUSDIngestError) as exc:
            errors += 1
            if errors > retries:
                raise XAUUSDIngestError(
                    f"REAL_DATA_REQUIRED: source download failed after {errors - 1} retries: {url}: {exc}"
                ) from exc
            time.sleep(min(30.0, 2.0 ** (errors - 1)) * random.uniform(0.8, 1.2))


def _period_starts(start: date, end: date, timeframe: str) -> list[date]:
    timeframe = timeframe.upper()
    if timeframe == "M1":
        days, current = [], start
        while current < end:
            if current.weekday() < 5:
                days.append(current)
            current += timedelta(days=1)
        return days
    if timeframe == "H1":
        periods: list[date] = []
        year, month = start.year, start.month
        final_year, final_month = (end - timedelta(days=1)).year, (end - timedelta(days=1)).month
        while (year, month) <= (final_year, final_month):
            periods.append(date(year, month, 1))
            month += 1
            if month == 13:
                month, year = 1, year + 1
        return periods
    raise ValueError("XAUUSD_TIMEFRAME_INVALID")


def _gap_audit(data: pd.DataFrame, timeframe: str) -> dict[str, object]:
    """Report gaps created by source closures/filler filtering; never fill them."""
    if len(data) < 2:
        return {"gap_count": 0, "same_utc_date_gap_count": 0, "examples": []}
    ts = pd.to_datetime(data["timestamp"], utc=True).reset_index(drop=True)
    expected = pd.Timedelta(minutes=1 if timeframe == "M1" else 60)
    gaps: list[dict[str, object]] = []
    same_day = 0
    for i in range(1, len(ts)):
        delta = ts.iloc[i] - ts.iloc[i - 1]
        if delta > expected:
            within_day = ts.iloc[i].date() == ts.iloc[i - 1].date()
            same_day += int(within_day)
            gaps.append({
                "previous_utc": ts.iloc[i - 1].isoformat(),
                "next_utc": ts.iloc[i].isoformat(),
                "elapsed_minutes": int(delta.total_seconds() // 60),
                "same_utc_date": within_day,
            })
    return {
        "gap_count": len(gaps),
        "same_utc_date_gap_count": same_day,
        "examples": gaps[:50],
    }


def ingest(
    start: date,
    end: date,
    output_dir: str | Path,
    *,
    timeframe: str = "H1",
    timeout: int = 30,
    retries: int = 3,
    throttle_retries: int = 8,
) -> dict[str, object]:
    """Download real data in [start,end), producing only an intake artifact."""
    timeframe = timeframe.upper()
    if end <= start:
        raise ValueError("XAUUSD_DATE_RANGE_INVALID")
    if timeframe not in TIMEFRAMES:
        raise ValueError("XAUUSD_TIMEFRAME_INVALID")

    root = Path(output_dir)
    raw_root = root / "raw" / SYMBOL / timeframe.lower()
    normalized_root = root / "normalized"
    raw_root.mkdir(parents=True, exist_ok=True)
    normalized_root.mkdir(parents=True, exist_ok=True)

    paired_periods: list[pd.DataFrame] = []
    source_hash_records: list[dict[str, str]] = []
    period_audit: list[dict[str, object]] = []

    for period_start in _period_starts(start, end, timeframe):
        sides: dict[str, pd.DataFrame] = {}
        for side in ("BID", "ASK"):
            url = _source_url(period_start, side, timeframe)
            cache_key = period_start.strftime("%Y-%m-%d" if timeframe == "M1" else "%Y-%m")
            path = raw_root / f"{cache_key}_{side}.bi5"
            payload = _download(
                url, path, timeout=timeout, retries=retries, throttle_retries=throttle_retries
            )
            sides[side] = decode_bi5(payload, period_start, side=side, timeframe=timeframe)
            source_hash_records.append({
                "period_start": period_start.isoformat(), "side": side, "url": url,
                "sha256": _sha256(payload), "bytes": str(len(payload)),
            })

        if sides["BID"].empty and sides["ASK"].empty:
            period_audit.append({"period_start": period_start.isoformat(), "status": "NO_SOURCE_BARS"})
            continue
        if sides["BID"].empty != sides["ASK"].empty:
            raise XAUUSDIngestError(
                f"XAUUSD_ONE_SIDED_SOURCE_DATA:{period_start}:"
                f"bid_rows={len(sides['BID'])}:ask_rows={len(sides['ASK'])}"
            )

        paired = merge_bid_ask(sides["BID"], sides["ASK"])
        raw_rows = len(paired)
        if not paired.empty:
            paired = paired.loc[
                (paired["timestamp"] >= pd.Timestamp(start, tz="UTC"))
                & (paired["timestamp"] < pd.Timestamp(end, tz="UTC"))
            ].copy()
        period_audit.append({
            "period_start": period_start.isoformat(),
            "status": "PAIRED" if not paired.empty else "NO_ACTIVE_BARS_IN_RANGE",
            "bid_source_rows": int(len(sides["BID"])),
            "ask_source_rows": int(len(sides["ASK"])),
            "active_paired_rows_before_range_filter": int(raw_rows),
            "rows_in_requested_range": int(len(paired)),
        })
        if not paired.empty:
            paired_periods.append(paired)

    if not paired_periods:
        raise XAUUSDIngestError("REAL_DATA_REQUIRED: requested range has no paired active XAUUSD bars")

    data = pd.concat(paired_periods, ignore_index=True).sort_values("timestamp")
    if data["timestamp"].duplicated().any():
        raise XAUUSDIngestError("XAUUSD_DUPLICATE_TIMESTAMP_ACROSS_PERIODS")
    data = data.reset_index(drop=True)
    gaps = _gap_audit(data, timeframe)

    dates = f"{start:%Y%m%d}_{end:%Y%m%d}"
    dataset_path = normalized_root / f"XAUUSD_{timeframe}_BIDASK_{dates}.csv"
    data.to_csv(dataset_path, index=False, float_format="%.5f",
                date_format="%Y-%m-%dT%H:%M:%SZ")
    data_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    source_hash = _sha256(json.dumps(source_hash_records, sort_keys=True).encode())
    manifest = {
        "schema": f"forexai.real_data.xauusd_bidask_{timeframe.lower()}.v1",
        "status": "INGESTION_ONLY_COVERAGE_REVIEW_REQUIRED",
        "symbol": SYMBOL,
        "timeframe": timeframe,
        "start_inclusive_utc": data["timestamp"].min().isoformat(),
        "end_exclusive_requested_utc": pd.Timestamp(end, tz="UTC").isoformat(),
        "end_inclusive_observed_utc": data["timestamp"].max().isoformat(),
        "requested_start_utc": start.isoformat(),
        "requested_end_exclusive_utc": end.isoformat(),
        "rows": int(len(data)),
        "price_scale": int(PRICE_SCALE),
        "source": "Dukascopy historical BID/ASK BI5 bars",
        "source_hash_sha256": source_hash,
        "data_sha256": data_hash,
        "source_files": source_hash_records,
        "period_audit": period_audit,
        "gap_audit": gaps,
        "spread_fields": ["spread_open", "spread_close"],
        "spread_semantics": (
            "ask-minus-bid from paired bar open/close values; not tick-level spread history"
        ),
        "provider_filler_bars": "flat zero-volume bars removed; no OHLC values synthesized",
        "synthetic_data": False,
        "backtest_run": False,
        "promotion_status": "RESEARCH_ONLY",
    }
    manifest_path = dataset_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "dataset": str(dataset_path), "manifest": str(manifest_path),
        "rows": int(len(data)), "data_sha256": data_hash, "source_sha256": source_hash,
        "timeframe": timeframe, "gap_count": gaps["gap_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download/validate real Dukascopy XAUUSD BID/ASK bars (no backtest)"
    )
    parser.add_argument("--start", required=True, help="UTC date inclusive, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="UTC date exclusive, YYYY-MM-DD")
    parser.add_argument("--timeframe", default="H1", choices=sorted(TIMEFRAMES))
    parser.add_argument("--output", default="data/real/xauusd")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--throttle-retries", type=int, default=8)
    args = parser.parse_args()
    result = ingest(
        date.fromisoformat(args.start), date.fromisoformat(args.end), args.output,
        timeframe=args.timeframe, timeout=args.timeout, retries=args.retries,
        throttle_retries=args.throttle_retries,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
