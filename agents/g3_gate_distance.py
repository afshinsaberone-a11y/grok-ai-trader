"""G3 gate-distance diagnostics."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--artifact",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    d=json.loads(Path(a.artifact).read_text(encoding="utf-8"))
    rows=d.get("result",{}).get("top_50_diagnostics",[])
    scored=[]
    for x in rows:
        ys={int(z["year"]):z["metrics"] for z in x.get("pre_oos",[])}
        if set(ys)!={2022,2023,2024}: continue
        pf_gap=sum(max(0.0,1.05-float(ys[y]["profit_factor"])) for y in ys)
        exp_gap=sum(max(0.0,-float(ys[y]["expectancy_R"])) for y in ys)
        dd_gap=sum(max(0.0,float(ys[y]["max_dd_pct"])-35.0) for y in ys)
        trade_gap=sum(max(0,int(100-ys[y]["trades"])) for y in ys)
        positive_years=sum(float(ys[y]["expectancy_R"])>0 for y in ys)
        score=pf_gap+10*exp_gap+0.02*dd_gap+0.005*trade_gap
        scored.append({"candidate_id":x.get("candidate_id"),"params":x.get("params"),
          "score_lower_is_better":round(score,8),"positive_expectancy_years":positive_years,
          "pf_gap_sum":round(pf_gap,6),"expectancy_gap_sum":round(exp_gap,6),
          "dd_gap_sum_pct":round(dd_gap,4),"trade_gap_sum":trade_gap,"year_metrics":ys})
    scored.sort(key=lambda x:(-x["positive_expectancy_years"],x["score_lower_is_better"]))
    payload={"schema":"forexai.g3_gate_distance.v1","source_artifact":a.artifact,
      "candidate_scope":"stored top_50_diagnostics","candidates_ranked":scored,
      "policy":{"gates_unchanged":True,"oos_2026_used":False,"synthetic_data":False}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
