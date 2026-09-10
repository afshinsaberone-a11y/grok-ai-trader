from __future__ import annotations

import json

import pytest

from agents.github_artifact_evidence_bridge import normalize_artifact, write_evidence


def test_normalize_binds_artifact_to_provenance(tmp_path):
    payload = {
        "schema": "forexai.sp2l_g8_real_baseline.v1",
        "commit_sha": "abc123",
        "strategy_family": "SP2L",
        "oos": {"status": "HELD_OUT", "evaluated": False},
    }
    envelope = normalize_artifact(
        artifact_id=101,
        artifact_name="sp2l-g8",
        artifact_digest="sha256:deadbeef",
        run_id=202,
        job_id=303,
        commit_sha="abc123",
        payload=payload,
    )
    path = write_evidence(envelope, output_dir=tmp_path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema"] == "forexai.github_artifact_evidence.v1"
    assert saved["artifact"]["id"] == 101
    assert saved["workflow"] == {"run_id": 202, "job_id": 303, "commit_sha": "abc123"}
    assert saved["payload"]["strategy_family"] == "SP2L"


def test_rejects_commit_mismatch():
    with pytest.raises(ValueError, match="commit SHA"):
        normalize_artifact(
            artifact_id=1,
            artifact_name="x",
            artifact_digest="sha256:x",
            run_id=2,
            job_id=3,
            commit_sha="expected",
            payload={"commit_sha": "other"},
        )


def test_rejects_contradictory_oos_state():
    with pytest.raises(ValueError, match="OOS payload"):
        normalize_artifact(
            artifact_id=1,
            artifact_name="x",
            artifact_digest="sha256:x",
            run_id=2,
            job_id=3,
            commit_sha="abc",
            payload={"oos": {"status": "HELD_OUT", "evaluated": True}},
        )


def test_rejects_missing_provenance():
    with pytest.raises(ValueError):
        normalize_artifact(
            artifact_id=0,
            artifact_name="x",
            artifact_digest="sha256:x",
            run_id=2,
            job_id=3,
            commit_sha="abc",
            payload={},
        )
