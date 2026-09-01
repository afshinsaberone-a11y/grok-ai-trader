"""SP2L v15.8 research audit: signal integrity and M5 data quality."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from research.optimization.sp2l_v15_7 import Params,signals,audit

def load(path):
 d=pd.read_csv(path); cols={c.lower():c for c in d.columns}; d=d.rename(columns={cols[k]:k.title() for k in ('open','high','low','close') if k in cols}); ts=next((c for c in d.columns if c.lower() in ('timestamp','time','datetime')),None)
 if ts is None: raise ValueError('TIMESTAMP_REQUIRED')
 d[ts]=pd.to_datetime(d[ts],utc=True); return d.set_index(ts).sort_index()

def run(path):
 d=load(path); s=signals(d,Params()); dif=d.index.to_series().diff().dropna(); expected=pd.Timedelta(minutes=5); gaps=dif[dif>expected]
 out=audit(d,Params()); out.update({'schema_version':'forexai.sp2l_research_audit.v15.8','timeframe':'M5','first_timestamp':str(d.index.min()),'last_timestamp':str(d.index.max()),'duplicate_timestamps':int(d.index.duplicated().sum()),'gap_count':int(len(gaps)),'gap_rows_lost_estimate':int((gaps/expected-1).clip(lower=0).sum()),'max_gap_minutes':float(gaps.max().total_seconds()/60) if len(gaps) else 0.0,'ohlc_valid':bool(((d.High>=d.Low)&(d.High>=d.Open)&(d.High>=d.Close)&(d.Low<=d.Open)&(d.Low<=d.Close)).all()),'long_short_balance_ratio':round(int((s==1).sum())/max(int((s==-1).sum()),1),4),'signal_clusters':int((s.ne(0)&s.shift(1).eq(0)).sum()),'same_bar_confirmation_possible':False})
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/sp2l-v15-8-audit.json'); a=ap.parse_args(); r=run(a.data); Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(r,indent=2),encoding='utf-8'); print(json.dumps(r,indent=2))
if __name__=='__main__': main()
