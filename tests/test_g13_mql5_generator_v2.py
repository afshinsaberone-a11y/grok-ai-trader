from __future__ import annotations

import json

import pytest

from research.optimization.g13_mql5_generator_v2 import canonical_hash, generate

PROMOTED = [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48]


def _params(cid: int) -> dict[str, float | int]:
    return {
        "pivot": 2 + cid % 3,
        "min_delta": 0.0001 + cid / 1_000_000,
        "atr_mult": 1.0 + (cid % 4) / 10,
        "rr": 1.5 + (cid % 3) / 10,
        "rsi_high": 55 + cid % 10,
    }


def _handoff() -> dict:
    candidates = []
    for cid in PROMOTED:
        params = _params(cid)
        candidates.append(
            {
                "candidate_id": cid,
                "config_hash": canonical_hash(params),
                "params": params,
            }
        )
    return {
        "schema_version": "forexai.g13.candidate_handoff.frozen.v1",
        "handoff_policy": {
            "parameters_are_frozen": True,
            "oos_optimization_disabled": True,
        },
        "candidates": candidates,
    }


def _manifest(handoff: dict) -> dict:
    return {
        "schema_version": "forexai.g13.promotion_manifest.m15.v1",
        "status": "PROMOTION_READY",
        "decision_policy": {
            "ea_generation_allowed": True,
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
        },
        "promoted_candidate_ids": PROMOTED,
        "candidates": [
            {
                "candidate_id": c["candidate_id"],
                "config_hash": c["config_hash"],
                "params": c["params"],
            }
            for c in handoff["candidates"]
        ],
    }


def test_generator_consumes_current_promotion_candidate_contract(tmp_path):
    handoff = _handoff()
    manifest = _manifest(handoff)
    handoff_path = tmp_path / "handoff.json"
    manifest_path = tmp_path / "promotion.json"
    out_dir = tmp_path / "mql5"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    generated = generate(manifest_path, handoff_path, out_dir)

    assert len(generated) == 15
    for path, cid in zip(generated, PROMOTED):
        text = path.read_text(encoding="utf-8")
        assert f"Candidate {cid:02d}" in text
        assert manifest["candidates"][PROMOTED.index(cid)]["config_hash"] in text
        assert "DemoTradingAuthorized = false;" in text
        assert 'Live trading is NOT authorized by this source.' in text


def test_generator_rejects_tampered_manifest_candidate_hash(tmp_path):
    handoff = _handoff()
    manifest = _manifest(handoff)
    manifest["candidates"][0]["config_hash"] = "0" * 64

    handoff_path = tmp_path / "handoff.json"
    manifest_path = tmp_path / "promotion.json"
    out_dir = tmp_path / "mql5"
    handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(AssertionError):
        generate(manifest_path, handoff_path, out_dir)
