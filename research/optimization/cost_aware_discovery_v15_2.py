"""Targeted cost-aware discovery v15.2.

This is a focused research sweep built on the v15.1 execution model. It does
not weaken the promotion gate and never loads 2026. The sweep expands strategy
logic/parameter neighborhoods around the strongest v15.1 diagnostics for:
- session_range_breakout
- momentum_breakout
- regime_zscore_reversion

Research data must be real EURUSD M5 data. No synthetic fallback is permitted.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from research.optimization.cost_aware_discovery_v15 import (
    PRE_OOS_YEARS, MIN_TRADES_EACH_YEAR, MIN_PF_EACH_YEAR,
    MIN_EXPECTANCY_R, MIN_PROFITABLE_YEARS, PRE_OOS_MAX_DD_PCT,
    VALIDATION_MIN_PF, VALIDATION_MAX_DD_PCT, VALIDATION_MIN_TRADES,
    _cost_price, _native, indicators,
)

PIP_SIZE = 0.0001
RISK_PCT = 0.005
MAX_HOLD_BARS = 30

FAMILIES = ("session_range_breakout", "momentum_breakout", "regime_zscore_reversion")


def _pf(m: dict[str, Any]) -> float:
    return 3.0 if m.get("profit_factor") == "inf" else float(m.get("profit_factor", 0.0))


def _signals(d: pd.DataFrame, family: str, p: dict[str, Any]) -> np.ndarray:
    sig = pd.Series(0, index=d.index, dtype=int)
    if family == "session_range_breakout":
        day = d.index.floor("D")
        start = int(p["session_start_hour"])
        prior = d.index.hour < start
        rh = d.High.where(prior).groupby(day).cummax().shift(1)
        rl = d.Low.where(prior).groupby(day).cummin().shift(1)
        buf = float(p["breakout_buffer_pips"]) * PIP_SIZE
        active = d.index.hour >= start
        sig[active & (d.Close > rh + buf)] = 1
        sig[active & (d.Close < rl - buf)] = -1
    elif family == "momentum_breakout":
        sig[(d.mom > p["threshold"]) & (d.Close > d.hh) & d.session] = 1
        sig[(d.mom < -p["threshold"]) & (d.Close < d.ll) & d.session] = -1
    elif family == "regime_zscore_reversion":
        calm = d.vol_ratio <= p["max_vol_ratio"]
        up = d.Close > d.ema_t
        dn = d.Close < d.ema_t
        sig[calm & (d.zscore < -p["entry_z"]) & up] = 1
        sig[calm & (d.zscore > p["entry_z"]) & dn] = -1
    return sig.to_numpy(copy=False)


def backtest(df: pd.DataFrame, family: str, params: dict[str, Any], *, spread_pips=.5, slippage_pips=.2) -> dict[str, Any]:
    if df.empty:
        return {"trades":0,"win_rate":0.0,"total_R":0.0,"expectancy_R":0.0,"profit_factor":0.0,"max_dd_pct":0.0,"final_equity":10000.0,"entries":0,"exits":0,"open_position_end":False,"ohlc_invariants_passed":True}
    d = indicators(df, params)
    if not ((d["High"] >= d[["Open","Close"]].max(axis=1)) & (d["Low"] <= d[["Open","Close"]].min(axis=1)) & (d["High"] >= d["Low"])).all():
        raise SystemExit("EXECUTION_INTEGRITY_FAIL: OHLC invariant")
    sig = _signals(d, family, params)
    op=d.Open.to_numpy(float); hi=d.High.to_numpy(float); lo=d.Low.to_numpy(float); cl=d.Close.to_numpy(float); atr=d.atr.to_numpy(float)
    adverse=_cost_price(spread_pips, slippage_pips)
    equity=peak=10000.0; maxdd=0.0; pos=0; entry=stop=tp=0.0; entry_i=-1; rs=[]; entries=exits=0
    for i in range(1, len(d)):
        a=atr[i-1]
        if pos==0:
            s=sig[i-1]
            if s==0 or not np.isfinite(a) or a<=0: continue
            pos=int(s); raw=op[i]; entry=raw+(adverse if pos==1 else -adverse)
            sd=float(params["atr_stop"])*a; stop=entry-pos*sd; tp=entry+pos*float(params["rr"])*sd; entry_i=i; entries+=1; continue
        s=sig[i-1]; ex=None
        if pos==1:
            if lo[i] <= stop: ex=stop
            elif hi[i] >= tp: ex=tp
            elif s==-1: ex=cl[i]-adverse
            elif i-entry_i >= MAX_HOLD_BARS: ex=cl[i]-adverse
            if ex is not None:
                rs.append((ex-entry)/abs(entry-stop)); pos=0; exits+=1
        else:
            if hi[i] >= stop: ex=stop
            elif lo[i] <= tp: ex=tp
            elif s==1: ex=cl[i]+adverse
            elif i-entry_i >= MAX_HOLD_BARS: ex=cl[i]+adverse
            if ex is not None:
                rs.append((entry-ex)/abs(stop-entry)); pos=0; exits+=1
        if len(rs) > 0:
            equity *= 1 + RISK_PCT*rs[-1]; peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    if pos:
        ex=cl[-1]-adverse if pos==1 else cl[-1]+adverse
        rs.append((ex-entry)/abs(entry-stop) if pos==1 else (entry-ex)/abs(stop-entry)); pos=0; exits+=1
        equity *= 1 + RISK_PCT*rs[-1]; peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    if entries != exits or pos != 0:
        raise SystemExit(f"EXECUTION_INTEGRITY_FAIL: entries={entries} exits={exits} pos={pos}")
    n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else ("inf" if gp>0 else 0.0); total=float(sum(rs))
    return {"trades":n,"win_rate":round(100*wins/n,2) if n else 0.0,"total_R":round(total,2),"expectancy_R":round(total/n,4) if n else 0.0,"profit_factor":round(float(pf),3) if pf!="inf" and np.isfinite(pf) else pf,"max_dd_pct":round(100*maxdd,2),"final_equity":round(equity,2),"entries":entries,"exits":exits,"open_position_end":False,"ohlc_invariants_passed":True,"spread_pips":float(spread_pips),"slippage_pips":float(slippage_pips),"round_trip_cost_pips":round(2*(spread_pips+slippage_pips),4),"execution_model":"v28.1_next_bar_open"}


def catalog() -> dict[str, list[dict[str, Any]]]:
    base={"atr":14,"bb":20,"fast":13,"slow":89,"rsi":14,"don":20,"trend":200}
    return {
        "session_range_breakout":[{**base,"atr_stop":a,"rr":rr,"session_start_hour":h,"breakout_buffer_pips":b} for h in (7,8,9) for b in (0.0,0.5,1.0) for a in (1.0,1.2,1.4) for rr in (1.25,1.5,2.0,2.5,3.0)],
        "momentum_breakout":[{**base,"mom":m,"threshold":th,"atr_stop":a,"rr":rr,"don":n} for m in (3,5,8) for th in (0.0025,0.0030,0.0035) for a in (2.0,2.2,2.4) for rr in (2.0,2.5,3.0) for n in (8,10,12)],
        "regime_zscore_reversion":[{**base,"zscore_lookback":z,"entry_z":ez,"max_vol_ratio":vr,"trend":t,"atr_stop":a,"rr":rr} for z in (40,60,80) for ez in (1.75,2.0,2.25) for vr in (0.9,1.0,1.1) for t in (100,150,200) for a in (1.0,1.2,1.4) for rr in (1.5,2.0,2.5)],
    }


def _reasons(pre):
    by={int(x["year"]):x["metrics"] for x in pre}; r=[]
    for y in PRE_OOS_YEARS:
        m=by[y]
        if int(m["trades"])<MIN_TRADES_EACH_YEAR: r.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if _pf(m)<MIN_PF_EACH_YEAR: r.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if float(m["max_dd_pct"])>PRE_OOS_MAX_DD_PCT: r.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
        if float(m["expectancy_R"])<=MIN_EXPECTANCY_R: r.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
    if sum(float(by[y]["expectancy_R"])>MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS: r.append(f"profitable_years<{MIN_PROFITABLE_YEARS}")
    return r


def _score(pre):
    pfs=[_pf(x["metrics"]) for x in pre]; ex=[float(x["metrics"]["expectancy_R"]) for x in pre]; totals=sum(float(x["metrics"]["total_R"]) for x in pre); dds=[float(x["metrics"]["max_dd_pct"]) for x in pre]; trades=[int(x["metrics"]["trades"]) for x in pre]
    return round(float(1.8*min(max(min(pfs),0),2)/2 + 1.0*min(max(np.mean(pfs),0),2)/2 + 2.0*np.tanh(totals/150) + np.tanh(np.mean(ex)*20) + .5*min(min(trades)/MIN_TRADES_EACH_YEAR,1) - 2.0*min(max(max(dds),0),100)/100),6)


def discover(df,family,spread,slippage):
    years={y:df[(df.index>=f"{y}-01-01")&(df.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}
    results=[]; rejects=Counter()
    for j,p in enumerate(catalog()[family],1):
        pre=[{"year":y,"metrics":backtest(years[y],family,p,spread_pips=spread,slippage_pips=slippage)} for y in PRE_OOS_YEARS]
        rr=_reasons(pre)
        for x in rr: rejects[x]+=1
        results.append({"family":family,"candidate":j,"params":p,"cost_aware_robustness_score":_score(pre),"pre_oos_gate":{"pass":not rr,"fail_closed":True},"pre_oos_cost_aware":pre,"pre_oos_rejection_reasons":rr})
    results.sort(key=lambda x:(-x["cost_aware_robustness_score"],x["candidate"]))
    finalists=[x for x in results if x["pre_oos_gate"]["pass"]][:50]
    validated=[]; vreject=Counter()
    for x in finalists:
        vm=backtest(years[2025],family,x["params"],spread_pips=spread,slippage_pips=slippage); rr=_reasons([{"year":2025,"metrics":vm}])
        # Validation uses its dedicated gate only.
        rr=[]
        if _pf(vm)<VALIDATION_MIN_PF: rr.append(f"validation_pf<{VALIDATION_MIN_PF}")
        if float(vm["max_dd_pct"])>VALIDATION_MAX_DD_PCT: rr.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
        if int(vm["trades"])<VALIDATION_MIN_TRADES: rr.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
        for z in rr: vreject[z]+=1
        validated.append({**x,"validation_2025_cost_aware":vm,"validation_qualifies":not rr,"validation_rejection_reasons":rr})
    qualified=[x for x in validated if x["validation_qualifies"]]
    qualified.sort(key=lambda x:(-x["cost_aware_robustness_score"],x["candidate"]))
    return {"family":family,"candidate_total":len(results),"execution_model":"v28.1_next_bar_open","cost_profile":{"spread_pips":spread,"slippage_pips":slippage,"round_trip_cost_pips":2*(spread+slippage)},"qualified_count":len(qualified),"champion":None,"candidate_pool":qualified[:20],"top_20_diagnostics":results[:20],"validated_pre_oos_finalists":validated,"reject_diagnostics":{"pre_oos_rejections":dict(sorted(rejects.items(),key=lambda x:(-x[1],x[0]))),"pre_oos_passed_candidates":len(finalists),"validation_rejections":dict(sorted(vreject.items(),key=lambda x:(-x[1],x[0]))),"validation_qualified_candidates":len(qualified)}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--family",choices=FAMILIES,required=True); ap.add_argument("--output",required=True); ap.add_argument("--spread-pips",type=float,default=.5); ap.add_argument("--slippage-pips",type=float,default=.2); a=ap.parse_args()
    df=pd.read_csv(a.data); df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True); df=df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("timestamp").sort_index()
    if df.empty: raise SystemExit("REAL_DATA_REQUIRED: empty dataset")
    r=discover(df,a.family,a.spread_pips,a.slippage_pips)
    report={"schema_version":"forexai.cost_aware_discovery.v15.2","result":r,"research_timeframe":"M5","real_data_required":True,"synthetic_fallback":False,"oos_policy":{"loaded":False,"start":"2026-01-01","status":"HELD_OUT"},"execution_model":{"name":"v28.1_next_bar_open","adverse_entry_cost_per_side_pips":a.spread_pips+a.slippage_pips,"adverse_exit_cost_per_side_pips":a.spread_pips+a.slippage_pips,"sl_first":True,"max_hold_bars":MAX_HOLD_BARS,"opposite_signal_exit":True,"one_position_at_a_time":True}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(_native(report),indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"family":a.family,"candidate_total":r["candidate_total"],"qualified_count":r["qualified_count"],"top_candidate":r["top_20_diagnostics"][0]["candidate"] if r["top_20_diagnostics"] else None},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
