from pathlib import Path

from tools.dropbox_evidence_sync import _safe_slug, sync_tree


def test_safe_slug_is_stable():
    assert _safe_slug("ForexAI G13 Final Promotion M15") == "forexai-g13-final-promotion-m15"
    assert _safe_slug("  weird___Name  ") == "weird-name"
    assert _safe_slug("!!!") == "workflow"


def test_sync_tree_rejects_missing_source(tmp_path):
    missing = tmp_path / "missing"
    try:
        sync_tree(missing, "/ForexAI/test")
    except RuntimeError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("missing source must fail closed")


def test_sync_tree_rejects_empty_source(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    try:
        sync_tree(empty, "/ForexAI/test")
    except RuntimeError as exc:
        assert "no evidence files" in str(exc)
    else:
        raise AssertionError("empty source must fail closed")
