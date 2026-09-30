"""Offline, fail-closed verifier for ForexAI Dropbox evidence manifests."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "forexai.dropbox_evidence_sync.v2"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ARTIFACT_DIGEST_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


class ManifestVerificationError(ValueError):
    """Manifest integrity or provenance violation."""


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestVerificationError(f"{field} must be a non-empty string")
    return value.strip()


def _positive_int(value: Any, field: str) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ManifestVerificationError(f"{field} must be a positive integer")
    return value


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestVerificationError("invalid manifest: " + str(path)) from exc
    if not isinstance(data, dict):
        raise ManifestVerificationError("manifest must be a JSON object")
    if data.get("schema_version") != SCHEMA:
        raise ManifestVerificationError("unexpected manifest schema")
    digest = hashlib.sha256(raw).hexdigest()
    if not SHA256_RE.fullmatch(digest):
        raise ManifestVerificationError("manifest SHA-256 generation failed")
    return data


def verify_manifest(
    data: dict[str, Any],
    *,
    expected_run_id: int | None = None,
    expected_run_attempt: int | None = None,
    expected_workflow: str | None = None,
    expected_head_sha: str | None = None,
    expected_conclusion: str | None = None,
) -> dict[str, Any]:
    workflow = data.get("workflow")
    if not isinstance(workflow, dict):
        raise ManifestVerificationError("workflow provenance is missing")

    run_id = _positive_int(workflow.get("run_id"), "workflow.run_id")
    run_attempt = _positive_int(workflow.get("run_attempt"), "workflow.run_attempt")
    workflow_name = _required_string(workflow.get("name"), "workflow.name")
    head_sha = _required_string(workflow.get("head_sha"), "workflow.head_sha")
    conclusion = _required_string(workflow.get("conclusion"), "workflow.conclusion")

    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", head_sha):
        raise ManifestVerificationError("workflow.head_sha is not a valid SHA")

    checks = {
        "run_id": (expected_run_id, run_id),
        "run_attempt": (expected_run_attempt, run_attempt),
        "workflow": (expected_workflow, workflow_name),
        "head_sha": (expected_head_sha, head_sha),
        "conclusion": (expected_conclusion, conclusion),
    }
    for field, (expected, actual) in checks.items():
        if expected is not None and expected != actual:
            raise ManifestVerificationError(
                f"manifest binding mismatch for {field}: expected={expected!r} actual={actual!r}"
            )

    root = _required_string(data.get("dropbox_root"), "dropbox_root")
    if not root.startswith("/ForexAI/"):
        raise ManifestVerificationError("dropbox_root must remain under /ForexAI/")
    expected_root_suffix = f"/{run_id}/attempt-{run_attempt}"
    if not root.endswith(expected_root_suffix):
        raise ManifestVerificationError(
            "dropbox_root is not bound to workflow run/attempt: "
            + root
            + " expected suffix "
            + expected_root_suffix
        )

    source_run = data.get("source_run")
    if not isinstance(source_run, dict):
        raise ManifestVerificationError("source_run provenance is missing")

    for field, expected in (
        ("run_id", run_id),
        ("run_attempt", run_attempt),
        ("workflow_name", workflow_name),
        ("head_sha", head_sha),
        ("conclusion", conclusion),
    ):
        actual = source_run.get(field)
        if actual != expected:
            raise ManifestVerificationError(
                f"source_run mismatch for {field}: expected={expected!r} actual={actual!r}"
            )

    created_at = source_run.get("created_at") or source_run.get("updated_at")
    _required_string(created_at, "source_run.created_at/updated_at")

    artifacts = source_run.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ManifestVerificationError("source_run.artifacts must be non-empty")

    seen_ids: set[int] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise ManifestVerificationError("source_run artifact entry is not an object")
        artifact_id = _positive_int(artifact.get("id"), "source_run.artifact.id")
        if artifact_id in seen_ids:
            raise ManifestVerificationError(
                f"duplicate source artifact id: {artifact_id}"
            )
        seen_ids.add(artifact_id)
        _required_string(artifact.get("name"), "source_run.artifact.name")
        digest = _required_string(artifact.get("digest"), "source_run.artifact.digest")
        if not ARTIFACT_DIGEST_RE.fullmatch(digest):
            raise ManifestVerificationError(
                "source_run.artifact.digest must be sha256:<64 hex>"
            )
        size = artifact.get("size_in_bytes")
        if not isinstance(size, int) or size < 0:
            raise ManifestVerificationError(
                "source_run.artifact.size_in_bytes must be a non-negative integer"
            )

    files = data.get("files")
    file_count = data.get("file_count")
    if not isinstance(files, list) or not isinstance(file_count, int):
        raise ManifestVerificationError("files/file_count are malformed")
    if file_count != len(files):
        raise ManifestVerificationError(
            f"file_count mismatch: declared={file_count} actual={len(files)}"
        )
    if file_count <= 0:
        raise ManifestVerificationError("manifest contains no synchronized evidence payload")

    seen_remote: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise ManifestVerificationError("file entry is not an object")
        remote = _required_string(entry.get("remote_path"), "files.remote_path")
        if not remote.startswith(root.rstrip("/") + "/"):
            raise ManifestVerificationError(
                f"file escapes run-scoped dropbox_root: {remote}"
            )
        if remote in seen_remote:
            raise ManifestVerificationError(
                f"duplicate remote evidence path: {remote}"
            )
        seen_remote.add(remote)

        size = entry.get("bytes")
        dropbox_size = entry.get("dropbox_size")
        if not isinstance(size, int) or size < 0:
            raise ManifestVerificationError("files.bytes must be non-negative integer")
        if dropbox_size is not None and dropbox_size != size:
            raise ManifestVerificationError(
                f"Dropbox size mismatch for {remote}: {dropbox_size} != {size}"
            )

        digest = _required_string(entry.get("sha256"), "files.sha256").lower()
        if not SHA256_RE.fullmatch(digest):
            raise ManifestVerificationError(f"invalid file SHA-256 for {remote}")
        if entry.get("immutable") is not True:
            raise ManifestVerificationError(f"immutable flag missing for {remote}")
        if entry.get("verified") is not True:
            raise ManifestVerificationError(f"verified flag missing for {remote}")

    policy = data.get("policy")
    if not isinstance(policy, dict):
        raise ManifestVerificationError("policy envelope is missing")
    if policy.get("real_data_only") is not True:
        raise ManifestVerificationError("real_data_only must be true")
    if policy.get("synthetic_generation") is not False:
        raise ManifestVerificationError("synthetic_generation must be false")
    if policy.get("source_artifacts_immutable") is not True:
        raise ManifestVerificationError("source_artifacts_immutable must be true")
    if policy.get("source_artifact_digest_verified") is not True:
        raise ManifestVerificationError("source_artifact_digest_verified must be true")
    if policy.get("source_artifact_size_verified") is not True:
        raise ManifestVerificationError("source_artifact_size_verified must be true")
    if policy.get("remote_paths_write_once") is not True:
        raise ManifestVerificationError("remote_paths_write_once must be true")
    if policy.get("idempotent_replay") is not True:
        raise ManifestVerificationError("idempotent_replay must be true")
    if policy.get("manifest_written_last") is not True:
        raise ManifestVerificationError("manifest_written_last must be true")

    return {
        "status": "PASS",
        "schema_version": SCHEMA,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "workflow": workflow_name,
        "head_sha": head_sha,
        "conclusion": conclusion,
        "file_count": file_count,
        "source_artifact_count": len(artifacts),
        "dropbox_root": root,
        "evidence_sha256_count": len(files),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--expected-run-id", type=int)
    parser.add_argument("--expected-run-attempt", type=int)
    parser.add_argument("--expected-workflow")
    parser.add_argument("--expected-head-sha")
    parser.add_argument("--expected-conclusion")
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest))
    report = verify_manifest(
        manifest,
        expected_run_id=args.expected_run_id,
        expected_run_attempt=args.expected_run_attempt,
        expected_workflow=args.expected_workflow,
        expected_head_sha=args.expected_head_sha,
        expected_conclusion=args.expected_conclusion,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ManifestVerificationError, OSError, ValueError) as exc:
        print("DROPBOX_MANIFEST_VERIFY_FAIL_CLOSED: " + str(exc))
        raise SystemExit(2)
