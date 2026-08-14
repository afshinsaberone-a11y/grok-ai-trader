"""Broad deterministic strategy-family sweep on pre-OOS real data only.

Families: trend-following, momentum breakout, Donchian breakout, Bollinger mean reversion,
RSI mean reversion, and London-session breakout. This module never loads 2026+ OOS.
It is a research screen, not a claim that any family is profitable.
"""
from __future__ import annotations

import argparse, json, math
from pathlib import Path
from typing import Any, Callable
import numpy as np
import pandas as pd

SEED = 20260815
RISK_PCT = 0.01
FAMILIES = ("trend", "momentum", "donchian", "bollinger_mr", "rsi_mr", "london_breakout")


def _prep(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    ts = pd.to_datetime(df["timestamp"], utc=True)
    x = df.loc[(ts >= pd.Timestamp(start, tz="UTC")) & (ts < pd.Timestamp(end, tz="UTC"))].copy()
    return x.rename(columns={"timestamp":"Timestamp","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("Timestamp")


def _atr(df, n=14):
    pc=df.Close.shift(); tr=pd.concat([df.High-df.Low,(df.High-pc).abs(),(df.Low-pc).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()


def _signals(df: pd.DataFrame, family: str, p: dict) -> pd.Series:
    c=df.Close; sig=pd.Series(0,index=df.index,dtype=int)
    if family=="trend":
        f=c.ewm(span=p["fast"],adjust=False).mean(); s=c.ewm(span=p["slow"],adjust=False).mean(); t=c.ewm(span=p["trend"],adjust=False).mean()
        sig[(f>s)&(f.shift(1)<=s.shift(1))&(c>t)]=1; sig[(f<s)&(f.shift(1)>=s.shift(1))&(c<t)]=-1
    elif family=="momentum":
        r=c.pct_change(p["lookback"]); sig[r>p["threshold"]]=1; sig[r<-p["threshold"]]=-1
    elif family=="donchian":
        hi=df.High.rolling(p["window"]).max().shift(1); lo=df.Low.rolling(p["window"]).min().shift(1)
        sig[c>hi]=1; sig[c<lo]=-1
    elif family=="bollinger_mr":
        m=c.rolling(p["window"]).mean(); sd=c.rolling(p["window"]).std(); z=(c-m)/sd.replace(0,np.nan)
        sig[z<-p["z"]]=1; sig[z>p["z"]]=-1
    elif family=="rsi_mr":
        d=c.diff(); g=d.clip(lower=0).rolling(14).mean(); l=(-d.clip(upper=0)).rolling(14).mean(); rsi=100-(100/(1+(g/l.replace(0,np.nan))))
        sig[rsi<p["low"]]=1; sig[rsi>p["high"]]=-1
    elif family=="london_breakout":
        h=df.index.hour; session=(h>=p["range_start"])&(h<p["range_end"]); rh=df.High.where(session).groupby(df.index.date).transform("max"); rl=df.Low.where(session).groupby(df.index.date).transform("min")
        active=(h>=p["trade_start"])&(h<=p["trade_end"]); sig[active&(c>rh)]=1; sig[active&(c<rl)]=-1
    return sig


def _backtest(df: pd.DataFrame, family: str, p: dict) -> dict[str, Any]:
    if df.empty: return {"trades":0,"win_rate":0.0,"profit_factor":0.0,"expectancy_R":0.0,"total_R":0.0,"max_dd_pct":100.0}
    sig=_signals(df,family,p); atr=_atr(df); equity=10000.0; peak=equity; maxdd=0.0; pos=0; entry=stop=tp=0.0; rs=[]
    for i in range(1,len(df)):
        row=df.iloc[i]; a=atr.iloc[i]
        if pd.isna(a) or a<=0: continue
        if pos==0 and sig.iloc[i-1]!=0:
            pos=int(sig.iloc[i-1]); entry=float(row.Open); stop=entry-(p["atr"]*a if pos>0 else -p["atr"]*a); tp=entry+(p["rr"]*(entry-stop) if pos>0 else -p["rr"]*(stop-entry)); continue
        if pos>0 and (row.Low<=stop or row.High>=tp or sig.iloc[i]==-1):
            ex=stop if row.Low<=stop else (tp if row.High>=tp else row.Close); r=(ex-entry)/(entry-stop); rs.append(r); equity*=1+r*RISK_PCT; pos=0
        elif pos<0 and (row.High>=stop or row.Low<=tp or sig.iloc[i]==1):
            ex=stop if row.High>=stop else (tp if row.Low<=tp else row.Close); r=(entry-ex)/(stop-entry); rs.append(r); equity*=1+r*RISK_PCT; pos=0
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    wins=[r for r in rs if r>0]; losses=[r for r in rs if r<=0]; gross_loss=abs(sum(losses)); pf=sum(wins)/gross_loss if gross_loss else (float("inf") if wins else 0.0)
    n=len(rs); total=sum(rs)
    return {"trades":n,"win_rate":round(100*sum(r>0 for r in rs)/n,2) if n else 0.0,"profit_factor":round(pf,3) if math.isfinite(pf) else "inf","expectancy_R":round(total/n,4) if n else 0.0,"total_R":round(total,3),"max_dd_pct":round(100*maxdd,2)}


def candidates():
    out=[]
    for fast in (5,9,13,21):
      for slow in (21,55,89):
       if fast<slow: out.append(("trend",{"fast":fast,"slow":slow,"trend":200,"atr":2.0,"rr":2.0}))
    for lb in (3,6,12,24):
      for th in (0.002,0.004,0.006): out.append(("momentum",{"lookback":lb,"threshold":th,"atr":2.0,"rr":2.0}))
    for w in (10,20,40,80): out.append(("donchian",{"window":w,"atr":2.0,"rr":2.0}))
    for w in (20,40,80):
      for z in (1.5,2.0,2.5): out.append(("bollinger_mr",{"window":w,"z":z,"atr":1.5,"rr":1.5}))
    for lo,hi in ((20,80),(25,75),(30,70)):
      out.append(("rsi_mr",{"low":lo,"high":hi,"atr":1.5,"rr":1.5}))
    for atr in (1.0,1.5,2.0): out.append(("london_breakout",{"range_start":7,"range_end":8,"trade_start":8,"trade_end":12,"atr":atr,"rr":2.0}))
    return out


def run(path: str, output: str):
    df=pd.read_csv(path); results=[]
    segs={y:_prep(df,f"{y}-01-01",f"{y+1}-01-01") for y in (2022,2023,2024,2025)}
    for idx,(family,p) in enumerate(candidates(),1):
        yrs=[_backtest(segs[y],family,p) for y in (2022,2023,2024)]
        v=_backtest(segs[2025],family,p)
        min_pf=min(float(y["profit_factor"]) if y["profit_factor"]!="inf" else 3.0 for y in yrs); avg_pf=sum(float(y["profit_factor"]) if y["profit_factor"]!="inf" else 3.0 for y in yrs)/3; maxdd=max(y["max_dd_pct"] for y in yrs); pos=sum(y["expectancy_R"]>0 for y in yrs)
        score=round(2.5*min(min_pf,2)/2 + 1.5*min(avg_pf,2)/2 + 0.75*(pos/3) + 1.5*math.tanh(sum(y["total_R"] for y in yrs)/150) - 2.0*min(maxdd,100)/100,6)
        results.append({"id":idx,"family":family,"params":p,"robustness_score":score,"pre_oos":dict(zip((2022,2023,2024),yrs)),"validation_2025":v})
    results.sort(key=lambda x:-x["robustness_score"])
    report={"schema_version":"forexai.strategy_family_sweep.v1","families":list(FAMILIES),"candidate_count":len(results),"oos_loaded":False,"oos_touched":False,"top":results[:50],"note":"2026+ OOS never loaded"}
    Path(output).parent.mkdir(parents=True,exist_ok=True); Path(output).write_text(json.dumps(report,indent=2,sort_keys=True)); print(json.dumps({"candidate_count":len(results),"top10":results[:10]},indent=2))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",default="artifacts/strategy_family_sweep.json"); a=ap.parse_args(); run(a.data,a.output)
