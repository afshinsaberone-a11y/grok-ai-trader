"""Deterministic G13 MQL5 generator.

This generator consumes the committed promotion manifest only. It never ranks,
optimizes, or chooses candidates. It emits one MQL5 EA per promoted frozen
configuration and records the config hash inside the source for auditability.
Generated EAs are research/demo candidates only; no live-trading authorization
is encoded here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA = "forexai.g13.promotion_manifest.m15.v1"

def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render(candidate: dict[str, Any]) -> str:
    p = candidate["params"]
    cid = int(candidate["candidate_id"])
    h = candidate["config_hash"]
    atr = float(p["atr_mult"])
    delta = float(p["min_delta"])
    pivot = int(p["pivot"])
    rr = float(p["rr"])
    rsi_high = int(p["rsi_high"])
    risk_pct = 0.5
    return f'''//+------------------------------------------------------------------+\n//| ForexAI G13 RSI Divergence M15 - Candidate {cid:02d}               |\n//| Generated only from a final promotion manifest.                  |\n//| Strategy: bearish RSI divergence, EURUSD M15, short-only.        |\n//| Frozen config hash: {h}\n//| Research authorization: DEMO/RESEARCH ONLY                       |\n//+------------------------------------------------------------------+\n#property strict\n#property version   "1.00"\n\n#include <Trade/Trade.mqh>\nCTrade trade;\n\ninput double RiskPercent = {risk_pct:.2f};\ninput long   MagicNumber = 130000 + {cid};\ninput int    RSIPeriod = 14;\ninput int    ATRPeriod = 14;\ninput int    Pivot = {pivot};\ninput double MinDelta = {delta:.10f};\ninput double ATRMult = {atr:.3f};\ninput double RR = {rr:.3f};\ninput double RSIHigh = {rsi_high:.1f};\ninput int    ExpiryBars = 30;\n\nint rsiHandle = INVALID_HANDLE;\nint atrHandle = INVALID_HANDLE;\ndatetime lastBar = 0;\n\nint OnInit()\n{{\n   rsiHandle = iRSI(_Symbol, PERIOD_M15, RSIPeriod, PRICE_CLOSE);\n   atrHandle = iATR(_Symbol, PERIOD_M15, ATRPeriod);\n   if(rsiHandle == INVALID_HANDLE || atrHandle == INVALID_HANDLE)\n      return INIT_FAILED;\n   trade.SetExpertMagicNumber(MagicNumber);\n   return INIT_SUCCEEDED;\n}}\n\nvoid OnDeinit(const int reason)\n{{\n   if(rsiHandle != INVALID_HANDLE) IndicatorRelease(rsiHandle);\n   if(atrHandle != INVALID_HANDLE) IndicatorRelease(atrHandle);\n}}\n\nbool IsNewBar()\n{{\n   datetime t = iTime(_Symbol, PERIOD_M15, 0);\n   if(t == lastBar) return false;\n   lastBar = t;\n   return true;\n}}\n\nint CountPositions()\n{{\n   int n = 0;\n   for(int i=PositionsTotal()-1; i>=0; --i)\n   {{\n      ulong ticket = PositionGetTicket(i);\n      if(ticket == 0) continue;\n      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber) n++;\n   }}\n   return n;\n}}\n\n// Returns the latest confirmed bearish RSI divergence.\n// A pivot at shift k is confirmed only after Pivot bars exist to both sides.\nbool BearishDivergence()\n{{\n   double rsi[];\n   ArraySetAsSeries(rsi, true);\n   int need = 2*Pivot + 40;\n   if(CopyBuffer(rsiHandle, 0, 0, need, rsi) < need) return false;\n\n   int firstShift = Pivot + 1;\n   int lastShift = need - Pivot - 1;\n   int prevShift = -1, newerShift = -1;\n   double prevHigh = 0.0, newerHigh = 0.0, prevRsi = 0.0, newerRsi = 0.0;\n\n   for(int s=firstShift; s<=lastShift; ++s)\n   {{\n      double h = iHigh(_Symbol, PERIOD_M15, s);\n      bool isPivot = true;\n      for(int j=1; j<=Pivot; ++j)\n      {{\n         if(iHigh(_Symbol, PERIOD_M15, s-j) > h || iHigh(_Symbol, PERIOD_M15, s+j) > h)\n         {{ isPivot = false; break; }}\n      }}\n      if(!isPivot || rsi[s] == EMPTY_VALUE) continue;\n\n      if(prevShift < 0)\n      {{\n         prevShift=s; prevHigh=h; prevRsi=rsi[s];\n      }}\n      else\n      {{\n         newerShift=s; newerHigh=h; newerRsi=rsi[s];\n         // Python reference uses the two latest confirmed highs and requires\n         // higher price by MinDelta plus RSI below the prior RSI and >= RSIHigh.\n         if(prevHigh > newerHigh)\n         {{\n            double th = prevHigh; double tr = prevRsi;\n            prevHigh = newerHigh; prevRsi = newerRsi; prevShift = newerShift;\n            newerShift = -1;\n            if(th < newerHigh - MinDelta && tr < newerRsi) return false;\n         }}\n         if(newerHigh > prevHigh + MinDelta && newerRsi < prevRsi && newerRsi >= RSIHigh)\n            return true;\n         prevShift = newerShift; prevHigh = newerHigh; prevRsi = newerRsi;\n         newerShift = -1;\n      }}\n   }}\n   return false;\n}}\n\ndouble CalcLots(double stopDistance)\n{{\n   if(stopDistance <= 0.0) return 0.0;\n   double balance = AccountInfoDouble(ACCOUNT_BALANCE);\n   double riskMoney = balance * RiskPercent / 100.0;\n   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);\n   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);\n   if(tickSize <= 0.0 || tickValue <= 0.0) return 0.0;\n   double lossPerLot = (stopDistance / tickSize) * tickValue;\n   if(lossPerLot <= 0.0) return 0.0;\n   double lots = riskMoney / lossPerLot;\n   double minLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);\n   double maxLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);\n   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);\n   if(step <= 0.0) return 0.0;\n   lots = MathFloor(lots / step) * step;\n   return NormalizeDouble(MathMax(minLot, MathMin(maxLot, lots)), 2);\n}}\n\nvoid OnTick()\n{{\n   if(!IsNewBar()) return;\n   if(CountPositions() > 0) return;\n\n   double atr[]; ArraySetAsSeries(atr, true);\n   if(CopyBuffer(atrHandle, 0, 0, 3, atr) < 3) return;\n\n   // Evaluate the decision on the just-closed bar; enter at current-bar open.\n   if(!BearishDivergence()) return;\n   double entry = iOpen(_Symbol, PERIOD_M15, 0);\n   double risk = ATRMult * atr[1];\n   if(risk <= 0.0) return;\n   double sl = entry + risk;\n   double tp = entry - RR * risk;\n   double lots = CalcLots(risk);\n   if(lots <= 0.0) return;\n   trade.Sell(lots, _Symbol, 0.0, sl, tp, "G13-{cid:02d}");\n}}\n//+------------------------------------------------------------------+\n'''


def generate(manifest_path: Path, out_dir: Path) -> list[Path]:
    m=json.loads(manifest_path.read_text(encoding='utf-8'))
    assert m['schema_version'] == MANIFEST_SCHEMA
    assert m['status'] == 'PROMOTION_READY'
    assert m['decision_policy']['ea_generation_allowed'] is True
    assert m['decision_policy']['demo_trading_allowed'] is False
    assert m['decision_policy']['live_trading_allowed'] is False
    ids=m['promoted_candidate_ids']
    assert len(ids) == 15 and len(set(ids)) == 15
    out_dir.mkdir(parents=True, exist_ok=True)
    paths=[]
    for c in m['candidates']:
        cid=int(c['candidate_id'])
        assert cid in ids
        assert c['config_hash'] == canonical_hash(c['params'])
        p=out_dir / f'ForexAI_G13_Candidate_{cid:02d}.mq5'
        p.write_text(render(c), encoding='utf-8')
        paths.append(p)
    assert len(paths) == 15
    return paths


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--output-dir',required=True,type=Path)
    a=ap.parse_args()
    paths=generate(a.manifest,a.output_dir)
    print(json.dumps({'generated_count':len(paths),'files':[p.name for p in paths],'live_trading_allowed':False,'demo_trading_allowed':False},sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
