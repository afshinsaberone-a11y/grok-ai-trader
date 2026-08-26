"""Cost-aware discovery on real pre-OOS data only.

Uses strict gate v7. 2022-2024 are discovery years; 2025 is validation;
2026 is held out. No synthetic fallback.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Any
import numpy as np,pandas as pd
from research.optimization.multi_family_discovery import FAMILIES,_native,catalog,indicators,signal_family
from research.optimization.cost_aware_gate_v7 import PRE_OOS_YEARS,MIN_PROFITABLE_YEARS,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,MIN_TRADES_EACH_YEAR,PRE_OOS_MAX_DD_PCT,VALIDATION_MIN_PF,VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES,candidate_gate,pre_oos_gate
PIP_SIZE=.0001; DEFAULT_SPREAD_PIPS=.5; DEFAULT_SLIPPAGE_PIPS=.2; RISK_PCT=.005

def round_trip_cost_price(spread_pips:float,slippage_pips:float)->float:
    if spread_pips<0 or slippage_pips<0: raise ValueError('execution costs cannot be negative')
    return 2*(float(spread_pips)+float(slippage_pips))*PIP_SIZE

def backtest_cost_aware(df:pd.DataFrame,family:str,params:dict[str,Any],*,spread_pips=DEFAULT_SPREAD_PIPS,slippage_pips=DEFAULT_SLIPPAGE_PIPS)->dict[str,Any]:
    d=indicators(df,params); sig=signal_family(d,family,params); close=d['Close'].to_numpy(float,copy=False); high=d['High'].to_numpy(float,copy=False); low=d['Low'].to_numpy(float,copy=False); atr=d['atr'].to_numpy(float,copy=False); signals=sig.to_numpy(copy=False); equity=peak=10000.; maxdd=0.; pos=0; entry=stop=tp=0.; rs=[]; cost=round_trip_cost_price(spread_pips,slippage_pips)
    for i in range(1,len(d)):
        a=atr[i]
        if not np.isfinite(a) or a<=0: continue
        s=signals[i]
        if pos==0 and s!=0: pos=int(s); entry=close[i]; sd=params['atr_stop']*a; stop=entry-pos*sd; tp=entry+pos*params['rr']*sd; continue
        if pos==1 and (low[i]<=stop or high[i]>=tp or s==-1):
            ex=stop if low[i]<=stop else (tp if high[i]>=tp else close[i]); rs.append((ex-entry)/abs(entry-stop)-cost/abs(entry-stop)); equity*=1+RISK_PCT*rs[-1]; pos=0
        elif pos==-1 and (high[i]>=stop or low[i]<=tp or s==1):
            ex=stop if high[i]>=stop else (tp if low[i]<=tp else close[i]); rs.append((entry-ex)/abs(stop-entry)-cost/abs(stop-entry)); equity*=1+RISK_PCT*rs[-1]; pos=0
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else ('inf' if gp>0 else 0.)
    return {'trades':n,'win_rate':round(100*wins/n,2) if n else 0.,'total_R':round(sum(rs),2),'expectancy_R':round(sum(rs)/n,4) if n else 0.,'profit_factor':round(pf,3) if pf!='inf' and np.isfinite(pf) else pf,'max_dd_pct':round(100*maxdd,2),'final_equity':round(equity,2),'spread_pips':float(spread_pips),'slippage_pips':float(slippage_pips),'round_trip_cost_pips':round(2*(spread_pips+slippage_pips),4)}

def _pf(m): return 3.0 if m['profit_factor']=='inf' else float(m['profit_factor'])
def score_cost_aware(metrics):
    if not pre_oos_gate(metrics): return -999.0
    pfs=[_pf(x['metrics']) for x in metrics]; ex=[float(x['metrics']['expectancy_R']) for x in metrics]; dd=[float(x['metrics']['max_dd_pct']) for x in metrics]; avg=sum(pfs)/3; total=sum(float(x['metrics']['total_R']) for x in metrics)
    return round(2.5*min(max(min(pfs),0),2)/2+1.5*min(max(avg,0),2)/2+sum(v>0 for v in ex)/3+1.5*np.tanh(total/150)-2.5*min(max(max(dd),0),100)/100,6)

def discover_family_cost_aware(df,family,*,spread_pips,slippage_pips):
    years={y:df[(df.index>=f'{y}-01-01')&(df.index<f'{y+1}-01-01')] for y in (2022,2023,2024,2025)}; results=[]
    for j,params in enumerate(catalog()[family]):
        pre=[{'year':y,'metrics':backtest_cost_aware(years[y],family,params,spread_pips=spread_pips,slippage_pips=slippage_pips)} for y in PRE_OOS_YEARS]; gate=pre_oos_gate(pre)
        results.append({'family':family,'candidate':j+1,'params':params,'cost_aware_robustness_score':score_cost_aware(pre),'pre_oos_gate':{'pass':gate,'years':list(PRE_OOS_YEARS),'min_trades_each_year':MIN_TRADES_EACH_YEAR,'min_pf_each_year':MIN_PF_EACH_YEAR,'min_profitable_years':MIN_PROFITABLE_YEARS,'min_expectancy_R':MIN_EXPECTANCY_R,'max_dd_pct':PRE_OOS_MAX_DD_PCT},'pre_oos_cost_aware':pre})
    results.sort(key=lambda x:(-x['cost_aware_robustness_score'],x['candidate'])); finalists=[x for x in results if x['pre_oos_gate']['pass']][:50]; validated=[]
    for x in finalists:
        vm=backtest_cost_aware(years[2025],family,x['params'],spread_pips=spread_pips,slippage_pips=slippage_pips); validated.append({**x,'validation_2025_cost_aware':vm,'validation_qualifies':candidate_gate(x['pre_oos_cost_aware'],vm)})
    qualified=[x for x in validated if x['validation_qualifies']]; qualified.sort(key=lambda x:(-x['cost_aware_robustness_score'],x['candidate']))
    return {'family':family,'candidate_total':len(results),'cost_profile':{'spread_pips':spread_pips,'slippage_pips':slippage_pips,'round_trip_cost_pips':2*(spread_pips+slippage_pips)},'qualified_count':len(qualified),'champion':qualified[0] if qualified else None,'top_50':validated}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--family',choices=FAMILIES,required=True); ap.add_argument('--output',default='artifacts/cost_aware_family.json'); ap.add_argument('--spread-pips',type=float,default=DEFAULT_SPREAD_PIPS); ap.add_argument('--slippage-pips',type=float,default=DEFAULT_SLIPPAGE_PIPS); a=ap.parse_args()
    if a.spread_pips<0 or a.slippage_pips<0: raise SystemExit('execution costs cannot be negative')
    df=pd.read_csv(a.data); df['timestamp']=pd.to_datetime(df['timestamp'],utc=True); df=df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index('timestamp'); result=discover_family_cost_aware(df,a.family,spread_pips=a.spread_pips,slippage_pips=a.slippage_pips)
    report={'schema_version':'forexai.cost_aware_discovery.v10','result':result,'oos_policy':{'loaded':False,'start':'2026-01-01','status':'HELD_OUT'},'real_data_required':True,'synthetic_fallback':False,'gate_policy':{'pre_oos_years':list(PRE_OOS_YEARS),'pre_oos_min_profitable_years':MIN_PROFITABLE_YEARS,'pre_oos_min_pf_each_year':MIN_PF_EACH_YEAR,'pre_oos_min_expectancy_R':MIN_EXPECTANCY_R,'pre_oos_min_trades_each_year':MIN_TRADES_EACH_YEAR,'pre_oos_max_dd_pct':PRE_OOS_MAX_DD_PCT,'validation_min_pf':VALIDATION_MIN_PF,'validation_max_dd_pct':VALIDATION_MAX_DD_PCT,'validation_min_trades':VALIDATION_MIN_TRADES,'fail_closed':True}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(_native(report),indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(_native({'family':a.family,'qualified_count':result['qualified_count'],'champion':result['champion'],'cost_profile':result['cost_profile']}),indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
