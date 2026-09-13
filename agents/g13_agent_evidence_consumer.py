"""Deterministic consumer for G13 OOS Agent Evidence.

No LLM/API is used. The consumer validates provenance, real-data/OOS policy,
frozen parameters, and the fail-closed promotion gate before emitting a
reproducible downstream decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EVIDENCE_SCHEMA = "forexai.github_artifact_evidence.v1"
G13_SCHEMA = "forexai.g13.oos_m15.2026.v1"
G13_ARTIFACT = "g13-oos-m15-2026-current"


@dataclass(frozen=True)
class ConsumerDecision:
    decision: str
    reason: str
    artifact: str
    schema: str | None
    payload_schema: str | None
    run_id: int | None
    commit_sha: str | None
    candidate_count: int | None
    oos_pass_count: int | None
    ea_generation_allowed: bool | None
    validations: dict[str, bool]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid evidence JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("evidence root must be a JSON object")
    return value


def consume_evidence(path: str | Path) -> ConsumerDecision:
    p = Path(path)
    try:
        d = _load(p)
    except ValueError as exc:
        return ConsumerDecision(
            "HOLD", str(exc), str(p), None, None, None, None, None, None, None, {"json": False}
        )

    artifact = d.get("artifact") if isinstance(d.get("artifact"), dict) else {}
    workflow = d.get("workflow") if isinstance(d.get("workflow"), dict) else {}
    payload = d.get("payload") if isinstance(d.get("payload"), dict) else {}
    scope = payload.get("research_scope") if isinstance(payload.get("research_scope"), dict) else {}
    data_scope = payload.get("data_scope") if isinstance(payload.get("data_scope"), dict) else {}
    oos = payload.get("oos") if isinstance(payload.get("oos"), dict) else {}
    gate = payload.get("promotion_gate") if isinstance(payload.get("promotion_gate"), dict) else {}
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []

    payload_sha = d.get("payload_sha256")
    canonical_payload = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    sha_ok = isinstance(payload_sha, str) and hashlib.sha256(canonical_payload).hexdigest() == payload_sha

    expected_end = "2027-01-01T00:00:00+00:00"
    checks = {
        "schema": d.get("schema") == EVIDENCE_SCHEMA,
        "artifact": artifact.get("name") == G13_ARTIFACT and isinstance(artifact.get("id"), int) and bool(artifact.get("digest")),
        "run_id": isinstance(workflow.get("run_id"), int) and workflow.get("run_id", 0) > 0,
        "commit_sha": isinstance(workflow.get("commit_sha"), str) and len(workflow.get("commit_sha", "")) == 40,
        "payload_schema": payload.get("schema_version") == G13_SCHEMA,
        "real_data_only": payload.get("real_data_only") is True,
        "scope_symbol": scope.get("symbol") == "EURUSD",
        "scope_timeframe": scope.get("timeframe") == "M15",
        "scope_year": scope.get("evaluation_year") == 2026,
        "oos_window": data_scope.get("oos_start") == "2026-01-01T00:00:00+00:00" and data_scope.get("oos_end") == expected_end,
        "oos_evaluated": oos.get("status") == "EVALUATED" and oos.get("evaluated") is True,
        "oos_no_optimization": oos.get("optimization_allowed") is False,
        "oos_no_selection": oos.get("selection_allowed") is False,
        "parameters_frozen": payload.get("parameters_frozen") is True,
        "selection_disabled": payload.get("selection_performed") is False,
        "optimization_disabled": payload.get("optimization_enabled") is False,
        "candidate_count": isinstance(payload.get("candidate_count"), int) and payload.get("candidate_count", 0) >= 1,
        "candidate_list": len(candidates) == payload.get("candidate_count"),
        "promotion_fail_closed": gate.get("ea_generation_allowed") is False,
        "payload_integrity": sha_ok,
    }

    failures = [name for name, ok in checks.items() if not ok]
    common = dict(
        artifact=str(artifact.get("name", p)),
        schema=d.get("schema"),
        payload_schema=payload.get("schema_version"),
        run_id=workflow.get("run_id"),
        commit_sha=workflow.get("commit_sha"),
        candidate_count=payload.get("candidate_count"),
        oos_pass_count=payload.get("oos_pass_count"),
        ea_generation_allowed=gate.get("ea_generation_allowed"),
        validations=checks,
    )

    if failures:
        return ConsumerDecision(
            "HOLD",
            "Evidence contract failed: " + ", ".join(failures),
            **common,
        )

    return ConsumerDecision(
        "HOLD",
        "G13 OOS evidence is valid, but promotion remains closed; no EA generation or deployment is allowed.",
        **common,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume G13 OOS Agent Evidence deterministically.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    decision = consume_evidence(args.evidence)
    payload = decision.to_json()
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if decision.decision == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
