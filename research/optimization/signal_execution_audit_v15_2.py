"""Signal/entry/exit audit v15.2.
Diagnoses trade-frequency and execution semantics on real pre-OOS data.
Does not alter strategy logic and never reads 2026.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.multi_family_discovery import FAMILIES,catalog,indicators,signal_family

def audit(df,family,params):
    d=indicators(df,params); sig=signal_family(d,family,params)
    s=sig.to_numpy(); close=d.Close.to_numpy(float); high=d.High.to_numpy(float); low=d.Low.to_numpy(float); atr=d.atr.to_numpy(float)
    nz=np.flatnonzero(s!=0); transitions=int(np.sum(s[1:]!=s[:-1])) if len(s)>1 else 0
    entries=exits=opposite=0; sl_hits=tp_hits=ambiguous=0; hold=[]; active=None; start=None
    for i in range(1,len(d)):
        if not np.isfinite(atr[i]) or atr[i]<=0: continue
        if active is None and s[i]!=0:
            active=int(s[i]); start=i; entries+=1; continue
        if active==1:
            stop=close[start]-params['atr_stop']*atr[start]; tp=close[start]+params['rr']*params['atr_stop']*atr[start]
            sl=low[i]<=stop; take=high[i]>=tp
            if sl or take or s[i]==-1:
                exits+=1; sl_hits+=int(sl); tp_hits+=int(take); ambiguous+=int(sl and take); opposite+=int(s[i]==-1); hold.append(i-start); active=None
        elif active==-1:
            stop=close[start]+params['atr_stop']*atr[start]; tp=close[start]-params['rr']*params['atr_stop']*atr[start]
            sl=high[i]>=stop; take=low[i]<=tp
            if sl or take or s[i]==1:
                exits+=1; sl_hits+=int(sl); tp_hits+=int(take); ambiguous+=int(sl and take); opposite+=int(s[i]==1); hold.append(i-start); active=None
    return {'rows':len(d),'signal_nonzero_bars':int(len(nz)),'signal_rate_pct':round(100*len(nz)/len(d),3) if len(d) else 0,'signal_transitions':transitions,'entries':entries,'exits':exits,'open_at_end':int(active is not None),'opposite_signal_exits':opposite,'sl_hits':sl_hits,'tp_hits':tp_hits,'same_bar_sl_tp_ambiguous':ambiguous,'avg_hold_bars':round(float(np.mean(hold)),2) if hold else 0,'median_hold_bars':round(float(np.median(hold)),2) if hold else 0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/signal-execution-audit-v15-2.json'); a=ap.parse_args()
    df=pd.read_csv(a.data); df['timestamp']=pd.to_datetime(df['timestamp'],utc=True); df=df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index('timestamp').sort_index(); df=df[df.index<pd.Timestamp('2026-01-01',tz='UTC')]
    out=[]
    for family in FAMILIES:
        p=catalog()[family][0]; out.append({'family':family,'params':p,'audit':audit(df,family,p)})
    report={'schema_version':'forexai.signal_execution_audit.v15.2','real_data_only':True,'holdout_2026_excluded':True,'families':out,'interpretation_rules':{'same_bar_sl_tp':'must be explicitly resolved conservatively','entry_signal_rate':'flag if implausibly high','opposite_signal_exit':'measure separately','position_sizing':'R-based engine invariant is audited separately'}}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(report,indent=2,default=str),encoding='utf-8'); print(json.dumps(report,indent=2,default=str))
if __name__=='__main__': raise SystemExit(main())
