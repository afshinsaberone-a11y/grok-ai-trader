//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5   GRK-FX-2026-051                       |
//| Regime switch: Trend pullback / Squeeze retest / Range fade      |
//| HTF MA + DI + session + Friday/weekend + ATR floor + halt        |
//| Regime hysteresis + MaxTradesPerDay + MaxHoldBars + ProfitLock   |
//| Wide-spread half risk                                            |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "51.0"
#include <Trade/Trade.mqh>

input double RiskPercent        = 0.5;
input double DailyLossLimit     = 2.0;
input double DailyProfitLock    = 2.0;
input int    MaxPositions       = 1;
input int    MaxTradesPerDay    = 3;
input int    ADX_Period         = 14;
input int    ADX_Trend          = 23;
input int    ADX_Range          = 17;
input int    RegimeConfirmBars  = 2;
input int    MA200_Period       = 200;
input ENUM_TIMEFRAMES HTF       = PERIOD_H4;
input int    ATR_Period         = 14;
input int    BB_Period          = 20;
input double BB_Dev             = 2.0;
input double ATR_SL_Mult        = 1.45;
input double RR_Target          = 1.9;
input double SpreadMultMax      = 1.3;
input bool   WideSpreadHalfRisk = true;
input int    ConsecutiveHalt    = 3;
input int    HaltCooldownBars   = 8;
input int    SessionStartHour   = 7;
input int    SessionEndHour     = 16;
input int    FridayCutoffHour   = 16;
input int    MinAtrSpreadMult   = 6;
input int    NewsBlackoutStart  = -1;
input int    NewsBlackoutEnd    = -1;
input int    MaxHoldBars        = 30;
input long   Magic              = 2026051;
input string TraceFileName      = "";

CTrade trade;
int adx_h, ma_h, htf_ma_h, atr_h, bb_h;
int consec_losses = 0;
int halt_bars_left = 0;
int trades_today = 0;
int last_regime_raw = 0;
int last_regime_stable = 0;
int regime_same_count = 0;
datetime day_stamp = 0;
double day_start_equity = 0;
string active_trace_trade_id = "";

string TraceFile()
{
  if(StringLen(TraceFileName) > 0)
    return TraceFileName;
  return StringFormat("ForexAI_RuntimeTrace_%I64d_%s.jsonl", Magic, _Symbol);
}

string TraceIsoUtc(const datetime value)
{
  MqlDateTime t;
  TimeToStruct(value, t);
  return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d+00:00",
                      t.year, t.mon, t.day, t.hour, t.min, t.sec);
}

string TraceBrokerIso(const datetime value)
{
  MqlDateTime t;
  TimeToStruct(value, t);
  return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",
                      t.year, t.mon, t.day, t.hour, t.min, t.sec);
}

string TraceJsonEscape(string value)
{
  StringReplace(value, "\\", "\\\\");
  StringReplace(value, "\"", "\\\"");
  StringReplace(value, "\r", "\\r");
  StringReplace(value, "\n", "\\n");
  return value;
}

void TraceLifecycle(const string trade_id,
                    const string state,
                    const string payload_fields)
{
  if(StringLen(trade_id) == 0 || StringLen(state) == 0)
    return;

  int handle = FileOpen(
      TraceFile(),
      FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON |
      FILE_SHARE_READ | FILE_SHARE_WRITE
  );
  if(handle == INVALID_HANDLE)
    return;

  FileSeek(handle, 0, SEEK_END);

  string broker_ts = TraceBrokerIso(TimeCurrent());
  string payload = StringFormat(
      "\"broker_timestamp\":\"%s\"",
      TraceJsonEscape(broker_ts)
  );
  if(StringLen(payload_fields) > 0)
    payload += "," + payload_fields;

  string event_id = "MQL5-" + trade_id + "-" + state;
  string row = StringFormat(
      "{\"schema\":\"forexai.runtime_trace.v1\","
      "\"source\":\"MQL5\","
      "\"trade_id\":\"%s\","
      "\"event_id\":\"%s\","
      "\"event_type\":\"%s\","
      "\"idempotency_key\":\"%s\","
      "\"timestamp_utc\":\"%s\","
      "\"state\":\"%s\","
      "\"payload\":{%s}}\n",
      TraceJsonEscape(trade_id),
      TraceJsonEscape(event_id),
      TraceJsonEscape(state),
      TraceJsonEscape(event_id),
      TraceIsoUtc(TimeGMT()),
      TraceJsonEscape(state),
      payload
  );

  FileWriteString(handle, row);
  FileFlush(handle);
  FileClose(handle);
}

string BuildTraceTradeId(const bool is_buy, const datetime signal_bar_time)
{
  string side = is_buy ? "B" : "S";
  return StringFormat(
      "T-%I64d-%s-%I64d-%s",
      Magic, _Symbol, (long)signal_bar_time, side
  );
}

datetime SignalBarForEntryTime(const datetime entry_time)
{
  int shift = iBarShift(_Symbol, PERIOD_CURRENT, entry_time, false);
  if(shift < 0)
    return 0;
  int signal_shift = shift + 1;
  if(iBars(_Symbol, PERIOD_CURRENT) <= signal_shift)
    return 0;
  return iTime(_Symbol, PERIOD_CURRENT, signal_shift);
}

string RecoverTraceTradeId(const ulong position_id)
{
  if(StringLen(active_trace_trade_id) > 0)
    return active_trace_trade_id;

  if(position_id == 0 || !HistorySelect(0, TimeCurrent()))
    return "";

  datetime earliest = 0;
  long direction = -1;
  int total = HistoryDealsTotal();
  for(int i=0; i<total; ++i)
  {
    ulong deal_ticket = HistoryDealGetTicket(i);
    if(deal_ticket == 0)
      continue;
    if((ulong)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID) != position_id)
      continue;
    if(HistoryDealGetString(deal_ticket, DEAL_SYMBOL) != _Symbol)
      continue;
    if((long)HistoryDealGetInteger(deal_ticket, DEAL_MAGIC) != Magic)
      continue;

    long entry = HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
    if(entry != DEAL_ENTRY_IN)
      continue;

    datetime deal_time = (datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME);
    if(earliest == 0 || deal_time < earliest)
    {
      earliest = deal_time;
      direction = HistoryDealGetInteger(deal_ticket, DEAL_TYPE);
    }
  }

  if(earliest == 0 || direction < 0)
    return "";

  datetime signal_bar = SignalBarForEntryTime(earliest);
  return BuildTraceTradeId(direction == DEAL_TYPE_BUY, signal_bar);
}

void TraceSuccessfulEntry(const string trade_id,
                           const bool is_buy,
                           const double requested_sl,
                           const double requested_tp,
                           const double requested_volume)
{
  active_trace_trade_id = trade_id;

  ulong deal_ticket = trade.ResultDeal();
  uint retcode = trade.ResultRetcode();
  double fill_price = is_buy
      ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
      : SymbolInfoDouble(_Symbol, SYMBOL_BID);
  if(deal_ticket > 0 && HistoryDealSelect(deal_ticket))
    fill_price = HistoryDealGetDouble(deal_ticket, DEAL_PRICE);

  string side = is_buy ? "BUY" : "SELL";
  string submitted_fields = StringFormat(
      "\"side\":\"%s\",\"retcode\":%u",
      side, retcode
  );
  TraceLifecycle(trade_id, "ORDER_SUBMITTED", submitted_fields);

  string accepted_fields = StringFormat(
      "\"side\":\"%s\",\"retcode\":%u,\"deal_ticket\":\"%I64d\"",
      side, retcode, (long)deal_ticket
  );
  TraceLifecycle(trade_id, "ACCEPTED", accepted_fields);

  string filled_fields = StringFormat(
      "\"side\":\"%s\",\"deal_ticket\":\"%I64d\","
      "\"fill_price\":%.10f,\"requested_volume\":%.8f,"
      "\"requested_sl\":%.10f,\"requested_tp\":%.10f",
      side, (long)deal_ticket, fill_price, requested_volume,
      requested_sl, requested_tp
  );
  TraceLifecycle(trade_id, "FILLED", filled_fields);

  if(PositionsByMagic() > 0)
  {
    string open_fields = StringFormat(
        "\"side\":\"%s\",\"deal_ticket\":\"%I64d\",\"position_count\":%d",
        side, (long)deal_ticket, PositionsByMagic()
    );
    TraceLifecycle(trade_id, "OPEN", open_fields);
  }
}

string SafetyKey(const string suffix)
{
  return "ForexAI.v1." + IntegerToString((int)Magic) + "." + _Symbol + "." + suffix;
}

void PersistSafetyState()
{
  GlobalVariableSet(SafetyKey("consec_losses"), (double)consec_losses);
  GlobalVariableSet(SafetyKey("halt_bars_left"), (double)halt_bars_left);
  GlobalVariableSet(SafetyKey("trades_today"), (double)trades_today);
  GlobalVariableSet(SafetyKey("day_stamp"), (double)day_stamp);
  GlobalVariableSet(SafetyKey("day_start_equity"), day_start_equity);
}

void LoadSafetyState()
{
  bool found = GlobalVariableCheck(SafetyKey("day_stamp"));
  if(!found)
  {
    consec_losses = 0;
    halt_bars_left = 0;
    trades_today = 0;
    day_stamp = TimeCurrent();
    day_start_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    PersistSafetyState();
    return;
  }

  consec_losses = (int)GlobalVariableGet(SafetyKey("consec_losses"));
  halt_bars_left = (int)GlobalVariableGet(SafetyKey("halt_bars_left"));
  trades_today = (int)GlobalVariableGet(SafetyKey("trades_today"));
  day_stamp = (datetime)GlobalVariableGet(SafetyKey("day_stamp"));
  day_start_equity = GlobalVariableGet(SafetyKey("day_start_equity"));
}
int OnInit()
{
  if(RiskPercent > 0.6) return INIT_FAILED;
  if(MaxPositions != 1) return INIT_FAILED;
  if(DailyLossLimit <= 0 || ATR_SL_Mult <= 0 || RR_Target < 1.0) return INIT_FAILED;
  if(MaxTradesPerDay < 1) return INIT_FAILED;
  if(MaxHoldBars < 1) return INIT_FAILED;
  if(DailyProfitLock < 0) return INIT_FAILED;

  adx_h    = iADX(_Symbol, PERIOD_CURRENT, ADX_Period);
  ma_h     = iMA(_Symbol, PERIOD_CURRENT, MA200_Period, 0, MODE_SMA, PRICE_CLOSE);
  htf_ma_h = iMA(_Symbol, HTF, MA200_Period, 0, MODE_SMA, PRICE_CLOSE);
  atr_h    = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
  bb_h     = iBands(_Symbol, PERIOD_CURRENT, BB_Period, 0, BB_Dev, PRICE_CLOSE);

  if(adx_h==INVALID_HANDLE || ma_h==INVALID_HANDLE || htf_ma_h==INVALID_HANDLE ||
     atr_h==INVALID_HANDLE || bb_h==INVALID_HANDLE)
    return INIT_FAILED;

  trade.SetExpertMagicNumber((ulong)Magic);
  trade.SetDeviationInPoints(20);
  trade.SetTypeFillingBySymbol(_Symbol);
  LoadSafetyState();
  RollDayIfNeeded();
  return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
  PersistSafetyState();
  if(adx_h!=INVALID_HANDLE)    IndicatorRelease(adx_h);
  if(ma_h!=INVALID_HANDLE)     IndicatorRelease(ma_h);
  if(htf_ma_h!=INVALID_HANDLE) IndicatorRelease(htf_ma_h);
  if(atr_h!=INVALID_HANDLE)    IndicatorRelease(atr_h);
  if(bb_h!=INVALID_HANDLE)    IndicatorRelease(bb_h);
}

int PositionsByMagic()
{
  int n = 0;
  for(int i=PositionsTotal()-1; i>=0; --i)
  {
    ulong ticket = PositionGetTicket(i);
    if(ticket==0) continue;
    if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
    if((long)PositionGetInteger(POSITION_MAGIC)!=Magic) continue;
    n++;
  }
  return n;
}

void TimeStopStale()
{
  if(MaxHoldBars <= 0) return;
  for(int i=PositionsTotal()-1; i>=0; --i)
  {
    ulong ticket = PositionGetTicket(i);
    if(ticket==0) continue;
    if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
    if((long)PositionGetInteger(POSITION_MAGIC)!=Magic) continue;
    datetime opened = (datetime)PositionGetInteger(POSITION_TIME);
    int bars = iBarShift(_Symbol, PERIOD_CURRENT, opened, false);
    if(bars >= MaxHoldBars)
    {
      bool submitted = trade.PositionClose(ticket);
      if(!submitted) continue;
      uint rc = trade.ResultRetcode();
      if(rc != TRADE_RETCODE_DONE && rc != TRADE_RETCODE_DONE_PARTIAL)
        continue;
      ulong position_id = (ulong)PositionGetInteger(POSITION_IDENTIFIER);
      string trace_trade_id = RecoverTraceTradeId(position_id);
      if(StringLen(trace_trade_id) > 0)
      {
        TraceLifecycle(
            trace_trade_id,
            "MANAGED",
            StringFormat(""reason":"MAX_HOLD_BARS","position_ticket":"%I64d","position_id":"%I64d"",
                         (long)ticket, (long)position_id)
        );
      }
    }
  }
}

double CurrentSpreadPrice()
{
  return (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
}

bool SpreadIsWide()
{
  double atr[];
  ArraySetAsSeries(atr, true);
  if(CopyBuffer(atr_h, 0, 1, 5, atr) < 5) return true;
  if(atr[1] <= 0) return true;
  double spr = CurrentSpreadPrice();
  return spr > SpreadMultMax * atr[1] * 0.08;
}

bool SpreadOk()
{
  double atr[];
  ArraySetAsSeries(atr, true);
  if(CopyBuffer(atr_h, 0, 1, 5, atr) < 5) return false;
  if(atr[1] <= 0) return false;
  double spr = CurrentSpreadPrice();
  if(spr <= 0) return false;
  if(atr[1] < MinAtrSpreadMult * spr) return false;
  return spr <= SpreadMultMax * atr[1] * 0.12;
}

bool SessionOk()
{
  MqlDateTime t;
  TimeToStruct(TimeCurrent(), t);
  if(t.day_of_week == 0 || t.day_of_week == 6) return false;
  if(t.day_of_week == 5 && t.hour >= FridayCutoffHour) return false;
  if(SessionStartHour == SessionEndHour) return true;
  if(SessionStartHour < SessionEndHour)
    return (t.hour >= SessionStartHour && t.hour < SessionEndHour);
  return (t.hour >= SessionStartHour || t.hour < SessionEndHour);
}

bool NewsBlackoutOk()
{
  if(NewsBlackoutStart < 0 || NewsBlackoutEnd < 0) return true;
  MqlDateTime t;
  TimeToStruct(TimeCurrent(), t);
  if(NewsBlackoutStart == NewsBlackoutEnd) return true;
  if(NewsBlackoutStart < NewsBlackoutEnd)
    return !(t.hour >= NewsBlackoutStart && t.hour < NewsBlackoutEnd);
  return !(t.hour >= NewsBlackoutStart || t.hour < NewsBlackoutEnd);
}

void RollDayIfNeeded()
{
  MqlDateTime nowt, then;
  TimeToStruct(TimeCurrent(), nowt);
  TimeToStruct(day_stamp, then);
  if(nowt.day!=then.day || nowt.mon!=then.mon || nowt.year!=then.year)
  {
    day_stamp = TimeCurrent();
    day_start_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    consec_losses = 0;
    trades_today = 0;
    halt_bars_left = 0;
    PersistSafetyState();
  }
}

bool DailyLossOk()
{
  RollDayIfNeeded();
  double eq = AccountInfoDouble(ACCOUNT_EQUITY);
  if(day_start_equity <= 0) return false;
  return 100.0 * (day_start_equity - eq) / day_start_equity < DailyLossLimit;
}

bool DailyProfitLockOk()
{
  RollDayIfNeeded();
  if(DailyProfitLock <= 0) return true;
  double eq = AccountInfoDouble(ACCOUNT_EQUITY);
  if(day_start_equity <= 0) return false;
  return 100.0 * (eq - day_start_equity) / day_start_equity < DailyProfitLock;
}

int RegimeRaw()
{
  double adx[];
  ArraySetAsSeries(adx, true);
  if(CopyBuffer(adx_h, 0, 1, 3, adx) < 3) return 0;
  if(adx[1] >= ADX_Trend) return 1;
  if(adx[1] <= ADX_Range) return -1;
  return 2;
}

int Regime()
{
  int raw = RegimeRaw();
  if(raw == last_regime_raw)
    regime_same_count++;
  else
  {
    last_regime_raw = raw;
    regime_same_count = 1;
  }
  int need = RegimeConfirmBars < 1 ? 1 : RegimeConfirmBars;
  if(regime_same_count >= need)
    last_regime_stable = raw;
  return last_regime_stable;
}

bool DiBull()
{
  double pdi[], mdi[];
  ArraySetAsSeries(pdi, true);
  ArraySetAsSeries(mdi, true);
  if(CopyBuffer(adx_h, 1, 1, 2, pdi) < 2) return false;
  if(CopyBuffer(adx_h, 2, 1, 2, mdi) < 2) return false;
  return pdi[1] > mdi[1];
}

bool AdxRising()
{
  double adx[];
  ArraySetAsSeries(adx, true);
  if(CopyBuffer(adx_h, 0, 1, 3, adx) < 3) return false;
  return adx[1] > adx[2];
}

bool HtfBull()
{
  double ma[], close[];
  ArraySetAsSeries(ma, true);
  ArraySetAsSeries(close, true);
  if(CopyBuffer(htf_ma_h, 0, 1, 2, ma) < 2) return false;
  if(CopyClose(_Symbol, HTF, 1, 2, close) < 2) return false;
  return close[1] > ma[1];
}

double NormalizeVol(double vol)
{
  double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
  double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
  double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
  if(step <= 0) step = 0.01;
  vol = MathFloor(vol / step) * step;
  if(vol < vmin) return 0;
  if(vol > vmax) vol = vmax;
  return vol;
}

double EffectiveRiskPercent()
{
  if(WideSpreadHalfRisk && SpreadIsWide())
    return RiskPercent * 0.5;
  return RiskPercent;
}

double PositionSize(double sl_price, bool is_buy)
{
  double price = is_buy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                        : SymbolInfoDouble(_Symbol, SYMBOL_BID);
  double sl_points = MathAbs(price - sl_price);
  double risk_money = AccountInfoDouble(ACCOUNT_EQUITY) * EffectiveRiskPercent() / 100.0;
  double tick_val = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
  double tick_sz  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
  if(sl_points <= 0 || tick_val <= 0 || tick_sz <= 0) return 0;
  return NormalizeVol(risk_money / (sl_points / tick_sz * tick_val));
}

bool TradeModeAllows(const bool is_buy)
{
  int trade_mode = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_MODE);
  if(trade_mode == SYMBOL_TRADE_MODE_DISABLED || trade_mode == SYMBOL_TRADE_MODE_CLOSEONLY)
    return false;
  if(is_buy && trade_mode == SYMBOL_TRADE_MODE_SHORTONLY)
    return false;
  if(!is_buy && trade_mode == SYMBOL_TRADE_MODE_LONGONLY)
    return false;

  int order_mode = (int)SymbolInfoInteger(_Symbol, SYMBOL_ORDER_MODE);
  int required = SYMBOL_ORDER_MARKET | SYMBOL_ORDER_SL | SYMBOL_ORDER_TP;
  return (order_mode & required) == required;
}

bool StopsValid(double sl, double tp, bool is_buy)
{
  double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
  int stops = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
  int freeze = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
  double min_dist = MathMax(stops, freeze) * point;
  if(min_dist <= 0) min_dist = 10 * point;
  if(is_buy)
  {
    if(sl >= bid - min_dist) return false;
    if(tp <= ask + min_dist) return false;
  }
  else
  {
    if(sl <= ask + min_dist) return false;
    if(tp >= bid - min_dist) return false;
  }
  return true;
}

bool TradeExecutionAccepted()
{
  uint rc = trade.ResultRetcode();
  ulong deal = trade.ResultDeal();
  return (rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_DONE_PARTIAL) && deal > 0;
}

bool SendBuy(double sl, double tp, const string cmt)
{
  if(!TradeModeAllows(true)) return false;
  if(trades_today >= MaxTradesPerDay) return false;
  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
  if(!StopsValid(sl, tp, true)) return false;
  double vol = PositionSize(sl, true);
  if(vol <= 0) return false;
  string trace_trade_id = BuildTraceTradeId(true, iTime(_Symbol, PERIOD_CURRENT, 1));
  bool submitted = trade.Buy(vol, _Symbol, ask, sl, tp, cmt);
  if(!submitted) return false;
  if(!TradeExecutionAccepted()) return false;
  TraceSuccessfulEntry(trace_trade_id, true, sl, tp, vol);
  trades_today++;
  return true;
}

bool SendSell(double sl, double tp, const string cmt)
{
  if(!TradeModeAllows(false)) return false;
  if(trades_today >= MaxTradesPerDay) return false;
  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
  if(!StopsValid(sl, tp, false)) return false;
  double vol = PositionSize(sl, false);
  if(vol <= 0) return false;
  string trace_trade_id = BuildTraceTradeId(false, iTime(_Symbol, PERIOD_CURRENT, 1));
  bool submitted = trade.Sell(vol, _Symbol, bid, sl, tp, cmt);
  if(!submitted) return false;
  if(!TradeExecutionAccepted()) return false;
  TraceSuccessfulEntry(trace_trade_id, false, sl, tp, vol);
  trades_today++;
  return true;
}

bool SqueezeThenExpand()
{
  double atr[];
  ArraySetAsSeries(atr, true);
  if(CopyBuffer(atr_h, 0, 1, 30, atr) < 30) return false;
  double recent = atr[1];
  double older = 0;
  for(int i=10; i<30; ++i) older += atr[i];
  older /= 20.0;
  return older > 0 && recent > older * 1.12 && atr[8] < older * 0.88;
}

void TryTrendPullback()
{
  double ma[], atr[], close[];
  ArraySetAsSeries(ma, true);
  ArraySetAsSeries(atr, true);
  ArraySetAsSeries(close, true);
  if(CopyBuffer(ma_h, 0, 1, 3, ma) < 3) return;
  if(CopyBuffer(atr_h, 0, 1, 3, atr) < 3) return;
  if(CopyClose(_Symbol, PERIOD_CURRENT, 1, 3, close) < 3) return;

  bool long_ok  = close[1] > ma[1] && close[1] <= ma[1] + atr[1] * 0.55 && DiBull() && HtfBull();
  bool short_ok = close[1] < ma[1] && close[1] >= ma[1] - atr[1] * 0.55 && !DiBull() && !HtfBull();

  if(long_ok)
  {
    double sl = SymbolInfoDouble(_Symbol, SYMBOL_BID) - ATR_SL_Mult * atr[1];
    double tp = SymbolInfoDouble(_Symbol, SYMBOL_BID) + RR_Target * ATR_SL_Mult * atr[1];
    SendBuy(sl, tp, "A-trend");
  }
  else if(short_ok)
  {
    double sl = SymbolInfoDouble(_Symbol, SYMBOL_ASK) + ATR_SL_Mult * atr[1];
    double tp = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - RR_Target * ATR_SL_Mult * atr[1];
    SendSell(sl, tp, "A-trend");
  }
}

void TrySqueezeBreak()
{
  if(!SqueezeThenExpand()) return;
  if(!AdxRising()) return;
  double bb_u[], bb_l[], atr[], close[];
  ArraySetAsSeries(bb_u, true);
  ArraySetAsSeries(bb_l, true);
  ArraySetAsSeries(atr, true);
  ArraySetAsSeries(close, true);
  if(CopyBuffer(bb_h, 1, 1, 4, bb_u) < 4) return;
  if(CopyBuffer(bb_h, 2, 1, 4, bb_l) < 4) return;
  if(CopyBuffer(atr_h, 0, 1, 3, atr) < 3) return;
  if(CopyClose(_Symbol, PERIOD_CURRENT, 1, 4, close) < 4) return;

  if(close[2] > bb_u[2] && close[1] <= close[2] && close[1] >= bb_u[1] && DiBull())
  {
    double sl = SymbolInfoDouble(_Symbol, SYMBOL_BID) - ATR_SL_Mult * atr[1];
    double tp = SymbolInfoDouble(_Symbol, SYMBOL_BID) + RR_Target * ATR_SL_Mult * atr[1];
    SendBuy(sl, tp, "B-squeeze");
  }
  else if(close[2] < bb_l[2] && close[1] >= close[2] && close[1] <= bb_l[1] && !DiBull())
  {
    double sl = SymbolInfoDouble(_Symbol, SYMBOL_ASK) + ATR_SL_Mult * atr[1];
    double tp = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - RR_Target * ATR_SL_Mult * atr[1];
    SendSell(sl, tp, "B-squeeze");
  }
}

void TryRangeFade()
{
  double bb_u[], bb_l[], atr[], close[], high[], low[];
  ArraySetAsSeries(bb_u, true);
  ArraySetAsSeries(bb_l, true);
  ArraySetAsSeries(atr, true);
  ArraySetAsSeries(close, true);
  ArraySetAsSeries(high, true);
  ArraySetAsSeries(low, true);
  if(CopyBuffer(bb_h, 1, 1, 3, bb_u) < 3) return;
  if(CopyBuffer(bb_h, 2, 1, 3, bb_l) < 3) return;
  if(CopyBuffer(atr_h, 0, 1, 3, atr) < 3) return;
  if(CopyClose(_Symbol, PERIOD_CURRENT, 1, 3, close) < 3) return;
  if(CopyHigh(_Symbol, PERIOD_CURRENT, 1, 3, high) < 3) return;
  if(CopyLow(_Symbol, PERIOD_CURRENT, 1, 3, low) < 3) return;

  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
  double mid = (bb_u[1] + bb_l[1]) * 0.5;

  bool reject_high = high[1] >= bb_u[1] && close[1] < bb_u[1];
  bool reject_low  = low[1]  <= bb_l[1] && close[1] > bb_l[1];

  if(reject_high && mid < bid)
  {
    double sl = ask + ATR_SL_Mult * atr[1];
    if(ask - mid < (sl - ask)) return;
    SendSell(sl, mid, "C-range");
  }
  else if(reject_low && mid > ask)
  {
    double sl = bid - ATR_SL_Mult * atr[1];
    if(mid - bid < (bid - sl)) return;
    SendBuy(sl, mid, "C-range");
  }
}

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
  if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
  if(!HistoryDealSelect(trans.deal)) return;
  if((long)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != Magic) return;
  long entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
  if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_INOUT) return;
  double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT)
                + HistoryDealGetDouble(trans.deal, DEAL_SWAP)
                + HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
  if(profit < 0)
  {
    consec_losses++;
    if(consec_losses >= ConsecutiveHalt) halt_bars_left = HaltCooldownBars;
  }
  else consec_losses = 0;

  if(PositionsByMagic() == 0)
  {
    ulong position_id = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
    string trace_trade_id = RecoverTraceTradeId(position_id);
    if(StringLen(trace_trade_id) > 0)
    {
      double exit_price = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
      double volume = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);
      double commission = HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
      double swap = HistoryDealGetDouble(trans.deal, DEAL_SWAP);
      double deal_profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT);
      TraceLifecycle(
          trace_trade_id,
          "CLOSED",
          StringFormat(
              ""deal_ticket":"%I64d","position_id":"%I64d","
              ""exit_price":%.10f,"volume":%.8f,"profit":%.8f,"
              ""swap":%.8f,"commission":%.8f",
              (long)trans.deal, (long)position_id, exit_price, volume,
              deal_profit, swap, commission
          )
      );
      active_trace_trade_id = "";
    }
  }
  PersistSafetyState();
}

void OnTick()
{
  TimeStopStale();
  if(!SpreadOk()) return;
  if(!SessionOk()) return;
  if(!NewsBlackoutOk()) return;
  if(!DailyLossOk()) return;
  if(!DailyProfitLockOk()) return;
  if(consec_losses >= ConsecutiveHalt) return;
  if(trades_today >= MaxTradesPerDay) return;
  if(PositionsByMagic() >= MaxPositions) return;

  static datetime last_bar = 0;
  datetime t = iTime(_Symbol, PERIOD_CURRENT, 0);
  if(t == last_bar) return;
  last_bar = t;
  if(halt_bars_left > 0)
  {
    halt_bars_left--;
    PersistSafetyState();
    return;
  }

  int rg = Regime();
  if(rg == 1) TryTrendPullback();
  else if(rg == 2) TrySqueezeBreak();
  else if(rg == -1) TryRangeFade();
}
// FOREXAI-EXECUTION-CONTRACT-V1
// Signal uses closed bar data; EA enters on the next bar's live market price.
// MaxHoldBars=30; actual execution is accepted only after ResultRetcode+ResultDeal verification.
// Filling mode is selected from the symbol; stop validation includes stops+freeze constraints.
// Trading permissions require SYMBOL_TRADE_MODE and MARKET+SL+TP order flags.
// Protective closes are counted only after broker ResultRetcode confirmation.
// Runtime timestamps use broker/server time; trace UTC ordering uses TimeGMT and payload retains broker time.
// FOREXAI-RUNTIME-TRACE-V1: MQL5 emits advisory ORDER_SUBMITTED/ACCEPTED/FILLED/OPEN/MANAGED/CLOSED events only.
// GRK-SAFETY-CONTRACT-051
// Hard StopLoss on every order. No averaging-up / recovery sizing. Risk<=0.6.
// No grid. No martingale. Closed-bar entries only. Daily profit/loss halt.
