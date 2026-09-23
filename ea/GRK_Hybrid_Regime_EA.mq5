//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5  v3.11                                  |
//| Safety: no grid, no martingale, hard risk cap                    |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "3.11"
input double InpRiskPercent     = 0.5;
input double InpMaxRiskPercent  = 0.5;
input double InpMaxDailyLossPct = 2.0;
input int    InpADXPeriod       = 14;
input int    InpATRPeriod       = 14;
input int    InpEMAFast         = 20;
input int    InpEMASlow         = 50;
input double InpTrendADX        = 25.0;
input double InpRangeADX        = 20.0;
input double InpMinRR           = 2.0;
input int    InpMagic           = 2026017;
input bool   InpAllowGrid       = false;
input bool   InpAllowMartingale = false;
int hADX, hATR, hEF, hES;
int OnInit()
{
   if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED;
   if(InpRiskPercent > InpMaxRiskPercent || InpRiskPercent <= 0) return INIT_FAILED;
   hADX = iADX(_Symbol, PERIOD_H4, InpADXPeriod);
   hATR = iATR(_Symbol, PERIOD_H1, InpATRPeriod);
   hEF  = iMA(_Symbol, PERIOD_H1, InpEMAFast, 0, MODE_EMA, PRICE_CLOSE);
   hES  = iMA(_Symbol, PERIOD_H1, InpEMASlow, 0, MODE_EMA, PRICE_CLOSE);
   if(hADX==INVALID_HANDLE || hATR==INVALID_HANDLE || hEF==INVALID_HANDLE || hES==INVALID_HANDLE) return INIT_FAILED;
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason)
{
   if(hADX!=INVALID_HANDLE) IndicatorRelease(hADX);
   if(hATR!=INVALID_HANDLE) IndicatorRelease(hATR);
   if(hEF!=INVALID_HANDLE)  IndicatorRelease(hEF);
   if(hES!=INVALID_HANDLE)  IndicatorRelease(hES);
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
   return spreadPts < 30;
}
int CountOurPositions()
{
   int n=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      if(!PositionSelectByTicket(PositionGetTicket(i))) continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==InpMagic) n++;
   }
   return n;
}
void OnTick()
{
   if(!SpreadOk()) return;
   if(CountOurPositions()>0) return;
   Regime rg = DetectRegime();
   if(rg==REGIME_FLAT) return;
   double emaF[], emaS[], atr[];
   if(CopyBuffer(hEF,0,1,3,emaF)<3) return;
   if(CopyBuffer(hES,0,1,3,emaS)<3) return;
   if(CopyBuffer(hATR,0,1,3,atr)<3) return;
   double close1 = iClose(_Symbol, PERIOD_H1, 1);
   double low1   = iLow(_Symbol, PERIOD_H1, 1);
   double high1  = iHigh(_Symbol, PERIOD_H1, 1);
   MqlTradeRequest req; MqlTradeResult res; ZeroMemory(req); ZeroMemory(res);
   req.action = TRADE_ACTION_DEAL; req.symbol = _Symbol; req.magic = InpMagic; req.deviation = 20;
   if(rg==REGIME_TREND && close1>emaS[0] && low1<=emaF[0] && close1>emaF[0])
   {
      double sl = low1 - atr[0]*0.3; double sl_dist = close1 - sl; if(sl_dist<=0) return;
      req.type = ORDER_TYPE_BUY; req.volume = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      req.sl = sl; req.tp = close1 + sl_dist * InpMinRR; req.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      OrderSend(req,res);
   }
}
