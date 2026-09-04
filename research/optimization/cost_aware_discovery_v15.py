"""Cost-aware multi-family discovery v15.1 diagnostics.

Real pre-OOS data only. Uses the v28.1/v29.1 execution model:
next-bar-open entry, adverse entry/exit costs, SL-first ambiguity,
30-bar expiry, opposite-signal exit, one position at a time.
2022-2024 are discovery years, 2025 validation, 2026 held out.

v15.1 keeps the strict fail-closed promotion gate, but also preserves
transparent diagnostics for the strongest rejected candidates so that a
zero-qualified run is actionable rather than opaque.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np,pandas as pd
from research.optimization.multi_family_discovery import FAMILIES,_native,catalog,indicators,signal_family
from research.optimization.cost_aware_gate_v14 import (PRE_OOS_YEARS,MIN_PROFITABLE_YEARS,MIN_PF_EACH_YEAR,MIN_EXPECTANCY_R,MIN_TRADES_EACH_YEAR,PRE_OOS_MAX_DD_PCT,VALIDATION_MIN_PF,VALIDATION_MAX_DD_PCT,VALIDATION_MIN_TRADES,pre_oos_gate)
PIP_SIZE=.0001
RISK_PCT=.005
MAX_HOLD_BARS=30
DIAGNOSTIC_TOP_N=20


def _cost_price(spread_pips: float, slippage_pips: float) -> float:
    if spread_pips < 0 or slippage_pips < 0:
        raise ValueError("execution costs cannot be negative")
    return (float(spread_pips)+float(slippage_pips))*PIP_SIZE


def backtest_execution_equivalent(df: pd.DataFrame, family: str, params: dict[str, Any], *, spread_pips=.5, slippage_pips=.2) -> dict[str, Any]:
    if df.empty:
        return {'trades':0,'win_rate':0.0,'total_R':0.0,'expectancy_R':0.0,'profit_factor':0.0,'max_dd_pct':0.0,'final_equity':10000.0}
    d=indicators(df,params)
    sig=signal_family(d,family,params).to_numpy(copy=False)
    op=d['Open'].to_numpy(float,copy=False); hi=d['High'].to_numpy(float,copy=False); lo=d['Low'].to_numpy(float,copy=False); cl=d['Close'].to_numpy(float,copy=False); atr=d['atr'].to_numpy(float,copy=False)
    adverse=_cost_price(spread_pips,slippage_pips)
    equity=peak=10000.0; maxdd=0.0; pos=0; entry=stop=tp=0.0; entry_i=-1; rs=[]
    for i in range(1,len(d)):
        a=atr[i-1]
        if pos==0:
            s=sig[i-1]
            if s==0 or not np.isfinite(a) or a<=0:
                continue
            pos=int(s)
            entry_raw=op[i]
            entry=entry_raw + (adverse if pos==1 else -adverse)
            sd=float(params['atr_stop'])*a
            stop=entry-pos*sd
            tp=entry+pos*float(params['rr'])*sd
            entry_i=i
            continue
        s=sig[i-1]
        exit_price=None
        if pos==1:
            if lo[i] <= stop and hi[i] >= tp: exit_price=stop
            elif lo[i] <= stop: exit_price=stop
            elif hi[i] >= tp: exit_price=tp
            elif s==-1: exit_price=cl[i] - adverse
            elif i-entry_i >= MAX_HOLD_BARS: exit_price=cl[i] - adverse
            if exit_price is not None:
                rs.append((exit_price-entry)/abs(entry-stop)); pos=0
        else:
            if hi[i] >= stop and lo[i] <= tp: exit_price=stop
            elif hi[i] >= stop: exit_price=stop
            elif lo[i] <= tp: exit_price=tp
            elif s==1: exit_price=cl[i] + adverse
            elif i-entry_i >= MAX_HOLD_BARS: exit_price=cl[i] + adverse
            if exit_price is not None:
                rs.append((entry-exit_price)/abs(stop-entry)); pos=0
        if rs:
            equity*=1+RISK_PCT*rs[-1]
            peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    if pos:
        exit_price=cl[-1] - adverse if pos==1 else cl[-1] + adverse
        rs.append((exit_price-entry)/abs(entry-stop) if pos==1 else (entry-exit_price)/abs(stop-entry))
        equity*=1+RISK_PCT*rs[-1]
        peak=max(peak,equity); maxdd=max(maxdd,(peak-equity)/peak)
    n=len(rs); wins=sum(x>0 for x in rs); gp=sum(x for x in rs if x>0); gl=abs(sum(x for x in rs if x<=0)); pf=gp/gl if gl else ('inf' if gp>0 else 0.0)
    return {'trades':n,'win_rate':round(100*wins/n,2) if n else 0.0,'total_R':round(float(sum(rs)),2),'expectancy_R':round(float(sum(rs))/n,4) if n else 0.0,'profit_factor':round(float(pf),3) if pf!='inf' and np.isfinite(pf) else pf,'max_dd_pct':round(100*maxdd,2),'final_equity':round(equity,2),'spread_pips':float(spread_pips),'slippage_pips':float(slippage_pips),'round_trip_cost_pips':round(2*(spread_pips+slippage_pips),4),'execution_model':'v28.1_next_bar_open'}


def _pf(m): return 3.0 if m.get('profit_factor')=='inf' else float(m.get('profit_factor',0.0))


def _pre_reasons(pre):
    by={int(x['year']):x['metrics'] for x in pre}; reasons=[]
    for y in PRE_OOS_YEARS:
        m=by[y]
        if int(m.get('trades',0))<MIN_TRADES_EACH_YEAR: reasons.append(f'trades<{MIN_TRADES_EACH_YEAR}:{y}')
        if _pf(m)<MIN_PF_EACH_YEAR: reasons.append(f'pf<{MIN_PF_EACH_YEAR}:{y}')
        if float(m.get('max_dd_pct',100))>PRE_OOS_MAX_DD_PCT: reasons.append(f'dd>{PRE_OOS_MAX_DD_PCT}:{y}')
        if float(m.get('expectancy_R',0))<=MIN_EXPECTANCY_R: reasons.append(f'expectancy<={MIN_EXPECTANCY_R}:{y}')
    if sum(float(by[y].get('expectancy_R',0))>MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)<MIN_PROFITABLE_YEARS: reasons.append(f'profitable_years<{MIN_PROFITABLE_YEARS}')
    return reasons


def _score(pre):
    """Diagnostic score for ranking even rejected candidates.

    This score is never a promotion gate. It is intentionally continuous so
    rejected candidates can be inspected and compared instead of all receiving
    the same sentinel score.
    """
    pfs=[_pf(x['metrics']) for x in pre]
    exps=[float(x['metrics'].get('expectancy_R',0.0)) for x in pre]
    totals=[float(x['metrics'].get('total_R',0.0)) for x in pre]
    dds=[float(x['metrics'].get('max_dd_pct',100.0)) for x in pre]
    trades=[int(x['metrics'].get('trades',0)) for x in pre]
    min_pf=min(pfs); mean_pf=float(np.mean(pfs)); mean_exp=float(np.mean(exps)); total_r=float(sum(totals)); worst_dd=max(dds)
    trade_factor=min(float(min(trades))/MIN_TRADES_EACH_YEAR,1.0)
    # Transparent diagnostic only: reward profitability/consistency and penalize DD.
    score=(1.8*min(max(min_pf,0.0),2.0)/2.0 + 1.0*min(max(mean_pf,0.0),2.0)/2.0 + 2.0*np.tanh(total_r/150.0) + 1.0*np.tanh(mean_exp*20.0) + 0.5*trade_factor - 2.0*min(max(worst_dd,0.0),100.0)/100.0)
    return round(float(score),6)


def _diagnostic_snapshot(pre):
    by={int(x['year']):x['metrics'] for x in pre}
    return {
        'years': {str(y): by[y] for y in PRE_OOS_YEARS},
        'aggregate': {
            'total_R': round(sum(float(by[y].get('total_R',0.0)) for y in PRE_OOS_YEARS),2),
            'mean_expectancy_R': round(float(np.mean([float(by[y].get('expectancy_R',0.0)) for y in PRE_OOS_YEARS])),4),
            'mean_profit_factor': round(float(np.mean([_pf(by[y]) for y in PRE_OOS_YEARS])),3),
            'min_profit_factor': round(min(_pf(by[y]) for y in PRE_OOS_YEARS),3),
            'max_drawdown_pct': round(max(float(by[y].get('max_dd_pct',100.0)) for y in PRE_OOS_YEARS),2),
            'total_trades': int(sum(int(by[y].get('trades',0)) for y in PRE_OOS_YEARS)),
        }
    }


def _val_reasons(m):
    r=[]
    if _pf(m)<VALIDATION_MIN_PF: r.append(f'validation_pf<{VALIDATION_MIN_PF}')
    if float(m.get('max_dd_pct',100))>VALIDATION_MAX_DD_PCT: r.append(f'validation_dd>{VALIDATION_MAX_DD_PCT}')
    if int(m.get('trades',0))<VALIDATION_MIN_TRADES: r.append(f'validation_trades<{VALIDATION_MIN_TRADES}')
    return r


def discover(df,family,spread_pips,slippage_pips):
    years={y:df[(df.index>=f'{y}-01-01')&(df.index<f'{y+1}-01-01')] for y in (2022,2023,2024,2025)}
    results=[]; rejects=Counter()
    for j,params in enumerate(catalog()[family],1):
        pre=[{'year':y,'metrics':backtest_execution_equivalent(years[y],family,params,spread_pips=spread_pips,slippage_pips=slippage_pips)} for y in PRE_OOS_YEARS]
        reasons=_pre_reasons(pre)
        for r in reasons: rejects[r]+=1
        results.append({'family':family,'candidate':j,'params':params,'cost_aware_robustness_score':_score(pre),'pre_oos_gate':{'pass':not reasons,'years':list(PRE_OOS_YEARS),'fail_closed':True},'pre_oos_cost_aware':pre,'pre_oos_rejection_reasons':reasons,'diagnostic_snapshot':_diagnostic_snapshot(pre)})
    results.sort(key=lambda x:(-x['cost_aware_robustness_score'],x['candidate']))
    diagnostics=results[:DIAGNOSTIC_TOP_N]
    finalists=[x for x in results if x['pre_oos_gate']['pass']][:50]
    validated=[]; vreject=Counter()
    for x in finalists:
        vm=backtest_execution_equivalent(years[2025],family,x['params'],spread_pips=spread_pips,slippage_pips=slippage_pips); rr=_val_reasons(vm)
        for r in rr: vreject[r]+=1
        validated.append({**x,'validation_2025_cost_aware':vm,'validation_qualifies':not rr,'validation_rejection_reasons':rr})
    qualified=[x for x in validated if x['validation_qualifies']]
    qualified.sort(key=lambda x:(-x['cost_aware_robustness_score'],x['candidate']))
    return {'family':family,'candidate_total':len(results),'execution_model':'v28.1_next_bar_open','cost_profile':{'spread_pips':spread_pips,'slippage_pips':slippage_pips,'round_trip_cost_pips':2*(spread_pips+slippage_pips)},'qualified_count':len(qualified),'champion':qualified[0] if qualified else None,'top_20_diagnostics':diagnostics,'top_50':validated,'reject_diagnostics':{'pre_oos_rejections':dict(sorted(rejects.items(),key=lambda x:(-x[1],x[0]))),'pre_oos_passed_candidates':len(finalists),'validation_rejections':dict(sorted(vreject.items(),key=lambda x:(-x[1],x[0]))),'validation_qualified_candidates':len(qualified)}}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',required=True); ap.add_argument('--family',choices=FAMILIES,required=True); ap.add_argument('--output',default='artifacts/cost_aware_v15.json'); ap.add_argument('--spread-pips',type=float,default=.5); ap.add_argument('--slippage-pips',type=float,default=.2); a=ap.parse_args()
    df=pd.read_csv(a.data); df['timestamp']=pd.to_datetime(df['timestamp'],utc=True); df=df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}).set_index('timestamp').sort_index()
    if df.empty: raise SystemExit('REAL_DATA_REQUIRED: empty dataset')
    result=discover(df,a.family,a.spread_pips,a.slippage_pips)
    report={'schema_version':'forexai.cost_aware_discovery.v15.1','result':result,'oos_policy':{'loaded':False,'start':'2026-01-01','status':'HELD_OUT'},'real_data_required':True,'synthetic_fallback':False,'execution_model':{'next_bar_open':True,'adverse_entry_cost_per_side_pips':a.spread_pips+a.slippage_pips,'adverse_exit_cost_per_side_pips':a.spread_pips+a.slippage_pips,'sl_first':True,'max_hold_bars':MAX_HOLD_BARS,'opposite_signal_exit':True,'one_position_at_a_time':True}}
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(_native(report),indent=2,sort_keys=True),encoding='utf-8'); print(json.dumps(_native({'family':a.family,'candidate_total':result['candidate_total'],'qualified_count':result['qualified_count'],'champion':result['champion'],'top_diagnostic_candidate':result['top_20_diagnostics'][0]['candidate'] if result['top_20_diagnostics'] else None}),indent=2,sort_keys=True))
if __name__=='__main__': raise SystemExit(main())
