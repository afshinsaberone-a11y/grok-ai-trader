//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5   GRK-FX-2026-044                       |
//| Regime switch: Trend pullback / Squeeze retest / Range fade      |
//| HTF MA + DI + session + spread + daily loss + consecutive halt   |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "44.0"
#include <Trade/Trade.mqh>

input double RiskPercent        = 0.5;
input double DailyLossLimit     = 2.0;
input int    MaxPositions       = 1;
input int    ADX_Period         = 14;
input int    ADX_Trend          = 23;
input int    ADX_Range          = 17;
input int    MA200_Period       = 200;
input ENUM_TIMEFRAMES HTF       = PERIOD_H4;
input int    ATR_Period         = 14;
input int    BB_Period          = 20;
input double BB_Dev             = 2.0;
input double ATR_SL_Mult        = 1.45;
input double RR_Target          = 1.9;
input double SpreadMultMax      = 1.3;
input int    ConsecutiveHalt    = 3;
input int    SessionStartHour   = 7;
input int    SessionEndHour     = 16;
input int    NewsBlackoutStart  = -1;
input int    NewsBlackoutEnd    = -1;
input long   Magic              = 2026044;

CTrade trade;
int adx_h, ma_h, htf_ma_h, atr_h, bb_h;
int consec_losses = 0;
datetime day_stamp = 0;
double day_start_equity = 0;

int OnInit()
{
  if(RiskPercent > 0.6) return INIT_FAILED;
  if(MaxPositions != 1) return INIT_FAILED;
  if(DailyLossLimit <= 0 || ATR_SL_Mult <= 0 || RR_Target < 1.0) return INIT_FAILED;

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
  day_start_equity = AccountInfoDouble(ACCOUNT_EQUITY);
  day_stamp = TimeCurrent();
  return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
  if(adx_h!=INVALID_HANDLE)    IndicatorRelease(adx_h);
  if(ma_h!=INVALID_HANDLE)     IndicatorRelease(ma_h);
  if(htf_ma_h!=INVALID_HANDLE) IndicatorRelease(htf_ma_h);
  if(atr_h!=INVALID_HANDLE)    IndicatorRelease(atr_h);
  if(bb_h!=INVALID_HANDLE)     IndicatorRelease(bb_h);
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

bool SpreadOk()
{
  double atr[];
  ArraySetAsSeries(atr, true);
  if(CopyBuffer(atr_h, 0, 1, 5, atr) < 5) return false;
  if(atr[1] <= 0) return false;
  double spr = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
  return spr <= SpreadMultMax * atr[1] * 0.12;
}

bool SessionOk()
{
  MqlDateTime t;
  TimeToStruct(TimeCurrent(), t);
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

bool DailyLossOk()
{
  MqlDateTime nowt, then;
  TimeToStruct(TimeCurrent(), nowt);
  TimeToStruct(day_stamp, then);
  if(nowt.day!=then.day || nowt.mon!=then.mon || nowt.year!=then.year)
  {
    day_stamp = TimeCurrent();
    day_start_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    consec_losses = 0;
  }
  double eq = AccountInfoDouble(ACCOUNT_EQUITY);
  if(day_start_equity <= 0) return false;
  return 100.0 * (day_start_equity - eq) / day_start_equity < DailyLossLimit;
}

int Regime()
{
  double adx[];
  ArraySetAsSeries(adx, true);
  if(CopyBuffer(adx_h, 0, 1, 3, adx) < 3) return 0;
  if(adx[1] >= ADX_Trend) return 1;
  if(adx[1] <= ADX_Range) return -1;
  return 2;
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

double PositionSize(double sl_price, bool is_buy)
{
  double price = is_buy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                        : SymbolInfoDouble(_Symbol, SYMBOL_BID);
  double sl_points = MathAbs(price - sl_price);
  double risk_money = AccountInfoDouble(ACCOUNT_EQUITY) * RiskPercent / 100.0;
  double tick_val = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
  double tick_sz  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
  if(sl_points <= 0 || tick_val <= 0 || tick_sz <= 0) return 0;
  return NormalizeVol(risk_money / (sl_points / tick_sz * tick_val));
}

bool StopsValid(double sl, double tp, bool is_buy)
{
  double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
  int stops = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
  double min_dist = stops * point;
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

bool SendBuy(double sl, double tp, const string cmt)
{
  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
  if(!StopsValid(sl, tp, true)) return false;
  double vol = PositionSize(sl, true);
  if(vol <= 0) return false;
  return trade.Buy(vol, _Symbol, ask, sl, tp, cmt);
}

bool SendSell(double sl, double tp, const string cmt)
{
  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
  if(!StopsValid(sl, tp, false)) return false;
  double vol = PositionSize(sl, false);
  if(vol <= 0) return false;
  return trade.Sell(vol, _Symbol, bid, sl, tp, cmt);
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

  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

  if(long_ok)
  {
    double sl = bid - ATR_SL_Mult * atr[1];
    double tp = bid + RR_Target * ATR_SL_Mult * atr[1];
    SendBuy(sl, tp, "A-trend");
  }
  else if(short_ok)
  {
    double sl = ask + ATR_SL_Mult * atr[1];
    double tp = ask - RR_Target * ATR_SL_Mult * atr[1];
    SendSell(sl, tp, "A-trend");
  }
}

void TrySqueezeBreak()
{
  if(!SqueezeThenExpand()) return;
  double bb_u[], bb_l[], atr[], close[];
  ArraySetAsSeries(bb_u, true);
  ArraySetAsSeries(bb_l, true);
  ArraySetAsSeries(atr, true);
  ArraySetAsSeries(close, true);
  if(CopyBuffer(bb_h, 1, 1, 4, bb_u) < 4) return;
  if(CopyBuffer(bb_h, 2, 1, 4, bb_l) < 4) return;
  if(CopyBuffer(atr_h, 0, 1, 3, atr) < 3) return;
  if(CopyClose(_Symbol, PERIOD_CURRENT, 1, 4, close) < 4) return;

  double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
  double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

  if(close[2] > bb_u[2] && close[1] <= close[2] && close[1] >= bb_u[1] && DiBull())
  {
    double sl = bid - ATR_SL_Mult * atr[1];
    double tp = bid + RR_Target * ATR_SL_Mult * atr[1];
    SendBuy(sl, tp, "B-squeeze");
  }
  else if(close[2] < bb_l[2] && close[1] >= close[2] && close[1] <= bb_l[1] && !DiBull())
  {
    double sl = ask + ATR_SL_Mult * atr[1];
    double tp = ask - RR_Target * ATR_SL_Mult * atr[1];
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
    double tp = mid;
    SendSell(sl, tp, "C-range");
  }
  else if(reject_low && mid > ask)
  {
    double sl = bid - ATR_SL_Mult * atr[1];
    double tp = mid;
    SendBuy(sl, tp, "C-range");
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
  if(profit < 0) consec_losses++;
  else consec_losses = 0;
}

void OnTick()
{
  if(!SpreadOk()) return;
  if(!SessionOk()) return;
  if(!NewsBlackoutOk()) return;
  if(!DailyLossOk()) return;
  if(consec_losses >= ConsecutiveHalt) return;
  if(PositionsByMagic() >= MaxPositions) return;

  static datetime last_bar = 0;
  datetime t = iTime(_Symbol, PERIOD_CURRENT, 0);
  if(t == last_bar) return;
  last_bar = t;

  int rg = Regime();
  if(rg == 1) TryTrendPullback();
  else if(rg == 2) TrySqueezeBreak();
  else if(rg == -1) TryRangeFade();
}
// GRK-SAFETY-CONTRACT-044
// Hard StopLoss on every order. No averaging-up / recovery sizing. Risk<=0.6.
// No grid. No martingale. Closed-bar entries only.
