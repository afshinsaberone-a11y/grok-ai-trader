from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .models import Candle


class DataFormatError(ValueError):
    pass


def load_ohlcv_csv(path: str | Path) -> List[Candle]:
    """Load real OHLCV candles from a CSV file.

    Accepted column names are case-insensitive: timestamp/time/date, open,
    high, low, close and optional volume/tick_volume. No synthetic rows are
    created and rows are not resampled by this loader.
    """
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DataFormatError("CSV has no header")
        fields = {name.strip().lower(): name for name in reader.fieldnames}
        time_key = next((fields[k] for k in ("timestamp", "time", "date") if k in fields), None)
        required = ["open", "high", "low", "close"]
        if time_key is None or any(k not in fields for k in required):
            raise DataFormatError("CSV requires timestamp/time/date, open, high, low and close")
        volume_key = next((fields[k] for k in ("volume", "tick_volume") if k in fields), None)
        candles: List[Candle] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                timestamp = _parse_timestamp(row[time_key])
                candle = Candle(
                    timestamp=timestamp,
                    open=float(row[fields["open"]]),
                    high=float(row[fields["high"]]),
                    low=float(row[fields["low"]]),
                    close=float(row[fields["close"]]),
                    volume=float(row[volume_key]) if volume_key and row.get(volume_key) else 0.0,
                )
            except (TypeError, ValueError) as exc:
                raise DataFormatError(f"invalid row {row_number}: {exc}") from exc
            if candle.high < max(candle.open, candle.close) or candle.low > min(candle.open, candle.close):
                raise DataFormatError(f"invalid OHLC relationship at row {row_number}")
            if candles and candle.timestamp <= candles[-1].timestamp:
                raise DataFormatError(f"timestamps must be strictly increasing at row {row_number}")
            candles.append(candle)
        return candles


def _parse_timestamp(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
