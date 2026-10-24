"""Contract tests for the persistent, fail-closed Provider entry point."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools import control_plane_provider_service_v1 as service


def _layout(tmp_path: Path):
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    state_dir = tmp_path / "state"
    keys_dir = tmp_path / "keys"
    for directory in (input_dir, output_dir, state_dir, keys_dir):
        directory.mkdir()
    key_path = keys_dir / "admission-provider-ed25519.pem"
    key_path.write_text("test-only-key-placeholder", encoding="utf-8")
    return input_dir, output_dir, state_dir, key_path


def test_poll_once_processes_a_stable_packet_once_with_content_bound_output(tmp_path, monkeypatch):
    input_dir, output_dir, state_dir, key_path = _layout(tmp_path)
    packet = b'{"schema":"test-only-packet"}'
    (input_dir / service.SOURCE_PACKET_NAME).write_bytes(packet)
    monkeypatch.setattr(
        service,
        "_read_stable_packet",
        lambda path, stability_delay_seconds: packet,
    )
    calls = []

    def fake_processor(packet_bytes, output_path, private_key_path, temporary_directory):
        calls.append((packet_bytes, output_path.name, private_key_path, temporary_directory))
        return {"status": "PASS", "reason": ""}

    seen = {}
    first = service.poll_once(
        input_dir, output_dir, key_path, state_dir, seen,
        stability_delay_seconds=0, processor=fake_processor,
    )
    second = service.poll_once(
        input_dir, output_dir, key_path, state_dir, seen,
        stability_delay_seconds=0, processor=fake_processor,
    )

    digest = hashlib.sha256(packet).hexdigest()
    assert first is not None and first["status"] == "PASS"
    assert first["packet_sha256_prefix"] == digest[:12]
    assert first["signed_request_created"] is True
    assert first["orders_submitted"] is False
    assert first["demo_trading_authorized"] is False
    assert first["live_trading_allowed"] is False
    assert calls == [(packet, f"admission-{digest}.json", key_path.resolve(), output_dir.resolve())]
    assert second is None


def test_poll_once_never_overwrites_existing_content_bound_output(tmp_path, monkeypatch):
    input_dir, output_dir, state_dir, key_path = _layout(tmp_path)
    packet = b'{"schema":"test-only-packet"}'
    (input_dir / service.SOURCE_PACKET_NAME).write_bytes(packet)
    digest = hashlib.sha256(packet).hexdigest()
    target = output_dir / f"admission-{digest}.json"
    target.write_text("preserve-existing", encoding="utf-8")
    monkeypatch.setattr(
        service,
        "_read_stable_packet",
        lambda path, stability_delay_seconds: packet,
    )
    calls = []
    result = service.poll_once(
        input_dir, output_dir, key_path, state_dir, {},
        stability_delay_seconds=0,
        processor=lambda *args: calls.append(args) or {"status": "PASS", "reason": ""},
    )

    assert result is not None
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "PROVIDER_OUTPUT_ALREADY_EXISTS"
    assert target.read_text(encoding="utf-8") == "preserve-existing"
    assert calls == []


def test_symlinked_source_packet_is_rejected_without_processing(tmp_path, monkeypatch):
    input_dir, output_dir, state_dir, key_path = _layout(tmp_path)
    elsewhere = tmp_path / "outside.json"
    elsewhere.write_text('{"secret":"must-not-be-read"}', encoding="utf-8")
    source = input_dir / service.SOURCE_PACKET_NAME
    try:
        source.symlink_to(elsewhere)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable in this test environment")
    calls = []
    result = service.poll_once(
        input_dir, output_dir, key_path, state_dir, {},
        stability_delay_seconds=0,
        processor=lambda *args: calls.append(args) or {"status": "PASS", "reason": ""},
    )
    assert result is not None
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "PROVIDER_SOURCE_PACKET_SYMLINK_FORBIDDEN"
    assert calls == []


def test_runtime_validation_fails_closed_for_missing_registry_and_directories(tmp_path):
    input_dir, output_dir, state_dir, key_path = _layout(tmp_path)
    env = {
        "FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE": "test-only",
        "FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH": str(tmp_path / "missing.sqlite3"),
    }
    with pytest.raises(service.ProviderServiceError, match="PROVIDER_ISSUANCE_REGISTRY_NOT_INITIALIZED"):
        service.validate_runtime(input_dir, output_dir, state_dir, key_path, env)


def test_single_instance_lock_rejects_a_second_process_lock_in_same_runtime(tmp_path):
    lock_path = tmp_path / "state" / "provider-service.lock"
    lock_path.parent.mkdir()
    with service.single_instance_lock(lock_path):
        with pytest.raises(service.ProviderServiceError, match="PROVIDER_SERVICE_ALREADY_RUNNING"):
            with service.single_instance_lock(lock_path):
                pytest.fail("second lock unexpectedly acquired")


def test_service_logs_do_not_include_paths_or_source_identifiers(capsys):
    service._emit(
        "BLOCKED",
        "PROVIDER_HOST_PREFLIGHT_BLOCKED",
        "a" * 64,
    )
    output = capsys.readouterr().out
    assert "PROVIDER_HOST_PREFLIGHT_BLOCKED" in output
    assert "packet_sha256_prefix" in output
    assert "orders_submitted" in output and '"orders_submitted": false' in output
    assert "live_trading_allowed" in output and '"live_trading_allowed": false' in output
    assert "C:\\ProgramData" not in output
    assert "signal_id" not in output
