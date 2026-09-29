"""Build immutable, byte-level provenance for G13 M15 evidence datasets.

This helper never fabricates market-data values. It hashes the exact CSV bytes
consumed by a producer workflow and records the upstream manifest bytes when
available.
"""
from __future__ import annotations

if not __debug__:
    raise RuntimeError("G13 data provenance refuses optimized Python execution.")

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "forexai.g13.data_provenance.m15.v1"
ALLOWED_SOURCES = ("HistData.com", "Dukascopy")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _inspect_csv(path: Path) -> tuple[int, str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        assert reader.fieldnames is not None
        assert required.issubset(reader.fieldnames), sorted(required - set(reader.fieldnames))
        rows = list(reader)

    assert rows, "G13 data provenance requires a non-empty CSV"
    timestamps = [
        datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        for row in rows
    ]
    assert all(ts.tzinfo is not None for ts in timestamps)
    assert all(left < right for left, right in zip(timestamps, timestamps[1:]))
    first = timestamps[0].astimezone(timezone.utc).isoformat()
    last = timestamps[-1].astimezone(timezone.utc).isoformat()
    return len(rows), first, last


def build(
    csv_path: Path,
    *,
    role: str,
    manifest_path: Path | None = None,
    upstream_manifest_path: Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M15",
    source: str | None = None,
    producer_workflow: str | None = None,
    producer_workflow_id: int | None = None,
    producer_run_id: int | None = None,
    producer_job_name: str | None = None,
    producer_job_id: int | None = None,
    head_sha: str | None = None,
) -> dict[str, Any]:
    csv_path = csv_path.resolve()
    assert csv_path.is_file(), f"missing dataset CSV: {csv_path}"
    assert role in {"validation", "robustness", "oos"}
    assert symbol == "EURUSD" and timeframe == "M15"

    rows, start, end = _inspect_csv(csv_path)
    data_sha256 = sha256(csv_path)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "role": role,
        "symbol": symbol,
        "timeframe": timeframe,
        "data_sha256": data_sha256,
        "rows": rows,
        "start": start,
        "end": end,
    }

    if manifest_path is not None:
        manifest_path = manifest_path.resolve()
        assert manifest_path.is_file(), f"missing dataset manifest: {manifest_path}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest.get("symbol") == symbol
        assert manifest.get("timeframe") == timeframe
        assert manifest.get("quality_status") == "PASS"
        assert manifest.get("timezone") == "UTC"
        manifest_sha256 = sha256(manifest_path)
        assert manifest.get("data_sha256") == data_sha256
        assert any(source_name in str(manifest.get("source")) for source_name in ALLOWED_SOURCES)
        payload["dataset_id"] = manifest["dataset_id"]
        payload["source"] = manifest["source"]
        payload["source_hash"] = manifest["source_hash"]
        payload["quality_status"] = manifest["quality_status"]
        payload["timezone"] = manifest["timezone"]
        payload["data_manifest_sha256"] = manifest_sha256
        payload["manifest_data_sha256"] = manifest["data_sha256"]

    if upstream_manifest_path is not None:
        upstream_manifest_path = upstream_manifest_path.resolve()
        assert upstream_manifest_path.is_file(), f"missing upstream manifest: {upstream_manifest_path}"
        upstream = json.loads(upstream_manifest_path.read_text(encoding="utf-8"))
        upstream_sha256 = sha256(upstream_manifest_path)
        assert upstream.get("symbol") == symbol
        assert any(source_name in str(upstream.get("source")) for source_name in ALLOWED_SOURCES)
        upstream_data_sha256 = upstream.get("data_sha256")
        assert isinstance(upstream_data_sha256, str) and len(upstream_data_sha256) == 64 and all(ch in "0123456789abcdefABCDEF" for ch in upstream_data_sha256)
        payload["upstream_manifest_sha256"] = upstream_sha256
        payload["upstream_data_sha256"] = upstream_data_sha256
        payload["upstream_dataset_id"] = upstream.get("dataset_id")
        payload["upstream_timeframe"] = upstream.get("timeframe")
        payload["upstream_source"] = upstream.get("source")

    if source is not None:
        assert any(source_name in source for source_name in ALLOWED_SOURCES)
        payload["source"] = source

    producer = {
        "workflow_name": producer_workflow,
        "workflow_id": producer_workflow_id,
        "run_id": producer_run_id,
        "job_name": producer_job_name,
        "job_id": producer_job_id,
        "head_sha": head_sha,
    }
    payload["producer"] = {k: v for k, v in producer.items() if v is not None}

    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--role", required=True, choices=("validation", "robustness", "oos"))
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--upstream-manifest", type=Path)
    ap.add_argument("--source")
    ap.add_argument("--producer-workflow")
    ap.add_argument("--producer-workflow-id", type=int)
    ap.add_argument("--producer-run-id", type=int)
    ap.add_argument("--producer-job-name")
    ap.add_argument("--producer-job-id", type=int)
    ap.add_argument("--head-sha")
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    payload = build(
        args.csv,
        role=args.role,
        manifest_path=args.manifest,
        upstream_manifest_path=args.upstream_manifest,
        source=args.source,
        producer_workflow=args.producer_workflow,
        producer_workflow_id=args.producer_workflow_id,
        producer_run_id=args.producer_run_id,
        producer_job_name=args.producer_job_name,
        producer_job_id=args.producer_job_id,
        head_sha=args.head_sha,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
