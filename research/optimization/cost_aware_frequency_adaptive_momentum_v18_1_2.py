"""Bounded Frequency-Adaptive Momentum Discovery v18.1.2.

Designed after v18.1 timeout. The hypothesis remains the same, but the sweep is
strictly bounded so a single GitHub runner can complete it deterministically.
No gate relaxation, no 2026 access, and no synthetic data.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.cost_aware_discovery_v15 import (
 PRE_OOS_YEARS,MIN_TRADES_EACH_YEAR,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,
 MIN_PROFITABLE_YEARS,PRE_OOS_MAX_DD_PCT,VALIDATION_MIN_PF,
 VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES,_cost_price,_native
)
from research.optimization.multi_family_discovery import indicators
RISK_PCT=.005; MAX_HOLD_BARS=30; FAMILY="frequency_adaptive_momentum_v18_1_2"

def pf(m): return 3.0 if m.get("profit_factor")=="inf" else float(m.get("profit_factor",0.0))

def bt(df,p,spread=.5,slip=.2):
    if df.empty:
        return {"trades":0,"win_rate":0,"total_R":0,"expectancy_R":0,"profit_factor":0,"max_dd_pct":0,"final_equity":10000,"entries":0,"exits":0,"open_position_end":False,"ohlc_invariants_passed":True,"execution_model":"v28.1_next_bar_open","round_trip_cost_pips":2*(spread+slip)}
    d=indicators(df,p)
    inv=(d.High>=d[["Open","Close"]].max(axis=1))&(d.Low<=d[["Open","Close"]].min(axis=1))&(d.High>=d.Low)
    if not bool(inv.all()): raise SystemExit("EXECUTION_INTEGRITY_FAIL: OHLC")
    session=(d.index.hour>=p["session_start"])&(d.index.hour<=p["session_end"])
    tl=(d.ema_f>d.ema_s)&(d.Close>d.ema_t); ts=(d.ema_f<d.ema_s)&(d.Close<d.ema_t)
    ml=d.mom>p["threshold"]; ms=d.mom<-p["threshold"]; bl=d.Close>d.hh; bs=d.Close<d.ll
    cl=(d.Close>d.ema_f)&(d.Close.shift(1)<=d.ema_f.shift(1))&(d.mom>p["threshold"]*p["cont_mult"])
    cs=(d.Close<d.ema_f)&(d.Close.shift(1)>=d.ema_f.shift(1))&(d.mom<-p["threshold"]*p["cont_mult"])
    out=pd.Series(0,index=d.index,dtype=int)
    if p["mode"]=="breakout":
        out[session&ml&bl]=1; out[session&ms&bs]=-1
    elif p["mode"]=="continuation":
        out[session&tl&ml&cl]=1; out[session&ts&ms&cs]=-1
    else:
        out[session&((ml&bl)|(tl&ml&cl))]=1; out[session&((ms&bs)|(ts&ms&cs))]=-1
    s=out.to_numpy(); op=d.Open.to_numpy(float); hi=d.High.to_numpy(float); lo=d.Low.to_numpy(float); cx=d.Close.to_numpy(float); atr=d.atr.to_numpy(float); cost=_cost_price(spread,slip)
    pos=0;entry=stop=tp=0.;ei=-1;rs=[];entries=exits=0;eq=peak=10000.;dd=0.
    for i in range(1,len(d)):
        a=atr[i-1]
        if pos==0:
            q=s[i-1]
            if q==0 or not np.isfinite(a) or a<=0: continue
            pos=int(q); entry=op[i]+(cost if pos==1 else -cost); sd=p["atr_stop"]*a; stop=entry-pos*sd; tp=entry+pos*p["rr"]*sd; ei=i; entries+=1; continue
        q=s[i-1]; tr=None
        if pos==1:
            if lo[i]<=stop: tr=(stop-entry)/abs(entry-stop)
            elif hi[i]>=tp: tr=(tp-entry)/abs(entry-stop)
            elif q==-1: tr=(cx[i]-cost-entry)/abs(entry-stop)
            elif i-ei>=MAX_HOLD_BARS: tr=(cx[i]-cost-entry)/abs(entry-stop)
        else:
            if hi[i]>=stop: tr=(entry-stop)/abs(stop-entry)
            elif lo[i]<=tp: tr=(entry-tp)/abs(stop-entry)
            elif q==1: tr=(entry-(cx[i]+cost))/abs(stop-entry)
            elif i-ei>=MAX_HOLD_BARS: tr=(entry-(cx[i]+cost))/abs(stop-entry)
        if tr is not None:
            rs.append(float(tr)); pos=0; exits+=1; eq*=1+RISK_PCT*tr; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
    if pos:
        tr=(cx[-1]-cost-entry)/abs(entry-stop) if pos==1 else (entry-(cx[-1]+cost))/abs(stop-entry)
        rs.append(float(tr));pos=0;exits+=1;eq*=1+RISK_PCT*tr;peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    if entries!=exits or pos: raise SystemExit(f"EXECUTION_INTEGRITY_FAIL entries={entries} exits={exits} pos={pos}")
    expected=10000.
    for tr in rs: expected*=1+RISK_PCT*tr
    if not np.isclose(eq,expected,rtol=1e-12,atol=1e-9): raise SystemExit("EXECUTION_INTEGRITY_FAIL equity")
    n=len(rs); wins=sum(r>0 for r in rs); gp=sum(r for r in rs if r>0); gl=abs(sum(r for r in rs if r<=0)); f=gp/gl if gl else ("inf" if gp>0 else 0); total=sum(rs)
    return {"trades":n,"win_rate":round(100*wins/n,2) if n else 0,"total_R":round(total,2),"expectancy_R":round(total/n,4) if n else 0,"profit_factor":round(f,3) if f!="inf" and np.isfinite(f) else f,"max_dd_pct":round(dd*100,2),"final_equity":round(eq,2),"entries":entries,"exits":exits,"open_position_end":False,"ohlc_invariants_passed":True,"execution_model":"v28.1_next_bar_open","round_trip_cost_pips":2*(spread+slip)}

def catalog():
    base={"atr":14,"bb":20,"fast":13,"slow":89,"rsi":14,"trend":200,"mom":5}
    return [{**base,"threshold":th,"atr_stop":a,"rr":rr,"don":n,"session_start":sh,"session_end":eh,"cont_mult":cm,"mode":mode}
      for th in (.001,.0015,.002)
      for a in (1.5,1.8)
      for rr in (1.75,2.25)
      for n in (3,6)
      for sh,eh in ((6,20),(7,22))
      for cm in (.5,1.0)
      for mode in ("breakout","hybrid")]

def reasons(pre):
    by={x["year"]:x["metrics"] for x in pre}; r=[]
    for y in PRE_OOS_YEARS:
        m=by[y]
        if m["trades"]<MIN_TRADES_EACH_YEAR:r.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if pf(m)<MIN_PF_EACH_YEAR:r.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if m["expectancy_R"]<=MIN_EXPECTANCY_R:r.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
        if m["max_dd_pct"]>PRE_OOS_MAX_DD_PCT:r.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
    if sum(by[y]["expectancy_R"]>MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS:r.append(f"profitable_years<{MIN_PROFITABLE_YEARS}")
    return r

def score(pre):
    p=[pf(x["metrics"]) for x in pre]; e=[x["metrics"]["expectancy_R"] for x in pre]; t=sum(x["metrics"]["total_R"] for x in pre); dd=[x["metrics"]["max_dd_pct"] for x in pre]; tr=[x["metrics"]["trades"] for x in pre]
    return round(float(min(p)+np.mean(p)+np.mean(e)*5+np.tanh(t/100)-max(dd)/100+min(min(tr)/MIN_TRADES_EACH_YEAR,1)),6)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--data",required=True);ap.add_argument("--output",required=True);ap.add_argument("--spread-pips",type=float,default=.5);ap.add_argument("--slippage-pips",type=float,default=.2);a=ap.parse_args()
    df=pd.read_csv(a.data); df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True); df=df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("timestamp").sort_index()
    if df.empty: raise SystemExit("REAL_DATA_REQUIRED")
    years={y:df[(df.index>=f"{y}-01-01")&(df.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}
    out=[]
    for i,p in enumerate(catalog(),1):
        pre=[{"year":y,"metrics":bt(years[y],p,a.spread_pips,a.slippage_pips)} for y in PRE_OOS_YEARS]; rr=reasons(pre)
        out.append({"family":FAMILY,"candidate":i,"params":p,"cost_aware_robustness_score":score(pre),"pre_oos_gate":{"pass":not rr,"fail_closed":True},"pre_oos_cost_aware":pre,"pre_oos_rejection_reasons":rr})
    out.sort(key=lambda x:(-x["cost_aware_robustness_score"],x["candidate"]))
    finals=[x for x in out if x["pre_oos_gate"]["pass"]][:50]; vals=[]
    for x in finals:
        vm=bt(years[2025],x["params"],a.spread_pips,a.slippage_pips); vr=[]
        if pf(vm)<VALIDATION_MIN_PF:vr.append(f"validation_pf<{VALIDATION_MIN_PF}")
        if vm["max_dd_pct"]>VALIDATION_MAX_DD_PCT:vr.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
        if vm["trades"]<VALIDATION_MIN_TRADES:vr.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
        vals.append({**x,"validation_2025_cost_aware":vm,"validation_qualifies":not vr,"validation_rejection_reasons":vr})
    q=[x for x in vals if x["validation_qualifies"]]
    report={"schema_version":"forexai.cost_aware_frequency_adaptive_momentum.v18.1.2","result":{"family":FAMILY,"candidate_total":len(out),"execution_model":"v28.1_next_bar_open","qualified_count":len(q),"champion":None,"candidate_pool":q[:20],"top_20_diagnostics":out[:20],"validated_pre_oos_finalists":vals},"research_timeframe":"M5","real_data_required":True,"synthetic_fallback":False,"oos_policy":{"loaded":False,"start":"2026-01-01","status":"HELD_OUT"},"execution_model":{"name":"v28.1_next_bar_open","round_trip_cost_pips":2*(a.spread_pips+a.slippage_pips),"sl_first":True,"max_hold_bars":MAX_HOLD_BARS,"opposite_signal_exit":True,"one_position_at_a_time":True}}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(_native(report),indent=2),encoding="utf-8")
    print(json.dumps({"candidate_total":len(out),"qualified_count":len(q),"top_candidate":out[0]["candidate"] if out else None}))
if __name__=="__main__":main()
