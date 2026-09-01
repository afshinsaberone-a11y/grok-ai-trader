from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.sp2l_v15_7 import Params,signals

def load(path):
 d=pd.read_csv(path); cols={c.lower():c for c in d.columns}; d=d.rename(columns={cols[k]:k.title() for k in ('open','high','low','close') if k in cols}); ts=next(c for c in d if c.lower() in ('timestamp','time','datetime')); d[ts]=pd.to_datetime(d[ts],utc=True); return d.set_index(ts).sort_index()
def audit(d,p):
 s=signals(d,p).to_numpy(); idx=np.flatnonzero(s); gaps=d.index.to_series().diff().dt.total_seconds().div(60); normal=gaps.le(5).fillna(True); valid=np.array([normal.iloc[i] and (i+1<len(normal) and normal.iloc[i+1]) for i in idx]); idx=idx[valid]
 return {'rows':len(d),'signals':int(len(idx)),'long':int((s[idx]>0).sum()),'short':int((s[idx]<0).sum()),'signal_rate_pct':float(len(idx)/len(d)*100),'gap_count':int((gaps>5).sum()),'max_gap_minutes':float(gaps.max()),'signals_near_gap_removed':int((~valid).sum())}
def main():
 a=argparse.ArgumentParser();a.add_argument('--data',required=True);a.add_argument('--output',default='artifacts/sp2l-v15-9-audit.json');x=a.parse_args();d=load(x.data); d=d[d.index<pd.Timestamp('2025-01-01',tz='UTC')]; r=audit(d,Params()); out={'schema_version':'forexai.sp2l_data_aware.v15.9','train_end_exclusive':'2025-01-01','synthetic_data':False,'gap_policy':'exclude_signals_touching_gap','audit':r};Path(x.output).parent.mkdir(exist_ok=True);Path(x.output).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
