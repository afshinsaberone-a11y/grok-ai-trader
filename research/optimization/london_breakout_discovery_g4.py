"""ForexAI Discovery Generation 4: London Breakout + causal regime/volatility filters.
REAL EURUSD M5 only. Discovery 2022-2024; validation 2025; 2026 held out.
No synthetic data, no fallback, no OOS optimization, no Champion promotion.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from research.optimization.cost_aware_gate_v14 import (MIN_EXPECTANCY_R, MIN_PF_EACH_YEAR, MIN_PROFITABLE_YEARS, MIN_TRADES_EACH_YEAR, PRE_OOS_MAX_DD_PCT, VALIDATION_MAX_DD_PCT, VALIDATION_MIN_PF, VALIDATION_MIN_TRADES)
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost, validate_ohlc
MAX_HOLD=30; LONDON=ZoneInfo("Europe/London"); SPREAD=.5; SLIPPAGE=.2; ATR_BASELINE_BARS=96; ADX_PERIOD=14

def catalog():
    out=[]
    for rm in (30,60,90):
      for eh in (8,9):
       for b in (0.0,0.05,0.10):
        for am in (1.0,1.5):
         for rr in (1.2,1.5,2.0):
          for side in ("long_only","short_only"):
           for min_ar in (0.8,1.0,1.2):
            for min_adx in (15.0,20.0):
             out.append({"range_minutes":rm,"entry_hour":eh,"buffer_atr":b,"atr_mult":am,"rr":rr,"side_mode":side,"min_atr_ratio":min_ar,"min_adx":min_adx})
    return out

def prepare(raw):
    d=raw.rename(columns={"timestamp":"Timestamp","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).copy(); d["Timestamp"]=pd.to_datetime(d["Timestamp"],utc=True); d=d.set_index("Timestamp").sort_index(); validate_ohlc(d)
    prev=d.Close.shift(1); tr=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1); d["ATR"]=tr.rolling(14,min_periods=14).mean()
    up=d.High.diff(); down=-d.Low.diff(); plus=up.where((up>down)&(up>0),0.0); minus=down.where((down>up)&(down>0),0.0); aw=tr.ewm(alpha=1/ADX_PERIOD,adjust=False,min_periods=ADX_PERIOD).mean(); pdi=100*plus.ewm(alpha=1/ADX_PERIOD,adjust=False,min_periods=ADX_PERIOD).mean()/aw; mdi=100*minus.ewm(alpha=1/ADX_PERIOD,adjust=False,min_periods=ADX_PERIOD).mean()/aw; dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan); d["ADX"]=dx.ewm(alpha=1/ADX_PERIOD,adjust=False,min_periods=ADX_PERIOD).mean()
    d["ATR_baseline"]=d["ATR"].rolling(ATR_BASELINE_BARS,min_periods=ATR_BASELINE_BARS).median(); d["ATR_ratio"]=d["ATR"]/d["ATR_baseline"]; local=d.index.tz_convert(LONDON); d["local_date"]=local.date; d["local_hour"]=local.hour; d["local_minute"]=local.minute; return d

def metrics(rs):
    n=len(rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else (3.0 if gp>0 else 0.0); eq=peak=10000.0; dd=0.0
    for r in rs: eq*=1+0.005*r; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
    return {"trades":n,"win_rate_pct":round(100*sum(x>0 for x in rs)/n,2) if n else 0.0,"total_R":round(float(sum(rs)),4),"expectancy_R":round(float(sum(rs))/n,6) if n else 0.0,"profit_factor":round(float(pf),4),"max_dd_pct":round(100*dd,4),"final_equity":round(eq,4)}

def backtest(d,p,cfg):
    rs=[]
    for _,g0 in d.groupby("local_date",sort=True):
        g=g0.copy(); pos=0; entry=stop=target=0.0; entry_i=-1; end=p["entry_hour"]*60; start=end-int(p["range_minutes"])
        for i in range(14,len(g)-1):
            minute=int(g.local_hour.iloc[i])*60+int(g.local_minute.iloc[i])
            if pos==0 and minute==end:
                bars=g.iloc[:i]; mins=bars.local_hour*60+bars.local_minute; ref=bars[(mins>=start)&(mins<end)]
                if len(ref)<max(2,int(p["range_minutes"]//5)): continue
                atr=float(g.ATR.iloc[i]); ratio=float(g.ATR_ratio.iloc[i]); adx=float(g.ADX.iloc[i])
                if not (np.isfinite(atr) and atr>0 and np.isfinite(ratio) and ratio>=p["min_atr_ratio"] and np.isfinite(adx) and adx>=p["min_adx"]): continue
                hi=float(ref.High.max())+float(p["buffer_atr"])*atr; lo=float(ref.Low.min())-float(p["buffer_atr"])*atr; c=float(g.Close.iloc[i]); side=1 if c>hi else -1 if c<lo else 0
                if (p["side_mode"]=="long_only" and side!=1) or (p["side_mode"]=="short_only" and side!=-1): continue
                entry_i=i+1; entry=apply_entry_cost(float(g.Open.iloc[entry_i]),side,cfg); unit=float(p["atr_mult"])*atr; stop=entry-side*unit; target=entry+side*float(p["rr"])*unit; pos=side; continue
            if pos!=0:
                age=i-entry_i+1; hit_sl=float(g.Low.iloc[i])<=stop if pos==1 else float(g.High.iloc[i])>=stop; hit_tp=float(g.High.iloc[i])>=target if pos==1 else float(g.Low.iloc[i])<=target; unit=float(p["atr_mult"])*float(g.ATR.iloc[entry_i-1])
                if not np.isfinite(unit) or unit<=0: continue
                r=None
                if hit_sl: r=pos*(apply_exit_cost(stop,pos,cfg)-entry)/unit
                elif hit_tp: r=pos*(apply_exit_cost(target,pos,cfg)-entry)/unit
                elif age>=MAX_HOLD: ex=float(g.Open.iloc[min(i+1,len(g)-1)]); r=pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit
                if r is not None: rs.append(float(r)); pos=0
        if pos!=0:
            ex=float(g.Open.iloc[-1]); unit=float(p["atr_mult"])*float(g.ATR.iloc[max(entry_i-1,0)]); 
            if np.isfinite(unit) and unit>0: rs.append(float(pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit))
    return metrics(rs)

def reject(pre):
    by={int(x["year"]):x["metrics"] for x in pre}; bad=[]
    for y in (2022,2023,2024):
        m=by[y]
        if m["trades"]<MIN_TRADES_EACH_YEAR: bad.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if float(m["profit_factor"])<MIN_PF_EACH_YEAR: bad.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if float(m["expectancy_R"])<=MIN_EXPECTANCY_R: bad.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
        if float(m["max_dd_pct"])>PRE_OOS_MAX_DD_PCT: bad.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
    if sum(float(by[y]["expectancy_R"])>0 for y in (2022,2023,2024))<MIN_PROFITABLE_YEARS: bad.append("profitable_years<3")
    return bad

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); ap.add_argument("--timeframe",required=True,choices=("M1","M5","M15")); ap.add_argument("--spread-pips",type=float,default=SPREAD); ap.add_argument("--slippage-pips",type=float,default=SLIPPAGE); a=ap.parse_args(); d=prepare(pd.read_csv(a.data)); cfg=ExecutionConfig(spread_pips=a.spread_pips,slippage_pips=a.slippage_pips); years={y:d[(d.index>=f"{y}-01-01")&(d.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}; rows=[]; gates=Counter(); candidates=catalog()
    for cid,p in enumerate(candidates,1):
        pre=[{"year":y,"metrics":backtest(years[y],p,cfg)} for y in (2022,2023,2024)]; bad=reject(pre); [gates.__setitem__(x,gates[x]+1) for x in bad]; rows.append({"candidate_id":cid,"params":p,"pre_oos":pre,"pre_oos_pass":not bad,"rejection_reasons":bad})
    ranked=sorted(rows,key=lambda x:(x["pre_oos_pass"],sum(m["metrics"]["expectancy_R"] for m in x["pre_oos"])),reverse=True); pre=[x for x in ranked if x["pre_oos_pass"]]; validated=[]
    for x in pre:
        vm=backtest(years[2025],x["params"],cfg); vr=[]
        if float(vm["profit_factor"])<VALIDATION_MIN_PF: vr.append(f"validation_pf<{VALIDATION_MIN_PF}")
        if float(vm["max_dd_pct"])>VALIDATION_MAX_DD_PCT: vr.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
        if int(vm["trades"])<VALIDATION_MIN_TRADES: vr.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
        if float(vm["expectancy_R"])<=0 or float(vm["total_R"])<=0: vr.append("validation_nonpositive_return")
        validated.append({**x,"validation_2025":vm,"validation_pass":not vr,"validation_rejection_reasons":vr})
    payload={"schema_version":"forexai.london_breakout_discovery.g4","research_timeframe":a.timeframe,"real_data_required":True,"synthetic_fallback":False,"session_timezone":"Europe/London","filter_model":{"name":"causal_regime_volatility","atr_baseline_bars":ATR_BASELINE_BARS,"atr_ratio_thresholds":[0.8,1.0,1.2],"adx_period":ADX_PERIOD,"adx_thresholds":[15.0,20.0],"decision_uses_only_information_available_at_entry_bar":True},"oos_policy":{"loaded":False,"status":"HELD_OUT","start":"2026-01-01"},"execution_model":{"entry":"next_bar_open","cost_pips_per_side":a.spread_pips+a.slippage_pips,"round_trip_cost_pips":2*(a.spread_pips+a.slippage_pips),"same_bar_resolution":"SL first (conservative)","expiry_bars":MAX_HOLD,"overlap":"one position at a time","adverse_exit_cost_applied":True},"catalog":{"candidate_total":len(rows),"family_counts":{"london_breakout_regime_volatility":len(rows)}},"result":{"candidate_total":len(rows),"pre_oos_qualified_count":len(pre),"validation_qualified_count":sum(1 for x in validated if x["validation_pass"]),"top_50_diagnostics":ranked[:50],"gate_rejection_counts_all_candidates":dict(gates),"validated_candidates":validated,"champion":None}}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8"); print(json.dumps({"candidate_total":len(rows),"pre_oos_qualified":len(pre),"validation_qualified":sum(1 for x in validated if x["validation_pass"])}))
if __name__=="__main__": main()
