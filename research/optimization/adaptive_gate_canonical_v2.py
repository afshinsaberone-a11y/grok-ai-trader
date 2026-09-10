from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.regime_aware_event_discovery_g6 import prepare, signal
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost, validate_ohlc

YEARS=(2022,2023,2024,2025); CAL=(2022,2023,2024); MAX_HOLD=30; WARMUP=500
VARIANT={"name":"adx30_50_slope","adx_q":0.30,"trend_persist":0.50,"require_slope":True}
CANDIDATE={"family":"regime_momentum","fast":16,"slow":50,"atr_pct":0.50,"atr_mult":1.0,"rr":2.0}
GATES={"min_profitable_years":3,"min_pf_each_year":1.05,"min_expectancy":0.0,"min_trades_each_year":100,"max_dd_pct":35.0}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def features(d):
    d=d.copy(); tr=pd.concat([(d.High-d.Low),(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1)
    d['ATR14']=tr.rolling(14,min_periods=14).mean(); plus=d.High.diff().clip(lower=0.0); minus=(-d.Low.diff()).clip(lower=0.0)
    pdi=100*plus.rolling(14).mean()/d.ATR14.replace(0,np.nan); mdi=100*minus.rolling(14).mean()/d.ATR14.replace(0,np.nan)
    d['DX14']=(100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)).fillna(0); d['ADX14']=d.DX14.rolling(14).mean()
    d['ADX_Q']=d.ADX14.rolling(96,min_periods=48).rank(pct=True); d['EMA_SLOPE_ATR']=(d.EMA16-d.EMA16.shift(4))/d.ATR14.replace(0,np.nan)
    d['TREND_PERSIST']=(d.EMA16>d.EMA50).astype(float).rolling(8).mean(); return d

def gate_row(side,aq,tp,sl):
    if not(np.isfinite(aq) and aq>=VARIANT['adx_q'] and np.isfinite(tp) and tp>=VARIANT['trend_persist']): return False
    return bool(np.isfinite(sl) and ((side==1 and sl>0) or (side==-1 and sl<0)))

def metrics(rs):
    if not rs:return {'trades':0,'win_rate_pct':0.0,'total_R':0.0,'expectancy_R':0.0,'profit_factor':0.0,'max_dd_pct':0.0}
    a=np.asarray(rs,float); gp=float(a[a>0].sum()); gl=float(-a[a<0].sum()); pf=gp/gl if gl>0 else (3.0 if gp>0 else 0.0); eq=peak=10000.; dd=0.
    for r in a: eq*=1+0.005*float(r); peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
    return {'trades':int(len(a)),'win_rate_pct':float((a>0).mean()*100),'total_R':float(a.sum()),'expectancy_R':float(a.mean()),'profit_factor':float(pf),'max_dd_pct':float(dd*100)}

def gate(m): return m['trades']>=100 and m['profit_factor']>=1.05 and m['expectancy_R']>0 and m['max_dd_pct']<=35

def run_year(part,y0,y1):
    d=features(prepare(part.reset_index())); s=[signal(d,i,CANDIDATE) for i in range(len(d))]; cfg=ExecutionConfig(expiry_bars=MAX_HOLD)
    pos=0; entry=stop=target=0.; entry_i=-1; rs=[]; entries=exits=0
    for i in range(1,len(d)-1):
        if d.index[i] < y0: continue
        if pos==0:
            side=int(s[i-1])
            if side==0 or not gate_row(side,float(d.ADX_Q.iloc[i-1]),float(d.TREND_PERSIST.iloc[i-1]),float(d.EMA_SLOPE_ATR.iloc[i-1])): continue
            atr=float(d.ATR14.iloc[i-1])
            if not np.isfinite(atr) or atr<=0: continue
            pos=side; entry_i=i; entry=apply_entry_cost(float(d.Open.iloc[i]),pos,cfg); stop=entry-pos*atr; target=entry+pos*2*atr; entries+=1; continue
        age=i-entry_i+1; hit_sl=(float(d.Low.iloc[i])<=stop) if pos==1 else (float(d.High.iloc[i])>=stop); hit_tp=(float(d.High.iloc[i])>=target) if pos==1 else (float(d.Low.iloc[i])<=target)
        if hit_sl or hit_tp:
            raw=stop if hit_sl else target; reason='SL' if hit_sl else 'TP'
            if hit_sl and hit_tp: reason='SL_FIRST'
            ex=apply_exit_cost(raw,pos,cfg)
        elif int(s[i])==-pos and i+1<len(d): reason='OPPOSITE_NEXT_OPEN'; ex=apply_exit_cost(float(d.Open.iloc[i+1]),pos,cfg)
        elif age>=MAX_HOLD and i+1<len(d): reason='EXPIRY_NEXT_OPEN'; ex=apply_exit_cost(float(d.Open.iloc[i+1]),pos,cfg)
        else: continue
        risk=float(d.ATR14.iloc[entry_i-1])
        if not np.isfinite(risk) or risk<=0: pos=0; continue
        rs.append(float(pos*(ex-entry)/risk)); exits+=1; pos=0
    if pos!=0:
        risk=float(d.ATR14.iloc[max(entry_i-1,0)])
        if np.isfinite(risk) and risk>0:
            ex=apply_exit_cost(float(d.Close.iloc[-1]),pos,cfg); rs.append(float(pos*(ex-entry)/risk)); exits+=1
        pos=0
    return metrics(rs),{'entries':entries,'exits':exits,'entries_equal_exits':entries==exits}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--g12-artifact',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    g12=json.loads(Path(a.g12_artifact).read_text()); assert g12['schema_version']=='forexai.g12.adaptive_gate_calibration.v1'; assert g12['recommended_for_canonical_rerun']==VARIANT; assert g12['policy']['oos_2026_used'] is False; assert g12['policy']['parameter_selection_used_2025'] is False
    raw=pd.read_csv(a.data); raw.columns=[str(c).strip() for c in raw.columns]; raw=raw.rename(columns={'Timestamp':'timestamp','Open':'open','High':'high','Low':'low','Close':'close'}); req={'timestamp','open','high','low','close'}; miss=req-set(raw.columns); assert not miss, f'missing {miss}'
    raw['timestamp']=pd.to_datetime(raw['timestamp'],utc=True); raw=raw.sort_values('timestamp').drop_duplicates('timestamp'); raw=raw[raw.timestamp.dt.year.isin(YEARS)]; raw=raw.rename(columns={'timestamp':'Timestamp','open':'Open','high':'High','low':'Low','close':'Close'}).set_index('Timestamp'); validate_ohlc(raw); assert raw.index.max().year<2026
    yearly={}; inv={}
    for y in YEARS:
        y0=pd.Timestamp(f'{y}-01-01',tz='UTC'); y1=pd.Timestamp(f'{y+1}-01-01',tz='UTC'); prior=raw.index[raw.index<y0]; warm=prior[-WARMUP] if len(prior)>=WARMUP else raw.index.min(); part=raw.loc[(raw.index>=warm)&(raw.index<y1)].copy(); yearly[str(y)],inv[str(y)]=run_year(part,y0,y1)
    cal=[yearly[str(y)] for y in CAL]; cal_gate=[gate(m) for m in cal]; pre=all(cal_gate) and sum(cal_gate)>=3; val=gate(yearly['2025']); payload={'schema_version':'forexai.g12.adaptive_gate_canonical.v2','source':{'g12_artifact':a.g12_artifact,'g12_artifact_sha256':sha(a.g12_artifact)},'research_scope':{'symbol':'EURUSD','timeframe':'M15','calibration_years':list(CAL),'validation_year':2025},'selected_variant':VARIANT,'base_candidate':CANDIDATE,'execution_model':{'entry':'next_bar_open','cost_pips_per_side':0.7,'round_trip_cost_pips':1.4,'same_bar_resolution':'SL first (conservative)','expiry_bars':MAX_HOLD,'overlap':'one position at a time'},'policy':{'real_data_required':True,'synthetic_data':False,'oos_2026_used':False,'parameter_selection_used_2025':False,'gates_unchanged':True,'champion':None},'official_gates':GATES,'yearly':yearly,'execution_invariants':inv,'validation':{'pre_oos_qualified':pre,'calibration_gate_results':dict(zip(map(str,CAL),cal_gate)),'validation_pass':val},'canonical_status':'GO_TO_ROBUSTNESS' if pre and val else 'HOLD'}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'canonical_status':payload['canonical_status'],'pre_oos_qualified':pre,'validation_pass':val,'champion':None}))
if __name__=='__main__': main()
