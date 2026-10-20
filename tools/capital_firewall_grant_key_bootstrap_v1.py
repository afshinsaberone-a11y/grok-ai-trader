"""Explicit, no-overwrite Ed25519 key bootstrap for the Capital Firewall Grant role.

This creates an encrypted PKCS#8 private key plus its raw-32-byte public anchor.
It does not configure trust anchors, initialize a registry, or authorize a Grant.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
from pathlib import Path
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.capital_firewall_grant_issuer_v1 import GRANT_KEY_ID


CONFIRMATION = "CREATE_CAPITAL_FIREWALL_GRANT_KEYPAIR"
MIN_PASSPHRASE_LENGTH = 20


class GrantKeyBootstrapError(RuntimeError):
    """Fail-closed validation or filesystem error while creating a keypair."""


def _resolve_new_outputs(
    private_key_path: str | Path,
    public_key_path: str | Path,
    *,
    repository_root: Path | None = None,
) -> tuple[Path, Path]:
    root = (repository_root or Path(__file__).resolve().parents[1]).resolve(strict=True)
    resolved: list[Path] = []
    for label, raw_value in (
        ("PRIVATE", private_key_path),
        ("PUBLIC", public_key_path),
    ):
        raw = Path(raw_value).expanduser()
        if not raw.is_absolute():
            raise GrantKeyBootstrapError(f"OUTPUT_PATH_NOT_ABSOLUTE:{label}")
        if raw.is_symlink():
            raise GrantKeyBootstrapError(f"OUTPUT_PATH_SYMLINK_FORBIDDEN:{label}")
        try:
            target = raw.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise GrantKeyBootstrapError(f"OUTPUT_PATH_RESOLUTION_FAILED:{label}") from exc
        if target.is_relative_to(root):
            raise GrantKeyBootstrapError(f"OUTPUT_PATH_INSIDE_REPOSITORY:{label}")
        if not target.parent.is_dir():
            raise GrantKeyBootstrapError(f"OUTPUT_PARENT_MISSING:{label}")
        if target.exists():
            raise GrantKeyBootstrapError(f"OUTPUT_ALREADY_EXISTS:{label}")
        resolved.append(target)
    if resolved[0] == resolved[1]:
        raise GrantKeyBootstrapError("PRIVATE_PUBLIC_OUTPUT_PATH_COLLISION")
    return resolved[0], resolved[1]


def create_keypair(
    private_key_path: str | Path,
    public_key_path: str | Path,
    *,
    confirmation: str,
    passphrase: str,
    repeated_passphrase: str,
    repository_root: Path | None = None,
) -> dict[str, str | bool]:
    """Create a new encrypted keypair without overwriting either output path."""
    if confirmation != CONFIRMATION:
        raise GrantKeyBootstrapError("CONFIRMATION_INVALID")
    private_path, public_path = _resolve_new_outputs(
        private_key_path,
        public_key_path,
        repository_root=repository_root,
    )
    if not isinstance(passphrase, str) or len(passphrase) < MIN_PASSPHRASE_LENGTH:
        raise GrantKeyBootstrapError("PASSPHRASE_TOO_SHORT")
    if passphrase != repeated_passphrase:
        raise GrantKeyBootstrapError("PASSPHRASE_MISMATCH")

    private_key = Ed25519PrivateKey.generate()
    public_raw = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    public_b64 = base64.b64encode(public_raw).decode("ascii")
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode("utf-8")),
    )
    public_text = public_b64 + "\n"

    created: list[Path] = []
    try:
        for path, data in ((private_path, private_pem), (public_path, public_text.encode("ascii"))):
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            fd = os.open(path, flags, 0o600)
            created.append(path)
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())

        # Re-read the encrypted key and written public file before reporting success.
        loaded = serialization.load_pem_private_key(
            private_path.read_bytes(),
            password=passphrase.encode("utf-8"),
        )
        if not isinstance(loaded, Ed25519PrivateKey):
            raise GrantKeyBootstrapError("CREATED_PRIVATE_KEY_TYPE_INVALID")
        derived = loaded.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        persisted_b64 = public_path.read_text(encoding="ascii").strip()
        if derived != public_raw or persisted_b64 != public_b64:
            raise GrantKeyBootstrapError("CREATED_KEYPAIR_ROUNDTRIP_MISMATCH")
    except Exception as exc:
        # Remove only outputs this invocation successfully created; never touch
        # pre-existing files. If cleanup fails, require manual inspection.
        cleanup_failed = False
        for path in reversed(created):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                cleanup_failed = True
        if isinstance(exc, GrantKeyBootstrapError):
            raise
        reason = "OUTPUT_WRITE_OR_KEYPAIR_VERIFICATION_FAILED"
        if cleanup_failed:
            reason += "_MANUAL_CLEANUP_REQUIRED"
        raise GrantKeyBootstrapError(reason) from exc

    fingerprint = hashlib.sha256(public_raw).hexdigest()
    return {
        "status": "PASS",
        "key_id": GRANT_KEY_ID,
        "public_key_sha256": fingerprint,
        "private_key_encrypted": True,
        "keypair_verified": True,
        "trust_anchor_activated": False,
        "registry_initialized": False,
        "grant_issued": False,
        "orders_submitted": False,
        "live_trading_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-key-out", required=True)
    parser.add_argument("--public-key-out", required=True)
    args = parser.parse_args(argv)

    try:
        if not sys.stdin.isatty():
            raise GrantKeyBootstrapError("INTERACTIVE_TTY_REQUIRED")
        private_path, public_path = _resolve_new_outputs(
            args.private_key_out,
            args.public_key_out,
        )
        print("This creates only the Grant keypair. It does not activate the trust anchor or issue a Grant.")
        typed = input(f"Type {CONFIRMATION} to continue: ").strip()
        if typed != CONFIRMATION:
            raise GrantKeyBootstrapError("CONFIRMATION_INVALID")
        from getpass import getpass

        first = getpass("New Grant private-key passphrase (20+ characters): ")
        second = getpass("Repeat Grant private-key passphrase: ")
        result = create_keypair(
            private_path,
            public_path,
            confirmation=typed,
            passphrase=first,
            repeated_passphrase=second,
        )
    except GrantKeyBootstrapError as exc:
        print(f"CAPITAL_FIREWALL_GRANT_KEY_BOOTSTRAP=BLOCKED reason={exc}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("CAPITAL_FIREWALL_GRANT_KEY_BOOTSTRAP=BLOCKED reason=OPERATOR_CANCELLED", file=sys.stderr)
        return 2
    except Exception:
        print("CAPITAL_FIREWALL_GRANT_KEY_BOOTSTRAP=BLOCKED reason=UNEXPECTED_FAILURE_MANUAL_REVIEW_REQUIRED", file=sys.stderr)
        return 2

    print(f"CAPITAL_FIREWALL_GRANT_KEY_BOOTSTRAP={result['status']}")
    print(f"GRANT_KEY_ID={result['key_id']}")
    print(f"GRANT_PUBLIC_KEY_SHA256={result['public_key_sha256']}")
    print("PRIVATE_KEY_ENCRYPTED=1")
    print("KEYPAIR_ROUNDTRIP_VERIFIED=1")
    print("TRUST_ANCHOR_ACTIVATED=0")
    print("REGISTRY_INITIALIZED=0")
    print("GRANT_ISSUED=0")
    print("ORDERS_SUBMITTED=0")
    print("LIVE_TRADING_ALLOWED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

