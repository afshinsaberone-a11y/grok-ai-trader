"""Evidence-only Robustness Mission for ForexAI.

Consumes validation evidence and freezes eligible candidates for the existing
robustness validator. It never evaluates market data, optimizes parameters,
loads OOS, or promotes an EA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
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
class RobustnessDecision:
    status: str
    artifact: str
    schema_version: str | None
    timeframe: str | None
    validation_qualified_count: int | None
    frozen_candidates: list[dict[str, Any]]
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


def _hash_params(params: dict[str, Any]) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def inspect_validation(path: str | Path, max_candidates: int = 20) -> RobustnessDecision:
    p = Path(path)
    try:
        d = _load(p)
    except ValueError as exc:
        return RobustnessDecision("HOLD", str(p), None, None, None, [], [str(exc)])

    reasons: list[str] = []
    schema = d.get("schema_version")
    timeframe = d.get("research_timeframe")
    result = d.get("result") if isinstance(d.get("result"), dict) else d
    val_count = result.get("validation_qualified_count")
    validated = result.get("validated_candidates")
    execution = d.get("execution_model")
    oos = d.get("oos_policy") if isinstance(d.get("oos_policy"), dict) else {}

    if d.get("real_data_required") is not True:
        reasons.append("real_data_required is not true")
    if d.get("synthetic_fallback") is not False:
        reasons.append("synthetic_fallback is not explicitly false")
    if oos.get("loaded") is not False or oos.get("status") != "HELD_OUT":
        reasons.append("2026 OOS is not explicitly held out")
    if not isinstance(execution, dict):
        reasons.append("execution_model is missing")
    else:
        for key, expected in REQUIRED_EXECUTION.items():
            if execution.get(key) != expected:
                reasons.append(f"execution_model.{key} != {expected!r}")
    if not isinstance(val_count, int) or val_count < 0:
        reasons.append("validation_qualified_count is missing or invalid")
    if not isinstance(validated, list):
        reasons.append("validated_candidates is missing")
        validated = []

    eligible = [x for x in validated if isinstance(x, dict) and x.get("validation_pass") is True]
    if val_count != len(eligible):
        reasons.append("validation_qualified_count does not match validation_pass evidence")

    frozen: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    for item in eligible:
        params = item.get("params")
        if not isinstance(params, dict) or not params:
            reasons.append("validation-approved candidate has no explicit params")
            continue
        config_hash = item.get("config_hash") or _hash_params(params)
        if config_hash in seen_hashes:
            reasons.append("duplicate validation-approved candidate config_hash")
            continue
        seen_hashes.add(config_hash)
        frozen.append({
            "candidate": item.get("candidate_id", item.get("candidate", item.get("id"))),
            "params": params.copy(),
            "config_hash": config_hash,
            "selection_frozen": True,
            "oos_optimization_allowed": False,
        })
        if len(frozen) >= max_candidates:
            break

    if val_count == 0 or not frozen:
        reasons.append("no validation-approved candidates are available for robustness review")

    status = "READY" if not reasons else "HOLD"
    return RobustnessDecision(status, str(p), schema, timeframe, val_count, frozen, reasons)


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze validation-approved candidates for robustness review.")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    decision = inspect_validation(args.artifact)
    payload = decision.to_json()
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if decision.status == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
