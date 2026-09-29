"""Fail-closed audit of G13 producer-side market-data lineage."""
from __future__ import annotations

if not __debug__:
    raise RuntimeError("G13 producer lineage audit refuses optimized Python execution.")

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "forexai.g13.producer_lineage_audit.m15.v1"
WORKFLOWS = {
    "validation": {
        "workflow_name": "ForexAI G13 Validation M15",
        "workflow_id": 355468598,
        "job_name": "g13-validation",
        "artifact_name": "g13-validation-m15",
        "provenance_name": "g13-validation-data-provenance.json",
    },
    "robustness": {
        "workflow_name": "ForexAI G13 Robustness M15",
        "workflow_id": 355473409,
        "job_name": "g13-robustness",
        "artifact_name": "g13-robustness-m15",
        "provenance_name": "g13-robustness-data-provenance.json",
    },
    "oos": {
        "workflow_name": "ForexAI G13 OOS M15 Current",
        "workflow_id": 356162316,
        "job_name": "G13 2026 OOS M15 Current",
        "artifact_name": "g13-oos-m15-2026-current",
        "provenance_name": "g13-oos-data-provenance.json",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def validate_provenance(
    provenance: dict[str, Any],
    *,
    role: str,
    run_id: int,
    workflow_name: str,
    target_sha: str,
) -> None:
    assert provenance["schema_version"] == "forexai.g13.data_provenance.m15.v1"
    assert provenance["role"] == role
    assert provenance["symbol"] == "EURUSD"
    assert provenance["timeframe"] == "M15"
    assert _hex64(provenance["data_sha256"])
    producer = provenance["producer"]
    assert producer["workflow_name"] == workflow_name
    expected_files = {
        "ForexAI G13 Validation M15": "forexai-g13-validation-m15.yml",
        "ForexAI G13 Robustness M15": "forexai-g13-robustness-m15.yml",
        "ForexAI G13 OOS M15 Current": "forexai-g13-oos-m15-current.yml",
    }
    assert producer["workflow_file"] == expected_files[workflow_name]
    assert int(producer["run_id"]) == run_id
    assert producer["head_sha"] == target_sha


def validate_lineage(
    provenance_by_role: dict[str, dict[str, Any]],
    *,
    target_sha: str,
    run_ids: dict[str, int],
    source_metadata_by_role: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    for role, p in provenance_by_role.items():
        validate_provenance(
            p,
            role=role,
            run_id=run_ids[role],
            workflow_name=WORKFLOWS[role]["workflow_name"],
            target_sha=target_sha,
        )

    validation = provenance_by_role["validation"]
    robustness = provenance_by_role["robustness"]
    oos = provenance_by_role["oos"]

    for field in ("data_sha256", "data_manifest_sha256", "dataset_id", "source", "quality_status", "timezone", "rows", "start", "end"):
        assert validation.get(field) == robustness.get(field), field
    assert validation["quality_status"] == "PASS"
    assert validation["timezone"] == "UTC"
    assert validation["dataset_id"] == "20220101_20251231"

    start = datetime.fromisoformat(oos["start"].replace("Z", "+00:00")).astimezone(timezone.utc)
    end = datetime.fromisoformat(oos["end"].replace("Z", "+00:00")).astimezone(timezone.utc)
    assert start >= datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert end < datetime(2027, 1, 1, tzinfo=timezone.utc)
    assert oos.get("upstream_timeframe") == "M1"
    assert "Dukascopy" in str(oos.get("upstream_source"))
    assert _hex64(oos.get("upstream_data_sha256"))
    assert _hex64(oos.get("upstream_manifest_sha256"))

    assert source_metadata_by_role is not None
    assert set(source_metadata_by_role) == set(WORKFLOWS)
    for role, metadata in source_metadata_by_role.items():
        expected = WORKFLOWS[role]
        assert metadata["workflow_name"] == expected["workflow_name"]
        assert int(metadata["workflow_id"]) == expected["workflow_id"]
        assert metadata["head_branch"] == "main"
        assert metadata["head_sha"] == target_sha
        assert metadata["job_name"] == expected["job_name"]
        assert int(metadata["run_id"]) == run_ids[role]
        assert metadata["artifact_name"] == expected["artifact_name"]
        assert int(metadata["artifact_id"]) > 0
        assert _hex64(metadata["artifact_sha256"])
        assert _hex64(metadata["downloaded_zip_sha256"])
        assert metadata["artifact_sha256"] == metadata["downloaded_zip_sha256"]
        assert metadata["expired"] is False
    return {
        "schema_version": SCHEMA,
        "status": "PASS",
        "target_sha": target_sha,
        "shared_pre_oos_dataset": {
            "data_sha256": validation["data_sha256"],
            "data_manifest_sha256": validation["data_manifest_sha256"],
            "dataset_id": validation["dataset_id"],
            "rows": validation["rows"],
            "start": validation["start"],
            "end": validation["end"],
            "source": validation["source"],
        },
        "oos_dataset": {
            "data_sha256": oos["data_sha256"],
            "rows": oos["rows"],
            "start": oos["start"],
            "end": oos["end"],
            "source": oos.get("source"),
            "upstream_data_sha256": oos["upstream_data_sha256"],
            "upstream_manifest_sha256": oos["upstream_manifest_sha256"],
        },
        "producer_runs": run_ids,
        "producer_evidence": source_metadata_by_role,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-sha", required=True)
    ap.add_argument("--validation-run-id", required=True, type=int)
    ap.add_argument("--robustness-run-id", required=True, type=int)
    ap.add_argument("--oos-run-id", required=True, type=int)
    ap.add_argument("--validation-provenance", required=True, type=Path)
    ap.add_argument("--robustness-provenance", required=True, type=Path)
    ap.add_argument("--oos-provenance", required=True, type=Path)
    ap.add_argument("--validation-source-metadata", type=Path)
    ap.add_argument("--robustness-source-metadata", type=Path)
    ap.add_argument("--oos-source-metadata", type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    run_ids = {
        "validation": args.validation_run_id,
        "robustness": args.robustness_run_id,
        "oos": args.oos_run_id,
    }
    provenance_by_role = {
        "validation": load(args.validation_provenance),
        "robustness": load(args.robustness_provenance),
        "oos": load(args.oos_provenance),
    }
    metadata = {}
    for role, arg in {
        "validation": args.validation_source_metadata,
        "robustness": args.robustness_source_metadata,
        "oos": args.oos_source_metadata,
    }.items():
        if arg is not None:
            metadata[role] = load(arg)
    report = validate_lineage(
        provenance_by_role,
        target_sha=args.target_sha,
        run_ids=run_ids,
        source_metadata_by_role=metadata,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
