from __future__ import annotations

import hashlib
import json

import pytest

from research.optimization.g13_demo_package_preflight_m15 import (
    validate_compile_artifact_binding,
    validate_data_manifest_binding,
    validate_mq5_source_binding,
)


def _manifest() -> dict:
    return {
        "compile_parity_run_id": 123,
        "ea_source_commit": "abc123",
    }


def test_compile_artifact_binding_passes():
    validate_compile_artifact_binding(
        _manifest(),
        compile_parity_run_id=123,
        compile_parity_head_sha="abc123",
        compile_parity_artifact_digest="sha256:" + "a" * 64,
        downloaded_zip_sha256="a" * 64,
    )


@pytest.mark.parametrize(
    ("kwargs",),
    [
        ({"compile_parity_run_id": 124, "compile_parity_head_sha": "abc123",
           "compile_parity_artifact_digest": "sha256:" + "a" * 64,
           "downloaded_zip_sha256": "a" * 64},),
        ({"compile_parity_run_id": 123, "compile_parity_head_sha": "wrong",
           "compile_parity_artifact_digest": "sha256:" + "a" * 64,
           "downloaded_zip_sha256": "a" * 64},),
        ({"compile_parity_run_id": 123, "compile_parity_head_sha": "abc123",
           "compile_parity_artifact_digest": "sha256:" + "b" * 64,
           "downloaded_zip_sha256": "a" * 64},),
    ],
)
def test_compile_artifact_binding_rejects_mismatch(kwargs):
    with pytest.raises(AssertionError):
        validate_compile_artifact_binding(_manifest(), **kwargs)


def test_mq5_source_binding_passes(tmp_path):
    source = tmp_path / "ForexAI_G13_Candidate_2.mq5"
    source.write_text("exact-source", encoding="utf-8")
    import hashlib

    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    rows = {2: {"mq5_sha256": expected}}

    assert validate_mq5_source_binding(rows, source) == expected


def test_mq5_source_binding_rejects_tampering(tmp_path):
    source = tmp_path / "ForexAI_G13_Candidate_2.mq5"
    source.write_text("tampered-source", encoding="utf-8")
    rows = {2: {"mq5_sha256": "a" * 64}}

    with pytest.raises(AssertionError):
        validate_mq5_source_binding(rows, source)


def test_data_manifest_binding_passes(tmp_path):
    data_manifest = tmp_path / "g13_real_eurusd_m15.manifest.json"
    payload = {
        "dataset_id": "20220101_20251231",
        "source": "HistData.com Generic ASCII M1 resampled to M15",
        "quality_status": "PASS",
        "data_sha256": "a" * 64,
        "rows": 120,
    }
    data_manifest.write_text(json.dumps(payload), encoding="utf-8")
    manifest_sha = hashlib.sha256(data_manifest.read_bytes()).hexdigest()
    parity = {
        "data_manifest_sha256": manifest_sha,
        "data_sha256": "a" * 64,
        "data_provenance": {
            "dataset_id": payload["dataset_id"],
            "source": payload["source"],
            "quality_status": payload["quality_status"],
        },
    }
    validate_data_manifest_binding(parity, data_manifest)


def test_data_manifest_binding_rejects_tampering(tmp_path):
    data_manifest = tmp_path / "g13_real_eurusd_m15.manifest.json"
    payload = {
        "dataset_id": "20220101_20251231",
        "source": "HistData.com Generic ASCII M1 resampled to M15",
        "quality_status": "PASS",
        "data_sha256": "a" * 64,
        "rows": 120,
    }
    data_manifest.write_text(json.dumps(payload), encoding="utf-8")
    parity = {
        "data_manifest_sha256": "b" * 64,
        "data_sha256": "a" * 64,
        "data_provenance": {
            "dataset_id": payload["dataset_id"],
            "source": payload["source"],
            "quality_status": payload["quality_status"],
        },
    }
    with pytest.raises(AssertionError):
        validate_data_manifest_binding(parity, data_manifest)
