from __future__ import annotations

import hashlib
import json

from research.optimization.g13_demo_package_manifest_builder_m15 import build


PROMOTED = [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48]


def _promotion():
    return {
        "schema_version": "forexai.g13.promotion_manifest.m15.v1",
        "status": "PROMOTION_READY",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "decision_policy": {
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
        },
        "promoted_candidate_ids": PROMOTED,
        "candidates": [
            {"candidate_id": cid, "config_hash": f"cfg-{cid}"}
            for cid in PROMOTED
        ],
    }


def _parity():
    return {
        "schema_version": "forexai.g13.mql5_signal_parity.v2",
        "data_sha256": "a" * 64,
        "data_manifest_sha256": "b" * 64,
        "data_provenance": {"dataset_id": "x", "source": "HistData.com Generic ASCII M1 resampled to M15", "quality_status": "PASS"},
        "status": "PASS",
        "real_data_only": True,
        "synthetic_data": False,
        "scope": {
            "symbol": "EURUSD",
            "timeframe": "M15",
            "data_end_exclusive": "2026-01-01T00:00:00+00:00",
        },
        "candidate_count": 15,
        "passed_count": 15,
        "results": [{"status": "PASS"} for _ in PROMOTED],
    }


def test_builder_binds_exact_package(tmp_path):
    package = tmp_path / "mql5"
    package.mkdir()
    for cid in PROMOTED:
        (package / f"ForexAI_G13_Candidate_{cid}.ex5").write_bytes(f"binary-{cid}".encode())
        (package / f"ForexAI_G13_Candidate_{cid}.mq5").write_text("source", encoding="utf-8")

    promotion_path = tmp_path / "promotion.json"
    parity_path = tmp_path / "parity.json"
    output_path = tmp_path / "manifest.json"
    promotion_path.write_text(json.dumps(_promotion()), encoding="utf-8")
    parity_path.write_text(json.dumps(_parity()), encoding="utf-8")

    result = build(
        promotion_path=promotion_path,
        parity_path=parity_path,
        package_root=package,
        output_path=output_path,
        source_commit="main-sha",
        compile_parity_run_id=123,
    )

    assert result["candidate_count"] == 15
    assert result["ea_source_commit"] == "main-sha"
    assert result["compile_parity_run_id"] == 123
    assert result["parity_evidence_sha256"]
    assert [x["mq5_sha256"] for x in result["candidates"]] == [
        hashlib.sha256((package / f"ForexAI_G13_Candidate_{cid}.mq5").read_bytes()).hexdigest()
        for cid in PROMOTED
    ]
    assert [x["candidate_id"] for x in result["candidates"]] == PROMOTED
