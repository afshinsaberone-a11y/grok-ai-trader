"""Tests for the fail-closed Demo evidence assembler."""
import hashlib
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
            "live_enabled": False,
            "trade_id": "T-DEMO-1",
            "strategy_id": "G13-M15",
            "symbol": "EURUSD",
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
                "side": "SELL",
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


def _assembly_inputs(tmp_path: Path):
    source = tmp_path / "ForexAI_G13_Candidate_02.mq5"
    source.write_text("// frozen G13 candidate 02\n", encoding="utf-8")
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    package_preflight = {
        "schema_version": "forexai.g13.controlled_demo_package_preflight.m15.v1",
        "status": "PASS",
        "candidate_ids": [2],
        "candidate_config_hashes": {"2": "a" * 64},
        "candidate_mq5_hashes": {"2": source_sha},
    }
    return {
        "candidate_id": 2,
        "config_hash": "a" * 64,
        "ea_source_path": source,
        "package_preflight": package_preflight,
    }


def _assemble(bundle, tmp_path):
    inputs = _assembly_inputs(tmp_path)
    return assemble(
        submission=bundle["submission"],
        preflight=bundle["preflight"],
        observation=bundle["observation"],
        runtime=bundle["runtime"],
        replay=bundle["replay"],
        strategy_id="G13-M15",
        trade_id="T-DEMO-1",
        commit_sha="4ba45299908948b6daf9c3f065cb69e40526d030",
        **inputs,
    )


def test_valid_bundle_assembles(tmp_path: Path):
    payload = _assemble(_bundle(), tmp_path)
    assert payload["status"] == "PASS"
    assert payload["candidate_id"] == 2
    assert payload["config_hash"] == "a" * 64
    assert payload["broker_order_id"] == "7001"
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
        _assemble(bundle, tmp_path)


def test_submission_and_observation_ids_must_match(tmp_path: Path):
    bundle = _bundle()
    bundle["observation"]["observation"]["broker_deal_id"] = "9999"
    with pytest.raises(DemoEvidenceAssemblyError, match="SUBMISSION_OBSERVATION_DEAL_ID_MISMATCH"):
        _assemble(bundle, tmp_path)


def test_replay_must_end_closed(tmp_path: Path):
    bundle = _bundle()
    bundle["replay"]["trades"][0]["final_state"] = "OPEN"
    with pytest.raises(DemoEvidenceAssemblyError, match="REPLAY_TRADE_NOT_CLOSED"):
        _assemble(bundle, tmp_path)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("candidate_id", 6, "PACKAGE_PREFLIGHT_CANDIDATE_MISMATCH"),
        ("config_hash", "b" * 64, "PACKAGE_PREFLIGHT_CONFIG_HASH_MISMATCH"),
    ],
)
def test_frozen_candidate_identity_mismatch_fails_closed(tmp_path: Path, field, value, error):
    bundle = _bundle()
    inputs = _assembly_inputs(tmp_path)
    inputs[field] = value
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
            **inputs,
        )


def test_frozen_source_hash_mismatch_fails_closed(tmp_path: Path):
    bundle = _bundle()
    inputs = _assembly_inputs(tmp_path)
    inputs["ea_source_path"].write_text("// tampered source\\n", encoding="utf-8")
    with pytest.raises(DemoEvidenceAssemblyError, match="PACKAGE_PREFLIGHT_SOURCE_HASH_MISMATCH"):
        assemble(
            submission=bundle["submission"],
            preflight=bundle["preflight"],
            observation=bundle["observation"],
            runtime=bundle["runtime"],
            replay=bundle["replay"],
            strategy_id="G13-M15",
            trade_id="T-DEMO-1",
            commit_sha="4ba45299908948b6daf9c3f065cb69e40526d030",
            **inputs,
        )
