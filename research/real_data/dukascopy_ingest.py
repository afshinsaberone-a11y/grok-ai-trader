"""Dukascopy real EURUSD M1 ingestion.

Dukascopy stores M1 candles as LZMA-compressed BI5 files. The public path uses
zero-based months (00=January) and one file per day. M1 records are decoded as
>IIIIIf: seconds-from-day-start, OHLC integer prices, and float volume.
No synthetic fallback is permitted.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import lzma
import struct
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from .manifest import build_manifest, sha256_file
from .normalizer import canonicalize_ohlcv, resample_ohlcv
from .validator import validate_ohlcv

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://datafeed.dukascopy.com/datafeed"
M1_RECORD = struct.Struct(">IIIIIf")
PRICE_SCALE = 100_000.0


class DukascopyIngestError(RuntimeError):
    """Raised when real Dukascopy data cannot be obtained or validated."""


@dataclass(frozen=True)
class DownloadedDay:
    day: date
    path: Path
    url: str
    sha256: str
    bytes: int


class DukascopyM1Ingestor:
    def __init__(self, output_dir: str | Path, *, timeout: int = 30, retries: int = 3) -> None:
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw" / "EURUSD" / "m1"
        self.normalized_dir = self.output_dir / "normalized"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries

    @staticmethod
    def url_for(day: date) -> str:
        return f"{BASE_URL}/EURUSD/{day.year:04d}/{day.month - 1:02d}/{day.day:02d}/BID_candles_min_1.bi5"

    def _download(self, url: str, destination: Path, *, force: bool = False) -> bool:
        if destination.exists() and destination.stat().st_size > 0 and not force:
            LOGGER.info("Using cached raw file: %s", destination)
            return True
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            tmp = destination.with_suffix(destination.suffix + ".part")
            try:
                request = Request(url, headers={"User-Agent": "ForexAI/0.1 real-data-ingestion"})
                with urlopen(request, timeout=self.timeout) as response, tmp.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                if tmp.stat().st_size == 0:
                    raise DukascopyIngestError(f"Empty Dukascopy response: {url}")
                tmp.replace(destination)
                return True
            except HTTPError as exc:
                last_error = exc
                if exc.code == 404:
                    LOGGER.info("No source file for %s (404): %s", destination.name, url)
                    if tmp.exists():
                        tmp.unlink()
                    return False
            except (URLError, TimeoutError, OSError, DukascopyIngestError) as exc:
                last_error = exc
            if tmp.exists():
                tmp.unlink()
            if attempt < self.retries:
                time.sleep(attempt)
                LOGGER.warning("Retry %d/%d for %s", attempt + 1, self.retries, url)
        raise DukascopyIngestError(f"Failed to download real Dukascopy data: {url}: {last_error}")

    @staticmethod
    def decode_m1(path: str | Path, day: date) -> pd.DataFrame:
        raw = lzma.decompress(Path(path).read_bytes())
        if len(raw) % M1_RECORD.size != 0:
            raise DukascopyIngestError(f"Invalid BI5 M1 payload size: {path}")
        rows = []
        day_start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        for offset in range(0, len(raw), M1_RECORD.size):
            seconds, open_i, high_i, low_i, close_i, volume = M1_RECORD.unpack_from(raw, offset)
            rows.append((
                day_start + timedelta(seconds=seconds),
                open_i / PRICE_SCALE,
                high_i / PRICE_SCALE,
                low_i / PRICE_SCALE,
                close_i / PRICE_SCALE,
                float(volume),
                float("nan"),
            ))
        return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume", "spread"])

    def download_range(self, start: date, end: date, *, force: bool = False) -> list[DownloadedDay]:
        if end <= start:
            raise ValueError("end must be after start")
        downloaded: list[DownloadedDay] = []
        current = start
        while current < end:
            destination = self.raw_dir / f"{current:%Y-%m-%d}.bi5"
            url = self.url_for(current)
            if self._download(url, destination, force=force):
                downloaded.append(DownloadedDay(current, destination, url, sha256_file(destination), destination.stat().st_size))
            current += timedelta(days=1)
        if not downloaded:
            raise DukascopyIngestError("REAL_DATA_REQUIRED: no real Dukascopy files were downloaded")
        return downloaded

    def build_m1(self, files: list[DownloadedDay]) -> pd.DataFrame:
        if not files:
            raise DukascopyIngestError("REAL_DATA_REQUIRED: no real M1 files available")
        raw = pd.concat([self.decode_m1(item.path, item.day) for item in files], ignore_index=True)
        report = validate_ohlcv(raw, symbol="EURUSD", timeframe="M1")
        if report.status != "PASS":
            raise DukascopyIngestError(f"REAL_DATA_REQUIRED: source validation failed: {report.to_dict()}")
        return canonicalize_ohlcv(raw)

    def write_dataset(self, m1: pd.DataFrame, *, dataset_id: str, files: list[DownloadedDay]) -> dict[str, object]:
        output = self.normalized_dir / f"EURUSD_M1_{dataset_id}.csv"
        m1.to_csv(output, index=False)
        source_hash = hashlib.sha256("".join(f.sha256 for f in files).encode("ascii")).hexdigest()
        report = validate_ohlcv(m1, symbol="EURUSD", timeframe="M1")
        if report.status != "PASS":
            raise DukascopyIngestError(f"REAL_DATA_REQUIRED: normalized dataset failed validation: {report.to_dict()}")
        manifest = build_manifest(
            m1, dataset_id=dataset_id, symbol="EURUSD", timeframe="M1",
            source="Dukascopy BID candles (BI5)", source_hash=source_hash,
            quality_status=report.status,
            output_path=self.normalized_dir / f"EURUSD_M1_{dataset_id}.manifest.json",
        )
        return {"dataset": output, "manifest": manifest, "quality": report.to_dict()}


def ingest_m1(start: date, end: date, output_dir: str | Path, *, force: bool = False) -> dict[str, object]:
    ingestor = DukascopyM1Ingestor(output_dir)
    files = ingestor.download_range(start, end, force=force)
    dataset_id = f"{start:%Y%m%d}_{(end - timedelta(days=1)):%Y%m%d}"
    m1 = ingestor.build_m1(files)
    return ingestor.write_dataset(m1, dataset_id=dataset_id, files=files)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download and validate real Dukascopy EURUSD data")
    parser.add_argument("--symbol", default="EURUSD", choices=["EURUSD"])
    parser.add_argument("--timeframe", default="M1", choices=["M1", "M5", "M15"])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", default="data/real")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Reuse existing raw files; default behavior")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
    try:
        result = ingest_m1(_parse_date(args.start), _parse_date(args.end), args.output, force=args.force)
        if args.timeframe != "M1":
            m1 = pd.read_csv(result["dataset"], parse_dates=["timestamp"])
            target = resample_ohlcv(m1, "5min" if args.timeframe == "M5" else "15min")
            out = Path(args.output) / "normalized" / f"EURUSD_{args.timeframe}_{_parse_date(args.start):%Y%m%d}_{(_parse_date(args.end) - timedelta(days=1)):%Y%m%d}.csv"
            target.to_csv(out, index=False)
            report = validate_ohlcv(target, symbol="EURUSD", timeframe=args.timeframe)
            if report.status != "PASS":
                raise DukascopyIngestError(f"REAL_DATA_REQUIRED: resampled dataset failed validation: {report.to_dict()}")
            print(report.to_dict())
        else:
            print(result["quality"])
            if args.manifest:
                print(result["manifest"])
        return 0
    except DukascopyIngestError as exc:
        LOGGER.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
