"""Audit active research engines for common execution/OOS semantics."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TARGETS=[
"research/optimization/cost_aware_discovery_v30.py",
"research/optimization/cost_aware_targeted_momentum_v15_5.py",
"research/optimization/cost_aware_structure_transition_v24.py",
"research/optimization/robustness_validation_v29_1.py",
]
def main():
 rows=[]
 for rel in TARGETS:
  p=ROOT/rel
  if not p.exists(): rows.append({"file":rel,"status":"MISSING"}); continue
  s=p.read_text(encoding="utf-8")
  rows.append({"file":rel,"status":"OK","unified_contract": "execution_contract_v1" in s,"next_bar_open":("next_bar_open" in s or "next-bar-open" in s),"cost_1_4":("1.4" in s),"sl_first":("SL first" in s or "same_bar_sl_first" in s),"oos_guard":("oos" in s.lower())})
 report={"schema":"forexai.execution_research_audit.v1","gate":"cost_aware_gate_v14","oos":"2026-01-01 held out","targets":rows,"decision":"STANDARDIZE_ACTIVE_ENGINES_BEFORE_NEW_DISCOVERY"}
 Path("artifacts").mkdir(exist_ok=True);Path("artifacts/execution-research-audit-v1.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2))
if __name__=="__main__": main()
