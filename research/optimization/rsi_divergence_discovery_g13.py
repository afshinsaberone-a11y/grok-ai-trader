"""ForexAI G13: deterministic RSI-divergence event discovery on REAL EURUSD M15.
Discovery 2022-2024; validation 2025; 2026 is never loaded.
This is a diagnostic discovery screen; no candidate is promoted here.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost, validate_ohlc
from research.optimization.cost_aware_gate_v14 import PRE_OOS_YEARS, MIN_PF_EACH_YEAR, MIN_EXPECTANCY_R, MIN_TRADES_EACH_YEAR, PRE_OOS_MAX_DD_PCT, MIN_PROFITABLE_YEARS

PIP_SIZE=0.0001
RISK_PCT=0.005
MAX_HOLD=30
YEARS=(2022,2023,2024,2025)
CATALOG=[]
for pivot in (3,5,8):
    for rsi_low,rsi_high in ((30,70),(35,65)):
        for min_delta in (0.0003,0.0005):
            for atr_mult,rr in ((1.0,1.5),(1.5,2.0)):
                for side in ("long","short"):
                    CATALOG.append(dict(pivot=pivot,rsi_low=rsi_low,rsi_high=rsi_high,min_delta=min_delta,atr_mult=atr_mult,rr=rr,side=side))

def prep(df):
    d=df.copy(); d.columns=[str(c).strip() for c in d.columns]
    if 'Timestamp' in d.columns and 'timestamp' not in d.columns: d=d.rename(columns={'Timestamp':'timestamp'})
    d['timestamp']=pd.to_datetime(d['timestamp'],utc=True); d=d.sort_values('timestamp').reset_index(drop=True)
    d=d[d.timestamp.dt.year.isin(YEARS)].copy(); d=d.rename(columns={'timestamp':'Timestamp','open':'Open','high':'High','low':'Low','close':'Close'})
    validate_ohlc(d)
    tr=pd.concat([(d.High-d.Low),(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1)
    d['ATR14']=tr.rolling(14,min_periods=14).mean()
    delta=d.Close.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=(-delta.clip(upper=0)).rolling(14).mean()
    d['RSI14']=100-100/(1+gain/loss.replace(0,np.nan))
    return d.set_index('Timestamp').sort_index()

def pivots(d,p):
    return d.High.eq(d.High.rolling(2*p+1,center=True).max()).fillna(False), d.Low.eq(d.Low.rolling(2*p+1,center=True).min()).fillna(False)

def signals(d,p):
    ph,pl=pivots(d,p['pivot']); out=pd.Series(0,index=d.index,dtype=int); highs=[]; lows=[]
    for i in range(p['pivot'],len(d)-p['pivot']):
        if not (np.isfinite(d.RSI14.iloc[i]) and np.isfinite(d.ATR14.iloc[i])): continue
        pi=i-p['pivot']
        if ph.iloc[pi]: highs.append((pi,float(d.High.iloc[pi]),float(d.RSI14.iloc[pi])))
        if pl.iloc[pi]: lows.append((pi,float(d.Low.iloc[pi]),float(d.RSI14.iloc[pi])))
        if p['side']=='short' and len(highs)>=2:
            a,b=highs[-2],highs[-1]
            if b[1]>a[1]+p['min_delta'] and b[2]<a[2] and b[2]>=p['rsi_high']: out.iloc[i]=-1
        if p['side']=='long' and len(lows)>=2:
            a,b=lows[-2],lows[-1]
            if b[1]<a[1]-p['min_delta'] and b[2]>a[2] and b[2]<=p['rsi_low']: out.iloc[i]=1
    return out

def empty(): return {'trades':0,'win_rate':0.0,'total_R':0.0,'expectancy_R':0.0,'profit_factor':0.0,'max_dd_pct':0.0,'entries':0,'exits':0}

def backtest(d,p):
    if len(d)<100: return empty()
    sig=signals(d,p); cfg=ExecutionConfig(); rs=[]; pos=None
    for i in range(1,len(d)):
        if pos is not None:
            h,l=float(d.High.iloc[i]),float(d.Low.iloc[i]); age=i-pos['entry_i']
            slhit=l<=pos['sl'] if pos['side']==1 else h>=pos['sl']; tphit=h>=pos['tp'] if pos['side']==1 else l<=pos['tp']
            opposite=bool(sig.iloc[i]==-pos['side'])
            if slhit or tphit or opposite or age>=MAX_HOLD:
                raw=pos['sl'] if slhit else pos['tp'] if tphit else float(d.Close.iloc[i]); ex=apply_exit_cost(raw,pos['side'],cfg)
                rs.append(float((ex-pos['entry'])/(pos['entry']-pos['sl'])*pos['side'])); pos=None
        if pos is None and bool(sig.iloc[i-1]):
            side=int(sig.iloc[i-1]); entry=apply_entry_cost(float(d.Open.iloc[i]),side,cfg); atr=float(d.ATR14.iloc[i-1])
            if not np.isfinite(atr) or atr<=0: continue
            risk=p['atr_mult']*atr; sl=entry-side*risk; tp=entry+side*p['rr']*risk; pos={'entry_i':i,'side':side,'entry':entry,'sl':sl,'tp':tp}
    if pos is not None:
        ex=apply_exit_cost(float(d.Close.iloc[-1]),pos['side'],cfg); rs.append(float((ex-pos['entry'])/(pos['entry']-pos['sl'])*pos['side']))
    r=np.asarray(rs,float); n=len(r); gp=r[r>0].sum() if n else 0.; gl=-r[r<0].sum() if n else 0.; pf=gp/gl if gl>0 else (3.0 if gp>0 else 0.0)
    eq=peak=10000.; dd=0.0
    for x in r: eq*=1+RISK_PCT*x; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
    return {'trades':n,'win_rate':float((r>0).mean()*100) if n else 0.0,'total_R':float(r.sum()),'expectancy_R':float(r.mean()) if n else 0.0,'profit_factor':float(pf),'max_dd_pct':float(dd*100),'entries':n,'exits':n}

def gate(yearly):
    reasons=[]
    for y,m in yearly.items():
        if m['trades']<MIN_TRADES_EACH_YEAR: reasons.append(f'trades<{MIN_TRADES_EACH_YEAR}:{y}')
        if m['profit_factor']<MIN_PF_EACH_YEAR: reasons.append(f'pf<{MIN_PF_EACH_YEAR}:{y}')
        if m['expectancy_R']<=MIN_EXPECTANCY_R: reasons.append(f'expectancy<={MIN_EXPECTANCY_R}:{y}')
        if m['max_dd_pct']>PRE_OOS_MAX_DD_PCT: reasons.append(f'dd>{PRE_OOS_MAX_DD_PCT}:{y}')
    if sum(yearly[y]['expectancy_R']>0 for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS: reasons.append(f'profitable_years<{MIN_PROFITABLE_YEARS}')
    return reasons

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    d=prep(pd.read_csv(a.data)); years={y:d[d.index.year==y] for y in YEARS}; results=[]
    for cid,p in enumerate(CATALOG,1):
        pre={y:backtest(years[y],p) for y in PRE_OOS_YEARS}; reasons=gate(pre)
        pfs=[m['profit_factor'] for m in pre.values()]
        exps=[m['expectancy_R'] for m in pre.values()]
        trs=[m['total_R'] for m in pre.values()]
        dds=[m['max_dd_pct'] for m in pre.values()]
        score=round(1.5*min(pfs)+float(np.mean(exps))+float(np.tanh(sum(trs)/100.0))-max(dds)/100.0,6)
        results.append({'candidate_id':cid,'params':p,'pre_oos':pre,'score':score,'pre_oos_pass':not reasons,'rejection_reasons':reasons,'validation_2025':backtest(years[2025],p)})
    results.sort(key=lambda x:-x['score']); qualified=[x for x in results if x['pre_oos_pass']]
    payload={'schema_version':'forexai.g13.rsi_divergence_discovery.v1','research_scope':{'symbol':'EURUSD','timeframe':'M15','discovery_years':[2022,2023,2024],'validation_year':2025},'candidate_total':len(results),'pre_oos_qualified':len(qualified),'validation_qualified':0,'champion':None,'top_50_diagnostics':results[:50],'execution_model':{'entry':'next_bar_open','cost_pips_per_side':0.7,'round_trip_cost_pips':1.4,'same_bar_resolution':'SL first (conservative)','expiry_bars':30,'overlap':'one position at a time'},'policy':{'real_data_required':True,'synthetic_data':False,'oos_2026_used':False,'parameter_selection_used_2025':False,'gates_unchanged':True,'champion':None},'official_gates':{'min_profitable_years':MIN_PROFITABLE_YEARS,'min_pf_each_year':MIN_PF_EACH_YEAR,'min_expectancy':MIN_EXPECTANCY_R,'min_trades_each_year':MIN_TRADES_EACH_YEAR,'max_dd_pct':PRE_OOS_MAX_DD_PCT},'results':results,'note':'2026 is never loaded; this is discovery evidence only.'}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(payload,indent=2),encoding='utf-8'); print(json.dumps({'candidate_total':len(results),'pre_oos_qualified':len(qualified),'champion':None}))

if __name__=='__main__': main()
