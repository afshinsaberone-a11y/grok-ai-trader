//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5                                         |
//| ID: GRK-FX-HYBRID-005  version 2.10                              |
//| Regime switch TREND / RANGE / SHOCK + closed-bar + correct BB    |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "2.10"
#property strict

#include <Trade\Trade.mqh>
CTrade trade;

input group "=== Trend EMAs ==="
input int    EMA_Fast = 20;
input int    EMA_Mid  = 50;
input int    EMA_Slow = 200;

input group "=== Regime ==="
input int    ADX_Period = 14;
input double ADX_Trend  = 22.0;
input double ADX_Range  = 18.0;
input int    ATR_Period = 14;
input int    ATR_SMA    = 50;
input double ShockRatio = 1.8;
input int    BB_Period  = 20;
input double BB_Dev     = 2.0;
input int    RSI_Period = 14;

input group "=== Risk ==="
input double RiskTrend    = 1.0;
input double RiskRange    = 0.7;
input double ATR_SL_T     = 1.6;
input double ATR_TP_T     = 2.4;
input double RangeSL_ATR  = 1.2;
input double MinRangeRR   = 0.6;
input double MaxDailyLoss = 2.0;
input bool   UseTrailing  = true;
input double TrailStartR  = 1.0;
input int    MagicNumber  = 20260922;
input int    Slippage     = 20;
input int    MaxSpreadPts = 25;

input group "=== Session (server clock) ==="
input bool UseSession = true;
input int  SessStart  = 7;
input int  SessEnd    = 20;
input bool TradeLong  = true;
input bool TradeShort = true;

enum Regime { REG_NEUTRAL=0, REG_TREND=1, REG_RANGE=2, REG_SHOCK=3 };

int hFast,hMid,hSlow,hADX,hATR,hBB,hRSI;
double dayStartEquity = 0;
datetime lastDay = 0;
bool tradingLocked = false;

int OnInit()
{
   hFast = iMA(_Symbol,PERIOD_CURRENT,EMA_Fast,0,MODE_EMA,PRICE_CLOSE);
   hMid  = iMA(_Symbol,PERIOD_CURRENT,EMA_Mid,0,MODE_EMA,PRICE_CLOSE);
   hSlow = iMA(_Symbol,PERIOD_CURRENT,EMA_Slow,0,MODE_EMA,PRICE_CLOSE);
   hADX  = iADX(_Symbol,PERIOD_CURRENT,ADX_Period);
   hATR  = iATR(_Symbol,PERIOD_CURRENT,ATR_Period);
   hBB   = iBands(_Symbol,PERIOD_CURRENT,BB_Period,0,BB_Dev,PRICE_CLOSE);
   hRSI  = iRSI(_Symbol,PERIOD_CURRENT,RSI_Period,PRICE_CLOSE);
   if(hFast==INVALID_HANDLE||hMid==INVALID_HANDLE||hSlow==INVALID_HANDLE||
      hADX==INVALID_HANDLE||hATR==INVALID_HANDLE||hBB==INVALID_HANDLE||hRSI==INVALID_HANDLE)
      return INIT_FAILED;

   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   ApplyFilling();

   dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   lastDay = TimeCurrent();
   tradingLocked = false;
   return INIT_SUCCEEDED;
}

void ApplyFilling()
{
   if(trade.SetTypeFilling(ORDER_FILLING_IOC)) return;
   if(trade.SetTypeFilling(ORDER_FILLING_FOK)) return;
   trade.SetTypeFilling(ORDER_FILLING_RETURN);
}

void OnDeinit(const int reason)
{
   IndicatorRelease(hFast); IndicatorRelease(hMid); IndicatorRelease(hSlow);
   IndicatorRelease(hADX); IndicatorRelease(hATR); IndicatorRelease(hBB); IndicatorRelease(hRSI);
}

void OnTick()
{
   CheckDailyLoss();
   ManageTrailing();
   if(tradingLocked) return;
   if(!IsNewBar()) return;
   if(UseSession && !InSession()) return;
   if(SpreadPoints() > MaxSpreadPts) return;
   if(CountPos() > 0) { MaybeExitRangeRegimeShift(); return; }

   double emaF[3],emaM[3],emaS[3],adx[3],atr[3],rsi[3],bbU[3],bbM[3],bbL[3];
   if(CopyBuffer(hFast,0,1,3,emaF)<3) return;
   if(CopyBuffer(hMid,0,1,3,emaM)<3) return;
   if(CopyBuffer(hSlow,0,1,3,emaS)<3) return;
   if(CopyBuffer(hADX,0,1,3,adx)<3) return;
   if(CopyBuffer(hATR,0,1,3,atr)<3) return;
   if(CopyBuffer(hRSI,0,1,3,rsi)<3) return;
   if(CopyBuffer(hBB,1,1,3,bbU)<3) return;
   if(CopyBuffer(hBB,0,1,3,bbM)<3) return;
   if(CopyBuffer(hBB,2,1,3,bbL)<3) return;

   double close1 = iClose(_Symbol,PERIOD_CURRENT,1);
   double low1   = iLow(_Symbol,PERIOD_CURRENT,1);
   double high1  = iHigh(_Symbol,PERIOD_CURRENT,1);

   double atrSma = AtrSma(ATR_SMA);
   Regime reg = Classify(adx[0], atr[0], atrSma, bbU[0], bbL[0], bbM[0]);
   if(reg==REG_SHOCK || reg==REG_NEUTRAL) return;

   if(reg==REG_TREND)
   {
      bool up = emaM[0] > emaS[0];
      bool dn = emaM[0] < emaS[0];
      bool pullL = up && close1 > emaF[0] && low1 <= emaF[0] * 1.0015 && close1 > emaM[0];
      bool pullS = dn && close1 < emaF[0] && high1 >= emaF[0] * 0.9985 && close1 < emaM[0];
      if(TradeLong && pullL) OpenBuy(atr[0], RiskTrend);
      if(TradeShort && pullS) OpenSell(atr[0], RiskTrend);
   }
   else if(reg==REG_RANGE)
   {
      bool longR  = TradeLong && low1 <= bbL[0] && rsi[0] < 30.0;
      bool shortR = TradeShort && high1 >= bbU[0] && rsi[0] > 70.0;
      if(longR) OpenBuyRange(bbM[0], atr[0]);
      if(shortR) OpenSellRange(bbM[0], atr[0]);
   }
}

Regime Classify(double adx, double atr, double atrSma, double up, double lo, double mid)
{
   if(atrSma > 0 && atr / atrSma >= ShockRatio) return REG_SHOCK;
   if(adx >= ADX_Trend) return REG_TREND;
   if(adx < ADX_Range && mid > 0)
   {
      double bw = (up-lo)/mid;
      if(bw > 0) return REG_RANGE;
   }
   return REG_NEUTRAL;
}

double AtrSma(int n)
{
   if(n < 2) n = 2;
   double a[];
   if(CopyBuffer(hATR,0,1,n,a) < n) return 0;
   double s=0;
   for(int i=0;i<n;i++) s+=a[i];
   return s/n;
}

bool IsNewBar()
{
   static datetime last=0;
   datetime t=iTime(_Symbol,PERIOD_CURRENT,0);
   if(t==last) return false;
   last=t; return true;
}

bool InSession()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   return (dt.hour>=SessStart && dt.hour<SessEnd);
}

int SpreadPoints()
{
   return (int)SymbolInfoInteger(_Symbol,SYMBOL_SPREAD);
}

int CountPos()
{
   int c=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong tk=PositionGetTicket(i);
      if(tk==0 || !PositionSelectByTicket(tk)) continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==MagicNumber) c++;
   }
   return c;
}

double Tick()
{
   double t=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   return (t>0 ? t : _Point);
}

double Align(double price)
{
   double t=Tick();
   return NormalizeDouble(MathRound(price/t)*t, _Digits);
}

double MinStopDist()
{
   long stops = SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   double dist = (double)stops * _Point;
   if(dist < Tick()) dist = Tick();
   return dist;
}

double NormLots(double lots)
{
   double minl=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maxl=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0) step=0.01;
   lots=MathFloor(lots/step)*step;
   lots=MathMax(minl,MathMin(maxl,lots));
   int dg=0; double st=step;
   while(st<1.0 && dg<8){ st*=10.0; dg++; }
   return NormalizeDouble(lots,dg);
}

double LotByRisk(double slDist, double riskPct)
{
   if(slDist<=0) return 0;
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   double risk=eq*riskPct/100.0;
   double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   double tickVal=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   if(tickSize<=0 || tickVal<=0) return 0;
   double perLot=(slDist/tickSize)*tickVal;
   if(perLot<=0) return 0;
   return NormLots(risk/perLot);
}

bool StopsValid(double price, double sl, double tp, bool isBuy)
{
   double minD = MinStopDist();
   if(isBuy)
   {
      if(price - sl < minD) return false;
      if(tp > 0 && tp - price < minD) return false;
   }
   else
   {
      if(sl - price < minD) return false;
      if(tp > 0 && price - tp < minD) return false;
   }
   return true;
}

void OpenBuy(double atr, double riskPct)
{
   double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   double sl=Align(ask-atr*ATR_SL_T);
   double tp=Align(ask+atr*ATR_TP_T);
   if(!StopsValid(ask,sl,tp,true)) return;
   double lots=LotByRisk(ask-sl, riskPct);
   if(lots>0) trade.Buy(lots,_Symbol,0,sl,tp,"GRK5-TREND-L");
}

void OpenSell(double atr, double riskPct)
{
   double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double sl=Align(bid+atr*ATR_SL_T);
   double tp=Align(bid-atr*ATR_TP_T);
   if(!StopsValid(bid,sl,tp,false)) return;
   double lots=LotByRisk(sl-bid, riskPct);
   if(lots>0) trade.Sell(lots,_Symbol,0,sl,tp,"GRK5-TREND-S");
}

void OpenBuyRange(double mid, double atr)
{
   double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   double sl=Align(ask-atr*RangeSL_ATR);
   double tp=Align(mid);
   if(tp<=ask) return;
   if((tp-ask) < (ask-sl)*MinRangeRR) return;
   if(!StopsValid(ask,sl,tp,true)) return;
   double lots=LotByRisk(ask-sl, RiskRange);
   if(lots>0) trade.Buy(lots,_Symbol,0,sl,tp,"GRK5-RANGE-L");
}

void OpenSellRange(double mid, double atr)
{
   double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double sl=Align(bid+atr*RangeSL_ATR);
   double tp=Align(mid);
   if(tp>=bid) return;
   if((bid-tp) < (sl-bid)*MinRangeRR) return;
   if(!StopsValid(bid,sl,tp,false)) return;
   double lots=LotByRisk(sl-bid, RiskRange);
   if(lots>0) trade.Sell(lots,_Symbol,0,sl,tp,"GRK5-RANGE-S");
}

void MaybeExitRangeRegimeShift()
{
   double adx[];
   if(CopyBuffer(hADX,0,1,1,adx)<1) return;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong tk=PositionGetTicket(i);
      if(tk==0 || !PositionSelectByTicket(tk)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      string cmt=PositionGetString(POSITION_COMMENT);
      if(StringFind(cmt,"RANGE")>=0 && adx[0]>=ADX_Trend)
         trade.PositionClose(tk);
   }
}

void ManageTrailing()
{
   if(!UseTrailing) return;
   double atr[];
   if(CopyBuffer(hATR,0,1,1,atr)<1) return;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong tk=PositionGetTicket(i);
      if(tk==0 || !PositionSelectByTicket(tk)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      if(StringFind(PositionGetString(POSITION_COMMENT),"RANGE")>=0) continue;
      double open=PositionGetDouble(POSITION_PRICE_OPEN);
      double sl=PositionGetDouble(POSITION_SL);
      double tp=PositionGetDouble(POSITION_TP);
      long type=PositionGetInteger(POSITION_TYPE);
      double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
      double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      double r=atr[0]*ATR_SL_T;
      if(r<=0) continue;
      if(type==POSITION_TYPE_BUY)
      {
         if((bid-open)/r >= TrailStartR)
         {
            double nsl=Align(bid-atr[0]*ATR_SL_T);
            if(nsl>sl && nsl>open && (bid-nsl)>=MinStopDist()) trade.PositionModify(tk,nsl,tp);
         }
      }
      else
      {
         if((open-ask)/r >= TrailStartR)
         {
            double nsl=Align(ask+atr[0]*ATR_SL_T);
            if(sl==0 || (nsl<sl && nsl<open && (nsl-ask)>=MinStopDist())) trade.PositionModify(tk,nsl,tp);
         }
      }
   }
}

void CheckDailyLoss()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   string ds=IntegerToString(dt.year)+"."+IntegerToString(dt.mon)+"."+IntegerToString(dt.day);
   datetime today=StringToTime(ds);
   if(today!=lastDay)
   {
      dayStartEquity=AccountInfoDouble(ACCOUNT_EQUITY);
      lastDay=today;
      tradingLocked=false;
   }
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   if(dayStartEquity<=0) return;
   double pl=(eq-dayStartEquity)/dayStartEquity*100.0;
   if(pl<=-MaxDailyLoss)
   {
      tradingLocked=true;
      for(int i=PositionsTotal()-1;i>=0;i--)
      {
         ulong tk=PositionGetTicket(i);
         if(tk==0 || !PositionSelectByTicket(tk)) continue;
         if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==MagicNumber)
            trade.PositionClose(tk);
      }
   }
}
