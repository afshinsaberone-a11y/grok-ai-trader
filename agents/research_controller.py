"""Deterministic evidence/content gate controller for ForexAI agents."""
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
        if root.exists():
            for pattern in patterns:
                hits.extend(p for p in root.rglob(pattern) if p.is_file())
    return sorted(set(hits))

def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None

def _walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk(value)

def _truthy_key(obj: Any, keys: set[str]) -> bool:
    return any(any(k in keys and v is True for k, v in node.items()) for node in _walk(obj) if isinstance(node, dict))

def _first_value(obj: Any, keys: set[str]) -> Any | None:
    for node in _walk(obj):
        if isinstance(node, dict):
            for key in keys:
                if key in node:
                    return node[key]
    return None

def _gate_real_evidence() -> Gate:
    files = _find_evidence(("*.json", "*.txt", "*.md"))
    return Gate("evidence_present", bool(files), str(len(files)) + " artifact/report files" if files else "", "Inspectable evidence exists." if files else "No artifact/report evidence is available.")

def _gate_no_synthetic_fallback() -> Gate:
    matches: list[Path] = []
    for path in _find_evidence(("*.json",)):
        data = _read_json(path)
        if data is not None and _truthy_key(data, {"synthetic", "synthetic_fallback", "used_synthetic_data"}):
            matches.append(path)
    return Gate("no_synthetic_fallback", not matches, ", ".join(str(p.relative_to(REPO_ROOT)) for p in matches[:10]), "Synthetic-data flag found." if matches else "No positive synthetic-data flag found; provenance must still be verified by data gates.")

def _gate_execution_contract() -> Gate:
    for path in _find_evidence(("*execution*.json", "*execution*.md", "*audit*.json", "*audit*.md")):
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "execution_contract_v1" in text and "sl-first" in text and "1.4" in text:
            return Gate("execution_contract", True, str(path.relative_to(REPO_ROOT)), "Unified execution contract is explicitly recorded.")
    return Gate("execution_contract", False, "", "No artifact explicitly records execution_contract_v1 + SL-first + 1.4 pip round trip.")

def _gate_discovery_content() -> Gate:
    files = _find_evidence(("*discovery*.json", "*aggregate*.json", "*.json"))
    for path in files:
        data = _read_json(path)
        if not isinstance(data, (dict, list)):
            continue
        if _first_value(data, {"family", "strategy_family"}) is None:
            continue
        if _first_value(data, {"discovery_years", "years"}) is None:
            continue
        if _truthy_key(data, {"oos_used_for_selection", "used_oos_for_selection"}):
            return Gate("discovery_content", False, str(path.relative_to(REPO_ROOT)), "Discovery artifact explicitly reports OOS contamination.")
        return Gate("discovery_content", True, str(path.relative_to(REPO_ROOT)), "Discovery artifact contains family and year information and no positive OOS-selection flag.")
    return Gate("discovery_content", False, "", "No sufficiently structured discovery artifact was found.")

def _gate_validation_content() -> Gate:
    files = _find_evidence(("*validation*.json", "*robustness*.json", "*.json"))
    for path in files:
        data = _read_json(path)
        if not isinstance(data, (dict, list)):
            continue
        validation_pass = _first_value(data, {"validation_pass", "strict_validation_pass", "pass"})
        if validation_pass is True:
            pf = _first_value(data, {"pf", "profit_factor", "validation_pf"})
            trades = _first_value(data, {"trades", "trade_count", "validation_trades"})
            if isinstance(pf, (int, float)) and isinstance(trades, (int, float)):
                return Gate("validation_content", True, str(path.relative_to(REPO_ROOT)), f"Validation pass with PF={pf}, trades={trades} explicitly recorded.")
    return Gate("validation_content", False, "", "No validation artifact with explicit passing status, PF and trade count was found.")

def _gate_robustness_content() -> Gate:
    files = _find_evidence(("*robustness*.json", "*.json"))
    for path in files:
        data = _read_json(path)
        if not isinstance(data, (dict, list)):
            continue
        robust = _first_value(data, {"robustness_pass", "robust_pass"})
        ready = _first_value(data, {"ready_for_oos"})
        if robust is True and ready is True:
            return Gate("robustness_content", True, str(path.relative_to(REPO_ROOT)), "Robustness pass and ready_for_oos are both explicitly true.")
    return Gate("robustness_content", False, "", "No artifact proves both robustness_pass=true and ready_for_oos=true.")

def _gate_oos_content() -> Gate:
    files = _find_evidence(("*oos*.json", "*oos*.md", "*.json"))
    for path in files:
        data = _read_json(path)
        if not isinstance(data, (dict, list)):
            continue
        year = _first_value(data, {"oos_year", "year"})
        status = _first_value(data, {"status"})
        if year == 2026 and isinstance(status, str) and "hold" in status.lower():
            return Gate("oos_content", True, str(path.relative_to(REPO_ROOT)), "2026 is explicitly marked held out.")
    return Gate("oos_content", False, "", "No explicit 2026 held-out OOS evidence was found.")

def decide(stage: str) -> ResearchDecision:
    if stage == "discovery":
        gates = [_gate_real_evidence(), _gate_no_synthetic_fallback(), _gate_execution_contract(), _gate_discovery_content()]
    elif stage == "optimization":
        gates = [_gate_real_evidence(), _gate_no_synthetic_fallback(), _gate_execution_contract(), _gate_discovery_content()]
    elif stage == "validation":
        gates = [_gate_real_evidence(), _gate_no_synthetic_fallback(), _gate_execution_contract(), _gate_discovery_content(), _gate_validation_content()]
    elif stage == "robustness":
        gates = [_gate_real_evidence(), _gate_no_synthetic_fallback(), _gate_execution_contract(), _gate_validation_content(), _gate_robustness_content()]
    elif stage == "oos":
        gates = [_gate_real_evidence(), _gate_no_synthetic_fallback(), _gate_execution_contract(), _gate_robustness_content(), _gate_oos_content()]
    else:
        raise ValueError(f"unsupported stage: {stage}")
    if any(not gate.passed for gate in gates):
        return ResearchDecision(stage, "HOLD", tuple(gates), None)
    next_stage = {"discovery": "optimization", "optimization": "validation", "validation": "robustness", "robustness": "oos", "oos": "ea_generation"}[stage]
    return ResearchDecision(stage, "GO", tuple(gates), next_stage)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["discovery", "optimization", "validation", "robustness", "oos"])
    print(decide(parser.parse_args().stage).to_json())
