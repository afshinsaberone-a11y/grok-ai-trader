#!/usr/bin/env python3
"""Disable MT5's built-in MCP endpoints in the automation-owned terminal profile.

The parity harness does not use MetaTrader's built-in MCP servers. On MT5
builds that enable the internal terminal/MetaEditor MCP listeners by default,
a user-interactive terminal can already own the default localhost port and
prevent the runner's separate service-profile terminal from initializing.
Only Config/assistant.ini under the explicitly supplied MT5 data profile is
changed; all unrelated sections and keys are preserved.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Iterable

MCP_SECTIONS = ("MCP.MetaTrader", "MCP.MetaEditor")
PROFILE_HASH = re.compile(r"^[0-9A-Fa-f]{32}$")
PORTABLE_ROOT = re.compile(r"^g13-mt5-parity-portable-\d+$")
SECTION_HEADER = re.compile(r"^\s*\[([^\]]+)\]\s*$")
ENABLE_KEY = re.compile(r"^\s*Enable\s*=.*$", re.IGNORECASE)
ENABLE_VALUE = re.compile(r"^\s*Enable\s*=\s*([^;#\s]+)", re.IGNORECASE)


def _decode_config(raw: bytes) -> tuple[str, bytes, str]:
    """Decode supported INI encodings without losing an existing BOM."""
    if raw.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        raise ValueError("assistant.ini encoding is unsupported; refusing to rewrite it")
    if raw.startswith(b"\xef\xbb\xbf"):
        bom, encoding = b"\xef\xbb\xbf", "utf-8"
    elif raw.startswith(b"\xff\xfe"):
        bom, encoding = b"\xff\xfe", "utf-16-le"
    elif raw.startswith(b"\xfe\xff"):
        bom, encoding = b"\xfe\xff", "utf-16-be"
    else:
        bom, encoding = b"", "utf-8"
    try:
        return raw[len(bom):].decode(encoding), bom, encoding
    except UnicodeDecodeError as exc:
        raise ValueError("assistant.ini encoding is unsupported; refusing to rewrite it") from exc


def _split_lines(text: str) -> tuple[list[str], str, bool]:
    if "\r\n" in text:
        newline = "\r\n"
    elif "\r" in text and "\n" not in text:
        newline = "\r"
    elif "\n" in text:
        newline = "\n"
    else:
        newline = "\r\n" if os.name == "nt" else "\n"
    ends_newline = text.endswith(("\n", "\r"))
    lines = re.split(r"\r\n|\n|\r", text)
    if ends_newline and lines and lines[-1] == "":
        lines.pop()
    return lines, newline, ends_newline


def _section_ranges(lines: list[str], section: str) -> list[tuple[int, int]]:
    headers: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        match = SECTION_HEADER.match(line)
        if match:
            headers.append((i, match.group(1).strip()))
    matches: list[tuple[int, int]] = []
    for n, (start, name) in enumerate(headers):
        if name.casefold() != section.casefold():
            continue
        end = headers[n + 1][0] if n + 1 < len(headers) else len(lines)
        matches.append((start, end))
    return matches


def _set_enable_zero(lines: list[str], section: str) -> None:
    ranges = _section_ranges(lines, section)
    if not ranges:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend((f"[{section}]", "Enable=0"))
        return

    # Work backwards because inserting a missing key changes later positions.
    for start, end in reversed(ranges):
        key_indices = [i for i in range(start + 1, end) if ENABLE_KEY.match(lines[i])]
        if key_indices:
            for i in key_indices:
                # Preserve an optional inline comment while forcing the value.
                prefix_match = re.match(r"^(\s*Enable\s*=\s*)", lines[i], re.IGNORECASE)
                comment_match = re.search(r"(\s+[;#].*)$", lines[i])
                prefix = prefix_match.group(1) if prefix_match else "Enable="
                comment = comment_match.group(1) if comment_match else ""
                lines[i] = f"{prefix}0{comment}"
        else:
            lines.insert(end, "Enable=0")


def _assert_disabled(lines: list[str]) -> None:
    for section in MCP_SECTIONS:
        ranges = _section_ranges(lines, section)
        if not ranges:
            raise ValueError(f"required section missing after update: {section}")
        for start, end in ranges:
            values = [
                match.group(1).strip()
                for line in lines[start + 1:end]
                if (match := ENABLE_VALUE.match(line))
            ]
            if not values or any(value != "0" for value in values):
                raise ValueError(f"{section} Enable=0 could not be verified")


def disable_internal_mcp(profile_root: Path, *, portable_root: bool = False) -> Path:
    """Disable MT5's internal terminal/editor MCP listeners for a data root.

    Normal mode targets the 32-hex MetaQuotes profile directory. Portable mode
    is restricted to a run-scoped G13 directory so arbitrary user/install paths
    cannot be targeted accidentally.
    """
    root = Path(profile_root)
    if root.is_symlink():
        raise ValueError("MT5 profile root must not be a symlink")
    if portable_root:
        if not PORTABLE_ROOT.fullmatch(root.name):
            raise ValueError("portable root must be named g13-mt5-parity-portable-<run-id>")
    elif not PROFILE_HASH.fullmatch(root.name):
        raise ValueError("profile root must be an MT5 32-character hexadecimal data-folder hash")
    if not root.is_dir():
        raise ValueError("MT5 profile root does not exist or is not a directory")

    config_dir = root / "Config"
    if config_dir.is_symlink():
        raise ValueError("MT5 Config directory must not be a symlink")
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "assistant.ini"
    if config_path.is_symlink():
        raise ValueError("assistant.ini must not be a symlink")

    existed = config_path.exists()
    raw = config_path.read_bytes() if existed else b""
    if existed:
        text, bom, encoding = _decode_config(raw)
        original_mode = config_path.stat().st_mode
    else:
        text, bom, encoding = "", b"", "utf-8"
        original_mode = None

    lines, newline, ends_newline = _split_lines(text)
    for section in MCP_SECTIONS:
        _set_enable_zero(lines, section)
    _assert_disabled(lines)

    result_text = newline.join(lines)
    if ends_newline or not result_text:
        result_text += newline
    encoded = bom + result_text.encode(encoding)

    # Atomic replacement prevents a partially written assistant.ini.
    fd, temp_name = tempfile.mkstemp(prefix=".assistant.ini.", suffix=".tmp", dir=config_dir)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if original_mode is not None:
            os.chmod(temp_path, original_mode)
        os.replace(temp_path, config_path)
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass

    # Validate bytes as persisted, not just the in-memory representation.
    persisted, _, _ = _decode_config(config_path.read_bytes())
    persisted_lines, _, _ = _split_lines(persisted)
    _assert_disabled(persisted_lines)
    return config_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile-root", help="MT5 data folder (the 32-hex terminal hash directory)")
    group.add_argument("--portable-root", help="Run-scoped G13 portable installation directory")
    args = parser.parse_args(argv)
    try:
        path = disable_internal_mcp(
            Path(args.profile_root or args.portable_root),
            portable_root=args.portable_root is not None,
        )
    except (OSError, ValueError) as exc:
        # Do not print the INI contents: assistant.ini may contain credentials.
        print(f"MT5_INTERNAL_MCP_PROFILE_FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print("MT5_INTERNAL_MCP_PROFILE_DISABLED sections=MCP.MetaTrader,MCP.MetaEditor")
    print(f"MT5_INTERNAL_MCP_CONFIG={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
