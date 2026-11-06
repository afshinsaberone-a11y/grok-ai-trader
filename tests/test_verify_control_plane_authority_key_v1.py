from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.create_control_plane_authority_key_v1 import ROLES, generate_authority_keypair
from tools.verify_control_plane_authority_key_v1 import verify_authority_keypair


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _generate(tmp_path: Path, role: str = "provider-admission") -> tuple[dict, Path, Path, str]:
    passphrase = "test-only-verify-passphrase-2026"
    output = tmp_path / ("key-" + role)
    result = generate_authority_keypair(
        output,
        role,
        passphrase,
        repository_root=REPOSITORY_ROOT,
    )
    manifest_path = Path(result["public_manifest_path"])
    private_path = Path(result["private_key_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest, private_path, manifest_path, passphrase


def _expected_status():
    return (
        "KEYPAIR_AND_PROCESS_ANCHOR_PASS_WINDOWS_ACL_REVIEW_REQUIRED"
        if os.name == "nt"
        else "PASS_KEYPAIR_AND_PROCESS_ANCHOR"
    )


def test_verifies_existing_encrypted_keypair_and_matching_process_anchor(tmp_path: Path):
    manifest, private_path, manifest_path, passphrase = _generate(tmp_path)
    environment = {
        ROLES["provider-admission"]["environment_variable"]: manifest["public_key_base64"]
    }

    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=passphrase,
        environ=environment,
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == _expected_status()
    assert report["reason"] in ("PASS", "WINDOWS_ACL_REVIEW_REQUIRED")
    assert report["keypair_matches_public_source"] is True
    assert report["process_anchor_status"] == "MATCH"
    assert report["process_anchor_matches_private_key"] is True
    assert report["private_key_fingerprint_sha256"] == manifest["public_key_sha256"]
    assert report["public_source_fingerprint_sha256"] == manifest["public_key_sha256"]
    assert report["private_key_material_printed"] is False
    assert report["passphrase_printed"] is False
    assert report["public_key_value_printed"] is False
    assert report["demo_trading_authorized"] is False
    assert report["live_trading_allowed"] is False
    assert report["orders_submitted"] is False
    assert report["grant_issued"] is False
    serialized = json.dumps(report)
    assert manifest["public_key_base64"] not in serialized
    assert passphrase not in serialized


def test_keypair_match_does_not_hide_process_anchor_mismatch(tmp_path: Path):
    manifest, private_path, manifest_path, passphrase = _generate(tmp_path)
    env_name = ROLES["provider-admission"]["environment_variable"]
    wrong_anchor = base64.b64encode(b"x" * 32).decode("ascii")
    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=passphrase,
        environ={env_name: wrong_anchor},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PROCESS_ANCHOR_MISMATCH"
    assert report["keypair_matches_public_source"] is True
    assert report["process_anchor_status"] == "MISMATCH"
    assert report["process_anchor_matches_private_key"] is False
    assert wrong_anchor not in json.dumps(report)


def test_keypair_proof_is_not_confused_with_missing_active_anchor(tmp_path: Path):
    _manifest, private_path, manifest_path, passphrase = _generate(tmp_path)
    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=passphrase,
        environ={},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "KEYPAIR_PROOF_PASS_PROCESS_ANCHOR_NOT_CONFIGURED"
    assert report["reason"] == "PROCESS_ANCHOR_NOT_CONFIGURED"
    assert report["keypair_matches_public_source"] is True
    assert report["process_anchor_matches_private_key"] is False
    assert report["demo_trading_authorized"] is False


def test_rejects_private_key_that_does_not_match_public_key_file(tmp_path: Path):
    _manifest, private_path, _manifest_path, passphrase = _generate(tmp_path)
    other = Ed25519PrivateKey.generate()
    other_public = other.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    public_file = tmp_path / "other-public-key.txt"
    public_file.write_text(base64.b64encode(other_public).decode("ascii") + "\n", encoding="utf-8")

    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        public_key_file=str(public_file),
        passphrase=passphrase,
        environ={},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PRIVATE_PUBLIC_KEYPAIR_MISMATCH"
    assert report["keypair_matches_public_source"] is False
    assert report["private_key_material_printed"] is False


def test_rejects_manifest_bound_to_another_role(tmp_path: Path):
    manifest, private_path, manifest_path, passphrase = _generate(tmp_path)
    manifest["role"] = "live-signal"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=passphrase,
        environ={},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PUBLIC_MANIFEST_ROLE_OR_SCHEMA_MISMATCH"


def test_rejects_unencrypted_private_key(tmp_path: Path):
    key = Ed25519PrivateKey.generate()
    private_path = tmp_path / "unencrypted.pem"
    private_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    try:
        private_path.chmod(0o600)
    except OSError:
        pass
    _manifest, _other_private, manifest_path, passphrase = _generate(tmp_path)

    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=passphrase,
        environ={},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PRIVATE_KEY_MUST_BE_ENCRYPTED_PKCS8"
    assert report["private_key_material_printed"] is False


def test_rejects_wrong_passphrase_without_disclosing_key_material(tmp_path: Path):
    manifest, private_path, manifest_path, _passphrase = _generate(tmp_path)
    wrong_passphrase = "deliberately-wrong-test-passphrase"
    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=wrong_passphrase,
        environ={},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PRIVATE_KEY_DECRYPTION_FAILED"
    assert manifest["public_key_base64"] not in json.dumps(report)
    assert wrong_passphrase not in json.dumps(report)


def test_rejects_private_key_inside_repository(tmp_path: Path):
    private_root = tmp_path / "repository"
    private_root.mkdir()
    private_path = private_root / "private-key.pem"
    key = Ed25519PrivateKey.generate()
    private_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"repository-test-passphrase"),
        )
    )
    try:
        private_path.chmod(0o600)
    except OSError:
        pass
    manifest, _external_private, manifest_path, _passphrase = _generate(tmp_path)

    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase="repository-test-passphrase",
        environ={ROLES["provider-admission"]["environment_variable"]: manifest["public_key_base64"]},
        repository_root=private_root,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PRIVATE_KEY_MUST_BE_OUTSIDE_REPOSITORY"
    assert report["private_key_material_printed"] is False


def test_rejects_manifest_with_unexpected_fields_without_echoing_them(tmp_path: Path):
    manifest, private_path, manifest_path, passphrase = _generate(tmp_path)
    secret_marker = "DO_NOT_PRINT_EXTRA_PRIVATE_MATERIAL"
    manifest["private_key"] = secret_marker
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=passphrase,
        environ={},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PUBLIC_MANIFEST_FIELDS_INVALID"
    assert secret_marker not in json.dumps(report)
    assert report["private_key_material_printed"] is False


def test_rejects_manifest_with_wrong_public_fingerprint(tmp_path: Path):
    manifest, private_path, manifest_path, passphrase = _generate(tmp_path)
    manifest["public_key_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = verify_authority_keypair(
        role="provider-admission",
        private_key_path=str(private_path),
        manifest_path=str(manifest_path),
        passphrase=passphrase,
        environ={},
        repository_root=REPOSITORY_ROOT,
    )

    assert report["status"] == "BLOCKED"
    assert report["reason"] == "PUBLIC_MANIFEST_FINGERPRINT_MISMATCH"
    assert report["keypair_matches_public_source"] is False
