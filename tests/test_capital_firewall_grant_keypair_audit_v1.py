from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.capital_firewall_grant_keypair_audit_v1 import (
    GrantKeyAuditError,
    audit_keypair,
)


PASSPHRASE = "correct-horse-battery-phrase-482"


def _repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir(exist_ok=True)
    return root


def _write_pair(directory: Path, *, key: Ed25519PrivateKey | None = None) -> tuple[Path, Path, bytes]:
    directory.mkdir(parents=True, exist_ok=True)
    private_key = key or Ed25519PrivateKey.generate()
    public_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(PASSPHRASE.encode("utf-8")),
    )
    private_path = directory / "capital-firewall-grant.pem"
    public_path = directory / "capital-firewall-grant-public.txt"
    private_path.write_bytes(private_pem)
    public_path.write_text(base64.b64encode(public_raw).decode("ascii") + "\n", encoding="ascii")
    return private_path, public_path, public_raw


def test_audit_accepts_encrypted_matching_ed25519_pair(tmp_path: Path) -> None:
    private_path, public_path, public_raw = _write_pair(tmp_path / "external-keys")
    report = audit_keypair(
        private_path,
        public_path,
        passphrase=PASSPHRASE,
        repository_root=_repo_root(tmp_path),
    )
    assert report["status"] == "PASS"
    assert report["private_key_encrypted"] is True
    assert report["private_public_match"] is True
    assert report["files_modified"] is False
    assert report["trust_anchor_activated"] is False
    assert report["registry_initialized"] is False
    assert report["grant_issued"] is False
    assert report["orders_submitted"] is False
    assert report["public_key_sha256"] == hashlib.sha256(public_raw).hexdigest()


def test_audit_rejects_wrong_passphrase(tmp_path: Path) -> None:
    private_path, public_path, _ = _write_pair(tmp_path / "external-keys")
    with pytest.raises(GrantKeyAuditError, match="PRIVATE_KEY_DECRYPTION_FAILED"):
        audit_keypair(
            private_path,
            public_path,
            passphrase="this-is-the-wrong-passphrase",
            repository_root=tmp_path / "repository",
        )


def test_audit_rejects_mismatched_public_key(tmp_path: Path) -> None:
    key_dir = tmp_path / "external-keys"
    private_path, public_path, _ = _write_pair(key_dir)
    other_key = Ed25519PrivateKey.generate()
    other_raw = other_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    public_path.write_text(base64.b64encode(other_raw).decode("ascii") + "\n", encoding="ascii")
    with pytest.raises(GrantKeyAuditError, match="PRIVATE_PUBLIC_KEY_MISMATCH"):
        audit_keypair(
            private_path,
            public_path,
            passphrase=PASSPHRASE,
            repository_root=tmp_path / "repository",
        )


def test_audit_rejects_unencrypted_private_key(tmp_path: Path) -> None:
    key_dir = tmp_path / "external-keys"
    private_path, public_path, _ = _write_pair(key_dir)
    key = Ed25519PrivateKey.generate()
    unencrypted_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    private_path.write_bytes(unencrypted_pem)
    with pytest.raises(GrantKeyAuditError, match="PRIVATE_KEY_MUST_BE_ENCRYPTED_PKCS8"):
        audit_keypair(
            private_path,
            public_path,
            passphrase=PASSPHRASE,
            repository_root=tmp_path / "repository",
        )


def test_audit_rejects_key_material_inside_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repository"
    private_path, public_path, _ = _write_pair(repo / "keys")
    with pytest.raises(GrantKeyAuditError, match="KEY_MATERIAL_INSIDE_REPOSITORY"):
        audit_keypair(
            private_path,
            public_path,
            passphrase=PASSPHRASE,
            repository_root=repo,
        )


def test_audit_rejects_noncanonical_public_key_encoding(tmp_path: Path) -> None:
    private_path, public_path, public_raw = _write_pair(tmp_path / "external-keys")
    # Change only unused base64 pad bits: it decodes to the same bytes but is noncanonical.
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    encoded = base64.b64encode(public_raw).decode("ascii")
    pad_index = alphabet.index(encoded[-2])
    noncanonical = encoded[:-2] + alphabet[pad_index | 1] + "="
    public_path.write_text(noncanonical + "\n", encoding="ascii")
    with pytest.raises(GrantKeyAuditError, match="PUBLIC_KEY_BASE64_NOT_CANONICAL"):
        audit_keypair(
            private_path,
            public_path,
            passphrase=PASSPHRASE,
            repository_root=tmp_path / "repository",
        )
