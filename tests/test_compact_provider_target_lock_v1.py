from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools.compact_provider_target_lock_v1 import compact_lock, parse_pins


def test_compact_lock_pins_each_exact_wheel_hash(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    lock_path = tmp_path / "input.lock.txt"
    output_path = tmp_path / "target.lock.txt"
    lock_path.write_text(
        "Example_Pkg==1.2.3 \\\n"
        "    --hash=sha256:" + ("a" * 64) + " \\\n"
        "    --hash=sha256:" + ("b" * 64) + "\n"
        "another-pkg==4.5.6 \\\n"
        "    --hash=sha256:" + ("c" * 64) + "\n",
        encoding="utf-8",
    )
    wheel_a = wheelhouse / "example_pkg-1.2.3-py3-none-any.whl"
    wheel_b = wheelhouse / "another_pkg-4.5.6-py3-none-any.whl"
    wheel_a.write_bytes(b"wheel-a")
    wheel_b.write_bytes(b"wheel-b")

    compact_lock(lock_path, wheelhouse, output_path)
    output = output_path.read_text(encoding="utf-8")

    assert f"Example_Pkg==1.2.3 --hash=sha256:{hashlib.sha256(b'wheel-a').hexdigest()}" in output
    assert f"another-pkg==4.5.6 --hash=sha256:{hashlib.sha256(b'wheel-b').hexdigest()}" in output
    assert len(parse_pins(output_path)) == 2


def test_compact_lock_fails_closed_for_missing_wheel(tmp_path: Path) -> None:
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    lock_path = tmp_path / "input.lock.txt"
    lock_path.write_text(
        "missing-package==1.0.0 \\\n"
        "    --hash=sha256:" + ("a" * 64) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="TARGET_WHEEL_MAPPING_FAILED"):
        compact_lock(lock_path, wheelhouse, tmp_path / "target.lock.txt")
