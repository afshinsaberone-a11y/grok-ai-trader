#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

FORBIDDEN = [
    (r"martin ?gale", "martingale_forbidden"),
    (r"grid", "grid_forbidden"),
    (r"average.?down", "averaging_down_forbidden"),
    (r"no stop", "missing_stop"),
    (r"بدون استاپ", "missing_stop"),
    (r"ضمانت سود|guaranteed profit", "profit_guarantee_forbidden"),
]
REQUIRED_EA = [
    ("risk_cap", r"InpRiskPercent|RiskPercent|0\.5"),
    ("spread_filter", r"spread|SYMBOL_SPREAD"),
    ("stop_loss", r"req\.sl|StopLoss|sl ="),
    ("no_grid_flag", r"InpAllowGrid\s*=\s*false"),
    ("no_martingale_flag", r"InpAllowMartingale\s*=\s*false"),
]

@dataclass
class Finding:
    path: str
    rule: str
    detail: str
    severity: str

def scan_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    findings = []
    for pat, rule in FORBIDDEN:
        if re.search(pat, lower):
            if "forbidden" in lower or "ممنوع" in text or "false" in lower:
                if rule in {"grid_forbidden", "martingale_forbidden"}:
                    continue
            findings.append(Finding(str(path), rule, pat, "high"))
    return findings

def scan_ea_required(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings = []
    for name, pat in REQUIRED_EA:
        if not re.search(pat, text):
            findings.append(Finding(str(path), f"missing_{name}", pat, "high"))
    return findings

def iter_targets(root: Path):
    out = []
    for rel in ("ea", "strategies", "research"):
        d = root / rel
        if d.exists():
            out.extend([p for p in d.rglob("*") if p.suffix in {".mq5", ".py", ".md"}])
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--max-loops", type=int, default=5)
    a = p.parse_args()
    root = Path(a.root).resolve()
    history = []
    remaining = []
    for i in range(1, a.max_loops + 1):
        findings = []
        for path in iter_targets(root):
            findings.extend(scan_file(path))
            if path.suffix == ".mq5" and path.name.startswith("GRK_Hybrid_Regime"):
                findings.extend(scan_ea_required(path))
        history.append({"loop": i, "count": len(findings)})
        remaining = findings
        if not findings:
            break
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "id": "GRK-FX-2026-018",
        "loops": history,
        "remaining": [asdict(f) for f in remaining],
        "clean": len(remaining) == 0,
        "disclaimer": "Static contract only. Not a profitability guarantee.",
    }
    out = root / "research" / "EA_AUDIT_LOOP_018.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["clean"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
