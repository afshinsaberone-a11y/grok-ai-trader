"""Read-only fail-closed preflight for a separately administered Capital Firewall host.

This script validates public trust-anchor shape, the locally mounted Grant keypair,
host-name separation from explicitly supplied provider/runner identities, and an
already-initialized read-only Grant registry. It never creates the registry, emits
a grant, alters configuration, or authorizes trading.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from contextlib import closing
import json
import os
from pathlib import Path
import platform
import sqlite3
import stat
from typing import Mapping
from urllib.parse import quote

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.capital_firewall_grant_issuer_v1 import (
    REGISTRY_SCHEMA,
    REGISTRY_TABLE_SQL,
    TRUST_ENVIRONMENTS,
)


SCHEMA = "forexai.capital_firewall_host_preflight.v1"
PASSPHRASE_ENVIRONMENT = "FOREXAI_CAPITAL_FIREWALL_GRANT_KEY_PASSPHRASE"
REGISTRY_COLUMNS = [
    "grant_id", "signal_id", "reservation_id", "authorization_id", "trade_id",
    "commit_sha", "candidate_id", "candidate_config_hash", "issued_at_utc", "grant_sha256",
]
EXPECTED_FORBIDDEN_HOST_COUNT = 2


def _decode_public_key(value: str) -> bytes | None:
    """Accept only canonical base64 encoding of a raw 32-byte Ed25519 key."""
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(raw) != 32 or base64.b64encode(raw).decode("ascii") != value:
        return None
    return raw


def _normalized_hostname(value: str) -> str:
    return value.strip().rstrip(".").casefold()


def _key_path_check(
    raw_path: str,
    *,
    passphrase: str,
    public_key: bytes | None,
    repository_root: Path,
) -> dict[str, object]:
    report: dict[str, object] = {
        "status": "NOT_CONFIGURED",
        "outside_repository": False,
        "symlink": False,
        "private_key_type": "NOT_CHECKED",
        "keypair_matches_trust_anchor": False,
        "posix_permissions": "NOT_CHECKED",
        "passphrase_value_printed": False,
        "private_key_value_printed": False,
    }
    if not raw_path.strip():
        return report
    try:
        raw = Path(os.path.expandvars(os.path.expanduser(raw_path.strip())))
        if not raw.is_absolute():
            report["status"] = "PRIVATE_KEY_PATH_NOT_ABSOLUTE"
            return report
        report["symlink"] = raw.is_symlink()
        if report["symlink"]:
            report["status"] = "SYMLINK_FORBIDDEN"
            return report
        path = raw.resolve(strict=True)
        repo_root = repository_root.resolve(strict=True)
        if path.is_relative_to(repo_root):
            report["status"] = "PRIVATE_KEY_MUST_BE_OUTSIDE_REPOSITORY"
            return report
        report["outside_repository"] = True
        if not path.is_file():
            report["status"] = "PRIVATE_KEY_PATH_NOT_FILE"
            return report
        if os.name != "nt":
            mode = stat.S_IMODE(path.stat().st_mode)
            if mode & 0o077:
                report["posix_permissions"] = "GROUP_OR_OTHER_ACCESS_PRESENT"
                report["status"] = "PRIVATE_KEY_PERMISSIONS_TOO_OPEN"
                return report
            report["posix_permissions"] = "OWNER_ONLY"
        else:
            # Python's portable permission bits do not reliably describe Windows ACLs.
            report["posix_permissions"] = "WINDOWS_ACL_REVIEW_REQUIRED"
        key_bytes = path.read_bytes()
        key = serialization.load_pem_private_key(
            key_bytes,
            password=passphrase.encode("utf-8") if passphrase else None,
        )
        del key_bytes
        if not isinstance(key, Ed25519PrivateKey):
            report["private_key_type"] = "NOT_ED25519"
            report["status"] = "PRIVATE_KEY_NOT_ED25519"
            return report
        report["private_key_type"] = "ED25519"
        actual = key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        if public_key is None:
            report["status"] = "GRANT_PUBLIC_TRUST_ANCHOR_INVALID"
            return report
        if actual != public_key:
            report["status"] = "PRIVATE_PUBLIC_KEYPAIR_MISMATCH"
            return report
        report["keypair_matches_trust_anchor"] = True
        report["status"] = (
            "KEYPAIR_PASS_WINDOWS_ACL_REVIEW_REQUIRED"
            if os.name == "nt" else "PASS"
        )
        return report
    except (OSError, ValueError, TypeError):
        report["status"] = "PRIVATE_KEY_UNAVAILABLE_OR_INVALID"
        return report


def _inspect_registry(raw_path: str) -> dict[str, object]:
    report: dict[str, object] = {
        "status": "NOT_CONFIGURED",
        "absolute_path": False,
        "symlink": False,
        "parent_directory_exists": False,
        "schema_check": "NOT_RUN",
        "opened_read_only": False,
        "registry_path_printed": False,
        "registry_mutated": False,
    }
    if not raw_path.strip():
        return report
    try:
        expanded = os.path.expandvars(os.path.expanduser(raw_path.strip()))
        supplied_path = Path(expanded)
        if not supplied_path.is_absolute():
            report["status"] = "PATH_NOT_ABSOLUTE"
            return report
        report["symlink"] = supplied_path.is_symlink()
        if report["symlink"]:
            report["status"] = "SYMLINK_FORBIDDEN"
            return report
        path = supplied_path.resolve(strict=False)
        if not path.is_absolute():
            report["status"] = "PATH_NOT_ABSOLUTE"
            return report
        report["absolute_path"] = True
        report["parent_directory_exists"] = path.parent.is_dir()
        if not report["parent_directory_exists"]:
            report["status"] = "PARENT_DIRECTORY_MISSING_OR_INACCESSIBLE"
            return report
        if not path.exists():
            report["status"] = "NOT_INITIALIZED"
            return report
        if not path.is_file():
            report["status"] = "REGISTRY_PATH_NOT_FILE"
            return report
        uri = "file:" + quote(str(path), safe="/:\\") + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=5.0)) as db:
            report["opened_read_only"] = True
            integrity = db.execute("PRAGMA integrity_check").fetchone()
            if not integrity or integrity[0] != "ok":
                report["schema_check"] = "INTEGRITY_FAILED"
                report["status"] = "REGISTRY_INTEGRITY_FAILED"
                return report
            metadata = db.execute(
                "SELECT value FROM registry_meta WHERE key='schema'"
            ).fetchone()
            version = db.execute("PRAGMA user_version").fetchone()
            table = db.execute("PRAGMA table_info(issued_grants)").fetchall()
            columns = [row[1] for row in table]
            if (
                metadata != (REGISTRY_SCHEMA,)
                or version != (1,)
                or columns != REGISTRY_COLUMNS
            ):
                report["schema_check"] = "SCHEMA_INVALID"
                report["status"] = "REGISTRY_SCHEMA_INVALID"
                return report
        report["schema_check"] = "PASS"
        report["status"] = "PASS"
        return report
    except (OSError, sqlite3.Error, ValueError, RuntimeError):
        report["status"] = "REGISTRY_READ_ONLY_CHECK_FAILED"
        return report


def inspect_host(
    *,
    environ: Mapping[str, str] | None = None,
    observed_hostname: str | None = None,
    expected_hostname: str = "",
    forbidden_hostnames: tuple[str, ...] | list[str] = (),
    grant_private_key_path: str = "",
    registry_path: str = "",
    repository_root: Path | None = None,
) -> dict[str, object]:
    """Inspect the host without creating files or modifying process/machine state."""
    env = os.environ if environ is None else environ
    actual_hostname = observed_hostname if observed_hostname is not None else platform.node()
    actual_norm = _normalized_hostname(actual_hostname)
    expected_norm = _normalized_hostname(expected_hostname)
    forbidden_norms = {
        _normalized_hostname(name) for name in forbidden_hostnames if _normalized_hostname(name)
    }
    host_separation = {
        "expected_hostname_supplied": bool(expected_norm),
        "expected_hostname_matches": bool(expected_norm and actual_norm == expected_norm),
        "forbidden_host_count": len(forbidden_norms),
        "required_forbidden_host_count": EXPECTED_FORBIDDEN_HOST_COUNT,
        "current_host_matches_forbidden": bool(actual_norm and actual_norm in forbidden_norms),
        "host_name_separation": False,
        # Names alone cannot prove that administrators, VM/hypervisor, network,
        # identity provider, or secret-manager ownership are independent.
        "independent_administration_verified": False,
    }
    host_separation["host_name_separation"] = bool(
        host_separation["expected_hostname_matches"]
        and len(forbidden_norms) >= EXPECTED_FORBIDDEN_HOST_COUNT
        and not host_separation["current_host_matches_forbidden"]
        and expected_norm not in forbidden_norms
    )
    host_separation["status"] = (
        "PASS_HOSTNAMES_ONLY_MANUAL_INDEPENDENCE_REVIEW_REQUIRED"
        if host_separation["host_name_separation"] else "HOST_NAME_SEPARATION_BLOCKED"
    )

    key_checks: dict[str, str] = {}
    decoded: dict[str, bytes] = {}
    for name, role in TRUST_ENVIRONMENTS.items():
        value = env.get(role, "").strip()
        if not value:
            key_checks[name] = "NOT_CONFIGURED"
            continue
        raw = _decode_public_key(value)
        if raw is None:
            key_checks[name] = "INVALID_BASE64_OR_LENGTH"
            continue
        decoded[name] = raw
        key_checks[name] = "FORMAT_PASS"
    first_by_key: dict[bytes, str] = {}
    for name, raw in decoded.items():
        previous = first_by_key.get(raw)
        if previous is not None:
            key_checks[name] = "DUPLICATE_KEY_MATERIAL"
            key_checks[previous] = "DUPLICATE_KEY_MATERIAL"
        else:
            first_by_key[raw] = name

    grant_public = decoded.get("grant")
    key_report = _key_path_check(
        grant_private_key_path,
        passphrase=env.get(PASSPHRASE_ENVIRONMENT, ""),
        public_key=grant_public,
        repository_root=repository_root or Path(__file__).resolve().parents[1],
    )
    registry_report = _inspect_registry(registry_path)

    keys_pass = all(key_checks.get(role) == "FORMAT_PASS" for role in TRUST_ENVIRONMENTS)
    keypair_pass = key_report["status"] == "PASS"
    # Windows requires an explicit ACL review even when the keypair matches.
    if os.name == "nt":
        keypair_pass = key_report["status"] == "KEYPAIR_PASS_WINDOWS_ACL_REVIEW_REQUIRED"
    host_pass = host_separation["host_name_separation"] is True
    registry_pass = registry_report["status"] == "PASS"
    local_checks_pass = keys_pass and keypair_pass and host_pass and registry_pass
    return {
        "schema": SCHEMA,
        "status": (
            "PREFLIGHT_PASS_MANUAL_TRUST_BOUNDARY_REVIEW_REQUIRED"
            if local_checks_pass else "BLOCKED"
        ),
        "host_separation": host_separation,
        "public_key_checks": key_checks,
        "grant_private_key_check": key_report,
        "registry_check": registry_report,
        "production_grant_issuance_authorized": False,
        "grant_issued": False,
        "orders_submitted": False,
        "demo_trading_authorized": False,
        "live_trading_allowed": False,
        "independent_administration_verified": False,
        "manual_requirements": [
            "independently verify the host, operating-system administrator, VM/hypervisor and secret-manager boundary",
            "verify operational owners, incident contacts, key rotation and revocation for all upstream authorities",
            "verify the real Signal Source, Risk+Reservation source and human approval workflow; key presence alone is not proof of an operating service",
            "review effective Windows ACLs or platform-specific secret-mount permissions for the Grant private key, registry, packet and output directories",
            "verify current exact-SHA G13 artifacts and fresh signed source attestations before grant issuance",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-hostname", required=True)
    parser.add_argument("--forbidden-hostname", action="append", default=[])
    parser.add_argument("--grant-private-key", required=True)
    parser.add_argument("--registry", required=True)
    args = parser.parse_args(argv)
    report = inspect_host(
        expected_hostname=args.expected_hostname,
        forbidden_hostnames=args.forbidden_hostname,
        grant_private_key_path=args.grant_private_key,
        registry_path=args.registry,
    )
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] == "PREFLIGHT_PASS_MANUAL_TRUST_BOUNDARY_REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
