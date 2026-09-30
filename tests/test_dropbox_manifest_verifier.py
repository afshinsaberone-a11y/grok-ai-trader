import json
from pathlib import Path

import pytest

from tools.verify_dropbox_evidence_manifest import (
    ManifestVerificationError,
    load_manifest,
    verify_manifest,
)


def sample_manifest():
    return {
        "schema_version": "forexai.dropbox_evidence_sync.v2",
        "generated_at_utc": "2026-09-30T18:00:00Z",
        "workflow": {
            "name": "ForexAI G13 Final Promotion M15",
            "run_id": 123,
            "run_attempt": 1,
            "head_sha": "a" * 40,
            "conclusion": "success",
        },
        "dropbox_root": "/ForexAI/11_GITHUB_ACTIONS/Artifacts/test/123/attempt-1",
        "source_run": {
            "run_id": 123,
            "run_attempt": 1,
            "workflow_name": "ForexAI G13 Final Promotion M15",
            "created_at": "2026-09-30T18:00:00Z",
            "updated_at": "2026-09-30T18:01:00Z",
            "head_sha": "a" * 40,
            "conclusion": "success",
            "artifacts": [
                {
                    "id": 999,
                    "name": "g13-promotion-manifest-m15",
                    "digest": "sha256:" + "b" * 64,
                    "size_in_bytes": 12,
                }
            ],
        },
        "file_count": 2,
        "files": [
            {
                "remote_path": "/ForexAI/11_GITHUB_ACTIONS/Artifacts/test/123/attempt-1/a.json",
                "bytes": 12,
                "dropbox_size": 12,
                "sha256": "c" * 64,
                "immutable": True,
                "verified": True,
            },
            {
                "remote_path": "/ForexAI/11_GITHUB_ACTIONS/Artifacts/test/123/attempt-1/b.json",
                "bytes": 12,
                "dropbox_size": 12,
                "sha256": "c" * 64,
                "immutable": True,
                "verified": True,
            },
        ],
        "policy": {
            "real_data_only": True,
            "synthetic_generation": False,
            "source_artifacts_immutable": True,
            "source_artifact_digest_verified": True,
            "source_artifact_size_verified": True,
            "remote_paths_write_once": True,
            "idempotent_replay": True,
            "manifest_written_last": True,
        },
    }


def test_valid_manifest_passes(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(sample_manifest()), encoding="utf-8")
    data = load_manifest(path)
    report = verify_manifest(
        data,
        expected_run_id=123,
        expected_run_attempt=1,
        expected_workflow="ForexAI G13 Final Promotion M15",
        expected_head_sha="a" * 40,
        expected_conclusion="success",
    )
    assert report["status"] == "PASS"
    assert report["file_count"] == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("run_id", 124),
        ("run_attempt", 2),
        ("workflow_name", "Other Workflow"),
        ("head_sha", "d" * 40),
        ("conclusion", "failure"),
    ],
)
def test_source_provenance_mismatch_fails(field, value):
    manifest = sample_manifest()
    manifest["source_run"][field] = value
    with pytest.raises(ManifestVerificationError):
        verify_manifest(manifest)


def test_duplicate_remote_path_fails():
    manifest = sample_manifest()
    manifest["files"][1]["remote_path"] = manifest["files"][0]["remote_path"]
    with pytest.raises(ManifestVerificationError, match="duplicate remote"):
        verify_manifest(manifest)


def test_file_outside_run_root_fails():
    manifest = sample_manifest()
    manifest["files"][0]["remote_path"] = "/ForexAI/elsewhere/file.json"
    with pytest.raises(ManifestVerificationError, match="escapes"):
        verify_manifest(manifest)


def test_real_data_and_write_once_flags_are_mandatory():
    manifest = sample_manifest()
    manifest["policy"]["real_data_only"] = False
    with pytest.raises(ManifestVerificationError, match="real_data_only"):
        verify_manifest(manifest)

    manifest = sample_manifest()
    manifest["policy"]["remote_paths_write_once"] = False
    with pytest.raises(ManifestVerificationError, match="remote_paths_write_once"):
        verify_manifest(manifest)


def test_duplicate_sha_content_is_allowed():
    report = verify_manifest(sample_manifest())
    assert report["evidence_sha256_count"] == 2



def test_root_must_bind_run_and_attempt():
    manifest = sample_manifest()
    manifest["dropbox_root"] = "/ForexAI/11_GITHUB_ACTIONS/Artifacts/test/999/attempt-1"
    with pytest.raises(ManifestVerificationError, match="not bound"):
        verify_manifest(manifest)


def test_empty_evidence_payload_fails():
    manifest = sample_manifest()
    manifest["files"] = []
    manifest["file_count"] = 0
    with pytest.raises(ManifestVerificationError, match="no synchronized evidence"):
        verify_manifest(manifest)



def test_generated_timestamp_mismatch_fails():
    manifest = sample_manifest()
    manifest["generated_at_utc"] = "2026-09-30T19:00:00Z"
    with pytest.raises(ManifestVerificationError, match="generated_at_utc"):
        verify_manifest(manifest)
