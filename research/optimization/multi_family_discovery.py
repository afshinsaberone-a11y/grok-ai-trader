"""Multi-family deterministic strategy discovery on pre-OOS real data only.

Families are deliberately simple, rule-based and reproducible. This module never
loads 2026 OOS and never creates synthetic market data.
"""
from __future__ import annotations

import argparse, json, math
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

SEED = 20260815
RISK_PCT = 0.005
MIN_TRADES = 100
VALIDATION_MIN_PF = 1.10
VALIDATION_MAX_DD = 35.0
FAMILIES = (
    "trend_ema_rsi", "momentum_breakout", "donchian_breakout",
    "bollinger_mean_reversion", "rsi_mean_reversion",
    "session_range_breakout", "volatility_expansion", "sp2l_lite",
)


def _native(x: Any) -> Any:
    if isinstance(x, dict): return {str(k): _native(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [_native(v) for v in x]
    if isinstance(x, np.generic): return x.item()
    return x


def indicators(df: pd.DataFrame, p: dict[str, Any]) -> pd.DataFrame:
    d = df.copy(); c, h, l = d.Close, d.High, d.Low
    d["atr"] = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1).rolling(p.get("atr",14)).mean()
    d["ema_f"] = c.ewm(span=p.get("fast",13), adjust=False).mean(); d["ema_s"] = c.ewm(span=p.get("slow",89), adjust=False).mean(); d["ema_t"] = c.ewm(span=p.get("trend",200), adjust=False).mean()
    d["mom"] = c.pct_change(p.get("mom",10)); n=p.get("bb",20); m=c.rolling(n).mean(); s=c.rolling(n).std(); d["bb_mid"], d["bb_up"], d["bb_dn"] = m, m+p.get("bb_k",2.0)*s, m-p.get("bb_k",2.0)*s
    r=p.get("rsi",14); delta=c.diff(); gain=delta.clip(lower=0).rolling(r).mean(); loss=(-delta.clip(upper=0)).rolling(r).mean(); rs=gain/loss.replace(0,np.nan); d["rsi"] = 100-(100/(1+rs))
    d["hh"] = h.rolling(p.get("don",20)).max().shift(1); d["ll"] = l.rolling(p.get("don",20)).min().shift(1); d["hour"] = d.index.hour; d["session"] = ((d.hour>=7)&(d.hour<=16)) | ((d.hour>=12)&(d.hour<=20))
    return d


def signal_family(d: pd.DataFrame, family: str, p: dict[str, Any]) -> pd.Series:
    sig=pd.Series(0,index=d.index,dtype=int)
    if family=="trend_ema_rsi":
        sig[((d.ema_f>d.ema_s)&(d.ema_f.shift()<=d.ema_s.shift())&(d.Close>d.ema_t)&(d.rsi>35)&(d.rsi<70)&d.session)]=1; sig[((d.ema_f<d.ema_s)&(d.ema_f.shift()>=d.ema_s.shift())&(d.Close<d.ema_t)&(d.rsi<65)&(d.rsi>30)&d.session)]=-1
    elif family=="momentum_breakout":
        sig[(d.mom>p["threshold"])&(d.Close>d.hh)&d.session]=1; sig[(d.mom<-p["threshold"])&(d.Close<d.ll)&d.session]=-1
    elif family=="donchian_breakout":
        sig[(d.Close>d.hh)&d.session]=1; sig[(d.Close<d.ll)&d.session]=-1
    elif family=="bollinger_mean_reversion":
        sig[(d.Close<d.bb_dn)&(d.rsi<p["rsi_low"])]=1; sig[(d.Close>d.bb_up)&(d.rsi>p["rsi_high"])]=-1
    elif family=="rsi_mean_reversion":
        sig[(d.rsi<p["rsi_low"])&(d.Close>d.ema_t)]=1; sig[(d.rsi>p["rsi_high"])&(d.Close<d.ema_t)]=-1
    elif family=="session_range_breakout":
        day=d.index.floor("D"); prior=(d.hour<7); rh=d.High.where(prior).groupby(day).cummax().shift(1); rl=d.Low.where(prior).groupby(day).cummin().shift(1); sig[(d.hour>=7)&(d.Close>rh)]=1; sig[(d.hour>=7)&(d.Close<rl)]=-1
    elif family=="volatility_expansion":
        atr_base=d.atr.rolling(p["vol_lookback"]).mean(); expanding=d.atr>atr_base*p["vol_mult"]; sig[expanding&(d.Close>d.ema_t)]=1; sig[expanding&(d.Close<d.ema_t)]=-1
    elif family=="sp2l_lite":
        body=(d.Close-d.Open).abs(); rng=d.High-d.Low; spike=(rng>0)&(body/rng>=p["body_ratio"])&(rng>=p["atr_mult"]*d.atr); gap_up=d.Low>d.High.shift(2); gap_dn=d.High<d.Low.shift(2); sig[spike&gap_up&d.Close>d.Open]=1; sig[spike&gap_dn&d.Close<d.Open]=-1
    return sig


def backtest(df: pd.DataFrame, family: str, p: dict[str, Any]) -> dict[str, Any]:
    d=indicators(df,p); sig=signal_family(d,family,p); equity=10000.0; peak=equity; maxdd=0.0; pos=0; entry=stop=tp=0.0; rs=[]
    for i in range(1,len(d)):
        r=d.iloc[i]; atr=r.atr
        if pd.isna(atr) or atr<=0: continue
        if pos==0 and sig.iloc[i]!=0: pos=int(sig.iloc[i]); entry=float(r.Close); stop=entry-pos*p["atr_stop"]*atr; tp=entry+pos*p["rr"]*abs(entry-stop); continue
        if pos==1 and (r.Low<=stop or r.High>=tp or sig.iloc[i]==-1):
            ex=stop if r.Low<=stop else (tp if r.High>=tp else r.Close); rr=(ex-entry)/abs(entry-stop); rs.append(rr); equity*=1+RISK_PCT*rr; pos=0
        elif pos==-1 and (r.High>=stop or r.Low<=tp or sig.iloc[i]==1):
            ex=stop if r.High>=stop else (tp if r.Low<=tp else r.Close); rr=(entry-ex)/abs(stop-entry); rs.append(rr); equity*=1+RISK_PCT*rr; pos=0
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else (float("inf") if gp>0 else 0.0); total=sum(rs)
    return {"trades":n,"win_rate":round(100*wins/n,2) if n else 0.0,"total_R":round(total,2),"expectancy_R":round(total/n,3) if n else 0.0,"profit_factor":round(pf,2) if np.isfinite(pf) else "inf","max_dd_pct":round(100*maxdd,2),"final_equity":round(equity,2)}


def catalog() -> dict[str, list[dict[str,Any]]]:
    base={"atr":14,"atr_stop":1.5,"rr":2.0,"fast":13,"slow":89,"trend":200,"rsi":14,"don":20,"bb":20}
    return {
        "trend_ema_rsi":[{**base,"fast":f,"slow":s,"trend":t,"atr_stop":a,"rr":rr} for f in (7,13,21) for s in (34,55,89) for t in (150,200,300) for a in (1.4,1.8,2.2) for rr in (1.5,2.5,3.5)],
        "momentum_breakout":[{**base,"mom":m,"threshold":th,"atr_stop":a,"rr":rr,"don":n} for m in (5,10,20) for th in (0.001,0.002,0.003) for a in (1.4,1.8,2.2) for rr in (1.5,2.5,3.5) for n in (10,20)],
        "donchian_breakout":[{**base,"don":n,"atr_stop":a,"rr":rr} for n in (10,20,30,55) for a in (1.4,1.8,2.2) for rr in (1.5,2.5,3.5)],
        "bollinger_mean_reversion":[{**base,"bb":n,"bb_k":k,"rsi_low":lo,"rsi_high":hi,"atr_stop":a,"rr":rr} for n in (14,20,30) for k in (1.5,2.0,2.5) for lo,hi in ((25,75),(30,70)) for a in (1.4,1.8) for rr in (1.0,1.5,2.0)],
        "rsi_mean_reversion":[{**base,"rsi":n,"rsi_low":lo,"rsi_high":hi,"atr_stop":a,"rr":rr} for n in (7,14,21) for lo,hi in ((20,80),(25,75),(30,70)) for a in (1.4,1.8,2.2) for rr in (1.0,1.5,2.0)],
        "session_range_breakout":[{**base,"atr_stop":a,"rr":rr} for a in (1.2,1.6,2.0,2.4) for rr in (1.5,2.0,3.0,4.0)],
        "volatility_expansion":[{**base,"vol_lookback":n,"vol_mult":m,"atr_stop":a,"rr":rr} for n in (10,20,40) for m in (1.1,1.25,1.5) for a in (1.4,1.8,2.2) for rr in (1.5,2.5,3.5)],
        "sp2l_lite":[{**base,"body_ratio":b,"atr_mult":m,"atr_stop":a,"rr":rr} for b in (0.55,0.65,0.75) for m in (1.2,1.5,2.0) for a in (1.0,1.5,2.0) for rr in (1.0,1.5,2.0)],
    }


def score(year_metrics:list[dict[str,Any]])->float:
    if any(x["metrics"]["trades"]<MIN_TRADES for x in year_metrics): return -999.0
    pfs=[3.0 if x["metrics"]["profit_factor"]=="inf" else float(x["metrics"]["profit_factor"]) for x in year_metrics]; ex=[float(x["metrics"]["expectancy_R"]) for x in year_metrics]; dd=[float(x["metrics"]["max_dd_pct"]) for x in year_metrics]
    profitable=sum(v>0 for v in ex)/len(ex); minpf=min(pfs); avpf=sum(pfs)/len(pfs); total=sum(float(x["metrics"]["total_R"]) for x in year_metrics)
    return round(2.5*min(max(minpf,0),2)/2 + 1.5*min(max(avpf,0),2)/2 + profitable + 1.5*math.tanh(total/150) - 2.5*min(max(max(dd),0),100)/100,6)


def discover_family(df: pd.DataFrame, family: str) -> dict[str, Any]:
    years={y:df[(df.index>=f"{y}-01-01")&(df.index<f"{y+1}-01-01")] for y in (2022,2023,2024,2025)}
    results=[]
    for j,p in enumerate(catalog()[family]):
        pre=[{"year":y,"metrics":backtest(years[y],family,p)} for y in (2022,2023,2024)]; s=score(pre); results.append({"family":family,"candidate":j+1,"params":p,"robustness_score":s,"pre_oos":pre})
    results.sort(key=lambda x:(-x["robustness_score"],x["candidate"])); finalists=results[:50]; final=[]
    for x in finalists:
        vm=backtest(years[2025],family,x["params"]); final.append({**x,"validation_2025":vm,"validation_qualifies":float(vm["profit_factor"] if vm["profit_factor"]!="inf" else 3.0)>=VALIDATION_MIN_PF and float(vm["max_dd_pct"])<=VALIDATION_MAX_DD and int(vm["trades"])>=MIN_TRADES})
    qualified=[x for x in final if x["validation_qualifies"]]; qualified.sort(key=lambda x:(-x["robustness_score"],x["candidate"]))
    return {"family":family,"candidate_total":len(results),"qualified_count":len(qualified),"champion":qualified[0] if qualified else None,"top_50":final}


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--data",required=True); ap.add_argument("--output",default="artifacts/multi_family_discovery.json"); ap.add_argument("--family",choices=FAMILIES, default=None)
    args=ap.parse_args(); df=pd.read_csv(args.data); df["timestamp"]=pd.to_datetime(df["timestamp"],utc=True); df=df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("timestamp")
    if args.family:
        result=discover_family(df,args.family); report={"schema_version":"forexai.multi_family_discovery.v1","family":args.family,"result":result,"oos_policy":{"loaded":False,"start":"2026-01-01","status":"HELD_OUT"},"sp2l_status":"SP2L-lite is an engineering proxy; official SP2L PR #2 is not merged into main"}
    else:
        all_results=[]
        for fam in FAMILIES: all_results.append(discover_family(df,fam))
        qualified=[x["champion"] for x in all_results if x["champion"] is not None]; qualified.sort(key=lambda x:(-float(x["robustness_score"]),x["family"],x["candidate"]))
        report={"schema_version":"forexai.multi_family_discovery.v1","families":list(FAMILIES),"results":all_results,"qualified_count":len(qualified),"champion":qualified[0] if qualified else None,"oos_policy":{"loaded":False,"start":"2026-01-01","status":"HELD_OUT"},"sp2l_status":"SP2L-lite is an engineering proxy; official SP2L PR #2 is not merged into main"}
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(_native(report),indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(_native({"family":args.family,"qualified_count":report.get("result",report).get("qualified_count",report.get("qualified_count",0)),"champion":report.get("result",report).get("champion",report.get("champion"))}),indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
