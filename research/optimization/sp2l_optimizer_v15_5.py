"""Deterministic SP2L v15.5 parameter search. Research proxy only."""
from __future__ import annotations
import argparse,json
from dataclasses import asdict
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.sp2l_v15_3 import Params,signals

def backtest(df,p,spread=.5,slippage=.2,rr=1.5):
 s=signals(df,p); trades=[]; pip=.0001
 for i,x in enumerate(s):
  if x==0 or i+1>=len(df): continue
  e=float(df.Close.iloc[i+1]); risk=max(float(df.High.iloc[i]-df.Low.iloc[i]),pip); sl=e-risk if x>0 else e+risk; tp=e+rr*risk if x>0 else e-rr*risk
  hit=None
  for j in range(i+1,min(len(df),i+1+p.expiry_bars)):
   h,l=float(df.High.iloc[j]),float(df.Low.iloc[j])
   if x>0:
    if l<=sl: hit=-risk; break
    if h>=tp: hit=rr*risk; break
   else:
    if h>=sl: hit=-risk; break
    if l<=tp: hit=rr*risk; break
  if hit is not None: trades.append(hit/pip-2*(spread+slippage))
 if not trades: return {'trades':0,'pf':0.,'win_rate':0.,'net_pips':0.,'max_dd_pips':0.,'expectancy_pips':0.}
 a=np.array(trades); w=a[a>0]; l=-a[a<0]; eq=np.cumsum(a); dd=np.maximum.accumulate(eq)-eq
 return {'trades':len(a),'pf':float(w.sum()/l.sum()) if l.sum()>0 else float('inf'),'win_rate':float((a>0).mean()*100),'net_pips':float(a.sum()),'max_dd_pips':float(dd.max()),'expectancy_pips':float(a.mean())}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/sp2l-v15-5.json'); a=ap.parse_args()
 d=pd.read_csv(a.data); cols={c.lower():c for c in d.columns}
 d=d.rename(columns={cols[k]:k.title() for k in ('open','high','low','close') if k in cols}); ts=next((c for c in d.columns if c.lower() in ('timestamp','time','datetime')),None)
 if ts is None: raise ValueError('TIMESTAMP_REQUIRED')
 d[ts]=pd.to_datetime(d[ts],utc=True); d=d.set_index(ts).sort_index(); d=d[d.index<pd.Timestamp('2025-01-01',tz='UTC')]
 grid={'atr_period':[10,14,20],'spike_atr':[1.2,1.5,1.8,2.1],'spike_body_ratio':[.55,.65,.75],'pullback_min_frac':[.2,.3,.4],'pullback_max_frac':[.6,.75,.9],'max_pullback_bars':[2,3,5],'confirmation_frac':[.4,.5,.6],'expiry_bars':[6,8,12]}
 keys=list(grid); rows=[]
 for vals in product(*[grid[k] for k in keys]):
  p=Params(**dict(zip(keys,vals))); rows.append({'params':asdict(p),'result':backtest(d,p)})
 rows.sort(key=lambda z:(z['result']['pf'],z['result']['expectancy_pips'],-z['result']['max_dd_pips']),reverse=True)
 report={'schema_version':'forexai.sp2l_optimizer.v15.5','data_end_exclusive':'2025-01-01','holdout_2025_2026_excluded':True,'candidate_count':len(rows),'top10':rows[:10]}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
