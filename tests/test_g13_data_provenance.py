from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from research.optimization.g13_data_provenance import build


def _write_csv(path: Path, count: int = 120) -> None:
    start = datetime(2022, 1, 3, tzinfo=timezone.utc)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for i in range(count):
            ts = start + timedelta(minutes=15 * i)
            close = 1.10 + i * 0.00001
            writer.writerow([ts.isoformat(), close, close + 0.00002, close - 0.00002, close, 1.0])


def _write_manifest(path: Path, csv_path: Path, rows: int = 120) -> None:
    start = datetime(2022, 1, 3, tzinfo=timezone.utc).isoformat()
    end = (datetime(2022, 1, 3, tzinfo=timezone.utc) + timedelta(minutes=15 * (rows - 1))).isoformat()
    payload = {
        "dataset_id": "20220101_20251231",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "source": "HistData.com Generic ASCII M1 resampled to M15",
        "source_hash": "a" * 64,
        "rows": rows,
        "start": start,
        "end": end,
        "timezone": "UTC",
        "quality_status": "PASS",
        "data_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_binds_exact_csv_and_manifest(tmp_path: Path):
    csv_path = tmp_path / "EURUSD_M15_20220101_20251231.csv"
    manifest_path = tmp_path / "EURUSD_M15_20220101_20251231.manifest.json"
    _write_csv(csv_path)
    _write_manifest(manifest_path, csv_path)

    result = build(
        csv_path,
        role="validation",
        manifest_path=manifest_path,
        producer_workflow="ForexAI G13 Validation M15",
        producer_workflow_id=355468598,
        producer_run_id=123,
        producer_job_name="g13-validation",
        producer_job_id=456,
        head_sha="deadbeef",
    )

    assert result["data_sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    assert result["data_manifest_sha256"] == hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert len(result["manifest_identity_sha256"]) == 64
    assert result["role"] == "validation"
    assert result["producer"]["workflow_id"] == 355468598
    assert result["producer"]["run_id"] == 123


def test_build_rejects_manifest_data_hash_mismatch(tmp_path: Path):
    csv_path = tmp_path / "EURUSD_M15_20220101_20251231.csv"
    manifest_path = tmp_path / "EURUSD_M15_20220101_20251231.manifest.json"
    _write_csv(csv_path)
    _write_manifest(manifest_path, csv_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["data_sha256"] = "b" * 64
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AssertionError):
        build(csv_path, role="robustness", manifest_path=manifest_path)


def test_build_supports_derived_oos_with_upstream_manifest(tmp_path: Path):
    csv_path = tmp_path / "EURUSD_M15_20260101_20260928.csv"
    upstream_manifest = tmp_path / "EURUSD_M1_20250101_20260928.manifest.json"
    _write_csv(csv_path)
    upstream_manifest.write_text(
        json.dumps(
            {
                "dataset_id": "20250101_20260928",
                "symbol": "EURUSD",
                "timeframe": "M1",
                "source": "Dukascopy JETTA",
                "data_sha256": "c" * 64,
            }
        ),
        encoding="utf-8",
    )

    result = build(
        csv_path,
        role="oos",
        upstream_manifest_path=upstream_manifest,
        source="Dukascopy JETTA M1 resampled to M15",
    )

    assert result["role"] == "oos"
    assert result["source"] == "Dukascopy JETTA M1 resampled to M15"
    assert result["upstream_data_sha256"] == "c" * 64
    assert len(result["upstream_manifest_sha256"]) == 64


def test_manifest_identity_ignores_volatile_created_at(tmp_path: Path):
    csv_path = tmp_path / "EURUSD_M15_20220101_20251231.csv"
    manifest_path = tmp_path / "EURUSD_M15_20220101_20251231.manifest.json"
    _write_csv(csv_path)
    _write_manifest(manifest_path, csv_path)

    first = json.loads(manifest_path.read_text(encoding="utf-8"))
    first["created_at"] = "2026-09-29T00:00:00+00:00"
    manifest_path.write_text(json.dumps(first), encoding="utf-8")
    one = build(csv_path, role="validation", manifest_path=manifest_path)

    second = dict(first)
    second["created_at"] = "2026-09-30T00:00:00+00:00"
    manifest_path.write_text(json.dumps(second), encoding="utf-8")
    two = build(csv_path, role="validation", manifest_path=manifest_path)

    assert one["data_manifest_sha256"] != two["data_manifest_sha256"]
    assert one["manifest_identity_sha256"] == two["manifest_identity_sha256"]


def test_validation_requires_exact_manifest(tmp_path: Path):
    csv_path = tmp_path / "EURUSD_M15_20220101_20251231.csv"
    _write_csv(csv_path)
    with pytest.raises(AssertionError):
        build(csv_path, role="validation")


def test_oos_requires_exact_upstream_manifest(tmp_path: Path):
    csv_path = tmp_path / "EURUSD_M15_20260101_20260928.csv"
    _write_csv(csv_path)
    with pytest.raises(AssertionError):
        build(csv_path, role="oos")
