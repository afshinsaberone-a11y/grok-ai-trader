from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from .histdata_current import _extract_year_csv, _parse_csv, fetch_month_archive, month_starts
from .session_time_audit import audit_session_time


def run(start: str, end: str, output_dir: str = "data/real") -> dict[str, object]:
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    raw_dir = Path(output_dir) / "raw" / "histdata"
    frames: list[pd.DataFrame] = []
    for year, month in month_starts(start_date, end_date):
        item = fetch_month_archive(year, month, raw_dir)
        _, payload = _extract_year_csv(item.archive)
        frame = _parse_csv(payload)
        frame = frame[(frame["timestamp"] >= pd.Timestamp(start_date, tz="UTC")) & (frame["timestamp"] < pd.Timestamp(end_date, tz="UTC"))]
        frames.append(frame)

    if not frames:
        raise RuntimeError("No monthly data downloaded")
    df = pd.concat(frames, ignore_index=True)
    report = audit_session_time(df).to_dict()
    report["duplicate_timestamp_count"] = int(df["timestamp"].duplicated(keep=False).sum())

    out = Path(output_dir) / "session_time_audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "current_year_session_time_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", default="data/real")
    args = parser.parse_args()
    print(run(args.start, args.end, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
