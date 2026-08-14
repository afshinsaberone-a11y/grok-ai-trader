"""HistData.com real EURUSD M1 ingestion."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import logging
import re
import time
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from .manifest import build_manifest, sha256_file
from .normalizer import canonicalize_ohlcv, resample_ohlcv
from .validator import validate_ohlcv

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.histdata.com"
DOWNLOAD_PAGE = BASE_URL + "/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/eurusd/{year}"
POST_URL = BASE_URL + "/get.php"
FIXED_EST = timezone(timedelta(hours=-5))


class HistDataIngestError(RuntimeError):
    """Raised when real HistData data cannot be obtained or validated."""


@dataclass(frozen=True)
class DownloadedYear:
    year: int
    archive: Path
    sha256: str


def _fetch(url: str, *, timeout: int = 60) -> bytes:
    request = Request(url, headers={"User-Agent": "ForexAI/0.1 real-data-ingestion"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _input_attrs(tag: str) -> dict[str, str]:
    """Parse an HTML input tag without assuming attribute ordering."""
    attrs: dict[str, str] = {}
    for match in re.finditer(
        r"([:\w-]+)\s*=\s*([\"'])(.*?)\2",
        tag,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        attrs[match.group(1).lower()] = html.unescape(match.group(3))
    return attrs


def _hidden_form(html_text: str) -> dict[str, str]:
    """Extract the current HistData download form fields.

    HistData has changed the ordering/markup of its form attributes over time.
    Parse complete input tags rather than relying on ``name`` appearing before
    ``value``. This preserves the real-data-only contract: if the live page
    does not expose the required token, ingestion still fails rather than
    fabricating a download URL or data.
    """
    fields: dict[str, str] = {}
    for tag_match in re.finditer(r"<input\b[^>]*>", html_text, flags=re.IGNORECASE | re.DOTALL):
        attrs = _input_attrs(tag_match.group(0))
        key = (attrs.get("name") or attrs.get("id") or "").lower()
        if key in {"tk", "date", "datemonth", "platform", "timeframe", "fxpair"} and "value" in attrs:
            fields[key] = attrs["value"]

    required = ("tk", "date", "datemonth", "platform", "timeframe", "fxpair")
    missing = {k for k in required if k not in fields}
    if missing:
        raise HistDataIngestError(
            "REAL_DATA_REQUIRED: HistData download form missing fields: "
            f"{sorted(missing)}"
        )
    return fields


def _years_for_range(start: date, end: date) -> list[int]:
    if end <= start:
        raise ValueError("end must be after start")
    last_year = end.year - 1 if (end.month, end.day) == (1, 1) else end.year
    return list(range(start.year, last_year + 1))


def fetch_year_archive(year: int, output_dir: str | Path, *, retries: int = 3, timeout: int = 60) -> DownloadedYear:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"HISTDATA_COM_ASCII_EURUSD_M1_{year}.zip"
    if archive.exists() and archive.stat().st_size > 0 and zipfile.is_zipfile(archive):
        return DownloadedYear(year, archive, sha256_file(archive))

    page_url = DOWNLOAD_PAGE.format(year=year)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            page = _fetch(page_url, timeout=timeout).decode("utf-8", errors="replace")
            fields = _hidden_form(page)
            payload = urlencode(fields).encode("utf-8")
            request = Request(
                POST_URL,
                data=payload,
                headers={
                    "User-Agent": "ForexAI/0.1 real-data-ingestion",
                    "Origin": BASE_URL,
                    "Referer": page_url,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/zip, application/octet-stream, */*",
                },
            )
            with urlopen(request, timeout=timeout) as response:
                content = response.read()
            if not content.startswith(b"PK"):
                raise HistDataIngestError(f"HistData returned a non-ZIP response for {year}")
            digest = hashlib.md5(content).hexdigest()
            if fields["tk"].lower() != digest.lower():
                raise HistDataIngestError(
                    f"HistData archive token/hash mismatch for {year}: token={fields['tk']} md5={digest}"
                )
            archive.write_bytes(content)
            return DownloadedYear(year, archive, sha256_file(archive))
        except (HTTPError, URLError, TimeoutError, OSError, HistDataIngestError) as exc:
            last_error = exc
            if archive.exists():
                archive.unlink()
            if attempt < retries:
                time.sleep(attempt * 5)
                LOGGER.warning("HistData retry %d/%d for year %s", attempt + 1, retries, year)
    raise HistDataIngestError(f"Failed to download real HistData EURUSD {year}: {last_error}")


def _extract_year_csv(archive: Path) -> tuple[str, bytes]:
    with zipfile.ZipFile(archive) as zf:
        csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise HistDataIngestError(f"REAL_DATA_REQUIRED: no CSV found in HistData archive {archive}")
        name = next((n for n in csv_names if "EURUSD" in n.upper() and "M1" in n.upper()), csv_names[0])
        return name, zf.read(name)


def _parse_csv(payload: bytes) -> pd.DataFrame:
    text = payload.decode("utf-8", errors="replace")
    rows: list[tuple[str, float, float, float, float, float]] = []
    reader = csv.reader(io.StringIO(text), delimiter=";")
    for row in reader:
        if not row or not row[0] or row[0].startswith("#"):
            continue
        if len(row) < 6:
            continue
        try:
            ts = datetime.strptime(row[0].strip(), "%Y%m%d %H%M%S").replace(tzinfo=FIXED_EST)
            rows.append((
                ts.astimezone(timezone.utc).isoformat(),
                float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]),
            ))
        except ValueError:
            continue
    if not rows:
        raise HistDataIngestError("REAL_DATA_REQUIRED: HistData CSV contained no parseable M1 rows")
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["spread"] = float("nan")
    return df


def _dedupe_exact_source_timestamps(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    duplicate_mask = df.duplicated(subset=["timestamp"], keep=False)
    if not duplicate_mask.any():
        return df, 0
    duplicate_rows = df.loc[duplicate_mask].copy()
    compare_columns = ["timestamp", "open", "high", "low", "close", "volume"]
    conflicting_timestamps: list[str] = []
    removed = 0
    for timestamp, group in duplicate_rows.groupby("timestamp", sort=False):
        unique_payloads = group[compare_columns].drop_duplicates()
        if len(unique_payloads) > 1:
            conflicting_timestamps.append(str(timestamp))
        else:
            removed += len(group) - 1
    if conflicting_timestamps:
        preview = ", ".join(conflicting_timestamps[:5])
        raise HistDataIngestError(
            "REAL_DATA_REQUIRED: conflicting duplicate timestamps in HistData source; "
            f"examples: {preview}"
        )
    deduped = df.drop_duplicates(subset=["timestamp"], keep="first").reset_index(drop=True)
    LOGGER.warning("Removed %d exact duplicate HistData source rows", removed)
    return deduped, removed


def ingest(start: date, end: date, output_dir: str | Path, *, timeframe: str = "M1") -> dict[str, object]:
    years = _years_for_range(start, end)
    all_frames: list[pd.DataFrame] = []
    archives: list[DownloadedYear] = []
    raw_dir = Path(output_dir) / "raw" / "histdata"
    for year in years:
        item = fetch_year_archive(year, raw_dir)
        archives.append(item)
        _, payload = _extract_year_csv(item.archive)
        all_frames.append(_parse_csv(payload))
    df = pd.concat(all_frames, ignore_index=True)
    df = df[(df["timestamp"] >= pd.Timestamp(start, tz="UTC")) & (df["timestamp"] < pd.Timestamp(end, tz="UTC"))]
    df, duplicate_rows_removed = _dedupe_exact_source_timestamps(df)
    df = canonicalize_ohlcv(df, symbol="EURUSD", source="HistData.com")
    m1_report = validate_ohlcv(df, symbol="EURUSD", timeframe="M1")
    if m1_report.status != "PASS":
        raise HistDataIngestError(f"REAL_DATA_REQUIRED: HistData M1 validation failed: {m1_report.to_dict()}")

    normalized = Path(output_dir) / "normalized"
    normalized.mkdir(parents=True, exist_ok=True)
    dataset_id = f"{start:%Y%m%d}_{(end - timedelta(days=1)):%Y%m%d}"
    m1_path = normalized / f"EURUSD_M1_{dataset_id}.csv"
    df.to_csv(m1_path, index=False)
    source_hash = hashlib.sha256("".join(item.sha256 for item in archives).encode("ascii")).hexdigest()
    manifest = build_manifest(
        df, dataset_id=dataset_id, symbol="EURUSD", timeframe="M1",
        source="HistData.com Generic ASCII M1", source_hash=source_hash,
        quality_status=m1_report.status,
        output_path=normalized / f"EURUSD_M1_{dataset_id}.manifest.json",
    )

    result: dict[str, object] = {
        "dataset": m1_path,
        "manifest": manifest,
        "quality": m1_report.to_dict(),
        "archives": [item.archive for item in archives],
        "duplicate_rows_removed": duplicate_rows_removed,
    }
    if timeframe != "M1":
        target = resample_ohlcv(df, "5min" if timeframe == "M5" else "15min")
        report = validate_ohlcv(target, symbol="EURUSD", timeframe=timeframe)
        if report.status != "PASS":
            raise HistDataIngestError(f"REAL_DATA_REQUIRED: HistData {timeframe} validation failed: {report.to_dict()}")
        out = normalized / f"EURUSD_{timeframe}_{dataset_id}.csv"
        target.to_csv(out, index=False)
        result["dataset"] = out
        result["quality"] = report.to_dict()
    return result


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download and validate real HistData EURUSD data")
    parser.add_argument("--symbol", default="EURUSD", choices=["EURUSD"])
    parser.add_argument("--timeframe", default="M1", choices=["M1", "M5", "M15"])
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", default="data/real")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--manifest", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        result = ingest(_parse_date(args.start), _parse_date(args.end), args.output, timeframe=args.timeframe)
        print(result["quality"])
        if args.manifest:
            print(result["manifest"])
        print({"duplicate_rows_removed": result["duplicate_rows_removed"]})
        return 0
    except HistDataIngestError as exc:
        LOGGER.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
