"""Trade-lifecycle trace for London Breakout G3.

This is a debugging audit, not a profitability backtest. It traces raw breakout
signals through entry, risk construction, and exit-state transitions on real M5 data.
2026 is excluded. No optimization and no synthetic data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, validate_ohlc

LONDON=ZoneInfo("Europe/London")
CONFIGS=(
    {"range_minutes":30,"entry_hour":8,"buffer_atr":0.0,"atr_mult":1.0,"rr":1.2,"side_mode":"both"},
    {"range_minutes":60,"entry_hour":8,"buffer_atr":0.05,"atr_mult":1.5,"rr":2.0,"side_mode":"both"},
    {"range_minutes":90,"entry_hour":9,"buffer_atr":0.10,"atr_mult":1.5,"rr":2.0,"side_mode":"both"},
)


def prep(path):
    d=pd.read_csv(path)
    d["Timestamp"]=pd.to_datetime(d["timestamp"],utc=True)
    d=d.set_index("Timestamp").sort_index()
    validate_ohlc(d.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}))
    prev=d.close.shift(1)
    tr=pd.concat([d.high-d.low,(d.high-prev).abs(),(d.low-prev).abs()],axis=1).max(axis=1)
    d["ATR"]=tr.rolling(14,min_periods=14).mean()
    local=d.index.tz_convert(LONDON)
    d["local_date"]=local.date
    d["local_minute"]=local.hour*60+local.minute
    return d


def trace_one(d,p,cfg):
    trace=[]
    entry_candidates=0
    invalid_risk=0
    completed=0
    open_at_day_end=0
    for day,g in d.groupby("local_date",sort=True):
        end=p["entry_hour"]*60
        start=end-p["range_minutes"]
        for i in range(100,len(g)-1):
            if int(g.local_minute.iloc[i])!=end:
                continue
            ref=g[(g.local_minute>=start)&(g.local_minute<end)]
            need=max(2,p["range_minutes"]//5)
            if len(ref)<need:
                continue
            atr=float(g.ATR.iloc[i])
            hi=float(ref.high.max())+p["buffer_atr"]*atr
            lo=float(ref.low.min())-p["buffer_atr"]*atr
            c=float(g.close.iloc[i])
            side=1 if c>hi else -1 if c<lo else 0
            if p["side_mode"]=="breakout_only" and side<0:
                side=0
            if side==0:
                continue
            entry_candidates+=1
            entry_i=i+1
            entry_price=apply_entry_cost(float(g.open.iloc[entry_i]),side,cfg)
            unit=p["atr_mult"]*atr
            stop=entry_price-side*unit
            target=entry_price+side*p["rr"]*unit
            if not np.isfinite(unit) or unit<=0 or not np.isfinite(stop) or not np.isfinite(target) or (target-entry_price)*side<=0:
                invalid_risk+=1
                if len(trace)<12:
                    trace.append({"day":str(day),"stage":"invalid_risk","side":side,"atr":atr,"entry":entry_price,"unit":unit,"stop":stop,"target":target})
                continue
            exit_found=False
            first_hit=None
            for j in range(entry_i,min(len(g),entry_i+31)):
                hit_sl=float(g.low.iloc[j])<=stop if side==1 else float(g.high.iloc[j])>=stop
                hit_tp=float(g.high.iloc[j])>=target if side==1 else float(g.low.iloc[j])<=target
                if hit_sl:
                    first_hit="SL"; exit_found=True; break
                if hit_tp:
                    first_hit="TP"; exit_found=True; break
            if exit_found:
                completed+=1
            else:
                open_at_day_end+=1
            if len(trace)<12:
                trace.append({"day":str(day),"stage":"completed" if exit_found else "open_at_day_end","side":side,"atr":round(atr,8),"entry":round(entry_price,8),"stop":round(stop,8),"target":round(target,8),"first_exit":first_hit})
    return {
        "config":p,
        "entry_candidates":entry_candidates,
        "invalid_risk":invalid_risk,
        "completed_or_hit":completed,
        "open_at_day_end":open_at_day_end,
        "sample_trace":trace,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    d=prep(args.data)
    cfg=ExecutionConfig(spread_pips=.5,slippage_pips=.2)
    payload={
        "schema":"forexai.london_trade_lifecycle_audit.v1",
        "source_rows":len(d),
        "configs":[trace_one(d,p,cfg) for p in CONFIGS],
        "policy":{"real_data_only":True,"profitability_evaluated":False,"oos_2026_used":False},
    }
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
