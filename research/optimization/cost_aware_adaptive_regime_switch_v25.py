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

def metrics(rs, entries, exits):
    n = len(rs)
    gross_profit = sum(value for value in rs if value > 0)
    gross_loss = abs(sum(value for value in rs if value < 0))
    profit_factor = gross_profit / gross_loss if gross_loss else (3.0 if gross_profit > 0 else 0.0)
    equity = peak = 10000.0
    max_dd = 0.0
    for value in rs:
        equity *= 1 + RISK * value
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
    return {
        "trades": n,
        "entries": int(entries),
        "exits": int(exits),
        "entries_equal_exits": entries == exits,
        "win_rate_pct": round(100 * sum(value > 0 for value in rs) / n, 2) if n else 0.0,
        "total_R": round(float(sum(rs)), 2),
        "expectancy_R": round(float(sum(rs)) / n, 4) if n else 0.0,
        "profit_factor": round(float(profit_factor), 3),
        "max_dd_pct": round(100 * max_dd, 2),
        "final_equity": round(equity, 2),
        "next_bar_open_entry": True,
        "actual_entry_price_for_stops": True,
        "adverse_exit_cost_applied": True,
        "same_bar_sl_first": True,
        "one_position_at_a_time": True,
    }


def bt(d, p, spread=0.5, slippage=0.2):
    cfg = ExecutionConfig(spread_pips=spread, slippage_pips=slippage)
    rs = []
    entries = 0
    exits = 0

    for _, group in d.groupby("day", sort=True):
        g = group.reset_index()
        n = len(g)
        pos = 0
        entry = stop = target = 0.0
        entry_i = -1

        for i in range(60, n - 1):
            atr = float(g.loc[i, "ATR"])
            adx = float(g.loc[i, "ADX"])
            rsi = float(g.loc[i, "RSI"])
            ema20 = float(g.loc[i, "EMA20"])
            ema50 = float(g.loc[i, "EMA50"])
            close = float(g.loc[i, "Close"])
            if pos == 0:
                # Entry signals require a complete indicator set. Existing positions
                # must still be checked for SL/TP/expiry if an indicator is missing.
                if not np.isfinite(atr + adx + rsi + ema20 + ema50) or atr <= 0:
                    continue
                trending = adx >= p["adx_threshold"]
                side = 0
                if trending and close > ema20 > ema50 and close > g.loc[i-p["lookback"]:i-1, "High"].max():
                    side = 1
                elif trending and close < ema20 < ema50 and close < g.loc[i-p["lookback"]:i-1, "Low"].min():
                    side = -1
                elif p["mode"] == "adaptive" and not trending:
                    if rsi <= p["rsi_low"] and close < ema20:
                        side = 1
                    elif rsi >= p["rsi_high"] and close > ema20:
                        side = -1

                if not side:
                    continue

                # Signal is evaluated on the closed bar i and filled at bar i+1 open.
                entry_i = i + 1
                entry = apply_entry_cost(float(g.loc[entry_i, "Open"]), side, cfg)
                risk_distance = p["atr_stop"] * atr
                stop = entry - side * risk_distance
                target = entry + side * p["rr"] * risk_distance if trending else ema20
                if (target - entry) * side <= 0:
                    entry_i = -1
                    continue

                pos = side
                entries += 1
                continue

            age = i - entry_i + 1
            low = float(g.loc[i, "Low"])
            high = float(g.loc[i, "High"])
            hit_sl = low <= stop if pos == 1 else high >= stop
            hit_tp = high >= target if pos == 1 else low <= target
            risk_unit = p["atr_stop"] * float(g.loc[entry_i - 1, "ATR"])
            if not np.isfinite(risk_unit) or risk_unit <= 0:
                raise RuntimeError(f"V25_INVALID_OPEN_TRADE_RISK_UNIT:entry_index={entry_i}")

            result_r = None
            if hit_sl:
                # Conservative fill convention when SL and TP are both touched.
                result_r = pos * (apply_exit_cost(stop, pos, cfg) - entry) / risk_unit
            elif hit_tp:
                result_r = pos * (apply_exit_cost(target, pos, cfg) - entry) / risk_unit
            elif age >= MAX_HOLD:
                # i is at most n-2, therefore i+1 is an actual in-group bar.
                result_r = pos * (apply_exit_cost(float(g.loc[i + 1, "Open"]), pos, cfg) - entry) / risk_unit
            elif (
                (pos == 1 and rsi >= 50 and p["mode"] == "adaptive" and adx < p["adx_threshold"])
                or (pos == -1 and rsi <= 50 and p["mode"] == "adaptive" and adx < p["adx_threshold"])
            ):
                result_r = pos * (apply_exit_cost(float(g.loc[i + 1, "Open"]), pos, cfg) - entry) / risk_unit

            if result_r is not None:
                rs.append(float(result_r))
                exits += 1
                pos = 0
                entry_i = -1

        # The day boundary is an explicit flat-by-close boundary: realize any
        # remaining trade at the final bar close rather than silently dropping it.
        if pos:
            final_index = n - 1
            final_low = float(g.loc[final_index, "Low"])
            final_high = float(g.loc[final_index, "High"])
            risk_unit = p["atr_stop"] * float(g.loc[entry_i - 1, "ATR"])
            if not np.isfinite(risk_unit) or risk_unit <= 0:
                raise RuntimeError(f"V25_INVALID_OPEN_TRADE_RISK_UNIT:entry_index={entry_i}")

            hit_sl = final_low <= stop if pos == 1 else final_high >= stop
            hit_tp = final_high >= target if pos == 1 else final_low <= target
            if hit_sl:
                raw_exit = stop
            elif hit_tp:
                raw_exit = target
            else:
                raw_exit = float(g.loc[final_index, "Close"])
            rs.append(float(pos * (apply_exit_cost(raw_exit, pos, cfg) - entry) / risk_unit))
            exits += 1
            pos = 0
            entry_i = -1

    if entries != exits:
        raise RuntimeError(f"V25_EXECUTION_INVARIANT_FAIL:entries={entries}:exits={exits}")
    result = metrics(rs, entries, exits)
    result["round_trip_cost_pips"] = cfg.round_trip_cost_pips
    return result

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
        'qualified_count':len(q),
        'champion':None,
        'top_20_diagnostics':res[:TOP_N],
        'all_candidate_diagnostics':res,
        'validated_candidates':val,
    },'execution_model':{'entry':'next_bar_open','cost_pips_per_side':a.spread_pips+a.slippage_pips,'round_trip_cost_pips':2*(a.spread_pips+a.slippage_pips),'same_bar_resolution':'SL first (conservative)','expiry_bars':MAX_HOLD,'overlap':'one position at a time','adverse_exit_cost_applied':True},'oos_policy':{'loaded':False,'status':'HELD_OUT','start':'2026-01-01'},'real_data_required':True,'synthetic_fallback':False}
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(rep,indent=2,default=str),encoding='utf-8');print(json.dumps({'candidate_total':len(res),'pre_oos_qualified':len(final),'validation_qualified':len(q),'research_timeframe':a.timeframe}))
if __name__=='__main__':main()
