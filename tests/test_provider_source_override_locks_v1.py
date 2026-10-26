from __future__ import annotations

import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "create_provider_source_override_locks_v1.py"
SPEC = importlib.util.spec_from_file_location("provider_source_override_locks", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_fixture(tmp_path: Path) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source_lock = tmp_path / "requirements-provider-lock-compiler.lock.txt"
    source_lock.write_text(
        "# source candidate closure\n"
        "build==1.6.1 \\\n"
        + "    --hash=sha256:" + ("a" * 64) + " \\\n"
        + "    --hash=sha256:" + ("b" * 64) + "\n"
        + "setuptools==84.2.1 \\\n"
        + "    --hash=sha256:" + ("c" * 64) + " \\\n"
        + "    --hash=sha256:" + ("d" * 64) + "\n"
        + "wheel==0.48.0 \\\n"
        + "    --hash=sha256:" + ("e" * 64) + "\n",
        encoding="utf-8",
    )

    wheel = tmp_path / "setuptools-80.9.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "setuptools-80.9.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: setuptools\nVersion: 80.9.0\n\n",
        )
        archive.writestr("setuptools/__init__.py", "__version__ = '80.9.0'\n")
    wheel_hash = sha(wheel)

    install_lock = tmp_path / "requirements-provider-setuptools-bootstrap.lock.txt"
    install_lock.write_text(f"setuptools==80.9.0 --hash=sha256:{wheel_hash}\n", encoding="utf-8")
    install_lock_hash = sha(install_lock)
    manifest = {
        "schema": "forexai.provider_setuptools_source_bootstrap.v1",
        "status": "SIGNED_SOURCE_BUILD_CANDIDATE_NOT_APPROVED",
        "production_approved": False,
        "bootstrap_approved": False,
        "package_name": "setuptools",
        "version": "80.9.0",
        "wheel_filename": wheel.name,
        "wheel_sha256": wheel_hash,
        "install_lock_filename": install_lock.name,
        "install_lock_sha256": install_lock_hash,
        "source": {
            "repository": "pypa/setuptools",
            "commit": "9c4d383631d3951fcae0afd73b5d08ff5a262976",
            "release_tag": "v80.9.0",
            "release_tag_object_sha": "ef921af5f4374a66c018304a2aa5306cb67962a0",
            "github_commit_signature_verified": True,
            "github_release_tag_signature_verified": True,
            "release_tag_target_commit": "9c4d383631d3951fcae0afd73b5d08ff5a262976",
        },
    }
    manifest_path = tmp_path / "setuptools-bootstrap-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return {
        "source_lock": source_lock,
        "wheel": wheel,
        "install_lock": install_lock,
        "manifest": manifest_path,
    }


def test_override_lock_excludes_pypi_setuptools_and_pins_the_signed_source_wheel(tmp_path: Path):
    files = make_fixture(tmp_path)
    download_lock = tmp_path / "compiler-download.lock.txt"
    install_lock = tmp_path / "compiler-install.lock.txt"
    report_path = tmp_path / "override-report.json"

    report = MODULE.create_override_locks(
        files["source_lock"],
        files["wheel"],
        files["manifest"],
        download_lock,
        install_lock,
        report_path,
    )

    download_text = download_lock.read_text(encoding="utf-8")
    install_text = install_lock.read_text(encoding="utf-8")
    signed_digest = sha(files["wheel"])

    assert "setuptools==" not in download_text
    assert "build==1.6.1" in download_text
    assert "--hash=sha256:" + "a" * 64 in download_text
    assert "wheel==0.48.0" in download_text
    assert f"setuptools==80.9.0 --hash=sha256:{signed_digest}" in install_text
    assert "setuptools==84.2.1" not in install_text
    assert install_text.count("setuptools==") == 1
    assert report["source_pin_replaced"] == "setuptools==84.2.1"
    assert report["replacement_pin"] == "setuptools==80.9.0"
    assert report["pypi_setuptools_wheel_excluded_from_download_lock"] is True
    assert report["source_built_wheel_hash_bound_into_install_lock"] is True
    assert report["production_approved"] is False
    assert report["bootstrap_approved"] is False
    assert report["download_lock_sha256"] == sha(download_lock)
    assert report["install_lock_sha256"] == sha(install_lock)
    assert json.loads(report_path.read_text(encoding="utf-8")) == report


def test_override_lock_fails_closed_if_the_source_signature_evidence_is_false(tmp_path: Path):
    files = make_fixture(tmp_path)
    manifest = json.loads(files["manifest"].read_text(encoding="utf-8"))
    manifest["source"]["github_release_tag_signature_verified"] = False
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="SIGNED_SOURCE_MANIFEST_IDENTITY_OR_BOUNDARY_MISMATCH"):
        MODULE.create_override_locks(
            files["source_lock"], files["wheel"], files["manifest"],
            tmp_path / "download.lock", tmp_path / "install.lock", tmp_path / "report.json",
        )


def test_override_lock_fails_closed_if_source_lock_pin_or_wheel_digest_is_wrong(tmp_path: Path):
    files = make_fixture(tmp_path)
    files["source_lock"].write_text(
        files["source_lock"].read_text(encoding="utf-8").replace("setuptools==84.2.1", "setuptools==84.2.2"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="SOURCE_LOCK_SETuptools_VERSION_UNEXPECTED"):
        MODULE.create_override_locks(
            files["source_lock"], files["wheel"], files["manifest"],
            tmp_path / "download.lock", tmp_path / "install.lock", tmp_path / "report.json",
        )

    files = make_fixture(tmp_path / "second-fixture")
    manifest = json.loads(files["manifest"].read_text(encoding="utf-8"))
    manifest["wheel_sha256"] = "f" * 64
    files["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="SIGNED_SOURCE_WHEEL_SHA256_MISMATCH"):
        MODULE.create_override_locks(
            files["source_lock"], files["wheel"], files["manifest"],
            tmp_path / "download.lock", tmp_path / "install.lock", tmp_path / "report.json",
        )
