"""Current-year OOS ingestion with explicit weekly-session filtering."""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

import pandas as pd

from .conflict_audit import audit_timestamp_conflicts
from .histdata_current import fetch_month_archive, _extract_year_csv, _parse_csv
from .histdata_ingest import HistDataIngestError, _dedupe_exact_source_timestamps
from .manifest import build_manifest
from .normalizer import canonicalize_ohlcv, resample_ohlcv
from .session_filter import filter_weekly_session
from .validator import validate_ohlcv


def _month_starts(start: date, end: date) -> list[tuple[int, int]]:
    cur = date(start.year, start.month, 1)
    out: list[tuple[int, int]] = []
    while cur < end:
        out.append((cur.year, cur.month))
        cur = date(cur.year + 1, 1, 1) if cur.month == 12 else date(cur.year, cur.month + 1, 1)
    return out


def ingest(start: date, end: date, output_dir: str, timeframe: str) -> dict[str, object]:
    if start.year != end.year or start.year != datetime.now(timezone.utc).year:
        raise ValueError("session-safe current-year ingest requires the current calendar year")

    raw = Path(output_dir) / "raw" / "histdata"
    frames: list[pd.DataFrame] = []
    archives = []
    for year, month in _month_starts(start, end):
        item = fetch_month_archive(year, month, raw)
        archives.append(item)
        _, payload = _extract_year_csv(item.archive)
        frame = _parse_csv(payload)
        frame["source_year"] = year
        frame["source_month"] = month
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    df = df[(df.timestamp >= pd.Timestamp(start, tz="UTC")) & (df.timestamp < pd.Timestamp(end, tz="UTC"))]
    if df.empty:
        raise HistDataIngestError("REAL_DATA_REQUIRED: empty current-year dataset")

    filtered, session_summary = filter_weekly_session(df, sunday_reopen_utc_hour=20)
    conflict_report, conflict_summary = audit_timestamp_conflicts(filtered)
    audit_dir = Path(output_dir) / "conflict_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    conflict_report.to_csv(audit_dir / "current_year_timestamp_conflicts.csv", index=False)
    (audit_dir / "current_year_timestamp_conflicts.json").write_text(
        pd.Series({"conflicts": conflict_summary.to_dict(), "weekly_session": session_summary}).to_json(indent=2),
        encoding="utf-8",
    )
    if conflict_summary.conflicting_timestamps:
        raise HistDataIngestError(
            "REAL_DATA_REQUIRED: conflicting duplicate timestamps remain after session filter; "
            f"count={conflict_summary.conflicting_timestamps}, max_ohlc_diff={conflict_summary.max_abs_ohlc_diff}"
        )

    df, duplicate_rows_removed = _dedupe_exact_source_timestamps(filtered)
    df = df.drop(columns=["source_year", "source_month"])
    df = canonicalize_ohlcv(df, symbol="EURUSD", source="HistData.com")
    m1 = validate_ohlcv(df, symbol="EURUSD", timeframe="M1")
    if m1.status != "PASS":
        raise HistDataIngestError(f"REAL_DATA_REQUIRED: M1 validation failed: {m1.to_dict()}")

    norm = Path(output_dir) / "normalized"
    norm.mkdir(parents=True, exist_ok=True)
    dataset_id = f"{start:%Y%m%d}_{(end - timedelta(days=1)):%Y%m%d}"
    m1_path = norm / f"EURUSD_M1_{dataset_id}.csv"
    df.to_csv(m1_path, index=False)
    source_hash = hashlib.sha256("".join(x.sha256 for x in archives).encode("ascii")).hexdigest()
    build_manifest(df, dataset_id=dataset_id, symbol="EURUSD", timeframe="M1", source="HistData.com Generic ASCII M1 monthly current-year -> session-filtered", source_hash=source_hash, quality_status=m1.status, output_path=norm / f"EURUSD_M1_{dataset_id}.manifest.json")

    target = resample_ohlcv(df, "5min" if timeframe == "M5" else "15min")
    quality = validate_ohlcv(target, symbol="EURUSD", timeframe=timeframe)
    if quality.status != "PASS":
        raise HistDataIngestError(f"REAL_DATA_REQUIRED: {timeframe} validation failed: {quality.to_dict()}")
    out = norm / f"EURUSD_{timeframe}_{dataset_id}.csv"
    target.to_csv(out, index=False)
    build_manifest(target, dataset_id=dataset_id, symbol="EURUSD", timeframe=timeframe, source="HistData.com -> session-filtered -> resampled", source_hash=source_hash, quality_status=quality.status, output_path=norm / f"EURUSD_{timeframe}_{dataset_id}.manifest.json")
    print({"dataset": str(out), "duplicate_rows_removed": duplicate_rows_removed, "weekly_session": session_summary, "quality": quality.to_dict()})
    return {"dataset": out, "quality": quality.to_dict(), "weekly_session": session_summary}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--timeframe", default="M5", choices=["M5", "M15"])
    p.add_argument("--output", default="data/real")
    a = p.parse_args()
    try:
        ingest(datetime.strptime(a.start, "%Y-%m-%d").date(), datetime.strptime(a.end, "%Y-%m-%d").date(), a.output, a.timeframe)
        return 0
    except (HistDataIngestError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
