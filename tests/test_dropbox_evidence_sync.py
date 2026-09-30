import hashlib
import json

from tools.dropbox_evidence_sync_v2 import (
    DropboxSyncError,
    collect_and_upload,
    safe_slug,
    upload_immutable_bytes,
    upload_small_bytes,
    verify_or_mark_existing,
)
from tools.dropbox_free_tier_policy_v2 import classify, load_policy, priority, select_files


def test_safe_slug_is_stable():
    assert safe_slug("ForexAI G13 Final Promotion M15") == "forexai-g13-final-promotion-m15"
    assert safe_slug("  weird___Name  ") == "weird-name"
    assert safe_slug("!!!") == "workflow"


def test_collect_rejects_missing_source(tmp_path):
    missing = tmp_path / "missing"
    policy = load_policy(__import__("pathlib").Path("config/dropbox_free_tier_policy.json"))
    try:
        collect_and_upload(missing, "/ForexAI/test", policy)
    except DropboxSyncError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("missing source must fail closed")


def test_collect_rejects_empty_source(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    policy = load_policy(__import__("pathlib").Path("config/dropbox_free_tier_policy.json"))
    try:
        collect_and_upload(empty, "/ForexAI/test", policy)
    except DropboxSyncError as exc:
        assert "no Dropbox Basic-compatible evidence files" in str(exc)
    else:
        raise AssertionError("empty source must fail closed")


def test_free_policy_excludes_market_data_and_zip(tmp_path):
    policy = load_policy(__import__("pathlib").Path("config/dropbox_free_tier_policy.json"))

    raw = tmp_path / "data" / "real" / "EURUSD_M5.csv"
    raw.parent.mkdir(parents=True)
    raw.write_text("timestamp,open,high,low,close\n", encoding="utf-8")
    zip_file = tmp_path / "release.zip"
    zip_file.write_bytes(b"zip")

    assert classify(raw, policy) == (False, "denied_path")
    assert classify(zip_file, policy) == (False, "denied_extension")


def test_priority_prefers_critical_evidence(tmp_path):
    policy = load_policy(__import__("pathlib").Path("config/dropbox_free_tier_policy.json"))
    critical = tmp_path / "promotion-manifest.json"
    standard = tmp_path / "research-summary.md"
    critical.write_text("x", encoding="utf-8")
    standard.write_text("x", encoding="utf-8")
    assert priority(critical, policy) == 0
    assert priority(standard, policy) == 1


def test_free_policy_allows_manifest(tmp_path):
    policy = load_policy(__import__("pathlib").Path("config/dropbox_free_tier_policy.json"))
    manifest = tmp_path / "promotion-manifest.json"
    manifest.write_text('{"schema_version":"test"}\n', encoding="utf-8")
    assert classify(manifest, policy) == (True, "allowed")


def test_sha256_recording_helper_is_deterministic(tmp_path):
    payload = tmp_path / "artifact.json"
    payload.write_text('{"schema":"test","value":1}\n', encoding="utf-8")
    expected = hashlib.sha256(payload.read_bytes()).hexdigest()
    assert len(expected) == 64



def test_remote_existing_identical_is_reused(monkeypatch):
    payload = b'{"evidence":true}\n'
    digest = hashlib.sha256(payload).hexdigest()
    remote = "/ForexAI/test/evidence.json"
    metadata = {"id": "id:existing", "rev": "123", "size": len(payload)}

    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.remote_metadata",
        lambda value: metadata if value == remote else None,
    )
    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.remote_sha256",
        lambda value, size: (metadata, digest),
    )

    reused = verify_or_mark_existing(remote, payload, digest)

    assert reused == metadata


def test_remote_existing_different_hash_fails_closed(monkeypatch):
    payload = b'{"evidence":true}\n'
    digest = hashlib.sha256(payload).hexdigest()
    remote = "/ForexAI/test/evidence.json"
    metadata = {"id": "id:existing", "rev": "123", "size": len(payload)}

    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.remote_metadata",
        lambda value: metadata,
    )
    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.remote_sha256",
        lambda value, size: (metadata, "0" * 64),
    )

    try:
        verify_or_mark_existing(remote, payload, digest)
    except DropboxSyncError as exc:
        assert "IMMUTABLE_CONFLICT" in str(exc)
    else:
        raise AssertionError("remote content mismatch must fail closed")


def test_upload_uses_write_once_mode(monkeypatch):
    calls = {}

    def fake_content_call(endpoint, args, data):
        calls["endpoint"] = endpoint
        calls["args"] = args
        calls["data"] = data
        return {"id": "id:new", "rev": "456", "size": len(data)}

    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.content_call",
        fake_content_call,
    )

    payload = b"manifest\n"
    meta = upload_small_bytes(payload, "/ForexAI/test/manifest.json")

    assert meta["id"] == "id:new"
    assert calls["endpoint"] == "files/upload"
    assert calls["args"]["mode"] == "add"
    assert calls["args"]["strict_conflict"] is True
    assert calls["args"]["autorename"] is False
    assert calls["data"] == payload


def test_upload_immutable_accepts_identical_race(monkeypatch):
    payload = b"manifest\n"
    digest = hashlib.sha256(payload).hexdigest()
    metadata = {"id": "id:raced", "rev": "789", "size": len(payload)}
    state = {"uploads": 0}

    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.remote_metadata",
        lambda value: None if state["uploads"] == 0 else metadata,
    )

    def fake_content_call(endpoint, args, data):
        state["uploads"] += 1
        raise DropboxSyncError("Dropbox content API files/upload HTTP 409: conflict")

    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.content_call",
        fake_content_call,
    )
    monkeypatch.setattr(
        "tools.dropbox_evidence_sync_v2.remote_sha256",
        lambda value, size: (metadata, digest),
    )

    meta, status = upload_immutable_bytes(
        "/ForexAI/test/manifest.json", payload, digest
    )

    assert meta == metadata
    assert status == "already_present_after_race"



def test_policy_manifest_limit_is_exposed():
    policy = load_policy(__import__("pathlib").Path("config/dropbox_free_tier_policy.json"))
    assert policy["max_manifest_bytes"] <= policy["max_file_upload_bytes"]
    assert policy["manifest_reserve_bytes"] > 0
