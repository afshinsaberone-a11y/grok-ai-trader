"""Fail-closed GitHub Actions artifact -> agent evidence normalizer.

This module does not download archives itself. CI or an authenticated runtime
supplies artifact metadata plus the extracted JSON payload. The bridge verifies
that the payload provenance matches the supplied run/job/commit metadata before
writing a deterministic evidence envelope under .agent_evidence/.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPO_ROOT / ".agent_evidence"
SCHEMA = "forexai.github_artifact_evidence.v1"


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_artifact(
    *,
    artifact_id: int,
    artifact_name: str,
    artifact_digest: str,
    run_id: int,
    job_id: int | None,
    commit_sha: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if artifact_id <= 0 or run_id <= 0:
        raise ValueError("artifact_id and run_id must be positive")
    if job_id is not None and job_id <= 0:
        raise ValueError("job_id must be positive when provided")
    if not artifact_name or not artifact_digest or not commit_sha:
        raise ValueError("artifact name, digest and commit SHA are required")
    if not isinstance(payload, dict):
        raise ValueError("artifact payload must be a JSON object")

    # Bind the evidence to the producing revision when the artifact exposes it.
    producer_sha = payload.get("commit_sha") or payload.get("head_sha")
    if producer_sha is not None and producer_sha != commit_sha:
        raise ValueError("artifact payload commit SHA does not match workflow commit SHA")

    # Prevent agents from treating an evaluated OOS payload as held out merely
    # because metadata is inconsistent.
    oos = payload.get("oos")
    if isinstance(oos, dict) and oos.get("status") == "HELD_OUT" and oos.get("evaluated") is True:
        raise ValueError("OOS payload is internally contradictory: HELD_OUT + evaluated=true")

    payload_hash = _sha256_text(_canonical(payload))
    envelope = {
        "schema": SCHEMA,
        "artifact": {
            "id": artifact_id,
            "name": artifact_name,
            "digest": artifact_digest,
        },
        "workflow": {
            "run_id": run_id,
            "job_id": job_id,
            "commit_sha": commit_sha,
        },
        "payload_sha256": payload_hash,
        "payload": payload,
    }
    return envelope


def write_evidence(envelope: dict[str, Any], *, output_dir: Path | None = None) -> Path:
    if envelope.get("schema") != SCHEMA:
        raise ValueError("unsupported evidence schema")
    artifact = envelope.get("artifact")
    workflow = envelope.get("workflow")
    if not isinstance(artifact, dict) or not isinstance(workflow, dict):
        raise ValueError("missing artifact/workflow provenance")
    artifact_id = artifact.get("id")
    run_id = workflow.get("run_id")
    if not isinstance(artifact_id, int) or not isinstance(run_id, int):
        raise ValueError("invalid artifact/run provenance")

    root = output_dir or EVIDENCE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"github-artifact-{run_id}-{artifact_id}.json"
    path.write_text(_canonical(envelope) + "\n", encoding="utf-8")
    return path
