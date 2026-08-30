"""Fail-closed project repair loop for ForexAI.

The loop audits implementation contracts before any new discovery/OOS run.
It never creates market data, metrics, or candidate results. It reports
problems as deterministic checks so a failed check blocks downstream work.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import json


@dataclass(frozen=True)
class Finding:
    check: str
    status: str
    severity: str
    evidence: str
    remediation: str


def _read(root: Path, rel: str) -> str:
    p = root / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def audit(root: Path) -> dict:
    findings: list[Finding] = []

    protocol = _read(root, "docs/FOREXAI_RESEARCH_LOOP_V2_RESET.md")
    findings.append(Finding(
        "canonical_protocol",
        "PASS" if protocol else "FAIL",
        "critical",
        "reset protocol present" if protocol else "missing canonical reset protocol",
        "Restore the canonical research-loop protocol before discovery.",
    ))

    gate_files = sorted((root / "research/optimization").glob("cost_aware_gate*.py")) if (root / "research/optimization").exists() else []
    gate_text = "\n".join(p.read_text(encoding="utf-8") for p in gate_files)
    year_guard = bool(re.search(r"2022|2023|2024", gate_text)) and bool(re.search(r"2025", gate_text))
    findings.append(Finding(
        "cost_gate_pre_oos_validation",
        "PASS" if year_guard else "FAIL",
        "critical",
        f"inspected {len(gate_files)} cost-aware gate files",
        "Require multi-year pre-OOS evidence plus independent validation; never qualify on validation alone.",
    ))

    workflow_files = list((root / ".github/workflows").glob("cost-aware*.yml")) if (root / ".github/workflows").exists() else []
    workflow_text = "\n".join(p.read_text(encoding="utf-8") for p in workflow_files)
    held_out = "2026" in workflow_text and ("HOLD" in workflow_text.upper() or "OOS" in workflow_text.upper())
    findings.append(Finding(
        "oos_isolation",
        "PASS" if held_out else "WARN",
        "critical",
        f"inspected {len(workflow_files)} cost-aware workflows",
        "Keep 2026 OOS unavailable to discovery/ranking and fail closed if it is loaded.",
    ))

    discovery = _read(root, "research/optimization/cost_aware_discovery.py") + _read(root, "research/optimization/cost_aware_discovery_v14.py")
    wrapper_support = "data.get(\"result\", data)" in discovery or "data.get('result', data)" in discovery
    findings.append(Finding(
        "result_schema_compatibility",
        "PASS" if wrapper_support else "WARN",
        "high",
        "wrapper-aware result extraction detected" if wrapper_support else "wrapper-aware extraction not found in sampled discovery files",
        "Normalize both wrapped and direct result schemas in aggregators and reject malformed records explicitly.",
    ))

    tests = list((root / "tests").glob("test_*.py")) if (root / "tests").exists() else []
    cost_tests = [p for p in tests if "cost" in p.name.lower()]
    findings.append(Finding(
        "regression_tests",
        "PASS" if len(cost_tests) >= 2 else "WARN",
        "high",
        f"found {len(cost_tests)} cost/regression test files",
        "Add regression coverage for gate years, cost accounting, schema wrappers, and OOS isolation.",
    ))

    failed = [f for f in findings if f.status == "FAIL"]
    return {
        "loop": "ForexAI Project Repair Loop v1",
        "fail_closed": True,
        "checks": [asdict(f) for f in findings],
        "status": "BLOCKED" if failed else "READY_FOR_TEST_RUN",
        "blocking_failures": len(failed),
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = audit(root)
    out = root / "artifacts" / "repair_loop"
    out.mkdir(parents=True, exist_ok=True)
    (out / "repair_loop_v1.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 2 if report["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
