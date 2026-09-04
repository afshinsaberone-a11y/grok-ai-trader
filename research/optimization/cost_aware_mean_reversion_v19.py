"""ForexAI v19: cost-aware mean-reversion discovery on REAL EURUSD M5.
2022-2024 discovery, 2025 validation, 2026 held out. Execution is v28.1-equivalent.
No synthetic data and no candidate promotion without the strict fail-closed gate.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
import numpy as np,pandas as pd
from research.optimization.cost_aware_gate_v14 import (PRE_OOS_YEARS,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,MIN_TRADES_EACH_YEAR,PRE_OOS_MAX_DD_PCT,MIN_PROFITABLE_YEARS,VALIDATION_MIN_PF,VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES)
PIP_SIZE=.0001; RISK_PCT=.005; MAX_HOLD_BARS=30; TOP_N=20

def catalog():
    out=[]
    for look in (20,30,50):
      for entry_z in (1.0,1.25,1.5):
       for exit_z in (0.0,0.25,0.5):
        for stop in (1.5,2.0,2.5):
         for rr in (1.0,1.25,1.5):
          for trend in (0,200):
           for session in ((0,24),(6,20)):
            out.append(dict(lookback=look,entry_z=entry_z,exit_z=exit_z,atr_stop=stop,rr=rr,trend_ema=trend,session_start=session[0],session_end=session[1]))
    return out

def metrics(rs,equity):
 n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else ('inf' if gp>0 else 0.0)
 peak=eq=10000.; dd=0.
 for r in rs:
  eq*=1+RISK_PCT*r; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
 return {'trades':n,'win_rate':round(100*wins/n,2) if n else 0.,'total_R':round(float(sum(rs)),2),'expectancy_R':round(float(sum(rs))/n,4) if n else 0.,'profit_factor':round(float(pf),3) if pf!='inf' else pf,'max_dd_pct':round(100*dd,2),'final_equity':round(eq,2),'execution_model':'v28.1_next_bar_open'}

def bt(df,p,spread=.5,slippage=.2):
 if len(df)<p['lookback']+5:return metrics([],10000)
 d=df.copy(); c=d.Close.astype(float); d['mid']=c.rolling(p['lookback']).mean(); d['sd']=c.rolling(p['lookback']).std(ddof=0); d['z']=(c-d.mid)/d.sd.replace(0,np.nan); d['atr']=pd.concat([d.High-d.Low,(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1).rolling(14).mean(); d['ema200']=c.ewm(span=200,adjust=False).mean();
 ts=d.index; z=d.z.to_numpy(float); atr=d.atr.to_numpy(float); op=d.Open.to_numpy(float); hi=d.High.to_numpy(float); lo=d.Low.to_numpy(float); cl=c.to_numpy(float); ema=d.ema200.to_numpy(float); cost=(spread+slippage)*PIP_SIZE
 pos=0; entry=stop=tp=0.; entry_i=-1; rs=[]
 for i in range(1,len(d)):
  if pos==0:
   h=ts[i-1].hour + ts[i-1].minute/60
   if not(p['session_start']<=h<p['session_end']) or not np.isfinite(z[i-1]) or not np.isfinite(atr[i-1]) or atr[i-1]<=0: continue
   s=0
   if z[i-1]<=-p['entry_z']: s=1
   elif z[i-1]>=p['entry_z']: s=-1
   if p['trend_ema']==200:
    if s==1 and cl[i-1]<ema[i-1]: s=0
    if s==-1 and cl[i-1]>ema[i-1]: s=0
   if not s: continue
   pos=s; entry=op[i]+(cost if s==1 else -cost); sd=p['atr_stop']*atr[i-1]; stop=entry-s*sd; tp=entry+s*p['rr']*sd; entry_i=i; continue
  s=z[i-1]; ep=None
  if pos==1:
   if lo[i]<=stop and hi[i]>=tp: ep=stop
   elif lo[i]<=stop: ep=stop
   elif hi[i]>=tp: ep=tp
   elif (s>=-p['exit_z']): ep=cl[i]-cost
   elif i-entry_i>=MAX_HOLD_BARS: ep=cl[i]-cost
   if ep is not None: rs.append((ep-entry)/abs(entry-stop)); pos=0
  else:
   if hi[i]>=stop and lo[i]<=tp: ep=stop
   elif hi[i]>=stop: ep=stop
   elif lo[i]<=tp: ep=tp
   elif (s<=p['exit_z']): ep=cl[i]+cost
   elif i-entry_i>=MAX_HOLD_BARS: ep=cl[i]+cost
   if ep is not None: rs.append((entry-ep)/abs(stop-entry)); pos=0
 if pos:
  ep=cl[-1]-cost if pos==1 else cl[-1]+cost; rs.append((ep-entry)/abs(entry-stop) if pos==1 else (entry-ep)/abs(stop-entry))
 return metrics(rs,10000)

def pf(m): return 3. if m.get('profit_factor')=='inf' else float(m.get('profit_factor',0))
def gate(pre):
 by={x['year']:x['metrics'] for x in pre}; reasons=[]
 for y in PRE_OOS_YEARS:
  m=by[y]
  if m['trades']<MIN_TRADES_EACH_YEAR: reasons.append(f'trades<{MIN_TRADES_EACH_YEAR}:{y}')
  if pf(m)<MIN_PF_EACH_YEAR: reasons.append(f'pf<{MIN_PF_EACH_YEAR}:{y}')
  if m['expectancy_R']<=MIN_EXPECTANCY_R: reasons.append(f'expectancy<={MIN_EXPECTANCY_R}:{y}')
  if m['max_dd_pct']>PRE_OOS_MAX_DD_PCT: reasons.append(f'dd>{PRE_OOS_MAX_DD_PCT}:{y}')
 if sum(by[y]['expectancy_R']>MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS: reasons.append(f'profitable_years<{MIN_PROFITABLE_YEARS}')
 return reasons

def score(pre):
 ms=[x['metrics'] for x in pre]; return round(float(1.5*min(pf(x) for x in ms)+.75*np.mean([pf(x) for x in ms])+2*np.tanh(sum(x['total_R'] for x in ms)/100)+np.tanh(np.mean([x['expectancy_R'] for x in ms])*10)-1.5*max(x['max_dd_pct'] for x in ms)/100),6)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',required=True); ap.add_argument('--spread-pips',type=float,default=.5); ap.add_argument('--slippage-pips',type=float,default=.2); a=ap.parse_args()
 d=pd.read_csv(a.data); d['timestamp']=pd.to_datetime(d.timestamp,utc=True); d=d.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index('timestamp').sort_index(); assert len(d)>0
 years={y:d[(d.index>=f'{y}-01-01')&(d.index<f'{y+1}-01-01')] for y in (2022,2023,2024,2025)}
 results=[]
 for i,p in enumerate(catalog(),1):
  pre=[{'year':y,'metrics':bt(years[y],p,a.spread_pips,a.slippage_pips)} for y in PRE_OOS_YEARS]; reasons=gate(pre)
  results.append({'candidate':i,'params':p,'score':score(pre),'pre_oos':pre,'pre_oos_pass':not reasons,'rejection_reasons':reasons})
 results.sort(key=lambda x:-x['score']); finalists=[x for x in results if x['pre_oos_pass']]; validated=[]
 for x in finalists:
  vm=bt(years[2025],x['params'],a.spread_pips,a.slippage_pips); vr=[]
  if pf(vm)<VALIDATION_MIN_PF: vr.append(f'validation_pf<{VALIDATION_MIN_PF}')
  if vm['max_dd_pct']>VALIDATION_MAX_DD_PCT: vr.append(f'validation_dd>{VALIDATION_MAX_DD_PCT}')
  if vm['trades']<VALIDATION_MIN_TRADES: vr.append(f'validation_trades<{VALIDATION_MIN_TRADES}')
  validated.append({**x,'validation_2025':vm,'validation_pass':not vr,'validation_rejection_reasons':vr})
 qualified=[x for x in validated if x['validation_pass']]
 report={'schema_version':'forexai.cost_aware_mean_reversion.v19','result':{'candidate_total':len(results),'qualified_count':len(qualified),'champion':None,'top_20_diagnostics':results[:TOP_N],'validated_candidates':validated,'execution_model':'v28.1_next_bar_open'},'oos_policy':{'loaded':False,'status':'HELD_OUT','start':'2026-01-01'},'real_data_required':True,'synthetic_fallback':False,'research_timeframe':'M5','cost_profile':{'spread_pips':a.spread_pips,'slippage_pips':a.slippage_pips,'round_trip_cost_pips':2*(a.spread_pips+a.slippage_pips)}}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(report,indent=2,default=lambda x:float(x) if isinstance(x,np.floating) else x),encoding='utf-8'); print(json.dumps({'candidate_total':len(results),'pre_oos_qualified':len(finalists),'validation_qualified':len(qualified),'top_candidate':results[0]['candidate']},indent=2))
if __name__=='__main__': main()
