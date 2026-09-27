"""Validate the frozen G13 M15 Demo package before any controlled execution.

This preflight is offline/read-only. It downloads no broker data and places no
orders. It verifies that the exact compiled EX5 package matches the committed
ConfigHash/SHA-256 manifest and that generated source artifacts retain the
Demo-only / Live-disabled safety contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PROMOTED = (2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48)
MANIFEST_SCHEMA = "forexai.g13.demo_package_manifest.m15.v1"

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


def audit(
    manifest_path: Path,
    package_root: Path,
    compile_parity_run_id: int,
    compile_parity_head_sha: str,
    compile_parity_artifact_id: int,
    compile_parity_artifact_digest: str,
    downloaded_zip_sha256: str,
) -> dict:
    manifest = load_manifest(manifest_path)
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
        assert cid in rows, f"unexpected MQ5 candidate {cid}"
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
        "ea_source_commit": manifest["ea_source_commit"],
        "symbol": manifest["symbol"],
        "timeframe": manifest["timeframe"],
        "candidate_count": 15,
        "candidate_ids": list(PROMOTED),
        "candidate_config_hashes": {str(cid): rows[cid]["config_hash"] for cid in PROMOTED},
        "binary_hashes_verified": 15,
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
