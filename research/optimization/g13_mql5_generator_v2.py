"""G13 deterministic MQL5 generator v2.

The generator consumes only the committed final promotion manifest. It never
ranks or mutates candidates. The emitted EA mirrors the Python signal concept:
confirmed swing-high pivots, bearish RSI divergence, ATR stop, fixed RR,
short-only, one position at a time, and 30-bar expiry.
"""
from __future__ import annotations

import argparse, hashlib, json
from pathlib import Path
from typing import Any

SCHEMA = "forexai.g13.promotion_manifest.m15.v1"

def canonical_hash(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render(c: dict[str, Any]) -> str:
    p=c["params"]; cid=int(c["candidate_id"])
    return f'''//+------------------------------------------------------------------+\n//| ForexAI G13 RSI Divergence M15 - Candidate {cid:02d}               |\n//| Frozen config: {c["config_hash"]}\n//| Research status: PROMOTION_READY / RESEARCH_ONLY                 |\n//| Live trading is NOT authorized by this source.                   |\n//+------------------------------------------------------------------+\n#property strict\n#property version "1.10"\n#include <Trade/Trade.mqh>\nCTrade trade;\n\ninput double RiskPercent = 0.50;\ninput long   MagicNumber = 130000 + {cid};\ninput int    RSIPeriod = 14;\ninput int    ATRPeriod = 14;\ninput int    Pivot = {int(p['pivot'])};\ninput double MinDelta = {float(p['min_delta']):.10f};\ninput double ATRMult = {float(p['atr_mult']):.3f};\ninput double RR = {float(p['rr']):.3f};\ninput double RSIHigh = {float(p['rsi_high']):.1f};\ninput int    ExpiryBars = 30;\n\nint hRSI=INVALID_HANDLE, hATR=INVALID_HANDLE;\ndatetime lastBar=0;\n\nbool IsNewBar()\n{{\n   datetime t=iTime(_Symbol,PERIOD_M15,0);\n   if(t==lastBar) return false;\n   lastBar=t; return true;\n}}\n\nint CountOwnPositions()\n{{\n   int n=0;\n   for(int i=PositionsTotal()-1;i>=0;--i)\n   {{\n      ulong ticket=PositionGetTicket(i);\n      if(ticket==0) continue;\n      if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==MagicNumber) n++;\n   }}\n   return n;\n}}\n\n// Mirrors the Python reference: walk confirmed pivots chronologically and\n// test only the two latest highs for higher-high / lower-RSI divergence.\nbool BearishDivergence()\n{{\n   int bars=Bars(_Symbol,PERIOD_M15);\n   int need=MathMin(bars,5000);\n   if(need < 2*Pivot+20) return false;\n\n   double rsi[]; ArraySetAsSeries(rsi,true);\n   if(CopyBuffer(hRSI,0,0,need,rsi) < need) return false;\n\n   bool havePrev=false; double prevHigh=0.0, prevRsi=0.0;\n   // Larger shift = older bar. Scan oldest -> newest so the last two\n   // confirmed pivots are the same pair used by the reference implementation.\n   for(int s=need-Pivot-1; s>=Pivot+1; --s)\n   {{\n      double h=iHigh(_Symbol,PERIOD_M15,s);\n      if(h<=0.0 || rsi[s]==EMPTY_VALUE) continue;\n      bool isPivot=true;\n      for(int j=1;j<=Pivot;++j)\n      {{\n         if(iHigh(_Symbol,PERIOD_M15,s-j)>h || iHigh(_Symbol,PERIOD_M15,s+j)>h)\n         {{ isPivot=false; break; }}\n      }}\n      if(!isPivot) continue;\n      if(!havePrev)\n      {{ prevHigh=h; prevRsi=rsi[s]; havePrev=true; continue; }}\n      double newerHigh=h, newerRsi=rsi[s];\n      if(newerHigh > prevHigh + MinDelta && newerRsi < prevRsi && newerRsi >= RSIHigh)\n         return true;\n      prevHigh=newerHigh; prevRsi=newerRsi;\n   }}\n   return false;\n}}\n\ndouble LotSize(double stopDistance)\n{{\n   if(stopDistance<=0.0) return 0.0;\n   double balance=AccountInfoDouble(ACCOUNT_BALANCE);\n   double riskMoney=balance*RiskPercent/100.0;\n   double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);\n   double tickValue=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);\n   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);\n   if(tickSize<=0.0 || tickValue<=0.0 || step<=0.0) return 0.0;\n   double lossPerLot=(stopDistance/tickSize)*tickValue;\n   if(lossPerLot<=0.0) return 0.0;\n   double lots=riskMoney/lossPerLot;\n   double minLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);\n   double maxLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);\n   lots=MathFloor(lots/step)*step;\n   lots=MathMax(minLot,MathMin(maxLot,lots));\n   return NormalizeDouble(lots,2);\n}}\n\nvoid ManageExpiry()\n{{\n   for(int i=PositionsTotal()-1;i>=0;--i)\n   {{\n      ulong ticket=PositionGetTicket(i);\n      if(ticket==0 || !PositionSelectByTicket(ticket)) continue;\n      if(PositionGetString(POSITION_SYMBOL)!=_Symbol || PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;\n      datetime openTime=(datetime)PositionGetInteger(POSITION_TIME);\n      int age=iBarShift(_Symbol,PERIOD_M15,openTime,false);\n      if(age>=ExpiryBars) trade.PositionClose(ticket);\n   }}\n}}\n\nint OnInit()\n{{\n   hRSI=iRSI(_Symbol,PERIOD_M15,RSIPeriod,PRICE_CLOSE);\n   hATR=iATR(_Symbol,PERIOD_M15,ATRPeriod);\n   if(hRSI==INVALID_HANDLE || hATR==INVALID_HANDLE) return INIT_FAILED;\n   trade.SetExpertMagicNumber(MagicNumber);\n   return INIT_SUCCEEDED;\n}}\n\nvoid OnDeinit(const int reason)\n{{\n   if(hRSI!=INVALID_HANDLE) IndicatorRelease(hRSI);\n   if(hATR!=INVALID_HANDLE) IndicatorRelease(hATR);\n}}\n\nvoid OnTick()\n{{\n   if(!IsNewBar()) return;\n   ManageExpiry();\n   if(CountOwnPositions()>0) return;\n   if(!BearishDivergence()) return;\n\n   double atr[]; ArraySetAsSeries(atr,true);\n   if(CopyBuffer(hATR,0,0,3,atr)<3) return;\n   double risk=ATRMult*atr[1];\n   if(risk<=0.0) return;\n\n   double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);\n   if(bid<=0.0) return;\n   double sl=bid+risk;\n   double tp=bid-RR*risk;\n   double lots=LotSize(risk);\n   if(lots<=0.0) return;\n   trade.Sell(lots,_Symbol,0.0,sl,tp,"ForexAI-G13-{cid:02d}");\n}}\n//+------------------------------------------------------------------+\n'''


def generate(manifest: Path, out_dir: Path) -> list[Path]:
    m=json.loads(manifest.read_text(encoding='utf-8'))
    assert m['schema_version']==SCHEMA and m['status']=='PROMOTION_READY'
    assert m['decision_policy']['ea_generation_allowed'] is True
    assert m['decision_policy']['demo_trading_allowed'] is False
    assert m['decision_policy']['live_trading_allowed'] is False
    ids=sorted(int(x) for x in m['promoted_candidate_ids'])
    assert len(ids)==15 and len(set(ids))==15
    cands={int(c['candidate_id']):c for c in json.loads(manifest.read_text())['candidates']}
    assert set(cands)==set(ids)
    out_dir.mkdir(parents=True,exist_ok=True)
    paths=[]
    for cid in ids:
        c=cands[cid]
        assert c['config_hash']==canonical_hash(c['params'])
        path=out_dir/f'ForexAI_G13_Candidate_{cid:02d}.mq5'
        path.write_text(render(c),encoding='utf-8')
        paths.append(path)
    return paths


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True,type=Path); ap.add_argument('--output-dir',required=True,type=Path)
    a=ap.parse_args(); paths=generate(a.manifest,a.output_dir)
    print(json.dumps({'generated_count':len(paths),'live_trading_allowed':False,'demo_trading_allowed':False,'files':[p.name for p in paths]},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
