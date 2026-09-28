"""Fail-closed validation for the real EURUSD M15 dataset consumed by G13 parity."""
from __future__ import annotations


if not __debug__:
    raise RuntimeError("G13 real-data provenance validator refuses optimized Python execution.")


import argparse
import hashlib
import json
import re
from pathlib import Path

ALLOWED_SOURCES = ("HistData.com", "Dukascopy")
EXPECTED_DATASET_ID = "20220101_20251231"
EXPECTED_SYMBOL = "EURUSD"
EXPECTED_TIMEFRAME = "M15"
START_MIN = "2022-01-01T00:00:00+00:00"
END_EXCLUSIVE = "2026-01-01T00:00:00+00:00"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(csv_path: Path, manifest_path: Path, *, expected_csv_path: Path | None = None) -> dict:
    csv_path = csv_path.resolve()
    manifest_path = manifest_path.resolve()
    if expected_csv_path is not None and csv_path != expected_csv_path.resolve():
        raise AssertionError(f"non-canonical real-data path: {csv_path}")

    if not csv_path.is_file() or not manifest_path.is_file():
        raise AssertionError("REAL_DATA_REQUIRED: dataset CSV and provenance manifest are both required")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == EXPECTED_DATASET_ID
    assert manifest["symbol"] == EXPECTED_SYMBOL
    assert manifest["timeframe"] == EXPECTED_TIMEFRAME
    assert manifest["quality_status"] == "PASS"
    assert manifest["timezone"] == "UTC"
    assert any(source in str(manifest["source"]) for source in ALLOWED_SOURCES)
    assert re.fullmatch(r"[0-9a-fA-F]{64}", str(manifest["source_hash"]))
    assert re.fullmatch(r"[0-9a-fA-F]{64}", str(manifest["data_sha256"]))

    csv_sha256 = sha256(csv_path)
    assert csv_sha256 == manifest["data_sha256"], (csv_sha256, manifest["data_sha256"])

    import pandas as pd

    data = pd.read_csv(csv_path)
    assert int(manifest["rows"]) == len(data), (manifest["rows"], len(data))
    ts = pd.to_datetime(data["timestamp"], utc=True)
    assert len(data) >= 100
    assert ts.is_monotonic_increasing
    assert ts.min() >= pd.Timestamp(START_MIN)
    assert ts.max() < pd.Timestamp(END_EXCLUSIVE)

    manifest_sha256 = sha256(manifest_path)
    return {
        "csv": str(csv_path),
        "manifest": str(manifest_path),
        "data_sha256": csv_sha256,
        "manifest_sha256": manifest_sha256,
        "rows": len(data),
        "source": manifest["source"],
        "dataset_id": manifest["dataset_id"],
        "quality_status": manifest["quality_status"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--expected-csv", type=Path)
    args = ap.parse_args()
    result = validate(args.csv, args.manifest, expected_csv_path=args.expected_csv)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
