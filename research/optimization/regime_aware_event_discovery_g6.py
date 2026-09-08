"""ForexAI G6: event-based regime-aware M5 discovery.

Families:
- regime_momentum: EMA crossover event + ROC + ATR percentile regime
- regime_pullback: trend regime + one-bar pullback/reclaim event

Discovery: 2022-2024
Validation: 2025
OOS 2026: held out
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.cost_aware_gate_v14 import (
    MIN_EXPECTANCY_R,MIN_PF_EACH_YEAR,MIN_PROFITABLE_YEARS,
    MIN_TRADES_EACH_YEAR,PRE_OOS_YEARS,PRE_OOS_MAX_DD_PCT,
    VALIDATION_MAX_DD_PCT,VALIDATION_MIN_PF,VALIDATION_MIN_TRADES
)
from research.optimization.execution_contract_v1 import ExecutionConfig,apply_entry_cost,apply_exit_cost,validate_ohlc

MAX_HOLD=24

def catalog():
    out=[]
    for family in ("regime_momentum","regime_pullback"):
        for fast,slow in ((8,26),(12,34),(16,50)):
            for atr_pct in (0.35,0.50,0.65):
                for atr_mult in (1.0,1.5):
                    for rr in (1.2,1.5,2.0):
                        out.append({"family":family,"fast":fast,"slow":slow,"atr_pct":atr_pct,"atr_mult":atr_mult,"rr":rr})
    return out

def prepare(raw):
    d=raw.rename(columns={"timestamp":"Timestamp","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).copy()
    d["Timestamp"]=pd.to_datetime(d["Timestamp"],utc=True); d=d.set_index("Timestamp").sort_index(); validate_ohlc(d)
    prev=d.Close.shift(1)
    tr=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1)
    d["ATR"]=tr.rolling(14,min_periods=14).mean()
    for n in (8,12,16,26,34,50): d[f"EMA{n}"]=d.Close.ewm(span=n,adjust=False).mean()
    delta=d.Close.diff(); up=delta.clip(lower=0); dn=-delta.clip(upper=0)
    rs=up.rolling(14).mean()/dn.rolling(14).mean().replace(0,np.nan); d["RSI"]=100-100/(1+rs)
    d["ROC3"]=d.Close.pct_change(3); d["ROC6"]=d.Close.pct_change(6)
    d["ATRq"]=d.ATR.rolling(96,min_periods=48).rank(pct=True)
    d["day"]=d.index.date
    return d

def metrics(rs):
    n=len(rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0))
    pf=gp/gl if gl else (3.0 if gp>0 else 0.0)
    eq=peak=10000.; dd=0.
    for r in rs:
        eq*=1+0.005*r; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
    return {"trades":n,"win_rate_pct":round(100*sum(x>0 for x in rs)/n,2) if n else 0.0,
            "total_R":round(float(sum(rs)),4),"expectancy_R":round(float(sum(rs))/n,6) if n else 0.0,
            "profit_factor":round(float(pf),4),"max_dd_pct":round(100*dd,4),"final_equity":round(eq,4)}

def signal(g,i,p):
    fast=float(g[f"EMA{p['fast']}"].iloc[i]); slow=float(g[f"EMA{p['slow']}"].iloc[i])
    pf=float(g[f"EMA{p['fast']}"].iloc[i-1]); ps=float(g[f"EMA{p['slow']}"].iloc[i-1])
    aq=float(g.ATRq.iloc[i]); c=float(g.Close.iloc[i]); o=float(g.Open.iloc[i])
    if not np.isfinite(aq) or aq<p["atr_pct"]: return 0
    if p["family"]=="regime_momentum":
        up=fast>slow and pf<=ps; dn=fast<slow and pf>=ps
        roc=max(abs(float(g.ROC3.iloc[i])),abs(float(g.ROC6.iloc[i])))
        if up and roc>0:return 1
        if dn and roc>0:return -1
    else:
        if fast>slow and pf>ps and c>fast and float(g.Low.iloc[i])<=fast and c>o:return 1
        if fast<slow and pf<ps and c<fast and float(g.High.iloc[i])>=fast and c<o:return -1
    return 0

def backtest(d,p,cfg):
    rs=[]
    for _,g in d.groupby("day",sort=True):
        pos=0; entry=stop=target=0.; entry_i=-1
        for i in range(50,len(g)-1):
            if pos==0:
                s=signal(g,i,p)
                if not s: continue
                atr=float(g.ATR.iloc[i])
                if not np.isfinite(atr) or atr<=0: continue
                entry_i=i+1; entry=apply_entry_cost(float(g.Open.iloc[entry_i]),s,cfg)
                unit=p["atr_mult"]*atr; stop=entry-s*unit; target=entry+s*p["rr"]*unit; pos=s; continue
            age=i-entry_i+1
            hit_sl=float(g.Low.iloc[i])<=stop if pos==1 else float(g.High.iloc[i])>=stop
            hit_tp=float(g.High.iloc[i])>=target if pos==1 else float(g.Low.iloc[i])<=target
            unit=p["atr_mult"]*float(g.ATR.iloc[entry_i-1])
            if not np.isfinite(unit) or unit<=0: continue
            r=None
            if hit_sl:r=pos*(apply_exit_cost(stop,pos,cfg)-entry)/unit
            elif hit_tp:r=pos*(apply_exit_cost(target,pos,cfg)-entry)/unit
            elif age>=MAX_HOLD:
                ex=float(g.Open.iloc[min(i+1,len(g)-1)]); r=pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit
            if r is not None: rs.append(float(r)); pos=0
        if pos!=0:
            ex=float(g.Open.iloc[-1]); unit=p["atr_mult"]*float(g.ATR.iloc[max(entry_i-1,0)])
            if np.isfinite(unit) and unit>0:rs.append(float(pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit))
    return metrics(rs)

def reject(pre):
    by={int(x["year"]):x["metrics"] for x in pre}; bad=[]
    for y in PRE_OOS_YEARS:
        m=by[y]
        if m["trades"]<MIN_TRADES_EACH_YEAR:bad.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if m["profit_factor"]<MIN_PF_EACH_YEAR:bad.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if m["expectancy_R"]<=MIN_EXPECTANCY_R:bad.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
        if m["max_dd_pct"]>PRE_OOS_MAX_DD_PCT:bad.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
    if sum(by[y]["expectancy_R"]>0 for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS:bad.append("profitable_years<3")
    return bad

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); ap.add_argument("--timeframe",required=True,choices=("M1","M5","M15")); ap.add_argument("--spread-pips",type=float,default=.5); ap.add_argument("--slippage-pips",type=float,default=.2)
    a=ap.parse_args(); d=prepare(pd.read_csv(a.data)); cfg=ExecutionConfig(spread_pips=a.spread_pips,slippage_pips=a.slippage_pips)
    years={y:d[(d.index>=f"{y}-01-01")&(d.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}
    rows=[]; gates=Counter()
    for cid,p in enumerate(catalog(),1):
        pre=[{"year":y,"metrics":backtest(years[y],p,cfg)} for y in PRE_OOS_YEARS]; bad=reject(pre)
        for b in bad:gates[b]+=1
        rows.append({"candidate_id":cid,"family":p["family"],"params":p,"pre_oos":pre,"pre_oos_pass":not bad,"rejection_reasons":bad})
    ranked=sorted(rows,key=lambda x:(x["pre_oos_pass"],sum(z["metrics"]["expectancy_R"] for z in x["pre_oos"])),reverse=True)
    q=[x for x in ranked if x["pre_oos_pass"]]; validated=[]
    for x in q:
        vm=backtest(years[2025],x["params"],cfg); vr=[]
        if vm["profit_factor"]<VALIDATION_MIN_PF:vr.append(f"validation_pf<{VALIDATION_MIN_PF}")
        if vm["max_dd_pct"]>VALIDATION_MAX_DD_PCT:vr.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
        if vm["trades"]<VALIDATION_MIN_TRADES:vr.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
        if vm["expectancy_R"]<=0 or vm["total_R"]<=0:vr.append("validation_nonpositive_return")
        validated.append({**x,"validation_2025":vm,"validation_pass":not vr,"validation_rejection_reasons":vr})
    famsum={}
    for fam in ("regime_momentum","regime_pullback"):
        fr=[x for x in rows if x["family"]==fam]
        famsum[fam]={"candidate_count":len(fr),"pre_oos_qualified":sum(x["pre_oos_pass"] for x in fr),
          "best_candidate":max(fr,key=lambda x:sum(z["metrics"]["expectancy_R"] for z in x["pre_oos"])),
          "median_trades_by_year":{str(y):float(np.median([z["metrics"]["trades"] for x in fr for z in x["pre_oos"] if z["year"]==y])) for y in PRE_OOS_YEARS},
          "median_pf_by_year":{str(y):float(np.median([z["metrics"]["profit_factor"] for x in fr for z in x["pre_oos"] if z["year"]==y])) for y in PRE_OOS_YEARS},
          "median_dd_by_year":{str(y):float(np.median([z["metrics"]["max_dd_pct"] for x in fr for z in x["pre_oos"] if z["year"]==y])) for y in PRE_OOS_YEARS},
          "median_expectancy_by_year":{str(y):float(np.median([z["metrics"]["expectancy_R"] for x in fr for z in x["pre_oos"] if z["year"]==y])) for y in PRE_OOS_YEARS}}
    payload={"schema_version":"forexai.g6.regime_aware_event.v1","research_timeframe":a.timeframe,"real_data_required":True,"synthetic_fallback":False,"oos_policy":{"loaded":False,"status":"HELD_OUT","start":"2026-01-01"},
      "execution_model":{"entry":"next_bar_open","cost_pips_per_side":a.spread_pips+a.slippage_pips,"round_trip_cost_pips":2*(a.spread_pips+a.slippage_pips),"same_bar_resolution":"SL first (conservative)","expiry_bars":MAX_HOLD,"overlap":"one position at a time","adverse_exit_cost_applied":True},
      "catalog":{"candidate_total":len(rows),"family_counts":dict(Counter(x["family"] for x in rows)),"family_summary":famsum},
      "result":{"candidate_total":len(rows),"pre_oos_qualified_count":len(q),"validation_qualified_count":sum(x["validation_pass"] for x in validated),"top_50_diagnostics":ranked[:50],"gate_rejection_counts_all_candidates":dict(gates),"validated_candidates":validated,"champion":None}}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"candidate_total":len(rows),"pre_oos_qualified":len(q),"validation_qualified":sum(x["validation_pass"] for x in validated),"family_counts":dict(Counter(x["family"] for x in rows))}))
if __name__=="__main__":main()
