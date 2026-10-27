#!/usr/bin/env python3
"""Create a target-specific hash lock from an already-downloaded wheelhouse.

This utility deliberately does not discover versions or download packages. The
input lock determines exact versions; the wheelhouse supplies the precise wheel
bytes accepted by the target interpreter/platform. Missing, duplicate, or
mismatched wheels fail closed. The output is never overwritten, and any failed
validation occurs before a lock file is created.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

from packaging.utils import canonicalize_name, parse_wheel_filename

PIN_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([^\s\\]+)",
    re.MULTILINE,
)


def parse_pins(lock_path: Path) -> dict[str, tuple[str, str]]:
    pins: dict[str, tuple[str, str]] = {}
    for name, version in PIN_RE.findall(lock_path.read_text(encoding="utf-8-sig")):
        key = canonicalize_name(name)
        if key in pins:
            raise ValueError(f"DUPLICATE_PIN:{key}")
        pins[key] = (name, version)
    if not pins:
        raise ValueError("NO_EXACT_PINS_FOUND")
    return pins


def compact_lock(lock_path: Path, wheelhouse: Path, output_path: Path) -> None:
    # Refuse output reuse up front, including a broken symlink. Never overwrite
    # a previous result or a path an operator may need to inspect.
    if output_path.exists() or output_path.is_symlink():
        raise ValueError("OUTPUT_PATH_ALREADY_EXISTS")

    pins = parse_pins(lock_path)
    wheels: dict[tuple[str, str], list[Path]] = {}
    for wheel in sorted(wheelhouse.glob("*.whl")):
        try:
            project, version, _build, _tags = parse_wheel_filename(wheel.name)
        except Exception as exc:
            raise ValueError(f"INVALID_WHEEL_FILENAME:{wheel.name}") from exc
        key = (canonicalize_name(str(project)), str(version))
        wheels.setdefault(key, []).append(wheel)

    lines = [
        "# Target-specific candidate lock generated from wheel bytes downloaded",
        "# with the full source lock; intended for the exact CI target only.",
    ]
    missing: list[str] = []
    for key in sorted(pins):
        name, version = pins[key]
        matching = wheels.get((key, version), [])
        if len(matching) != 1:
            missing.append(f"{key}=={version}:MATCHING_WHEELS={len(matching)}")
            continue
        wheel = matching[0]
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        lines.append(f"{name}=={version} --hash=sha256:{digest}")

    if missing:
        raise ValueError("TARGET_WHEEL_MAPPING_FAILED:" + ";".join(missing))

    # A matching wheel for every pin is not enough: reject extra/unpinned
    # wheel files before writing anything, so an exception cannot leave a
    # plausible-looking lock artifact behind.
    if len(wheels) != len(pins):
        raise ValueError(f"WHEEL_PIN_COUNT_MISMATCH:WHEELS={len(wheels)}:PINS={len(pins)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_text = "\n".join(lines) + "\n"
    created_by_this_call = False
    try:
        # Exclusive creation closes the check/write race and never overwrites.
        with output_path.open("x", encoding="utf-8", newline="\n") as stream:
            created_by_this_call = True
            stream.write(output_text)
            stream.flush()
    except FileExistsError as exc:
        raise ValueError("OUTPUT_PATH_ALREADY_EXISTS") from exc
    except OSError:
        # If a write fails after exclusive creation, remove only the partial
        # file this invocation created; preserve any pre-existing path.
        if created_by_this_call:
            try:
                output_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--wheelhouse", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        compact_lock(args.lock, args.wheelhouse, args.output)
    except Exception as exc:
        print(f"TARGET_LOCK_COMPACTION=FAIL:{exc}", file=sys.stderr)
        return 2
    print(f"TARGET_LOCK_COMPACTION=PASS:{args.output.name}")
    print(f"TARGET_LOCK_PIN_COUNT={len(parse_pins(args.output))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
