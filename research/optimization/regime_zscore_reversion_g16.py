"""G16: fail-closed Regime Z-Score Reversion discovery on real EURUSD M5.
IS 2022-24 ranks; 2025 is pass/fail only; 2026+ is rejected at input.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

SCHEMA = "forexai.g16.regime_zscore_reversion.v1"
YEARS = (2022, 2023, 2024)
VALIDATION_YEAR = 2025
ALL_YEARS = (*YEARS, VALIDATION_YEAR)
OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
INITIAL_EQUITY, RISK_PCT, PIP = 10000.0, 0.005, 0.0001
BASE_COST, STRESS_COST, SEVERE_COST = (0.5, 0.2), (0.75, 0.30), (1.0, 0.5)
IS_TRADES, IS_PF, IS_DD = 100, 1.05, 35.0
VAL_TRADES, VAL_PF, VAL_DD = 100, 1.10, 35.0
STRESS_TRADES, STRESS_PF, STRESS_DD = 100, 1.0, 35.0
MAX_FINALISTS = 25


def catalog() -> list[dict[str, Any]]:
    """Fixed 108-candidate grid, independent of the observed data."""
    keys = ("z_lookback", "entry_z", "adx_max", "atr_stop", "max_hold_bars")
    values = ((20, 40, 60), (1.5, 2.0, 2.5), (15.0, 20.0, 25.0), (1.5, 2.0), (24, 48))
    return [dict(zip(keys, row)) | {"exit_z": 0.0} for row in itertools.product(*values)]


def _features(frame: pd.DataFrame, lookback: int) -> pd.DataFrame:
    required = {"Open", "High", "Low", "Close"}
    if required - set(frame.columns):
        raise ValueError(f"G16_REQUIRED_COLUMNS_MISSING:{sorted(required-set(frame.columns))}")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("G16_BAD_CHRONOLOGICAL_INDEX")
    hi, lo, cl = (frame[c].astype(float) for c in ("High", "Low", "Close"))
    if not ((hi >= frame[["Open", "Close"]].max(axis=1)) &
            (lo <= frame[["Open", "Close"]].min(axis=1)) & (hi >= lo)).all():
        raise ValueError("G16_OHLC_INVARIANT_FAIL")
    tr = pd.concat([hi-lo, (hi-cl.shift()).abs(), (lo-cl.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    up, down = hi.diff(), -lo.diff()
    pdm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=frame.index)
    mdm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=frame.index)
    smooth_tr = atr.replace(0.0, np.nan)
    pdi = 100*pdm.ewm(alpha=1/14, adjust=False, min_periods=14).mean()/smooth_tr
    mdi = 100*mdm.ewm(alpha=1/14, adjust=False, min_periods=14).mean()/smooth_tr
    dx = 100*(pdi-mdi).abs()/(pdi+mdi).replace(0.0, np.nan)
    adx = dx.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    mean = cl.rolling(lookback, min_periods=lookback).mean()
    sd = cl.rolling(lookback, min_periods=lookback).std(ddof=0).replace(0.0, np.nan)
    return pd.DataFrame({"Open": frame.Open, "High": hi, "Low": lo, "Close": cl,
                         "atr": atr, "adx": adx, "z": (cl-mean)/sd}, index=frame.index)


def _entry(z1: float, z2: float, adx: float, p: dict[str, Any]) -> int:
    if not np.isfinite([z1, z2, adx]).all() or adx > p["adx_max"]:
        return 0
    t = p["entry_z"]
    if z1 <= -t < z2: return 1
    if z1 >= t > z2: return -1
    return 0


def backtest(frame: pd.DataFrame, p: dict[str, Any], costs: tuple[float, float] = BASE_COST) -> dict[str, Any]:
    spread, slip = map(float, costs)
    if spread < 0 or slip < 0: raise ValueError("G16_NEGATIVE_COST")
    if frame.empty: return {"trades": 0, "total_R": 0.0, "expectancy_R": 0.0,
                            "profit_factor": 0.0, "max_dd_pct": 0.0,
                            "final_equity": INITIAL_EQUITY, "round_trip_cost_pips": 2*(spread+slip)}
    d = _features(frame, int(p["z_lookback"]))
    op, hi, lo, cl = (d[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
    atr, z, adx = (d[c].to_numpy(float) for c in ("atr", "z", "adx"))
    adverse = (spread+slip)*PIP
    eq = peak = INITIAL_EQUITY; maxdd = 0.0; pos = 0
    entry = stop = unit = 0.0; entry_i = -1; rs: list[float] = []; entries = same_bar = 0
    def close(raw: float) -> None:
        nonlocal eq, peak, maxdd, pos
        fill = raw-pos*adverse
        r = pos*(fill-entry)/unit
        factor = 1+RISK_PCT*r
        if not np.isfinite(r) or not np.isfinite(factor) or factor <= 0:
            raise RuntimeError("G16_NONFINITE_OR_BANKRUPTCY")
        eq *= factor; rs.append(float(r)); peak=max(peak,eq)
        maxdd=max(maxdd,(peak-eq)/peak); pos=0
    for i in range(2, len(d)):
        z1 = z[i-1]
        if pos:
            if ((pos == 1 and z1 >= -p["exit_z"]) or
                (pos == -1 and z1 <= p["exit_z"]) or
                i-entry_i >= p["max_hold_bars"]):
                close(op[i]); continue
            if (pos == 1 and lo[i] <= stop) or (pos == -1 and hi[i] >= stop):
                close(min(stop,op[i]) if pos == 1 else max(stop,op[i])); continue
            continue
        side = _entry(z1, z[i-2], adx[i-1], p)
        if not side or not np.isfinite(atr[i-1]) or atr[i-1] <= 0: continue
        pos=side; entry=op[i]+pos*adverse; unit=p["atr_stop"]*atr[i-1]
        if not np.isfinite(unit) or unit <= 0: pos=0; continue
        stop=entry-pos*unit; entry_i=i; entries += 1
        # Check the entry candle immediately; stop wins any ambiguous path.
        if (pos == 1 and lo[i] <= stop) or (pos == -1 and hi[i] >= stop):
            same_bar += 1; close(min(stop,op[i]) if pos == 1 else max(stop,op[i]))
    if pos: close(cl[-1])
    if pos or entries != len(rs): raise RuntimeError("G16_EXECUTION_INTEGRITY_FAIL")
    expected=INITIAL_EQUITY
    for r in rs: expected *= 1+RISK_PCT*r
    if not np.isclose(eq,expected,rtol=1e-12,atol=1e-8): raise RuntimeError("G16_EQUITY_RECONCILIATION_FAIL")
    a=np.asarray(rs); wins=a[a>0]; losses=a[a<=0]; gl=abs(float(losses.sum()))
    pf=float(wins.sum())/gl if gl else ("inf" if len(wins) else 0.0)
    n=len(rs); total=float(a.sum())
    return {"trades":n,"total_R":round(total,6),"expectancy_R":round(total/n,6) if n else 0.0,
            "profit_factor":round(pf,6) if pf != "inf" else pf,
            "win_rate_pct":round(float((a>0).mean()*100),3) if n else 0.0,
            "max_dd_pct":round(maxdd*100,6),"final_equity":round(eq,2),
            "net_return_pct":round((eq/INITIAL_EQUITY-1)*100,6),"entries":n,"exits":n,
            "open_position_end":False,"spread_pips":spread,"slippage_pips":slip,
            "round_trip_cost_pips":2*(spread+slip),"same_bar_stop_first_count":same_bar}


def _pf(m: dict[str, Any]) -> float:
    return 3.0 if m.get("profit_factor") == "inf" else float(m.get("profit_factor",0))


def _gate(m: dict[str, Any], trades: int, pf: float, dd: float) -> list[str]:
    out=[]
    if m["trades"] < trades: out.append(f"trades<{trades}")
    if _pf(m) < pf: out.append(f"profit_factor<{pf}")
    if m["expectancy_R"] <= 0: out.append("expectancy_R<=0")
    if m["total_R"] <= 0: out.append("total_R<=0")
    if m["final_equity"] <= INITIAL_EQUITY: out.append("final_equity<=initial_equity")
    if m["max_dd_pct"] > dd: out.append(f"max_dd_pct>{dd}")
    return out


def _is_reject(by_year: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    return {str(y): r for y in YEARS if (r:=_gate(by_year[str(y)],IS_TRADES,IS_PF,IS_DD))}


def _hash(value: dict[str, Any]) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def _load(data_path: str | Path, manifest_path: str | Path):
    data, mf=Path(data_path),Path(manifest_path)
    if not data.is_file() or not data.stat().st_size: raise ValueError("G16_DATA_MISSING")
    if not mf.is_file(): raise ValueError("G16_MANIFEST_MISSING")
    manifest=json.loads(mf.read_text(encoding="utf-8"))
    dh=hashlib.sha256(data.read_bytes()).hexdigest(); mh=hashlib.sha256(mf.read_bytes()).hexdigest()
    if manifest.get("symbol")!="EURUSD": raise ValueError("G16_SYMBOL_MISMATCH")
    if str(manifest.get("timeframe","")).upper()!="M5": raise ValueError("G16_TIMEFRAME_MISMATCH")
    if manifest.get("quality_status")!="PASS": raise ValueError("G16_QUALITY_NOT_PASS")
    if "HistData" not in str(manifest.get("source","")): raise ValueError("G16_SOURCE_NOT_HISTDATA")
    if manifest.get("data_sha256")!=dh: raise ValueError("G16_DATA_SHA256_MISMATCH")
    if not manifest.get("source_hash"): raise ValueError("G16_SOURCE_HASH_MISSING")
    raw=pd.read_csv(data); need={"timestamp","open","high","low","close","volume"}
    if need-set(raw.columns): raise ValueError(f"G16_REQUIRED_COLUMNS_MISSING:{sorted(need-set(raw.columns))}")
    ts=pd.to_datetime(raw.timestamp,format="mixed",utc=True,errors="raise")
    if ts.isna().any() or ts.duplicated().any() or not ts.is_monotonic_increasing: raise ValueError("G16_TIMESTAMP_SEQUENCE_INVALID")
    if len(raw)!=int(manifest.get("rows",-1)): raise ValueError("G16_ROW_COUNT_MISMATCH")
    if ts.max()>=OOS_START: raise ValueError("G16_OOS_POLICY_VIOLATION_2026_DATA_PRESENT")
    if ts.min()>=pd.Timestamp("2022-01-08",tz="UTC"): raise ValueError("G16_DATA_START_TOO_LATE")
    if not ((ts.dt.minute%5==0)&(ts.dt.second==0)&(ts.dt.microsecond==0)).all(): raise ValueError("G16_M5_ALIGNMENT_FAIL")
    if not set(ALL_YEARS).issubset(set(ts.dt.year.astype(int))): raise ValueError("G16_REQUIRED_YEAR_MISSING")
    raw["timestamp"]=ts
    for c in ("open","high","low","close","volume"):
        raw[c]=pd.to_numeric(raw[c],errors="raise")
        if not np.isfinite(raw[c].to_numpy(float)).all(): raise ValueError(f"G16_NONFINITE:{c}")
    if not ((raw.high>=raw[["open","close"]].max(axis=1))&(raw.low<=raw[["open","close"]].min(axis=1))&(raw.high>=raw.low)).all(): raise ValueError("G16_RAW_OHLC_INVALID")
    if manifest.get("start") and pd.to_datetime(manifest["start"],utc=True)!=ts.min(): raise ValueError("G16_MANIFEST_START_MISMATCH")
    if manifest.get("end") and pd.to_datetime(manifest["end"],utc=True)!=ts.max(): raise ValueError("G16_MANIFEST_END_MISMATCH")
    frame=raw.rename(columns={"timestamp":"Timestamp","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("Timestamp")
    return frame,manifest,dh,mh


def run_discovery(data_path: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    frame,mf,dh,mh=_load(data_path,manifest_path)
    years={y:frame.loc[(frame.index>=pd.Timestamp(f"{y}-01-01",tz="UTC"))&(frame.index<pd.Timestamp(f"{y+1}-01-01",tz="UTC"))] for y in ALL_YEARS}
    if any(part.empty for part in years.values()): raise ValueError("G16_EMPTY_REQUIRED_YEAR")
    ranked=[]; total_trades=0
    for cid,p in enumerate(catalog(),1):
        by={str(y):backtest(years[y],p) for y in YEARS}; total_trades+=sum(m["trades"] for m in by.values())
        rejects=_is_reject(by); pfs=[_pf(by[str(y)]) for y in YEARS]
        score=1.5*min(min(pfs),2)/2+0.75*min(float(np.mean(pfs)),2)/2+np.tanh(sum(m["total_R"] for m in by.values())/150)-2*max(m["max_dd_pct"] for m in by.values())/100
        ranked.append({"candidate_id":cid,"params":p,"is_metrics_by_year":by,"is_gate_pass":not rejects,"is_rejections_by_year":rejects,"is_score":round(float(score),8)})
    if total_trades<=0: raise RuntimeError("G16_NO_IS_TRADES_SIGNAL_INTEGRITY_FAILURE")
    ranked.sort(key=lambda x:(-x["is_score"],x["candidate_id"]))
    passed=[x for x in ranked if x["is_gate_pass"]]; finalists=passed[:MAX_FINALISTS]; evaluated=[]
    for row in finalists:
        p=row["params"]; val=backtest(years[2025],p); vr=_gate(val,VAL_TRADES,VAL_PF,VAL_DD)
        stress={str(y):backtest(years[y],p,STRESS_COST) for y in ALL_YEARS}
        sr={y:r for y,m in stress.items() if (r:=_gate(m,STRESS_TRADES,STRESS_PF,STRESS_DD))}
        severe=backtest(years[2025],p,SEVERE_COST)
        evaluated.append({**row,"validation_2025":val,"validation_pass":not vr,"validation_rejections":vr,
                          "moderate_stress_by_year":stress,"moderate_stress_pass":not sr,"moderate_stress_rejections":sr,
                          "severe_2025_diagnostic":severe})
    qualified=[x for x in evaluated if x["validation_pass"] and x["moderate_stress_pass"]]
    frozen=None
    if qualified:
        x=qualified[0]; frozen={"family":"regime_zscore_reversion","symbol":"EURUSD","timeframe":"M5","candidate_id":x["candidate_id"],"params":x["params"],"risk_pct":RISK_PCT,"data_sha256":dh,"manifest_sha256":mh,"is_years":list(YEARS),"validation_year":2025,"baseline_cost":BASE_COST,"moderate_stress_cost":STRESS_COST,"gate_policy":{"is_trades":IS_TRADES,"is_pf":IS_PF,"is_dd":IS_DD,"validation_trades":VAL_TRADES,"validation_pf":VAL_PF,"validation_dd":VAL_DD,"stress_trades":STRESS_TRADES,"stress_pf":STRESS_PF,"stress_dd":STRESS_DD},"oos_start":"2026-01-01","oos_read_during_discovery":False}
        frozen["config_sha256"]=_hash(frozen)
    decision=("NO_GO_NO_IS_QUALIFIED_CANDIDATES" if not passed else "NO_GO_VALIDATION_OR_COST_STRESS_FAILED" if not qualified else "FROZEN_CANDIDATE_HOLDOUT_PENDING")
    return {"schema_version":SCHEMA,"strategy":"Regime Z-Score Reversion","symbol":"EURUSD","timeframe":"M5","real_data_required":True,"synthetic_fallback":False,
            "source_data":{"source":mf.get("source"),"dataset_id":mf.get("dataset_id"),"rows":len(frame),"start":str(frame.index.min()),"end":str(frame.index.max()),"data_sha256":dh,"manifest_sha256":mh,"quality_status":mf["quality_status"]},
            "protocol":{"catalog_locked":True,"catalog_total":len(ranked),"is_ranks_candidates":True,"is_used_for_ranking":True,"validation_2025_is_pass_fail_only":True,"validation_used_for_ranking":False,"max_validation_finalists":MAX_FINALISTS,"signal":"fresh closed-bar Z crossing; next-open entry","regime":"Wilder ADX(14) <= candidate threshold","exit":"Z returns through zero, ATR stop, or max hold","2026_loaded":False},
            "costs":{"base_round_trip_pips":2*sum(BASE_COST),"moderate_stress_round_trip_pips":2*sum(STRESS_COST),"severe_diagnostic_round_trip_pips":2*sum(SEVERE_COST),"commission_included":False,"swap_included":false},
            "gates":{"is_each_year":{"trades":IS_TRADES,"pf":IS_PF,"max_dd_pct":IS_DD,"all_years_required":True},"validation_2025":{"trades":VAL_TRADES,"pf":VAL_PF,"max_dd_pct":VAL_DD},"moderate_stress_2022_2025":{"trades":STRESS_TRADES,"pf":STRESS_PF,"max_dd_pct":STRESS_DD}},
            "catalog":{"candidate_total":éÈÜÝÈ[[[\ÝÎ\ÝÖÈ\[\ÈNÈ[XXÚÝ\Ý
YX\ÖÌWK
NÈWÙØ]J[SÕQTËSÔSÑ
BÝ\ÜÏ^ÜÝJNXÚÝ\Ý
YX\ÖÞWKÕTÔ×ÐÓÔÕ
HÜH[SÖQPTßBÜ^ÞNÜKH[Ý\ÜË][\Ê
HY
WÙØ]JKÕTÔ×ÕQTËÕTÔ×ÔÕTÔ×Ñ
J_BÙ]\OXXÚÝ\Ý
YX\ÖÌWKÑUTWÐÓÔÕ
B][X]Y\[
ÊÝË[Y][ÛÌH[[Y][ÛÜ\ÜÈÝ[Y][ÛÜZXÝ[ÛÈ[Ù\]WÜÝ\Ü×ØWÞYX\Ý\ÜË[Ù\]WÜÝ\Ü×Ü\ÜÈÝÜ[Ù\]WÜÝ\Ü×ÜZXÝ[ÛÈÜÙ]\WÌWÙXYÛÜÝXÈÙ]\_JB]X[YYYVÞÜ[][X]YYÈ[Y][ÛÜ\ÜÈH[È[Ù\]WÜÝ\Ü×Ü\ÜÈWBÞ[SÛBY]X[YYY\]X[YYYÌNÈÞ[^È[Z[HYÚ[YWÞØÛÜWÜ]\Ú[ÛÞ[XÛUTTÑ[YY[YHMHØ[Y]WÚYÈØ[Y]WÚYK\[\ÈÈ\[\ÈK\Ú×ÜÝTÒ×ÔÕ]WÜÚLMX[Y\ÝÜÚLMZ\×ÞYX\È\Ý
QPTÊK[Y][ÛÞYX\K\Ù[[WØÛÜÝTÑWÐÓÔÕ[Ù\]WÜÝ\Ü×ØÛÜÝÕTÔ×ÐÓÔÕØ]WÜÛXÞHÈ\×ÝY\ÈT×ÕQTË\×ÜT×Ô\×ÙT×Ñ[Y][ÛÝY\ÈSÕQTË[Y][ÛÜSÔ[Y][ÛÙSÑÝ\Ü×ÝY\ÈÕTÔ×ÕQTËÝ\Ü×ÜÕTÔ×ÔÝ\Ü×ÙÕTÔ×ÑKÛÜ×ÜÝ\LKLHÛÜ×ÜXYÙ\[×Ù\ØÛÝ\H[Ù_BÞ[ÈÛÛY×ÜÚLMOWÚ\Ú
Þ[BXÚ\Ú[ÛJ×ÑÓ×Ó×ÒT×ÔUPSQQQÐÐSQUTÈYÝ\ÜÙY[ÙH×ÑÓ×ÕSQUSÓÓÔÐÓÔÕÔÕTÔ×ÑRSQYÝ]X[YYY[ÙHÖSÐÐSQUWÒÓÕUÔSSÈB]\ÈØÚ[XWÝ\Ú[ÛÐÒSPKÝ]YÞHYÚ[YHTØÛÜH]\Ú[ÛÞ[XÛUTTÑ[YY[YHMHX[Ù]WÜ\]Z\YYKÞ[]X×Ù[XÚÈ[ÙKÛÝ\ÙWÙ]HÈÛÝ\ÙHYÙ]
ÛÝ\ÙHK]\Ù]ÚYYÙ]
]\Ù]ÚYKÝÜÈ[[YJKÝ\Ý[YK[^Z[
JK[Ý[YK[^X^

JK]WÜÚLMX[Y\ÝÜÚLMZ]X[]WÜÝ]\ÈYÈ]X[]WÜÝ]\È_KÝØÛÛÈØ][Ù×ÛØÚÙYYKØ][Ù×ÝÝ[[[ÙY
K\×Ü[Ü×ØØ[Y]\ÈYK\×Ý\ÙYÙÜÜ[Ú[ÈYK[Y][ÛÌWÚ\×Ü\Ü×ÙZ[ÛÛHYK[Y][ÛÝ\ÙYÙÜÜ[Ú[È[ÙKX^Ý[Y][ÛÙ[[\ÝÈPVÑSSTÕËÚYÛ[\ÚÛÜÙYX\ÜÜÜÚ[ÎÈ^[Ü[[HYÚ[YHÚ[\Q
M
HHØ[Y]H\ÚÛ^]]\ÈÝYÚ\ËUÝÜÜX^ÛÛØYY[Ù_KÛÜÝÈÈ\ÙWÜÝ[Ý\Ü\ÈÝ[JTÑWÐÓÔÕ
K[Ù\]WÜÝ\Ü×ÜÝ[Ý\Ü\ÈÝ[JÕTÔ×ÐÓÔÕ
KÙ]\WÙXYÛÜÝX×ÜÝ[Ý\Ü\È7VÒ6WfW&Uô4õ5BÂ'Fr#¢&6öÖÖ76öåöæõ÷7vöæò'ÒÀ¢&vFW2#§²&5öV6÷V"#§²'G&FW2#¤5õE$DU2Â'b#¤5õbÂ&ÖöFE÷7B#¤5ôDBÂ&ÆÅ÷V'5÷&WV&VB#¥G'VWÒÂ'fÆFFöåó##R#§²'G&FW2#¥dÅõE$DU2Â'b#¥dÅõbÂ&ÖöFE÷7B#¥dÅôDGÒÂ&ÖöFW&FU÷7G&W75ó##%ó##R#§²'G&FW2#¥5E$U55õE$DU2Â'b#¥5E$U55õbÂ&ÖöFE÷7B#¥5E$U55ôDG×ÒÀ¢&6FÆör#§²&6æFFFU÷F÷FÂ#¦ÆVâ&æ¶VBÂ&5÷VÆfVEö6÷VçB#¦ÆVâ76VBÂ'fÆFFöåöfæÆ7G5öWfÇVFVB#¦ÆVâfæÆ7G2Â&gVÆÇ÷VÆfVEö6÷VçB#¦ÆVâVÆfVBÂ'F÷FÅö5÷G&FW5ö7&÷75ö6FÆör#§F÷FÅ÷G&FW7ÒÀ¢&FV66öâ#¦FV66öâÂ'F÷ó#ö5öFvæ÷7F72#§&æ¶VE³£#ÒÂ&WfÇVFVEöfæÆ7G2#¦WfÇVFVBÂ&g&÷¦Våö6æFFFR#¦g&÷¦VâÂ'6VÆV7Föåög&÷¦Vâ#¦g&÷¦Vâ2æ÷BæöæRÀ¢'&öÖ÷FöåöFV66öâ#¢$ôÄDõUEôäõEõ%Tåôäõõ$ôÔõDôâ"Â&FVÖõöWF÷&¦VB#¦fÇ6RÂ&ÆfUöWF÷&¦VB#¦fÇ6RÂ&÷&FW'5÷7V&ÖGFVB#¦fÇ6RÀ¢&ö÷5÷öÆ7#§²&ÆöFVB#¦fÇ6RÂ'7FGW2#¢$TÄEôõUB"Â'7F'B#¢###bÓÓ"Â&ö÷5÷'VææW%öçfö¶VB#¦fÇ6RÂ&ö÷5ö÷FÖ¦FöåöÆÆ÷vVB#¦fÇ6RÂ&÷FÖ¦FöåöÆÆ÷vVB#¦fÇ6W×Ð  ¦FVbÖâÓâçC ¢Ö&w'2ä&wVÖVçE'6W"FW67&FöãÒ$fÂÖ6Æ÷6VBsb&VÂÖFFUU%U4BÓRF66÷fW'"¢æFEö&wVÖVçB"ÒÖFF"Ç&WV&VCÕG'VR²æFEö&wVÖVçB"ÒÖÖæfW7B"Ç&WV&VCÕG'VR²æFEö&wVÖVçB"ÒÖ÷WGWB"Ç&WV&VCÕG'VR¢Öç'6Uö&w2²&W÷'C×'VåöF66÷fW'æFFÆæÖæfW7B²÷WCÕFæ÷WGWB²÷WBç&VçBæÖ¶F"&VçG3ÕG'VRÆW7Eöö³ÕG'VR¢÷WBçw&FU÷FWB§6öâæGV×2&W÷'BÆæFVçCÓ"Ç6÷'Eö¶W3ÕG'VRÆVæ6öFæsÒ'WFbÓ"¢&çB§6öâæGV×2²&6FÆör#§&W÷'E²&6FÆör%ÒÂ&FV66öâ#§ü\ÜÈXÚ\Ú[ÛKÛÜ×ÛØYY\Üû"oos_policy"]["loaded"]},indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
