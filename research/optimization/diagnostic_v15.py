"""Diagnostic harness for Cost-Aware Discovery v15.
Runs invariant checks on the real-data backtest path and writes diagnostics.
Never generates synthetic market data and never loads 2026 OOS data.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
import numpy as np
from research.optimization.cost_aware_discovery_v14 import backtest_cost_aware
from research.optimization.multi_family_discovery import FAMILIES, catalog

PRE_OOS=(2022,2023,2024)

def load(path):
    df=pd.read_csv(path)
    if 'timestamp' not in df: raise ValueError('missing timestamp column')
    df['timestamp']=pd.to_datetime(df['timestamp'],utc=True)
    cols={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}
    df=df.rename(columns=cols).set_index('timestamp').sort_index()
    required={'Open','High','Low','Close'}
    if not required.issubset(df.columns): raise ValueError(f'missing OHLC columns: {required-set(df.columns)}')
    if df.index.duplicated().any(): raise ValueError('duplicate timestamps detected')
    if not (df['High']>=df[['Open','Close','Low']].max(axis=1)).all(): raise ValueError('invalid OHLC high values')
    if not (df['Low']<=df[['Open','Close','High']].min(axis=1)).all(): raise ValueError('invalid OHLC low values')
    return df

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/diagnostic-v15.json'); a=ap.parse_args()
    df=load(a.data)
    years={y:df[(df.index>=f'{y}-01-01')&(df.index<f'{y+1}-01-01')] for y in (*PRE_OOS,2025)}
    checks=[]
    for y,d in years.items():
        checks.append({'year':y,'rows':len(d),'first':str(d.index.min()) if len(d) else None,'last':str(d.index.max()) if len(d) else None})
    sample=[]
    for family in FAMILIES:
        params=catalog()[family][0]
        row={'family':family,'sample_params':params,'years':{}}
        for y in PRE_OOS:
            row['years'][str(y)]=backtest_cost_aware(years[y],family,params)
        sample.append(row)
    report={'schema_version':'forexai.diagnostic.v15','data_checks':checks,'family_count':len(FAMILIES),'families':list(FAMILIES),'sample_backtests':sample,'oos_policy':{'2026':'HELD_OUT','loaded':False},'synthetic_fallback':False}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,default=str),encoding='utf-8'); print(json.dumps(report,indent=2,default=str))
if __name__=='__main__': raise SystemExit(main())
