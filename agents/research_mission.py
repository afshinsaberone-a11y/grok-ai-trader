"""Evidence-only Research Mission for ForexAI discovery artifacts.

This module does not backtest, optimize, or create candidates. It reads committed/local
research artifacts and produces a deterministic handoff decision for specialist agents.
Missing or inconsistent evidence yields HOLD. Validation/OOS data are never used to rank.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

REQUIRED_EXECUTION = {
    "entry": "next_bar_open",
    "round_trip_cost_pips": 1.4,
    "same_bar_resolution": "SL first (conservative)",
    "expiry_bars": 30,
    "overlap": "one position at a time",
    "adverse_exit_cost_applied": True,
}

@dataclass(frozen=True)
class MissionDecision:
    status: str  # READY / HOLD / REJECT
    artifact: str
    schema_version: str | None
    timeframe: str | None
    candidate_total: int | None
    qualified_count: int | None
    selected_candidates: list[dict[str, Any]]
    reasons: list[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid artifact: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("artifact root must be a JSON object")
    return value


def inspect_discovery(path: str | Path, max_candidates: int = 20) -> MissionDecision:
    p = Path(path)
    reasons: list[str] = []
    try:
        d = _load(p)
    except ValueError as exc:
        return MissionDecision("HOLD", str(p), None, None, None, None, [], [str(exc)])

    schema = d.get("schema_version")
    timeframe = d.get("research_timeframe")
    result = d.get("result") if isinstance(d.get("result"), dict) else d
    candidate_total = result.get("candidate_total")
    qualified_count = result.get("qualified_count")

    if d.get("real_data_required") is not True:
        reasons.append("real_data_required is not true")
    if d.get("synthetic_fallback") is not False:
        reasons.append("synthetic_fallback is not explicitly false")
    oos = d.get("oos_policy") if isinstance(d.get("oos_policy"), dict) else {}
    if oos.get("loaded") is not False or oos.get("status") != "HELD_OUT":
        reasons.append("2026 OOS is not explicitly held out")
    execution = d.get("execution_model")
    if not isinstance(execution, dict):
        reasons.append("execution_model is missing")
    else:
        for key, expected in REQUIRED_EXECUTION.items():
            if execution.get(key) != expected:
                reasons.append(f"execution_model.{key} != {expected!r}")

    if not isinstance(candidate_total, int) or candidate_total < 1:
        reasons.append("candidate_total is missing or invalid")
    if not isinstance(qualified_count, int) or qualified_count < 0:
        reasons.append("qualified_count is missing or invalid")

    champion = result.get("champion", d.get("champion"))
    if champion is not None:
        reasons.append("discovery artifact contains a Champion; discovery must not promote")

    selected: list[dict[str, Any]] = []
    top = result.get("top_50")
    if isinstance(top, list):
        for item in top[:max_candidates]:
            if isinstance(item, dict):
                selected.append(item.copy())

    if qualified_count == 0:
        reasons.append("no discovery-qualified candidates are available for downstream validation")

    status = "READY" if not reasons else "HOLD"
    return MissionDecision(status, str(p), schema, timeframe, candidate_total, qualified_count, selected, reasons)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a ForexAI discovery artifact without optimizing it.")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    decision = inspect_discovery(args.artifact)
    payload = decision.to_json()
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if decision.status == "READY" else 2

if __name__ == "__main__":
    raise SystemExit(main())
