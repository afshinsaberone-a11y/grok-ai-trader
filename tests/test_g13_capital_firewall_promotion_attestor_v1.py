from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import tools.g13_capital_firewall_promotion_attestor_v1 as attestor_module
from tools.g13_capital_firewall_promotion_attestor_v1 import (
    ATTESTOR_KEY_ID,
    GRANT_KEY_ID,
    GRANT_SCHEMA,
    REQUIRED_RUNS,
    RUN_ID_FIELDS,
    AttestorError,
    _artifact_documents,
    _validate_evidence,
    _verify_grant,
    build_signed_attestation,
    canonical_json,
)


NOW = datetime(2026, 10, 12, 16, 30, tzinfo=timezone.utc)
REPO = "afshinsaberone-a11y/grok-ai-trader"
SHA = "e" * 40
CONFIG = "c" * 64
DATA = "d" * 64
MANIFEST = "a" * 64
GRANT_KEY = Ed25519PrivateKey.generate()
ATTESTOR_KEY = Ed25519PrivateKey.generate()


def raw_public(key: Ed25519PrivateKey) -> str:
    return base64.b64encode(key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )).decode("ascii")


def make_grant(**updates):
    body = {
        "schema": GRANT_SCHEMA,
        "key_id": GRANT_KEY_ID,
        "grant_id": "capital-firewall-grant-20261012-001",
        "repository": REPO,
        "commit_sha": SHA,
        "run_ids": {
            "validation": 41001,
            "robustness": 41002,
            "oos": 41003,
            "promotion": 41004,
            "parity": 41005,
            "package_preflight": 41006,
            "safety_audit": 41007,
            "readiness": 41008,
        },
        "candidate_id": 2,
        "candidate_config_hash": CONFIG,
        "signal_id": "signal-20261012-001",
        "trade_id": "FOREXAI-G13-C2-S",
        "authorization_id": "auth-20261012-001",
        "reservation_id": "reserve-20261012-001",
        "scope": "ONE_SIGNAL_DEMO_ONLY",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "side": "SELL",
        "issued_at_utc": NOW.isoformat(),
        "valid_until_utc": (NOW + timedelta(minutes=5)).isoformat(),
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
    }
    body.update(updates)
    body["signature"] = {
        "algorithm": "Ed25519",
        "key_id": GRANT_KEY_ID,
        "signature": base64.b64encode(GRANT_KEY.sign(canonical_json(body))).decode("ascii"),
    }
    return body


def fixture_chain():
    run_ids = {
        "validation": 41001,
        "robustness": 41002,
        "oos": 41003,
        "promotion": 41004,
        "parity": 41005,
        "package_preflight": 41006,
        "safety_audit": 41007,
        "readiness": 41008,
    }
    runs = {
        role: {
            "id": rid, "name": spec["name"], "path": spec["path"],
            "workflow_id": spec["workflow_id"], "head_sha": SHA,
            "_attestor_success_job_id": 61000 + rid,
        }
        for role, rid in run_ids.items()
        for spec in [REQUIRED_RUNS[role]]
    }
    artifacts = {}
    digests = {}
    for role, spec in REQUIRED_RUNS.items():
        artifacts[role] = {
            "id": 51000 + run_ids[role],
            "name": spec.get("artifact_name", f"g13-mt5-compile-parity-{run_ids[role]}"),
        }
        digests[role] = "sha256:" + hashlib.sha256(f"artifact-{role}".encode()).hexdigest()
        artifacts[role]["digest"] = digests[role]

    source_artifacts = {}
    for role in ("validation", "robustness", "oos"):
        source_artifacts[role] = {
            "run_id": runs[role]["id"],
            "artifact_id": artifacts[role]["id"],
            "artifact_name": artifacts[role]["name"],
            "artifact_digest": digests[role],
            "run_head_sha": SHA,
            "head_branch": "main",
            "workflow_id": runs[role]["workflow_id"],
            "workflow_name": runs[role]["name"],
            "job_id": runs[role]["_attestor_success_job_id"],
            "job_name": REQUIRED_RUNS[role]["job_name"],
        }

    validation = {
        "schema": "forexai.g13.validation_m15.v1",
        "real_data_only": True,
        "selection_used_2025": False,
        "oos_evaluated": False,
        "validation_qualified_count": 1,
        "candidates": [{"candidate_id": 2, "validation_pass": True}],
    }
    robustness = {
        "schema": "forexai.g13.robustness_m15.v1",
        "status": "PASS",
        "real_data_only": True,
        "selection_performed": False,
        "optimization_enabled": False,
        "oos": {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False},
        "candidate_count": 1,
        "robustness_pass_count": 1,
        "candidates": [{"candidate_id": 2, "robustness_pass": True}],
    }
    oos = {
        "schema_version": "forexai.g13.oos_m15.2026.v1",
        "real_data_only": True,
        "selection_performed": False,
        "optimization_enabled": False,
        "parameters_frozen": True,
        "oos": {
            "status": "EVALUATED",
            "evaluated": True,
            "optimization_allowed": False,
            "selection_allowed": False,
        },
        "oos_pass_count": 1,
        "candidates": [{"candidate_id": 2, "oos_pass": True}],
    }
    promotion = {
        "schema_version": "forexai.g13.promotion_manifest.m15.v1",
        "status": "PROMOTION_READY",
        "decision_policy": {
            "selection_performed": False,
            "optimization_performed": False,
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
        },
        "promoted_candidate_ids": [2],
        "candidates": [{"candidate_id": 2, "config_hash": CONFIG}],
        "source_artifacts": source_artifacts,
    }
    parity = {
        "schema_version": "forexai.g13.mql5_signal_parity.v2",
        "status": "PASS",
        "real_data_only": True,
        "synthetic_data": False,
        "selection_performed": False,
        "optimization_enabled": False,
        "candidate_count": 1,
        "passed_count": 1,
        "data_sha256": DATA,
        "data_manifest_sha256": MANIFEST,
        "results": [{"candidate_id": 2, "status": "PASS", "actual_signals": 12, "expected_signals": 12}],
    }
    package = {
        "schema_version": "forexai.g13.demo_package_manifest.m15.v2",
        "ea_source_commit": SHA,
        "compile_parity_run_id": run_ids["parity"],
        "promoted_candidate_ids": [2],
        "demo_trading_allowed_by_source": False,
        "live_trading_allowed": False,
        "real_data_only": True,
        "synthetic_data": False,
        "data_sha256": DATA,
        "data_manifest_sha256": MANIFEST,
    }
    preflight = {
        "schema_version": "forexai.g13.controlled_demo_package_preflight.m15.v1",
        "status": "PASS",
        "ea_source_commit": SHA,
        "compile_parity_head_sha": SHA,
        "compile_parity_run_id": run_ids["parity"],
        "compile_parity_artifact_id": artifacts["parity"]["id"],
        "compile_parity_artifact_digest": digests["parity"],
        "downloaded_zip_sha256": digests["parity"][7:],
        "candidate_ids": [2],
        "candidate_count": 1,
        "source_hashes_verified": 1,
        "binary_hashes_verified": 1,
        "source_safety_contracts_verified": 1,
        "demo_trading_allowed_by_source": False,
        "live_trading_allowed": False,
        "real_data_only": True,
        "synthetic_data": False,
        "data_sha256": DATA,
        "data_manifest_sha256": MANIFEST,
    }
    safety = {
        "schema": "forexai.g13.execution_safety_audit_m15.v1",
        "status": "PASS",
        "scope": {"candidate_count": 1, "candidate_ids": [2]},
        "policy": {"live_trading_allowed": False, "demo_trading_default_authorized": False},
        "sources": [{"candidate_id": 2, "pass": True}],
        "matrix": [{"pass": True} for _ in range(1536)],
    }
    readiness = {
        "schema": "forexai.g13.demo_readiness_gate_m15.v1",
        "status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
        "next_gate": "CONTROLLED_DEMO_EXECUTION_AUDIT",
        "live_remains_disabled": True,
        "promotion": {
            "head_sha": SHA,
            "run_id": run_ids["promotion"],
            "status": "PROMOTION_READY",
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
        },
        "evidence": {
            "parity_head_sha": SHA,
            "parity_status": "PASS",
            "parity_passed_count": 1,
            "safety_head_sha": SHA,
            "data_sha256": DATA,
            "data_manifest_sha256": MANIFEST,
        },
        "preflight": {
            "status": "PASS",
            "run_id": run_ids["package_preflight"],
            "compile_parity_run_id": run_ids["parity"],
        },
        "runtime": {"orders_submitted": False, "real_account_detected": False},
    }
    docs = {
        "validation": validation,
        "robustness": robustness,
        "oos": oos,
        "promotion": promotion,
        "parity": parity,
        "parity_package": package,
        "package_preflight": preflight,
        "safety_audit": safety,
        "readiness": readiness,
    }
    grant = make_grant()
    return grant, runs, artifacts, docs, digests


def test_signed_grant_verifies_and_is_time_bounded():
    grant = make_grant()
    verified = _verify_grant(
        grant, repo=REPO, target_sha=SHA, now=NOW,
        public_key_encoded=raw_public(GRANT_KEY),
    )
    assert verified["grant_id"] == grant["grant_id"]
    assert verified["run_ids"]["readiness"] == 41008
    assert verified["_until"] == NOW + timedelta(minutes=5)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("demo_trading_allowed", False, "G13_ATTESTOR_GRANT_DEMO_NOT_GRANTED"),
        ("live_trading_allowed", True, "G13_ATTESTOR_GRANT_LIVE_MUST_REMAIN_DISABLED"),
        ("scope", "UNLIMITED", "G13_ATTESTOR_GRANT_SCOPE_INVALID"),
        ("candidate_id", 0, "G13_ATTESTOR_GRANT_CANDIDATE_ID_INVALID"),
    ],
)
def test_grant_policy_and_identity_fail_closed(field, value, reason):
    grant = make_grant(**{field: value})
    with pytest.raises(AttestorError, match=reason):
        _verify_grant(grant, repo=REPO, target_sha=SHA, now=NOW, public_key_encoded=raw_public(GRANT_KEY))


def test_tampered_grant_signature_is_rejected():
    grant = make_grant()
    grant["signal_id"] = "signal-tampered-after-signing"
    with pytest.raises(AttestorError, match="G13_ATTESTOR_GRANT_SIGNATURE_VERIFICATION_FAILED"):
        _verify_grant(grant, repo=REPO, target_sha=SHA, now=NOW, public_key_encoded=raw_public(GRANT_KEY))


def test_grant_must_bind_current_commit_and_full_evidence_chain():
    grant = make_grant(commit_sha="a" * 40)
    with pytest.raises(AttestorError, match="G13_ATTESTOR_GRANT_REPOSITORY_OR_SHA_MISMATCH"):
        _verify_grant(grant, repo=REPO, target_sha=SHA, now=NOW, public_key_encoded=raw_public(GRANT_KEY))
    duplicate_ids = make_grant(run_ids={key: 1 for key in RUN_ID_FIELDS})
    with pytest.raises(AttestorError, match="G13_ATTESTOR_GRANT_RUN_IDS_NOT_UNIQUE"):
        _verify_grant(duplicate_ids, repo=REPO, target_sha=SHA, now=NOW, public_key_encoded=raw_public(GRANT_KEY))
    distinct_ids = make_grant(run_ids={key: 42000 + i for i, key in enumerate(RUN_ID_FIELDS)})
    assert _verify_grant(distinct_ids, repo=REPO, target_sha=SHA, now=NOW, public_key_encoded=raw_public(GRANT_KEY))["run_ids"]["readiness"] > 0


def test_successful_research_chain_still_requires_explicit_source_grant_and_is_candidate_scoped():
    grant, runs, artifacts, docs, digests = fixture_chain()
    payload, audit = _validate_evidence(
        repo=REPO, target_sha=SHA, grant=grant, runs=runs,
        artifacts=artifacts, docs=docs, digests=digests,
    )
    assert payload["demo_trading_allowed"] is True
    assert payload["live_trading_allowed"] is False
    assert payload["promoted_candidate_ids"] == [2]
    assert payload["source_grant_candidate_id"] == 2
    assert payload["source_grant_signal_id"] == grant["signal_id"]
    assert payload["source_grant_trade_id"] == grant["trade_id"]
    assert payload["source_grant_authorization_id"] == grant["authorization_id"]
    assert payload["source_grant_reservation_id"] == grant["reservation_id"]
    assert payload["run_ids"] == grant["run_ids"]
    assert audit["orders_submitted"] is False
    assert audit["live_trading_allowed"] is False
    assert audit["evidence_bundle_sha256"] == payload["evidence_bundle_sha256"]


def test_promotion_or_preflight_cannot_self_grant_demo_permission():
    grant, runs, artifacts, docs, digests = fixture_chain()
    docs["promotion"]["decision_policy"]["demo_trading_allowed"] = True
    with pytest.raises(AttestorError, match="G13_ATTESTOR_PROMOTION_POLICY_INVALID"):
        _validate_evidence(repo=REPO, target_sha=SHA, grant=grant, runs=runs,
                           artifacts=artifacts, docs=docs, digests=digests)
    grant, runs, artifacts, docs, digests = fixture_chain()
    docs["package_preflight"]["demo_trading_allowed_by_source"] = True
    with pytest.raises(AttestorError, match="G13_ATTESTOR_PREFLIGHT_PERMISSION_MUST_BE_SOURCE_DENIED"):
        _validate_evidence(repo=REPO, target_sha=SHA, grant=grant, runs=runs,
                           artifacts=artifacts, docs=docs, digests=digests)


def test_wrong_commit_artifact_or_gate_is_rejected():
    grant, runs, artifacts, docs, digests = fixture_chain()
    docs["parity"]["passed_count"] = 0
    with pytest.raises(AttestorError, match="G13_ATTESTOR_PARITY_CANDIDATE_COVERAGE_INVALID"):
        _validate_evidence(repo=REPO, target_sha=SHA, grant=grant, runs=runs,
                           artifacts=artifacts, docs=docs, digests=digests)
    grant, runs, artifacts, docs, digests = fixture_chain()
    artifacts["robustness"] = dict(artifacts["robustness"], digest="sha256:" + "0" * 64)
    docs["promotion"]["source_artifacts"]["robustness"]["artifact_digest"] = artifacts["robustness"]["digest"]
    with pytest.raises(AttestorError, match="G13_ATTESTOR_PROMOTION_SOURCE_DIGEST_MISMATCH"):
        _validate_evidence(repo=REPO, target_sha=SHA, grant=grant, runs=runs,
                           artifacts=artifacts, docs=docs, digests=digests)


def test_attestation_signature_verifies_and_expiry_never_exceeds_grant():
    payload = {"schema": "forexai.g13.promotion_evidence.v1", "demo_trading_allowed": True, "live_trading_allowed": False}
    signed = build_signed_attestation(payload, private_key=ATTESTOR_KEY, now=NOW, grant_expiry=NOW + timedelta(seconds=45))
    unsigned = {key: value for key, value in signed.items() if key != "signature"}
    signature = base64.b64decode(signed["signature"]["signature"], validate=True)
    ATTESTOR_KEY.public_key().verify(signature, canonical_json(unsigned))
    assert signed["key_id"] == ATTESTOR_KEY_ID
    assert datetime.fromisoformat(signed["valid_until_utc"]) == NOW + timedelta(seconds=45)


def test_artifact_document_selection_rejects_traversal_and_duplicate_basenames():
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../g13-readiness.json", "{}")
    with pytest.raises(AttestorError, match="G13_ATTESTOR_ARTIFACT_PATH_INVALID"):
        _artifact_documents(archive.getvalue(), {"g13-readiness.json"})

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("a/g13-readiness.json", "{}")
        zf.writestr("b/g13-readiness.json", "{}")
    with pytest.raises(AttestorError, match="G13_ATTESTOR_ARTIFACT_DOCUMENT_CARDINALITY"):
        _artifact_documents(archive.getvalue(), {"g13-readiness.json"})


def test_run_attestor_requires_exact_successful_source_job_and_artifact(monkeypatch):
    role = "validation"
    run_id = 41001
    spec = REQUIRED_RUNS[role]
    artifact_id = 51001
    artifact_name = spec["artifact_name"]
    artifact_digest = "sha256:" + hashlib.sha256(b"test-artifact").hexdigest()
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(spec["document"], json.dumps({"schema": "forexai.g13.validation_m15.v1"}))

    api_payloads = {
        f"actions/runs/{run_id}": {
            "id": run_id,
            "name": spec["name"],
            "path": spec["path"],
            "workflow_id": spec["workflow_id"],
            "head_branch": "main",
            "head_sha": SHA,
            "status": "completed",
            "conclusion": "success",
            "repository": {"full_name": REPO},
        },
        f"actions/runs/{run_id}/jobs?per_page=100": {
            "jobs": [{
                "id": 62001,
                "run_id": run_id,
                "head_sha": SHA,
                "name": spec["job_name"],
                "status": "completed",
                "conclusion": "success",
            }]
        },
        f"actions/runs/{run_id}/artifacts?per_page=100": {
            "artifacts": [{
                "id": artifact_id,
                "name": artifact_name,
                "expired": False,
                "digest": artifact_digest,
            }]
        },
    }

    def fake_api_json(repo, path, token):
        assert repo == REPO
        assert token == "read-only-test-token"
        return api_payloads[path]

    monkeypatch.setattr(attestor_module, "_api_json", fake_api_json)
    monkeypatch.setattr(
        attestor_module,
        "_download_verified_artifact",
        lambda repo, actual_run_id, artifact, token: (archive.getvalue(), artifact_digest),
    )

    run, artifact, docs, digest = attestor_module._fetch_run_and_artifact(
        REPO, role, run_id, SHA, "read-only-test-token"
    )
    assert run["_attestor_success_job_id"] == 62001
    assert artifact["id"] == artifact_id
    assert docs[spec["document"]]["schema"] == "forexai.g13.validation_m15.v1"
    assert digest == artifact_digest

    api_payloads[f"actions/runs/{run_id}/jobs?per_page=100"]["jobs"][0]["conclusion"] = "failure"
    with pytest.raises(AttestorError, match="G13_ATTESTOR_EXACT_SHA_JOB_NOT_SUCCESS:validation"):
        attestor_module._fetch_run_and_artifact(
            REPO, role, run_id, SHA, "read-only-test-token"
        )
