"""Fail-closed parity comparator for the G13 M15 generated EAs.

The MetaTrader side must export g13_mql5_parity.csv with rows:
 candidate_id,event,timestamp,side,entry,sl,tp,atr

Only SIGNAL rows are compared here. This deliberately separates deterministic
strategy/signal parity from broker-dependent fill, spread and tick execution.
No synthetic data is accepted; Python expectations are generated from the
same committed real-data pipeline and frozen candidate handoff.
"""
from __future__ import annotations


# Gate assertions are part of the fail-closed contract; optimized Python (-O) must never disable them.
if not __debug__:
    raise RuntimeError("G13 gate refuses optimized Python execution; assertions must remain enabled.")

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from research.optimization.rsi_divergence_discovery_g13 import prep, signals

HANDOFF_SCHEMA = "forexai.g13.candidate_handoff.frozen.v1"
MANIFEST_SCHEMA = "forexai.g13.promotion_manifest.m15.v1"
REAL_DATA_SOURCES = ("HistData.com", "Dukascopy")
PROMOTED = (2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48)


def expected_signals(data: pd.DataFrame, params: dict[str, Any]) -> list[dict[str, Any]]:
    d = prep(data)
    sig = signals(d, params)
    out: list[dict[str, Any]] = []
    for i in range(1, len(d)):
        if bool(sig.iloc[i - 1]):
            atr = float(d.ATR14.iloc[i - 1])
            if not pd.notna(atr) or atr <= 0:
                continue
            entry = float(d.Open.iloc[i])
            risk = float(params["atr_mult"]) * atr
            sl = entry + risk
            tp = entry - float(params["rr"]) * risk
            out.append(
                {
                    "candidate_id": None,
                    "event": "SIGNAL",
                    "timestamp": d.index[i].strftime("%Y-%m-%dT%H:%M:00+00:00"),
                    "side": -1,
                    "entry": entry,
                    "sl": sl,
                    "tp": tp,
                    "atr": atr,
                }
            )
    return out


def read_mt5(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise AssertionError(f"missing MetaTrader parity file: {path}")
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig", newline="")))
    required = {"candidate_id", "event", "timestamp", "side", "entry", "sl", "tp", "atr"}
    if rows and not required.issubset(rows[0]):
        raise AssertionError(f"missing parity columns: {sorted(required - set(rows[0]))}")
    return rows


def compare(expected: list[dict[str, Any]], actual: list[dict[str, Any]], cid: int, tol: float) -> dict[str, Any]:
    exp = [x for x in expected if x["event"] == "SIGNAL"]
    act = [x for x in actual if x["event"] == "SIGNAL"]
    assert all(int(x["candidate_id"]) == cid for x in act), f"candidate contamination for {cid}"
    assert len(exp) == len(act), (cid, len(exp), len(act))
    mismatches = []
    for i, (e, a) in enumerate(zip(exp, act)):
        actual_ts = pd.to_datetime(a["timestamp"], utc=True).strftime("%Y-%m-%dT%H:%M:00+00:00")
        if e["timestamp"] != actual_ts:
            mismatches.append((i, "timestamp", e["timestamp"], actual_ts))
        if int(a["side"]) != -1:
            mismatches.append((i, "side", -1, a["side"]))
        for k in ("entry", "sl", "tp", "atr"):
            av = float(a[k])
            if abs(float(e[k]) - av) > tol:
                mismatches.append((i, k, float(e[k]), av))
    assert not mismatches, f"candidate {cid} mismatches: {mismatches[:5]}"
    return {"candidate_id": cid, "expected_signals": len(exp), "actual_signals": len(act), "status": "PASS"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--data-manifest", required=True, type=Path)
    ap.add_argument("--handoff", required=True, type=Path)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--mt5", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--tolerance", type=float, default=1e-8)
    a = ap.parse_args()

    h = json.loads(a.handoff.read_text(encoding="utf-8"))
    m = json.loads(a.manifest.read_text(encoding="utf-8"))
    assert h["schema_version"] == HANDOFF_SCHEMA
    assert m["schema_version"] == MANIFEST_SCHEMA and m["status"] == "PROMOTION_READY"
    promoted = tuple(sorted(map(int, m["promoted_candidate_ids"])))
    assert promoted and len(promoted) == len(set(promoted))
    assert h["handoff_policy"]["parameters_are_frozen"] is True
    assert h["handoff_policy"]["oos_optimization_disabled"] is True
    assert h["research_symbol"] == "EURUSD" and h["research_timeframe"] == "M15"

    data_manifest = json.loads(a.data_manifest.read_text(encoding="utf-8"))
    assert data_manifest["symbol"] == "EURUSD"
    assert data_manifest["timeframe"] == "M15"
    assert data_manifest["quality_status"] == "PASS"
    assert any(source in str(data_manifest["source"]) for source in REAL_DATA_SOURCES)
    assert data_manifest["rows"] >= 100

    raw = pd.read_csv(a.data)
    assert int(data_manifest["rows"]) == len(raw), (data_manifest["rows"], len(raw))
    data_sha256 = hashlib.sha256(a.data.read_bytes()).hexdigest()
    assert data_sha256 == data_manifest["data_sha256"], (data_sha256, data_manifest["data_sha256"])
    data_manifest_sha256 = hashlib.sha256(a.data_manifest.read_bytes()).hexdigest()
    ts = pd.to_datetime(raw["timestamp"], utc=True)
    assert ts.is_monotonic_increasing
    assert ts.max() < pd.Timestamp("2026-01-01", tz="UTC")

    actual = read_mt5(a.mt5)
    results = []
    by_id: dict[int, list[dict[str, Any]]] = {cid: [] for cid in promoted}
    for row in actual:
        cid = int(row["candidate_id"])
        assert cid in by_id, f"unpromoted/unknown candidate in MT5 output: {cid}"
        by_id[cid].append(row)

    candidates = {int(c["candidate_id"]): c for c in h["candidates"]}
    for cid in promoted:
        results.append(compare(expected_signals(raw, candidates[cid]["params"]), by_id[cid], cid, a.tolerance))

    payload = {
        "schema_version": "forexai.g13.mql5_signal_parity.v2",
        "status": "PASS",
        "real_data_only": True,
        "synthetic_data": False,
        "selection_performed": False,
        "optimization_enabled": False,
        "candidate_count": len(promoted),
        "passed_count": len(results),
        "tolerance": a.tolerance,
        "data_sha256": data_sha256,
        "data_manifest_sha256": data_manifest_sha256,
        "data_provenance": {
            "dataset_id": data_manifest["dataset_id"],
            "source": data_manifest["source"],
            "quality_status": data_manifest["quality_status"],
        },
        "scope": {"symbol": "EURUSD", "timeframe": "M15", "data_end_exclusive": "2026-01-01T00:00:00+00:00"},
        "results": results,
        "note": "Signal parity is deterministic; broker-dependent fill/spread/tick execution is audited separately.",
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "candidate_count": len(promoted), "passed_count": len(results)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
