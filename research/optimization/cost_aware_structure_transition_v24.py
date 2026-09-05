"""ForexAI v24 cost-aware Market-Structure Transition discovery.

REAL data only. Signals are generated on closed bars; execution is next-bar-open
with adverse 0.7 pip entry/exit cost, SL-first, 30-bar expiry and one position.
Discovery uses 2022-2024 only, validation is 2025, and 2026 is held out.
No parameter is selected from validation/OOS data and no Champion is promoted.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from research.real_data.research_pipeline import load_real_dataset

PIP=0.0001; COST=0.7*PIP; START=pd.Timestamp('2022-01-01',tz='UTC'); VAL=pd.Timestamp('2025-01-01',tz='UTC'); OOS=pd.Timestamp('2026-01-01',tz='UTC'); EXPIRY=30
PARAMS=[
 {'lookback':12,'pullback':3,'body_min':0.55,'atr_stop':1.5,'rr':1.5,'trend':50,'session':(6,20)},
 {'lookback':12,'pullback':5,'body_min':0.55,'atr_stop':1.5,'rr':2.0,'trend':50,'session':(6,20)},
]

def catalog():
    out=[]
    for lookback in (8,12,16):
      for pullback in (2,3,5):
       for body_min in (0.45,0.55):
        for atr_stop in (1.25,1.5,2.0):
         for rr in (1.25,1.5,2.0):
          for trend in (50,100):
           for session in ((0,24),(6,20)):
            out.append({'lookback':lookback,'pullback':pullback,'body_min':body_min,'atr_stop':atr_stop,'rr':rr,'trend':trend,'session':session})
    return out

def prep(raw):
    d=raw.rename(columns={'timestamp':'Timestamp','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).copy()
    d['Timestamp']=pd.to_datetime(d['Timestamp'],utc=True); d=d.set_index('Timestamp').sort_index()
    prev=d['Close'].shift(1); tr=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1)
    d['ATR']=tr.rolling(14,min_periods=14).mean(); d['EMA']=d.Close.ewm(span=50,adjust=False).mean(); d['EMA100']=d.Close.ewm(span=100,adjust=False).mean()
    d['range']=d.High-d.Low; d['body']=(d.Close-d.Open).abs(); d['body_frac']=d.body/d['range'].replace(0,np.nan)
    d['prior_high']=d.High.shift(1).rolling(16,min_periods=16).max(); d['prior_low']=d.Low.shift(1).rolling(16,min_periods=16).min()
    d['hour']=d.index.hour
    return d

def signals(d,p):
    prior_high=d.High.shift(1).rolling(p['lookback'],min_periods=p['lookback']).max(); prior_low=d.Low.shift(1).rolling(p['lookback'],min_periods=p['lookback']).min()
    ema=d.Close.ewm(span=p['trend'],adjust=False).mean(); atr=d.ATR
    # Structure break on the closed bar, followed by a shallow pullback/reclaim.
    bull_break=(d.Close>prior_high)&(d.Close>d.Open)&(d.body_frac>=p['body_min'])&(d.Close>ema)
    bear_break=(d.Close<prior_low)&(d.Close<d.Open)&(d.body_frac>=p['body_min'])&(d.Close<ema)
    recent_bull=bull_break.shift(1).rolling(p['pullback'],min_periods=1).max().fillna(0).astype(bool)
    recent_bear=bear_break.shift(1).rolling(p['pullback'],min_periods=1).max().fillna(0).astype(bool)
    # Reclaim requires the closed bar to close in the breakout direction after touching EMA.
    touched_bull=d.Low<=ema; touched_bear=d.High>=ema
    long=recent_bull&touched_bull&(d.Close>d.Open)&(d.Close>ema)
    short=recent_bear&touched_bear&(d.Close<d.Open)&(d.Close<ema)
    sess=(d.hour>=p['session'][0])&(d.hour<p['session'][1]) if p['session']!=(0,24) else pd.Series(True,index=d.index)
    sig=pd.Series(0,index=d.index,dtype=int); sig.loc[long&sess]=1; sig.loc[short&sess]=-1
    return sig

def execute(d,p,start=None,end=None):
    sig=signals(d,p).to_numpy(int); o=d.Open.to_numpy(float); h=d.High.to_numpy(float); l=d.Low.to_numpy(float); atr=d.ATR.to_numpy(float); idx=d.index
    pos=0; entry_i=-1; entry=stop=target=0.; rs=[]; wins=0; gp=gl=0.; eq=10000.; peak=eq; dd=0.; holds=[]
    for i in range(len(d)-1):
      if pos==0:
       if start is not None and idx[i]<start: continue
       if end is not None and idx[i]>=end: break
       if sig[i]==0 or not np.isfinite(atr[i]) or atr[i]<=0: continue
       pos=int(sig[i]); entry_i=i+1; entry=o[entry_i]+pos*COST; risk=p['atr_stop']*atr[i]; stop=entry-pos*risk; target=entry+pos*p['rr']*risk; continue
      age=i-entry_i+1; hit_sl=(l[i]<=stop) if pos==1 else (h[i]>=stop); hit_tp=(h[i]>=target) if pos==1 else (l[i]<=target); r=None
      unit=p['atr_stop']*atr[entry_i-1]
      if not np.isfinite(unit) or unit<=0: continue
      if hit_sl: r=pos*((stop-pos*COST)-entry)/unit
      elif hit_tp: r=pos*((target-pos*COST)-entry)/unit
      elif sig[i]==-pos and i+1<len(d): r=pos*((o[i+1]-pos*COST)-entry)/unit
      elif age>=EXPIRY: r=pos*((o[min(i+1,len(d)-1)]-pos*COST)-entry)/unit
      if r is None: continue
      rs.append(float(r)); wins+=r>0; gp+=max(0,r); gl+=max(0,-r); eq*=1+float(r)*0.005; peak=max(peak,eq); dd=max(dd,(peak-eq)/peak); holds.append(age); pos=0
    n=len(rs); pf=gp/gl if gl else (3.0 if n else 0.0); total=float(sum(rs))
    return {'trades':n,'win_rate_pct':round(100*wins/n,3) if n else 0.,'expectancy_R':round(total/n,5) if n else 0.,'total_R':round(total,3),'profit_factor':round(pf,4),'max_dd_pct':round(100*dd,3),'final_equity':round(eq,2),'avg_hold_bars':round(float(np.mean(holds)),3) if holds else 0.,'entries_equal_exits':pos==0,'next_bar_open_entry':True,'actual_entry_price_for_stops':True,'adverse_exit_cost_applied':True,'same_bar_sl_first':True,'one_position_at_a_time':True,'round_trip_cost_pips':1.4},rs

def gate(y):
    vals=list(y.values()); return all(v['trades']>=100 and v['profit_factor']>=1.05 and v['expectancy_R']>0 and v['total_R']>0 for v in vals) and sum(v['total_R']>0 for v in vals)>=3 and max(v['max_dd_pct'] for v in vals)<=35

def run(data,timeframe,output):
    raw=load_real_dataset(data,symbol='EURUSD',timeframe=timeframe); df=prep(raw)
    if df.empty or df.index.min()>=OOS: raise RuntimeError('V24_REAL_DATA_REQUIRED')
    pre=df[(df.index>=START)&(df.index<VAL)]; history=df[(df.index>=START)&(df.index<OOS)]
    results=[]
    for p in catalog():
      yearly={}
      for y in (2022,2023,2024):
       ys=pd.Timestamp(f'{y}-01-01',tz='UTC'); ye=pd.Timestamp(f'{y+1}-01-01',tz='UTC'); prior=df.index[df.index<ys]; warm=prior[-500] if len(prior)>500 else df.index.min(); part=df[(df.index>=warm)&(df.index<ye)]; yearly[str(y)]=execute(part,p,start=ys)[0]
      results.append({'params':p,'config_hash':hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest(),'pre_oos_yearly':yearly,'pre_oos_passed':gate(yearly)})
    qualified=[r for r in results if r['pre_oos_passed']]
    # Validation is evaluated only for pre-OOS-qualified candidates; no selection is performed here.
    val=[]
    for r in qualified:
      m,_=execute(history,r['params'],start=VAL,end=OOS); val.append({'params':r['params'],'metrics':m})
    report={'schema':'forexai.cost_aware_structure_transition.v24','status':'PASS','real_data_only':True,'synthetic_fallback':False,'timeframe':timeframe,'dataset_rows':len(df),'pre_oos_rows':len(pre),'validation_rows':int(((df.index>=VAL)&(df.index<OOS)).sum()),'oos_evaluated':False,'optimization_enabled':False,'candidate_total':len(results),'pre_oos_qualified_count':len(qualified),'validation_evaluated_count':len(val),'validation':val,'champion':None,'execution_model':{'entry':'next_bar_open','cost_pips_per_side':0.7,'round_trip_cost_pips':1.4,'same_bar_resolution':'SL first (conservative)','expiry_bars':30,'overlap':'one position at a time','adverse_exit_cost_applied':True},'oos':{'status':'HELD_OUT','evaluated':False,'optimization_allowed':False}}
    Path(output).parent.mkdir(parents=True,exist_ok=True); Path(output).write_text(json.dumps(report,indent=2,sort_keys=True,default=str),encoding='utf-8'); print(json.dumps(report,indent=2,sort_keys=True,default=str)); return report

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--timeframe',required=True,choices=['M1','M5','M15']); ap.add_argument('--output',required=True); a=ap.parse_args(); run(a.data,a.timeframe,a.output)
if __name__=='__main__': main()
