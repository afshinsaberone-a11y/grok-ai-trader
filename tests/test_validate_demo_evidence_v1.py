"""Tests for the Demo execution evidence contract."""
import json
from pathlib import Path

import pytest

from tools.validate_demo_evidence_v1 import DemoEvidenceError, validate_demo_evidence


def _valid():
    return {
        "schema": "forexai.demo_execution_evidence.v1",
        "status": "PASS",
        "commit_sha": "4ba45299908948b6daf9c3f065cb69e40526d030",
        "strategy_id": "demo-candidate-1",
        "trade_id": "T-DEMO-1",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "account_mode": "DEMO",
        "terminal_connected": True,
        "broker_order_id": "O-DEMO-1",
        "broker_deal_id": "D-DEMO-1",
        "execution_status": "ACCEPTED",
        "full_fill": True,
        "reconciliation_status": "RECONCILED",
        "unresolved_broker_outcomes": False,
        "runtime_evidence_gate_status": "PASS",
        "deterministic_replay_status": "PASS",
        "live_enabled": False,
        "order_submission_performed": True,
    }


def test_valid_demo_evidence_passes():
    result = validate_demo_evidence(_valid())
    assert result["status"] == "PASS"
    assert result["account_mode"] == "DEMO"
    assert result["reconciliation_status"] == "RECONCILED"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("account_mode", "REAL", "ACCOUNT_NOT_DEMO"),
        ("live_enabled", True, "LIVE_MUST_REMAIN_DISABLED"),
        ("unresolved_broker_outcomes", True, "UNRESOLVED_BROKER_OUTCOME"),
        ("reconciliation_status", "PENDING", "NOT_RECONCILED"),
        ("execution_status", "PARTIAL", "EXECUTION_NOT_ACCEPTED"),
        ("full_fill", False, "FILL_NOT_COMPLETE"),
        ("broker_deal_id", "", "BROKER_DEAL_ID_MISSING"),
        ("terminal_connected", False, "TERMINAL_NOT_CONNECTED"),
        ("runtime_evidence_gate_status", "FAIL", "RUNTIME_GATE_NOT_PASS"),
    ],
)
def test_unsafe_demo_evidence_fails_closed(field, value, error):
    payload = _valid()
    payload[field] = value
    with pytest.raises(DemoEvidenceError, match=error):
        validate_demo_evidence(payload)


def test_missing_field_fails_closed():
    payload = _valid()
    payload.pop("broker_order_id")
    with pytest.raises(DemoEvidenceError, match="REQUIRED_FIELD_MISSING"):
        validate_demo_evidence(payload)


def test_json_cli_shape_round_trips(tmp_path: Path):
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(_valid()), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert validate_demo_evidence(loaded)["trade_id"] == "T-DEMO-1"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("commit_sha", "not-a-sha", "COMMIT_SHA_INVALID"),
        ("broker_order_id", "None", "BROKER_ORDER_ID_MISSING"),
        ("broker_deal_id", 0, "BROKER_DEAL_ID_MISSING"),
        ("strategy_id", "", "STRATEGY_ID_MISSING"),
        ("symbol", "", "SYMBOL_MISSING"),
        ("timeframe", "", "TIMEFRAME_MISSING"),
    ],
)
def test_identity_and_broker_provenance_fail_closed(field, value, error):
    payload = _valid()
    payload[field] = value
    with pytest.raises(DemoEvidenceError, match=error):
        validate_demo_evidence(payload)
