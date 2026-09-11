"""Real EURUSD M1 ingestion from Dukascopy's current JSON data API.

The legacy datafeed.dukascopy.com BI5 endpoint has been unreliable in CI.
The current Dukascopy data API used by dukascopy-node is JETTA v1, with
one compact JSON candle response per day. No synthetic fallback is permitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
DATA_API_ROOT = "https://jetta.dukascopy.com/v1"
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}


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
    def __init__(
        self,
        output_dir: str | Path,
        *,
        timeout: int = 30,
        retries: int = 8,
        workers: int = 4,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw" / "EURUSD" / "m1"
        self.normalized_dir = self.output_dir / "normalized"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retries = retries
        self.workers = workers

    @staticmethod
    def url_for(day: date) -> str:
        # Current JETTA API uses one-based month paths and compact candle JSON.
        return (
            f"{DATA_API_ROOT}/candles/minute/EUR-USD/BID/"
            f"{day.year:04d}/{day.month:02d}/{day.day:02d}"
        )

    @staticmethod
    def _is_weekend(day: date) -> bool:
        return day.weekday() >= 5

    def _download(self, url: str, destination: Path, *, day: date, force: bool = False) -> bool:
        if destination.exists() and destination.stat().st_size > 0 and not force:
            LOGGER.info("Using cached JETTA JSON: %s", destination)
            return True

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            tmp = destination.with_suffix(destination.suffix + ".part")
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": "ForexAI/0.1 real-data-ingestion",
                        "Accept": "application/json",
                    },
                )
                with urlopen(request, timeout=self.timeout) as response:
                    payload = response.read()
                if not payload:
                    raise DukascopyIngestError(f"Empty Dukascopy response: {url}")
                json.loads(payload.decode("utf-8"))
                tmp.write_bytes(payload)
                tmp.replace(destination)
                return True
            except HTTPError as exc:
                last_error = exc
                if exc.code == 404:
                    if self._is_weekend(day):
                        LOGGER.info("No JETTA source for weekend %s", day.isoformat())
                        if tmp.exists():
                            tmp.unlink()
                        return False
                    if tmp.exists():
                        tmp.unlink()
                    raise DukascopyIngestError(
                        f"REAL_DATA_REQUIRED: weekday JETTA source returned 404 for {day.isoformat()}: {url}"
                    ) from exc
                if exc.code not in TRANSIENT_HTTP_CODES:
                    if tmp.exists():
                        tmp.unlink()
                    raise DukascopyIngestError(
                        f"Non-retryable Dukascopy HTTP {exc.code}: {url}"
                    ) from exc
            except (URLError, TimeoutError, OSError, json.JSONDecodeError, DukascopyIngestError) as exc:
                last_error = exc

            if tmp.exists():
                tmp.unlink()
            if attempt < self.retries:
                delay = min(20.0, 1.5 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.75)
                LOGGER.warning(
                    "Transient JETTA failure for %s (attempt %d/%d); retrying in %.2fs: %s",
                    day.isoformat(), attempt, self.retries, delay, last_error,
                )
                time.sleep(delay)

        if self._is_weekend(day):
            LOGGER.warning(
                "JETTA unavailable after retries for weekend %s; recording as non-trading day",
                day.isoformat(),
            )
            return False
        raise DukascopyIngestError(
            f"REAL_DATA_REQUIRED: failed to download weekday JETTA data after "
            f"{self.retries} attempts: {url}: {last_error}"
        )

    def download_range(self, start: date, end: date, *, force: bool = False) -> list[DownloadedDay]:
        if end <= start:
            raise ValueError("end must be after start")

        downloaded: list[DownloadedDay] = []
        days = []
        current = start
        while current < end:
            days.append(current)
            current += timedelta(days=1)

        def fetch(day: date) -> DownloadedDay | None:
            destination = self.raw_dir / f"{day:%Y-%m-%d}.json"
            url = self.url_for(day)
            if not self._download(url, destination, day=day, force=force):
                return None
            return DownloadedDay(day, destination, url, sha256_file(destination), destination.stat().st_size)

        # Limited concurrency avoids hammering the provider while keeping a large
        # two-year daily pull practical inside GitHub Actions.
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(fetch, day): day for day in days}
            for future in as_completed(futures):
                downloaded_day = future.result()
                if downloaded_day is not None:
                    downloaded.append(downloaded_day)

        downloaded.sort(key=lambda item: item.day)
        if not downloaded:
            raise DukascopyIngestError("REAL_DATA_REQUIRED: no real JETTA files were downloaded")
        return downloaded

    @staticmethod
    def decode_m1(path: str | Path, day: date) -> pd.DataFrame:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        required = {"timestamp", "multiplier", "times", "shift", "open", "high", "low", "close", "opens", "highs", "lows", "closes", "volumes"}
        missing = required.difference(data)
        if missing:
            raise DukascopyIngestError(f"Invalid JETTA candle payload for {day}: missing {sorted(missing)}")

        times = data["times"]
        opens = data["opens"]
        highs = data["highs"]
        lows = data["lows"]
        closes = data["closes"]
        volumes = data["volumes"]
        n = len(times)
        if not all(len(column) == n for column in (opens, highs, lows, closes, volumes)):
            raise DukascopyIngestError(f"Invalid JETTA candle payload for {day}: column length mismatch")
        if n == 0:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume", "spread"])

        multiplier = float(data["multiplier"])
        shift = int(data["shift"])
        timestamp = int(data["timestamp"])
        open_units = round(float(data["open"]) / multiplier)
        high_units = round(float(data["high"]) / multiplier)
        low_units = round(float(data["low"]) / multiplier)
        close_units = round(float(data["close"]) / multiplier)
        rows: list[tuple[datetime, float, float, float, float, float, float]] = []

        for i in range(n):
            delta = int(times[i])
            timestamp += delta * shift
            open_units += int(opens[i])
            high_units += int(highs[i])
            low_units += int(lows[i])
            close_units += int(closes[i])
            rows.append(
                (
                    datetime.fromtimestamp(timestamp / 1000.0, tz=timezone.utc),
                    open_units * multiplier,
                    high_units * multiplier,
                    low_units * multiplier,
                    close_units * multiplier,
                    float(volumes[i]),
                    float("nan"),
                )
            )

        return pd.DataFrame(
            rows,
            columns=["timestamp", "open", "high", "low", "close", "volume", "spread"],
        )

    def build_m1(self, files: list[DownloadedDay]) -> pd.DataFrame:
        if not files:
            raise DukascopyIngestError("REAL_DATA_REQUIRED: no real M1 files available")

        frames = []
        for item in files:
            frame = self.decode_m1(item.path, item.day)
            if frame.empty:
                if self._is_weekend(item.day):
                    continue
                raise DukascopyIngestError(
                    f"REAL_DATA_REQUIRED: empty real M1 response on weekday {item.day.isoformat()}"
                )
            frames.append(frame)

        if not frames:
            raise DukascopyIngestError("REAL_DATA_REQUIRED: no non-empty real M1 data available")

        raw = pd.concat(frames, ignore_index=True)
        report = validate_ohlcv(raw, symbol="EURUSD", timeframe="M1")
        if report.status != "PASS":
            raise DukascopyIngestError(
                f"REAL_DATA_REQUIRED: source validation failed: {report.to_dict()}"
            )
        return canonicalize_ohlcv(raw)

    def write_dataset(
        self,
        m1: pd.DataFrame,
        *,
        dataset_id: str,
        files: list[DownloadedDay],
    ) -> dict[str, object]:
        output = self.normalized_dir / f"EURUSD_M1_{dataset_id}.csv"
        m1.to_csv(output, index=False)
        source_hash = hashlib.sha256(
            "".join(f.sha256 for f in files).encode("ascii")
        ).hexdigest()
        report = validate_ohlcv(m1, symbol="EURUSD", timeframe="M1")
        if report.status != "PASS":
            raise DukascopyIngestError(
                f"REAL_DATA_REQUIRED: normalized dataset failed validation: {report.to_dict()}"
            )
        manifest = build_manifest(
            m1,
            dataset_id=dataset_id,
            symbol="EURUSD",
            timeframe="M1",
            source="Dukascopy JETTA v1 BID candles (JSON)",
            source_hash=source_hash,
            quality_status=report.status,
            output_path=self.normalized_dir / f"EURUSD_M1_{dataset_id}.manifest.json",
        )
        return {"dataset": output, "manifest": manifest, "quality": report.to_dict()}


def ingest_m1(
    start: date,
    end: date,
    output_dir: str | Path,
    *,
    force: bool = False,
) -> dict[str, object]:
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
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        result = ingest_m1(
            _parse_date(args.start),
            _parse_date(args.end),
            args.output,
            force=args.force,
        )
        if args.timeframe != "M1":
            m1 = pd.read_csv(result["dataset"], parse_dates=["timestamp"])
            target = resample_ohlcv(m1, "5min" if args.timeframe == "M5" else "15min")
            out = (
                Path(args.output)
                / "normalized"
                / f"EURUSD_{args.timeframe}_{_parse_date(args.start):%Y%m%d}_"
                f"{(_parse_date(args.end) - timedelta(days=1)):%Y%m%d}.csv"
            )
            target.to_csv(out, index=False)
            report = validate_ohlcv(target, symbol="EURUSD", timeframe=args.timeframe)
            if report.status != "PASS":
                raise DukascopyIngestError(
                    f"REAL_DATA_REQUIRED: resampled dataset failed validation: {report.to_dict()}"
                )
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
