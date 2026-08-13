"""HistData current-year M1 downloader for OOS evaluation.

HistData serves the current year by month, while completed historical years are
served as annual archives. This module handles the current-year monthly case
without synthesizing data or changing the frozen trading parameters.
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from .conflict_audit import audit_timestamp_conflicts
from .histdata_ingest import HistDataIngestError, _dedupe_exact_source_timestamps, _extract_year_csv, _parse_csv
from .manifest import build_manifest, sha256_file
from .normalizer import canonicalize_ohlcv, resample_ohlcv
from .session_audit import audit_weekly_session
from .validator import validate_ohlcv

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.histdata.com"
PREFIX = BASE_URL + "/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/eurusd"
POST_URL = BASE_URL + "/get.php"
FIXED_EST = timezone(timedelta(hours=-5))


@dataclass(frozen=True)
class DownloadedMonth:
    year: int
    month: int
    archive: Path
    sha256: str


class _InputParser(HTMLParser):
    """Parse hidden/input fields without assuming HTML attribute order."""

    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "input":
            return
        data = {key.lower(): value for key, value in attrs}
        key = data.get("name") or data.get("id")
        value = data.get("value")
        if key and value is not None:
            self.fields[key] = html.unescape(value)


def _fetch(url: str, timeout: int = 60) -> bytes:
    request = Request(url, headers={"User-Agent": "ForexAI/0.1 real-data-ingestion"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _hidden_form_current_year(html_text: str) -> dict[str, str]:
    parser = _InputParser()
    parser.feed(html_text)
    fields = parser.fields
    required = ("tk", "date", "datemonth", "platform", "timeframe", "fxpair")
    missing = [key for key in required if key not in fields]
    if missing:
        raise HistDataIngestError(
            f"REAL_DATA_REQUIRED: HistData current-year download form missing fields: {missing}"
        )
    return {key: fields[key] for key in required}


def fetch_month_archive(year: int, month: int, output_dir: str | Path, *, retries: int = 3, timeout: int = 60) -> DownloadedMonth:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"HISTDATA_COM_ASCII_EURUSD_M1_{year}{month:02d}.zip"
    if archive.exists() and archive.stat().st_size > 0 and zipfile.is_zipfile(archive):
        return DownloadedMonth(year, month, archive, sha256_file(archive))

    page_url = f"{PREFIX}/{year}/{month}"
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            page = _fetch(page_url, timeout=timeout).decode("utf-8", errors="replace")
            fields = _hidden_form_current_year(page)
            payload = urlencode(fields).encode("utf-8")
            request = Request(
                POST_URL,
                data=payload,
                headers={
                    "User-Agent": "ForexAI/0.1 real-data-ingestion",
                    "Host": "www.histdata.com",
                    "Origin": BASE_URL,
                    "Referer": page_url,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
            )
            with urlopen(request, timeout=timeout) as response:
                content = response.read()
            if not content.startswith(b"PK"):
                raise HistDataIngestError(
                    f"HistData returned a non-ZIP response for {year}-{month:02d}"
                )
            archive.write_bytes(content)
            return DownloadedMonth(year, month, archive, sha256_file(archive))
        except (HTTPError, URLError, TimeoutError, OSError, HistDataIngestError) as exc:
            last_error = exc
            if archive.exists():
                archive.unlink()
            if attempt < retries:
                time.sleep(attempt * 5)
                LOGGER.warning(
                    "HistData current-year retry %d/%d for %s-%02d",
                    attempt + 1,
                    retries,
                    year,
                    month,
                )
    raise HistDataIngestError(
        f"Failed to download real HistData EURUSD {year}-{month:02d}: {last_error}"
    )


def month_starts(start: date, end: date) -> list[tuple[int, int]]:
    if end <= start:
        raise ValueError("end must be after start")
    cursor = date(start.year, start.month, 1)
    result: list[tuple[int, int]] = []
    while cursor < end:
        result.append((cursor.year, cursor.month))
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    return result


def _write_conflict_audit(
    output_dir: str | Path,
    report: pd.DataFrame,
    summary: dict[str, object],
    session_summary: dict[str, object],
) -> None:
    artifacts = Path(output_dir) / "conflict_audit"
    artifacts.mkdir(parents=True, exist_ok=True)
    report.to_csv(artifacts / "current_year_timestamp_conflicts.csv", index=False)
    (artifacts / "current_year_timestamp_conflicts.json").write_text(
        json.dumps(
            {
                "conflicts": summary,
                "weekly_session": session_summary,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def ingest_current_year(start: date, end: date, output_dir: str | Path, *, timeframe: str = "M5") -> dict[str, object]:
    if start.year != end.year:
        raise ValueError("Current-year OOS downloader requires a single calendar year")
    if start.year != datetime.now(timezone.utc).year:
        raise ValueError("This downloader is only for the current calendar year")

    raw_dir = Path(output_dir) / "raw" / "histdata"
    frames: list[pd.DataFrame] = []
    archives: list[DownloadedMonth] = []
    for year, month in month_starts(start, end):
        item = fetch_month_archive(year, month, raw_dir)
        archives.append(item)
        _, payload = _extract_year_csv(item.archive)
        frame = _parse_csv(payload)
        frame["source_year"] = year
        frame["source_month"] = month
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    df = df[(df["timestamp"] >= pd.Timestamp(start, tz="UTC")) & (df["timestamp"] < pd.Timestamp(end, tz="UTC"))]
    if df.empty:
        raise HistDataIngestError("REAL_DATA_REQUIRED: current-year OOS HistData dataset is empty")

    # Diagnostic only: do not remove all Sunday rows because legitimate FX trading
    # resumes on Sunday evening UTC. Unambiguously closed-session rows are reported
    # separately so they cannot be mistaken for valid market data.
    session_summary = audit_weekly_session(df)
    conflict_report, conflict_summary = audit_timestamp_conflicts(df)
    _write_conflict_audit(output_dir, conflict_report, conflict_summary.to_dict(), session_summary)
    if conflict_summary.conflicting_timestamps:
        raise HistDataIngestError(
            "REAL_DATA_REQUIRED: conflicting duplicate timestamps detected; "
            f"count={conflict_summary.conflicting_timestamps}, "
            f"max_ohlc_diff={conflict_summary.max_abs_ohlc_diff}, "
            f"weekly_session={session_summary}, "
            f"audit={Path(output_dir) / 'conflict_audit'}"
        )

    df = df.drop(columns=["source_year", "source_month"])
    df, duplicate_rows_removed = _dedupe_exact_source_timestamps(df)
    df = canonicalize_ohlcv(df, symbol="EURUSD", source="HistData.com")
    m1_report = validate_ohlcv(df, symbol="EURUSD", timeframe="M1")
    if m1_report.status != "PASS":
        raise HistDataIngestError(
            f"REAL_DATA_REQUIRED: current-year M1 validation failed: {m1_report.to_dict()}"
        )

    normalized = Path(output_dir) / "normalized"
    normalized.mkdir(parents=True, exist_ok=True)
    dataset_id = f"{start:%Y%m%d}_{(end - timedelta(days=1)):%Y%m%d}"
    m1_path = normalized / f"EURUSD_M1_{dataset_id}.csv"
    df.to_csv(m1_path, index=False)
    source_hash = hashlib.sha256("".join(item.sha256 for item in archives).encode("ascii")).hexdigest()
    build_manifest(
        df,
        dataset_id=dataset_id,
        symbol="EURUSD",
        timeframe="M1",
        source="HistData.com Generic ASCII M1 monthly current-year",
        source_hash=source_hash,
        quality_status=m1_report.status,
        output_path=normalized / f"EURUSD_M1_{dataset_id}.manifest.json",
    )

    target = resample_ohlcv(df, "5min" if timeframe == "M5" else "15min")
    report = validate_ohlcv(target, symbol="EURUSD", timeframe=timeframe)
    if report.status != "PASS":
        raise HistDataIngestError(
            f"REAL_DATA_REQUIRED: current-year {timeframe} validation failed: {report.to_dict()}"
        )
    out = normalized / f"EURUSD_{timeframe}_{dataset_id}.csv"
    target.to_csv(out, index=False)
    build_manifest(
        target,
        dataset_id=dataset_id,
        symbol="EURUSD",
        timeframe=timeframe,
        source="HistData.com Generic ASCII M1 monthly current-year -> resampled",
        source_hash=source_hash,
        quality_status=report.status,
        output_path=normalized / f"EURUSD_{timeframe}_{dataset_id}.manifest.json",
    )
    return {
        "dataset": out,
        "quality": report.to_dict(),
        "m1_quality": m1_report.to_dict(),
        "archives": [item.archive for item in archives],
        "duplicate_rows_removed": duplicate_rows_removed,
        "weekly_session": session_summary,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Download current-year real HistData monthly EURUSD data")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timeframe", default="M5", choices=["M5", "M15"])
    parser.add_argument("--output", default="data/real")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        result = ingest_current_year(
            datetime.strptime(args.start, "%Y-%m-%d").date(),
            datetime.strptime(args.end, "%Y-%m-%d").date(),
            args.output,
            timeframe=args.timeframe,
        )
        print(result["quality"])
        print(result["m1_quality"])
        print({"duplicate_rows_removed": result["duplicate_rows_removed"]})
        print({"weekly_session": result["weekly_session"]})
        return 0
    except HistDataIngestError as exc:
        LOGGER.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
