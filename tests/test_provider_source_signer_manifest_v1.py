"""End-to-end tests for binding provider source-build wheel hashes to signed signer policy."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

import pytest

from tools.verify_provider_source_signer_manifest_v1 import (
    MANIFEST_PATH_ENV,
    MANIFEST_SHA256_ENV,
    SOURCE_CANDIDATE_STATUS,
    SOURCE_MANIFEST_SCHEMA,
    SourceSignerManifestError,
    inspect_source_manifest,
    verify_source_manifest_tree,
)
from tests.trust_registry_bundle_test_support import build_test_bundle


SOURCES = [
    ("pycparser", "3.12", "eliben/pycparser", "3ec766b7cd94724cba714296509604597ea4ce4e", "release_v3.12", False, False),
    ("cffi", "2.1.1", "python-cffi/cffi", "fd33e7700f0ebafe6f30bd5053f13327221b77a2", "v2.1.1", True, False),
    ("colorama", "0.4.6", "tartley/colorama", "3de9f013df4b470069d03d250224062e8cf15c49", "0.4.6", False, False),
    ("pygments", "2.21.0", "pygments/pygments", "a43b45dcf081b6010c6ab4428f149f7f6d2499c4", "2.21.0", False, False),
    ("setuptools-bootstrap", "80.9.0", "pypa/setuptools", "9c4d383631d3951fcae0afd73b5d08ff5a262976", "v80.9.0", True, True),
]
SETUPTOOLS_COMMIT = "9c4d383631d3951fcae0afd73b5d08ff5a262976"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def signer_record(source: tuple, index: int, now: datetime) -> dict:
    _, _, repository, commit, tag, _commit_verified, _tag_verified = source
    review_id = f"source-review-{index}"
    return {
        "signer_id": f"exact-source-exception-{index}",
        "repository": repository,
        "commit_sha": commit,
        "release_tag": tag,
        "trust_basis": "INDEPENDENT_SOURCE_EXCEPTION",
        "signature_status": "NOT_VERIFIED",
        "signer_identity": f"source-exception:{review_id}",
        "signer_fingerprint": "not_applicable_source_exception",
        "evidence_reference": f"https://example.invalid/reviews/{review_id}",
        "evidence_sha256": f"{index:064x}",
        "source_author_identity": f"upstream-author-{index}",
        "reviewer_identity": f"independent-reviewer-{index}",
        "review_id": review_id,
        "reviewed_at_utc": (now - timedelta(minutes=1)).isoformat().replace("+00:00", "Z"),
        "valid_from_utc": (now - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        "valid_until_utc": (now + timedelta(days=90)).isoformat().replace("+00:00", "Z"),
        "status": "ACTIVE",
        "independently_reviewed": True,
    }


def make_artifact_tree(tmp_path: Path, source_signers: list[dict]) -> tuple[Path, dict]:
    artifacts_root = tmp_path / "artifacts"
    source_root = artifacts_root / "provider-source-build"
    wheel_dir = source_root / "wheels"
    bootstrap_root = artifacts_root / "provider-setuptools-bootstrap"
    bootstrap_wheel_dir = bootstrap_root / "wheels"
    wheel_dir.mkdir(parents=True)
    bootstrap_wheel_dir.mkdir(parents=True)

    wheel_records = []
    for index, source in enumerate(SOURCES[:4], start=1):
        package, version, repository, commit, tag, commit_verified, tag_verified = source
        filename = f"{package}-{version}-py3-none-any.whl"
        wheel_bytes = f"test-only-wheel:{package}=={version}".encode("utf-8")
        (wheel_dir / filename).write_bytes(wheel_bytes)
        wheel_records.append({
            "package": package,
            "version": version,
            "filename": filename,
            "sha256": sha256_bytes(wheel_bytes),
            "source": {
                "repository": repository,
                "commit": commit,
                "github_api_commit_sha_matches": True,
                "github_commit_signature_verified": commit_verified,
                "github_release_tag": tag,
                "github_release_tag_target_commit": commit,
                "github_release_tag_signature_verified": tag_verified,
            },
        })

    bootstrap_source = SOURCES[4]
    boot_name, boot_version, boot_repo, boot_commit, boot_tag, boot_commit_verified, boot_tag_verified = bootstrap_source
    bootstrap_filename = "setuptools-80.9.0-py3-none-any.whl"
    bootstrap_bytes = b"test-only-setuptools-bootstrap-wheel"
    (bootstrap_wheel_dir / bootstrap_filename).write_bytes(bootstrap_bytes)
    bootstrap_manifest = {
        "schema": "forexai.provider_setuptools_source_bootstrap.v1",
        "status": "SIGNED_SOURCE_BUILD_CANDIDATE_NOT_APPROVED",
        "production_approved": False,
        "bootstrap_approved": False,
        "package_name": "setuptools",
        "version": "80.9.0",
        "wheel_filename": bootstrap_filename,
        "wheel_sha256": sha256_bytes(bootstrap_bytes),
        "source": {
            "repository": boot_repo,
            "commit": boot_commit,
            "release_tag": boot_tag,
            "release_tag_target_commit": boot_commit,
            "github_commit_signature_verified": boot_commit_verified,
            "github_release_tag_signature_verified": boot_tag_verified,
        },
    }
    bootstrap_manifest_path = bootstrap_root / "setuptools-bootstrap-manifest.json"
    bootstrap_manifest_bytes = (json.dumps(bootstrap_manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    bootstrap_manifest_path.write_bytes(bootstrap_manifest_bytes)

    manifest = {
        "schema": SOURCE_MANIFEST_SCHEMA,
        "status": SOURCE_CANDIDATE_STATUS,
        "production_approved": False,
        "bootstrap_approved": False,
        "target": {"runner": "windows-2022", "python": "3.13.17", "architecture": "x86_64"},
        "build_tools": {
            "setuptools_source_commit_signature_verified": True,
            "setuptools_source_release_tag_signature_verified": True,
            "setuptools_source_commit": SETUPTOOLS_COMMIT,
            "setuptools_source_release_tag": "v80.9.0",
            "setuptools_source_bootstrap_manifest_sha256": sha256_bytes(bootstrap_manifest_bytes),
            "setuptools_source_bootstrap_wheel_sha256": sha256_bytes(bootstrap_bytes),
        },
        "upstream_sources_with_unverified_commit_signatures": ["pycparser", "colorama", "pygments"],
        "upstream_sources_without_verified_commit_or_signed_release_tag": ["colorama", "pycparser", "pygments"],
        "wheels": wheel_records,
    }
    manifest_path = source_root / "source-build-manifest.json"
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    return manifest_path, manifest


def make_bundle_config(tmp_path: Path, source_signers: list[dict], manifest_path: Path) -> tuple[dict[str, str], dict]:
    # Synthetic trust roots remain in memory; no private key is written to disk.
    def install_signers(payload: dict) -> None:
        payload["trusted_signers"]["signers"] = source_signers
        payload["trusted_signers"]["source_build_manifest_sha256"] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    config, bundle_path, _test_root_key = build_test_bundle(
        tmp_path / "trust-registry-test-bundle",
        mutate_payload=install_signers,
    )
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    return config, bundle["payload"]["trusted_signers"]


def make_source_signers(count: int | None = None) -> list[dict]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    records = [signer_record(source, index, now) for index, source in enumerate(SOURCES, start=1)]
    return records if count is None else records[:count]


def test_signed_bundle_allowlist_matches_all_exact_wheel_and_bootstrap_sources(tmp_path: Path):
    signers = make_source_signers()
    manifest_path, _ = make_artifact_tree(tmp_path, signers)
    config, _ = make_bundle_config(tmp_path, signers, manifest_path)
    config[MANIFEST_PATH_ENV] = str(manifest_path)
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    report = inspect_source_manifest(config)

    assert report["status"] == "PASS_SOURCE_SIGNER_ALLOWLIST_MATCH"
    assert report["reason_code"] == "ALL_SOURCE_COMMITS_EXACTLY_ALLOWLISTED"
    assert report["manifest_digest_pin_verified"] is True
    assert report["source_count"] == 5
    assert report["source_wheel_count"] == 4
    assert report["bundle_source_signer_count"] == 5
    assert report["production_approved"] is False
    assert report["bootstrap_approved"] is False
    assert report["trading_authorization_created"] is False


def test_missing_exact_source_allowlist_entry_blocks(tmp_path: Path):
    signers = make_source_signers(count=4)
    manifest_path, _ = make_artifact_tree(tmp_path, signers)
    config, _ = make_bundle_config(tmp_path, signers, manifest_path)
    config[MANIFEST_PATH_ENV] = str(manifest_path)
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    report = inspect_source_manifest(config)

    assert report["status"] == "BLOCKED"
    assert "SOURCE_COMMIT_NOT_UNIQUELY_ALLOWLISTED" in report["reason_code"]
    assert report["trading_authorization_created"] is False


def test_modified_wheel_after_manifest_creation_blocks(tmp_path: Path):
    signers = make_source_signers()
    manifest_path, _ = make_artifact_tree(tmp_path, signers)
    (manifest_path.parent / "wheels" / "cffi-2.1.1-py3-none-any.whl").write_bytes(b"changed after review")
    config, _ = make_bundle_config(tmp_path, signers, manifest_path)
    config[MANIFEST_PATH_ENV] = str(manifest_path)
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    report = inspect_source_manifest(config)

    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "SOURCE_MANIFEST_WHEEL_HASH_MISMATCH:cffi"


def test_source_commit_not_matching_signer_allowlist_blocks(tmp_path: Path):
    signers = make_source_signers()
    manifest_path, manifest = make_artifact_tree(tmp_path, signers)
    manifest["wheels"][0]["source"]["commit"] = "f" * 40
    manifest["wheels"][0]["source"]["github_release_tag_target_commit"] = "f" * 40
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    config, _ = make_bundle_config(tmp_path, signers, manifest_path)
    config[MANIFEST_PATH_ENV] = str(manifest_path)
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    report = inspect_source_manifest(config)

    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "SOURCE_COMMIT_NOT_UNIQUELY_ALLOWLISTED:pycparser"


def test_candidate_manifest_cannot_self_approve_production(tmp_path: Path):
    signers = make_source_signers()
    manifest_path, manifest = make_artifact_tree(tmp_path, signers)
    manifest["production_approved"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    config, _ = make_bundle_config(tmp_path, signers, manifest_path)
    config[MANIFEST_PATH_ENV] = str(manifest_path)
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    report = inspect_source_manifest(config)

    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "SOURCE_MANIFEST_APPROVAL_FLAG_MUST_REMAIN_FALSE:production_approved"


def test_verified_identity_pin_requires_signer_fingerprint_in_build_manifest(tmp_path: Path):
    signers = make_source_signers()
    signers[0]["trust_basis"] = "VERIFIED_SIGNATURE_IDENTITY_PIN"
    signers[0]["signature_status"] = "VERIFIED"
    signers[0]["signer_identity"] = "upstream-maintainer"
    signers[0]["signer_fingerprint"] = "gpg:" + ("A" * 40)
    manifest_path, manifest = make_artifact_tree(tmp_path, signers)
    manifest["wheels"][0]["source"]["github_commit_signature_verified"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    config, _ = make_bundle_config(tmp_path, signers, manifest_path)
    config[MANIFEST_PATH_ENV] = str(manifest_path)
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    report = inspect_source_manifest(config)

    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "SOURCE_SIGNER_FINGERPRINT_NOT_BOUND_IN_MANIFEST:pycparser"


def test_modified_manifest_without_updating_external_digest_pin_blocks(tmp_path: Path):
    signers = make_source_signers()
    manifest_path, _ = make_artifact_tree(tmp_path, signers)
    config, _ = make_bundle_config(tmp_path, signers, manifest_path)
    config[MANIFEST_PATH_ENV] = str(manifest_path)
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    manifest_path.write_bytes(manifest_path.read_bytes() + b" ")
    # Simulate a host administrator changing both the file and mutable env pin.
    # The root-signed registry digest must still reject this substitution.
    config[MANIFEST_SHA256_ENV] = "sha256:" + sha256_bytes(manifest_path.read_bytes())

    report = inspect_source_manifest(config)

    assert report["status"] == "BLOCKED"
    assert report["reason_code"] == "SIGNED_SOURCE_MANIFEST_DIGEST_PIN_MISMATCH"
    assert report["trading_authorization_created"] is False