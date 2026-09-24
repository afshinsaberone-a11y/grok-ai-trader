//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5  v3.22                                  |
//| Contract-safety hybrid. NOT a profit guarantee.                  |
//| Banned: grid, martingale, average-down.                          |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "3.22"
#property strict

#include <Trade/Trade.mqh>

input double RiskPercent        = 0.5;
input double MaxDailyLossPct    = 2.0;
input int    MaxSpreadPoints    = 25;
input int    CoolDownBars       = 8;
input int    MaxTradesDay       = 3;
input int    MaxConsecutiveLoss = 2;
input int    Magic              = 20260322;
input int    SlippagePoints     = 20;
input double MinMarginLevelPct  = 400.0;
input double CostAtrFraction    = 0.25;
input int    ADX_Period         = 14;
input int    ATR_Period         = 14;
input int    EMA_Fast           = 20;
input int    EMA_Slow           = 50;
input int    EMA_Daily          = 50;
input double ADX_Trend          = 25.0;
input double ADX_Range          = 18.0;
input double ShockAtrMult       = 2.5;
input double RR                 = 2.0;
input int    RSI_Period         = 14;
input int    BB_Period          = 20;
input int    SessLondonStart    = 8;
input int    SessLondonEnd      = 17;
input int    SessNYStart        = 13;
input int    SessNYEnd          = 21;
input int    FridayFlattenHour  = 20;

CTrade trade;
datetime day_start = 0;
double   day_start_eq = 0;
int      trades_today = 0;
int      consec_loss = 0;
int      cooldown_left = 0;
datetime last_bar = 0;

int h_adx, h_atr, h_ema_f, h_ema_s, h_ema_d, h_rsi, h_bb;

int OnInit()
{
   trade.SetExpertMagicNumber(Magic);
   trade.SetDeviationInPoints(SlippagePoints);
   h_adx   = iADX(_Symbol, PERIOD_CURRENT, ADX_Period);
   h_atr   = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
   h_ema_f = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_s = iMA(_Symbol, PERIOD_CURRENT, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   h_ema_d = iMA(_Symbol, PERIOD_D1, EMA_Daily, 0, MODE_EMA, PRICE_CLOSE);
   h_rsi   = iRSI(_Symbol, PERIOD_CURRENT, RSI_Period, PRICE_CLOSE);
   h_bb    = iBands(_Symbol, PERIOD_CURRENT, BB_Period, 0, 2.0, PRICE_CLOSE);
   if(h_adx==INVALID_HANDLE || h_atr==INVALID_HANDLE || h_ema_f==INVALID_HANDLE ||
      h_ema_s==INVALID_HANDLE || h_ema_d==INVALID_HANDLE || h_rsi==INVALID_HANDLE || h_bb==INVALID_HANDLE)
      return INIT_FAILED;
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(h_adx); IndicatorRelease(h_atr);
   IndicatorRelease(h_ema_f); IndicatorRelease(h_ema_s); IndicatorRelease(h_ema_d);
   IndicatorRelease(h_rsi); IndicatorRelease(h_bb);
}

bool NewBar()
{
   datetime t = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(t == last_bar) return false;
   last_bar = t;
   return true;
}

bool IsFridayLate()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   return (dt.day_of_week == 5 && dt.hour >= FridayFlattenHour);
}

bool SessionAllowed()
{
   if(IsFridayLate()) return false;
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   int h = dt.hour;
   bool london = (h >= SessLondonStart && h < SessLondonEnd);
   bool ny     = (h >= SessNYStart && h < SessNYEnd);
   return (london || ny);
}

void ResetDay()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   datetime start = StringToTime(StringFormat("%04d.%02d.%02d 00:00", dt.year, dt.mon, dt.day));
   if(start != day_start)
   {
      day_start = start;
      day_start_eq = AccountInfoDouble(ACCOUNT_EQUITY);
      trades_today = 0;
      consec_loss = 0;
   }
}

bool SafetyOk()
{
   if(!SessionAllowed()) return false;
   if(consec_loss >= MaxConsecutiveLoss) return false;
   if(trades_today >= MaxTradesDay) return false;
   if(cooldown_left > 0) return false;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(day_start_eq > 0.0)
   {
      double dd = 100.0 * (day_start_eq - eq) / day_start_eq;
      if(dd >= MaxDailyLossPct) return false;
   }
   long spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(spread > MaxSpreadPoints) return false;
   double ml = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
   if(ml > 0.0 && ml < MinMarginLevelPct) return false;
   if(PositionSelect(_Symbol)) return false;
   return true;
}

double Buf(int handle, int buf, int sh)
{
   double a[];
   if(CopyBuffer(handle, buf, sh, 1, a) != 1) return EMPTY_VALUE;
   return a[0];
}

enum ENUM_REGIME { REG_TREND=1, REG_RANGE=2, REG_TRANS=3 };

ENUM_REGIME Regime(double adx)
{
   if(adx >= ADX_Trend) return REG_TREND;
   if(adx <= ADX_Range) return REG_RANGE;
   return REG_TRANS;
}

double LotForStop(double sl_price, bool is_buy)
{
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double risk_money = eq * RiskPercent / 100.0;
   double tick_val = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_sz  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double price = is_buy ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double dist = MathAbs(price - sl_price);
   if(dist <= 0 || tick_val <= 0 || tick_sz <= 0) return 0;
   double loss_per_lot = (dist / tick_sz) * tick_val;
   if(loss_per_lot <= 0) return 0;
   double lots = risk_money / loss_per_lot;
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   lots = MathFloor(lots / step) * step;
   if(lots < vmin) return 0;
   if(lots > vmax) lots = vmax;
   return lots;
}

void NormalizeStops(bool is_buy, double &sl, double &tp)
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);
   long stops_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_dist = stops_level * _Point;
   double price = is_buy ? SymbolInfoDouble(_Symbol, SYMBOL_BID) : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   if(is_buy)
   {
      if(price - sl < min_dist) sl = NormalizeDouble(price - min_dist, digits);
      if(tp - price < min_dist) tp = NormalizeDouble(price + min_dist, digits);
   }
   else
   {
      if(sl - price < min_dist) sl = NormalizeDouble(price + min_dist, digits);
      if(price - tp < min_dist) tp = NormalizeDouble(price - min_dist, digits);
   }
}

void MaybeFlattenShock(double atr)
{
   double high1 = iHigh(_Symbol, PERIOD_CURRENT, 1);
   double low1  = iLow(_Symbol, PERIOD_CURRENT, 1);
   if(atr > 0 && (high1 - low1) >= ShockAtrMult * atr)
   {
      if(PositionSelect(_Symbol))
         trade.PositionClose(_Symbol);
      cooldown_left = CoolDownBars;
   }
}

void MaybeFlattenFriday()
{
   if(!IsFridayLate()) return;
   if(PositionSelect(_Symbol))
      trade.PositionClose(_Symbol);
}

void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if((int)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != Magic) return;
   long entry = HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_INOUT) return;
   double profit = HistoryDealGetDouble(trans.deal, DEAL_PROFIT)
                 + HistoryDealGetDouble(trans.deal, DEAL_SWAP)
                 + HistoryDealGetDouble(trans.deal, DEAL_COMMISSION);
   if(profit < 0) consec_loss++;
   else consec_loss = 0;
}

void OnTick()
{
   ResetDay();
   if(!NewBar()) return;
   if(cooldown_left > 0) cooldown_left--;

   double adx = Buf(h_adx, 0, 1);
   double pdi = Buf(h_adx, 1, 1);
   double mdi = Buf(h_adx, 2, 1);
   double atr = Buf(h_atr, 0, 1);
   double ema_f = Buf(h_ema_f, 0, 1);
   double ema_s = Buf(h_ema_s, 0, 1);
   double ema_d = Buf(h_ema_d, 0, 1);
   double rsi = Buf(h_rsi, 0, 1);
   double bb_u = Buf(h_bb, 1, 1);
   double bb_m = Buf(h_bb, 0, 1);
   double bb_l = Buf(h_bb, 2, 1);
   if(adx==EMPTY_VALUE || atr==EMPTY_VALUE || atr<=0 || ema_d==EMPTY_VALUE) return;

   MaybeFlattenShock(atr);
   MaybeFlattenFriday();

   double spread_price = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   if(spread_price > CostAtrFraction * atr) return;
   if(!SafetyOk()) return;

   ENUM_REGIME rg = Regime(adx);
   if(rg == REG_TRANS) return;

   double close1 = iClose(_Symbol, PERIOD_CURRENT, 1);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   bool buy=false, sell=false;
   if(rg == REG_TREND)
   {
      bool htf_up = close1 > ema_d;
      bool htf_dn = close1 < ema_d;
      if(htf_up && ema_f > ema_s && pdi > mdi && close1 <= ema_f && close1 > ema_s)
         buy = true;
      if(htf_dn && ema_f < ema_s && mdi > pdi && close1 >= ema_f && close1 < ema_s)
         sell = true;
   }
   else if(rg == REG_RANGE)
   {
      if(bb_m==EMPTY_VALUE || rsi==EMPTY_VALUE) return;
      if(close1 <= bb_l && rsi < 30) buy = true;
      if(close1 >= bb_u && rsi > 70) sell = true;
   }

   if(!buy && !sell) return;

   double sl, tp, lots;
   if(buy)
   {
      sl = bid - 1.4 * atr;
      if(rg == REG_RANGE && bb_m != EMPTY_VALUE) tp = bb_m;
      else tp = bid + RR * (bid - sl);
      NormalizeStops(true, sl, tp);
      if(tp <= bid) return;
      lots = LotForStop(sl, true);
      if(lots > 0 && trade.Buy(lots, _Symbol, ask, sl, tp, "GRK-v322"))
      {
         if(trade.ResultRetcode() == TRADE_RETCODE_DONE || trade.ResultRetcode() == TRADE_RETCODE_PLACED)
            trades_today++;
      }
   }
   else
   {
      sl = ask + 1.4 * atr;
      if(rg == REG_RANGE && bb_m != EMPTY_VALUE) tp = bb_m;
      else tp = ask - RR * (sl - ask);
      NormalizeStops(false, sl, tp);
      if(tp >= ask) return;
      lots = LotForStop(sl, false);
      if(lots > 0 && trade.Sell(lots, _Symbol, bid, sl, tp, "GRK-v322"))
      {
         if(trade.ResultRetcode() == TRADE_RETCODE_DONE || trade.ResultRetcode() == TRADE_RETCODE_PLACED)
            trades_today++;
      }
   }
}
//+------------------------------------------------------------------+
