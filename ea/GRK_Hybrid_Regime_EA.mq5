//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5  v3.12                                  |
//| Safety: no grid, no martingale, hard risk cap                    |
//| Educational research only. Not a profitability guarantee.        |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "3.12"

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
input double InpShockATR        = 1.8;
input double InpMinRR           = 2.0;
input int    InpMaxPositions    = 2;
input int    InpMagic           = 2026018;
input bool   InpAllowGrid       = false;
input bool   InpAllowMartingale = false;

int hADX, hATR, hEF, hES, hRSI, hBB;
double gDayStartEquity = 0.0;
int    gDayStamp = -1;

int OnInit()
{
   if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED;
   if(InpRiskPercent > InpMaxRiskPercent || InpRiskPercent <= 0) return INIT_FAILED;
   hADX = iADX(_Symbol, PERIOD_H4, InpADXPeriod);
   hATR = iATR(_Symbol, PERIOD_H1, InpATRPeriod);
   hEF  = iMA(_Symbol, PERIOD_H1, InpEMAFast, 0, MODE_EMA, PRICE_CLOSE);
   hES  = iMA(_Symbol, PERIOD_H1, InpEMASlow, 0, MODE_EMA, PRICE_CLOSE);
   hRSI = iRSI(_Symbol, PERIOD_H1, InpRSIPeriod, PRICE_CLOSE);
   hBB  = iBands(_Symbol, PERIOD_H1, 20, 0, 2.0, PRICE_CLOSE);
   if(hADX==INVALID_HANDLE || hATR==INVALID_HANDLE || hEF==INVALID_HANDLE ||
      hES==INVALID_HANDLE || hRSI==INVALID_HANDLE || hBB==INVALID_HANDLE)
      return INIT_FAILED;
   gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(hADX!=INVALID_HANDLE) IndicatorRelease(hADX);
   if(hATR!=INVALID_HANDLE) IndicatorRelease(hATR);
   if(hEF!=INVALID_HANDLE)  IndicatorRelease(hEF);
   if(hES!=INVALID_HANDLE)  IndicatorRelease(hES);
   if(hRSI!=INVALID_HANDLE) IndicatorRelease(hRSI);
   if(hBB!=INVALID_HANDLE)  IndicatorRelease(hBB);
}

enum Regime { REGIME_FLAT=0, REGIME_TREND=1, REGIME_RANGE=2, REGIME_SHOCK=3 };

Regime DetectRegime()
{
   double adx[], atr[];
   if(CopyBuffer(hADX,0,1,3,adx)<3) return REGIME_FLAT;
   if(CopyBuffer(hATR,0,1,20,atr)<20) return REGIME_FLAT;
   double sma=0;
   for(int i=0;i<20;i++) sma+=atr[i];
   sma/=20.0;
   if(sma>0 && atr[0]/sma >= InpShockATR) return REGIME_SHOCK;
   if(adx[0] >= InpTrendADX) return REGIME_TREND;
   if(adx[0] < InpRangeADX) return REGIME_RANGE;
   return REGIME_FLAT;
}

bool SpreadOk()
{
   long spreadPts = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   return spreadPts < 30;
}

bool SessionOk()
{
   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);
   int h = t.hour;
   return (h>=7 && h<17); // London/NY overlap window (server time dependent)
}

void ResetDayIfNeeded()
{
   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);
   int stamp = t.year*10000 + t.mon*100 + t.day;
   if(stamp != gDayStamp)
   {
      gDayStamp = stamp;
      gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   }
}

bool DailyLossOk()
{
   ResetDayIfNeeded();
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(gDayStartEquity <= 0) return false;
   double dd = (gDayStartEquity - eq) / gDayStartEquity * 100.0;
   return dd < InpMaxDailyLossPct;
}

int CountOurPositions()
{
   int n=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagic) n++;
   }
   return n;
}

double DailyBias()
{
   double c1 = iClose(_Symbol, PERIOD_D1, 1);
   double c2 = iClose(_Symbol, PERIOD_D1, 2);
   if(c1>c2) return 1;
   if(c1<c2) return -1;
   return 0;
}

double VolumeByRisk(double sl_dist)
{
   if(sl_dist <= 0) return 0;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double risk_money = equity * (InpRiskPercent / 100.0);
   double tick_val = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_sz  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_val<=0 || tick_sz<=0) return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vol = risk_money / (sl_dist / tick_sz * tick_val);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step<=0) step = vmin;
   vol = MathMax(vmin, MathMin(vmax, MathFloor(vol/step)*step));
   return vol;
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
   req.volume = VolumeByRisk(sl_dist);
   if(req.volume <= 0) return false;
   return OrderSend(req, res);
}

void OnTick()
{
   if(!SpreadOk()) return;
   if(!SessionOk()) return;
   if(!DailyLossOk()) return;
   if(CountOurPositions() >= InpMaxPositions) return;

   Regime rg = DetectRegime();
   if(rg==REGIME_FLAT || rg==REGIME_SHOCK) return;

   double emaF[], emaS[], atr[], rsi[], bbU[], bbL[], bbM[];
   if(CopyBuffer(hEF,0,1,3,emaF)<3) return;
   if(CopyBuffer(hES,0,1,3,emaS)<3) return;
   if(CopyBuffer(hATR,0,1,3,atr)<3) return;
   if(CopyBuffer(hRSI,0,1,3,rsi)<3) return;
   if(CopyBuffer(hBB,1,1,3,bbU)<3) return;
   if(CopyBuffer(hBB,2,1,3,bbL)<3) return;
   if(CopyBuffer(hBB,0,1,3,bbM)<3) return;

   double close1 = iClose(_Symbol, PERIOD_H1, 1);
   double low1   = iLow(_Symbol, PERIOD_H1, 1);
   double high1  = iHigh(_Symbol, PERIOD_H1, 1);
   double bias   = DailyBias();

   if(rg==REGIME_TREND)
   {
      if(bias>=0 && close1>emaS[0] && low1<=emaF[0] && close1>emaF[0])
      {
         double sl = low1 - atr[0]*0.3;
         double sl_dist = close1 - sl;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_BUY, sl, close1 + sl_dist * InpMinRR);
      }
      if(bias<=0 && close1<emaS[0] && high1>=emaF[0] && close1<emaF[0])
      {
         double sl = high1 + atr[0]*0.3;
         double sl_dist = sl - close1;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_SELL, sl, close1 - sl_dist * InpMinRR);
      }
   }
   else if(rg==REGIME_RANGE)
   {
      if(close1<=bbL[0] && rsi[0]<=30)
      {
         double sl = low1 - atr[0]*0.4;
         double sl_dist = close1 - sl;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_BUY, sl, bbM[0]);
      }
      if(close1>=bbU[0] && rsi[0]>=70)
      {
         double sl = high1 + atr[0]*0.4;
         double sl_dist = sl - close1;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_SELL, sl, bbM[0]);
      }
   }
}
