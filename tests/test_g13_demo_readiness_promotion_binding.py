from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.optimization.g13_demo_readiness_gate_m15 import validate_promotion_binding


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
