//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5  v3.12                                  |
//| Safety: no grid, no martingale, hard risk cap                    |
//| Regime switch: TREND pullback + RANGE mean-reversion + FLAT off  |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "3.12"
#property strict

input double InpRiskPercent     = 0.5;
input double InpMaxRiskPercent  = 0.5;
input double InpMaxDailyLossPct = 2.0;
input int    InpADXPeriod       = 14;
input int    InpATRPeriod       = 14;
input int    InpEMAFast         = 20;
input int    InpEMASlow         = 50;
input int    InpRSIPeriod       = 14;
input double InpTrendADX        = 25.0;
input double InpRangeADX        = 20.0;
input double InpMinRR           = 2.0;
input int    InpMagic           = 2026018;
input int    InpMaxSpreadPoints = 30;
input int    InpNewsBlackoutMin = 30;
input bool   InpBlockHighImpactNews = true;
input bool   InpAllowGrid       = false;
input bool   InpAllowMartingale = false;

int hADX, hATR, hEF, hES, hRSI;
datetime lastBarTime = 0;
double   dayStartEquity = 0.0;
int      dayStamp = 0;

int OnInit()
{
   if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED;
   if(InpRiskPercent > InpMaxRiskPercent || InpRiskPercent <= 0) return INIT_FAILED;
   if(InpMinRR < 2.0) return INIT_FAILED;
   hADX = iADX(_Symbol, PERIOD_H4, InpADXPeriod);
   hATR = iATR(_Symbol, PERIOD_H1, InpATRPeriod);
   hEF  = iMA(_Symbol, PERIOD_H1, InpEMAFast, 0, MODE_EMA, PRICE_CLOSE);
   hES  = iMA(_Symbol, PERIOD_H1, InpEMASlow, 0, MODE_EMA, PRICE_CLOSE);
   hRSI = iRSI(_Symbol, PERIOD_H1, InpRSIPeriod, PRICE_CLOSE);
   if(hADX==INVALID_HANDLE || hATR==INVALID_HANDLE || hEF==INVALID_HANDLE || hES==INVALID_HANDLE || hRSI==INVALID_HANDLE)
      return INIT_FAILED;
   dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   dayStamp = DayKey();
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(hADX!=INVALID_HANDLE) IndicatorRelease(hADX);
   if(hATR!=INVALID_HANDLE) IndicatorRelease(hATR);
   if(hEF!=INVALID_HANDLE)  IndicatorRelease(hEF);
   if(hES!=INVALID_HANDLE)  IndicatorRelease(hES);
   if(hRSI!=INVALID_HANDLE) IndicatorRelease(hRSI);
}

enum Regime { REGIME_FLAT=0, REGIME_TREND=1, REGIME_RANGE=2 };

int DayKey()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return dt.year*10000 + dt.mon*100 + dt.day;
}

void ResetDayIfNeeded()
{
   int k = DayKey();
   if(k != dayStamp)
   {
      dayStamp = k;
      dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   }
}

bool DailyLossBreached()
{
   ResetDayIfNeeded();
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(dayStartEquity <= 0) return true;
   double dd = 100.0 * (dayStartEquity - eq) / dayStartEquity;
   return dd >= InpMaxDailyLossPct;
}

Regime DetectRegime()
{
   double adx[];
   ArraySetAsSeries(adx, true);
   if(CopyBuffer(hADX, 0, 1, 3, adx) < 3) return REGIME_FLAT;
   if(adx[0] >= InpTrendADX) return REGIME_TREND;
   if(adx[0] < InpRangeADX)  return REGIME_RANGE;
   return REGIME_FLAT;
}

bool SpreadOk()
{
   long spreadPts = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   return spreadPts > 0 && spreadPts < InpMaxSpreadPoints;
}

bool NewsFilterOk()
{
   if(!InpBlockHighImpactNews) return true;
   MqlCalendarValue values[];
   datetime from = TimeCurrent() - InpNewsBlackoutMin * 60;
   datetime to   = TimeCurrent() + InpNewsBlackoutMin * 60;
   int n = CalendarValueHistory(values, from, to, NULL, NULL);
   if(n < 0) return true;
   string base = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE);
   string profit = SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT);
   for(int i=0;i<n;i++)
   {
      MqlCalendarEvent ev;
      if(!CalendarEventById(values[i].event_id, ev)) continue;
      if(ev.importance < CALENDAR_IMPORTANCE_HIGH) continue;
      MqlCalendarCountry co;
      if(!CalendarCountryById(ev.country_id, co)) continue;
      if(StringFind(co.currency, base) >= 0 || StringFind(co.currency, profit) >= 0)
         return false;
   }
   return true;
}

int CountOurPositions()
{
   int n=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket==0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagic) n++;
   }
   return n;
}

double RiskLots(double sl_dist)
{
   if(sl_dist <= 0) return 0;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskMoney = equity * InpRiskPercent / 100.0;
   double tickVal = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickVal<=0 || tickSize<=0) return 0;
   double moneyPerLot = (sl_dist / tickSize) * tickVal;
   if(moneyPerLot<=0) return 0;
   double lots = riskMoney / moneyPerLot;
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step<=0) step = vmin;
   lots = MathFloor(lots / step) * step;
   if(lots < vmin) return 0;
   if(lots > vmax) lots = vmax;
   return NormalizeDouble(lots, 2);
}

bool NewH1Bar()
{
   datetime t = iTime(_Symbol, PERIOD_H1, 0);
   if(t == 0) return false;
   if(t == lastBarTime) return false;
   lastBarTime = t;
   return true;
}

bool SendDeal(ENUM_ORDER_TYPE type, double sl, double tp)
{
   MqlTradeRequest req; MqlTradeResult res;
   ZeroMemory(req); ZeroMemory(res);
   req.action = TRADE_ACTION_DEAL;
   req.symbol = _Symbol;
   req.magic  = InpMagic;
   req.deviation = 20;
   req.type = type;
   req.sl = sl;
   req.tp = tp;
   req.price = (type==ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                      : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl_dist = MathAbs(req.price - sl);
   req.volume = RiskLots(sl_dist);
   if(req.volume <= 0) return false;
   return OrderSend(req, res);
}

void OnTick()
{
   if(!SpreadOk()) return;
   if(DailyLossBreached()) return;
   if(!NewsFilterOk()) return;
   if(!NewH1Bar()) return;
   if(CountOurPositions()>0) return;

   Regime rg = DetectRegime();
   if(rg==REGIME_FLAT) return;

   double emaF[], emaS[], atr[], rsi[];
   ArraySetAsSeries(emaF, true);
   ArraySetAsSeries(emaS, true);
   ArraySetAsSeries(atr, true);
   ArraySetAsSeries(rsi, true);
   if(CopyBuffer(hEF,0,1,3,emaF)<3) return;
   if(CopyBuffer(hES,0,1,3,emaS)<3) return;
   if(CopyBuffer(hATR,0,1,3,atr)<3) return;
   if(CopyBuffer(hRSI,0,1,3,rsi)<3) return;

   double close1 = iClose(_Symbol, PERIOD_H1, 1);
   double low1   = iLow(_Symbol, PERIOD_H1, 1);
   double high1  = iHigh(_Symbol, PERIOD_H1, 1);
   double dailyClose = iClose(_Symbol, PERIOD_D1, 1);
   bool dailyUp = dailyClose > iClose(_Symbol, PERIOD_D1, 5);

   if(rg==REGIME_TREND)
   {
      if(close1>emaS[0] && low1<=emaF[0] && close1>emaF[0] && dailyUp)
      {
         double sl = low1 - atr[0]*0.3;
         double sl_dist = close1 - sl;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_BUY, sl, close1 + sl_dist * InpMinRR);
      }
      else if(close1<emaS[0] && high1>=emaF[0] && close1<emaF[0] && !dailyUp)
      {
         double sl = high1 + atr[0]*0.3;
         double sl_dist = sl - close1;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_SELL, sl, close1 - sl_dist * InpMinRR);
      }
   }
   else if(rg==REGIME_RANGE)
   {
      if(rsi[0] < 30.0 && close1 < emaF[0])
      {
         double sl = low1 - atr[0]*0.4;
         double sl_dist = close1 - sl;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_BUY, sl, close1 + sl_dist * InpMinRR);
      }
      else if(rsi[0] > 70.0 && close1 > emaF[0])
      {
         double sl = high1 + atr[0]*0.4;
         double sl_dist = sl - close1;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_SELL, sl, close1 - sl_dist * InpMinRR);
      }
   }
}
