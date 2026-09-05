"""ForexAI v21.1: optimized cost-aware London Breakout discovery on REAL EURUSD M5.
Same hypothesis and gates as v21; only execution implementation is optimized.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.cost_aware_gate_v14 import (
 PRE_OOS_YEARS,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,MIN_TRADES_EACH_YEAR,
 PRE_OOS_MAX_DD_PCT,MIN_PROFITABLE_YEARS,VALIDATION_MIN_PF,
 VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES,
)
PIP_SIZE=.0001;RISK_PCT=.005;MAX_HOLD_BARS=30;TOP_N=20

def catalog():
    out=[]
    for range_end in (9,10):
      for breakout_end in (13,14,15):
       for buffer_atr in (0.0,0.1,0.2):
        for atr_stop in (1.0,1.5,2.0):
         for rr in (1.0,1.5,2.0):
          for trend_ema in (0,200):
           out.append(dict(range_start=7,range_end=range_end,breakout_start=range_end,breakout_end=breakout_end,buffer_atr=buffer_atr,atr_stop=atr_stop,rr=rr,trend_ema=trend_ema))
    return out

def _prepare(df):
    d=df.copy()
    d['timestamp']=pd.to_datetime(d['timestamp'],utc=True)
    d=d.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index('timestamp').sort_index()
    tr=pd.concat([d.High-d.Low,(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1)
    d['atr']=tr.rolling(14).mean();d['ema200']=d.Close.ewm(span=200,adjust=False).mean();d['day']=d.index.date;d['hour']=d.index.hour+d.index.minute/60
    return d

def metrics(rs):
    n=len(rs);wins=sum(x>0 for x in rs);gp=sum(x for x in rs if x>0);gl=abs(sum(x for x in rs if x<=0));pf=gp/gl if gl else ('inf' if gp>0 else 0.0)
    eq=peak=10000.;dd=0.
    for r in rs:eq*=1+RISK_PCT*r;peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    return {'trades':n,'win_rate':round(100*wins/n,2) if n else 0.0,'total_R':round(float(sum(rs)),2),'expectancy_R':round(float(sum(rs))/n,4) if n else 0.0,'profit_factor':round(float(pf),3) if pf!='inf' else pf,'max_dd_pct':round(100*dd,2),'final_equity':round(eq,2),'execution_model':'v28.1_next_bar_open','entries':n,'exits':n,'open_position':False}

def bt(d,p,spread=.5,slippage=.2):
    if len(d)<100:return metrics([])
    cost=(spread+slippage)*PIP_SIZE;rs=[];last_day=None
    for day,g in d.groupby('day',sort=True):
        # one-trade-per-day rule
        rng=g[(g.hour>=p['range_start'])&(g.hour<p['range_end'])]
        bo=g[(g.hour>=p['breakout_start'])&(g.hour<p['breakout_end'])]
        if rng.empty or bo.empty:continue
        ri=rng.index
        rh=float(g.loc[ri,'High'].max());rl=float(g.loc[ri,'Low'].min())
        # only use closed-bar ATR/EMA and enter on next bar open
        for ts,row in bo.iterrows():
            loc=g.index.get_loc(ts)
            if loc+1>=len(g):continue
            a=float(g.iloc[loc]['atr']); ema=float(g.iloc[loc]['ema200']); close=float(row['Close'])
            if not np.isfinite(a) or a<=0:continue
            buf=p['buffer_atr']*a
            long_sig=close>rh+buf;short_sig=close<rl-buf
            if p['trend_ema']==200:
                long_sig=long_sig and close>ema;short_sig=short_sig and close<ema
            s=1 if long_sig else (-1 if short_sig else 0)
            if not s:continue
            j=loc+1;entry=float(g.iloc[j]['Open'])+(cost if s==1 else -cost);dist=p['atr_stop']*a;stop=entry-s*dist;tp=entry+s*p['rr']*dist;exit_j=None;exit_price=None
            max_j=min(j+MAX_HOLD_BARS,len(g)-1)
            for k in range(j,max_j+1):
                hi=float(g.iloc[k]['High']);lo=float(g.iloc[k]['Low'])
                if s==1:
                    if lo<=stop:exit_j=k;exit_price=stop;break
                    if hi>=tp:exit_j=k;exit_price=tp;break
                else:
                    if hi>=stop:exit_j=k;exit_price=stop;break
                    if lo<=tp:exit_j=k;exit_price=tp;break
            if exit_j is None:
                exit_j=max_j;exit_price=float(g.iloc[exit_j]['Close'])-(cost if s==1 else -cost)
            rs.append((exit_price-entry)/abs(entry-stop) if s==1 else (entry-exit_price)/abs(stop-entry))
            last_day=day;break
    return metrics(rs)

def pf(m):return 3.0 if m.get('profit_factor')=='inf' else float(m.get('profit_factor',0))

def gate(pre):
    by={x['year']:x['metrics'] for x in pre};reasons=[]
    for y in PRE_OOS_YEARS:
        m=by[y]
        if m['trades']<MIN_TRADES_EACH_YEAR:reasons.append(f'trades<{MIN_TRADES_EACH_YEAR}:{y}')
        if pf(m)<MIN_PF_EACH_YEAR:reasons.append(f'pf<{MIN_PF_EACH_YEAR}:{y}')
        if m['expectancy_R']<=MIN_EXPECTANCY_R:reasons.append(f'expectancy<={MIN_EXPECTANCY_R}:{y}')
        if m['max_dd_pct']>PRE_OOS_MAX_DD_PCT:reasons.append(f'dd>{PRE_OOS_MAX_DD_PCT}:{y}')
    if sum(by[y]['expectancy_R']>MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS:reasons.append(f'profitable_years<{MIN_PROFITABLE_YEARS}')
    return reasons

def score(pre):
    ms=[x['metrics'] for x in pre]
    return round(float(1.5*min(pf(x) for x in ms)+.75*np.mean([pf(x) for x in ms])+2*np.tanh(sum(x['total_R'] for x in ms)/100)+np.tanh(np.mean([x['expectancy_R'] for x in ms])*10)-1.5*max(x['max_dd_pct'] for x in ms)/100),6)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--output',required=True);ap.add_argument('--spread-pips',type=float,default=.5);ap.add_argument('--slippage-pips',type=float,default=.2);a=ap.parse_args()
    d=_prepare(pd.read_csv(a.data));years={y:d[(d.index>=f'{y}-01-01')&(d.index<f'{y+1}-01-01')] for y in (2022,2023,2024,2025)};results=[]
    for i,p in enumerate(catalog(),1):
        pre=[{'year':y,'metrics':bt(years[y],p,a.spread_pips,a.slippage_pips)} for y in PRE_OOS_YEARS];reasons=gate(pre)
        results.append({'candidate':i,'params':p,'score':score(pre),'pre_oos':pre,'pre_oos_pass':not reasons,'rejection_reasons':reasons})
    results.sort(key=lambda x:-x['score']);finalists=[x for x in results if x['pre_oos_pass']];validated=[]
    for x in finalists:
        vm=bt(years[2025],x['params'],a.spread_pips,a.slippage_pips);vr=[]
        if pf(vm)<VALIDATION_MIN_PF:vr.append(f'validation_pf<{VALIDATION_MIN_PF}')
        if vm['max_dd_pct']>VALIDATION_MAX_DD_PCT:vr.append(f'validation_dd>{VALIDATION_MAX_DD_PCT}')
        if vm['trades']<VALIDATION_MIN_TRADES:vr.append(f'validation_trades<{VALIDATION_MIN_TRADES}')
        validated.append({**x,'validation_2025':vm,'validation_pass':not vr,'validation_rejection_reasons':vr})
    qualified=[x for x in validated if x['validation_pass']]
    report={'schema_version':'forexai.cost_aware_london_breakout.v21.1','result':{'candidate_total':len(results),'qualified_count':len(qualified),'champion':None,'top_20_diagnostics':results[:TOP_N],'validated_candidates':validated,'execution_model':'v28.1_next_bar_open'},'oos_policy':{'loaded':False,'status':'HELD_OUT','start':'2026-01-01'},'real_data_required':True,'synthetic_fallback':False,'research_timeframe':'M5','cost_profile':{'spread_pips':a.spread_pips,'slippage_pips':a.slippage_pips,'round_trip_cost_pips':2*(a.spread_pips+a.slippage_pips)}}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(report,indent=2,default=lambda x:float(x) if isinstance(x,np.floating) else x),encoding='utf-8');print(json.dumps({'candidate_total':len(results),'pre_oos_qualified':len(finalists),'validation_qualified':len(qualified),'top_candidate':results[0]['candidate']},indent=2))
if __name__=='__main__':main()
