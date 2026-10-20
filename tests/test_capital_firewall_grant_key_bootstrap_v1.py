from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.capital_firewall_grant_issuer_v1 import GRANT_KEY_ID
from tools.capital_firewall_grant_key_bootstrap_v1 import (
    CONFIRMATION,
    GrantKeyBootstrapError,
    create_keypair,
)


PASSPHRASE = "test-only-passphrase-at-least-20-chars"


def test_generates_encrypted_pkcs8_key_and_canonical_public_anchor(tmp_path: Path):
    private_path = tmp_path / "grant-private.pem"
    public_path = tmp_path / "grant-public.txt"

    result = create_keypair(
        private_path,
        public_path,
        confirmation=CONFIRMATION,
        passphrase=PASSPHRASE,
        repeated_passphrase=PASSPHRASE,
    )

    loaded = serialization.load_pem_private_key(
        private_path.read_bytes(), password=PASSPHRASE.encode("utf-8")
    )
    assert isinstance(loaded, Ed25519PrivateKey)
    public_raw = loaded.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    encoded_public = public_path.read_text(encoding="ascii").strip()
    assert base64.b64decode(encoded_public, validate=True) == public_raw
    assert base64.b64encode(public_raw).decode("ascii") == encoded_public
    assert result["status"] == "PASS"
    assert result["key_id"] == GRANT_KEY_ID
    assert result["public_key_sha256"] == hashlib.sha256(public_raw).hexdigest()
    assert result["private_key_encrypted"] is True
    assert result["keypair_verified"] is True
    assert result["trust_anchor_activated"] is False
    assert result["registry_initialized"] is False
    assert result["grant_issued"] is False
    assert result["orders_submitted"] is False
    assert result["live_trading_allowed"] is False
    with pytest.raises((TypeError, ValueError, InvalidKey)):
        serialization.load_pem_private_key(
            private_path.read_bytes(), password=b"wrong-passphrase-for-test"
        )


def test_key_bootstrap_requires_exact_confirmation(tmp_path: Path):
    private_path = tmp_path / "grant-private.pem"
    public_path = tmp_path / "grant-public.txt"
    with pytest.raises(GrantKeyBootstrapError, match="CONFIRMATION_INVALID"):
        create_keypair(
            private_path,
            public_path,
            confirmation="yes",
            passphrase=PASSPHRASE,
            repeated_passphrase=PASSPHRASE,
        )
    assert not private_path.exists()
    assert not public_path.exists()


def test_key_bootstrap_requires_long_matching_passphrase(tmp_path: Path):
    private_path = tmp_path / "grant-private.pem"
    public_path = tmp_path / "grant-public.txt"
    with pytest.raises(GrantKeyBootstrapError, match="PASSPHRASE_TOO_SHORT"):
        create_keypair(
            private_path,
            public_path,
            confirmation=CONFIRMATION,
            passphrase="short",
            repeated_passphrase="short",
        )
    with pytest.raises(GrantKeyBootstrapError, match="PASSPHRASE_MISMATCH"):
        create_keypair(
            private_path,
            public_path,
            confirmation=CONFIRMATION,
            passphrase=PASSPHRASE,
            repeated_passphrase="a-different-long-passphrase",
        )
    assert not private_path.exists()
    assert not public_path.exists()


def test_key_bootstrap_refuses_overwrite_and_preserves_existing_file(tmp_path: Path):
    private_path = tmp_path / "grant-private.pem"
    public_path = tmp_path / "grant-public.txt"
    private_path.write_text("existing private placeholder", encoding="utf-8")
    with pytest.raises(GrantKeyBootstrapError, match="OUTPUT_ALREADY_EXISTS:PRIVATE"):
        create_keypair(
            private_path,
            public_path,
            confirmation=CONFIRMATION,
            passphrase=PASSPHRASE,
            repeated_passphrase=PASSPHRASE,
        )
    assert private_path.read_text(encoding="utf-8") == "existing private placeholder"
    assert not public_path.exists()


def test_key_bootstrap_rejects_repository_paths(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[1]
    private_path = repo_root / ".capital-firewall-test-private-key.pem"
    public_path = tmp_path / "grant-public.txt"
    with pytest.raises(GrantKeyBootstrapError, match="OUTPUT_PATH_INSIDE_REPOSITORY:PRIVATE"):
        create_keypair(
            private_path,
            public_path,
            confirmation=CONFIRMATION,
            passphrase=PASSPHRASE,
            repeated_passphrase=PASSPHRASE,
            repository_root=repo_root,
        )
    assert not private_path.exists()
    assert not public_path.exists()


def test_key_bootstrap_rejects_colliding_paths(tmp_path: Path):
    target = tmp_path / "one-file.pem"
    with pytest.raises(GrantKeyBootstrapError, match="PRIVATE_PUBLIC_OUTPUT_PATH_COLLISION"):
        create_keypair(
            target,
            target,
            confirmation=CONFIRMATION,
            passphrase=PASSPHRASE,
            repeated_passphrase=PASSPHRASE,
        )
    assert not target.exists()


def test_key_bootstrap_requires_existing_parent_directories(tmp_path: Path):
    private_path = tmp_path / "missing" / "grant-private.pem"
    public_path = tmp_path / "grant-public.txt"
    with pytest.raises(GrantKeyBootstrapError, match="OUTPUT_PARENT_MISSING:PRIVATE"):
        create_keypair(
            private_path,
            public_path,
            confirmation=CONFIRMATION,
            passphrase=PASSPHRASE,
            repeated_passphrase=PASSPHRASE,
        )
    assert not private_path.parent.exists()
    assert not public_path.exists()

