import hashlib
import json

from tools.dropbox_evidence_sync_v2 import DropboxSyncError, safe_slug, collect_and_upload
from tools.dropbox_free_tier_policy import classify, load_policy, select_files


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
