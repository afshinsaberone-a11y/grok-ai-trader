"""ForexAI G10: M15 regime-transition forensics.
Diagnostic only. No parameter promotion and no 2026 evaluation.
Uses the two G8 M15 regime-momentum candidates and decomposes performance by
trend persistence, ADX-like strength, EMA slope, ATR regime, and transition state.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.regime_stability_forensics_g9 import CANDIDATES, MAX_HOLD
from research.optimization.regime_aware_event_discovery_g6 import prepare, signal
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost

YEARS=(2022,2023,2024,2025)

def enrich(d):
    d=d.copy()
    h,l,c=d.High,d.Low,d.Close
    up=h.diff(); dn=-l.diff()
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    plus_dm=up.where((up>dn)&(up>0),0.0)
    minus_dm=dn.where((dn>up)&(dn>0),0.0)
    atr=tr.rolling(14,min_periods=14).mean()
    pdi=100*plus_dm.rolling(14,min_periods=14).mean()/atr.replace(0,np.nan)
    mdi=100*minus_dm.rolling(14,min_periods=14).mean()/atr.replace(0,np.nan)
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    d["ADX14"]=dx.rolling(14,min_periods=14).mean()
    d["EMA_SLOPE_ATR"]=(d["EMA16"]-d["EMA16"].shift(4))/d["ATR"].replace(0,np.nan)
    d["TREND_PERSIST"]=(d["EMA16"]>d["EMA50"]).astype(int).rolling(8,min_periods=8).mean()
    d["TREND_STATE"]=(d["EMA16"]>d["EMA50"]).astype(int)
    d["ADX_Q"]=d["ADX14"].rolling(96,min_periods=48).rank(pct=True)
    return d

def summarize(rows):
    if not rows:return {"trades":0,"total_R":0.0,"expectancy_R":0.0,"profit_factor":0.0,"win_rate_pct":0.0}
    rs=np.array([x["r"] for x in rows]); gp=rs[rs>0].sum(); gl=abs(rs[rs<=0].sum())
    return {"trades":int(len(rs)),"total_R":round(float(rs.sum()),6),"expectancy_R":round(float(rs.mean()),6),"profit_factor":round(float(gp/gl),6) if gl else (3.0 if gp>0 else 0.0),"win_rate_pct":round(float((rs>0).mean()*100),3)}

def bucket(rows,key):
    groups={}
    for label,pred in key:
        groups[label]=summarize([r for r in rows if pred(r)])
    return groups

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
                entry_i=i+1; entry=apply_entry_cost(float(g.Open.iloc[entry_i]),s,cfg); stop=entry-s*unit; target=entry+s*p["rr"]*unit; pos=s; continue
            age=i-entry_i+1
            hit_sl=float(g.Low.iloc[i])<=stop if pos==1 else float(g.High.iloc[i])>=stop
            hit_tp=float(g.High.iloc[i])>=target if pos==1 else float(g.Low.iloc[i])<=target
            r=None; reason=None
            if hit_sl:r=pos*(apply_exit_cost(stop,pos,cfg)-entry)/unit; reason="SL"
            elif hit_tp:r=pos*(apply_exit_cost(target,pos,cfg)-entry)/unit; reason="TP"
            elif age>=MAX_HOLD:
                ex=float(g.Open.iloc[min(i+1,len(g)-1)]); r=pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit; reason="EXPIRY"
            if r is not None:
                j=max(entry_i-1,0)
                rows.append({"r":float(r),"side":"long" if pos==1 else "short","adx":float(g.ADX14.iloc[j]),"adxq":float(g.ADX_Q.iloc[j]),"slope":float(g.EMA_SLOPE_ATR.iloc[j]),"persist":float(g.TREND_PERSIST.iloc[j]),"state":int(g.TREND_STATE.iloc[j]),"atrq":float(g.ATRq.iloc[j]),"exit":reason})
                pos=0
        if pos!=0:
            j=max(entry_i-1,0); ex=float(g.Open.iloc[-1]); rows.append({"r":float(pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit),"side":"long" if pos==1 else "short","adx":float(g.ADX14.iloc[j]),"adxq":float(g.ADX_Q.iloc[j]),"slope":float(g.EMA_SLOPE_ATR.iloc[j]),"persist":float(g.TREND_PERSIST.iloc[j]),"state":int(g.TREND_STATE.iloc[j]),"atrq":float(g.ATRq.iloc[j]),"exit":"DAY_END"})
    return rows

def analyze(rows):
    finite=lambda r,k:np.isfinite(r.get(k,np.nan))
    out={"overall":summarize(rows),"direction":bucket(rows,[("long",lambda r:r["side"]=="long"),("short",lambda r:r["side"]=="short")]),
      "adx":bucket(rows,[("low",lambda r:finite(r,"adxq") and r["adxq"]<.33),("mid",lambda r:finite(r,"adxq") and .33<=r["adxq"]<.67),("high",lambda r:finite(r,"adxq") and r["adxq"]>=.67)]),
      "trend_persistence":bucket(rows,[("low",lambda r:finite(r,"persist") and r["persist"]<.5),("mid",lambda r:finite(r,"persist") and .5<=r["persist"]<.75),("high",lambda r:finite(r,"persist") and r["persist"]>=.75)]),
      "slope":bucket(rows,[("negative",lambda r:finite(r,"slope") and r["slope"]<-.1),("flat",lambda r:finite(r,"slope") and -.1<=r["slope"]<=.1),("positive",lambda r:finite(r,"slope") and r["slope"]>.1)]),
      "transition":bucket(rows,[("aligned",lambda r:finite(r,"persist") and r["persist"]>=.75),("mixed",lambda r:finite(r,"persist") and .25<=r["persist"]<.75),("unstable",lambda r:finite(r,"persist") and r["persist"]<.25)]),
      "atr":bucket(rows,[("low",lambda r:finite(r,"atrq") and r["atrq"]<.33),("mid",lambda r:finite(r,"atrq") and .33<=r["atrq"]<.67),("high",lambda r:finite(r,"atrq") and r["atrq"]>=.67)])}
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); a=ap.parse_args()
    d=enrich(prepare(pd.read_csv(a.data))); cfg=ExecutionConfig(spread_pips=.5,slippage_pips=.2)
    years={y:d[(d.index>=f"{y}-01-01")&(d.index<f"{y+1}-01-01")] for y in YEARS}
    results={}
    for p in CANDIDATES:
        results[p["id"]]={str(y):analyze(run(years[y],p,cfg)) for y in YEARS}
    payload={"schema_version":"forexai.g10.regime_transition_forensics.v1","real_data_required":True,"synthetic_data":False,"candidate_scope":"G8 top M15 regime_momentum candidates","candidates":CANDIDATES,"execution_model":{"entry":"next_bar_open","round_trip_cost_pips":1.4,"same_bar_resolution":"SL first","expiry_bars":24},"oos_2026":{"loaded":False,"status":"HELD_OUT"},"parameter_selection":{"used_2025":False},"results":results,"champion":None}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps({"candidates":2,"years":list(YEARS),"champion":None}))
if __name__=="__main__":main()
