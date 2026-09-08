"""ForexAI G9: M15 regime-stability/year-shift forensics.
Diagnostic only; never promotes or selects parameters.
2022-2024 discovery context, 2025 diagnostic holdout, 2026 excluded.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.regime_aware_event_discovery_g6 import prepare, signal
from research.optimization.execution_contract_v1 import ExecutionConfig,apply_entry_cost,apply_exit_cost

YEARS=(2022,2023,2024,2025)
CANDIDATES=(
 {"id":"atrpct_050","family":"regime_momentum","fast":16,"slow":50,"atr_pct":0.50,"atr_mult":1.0,"rr":2.0},
 {"id":"atrpct_065","family":"regime_momentum","fast":16,"slow":50,"atr_pct":0.65,"atr_mult":1.0,"rr":2.0},
)
MAX_HOLD=24

def run(d,p,cfg):
 rows=[]
 for _,g in d.groupby(d.index.date,sort=True):
  pos=0; entry=stop=target=unit=0.; entry_i=-1
  for i in range(50,len(g)-1):
   if pos==0:
    s=signal(g,i,p)
    if not s: continue
    atr=float(g.ATR.iloc[i]); unit=p["atr_mult"]*atr
    if not np.isfinite(unit) or unit<=0: continue
    entry_i=i+1; entry=apply_entry_cost(float(g.Open.iloc[entry_i]),s,cfg); stop=entry-s*unit; target=entry+s*p["rr"]*unit; pos=s
    continue
   age=i-entry_i+1; hit_sl=float(g.Low.iloc[i])<=stop if pos==1 else float(g.High.iloc[i])>=stop; hit_tp=float(g.High.iloc[i])>=target if pos==1 else float(g.Low.iloc[i])<=target
   r=None; reason=None
   if hit_sl:r=pos*(apply_exit_cost(stop,pos,cfg)-entry)/unit; reason="SL"
   elif hit_tp:r=pos*(apply_exit_cost(target,pos,cfg)-entry)/unit; reason="TP"
   elif age>=MAX_HOLD:
    ex=float(g.Open.iloc[min(i+1,len(g)-1)]); r=pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit; reason="EXPIRY"
   if r is not None:
    atrq=float(g.ATRq.iloc[entry_i-1]); trend=abs(float(g[f"EMA{p['fast']}"].iloc[entry_i-1])-float(g[f"EMA{p['slow']}"].iloc[entry_i-1]))/float(g.ATR.iloc[entry_i-1]) if float(g.ATR.iloc[entry_i-1])>0 else np.nan
    rows.append({"r":float(r),"side":"long" if pos==1 else "short","atrq":atrq,"trend_strength":trend,"exit":reason}); pos=0
  if pos!=0:
   ex=float(g.Open.iloc[-1]); rows.append({"r":float(pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit),"side":"long" if pos==1 else "short","atrq":float(g.ATRq.iloc[max(entry_i-1,0)]),"trend_strength":np.nan,"exit":"DAY_END"})
 return rows

def summarize(rows):
 if not rows:return {"trades":0,"total_R":0.0,"expectancy_R":0.0,"profit_factor":0.0,"win_rate_pct":0.0}
 rs=np.array([x["r"] for x in rows]); gp=rs[rs>0].sum(); gl=abs(rs[rs<=0].sum())
 return {"trades":int(len(rs)),"total_R":round(float(rs.sum()),6),"expectancy_R":round(float(rs.mean()),6),"profit_factor":round(float(gp/gl),6) if gl else (3.0 if gp>0 else 0.0),"win_rate_pct":round(float((rs>0).mean()*100),3)}

def bucket(rows):
 out={}
 for side in ("long","short"):
  sr=[x for x in rows if x["side"]==side]; out[side]=summarize(sr)
 for name,fn in (("atr_low",lambda x:x["atrq"]<.33),("atr_mid",lambda x:.33<=x["atrq"]<.67),("atr_high",lambda x:x["atrq"]>=.67),("trend_low",lambda x:x["trend_strength"]<.5),("trend_mid",lambda x:.5<=x["trend_strength"]<1.0),("trend_high",lambda x:x["trend_strength"]>=1.0)):
  br=[x for x in rows if np.isfinite(x.get("atrq",np.nan) if name.startswith("atr") else x.get("trend_strength",np.nan)) and fn(x)]; out[name]=summarize(br)
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); a=ap.parse_args()
 d=prepare(pd.read_csv(a.data)); cfg=ExecutionConfig(spread_pips=.5,slippage_pips=.2)
 years={y:d[(d.index>=f"{y}-01-01")&(d.index<f"{y+1}-01-01")] for y in YEARS}
 results={}
 for p in CANDIDATES:
  results[p["id"]]={str(y):{"overall":summarize((r:=run(years[y],p,cfg))),"regimes":bucket(r)} for y in YEARS}
 payload={"schema_version":"forexai.g9.regime_stability_forensics.v1","real_data_required":True,"synthetic_data":False,"candidate_scope":"G8 top M15 regime_momentum candidates","candidates":CANDIDATES,"execution_model":{"entry":"next_bar_open","round_trip_cost_pips":1.4,"same_bar_resolution":"SL first","expiry_bars":24},"oos_2026":{"loaded":False,"status":"HELD_OUT"},"parameter_selection":{"used_2025":False},"results":results,"champion":None}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps({"candidates":len(CANDIDATES),"years":list(YEARS),"champion":None}))
if __name__=="__main__":main()
