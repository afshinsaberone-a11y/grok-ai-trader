//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5  v3.12                                  |
//| Safety: no grid, no martingale, hard risk cap                    |
//| Contract: risk 0.5%, spread filter, news window block, daily loss|
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "3.12"
#include <Trade/Trade.mqh>
input double InpRiskPercent     = 0.5;
input double InpMaxRiskPercent  = 0.5;
input double InpMaxDailyLossPct = 2.0;
input int    InpADXPeriod       = 14;
input int    InpATRPeriod       = 14;
input int    InpRSIPeriod       = 14;
input int    InpEMAFast         = 20;
input int    InpEMASlow         = 50;
input int    InpRangeLookback   = 20;
input double InpTrendADX        = 25.0;
input double InpRangeADX        = 20.0;
input double InpMinRR           = 2.0;
input int    InpMaxSpreadPts    = 30;
input int    InpMaxPositions    = 2;
input int    InpNewsBlockMin    = 30;
input int    InpMagic           = 2026018;
input bool   InpAllowGrid       = false;
input bool   InpAllowMartingale = false;
input bool   InpNewsFilter      = true;
CTrade trade;
int hADX, hATR, hRSI, hEF, hES, hEMADaily;
datetime lastBar = 0;
double dayStartEquity = 0;
int OnInit()
{
   if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED;
   if(InpRiskPercent > InpMaxRiskPercent || InpRiskPercent <= 0) return INIT_FAILED;
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(20);
   hADX = iADX(_Symbol, PERIOD_H4, InpADXPeriod);
   hATR = iATR(_Symbol, PERIOD_H1, InpATRPeriod);
   hRSI = iRSI(_Symbol, PERIOD_H1, InpRSIPeriod, PRICE_CLOSE);
   hEF  = iMA(_Symbol, PERIOD_H1, InpEMAFast, 0, MODE_EMA, PRICE_CLOSE);
   hES  = iMA(_Symbol, PERIOD_H1, InpEMASlow, 0, MODE_EMA, PRICE_CLOSE);
   hEMADaily = iMA(_Symbol, PERIOD_D1, InpEMASlow, 0, MODE_EMA, PRICE_CLOSE);
   if(hADX==INVALID_HANDLE || hATR==INVALID_HANDLE || hRSI==INVALID_HANDLE || hEF==INVALID_HANDLE || hES==INVALID_HANDLE || hEMADaily==INVALID_HANDLE) return INIT_FAILED;
   dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason)
{
   if(hADX!=INVALID_HANDLE) IndicatorRelease(hADX);
   if(hATR!=INVALID_HANDLE) IndicatorRelease(hATR);
   if(hRSI!=INVALID_HANDLE) IndicatorRelease(hRSI);
   if(hEF!=INVALID_HANDLE)  IndicatorRelease(hEF);
   if(hES!=INVALID_HANDLE)  IndicatorRelease(hES);
   if(hEMADaily!=INVALID_HANDLE) IndicatorRelease(hEMADaily);
}
enum Regime { REGIME_FLAT=0, REGIME_TREND=1, REGIME_RANGE=2 };
Regime DetectRegime()
{
   double adx[];
   if(CopyBuffer(hADX,0,1,3,adx)<3) return REGIME_FLAT;
   if(adx[0] >= InpTrendADX) return REGIME_TREND;
   if(adx[0] < InpRangeADX) return REGIME_RANGE;
   return REGIME_FLAT;
}
bool SpreadOk()
{
   long spreadPts = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   return spreadPts > 0 && spreadPts < InpMaxSpreadPts;
}
bool NewsWindowBlocked()
{
   if(!InpNewsFilter) return false;
   MqlDateTime t; TimeToStruct(TimeCurrent(), t);
   if((t.hour==12 && t.min>=30) || (t.hour==13 && t.min<=30)) return true;
   if((t.hour==14 && t.min>=30) || (t.hour==15 && t.min<=30)) return true;
   return false;
}
bool DailyLossExceeded()
{
   MqlDateTime t; TimeToStruct(TimeCurrent(), t);
   static int lastDay = -1;
   if(t.day != lastDay) { lastDay = t.day; dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY); }
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(dayStartEquity <= 0) return true;
   return (100.0 * (dayStartEquity - eq) / dayStartEquity) >= InpMaxDailyLossPct;
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
double VolumeFromRisk(double sl_dist)
{
   if(sl_dist <= 0) return 0;
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskMoney = equity * InpRiskPercent / 100.0;
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(tickSize<=0 || tickValue<=0) return vmin;
   double vol = riskMoney / (sl_dist / tickSize * tickValue);
   vol = MathFloor(vol / step) * step;
   if(vol < vmin) vol = 0;
   if(vol > vmax) vol = vmax;
   return vol;
}
void OnTick()
{
   datetime bar = iTime(_Symbol, PERIOD_H1, 0);
   if(bar == lastBar) return;
   lastBar = bar;
   if(!SpreadOk()) return;
   if(NewsWindowBlocked()) return;
   if(DailyLossExceeded()) return;
   if(CountOurPositions() >= InpMaxPositions) return;
   Regime rg = DetectRegime();
   if(rg==REGIME_FLAT) return;
   double emaF[], emaS[], emaD[], atr[], rsi[];
   if(CopyBuffer(hEF,0,1,3,emaF)<3) return;
   if(CopyBuffer(hES,0,1,3,emaS)<3) return;
   if(CopyBuffer(hEMADaily,0,1,3,emaD)<3) return;
   if(CopyBuffer(hATR,0,1,3,atr)<3) return;
   if(CopyBuffer(hRSI,0,1,3,rsi)<3) return;
   double close1 = iClose(_Symbol, PERIOD_H1, 1);
   double low1   = iLow(_Symbol, PERIOD_H1, 1);
   double high1  = iHigh(_Symbol, PERIOD_H1, 1);
   double highN  = iHigh(_Symbol, PERIOD_H1, iHighest(_Symbol, PERIOD_H1, MODE_HIGH, InpRangeLookback, 1));
   double lowN   = iLow(_Symbol, PERIOD_H1, iLowest(_Symbol, PERIOD_H1, MODE_LOW, InpRangeLookback, 1));
   double mid = (highN + lowN) * 0.5;
   if(rg==REGIME_TREND)
   {
      bool bullBias = close1 > emaD[0] && close1 > emaS[0];
      bool bearBias = close1 < emaD[0] && close1 < emaS[0];
      if(bullBias && low1<=emaF[0] && close1>emaF[0])
      {
         double sl = low1 - atr[0]*0.3; double sl_dist = close1 - sl; double vol = VolumeFromRisk(sl_dist); if(vol<=0) return;
         trade.Buy(vol, _Symbol, 0, sl, close1 + sl_dist * InpMinRR);
      }
      if(bearBias && high1>=emaF[0] && close1<emaF[0])
      {
         double sl = high1 + atr[0]*0.3; double sl_dist = sl - close1; double vol = VolumeFromRisk(sl_dist); if(vol<=0) return;
         trade.Sell(vol, _Symbol, 0, sl, close1 - sl_dist * InpMinRR);
      }
   }
   if(rg==REGIME_RANGE && highN>lowN)
   {
      double width = highN - lowN;
      if(close1 <= lowN + 0.15*width && rsi[0] < 30)
      {
         double sl = lowN - atr[0]*0.2; double sl_dist = close1 - sl; double vol = VolumeFromRisk(sl_dist); if(vol<=0) return;
         trade.Buy(vol, _Symbol, 0, sl, mid);
      }
      if(close1 >= highN - 0.15*width && rsi[0] > 70)
      {
         double sl = highN + atr[0]*0.2; double sl_dist = sl - close1; double vol = VolumeFromRisk(sl_dist); if(vol<=0) return;
         trade.Sell(vol, _Symbol, 0, sl, mid);
      }
   }
}
