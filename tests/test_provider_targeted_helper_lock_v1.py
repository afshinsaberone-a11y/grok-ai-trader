import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "create_provider_targeted_helper_lock_v1.py"
SPEC = importlib.util.spec_from_file_location("provider_targeted_helper_lock", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_candidate_lock(path: Path, wheels: list[Path], hashes: dict[str, str]) -> None:
    rows = ["# generated candidate lock"]
    for wheel in wheels:
        name, version, _build, _tags = MODULE.parse_wheel_filename(wheel.name)
        rows.append(f"{name}=={version} \\")
        rows.append(f"    --hash=sha256:{hashes[str(name)]}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_target_lock_is_reproducible_and_pins_only_matching_wheel_bytes(tmp_path: Path):
    house = tmp_path / "wheelhouse"
    house.mkdir()
    alpha = house / "alpha-1.0-py3-none-any.whl"
    beta = house / "beta-2.0-py3-none-any.whl"
    alpha.write_bytes(b"verified alpha wheel bytes")
    beta.write_bytes(b"verified beta wheel bytes")
    hashes = {"alpha": _sha(alpha), "beta": _sha(beta)}
    candidate = tmp_path / "candidate.lock.txt"
    _write_candidate_lock(candidate, [alpha, beta], hashes)
    target = tmp_path / "target.lock.txt"

    report = MODULE.build_target_lock(candidate, house, target, "windows-cp313")

    assert report["status"] == "TARGET_WHEEL_HASHES_PINNED"
    assert report["pinned_requirement_count"] == 2
    assert report["wheel_file_count"] == 2
    assert report["all_exact_versions_matched"] is True
    assert report["all_wheel_hashes_sha256"] is True
    rows = [line for line in target.read_text(encoding="utf-8").splitlines() if "==" in line]
    assert rows == [
        f"alpha==1.0 --hash=sha256:{hashes['alpha']}",
        f"beta==2.0 --hash=sha256:{hashes['beta']}",
    ]
    assert MODULE.sha256(target) == report["target_lock_sha256"]


def test_target_lock_fails_when_downloaded_wheel_hash_is_not_in_candidate_lock(tmp_path: Path):
    house = tmp_path / "wheelhouse"
    house.mkdir()
    alpha = house / "alpha-1.0-py3-none-any.whl"
    alpha.write_bytes(b"different bytes than the candidate lock allows")
    candidate = tmp_path / "candidate.lock.txt"
    candidate.write_text(
        "alpha==1.0 \\\n"
        + "    --hash=sha256:" + ("a" * 64) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="WHEEL_HASH_NOT_IN_SOURCE_CANDIDATE_LOCK"):
        MODULE.build_target_lock(candidate, house, tmp_path / "target.lock.txt", "windows-cp313")


def test_target_lock_fails_closed_for_missing_or_unexpected_wheels(tmp_path: Path):
    house = tmp_path / "wheelhouse"
    house.mkdir()
    alpha = house / "alpha-1.0-py3-none-any.whl"
    alpha.write_bytes(b"alpha")
    beta = house / "beta-2.0-py3-none-any.whl"
    beta.write_bytes(b"beta")
    candidate = tmp_path / "candidate.lock.txt"
    _write_candidate_lock(candidate, [alpha], {"alpha": _sha(alpha)})
    with pytest.raises(ValueError, match="WHEEL_PACKAGE_SET_MISMATCH"):
        MODULE.build_target_lock(candidate, house, tmp_path / "target.lock.txt", "windows-cp313")


def test_target_lock_fails_for_package_version_mismatch(tmp_path: Path):
    house = tmp_path / "wheelhouse"
    house.mkdir()
    alpha = house / "alpha-1.1-py3-none-any.whl"
    alpha.write_bytes(b"alpha")
    candidate = tmp_path / "candidate.lock.txt"
    candidate.write_text(
        "alpha==1.0 \\\n"
        + "    --hash=sha256:" + _sha(alpha) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="WHEEL_VERSION_MISMATCH"):
        MODULE.build_target_lock(candidate, house, tmp_path / "target.lock.txt", "windows-cp313")
