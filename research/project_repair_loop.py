#!/usr/bin/env python3
"""Safety-contract audit/repair loop for grok-ai-trader EAs.

Does NOT claim live profitability. Checks structural safety rules.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

CONTRACT = (
    "// GRK-SAFETY-CONTRACT-051\n"
    "// Hard StopLoss on every order. No averaging-up / recovery sizing. Risk<=0.6.\n"
    "// No grid. No martingale. Closed-bar entries only. Daily profit/loss halt.\n"
)

FORBIDDEN = [
    re.compile(r"\bmartingale\b", re.I),
    re.compile(r"\bgrid\b", re.I),
    re.compile(r"averag(e|ing)[-_ ]?up", re.I),
    re.compile(r"recover(y)?[-_ ]?lot", re.I),
    re.compile(r"\bdouble\s+lot\b", re.I),
]

COMMENT_OR_STRING = re.compile(
    r"""//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"""",
    re.S,
)

def _executable_code(text: str) -> str:
    """Remove comments and string literals before scanning executable code."""
    return COMMENT_OR_STRING.sub(" ", text)



def _issues_to_checks(path: Path, issues: list[str]) -> list[dict]:
    checks = []
    if issues:
        for issue in issues:
            checks.append(
                {
                    "check": f"{path.name}: {issue}",
                    "status": "FAIL",
                    "severity": "high",
                    "evidence": issue,
                    "remediation": "Add hard SL, risk cap, single position, closed-bar gate, safety contract.",
                }
            )
    else:
        checks.append(
            {
                "check": f"{path.name}: safety contract",
                "status": "PASS",
                "severity": "info",
                "evidence": "structural rules present",
                "remediation": "",
            }
        )
    return checks


def audit_mq5(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    code = _executable_code(text)
    issues: list[str] = []

    trade_capable = bool(
        re.search(r"trade\.(Buy|Sell)\s*\(", code)
        or re.search(r"\bOrderSend\s*\(", code)
    )

    for rx in FORBIDDEN:
        if rx.search(code):
            issues.append(f"forbidden executable pattern: {rx.pattern}")

    if trade_capable:
        if "StopLoss" not in code and not re.search(r"\bsl\s*[,\=]", code, re.I):
            issues.append("no obvious StopLoss usage")

        if not re.search(r"trade\.(Buy|Sell)\s*\(", code) and not re.search(r"\bOrderSend\s*\(", code):
            issues.append("no executable order-send path")

        for m in re.finditer(r"trade\.(Buy|Sell)\s*\(([^;]+)\)", code):
            args = m.group(2)
            if args.count(",") < 3:
                issues.append(f"{m.group(1)} call may miss SL/TP args")

        if "RiskPercent" in text and not re.search(r"if\s*\(\s*RiskPercent\s*>\s*0\.6\s*\)", code):
            issues.append("missing OnInit RiskPercent hard cap 0.6")

        if "MaxPositions" in text and not re.search(r"if\s*\(\s*MaxPositions\s*!=\s*1\s*\)", code):
            issues.append("missing OnInit MaxPositions==1 guard")

        if "SetExpertMagicNumber" not in code:
            issues.append("missing magic number")

        if "last_bar" not in code and "iTime" not in code:
            issues.append("possible every-tick entries (no new-bar gate)")
    else:
        if "EA_ROLE: ANALYTICS_ONLY_NO_ORDERS" not in text:
            issues.append("non-trading EA must declare EA_ROLE: ANALYTICS_ONLY_NO_ORDERS")

    if "GRK-SAFETY-CONTRACT" not in text:
        issues.append("missing safety contract comment")

    return issues


def maybe_fix(path: Path, issues: list[str]) -> bool:
    if not issues:
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    changed = False
    if "GRK-SAFETY-CONTRACT" not in text:
        text = text.rstrip() + "\n" + CONTRACT
        changed = True
    else:
        text2 = re.sub(r"GRK-SAFETY-CONTRACT-\d+", "GRK-SAFETY-CONTRACT-051", text)
        if text2 != text:
            text = text2
            changed = True
    if changed:
        path.write_text(text + ("\n" if not text.endswith("\n") else ""), encoding="utf-8")
    return changed


def audit(root: Path) -> dict:
    ea_dir = Path(root) / "ea"
    files = sorted(ea_dir.glob("*.mq5")) if ea_dir.is_dir() else []
    checks: list[dict] = []
    remaining = 0
    for f in files:
        issues = audit_mq5(f)
        checks.extend(_issues_to_checks(f, issues))
        if issues:
            remaining += 1
    if not files:
        checks.append(
            {
                "check": "ea directory present",
                "status": "FAIL",
                "severity": "high",
                "evidence": "no mq5 files",
                "remediation": "add EA under ea/",
            }
        )
        remaining = 1
    status = "READY_FOR_TEST_RUN" if remaining == 0 else "BLOCKED"
    return {
        "fail_closed": True,
        "status": status,
        "checks": checks,
        "files": [str(f) for f in files],
    }


def run(root: Path, do_fix: bool, max_loops: int) -> str:
    ea_dir = root / "ea"
    files = sorted(ea_dir.glob("*.mq5")) if ea_dir.is_dir() else []
    lines = ["# EA_AUDIT_LOOP_051_REPORT", "", f"root: {root}", f"files: {len(files)}", ""]
    remaining: list = []
    for loop in range(1, max_loops + 1):
        remaining = []
        lines.append(f"## loop {loop}")
        for f in files:
            issues = audit_mq5(f)
            if do_fix and issues:
                maybe_fix(f, issues)
                issues = audit_mq5(f)
            if issues:
                remaining.append((f, issues))
                lines.append(f"- FAIL {f.name}: {issues}")
            else:
                lines.append(f"- PASS {f.name}")
        lines.append("")
        if not remaining:
            lines.append("STATUS: CLEAN")
            break
    else:
        lines.append("STATUS: ISSUES_REMAIN")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--fix", action="store_true")
    p.add_argument("--max-loops", type=int, default=4)
    args = p.parse_args()
    root = Path(args.root).resolve()
    report = run(root, args.fix, args.max_loops)
    out = root / "research" / "EA_AUDIT_LOOP_051_REPORT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    return 0 if "STATUS: CLEAN" in report else 1


if __name__ == "__main__":
    raise SystemExit(main())
