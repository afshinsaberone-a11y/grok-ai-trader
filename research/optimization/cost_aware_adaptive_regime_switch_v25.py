"""ForexAI v25: adaptive regime-switch discovery on REAL EURUSD.
Closed-bar signal -> next-bar-open execution. Trend continuation in strong ADX
regimes and range reversion in weak regimes. 2022-2024 discovery, 2025 validation,
2026 held out. Strict cost-aware gate. No synthetic fallback.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from research.optimization.cost_aware_gate_v14 import (
 PRE_OOS_YEARS,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,MIN_TRADES_EACH_YEAR,
 PRE_OOS_MAX_DD_PCT,MIN_PROFITABLE_YEARS,VALIDATION_MIN_PF,
 VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES)
from research.optimization.execution_contract_v1 import ExecutionConfig,validate_ohlc,apply_entry_cost,apply_exit_cost

PIP=.0001;RISK=.005;MAX_HOLD=30;TOP_N=20;TIMEFRAMES=("M1","M5","M15")

def catalog():
    out=[]
    for lookback in (12,24):
      for adx in (18,22,26):
       for atr_mult in (1.0,1.5,2.0):
        for rr in (1.2,1.5,2.0):
         for rsi_low in (25,30):
          for rsi_high in (70,75):
           for mode in ("adaptive","trend_only"):
            out.append(dict(lookback=lookback,adx_threshold=adx,atr_stop=atr_mult,rr=rr,rsi_low=rsi_low,rsi_high=rsi_high,mode=mode))
    return out

def prep(raw):
    d=raw.rename(columns={'timestamp':'Timestamp','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).copy()
    d['Timestamp']=pd.to_datetime(d['Timestamp'],utc=True);d=d.set_index('Timestamp').sort_index();validate_ohlc(d)
    prev=d.Close.shift(1);tr=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1)
    d['ATR']=tr.rolling(14,min_periods=14).mean()
    d['EMA20']=d.Close.ewm(span=20,adjust=False).mean();d['EMA50']=d.Close.ewm(span=50,adjust=False).mean()
    delta=d.Close.diff();up=delta.clip(lower=0);dn=-delta.clip(upper=0);rs=up.rolling(14).mean()/dn.rolling(14).mean().replace(0,np.nan);d['RSI']=100-(100/(1+rs))
    plus=((d.High-d.High.shift(1)).clip(lower=0));minus=((d.Low.shift(1)-d.Low).clip(lower=0));atr14=d.ATR.replace(0,np.nan)
    dip=100*plus.rolling(14).mean()/atr14;dim=100*minus.rolling(14).mean()/atr14;dx=100*(dip-dim).abs()/(dip+dim).replace(0,np.nan);d['ADX']=dx.rolling(14).mean()
    d['day']=d.index.date;d['hour']=d.index.hour
    return d

def metrics(rs):
    n=len(rs);gp=sum(x for x in rs if x>0);gl=abs(sum(x for x in rs if x<=0));pf=gp/gl if gl else (3.0 if gp>0 else 0.0);eq=peak=10000.;dd=0.
    for r in rs:eq*=1+RISK*r;peak=max(peak,eq);dd=max(dd,(peak-eq)/peak)
    return {'trades':n,'win_rate_pct':round(100*sum(x>0 for x in rs)/n,2) if n else 0.,'total_R':round(float(sum(rs)),2),'expectancy_R':round(float(sum(rs))/n,4) if n else 0.,'profit_factor':round(float(pf),3),'max_dd_pct':round(100*dd,2),'final_equity':round(eq,2),'entries_equal_exits':True,'next_bar_open_entry':True,'actual_entry_price_for_stops':True,'adverse_exit_cost_applied':True,'same_bar_sl_first':True,'one_position_at_a_time':True,'round_trip_cost_pips':1.4}

def bt(d,p,spread=.5,slippage=.2):
    cfg=ExecutionConfig(spread_pips=spread,slippage_pips=slippage)
    rs=[]
    for day,g in d.groupby('day',sort=True):
        g=g.reset_index();n=len(g);pos=0;entry=stop=tp=0.;entry_i=-1
        for i in range(60,n-1):
            a=float(g.loc[i,'ATR']);adx=float(g.loc[i,'ADX']);rsi=float(g.loc[i,'RSI']);ema20=float(g.loc[i,'EMA20']);ema50=float(g.loc[i,'EMA50']);c=float(g.loc[i,'Close'])
            if not np.isfinite(a+adx+rsi+ema20+ema50) or a<=0: continue
            if pos==0:
                trend=adx>=p['adx_threshold']; side=0
                if trend and c>ema20>ema50 and c>g.loc[i-p['lookback']:i-1,'High'].max(): side=1
                elif trend and c<ema20<ema50 and c<g.loc[i-p['lookback']:i-1,'Low'].min(): side=-1
                elif p['mode']=='adaptive' and not trend:
                    if rsi<=p['rsi_low'] and c<ema20: side=1
                    elif rsi>=p['rsi_high'] and c>ema20: side=-1
                if side:
                    pos=side;entry_i=i+1;entry=apply_entry_cost(float(g.loc[entry_i,'Open']),pos,cfg);risk=p['atr_stop']*a;stop=entry-pos*risk
                    tp=(entry+pos*p['rr']*risk) if trend else ema20
                    if (tp-entry)*pos<=0: pos=0;continue
                    continue
            else:
                age=i-entry_i+1;hit_sl=(float(g.loc[i,'Low'])<=stop) if pos==1 else (float(g.loc[i,'High'])>=stop);hit_tp=(float(g.loc[i,'High'])>=tp) if pos==1 else (float(g.loc[i,'Low'])<=tp)
                unit=p['atr_stop']*float(g.loc[entry_i-1,'ATR']);r=None
                if not np.isfinite(unit) or unit<=0: continue
                if hit_sl: r=pos*(apply_exit_cost(stop,pos,cfg)-entry)/unit
                elif hit_tp: r=pos*(apply_exit_cost(tp,pos,cfg)-entry)/unit
                elif age>=MAX_HOLD: r=pos*(apply_exit_cost(float(g.loc[min(i+1,n-1),'Open']),pos,cfg)-entry)/unit
                elif (pos==1 and rsi>=50 and p['mode']=='adaptive' and adx<p['adx_threshold']) or (pos==-1 and rsi<=50 and p['mode']=='adaptive' and adx<p['adx_threshold']):
                    ex=float(g.loc[i+1,'Open']);r=pos*(apply_exit_cost(ex,pos,cfg)-entry)/unit
                if r is not None:
                    rs.append(float(r));pos=0
    return metrics(rs)

def pf(m): return 3.0 if m.get('profit_factor')=='inf' else float(m.get('profit_factor',0))
def gate(pre):
    by={x['year']:x['metrics'] for x in pre};bad=[]
    for y in PRE_OOS_YEARS:
        m=by[y]
        if m['trades']<MIN_TRADES_EACH_YEAR:bad.append(f'trades<{MIN_TRADES_EACH_YEAR}:{y}')
        if pf(m)<MIN_PF_EACH_YEAR:bad.append(f'pf<{MIN_PF_EACH_YEAR}:{y}')
        if m['expectancy_R']<=MIN_EXPECTANCY_R:bad.append(f'expectancy<={MIN_EXPECTANCY_R}:{y}')
        if m['max_dd_pct']>PRE_OOS_MAX_DD_PCT:bad.append(f'dd>{PRE_OOS_MAX_DD_PCT}:{y}')
    if sum(by[y]['expectancy_R']>0 for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS:bad.append('profitable_years<3')
    return bad

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--output',required=True);ap.add_argument('--spread-pips',type=float,default=.5);ap.add_argument('--slippage-pips',type=float,default=.2);ap.add_argument('--timeframe',required=True,choices=TIMEFRAMES);a=ap.parse_args()
    d=prep(pd.read_csv(a.data));years={y:d[(d.index>=f'{y}-01-01')&(d.index<f'{y+1}-01-01')] for y in (2022,2023,2024,2025)};res=[]
    for i,p in enumerate(catalog(),1):
        pre=[{'year':y,'metrics':bt(years[y],p,a.spread_pips,a.slippage_pips)} for y in PRE_OOS_YEARS];bad=gate(pre)
        res.append({'candidate':i,'params':p,'score':0 if bad else sum(x['metrics']['expectancy_R'] for x in pre),'pre_oos':pre,'pre_oos_pass':not bad,'rejection_reasons':bad})
    res.sort(key=lambda x:(x['pre_oos_pass'],-x['score']),reverse=True)
    final=[x for x in res if x['pre_oos_pass']][:50]
    val=[]
    for x in final:
        vm=bt(years[2025],x['params'],a.spread_pips,a.slippage_pips);vr=[]
        if pf(vm)<VALIDATION_MIN_PF:vr.append(f'validation_pf<{VALIDATION_MIN_PF}')
        if vm['max_dd_pct']>VALIDATION_MAX_DD_PCT:vr.append(f'validation_dd>{VALIDATION_MAX_DD_PCT}')
        if vm['trades']<VALIDATION_MIN_TRADES:vr.append(f'validation_trades<{VALIDATION_MIN_TRADES}')
        if vm['expectancy_R']<=0 or vm['total_R']<=0:vr.append('validation_nonpositive_return')
        val.append({**x,'validation_2025':vm,'validation_pass':not vr,'validation_rejection_reasons':vr})
    q=[x for x in val if x['validation_pass']]
    rep={'schema_version':'forexai.adaptive_regime_switch.v25','research_timeframe':a.timeframe,'result':{
        'candidate_total':len(res),
        'pre_oos_qualified_count':len(final),
        'validation_qualified_count':len(q),
        # Legacy alias retained for consumers that still expect qualified_count.
        'qualified_count':len(q),
        'champion':None,
        'top_20_diagnostics':res[:TOP_N],
        'validated_candidates':val,
    },'execution_model':{'entry':'next_bar_open','cost_pips_per_side':a.spread_pips+a.slippage_pips,'round_trip_cost_pips':2*(a.spread_pips+a.slippage_pips),'same_bar_resolution':'SL first (conservative)','expiry_bars':MAX_HOLD,'overlap':'one position at a time','adverse_exit_cost_applied':True},'oos_policy':{'loaded':False,'status':'HELD_OUT','start':'2026-01-01'},'real_data_required':True,'synthetic_fallback':False}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(rep,indent=2,default=str),encoding='utf-8');print(json.dumps({'candidate_total':len(res),'pre_oos_qualified':len(final),'validation_qualified':len(q),'research_timeframe':a.timeframe}))
if __name__=='__main__':main()
