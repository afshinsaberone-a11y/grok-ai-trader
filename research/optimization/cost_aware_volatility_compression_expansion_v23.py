"""ForexAI v23: cost-aware volatility compression -> expansion discovery on REAL EURUSD M5.
Signal uses only closed bars; entry is next-bar open. 2022-2024 discovery, 2025 validation, 2026 held out.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.cost_aware_gate_v14 import PRE_OOS_YEARS,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,MIN_TRADES_EACH_YEAR,PRE_OOS_MAX_DD_PCT,MIN_PROFITABLE_YEARS,VALIDATION_MIN_PF,VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES
PIP=.0001;RISK=.005;MAX_HOLD=30;TOP_N=20
def catalog():
 out=[]
 for lb in (12,24):
  for comp in (.6,.8):
   for breakout in (.5,1.0):
    for atr_stop in (1.0,1.5,2.0):
     for rr in (1.0,1.5,2.0):
      for direction in ('both','trend'):
       for session in ((0,24),(6,20)):
        out.append(dict(lookback=lb,compression_ratio=comp,breakout_atr=breakout,atr_stop=atr_stop,rr=rr,direction=direction,session_start=session[0],session_end=session[1]))
 return out
def prep(df):
 d=df.copy();d.timestamp=pd.to_datetime(d.timestamp,utc=True);d=d.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index('timestamp').sort_index()
 tr=pd.concat([d.High-d.Low,(d.High-d.Close.shift()).abs(),(d.Low-d.Close.shift()).abs()],axis=1).max(axis=1)
 d['atr']=tr.rolling(14).mean();d['atr_base']=d.atr.rolling(50).mean();d['ema200']=d.Close.ewm(span=200,adjust=False).mean();d['day']=d.index.date
 return d
def metrics(rs):
 n=len(rs);gp=sum(x for x in rs if x>0);gl=abs(sum(x for x in rs if x<=0));pf=gp/gl if gl else ('inf' if gp>0 else 0.);eq=peak=10000.;dd=0.
 for r in rs:eq*=1+RISK*r;peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
 return {'trades':n,'win_rate':round(100*sum(x>0 for x in rs)/n,2) if n else 0.,'total_R':round(float(sum(rs)),2),'expectancy_R':round(float(sum(rs))/n,4) if n else 0.,'profit_factor':round(float(pf),3) if pf!='inf' else pf,'max_dd_pct':round(100*dd,2),'final_equity':round(eq,2),'execution_model':'v28.1_next_bar_open','entries':n,'exits':n,'open_position':False}
def bt(d,p,spread=.5,slippage=.2):
 if len(d)<100:return metrics([])
 cost=(spread+slippage)*PIP;rs=[]
 for day,g in d.groupby('day',sort=True):
  g=g.reset_index(drop=False);n=len(g)
  for i in range(max(50,p['lookback']+1),n-1):
   h=g.loc[i,'timestamp'].hour+g.loc[i,'timestamp'].minute/60
   if not(p['session_start']<=h<p['session_end']):continue
   a=float(g.loc[i,'atr']);base=float(g.loc[i,'atr_base'])
   if not np.isfinite(a) or not np.isfinite(base) or a<=0 or base<=0:continue
   recent=float(g.loc[i-p['lookback']:i-1,'atr'].mean())
   if not np.isfinite(recent) or recent>p['compression_ratio']*base:continue
   c=float(g.loc[i,'Close']);prev_hi=float(g.loc[i-p['lookback']:i-1,'High'].max());prev_lo=float(g.loc[i-p['lookback']:i-1,'Low'].min())
   up=c>prev_hi+p['breakout_atr']*a;dn=c<prev_lo-p['breakout_atr']*a
   if p['direction']=='trend':
    up=up and c>float(g.loc[i,'ema200']);dn=dn and c<float(g.loc[i,'ema200'])
   side=1 if up else (-1 if dn else 0)
   if not side:continue
   j=i+1;entry=float(g.loc[j,'Open'])+(cost if side==1 else -cost);dist=p['atr_stop']*a;stop=entry-side*dist;tp=entry+side*p['rr']*dist;maxj=min(j+MAX_HOLD,n-1);ep=None
   for k in range(j,maxj+1):
    hi=float(g.loc[k,'High']);lo=float(g.loc[k,'Low'])
    if side==1:
     if lo<=stop:ep=stop;break
     if hi>=tp:ep=tp;break
    else:
     if hi>=stop:ep=stop;break
     if lo<=tp:ep=tp;break
   if ep is None:ep=float(g.loc[maxj,'Close'])-(cost if side==1 else -cost)
   rs.append((ep-entry)/abs(entry-stop) if side==1 else (entry-ep)/abs(stop-entry));break
 return metrics(rs)
def pf(m):return 3. if m.get('profit_factor')=='inf' else float(m.get('profit_factor',0))
def gate(pre):
 by={x['year']:x['metrics'] for x in pre};r=[]
 for y in PRE_OOS_YEARS:
  m=by[y]
  if m['trades']<MIN_TRADES_EACH_YEAR:r.append(f'trades<{MIN_TRADES_EACH_YEAR}:{y}')
  if pf(m)<MIN_PF_EACH_YEAR:r.append(f'pf<{MIN_PF_EACH_YEAR}:{y}')
  if m['expectancy_R']<=MIN_EXPECTANCY_R:r.append(f'expectancy<={MIN_EXPECTANCY_R}:{y}')
  if m['max_dd_pct']>PRE_OOS_MAX_DD_PCT:r.append(f'dd>{PRE_OOS_MAX_DD_PCT}:{y}')
 if sum(by[y]['expectancy_R']>MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS:r.append(f'profitable_years<{MIN_PROFITABLE_YEARS}')
 return r
def score(pre):
 ms=[x['metrics'] for x in pre]
 return round(float(1.5*min(pf(x) for x in ms)+.75*np.mean([pf(x) for x in ms])+2*np.tanh(sum(x['total_R'] for x in ms)/100)+np.tanh(np.mean([x['expectancy_R'] for x in ms])*10)-1.5*max(x['max_dd_pct'] for x in ms)/100),6)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--output',required=True);ap.add_argument('--spread-pips',type=float,default=.5);ap.add_argument('--slippage-pips',type=float,default=.2);a=ap.parse_args()
 d=prep(pd.read_csv(a.data));years={y:d[(d.index>=f'{y}-01-01')&(d.index<f'{y+1}-01-01')] for y in (2022,2023,2024,2025)};res=[]
 for i,p in enumerate(catalog(),1):
  pre=[{'year':y,'metrics':bt(years[y],p,a.spread_pips,a.slippage_pips)} for y in PRE_OOS_YEARS];g=gate(pre);res.append({'candidate':i,'params':p,'score':score(pre),'pre_oos':pre,'pre_oos_pass':not g,'rejection_reasons':g})
 res.sort(key=lambda x:-x['score']);fin=[x for x in res if x['pre_oos_pass']][:50];val=[]
 for x in fin:
  vm=bt(years[2025],x['params'],a.spread_pips,a.slippage_pips);vr=[]
  if pf(vm)<VALIDATION_MIN_PF:vr.append(f'validation_pf<{VALIDATION_MIN_PF}')
  if vm['max_dd_pct']>VALIDATION_MAX_DD_PCT:vr.append(f'validation_dd>{VALIDATION_MAX_DD_PCT}')
  if vm['trades']<VALIDATION_MIN_TRADES:vr.append(f'validation_trades<{VALIDATION_MIN_TRADES}')
  val.append({**x,'validation_2025':vm,'validation_pass':not vr,'validation_rejection_reasons':vr})
 q=[x for x in val if x['validation_pass']]
 rep={'schema_version':'forexai.cost_aware_volatility_compression_expansion.v23','result':{'candidate_total':len(res),'qualified_count':len(q),'champion':None,'top_20_diagnostics':res[:TOP_N],'validated_candidates':val,'execution_model':'v28.1_next_bar_open'},'oos_policy':{'loaded':False,'status':'HELD_OUT','start':'2026-01-01'},'real_data_required':True,'synthetic_fallback':False,'research_timeframe':'M5','cost_profile':{'spread_pips':a.spread_pips,'slippage_pips':a.slippage_pips,'round_trip_cost_pips':2*(a.spread_pips+a.slippage_pips)}}
 Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(rep,indent=2,default=lambda x:float(x) if isinstance(x,np.floating) else x),encoding='utf-8');print(json.dumps({'candidate_total':len(res),'pre_oos_qualified':len(fin),'validation_qualified':len(q),'top_candidate':res[0]['candidate']}))
if __name__=='__main__':main()
