"""SP2L v15.7-compatible bounded optimizer.
Uses the corrected explicit two-leg state machine. Real data only; holdout excluded.
"""
from __future__ import annotations
import argparse,json
from dataclasses import asdict
from itertools import product
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.sp2l_v15_7 import Params,signals

def bt(sig,high,low,close,expiry,spread,slippage,rr=1.5):
 idx=np.flatnonzero(sig); pip=.0001; trades=[]; n=len(close)
 for i in idx:
  if i+1>=n: continue
  e=close[i+1]; risk=max(high[i]-low[i],pip); long=sig[i]>0; sl=e-risk if long else e+risk; tp=e+rr*risk if long else e-rr*risk; hit=None
  for j in range(i+1,min(n,i+1+expiry)):
   if long:
    if low[j]<=sl: hit=-risk; break
    if high[j]>=tp: hit=rr*risk; break
   else:
    if high[j]>=sl: hit=-risk; break
    if low[j]<=tp: hit=rr*risk; break
  if hit is not None: trades.append(hit/pip-2*(spread+slippage))
 if not trades:return {'trades':0,'pf':0.,'win_rate':0.,'net_pips':0.,'max_dd_pips':0.,'expectancy_pips':0.}
 a=np.asarray(trades); w=a[a>0]; l=-a[a<0]; eq=np.cumsum(a); dd=np.maximum.accumulate(eq)-eq
 return {'trades':int(a.size),'pf':float(w.sum()/l.sum()) if l.sum() else 999.,'win_rate':float((a>0).mean()*100),'net_pips':float(a.sum()),'max_dd_pips':float(dd.max()),'expectancy_pips':float(a.mean())}

def norm(df):
 cols={c.lower():c for c in df.columns}; d=df.rename(columns={cols[k]:k.title() for k in ('open','high','low','close') if k in cols}); ts=next((c for c in d.columns if c.lower() in ('timestamp','time','datetime')),None)
 if ts is None: raise ValueError('TIMESTAMP_REQUIRED')
 d[ts]=pd.to_datetime(d[ts],utc=True); return d.set_index(ts).sort_index()

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/sp2l-v15-6.json'); ap.add_argument('--spread-pips',type=float,default=.5); ap.add_argument('--slippage-pips',type=float,default=.2); ap.add_argument('--stage-a-limit',type=int,default=576); ap.add_argument('--seeds',type=int,default=12); ap.add_argument('--fine-limit',type=int,default=972); a=ap.parse_args()
 d=norm(pd.read_csv(a.data)); d=d[d.index<pd.Timestamp('2025-01-01',tz='UTC')]
 if d.empty: raise RuntimeError('REAL_DATA_REQUIRED')
 H=d.High.to_numpy(float); L=d.Low.to_numpy(float); C=d.Close.to_numpy(float)
 A={'atr_period':[10,14,20],'spike_atr':[1.2,1.5,1.8],'spike_body_ratio':[.55,.65],'pullback_min_frac':[.2,.4],'pullback_max_frac':[.6,.9],'max_pullback_bars':[2,5],'confirmation_frac':[.4,.6],'expiry_bars':[6,12]}; keys=list(A); vals=list(product(*[A[k] for k in keys])); vals=vals[::max(1,int(np.ceil(len(vals)/a.stage_a_limit)))][:a.stage_a_limit]
 rows=[]
 for v in vals:
  p=Params(*v); rows.append({'params':asdict(p),'result':bt(signals(d,p).to_numpy(),H,L,C,p.expiry_bars,a.spread_pips,a.slippage_pips)})
 key=lambda z:(z['result']['pf'],z['result']['expectancy_pips'],-z['result']['max_dd_pips'],z['result']['trades']); rows.sort(key=key,reverse=True); fine=[]; seen=set()
 for z in rows[:a.seeds]:
  q=z['params']
  grid=product([q['atr_period']],[q['spike_atr']],[q['spike_body_ratio']],[max(.1,q['pullback_min_frac']-.1),q['pullback_min_frac'],min(.5,q['pullback_min_frac']+.1)],[max(.5,q['pullback_max_frac']-.1),q['pullback_max_frac'],min(.95,q['pullback_max_frac']+.1)],[q['max_pullback_bars']],[max(.3,q['confirmation_frac']-.1),q['confirmation_frac'],min(.7,q['confirmation_frac']+.1)],[max(4,q['expiry_bars']-2),q['expiry_bars'],q['expiry_bars']+2])
  for v in grid:
   if v[3]>=v[4] or v in seen: continue
   seen.add(v); p=Params(*v); fine.append({'params':asdict(p),'result':bt(signals(d,p).to_numpy(),H,L,C,p.expiry_bars,a.spread_pips,a.slippage_pips)})
   if len(fine)>=a.fine_limit: break
  if len(fine)>=a.fine_limit: break
 fine.sort(key=key,reverse=True); report={'schema_version':'forexai.sp2l_optimizer.v15.7','train_end_exclusive':'2025-01-01','holdout_2025_2026_excluded':True,'real_data_required':True,'synthetic_fallback':False,'stage_a_candidates':len(rows),'stage_b_candidates':len(fine),'top10':fine[:10]}; Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
