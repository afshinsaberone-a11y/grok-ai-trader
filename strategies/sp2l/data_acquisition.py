from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


@dataclass(frozen=True)
class OHLCV:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_histdata_m1(path: str | Path) -> Iterator[OHLCV]:
    """Parse HistData Generic ASCII M1 files.

    HistData documents fields as datetime;open;high;low;close;volume and
    states that its M1 Generic ASCII timestamps are EST without DST.
    We explicitly convert that source timezone to UTC here.
    """
    from zoneinfo import ZoneInfo

    est = ZoneInfo("America/New_York")
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        for row_number, row in enumerate(csv.reader(handle, delimiter=";"), start=1):
            if not row:
                continue
            if len(row) != 6:
                raise ValueError(f"HistData row {row_number}: expected 6 fields, got {len(row)}")
            dt = datetime.strptime(row[0].strip(), "%Y%m%d %H%M%S").replace(tzinfo=est)
            yield OHLCV(
                timestamp=dt.astimezone(timezone.utc),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )


def validate_ohlcv(rows: Iterable[OHLCV]) -> List[OHLCV]:
    """Validate and return sorted, unique OHLCV rows; fail on corrupt data."""
    data = list(rows)
    if not data:
        raise ValueError("No market-data rows supplied")
    data.sort(key=lambda x: x.timestamp)
    previous = None
    for i, row in enumerate(data):
        if row.high < max(row.open, row.close, row.low):
            raise ValueError(f"Invalid OHLC high at index {i}")
        if row.low > min(row.open, row.close, row.high):
            raise ValueError(f"Invalid OHLC low at index {i}")
        if row.volume < 0:
            raise ValueError(f"Negative volume at index {i}")
        if previous is not None and row.timestamp <= previous:
            raise ValueError("Timestamps must be strictly increasing after normalization")
        previous = row.timestamp
    return data


def resample_m1(rows: Sequence[OHLCV], minutes: int) -> List[OHLCV]:
    """Aggregate canonical M1 rows to M5/M15 bars using UTC bucket boundaries."""
    if minutes not in (5, 15):
        raise ValueError("Only 5 and 15 minute resampling is supported")
    data = validate_ohlcv(rows)
    buckets: dict[datetime, list[OHLCV]] = {}
    for row in data:
        minute = (row.timestamp.minute // minutes) * minutes
        bucket = row.timestamp.replace(minute=minute, second=0, microsecond=0)
        buckets.setdefault(bucket, []).append(row)

    result: list[OHLCV] = []
    for bucket in sorted(buckets):
        group = buckets[bucket]
        result.append(
            OHLCV(
                timestamp=bucket,
                open=group[0].open,
                high=max(x.high for x in group),
                low=min(x.low for x in group),
                close=group[-1].close,
                volume=sum(x.volume for x in group),
            )
        )
    return result


def _unix_ms(dt: datetime) -> int:
    return int(_ensure_utc(dt).timestamp() * 1000)


def dukascopy_historical_prices(
    instrument_id: int,
    start: datetime,
    end: datetime,
    timeframe: str = "1min",
    offer_side: str = "B",
    count: int = 5000,
    timeout: float = 30.0,
) -> object:
    """Fetch a single Dukascopy historicalPrices API page.

    The official API documents timeframe values including '1min' and 'tick',
    a maximum count of 5000, Unix timestamps in milliseconds, and bid/ask side.
    """
    if timeframe not in {"1day_eet", "1day", "1hour", "10m", "1min", "10sec", "tick"}:
        raise ValueError("Unsupported Dukascopy timeframe")
    if offer_side not in {"B", "A"}:
        raise ValueError("offer_side must be 'B' or 'A'")
    if not 1 <= count <= 5000:
        raise ValueError("count must be between 1 and 5000")

    params = urllib.parse.urlencode(
        {
            "path": "api/historicalPrices",
            "instrument": instrument_id,
            "timeFrame": timeframe,
            "count": count,
            "start": _unix_ms(start),
            "end": _unix_ms(end),
            "dayStartTime": "UTC",
            "offerSide": offer_side,
        }
    )
    url = f"https://freeserv.dukascopy.com/2.0/?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": "ForexAI/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
    return json.loads(payload)
