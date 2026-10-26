#!/usr/bin/env python3
"""Verify an existing authority keypair without revealing private material.

Read-only: this utility never generates, rotates, copies, or activates a key.
It requires an encrypted Ed25519 PKCS#8 private key and either its public-only
manifest or a separate canonical-base64 public-key file. It checks the role
mapping, keypair fingerprint, permissions where portable, and the current
process-scoped trust anchor. A result is proof of keypair consistency only;
it is not proof of independent administration or trading authority.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import getpass
import json
import os
from pathlib import Path
import stat
from typing import Mapping, Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.create_control_plane_authority_key_v1 import MANIFEST_SCHEMA, ROLES


SCHEMA = "forexai.authority_key_proof.v1"


def _decode_public_key(value: str) -> bytes | None:
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(raw) != 32 or base64.b64encode(raw).decode("ascii") != value:
        return None
    return raw


def _safe_path(raw_path: str, *, private: bool, repository_root: Path) -> tuple[Path | None, str]:
    supplied = Path(raw_path)
    if not supplied.is_absolute():
        return None, "PATH_MUST_BE_ABSOLUTE"
    if supplied.is_symlink():
        return None, "SYMLINK_FORBIDDEN"
    try:
        resolved = supplied.resolve(strict=True)
    except (OSError, RuntimeError):
        return None, "PATH_NOT_FOUND_OR_INACCESSIBLE"
    if not resolved.is_file():
        return None, "PATH_NOT_REGULAR_FILE"
    if private:
        try:
            resolved.relative_to(repository_root.resolve(strict=True))
        except ValueError:
            pass
        else:
            return None, "PRIVATE_KEY_MUST_BE_OUTSIDE_REPOSITORY"
        if os.name != "nt":
            try:
                mode = stat.S_IMODE(resolved.stat().st_mode)
            except OSError:
                return None, "PRIVATE_KEY_PERMISSION_CHECK_FAILED"
            if mode & 0o077:
                return None, "PRIVATE_KEY_PERMISSIONS_TOO_OPEN"
    return resolved, "PASS"


def _expected_public(
    role: str,
    manifest_path: str,
    public_key_file: str,
    repository_root: Path,
) -> tuple[bytes | None, str, str]:
    if bool(manifest_path) == bool(public_key_file):
        return None, "PUBLIC_SOURCE_ARGUMENTS_INVALID", ""
    selected = manifest_path or public_key_file
    path, path_status = _safe_path(selected, private=False, repository_root=repository_root)
    if path is None:
        return None, path_status, ""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, "PUBLIC_SOURCE_READ_FAILED", ""

    if manifest_path:
        try:
            document = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None, "PUBLIC_MANIFEST_INVALID_JSON", ""
        config = ROLES[role]
        required = {
            "schema": MANIFEST_SCHEMA,
            "role": role,
            "algorithm": "Ed25519",
            "key_id": config["key_id"],
            "environment_variable": config["environment_variable"],
            "public_key_encoding": "base64-raw-32-byte",
            "private_key_encrypted": True,
            "private_key_in_manifest": False,
        }
        if not isinstance(document, dict) or any(document.get(key) != value for key, value in required.items()):
            return None, "PUBLIC_MANIFEST_ROLE_OR_SCHEMA_MISMATCH", ""
        value = document.get("public_key_base64")
        fingerprint = document.get("public_key_sha256")
        if not isinstance(value, str) or not isinstance(fingerprint, str):
            return None, "PUBLIC_MANIFEST_KEY_FIELDS_INVALID", ""
        raw = _decode_public_key(value)
        if raw is None:
            return None, "PUBLIC_MANIFEST_KEY_INVALID", ""
        if hashlib.sha256(raw).hexdigest() != fingerprint:
            return None, "PUBLIC_MANIFEST_FINGERPRINT_MISMATCH", ""
        return raw, "PASS", "manifest"
    raw = _decode_public_key(text.strip())
    if raw is None:
        return None, "PUBLIC_KEY_FILE_INVALID", ""
    return raw, "PASS", "public-key-file"


def verify_authority_keypair(
    *,
    role: str,
    private_key_path: str,
    manifest_path: str = "",
    public_key_file: str = "",
    passphrase: str,
    environ: Mapping[str, str] | None = None,
    repository_root: Path | None = None,
) -> dict[str, Any]:
    """Return a redacted proof report. Never print or return key/passphrase values."""
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "BLOCKED",
        "role": role,
        "key_id": ROLES.get(role, {}).get("key_id"),
        "environment_variable": ROLES.get(role, {}).get("environment_variable"),
        "private_key_encrypted": False,
        "private_key_material_printed": False,
        "passphrase_printed": False,
        "public_key_value_printed": False,
        "private_key_fingerprint_sha256": None,
        "public_source_fingerprint_sha256": None,
        "keypair_matches_public_source": False,
        "process_anchor_status": "NOT_CHECKED",
        "process_anchor_matches_private_key": False,
        "windows_acl_review_required": os.name == "nt",
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "orders_submitted": False,
        "grant_issued": False,
    }
    if role not in ROLES:
        report["reason"] = "ROLE_INVALID"
        return report

    root = repository_root or Path(__file__).resolve().parents[1]
    private_path, private_status = _safe_path(
        private_key_path, private=True, repository_root=root
    )
    if private_path is None:
        report["reason"] = private_status
        return report

    try:
        with private_path.open("rb") as stream:
            header = stream.readline(256).strip()
            if header != b"-----BEGIN ENCRYPTED PRIVATE KEY-----":
                report["reason"] = "PRIVATE_KEY_MUST_BE_ENCRYPTED_PKCS8"
                return report
            stream.seek(0)
            private_pem = stream.read()
        report["private_key_encrypted"] = True
        private_key = serialization.load_pem_private_key(
            private_pem, password=passphrase.encode("utf-8")
        )
        del private_pem
    except (OSError, ValueError, TypeError):
        report["reason"] = "PRIVATE_KEY_DECRYPTION_FAILED"
        return report

    if not isinstance(private_key, Ed25519PrivateKey):
        report["reason"] = "PRIVATE_KEY_NOT_ED25519"
        return report

    derived_public = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    derived_fingerprint = hashlib.sha256(derived_public).hexdigest()
    report["private_key_fingerprint_sha256"] = derived_fingerprint

    public_raw, source_status, source_kind = _expected_public(
        role, manifest_path, public_key_file, root
    )
    report["public_source"] = source_kind or None
    if public_raw is None:
        report["reason"] = source_status
        return report
    report["public_source_fingerprint_sha256"] = hashlib.sha256(public_raw).hexdigest()
    if derived_public != public_raw:
        report["reason"] = "PRIVATE_PUBLIC_KEYPAIR_MISMATCH"
        return report
    report["keypair_matches_public_source"] = True

    env = os.environ if environ is None else environ
    env_name = ROLES[role]["environment_variable"]
    anchor_text = env.get(env_name, "").strip()
    if not anchor_text:
        report["process_anchor_status"] = "NOT_CONFIGURED"
        report["status"] = "KEYPAIR_PROOF_PASS_PROCESS_ANCHOR_NOT_CONFIGURED"
        report["reason"] = "PROCESS_ANCHOR_NOT_CONFIGURED"
        return report
    anchor_raw = _decode_public_key(anchor_text)
    if anchor_raw is None:
        report["process_anchor_status"] = "INVALID_BASE64_OR_LENGTH"
        report["reason"] = "PROCESS_ANCHOR_INVALID"
        return report
    if anchor_raw != derived_public:
        report["process_anchor_status"] = "MISMATCH"
        report["reason"] = "PROCESS_ANCHOR_MISMATCH"
        return report

    report["process_anchor_status"] = "MATCH"
    report["process_anchor_matches_private_key"] = True
    if os.name == "nt":
        report["status"] = "KEYPAIR_AND_PROCESS_ANCHOR_PASS_WINDOWS_ACL_REVIEW_REQUIRED"
        report["reason"] = "WINDOWS_ACL_REVIEW_REQUIRED"
    else:
        report["status"] = "PASS_KEYPAIR_AND_PROCESS_ANCHOR"
        report["reason"] = "PASS"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=sorted(ROLES), required=True)
    parser.add_argument("--private-key", required=True, help="Absolute path to encrypted PKCS#8 private key")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", help="Absolute path to the role-specific public-key.json manifest")
    source.add_argument("--public-key-file", help="Absolute path to a canonical base64 raw Ed25519 public-key file")
    args = parser.parse_args(argv)
    passphrase = getpass.getpass("Existing private-key passphrase (not echoed): ")
    report = verify_authority_keypair(
        role=args.role,
        private_key_path=args.private_key,
        manifest_path=args.manifest or "",
        public_key_file=args.public_key_file or "",
        passphrase=passphrase,
    )
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] == "PASS_KEYPAIR_AND_PROCESS_ANCHOR" else 2


if __name__ == "__main__":
    sys.exit(main())
