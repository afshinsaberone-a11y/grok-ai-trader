"""ForexAI G7: multi-timeframe event/regime diagnosis plus execution-cost sensitivity.

No promotion is performed. 2022-2024 are discovery; 2025 is diagnostic validation only;
2026 remains held out. Uses the same G6 event/regime catalog and canonical execution model.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from research.optimization.regime_aware_event_discovery_g6 import catalog,prepare,backtest
from research.optimization.execution_contract_v1 import ExecutionConfig\nfrom research.optimization.cost_aware_gate_v14 import pre_oos_gate, validation_gate

YEARS=(2022,2023,2024)
COSTS=(0.0,0.7,1.4,2.0)  # round-trip pips; converted to equal adverse side costs

def run_one(d, p, rt_cost):
    side=rt_cost/2.0
    cfg=ExecutionConfig(spread_pips=side,slippage_pips=0.0)
    return backtest(d,p,cfg)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',required=True); ap.add_argument('--timeframe',required=True,choices=('M1','M5','M15'))
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    d=prepare(pd.read_csv(a.data))
    years={y:d[(d.index>=f'{y}-01-01')&(d.index<f'{y+1}-01-01')] for y in (*YEARS,2025)}
    rows=[]
    for p in catalog():
        rec={'family':p['family'],'params':p,'costs':{}}
        for cost in COSTS:
            ys={str(y):run_one(years[y],p,cost) for y in YEARS}
            pre_metrics=[{'year':y,'metrics':ys[str(y)]} for y in YEARS]\n            rec['costs'][str(cost)]={'years':ys,'positive_years':sum(ys[str(y)]['expectancy_R']>0 for y in YEARS),'sum_expectancy':sum(ys[str(y)]['expectancy_R'] for y in YEARS),'min_pf':min(ys[str(y)]['profit_factor'] for y in YEARS),'max_dd':max(ys[str(y)]['max_dd_pct'] for y in YEARS),'strict_pre_oos_pass':pre_oos_gate(pre_metrics)}
        rec['validation_2025']={str(c):run_one(years[2025],p,c) for c in COSTS}
        rows.append(rec)
    summary={}
    for cost in COSTS:
        key=str(cost); eligible=[r for r in rows if r['costs'][key]['strict_pre_oos_pass']]
        summary[key]={'candidate_count':len(rows),'diagnostic_robust_count':len(eligible),'best_sum_expectancy':max((r['costs'][key]['sum_expectancy'] for r in rows),default=None),'best_min_pf':max((r['costs'][key]['min_pf'] for r in rows),default=None),'best_max_dd':min((r['costs'][key]['max_dd'] for r in rows),default=None),'strict_pre_oos_count':sum(r['costs'][key]['strict_pre_oos_pass'] for r in rows)}
    tf_payload={'schema_version':'forexai.g7.mtf_cost_sensitivity.v1','research_timeframe':a.timeframe,'real_data_required':True,'synthetic_fallback':False,'oos_policy':{'loaded':False,'status':'HELD_OUT','start':'2026-01-01'},'execution_model':{'entry':'next_bar_open','same_bar_resolution':'SL first (conservative)','expiry_bars':24,'overlap':'one position at a time'},'costs_round_trip_pips':list(COSTS),'candidate_total':len(rows),'summary':summary,'candidates':rows,'champion':None}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(tf_payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'candidate_total':len(rows),'timeframe':a.timeframe,'costs':list(COSTS),'summary':summary}))
if __name__=='__main__':main()
