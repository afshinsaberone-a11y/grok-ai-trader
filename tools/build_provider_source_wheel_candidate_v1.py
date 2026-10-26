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
import urllib.parse
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
        "release_tag": "release_v3.12",
        "expected_tag_object_type": "commit",
        "expected_tag_object_sha": "3ec766b7cd94724cba714296509604597ea4ce4e",
        "expected_release_tag_signature_verified": False,
        "expected_signature_verified": False,
        "expected_unsigned_commit_files": ["MANIFEST.in", "pyproject.toml"],
        "expected_unsigned_file_evidence": {
            "MANIFEST.in": {
                "blob_sha": "ef517eea61d10638710ef60966f9086b2daabf15",
                "patch_sha256": "333edb449017ef2ef0c33a8070bb043b82c7b5850edd38274a78c4806d6a99d4",
            },
            "pyproject.toml": {
                "blob_sha": "24577fc9b72034c7a1c8457f17d042c7c72d6b43",
                "patch_sha256": "71b313c81728f97c4e59929d225dfb6d6ae410b6aaad846d6939bab1c3c6abba",
            },
        },
        "build_backend": "setuptools.build_meta",
        "license": "BSD-3-Clause",
    },
    {
        "name": "cffi",
        "version": "2.1.1",
        "repository": "python-cffi/cffi",
        "git_url": "https://github.com/python-cffi/cffi.git",
        "commit": "fd33e7700f0ebafe6f30bd5053f13327221b77a2",
        "release_tag": "v2.1.1",
        "expected_tag_object_type": "commit",
        "expected_tag_object_sha": "fd33e7700f0ebafe6f30bd5053f13327221b77a2",
        "expected_release_tag_signature_verified": False,
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
        "release_tag": "0.4.6",
        "expected_tag_object_type": "tag",
        "expected_tag_object_sha": "4ea8b1c7cbf96cc21613bb51b38fc49831fdddb4",
        "expected_release_tag_signature_verified": False,
        "expected_signature_verified": False,
        "expected_unsigned_commit_files": ["README-hacking.md", "colorama/__init__.py"],
        "expected_unsigned_file_evidence": {
            "README-hacking.md": {
                "blob_sha": "324f29d24781161694a634648f9a5e8676ba79de",
                "patch_sha256": "2ed501e893f0eea9aab612c721bd57e706e3b295dff8fe4e85f76fff9324e5dd",
            },
            "colorama/__init__.py": {
                "blob_sha": "383101cdb38706c305449674044e9288b92b7d75",
                "patch_sha256": "673579f502a4527f94a3aab94922a1aec8e93742729b58779a0bcb80c2612ed2",
            },
        },
        "build_backend": "hatchling.build",
        "license": "BSD-3-Clause",
    },
    {
        "name": "pygments",
        "version": "2.21.0",
        "repository": "pygments/pygments",
        "git_url": "https://github.com/pygments/pygments.git",
        "commit": "a43b45dcf081b6010c6ab4428f149f7f6d2499c4",
        "release_tag": "2.21.0",
        "expected_tag_object_type": "tag",
        "expected_tag_object_sha": "2ade8335807203e11d67effb4108c78672519f0d",
        "expected_release_tag_signature_verified": False,
        "expected_signature_verified": False,
        "expected_unsigned_commit_files": ["CHANGES", "pygments/__init__.py"],
        "expected_unsigned_file_evidence": {
            "CHANGES": {
                "blob_sha": "5c18a8ea2e51bc7c0314726d1d4ca46b100a6cad",
                "patch_sha256": "2f342a7fa0d530fc32069338d755a16d5f77437ff673ba5abda005bd7fea5d9e",
            },
            "pygments/__init__.py": {
                "blob_sha": "1d41b0a400d23fa0216c17e45de2a3de0c9f8e12",
                "patch_sha256": "5569e50fb8ff799d46e6c5edd7f76b448289cca76d7a3906ed7e6f053aca304b",
            },
        },
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

    commit_files = payload.get("files")
    if not isinstance(commit_files, list) or not commit_files:
        raise RuntimeError(f"GITHUB_SOURCE_COMMIT_FILE_LIST_MISSING:{repository}")
    changed_files: list[str] = []
    file_entries: dict[str, dict[str, Any]] = {}
    for entry in commit_files:
        if not isinstance(entry, dict) or not isinstance(entry.get("filename"), str):
            raise RuntimeError(f"GITHUB_SOURCE_COMMIT_FILE_LIST_INVALID:{repository}")
        filename = entry["filename"]
        if filename in file_entries:
            raise RuntimeError(f"GITHUB_SOURCE_COMMIT_FILE_LIST_DUPLICATE:{repository}")
        changed_files.append(filename)
        file_entries[filename] = entry
    changed_files.sort()

    # Filename allowlisting alone is not enough: build configuration (notably
    # pyproject.toml) can change executed build behavior. For unsigned release
    # commits, pin both the exact Git blob SHA and exact GitHub patch SHA-256.
    unsigned_patch_hashes_match: bool | None = None
    unsigned_file_evidence: dict[str, dict[str, str]] = {}
    expected_unsigned_files = spec.get("expected_unsigned_commit_files")
    if not verified:
        expected_file_evidence = spec.get("expected_unsigned_file_evidence")
        if not isinstance(expected_unsigned_files, list) or not expected_unsigned_files:
            raise RuntimeError(f"UNSIGNED_COMMIT_ALLOWLIST_MISSING:{repository}")
        if changed_files != sorted(expected_unsigned_files):
            raise RuntimeError(f"UNSIGNED_UPSTREAM_COMMIT_CHANGED_UNREVIEWED_FILES:{repository}")
        if (
            not isinstance(expected_file_evidence, dict)
            or set(expected_file_evidence) != set(expected_unsigned_files)
        ):
            raise RuntimeError(f"UNSIGNED_COMMIT_FILE_EVIDENCE_ALLOWLIST_INVALID:{repository}")

        for filename in changed_files:
            entry = file_entries[filename]
            expected = expected_file_evidence[filename]
            if entry.get("status") != "modified":
                raise RuntimeError(f"UNSIGNED_UPSTREAM_FILE_STATUS_MISMATCH:{repository}:{filename}")
            if entry.get("sha") != expected.get("blob_sha"):
                raise RuntimeError(f"UNSIGNED_UPSTREAM_FILE_BLOB_MISMATCH:{repository}:{filename}")
            patch = entry.get("patch")
            if not isinstance(patch, str) or not patch:
                raise RuntimeError(f"UNSIGNED_UPSTREAM_FILE_PATCH_MISSING:{repository}:{filename}")
            patch_sha256 = hashlib.sha256(patch.encode("utf-8")).hexdigest()
            if patch_sha256 != expected.get("patch_sha256"):
                raise RuntimeError(f"UNSIGNED_UPSTREAM_FILE_PATCH_MISMATCH:{repository}:{filename}")
            unsigned_file_evidence[filename] = {
                "status": entry["status"],
                "blob_sha": entry["sha"],
                "patch_sha256": patch_sha256,
            }
        unsigned_patch_hashes_match = True

    return {
        "repository": repository,
        "commit": commit,
        "github_api_commit_sha_matches": True,
        "github_commit_changed_files": changed_files,
        "unsigned_commit_changed_files_match_allowlist": (
            changed_files == sorted(expected_unsigned_files) if not verified else None
        ),
        "unsigned_commit_patch_hashes_match": unsigned_patch_hashes_match,
        "unsigned_commit_file_evidence": unsigned_file_evidence,
        "expected_unsigned_commit_files": expected_unsigned_files if not verified else [],
        "github_commit_signature_verified": verified,
        "github_commit_signature_reason": reason,
        "upstream_signature_policy": (
            "SIGNED_COMMIT_VERIFIED"
            if verified
            else "UNSIGNED_RELEASE_DIFF_EXACT_PATCH_HASHES_REQUIRE_INDEPENDENT_SOURCE_REVIEW"
        ),
    }


def github_release_tag_metadata(spec: dict[str, Any]) -> dict[str, Any]:
    """Verify that the upstream release ref still points to the pinned source commit.

    A signed tag is useful source evidence, but a lightweight tag has no separate
    signature. In that case the pinned commit's GitHub signature status remains
    the independent signature signal; unsigned refs stay explicitly review-blocked.
    """
    repository = spec["repository"]
    tag_name = spec["release_tag"]
    ref_url = (
        f"https://api.github.com/repos/{repository}/git/ref/tags/"
        f"{urllib.parse.quote(tag_name, safe='')}"
    )
    request = urllib.request.Request(
        ref_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "ForexAI-Provider-Source-Wheel-Candidate/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            ref_payload = json.loads(response.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GITHUB_RELEASE_TAG_LOOKUP_FAILED:{repository}:{tag_name}") from exc

    expected_ref = f"refs/tags/{tag_name}"
    tag_object = ref_payload.get("object", {})
    if (
        ref_payload.get("ref") != expected_ref
        or tag_object.get("type") != spec["expected_tag_object_type"]
        or tag_object.get("sha") != spec["expected_tag_object_sha"]
    ):
        raise RuntimeError(f"UPSTREAM_RELEASE_TAG_REF_CHANGED:{repository}:{tag_name}")

    tag_signature_verified = False
    tag_signature_reason = "lightweight_tag_has_no_independent_tag_signature"
    target_commit = tag_object.get("sha")
    tag_object_sha = tag_object.get("sha")

    if tag_object.get("type") == "tag":
        tag_url = f"https://api.github.com/repos/{repository}/git/tags/{tag_object_sha}"
        tag_request = urllib.request.Request(
            tag_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "ForexAI-Provider-Source-Wheel-Candidate/1.0",
            },
        )
        try:
            with urllib.request.urlopen(tag_request, timeout=25) as response:
                tag_payload = json.loads(response.read().decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"GITHUB_RELEASE_TAG_OBJECT_LOOKUP_FAILED:{repository}:{tag_name}") from exc

        verification = tag_payload.get("verification", {})
        target = tag_payload.get("object", {})
        if (
            tag_payload.get("sha") != tag_object_sha
            or tag_payload.get("tag") != tag_name
            or target.get("type") != "commit"
            or not isinstance(verification.get("verified"), bool)
        ):
            raise RuntimeError(f"GITHUB_RELEASE_TAG_OBJECT_INVALID:{repository}:{tag_name}")
        target_commit = target.get("sha")
        tag_signature_verified = verification["verified"]
        tag_signature_reason = str(verification.get("reason") or "unknown")

    if target_commit != spec["commit"]:
        raise RuntimeError(f"UPSTREAM_RELEASE_TAG_TARGET_COMMIT_MISMATCH:{repository}:{tag_name}")
    if tag_signature_verified is not spec["expected_release_tag_signature_verified"]:
        raise RuntimeError(f"UPSTREAM_RELEASE_TAG_SIGNATURE_STATUS_CHANGED:{repository}:{tag_name}")

    return {
        "github_release_tag": tag_name,
        "github_release_tag_ref_sha": tag_object_sha,
        "github_release_tag_object_type": tag_object.get("type"),
        "github_release_tag_target_commit": target_commit,
        "github_release_tag_signature_verified": tag_signature_verified,
        "github_release_tag_signature_reason": tag_signature_reason,
        "upstream_release_identity_policy": (
            "SIGNED_RELEASE_TAG_VERIFIED"
            if tag_signature_verified
            else "UNSIGNED_RELEASE_TAG_REQUIRES_COMMIT_SIGNATURE_OR_INDEPENDENT_REVIEW"
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
    source_metadata.update(github_release_tag_metadata(spec))
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
            r"(?m)^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)\s*\\?\s*$",
            build_tool_lock_text,
        )
    }
    if lock_pins != EXPECTED_BUILD_TOOL_PINS:
        raise RuntimeError("SOURCE_BUILD_TOOL_LOCK_PINS_MISMATCH")
    lock_hash_count = len(re.findall(r"--hash=sha256:[0-9a-f]{64}", build_tool_lock_text))
    if lock_hash_count != len(EXPECTED_BUILD_TOOL_PINS):
        raise RuntimeError("SOURCE_BUILD_TOOL_LOCK_HASH_COUNT_MISMATCH")
    # Path.read_text uses universal-newline translation; hash canonical UTF-8/LF text
    # so Windows autocrlf settings cannot make the manifest digest platform-dependent.
    build_tool_lock_sha256 = hashlib.sha256(build_tool_lock_text.encode("utf-8")).hexdigest()

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
        "upstream_sources_without_verified_commit_or_signed_release_tag": sorted(
            wheel["package"]
            for wheel in wheel_records
            if not wheel["source"]["github_commit_signature_verified"]
            and not wheel["source"]["github_release_tag_signature_verified"]
        ),
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
