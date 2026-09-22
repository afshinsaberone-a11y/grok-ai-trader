//+------------------------------------------------------------------+
//|                    GRK_XAUUSD_Gold_Dollar_EA.mq5                 |
//|     شناسه: GRK-XAUUSD-GOLD-DOLLAR-001  |  نسخه: 1.10             |
//|     ربات اختصاصی طلا/دلار با فیلتر هزینه، Squeeze و ریسک ATR     |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - XAUUSD Gold Dollar"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "1.10"

#include <Trade\\Trade.mqh>
CTrade trade;

input group "=== Trend ==="
input int    EMA_Fast=20;
input int    EMA_Mid=50;
input int    EMA_Slow=200;
input int    ADX_Period=14;
input double ADX_Min=22.0;

input group "=== Squeeze / Momentum ==="
input int    BB_Period=20;
input double BB_Dev=2.0;
input int    BW_Lookback=30;
input double BW_Pct=25.0;
input int    RSI_Period=14;
input double RSI_LongLow=40;
input double RSI_LongHigh=68;
input double RSI_ShortLow=32;
input double RSI_ShortHigh=60;

input group "=== Gold risk ==="
input int    ATR_Period=14;
input double ATR_SL=1.8;
input double ATR_TP=2.4;
input double PartialR=1.2;
input double RiskPercent=0.5;
input double MaxDailyLoss=2.0;
input double MinSLSpreadMult=1.8;
input double MaxSpreadATRRatio=0.25;
input bool   UseTrailing=true;
input int    MagicNumber=20260922;

input group "=== Session UTC ==="
input bool UseSession=true;
input int  SessionStart=7;
input int  SessionEnd=20;

int hFast,hMid,hSlow,hADX,hATR,hBB,hRSI;
double dayStart=0;
datetime lastDay=0;
bool partialDone=false;

int OnInit()
{
   hFast=iMA(_Symbol,PERIOD_CURRENT,EMA_Fast,0,MODE_EMA,PRICE_CLOSE);
   hMid =iMA(_Symbol,PERIOD_CURRENT,EMA_Mid,0,MODE_EMA,PRICE_CLOSE);
   hSlow=iMA(_Symbol,PERIOD_CURRENT,EMA_Slow,0,MODE_EMA,PRICE_CLOSE);
   hADX =iADX(_Symbol,PERIOD_CURRENT,ADX_Period);
   hATR =iATR(_Symbol,PERIOD_CURRENT,ATR_Period);
   hBB  =iBands(_Symbol,PERIOD_CURRENT,BB_Period,0,BB_Dev,PRICE_CLOSE);
   hRSI =iRSI(_Symbol,PERIOD_CURRENT,RSI_Period,PRICE_CLOSE);
   if(hFast==INVALID_HANDLE||hMid==INVALID_HANDLE||hSlow==INVALID_HANDLE||
      hADX==INVALID_HANDLE||hATR==INVALID_HANDLE||hBB==INVALID_HANDLE||hRSI==INVALID_HANDLE)
      return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(30);
   dayStart=AccountInfoDouble(ACCOUNT_BALANCE);
   lastDay=TimeCurrent();
   Print("GRK XAUUSD Gold-Dollar EA v1.10 ready");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(hFast); IndicatorRelease(hMid); IndicatorRelease(hSlow);
   IndicatorRelease(hADX); IndicatorRelease(hATR); IndicatorRelease(hBB); IndicatorRelease(hRSI);
}

bool IsNewBar()
{
   static datetime last=0;
   datetime cur=iTime(_Symbol,PERIOD_CURRENT,0);
   if(cur==last) return false;
   last=cur; return true;
}

bool InSession()
{
   if(!UseSession) return true;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   return (dt.hour>=SessionStart && dt.hour<SessionEnd);
}

int CountPos()
{
   int n=0;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong t=PositionGetTicket(i);
      if(t==0) continue;
      if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==MagicNumber) n++;
   }
   return n;
}

double LotFromSL(double slDist)
{
   if(slDist<=0) return 0;
   double risk=AccountInfoDouble(ACCOUNT_BALANCE)*RiskPercent/100.0;
   double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   double tickVal=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   if(tickSize==0||tickVal==0) return 0;
   double perLot=(slDist/tickSize)*tickVal;
   if(perLot<=0) return 0;
   double lots=risk/perLot;
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double minl=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maxl=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   lots=MathFloor(lots/step)*step;
   return NormalizeDouble(MathMax(minl,MathMin(maxl,lots)),2);
}

bool CostOk(double slDist, double atr)
{
   double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double spread=ask-bid;
   if(spread<=0) return false;
   if(slDist < MinSLSpreadMult*spread) return false;
   if(atr>0 && spread > MaxSpreadATRRatio*atr) return false;
   return true;
}

bool InSqueeze()
{
   double bw[];
   ArrayResize(bw,BW_Lookback+1);
   for(int i=0;i<=BW_Lookback;i++)
   {
      double u[1],m[1],l[1];
      if(CopyBuffer(hBB,0,i,1,u)<1||CopyBuffer(hBB,1,i,1,m)<1||CopyBuffer(hBB,2,i,1,l)<1) return false;
      if(m[0]==0) return false;
      bw[i]=(u[0]-l[0])/m[0];
   }
   int below=0;
   for(int i=1;i<=BW_Lookback;i++) if(bw[0]<=bw[i]) below++;
   return ((double)below/BW_Lookback*100.0)<=BW_Pct;
}

void CheckDay()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   datetime today=StringToTime(IntegerToString(dt.year)+"."+IntegerToString(dt.mon)+"."+IntegerToString(dt.day));
   if(today!=lastDay){ dayStart=AccountInfoDouble(ACCOUNT_BALANCE); lastDay=today; partialDone=false; }
   if(dayStart<=0) return;
   double pl=(AccountInfoDouble(ACCOUNT_BALANCE)-dayStart)/dayStart*100.0;
   if(pl<=-MaxDailyLoss)
   {
      for(int i=PositionsTotal()-1;i>=0;i--)
      {
         ulong t=PositionGetTicket(i);
         if(t==0) continue;
         if(PositionGetString(POSITION_SYMBOL)==_Symbol && PositionGetInteger(POSITION_MAGIC)==MagicNumber)
            trade.PositionClose(t);
      }
   }
}

void Manage()
{
   double atr[1]; if(CopyBuffer(hATR,0,0,1,atr)<1) return;
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong t=PositionGetTicket(i);
      if(t==0||!PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol || PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double open=PositionGetDouble(POSITION_PRICE_OPEN);
      double sl=PositionGetDouble(POSITION_SL);
      double tp=PositionGetDouble(POSITION_TP);
      double vol=PositionGetDouble(POSITION_VOLUME);
      long type=PositionGetInteger(POSITION_TYPE);
      double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
      double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      double r=atr[0]*ATR_SL;
      if(type==POSITION_TYPE_BUY)
      {
         double profitR=(bid-open)/r;
         if(!partialDone && profitR>=PartialR && vol>SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN)*1.01)
         {
            trade.PositionClosePartial(t, NormalizeDouble(vol*0.5,2));
            partialDone=true;
            trade.PositionModify(t, MathMax(sl,open), tp);
         }
         else if(UseTrailing && profitR>=1.0)
         {
            double nsl=bid-atr[0]*ATR_SL;
            if(nsl>sl && nsl>open) trade.PositionModify(t,nsl,tp);
         }
      }
      else
      {
         double profitR=(open-ask)/r;
         if(!partialDone && profitR>=PartialR && vol>SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN)*1.01)
         {
            trade.PositionClosePartial(t, NormalizeDouble(vol*0.5,2));
            partialDone=true;
            trade.PositionModify(t, (sl==0?open:MathMin(sl,open)), tp);
         }
         else if(UseTrailing && profitR>=1.0)
         {
            double nsl=ask+atr[0]*ATR_SL;
            if((sl==0||nsl<sl) && nsl<open) trade.PositionModify(t,nsl,tp);
         }
      }
   }
}

void OnTick()
{
   CheckDay();
   if(!IsNewBar()) { if(CountPos()>0) Manage(); return; }
   if(!InSession()) return;
   if(CountPos()>0) { Manage(); return; }
   partialDone=false;

   double f[3],m[3],s[3],adx[3],atr[3],rsi[3];
   if(CopyBuffer(hFast,0,0,3,f)<3) return;
   if(CopyBuffer(hMid,0,0,3,m)<3) return;
   if(CopyBuffer(hSlow,0,0,3,s)<3) return;
   if(CopyBuffer(hADX,0,0,3,adx)<3) return;
   if(CopyBuffer(hATR,0,0,3,atr)<3) return;
   if(CopyBuffer(hRSI,0,0,3,rsi)<3) return;

   bool squeeze=InSqueeze();
   bool trendUp=m[0]>s[0] && adx[0]>ADX_Min;
   bool trendDn=m[0]<s[0] && adx[0]>ADX_Min;
   bool xUp=f[1]<=m[1] && f[0]>m[0];
   bool xDn=f[1]>=m[1] && f[0]<m[0];
   double close0=iClose(_Symbol,PERIOD_CURRENT,0);

   if(trendUp && squeeze && xUp && rsi[0]>=RSI_LongLow && rsi[0]<=RSI_LongHigh)
   {
      double sl=close0-atr[0]*ATR_SL;
      double tp=close0+atr[0]*ATR_TP;
      if(CostOk(close0-sl, atr[0]))
      {
         double lots=LotFromSL(close0-sl);
         if(lots>0) trade.Buy(lots,_Symbol,0,sl,tp,"XAU-GD-L-v1.1");
      }
   }
   else if(trendDn && squeeze && xDn && rsi[0]>=RSI_ShortLow && rsi[0]<=RSI_ShortHigh)
   {
      double sl=close0+atr[0]*ATR_SL;
      double tp=close0-atr[0]*ATR_TP;
      if(CostOk(sl-close0, atr[0]))
      {
         double lots=LotFromSL(sl-close0);
         if(lots>0) trade.Sell(lots,_Symbol,0,sl,tp,"XAU-GD-S-v1.1");
      }
   }
}
