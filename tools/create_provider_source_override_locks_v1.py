#!/usr/bin/env python3
"""Create two hash locks that replace an untrusted setuptools wheel with a signed-source candidate.

The download lock omits setuptools so pip never installs the PyPI candidate.
The install lock contains the exact locally built setuptools wheel digest after
validating its manifest, signed source identity, and one-line install lock.
Both outputs remain CI-only candidates; neither authorizes Provider deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Any

PACKAGE = "setuptools"
SOURCE_VERSION = "80.9.0"
SOURCE_REPOSITORY = "pypa/setuptools"
SOURCE_COMMIT = "9c4d383631d3951fcae0afd73b5d08ff5a262976"
SOURCE_TAG = "v80.9.0"
SOURCE_TAG_OBJECT = "ef921af5f4374a66c018304a2aa5306cb67962a0"
EXPECTED_SOURCE_LOCK_VERSION = "84.2.1"
PIN_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)")
HASH_RE = re.compile(r"--hash=sha256:([0-9a-f]{64})")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def package_blocks(lock_text: str) -> tuple[list[str], list[dict[str, Any]]]:
    lines = lock_text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    starts: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        match = PIN_RE.match(line)
        if match:
            starts.append((index, normalize_name(match.group(1)), match.group(2)))
    if not starts:
        raise ValueError("SOURCE_LOCK_HAS_NO_EXACT_PINS")

    prefix = lines[: starts[0][0]]
    blocks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pos, (start, name, version) in enumerate(starts):
        if name in seen:
            raise ValueError(f"DUPLICATE_SOURCE_LOCK_PIN:{name}")
        seen.add(name)
        end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
        block_lines = lines[start:end]
        hashes = HASH_RE.findall("\n".join(block_lines))
        if not hashes:
            raise ValueError(f"SOURCE_LOCK_PACKAGE_HAS_NO_SHA256:{name}")
        blocks.append({"name": name, "version": version, "lines": block_lines})
    return prefix, blocks


def wheel_metadata(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        candidates = [
            entry for entry in archive.namelist()
            if entry.endswith(".dist-info/METADATA") and entry.count("/") == 1
        ]
        if len(candidates) != 1:
            raise ValueError("REPLACEMENT_WHEEL_METADATA_CARDINALITY_INVALID")
        metadata = Parser().parsestr(archive.read(candidates[0]).decode("utf-8"))
    name, version = metadata.get("Name"), metadata.get("Version")
    if not name or not version:
        raise ValueError("REPLACEMENT_WHEEL_METADATA_MISSING")
    return normalize_name(name), version


def validate_signed_candidate(wheel: Path, manifest_path: Path) -> tuple[str, dict[str, Any]]:
    if wheel.name != "setuptools-80.9.0-py3-none-any.whl":
        raise ValueError("REPLACEMENT_WHEEL_FILENAME_MISMATCH")
    name, version = wheel_metadata(wheel)
    if name != PACKAGE or version != SOURCE_VERSION:
        raise ValueError(f"REPLACEMENT_WHEEL_NAME_VERSION_MISMATCH:{name}=={version}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source = manifest.get("source", {})
    if (
        manifest.get("schema") != "forexai.provider_setuptools_source_bootstrap.v1"
        or manifest.get("status") != "SIGNED_SOURCE_BUILD_CANDIDATE_NOT_APPROVED"
        or manifest.get("production_approved") is not False
        or manifest.get("bootstrap_approved") is not False
        or manifest.get("package_name") != PACKAGE
        or manifest.get("version") != SOURCE_VERSION
        or source.get("repository") != SOURCE_REPOSITORY
        or source.get("commit") != SOURCE_COMMIT
        or source.get("release_tag") != SOURCE_TAG
        or source.get("release_tag_object_sha") != SOURCE_TAG_OBJECT
        or source.get("github_commit_signature_verified") is not True
        or source.get("github_release_tag_signature_verified") is not True
        or source.get("release_tag_target_commit") != SOURCE_COMMIT
    ):
        raise ValueError("SIGNED_SOURCE_MANIFEST_IDENTITY_OR_BOUNDARY_MISMATCH")

    wheel_digest = sha256_file(wheel)
    if manifest.get("wheel_sha256") != wheel_digest:
        raise ValueError("SIGNED_SOURCE_WHEEL_SHA256_MISMATCH")
    lock_filename = manifest.get("install_lock_filename")
    if not isinstance(lock_filename, str) or Path(lock_filename).name != lock_filename:
        raise ValueError("SIGNED_SOURCE_INSTALL_LOCK_FILENAME_INVALID")
    source_install_lock = manifest_path.parent / lock_filename
    if not source_install_lock.is_file():
        raise ValueError("SIGNED_SOURCE_INSTALL_LOCK_MISSING")
    expected_lock_text = f"{PACKAGE}=={SOURCE_VERSION} --hash=sha256:{wheel_digest}\n"
    source_lock_bytes = source_install_lock.read_bytes()
    if (
        source_lock_bytes.decode("utf-8") != expected_lock_text
        or sha256_bytes(source_lock_bytes) != manifest.get("install_lock_sha256")
    ):
        raise ValueError("SIGNED_SOURCE_INSTALL_LOCK_MISMATCH")
    return wheel_digest, manifest


def create_override_locks(
    source_lock: Path,
    replacement_wheel: Path,
    source_manifest: Path,
    download_lock: Path,
    install_lock: Path,
    report_path: Path,
) -> dict[str, Any]:
    wheel_digest, manifest = validate_signed_candidate(replacement_wheel, source_manifest)
    prefix, blocks = package_blocks(source_lock.read_text(encoding="utf-8-sig"))
    matching = [block for block in blocks if block["name"] == PACKAGE]
    if len(matching) != 1:
        raise ValueError("SOURCE_LOCK_SETuptools_PIN_CARDINALITY_INVALID")
    target = matching[0]
    if target["version"] != EXPECTED_SOURCE_LOCK_VERSION:
        raise ValueError(f"SOURCE_LOCK_SETuptools_VERSION_UNEXPECTED:{target['version']}")

    download_blocks = [block["lines"] for block in blocks if block["name"] != PACKAGE]
    install_blocks = [
        [f"{PACKAGE}=={SOURCE_VERSION} --hash=sha256:{wheel_digest}"]
        if block["name"] == PACKAGE else block["lines"]
        for block in blocks
    ]
    download_text = "\n".join(prefix + [line for block in download_blocks for line in block]).rstrip() + "\n"
    install_text = "\n".join(prefix + [line for block in install_blocks for line in block]).rstrip() + "\n"
    if download_lock.exists() or install_lock.exists() or report_path.exists():
        raise ValueError("OVERRIDE_LOCK_OUTPUT_ALREADY_EXISTS")

    for destination, data in (
        (download_lock, download_text.encode("utf-8")),
        (install_lock, install_text.encode("utf-8")),
    ):
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(destination)

    download_names = [block["name"] for block in blocks if block["name"] != PACKAGE]
    report = {
        "schema": "forexai.provider_source_override_locks.v1",
        "status": "SIGNED_SOURCE_SETuptools_OVERRIDE_LOCKS_GENERATED_NOT_APPROVED",
        "source_lock_filename": source_lock.name,
        "source_lock_sha256": sha256_file(source_lock),
        "source_pin_replaced": f"{PACKAGE}=={target['version']}",
        "replacement_pin": f"{PACKAGE}=={SOURCE_VERSION}",
        "replacement_wheel_filename": replacement_wheel.name,
        "replacement_wheel_sha256": wheel_digest,
        "replacement_source_repository": manifest["source"]["repository"],
        "replacement_source_commit": manifest["source"]["commit"],
        "replacement_source_commit_signature_verified": True,
        "replacement_source_release_tag": manifest["source"]["release_tag"],
        "replacement_source_release_tag_signature_verified": True,
        "download_lock_filename": download_lock.name,
        "download_lock_sha256": sha256_file(download_lock),
        "download_lock_package_count": len(download_names),
        "install_lock_filename": install_lock.name,
        "install_lock_sha256": sha256_file(install_lock),
        "install_lock_package_count": len(blocks),
        "pypi_setuptools_wheel_excluded_from_download_lock": True,
        "source_built_wheel_hash_bound_into_install_lock": True,
        "production_approved": False,
        "bootstrap_approved": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", required=True, type=Path)
    parser.add_argument("--replacement-wheel", required=True, type=Path)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--download-lock", required=True, type=Path)
    parser.add_argument("--install-lock", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = create_override_locks(
            args.source_lock.resolve(),
            args.replacement_wheel.resolve(),
            args.source_manifest.resolve(),
            args.download_lock.resolve(),
            args.install_lock.resolve(),
            args.report.resolve(),
        )
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        print(f"SOURCE_OVERRIDE_LOCK_GENERATION=BLOCKED:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
