"""Tests for binding the G13 EA generation output to the Control Plane."""
from __future__ import annotations

import pytest

from research.optimization.g13_control_plane_ea_gate_v1 import patch_generated_source
from research.optimization.g13_mql5_generator_v2 import render


def candidate():
    params = {
        "pivot": 3,
        "min_delta": 0.0003,
        "atr_mult": 1.0,
        "rr": 1.5,
        "rsi_high": 70,
        "rsi_low": 30,
        "side": "short",
    }
    import hashlib
    import json
    digest = hashlib.sha256(
        json.dumps(params, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {"candidate_id": 2, "config_hash": digest, "params": params}


def test_generated_ea_has_control_plane_intent_and_one_shot_gate():
    c = candidate()
    source = patch_generated_source(render(c), c["candidate_id"], c["config_hash"])
    assert 'ControlPlaneWriteSignalIntent' in source
    assert 'forexai.g13.runtime_signal_intent.m15.v1' in source
    assert 'ControlPlaneProcessDemoTick(newBar)' in source
    assert 'VerifyRuntimeAuthorization(trade_id,false,decision_id)' in source
    assert 'MarkRuntimeAuthorizationConsumed(trade_id)' in source
    assert 'ForexAI_Authorization_%I64d_%s.auth' in source
    assert 'if(_Symbol!="EURUSD" || _Period!=PERIOD_M15) return INIT_FAILED;' in source
    assert 'live' in source.lower()
    assert 'order_send' not in source.lower()


def test_generated_ea_uses_current_decision_id_and_hash_before_order():
    c = candidate()
    source = patch_generated_source(render(c), c["candidate_id"], c["config_hash"])
    assert 'if(parts[15]!=expected_decision_id) return false;' in source
    assert 'G13-%I64d-%I64d-SELL' in source
    assert 'G13-%I64d-%I64d-S' in source
    assert 'ControlPlaneCurrentRiskWithinReservation(cp_pending_lots,bid,cp_pending_sl)' in source
    assert source.index('MarkRuntimeAuthorizationConsumed(trade_id)') < source.index('bool accepted=trade.Sell(')


def test_generated_ea_patch_fails_closed_when_generator_shape_changes():
    with pytest.raises(ValueError, match="CONTROL_PLANE_GENERATOR_SOURCE_SHAPE_UNKNOWN"):
        patch_generated_source("void OnTick() {}", 2, "a" * 64)


@pytest.mark.parametrize("candidate_id", [0, 1, 49, 999])
def test_gate_rejects_candidate_magic_range_outside_promoted_set(candidate_id):
    with pytest.raises(ValueError, match="CONTROL_PLANE_CANDIDATE_ID_OUT_OF_RANGE"):
        patch_generated_source("void OnTick() {}", candidate_id, "a" * 64)
