"""Deterministic research-stage controller for ForexAI agents.

This module is intentionally model-independent. It decides whether the evidence
visible in the current checkout is sufficient to move between research stages.
It never computes or fabricates trading performance; missing evidence yields HOLD.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOTS = (REPO_ROOT / "artifacts", REPO_ROOT / "reports")


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    evidence: str
    reason: str


@dataclass(frozen=True)
class ResearchDecision:
    stage: str
    status: str  # GO / HOLD / REJECT
    gates: tuple[Gate, ...]
    next_stage: str | None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


def _find_evidence(patterns: tuple[str, ...]) -> list[Path]:
    hits: list[Path] = []
    for root in ARTIFACT_ROOTS:
        if not root.exists():
            continue
        for pattern in patterns:
            hits.extend(p for p in root.rglob(pattern) if p.is_file())
    return sorted(set(hits))


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _contains_truthy_key(obj: Any, keys: set[str]) -> bool:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in keys and value is True:
                return True
            if _contains_truthy_key(value, keys):
                return True
    elif isinstance(obj, list):
        return any(_contains_truthy_key(v, keys) for v in obj)
    return False


def _gate_real_evidence() -> Gate:
    files = _find_evidence(("*.json", "*.txt", "*.md"))
    if files:
        return Gate("evidence_present", True, str(len(files)) + " artifact/report files", "Inspectable evidence exists.")
    return Gate("evidence_present", False, "", "No artifact/report evidence is available in this checkout.")


def _gate_no_synthetic_fallback() -> Gate:
    matches = []
    for root in ARTIFACT_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            data = _read_json(path)
            if data is None:
                continue
            if _contains_truthy_key(data, {"synthetic", "synthetic_fallback", "used_synthetic_data"}):
                matches.append(path)
    if matches:
        return Gate("no_synthetic_fallback", False, ", ".join(str(p.relative_to(REPO_ROOT)) for p in matches[:10]), "Evidence explicitly indicates synthetic data/fallback.")
    return Gate("no_synthetic_fallback", True, "No positive synthetic-data flag found", "No synthetic-use flag was observed; absence is not proof of data provenance.")


def _gate_oos_holdout(stage: str) -> Gate:
    if stage in {"discovery", "optimization"}:
        return Gate("oos_holdout", True, "controller policy", "2026 OOS is forbidden as a selection input at this stage.")
    candidates = _find_evidence(("*oos*.json", "*oos*.md", "*validation*.json", "*validation*.md", "*.json"))
    for path in candidates:
        data = _read_json(path)
        if data is not None and _contains_truthy_key(data, {"oos_isolated", "oos_holdout", "ready_for_oos"}):
            return Gate("oos_holdout", True, str(path.relative_to(REPO_ROOT)), "Explicit OOS isolation/readiness evidence was found.")
    return Gate("oos_holdout", False, "", "No explicit OOS isolation/readiness evidence was found.")


def _gate_execution_contract() -> Gate:
    patterns = ("*execution*.json", "*execution*.md", "*audit*.json", "*audit*.md")
    files = _find_evidence(patterns)
    required_terms = {"execution_contract_v1", "SL-first", "1.4"}
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if all(term.lower() in text.lower() for term in required_terms):
            return Gate("execution_contract", True, str(path.relative_to(REPO_ROOT)), "Execution contract evidence is present.")
    return Gate("execution_contract", False, "", "No evidence file explicitly records the unified execution contract.")


def decide(stage: str) -> ResearchDecision:
    """Return a fail-closed stage decision without calculating strategy metrics."""
    gates = [_gate_real_evidence(), _gate_no_synthetic_fallback(), _gate_execution_contract(), _gate_oos_holdout(stage)]
    failed = [g for g in gates if not g.passed]

    if failed:
        return ResearchDecision(stage=stage, status="HOLD", gates=tuple(gates), next_stage=None)

    next_stage = {
        "discovery": "optimization",
        "optimization": "validation",
        "validation": "robustness",
        "robustness": "oos",
        "oos": "ea_generation",
    }.get(stage)
    return ResearchDecision(stage=stage, status="GO", gates=tuple(gates), next_stage=next_stage)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["discovery", "optimization", "validation", "robustness", "oos"])
    args = parser.parse_args()
    print(decide(args.stage).to_json())
