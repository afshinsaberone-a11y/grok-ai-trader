"""Rank the three strongest pre-OOS candidates using only recorded 2022-2025 results.

Evidence is copied from completed CI discovery runs. 2026 OOS is explicitly excluded.
No synthetic data and no re-optimization is performed here.
"""
from __future__ import annotations

import json
from pathlib import Path

EVIDENCE = [
    {
        "family": "rsi_mean_reversion",
        "candidate": 30,
        "source_run": 31845719092,
        "source_note": "family artifact from completed multi-family discovery",
        "years": {
            "2022": {"pf": 1.34, "total_r": 61.00, "max_dd_pct": 5.86},
            "2023": {"pf": 1.07, "total_r": 16.00, "max_dd_pct": 9.23},
            "2024": {"pf": 1.12, "total_r": 28.00, "max_dd_pct": 9.14},
            "2025": {"pf": 1.11, "total_r": 23.74, "max_dd_pct": 7.42, "trades": 346},
        },
        "params": {"rsi_period": 14, "rsi_low": 20, "rsi_high": 80, "atr_stop": 1.4, "rr": 2.0, "trend": 200},
    },
    {
        "family": "bollinger_mean_reversion",
        "candidate": 10,
        "source_run": 31845719092,
        "source_note": "family artifact from completed multi-family discovery",
        "years": {
            "2022": {"pf": 1.14, "total_r": 194.26, "max_dd_pct": 10.39, "trades": 3041},
            "2023": {"pf": 1.17, "total_r": 213.02, "max_dd_pct": 11.53, "trades": 2702},
            "2024": {"pf": 1.12, "total_r": 177.50, "max_dd_pct": 11.42, "trades": 3094},
            "2025": {"pf": 1.11, "total_r": 156.30, "max_dd_pct": 12.56, "trades": 3078},
        },
        "params": {"bb": 14, "bb_k": 1.5, "rsi": 14, "rsi_low": 30, "rsi_high": 70, "atr_stop": 1.8, "rr": 1.0},
    },
    {
        "family": "trend_ema_rsi",
        "candidate": 43,
        "source_run": 31892274331,
        "source_note": "dedicated trend EMA/RSI discovery run",
        "years": {
            "2022": {"pf": 1.08, "total_r": 20.08, "max_dd_pct": 9.80, "trades": 500},
            "2023": {"pf": 1.18, "total_r": 40.26, "max_dd_pct": 7.43, "trades": 423},
            "2024": {"pf": 0.95, "total_r": -14.71, "max_dd_pct": 11.35, "trades": 517},
            "2025": {"pf": 1.10, "total_r": 29.67, "max_dd_pct": 12.43, "trades": 532},
        },
        "params": {"fast": 7, "slow": 55, "trend": 200, "rsi": 14, "atr_stop": 2.2, "rr": 1.5},
    },
]


def score(item: dict) -> float:
    ys = item["years"]
    pfs = [float(ys[y]["pf"]) for y in ("2022", "2023", "2024")]
    dds = [float(ys[y]["max_dd_pct"]) for y in ("2022", "2023", "2024", "2025")]
    total_r = sum(float(ys[y]["total_r"]) for y in ("2022", "2023", "2024"))
    profitable_years = sum(float(ys[y]["total_r"]) > 0 for y in ("2022", "2023", "2024"))
    negative_year_penalty = 1.5 * sum(float(ys[y]["pf"]) < 1.0 for y in ("2022", "2023", "2024"))
    min_pf = min(pfs)
    avg_pf = sum(pfs) / len(pfs)
    max_dd = max(dds)
    return round(3.0 * min_pf + 1.5 * avg_pf + 1.0 * profitable_years + 0.02 * total_r - 0.05 * max_dd - negative_year_penalty, 6)


def main() -> int:
    ranked = []
    for item in EVIDENCE:
        row = dict(item)
        row["ranking_score"] = score(item)
        row["oos_loaded"] = False
        ranked.append(row)
    ranked.sort(key=lambda x: (-x["ranking_score"], x["family"], x["candidate"]))
    report = {
        "schema_version": "forexai.champion_ranking.v1",
        "scope": "pre_oos_only",
        "oos": {"start": "2026-01-01", "loaded": False, "touched": False},
        "ranking": ranked,
        "freeze_candidate": ranked[0],
        "selection_policy": "ranking only; OOS must be run only after this freeze",
    }
    out = Path("artifacts/champion_ranking_v1.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"freeze_candidate": ranked[0], "ranking": [{"family": x["family"], "candidate": x["candidate"], "score": x["ranking_score"]} for x in ranked]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
