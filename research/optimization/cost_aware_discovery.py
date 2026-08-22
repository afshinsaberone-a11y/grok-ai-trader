"""Cost-aware discovery on real pre-OOS data only."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from research.optimization.multi_family_discovery import FAMILIES, MIN_TRADES, VALIDATION_MAX_DD, VALIDATION_MIN_PF, _native, catalog, indicators, signal_family
PIP_SIZE=0.0001; DEFAULT_SPREAD_PIPS=0.5; DEFAULT_SLIPPAGE_PIPS=0.2; RISK_PCT=0.005; PRE_OOS_YEARS=(2022,2023,2024)
def round_trip_cost_price(spread_pips:float, slippage_pips:float)->float:
    if spread_pips<0 or slippage_pips<0: raise ValueError("execution costs cannot be negative")
    return 2*(float(spread_pips)+float(slippage_pips))*PIP_SIZE
def backtest_cost_aware(df:pd.DataFrame,family:str,params:dict[str,Any],*,spread_pips=DEFAULT_SPREAD_PIPS,slippage_pips=DEFAULT_SLIPPAGE_PIPS)->dict[str,Any]:
    d=indicators(df,params); sig=signal_family(d,family,params); equity=peak=10000.; maxdd=0.; pos=0; entry=stop=tp=0.; rs=[]; cost=round_trip_cost_price(spread_pips,slippage_pips)
    for i in range(1,len(d)):
        r=d.iloc[i]; atr=r.atr
        if pd.isna(atr) or atr<=0: continue
        if pos==0 and sig.iloc[i]!=0:
            pos=int(sig.iloc[i]); entry=float(r.Close); sd=params["atr_stop"]*float(atr); stop=entry-pos*sd; tp=entry+pos*params["rr"]*sd; continue
        if pos==1 and (r.Low<=stop or r.High>=tp or sig.iloc[i]==-1):
            ex=stop if r.Low<=stop else (tp if r.High>=tp else r.Close); rs.append((ex-entry)/abs(entry-stop)-cost/abs(entry-stop)); equity*=1+RISK_PCT*rs[-1]; pos=0
        elif pos==-1 and (r.High>=stop or r.Low<=tp or sig.iloc[i]==1):
            ex=stop if r.High>=stop else (tp if r.Low<=tp else r.Close); rs.append((entry-ex)/abs(stop-entry)-cost/abs(stop-entry)); equity*=1+RISK_PCT*rs[-1]; pos=0
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else (float("inf") if gp>0 else 0.)
    return {"trades":n,"win_rate":round(100*wins/n,2) if n else 0.,"total_R":round(sum(rs),2),"expectancy_R":round(sum(rs)/n,4) if n else 0.,"profit_factor":round(pf,3) if np.isfinite(pf) else "inf","max_dd_pct":round(100*maxdd,2),"final_equity":round(equity,2),"spread_pips":float(spread_pips),"slippage_pips":float(slippage_pips),"round_trip_cost_pips":round(2*(spread_pips+slippage_pips),4)}
def _pf(m): return 3. if m["profit_factor"]=="inf" else float(m["profit_factor"])
def score_cost_aware(metrics):
    pfs=[_pf(x["metrics"]) for x in metrics]; ex=[float(x["metrics"]["expectancy_R"]) for x in metrics]; dd=[float(x["metrics"]["max_dd_pct"]) for x in metrics]
    if any(int(x["metrics"]["trades"])<MIN_TRADES for x in metrics) or sum(v>0 for v in ex)<2 or min(pfs)<1.0: return -999.
    avg=sum(pfs)/3; total=sum(float(x["metrics"]["total_R"]) for x in metrics)
    return round(2.5*min(max(min(pfs),0),2)/2+1.5*min(max(avg,0),2)/2+sum(v>0 for v in ex)/3+1.5*np.tanh(total/150)-2.5*min(max(max(dd),0),100)/100,6)
def discover_family_cost_aware(df,family,*,spread_pips,slippage_pips):
    years={y:df[(df.index>=f"{y}-01-01")&(df.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}; results=[]
    for j,params in enumerate(catalog()[family]):
        pre=[{"year":y,"metrics":backtest_cost_aware(years[y],family,params,spread_pips=spread_pips,slippage_pips=slippage_pips)} for y in PRE_OOS_YEARS]; results.append({"family":family,"candidate":j+1,"params":params,"cost_aware_robustness_score":score_cost_aware(pre),"pre_oos_cost_aware":pre})
    results.sort(key=lambda x:(-x["cost_aware_robustness_score"],x["candidate"])); finalists=[x for x in results if x["cost_aware_robustness_score"]>-999][:50]; validated=[]
    for x in finalists:
        vm=backtest_cost_aware(years[2025],family,x["params"],spread_pips=spread_pips,slippage_pips=slippage_pips); q=_pf(vm)>=VALIDATION_MIN_PF and float(vm["max_dd_pct"])<=VALIDATION_MAX_DD and int(vm["trades"])>=MIN_TRADES; validated.append({**x,"validation_2025_cost_aware":vm,"validation_qualifies":q})
    qualified=[x for x in validated if x["validation_qualifies"]]; qualified.sort(key=lambda x:(-x["cost_aware_robustness_score"],x["candidate"]))
    return {"family":family,"candidate_total":len(results),"cost_profile":{"spread_pips":spread_pips,"slippage_pips":slippage_pips,"round_trip_cost_pips":2*(spread_pips+slippage_pips)},"qualified_count":len(qualified),"champion":qualified[0] if qualified else None,"top_50":validated}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--family",choices=FAMILIES,required=True); ap.add_argument("--output",default="artifacts/cost_aware_family.json"); ap.add_argument("--spread-pips",type=float,default=DEFAULT_SPREAD_PIPS); ap.add_argument("--slippage-pips",type=float,default=DEFAULT_SLIPPAGE_PIPS); a=ap.parse_args()
    if a.spread_pips<0 or a.slippage_pips<0: raise SystemExit("execution costs cannot be negative")
    df=pd.read_csv(a.data); df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True); df=df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("timestamp"); result=discover_family_cost_aware(df,a.family,spread_pips=a.spread_pips,slippage_pips=a.slippage_pips)
    report={"schema_version":"forexai.cost_aware_discovery.v1","result":result,"oos_policy":{"loaded":False,"start":"2026-01-01","status":"HELD_OUT"},"real_data_required":True,"synthetic_fallback":False,"pre_oos_gate":{"years":list(PRE_OOS_YEARS),"min_profitable_years":2,"min_pf_each_year":1.0}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(_native(report),indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(_native({"family":a.family,"qualified_count":result["qualified_count"],"champion":result["champion"],"cost_profile":result["cost_profile"]}),indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
