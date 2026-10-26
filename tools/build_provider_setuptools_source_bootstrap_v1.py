#!/usr/bin/env python3
"""Build setuptools from an exact GitHub-signature-verified upstream release.

The generated wheel is a candidate bootstrap tool, not a Provider deployment
artifact. The PyPI setuptools wheel is deliberately not installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Any

REPOSITORY = "pypa/setuptools"
GIT_URL = "https://github.com/pypa/setuptools.git"
VERSION = "80.9.0"
RELEASE_TAG = "v80.9.0"
COMMIT = "9c4d383631d3951fcae0afd73b5d08ff5a262976"
TAG_OBJECT_SHA = "ef921af5f4374a66c018304a2aa5306cb67962a0"
PACKAGE_NAME = "setuptools"
MANIFEST_SCHEMA = "forexai.provider_setuptools_source_bootstrap.v1"
STATUS = "SIGNED_SOURCE_BUILD_CANDIDATE_NOT_APPROVED"


def run(command: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ForexAI-Setuptools-Source-Bootstrap/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GITHUB_SOURCE_IDENTITY_LOOKUP_FAILED:{url}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("GITHUB_SOURCE_IDENTITY_PAYLOAD_INVALID")
    return payload


def validate_source_identity(
    commit_payload: dict[str, Any],
    tag_ref_payload: dict[str, Any],
    tag_payload: dict[str, Any],
) -> dict[str, Any]:
    if commit_payload.get("sha") != COMMIT:
        raise RuntimeError("SETUPTOOLS_COMMIT_SHA_MISMATCH")
    commit_verification = commit_payload.get("commit", {}).get("verification", {})
    if (
        commit_verification.get("verified") is not True
        or commit_verification.get("reason") != "valid"
    ):
        raise RuntimeError("SETUPTOOLS_COMMIT_SIGNATURE_NOT_VERIFIED")

    if tag_ref_payload.get("ref") != f"refs/tags/{RELEASE_TAG}":
        raise RuntimeError("SETUPTOOLS_RELEASE_TAG_REF_MISMATCH")
    tag_ref_object = tag_ref_payload.get("object", {})
    if (
        tag_ref_object.get("type") != "tag"
        or tag_ref_object.get("sha") != TAG_OBJECT_SHA
    ):
        raise RuntimeError("SETUPTOOLS_RELEASE_TAG_OBJECT_MISMATCH")

    tag_verification = tag_payload.get("verification", {})
    tag_target = tag_payload.get("object", {})
    if (
        tag_payload.get("sha") != TAG_OBJECT_SHA
        or tag_payload.get("tag") != RELEASE_TAG
        or tag_target.get("type") != "commit"
        or tag_target.get("sha") != COMMIT
    ):
        raise RuntimeError("SETUPTOOLS_RELEASE_TAG_TARGET_MISMATCH")
    if (
        tag_verification.get("verified") is not True
        or tag_verification.get("reason") != "valid"
    ):
        raise RuntimeError("SETUPTOOLS_RELEASE_TAG_SIGNATURE_NOT_VERIFIED")

    return {
        "repository": REPOSITORY,
        "git_url": GIT_URL,
        "commit": COMMIT,
        "github_commit_signature_verified": True,
        "github_commit_signature_reason": commit_verification.get("reason"),
        "release_tag": RELEASE_TAG,
        "release_tag_object_sha": TAG_OBJECT_SHA,
        "github_release_tag_signature_verified": True,
        "github_release_tag_signature_reason": tag_verification.get("reason"),
        "release_tag_target_commit": COMMIT,
    }


def get_verified_source_identity() -> dict[str, Any]:
    # Verify source identity before running any code from the source checkout.
    commit_payload = get_json(f"https://api.github.com/repos/{REPOSITORY}/commits/{COMMIT}")
    tag_ref_payload = get_json(
        f"https://api.github.com/repos/{REPOSITORY}/git/ref/tags/"
        + urllib.parse.quote(RELEASE_TAG, safe="")
    )
    tag_payload = get_json(
        f"https://api.github.com/repos/{REPOSITORY}/git/tags/{TAG_OBJECT_SHA}"
    )
    return validate_source_identity(commit_payload, tag_ref_payload, tag_payload)


def wheel_metadata(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        candidates = [
            item for item in archive.namelist()
            if item.endswith(".dist-info/METADATA") and item.count("/") == 1
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"WHEEL_METADATA_CARDINALITY_INVALID:{path.name}")
        metadata = Parser().parsestr(archive.read(candidates[0]).decode("utf-8"))
    name, version = metadata.get("Name"), metadata.get("Version")
    if not name or not version:
        raise RuntimeError(f"WHEEL_METADATA_MISSING:{path.name}")
    canonical_name = re.sub(r"[-_.]+", "-", name).lower()
    return canonical_name, version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--builder-python", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    builder_python = args.builder_python.resolve()
    output_root = args.output_root.resolve()
    if not workspace.is_dir():
        raise RuntimeError("WORKSPACE_NOT_FOUND")
    if not builder_python.is_file():
        raise RuntimeError("BUILDER_PYTHON_NOT_FOUND")
    if output_root == workspace or workspace not in output_root.parents:
        raise RuntimeError("OUTPUT_ROOT_MUST_BE_A_NEW_WORKSPACE_CHILD")
    if output_root.exists():
        raise RuntimeError("OUTPUT_ROOT_ALREADY_EXISTS_INSPECT_BEFORE_RETRY")

    source_identity = get_verified_source_identity()

    probe_code = (
        "import importlib.metadata\n"
        "try:\n"
        " importlib.metadata.version('setuptools')\n"
        " print('SETUPTOOLS_PRESENT')\n"
        "except importlib.metadata.PackageNotFoundError:\n"
        " print('SETUPTOOLS_ABSENT')\n"
    )
    probe = subprocess.run(
        [str(builder_python), "-c", probe_code],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if probe.returncode != 0 or probe.stdout.strip() != "SETUPTOOLS_ABSENT":
        raise RuntimeError("SETUPTOOLS_BOOTSTRAP_ENVIRONMENT_NOT_CLEAN")

    output_root.mkdir(parents=True, exist_ok=False)
    source_dir = output_root / "source"
    wheel_dir = output_root / "wheels"
    source_dir.mkdir(parents=True, exist_ok=False)
    wheel_dir.mkdir(parents=True, exist_ok=False)

    run(["git", "init", "--quiet", str(source_dir)])
    run(["git", "-C", str(source_dir), "remote", "add", "origin", GIT_URL])
    run([
        "git", "-C", str(source_dir), "fetch", "--quiet",
        "--depth=1", "origin", COMMIT,
    ])
    run(["git", "-C", str(source_dir), "checkout", "--quiet", "--detach", "FETCH_HEAD"])
    checked_out = run(["git", "-C", str(source_dir), "rev-parse", "HEAD"])
    if checked_out != COMMIT:
        raise RuntimeError("SETUPTOOLS_CHECKED_OUT_COMMIT_MISMATCH")
    if run(["git", "-C", str(source_dir), "status", "--porcelain=v1"]):
        raise RuntimeError("SETUPTOOLS_SOURCE_CHECKOUT_NOT_CLEAN")

    wheel_builder_version = run([
        str(builder_python), "-c",
        "import importlib.metadata; print(importlib.metadata.version('wheel'))",
    ])
    run([
        str(builder_python), "-m", "pip", "wheel",
        "--disable-pip-version-check",
        "--no-deps",
        "--no-build-isolation",
        "--wheel-dir", str(wheel_dir),
        ".",
    ], cwd=source_dir)

    wheels = sorted(wheel_dir.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"SETUPTOOLS_EXPECTED_ONE_WHEEL:GOT={len(wheels)}")
    wheel = wheels[0]
    name, version = wheel_metadata(wheel)
    if name != PACKAGE_NAME or version != VERSION:
        raise RuntimeError(f"SETUPTOOLS_WHEEL_NAME_VERSION_MISMATCH:{name}=={version}")
    expected_filename = "setuptools-80.9.0-py3-none-any.whl"
    if wheel.name != expected_filename:
        raise RuntimeError(f"SETUPTOOLS_WHEEL_FILENAME_MISMATCH:{wheel.name}")

    wheel_digest = sha256_file(wheel)
    install_lock_text = f"setuptools=={VERSION} --hash=sha256:{wheel_digest}\n"
    install_lock = output_root / "requirements-provider-setuptools-bootstrap.lock.txt"
    install_lock.write_text(install_lock_text, encoding="utf-8", newline="\n")
    install_lock_digest = sha256_bytes(install_lock_text.encode("utf-8"))

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": STATUS,
        "production_approved": False,
        "bootstrap_approved": False,
        "policy": (
            "The PyPI setuptools wheel is not installed. This wheel is built from the "
            "exact upstream commit and annotated release tag whose GitHub signature "
            "statuses were verified before source execution. The wheel is still a "
            "candidate requiring attestation verification and independent review."
        ),
        "package_name": PACKAGE_NAME,
        "version": VERSION,
        "wheel_filename": wheel.name,
        "wheel_sha256": wheel_digest,
        "install_lock_filename": install_lock.name,
        "install_lock_sha256": install_lock_digest,
        "source": source_identity,
        "build": {
            "python": run([
                str(builder_python), "-c",
                "import platform; print(platform.python_version())",
            ]),
            "wheel_builder_version": wheel_builder_version,
            "builder_environment_had_no_installed_setuptools": True,
            "build_isolation": False,
            "backend_path_policy": "Use the pinned source tree's pyproject backend-path",
            "source_checkout_commit": checked_out,
            "source_checkout_clean_before_build": True,
        },
    }
    manifest_path = output_root / "setuptools-bootstrap-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("SETUPTOOLS_SOURCE_COMMIT_SIGNATURE=PASS")
    print("SETUPTOOLS_RELEASE_TAG_SIGNATURE=PASS")
    print("SETUPTOOLS_BOOTSTRAP_WHEEL=" + wheel.name)
    print("SETUPTOOLS_BOOTSTRAP_WHEEL_SHA256=" + wheel_digest)
    print("SETUPTOOLS_BOOTSTRAP_INSTALL_LOCK_SHA256=" + install_lock_digest)
    print("SETUPTOOLS_BOOTSTRAP_APPROVED=false")
    print("SETUPTOOLS_BOOTSTRAP_MANIFEST=" + str(manifest_path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError, urllib.error.URLError) as exc:
        print(f"SETUPTOOLS_SOURCE_BOOTSTRAP_BLOCKED={type(exc).__name__}:{exc}", file=sys.stderr)
        raise SystemExit(1)
