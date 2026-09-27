from __future__ import annotations

import pytest

from research.optimization.g13_demo_package_preflight_m15 import (
    validate_compile_artifact_binding,
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
