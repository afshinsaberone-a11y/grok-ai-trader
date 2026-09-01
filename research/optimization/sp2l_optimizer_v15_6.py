"""Fast deterministic SP2L v15.6 optimizer. Real data only; train ends 2025-01-01."""
from __future__ import annotations
import argparse,json
from dataclasses import asdict
from itertools import product
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.sp2l_v15_3 import Params,signals

def bt(df,p,spread=.5,slippage=.2,rr=1.5):
 s=signals(df,p).to_numpy(); H=df.High.to_numpy(); L=df.Low.to_numpy(); C=df.Close.to_numpy(); idx=np.flatnonzero(s); pip=.0001; trades=[]
 for i in idx:
  if i+1>=len(df): continue
  e=C[i+1]; risk=max(H[i]-L[i],pip); sl=e-risk if s[i]>0 else e+risk; tp=e+rr*risk if s[i]>0 else e-rr*risk; hit=None
  for j in range(i+1,min(len(df),i+1+p.expiry_bars)):
   if s[i]>0:
    if L[j]<=sl: hit=-risk; break
    if H[j]>=tp: hit=rr*risk; break
   else:
    if H[j]>=sl: hit=-risk; break
    if L[j]<=tp: hit=rr*risk; break
  if hit is not None: trades.append(hit/pip-2*(spread+slippage))
 if not trades:return {'trades':0,'pf':0.,'win_rate':0.,'net_pips':0.,'max_dd_pips':0.,'expectancy_pips':0.}
 a=np.asarray(trades); w=a[a>0]; l=-a[a<0]; eq=np.cumsum(a); dd=np.maximum.accumulate(eq)-eq
 return {'trades':int(a.size),'pf':float(w.sum()/l.sum()) if l.sum() else 999.,'win_rate':float((a>0).mean()*100),'net_pips':float(a.sum()),'max_dd_pips':float(dd.max()),'expectancy_pips':float(a.mean())}

def norm(df):
 cols={c.lower():c for c in df.columns}; d=df.rename(columns={cols[k]:k.title() for k in ('open','high','low','close') if k in cols}); ts=next((c for c in d.columns if c.lower() in ('timestamp','time','datetime')),None)
 if ts is None: raise ValueError('TIMESTAMP_REQUIRED')
 d[ts]=pd.to_datetime(d[ts],utc=True); return d.set_index(ts).sort_index()

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/sp2l-v15-6.json'); ap.add_argument('--spread-pips',type=float,default=.5); ap.add_argument('--slippage-pips',type=float,default=.2); a=ap.parse_args()
 d=norm(pd.read_csv(a.data)); d=d[d.index<pd.Timestamp('2025-01-01',tz='UTC')]
 A={'atr_period':[10,14,20],'spike_atr':[1.2,1.5,1.8,2.1],'spike_body_ratio':[.55,.65,.75],'pullback_min_frac':[.2,.4],'pullback_max_frac':[.6,.9],'max_pullback_bars':[2,5],'confirmation_frac':[.4,.6],'expiry_bars':[6,12]}; keys=list(A); rows=[]
 for vals in product(*[A[k] for k in keys]):
  p=Params(**dict(zip(keys,vals))); rows.append({'params':asdict(p),'result':bt(d,p,a.spread_pips,a.slippage_pips)})
 rows.sort(key=lambda z:(z['result']['pf'],z['result']['expectancy_pips'],-z['result']['max_dd_pips']),reverse=True); seeds=rows[:20]; fine=[]
 for z in seeds:
  q=z['params']
  for atr,sp,br,pmn,pmx,mpb,cf,ex in product([q['atr_period']],[q['spike_atr']],[q['spike_body_ratio']],[max(.1,q['pullback_min_frac']-.1),q['pullback_min_frac'],min(.5,q['pullback_min_frac']+.1)],[max(.5,q['pullback_max_frac']-.1),q['pullback_max_frac'],min(.95,q['pullback_max_frac']+.1)],[q['max_pullback_bars']],[max(.3,q['confirmation_frac']-.1),q['confirmation_frac'],min(.7,q['confirmation_frac']+.1)],[max(4,q['expiry_bars']-2),q['expiry_bars'],q['expiry_bars']+2]):
   if pmn>=pmx: continue
   p=Params(atr,sp,br,pmn,pmx,mpb,cf,ex); fine.append({'params':asdict(p),'result':bt(d,p,a.spread_pips,a.slippage_pips)})
 fine.sort(key=lambda z:(z['result']['pf'],z['result']['expectancy_pips'],-z['result']['max_dd_pips']),reverse=True)
 report={'schema_version':'forexai.sp2l_optimizer.v15.6','train_end_exclusive':'2025-01-01','holdout_2025_2026_excluded':True,'stage_a_candidates':len(rows),'stage_b_candidates':len(fine),'top10':fine[:10]}; Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
