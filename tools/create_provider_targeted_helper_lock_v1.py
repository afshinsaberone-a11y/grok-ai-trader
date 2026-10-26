#!/usr/bin/env python3
"""Create a target-specific hash lock from exact wheels downloaded for this runner."""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

from packaging.utils import canonicalize_name, parse_wheel_filename

PIN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)(?:\s|\\|$)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_locked_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    package_blocks: dict[str, list[str]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        match = PIN.match(raw)
        if match:
            name = canonicalize_name(match.group(1))
            version = match.group(2)
            if name in pins:
                raise ValueError(f"DUPLICATE_LOCK_PIN:{name}")
            pins[name] = version
            package_blocks[name] = []
            current = name
            continue
        stripped = raw.strip()
        if stripped.startswith("--hash=sha256:") and current:
            package_blocks[current].append(stripped)
        elif stripped and not stripped.startswith("#") and not stripped.startswith("--"):
            current = None
    if not pins:
        raise ValueError("LOCK_CONTAINS_NO_EXACT_PINS")
    for name, hashes in package_blocks.items():
        if not hashes or any(not re.fullmatch(r"--hash=sha256:[0-9a-f]{64}", h) for h in hashes):
            raise ValueError(f"LOCK_PACKAGE_HASH_MISSING_OR_INVALID:{name}")
    return pins


def build_target_lock(requirements: Path, wheelhouse: Path, output: Path, target_label: str) -> dict:
    pins = read_locked_pins(requirements)
    if not wheelhouse.is_dir():
        raise ValueError("WHEELHOUSE_NOT_FOUND")
    wheels = sorted(wheelhouse.glob("*.whl"))
    found: dict[str, tuple[str, Path]] = {}
    for wheel in wheels:
        try:
            name, version, _build, _tags = parse_wheel_filename(wheel.name)
        except Exception as exc:
            raise ValueError(f"INVALID_WHEEL_FILENAME:{wheel.name}") from exc
        normalized = canonicalize_name(str(name))
        if normalized in found:
            raise ValueError(f"DUPLICATE_WHEEL_FOR_PACKAGE:{normalized}")
        found[normalized] = (str(version), wheel)

    if set(found) != set(pins):
        missing = sorted(set(pins) - set(found))
        extra = sorted(set(found) - set(pins))
        raise ValueError(f"WHEEL_PACKAGE_SET_MISMATCH:missing={missing};extra={extra}")
    rows = []
    for name in sorted(pins):
        locked_version = pins[name]
        wheel_version, wheel = found[name]
        if wheel_version != locked_version:
            raise ValueError(f"WHEEL_VERSION_MISMATCH:{name}:{wheel_version}!={locked_version}")
        digest = sha256(wheel)
        rows.append((name, locked_version, digest))

    source_hash = sha256(requirements)
    output.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "# schema: forexai.provider_targeted_helper_lock.v1\n"
        f"# target: {target_label}\n"
        f"# source_candidate_lock_sha256: {source_hash}\n"
        "# each pin hashes the exact compatible wheel downloaded and tested in the candidate workflow\n"
        + "".join(f"{name}=={version} --hash=sha256:{digest}\n" for name, version, digest in rows)
    )
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(output)
    return {
        "schema": "forexai.provider_targeted_helper_lock.v1",
        "status": "TARGET_WHEEL_HASHES_PINNED",
        "target": target_label,
        "source_candidate_lock_sha256": source_hash,
        "target_lock_file": output.name,
        "target_lock_sha256": sha256(output),
        "pinned_requirement_count": len(rows),
        "wheel_file_count": len(wheels),
        "all_exact_versions_matched": True,
        "all_wheel_hashes_sha256": True,
        "production_approved": False,
        "bootstrap_approved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", required=True, type=Path)
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--target-label", required=True)
    args = parser.parse_args()
    try:
        print(__import__("json").dumps(
            build_target_lock(args.requirements, args.wheelhouse, args.output, args.target_label),
            sort_keys=True,
        ))
    except (OSError, ValueError) as exc:
        print(f"TARGET_HELPER_LOCK_FAILED:{exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
