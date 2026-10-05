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
#property version "1.25"
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
// ParityMode is a deterministic signal-telemetry mode. When true, the EA
// must not filter on open positions and must not submit broker orders.
input bool   ParityMode = false;
input bool   DemoTradingAuthorized = false;
input string ConfigHash = "{cfg_hash}";
input string ParityFile = "g13_mql5_parity.csv";
input string ExecutionAuditFile = "g13_demo_execution_audit.csv";
input bool   RequireRuntimeAuthorization = true;
input string AuthorizationFileName = "";
input string TraceFileName = "";
input string DemoTradeContextFileName = "ForexAI_G13_Demo_TradeId.txt";

const long RuntimeAuthorizationMaxAgeSeconds = 10;

datetime lastBar=0;
int parityHandle=INVALID_HANDLE;
int executionAuditHandle=INVALID_HANDLE;
string active_trace_trade_id="";
bool runtime_authorization_healthy=false;
bool runtime_trace_healthy=true;
string runtime_authorization_id="";
string runtime_reservation_id="";
double runtime_reserved_risk=0.0;

bool IsNewBar()
{{
   datetime t=iTime(_Symbol,PERIOD_M15,0);
   if(t==lastBar) return false;
   lastBar=t;
   return true;
}}

string AuthorizationFile()
{{
   if(StringLen(AuthorizationFileName)>0) return AuthorizationFileName;
   return StringFormat("ForexAI_Authorization_%I64d_%s.auth",MagicNumber,_Symbol);
}}

string Sha256Hex(const string value)
{{
   uchar data[];
   uchar key[];
   uchar digest[];
   int count=StringToCharArray(value,data,0,StringLen(value),CP_UTF8);
   if(count<=0) return "";
   ArrayResize(data,count);
   int size=CryptEncode(CRYPT_HASH_SHA256,data,key,digest);
   if(size<=0) return "";
   string hex="";
   for(int i=0;i<size;++i) hex+=StringFormat("%02X",digest[i]);
   return hex;
}}

bool AuthorizationFieldSafe(const string value)
{{
   if(StringLen(value)<=0) return false;
   return StringFind(value,"\\\\n")<0 && StringFind(value,"\\\\r")<0;
}}

string AuthorizationIdentityDigest(const string trade_id,const string authorization_id,const string reservation_id)
{{
   string material=IntegerToString(MagicNumber)+"|"+_Symbol+"|"+trade_id+"|"+authorization_id+"|"+reservation_id;
   string digest=Sha256Hex(material);
   if(StringLen(digest)<32) return "";
   return StringSubstr(digest,0,32);
}}

string AuthorizationConsumedKey(const string trade_id,const string authorization_id,const string reservation_id)
{{
   return "ForexAI.v1.a.c."+AuthorizationIdentityDigest(trade_id,authorization_id,reservation_id);
}}

string AuthorizationAttemptKey(const string trade_id,const string authorization_id,const string reservation_id)
{{
   return "ForexAI.v1.a.t."+AuthorizationIdentityDigest(trade_id,authorization_id,reservation_id);
}}

bool BeginRuntimeAuthorizationAttempt(const string trade_id)
{{
   string key=AuthorizationAttemptKey(trade_id,runtime_authorization_id,runtime_reservation_id);
   if(GlobalVariableCheck(key)) return false;

   if(GlobalVariableSetOnCondition(key,1.0,0.0))
      return true;

   if(GlobalVariableCheck(key))
      return false;

   if(GlobalVariableSet(key,0.0)==0)
      return false;

   if(!GlobalVariableSetOnCondition(key,1.0,0.0))
      return false;

   GlobalVariablesFlush();
   return true;
}}

bool VerifyRuntimeAuthorization(const string trade_id,const bool is_buy)
{{
   runtime_authorization_healthy=false;
   if(!RequireRuntimeAuthorization) return false;
   if(StringLen(trade_id)==0) return false;

   string expected_side=is_buy ? "B" : "S";
   if(StringSubstr(trade_id,StringLen(trade_id)-1,1)!=expected_side) return false;

   int handle=FileOpen(
      AuthorizationFile(),FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,'|',CP_UTF8
   );
   if(handle==INVALID_HANDLE) return false;
   string line=FileReadString(handle);
   FileClose(handle);
   if(StringLen(line)<=0) return false;

   string parts[];
   ushort sep=StringGetCharacter("|",0);
   int count=StringSplit(line,sep,parts);
   if(count!=23) return false;
   for(int i=0;i<count;++i) if(!AuthorizationFieldSafe(parts[i])) return false;

   if(parts[0]!="FOREXAI-AUTH-V1" || parts[1]!="forexai.mql5_authorization_record.v1") return false;
   if(parts[2]!=trade_id || parts[5]!=_Symbol) return false;

   string current_timeframe=EnumToString(_Period);
   StringReplace(current_timeframe,"PERIOD_","");
   if(parts[6]!=current_timeframe) return false;

   double authorized=StringToDouble(parts[7]);
   double reserved=StringToDouble(parts[8]);
   if(!MathIsValidNumber(authorized) || !MathIsValidNumber(reserved)) return false;
   if(authorized<=0 || reserved<=0 || reserved>authorized || authorized>0.006) return false;
   if(DoubleToString(authorized,12)!=parts[7] || DoubleToString(reserved,12)!=parts[8]) return false;

   long now_epoch=(long)TimeGMT();
   long expiry_epoch=StringToInteger(parts[10]);
   long issued_epoch=StringToInteger(parts[12]);
   if(expiry_epoch<=0 || issued_epoch<=0 || now_epoch>=expiry_epoch || issued_epoch>now_epoch) return false;
   if(now_epoch-issued_epoch>RuntimeAuthorizationMaxAgeSeconds) return false;

   if(parts[18]!=parts[3] || parts[19]!=parts[9] || parts[21]!="forexai.execution.v1") return false;

   string body=parts[0];
   for(int i=1;i<22;++i) body+="|"+parts[i];
   string supplied_hash=parts[22];
   StringToUpper(supplied_hash);
   if(supplied_hash!=Sha256Hex(body)) return false;

   for(int i=13;i<=21;++i) if(StringLen(parts[i])==0) return false;

   if(GlobalVariableCheck(AuthorizationConsumedKey(parts[2],parts[3],parts[4]))) return false;
   if(GlobalVariableCheck(AuthorizationAttemptKey(parts[2],parts[3],parts[4]))) return false;

   runtime_authorization_id=parts[3];
   runtime_reservation_id=parts[4];
   runtime_reserved_risk=reserved;
   runtime_authorization_healthy=true;
   return true;
}}

bool MarkRuntimeAuthorizationConsumed(const string trade_id)
{{
   if(!RequireRuntimeAuthorization || !runtime_authorization_healthy) return false;
   string key=AuthorizationConsumedKey(trade_id,runtime_authorization_id,runtime_reservation_id);
   if(GlobalVariableSet(key,1.0)==0 || !GlobalVariableCheck(key))
   {{
      runtime_authorization_healthy=false;
      return false;
   }}
   GlobalVariablesFlush();
   return GlobalVariableCheck(key);
}}

string TraceFile()
{{
   if(StringLen(TraceFileName)>0) return TraceFileName;
   return StringFormat("ForexAI_RuntimeTrace_%I64d_%s.jsonl",MagicNumber,_Symbol);
}}

bool EnsureRuntimeTraceReady()
{{
   int handle=FileOpen(
      TraceFile(),
      FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE
   );
   if(handle==INVALID_HANDLE) return false;
   FileClose(handle);
   return true;
}}

string TraceIsoUtc(const datetime value)
{{
   MqlDateTime t;
   TimeToStruct(value,t);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d+00:00",t.year,t.mon,t.day,t.hour,t.min,t.sec);
}}

string TraceBrokerIso(const datetime value)
{{
   MqlDateTime t;
   TimeToStruct(value,t);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",t.year,t.mon,t.day,t.hour,t.min,t.sec);
}}

string TraceJsonEscape(string value)
{{
   StringReplace(value,"\\\\","\\\\\\\\");
   StringReplace(value,"\\\"","\\\\\\\"");
   StringReplace(value,"\\r","\\\\r");
   StringReplace(value,"\\n","\\\\n");
   return value;
}}

void TraceRecord(const string trade_id,const string event_type,const string state,const string payload_fields)
{{
   if((bool)MQLInfoInteger(MQL_TESTER)) return;
   if(StringLen(trade_id)==0 || StringLen(event_type)==0 || StringLen(state)==0)
      return;

   int handle=FileOpen(
      TraceFile(),
      FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE
   );
   if(handle==INVALID_HANDLE)
   {{
      runtime_trace_healthy=false;
      return;
   }}

   FileSeek(handle,0,SEEK_END);
   long offset=(long)(TimeCurrent()-TimeGMT());
   string payload=StringFormat(
      "\\\"broker_timestamp\\\":\\\"%s\\\",\\\"broker_utc_offset_seconds\\\":%I64d",
      TraceJsonEscape(TraceBrokerIso(TimeCurrent())),offset
   );
   if(StringLen(payload_fields)>0)
      payload+=","+payload_fields;

   string event_id="G13-MQL5-"+trade_id+"-"+event_type;
   string row=StringFormat(
      "{{\\\"schema\\\":\\\"forexai.runtime_trace.v1\\\",\\\"source\\\":\\\"MQL5\\\",\\\"trade_id\\\":\\\"%s\\\",\\\"event_id\\\":\\\"%s\\\",\\\"event_type\\\":\\\"%s\\\",\\\"idempotency_key\\\":\\\"%s\\\",\\\"timestamp_utc\\\":\\\"%s\\\",\\\"state\\\":\\\"%s\\\",\\\"payload\\\":{{%s}}}}\\n",
      TraceJsonEscape(trade_id),
      TraceJsonEscape(event_id),
      TraceJsonEscape(event_type),
      TraceJsonEscape(event_id),
      TraceIsoUtc(TimeGMT()),
      TraceJsonEscape(state),
      payload
   );

   uint written=FileWriteString(handle,row);
   FileFlush(handle);
   FileClose(handle);
   if(written!=(uint)StringLen(row))
      runtime_trace_healthy=false;
}}

void TraceLifecycle(const string trade_id,const string state,const string payload_fields)
{{
   TraceRecord(trade_id,state,state,payload_fields);
}}

string LoadDemoTradeId()
{{
   if((bool)MQLInfoInteger(MQL_TESTER)) return "";
   int handle=FileOpen(
      DemoTradeContextFileName,
      FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ
   );
   if(handle==INVALID_HANDLE) return "";
   string value=FileReadString(handle);
   FileClose(handle);
   if(StringLen(value)<=0 || StringFind(value,"|")>=0 || StringFind(value,"\\n")>=0 || StringFind(value,"\\r")>=0)
      return "";
   return value;
}}

string BuildTraceTradeId(const datetime signal_bar_time)
{{
   string demo_trade_id=LoadDemoTradeId();
   if(StringLen(demo_trade_id)>0) return demo_trade_id;
   return StringFormat("T-%I64d-%s-%I64d-S",MagicNumber,_Symbol,(long)signal_bar_time);
}}

void TraceSuccessfulEntry(
   const string trade_id,
   const double requested_volume,
   const double requested_sl,
   const double requested_tp
)
{{
   active_trace_trade_id=trade_id;
   ulong order_ticket=trade.ResultOrder();
   ulong deal_ticket=trade.ResultDeal();
   double fill_price=trade.ResultPrice();
   if(deal_ticket>0 && HistoryDealSelect(deal_ticket))
      fill_price=HistoryDealGetDouble(deal_ticket,DEAL_PRICE);

   TraceLifecycle(
      trade_id,"ACCEPTED",
      StringFormat(
         "\\\"side\\\":\\\"SELL\\\",\\\"retcode\\\":%u,\\\"order_ticket\\\":\\\"%I64d\\\",\\\"deal_ticket\\\":\\\"%I64d\\\",\\\"requested_volume\\\":%.8f,\\\"confirmed_volume\\\":%.8f",
         trade.ResultRetcode(),(long)order_ticket,(long)deal_ticket,
         requested_volume,trade.ResultVolume()
      )
   );

   TraceLifecycle(
      trade_id,"FILLED",
      StringFormat(
         "\\\"side\\\":\\\"SELL\\\",\\\"order_ticket\\\":\\\"%I64d\\\",\\\"deal_ticket\\\":\\\"%I64d\\\",\\\"fill_price\\\":%.10f,\\\"requested_volume\\\":%.8f,\\\"requested_sl\\\":%.10f,\\\"requested_tp\\\":%.10f",
         (long)order_ticket,(long)deal_ticket,fill_price,
         requested_volume,requested_sl,requested_tp
      )
   );

   if(CountOwnPositions()>0)
      TraceLifecycle(
         trade_id,"OPEN",
         StringFormat(
            "\\\"side\\\":\\\"SELL\\\",\\\"order_ticket\\\":\\\"%I64d\\\",\\\"deal_ticket\\\":\\\"%I64d\\\",\\\"position_count\\\":%d",
            (long)order_ticket,(long)deal_ticket,CountOwnPositions()
         )
      );
}}

// These functions intentionally use the same simple rolling arithmetic as
// the canonical Python research implementation, rather than platform RSI/ATR
// smoothing. This is required for deterministic signal parity.
double RSIAtShift(int shift)
{{
   if(shift<1 || Bars(_Symbol,PERIOD_M15)<shift+RSIPeriod+1) return EMPTY_VALUE;
   double gain=0.0, loss=0.0;
   for(int k=shift; k<shift+RSIPeriod; ++k)
   {{
      double delta=iClose(_Symbol,PERIOD_M15,k)-iClose(_Symbol,PERIOD_M15,k+1);
      if(delta>0.0) gain+=delta;
      else if(delta<0.0) loss-=delta;
   }}
   gain/=RSIPeriod;
   loss/=RSIPeriod;
   if(loss<=0.0) return EMPTY_VALUE;
   return 100.0-100.0/(1.0+gain/loss);
}}

double ATRAtShift(int shift)
{{
   if(shift<1 || Bars(_Symbol,PERIOD_M15)<shift+ATRPeriod+1) return EMPTY_VALUE;
   double sum=0.0;
   for(int k=shift; k<shift+ATRPeriod; ++k)
   {{
      double hi=iHigh(_Symbol,PERIOD_M15,k);
      double lo=iLow(_Symbol,PERIOD_M15,k);
      double prev=iClose(_Symbol,PERIOD_M15,k+1);
      double tr=MathMax(hi-lo,MathMax(MathAbs(hi-prev),MathAbs(lo-prev)));
      sum+=tr;
   }}
   return sum/ATRPeriod;
}}

void ParityLogSignal(double entry,double sl,double tp,double atr)
{{
   if(!ParityMode) return;
   if(parityHandle==INVALID_HANDLE)
   {{
      parityHandle=FileOpen(ParityFile,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
      if(parityHandle==INVALID_HANDLE) return;
      if(FileSize(parityHandle)==0) FileWrite(parityHandle,"candidate_id","event","timestamp","side","entry","sl","tp","atr");
      FileSeek(parityHandle,0,SEEK_END);
   }}
   FileWrite(parityHandle,MagicNumber-130000,"SIGNAL",TimeToString(iTime(_Symbol,PERIOD_M15,0),TIME_DATE|TIME_MINUTES),-1,DoubleToString(entry,_Digits),DoubleToString(sl,_Digits),DoubleToString(tp,_Digits),DoubleToString(atr,_Digits));
   FileFlush(parityHandle);
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

// Evaluate only the most recent two confirmed swing highs. The first pivot
// found from recent -> older is the newest confirmed pivot; the second is the
// previous pivot. This mirrors the causal Python signal construction.
bool BearishDivergence()
{{
   int bars=Bars(_Symbol,PERIOD_M15);
   int need=MathMin(bars,5000);
   if(need < 2*Pivot+RSIPeriod+5) return false;

   bool haveNewer=false;
   double newerHigh=0.0, newerRsi=0.0;
   bool haveOlder=false;
   double olderHigh=0.0, olderRsi=0.0;

   for(int s=Pivot+1; s<=need-Pivot-1; ++s)
   {{
      double h=iHigh(_Symbol,PERIOD_M15,s);
      double r=RSIAtShift(s);
      if(h<=0.0 || r==EMPTY_VALUE) continue;
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
         newerRsi=r;
         haveNewer=true;
         continue;
      }}

      olderHigh=h;
      olderRsi=r;
      haveOlder=true;
      break;
   }}

   if(!haveNewer || !haveOlder) return false;
   return newerHigh > olderHigh + MinDelta && newerRsi < olderRsi && newerRsi >= RSIHigh;
}}

double LotSize(double stopDistance,const double entry)
{{
   if(stopDistance<=0.0 || entry<=0.0) return 0.0;
   double balance=AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney=balance*RiskPercent/100.0;
   if(riskMoney<=0.0) return 0.0;

   // Use the platform's account-currency profit model for a 1-lot SELL
   // from the expected entry to the planned stop. This avoids hard-coding
   // contract/tick-value assumptions for different symbol configurations.
   double oneLotLoss=0.0;
   if(!OrderCalcProfit(ORDER_TYPE_SELL,_Symbol,1.0,entry,entry+stopDistance,oneLotLoss))
      return 0.0;
   oneLotLoss=MathAbs(oneLotLoss);
   if(oneLotLoss<=0.0) return 0.0;

   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double minLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maxLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   if(step<=0.0 || minLot<=0.0 || maxLot<minLot) return 0.0;

   double lots=riskMoney/oneLotLoss;
   // Fail closed when the risk-derived size is below broker minimum.
   // Never round upward to minLot because that could exceed RiskPercent.
   if(lots<minLot) return 0.0;
   lots=MathMin(maxLot,lots);
   lots=MathFloor(lots/step)*step;
   if(lots<minLot) return 0.0;
   return NormalizeDouble(lots,8);
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
      if(age>=ExpiryBars)
      {{
         ulong started=GetTickCount64();
         bool closed=trade.PositionClose(ticket);
         ulong elapsed=GetTickCount64()-started;
         ExecutionAuditLog("CLOSE_ATTEMPT","CLOSE",trade.ResultOrder(),trade.ResultDeal(),
                           0.0,trade.ResultVolume(),0.0,trade.ResultPrice(),0.0,0.0,0.0,0.0,
                           trade.ResultRetcode(),trade.ResultRetcodeDescription(),elapsed,
                           closed ? trade.ResultComment() : "PositionClose returned false");
      }}
   }}
}}

int OnInit()
{{
   trade.SetExpertMagicNumber(MagicNumber);
   if(!RequireRuntimeAuthorization) return INIT_FAILED;
   if(!(bool)MQLInfoInteger(MQL_TESTER) && !EnsureRuntimeTraceReady()) return INIT_FAILED;
   if(!trade.SetTypeFillingBySymbol(_Symbol)) return INIT_FAILED;
   return INIT_SUCCEEDED;
}}

void ExecutionAuditOpen()
{{
   if(executionAuditHandle!=INVALID_HANDLE) return;
   executionAuditHandle=FileOpen(ExecutionAuditFile,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
   if(executionAuditHandle==INVALID_HANDLE) return;
   if(FileSize(executionAuditHandle)==0)
      FileWrite(executionAuditHandle,"candidate_id","config_hash","event","timestamp_utc",
                "symbol","timeframe","side","order","deal","requested_volume","executed_volume",
                "requested_price","executed_price","sl","tp","spread_points","slippage_points",
                "retcode","retcode_description","elapsed_ms","comment");
   FileSeek(executionAuditHandle,0,SEEK_END);
}}

void ExecutionAuditLog(const string event,const string side,
                       const ulong order,const ulong deal,
                       const double requestedVolume,const double executedVolume,
                       const double requestedPrice,const double executedPrice,
                       const double sl,const double tp,
                       const double spreadPoints,const double slippagePoints,
                       const long retcode,const string retcode_description,
                       const ulong elapsed_ms,const string comment)
{{
   ExecutionAuditOpen();
   if(executionAuditHandle==INVALID_HANDLE) return;
   FileWrite(executionAuditHandle,MagicNumber-130000,ConfigHash,event,
             TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),_Symbol,"M15",side,
             (string)order,(string)deal,
             DoubleToString(requestedVolume,8),DoubleToString(executedVolume,8),
             DoubleToString(requestedPrice,_Digits),DoubleToString(executedPrice,_Digits),
             DoubleToString(sl,_Digits),DoubleToString(tp,_Digits),
             DoubleToString(spreadPoints,2),DoubleToString(slippagePoints,2),
             (string)retcode,retcode_description,(string)elapsed_ms,comment);
   FileFlush(executionAuditHandle);
}}

void OnDeinit(const int reason)
{{
   if(parityHandle!=INVALID_HANDLE) FileClose(parityHandle);
   if(executionAuditHandle!=INVALID_HANDLE) FileClose(executionAuditHandle);
}}

void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result)
{{
   if(trans.symbol!=_Symbol) return;
   long magic=0;
   if(trans.deal>0 && HistoryDealSelect(trans.deal))
      magic=(long)HistoryDealGetInteger(trans.deal,DEAL_MAGIC);
   else if(trans.order>0 && HistoryOrderSelect(trans.order))
      magic=(long)HistoryOrderGetInteger(trans.order,ORDER_MAGIC);
   else
      magic=(long)request.magic;
   if(magic!=MagicNumber) return;
   string transactionComment=result.comment;
   if(trans.deal>0 && HistoryDealSelect(trans.deal))
      transactionComment=HistoryDealGetString(trans.deal,DEAL_COMMENT);
   else if(trans.order>0 && HistoryOrderSelect(trans.order))
      transactionComment=HistoryOrderGetString(trans.order,ORDER_COMMENT);
   string side="UNKNOWN";
   if(trans.deal>0 && HistoryDealSelect(trans.deal))
      side=(HistoryDealGetInteger(trans.deal,DEAL_TYPE)==DEAL_TYPE_SELL ? "SELL" : "OTHER");
   else if(trans.order>0 && HistoryOrderSelect(trans.order))
      side=(HistoryOrderGetInteger(trans.order,ORDER_TYPE)==ORDER_TYPE_SELL ? "SELL" : "OTHER");
   ExecutionAuditLog("TRADE_TRANSACTION",side,trans.order,trans.deal,
                     0.0,trans.volume,0.0,trans.price,0.0,0.0,0.0,0.0,
                     result.retcode,result.comment,0,transactionComment);

   if(trans.deal>0 && HistoryDealSelect(trans.deal))
   {{
      long entry=HistoryDealGetInteger(trans.deal,DEAL_ENTRY);
      if(entry==DEAL_ENTRY_OUT || entry==DEAL_ENTRY_INOUT)
      {{
         if(CountOwnPositions()==0 && StringLen(active_trace_trade_id)>0)
         {{
            double exit_price=HistoryDealGetDouble(trans.deal,DEAL_PRICE);
            double volume=HistoryDealGetDouble(trans.deal,DEAL_VOLUME);
            double profit=HistoryDealGetDouble(trans.deal,DEAL_PROFIT);
            double swap=HistoryDealGetDouble(trans.deal,DEAL_SWAP);
            double commission=HistoryDealGetDouble(trans.deal,DEAL_COMMISSION);
            TraceLifecycle(
               active_trace_trade_id,"CLOSED",
               StringFormat("\\\"deal_ticket\\\":\\\"%I64d\\\",\\\"position_id\\\":\\\"%I64d\\\",\\\"exit_price\\\":%.10f,\\\"volume\\\":%.8f,\\\"profit\\\":%.8f,\\\"swap\\\":%.8f,\\\"commission\\\":%.8f",
                            (long)trans.deal,
                            (long)HistoryDealGetInteger(trans.deal,DEAL_POSITION_ID),
                            exit_price,volume,profit,swap,commission)
            );
            active_trace_trade_id="";
         }}
      }}
   }}
}}

bool DemoKillSwitchAllowed()
{{
   int h=FileOpen("g13_demo_kill_switch.txt",FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(h==INVALID_HANDLE) return false;
   string state=FileReadString(h);
   FileClose(h);
   return state=="ALLOW";
}}

bool HasOtherG13Position()
{{
   for(int i=PositionsTotal()-1;i>=0;--i)
   {{
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      long magic=PositionGetInteger(POSITION_MAGIC);
      if(magic>=130000+2 && magic<=130000+48 && magic!=MagicNumber) return true;
   }}
   return false;
}}

bool DemoTradingExecutionAllowed()
{{
   // Strategy Tester remains available for research/backtest simulation.
   if((bool)MQLInfoInteger(MQL_TESTER)) return true;
   // Outside Tester, order submission is strictly Demo-only and opt-in.
   if(!DemoTradingAuthorized) return false;
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;
   // Broker/terminal/program/account permissions must all allow trading.
   if(!TerminalInfoInteger(TERMINAL_CONNECTED)) return false;
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) return false;
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED)) return false;
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) return false;
   if(!AccountInfoInteger(ACCOUNT_TRADE_EXPERT)) return false;
   // G13 submits only market SELL orders with SL/TP.
   int trade_mode=(int)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE);
   if(trade_mode!=SYMBOL_TRADE_MODE_FULL && trade_mode!=SYMBOL_TRADE_MODE_SHORTONLY) return false;
   long order_mode=SymbolInfoInteger(_Symbol,SYMBOL_ORDER_MODE);
   if((order_mode & SYMBOL_ORDER_MARKET)==0) return false;
   if((order_mode & SYMBOL_ORDER_SL)==0) return false;
   if((order_mode & SYMBOL_ORDER_TP)==0) return false;
   // Shared kill-switch file must explicitly contain ALLOW; missing file fails closed.
   if(!DemoKillSwitchAllowed()) return false;
   // Demo cluster uses one position at a time across all G13 candidate EAs.
   if(HasOtherG13Position()) return false;
   return true;
}}

void OnTick()
{{
   if(!IsNewBar()) return;

   // Signal-only parity path: log the deterministic signal and do not let
   // position state, lot sizing, broker rules, or order execution affect it.
   if(ParityMode)
   {{
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
   }}

   // Normal research/backtest execution path. Outside Tester this is Demo-only.
   if(!DemoTradingExecutionAllowed()) return;
   ManageExpiry();
   if(CountOwnPositions()>0) return;
   if(!BearishDivergence()) return;

   double atr=ATRAtShift(1);
   if(atr==EMPTY_VALUE || atr<=0.0) return;
   double risk=ATRMult*atr;
   // In the real Demo execution path, SELL uses the current Bid snapshot as
   // the planned/requested execution price. Risk, SL/TP, and slippage are
   // therefore tied to the same observable quote rather than a historical
   // bar-open proxy used only by the deterministic research path.
   MqlTick quote;
   if(!SymbolInfoTick(_Symbol,quote)) return;
   double bid=quote.bid;
   double ask=quote.ask;
   if(bid<=0.0 || ask<=0.0 || ask<bid) return;
   double entry=bid;
   double sl=entry+risk;
   double tp=entry-RR*risk;
   long stopsLevel=(long)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   if(stopsLevel<0) return;
   if(risk < (double)stopsLevel*_Point) return;
   if(RR<=0.0) return;
   string trace_trade_id=BuildTraceTradeId(iTime(_Symbol,PERIOD_M15,1));
   if(!(bool)MQLInfoInteger(MQL_TESTER))
   {{
      if(!VerifyRuntimeAuthorization(trace_trade_id,false)) return;
      if(!BeginRuntimeAuthorizationAttempt(trace_trade_id)) return;
   }}
   double lots=0.0;
   if((bool)MQLInfoInteger(MQL_TESTER))
   {{
      // Tester path: preserve deterministic research/backtest sizing without
      // requiring runtime authorization artifacts.
      lots=LotSize(risk,entry);
   }}
   else
   {{
      // Demo path: runtime authorization independently caps risk before submit.
      if(runtime_reserved_risk<=0.0) return;
      double authorized_risk_percent=MathMin(RiskPercent/100.0,runtime_reserved_risk);
      double riskMoney=AccountInfoDouble(ACCOUNT_BALANCE)*authorized_risk_percent;
      double oneLotLoss=0.0;
      if(!OrderCalcProfit(ORDER_TYPE_SELL,_Symbol,1.0,entry,entry+risk,oneLotLoss)) return;
      oneLotLoss=MathAbs(oneLotLoss);
      if(oneLotLoss<=0.0) return;
      lots=NormalizeDouble(riskMoney/oneLotLoss,8);
      double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
      double minLot=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
      if(step<=0.0 || minLot<=0.0 || lots<minLot) return;
      lots=MathFloor(lots/step)*step;
      if(lots<minLot) return;
   }}
   if(lots<=0.0) return;
   if(!(bool)MQLInfoInteger(MQL_TESTER))
      TraceLifecycle(
         trace_trade_id,"ORDER_SUBMITTED",
         StringFormat("\\\"side\\\":\\\"SELL\\\",\\\"requested_volume\\\":%.8f,\\\"requested_price\\\":%.10f,\\\"requested_sl\\\":%.10f,\\\"requested_tp\\\":%.10f,\\\"order_ticket\\\":\\\"0\\\"",
                      lots,entry,sl,tp)
      );
   double spreadPoints=(ask-bid)/_Point;
   ulong started=GetTickCount64();
   bool accepted=trade.Sell(lots,_Symbol,entry,sl,tp,"ForexAI-G13-{cid:02d}");
   ulong elapsed=GetTickCount64()-started;
   double executedPrice=trade.ResultPrice();
   double slippagePoints=(executedPrice>0.0 ? (executedPrice-entry)/_Point : 0.0);
   string executionComment=(accepted ? trade.ResultComment() : "CTrade Sell returned false");
    ExecutionAuditLog("ORDER_ATTEMPT","SELL",trade.ResultOrder(),trade.ResultDeal(),
                     lots,trade.ResultVolume(),entry,executedPrice,sl,tp,
                     spreadPoints,slippagePoints,
                     trade.ResultRetcode(),trade.ResultRetcodeDescription(),
                     elapsed,executionComment);
   if(!accepted)
   {{
      TraceRecord(
         trace_trade_id,"BROKER_OUTCOME_UNKNOWN","ORDER_SUBMITTED",
         StringFormat("\\\"retcode\\\":%u,\\\"order_ticket\\\":\\\"%I64d\\\",\\\"deal_ticket\\\":\\\"%I64d\\\",\\\"requested_volume\\\":%.8f",
                      trade.ResultRetcode(),(long)trade.ResultOrder(),(long)trade.ResultDeal(),lots)
      );
      runtime_authorization_healthy=false;
      return;
   }}
   if(trade.ResultRetcode()!=TRADE_RETCODE_DONE || trade.ResultOrder()==0 || trade.ResultDeal()==0 ||
      trade.ResultVolume()<=0.0 || MathAbs(trade.ResultVolume()-lots)>1e-9)
   {{
      TraceRecord(
         trace_trade_id,"BROKER_OUTCOME_UNKNOWN","ORDER_SUBMITTED",
         StringFormat("\\\"retcode\\\":%u,\\\"order_ticket\\\":\\\"%I64d\\\",\\\"deal_ticket\\\":\\\"%I64d\\\",\\\"requested_volume\\\":%.8f",
                      trade.ResultRetcode(),(long)trade.ResultOrder(),(long)trade.ResultDeal(),lots)
      );
      runtime_authorization_healthy=false;
      return;
   }}
   if(!(bool)MQLInfoInteger(MQL_TESTER))
   {{
      TraceSuccessfulEntry(trace_trade_id,lots,sl,tp);
      if(!MarkRuntimeAuthorizationConsumed(trace_trade_id)) return;
   }}
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
    manifest_candidates={int(c['candidate_id']):c for c in manifest['candidates']}
    assert len(manifest_candidates)==15
    assert set(manifest_candidates)==set(ids)
    cands={int(c['candidate_id']):c for c in handoff['candidates']}
    assert set(cands)>=set(ids)
    out_dir.mkdir(parents=True,exist_ok=True)
    paths=[]
    for cid in ids:
        handoff_candidate=cands[cid]
        manifest_candidate=manifest_candidates[cid]
        assert manifest_candidate['config_hash']==handoff_candidate['config_hash']
        assert manifest_candidate['params']==handoff_candidate['params']
        assert manifest_candidate['config_hash']==canonical_hash(manifest_candidate['params'])
        c=handoff_candidate
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
