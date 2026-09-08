"""G8: M15 candidate forensics from G7.

Selects candidates by pre-OOS diagnostics at zero and 0.7 pip round-trip,
then reports year-by-year performance and cost degradation. No 2026 use.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    d=json.loads(Path(a.artifact).read_text(encoding="utf-8"))
    rows=d["candidates"]
    scored=[]
    for r in rows:
        c0=r["costs"]["0.0"]; c07=r["costs"]["0.7"]; c14=r["costs"]["1.4"]
        score=(c0["sum_expectancy"] + max(0,c07["sum_expectancy"])*2
               + 0.25*c0["min_pf"] - 0.05*c0["max_dd"])
        scored.append({
            "family":r["family"],"params":r["params"],
            "diagnostic_score":round(score,6),
            "cost_profiles":{
                "0.0":c0,"0.7":c07,"1.4":c14
            },
            "validation_2025":{"0.0":r["validation_2025"]["0.0"],"0.7":r["validation_2025"]["0.7"],"1.4":r["validation_2025"]["1.4"]},
        })
    scored.sort(key=lambda x:x["diagnostic_score"],reverse=True)
    payload={
      "schema_version":"forexai.g8.m15_candidate_forensics.v1",
      "source_g7_artifact":a.artifact,
      "selection_scope":"all 108 G7 candidates",
      "top_10":scored[:10],
      "cost_robust_candidates":{
        "at_0.0":[x for x in scored if x["cost_profiles"]["0.0"]["positive_years"]>=2 and x["cost_profiles"]["0.0"]["min_pf"]>=1.05 and x["cost_profiles"]["0.0"]["max_dd"]<=35],
        "at_0.7":[x for x in scored if x["cost_profiles"]["0.7"]["positive_years"]>=2 and x["cost_profiles"]["0.7"]["min_pf"]>=1.05 and x["cost_profiles"]["0.7"]["max_dd"]<=35]
      },
      "policy":{"oos_2026_used":False,"synthetic_data":False,"gates_unchanged":True},
      "champion":None
    }
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"top_10":[{"family":x["family"],"params":x["params"],"score":x["diagnostic_score"],"cost0_sumE":x["cost_profiles"]["0.0"]["sum_expectancy"],"cost07_sumE":x["cost_profiles"]["0.7"]["sum_expectancy"],"cost14_sumE":x["cost_profiles"]["1.4"]["sum_expectancy"]} for x in scored[:10]],"robust0":len(payload["cost_robust_candidates"]["at_0.0"]),"robust07":len(payload["cost_robust_candidates"]["at_0.7"])},indent=2))
if __name__=="__main__":main()
