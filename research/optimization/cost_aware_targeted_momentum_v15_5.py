"""Targeted Momentum Discovery v15.5.

Frequency/consistency expansion after v15.4. This is a pre-registered sweep:
lower momentum thresholds and shorter breakout lookbacks are explored to test
whether the observed M5 edge can reach the existing minimum sample-size gate
without sacrificing PF, expectancy, or drawdown.

Strict promotion criteria are unchanged. REAL EURUSD M5 only.
2022-2024 discovery, 2025 validation, 2026 held out.
Execution model: v28.1/v29.1 next-bar-open with adverse 1.4 pip round trip,
SL-first, 30-bar expiry, opposite-signal exit, one position at a time.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np,pandas as pd
from research.optimization.cost_aware_discovery_v15 import (
    PRE_OOS_YEARS,MIN_TRADES_EACH_YEAR,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,
    MIN_PROFITABLE_YEARS,PRE_OOS_MAX_DD_PCT,VALIDATION_MIN_PF,
    VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES,_cost_price,_native,indicators
)
PIP_SIZE=.0001
RISK_PCT=.005
MAX_HOLD_BARS=30
FAMILY="momentum_breakout"

def _pf(m): return 3.0 if m.get("profit_factor")=="inf" else float(m.get("profit_factor",0.0))

def backtest(df:pd.DataFrame,p:dict[str,Any],*,spread_pips=.5,slippage_pips=.2):
    if df.empty:
        return {"trades":0,"win_rate":0.0,"total_R":0.0,"expectancy_R":0.0,"profit_factor":0.0,"max_dd_pct":0.0,"final_equity":10000.0,"entries":0,"exits":0,"open_position_end":False,"ohlc_invariants_passed":True,"execution_model":"v28.1_next_bar_open","round_trip_cost_pips":2*(spread_pips+slippage_pips)}
    d=indicators(df,p)
    inv=(d.High>=d[["Open","Close"]].max(axis=1))&(d.Low<=d[["Open","Close"]].min(axis=1))&(d.High>=d.Low)
    if not bool(inv.all()): raise SystemExit("EXECUTION_INTEGRITY_FAIL: OHLC invariant")
    sig=pd.Series(0,index=d.index,dtype=int)
    active=(d.index.hour>=p["session_start_hour"])&(d.index.hour<=p["session_end_hour"])
    sig[(d.mom>p["threshold"])&(d.Close>d.hh)&active]=1
    sig[(d.mom<-p["threshold"])&(d.Close<d.ll)&active]=-1
    s=sig.to_numpy(copy=False)
    op=d.Open.to_numpy(float); hi=d.High.to_numpy(float); lo=d.Low.to_numpy(float); cl=d.Close.to_numpy(float); atr=d.atr.to_numpy(float)
    adverse=_cost_price(spread_pips,slippage_pips)
    equity=peak=10000.0; maxdd=0.0; pos=0; entry=stop=tp=0.0; entry_i=-1; rs=[]; entries=exits=0
    for i in range(1,len(d)):
        a=atr[i-1]
        if pos==0:
            q=s[i-1]
            if q==0 or not np.isfinite(a) or a<=0: continue
            pos=int(q); raw=op[i]; entry=raw+(adverse if pos==1 else -adverse)
            sd=float(p["atr_stop"])*a; stop=entry-pos*sd; tp=entry+pos*p["rr"]*sd
            entry_i=i; entries+=1; continue
        q=s[i-1]; tr=None
        if pos==1:
            if lo[i]<=stop: tr=(stop-entry)/abs(entry-stop)
            elif hi[i]>=tp: tr=(tp-entry)/abs(entry-stop)
            elif q==-1: tr=(cl[i]-adverse-entry)/abs(entry-stop)
            elif i-entry_i>=MAX_HOLD_BARS: tr=(cl[i]-adverse-entry)/abs(entry-stop)
        else:
            if hi[i]>=stop: tr=(entry-stop)/abs(stop-entry)
            elif lo[i]<=tp: tr=(entry-tp)/abs(stop-entry)
            elif q==1: tr=(entry-(cl[i]+adverse))/abs(stop-entry)
            elif i-entry_i>=MAX_HOLD_BARS: tr=(entry-(cl[i]+adverse))/abs(stop-entry)
        if tr is not None:
            rs.append(float(tr)); pos=0; exits+=1
            equity*=1+RISK_PCT*tr; peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    if pos:
        tr=(cl[-1]-adverse-entry)/abs(entry-stop) if pos==1 else (entry-(cl[-1]+adverse))/abs(stop-entry)
        rs.append(float(tr)); pos=0; exits+=1
        equity*=1+RISK_PCT*tr; peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    if entries!=exits: raise SystemExit(f"EXECUTION_INTEGRITY_FAIL: entries={entries} exits={exits}")
    expected=10000.0
    for tr in rs: expected*=1+RISK_PCT*tr
    if not np.isclose(equity,expected,rtol=1e-12,atol=1e-9):
        raise SystemExit(f"EXECUTION_INTEGRITY_FAIL: equity_mismatch observed={equity} expected={expected}")
    n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else ("inf" if gp>0 else 0.0); total=sum(rs)
    return {"trades":n,"win_rate":round(100*wins/n,2) if n else 0.0,"total_R":round(float(total),2),"expectancy_R":round(float(total)/n,4) if n else 0.0,"profit_factor":round(float(pf),3) if pf!="inf" and np.isfinite(pf) else pf,"max_dd_pct":round(100*maxdd,2),"final_equity":round(equity,2),"entries":entries,"exits":exits,"open_position_end":False,"ohlc_invariants_passed":True,"spread_pips":float(spread_pips),"slippage_pips":float(slippage_pips),"round_trip_cost_pips":round(2*(spread_pips+slippage_pips),4),"execution_model":"v28.1_next_bar_open"}

def catalog():
    base={"atr":14,"bb":20,"fast":13,"slow":89,"rsi":14,"trend":200}
    return [{**base,"mom":m,"threshold":th,"atr_stop":a,"rr":rr,"don":n,
             "session_start_hour":sh,"session_end_hour":eh}
            for m in (1,2,3,4)
            for th in (0.0005,0.00075,0.0010,0.0015,0.0020)
            for a in (1.4,1.6,1.8)
            for rr in (1.75,2.0,2.25)
            for n in (2,3,4,5)
            for sh,eh in ((7,20),(6,20),(7,22))]

def reasons(pre):
    by={int(x["year"]):x["metrics"] for x in pre}; out=[]
    for y in PRE_OOS_YEARS:
        m=by[y]
        if int(m["trades"])<MIN_TRADES_EACH_YEAR: out.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if _pf(m)<MIN_PF_EACH_YEAR: out.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if float(m["max_dd_pct"])>PRE_OOS_MAX_DD_PCT: out.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
        if float(m["expectancy_R"])<=MIN_EXPECTANCY_R: out.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
    if sum(float(by[y]["expectancy_R"])>MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS:
        out.append(f"profitable_years<{MIN_PROFITABLE_YEARS}")
    return out

def score(pre):
    p=[_pf(x["metrics"]) for x in pre]; e=[float(x["metrics"]["expectancy_R"]) for x in pre]; t=sum(float(x["metrics"]["total_R"]) for x in pre); d=[float(x["metrics"]["max_dd_pct"]) for x in pre]; tr=[int(x["metrics"]["trades"]) for x in pre]
    return round(float(1.8*min(max(min(p),0),2)/2+1.0*min(max(np.mean(p),0),2)/2+2*np.tanh(t/150)+np.tanh(np.mean(e)*20)+.5*min(min(tr)/MIN_TRADES_EACH_YEAR,1)-2*min(max(max(d),0),100)/100),6)

def discover(df,spread,slippage):
    years={y:df[(df.index>=f"{y}-01-01")&(df.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}
    results=[]; rej=Counter()
    for j,p in enumerate(catalog(),1):
        pre=[{"year":y,"metrics":backtest(years[y],p,spread_pips=spread,slippage_pips=slippage)} for y in PRE_OOS_YEARS]
        rr=reasons(pre)
        for x in rr: rej[x]+=1
        results.append({"family":FAMILY,"candidate":j,"params":p,"cost_aware_robustness_score":score(pre),"pre_oos_gate":{"pass":not rr,"years":list(PRE_OOS_YEARS),"fail_closed":True},"pre_oos_cost_aware":pre,"pre_oos_rejection_reasons":rr})
    results.sort(key=lambda x:(-x["cost_aware_robustness_score"],x["candidate"]))
    finals=[x for x in results if x["pre_oos_gate"]["pass"]][:50]; validated=[]
    for x in finals:
        vm=backtest(years[2025],x["params"],spread_pips=spread,slippage_pips=slippage); rr=[]
        if _pf(vm)<VALIDATION_MIN_PF: rr.append(f"validation_pf<{VALIDATION_MIN_PF}")
        if float(vm["max_dd_pct"])>VALIDATION_MAX_DD_PCT: rr.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
        if int(vm["trades"])<VALIDATION_MIN_TRADES: rr.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
        validated.append({**x,"validation_2025_cost_aware":vm,"validation_qualifies":not rr,"validation_rejection_reasons":rr})
    qualified=[x for x in validated if x["validation_qualifies"]]
    return {"family":FAMILY,"candidate_total":len(results),"execution_model":"v28.1_next_bar_open","cost_profile":{"spread_pips":spread,"slippage_pips":slippage,"round_trip_cost_pips":2*(spread+slippage)},"qualified_count":len(qualified),"champion":None,"candidate_pool":qualified[:20],"top_20_diagnostics":results[:20],"validated_pre_oos_finalists":validated,"reject_diagnostics":{"pre_oos_rejections":dict(sorted(rej.items(),key=lambda x:(-x[1],x[0]))),"pre_oos_passed_candidates":len(finals),"validation_qualified_candidates":len(qualified)}}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); ap.add_argument("--spread-pips",type=float,default=.5); ap.add_argument("--slippage-pips",type=float,default=.2); a=ap.parse_args()
    df=pd.read_csv(a.data); df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True); df=df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("timestamp").sort_index()
    if df.empty: raise SystemExit("REAL_DATA_REQUIRED: empty dataset")
    r=discover(df,a.spread_pips,a.slippage_pips)
    report={"schema_version":"forexai.cost_aware_targeted_momentum.v15.5","result":r,"research_timeframe":"M5","real_data_required":True,"synthetic_fallback":False,"oos_policy":{"loaded":False,"start":"2026-01-01","status":"HELD_OUT"},"execution_model":{"name":"v28.1_next_bar_open","adverse_entry_cost_per_side_pips":a.spread_pips+a.slippage_pips,"adverse_exit_cost_per_side_pips":a.spread_pips+a.slippage_pips,"sl_first":True,"max_hold_bars":MAX_HOLD_BARS,"opposite_signal_exit":True,"one_position_at_a_time":True}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(_native(report),indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"family":FAMILY,"candidate_total":r["candidate_total"],"qualified_count":r["qualified_count"],"top_candidate":r["top_20_diagnostics"][0]["candidate"] if r["top_20_diagnostics"] else None},indent=2))
if __name__=="__main__": raise SystemExit(main())
