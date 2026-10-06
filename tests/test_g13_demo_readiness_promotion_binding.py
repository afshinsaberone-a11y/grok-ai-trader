from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.optimization.g13_demo_readiness_gate_m15 import validate_preflight_binding, validate_promotion_binding


def _write(tmp_path: Path, name: str, payload: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _case(tmp_path: Path):
    provenance = {
        "schema_version": "forexai.g13.promotion_evidence_provenance.m15.v1",
        "sources": {
            "validation": {"run_id": 34559825574},
            "robustness": {"run_id": 34679210600},
            "oos": {"run_id": 34679937623},
        },
    }
    promotion = {
        "schema_version": "forexai.g13.promotion_manifest.m15.v1",
        "status": "PROMOTION_READY",
        "evidence_provenance_sha256": __import__(
            "research.optimization.g13_demo_readiness_gate_m15",
            fromlist=["canonical_hash"],
        ).canonical_hash(provenance),
    }
    p = _write(tmp_path, "promotion.json", promotion)
    prov = _write(tmp_path, "source-provenance.json", provenance)
    attestation = {
        "schema_version": "forexai.g13.promotion_run_attestation.m15.v1",
        "workflow_run_id": 999,
        "head_sha": "abc123",
        "manifest_sha256": __import__(
            "research.optimization.g13_demo_readiness_gate_m15",
            fromlist=["file_sha256"],
        ).file_sha256(p),
        "provenance_sha256": __import__(
            "research.optimization.g13_demo_readiness_gate_m15",
            fromlist=["file_sha256"],
        ).file_sha256(prov),
    }
    a = _write(tmp_path, "attestation.json", attestation)
    return p, prov, a


def test_exact_promotion_binding_passes(tmp_path: Path):
    p, prov, att = _case(tmp_path)
    validate_promotion_binding(
        json.loads(p.read_text()),
        json.loads(prov.read_text()),
        json.loads(att.read_text()),
        promotion_run_id=999,
        main_head_sha="abc123",
        promotion_path=p,
        provenance_path=prov,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workflow_run_id", 1000),
        ("head_sha", "wrong"),
        ("manifest_sha256", "bad"),
        ("provenance_sha256", "bad"),
    ],
)
def test_tampered_promotion_attestation_fails(tmp_path: Path, field: str, value):
    p, prov, att = _case(tmp_path)
    payload = json.loads(att.read_text())
    payload[field] = value
    with pytest.raises(AssertionError):
        validate_promotion_binding(
            json.loads(p.read_text()),
            json.loads(prov.read_text()),
            payload,
            promotion_run_id=999,
            main_head_sha="abc123",
            promotion_path=p,
            provenance_path=prov,
        )


def test_provenance_hash_mismatch_fails(tmp_path: Path):
    p, prov, att = _case(tmp_path)
    payload = json.loads(p.read_text())
    payload["evidence_provenance_sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_promotion_binding(
            payload,
            json.loads(prov.read_text()),
            json.loads(att.read_text()),
            promotion_run_id=999,
            main_head_sha="abc123",
            promotion_path=p,
            provenance_path=prov,
        )


def _preflight():
    hashes = {
        str(cid): f"hash-{cid}"
        for cid in [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48]
    }
    return {
        "schema_version": "forexai.g13.controlled_demo_package_preflight.m15.v1",
        "status": "PASS",
        "candidate_count": 15,
        "candidate_ids": [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48],
        "binary_hashes_verified": 15,
        "source_hashes_verified": 15,
        "source_safety_contracts_verified": 15,
        "real_data_only": True,
        "synthetic_data": False,
        "demo_trading_allowed_by_source": False,
        "live_trading_allowed": False,
        "compile_parity_run_id": 55,
        "compile_parity_head_sha": "main-sha",
        "compile_parity_artifact_id": 66,
        "compile_parity_artifact_digest": "sha256:" + "a" * 64,
        "downloaded_zip_sha256": "a" * 64,
        "promotion_manifest_sha256": "p" * 64,
        "candidate_config_hashes": hashes,
    }


def _promotion():
    return {
        "status": "PROMOTION_READY",
        "candidates": [
            {"candidate_id": int(cid), "config_hash": value}
            for cid, value in _preflight()["candidate_config_hashes"].items()
        ],
    }


def test_exact_preflight_binding_passes():
    validate_preflight_binding(
        _promotion(),
        _preflight(),
        promotion_manifest_sha256=_preflight()["promotion_manifest_sha256"],
        parity_run_id=55,
        parity_head_sha="main-sha",
        main_head_sha="main-sha",
        promoted_ids=tuple(_preflight()["candidate_ids"]),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("compile_parity_run_id", 56),
        ("compile_parity_head_sha", "wrong"),
        ("promotion_manifest_sha256", "q" * 64),
        ("downloaded_zip_sha256", "b" * 64),
    ],
)
def test_preflight_binding_rejects_tampering(field, value):
    payload = _preflight()
    payload[field] = value
    with pytest.raises(AssertionError):
        validate_preflight_binding(
            _promotion(),
            payload,
            promotion_manifest_sha256="p" * 64,
            parity_run_id=55,
            parity_head_sha="main-sha",
            main_head_sha="main-sha",
        )


def test_preflight_candidate_hash_mismatch_fails():
    payload = _preflight()
    payload["candidate_config_hashes"]["2"] = "wrong"
    with pytest.raises(AssertionError):
        validate_preflight_binding(
            _promotion(),
            payload,
            promotion_manifest_sha256="p" * 64,
            parity_run_id=55,
            parity_head_sha="main-sha",
            main_head_sha="main-sha",
        )
