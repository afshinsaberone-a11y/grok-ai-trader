"""Diagnostic analyzer for ForexAI v25 gate rejections.

Reads an existing discovery artifact and summarizes why candidates failed.
It never changes gates, loads OOS data, or creates synthetic data.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    d = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
    result = d.get("result", d)
    candidates = result.get("all_candidate_diagnostics") or result.get("top_20_diagnostics", [])
    total = int(result.get("candidate_total", 0))
    pre = int(result.get("pre_oos_qualified_count", 0))
    val = int(result.get("validation_qualified_count", 0))

    reasons = Counter()
    year_reason = Counter()
    passing_years = Counter()
    candidate_failure_counts = Counter()
    for c in candidates:
        if not isinstance(c, dict):
            continue
        rr = c.get("rejection_reasons", [])
        if isinstance(rr, list):
            candidate_failure_counts[str(c.get("candidate"))] = len(rr)
            for reason in rr:
                reasons[str(reason)] += 1
                if ":" in str(reason):
                    code, year = str(reason).rsplit(":", 1)
                    year_reason[f"{year}|{code}"] += 1
        for row in c.get("pre_oos", []) if isinstance(c.get("pre_oos"), list) else []:
            if not isinstance(row, dict):
                continue
            m = row.get("metrics", {})
            if isinstance(m, dict) and float(m.get("expectancy_R", 0.0)) > 0:
                passing_years[str(row.get("year"))] += 1

    used_all = len(candidates) == total and total > 0
    payload = {
        "schema": "forexai.v25_gate_diagnostics.v2",
        "artifact": args.artifact,
        "candidate_total": total,
        "diagnostic_candidates_analyzed": len(candidates),
        "pre_oos_qualified_count": pre,
        "validation_qualified_count": val,
        "diagnostic_scope": "all_candidate_diagnostics" if used_all else "top_20_diagnostics_fallback",
        "warning": None if used_all else "Artifact does not contain all candidate diagnostics; counts are limited to the stored top-20 set.",
        "rejection_reason_counts": dict(reasons.most_common()),
        "year_reason_counts": dict(year_reason.most_common()),
        "positive_expectancy_candidates_by_year": dict(passing_years),
        "failure_count_distribution": dict(Counter(candidate_failure_counts.values()).most_common()),
        "policy": {
            "gates_unchanged": True,
            "synthetic_data": False,
            "oos_2026_used": False,
        },
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
