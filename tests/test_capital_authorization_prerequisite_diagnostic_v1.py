from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.diagnose_capital_authorization_prerequisites_v1 import diagnose


def test_missing_authorization_inputs_fail_closed_without_exposing_trade_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    common_files = tmp_path / "Common" / "Files"
    common_files.mkdir(parents=True)
    monkeypatch.delenv("FOREXAI_CONTROL_PLANE_HMAC_SECRET", raising=False)

    report = diagnose(
        candidate_id=2,
        common_files=common_files,
        expected_trade_id="FOREXAI-G13-CANDIDATE-2-S",
        now_utc="2026-10-10T12:00:00+00:00",
    )

    serialized = json.dumps(report, sort_keys=True)
    assert report["status"] == "BLOCKED"
    assert "MQL5_AUTHORIZATION_RECORD_MISSING" in report["blockers"]
    assert "TRADE_LEDGER_PATH_NOT_CONFIGURED" in report["blockers"]
    assert "AUTHENTICATED_ENVELOPE_PATH_NOT_CONFIGURED" in report["blockers"]
    assert "CONTROL_PLANE_SECRET_NOT_CONFIGURED" in report["blockers"]
    assert report["authorization_record_created"] is False
    assert report["ledger_mutated"] is False
    assert report["order_submission_performed"] is False
    assert report["kill_switch_changed"] is False
    assert "FOREXAI-G13-CANDIDATE-2-S" not in serialized
    assert not list(common_files.glob("ForexAI_Authorization_*.auth"))


def test_invalid_candidate_id_is_rejected(tmp_path: Path):
    common_files = tmp_path / "Files"
    common_files.mkdir()
    with pytest.raises(ValueError, match="CANDIDATE_ID_MUST_BE_POSITIVE"):
        diagnose(candidate_id=0, common_files=common_files)


def test_report_does_not_echo_local_paths_or_secret_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    common_files = tmp_path / "profile-should-not-leak" / "Common" / "Files"
    common_files.mkdir(parents=True)
    ledger = tmp_path / "secret-ledger-location.jsonl"
    envelope = tmp_path / "private-envelope-location.json"
    monkeypatch.setenv("FOREXAI_CONTROL_PLANE_HMAC_SECRET", "S" * 64)

    report = diagnose(
        candidate_id=2,
        common_files=common_files,
        ledger_path=ledger,
        authenticated_envelope_path=envelope,
        now_utc="2026-10-10T12:00:00+00:00",
    )

    serialized = json.dumps(report, sort_keys=True)
    assert str(tmp_path) not in serialized
    assert "S" * 64 not in serialized
    assert report["control_plane_secret_configured"] is True
    assert report["authorization_record_created"] is False
