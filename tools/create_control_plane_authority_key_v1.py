#!/usr/bin/env python3
"""Create ONE encrypted Ed25519 authority keypair in a local, protected directory.

This creates key material only. It does not provision an authority service, prove
independence, issue attestations, configure Provider trust, or authorize trading.
Run it on the dedicated host owned by the role's actual signing authority.
"""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


MANIFEST_SCHEMA = "forexai.authority_key_manifest.v1"
MIN_PASSPHRASE_LENGTH = 16

ROLES: dict[str, dict[str, str]] = {
    "provider-admission": {
        "key_id": "forexai-demo-admission-provider-v1",
        "environment_variable": "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY",
    },
    "promotion-attestor": {
        "key_id": "forexai-g13-evidence-attestor-v1",
        "environment_variable": "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY",
    },
    "live-signal": {
        "key_id": "forexai-live-signal-source-v1",
        "environment_variable": "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY",
    },
    "risk-reservation": {
        "key_id": "forexai-demo-risk-engine-v1",
        "environment_variable": "FOREXAI_PROVIDER_RISK_PUBLIC_KEY",
    },
    "operator-approval": {
        "key_id": "forexai-demo-operator-approval-v1",
        "environment_variable": "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY",
    },
    "capital-firewall-grant": {
        "key_id": "forexai-capital-firewall-grant-v1",
        "environment_variable": "FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY",
    },
}


class AuthorityKeyGenerationError(RuntimeError):
    """A safe, non-secret error code for local authority key provisioning."""


def _normalized_new_directory(output_dir: str | Path, repository_root: str | Path) -> Path:
    requested = Path(output_dir)
    if not requested.is_absolute():
        raise AuthorityKeyGenerationError("OUTPUT_DIR_MUST_BE_ABSOLUTE")
    if requested.name in ("", ".", ".."):
        raise AuthorityKeyGenerationError("OUTPUT_DIR_LEAF_INVALID")
    if requested.exists() or requested.is_symlink():
        raise AuthorityKeyGenerationError("OUTPUT_DIR_ALREADY_EXISTS")
    if not requested.parent.exists() or not requested.parent.is_dir():
        raise AuthorityKeyGenerationError("OUTPUT_DIR_PARENT_MISSING")

    target = requested.parent.resolve(strict=True) / requested.name
    repository = Path(repository_root).resolve(strict=True)
    try:
        target.relative_to(repository)
    except ValueError:
        pass
    else:
        raise AuthorityKeyGenerationError("OUTPUT_DIR_MUST_BE_OUTSIDE_REPOSITORY")
    return target


def _secure_private_directory(directory: Path) -> None:
    """Remove inherited access on Windows; grant only the current SID and SYSTEM."""
    if os.name == "nt":
        try:
            identity = subprocess.run(
                ["whoami", "/user", "/fo", "csv", "/nh"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            rows = list(csv.reader(identity.stdout.splitlines()))
            sid = rows[0][-1].strip() if rows and rows[0] else ""
            if not re.fullmatch(r"S-1-\d+(?:-\d+)+", sid):
                raise AuthorityKeyGenerationError("CURRENT_WINDOWS_SID_UNAVAILABLE")
            acl = subprocess.run(
                [
                    "icacls",
                    str(directory),
                    "/inheritance:r",
                    "/grant:r",
                    f"*{sid}:(OI)(CI)F",
                    "/grant",
                    "*S-1-5-18:(OI)(CI)F",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
            if acl.returncode != 0:
                raise AuthorityKeyGenerationError("PRIVATE_DIRECTORY_ACL_SETUP_FAILED")

            # Newly created Windows directories can contain explicit default DACL
            # entries even after inherited ACEs are removed. Remove these entries
            # so the final discretionary ACL grants only the current SID and SYSTEM.
            # Windows administrators can still take ownership by OS privilege; this
            # removes broad direct grants and does not claim to defeat host admins.
            for extra_sid in ("*S-1-5-32-544", "*S-1-3-4"):
                removal = subprocess.run(
                    ["icacls", str(directory), "/remove", extra_sid],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if removal.returncode != 0:
                    raise AuthorityKeyGenerationError("PRIVATE_DIRECTORY_ACL_SETUP_FAILED")
        except subprocess.TimeoutExpired as exc:
            raise AuthorityKeyGenerationError("PRIVATE_DIRECTORY_ACL_SETUP_TIMEOUT") from exc
        except (OSError, subprocess.CalledProcessError) as exc:
            raise AuthorityKeyGenerationError("PRIVATE_DIRECTORY_ACL_SETUP_FAILED") from exc
    else:
        try:
            os.chmod(directory, 0o700)
        except OSError as exc:
            raise AuthorityKeyGenerationError("PRIVATE_DIRECTORY_PERMISSION_SETUP_FAILED") from exc


def _write_new_file(path: Path, data: bytes, private: bool) -> None:
    try:
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != "nt":
            os.chmod(path, 0o600 if private else 0o644)
    except OSError as exc:
        raise AuthorityKeyGenerationError("KEY_FILE_WRITE_FAILED") from exc


def generate_authority_keypair(
    output_dir: str | Path,
    role: str,
    passphrase: str,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Generate one encrypted PKCS#8 private key and a public-only manifest."""
    if role not in ROLES:
        raise AuthorityKeyGenerationError("ROLE_INVALID")
    if not isinstance(passphrase, str) or len(passphrase) < MIN_PASSPHRASE_LENGTH:
        raise AuthorityKeyGenerationError("PASSPHRASE_TOO_SHORT")

    repo_root = Path(repository_root) if repository_root is not None else Path(__file__).resolve().parents[1]
    target = _normalized_new_directory(output_dir, repo_root)
    private_path = target / "private-key.pem"
    manifest_path = target / "public-key.json"
    created_files: list[Path] = []
    created_directory = False

    try:
        target.mkdir(mode=0o700)
        created_directory = True
        _secure_private_directory(target)

        private_key = Ed25519PrivateKey.generate()
        public_raw = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        public_b64 = base64.b64encode(public_raw).decode("ascii")
        fingerprint = hashlib.sha256(public_raw).hexdigest()
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode("utf-8")),
        )

        # Verify the encrypted serialization before writing any key material.
        recovered = serialization.load_pem_private_key(private_pem, password=passphrase.encode("utf-8"))
        recovered_raw = recovered.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        if not isinstance(recovered, Ed25519PrivateKey) or recovered_raw != public_raw:
            raise AuthorityKeyGenerationError("GENERATED_KEYPAIR_SELF_CHECK_FAILED")

        _write_new_file(private_path, private_pem, private=True)
        created_files.append(private_path)

        role_config = ROLES[role]
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "role": role,
            "algorithm": "Ed25519",
            "key_id": role_config["key_id"],
            "environment_variable": role_config["environment_variable"],
            "public_key_encoding": "base64-raw-32-byte",
            "public_key_base64": public_b64,
            "public_key_sha256": fingerprint,
            "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "private_key_encrypted": True,
            "private_key_in_manifest": False,
        }
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        _write_new_file(manifest_path, manifest_bytes, private=False)
        created_files.append(manifest_path)

        return {
            "role": role,
            "key_id": role_config["key_id"],
            "environment_variable": role_config["environment_variable"],
            "public_key_sha256": fingerprint,
            "private_key_path": str(private_path),
            "public_manifest_path": str(manifest_path),
            "private_key_encrypted": True,
            "private_key_material_printed": False,
            "passphrase_printed": False,
        }
    except Exception:
        if created_directory:
            # The output directory was created exclusively by this invocation.
            # Never touch files if mkdir lost a race to another process.
            cleanup_candidates = [manifest_path, private_path, *reversed(created_files)]
            for path in cleanup_candidates:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                target.rmdir()
            except OSError:
                # Leave unexpected contents for operator review; never recurse-delete.
                pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=sorted(ROLES), required=True)
    parser.add_argument(
        "--output-dir",
        required=True,
        help="New absolute directory outside the repository; its parent must already exist",
    )
    args = parser.parse_args(argv)

    passphrase = getpass.getpass("New private-key encryption passphrase (minimum 16 characters): ")
    confirmation = getpass.getpass("Repeat passphrase: ")
    if passphrase != confirmation:
        print(json.dumps({"status": "BLOCKED", "reason": "PASSPHRASE_MISMATCH"}))
        return 2
    try:
        result = generate_authority_keypair(args.output_dir, args.role, passphrase)
    except AuthorityKeyGenerationError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc), "private_key_material_printed": False}))
        return 2
    except Exception:
        print(json.dumps({"status": "BLOCKED", "reason": "AUTHORITY_KEY_GENERATION_FAILED", "private_key_material_printed": False}))
        return 2

    print(json.dumps({"status": "KEYPAIR_CREATED_LOCAL_ONLY", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
