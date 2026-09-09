from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.regime_aware_event_discovery_g6 import prepare, signal
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost

CANDIDATES = [
    {"name": "atrpct_050", "fast_ema": 16, "slow_ema": 50, "atr_pct": 0.50, "atr_mult": 1.0, "rr": 2.0},
    {"name": "atrpct_065", "fast_ema": 16, "slow_ema": 50, "atr_pct": 0.65, "atr_mult": 1.0, "rr": 2.0},
]
YEARS = [2022, 2023, 2024, 2025]
MAX_HOLD = 24
GATES = {"min_profitable_years": 3, "min_pf_each_year": 1.05, "min_expectancy": 0.0, "min_trades_each_year": 100, "max_dd_pct": 35.0}


def features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    tr = pd.concat([(d.High-d.Low), (d.High-d.Close.shift()).abs(), (d.Low-d.Close.shift()).abs()], axis=1).max(axis=1)
    d["ATR14"] = tr.rolling(14).mean()
    plus = (d.High.diff()).clip(lower=0.0)
    minus = (-d.Low.diff()).clip(lower=0.0)
    pdi = 100 * plus.rolling(14).mean() / d["ATR14"].replace(0, np.nan)
    mdi = 100 * minus.rolling(14).mean() / d["ATR14"].replace(0, np.nan)
    d["DX14"] = (100 * (pdi-mdi).abs() / (pdi+mdi).replace(0, np.nan)).fillna(0)
    d["ADX14"] = d["DX14"].rolling(14).mean()
    d["ADX_Q"] = d["ADX14"].rolling(96, min_periods=48).rank(pct=True)
    d["EMA_SLOPE_ATR"] = (d["EMA16"] - d["EMA16"].shift(4)) / d["ATR14"].replace(0, np.nan)
    d["TREND_PERSIST"] = (d["EMA16"] > d["EMA50"]).astype(float).rolling(8).mean()
    return d


def bucket(x, low, high):
    if pd.isna(x): return "unknown"
    if x < low: return "low"
    if x > high: return "high"
    return "mid"


def run_candidate(d, c, mode):
    s = signal(d, c["fast_ema"], c["slow_ema"], c["atr_pct"])
    trades=[]; pos=None
    for i in range(1, len(d)-1):
        if pos is not None:
            age=i-pos["entry_i"]
            hi=float(d.High.iloc[i]); lo=float(d.Low.iloc[i])
            hit_sl=lo<=pos["sl"] if pos["side"]==1 else hi>=pos["sl"]
            hit_tp=hi>=pos["tp"] if pos["side"]==1 else lo<=pos["tp"]
            if hit_sl or hit_tp or age>=MAX_HOLD:
                if hit_sl: raw=pos["sl"]
                elif hit_tp: raw=pos["tp"]
                else: raw=float(d.Close.iloc[i])
                exitp=apply_exit_cost(raw,pos["side"],ExecutionConfig())
                r=(exitp-pos["entry"])/(pos["entry"]-pos["sl"])*pos["side"]
                trades.append({**pos,"exit_i":i,"r":r,"exit_reason":"SL" if hit_sl else "TP" if hit_tp else "EXPIRY"})
                pos=None
        if pos is None and bool(s.iloc[i-1]) and i < len(d)-1:
            side=int(s.iloc[i-1])
            raw=float(d.Open.iloc[i])
            entry=apply_entry_cost(raw,side,ExecutionConfig())
            atr=float(d.ATR14.iloc[i-1])
            if not np.isfinite(atr) or atr<=0: continue
            risk=atr*c["atr_mult"]
            sl=entry-risk*side; tp=entry+risk*c["rr"]*side
            pos={"entry_i":i,"side":side,"entry":entry,"sl":sl,"tp":tp,
                 "adx_q":d.ADX_Q.iloc[i-1],"trend_persist":d.TREND_PERSIST.iloc[i-1],
                 "slope":d.EMA_SLOPE_ATR.iloc[i-1],"atr":atr}
    if pos is not None:
        # diagnostic end-of-year/day closure only; promotion still requires canonical re-run
        raw=float(d.Close.iloc[-1]); exitp=apply_exit_cost(raw,pos["side"],ExecutionConfig())
        r=(exitp-pos["entry"])/(pos["entry"]-pos["sl"])*pos["side"]
        trades.append({**pos,"exit_i":len(d)-1,"r":r,"exit_reason":"END"})
    return pd.DataFrame(trades)


def metrics(x):
    if x.empty: return {"trades":0,"win_rate":0.0,"total_R":0.0,"expectancy_R":0.0,"profit_factor":0.0,"max_drawdown_pct":0.0}
    r=x.r.to_numpy(float); wins=r[r>0].sum(); losses=-r[r<0].sum()
    eq=np.cumsum(r); peak=np.maximum.accumulate(eq); dd=np.max(peak-eq) if len(eq) else 0
    return {"trades":int(len(r)),"win_rate":float((r>0).mean()*100),"total_R":float(r.sum()),"expectancy_R":float(r.mean()),"profit_factor":float(wins/losses) if losses>0 else float("inf"),"max_drawdown_pct":float(dd*0.5)}


def gate(m):
    return m["trades"]>=GATES["min_trades_each_year"] and m["profit_factor"]>=GATES["min_pf_each_year"] and m["expectancy_R"]>GATES["min_expectancy"] and m["max_drawdown_pct"]<=GATES["max_dd_pct"]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",required=True); args=ap.parse_args()
    d=pd.read_csv(args.data,parse_dates=["Timestamp"]); d=d.sort_values("Timestamp").reset_index(drop=True)
    d=d[d.Timestamp.dt.year.isin(YEARS)].copy(); d=prepare(d); d=features(d)
    out={"schema":"forexai.g11.adaptive_regime_gating.v1","execution_model":{"next_bar_open":True,"round_trip_cost_pips":1.4,"same_bar_resolution":"SL first (conservative)","max_hold_bars":24},"data":{"symbol":"EURUSD","timeframe":"M15","years":YEARS,"synthetic_data":False,"oos_2026_used":False},"parameter_selection":{"used_2025":False},"gates":GATES,"champion":None,"candidates":[]}
    for c in CANDIDATES:
        cr={"candidate":c,"variants":{}}
        for mode in ["baseline","adaptive"]:
            rows=[]
            for y in YEARS:
                yy=d[d.Timestamp.dt.year==y].reset_index(drop=True)
                t=run_candidate(yy,c,mode)
                if mode=="adaptive" and not t.empty:
                    aq=t.adx_q.fillna(0.5); tp=t.trend_persist.fillna(0.5); sl=t.slope.fillna(0)
                    # Fixed, pre-declared gate: trade only when trend persistence is not weak,
                    # ADX is above its rolling median, and slope agrees with direction.
                    keep=(aq>=0.50)&(tp>=0.50)&(((t.side==1)&(sl>0))|((t.side==-1)&(sl<0)))
                    t=t[keep].copy()
                rows.append({"year":y,"metrics":metrics(t)})
            qualified_years=sum(gate(x["metrics"]) for x in rows)
            cr["variants"][mode]={"years":rows,"profitable_years":sum(x["metrics"]["expectancy_R"]>0 for x in rows),"qualified_years":qualified_years}
        out["candidates"].append(cr)
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({"candidates":len(CANDIDATES),"champion":None}))

if __name__=="__main__": main()
