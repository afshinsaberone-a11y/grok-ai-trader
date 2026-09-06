"""Canonical handoff contract between Validation and Robustness agents."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "forexai.candidate_handoff.v1"


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible values deterministically for hashing."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def config_hash(params: dict[str, Any]) -> str:
    if not isinstance(params, dict) or not params:
        raise ValueError("candidate params must be a non-empty JSON object")
    try:
        payload = canonical_json(params).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("candidate params must be JSON serializable") from exc
    return hashlib.sha256(payload).hexdigest()


def _artifact_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_handoff(artifact_path: str | Path, validation_decision: Any, max_candidates: int = 20) -> dict[str, Any]:
    """Build a frozen handoff from an already-validated ValidationDecision.

    The function deliberately consumes the Validation Agent decision rather than
    accepting free-form parameter input. Candidates are copied, hashed and frozen.
    """
    if getattr(validation_decision, "status", None) != "READY":
        raise ValueError("validation decision is not READY")

    p = Path(artifact_path)
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in getattr(validation_decision, "robustness_candidates", [])[:max_candidates]:
        if not isinstance(item, dict) or item.get("validation_pass") is not True:
            continue
        candidate_id = item.get("candidate_id", item.get("candidate", item.get("id")))
        params = item.get("params")
        if candidate_id is None:
            raise ValueError("validation-approved candidate has no stable candidate identity")
        digest = config_hash(params)
        if digest in seen:
            raise ValueError("duplicate candidate configuration in validation handoff")
        seen.add(digest)
        candidates.append({
            "candidate_id": candidate_id,
            "params": json.loads(canonical_json(params)),
            "config_hash": digest,
            "validation_pass": True,
            "pre_oos_verified": True,
            "selection_frozen": True,
            "oos_optimization_allowed": False,
        })

    if not candidates:
        raise ValueError("validation handoff contains no approved candidates")

    return {
        "schema_version": SCHEMA_VERSION,
        "source_validation_artifact": str(p),
        "source_validation_sha256": _artifact_sha256(p),
        "research_timeframe": getattr(validation_decision, "timeframe", None),
        "validation_qualified_count": getattr(validation_decision, "validation_qualified_count", None),
        "oos_policy": {"loaded": False, "status": "HELD_OUT"},
        "candidates": candidates,
        "handoff_policy": {
            "ai_may_propose": True,
            "validation_must_approve": True,
            "robustness_may_not_select": True,
            "parameters_are_frozen": True,
            "oos_optimization_disabled": True,
        },
    }


def validate_handoff(value: dict[str, Any], max_candidates: int = 20) -> list[dict[str, Any]]:
    """Validate and return frozen candidates; reject tampered or non-approved data."""
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("invalid candidate handoff schema_version")
    if value.get("oos_policy") != {"loaded": False, "status": "HELD_OUT"}:
        raise ValueError("2026 OOS must remain held out")
    policy = value.get("handoff_policy")
    if not isinstance(policy, dict) or policy.get("validation_must_approve") is not True \
            or policy.get("robustness_may_not_select") is not True \
            or policy.get("parameters_are_frozen") is not True \
            or policy.get("oos_optimization_disabled") is not True:
        raise ValueError("candidate handoff policy is not fail-closed")
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate handoff contains no candidates")

    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates[:max_candidates]:
        if not isinstance(item, dict) or item.get("validation_pass") is not True:
            raise ValueError("handoff contains a non-validation-approved candidate")
        if item.get("pre_oos_verified") is not True or item.get("selection_frozen") is not True:
            raise ValueError("candidate is not explicitly pre-OOS verified and frozen")
        if item.get("oos_optimization_allowed") is not False:
            raise ValueError("OOS optimization must remain disabled")
        if item.get("candidate_id") is None:
            raise ValueError("candidate has no stable identity")
        params = item.get("params")
        expected = config_hash(params)
        supplied = item.get("config_hash")
        if supplied != expected:
            raise ValueError("candidate config_hash does not match canonical params")
        if expected in seen:
            raise ValueError("duplicate candidate configuration")
        seen.add(expected)
        result.append({
            "candidate_id": item["candidate_id"],
            "params": json.loads(canonical_json(params)),
            "config_hash": expected,
            "validation_pass": True,
            "pre_oos_verified": True,
            "selection_frozen": True,
            "oos_optimization_allowed": False,
        })
    return result
