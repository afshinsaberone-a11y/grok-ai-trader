#!/usr/bin/env python3
"""Build untrusted, source-pinned Provider dependency wheel candidates.

This tool never authorizes a production install. Its output manifest records upstream
commit identity, GitHub commit-signature status, wheel digests and build-tool versions.
Unsigned upstream commits remain explicit human-review blockers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
from email.parser import Parser
from pathlib import Path
from typing import Any

SOURCE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "name": "pycparser",
        "version": "3.12",
        "repository": "eliben/pycparser",
        "git_url": "https://github.com/eliben/pycparser.git",
        "commit": "3ec766b7cd94724cba714296509604597ea4ce4e",
        "expected_signature_verified": False,
        "build_backend": "setuptools.build_meta",
        "license": "BSD-3-Clause",
    },
    {
        "name": "cffi",
        "version": "2.1.1",
        "repository": "python-cffi/cffi",
        "git_url": "https://github.com/python-cffi/cffi.git",
        "commit": "fd33e7700f0ebafe6f30bd5053f13327221b77a2",
        "expected_signature_verified": True,
        "build_backend": "setuptools.build_meta",
        "license": "MIT-0",
    },
    {
        "name": "colorama",
        "version": "0.4.6",
        "repository": "tartley/colorama",
        "git_url": "https://github.com/tartley/colorama.git",
        "commit": "3de9f013df4b470069d03d250224062e8cf15c49",
        "expected_signature_verified": False,
        "build_backend": "hatchling.build",
        "license": "BSD-3-Clause",
    },
    {
        "name": "pygments",
        "version": "2.21.0",
        "repository": "pygments/pygments",
        "git_url": "https://github.com/pygments/pygments.git",
        "commit": "a43b45dcf081b6010c6ab4428f149f7f6d2499c4",
        "expected_signature_verified": False,
        "build_backend": "hatchling.build",
        "license": "BSD-2-Clause",
    },
)

MANIFEST_SCHEMA = "forexai.provider_source_built_wheel_candidate.v1"
CANDIDATE_ONLY_STATUS = "SOURCE_BUILD_CANDIDATE_NOT_APPROVED"
BUILD_TOOL_LOCK_FILENAME = "requirements-provider-source-build-tools.lock.txt"
EXPECTED_BUILD_TOOL_PINS = {
    "hatchling": "1.27.0",
    "packaging": "26.3",
    "pathspec": "1.1.1",
    "pip": "26.2.2",
    "pluggy": "1.7.0",
    "setuptools": "80.9.0",
    "trove-classifiers": "2026.9.21.13",
    "wheel": "0.45.1",
}


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def github_commit_metadata(repository: str, commit: str) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repository}/commits/{commit}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ForexAI-Provider-Source-Wheel-Candidate/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GITHUB_SOURCE_METADATA_LOOKUP_FAILED:{repository}") from exc

    returned_sha = payload.get("sha")
    verification = payload.get("commit", {}).get("verification", {})
    if returned_sha != commit or not isinstance(verification.get("verified"), bool):
        raise RuntimeError(f"GITHUB_SOURCE_METADATA_INVALID:{repository}")

    verified = verification["verified"]
    reason = str(verification.get("reason") or "unknown")
    spec = next(item for item in SOURCE_SPECS if item["repository"] == repository)
    if verified is not spec["expected_signature_verified"]:
        raise RuntimeError(f"UPSTREAM_COMMIT_SIGNATURE_STATUS_CHANGED:{repository}")

    return {
        "repository": repository,
        "commit": commit,
        "github_api_commit_sha_matches": True,
        "github_commit_signature_verified": verified,
        "github_commit_signature_reason": reason,
        "upstream_signature_policy": (
            "SIGNED_COMMIT_VERIFIED"
            if verified
            else "UNSIGNED_COMMIT_REQUIRES_INDEPENDENT_SOURCE_REVIEW"
        ),
    }


def wheel_metadata(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        candidates = [
            name for name in archive.namelist()
            if name.endswith(".dist-info/METADATA") and name.count("/") == 1
        ]
        if len(candidates) != 1:
            raise RuntimeError(f"WHEEL_METADATA_CARDINALITY_INVALID:{path.name}")
        metadata = Parser().parsestr(archive.read(candidates[0]).decode("utf-8"))
    name, version = metadata.get("Name"), metadata.get("Version")
    if not name or not version:
        raise RuntimeError(f"WHEEL_METADATA_MISSING:{path.name}")
    canonical_name = re.sub(r"[-_.]+", "-", name).lower()
    return canonical_name, version


def clone_exact_source(spec: dict[str, Any], source_root: Path) -> tuple[Path, dict[str, Any]]:
    directory = source_root / spec["name"]
    if directory.exists():
        raise RuntimeError(f"SOURCE_DESTINATION_ALREADY_EXISTS:{spec['name']}")
    directory.mkdir(parents=True, exist_ok=False)
    run(["git", "init", "--quiet", str(directory)])
    run(["git", "-C", str(directory), "remote", "add", "origin", spec["git_url"]])
    run(
        [
            "git", "-C", str(directory), "fetch", "--quiet",
            "--depth=1", "origin", spec["commit"],
        ]
    )
    run(["git", "-C", str(directory), "checkout", "--quiet", "--detach", "FETCH_HEAD"])
    actual = run(["git", "-C", str(directory), "rev-parse", "HEAD"])
    if actual != spec["commit"]:
        raise RuntimeError(f"CHECKED_OUT_SOURCE_SHA_MISMATCH:{spec['name']}")
    if run(["git", "-C", str(directory), "status", "--porcelain=v1"]):
        raise RuntimeError(f"SOURCE_CHECKOUT_NOT_CLEAN:{spec['name']}")
    source_metadata = github_commit_metadata(spec["repository"], spec["commit"])
    return directory, source_metadata


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

    build_tool_lock = workspace / BUILD_TOOL_LOCK_FILENAME
    if not build_tool_lock.is_file():
        raise RuntimeError("SOURCE_BUILD_TOOL_LOCK_MISSING")
    build_tool_lock_text = build_tool_lock.read_text(encoding="utf-8")
    lock_pins = {
        re.sub(r"[-_.]+", "-", name).lower(): version
        for name, version in re.findall(
            r"(?m)^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\\s\\\\]+)\\s*\\\\?\\s*$",
            build_tool_lock_text,
        )
    }
    if lock_pins != EXPECTED_BUILD_TOOL_PINS:
        raise RuntimeError("SOURCE_BUILD_TOOL_LOCK_PINS_MISMATCH")
    lock_hash_count = len(re.findall(r"--hash=sha256:[0-9a-f]{64}", build_tool_lock_text))
    if lock_hash_count != len(EXPECTED_BUILD_TOOL_PINS):
        raise RuntimeError("SOURCE_BUILD_TOOL_LOCK_HASH_COUNT_MISMATCH")
    build_tool_lock_sha256 = sha256_file(build_tool_lock)

    build_tool_freeze = run([str(builder_python), "-m", "pip", "freeze", "--all"])
    actual_build_tool_pins = sorted(line.strip() for line in build_tool_freeze.splitlines() if line.strip())
    expected_build_tool_freeze = sorted(
        f"{name}=={version}" for name, version in EXPECTED_BUILD_TOOL_PINS.items()
    )
    if actual_build_tool_pins != expected_build_tool_freeze:
        raise RuntimeError("SOURCE_BUILD_TOOL_FREEZE_MISMATCH")

    source_root = output_root / "sources"
    wheel_root = output_root / "wheels"
    source_root.mkdir(parents=True, exist_ok=False)
    wheel_root.mkdir(parents=True, exist_ok=False)
    wheel_records: list[dict[str, Any]] = []
    unsigned_sources: list[str] = []

    # The source list is deliberately fixed in this script; callers cannot select
    # an arbitrary source repository, branch, tag, package name or commit.
    for spec in SOURCE_SPECS:
        source_dir, source_metadata = clone_exact_source(spec, source_root)
        if not source_metadata["github_commit_signature_verified"]:
            unsigned_sources.append(spec["name"])

        before = {item.name for item in wheel_root.glob("*.whl")}
        run(
            [
                str(builder_python), "-m", "pip", "wheel",
                "--disable-pip-version-check",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir", str(wheel_root),
                ".",
            ],
            cwd=source_dir,
        )
        created = [item for item in wheel_root.glob("*.whl") if item.name not in before]
        if len(created) != 1:
            raise RuntimeError(f"EXPECTED_EXACTLY_ONE_NEW_WHEEL:{spec['name']}")
        wheel = created[0]
        actual_name, actual_version = wheel_metadata(wheel)
        if actual_name != spec["name"] or actual_version != spec["version"]:
            raise RuntimeError(f"WHEEL_NAME_OR_VERSION_MISMATCH:{spec['name']}")
        wheel_records.append(
            {
                "package": spec["name"],
                "version": spec["version"],
                "filename": wheel.name,
                "sha256": sha256_file(wheel),
                "build_backend": spec["build_backend"],
                "license": spec["license"],
                "source": source_metadata,
            }
        )

    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": CANDIDATE_ONLY_STATUS,
        "production_approved": False,
        "bootstrap_approved": False,
        "policy": (
            "This GitHub Actions attestation binds the wheel digests to this build workflow "
            "and the exact upstream commit identifiers listed below. It does not establish "
            "that unsigned upstream source is trustworthy. Independent source review and "
            "a separately reviewed bootstrap integration remain mandatory."
        ),
        "target": {
            "runner": "windows-2022",
            "python": run([str(builder_python), "-c", "import platform,sys; print(platform.python_version())"]),
            "architecture": "x86_64",
        },
        "build_tools": {
            "direct_pins_expected": {
                "setuptools": "80.9.0",
                "wheel": "0.45.1",
                "hatchling": "1.27.0",
            },
            "pip_freeze_all": build_tool_freeze.splitlines(),
            "lockfile": BUILD_TOOL_LOCK_FILENAME,
            "lockfile_sha256": build_tool_lock_sha256,
            "locked_package_pins": dict(sorted(EXPECTED_BUILD_TOOL_PINS.items())),
            "transitive_build_tool_dependencies_hash_locked": True,
            "packages_without_verified_pypi_provenance": ["setuptools==80.9.0"],
            "review_required": True,
        },
        "upstream_sources_with_unverified_commit_signatures": unsigned_sources,
        "wheels": wheel_records,
    }
    manifest_path = output_root / "source-build-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"SOURCE_WHEEL_CANDIDATE_STATUS={CANDIDATE_ONLY_STATUS}")
    print(f"SOURCE_WHEEL_COUNT={len(wheel_records)}")
    print(f"UNSIGNED_UPSTREAM_SOURCE_COUNT={len(unsigned_sources)}")
    for wheel in wheel_records:
        print(f"SOURCE_WHEEL={wheel['filename']}")
        print(f"SOURCE_WHEEL_SHA256={wheel['sha256']}")
        print(
            "UPSTREAM_SIGNATURE="
            + wheel["package"]
            + ":"
            + wheel["source"]["upstream_signature_policy"]
        )
    print(f"SOURCE_WHEEL_MANIFEST={manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError, urllib.error.URLError) as exc:
        print(f"SOURCE_WHEEL_CANDIDATE_BLOCKED={type(exc).__name__}:{exc}", file=sys.stderr)
        raise SystemExit(1)
