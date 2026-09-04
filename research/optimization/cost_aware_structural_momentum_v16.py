"""Structural Momentum Discovery v16.
Real EURUSD M5 only; 2022-2024 discovery, 2025 validation, 2026 held out.
Uses the v28.1 next-bar-open execution model and the unchanged strict gate.
Signal = momentum breakout conditioned by trend and volatility regime.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
import numpy as np,pandas as pd
from research.optimization.cost_aware_discovery_v15 import PRE_OOS_YEARS,MIN_TRADES_EACH_YEAR,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,MIN_PROFITABLE_YEARS,PRE_OOS_MAX_DD_PCT,VALIDATION_MIN_PF,VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES,_cost_price,_native
from research.optimization.multi_family_discovery import indicators
RISK_PCT=.005; MAX_HOLD_BARS=30; FAMILY='structural_momentum_v16'
def pf(m): return 3.0 if m.get('profit_factor')=='inf' else float(m.get('profit_factor',0.0))
def signal(d,p):
 s=pd.Series(0,index=d.index,dtype=int); trend=((d.ema_f>d.ema_s)&(d.ema_s>d.ema_t))|((d.ema_f<d.ema_s)&(d.ema_s<d.ema_t)); vol=(d.vol_ratio>=p['vol_min'])&(d.vol_ratio<=p['vol_max']); long=(d.mom>p['threshold'])&(d.Close>d.hh)&(d.ema_f>d.ema_s)&(d.Close>d.ema_t)&trend&vol&d.session; short=(d.mom<-p['threshold'])&(d.Close<d.ll)&(d.ema_f<d.ema_s)&(d.Close<d.ema_t)&trend&vol&d.session; s[long]=1; s[short]=-1; return s
def bt(df,p,spread=.5,slip=.2):
 if df.empty: return {'trades':0,'win_rate':0,'total_R':0,'expectancy_R':0,'profit_factor':0,'max_dd_pct':0,'entries':0,'exits':0,'open_position_end':False,'ohlc_invariants_passed':True,'execution_model':'v28.1_next_bar_open'}
 d=indicators(df,p); inv=(d.High>=d[['Open','Close']].max(axis=1))&(d.Low<=d[['Open','Close']].min(axis=1))&(d.High>=d.Low)
 if not bool(inv.all()): raise SystemExit('EXECUTION_INTEGRITY_FAIL: OHLC invariant')
 sig=signal(d,p).to_numpy(); op=d.Open.to_numpy(float); hi=d.High.to_numpy(float); lo=d.Low.to_numpy(float); cl=d.Close.to_numpy(float); atr=d.atr.to_numpy(float); cost=_cost_price(spread,slip); pos=0; entry=stop=tp=0.; ei=-1; rs=[]; entries=exits=0; eq=peak=10000.; dd=0.
 for i in range(1,len(d)):
  a=atr[i-1]
  if pos==0:
   q=sig[i-1]
   if q==0 or not np.isfinite(a) or a<=0: continue
   pos=int(q); entry=op[i]+(cost if pos==1 else -cost); sd=p['atr_stop']*a; stop=entry-pos*sd; tp=entry+pos*p['rr']*sd; ei=i; entries+=1; continue
  q=sig[i-1]; tr=None
  if pos==1:
   if lo[i]<=stop: tr=(stop-entry)/abs(entry-stop)
   elif hi[i]>=tp: tr=(tp-entry)/abs(entry-stop)
   elif q==-1: tr=(cl[i]-cost-entry)/abs(entry-stop)
   elif i-ei>=MAX_HOLD_BARS: tr=(cl[i]-cost-entry)/abs(entry-stop)
  else:
   if hi[i]>=stop: tr=(entry-stop)/abs(stop-entry)
   elif lo[i]<=tp: tr=(entry-tp)/abs(stop-entry)
   elif q==1: tr=(entry-(cl[i]+cost))/abs(stop-entry)
   elif i-ei>=MAX_HOLD_BARS: tr=(entry-(cl[i]+cost))/abs(stop-entry)
  if tr is not None:
   rs.append(float(tr)); pos=0; exits+=1; eq*=1+RISK_PCT*tr; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak)
 if pos:
  tr=(cl[-1]-cost-entry)/abs(entry-stop) if pos==1 else (entry-(cl[-1]+cost))/abs(stop-entry); rs.append(float(tr)); exits+=1; eq*=1+RISK_PCT*tr; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak); pos=0
 if entries!=exits or pos!=0: raise SystemExit(f'EXECUTION_INTEGRITY_FAIL entries={entries} exits={exits} pos={pos}')
 expected=10000.
 for x in rs: expected*=1+RISK_PCT*x
 if not np.isclose(eq,expected,rtol=1e-12,atol=1e-9): raise SystemExit('EXECUTION_INTEGRITY_FAIL equity')
 n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); f=gp/gl if gl else ('inf' if gp>0 else 0); total=sum(rs)
 return {'trades':n,'win_rate':round(100*wins/n,2) if n else 0,'total_R':round(total,2),'expectancy_R':round(total/n,4) if n else 0,'profit_factor':round(f,3) if f!='inf' and np.isfinite(f) else f,'max_dd_pct':round(dd*100,2),'final_equity':round(eq,2),'entries':entries,'exits':exits,'open_position_end':False,'ohlc_invariants_passed':True,'execution_model':'v28.1_next_bar_open','round_trip_cost_pips':2*(spread+slip)}
def catalog():
 base={'atr':14,'bb':20,'fast':13,'slow':89,'rsi':14,'trend':200}
 return [{**base,'mom':m,'threshold':t,'atr_stop':a,'rr':rr,'don':n,'vol_lookback':v,'vol_min':vmin,'vol_max':vmax} for m in (1,2,3) for t in (.001,.0015,.002) for a in (1.4,1.6,1.8) for rr in (1.75,2,2.25) for n in (2,3,4) for v in (10,20) for vmin,vmax in ((.8,2.0),(.9,2.5))]
def reasons(pre):
 b={x['year']:x['metrics'] for x in pre}; r=[]
 for y in PRE_OOS_YEARS:
  m=b[y]
  if m['trades']<MIN_TRADES_EACH_YEAR:r.append(f'trades<{MIN_TRADES_EACH_YEAR}:{y}')
  if pf(m)<MIN_PF_EACH_YEAR:r.append(f'pf<{MIN_PF_EACH_YEAR}:{y}')
  if m['expectancy_R']<=MIN_EXPECTANCY_R:r.append(f'expectancy<={MIN_EXPECTANCY_R}:{y}')
  if m['max_dd_pct']>PRE_OOS_MAX_DD_PCT:r.append(f'dd>{PRE_OOS_MAX_DD_PCT}:{y}')
 if sum(b[y]['expectancy_R']>0 for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS:r.append(f'profitable_years<{MIN_PROFITABLE_YEARS}')
 return r
def score(pre):
 p=[pf(x['metrics']) for x in pre]; e=[x['metrics']['expectancy_R'] for x in pre]; tr=[x['metrics']['trades'] for x in pre]; dd=[x['metrics']['max_dd_pct'] for x in pre]; return round(float(1.8*min(max(min(p),0),2)/2+np.mean(p)/2+2*np.tanh(sum(x['metrics']['total_R'] for x in pre)/150)+np.tanh(np.mean(e)*20)+.5*min(min(tr)/100,1)-2*min(max(max(dd),0),100)/100),6)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--output',required=True); ap.add_argument('--spread-pips',type=float,default=.5); ap.add_argument('--slippage-pips',type=float,default=.2); a=ap.parse_args(); df=pd.read_csv(a.data); df['timestamp']=pd.to_datetime(df['timestamp'],utc=True); df=df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index('timestamp').sort_index(); years={y:df[(df.index>=f'{y}-01-01')&(df.index<f'{y+1}-01-01')] for y in (2022,2023,2024,2025)}; out=[]
 for i,p in enumerate(catalog(),1):
  pre=[{'year':y,'metrics':bt(years[y],p,a.spread_pips,a.slippage_pips)} for y in PRE_OOS_YEARS]; rr=reasons(pre); out.append({'family':FAMILY,'candidate':i,'params':p,'cost_aware_robustness_score':score(pre),'pre_oos_gate':{'pass':not rr,'fail_closed':True},'pre_oos_cost_aware':pre,'pre_oos_rejection_reasons':rr})
 out.sort(key=lambda x:(-x['cost_aware_robustness_score'],x['candidate'])); finals=[x for x in out if x['pre_oos_gate']['pass']][:50]; vals=[]
 for x in finals:
  vm=bt(years[2025],x['params'],a.spread_pips,a.slippage_pips); vr=[]
  if pf(vm)<VALIDATION_MIN_PF:vr.append(f'validation_pf<{VALIDATION_MIN_PF}')
  if vm['max_dd_pct']>VALIDATION_MAX_DD_PCT:vr.append(f'validation_dd>{VALIDATION_MAX_DD_PCT}')
  if vm['trades']<VALIDATION_MIN_TRADES:vr.append(f'validation_trades<{VALIDATION_MIN_TRADES}')
  vals.append({**x,'validation_2025_cost_aware':vm,'validation_qualifies':not vr,'validation_rejection_reasons':vr})
 q=[x for x in vals if x['validation_qualifies']]; report={'schema_version':'forexai.cost_aware_structural_momentum.v16','result':{'family':FAMILY,'candidate_total':len(out),'qualified_count':len(q),'champion':q[0] if q else None,'candidate_pool':q[:20],'top_20_diagnostics':out[:20],'validated_pre_oos_finalists':vals,'execution_model':'v28.1_next_bar_open'},'research_timeframe':'M5','real_data_required':True,'synthetic_fallback':False,'oos_policy':{'loaded':False,'start':'2026-01-01','status':'HELD_OUT'},'execution_model':{'name':'v28.1_next_bar_open','round_trip_cost_pips':2*(a.spread_pips+a.slippage_pips),'sl_first':True,'max_hold_bars':MAX_HOLD_BARS,'opposite_signal_exit':True,'one_position_at_a_time':True}}; Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(_native(report),indent=2),encoding='utf-8'); print(json.dumps({'candidate_total':len(out),'qualified_count':len(q),'top_candidate':out[0]['candidate'] if out else None}))
if __name__=='__main__': main()
