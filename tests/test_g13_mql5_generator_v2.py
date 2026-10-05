from __future__ import annotations

import json

import pytest

from research.optimization.g13_mql5_generator_v2 import canonical_hash, generate, render

PROMOTED = [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48]


def _params(cid: int) -> dict[str, float | int]:
    return {
        "pivot": 2 + cid % 3,
        "min_delta": 0.0001 + cid / 1_000_000,
        "atr_mult": 1.0 + (cid % 4) / 10,
        "rr": 1.5 + (cid % 3) / 10,
        "rsi_high": 65 + cid % 5,
        "rsi_low": 30 if cid % 2 == 0 else 35,
        "side": "short",
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


def test_render_mql5_trace_literals_and_lifecycle_symbols():

    params = _params(2)
    source = render({"candidate_id": 2, "config_hash": canonical_hash(params), "params": params})

    bs = chr(92)
    assert ('"' + bs + '"side' + bs + '":' + bs + '"SELL' + bs + '"') in source
    assert (bs + '"retcode' + bs + '":%u') in source
    assert ('"' + bs + '"deal_ticket' + bs + '":' + bs + '"%I64d' + bs + '"') in source
    assert ('StringReplace(value,"' + bs + bs + '","' + bs + bs + bs + bs + '");') in source
    expected_quote_escape = 'StringReplace(value,"' + bs + '"' + '","' + bs + bs + bs + '"' + '");'
    assert expected_quote_escape in source
    expected_newline_escape = 'StringFind(value,"' + bs + bs + 'n")<0'
    expected_carriage_escape = 'StringFind(value,"' + bs + bs + 'r")<0'
    assert expected_newline_escape in source
    assert expected_carriage_escape in source
    assert "IntegerToString(MagicNumber)" in source
    assert "LongToString(" not in source
    assert ('StringFormat("' + bs + '"retcode' + bs + '":%u') in source
    assert ('StringFormat("{' + bs + '"schema' + bs + '":' + bs + '"forexai.runtime_trace.v1') in source
    trace_escape = source.split("string TraceJsonEscape", 1)[1].split("void TraceRecord", 1)[0]
    assert trace_escape.count("StringReplace(value") == 4
    assert 'PositionsByMagic(' not in source

def test_render_preserves_tester_execution_without_runtime_artifacts():
    params = _params(2)
    source = render({"candidate_id": 2, "config_hash": canonical_hash(params), "params": params})

    assert "double lots=0.0;" in source
    assert "lots=LotSize(risk,entry);" in source
    assert "if(!(bool)MQLInfoInteger(MQL_TESTER) && !EnsureRuntimeTraceReady()) return INIT_FAILED;" in source
    assert "input bool   DemoTradingAuthorized = false;" in source
