from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.optimization.g13_real_data_provenance import validate


def _rows(count: int = 120):
    start = datetime(2022, 1, 3, tzinfo=timezone.utc)
    rows = []
    for i in range(count):
        ts = start + timedelta(minutes=15 * i)
        close = 1.10 + i * 0.00001
        rows.append((ts.isoformat(), close, close + 0.00002, close - 0.00002, close, 1.0))
    return rows


def _write_pair(tmp_path: Path):
    csv_path = tmp_path / "EURUSD_M15_20220101_20251231.csv"
    manifest_path = tmp_path / "EURUSD_M15_20220101_20251231.manifest.json"
    rows = _rows()
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        writer.writerows(rows)

    payload = {
        "dataset_id": "20220101_20251231",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "source": "HistData.com Generic ASCII M1 resampled to M15",
        "source_hash": "a" * 64,
        "rows": len(rows),
        "start": rows[0][0],
        "end": rows[-1][0],
        "timezone": "UTC",
        "quality_status": "PASS",
        "data_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return csv_path, manifest_path


def test_real_data_provenance_passes(tmp_path: Path):
    csv_path, manifest_path = _write_pair(tmp_path)
    result = validate(csv_path, manifest_path, expected_csv_path=csv_path)
    assert result["rows"] == 120
    assert result["quality_status"] == "PASS"
    assert len(result["data_sha256"]) == 64


@pytest.mark.parametrize("mutation", ["csv", "manifest"])
def test_real_data_provenance_rejects_tampering(tmp_path: Path, mutation: str):
    csv_path, manifest_path = _write_pair(tmp_path)
    if mutation == "csv":
        csv_path.write_text(csv_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
    else:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload["data_sha256"] = "b" * 64
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AssertionError):
        validate(csv_path, manifest_path, expected_csv_path=csv_path)


def test_real_data_provenance_rejects_noncanonical_path(tmp_path: Path):
    csv_path, manifest_path = _write_pair(tmp_path)
    with pytest.raises(AssertionError, match="non-canonical"):
        validate(csv_path, manifest_path, expected_csv_path=tmp_path / "somewhere-else.csv")
