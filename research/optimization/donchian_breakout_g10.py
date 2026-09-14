"""ForexAI G10: cost-aware Donchian breakout discovery on real EURUSD M5.

Discovery uses 2022-2024 only; 2025 is diagnostic validation; 2026 is never loaded.
The family is deliberately independent of EMA-regime, Bollinger mean reversion,
and SP2L logic. Signals are generated from prior-bar Donchian extremes and are
executed at the next bar open under the unified execution contract.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost

SCHEMA="forexai.g10.donchian_breakout.v1"
YEARS=(2022,2023,2024)
VALIDATION_YEAR=2025
WINDOWS=(20,40,60,80)
ATR_MULTS=(1.0,1.5)
RRS=(1.5,2.0)
SIDES=(1,-1)
BUFFERS=(0.0,0.00005)


def candidates():
    out=[]
    idx=1
    for w in WINDOWS:
        for atr in ATR_MULTS:
            for rr in RRS:
                for buf in BUFFERS:
                    for side in SIDES:
                        out.append({"id":idx,"family":"donchian_breakout","window":w,"atr_mult":atr,"rr":rr,"buffer_price":buf,"side":"long" if side==1 else "short"})
                        idx+=1
    return out


def load_year(df, year):
    ts=pd.to_datetime(df["timestamp"],utc=True)
    x=df.loc[(ts>=pd.Timestamp(f"{year}-01-01",tz="UTC"))&(ts<pd.Timestamp(f"{year+1}-01-01",tz="UTC")),["timestamp","open","high","low","close"]].copy()
    x.columns=["Timestamp","Open","High","Low","Close"]
    x["Timestamp"]=pd.to_datetime(x["Timestamp"],utc=True)
    x=x.set_index("Timestamp")
    if x.empty: raise ValueError(f"G10_EMPTY_YEAR:{year}")
    if x.index.has_duplicates or not x.index.is_monotonic_increasing: raise ValueError(f"G10_BAD_INDEX:{year}")
    if (x.High<x.Low).any() or (x.High<x.Open).any() or (x.High<x.Close).any() or (x.Low>x.Open).any() or (x.Low>x.Close).any(): raise ValueError(f"G10_OHLC_FAIL:{year}")
    return x


def atr_series(x, n=14):
    pc=x.Close.shift(1)
    tr=pd.concat([(x.High-x.Low),(x.High-pc).abs(),(x.Low-pc).abs()],axis=1).max(axis=1)
    return tr.rolling(n,min_periods=n).mean().to_numpy()


def backtest(x, p, cfg):
    if len(x)<max(p["window"],14)+2:
        return {"trades":0,"win_rate_pct":0.0,"profit_factor":0.0,"expectancy_R":0.0,"total_R":0.0,"max_dd_pct":100.0}
    o,h,l,c=x.Open.to_numpy(float),x.High.to_numpy(float),x.Low.to_numpy(float),x.Close.to_numpy(float)
    atr=atr_series(x)
    prev_hi=pd.Series(h).rolling(p["window"]).max().shift(1).to_numpy()
    prev_lo=pd.Series(l).rolling(p["window"]).min().shift(1).to_numpy()
    side=1 if p["side"]=="long" else -1
    pos=0; entry=stop=target=0.0; age=0; rs=[]; equity=10000.0; peak=equity; maxdd=0.0; entries=0
    for i in range(max(p["window"],14)+1,len(x)):
        if pos==0:
            level=(prev_hi[i]+p["buffer_price"]) if side==1 else (prev_lo[i]-p["buffer_price"])
            trigger=(c[i-1]>level) if side==1 else (c[i-1]<level)
            if trigger and np.isfinite(atr[i-1]) and atr[i-1]>0:
                entry=apply_entry_cost(o[i],side,cfg)
                risk=p["atr_mult"]*atr[i-1]
                stop=entry-side*risk
                target=entry+side*p["rr"]*risk
                pos=side; age=0; entries+=1
                continue
        age+=1
        hit_sl=(l[i]<=stop) if pos==1 else (h[i]>=stop)
        hit_tp=(h[i]>=target) if pos==1 else (l[i]<=target)
        if hit_sl or hit_tp or age>=cfg.expiry_bars:
            if hit_sl:
                raw=stop; reason="SL"
            elif hit_tp:
                raw=target; reason="TP"
            else:
                raw=o[i] if i<len(x) else c[i]; reason="EXPIRY"
            ex=apply_exit_cost(raw,pos,cfg)
            r=pos*(ex-entry)/(abs(stop-entry))
            rs.append(float(r))
            equity*=1.0+r*cfg.risk_pct
            peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
            pos=0
    if pos!=0:
        ex=apply_exit_cost(c[-1],pos,cfg); r=pos*(ex-entry)/(abs(stop-entry)); rs.append(float(r)); equity*=1.0+r*cfg.risk_pct; peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    arr=np.asarray(rs,float); wins=arr[arr>0]; losses=arr[arr<=0]; gross_loss=abs(losses.sum())
    pf=float(wins.sum()/gross_loss) if gross_loss>0 else (3.0 if wins.size else 0.0)
    return {"trades":int(arr.size),"win_rate_pct":round(float((arr>0).mean()*100),3) if arr.size else 0.0,"profit_factor":round(pf,6),"expectancy_R":round(float(arr.mean()),6) if arr.size else 0.0,"total_R":round(float(arr.sum()),6) if arr.size else 0.0,"max_dd_pct":round(float(maxdd*100),6)}


def strict_year(m):
    return m["trades"]>=100 and m["profit_factor"]>=1.05 and m["expectancy_R"]>0 and m["max_dd_pct"]<35.0


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); a=ap.parse_args()
    raw=pd.read_csv(a.data)
    ts=pd.to_datetime(raw["timestamp"],utc=True)
    assert ts.max()<pd.Timestamp("2026-01-01",tz="UTC"), "G10_2026_DATA_LOADED"
    years={y:load_year(raw,y) for y in (*YEARS,VALIDATION_YEAR)}
    cfg=ExecutionConfig(spread_pips=.5,slippage_pips=.2,expiry_bars=30)
    results=[]
    for p in candidates():
        pre={str(y):backtest(years[y],p,cfg) for y in YEARS}
        val=backtest(years[VALIDATION_YEAR],p,cfg)
        strict=sum(strict_year(pre[str(y)]) for y in YEARS)==3
        min_pf=min(m["profit_factor"] for m in pre.values())
        min_exp=min(m["expectancy_R"] for m in pre.values())
        max_dd=max(m["max_dd_pct"] for m in pre.values())
        total=sum(m["total_R"] for m in pre.values())
        score=2.5*min(min_pf,2.0)/2.0+1.5*min(sum(m["profit_factor"] for m in pre.values())/3.0,2.0)/2.0+1.5*math.tanh(total/150.0)-2.0*min(max_dd,100.0)/100.0
        results.append({**p,"pre_oos":pre,"validation_2025":val,"strict_pre_oos":strict,"min_pf":round(min_pf,6),"min_expectancy_R":round(min_exp,6),"max_dd_pct":round(max_dd,6),"robustness_score":round(score,6)})
    results.sort(key=lambda r:(not r["strict_pre_oos"],-r["robustness_score"]))
    strict=[r for r in results if r["strict_pre_oos"]]
    champion=None
    payload={"schema_version":SCHEMA,"strategy":"Donchian Breakout","research_timeframe":"M5","symbol":"EURUSD","real_data_required":True,"synthetic_fallback":False,"candidate_total":len(results),"catalog":{"windows":WINDOWS,"atr_mults":ATR_MULTS,"rrs":RRS,"buffers_price":BUFFERS,"sides":["long","short"]},"execution_model":{"signal":"closed_candle","entry":"next_bar_open","round_trip_cost_pips":1.4,"same_bar_resolution":"SL first (conservative)","expiry_bars":30},"discovery_years":[2022,2023,2024],"validation_year":2025,"oos_2026":{"loaded":False,"status":"HELD_OUT","start":"2026-01-01"},"qualified_count":len(strict),"champion":champion,"top_20_diagnostics":results[:20],"validated_candidates":[],"selection_frozen":False,"oos_optimization_allowed":False}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"candidate_total":len(results),"qualified_count":len(strict),"champion":champion,"validation_candidates":len(strict)},indent=2))

if __name__=="__main__": main()
