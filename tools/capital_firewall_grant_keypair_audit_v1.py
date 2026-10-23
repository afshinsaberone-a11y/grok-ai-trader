#!/usr/bin/env python3
"""Read-only audit for an existing encrypted Capital Firewall Grant keypair.

This command never creates, rewrites, exports, or activates key material. It
opens the encrypted PKCS#8 private key only to derive the public key in memory,
then compares it to the canonical base64 raw-Ed25519 public-key file.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import getpass
import hashlib
import hmac
import json
from pathlib import Path
import sys
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

GRANT_KEY_ID = "forexai-capital-firewall-grant-v1"
PRIVATE_KEY_HEADER = b"-----BEGIN ENCRYPTED PRIVATE KEY-----"


class GrantKeyAuditError(RuntimeError):
    """Safe, non-secret error emitted by the read-only keypair audit."""


def _existing_external_file(raw_path: str | Path, label: str, repo_root: Path) -> Path:
    raw = Path(raw_path).expanduser()
    if not raw.is_absolute():
        raise GrantKeyAuditError(f"PATH_NOT_ABSOLUTE:{label}")
    if raw.is_symlink():
        raise GrantKeyAuditError(f"PATH_SYMLINK_FORBIDDEN:{label}")
    try:
        resolved = raw.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GrantKeyAuditError(f"FILE_UNAVAILABLE:{label}") from exc
    if not resolved.is_file():
        raise GrantKeyAuditError(f"PATH_NOT_REGULAR_FILE:{label}")
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise GrantKeyAuditError(f"KEY_MATERIAL_INSIDE_REPOSITORY:{label}")
    return resolved


def audit_keypair(
    private_key_path: str | Path,
    public_key_path: str | Path,
    *,
    passphrase: str,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Verify an encrypted Ed25519 PKCS#8 key against a base64 raw public key."""
    root = Path(
        repository_root or Path(__file__).resolve().parents[1]
    ).resolve(strict=True)

    private_path = _existing_external_file(private_key_path, "PRIVATE", root)
    public_path = _existing_external_file(public_key_path, "PUBLIC", root)
    if private_path == public_path:
        raise GrantKeyAuditError("PRIVATE_PUBLIC_PATH_COLLISION")

    try:
        pem = private_path.read_bytes()
    except OSError as exc:
        raise GrantKeyAuditError("PRIVATE_KEY_UNAVAILABLE") from exc

    if not pem.lstrip().startswith(PRIVATE_KEY_HEADER):
        raise GrantKeyAuditError("PRIVATE_KEY_MUST_BE_ENCRYPTED_PKCS8")

    if not isinstance(passphrase, str) or not passphrase:
        raise GrantKeyAuditError("PASSPHRASE_REQUIRED")

    try:
        private_key = serialization.load_pem_private_key(
            pem,
            password=passphrase.encode("utf-8"),
        )
    except (ValueError, TypeError, OSError) as exc:
        raise GrantKeyAuditError("PRIVATE_KEY_DECRYPTION_FAILED") from exc

    if not isinstance(private_key, Ed25519PrivateKey):
        raise GrantKeyAuditError("PRIVATE_KEY_MUST_BE_ED25519")

    try:
        public_text = public_path.read_text(encoding="ascii").strip()
        public_raw = base64.b64decode(public_text, validate=True)
    except (OSError, UnicodeError, binascii.Error, ValueError) as exc:
        raise GrantKeyAuditError("PUBLIC_KEY_FILE_INVALID") from exc

    if len(public_raw) != 32:
        raise GrantKeyAuditError("PUBLIC_KEY_RAW_LENGTH_INVALID")
    if base64.b64encode(public_raw).decode("ascii") != public_text:
        raise GrantKeyAuditError("PUBLIC_KEY_BASE64_NOT_CANONICAL")

    derived_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    if not hmac.compare_digest(derived_raw, public_raw):
        raise GrantKeyAuditError("PRIVATE_PUBLIC_KEY_MISMATCH")

    fingerprint = hashlib.sha256(public_raw).hexdigest()
    return {
        "schema": "forexai.capital_firewall.grant_keypair_audit.v1",
        "status": "PASS",
        "key_id": GRANT_KEY_ID,
        "public_key_sha256": fingerprint,
        "private_key_encrypted": True,
        "private_public_match": True,
        "files_modified": False,
        "trust_anchor_activated": False,
        "registry_initialized": False,
        "grant_issued": False,
        "orders_submitted": False,
        "live_trading_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-key", required=True, help="External encrypted PKCS#8 PEM path")
    parser.add_argument("--public-key", required=True, help="External canonical base64 raw Ed25519 public-key path")
    args = parser.parse_args(argv)

    try:
        if not sys.stdin.isatty():
            raise GrantKeyAuditError("INTERACTIVE_TTY_REQUIRED")
        passphrase = getpass.getpass("Capital Firewall Grant private-key passphrase: ")
        report = audit_keypair(
            args.private_key,
            args.public_key,
            passphrase=passphrase,
        )
    except GrantKeyAuditError as exc:
        print(
            json.dumps({
                "schema": "forexai.capital_firewall.grant_keypair_audit.v1",
                "status": "BLOCKED",
                "reason": str(exc),
                "files_modified": False,
                "trust_anchor_activated": False,
                "grant_issued": False,
                "orders_submitted": False,
                "live_trading_allowed": False,
            }, sort_keys=True),
            file=sys.stdout,
        )
        return 2
    except (EOFError, KeyboardInterrupt):
        print(
            json.dumps({
                "schema": "forexai.capital_firewall.grant_keypair_audit.v1",
                "status": "BLOCKED",
                "reason": "OPERATOR_CANCELLED",
                "files_modified": False,
                "trust_anchor_activated": False,
                "grant_issued": False,
                "orders_submitted": False,
                "live_trading_allowed": False,
            }, sort_keys=True),
            file=sys.stdout,
        )
        return 2
    except Exception:
        # Avoid logging paths, PEM data, passphrase data, or arbitrary exception text.
        print(
            json.dumps({
                "schema": "forexai.capital_firewall.grant_keypair_audit.v1",
                "status": "BLOCKED",
                "reason": "UNEXPECTED_FAILURE",
                "files_modified": False,
                "trust_anchor_activated": False,
                "grant_issued": False,
                "orders_submitted": False,
                "live_trading_allowed": False,
            }, sort_keys=True),
            file=sys.stdout,
        )
        return 2

    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
