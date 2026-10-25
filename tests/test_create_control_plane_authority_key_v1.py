from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools import create_control_plane_authority_key_v1 as keygen
from tools.create_control_plane_authority_key_v1 import (
    AuthorityKeyGenerationError,
    MANIFEST_SCHEMA,
    ROLES,
    generate_authority_keypair,
)


def test_generates_encrypted_private_key_and_public_only_manifest(tmp_path: Path):
    repository = tmp_path / "repository"
    repository.mkdir()
    output_dir = tmp_path / "authority-admission"
    passphrase = "test-only-passphrase-2026"

    result = generate_authority_keypair(
        output_dir,
        "provider-admission",
        passphrase,
        repository_root=repository,
    )

    private_path = Path(result["private_key_path"])
    manifest_path = Path(result["public_manifest_path"])
    private_pem = private_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert private_pem.startswith(b"-----BEGIN ENCRYPTED PRIVATE KEY-----")
    assert manifest["schema"] == MANIFEST_SCHEMA
    assert manifest["algorithm"] == "Ed25519"
    assert manifest["role"] == "provider-admission"
    assert manifest["key_id"] == ROLES["provider-admission"]["key_id"]
    assert manifest["environment_variable"] == "FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY"
    assert manifest["private_key_encrypted"] is True
    assert manifest["private_key_in_manifest"] is False
    assert "private_key" not in manifest
    assert "passphrase" not in manifest

    public_raw = base64.b64decode(manifest["public_key_base64"], validate=True)
    assert len(public_raw) == 32
    assert base64.b64encode(public_raw).decode("ascii") == manifest["public_key_base64"]
    assert hashlib.sha256(public_raw).hexdigest() == manifest["public_key_sha256"]

    recovered = serialization.load_pem_private_key(private_pem, password=passphrase.encode("utf-8"))
    assert isinstance(recovered, Ed25519PrivateKey)
    recovered_public = recovered.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    assert recovered_public == public_raw

    with pytest.raises(ValueError):
        serialization.load_pem_private_key(private_pem, password=b"wrong-passphrase")


def test_private_key_material_is_not_returned_or_printed(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    repository = tmp_path / "repository"
    repository.mkdir()
    result = generate_authority_keypair(
        tmp_path / "authority-signal",
        "live-signal",
        "another-test-passphrase-2026",
        repository_root=repository,
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert result["private_key_material_printed"] is False
    assert result["passphrase_printed"] is False
    assert result["environment_variable"] == "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY"


def test_refuses_to_overwrite_existing_key_directory(tmp_path: Path):
    repository = tmp_path / "repository"
    repository.mkdir()
    output_dir = tmp_path / "authority"
    generate_authority_keypair(
        output_dir,
        "risk-reservation",
        "risk-test-passphrase-2026",
        repository_root=repository,
    )
    with pytest.raises(AuthorityKeyGenerationError, match="OUTPUT_DIR_ALREADY_EXISTS"):
        generate_authority_keypair(
            output_dir,
            "risk-reservation",
            "risk-test-passphrase-2026",
            repository_root=repository,
        )


def test_refuses_output_inside_repository(tmp_path: Path):
    repository = tmp_path / "repository"
    repository.mkdir()
    with pytest.raises(AuthorityKeyGenerationError, match="OUTPUT_DIR_MUST_BE_OUTSIDE_REPOSITORY"):
        generate_authority_keypair(
            repository / "private-keys",
            "operator-approval",
            "operator-test-passphrase-2026",
            repository_root=repository,
        )


def test_refuses_relative_or_short_passphrase_without_creating_files(tmp_path: Path):
    repository = tmp_path / "repository"
    repository.mkdir()
    with pytest.raises(AuthorityKeyGenerationError, match="PASSPHRASE_TOO_SHORT"):
        generate_authority_keypair(
            tmp_path / "short-passphrase",
            "provider-admission",
            "too-short",
            repository_root=repository,
        )
    with pytest.raises(AuthorityKeyGenerationError, match="OUTPUT_DIR_MUST_BE_ABSOLUTE"):
        generate_authority_keypair(
            "relative-key-dir",
            "provider-admission",
            "long-enough-test-passphrase",
            repository_root=repository,
        )
    assert not (tmp_path / "short-passphrase").exists()


def test_does_not_clean_an_output_directory_if_creation_races(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    repository = tmp_path / "repository"
    repository.mkdir()
    output_dir = tmp_path / "authority-race"
    original_mkdir = Path.mkdir

    def race_directory_creation(path: Path, *args, **kwargs):
        if path == output_dir:
            original_mkdir(path, *args, **kwargs)
            sentinel = path / "created-by-other-process.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            raise FileExistsError("simulated directory creation race")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", race_directory_creation)
    with pytest.raises(FileExistsError):
        generate_authority_keypair(
            output_dir,
            "provider-admission",
            "long-enough-test-passphrase",
            repository_root=repository,
        )

    assert (output_dir / "created-by-other-process.txt").read_text(encoding="utf-8") == "preserve"


def test_windows_key_directory_acl_removes_default_admin_and_owner_rights(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    original_os_name = keygen.os.name
    monkeypatch.setattr(keygen.os, "name", "nt")
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        if args[0] == "whoami":
            return SimpleNamespace(
                returncode=0,
                stdout='"HOST\\TestUser","S-1-5-21-111-222-333-1001"\n',
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(keygen.subprocess, "run", fake_run)
    try:
        keygen._secure_private_directory(tmp_path)
    finally:
        # os.name is process-global. Restore it before pytest formats assertions
        # so pathlib does not try to instantiate WindowsPath on a POSIX runner.
        keygen.os.name = original_os_name

    acl_calls = [args for args in calls if args[0] == "icacls"]
    assert len(acl_calls) == 3
    assert "/inheritance:r" in acl_calls[0]
    assert "*S-1-5-21-111-222-333-1001:(OI)(CI)F" in acl_calls[0]
    assert "*S-1-5-18:(OI)(CI)F" in acl_calls[0]
    assert ["icacls", str(tmp_path), "/remove", "*S-1-5-32-544"] in acl_calls
    assert ["icacls", str(tmp_path), "/remove", "*S-1-3-4"] in acl_calls


def test_windows_key_directory_acl_failure_to_remove_extra_ace_blocks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    original_os_name = keygen.os.name
    monkeypatch.setattr(keygen.os, "name", "nt")

    def fake_run(args, **kwargs):
        if args[0] == "whoami":
            return SimpleNamespace(
                returncode=0,
                stdout='"HOST\\TestUser","S-1-5-21-111-222-333-1001"\n',
                stderr="",
            )
        if "/remove" in args:
            return SimpleNamespace(returncode=1, stdout="", stderr="simulated ACL error")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(keygen.subprocess, "run", fake_run)
    try:
        with pytest.raises(AuthorityKeyGenerationError, match="PRIVATE_DIRECTORY_ACL_SETUP_FAILED"):
            keygen._secure_private_directory(tmp_path)
    finally:
        keygen.os.name = original_os_name


def test_all_required_roles_have_distinct_key_ids_and_correct_environment_names():
    assert set(ROLES) == {
        "provider-admission",
        "promotion-attestor",
        "live-signal",
        "risk-reservation",
        "operator-approval",
        "capital-firewall-grant",
    }
    assert len({value["key_id"] for value in ROLES.values()}) == len(ROLES)
    assert len({value["environment_variable"] for value in ROLES.values()}) == len(ROLES)
