from __future__ import annotations

import pytest

from research.optimization.g13_demo_package_preflight_m15 import (
    validate_compile_artifact_binding,
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
