"""Deterministic consumer for ForexAI Agent Evidence.

This module intentionally uses no LLM/API. It validates the evidence envelope,
checks the research contract, and emits a deterministic downstream decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

EVIDENCE_SCHEMA = "forexai.github_artifact_evidence.v1"
G9_SCHEMA = "forexai.cost_aware_mean_reversion.v19"
G9_ARTIFACT = "g9-bollinger-mean-reversion-m5"
EXPECTED_OOS = {"loaded": False, "status": "HELD_OUT", "start": "2026-01-01"}


@dataclass(frozen=True)
class ConsumerDecision:
    decision: str  # READY / HOLD / REJECT
    reason: str
    artifact: str
    schema: str | None
    payload_schema: str | None
    run_id: int | None
    commit_sha: str | None
    candidate_total: int | None
    qualified_count: int | None
    champion: Any
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
            "HOLD", str(exc), str(p), None, None, None, None, None, None, None,
            {"json": False},
        )

    artifact = d.get("artifact") if isinstance(d.get("artifact"), dict) else {}
    workflow = d.get("workflow") if isinstance(d.get("workflow"), dict) else {}
    payload = d.get("payload") if isinstance(d.get("payload"), dict) else {}
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}

    payload_sha = d.get("payload_sha256")
    canonical_payload = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sha_ok = isinstance(payload_sha, str) and hashlib.sha256(canonical_payload).hexdigest() == payload_sha

    checks = {
        "schema": d.get("schema") == EVIDENCE_SCHEMA,
        "artifact": artifact.get("name") == G9_ARTIFACT and isinstance(artifact.get("id"), int) and bool(artifact.get("digest")),
        "run_id": isinstance(workflow.get("run_id"), int) and workflow.get("run_id", 0) > 0,
        "commit_sha": isinstance(workflow.get("commit_sha"), str) and len(workflow.get("commit_sha", "")) == 40,
        "payload_schema": payload.get("schema_version") == G9_SCHEMA,
        "real_data": payload.get("real_data_required") is True,
        "synthetic_fallback": payload.get("synthetic_fallback") is False,
        "timeframe": payload.get("research_timeframe") == "M5",
        "oos_held_out": payload.get("oos_policy") == EXPECTED_OOS,
        "candidate_total": isinstance(result.get("candidate_total"), int) and result.get("candidate_total", 0) >= 1,
        "qualified_count": isinstance(result.get("qualified_count"), int) and result.get("qualified_count", -1) >= 0,
        "validated_candidates": isinstance(result.get("validated_candidates"), list)
        and len(result.get("validated_candidates", [])) == result.get("qualified_count"),
        "champion_absent_on_no_qualification": result.get("qualified_count") != 0 or result.get("champion") is None,
        "payload_integrity": sha_ok,
    }

    failures = [name for name, ok in checks.items() if not ok]
    if failures:
        return ConsumerDecision(
            "HOLD",
            "Evidence contract failed: " + ", ".join(failures),
            str(artifact.get("name", p)),
            d.get("schema"),
            payload.get("schema_version"),
            workflow.get("run_id"),
            workflow.get("commit_sha"),
            result.get("candidate_total"),
            result.get("qualified_count"),
            result.get("champion"),
            checks,
        )

    if result.get("qualified_count") == 0:
        return ConsumerDecision(
            "HOLD",
            "No validated candidate; do not promote or deploy.",
            str(artifact.get("name", p)),
            d.get("schema"),
            payload.get("schema_version"),
            workflow.get("run_id"),
            workflow.get("commit_sha"),
            result.get("candidate_total"),
            result.get("qualified_count"),
            result.get("champion"),
            checks,
        )

    if result.get("champion") is None:
        return ConsumerDecision(
            "HOLD",
            "Validated candidates exist but no Champion is present.",
            str(artifact.get("name", p)),
            d.get("schema"),
            payload.get("schema_version"),
            workflow.get("run_id"),
            workflow.get("commit_sha"),
            result.get("candidate_total"),
            result.get("qualified_count"),
            result.get("champion"),
            checks,
        )

    return ConsumerDecision(
        "READY",
        "Evidence is valid and a qualified Champion is present for the next gate.",
        str(artifact.get("name", p)),
        d.get("schema"),
        payload.get("schema_version"),
        workflow.get("run_id"),
        workflow.get("commit_sha"),
        result.get("candidate_total"),
        result.get("qualified_count"),
        result.get("champion"),
        checks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume ForexAI Agent Evidence deterministically.")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    decision = consume_evidence(args.evidence)
    payload = decision.to_json()
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if decision.decision == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
