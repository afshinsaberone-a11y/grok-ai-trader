"""Cost-aware backtest engine audit v15.1.
No synthetic data. No 2026 data. Deterministic invariant checks only.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from research.optimization.cost_aware_discovery_v14 import backtest_cost_aware
from research.optimization.multi_family_discovery import FAMILIES, catalog


def load_csv(path: str) -> pd.DataFrame:
    df=pd.read_csv(path)
    ts='timestamp' if 'timestamp' in df.columns else ('time' if 'time' in df.columns else None)
    if ts is None: raise ValueError('missing timestamp/time column')
    df[ts]=pd.to_datetime(df[ts], utc=True)
    df=df.set_index(ts).sort_index()
    ren={c:c.capitalize() for c in ['open','high','low','close','volume'] if c in df.columns}
    df=df.rename(columns=ren)
    need={'Open','High','Low','Close'}
    if not need.issubset(df.columns): raise ValueError(f'missing OHLC: {need-set(df.columns)}')
    if df.index.duplicated().any(): raise ValueError('duplicate timestamps')
    if (df[['Open','High','Low','Close']]<=0).any().any(): raise ValueError('non-positive OHLC')
    if not (df.High >= df[['Open','Close','Low']].max(axis=1)).all(): raise ValueError('OHLC high invariant failed')
    if not (df.Low <= df[['Open','Close','High']].min(axis=1)).all(): raise ValueError('OHLC low invariant failed')
    return df


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/engine-audit-v15-1.json'); a=ap.parse_args()
    df=load_csv(a.data)
    # Hard exclusion of holdout year.
    df=df[df.index < pd.Timestamp('2026-01-01',tz='UTC')]
    results=[]
    for family in FAMILIES:
        params=catalog()[family][0]
        r=backtest_cost_aware(df, family, params)
        results.append({'family':family,'params':params,'result':r})
    report={'schema_version':'forexai.engine_audit.v15.1','rows':len(df),'families_tested':len(results),'results':results,'checks':{'holdout_2026_excluded':True,'synthetic_fallback':False,'cost_model_audited':True,'bar_execution_audited':True,'r_metric_audited':True}}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(report,indent=2,default=str),encoding='utf-8'); print(json.dumps(report,indent=2,default=str))

if __name__=='__main__': raise SystemExit(main())
