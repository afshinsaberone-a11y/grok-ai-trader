"""Validate the frozen G13 M15 Demo package before any controlled execution.

This preflight is offline/read-only. It downloads no broker data and places no
orders. It verifies that the exact compiled EX5 package matches the committed
ConfigHash/SHA-256 manifest and that generated source artifacts retain the
Demo-only / Live-disabled safety contract.
"""
from __future__ import annotations


# Gate assertions are part of the fail-closed contract; optimized Python (-O) must never disable them.
if not __debug__:
    raise RuntimeError("G13 gate refuses optimized Python execution; assertions must remain enabled.")

import argparse
import hashlib
import json
from pathlib import Path

PROMOTED = (2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48)
MANIFEST_SCHEMA = "forexai.g13.demo_package_manifest.m15.v2"

REQUIRED_SOURCE_TOKENS = (
    "input bool DemoTradingAuthorized = false;",
    "bool DemoTradingExecutionAllowed()",
    "ACCOUNT_TRADE_MODE_DEMO",
    "MQLInfoInteger(MQL_TESTER)",
    "g13_demo_kill_switch.txt",
    "DemoKillSwitchAllowed()",
    "HistoryDealSelect(",
    "HistoryOrderSelect(",
    "OrderCalcProfit(ORDER_TYPE_SELL",
    "SYMBOL_TRADE_STOPS_LEVEL",
    "OnTradeTransaction(",
    "ExecutionAuditLog(",
)

FORBIDDEN_SOURCE_TOKENS = (
    "trans.magic",
    "trans.comment",
    "AllowLiveTrading=1",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload.get("schema_version") == MANIFEST_SCHEMA
    assert payload.get("compile_parity_status") == "PASS"
    assert payload.get("symbol") == "EURUSD"
    assert payload.get("timeframe") == "M15"
    assert payload.get("real_data_only") is True
    assert payload.get("synthetic_data") is False
    assert payload.get("demo_trading_allowed_by_source") is False
    assert payload.get("live_trading_allowed") is False
    assert tuple(x["candidate_id"] for x in payload["candidates"]) == PROMOTED
    return payload


def find_package(root: Path) -> Path:
    candidates = [root / "g13" / "mql5", root / "mql5", root]
    for c in candidates:
        if c.is_dir() and list(c.glob("ForexAI_G13_Candidate_*.ex5")):
            return c
    raise AssertionError(f"no G13 EX5 package found under {root}")


def validate_data_manifest_binding(parity: dict, data_manifest_path: Path) -> None:
    assert data_manifest_path.is_file(), f"missing real-data provenance manifest: {data_manifest_path}"
    actual_manifest_sha = sha256(data_manifest_path)
    assert actual_manifest_sha == parity["data_manifest_sha256"], (
        actual_manifest_sha,
        parity["data_manifest_sha256"],
    )
    data_manifest = json.loads(data_manifest_path.read_text(encoding="utf-8"))
    assert data_manifest["dataset_id"] == parity["data_provenance"]["dataset_id"]
    assert data_manifest["source"] == parity["data_provenance"]["source"]
    assert data_manifest["quality_status"] == parity["data_provenance"]["quality_status"]
    assert data_manifest["data_sha256"] == parity["data_sha256"]
    assert int(data_manifest["rows"]) >= 100


def validate_compile_artifact_binding(
    manifest: dict,
    *,
    compile_parity_run_id: int,
    compile_parity_head_sha: str,
    compile_parity_artifact_digest: str,
    downloaded_zip_sha256: str,
) -> None:
    assert int(manifest["compile_parity_run_id"]) == compile_parity_run_id
    assert manifest["ea_source_commit"] == compile_parity_head_sha
    assert compile_parity_artifact_digest == "sha256:" + downloaded_zip_sha256


def validate_mq5_source_binding(rows: dict[int, dict], source_path: Path) -> str:
    cid = int(source_path.stem.rsplit("_", 1)[1])
    assert cid in rows, f"unexpected MQ5 candidate {cid}"
    expected_sha = rows[cid].get("mq5_sha256")
    assert isinstance(expected_sha, str) and len(expected_sha) == 64, (
        f"missing MQ5 hash in manifest candidate {cid}"
    )
    actual_sha = sha256(source_path)
    assert actual_sha == expected_sha, f"MQ5 hash mismatch candidate {cid}"
    return actual_sha


def audit(
    manifest_path: Path,
    package_root: Path,
    compile_parity_run_id: int,
    compile_parity_head_sha: str,
    compile_parity_artifact_id: int,
    compile_parity_artifact_digest: str,
    downloaded_zip_sha256: str,
    parity_evidence_path: Path,
    data_manifest_path: Path,
) -> dict:
    manifest = load_manifest(manifest_path)
    parity = json.loads(parity_evidence_path.read_text(encoding="utf-8"))
    assert manifest["parity_evidence_sha256"] == sha256(parity_evidence_path)
    assert parity["schema_version"] == "forexai.g13.mql5_signal_parity.v2"
    validate_data_manifest_binding(parity, data_manifest_path)
    assert len(parity["data_sha256"]) == 64
    assert len(parity["data_manifest_sha256"]) == 64
    assert parity["data_provenance"]["quality_status"] == "PASS"
    assert any(source in parity["data_provenance"]["source"] for source in ("HistData.com", "Dukascopy"))
    assert parity["status"] == "PASS"
    assert parity["real_data_only"] is True
    assert parity["synthetic_data"] is False
    assert parity["candidate_count"] == 15
    assert parity["passed_count"] == 15
    assert parity["scope"] == {
        "symbol": "EURUSD",
        "timeframe": "M15",
        "data_end_exclusive": manifest["research_data_end_exclusive"],
    }
    assert manifest["data_sha256"] == parity["data_sha256"]
    assert manifest["data_manifest_sha256"] == parity["data_manifest_sha256"]
    assert manifest["data_provenance"] == parity["data_provenance"]
    validate_compile_artifact_binding(
        manifest,
        compile_parity_run_id=compile_parity_run_id,
        compile_parity_head_sha=compile_parity_head_sha,
        compile_parity_artifact_digest=compile_parity_artifact_digest,
        downloaded_zip_sha256=downloaded_zip_sha256,
    )
    package = find_package(package_root)

    rows = {x["candidate_id"]: x for x in manifest["candidates"]}
    ex5 = sorted(package.glob("ForexAI_G13_Candidate_*.ex5"))
    mq5 = sorted(package.glob("ForexAI_G13_Candidate_*.mq5"))

    assert len(ex5) == 15, f"expected 15 EX5 files, found {len(ex5)}"
    assert len(mq5) == 15, f"expected 15 MQ5 files, found {len(mq5)}"

    verified = []
    for f in ex5:
        cid = int(f.stem.rsplit("_", 1)[1])
        assert cid in rows, f"unexpected EX5 candidate {cid}"
        actual_sha = sha256(f)
        assert actual_sha == rows[cid]["ex5_sha256"], f"EX5 hash mismatch candidate {cid}"
        verified.append({"candidate_id": cid, "ex5_sha256": actual_sha})

    source_checks = []
    for f in mq5:
        cid = int(f.stem.rsplit("_", 1)[1])
        actual_source_sha = validate_mq5_source_binding(rows, f)
        text = f.read_text(encoding="utf-8")
        assert f'ConfigHash = "{rows[cid]["config_hash"]}";' in text, f"ConfigHash mismatch candidate {cid}"
        assert f"MagicNumber = 130000 + {cid};" in text, f"MagicNumber mismatch candidate {cid}"
        for token in REQUIRED_SOURCE_TOKENS:
            assert token in text, f"missing safety token candidate {cid}: {token}"
        for token in FORBIDDEN_SOURCE_TOKENS:
            assert token not in text, f"forbidden token candidate {cid}: {token}"
        source_checks.append(cid)

    return {
        "schema_version": "forexai.g13.controlled_demo_package_preflight.m15.v1",
        "status": "PASS",
        "compile_parity_run_id": manifest["compile_parity_run_id"],
        "compile_parity_head_sha": compile_parity_head_sha,
        "compile_parity_artifact_id": compile_parity_artifact_id,
        "compile_parity_artifact_digest": compile_parity_artifact_digest,
        "downloaded_zip_sha256": downloaded_zip_sha256,
        "parity_evidence_sha256": manifest["parity_evidence_sha256"],
        "promotion_manifest_sha256": manifest["promotion_manifest_sha256"],
        "data_sha256": parity["data_sha256"],
        "data_manifest_sha256": parity["data_manifest_sha256"],
        "data_provenance": parity["data_provenance"],
        "data_sha256": manifest["data_sha256"],
        "data_manifest_sha256": manifest["data_manifest_sha256"],
        "data_provenance": manifest["data_provenance"],
        "ea_source_commit": manifest["ea_source_commit"],
        "symbol": manifest["symbol"],
        "timeframe": manifest["timeframe"],
        "candidate_count": 15,
        "candidate_ids": list(PROMOTED),
        "candidate_config_hashes": {str(cid): rows[cid]["config_hash"] for cid in PROMOTED},
        "candidate_mq5_hashes": {str(cid): rows[cid]["mq5_sha256"] for cid in PROMOTED},
        "candidate_ex5_hashes": {str(cid): rows[cid]["ex5_sha256"] for cid in PROMOTED},
        "binary_hashes_verified": 15,
        "source_hashes_verified": 15,
        "source_safety_contracts_verified": 15,
        "real_data_only": True,
        "synthetic_data": False,
        "demo_trading_allowed_by_source": False,
        "live_trading_allowed": False,
        "notes": [
            "Preflight is offline/read-only.",
            "No broker connection or order submission occurs.",
            "A PASS does not establish profitability or authorize execution.",
        ],
        "verified": verified,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--package-root", type=Path, required=True)
    ap.add_argument("--compile-parity-run-id", type=int, required=True)
    ap.add_argument("--compile-parity-head-sha", required=True)
    ap.add_argument("--compile-parity-artifact-id", type=int, required=True)
    ap.add_argument("--compile-parity-artifact-digest", required=True)
    ap.add_argument("--downloaded-zip-sha256", required=True)
    ap.add_argument("--parity-evidence", type=Path, required=True)
    ap.add_argument("--data-manifest", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()

    result = audit(
        args.manifest,
        args.package_root,
        args.compile_parity_run_id,
        args.compile_parity_head_sha,
        args.compile_parity_artifact_id,
        args.compile_parity_artifact_digest,
        args.downloaded_zip_sha256,
        args.parity_evidence,
        args.data_manifest,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "candidate_count": result["candidate_count"],
        "binary_hashes_verified": result["binary_hashes_verified"],
        "source_safety_contracts_verified": result["source_safety_contracts_verified"],
        "live_trading_allowed": result["live_trading_allowed"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
