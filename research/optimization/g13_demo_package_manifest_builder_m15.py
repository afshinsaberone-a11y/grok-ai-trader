"""Build an immutable G13 M15 Demo-package manifest from the exact compile/parity workspace.

This is a read-only packaging step: it does not place orders or authorize trading.
The manifest is produced from the Promotion manifest, parity evidence and the
freshly compiled EX5/MQ5 package from the same Compile/Parity run.
"""
from __future__ import annotations


# Gate assertions are part of the fail-closed contract; optimized Python (-O) must never disable them.
if not __debug__:
    raise RuntimeError("G13 gate refuses optimized Python execution; assertions must remain enabled.")

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTED = (2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48)
PROMOTION_SCHEMA = "forexai.g13.promotion_manifest.m15.v1"
PARITY_SCHEMA = "forexai.g13.mql5_signal_parity.v1"
OUTPUT_SCHEMA = "forexai.g13.demo_package_manifest.m15.v2"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build(
    *,
    promotion_path: Path,
    parity_path: Path,
    package_root: Path,
    output_path: Path,
    source_commit: str,
    compile_parity_run_id: int,
) -> dict[str, Any]:
    promotion = load(promotion_path)
    parity = load(parity_path)

    assert promotion["schema_version"] == PROMOTION_SCHEMA
    assert promotion["status"] == "PROMOTION_READY"
    assert promotion["symbol"] == "EURUSD"
    assert promotion["timeframe"] == "M15"
    assert promotion["decision_policy"]["demo_trading_allowed"] is False
    assert promotion["decision_policy"]["live_trading_allowed"] is False
    assert promotion["promoted_candidate_ids"] == list(PROMOTED)

    assert parity["schema_version"] == PARITY_SCHEMA
    assert parity["status"] == "PASS"
    assert parity["real_data_only"] is True
    assert parity["synthetic_data"] is False
    assert parity["scope"] == {
        "symbol": "EURUSD",
        "timeframe": "M15",
        "data_end_exclusive": "2026-01-01T00:00:00+00:00",
    }
    assert parity["candidate_count"] == 15
    assert parity["passed_count"] == 15
    assert all(row["status"] == "PASS" for row in parity["results"])

    candidates = sorted(
        package_root.glob("ForexAI_G13_Candidate_*.ex5"),
        key=lambda p: int(p.stem.rsplit("_", 1)[1]),
    )
    sources = sorted(
        package_root.glob("ForexAI_G13_Candidate_*.mq5"),
        key=lambda p: int(p.stem.rsplit("_", 1)[1]),
    )
    assert len(candidates) == 15, f"expected 15 EX5 files, found {len(candidates)}"
    assert len(sources) == 15, f"expected 15 MQ5 files, found {len(sources)}"

    by_id = {int(x["candidate_id"]): x for x in promotion["candidates"]}
    assert tuple(sorted(by_id)) == PROMOTED

    source_by_id = {
        int(source.stem.rsplit("_", 1)[1]): source
        for source in sources
    }
    assert tuple(sorted(source_by_id)) == PROMOTED

    rows = []
    for binary in candidates:
        cid = int(binary.stem.rsplit("_", 1)[1])
        assert cid in by_id, f"unexpected promoted binary candidate {cid}"
        source = source_by_id[cid]
        rows.append({
            "candidate_id": cid,
            "config_hash": by_id[cid]["config_hash"],
            "mq5_sha256": sha256(source),
            "ex5_sha256": sha256(binary),
        })
    assert tuple(row["candidate_id"] for row in rows) == PROMOTED

    output = {
        "schema_version": OUTPUT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository_ledger_commit": source_commit,
        "ea_source_commit": source_commit,
        "compile_parity_run_id": compile_parity_run_id,
        "compile_parity_status": "PASS",
        "parity_evidence_sha256": sha256(parity_path),
        "promotion_manifest_sha256": sha256(promotion_path),
        "symbol": "EURUSD",
        "timeframe": "M15",
        "research_data_end_exclusive": parity["scope"]["data_end_exclusive"],
        "real_data_only": True,
        "synthetic_data": False,
        "demo_trading_allowed_by_source": False,
        "live_trading_allowed": False,
        "candidate_count": 15,
        "candidates": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--promotion", type=Path, required=True)
    ap.add_argument("--parity", type=Path, required=True)
    ap.add_argument("--package-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--compile-parity-run-id", type=int, required=True)
    args = ap.parse_args()

    result = build(
        promotion_path=args.promotion,
        parity_path=args.parity,
        package_root=args.package_root,
        output_path=args.output,
        source_commit=args.source_commit,
        compile_parity_run_id=args.compile_parity_run_id,
    )
    print(json.dumps({
        "status": result["compile_parity_status"],
        "candidate_count": result["candidate_count"],
        "compile_parity_run_id": result["compile_parity_run_id"],
        "ea_source_commit": result["ea_source_commit"],
        "parity_evidence_sha256": result["parity_evidence_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
