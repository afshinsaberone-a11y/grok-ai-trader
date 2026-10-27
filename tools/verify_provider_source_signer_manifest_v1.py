"""Bind a source-built wheelhouse manifest to the signed trust-registry allowlist.

This is a candidate provenance check, not a production approval. It requires a
signed registry bundle with root key/fingerprint/digest pins configured outside
the repository. For the current source-manifest schema, signed-identity trust
records are usable only when the manifest includes the actual signer fingerprint;
otherwise an exact, reviewed source exception is required.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping

try:
    from tools.verify_provider_trust_registry_bundle_v1 import (
        BUNDLE_PATH_ENV,
        EXPECTED_BUNDLE_SHA256_ENV,
        ROOT_FINGERPRINT_ENV,
        ROOT_PUBLIC_KEY_ENV,
        TrustRegistryVerificationError,
        _unique_object,
        _validate_source_signers,
        verify_trust_registry_bundle,
    )
except ModuleNotFoundError as exc:
    if exc.name not in {"tools", "tools.verify_provider_trust_registry_bundle_v1"}:
        raise
    from verify_provider_trust_registry_bundle_v1 import (
        BUNDLE_PATH_ENV,
        EXPECTED_BUNDLE_SHA256_ENV,
        ROOT_FINGERPRINT_ENV,
        ROOT_PUBLIC_KEY_ENV,
        TrustRegistryVerificationError,
        _unique_object,
        _validate_source_signers,
        verify_trust_registry_bundle,
    )

MANIFEST_PATH_ENV = "FOREXAI_PROVIDER_SOURCE_BUILD_MANIFEST_PATH"
MANIFEST_SHA256_ENV = "FOREXAI_PROVIDER_SOURCE_BUILD_MANIFEST_SHA256"
SOURCE_MANIFEST_SCHEMA = "forexai.provider_source_built_wheel_candidate.v1"
SOURCE_CANDIDATE_STATUS = "SOURCE_BUILD_CANDIDATE_NOT_APPROVED"
SETUPTOOLS_BOOTSTRAP_SCHEMA = "forexai.provider_setuptools_source_bootstrap.v1"
SETUPTOOLS_BOOTSTRAP_STATUS = "SIGNED_SOURCE_BUILD_CANDIDATE_NOT_APPROVED"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
SHA256_PIN = re.compile(r"^sha256:[0-9a-f]{64}$")
EXPECTED_WHEELS = {
    "cffi": "2.1.1",
    "colorama": "0.4.6",
    "pycparser": "3.12",
    "pygments": "2.21.0",
}
SETUPTOOLS_SOURCE = ("pypa/setuptools", "9c4d383631d3951fcae0afd73b5d08ff5a262976", "v80.9.0")


class SourceSignerManifestError(RuntimeError):
    """Sanitized fail-closed result for a source-manifest/allowlist mismatch."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json_object(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except TrustRegistryVerificationError as exc:
        raise SourceSignerManifestError("SOURCE_MANIFEST_DUPLICATE_JSON_KEY") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SourceSignerManifestError(code) from exc
    if not isinstance(value, dict):
        raise SourceSignerManifestError(code)
    return value


def _require_string(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceSignerManifestError(code)
    return value


def _source_tuple(source: Mapping[str, Any], label: str) -> tuple[str, str, str]:
    repository = _require_string(source.get("repository"), f"SOURCE_REPOSITORY_MISSING:{label}")
    commit = _require_string(source.get("commit"), f"SOURCE_COMMIT_MISSING:{label}")
    release_tag = _require_string(source.get("github_release_tag") or source.get("release_tag"), f"SOURCE_RELEASE_TAG_MISSING:{label}")
    if not HEX_40.fullmatch(commit):
        raise SourceSignerManifestError(f"SOURCE_COMMIT_SHA_INVALID:{label}")
    target_commit = source.get("github_release_tag_target_commit") or source.get("release_tag_target_commit")
    if target_commit != commit:
        raise SourceSignerManifestError(f"SOURCE_TAG_TARGET_COMMIT_MISMATCH:{label}")
    return repository, commit, release_tag


def _match_source_to_allowlist(
    source: Mapping[str, Any],
    signers: list[dict[str, Any]],
    label: str,
) -> dict[str, str]:
    repository, commit, release_tag = _source_tuple(source, label)
    matches = [
        item for item in signers
        if item.get("repository") == repository
        and item.get("commit_sha") == commit
        and item.get("release_tag") == release_tag
    ]
    if len(matches) != 1:
        raise SourceSignerManifestError(f"SOURCE_COMMIT_NOT_UNIQUELY_ALLOWLISTED:{label}")
    record = matches[0]
    basis = record.get("trust_basis")
    if basis == "VERIFIED_SIGNATURE_IDENTITY_PIN":
        if source.get("github_commit_signature_verified") is not True:
            raise SourceSignerManifestError(f"SOURCE_SIGNATURE_NOT_VERIFIED_FOR_PINNED_SIGNER:{label}")
        actual_fingerprint = source.get("signer_fingerprint")
        if not isinstance(actual_fingerprint, str) or actual_fingerprint != record.get("signer_fingerprint"):
            raise SourceSignerManifestError(f"SOURCE_SIGNER_FINGERPRINT_NOT_BOUND_IN_MANIFEST:{label}")
    elif basis == "INDEPENDENT_SOURCE_EXCEPTION":
        # This is intentionally scoped to the exact tuple. The source build
        # manifest may report a GitHub "verified" boolean, but it currently
        # does not bind that verification to the independently pinned signer
        # fingerprint. Do not promote it as identity-verified on that boolean.
        if record.get("signature_status") != "NOT_VERIFIED":
            raise SourceSignerManifestError(f"SOURCE_EXCEPTION_SIGNATURE_POLICY_MISMATCH:{label}")
    else:
        raise SourceSignerManifestError(f"SOURCE_TRUST_BASIS_UNSUPPORTED:{label}")
    return {
        "label": label,
        "repository": repository,
        "commit_sha": commit,
        "release_tag": release_tag,
        "trust_basis": str(basis),
        "evidence_sha256": str(record.get("evidence_sha256", "")),
    }


def verify_source_manifest_tree(
    manifest_path: Path,
    manifest: Mapping[str, Any],
    trusted_signers: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify actual wheel hashes and ensure each exact source pin has an approved entry."""
    if manifest.get("schema") != SOURCE_MANIFEST_SCHEMA:
        raise SourceSignerManifestError("SOURCE_MANIFEST_SCHEMA_INVALID")
    if manifest.get("status") != SOURCE_CANDIDATE_STATUS:
        raise SourceSignerManifestError("SOURCE_MANIFEST_STATUS_INVALID")
    for field in ("production_approved", "bootstrap_approved"):
        if manifest.get(field) is not False:
            raise SourceSignerManifestError(f"SOURCE_MANIFEST_APPROVAL_FLAG_MUST_REMAIN_FALSE:{field}")

    signer_count = _validate_source_signers(trusted_signers, datetime.now(timezone.utc))
    signer_entries = trusted_signers.get("signers")
    if signer_count <= 0 or not isinstance(signer_entries, list):
        raise SourceSignerManifestError("SOURCE_SIGNER_ALLOWLIST_EMPTY")

    wheel_records = manifest.get("wheels")
    if not isinstance(wheel_records, list) or len(wheel_records) != len(EXPECTED_WHEELS):
        raise SourceSignerManifestError("SOURCE_MANIFEST_WHEEL_CARDINALITY_INVALID")
    by_package: dict[str, Mapping[str, Any]] = {}
    wheel_dir = manifest_path.parent / "wheels"
    wheel_sources: list[dict[str, str]] = []
    seen_filenames: set[str] = set()
    for value in wheel_records:
        if not isinstance(value, dict):
            raise SourceSignerManifestError("SOURCE_MANIFEST_WHEEL_RECORD_INVALID")
        package = _require_string(value.get("package"), "SOURCE_MANIFEST_PACKAGE_MISSING")
        version = _require_string(value.get("version"), f"SOURCE_MANIFEST_VERSION_MISSING:{package}")
        if package not in EXPECTED_WHEELS or EXPECTED_WHEELS[package] != version or package in by_package:
            raise SourceSignerManifestError(f"SOURCE_MANIFEST_PACKAGE_SET_MISMATCH:{package}")
        filename = _require_string(value.get("filename"), f"SOURCE_MANIFEST_WHEEL_FILENAME_MISSING:{package}")
        if Path(filename).name != filename or not filename.lower().endswith(".whl") or filename in seen_filenames:
            raise SourceSignerManifestError(f"SOURCE_MANIFEST_WHEEL_FILENAME_INVALID:{package}")
        wheel_digest = value.get("sha256")
        if not isinstance(wheel_digest, str) or not HEX_64.fullmatch(wheel_digest):
            raise SourceSignerManifestError(f"SOURCE_MANIFEST_WHEEL_HASH_INVALID:{package}")
        wheel_path = wheel_dir / filename
        if wheel_path.is_symlink() or not wheel_path.is_file():
            raise SourceSignerManifestError(f"SOURCE_MANIFEST_WHEEL_FILE_MISSING:{package}")
        if _sha256(wheel_path.read_bytes()) != wheel_digest:
            raise SourceSignerManifestError(f"SOURCE_MANIFEST_WHEEL_HASH_MISMATCH:{package}")

        source = value.get("source")
        if not isinstance(source, dict) or source.get("github_api_commit_sha_matches") is not True:
            raise SourceSignerManifestError(f"SOURCE_MANIFEST_SOURCE_IDENTITY_INVALID:{package}")
        wheel_sources.append(_match_source_to_allowlist(source, signer_entries, package))
        by_package[package] = value
        seen_filenames.add(filename)

    if set(by_package) != set(EXPECTED_WHEELS):
        raise SourceSignerManifestError("SOURCE_MANIFEST_REQUIRED_PACKAGE_MISSING")

    # The builder has a separate source-built setuptools bootstrap. Bind its
    # manifest, wheel digest and source identity as part of the same candidate.
    build_tools = manifest.get("build_tools")
    if not isinstance(build_tools, dict):
        raise SourceSignerManifestError("SOURCE_MANIFEST_BUILD_TOOLS_MISSING")
    if (
        build_tools.get("setuptools_source_commit_signature_verified") is not True
        or build_tools.get("setuptools_source_release_tag_signature_verified") is not True
        or build_tools.get("setuptools_source_commit") != SETUPTOOLS_SOURCE[1]
        or build_tools.get("setuptools_source_release_tag") != SETUPTOOLS_SOURCE[2]
    ):
        raise SourceSignerManifestError("SOURCE_MANIFEST_SETUPTOOLS_SOURCE_IDENTITY_INVALID")

    artifacts_root = manifest_path.parent.parent
    bootstrap_root = artifacts_root / "provider-setuptools-bootstrap"
    bootstrap_manifest_path = bootstrap_root / "setuptools-bootstrap-manifest.json"
    if bootstrap_manifest_path.is_symlink() or not bootstrap_manifest_path.is_file():
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_MANIFEST_MISSING")
    bootstrap_manifest_digest = _sha256(bootstrap_manifest_path.read_bytes())
    expected_bootstrap_manifest_digest = build_tools.get("setuptools_source_bootstrap_manifest_sha256")
    if not isinstance(expected_bootstrap_manifest_digest, str) or not hmac_compare(
        bootstrap_manifest_digest, expected_bootstrap_manifest_digest
    ):
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_MANIFEST_HASH_MISMATCH")
    bootstrap_manifest = _read_json_object(bootstrap_manifest_path, "SETUPTOOLS_BOOTSTRAP_MANIFEST_INVALID")
    if (
        bootstrap_manifest.get("schema") != SETUPTOOLS_BOOTSTRAP_SCHEMA
        or bootstrap_manifest.get("status") != SETUPTOOLS_BOOTSTRAP_STATUS
        or bootstrap_manifest.get("production_approved") is not False
        or bootstrap_manifest.get("bootstrap_approved") is not False
        or bootstrap_manifest.get("package_name") != "setuptools"
        or bootstrap_manifest.get("version") != "80.9.0"
    ):
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_MANIFEST_BOUNDARY_MISMATCH")
    setuptools_source = bootstrap_manifest.get("source")
    if not isinstance(setuptools_source, dict):
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_SOURCE_MISSING")
    if _source_tuple_setuptools(setuptools_source) != SETUPTOOLS_SOURCE:
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_SOURCE_IDENTITY_MISMATCH")
    if (
        build_tools.get("setuptools_source_bootstrap_wheel_sha256") != bootstrap_manifest.get("wheel_sha256")
    ):
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_WHEEL_HASH_METADATA_MISMATCH")

    bootstrap_filename = _require_string(
        bootstrap_manifest.get("wheel_filename"), "SETUPTOOLS_BOOTSTRAP_WHEEL_FILENAME_MISSING"
    )
    if Path(bootstrap_filename).name != bootstrap_filename or not bootstrap_filename.lower().endswith(".whl"):
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_WHEEL_FILENAME_INVALID")
    bootstrap_wheel_path = bootstrap_root / "wheels" / bootstrap_filename
    if bootstrap_wheel_path.is_symlink() or not bootstrap_wheel_path.is_file():
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_WHEEL_MISSING")
    bootstrap_wheel_digest = _sha256(bootstrap_wheel_path.read_bytes())
    if (
        bootstrap_wheel_digest != bootstrap_manifest.get("wheel_sha256")
        or bootstrap_wheel_digest != build_tools.get("setuptools_source_bootstrap_wheel_sha256")
    ):
        raise SourceSignerManifestError("SETUPTOOLS_BOOTSTRAP_WHEEL_HASH_MISMATCH")

    wheel_sources.append(_match_source_to_allowlist(setuptools_source, signer_entries, "setuptools-bootstrap"))
    return {
        "status": "PASS_SOURCE_SIGNER_ALLOWLIST_MATCH",
        "reason_code": "ALL_SOURCE_COMMITS_EXACTLY_ALLOWLISTED",
        "source_count": len(wheel_sources),
        "source_wheel_count": len(wheel_records),
        "source_matches": wheel_sources,
        "bundle_source_signer_count": signer_count,
        "production_approved": False,
        "bootstrap_approved": False,
        "trading_authorization_created": False,
    }


def _source_tuple_setuptools(source: Mapping[str, Any]) -> tuple[str, str, str]:
    repository = _require_string(source.get("repository"), "SETUPTOOLS_SOURCE_REPOSITORY_MISSING")
    commit = _require_string(source.get("commit"), "SETUPTOOLS_SOURCE_COMMIT_MISSING")
    release_tag = _require_string(source.get("release_tag"), "SETUPTOOLS_SOURCE_RELEASE_TAG_MISSING")
    if repository != "pypa/setuptools" or not HEX_40.fullmatch(commit):
        raise SourceSignerManifestError("SETUPTOOLS_SOURCE_IDENTITY_INVALID")
    if source.get("release_tag_target_commit") != commit:
        raise SourceSignerManifestError("SETUPTOOLS_SOURCE_TAG_TARGET_MISMATCH")
    return repository, commit, release_tag


def hmac_compare(left: str, right: Any) -> bool:
    # Digests are non-secret, but constant-time comparison avoids inconsistent
    # handling when the value is malformed or of an unexpected type.
    import hmac
    return isinstance(right, str) and hmac.compare_digest(left, right)


def inspect_source_manifest(environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Validate the externally pinned source-build manifest and its wheel tree."""
    env = os.environ if environ is None else environ
    report: dict[str, Any] = {
        "status": "NOT_CONFIGURED",
        "reason_code": "SOURCE_MANIFEST_PATH_NOT_CONFIGURED",
        "production_approved": False,
        "bootstrap_approved": False,
        "trading_authorization_created": False,
    }
    try:
        manifest_raw = env.get(MANIFEST_PATH_ENV, "").strip()
        if not manifest_raw:
            return report
        manifest_pin = env.get(MANIFEST_SHA256_ENV, "").strip()
        if not SHA256_PIN.fullmatch(manifest_pin):
            raise SourceSignerManifestError("SOURCE_MANIFEST_DIGEST_PIN_NOT_CONFIGURED_OR_INVALID")

        manifest_path = Path(os.path.expandvars(os.path.expanduser(manifest_raw)))
        if not manifest_path.is_absolute():
            raise SourceSignerManifestError("SOURCE_MANIFEST_PATH_NOT_ABSOLUTE")
        if manifest_path.is_symlink() or not manifest_path.is_file():
            raise SourceSignerManifestError("SOURCE_MANIFEST_FILE_NOT_FOUND_OR_SYMLINK")
        repo_root = Path(__file__).resolve().parents[1]
        resolved_manifest = manifest_path.resolve(strict=True)
        try:
            resolved_manifest.relative_to(repo_root.resolve())
        except ValueError:
            pass
        else:
            raise SourceSignerManifestError("SOURCE_MANIFEST_MUST_BE_OUTSIDE_REPOSITORY")
        manifest_size = resolved_manifest.stat().st_size
        if manifest_size <= 0 or manifest_size > 4 * 1024 * 1024:
            raise SourceSignerManifestError("SOURCE_MANIFEST_SIZE_INVALID")
        manifest_bytes = resolved_manifest.read_bytes()
        if len(manifest_bytes) != manifest_size:
            raise SourceSignerManifestError("SOURCE_MANIFEST_CHANGED_DURING_READ")
        manifest_digest = "sha256:" + _sha256(manifest_bytes)
        if not hmac_compare(manifest_digest, manifest_pin):
            raise SourceSignerManifestError("SOURCE_MANIFEST_DIGEST_PIN_MISMATCH")

        # Verify the exact signed registry bundle through the same verifier used
        # by Provider preflight. Re-hash the bytes parsed below to detect a
        # bundle replacement between verifier read and manifest inspection.
        verify_report = verify_trust_registry_bundle(environ=env, repository_root=repo_root)
        bundle_raw_path = env.get(BUNDLE_PATH_ENV, "").strip()
        bundle_path = Path(os.path.expandvars(os.path.expanduser(bundle_raw_path)))
        if not bundle_path.is_absolute() or bundle_path.is_symlink() or not bundle_path.is_file():
            raise SourceSignerManifestError("TRUST_REGISTRY_BUNDLE_FILE_NOT_FOUND_OR_UNSAFE")
        resolved_bundle = bundle_path.resolve(strict=True)
        bundle_bytes = resolved_bundle.read_bytes()
        if len(bundle_bytes) > 2 * 1024 * 1024:
            raise SourceSignerManifestError("TRUST_REGISTRY_BUNDLE_SIZE_INVALID")
        if "sha256:" + _sha256(bundle_bytes) != verify_report.get("bundle_sha256"):
            raise SourceSignerManifestError("TRUST_REGISTRY_BUNDLE_CHANGED_DURING_INSPECTION")

        try:
            bundle = json.loads(bundle_bytes.decode("utf-8"), object_pairs_hook=_unique_object)
            manifest = json.loads(manifest_bytes.decode("utf-8"), object_pairs_hook=_unique_object)
        except TrustRegistryVerificationError as exc:
            raise SourceSignerManifestError("SOURCE_MANIFEST_OR_BUNDLE_DUPLICATE_JSON_KEY") from exc
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise SourceSignerManifestError("SOURCE_MANIFEST_OR_BUNDLE_JSON_INVALID") from exc
        if not isinstance(bundle, dict) or not isinstance(manifest, dict):
            raise SourceSignerManifestError("SOURCE_MANIFEST_OR_BUNDLE_ROOT_INVALID")

        payload = bundle.get("payload", {})
        trusted_signers = payload.get("trusted_signers", {}) if isinstance(payload, dict) else {}
        report.update(verify_source_manifest_tree(resolved_manifest, manifest, trusted_signers))
        report["source_manifest_sha256"] = manifest_digest
        report["manifest_digest_pin_verified"] = True
        report["verified_bundle_sha256"] = verify_report["bundle_sha256"]
        report["verified_registry_revision"] = verify_report["registry_revision"]
        report["signature_verified"] = True
        return report
    except (SourceSignerManifestError, TrustRegistryVerificationError) as exc:
        report["status"] = "BLOCKED"
        report["reason_code"] = str(exc)
        return report
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError, OverflowError, RecursionError, RuntimeError):
        report["status"] = "BLOCKED"
        report["reason_code"] = "SOURCE_SIGNER_MANIFEST_INSPECTION_FAILED"
        return report

def main() -> int:
    report = inspect_source_manifest()
    print(f"SOURCE_SIGNER_MANIFEST_GATE={report.get('status')}")
    print(f"REASON_CODE={report.get('reason_code')}")
    print("PRODUCTION_APPROVED=false")
    print("BOOTSTRAP_APPROVED=false")
    print("TRADING_AUTHORIZATION_CREATED=false")
    if report.get("status") == "PASS_SOURCE_SIGNER_ALLOWLIST_MATCH":
        print(f"SOURCE_COUNT={report['source_count']}")
        print(f"SOURCE_WHEEL_COUNT={report['source_wheel_count']}")
    return 0 if report.get("status") == "PASS_SOURCE_SIGNER_ALLOWLIST_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
