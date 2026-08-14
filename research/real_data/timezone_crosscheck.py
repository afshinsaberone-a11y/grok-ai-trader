"""Verify HistData timezone normalization against an explicit DST-aware policy."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TARGETS = [
    datetime(2026, 7, 5, 22, 31, tzinfo=timezone.utc),
    datetime(2026, 7, 5, 22, 32, tzinfo=timezone.utc),
    datetime(2026, 7, 5, 22, 34, tzinfo=timezone.utc),
    datetime(2026, 7, 5, 22, 35, tzinfo=timezone.utc),
]
HISTDATA_LOCAL_ZONE = ZoneInfo("America/New_York")


def main() -> int:
    print("TIMEZONE_POLICY=HistData local America/New_York (DST-aware)")
    print("UTC_TARGET_TO_HISTDATA_SOURCE_LOCAL=")
    for target in TARGETS:
        local = target.astimezone(HISTDATA_LOCAL_ZONE)
        print(f"  {target.isoformat()} -> {local.strftime('%Y-%m-%d %H:%M:%S %z %Z')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
