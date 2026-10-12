"""Bind generated G13 M15 EAs to one-shot Control Plane intents.

This patch is applied to deterministic generator output. It preserves the
strategy and research-parity path, while replacing only the real Demo OnTick
path with a signal -> short-lived intent -> current authority -> one attempt
state machine. Live accounts are always rejected by existing Demo-only checks.
"""
from __future__ import annotations

from pathlib import Path


INTENT_SCHEMA = "forexai.g13.runtime_signal_intent.m15.v1"


def control_plane_gate_source(candidate_id: int, config_hash: str) -> str:
    # Plain template string deliberately avoids interpolating MQL5 braces.
    template = r'''
datetime cp_pending_bar=0;
datetime cp_pending_created=0;
double cp_pending_entry=0.0;
double cp_pending_sl=0.0;
double cp_pending_tp=0.0;
double cp_pending_lots=0.0;
bool cp_pending_signal=false;

string ControlPlaneIntentFile()
{
   return StringFormat("ForexAI_G13_SignalIntent_%I64d_EURUSD.json",(long)(MagicNumber-130000));
}

long ControlPlaneSignalBarEpoch(const datetime bar_time)
{
   long broker_offset=(long)(TimeCurrent()-TimeGMT());
   return (long)bar_time-broker_offset;
}

void ControlPlaneResetPending()
{
   cp_pending_bar=0;
   cp_pending_created=0;
   cp_pending_entry=0.0;
   cp_pending_sl=0.0;
   cp_pending_tp=0.0;
   cp_pending_lots=0.0;
   cp_pending_signal=false;
}

bool ControlPlaneWriteSignalIntent(const long bar_epoch,const double entry,const double sl,const double tp,const double lots)
{
   string target=ControlPlaneIntentFile();
   string temp=target+".tmp";
   if(FileIsExist(target,FILE_COMMON)) return false;
   if(FileIsExist(temp,FILE_COMMON) && !FileDelete(temp,FILE_COMMON)) return false;

   long cid=(long)(MagicNumber-130000);
   string created=TraceIsoUtc(TimeGMT());
   string payload=StringFormat(
      "{\"schema\":\"forexai.g13.runtime_signal_intent.m15.v1\",\"candidate_id\":%I64d,\"symbol\":\"EURUSD\",\"timeframe\":\"M15\",\"side\":\"SELL\",\"config_hash\":\"%s\",\"signal_bar_epoch\":%I64d,\"created_at_utc\":\"%s\",\"entry_price\":%.10f,\"stop_loss\":%.10f,\"take_profit\":%.10f,\"volume\":%.8f}",
      cid,ConfigHash,bar_epoch,created,entry,sl,tp,lots
   );
   int h=FileOpen(temp,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(h==INVALID_HANDLE) return false;
   uint written=FileWriteString(h,payload);
   FileFlush(h);
   FileClose(h);
   if(written!=(uint)StringLen(payload))
   {
      FileDelete(temp,FILE_COMMON);
      return false;
   }
   if(!FileMove(temp,FILE_COMMON,target,FILE_COMMON))
   {
      FileDelete(temp,FILE_COMMON);
      return false;
   }
   return FileIsExist(target,FILE_COMMON);
}

bool ControlPlaneDeletePendingFiles()
{
   bool ok=true;
   string auth=AuthorizationFile();
   string intent=ControlPlaneIntentFile();
   if(FileIsExist(auth,FILE_COMMON) && !FileDelete(auth,FILE_COMMON)) ok=false;
   if(FileIsExist(intent,FILE_COMMON) && !FileDelete(intent,FILE_COMMON)) ok=false;
   return ok;
}

bool ControlPlaneGlobalExecutionPreconditions()
{
   if((bool)MQLInfoInteger(MQL_TESTER)) return false;
   if(_Symbol!="EURUSD" || _Period!=PERIOD_M15) return false;
   if(!DemoTradingExecutionAllowed()) return false;
   if(CountOwnPositions()>0) return false;
   return true;
}

bool ControlPlaneCurrentRiskWithinReservation(const double lots,const double bid,const double sl)
{
   if(runtime_reserved_risk<=0.0 || lots<=0.0 || bid<=0.0 || sl<=bid) return false;
   double equity=AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity<=0.0) return false;
   double projected=0.0;
   if(!OrderCalcProfit(ORDER_TYPE_SELL,_Symbol,lots,bid,sl,projected)) return false;
   if(!MathIsValidNumber(projected) || projected>=0.0) return false;
   double actual_risk=MathAbs(projected)/equity;
   return MathIsValidNumber(actual_risk) && actual_risk>0.0 && actual_risk<=runtime_reserved_risk+1e-9;
}

void ControlPlaneProcessDemoTick(const bool new_bar)
{
   if(_Symbol!="EURUSD" || _Period!=PERIOD_M15) return;
   if((bool)MQLInfoInteger(MQL_TESTER)) return;
   if(_Symbol!="EURUSD" || _Period!=PERIOD_M15) return;
   // Preserve the strategy's existing expiry management even while new entries
   // are blocked by DENY, missing authorization, or another candidate position.
   if(new_bar) ManageExpiry();

   datetime now_utc=TimeGMT();
   if(cp_pending_signal)
   {
      long age=(long)now_utc-(long)cp_pending_created;
      if(age<0 || age>RuntimeAuthorizationMaxAgeSeconds)
      {
         ControlPlaneDeletePendingFiles();
         ControlPlaneResetPending();
         return;
      }
   }

   if(!cp_pending_signal)
   {
      if(!new_bar) return;
      if(!ControlPlaneGlobalExecutionPreconditions()) return;
      if(!BearishDivergence()) return;

      double atr=ATRAtShift(1);
      if(atr==EMPTY_VALUE || atr<=0.0) return;
      double risk=ATRMult*atr;
      MqlTick quote;
      if(!SymbolInfoTick(_Symbol,quote)) return;
      double bid=quote.bid;
      double ask=quote.ask;
      if(bid<=0.0 || ask<=0.0 || ask<bid) return;
      double sl=bid+risk;
      double tp=bid-RR*risk;
      if(sl<=ask || tp<=0.0 || tp>=bid || RR<=0.0) return;
      long stops=(long)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
      if(stops<0 || (sl-ask)<(double)stops*_Point || (bid-tp)<(double)stops*_Point) return;
      double lots=LotSize(risk,bid);
      if(lots<=0.0) return;

      datetime bar_time=iTime(_Symbol,PERIOD_M15,0);
      long bar_epoch=ControlPlaneSignalBarEpoch(bar_time);
      if(bar_epoch<=0) return;
      if(!ControlPlaneWriteSignalIntent(bar_epoch,bid,sl,tp,lots)) return;
      cp_pending_bar=bar_time;
      cp_pending_created=now_utc;
      cp_pending_entry=bid;
      cp_pending_sl=sl;
      cp_pending_tp=tp;
      cp_pending_lots=lots;
      cp_pending_signal=true;
      return;
   }

   // A pending intent may only be submitted while every live Demo gate is
   // still satisfied. DENY, stale auth, quote drift, and account changes block.
   if(!ControlPlaneGlobalExecutionPreconditions()) return;

   MqlTick quote;
   if(!SymbolInfoTick(_Symbol,quote)) return;
   double bid=quote.bid;
   double ask=quote.ask;
   if(bid<=0.0 || ask<=0.0 || ask<bid) return;
   if(MathAbs(bid-cp_pending_entry)>30.0*_Point) return;
   if(cp_pending_sl<=ask || cp_pending_tp>=bid || cp_pending_tp<=0.0) return;
   long stops=(long)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   if(stops<0 || (cp_pending_sl-ask)<(double)stops*_Point || (bid-cp_pending_tp)<(double)stops*_Point) return;

   long bar_epoch=ControlPlaneSignalBarEpoch(cp_pending_bar);
   string trade_id=StringFormat("G13-%I64d-%I64d-S",MagicNumber-130000,bar_epoch);
   string decision_id=StringFormat("G13-%I64d-%I64d-SELL",MagicNumber-130000,bar_epoch);
   if(!VerifyRuntimeAuthorization(trade_id,false,decision_id)) return;
   if(!ControlPlaneCurrentRiskWithinReservation(cp_pending_lots,bid,cp_pending_sl))
   {
      ControlPlaneDeletePendingFiles();
      ControlPlaneResetPending();
      return;
   }

   // Persist both attempt and consumption locks before deleting the token and
   // making exactly one broker call. A crash/timeout can never trigger a retry.
   if(!BeginRuntimeAuthorizationAttempt(trade_id))
   {
      ControlPlaneDeletePendingFiles();
      ControlPlaneResetPending();
      return;
   }
   if(!MarkRuntimeAuthorizationConsumed(trade_id))
   {
      ControlPlaneDeletePendingFiles();
      ControlPlaneResetPending();
      return;
   }
   if(!ControlPlaneDeletePendingFiles())
   {
      ControlPlaneResetPending();
      return;
   }

   double requested_entry=bid;
   double requested_sl=cp_pending_sl;
   double requested_tp=cp_pending_tp;
   double lots=cp_pending_lots;
   string trace_trade_id=trade_id;
   ControlPlaneResetPending();

   TraceLifecycle(
      trace_trade_id,"ORDER_SUBMITTED",
      StringFormat("\"side\":\"SELL\",\"requested_volume\":%.8f,\"requested_price\":%.10f,\"requested_sl\":%.10f,\"requested_tp\":%.10f,\"order_ticket\":\"0\"",
                   lots,requested_entry,requested_sl,requested_tp)
   );
   double spreadPoints=(ask-bid)/_Point;
   ulong started=GetTickCount64();
   bool accepted=trade.Sell(lots,_Symbol,requested_entry,requested_sl,requested_tp,"ForexAI-G13-@CID@");
   ulong elapsed=GetTickCount64()-started;
   double executedPrice=trade.ResultPrice();
   double slippagePoints=(executedPrice>0.0 ? (executedPrice-requested_entry)/_Point : 0.0);
   string executionComment=(accepted ? trade.ResultComment() : "CTrade Sell returned false");
   ExecutionAuditLog("ORDER_ATTEMPT","SELL",trade.ResultOrder(),trade.ResultDeal(),
                     lots,trade.ResultVolume(),requested_entry,executedPrice,requested_sl,requested_tp,
                     spreadPoints,slippagePoints,
                     trade.ResultRetcode(),trade.ResultRetcodeDescription(),
                     elapsed,executionComment);
   if(!accepted || trade.ResultRetcode()!=TRADE_RETCODE_DONE ||
      trade.ResultOrder()==0 || trade.ResultDeal()==0 ||
      trade.ResultVolume()<=0.0 || MathAbs(trade.ResultVolume()-lots)>1e-9)
   {
      TraceRecord(
         trace_trade_id,"BROKER_OUTCOME_UNKNOWN","ORDER_SUBMITTED",
         StringFormat("\"retcode\":%u,\"order_ticket\":\"%I64d\",\"deal_ticket\":\"%I64d\",\"requested_volume\":%.8f",
                      trade.ResultRetcode(),(long)trade.ResultOrder(),(long)trade.ResultDeal(),lots)
      );
      runtime_authorization_healthy=false;
      return;
   }
   TraceSuccessfulEntry(trace_trade_id,lots,requested_sl,requested_tp);
}

'''
    return template.replace("@CID@", str(candidate_id)).replace("@CONFIG_HASH@", config_hash)


def patch_generated_source(source: str, candidate_id: int, config_hash: str) -> str:
    """Patch only reviewed generator markers and fail if upstream shape drifts."""
    if not 130002 <= 130000 + candidate_id <= 130048:
        raise ValueError("CONTROL_PLANE_CANDIDATE_ID_OUT_OF_RANGE")
    if len(config_hash) != 64 or any(ch not in "0123456789abcdef" for ch in config_hash.lower()):
        raise ValueError("CONTROL_PLANE_CONFIG_HASH_INVALID")
    if "void OnTick()\n{" not in source or "bool VerifyRuntimeAuthorization(const string trade_id,const bool is_buy)" not in source:
        raise ValueError("CONTROL_PLANE_GENERATOR_SOURCE_SHAPE_UNKNOWN")
    if "CTrade trade;" not in source or "bool DemoTradingExecutionAllowed()" not in source:
        raise ValueError("CONTROL_PLANE_GENERATOR_SAFETY_GATES_MISSING")
    patched = source.replace(
        "bool VerifyRuntimeAuthorization(const string trade_id,const bool is_buy)",
        "bool VerifyRuntimeAuthorization(const string trade_id,const bool is_buy,const string expected_decision_id)",
        1,
    )
    old_identity = 'if(parts[2]!=trade_id || parts[5]!=_Symbol) return false;'
    if old_identity not in patched:
        raise ValueError("CONTROL_PLANE_AUTH_IDENTITY_CHECK_NOT_FOUND")
    patched = patched.replace(
        old_identity,
        old_identity + '\n   if(parts[14]!=expected_decision_id) return false;',
        1,
    )
    old_trade_id = '''string BuildTraceTradeId(const datetime signal_bar_time)
{
   string demo_trade_id=LoadDemoTradeId();
   if(StringLen(demo_trade_id)>0) return demo_trade_id;
   return StringFormat("T-%I64d-%s-%I64d-S",MagicNumber,_Symbol,(long)signal_bar_time);
}'''
    new_trade_id = '''string BuildTraceTradeId(const datetime signal_bar_time)
{
   long bar_epoch=(long)signal_bar_time-(long)(TimeCurrent()-TimeGMT());
   return StringFormat("G13-%I64d-%I64d-S",MagicNumber-130000,bar_epoch);
}'''
    if old_trade_id not in patched:
        raise ValueError("CONTROL_PLANE_TRADE_ID_FACTORY_NOT_FOUND")
    patched = patched.replace(old_trade_id, new_trade_id, 1)
    tick_start = patched.index("\nvoid OnTick()\n{")
    tick_end = patched.index("\n}\n//+------------------------------------------------------------------+", tick_start) + 2
    # Keep deterministic parity/backtest behavior byte-for-byte and gate only
    # the live terminal execution path behind the new producer/one-shot intent.
    new_tick = '''\nvoid OnTick()
{
   bool newBar=IsNewBar();

   // Deterministic parity path remains signal-only; it never requires or emits
   // runtime authorization and cannot submit orders.
   if(ParityMode)
   {
      if(!newBar) return;
      if(!BearishDivergence()) return;
      double atr=ATRAtShift(1);
      if(atr==EMPTY_VALUE || atr<=0.0) return;
      double risk=ATRMult*atr;
      double entry=iOpen(_Symbol,PERIOD_M15,0);
      if(entry<=0.0) return;
      double sl=entry+risk;
      double tp=entry-RR*risk;
      ParityLogSignal(entry,sl,tp,atr);
      return;
   }

   // Strategy Tester preserves the existing research/backtest path. No
   // terminal-side authorization or live/Demo order is ever used in Tester.
   if((bool)MQLInfoInteger(MQL_TESTER))
   {
      if(!newBar) return;
      ManageExpiry();
      if(CountOwnPositions()>0 || !BearishDivergence()) return;
      double atr=ATRAtShift(1);
      if(atr==EMPTY_VALUE || atr<=0.0) return;
      double risk=ATRMult*atr;
      MqlTick quote;
      if(!SymbolInfoTick(_Symbol,quote)) return;
      double bid=quote.bid;
      double ask=quote.ask;
      if(bid<=0.0 || ask<=0.0 || ask<bid) return;
      double entry=bid;
      double sl=entry+risk;
      double tp=entry-RR*risk;
      long stops=(long)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
      if(stops<0 || risk<(double)stops*_Point || RR<=0.0) return;
      double lots=0.0;
      lots=LotSize(risk,entry);
      if(lots<=0.0) return;
      trade.Sell(lots,_Symbol,bid,sl,tp,"ForexAI-G13-@CID@");
      return;
   }

   ControlPlaneProcessDemoTick(newBar);
}'''
    new_tick = new_tick.replace("@CID@", str(candidate_id))
    patched = patched[:tick_start] + new_tick + patched[tick_end:]
    insertion = patched.index("\nvoid OnTick()\n{")
    patched = patched[:insertion] + "\n" + control_plane_gate_source(candidate_id, config_hash) + patched[insertion:]
    init_guard = '''int OnInit()
{
   trade.SetExpertMagicNumber(MagicNumber);'''
    guarded_init = '''int OnInit()
{
   if(_Symbol!="EURUSD" || _Period!=PERIOD_M15) return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);'''
    if init_guard not in patched:
        raise ValueError("CONTROL_PLANE_ONINIT_MARKER_NOT_FOUND")
    patched = patched.replace(init_guard, guarded_init, 1)
    if "ControlPlaneProcessDemoTick(newBar)" not in patched or "VerifyRuntimeAuthorization(trade_id,false,decision_id)" not in patched:
        raise ValueError("CONTROL_PLANE_GATE_INSERTION_FAILED")
    if "void ControlPlaneProcessDemoTick" not in patched:
        raise ValueError("CONTROL_PLANE_GATE_HELPERS_MISSING")
    return patched
