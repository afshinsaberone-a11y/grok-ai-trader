"""Tests for the fail-closed Demo evidence assembler."""
import json
from pathlib import Path

import pytest

from tools.assemble_demo_evidence_v1 import DemoEvidenceAssemblyError, assemble


def _bundle():
    return {
        "submission": {
            "schema": "forexai.mt5_demo_execution_submission.v1",
            "status": "PASS",
            "account_mode": "DEMO",
            "terminal_connected": True,
            "order_submission_performed": True,
            "execution_status": "ACCEPTED",
            "full_fill": True,
            "broker_order_id": "7001",
            "broker_deal_id": "5001",
            "timeframe": "M15",
        },
        "preflight": {
            "schema": "forexai.mt5_terminal_preflight.v1",
            "status": "PASS",
            "account_mode": "DEMO",
            "terminal_connected": True,
            "order_submission_performed": False,
        },
        "observation": {
            "schema": "forexai.mt5_demo_broker_observation.v1",
            "status": "OBSERVED",
            "account_mode": "DEMO",
            "terminal_connected": True,
            "order_submission_performed": False,
            "retry_performed": False,
            "capital_authority_granted": False,
            "observation": {
                "status": "ACCEPTED",
                "broker_order_id": "7001",
                "broker_deal_id": "5001",
                "symbol": "EURUSD",
                "side": "BUY",
                "volume": 0.10,
                "filled_volume": 0.10,
                "remaining_volume": 0.0,
            },
        },
        "runtime": {
            "schema": "forexai.runtime_evidence_gate.v1",
            "status": "PASS",
            "trade_id": "T-DEMO-1",
            "reconciliation_status": "RECONCILED",
        },
        "replay": {
            "schema": "forexai.deterministic_replay.v1",
            "unresolved_reconciliation": [],
            "trades": [
                {"trade_id": "T-DEMO-1", "final_state": "CLOSED"}
            ],
        },
    }


def _write_bundle(tmp_path: Path):
    paths = {}
    for name, payload in _bundle().items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = path
    return paths


def test_valid_bundle_assembles(tmp_path: Path):
    paths = _write_bundle(tmp_path)
    source = Path("ea/GRK_Hybrid_Regime_EA.mq5")
    payload = assemble(
        submission=json.loads(paths["submission"].read_text()),
        preflight=json.loads(paths["preflight"].read_text()),
        observation=json.loads(paths["observation"].read_text()),
        runtime=json.loads(paths["runtime"].read_text()),
        replay=json.loads(paths["replay"].read_text()),
        strategy_id="G13-M15",
        trade_id="T-DEMO-1",
        commit_sha="4ba45299908948b6daf9c3f065cb69e40526d030",
        ea_source_path=source,
    )
    assert payload["status"] == "PASS"
    assert payload["broker_order_id"] == "7001"
    assert payload["strategy_id"] == "G13-M15"
    assert len(payload["ea_source_sha256"]) == 64


@pytest.mark.parametrize(
    ("component", "field", "value", "error"),
    [
        ("submission", "full_fill", False, "FIELD_MISMATCH:full_fill"),
        ("submission", "strategy_id", "OTHER", "SUBMISSION_STRATEGY_ID_MISMATCH"),
        ("observation", "capital_authority_granted", True, "FIELD_MISMATCH:capital_authority_granted"),
        ("runtime", "reconciliation_status", "PENDING", "FIELD_MISMATCH:reconciliation_status"),
    ],
)
def test_inconsistent_component_fails_closed(tmp_path: Path, component, field, value, error):
    bundle = _bundle()
    bundle[component][field] = value
    with pytest.raises(DemoEvidenceAssemblyError, match=error):
        assemble(
            submission=bundle["submission"],
            preflight=bundle["preflight"],
            observation=bundle["observation"],
            runtime=bundle["runtime"],
            replay=bundle["replay"],
            strategy_id="G13-M15",
            trade_id="T-DEMO-1",
            commit_sha="4ba45299908948b6daf9c3f065cb69e40526d030",
            ea_source_path=Path("ea/GRK_Hybrid_Regime_EA.mq5"),
        )


def test_submission_and_observation_ids_must_match():
    bundle = _bundle()
    bundle["observation"]["observation"]["broker_deal_id"] = "9999"
    with pytest.raises(DemoEvidenceAssemblyError, match="SUBMISSION_OBSERVATION_DEAL_ID_MISMATCH"):
        assemble(
            submission=bundle["submission"],
            preflight=bundle["preflight"],
            observation=bundle["observation"],
            runtime=bundle["runtime"],
            replay=bundle["replay"],
            strategy_id="G13-M15",
            trade_id="T-DEMO-1",
            commit_sha="4ba45299908948b6daf9c3f065cb69e40526d030",
            ea_source_path=Path("ea/GRK_Hybrid_Regime_EA.mq5"),
        )


def test_replay_must_end_closed():
    bundle = _bundle()
    bundle["replay"]["trades"][0]["final_state"] = "OPEN"
    with pytest.raises(DemoEvidenceAssemblyError, match="REPLAY_TRADE_NOT_CLOSED"):
        assemble(
            submission=bundle["submission"],
            preflight=bundle["preflight"],
            observation=bundle["observation"],
            runtime=bundle["runtime"],
            replay=bundle["replay"],
            strategy_id="G13-M15",
            trade_id="T-DEMO-1",
            commit_sha="4ba45299908948b6daf9c3f065cb69e40526d030",
            ea_source_path=Path("ea/GRK_Hybrid_Regime_EA.mq5"),
        )
