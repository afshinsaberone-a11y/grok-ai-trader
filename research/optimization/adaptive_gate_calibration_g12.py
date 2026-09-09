from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.regime_aware_event_discovery_g6 import prepare, signal
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost

CANDIDATE={"name":"atrpct_050","fast_ema":16,"slow_ema":50,"atr_pct":0.50,"atr_mult":1.0,"rr":2.0}
YEARS=[2022,2023,2024,2025]; CALIBRATION_YEARS=[2022,2023,2024]; MAX_HOLD=24
GATES={"min_profitable_years":3,"min_pf_each_year":1.05,"min_expectancy":0.0,"min_trades_each_year":100,"max_dd_pct":35.0}
VARIANTS=[
 {"name":"strict_50_50_slope","adx_q":0.50,"trend_persist":0.50,"require_slope":True},
 {"name":"adx40_50_slope","adx_q":0.40,"trend_persist":0.50,"require_slope":True},
 {"name":"adx30_50_slope","adx_q":0.30,"trend_persist":0.50,"require_slope":True},
 {"name":"adx40_375_slope","adx_q":0.40,"trend_persist":0.375,"require_slope":True},
 {"name":"adx40_no_persist","adx_q":0.40,"trend_persist":None,"require_slope":True},
 {"name":"adx40_persist50_no_slope","adx_q":0.40,"trend_persist":0.50,"require_slope":False},
]

def features(d):
 d=d.copy(); tr=pd.concat([(d.High-d.Low),(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1)
 d['ATR14']=tr.rolling(14).mean(); plus=d.High.diff().clip(lower=0.0); minus=(-d.Low.diff()).clip(lower=0.0)
 pdi=100*plus.rolling(14).mean()/d.ATR14.replace(0,np.nan); mdi=100*minus.rolling(14).mean()/d.ATR14.replace(0,np.nan)
 d['DX14']=(100*(pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)).fillna(0); d['ADX14']=d.DX14.rolling(14).mean()
 d['ADX_Q']=d.ADX14.rolling(96,min_periods=48).rank(pct=True); d['EMA_SLOPE_ATR']=(d.EMA16-d.EMA16.shift(4))/d.ATR14.replace(0,np.nan)
 d['TREND_PERSIST']=(d.EMA16>d.EMA50).astype(float).rolling(8).mean(); return d

def run_candidate(d):
 p={"family":"regime_momentum","fast":16,"slow":50,"atr_pct":0.50,"atr_mult":1.0,"rr":2.0}; s=pd.Series([signal(d,i,p) for i in range(len(d))],index=d.index)
 trades=[]; pos=None
 for i in range(1,len(d)-1):
  if pos is not None:
   age=i-pos['entry_i']; hi=float(d.High.iloc[i]); lo=float(d.Low.iloc[i]); slhit=lo<=pos['sl'] if pos['side']==1 else hi>=pos['sl']; tphit=hi>=pos['tp'] if pos['side']==1 else lo<=pos['tp']
   if slhit or tphit or age>=MAX_HOLD:
    raw=pos['sl'] if slhit else pos['tp'] if tphit else float(d.Close.iloc[i]); ex=apply_exit_cost(raw,pos['side'],ExecutionConfig()); r=(ex-pos['entry'])/(pos['entry']-pos['sl'])*pos['side']
    trades.append({**pos,'exit_i':i,'r':r,'exit_reason':'SL' if slhit else 'TP' if tphit else 'EXPIRY'}); pos=None
  if pos is None and bool(s.iloc[i-1]):
   side=int(s.iloc[i-1]); entry=apply_entry_cost(float(d.Open.iloc[i]),side,ExecutionConfig()); atr=float(d.ATR14.iloc[i-1])
   if not np.isfinite(atr) or atr<=0: continue
   risk=atr; sl=entry-risk*side; tp=entry+risk*2.0*side
   pos={'entry_i':i,'side':side,'entry':entry,'sl':sl,'tp':tp,'adx_q':d.ADX_Q.iloc[i-1],'trend_persist':d.TREND_PERSIST.iloc[i-1],'slope':d.EMA_SLOPE_ATR.iloc[i-1]}
 if pos is not None:
  ex=apply_exit_cost(float(d.Close.iloc[-1]),pos['side'],ExecutionConfig()); r=(ex-pos['entry'])/(pos['entry']-pos['sl'])*pos['side']; trades.append({**pos,'exit_i':len(d)-1,'r':r,'exit_reason':'END'})
 return pd.DataFrame(trades)

def metrics(t):
 if t.empty:return {"trades":0,"win_rate":0.0,"total_R":0.0,"expectancy_R":0.0,"profit_factor":0.0,"max_drawdown_pct":0.0}
 r=t.r.to_numpy(float); wins=r[r>0].sum(); losses=-r[r<0].sum(); eq=peak=10000.; dd=0.
 for x in r: eq*=1+0.005*x; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
 return {"trades":int(len(r)),"win_rate":float((r>0).mean()*100),"total_R":float(r.sum()),"expectancy_R":float(r.mean()),"profit_factor":float(wins/losses) if losses>0 else (3.0 if wins>0 else 0.0),"max_drawdown_pct":float(dd*100)}

def apply_gate(t,v):
 if t.empty:return t.copy()
 aq=t.adx_q.fillna(0.0); tp=t.trend_persist.fillna(0.0); sl=t.slope.fillna(0.0); keep=aq>=v['adx_q']
 if v['trend_persist'] is not None: keep &= tp>=v['trend_persist']
 if v['require_slope']: keep &= (((t.side==1)&(sl>0))|((t.side==-1)&(sl<0)))
 return t[keep].copy()

def gate(m): return m['trades']>=100 and m['profit_factor']>=1.05 and m['expectancy_R']>0 and m['max_drawdown_pct']<=35

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
 d=pd.read_csv(a.data); d.columns=[str(c).strip() for c in d.columns]
 if 'timestamp' not in d.columns and 'Timestamp' in d.columns:d=d.rename(columns={'Timestamp':'timestamp'})
 req={'timestamp','open','high','low','close'}; miss=req-set(d.columns)
 if miss: raise ValueError(f'REAL_DATA_REQUIRED: missing columns {sorted(miss)}')
 d['timestamp']=pd.to_datetime(d['timestamp'],utc=True); d=d.sort_values('timestamp').reset_index(drop=True)
 d=d.rename(columns={'timestamp':'Timestamp','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}); d=d[d.Timestamp.dt.year.isin(YEARS)].copy(); d=features(prepare(d))
 years={y:d[d.index.year==y].reset_index(drop=True) for y in YEARS}; raw={y:run_candidate(years[y]) for y in YEARS}; results=[]
 for v in VARIANTS:
  rows=[]
  for y in YEARS: rows.append({'year':y,'metrics':metrics(apply_gate(raw[y],v))})
  cal=[x for x in rows if x['year'] in CALIBRATION_YEARS]; score=(sum(gate(x['metrics']) for x in cal),sum(x['metrics']['expectancy_R']>0 for x in cal),sum(x['metrics']['trades'] for x in cal),sum(x['metrics']['total_R'] for x in cal))
  results.append({'variant':v,'years':rows,'calibration_score':score,'calibration_qualified_years':score[0],'calibration_positive_years':score[1]})
 ranked=sorted(results,key=lambda x:x['calibration_score'],reverse=True)
 payload={'schema_version':'forexai.g12.adaptive_gate_calibration.v1','research_scope':{'symbol':'EURUSD','timeframe':'M15','years':YEARS,'calibration_years':CALIBRATION_YEARS,'validation_year':2025},'candidate':CANDIDATE,'execution_model':{'entry':'next_bar_open','round_trip_cost_pips':1.4,'same_bar_resolution':'SL first (conservative)','max_hold_bars':MAX_HOLD,'overlap':'one position at a time'},'policy':{'real_data_required':True,'synthetic_data':False,'oos_2026_used':False,'parameter_selection_used_2025':False,'gates_unchanged':True,'champion':None},'official_gates':GATES,'selection_policy':'Predeclared variants; ranking uses 2022-2024 only. 2025 is reported after calibration and cannot select a variant.','variants':ranked,'recommended_for_canonical_rerun':ranked[0]['variant'] if ranked else None,'canonical_rerun_required':True}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'candidate':'atrpct_050','variant_count':len(VARIANTS),'recommended_for_canonical_rerun':payload['recommended_for_canonical_rerun'],'champion':None}))
if __name__=='__main__':main()
