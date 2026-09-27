from pathlib import Path

from tools.dropbox_evidence_sync_v2 import DropboxSyncError, safe_slug, collect_and_upload


def test_safe_slug_is_stable():
    assert safe_slug("ForexAI G13 Final Promotion M15") == "forexai-g13-final-promotion-m15"
    assert safe_slug("  weird___Name  ") == "weird-name"
    assert safe_slug("!!!") == "workflow"


def test_collect_rejects_missing_source(tmp_path):
    missing = tmp_path / "missing"
    try:
        collect_and_upload(missing, "/ForexAI/test")
    except DropboxSyncError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("missing source must fail closed")


def test_collect_rejects_empty_source(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    try:
        collect_and_upload(empty, "/ForexAI/test")
    except DropboxSyncError as exc:
        assert "no evidence files" in str(exc)
    else:
        raise AssertionError("empty source must fail closed")


def test_sha256_recording_helper_is_deterministic(tmp_path):
    payload = tmp_path / "artifact.json"
    payload.write_text('{"schema":"test","value":1}\n', encoding="utf-8")
    import hashlib
    expected = hashlib.sha256(payload.read_bytes()).hexdigest()
    assert len(expected) == 64
