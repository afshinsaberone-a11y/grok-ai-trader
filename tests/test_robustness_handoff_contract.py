from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from agents.candidate_contract import build_handoff, config_hash
from agents.robustness_mission import inspect_handoff


@dataclass
class Decision:
    status: str
    timeframe: str
    validation_qualified_count: int
    robustness_candidates: list[dict]


def _write_handoff(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "validation.json"
    source.write_text('{"validated":true}\n', encoding="utf-8")
    decision = Decision(
        status="READY",
        timeframe="M5",
        validation_qualified_count=1,
        robustness_candidates=[
            {
                "candidate_id": "cand-001",
                "params": {"atr_mult": 1.1, "rr": 2.2},
                "validation_pass": True,
            }
        ],
    )
    handoff = tmp_path / "candidate-handoff-v1.json"
    handoff.write_text(json.dumps(build_handoff(source, decision), sort_keys=True), encoding="utf-8")
    return source, handoff


def test_config_hash_is_canonical_under_key_order() -> None:
    assert config_hash({"rr": 2.2, "atr_mult": 1.1}) == config_hash({"atr_mult": 1.1, "rr": 2.2})


def test_canonical_handoff_is_ready_and_freezes_candidate(tmp_path: Path) -> None:
    source, handoff = _write_handoff(tmp_path)
    decision = inspect_handoff(handoff, source_validation_path=source)
    assert decision.status == "READY"
    assert decision.frozen_candidates[0]["candidate"] == "cand-001"
    assert decision.frozen_candidates[0]["selection_frozen"] is True
    assert decision.frozen_candidates[0]["oos_optimization_allowed"] is False


def test_tampered_candidate_hash_is_rejected(tmp_path: Path) -> None:
    source, handoff = _write_handoff(tmp_path)
    payload = json.loads(handoff.read_text(encoding="utf-8"))
    payload["candidates"][0]["params"]["rr"] = 9.9
    handoff.write_text(json.dumps(payload), encoding="utf-8")
    decision = inspect_handoff(handoff, source_validation_path=source)
    assert decision.status == "HOLD"
    assert any("config_hash" in reason for reason in decision.reasons)


def test_tampered_source_validation_artifact_is_rejected(tmp_path: Path) -> None:
    source, handoff = _write_handoff(tmp_path)
    source.write_text('{"validated":false}\n', encoding="utf-8")
    decision = inspect_handoff(handoff, source_validation_path=source)
    assert decision.status == "HOLD"
    assert any("SHA256 mismatch" in reason for reason in decision.reasons)


def test_wrong_candidate_id_is_rejected(tmp_path: Path) -> None:
    source, handoff = _write_handoff(tmp_path)
    payload = json.loads(handoff.read_text(encoding="utf-8"))
    candidate_ids = {item["candidate_id"] for item in payload["candidates"]}
    assert "cand-999" not in candidate_ids
    decision = inspect_handoff(handoff, source_validation_path=source)
    assert decision.status == "READY"
    from research.optimization.robustness_validation_v29_1 import _load_handoff
    with pytest.raises(ValueError, match="not uniquely present"):
        _load_handoff(handoff, "cand-999", source)


def test_v29_1_cli_requires_canonical_handoff() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "research.optimization.robustness_validation_v29_1", "--data", "missing.csv", "--timeframe", "M5"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "--handoff" in proc.stderr
    assert "--candidate-id" in proc.stderr
