"""G16: fail-closed Regime Z-Score Reversion discovery on real EURUSD M5.
IS 2022-24 ranks; 2025 is pass/fail only; 2026+ is rejected at input.
HistData M1 OHLC is BID; ASK is reconstructed with the fixed spread assumption.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import numpy as np
import pandas as pd

SCHEMA="forexai.g16.regime_zscore_reversion.v1"
YEARS=(2022,2023,2024)
VALIDATION_YEAR=2025
ALL_YEARS=(*YEARS,VALIDATION_YEAR)
OOS_START=pd.Timestamp("2026-01-01",tz="UTC")
INITIAL_EQUITY,RISK_PCT,PIP=10000.0,0.005,0.0001
BASE_COST,STRESS_COST,SEVERE_COST=(0.5,0.2),(0.75,0.30),(1.0,0.5)
IS_TRADES,IS_PF,IS_DD=100,1.05,35.0
VAL_TRADES,VAL_PF,VAL_DD=100,1.10,35.0
STRESS_TRADES,STRESS_PF,STRESS_DD=100,1.0,35.0
MAX_FINALISTS=25


def catalog():
    keys=("z_lookback","entry_z","adx_max","atr_stop","max_hold_bars")
    vals=((20,40,60),(1.5,2.0,2.5),(15.0,20.0,25.0),(1.5,2.0),(24,48))
    return [dict(zip(keys,x))|{"exit_z":0.0} for x in itertools.product(*vals)]


def _entry_fill(bid_open: float, pos: int, spread_pips: float, slippage_pips: float) -> float:
    """BUY enters at reconstructed ASK+slippage; SELL enters at BID-slippage."""
    if pos==1:
        return float(bid_open)+(spread_pips+slippage_pips)*PIP
    return float(bid_open)-slippage_pips*PIP


def _exit_fill(side_quote: float, pos: int, slippage_pips: float) -> float:
    """side_quote is BID for a long sale and ASK for a short cover."""
    if pos==1:
        return float(side_quote)-slippage_pips*PIP
    return float(side_quote)+slippage_pips*PIP


def _round_trip_cost_pips(spread_pips: float, slippage_pips: float) -> float:
    """BID OHLC: spread is paid once; slippage is paid on entry and exit."""
    return float(spread_pips)+2.0*float(slippage_pips)


def _stop_hit(pos: int, high_bid: float, low_bid: float, stop: float, spread_pips: float) -> bool:
    if pos==1:
        return float(low_bid)<=float(stop)
    return float(high_bid)+float(spread_pips)*PIP>=float(stop)


def _stop_side_quote(pos: int, stop: float, open_bid: float, spread_pips: float) -> float:
    if pos==1:
        return min(float(stop),float(open_bid))
    open_ask=float(open_bid)+float(spread_pips)*PIP
    return max(float(stop),open_ask)


def _features(frame: pd.DataFrame, lookback: int) -> pd.DataFrame:
    required={"Open","High","Low","Close"}
    if required-set(frame.columns):
        raise ValueError(f"G16_REQUIRED_COLUMNS_MISSING:{sorted(required-set(frame.columns))}")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("G16_BAD_CHRONOLOGICAL_INDEX")
    hi,lo,cl=(frame[c].astype(float) for c in ("High","Low","Close"))
    if not ((hi>=frame[["Open","Close"]].max(axis=1))&(lo<=frame[["Open","Close"]].min(axis=1))&(hi>=lo)).all():
        raise ValueError("G16_OHLC_INVARIANT_FAIL")
    tr=pd.concat([hi-lo,(hi-cl.shift()).abs(),(lo-cl.shift()).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    up,down=hi.diff(),-lo.diff()
    pdm=pd.Series(np.where((up>down)&(up>0),up,0.0),index=frame.index)
    mdm=pd.Series(np.where((down>up)&(down>0),down,0.0),index=frame.index)
    pdi=100*pdm.ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr.replace(0,np.nan)
    mdi=100*mdm.ewm(alpha=1/14,adjust=False,min_periods=14).mean()/atr.replace(0,np.nan)
    dx=100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)
    adx=dx.ewm(alpha=1/14,adjust=False,min_periods=14).mean()
    mean=cl.rolling(lookback,min_periods=lookback).mean()
    sd=cl.rolling(lookback,min_periods=lookback).std(ddof=0).replace(0,np.nan)
    return pd.DataFrame({"Open":frame.Open.astype(float),"High":hi,"Low":lo,"Close":cl,
                         "atr":atr,"adx":adx,"z":(cl-mean)/sd},index=frame.index)


def _entry(z1: float, z2: float, adx: float, p: dict) -> int:
    if not np.isfinite([z1,z2,adx]).all() or adx>p["adx_max"]:
        return 0
    t=p["entry_z"]
    if z1<=-t<z2:
        return 1
    if z1>=t>z2:
        return -1
    return 0


def backtest(frame: pd.DataFrame, p: dict, costs=BASE_COST) -> dict:
    spread,slip=map(float,costs)
    if spread<0 or slip<0:
        raise ValueError("G16_NEGATIVE_COST")
    if frame.empty:
        return {"trades":0,"total_R":0.0,"expectancy_R":0.0,"profit_factor":0.0,"max_dd_pct":0.0,
                "final_equity":INITIAL_EQUITY,"round_trip_cost_pips":_round_trip_cost_pips(spread,slip)}
    d=_features(frame,int(p["z_lookback"]))
    op,hi,lo,cl=(d[c].to_numpy(float) for c in ("Open","High","Low","Close"))
    atr,z,adx=(d[c].to_numpy(float) for c in ("atr","z","adx"))
    eq=peak=INITIAL_EQUITY
    maxdd=0.0
    pos=0
    entry=stop=unit=0.0
    entry_i=-1
    rs=[]
    entries=same_bar=0

    def close(side_quote: float) -> None:
        nonlocal eq,peak,maxdd,pos
        fill=_exit_fill(side_quote,pos,slip)
        r=pos*(fill-entry)/unit
        factor=1+RISK_PCT*r
        if not np.isfinite(r) or not np.isfinite(factor) or factor<=0:
            raise RuntimeError("G16_NONFINITE_OR_BANKRUPTCY")
        eq*=factor
        rs.append(float(r))
        peak=max(peak,eq)
        maxdd=max(maxdd,(peak-eq)/peak)
        pos=0

    for i in range(2,len(d)):
        z1=z[i-1]
        if pos:
            if ((pos==1 and z1>=-p["exit_z"]) or
                (pos==-1 and z1<=p["exit_z"]) or
                i-entry_i>=p["max_hold_bars"]):
                exit_quote=op[i] if pos==1 else op[i]+spread*PIP
                close(exit_quote)
                continue
            if _stop_hit(pos,hi[i],lo[i],stop,spread):
                close(_stop_side_quote(pos,stop,op[i],spread))
                continue
            continue

        side=_entry(z1,z[i-2],adx[i-1],p)
        if not side or not np.isfinite(atr[i-1]) or atr[i-1]<=0:
            continue
        pos=side
        entry=_entry_fill(op[i],pos,spread,slip)
        unit=p["atr_stop"]*atr[i-1]
        if not np.isfinite(unit) or unit<=0:
            pos=0
            continue
        stop=entry-pos*unit
        entry_i=i
        entries+=1
        if _stop_hit(pos,hi[i],lo[i],stop,spread):
            same_bar+=1
            close(_stop_side_quote(pos,stop,op[i],spread))

    if pos:
        exit_quote=cl[-1] if pos==1 else cl[-1]+spread*PIP
        close(exit_quote)
    if pos or entries!=len(rs):
        raise RuntimeError("G16_EXECUTION_INTEGRITY_FAIL")
    expected=INITIAL_EQUITY
    for r in rs:
        expected*=1+RISK_PCT*r
    if not np.isclose(eq,expected,rtol=1e-12,atol=1e-8):
        raise RuntimeError("G16_EQUITY_RECONCILIATION_FAIL")
    a=np.asarray(rs)
    wins=a[a>0]
    losses=a[a<=0]
    gl=abs(float(losses.sum()))
    pf=float(wins.sum())/gl if gl else ("inf" if len(wins) else 0.0)
    n=len(rs)
    total=float(a.sum())
    return {"trades":n,"total_R":round(total,6),"expectancy_R":round(total/n,6) if n else 0.0,
            "profit_factor":round(pf,6) if pf!="inf" else pf,
            "win_rate_pct":round(float((a>0).mean()*100),3) if n else 0.0,
            "max_dd_pct":round(maxdd*100,6),"final_equity":round(eq,2),
            "net_return_pct":round((eq/INITIAL_EQUITY-1)*100,6),
            "entries":n,"exits":n,"open_position_end":False,
            "spread_pips":spread,"slippage_pips":slip,
            "round_trip_cost_pips":_round_trip_cost_pips(spread,slip),
            "same_bar_stop_first_count":same_bar,"price_basis":"BID_OHLC_ASK_RECONSTRUCTED"}


def _pf(m):
    return 3.0 if m.get("profit_factor")=="inf" else float(m.get("profit_factor",0))


def _gate(m,trades,pf,dd):
    r=[]
    if m["trades"]<trades:r.append(f"trades<{trades}")
    if _pf(m)<pf:r.append(f"profit_factor<{pf}")
    if m["expectancy_R"]<=0:r.append("expectancy_R<=0")
    if m["total_R"]<=0:r.append("total_R<=0")
    if m["final_equity"]<=INITIAL_EQUITY:r.append("final_equity<=initial_equity")
    if m["max_dd_pct"]>dd:r.append(f"max_dd_pct>{dd}")
    return r


def _is_reject(by):
    return {str(y):r for y in YEARS if (r:=_gate(by[str(y)],IS_TRADES,IS_PF,IS_DD))}


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()


def _load(data_path,manifest_path):
    data,mf=Path(data_path),Path(manifest_path)
    if not data.is_file() or not data.stat().st_size:
        raise ValueError("G16_DATA_MISSING")
    if not mf.is_file():
        raise ValueError("G16_MANIFEST_MISSING")
    m=json.loads(mf.read_text(encoding="utf-8"))
    dh=hashlib.sha256(data.read_bytes()).hexdigest()
    mh=hashlib.sha256(mf.read_bytes()).hexdigest()
    if m.get("symbol")!="EURUSD":
        raise ValueError("G16_SYMBOL_MISMATCH")
    if str(m.get("timeframe","")).upper()!="M5":
        raise ValueError("G16_TIMEFRAME_MISMATCH")
    if m.get("quality_status")!="PASS":
        raise ValueError("G16_QUALITY_NOT_PASS")
    if "HistData" not in str(m.get("source","")):
        raise ValueError("G16_SOURCE_NOT_HISTDATA")
    if m.get("data_sha256")!=dh:
        raise ValueError("G16_DATA_SHA256_MISMATCH")
    if not m.get("source_hash"):
        raise ValueError("G16_SOURCE_HASH_MISSING")
    raw=pd.read_csv(data)
    need={"timestamp","open","high","low","close","volume"}
    if need-set(raw.columns):
        raise ValueError(f"G16_REQUIRED_COLUMNS_MISSING:{sorted(need-set(raw.columns))}")
    ts=pd.to_datetime(raw.timestamp,format="mixed",utc=True,errors="raise")
    if ts.isna().any() or ts.duplicated().any() or not ts.is_monotonic_increasing:
        raise ValueError("G16_TIMESTAMP_SEQUENCE_INVALID")
    if len(raw)!=int(m.get("rows",-1)):
        raise ValueError("G16_ROW_COUNT_MISMATCH")
    if ts.max()>=OOS_START:
        raise ValueError("G16_OOS_POLICY_VIOLATION_2026_DATA_PRESENT")
    if ts.min()>=pd.Timestamp("2022-01-08",tz="UTC"):
        raise ValueError("G16_DATA_START_TOO_LATE")
    if not ((ts.dt.minute%5==0)&(ts.dt.second==0)&(ts.dt.microsecond==0)).all():
        raise ValueError("G16_M5_ALIGNMENT_FAIL")
    if not set(ALL_YEARS).issubset(set(ts.dt.year.astype(int))):
        raise ValueError("G16_REQUIRED_YEAR_MISSING")
    raw["timestamp"]=ts
    for c in ("open","high","low","close","volume"):
        raw[c]=pd.to_numeric(raw[c],errors="raise")
        if not np.isfinite(raw[c].to_numpy(float)).all():
            raise ValueError(f"G16_NONFINITE:{c}")
    if not ((raw.high>=raw[["open","close"]].max(axis=1))&
            (raw.low<=raw[["open","close"]].min(axis=1))&(raw.high>=raw.low)).all():
        raise ValueError("G16_RAW_OHLC_INVALID")
    if m.get("start") and pd.to_datetime(m["start"],utc=True)!=ts.min():
        raise ValueError("G16_MANIFEST_START_MISMATCH")
    if m.get("end") and pd.to_datetime(m["end"],utc=True)!=ts.max():
        raise ValueError("G16_MANIFEST_END_MISMATCH")
    frame=raw.rename(columns={"timestamp":"Timestamp","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("Timestamp")
    return frame,m,dh,mh


def run_discovery(data_path,manifest_path):
    frame,m,dh,mh=_load(data_path,manifest_path)
    years={y:frame.loc[(frame.index>=pd.Timestamp(f"{y}-01-01",tz="UTC"))&
                        (frame.index<pd.Timestamp(f"{y+1}-01-01",tz="UTC"))] for y in ALL_YEARS}
    if any(part.empty for part in years.values()):
        raise ValueError("G16_EMPTY_REQUIRED_YEAR")
    ranked=[]
    total_trades=0
    for cid,p in enumerate(catalog(),1):
        by={str(y):backtest(years[y],p) for y in YEARS}
        total_trades+=sum(x["trades"] for x in by.values())
        rejects=_is_reject(by)
        pfs=[_pf(by[str(y)]) for y in YEARS]
        score=(1.5*min(min(pfs),2)/2+
               0.75*min(float(np.mean(pfs)),2)/2+
               np.tanh(sum(x["total_R"] for x in by.values())/150)-
               2*max(x["max_dd_pct"] for x in by.values())/100)
        ranked.append({"candidate_id":cid,"params":p,"is_metrics_by_year":by,
                       "is_gate_pass":not rejects,"is_rejections_by_year":rejects,
                       "is_score":round(float(score),8)})
    if total_trades<=0:
        raise RuntimeError("G16_NO_IS_TRADES_SIGNAL_INTEGRITY_FAILURE")
    ranked.sort(key=lambda x:(-x["is_score"],x["candidate_id"]))
    passed=[x for x in ranked if x["is_gate_pass"]]
    finalists=passed[:MAX_FINALISTS]
    evaluated=[]
    for x in finalists:
        p=x["params"]
        val=backtest(years[2025],p)
        vr=_gate(val,VAL_TRADES,VAL_PF,VAL_DD)
        stress={str(y):backtest(years[y],p,STRESS_COST) for y in ALL_YEARS}
        sr={y:r for y,v in stress.items() if (r:=_gate(v,STRESS_TRADES,STRESS_PF,STRESS_DD))}
        severe=backtest(years[2025],p,SEVERE_COST)
        evaluated.append({**x,"validation_2025":val,"validation_pass":not vr,
                          "validation_rejections":vr,"moderate_stress_by_year":stress,
                          "moderate_stress_pass":not sr,"moderate_stress_rejections":sr,
                          "severe_2025_diagnostic":severe})
    qualified=[x for x in evaluated if x["validation_pass"] and x["moderate_stress_pass"]]
    frozen=None
    if qualified:
        x=qualified[0]
        frozen={"family":"regime_zscore_reversion","symbol":"EURUSD","timeframe":"M5",
                "candidate_id":x["candidate_id"],"params":x["params"],"risk_pct":RISK_PCT,
                "data_sha256":dh,"manifest_sha256":mh,"is_years":list(YEARS),
                "validation_year":2025,"baseline_cost":BASE_COST,"moderate_stress_cost":STRESS_COST,
                "oos_start":"2026-01-01","oos_read_during_discovery":False}
        frozen["config_sha256"]=_hash(frozen)
    decision=("NO_GO_NO_IS_QUALIFIED_CANDIDATES" if not passed else
              ("NO_GO_VALIDATION_OR_COST_STRESS_FAILED" if not qualified else "FROZEN_CANDIDATE_HOLDOUT_PENDING"))
    return {"schema_version":SCHEMA,"strategy":"Regime Z-Score Reversion","symbol":"EURUSD","timeframe":"M5",
            "real_data_required":True,"synthetic_fallback":False,
            "source_data":{"source":m.get("source"),"dataset_id":m.get("dataset_id"),"rows":len(frame),
                           "start":str(frame.index.min()),"end":str(frame.index.max()),"data_sha256":dh,
                           "manifest_sha256":mh,"quality_status":m["quality_status"],
                           "price_basis":"BID_OHLC","ask_reconstruction":"bid_plus_assumed_spread"},
            "protocol":{"catalog_locked":True,"catalog_total":len(ranked),"is_ranks_candidates":True,
                        "is_used_for_ranking":True,"validation_2025_is_pass_fail_only":True,
                        "validation_used_for_ranking":False,"max_validation_finalists":MAX_FINALISTS,
                        "signal":"fresh closed-bar Z crossing; next-open entry",
                        "regime":"Wilder ADX(14) <= candidate threshold",
                        "exit":"Z returns through zero, BID/ASK-aware stop, or max hold",
                        "2026_loaded":False},
            "costs":{"baseline_round_trip_pips":_round_trip_cost_pips(*BASE_COST),
                     "moderate_stress_round_trip_pips":_round_trip_cost_pips(*STRESS_COST),
                     "severe_diagnostic_round_trip_pips":_round_trip_cost_pips(*SEVERE_COST),
                     "spread_paid_once":True,"slippage_paid_each_side":True,
                     "commission_included":False,"swap_included":False},
            "gates":{"is_each_year":{"trades":IS_TRADES,"pf":IS_PF,"max_dd_pct":IS_DD,"all_years_required":True},
                     "validation_2025":{"trades":VAL_TRADES,"pf":VAL_PF,"max_dd_pct":VAL_DD},
                     "moderate_stress_2022_2025":{"trades":STRESS_TRADES,"pf":STRESS_PF,"max_dd_pct":STRESS_DD}},
            "catalog":{"candidate_total":len(ranked),"is_qualified_count":len(passed),
                       "validation_finalists_evaluated":len(finalists),"fully_qualified_count":len(qualified),
                       "total_is_trades_across_catalog":total_trades},
            "decision":decision,"top_20_is_diagnostics":ranked[:20],"evaluated_finalists":evaluated,
            "frozen_candidate":frozen,"selection_frozen":frozen is not None,
            "promotion_decision":"HOLDOUT_NOT_RUN_NO_PROMOTION",
            "demo_authorized":False,"live_authorized":False,"orders_submitted":False,
            "oos_policy":{"loaded":False,"status":"HELD_OUT","start":"2026-01-01",
                          "oos_runner_invoked":False,"optimization_allowed":False,
                          "oos_optimization_allowed":False}}


def main():
    ap=argparse.ArgumentParser(description="Fail-closed G16 real-data EURUSD M5 discovery")
    ap.add_argument("--data",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    report=run_discovery(a.data,a.manifest)
    out=Path(a.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"catalog":report["catalog"],"decision":report["decision"],
                      "costs":report["costs"],"oos_loaded":report["oos_policy"]["loaded"]},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
