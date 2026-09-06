"""Evidence-only Validation Mission for ForexAI.

Consumes an existing discovery artifact whose validation evidence has already been
computed. It never backtests, optimizes, ranks on OOS, or creates candidates. Its job
is to verify that validation-approved candidates are a subset of the explicit pre-OOS
handoff and can proceed to robustness review.
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

OOS_STATUS = "HELD_OUT"
PRE_OOS_YEARS = {2022, 2023, 2024}


@dataclass(frozen=True)
class ValidationDecision:
    status: str  # READY / HOLD / REJECT
    artifact: str
    schema_version: str | None
    timeframe: str | None
    candidate_total: int | None
    pre_oos_qualified_count: int | None
    validation_qualified_count: int | None
    robustness_candidates: list[dict[str, Any]]
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


def _identity(item: dict[str, Any]) -> str | None:
    candidate = item.get("candidate_id", item.get("candidate", item.get("id")))
    if candidate is not None:
        return f"candidate:{candidate}"
    params = item.get("params")
    if isinstance(params, dict):
        payload = json.dumps(params, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "params:" + hashlib.sha256(payload).hexdigest()
    return None


def _is_explicit_pre_oos(item: dict[str, Any]) -> bool:
    years = item.get("discovery_years", item.get("pre_oos_years"))
    if isinstance(years, (list, tuple, set)) and years:
        try:
            return set(int(y) for y in years).issubset(PRE_OOS_YEARS)
        except (TypeError, ValueError):
            return False
    return item.get("pre_oos_pass") is True or item.get("selection_source") in {
        "pre_oos",
        "discovery",
        "pre_oos_score",
    }


def inspect_validation(path: str | Path, max_candidates: int = 20) -> ValidationDecision:
    p = Path(path)
    reasons: list[str] = []
    try:
        d = _load(p)
    except ValueError as exc:
        return ValidationDecision("HOLD", str(p), None, None, None, None, None, [], [str(exc)])

    schema = d.get("schema_version")
    timeframe = d.get("research_timeframe")
    result = d.get("result") if isinstance(d.get("result"), dict) else d
    candidate_total = result.get("candidate_total")
    pre_count = result.get("pre_oos_qualified_count")
    val_count = result.get("validation_qualified_count")
    validated = result.get("validated_candidates")
    diagnostics = result.get("top_20_diagnostics")

    if d.get("real_data_required") is not True:
        reasons.append("real_data_required is not true")
    if d.get("synthetic_fallback") is not False:
        reasons.append("synthetic_fallback is not explicitly false")
    oos = d.get("oos_policy") if isinstance(d.get("oos_policy"), dict) else {}
    if oos.get("loaded") is not False or oos.get("status") != OOS_STATUS:
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
    if not isinstance(pre_count, int) or pre_count < 0:
        reasons.append("pre_oos_qualified_count is missing or invalid")
    if not isinstance(val_count, int) or val_count < 0:
        reasons.append("validation_qualified_count is missing or invalid")
    if val_count is not None and pre_count is not None and val_count > pre_count:
        reasons.append("validation_qualified_count exceeds pre_oos_qualified_count")
    if not isinstance(validated, list):
        reasons.append("validated_candidates is missing")
        validated = []
    if not isinstance(diagnostics, list):
        reasons.append("top_20_diagnostics is missing")
        diagnostics = []

    pre_ids = {
        ident
        for item in diagnostics
        if isinstance(item, dict) and _is_explicit_pre_oos(item)
        for ident in [_identity(item)]
        if ident is not None
    }

    robust: list[dict[str, Any]] = []
    for item in validated:
        if not isinstance(item, dict) or item.get("validation_pass") is not True:
            continue
        ident = _identity(item)
        if ident is None:
            reasons.append("a validation-approved candidate has no stable identity")
            continue
        if ident not in pre_ids:
            reasons.append(f"validation-approved candidate {ident} was not in the pre-OOS handoff")
            continue
        robust.append(item.copy())
        if len(robust) >= max_candidates:
            break

    if pre_count and not pre_ids:
        reasons.append("pre-OOS handoff count is positive but no explicit pre-OOS identities were found")
    if val_count != sum(1 for x in validated if isinstance(x, dict) and x.get("validation_pass") is True):
        reasons.append("validation_qualified_count does not match validation_pass evidence")
    if val_count == 0 or not robust:
        reasons.append("no validation-approved candidates are available for robustness review")

    # Validation records may determine eligibility for robustness, but they do not
    # authorize OOS evaluation or EA promotion. The order is preserved exactly as
    # stored in the validated_candidates evidence; no new ranking is performed.
    status = "READY" if not reasons else "HOLD"
    return ValidationDecision(
        status,
        str(p),
        schema,
        timeframe,
        candidate_total,
        pre_count,
        val_count,
        robust,
        reasons,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect ForexAI validation evidence without optimizing it.")
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
