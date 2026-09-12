"""G13 deterministic MQL5 generator v2.

Consumes only the committed final promotion manifest plus frozen validation
handoff. It never ranks or mutates candidates. Generated EAs are research
artifacts only; live trading is not authorized here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "forexai.g13.promotion_manifest.m15.v1"
HANDOFF_SCHEMA = "forexai.g13.candidate_handoff.frozen.v1"


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def render(candidate: dict[str, Any]) -> str:
    p = candidate["params"]
    cid = int(candidate["candidate_id"])
    cfg_hash = candidate["config_hash"]
    return f'''//+------------------------------------------------------------------+
//| ForexAI G13 RSI Divergence M15 - Candidate {cid:02d}               |
//| Frozen config hash: {cfg_hash}
//| Research status: PROMOTION_READY / RESEARCH_ONLY                 |
//| Live trading is NOT authorized by this source.                   |
//+------------------------------------------------------------------+
#property strict
#property version "1.20"
#include <Trade/Trade.mqh>
CTrade trade;

input double RiskPercent = 0.50;
input long   MagicNumber = 130000 + {cid};
input int    RSIPeriod = 14;
input int    ATRPeriod = 14;
input int    Pivot = {int(p['pivot'])};
input double MinDelta = {float(p['min_delta']):.10f};
input double ATRMult = {float(p['atr_mult']):.3f};
input double RR = {float(p['rr']):.3f};
input double RSIHigh = {float(p['rsi_high']):.1f};
input int    ExpiryBars = 30;

int hRSI=INVALID_HANDLE, hATR=INVALID_HANDLE;
datetime lastBar=0;

bool IsNewBar()
{{
   datetime t=iTime(_Symbol,PERIOD_M15,0);
   if(t==lastBar) return false;
   lastBar=t;
   return true;
}}

int CountOwnPositions()
{{
   int n=0;
   for(int i=PositionsTotal()-1;i>=0;--i)
   {{
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==MagicNumber) n++;
   }}
   return n;
}}

// Evaluate only the most recent two confirmed swing highs. This avoids the
// common live-EA error of reusing an old historical divergence indefinitely.
bool BearishDivergence()
{{
   int bars=Bars(_Symbol,PERIOD_M15);
   int need=MathMin(bars,5000);
   if(need < 2*Pivot+20) return false;

   double rsi[];
   ArraySetAsSeries(rsi,true);
   if(CopyBuffer(hRSI,0,0,need,rsi)<need) return false;

   bool haveNewer=false;
   double newerHigh=0.0, newerRsi=0.0;
   bool haveOlder=false;
   double olderHigh=0.0, olderRsi=0.0;

   // Series shifts: 1 is the most recent closed bar. The first pivot found
   // while walking from recent -> older is the latest confirmed pivot.
   for(int s=Pivot+1; s<=need-Pivot-1; ++s)
   {{
      double h=iHigh(_Symbol,PERIOD_M15,s);
      if(h<=0.0 || rsi[s]==EMPTY_VALUE) continue;
      bool isPivot=true;
      for(int j=1;j<=Pivot;++j)
      {{
         if(iHigh(_Symbol,PERIOD_M15,s-j)>h || iHigh(_Symbol,PERIOD_M15,s+j)>h)
         {{ isPivot=false; break; }}
      }}
      if(!isPivot) continue;

      if(!haveNewer)
      {{
         newerHigh=h;
         newerRsi=rsi[s];
         haveNewer=true;
         continue;
      }}

      olderHigh=h;
      olderRsi=rsi[s];
      haveOlder=true;
      break;
   }}

   if(!haveNewer || !haveOlder) return false;
   // Price makes a higher high by MinDelta while RSI makes a lower high.
   return newerHigh > olderHigh + MinDelta && newerRsi < olderRsi && newerRsi >= RSIHigh;
}}

double LotSize(double stopDistance)
{{
   if(stopDistance<=0.0) return 0.0;
   double balance=AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney=balance*RiskPercent/100.0;
   double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   double tickValue=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(tickSize<=0.0 || tickValue<=0.0 || step<=0.0) return 0.0;
   double lossPerLot=(stopDistance/tickSize)*tickValue;
   if(lossPerLot<=0.0) return 0.0;
   double lots=riskMoney/lossPerLot;
   double minLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maxLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   lots=MathFloor(lots/step)*step;
   lots=MathMax(minLot,MathMin(maxLot,lots));
   return NormalizeDouble(lots,2);
}}

void ManageExpiry()
{{
   for(int i=PositionsTotal()-1;i>=0;--i)
   {{
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || !PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol || PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      datetime openTime=(datetime)PositionGetInteger(POSITION_TIME);
      int age=iBarShift(_Symbol,PERIOD_M15,openTime,false);
      if(age>=ExpiryBars) trade.PositionClose(ticket);
   }}
}}

int OnInit()
{{
   hRSI=iRSI(_Symbol,PERIOD_M15,RSIPeriod,PRICE_CLOSE);
   hATR=iATR(_Symbol,PERIOD_M15,ATRPeriod);
   if(hRSI==INVALID_HANDLE || hATR==INVALID_HANDLE) return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   return INIT_SUCCEEDED;
}}

void OnDeinit(const int reason)
{{
   if(hRSI!=INVALID_HANDLE) IndicatorRelease(hRSI);
   if(hATR!=INVALID_HANDLE) IndicatorRelease(hATR);
}}

void OnTick()
{{
   if(!IsNewBar()) return;
   ManageExpiry();
   if(CountOwnPositions()>0) return;
   if(!BearishDivergence()) return;

   double atr[];
   ArraySetAsSeries(atr,true);
   if(CopyBuffer(hATR,0,0,3,atr)<3) return;
   double risk=ATRMult*atr[1];
   if(risk<=0.0) return;

   // Reference research uses next-bar open concept. The market order is sent
   // on the first tick of the new M15 bar; execution-price slippage is broker-dependent.
   double entry=iOpen(_Symbol,PERIOD_M15,0);
   if(entry<=0.0) return;
   double sl=entry+risk;
   double tp=entry-RR*risk;
   double lots=LotSize(risk);
   if(lots<=0.0) return;
   trade.Sell(lots,_Symbol,0.0,sl,tp,"ForexAI-G13-{cid:02d}");
}}
//+------------------------------------------------------------------+
'''


def generate(manifest_path: Path, handoff_path: Path, out_dir: Path) -> list[Path]:
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    handoff=json.loads(handoff_path.read_text(encoding='utf-8'))
    assert manifest['schema_version']==SCHEMA and manifest['status']=='PROMOTION_READY'
    policy=manifest['decision_policy']
    assert policy['ea_generation_allowed'] is True
    assert policy['demo_trading_allowed'] is False
    assert policy['live_trading_allowed'] is False
    assert handoff['schema_version']==HANDOFF_SCHEMA
    hp=handoff['handoff_policy']
    assert hp['parameters_are_frozen'] is True
    assert hp['oos_optimization_disabled'] is True
    ids=sorted(int(x) for x in manifest['promoted_candidate_ids'])
    assert len(ids)==15 and len(set(ids))==15
    cands={int(c['candidate_id']):c for c in handoff['candidates']}
    hashes=manifest['candidate_config_hashes']
    assert set(cands)>=set(ids)
    out_dir.mkdir(parents=True,exist_ok=True)
    paths=[]
    for cid in ids:
        c=cands[cid]
        assert c['config_hash']==hashes[str(cid)]
        assert c['config_hash']==canonical_hash(c['params'])
        path=out_dir/f'ForexAI_G13_Candidate_{cid:02d}.mq5'
        path.write_text(render(c),encoding='utf-8')
        paths.append(path)
    assert len(paths)==15
    return paths


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--handoff',required=True,type=Path)
    ap.add_argument('--output-dir',required=True,type=Path)
    a=ap.parse_args()
    paths=generate(a.manifest,a.handoff,a.output_dir)
    print(json.dumps({'generated_count':len(paths),'live_trading_allowed':False,'demo_trading_allowed':False,'files':[p.name for p in paths]},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
