"""Diagnose timezone alignment between normalized HistData M1 and Dukascopy M1.

HistData Generic ASCII timestamps are fixed EST (UTC-5, no DST). The ingestion
normalizes them to UTC before writing canonical CSVs. This diagnostic does not
change timestamps or choose a feed; it checks the documented UTC-5 mapping and
searches nearby minute offsets for evidence of an accidental alignment shift.
"""
from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

TARGETS = [
    datetime(2026, 7, 5, 22, 31, tzinfo=timezone.utc),
    datetime(2026, 7, 5, 22, 32, tzinfo=timezone.utc),
    datetime(2026, 7, 5, 22, 34, tzinfo=timezone.utc),
    datetime(2026, 7, 5, 22, 35, tzinfo=timezone.utc),
]
FIXED_EST = timezone(timedelta(hours=-5))


def parse_ts(value: str) -> datetime | None:
    s = str(value).strip()
    if s.isdigit():
        n = int(s)
        if n >= 100_000_000_000:
            return datetime.fromtimestamp(n / 1000, tz=timezone.utc)
        if n >= 100_000_000:
            return datetime.fromtimestamp(n, tz=timezone.utc)
    for candidate in (s, s.replace("Z", "+00:00"), s.replace(" ", "T")):
        try:
            ts = datetime.fromisoformat(candidate)
            return (ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
        except ValueError:
            pass
    return None


def load(path: Path) -> dict[datetime, list[dict[str, str]]]:
    result: dict[datetime, list[dict[str, str]]] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            raw = row.get("timestamp") or row.get("datetime") or row.get("timestamp_utc") or row.get("date")
            if not raw:
                continue
            ts = parse_ts(raw)
            if ts:
                result.setdefault(ts, []).append(row)
    return result


def ohlc(row: dict[str, str]) -> tuple[float, float, float, float] | None:
    def get(name: str) -> float | None:
        value = row.get(name) or row.get(f"{name}_bid")
        try:
            return float(value) if value not in (None, "") else None
        except ValueError:
            return None
    values = tuple(get(k) for k in ("open", "high", "low", "close"))
    return values if all(v is not None for v in values) else None


def main() -> int:
    duka_path = Path("artifacts/dukascopy/eurusd-m1-bid-2026-07-05-2026-07-06.csv")
    hist_paths = sorted(Path("data/real/normalized").rglob("*.csv"))
    duka = load(duka_path)
    hist: dict[datetime, list[dict[str, str]]] = {}
    for path in hist_paths:
        if "source_conflicts" in path.name:
            continue
        for ts, rows in load(path).items():
            hist.setdefault(ts, []).extend(rows)

    print("TIMEZONE_POLICY=HistData fixed EST (UTC-5, no DST)")
    print("UTC_TARGET_TO_HISTDATA_SOURCE_LOCAL=")
    for target in TARGETS:
        print(f"  {target.isoformat()} -> {target.astimezone(FIXED_EST).strftime('%Y-%m-%d %H:%M:%S %z')}")

    # Search nearby shifts only as a diagnostic. Canonical comparison remains UTC.
    offsets = [-360, -300, -240, -120, -60, 0, 60, 120, 240, 300, 360]
    print("NEAREST_SHIFT_DIAGNOSTIC=")
    for target in TARGETS:
        drow = next(iter(duka.get(target, [])), None)
        dov = ohlc(drow) if drow else None
        best = None
        for minutes in offsets:
            candidate_ts = target + timedelta(minutes=minutes)
            for hrow in hist.get(candidate_ts, []):
                hov = ohlc(hrow)
                if dov is None or hov is None:
                    continue
                distance = max(abs(a - b) for a, b in zip(hov, dov))
                item = (distance, minutes, candidate_ts, hov)
                if best is None or item[0] < best[0]:
                    best = item
        if best is None:
            print(f"  {target.isoformat()} -> NO_NEARBY_HISTDATA_MATCH")
        else:
            distance, minutes, candidate_ts, hov = best
            print(f"  {target.isoformat()} -> shift_minutes={minutes} candidate={candidate_ts.isoformat()} max_abs_diff={distance:.5f} hist_ohlc={hov}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
