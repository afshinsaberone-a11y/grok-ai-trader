//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5  v3.15                                  |
//| Safety: no grid, no martingale, flatten on shock/weekend         |
//| Educational research only. Not a profitability guarantee.        |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "3.15"

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
input double InpRangeMinRR      = 1.5;
input int    InpMaxPositions    = 2;
input int    InpMagic           = 2026021;
input bool   InpAllowGrid       = false;
input bool   InpAllowMartingale = false;
input int    InpMaxSpreadPoints = 40;

int hADX, hATR, hEF, hES, hRSI, hBB;
double gDayStartEquity = 0.0;
int    gDayStamp = -1;
datetime gLastBar = 0;

int OnInit()
{
   if(InpAllowGrid || InpAllowMartingale) return INIT_FAILED;
   if(InpRiskPercent > InpMaxRiskPercent || InpRiskPercent <= 0) return INIT_FAILED;
   if(!SymbolAllowed()) return INIT_FAILED;
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

bool SymbolAllowed()
{
   string s = _Symbol;
   return (StringFind(s,"EURUSD")>=0 || StringFind(s,"GBPUSD")>=0 ||
           StringFind(s,"USDJPY")>=0 || StringFind(s,"XAUUSD")>=0);
}

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
   int cap = InpMaxSpreadPoints;
   if(StringFind(_Symbol,"XAU")>=0) cap = InpMaxSpreadPoints * 6;
   return spreadPts < cap;
}

bool WeekendFlattenWindow()
{
   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);
   if(t.day_of_week==0 || t.day_of_week==6) return true;
   if(t.day_of_week==5 && t.hour>=16) return true;
   return false;
}

bool SessionOk()
{
   MqlDateTime t;
   TimeToStruct(TimeCurrent(), t);
   int h = t.hour;
   if(WeekendFlattenWindow()) return false;
   return (h>=7 && h<17);
}

bool NewH1Bar()
{
   datetime bar = iTime(_Symbol, PERIOD_H1, 0);
   if(bar==0) return false;
   if(bar==gLastBar) return false;
   gLastBar = bar;
   return true;
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

int OurDirection()
{
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol || PositionGetInteger(POSITION_MAGIC)!=InpMagic) continue;
      long type = PositionGetInteger(POSITION_TYPE);
      if(type==POSITION_TYPE_BUY) return 1;
      if(type==POSITION_TYPE_SELL) return -1;
   }
   return 0;
}

void FlattenAll()
{
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol || PositionGetInteger(POSITION_MAGIC)!=InpMagic) continue;
      long type = PositionGetInteger(POSITION_TYPE);
      double vol = PositionGetDouble(POSITION_VOLUME);
      MqlTradeRequest req; MqlTradeResult res;
      ZeroMemory(req); ZeroMemory(res);
      req.action = TRADE_ACTION_DEAL;
      req.symbol = _Symbol;
      req.magic  = InpMagic;
      req.volume = vol;
      req.deviation = 30;
      req.position = ticket;
      if(type==POSITION_TYPE_BUY)
      {
         req.type = ORDER_TYPE_SELL;
         req.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      }
      else
      {
         req.type = ORDER_TYPE_BUY;
         req.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      }
      OrderSend(req, res);
   }
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
   if(tick_val<=0 || tick_sz<=0) return 0;
   double vol = risk_money / (sl_dist / tick_sz * tick_val);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step<=0) step = vmin;
   vol = MathMax(vmin, MathMin(vmax, MathFloor(vol/step)*step));
   return vol;
}

bool CostOk(double sl_dist, double tp_dist)
{
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point<=0) return false;
   double spread = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * point;
   if(tp_dist < spread * 3.0) return false;
   if(sl_dist<=0 || tp_dist/sl_dist < 1.0) return false;
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
   req.comment = "GRK021";
   req.price = (type==ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                     : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double sl_dist = MathAbs(req.price - sl);
   double tp_dist = MathAbs(tp - req.price);
   if(!CostOk(sl_dist, tp_dist)) return false;
   req.volume = VolumeByRisk(sl_dist);
   if(req.volume <= 0) return false;
   return OrderSend(req, res);
}

void OnTick()
{
   if(!SymbolAllowed()) return;
   if(WeekendFlattenWindow())
   {
      FlattenAll();
      return;
   }
   Regime rg = DetectRegime();
   if(rg==REGIME_SHOCK)
   {
      FlattenAll();
      return;
   }
   if(!SpreadOk()) return;
   if(!SessionOk()) return;
   if(!DailyLossOk()) return;
   if(!NewH1Bar()) return;
   if(CountOurPositions() >= InpMaxPositions) return;
   if(rg==REGIME_FLAT) return;

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
   int dir = OurDirection();
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   if(rg==REGIME_TREND)
   {
      if(dir<=0 && bias>=0 && close1>emaS[0] && low1<=emaF[0] && close1>emaF[0])
      {
         double sl = low1 - atr[0]*0.3;
         double sl_dist = ask - sl;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_BUY, sl, ask + sl_dist * InpMinRR);
      }
      if(dir>=0 && bias<=0 && close1<emaS[0] && high1>=emaF[0] && close1<emaF[0])
      {
         double sl = high1 + atr[0]*0.3;
         double sl_dist = sl - bid;
         if(sl_dist<=0) return;
         SendDeal(ORDER_TYPE_SELL, sl, bid - sl_dist * InpMinRR);
      }
   }
   else if(rg==REGIME_RANGE)
   {
      if(dir<=0 && close1<=bbL[0] && rsi[0]<=30)
      {
         double sl = low1 - atr[0]*0.4;
         double sl_dist = ask - sl;
         double tp_dist = bbM[0] - ask;
         if(sl_dist<=0 || tp_dist/sl_dist < InpRangeMinRR) return;
         SendDeal(ORDER_TYPE_BUY, sl, bbM[0]);
      }
      if(dir>=0 && close1>=bbU[0] && rsi[0]>=70)
      {
         double sl = high1 + atr[0]*0.4;
         double sl_dist = sl - bid;
         double tp_dist = bid - bbM[0];
         if(sl_dist<=0 || tp_dist/sl_dist < InpRangeMinRR) return;
         SendDeal(ORDER_TYPE_SELL, sl, bbM[0]);
      }
   }
}
