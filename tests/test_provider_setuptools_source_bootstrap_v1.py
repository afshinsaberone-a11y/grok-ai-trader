from __future__ import annotations

import hashlib
import importlib.util
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_provider_setuptools_source_bootstrap_v1.py"
SPEC = importlib.util.spec_from_file_location("provider_setuptools_source_bootstrap", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _valid_identity_payloads():
    return (
        {
            "sha": MODULE.COMMIT,
            "commit": {"verification": {"verified": True, "reason": "valid"}},
        },
        {
            "ref": "refs/tags/" + MODULE.RELEASE_TAG,
            "object": {"type": "tag", "sha": MODULE.TAG_OBJECT_SHA},
        },
        {
            "sha": MODULE.TAG_OBJECT_SHA,
            "tag": MODULE.RELEASE_TAG,
            "object": {"type": "commit", "sha": MODULE.COMMIT},
            "verification": {"verified": True, "reason": "valid"},
        },
    )


def test_setuptools_bootstrap_pins_exact_verified_source_commit_and_release_tag():
    assert MODULE.REPOSITORY == "pypa/setuptools"
    assert MODULE.VERSION == "80.9.0"
    assert MODULE.COMMIT == "9c4d383631d3951fcae0afd73b5d08ff5a262976"
    assert MODULE.TAG_OBJECT_SHA == "ef921af5f4374a66c018304a2aa5306cb67962a0"
    assert all(len(value) == 40 for value in (MODULE.COMMIT, MODULE.TAG_OBJECT_SHA))
    assert MODULE.STATUS == "SIGNED_SOURCE_BUILD_CANDIDATE_NOT_APPROVED"


def test_signed_source_identity_passes_and_reports_both_signature_boundaries():
    commit, ref, tag = _valid_identity_payloads()
    result = MODULE.validate_source_identity(commit, ref, tag)
    assert result["github_commit_signature_verified"] is True
    assert result["github_commit_signature_reason"] == "valid"
    assert result["github_release_tag_signature_verified"] is True
    assert result["github_release_tag_signature_reason"] == "valid"
    assert result["release_tag_target_commit"] == MODULE.COMMIT


@pytest.mark.parametrize("mutation,expected_error", [
    ("commit_unsigned", "SETUPTOOLS_COMMIT_SIGNATURE_NOT_VERIFIED"),
    ("tag_unsigned", "SETUPTOOLS_RELEASE_TAG_SIGNATURE_NOT_VERIFIED"),
    ("tag_moved", "SETUPTOOLS_RELEASE_TAG_OBJECT_MISMATCH"),
    ("tag_target_moved", "SETUPTOOLS_RELEASE_TAG_TARGET_MISMATCH"),
    ("commit_moved", "SETUPTOOLS_COMMIT_SHA_MISMATCH"),
])
def test_setuptools_source_identity_fails_closed(mutation, expected_error):
    commit, ref, tag = _valid_identity_payloads()
    if mutation == "commit_unsigned":
        commit["commit"]["verification"]["verified"] = False
    elif mutation == "tag_unsigned":
        tag["verification"]["verified"] = False
    elif mutation == "tag_moved":
        ref["object"]["sha"] = "f" * 40
    elif mutation == "tag_target_moved":
        tag["object"]["sha"] = "e" * 40
    elif mutation == "commit_moved":
        commit["sha"] = "d" * 40
    with pytest.raises(RuntimeError, match=expected_error):
        MODULE.validate_source_identity(commit, ref, tag)


def test_bootstrap_wheel_metadata_is_read_from_wheel_contents(tmp_path: Path):
    wheel = tmp_path / "setuptools-80.9.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "setuptools-80.9.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: setuptools\nVersion: 80.9.0\n\n",
        )
    assert MODULE.wheel_metadata(wheel) == ("setuptools", "80.9.0")


def test_release_build_tree_removes_only_the_exact_dev_suffix_config_in_copy(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    original_config = "[egg_info]\ntag_build = .post\ntag_date = 1\n"
    (source / "setup.cfg").write_text(original_config, encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git" / "sentinel").write_text("git metadata", encoding="utf-8")
    (source / "setup.py").write_text("setup source", encoding="utf-8")

    build = tmp_path / "build-source"
    result = MODULE.prepare_release_build_tree(source, build)

    assert (source / "setup.cfg").read_text(encoding="utf-8") == original_config
    assert (build / "setup.cfg").read_text(encoding="utf-8") == ""
    assert not (build / ".git").exists()
    assert (build / "setup.py").read_text(encoding="utf-8") == "setup source"
    assert result["signed_source_checkout_is_left_unmodified"] is True
    assert result["git_metadata_copied_to_build_tree"] is False
    assert result["modified_configuration_is_empty"] is True
    assert result["original_normalized_text_sha256"] == hashlib.sha256(original_config.encode("utf-8")).hexdigest()
    assert result["modified_normalized_text_sha256"] == hashlib.sha256(b"").hexdigest()
    assert len(result["override_diff_sha256"]) == 64


def test_release_build_tree_fails_closed_if_upstream_setup_config_differs(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "setup.cfg").write_text("[egg_info]\ntag_date = 0\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="SETUPTOOLS_SOURCE_SETUP_CFG_CONTENT_MISMATCH"):
        MODULE.prepare_release_build_tree(source, tmp_path / "build-source")


def test_source_bootstrap_build_is_hash_locked_and_does_not_install_pypi_setuptools():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "https://github.com/pypa/setuptools.git" in source
    assert '"setup.py", "bdist_wheel"' in source
    assert "pip wheel" not in source
    assert "SETUPTOOLS_ABSENT" in source
    assert "SETUPTOOLS_COMMIT_SIGNATURE_NOT_VERIFIED" in source
    assert "SETUPTOOLS_RELEASE_TAG_SIGNATURE_NOT_VERIFIED" in source
    assert "setup.cfg" in source
    assert "SETUPTOOLS_SOURCE_SETUP_CFG_CONTENT_MISMATCH" in source
    assert "build_source_tree_config_override" in source
    assert "requirements-provider-setuptools-bootstrap.lock.txt" in source
    assert "install_lock_sha256" in source
    assert '"production_approved": False' in source
    assert '"bootstrap_approved": False' in source
