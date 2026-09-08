"""G5 wrapper: isolate Momentum + Trend Pullback from the already-tested G2 engine."""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from research.optimization.multi_family_discovery_g2 import (
    catalog,prepare,backtest,rejection_reasons,ExecutionConfig,
    PRE_OOS_YEARS,VALIDATION_MIN_PF,VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES
)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",required=True); ap.add_argument("--output",required=True)
    ap.add_argument("--timeframe",required=True,choices=("M1","M5","M15"))
    ap.add_argument("--spread-pips",type=float,default=.5); ap.add_argument("--slippage-pips",type=float,default=.2)
    a=ap.parse_args()
    d=prepare(__import__("pandas").read_csv(a.data))
    cfg=ExecutionConfig(spread_pips=a.spread_pips,slippage_pips=a.slippage_pips)
    years={y:d[(d.index>=f"{y}-01-01")&(d.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}
    candidates=[p for p in catalog() if p["family"] in ("momentum","trend_pullback")]
    rows=[]; gates=Counter()
    for cid,p in enumerate(candidates,1):
        pre=[{"year":y,"metrics":backtest(years[y],p,cfg)} for y in PRE_OOS_YEARS]
        bad=rejection_reasons(pre)
        for b in bad:gates[b]+=1
        rows.append({"candidate_id":cid,"family":p["family"],"params":p,"pre_oos":pre,"pre_oos_pass":not bad,"rejection_reasons":bad})
    ranked=sorted(rows,key=lambda x:(x["pre_oos_pass"],sum(m["metrics"]["expectancy_R"] for m in x["pre_oos"])),reverse=True)
    qualified=[x for x in ranked if x["pre_oos_pass"]]
    validated=[]
    for x in qualified:
        vm=backtest(years[2025],x["params"],cfg); vr=[]
        if vm["profit_factor"]<VALIDATION_MIN_PF: vr.append(f"validation_pf<{VALIDATION_MIN_PF}")
        if vm["max_dd_pct"]>VALIDATION_MAX_DD_PCT: vr.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
        if vm["trades"]<VALIDATION_MIN_TRADES: vr.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
        if vm["expectancy_R"]<=0 or vm["total_R"]<=0: vr.append("validation_nonpositive_return")
        validated.append({**x,"validation_2025":vm,"validation_pass":not vr,"validation_rejection_reasons":vr})
    family_summary={}
    for fam in ("momentum","trend_pullback"):
        fr=[x for x in rows if x["family"]==fam]
        ranked_f=sorted(fr,key=lambda x:(sum(z["metrics"]["expectancy_R"] for z in x["pre_oos"]),-sum(z["metrics"]["max_dd_pct"] for z in x["pre_oos"])),reverse=True)
        family_summary[fam]={
            "candidate_count":len(fr),
            "pre_oos_qualified":sum(x["pre_oos_pass"] for x in fr),
            "positive_expectancy_year_counts":sorted([
                sum(float(z["metrics"]["expectancy_R"])>0 for z in x["pre_oos"])
                for x in fr
            ],reverse=True)[:10],
            "best_candidate":ranked_f[0],
            "median_pf_by_year":{
                str(y):float(np.median([z["metrics"]["profit_factor"] for x in fr for z in x["pre_oos"] if z["year"]==y]))
                for y in (2022,2023,2024)
            },
            "median_expectancy_by_year":{
                str(y):float(np.median([z["metrics"]["expectancy_R"] for x in fr for z in x["pre_oos"] if z["year"]==y]))
                for y in (2022,2023,2024)
            },
            "median_dd_by_year":{
                str(y):float(np.median([z["metrics"]["max_dd_pct"] for x in fr for z in x["pre_oos"] if z["year"]==y]))
                for y in (2022,2023,2024)
            },
            "median_trades_by_year":{
                str(y):float(np.median([z["metrics"]["trades"] for x in fr for z in x["pre_oos"] if z["year"]==y]))
                for y in (2022,2023,2024)
            },
        }

    payload={
      "schema_version":"forexai.g5.momentum_trend_pullback.v1",
      "research_timeframe":a.timeframe,"real_data_required":True,"synthetic_fallback":False,
      "oos_policy":{"loaded":False,"status":"HELD_OUT","start":"2026-01-01"},
      "execution_model":{"entry":"next_bar_open","cost_pips_per_side":a.spread_pips+a.slippage_pips,"round_trip_cost_pips":2*(a.spread_pips+a.slippage_pips),"same_bar_resolution":"SL first (conservative)","expiry_bars":30,"overlap":"one position at a time","adverse_exit_cost_applied":True},
      "catalog":{"candidate_total":len(rows),"family_counts":dict(Counter(x["family"] for x in rows)),"family_summary":family_summary},
      "result":{"candidate_total":len(rows),"pre_oos_qualified_count":len(qualified),"validation_qualified_count":sum(x["validation_pass"] for x in validated),"top_50_diagnostics":ranked[:50],"gate_rejection_counts_all_candidates":dict(gates),"validated_candidates":validated,"champion":None}
    }
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"candidate_total":len(rows),"pre_oos_qualified":len(qualified),"validation_qualified":sum(x["validation_pass"] for x in validated),"family_counts":payload["catalog"]["family_counts"]}))
if __name__=="__main__": main()
