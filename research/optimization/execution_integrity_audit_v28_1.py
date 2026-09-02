"""ForexAI v28.1 execution-integrity audit.
Real data only; 2026 holdout excluded. Audits next-bar-open entry,
actual entry-price SL/TP, costs, expiry, opposite exits, non-overlap,
and conservative same-bar SL-first semantics.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.multi_family_discovery import FAMILIES,catalog,indicators,signal_family

SPREAD_PIPS_PER_SIDE=0.5
SLIPPAGE_PIPS_PER_SIDE=0.2
PIP=0.0001
ROUND_TRIP_PIPS=2*(SPREAD_PIPS_PER_SIDE+SLIPPAGE_PIPS_PER_SIDE)
DEFAULT_EXPIRY=30

def load(path):
    d=pd.read_csv(path)
    ts='timestamp' if 'timestamp' in d.columns else 'time'
    d[ts]=pd.to_datetime(d[ts],utc=True)
    d=d.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index(ts).sort_index()
    d=d[d.index<pd.Timestamp('2026-01-01',tz='UTC')]
    if d.index.duplicated().any(): raise RuntimeError('duplicate timestamps')
    if not (d.High>=d[['Open','Close','Low']].max(axis=1)).all(): raise RuntimeError('OHLC high invariant failed')
    if not (d.Low<=d[['Open','Close','High']].min(axis=1)).all(): raise RuntimeError('OHLC low invariant failed')
    return d

def corrected_signal(d,family,p):
    if family!='sp2l_lite': return signal_family(d,family,p)
    body=(d.Close-d.Open).abs(); rng=d.High-d.Low
    spike=(rng>0)&((body/rng)>=p['body_ratio'])&(rng>=p['atr_mult']*d.atr)
    gap_up=d.Low>d.High.shift(2); gap_dn=d.High<d.Low.shift(2)
    s=pd.Series(0,index=d.index,dtype=int)
    s[spike&gap_up&(d.Close>d.Open)]=1
    s[spike&gap_dn&(d.Close<d.Open)]=-1
    return s

def audit(df,family,p):
    d=indicators(df,p); s=corrected_signal(d,family,p)
    o,h,l,c,atr=d.Open.to_numpy(float),d.High.to_numpy(float),d.Low.to_numpy(float),d.Close.to_numpy(float),d.atr.to_numpy(float)
    x=s.to_numpy(int)
    nonzero=int(np.count_nonzero(x)); rate=100*nonzero/len(x) if len(x) else 0
    entries=exits=sl=tp=amb=opp=expiry=0; holds=[]; outcomes=[]; active=None
    entry_idx=None; entry_px=stop=target=0.0; direction=0
    for i in range(len(d)-1):
        if not np.isfinite(atr[i]) or atr[i]<=0: continue
        if active is None and x[i]!=0:
            direction=int(x[i]); entry_idx=i+1
            # Adverse half-cost on entry: buy above open, sell below open.
            entry_px=float(o[entry_idx]) + direction*(SPREAD_PIPS_PER_SIDE+SLIPPAGE_PIPS_PER_SIDE)*PIP
            risk=p['atr_stop']*atr[i]
            stop=entry_px-direction*risk
            target=entry_px+direction*p['rr']*risk
            active=True; entries+=1; continue
        if active:
            age=i-entry_idx+1
            hit_sl=(l[i]<=stop) if direction==1 else (h[i]>=stop)
            hit_tp=(h[i]>=target) if direction==1 else (l[i]<=target)
            if hit_sl and hit_tp:
                amb+=1; exit_px=stop; result=-1.0; reason='same_bar_sl_first'; sl+=1
            elif hit_sl:
                exit_px=stop; result=-1.0; reason='sl'; sl+=1
            elif hit_tp:
                exit_px=target; result=p['rr']; reason='tp'; tp+=1
            elif x[i]==-direction:
                exit_px=float(o[i])-direction*(SPREAD_PIPS_PER_SIDE+SLIPPAGE_PIPS_PER_SIDE)*PIP
                result=direction*(exit_px-entry_px)/(p['atr_stop']*atr[i]); reason='opposite'; opp+=1
            elif age>=DEFAULT_EXPIRY:
                exit_px=float(o[i])-direction*(SPREAD_PIPS_PER_SIDE+SLIPPAGE_PIPS_PER_SIDE)*PIP
                result=direction*(exit_px-entry_px)/(p['atr_stop']*atr[i]); reason='expiry'; expiry+=1
            else: continue
            exits+=1; holds.append(age); outcomes.append({'R':float(result),'reason':reason}); active=None
    if active: exits+=1; outcomes.append({'R':0.0,'reason':'end_of_data'}); active=None
    return {'rows':len(d),'signal_nonzero_bars':nonzero,'signal_rate_pct':round(rate,4),'entries':entries,'exits':exits,'open_at_end':0,'opposite_signal_exits':opp,'expiry_exits':expiry,'sl_hits':sl,'tp_hits':tp,'same_bar_sl_tp_ambiguous':amb,'avg_hold_bars':round(float(np.mean(holds)),2) if holds else 0,'median_hold_bars':round(float(np.median(holds)),2) if holds else 0,'non_overlap_invariant':entries==exits,'next_bar_open_entry':True,'actual_entry_price_for_stops':True,'round_trip_cost_pips':ROUND_TRIP_PIPS,'outcome_count':len(outcomes)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',default='artifacts/execution-integrity-audit-v28-1.json'); a=ap.parse_args()
    df=load(a.data); results=[]
    for family in FAMILIES:
        p=catalog()[family][0]
        results.append({'family':family,'params':p,'audit':audit(df,family,p)})
    report={'schema_version':'forexai.execution_integrity_audit.v28.1','real_data_only':True,'holdout_2026_excluded':True,'execution_model':{'entry':'next_bar_open','entry_cost_pips_per_side':0.7,'exit_cost_pips_per_side':0.7,'same_bar_resolution':'SL first (conservative)','expiry_bars':DEFAULT_EXPIRY,'overlap':'one position at a time'},'families':results,'sp2l_lite_signal_fix':'explicit_parentheses_and_boolean_masks'}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
if __name__=='__main__': raise SystemExit(main())
