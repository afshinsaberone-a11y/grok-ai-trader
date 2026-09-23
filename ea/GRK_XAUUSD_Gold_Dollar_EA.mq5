//+------------------------------------------------------------------+
//|                    GRK_XAUUSD_Gold_Dollar_EA.mq5                 |
//|     شناسه: GRK-XAUUSD-GOLD-DOLLAR-001  |  نسخه: 2.10             |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - XAUUSD Gold Dollar"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "2.10"

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
input int    ATR_MedPeriod=50;
input double ATR_SL=1.8;
input double ATR_SL_Low=1.6;
input double ATR_SL_High=2.2;
input double ATR_LowRatio=0.85;
input double ATR_HighRatio=1.40;
input double ShockAtrMult=2.0;
input double PullbackAtr=0.25;
input double ATR_TP=2.4;
input double PartialR=1.2;
input double RiskPercent=0.5;
input double LossRiskMult=0.5;
input double MaxDailyLoss=2.0;
input double MaxDailyLossEntry=1.0;
input int    MaxTradesPerDay=2;
input int    MaxConsecutiveLossesPerDay=2;
input double MinSLSpreadMult=1.8;
input double MaxSpreadATRRatio=0.25;
input bool   UseTrailing=true;
input double TrailStartR=1.0;
input double TrailTightR=1.8;
input double TrailWideMult=1.2;
input double TrailTightMult=0.80;
input int    MagicNumber=20260922;

input group "=== Session UTC ==="
input bool UseSession=true;
input int  SessionStart=7;
input int  SessionEnd=20;
input int  CoreSessionStart=12;
input int  CoreSessionEnd=16;
input int  MinQuality=2;

input group "=== High-risk news window ==="
input bool UseNewsBlock=true;
input int  NewsFriStart=12;
input int  NewsFriEnd=15;
input int  NewsWedStart=18;
input int  NewsWedEnd=20;

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
   Print("GRK XAUUSD Gold-Dollar EA v2.10 ready");
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

bool InCoreSession()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   return (dt.hour>=CoreSessionStart && dt.hour<CoreSessionEnd);
}

bool InNewsWindow()
{
   if(!UseNewsBlock) return false;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   if(dt.day_of_week==5 && dt.hour>=NewsFriStart && dt.hour<NewsFriEnd) return true;
   if(dt.day_of_week==3 && dt.hour>=NewsWedStart && dt.hour<NewsWedEnd) return true;
   return false;
}

int QualityScore(double adx0, double adx1, double bw0, double bw1)
{
   int q=0;
   if(InCoreSession()) q++;
   if(adx0>adx1 && adx0>=ADX_Min) q++;
   if(bw0>bw1) q++;
   return q;
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

datetime DayStartTime()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   dt.hour=0; dt.min=0; dt.sec=0;
   return StructToTime(dt);
}

int CountTodayEntries()
{
   datetime from=DayStartTime();
   if(!HistorySelect(from,TimeCurrent())) return 0;
   int n=0;
   int total=HistoryDealsTotal();
   for(int i=0;i<total;i++)
   {
      ulong ticket=HistoryDealGetTicket(i);
      if(ticket==0) continue;
      if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol) continue;
      if((int)HistoryDealGetInteger(ticket,DEAL_MAGIC)!=MagicNumber) continue;
      if((int)HistoryDealGetInteger(ticket,DEAL_ENTRY)!=DEAL_ENTRY_IN) continue;
      n++;
   }
   return n;
}

bool DayCapReached()
{
   if(MaxTradesPerDay<=0) return false;
   return CountTodayEntries()>=MaxTradesPerDay;
}

int TodayConsecutiveLosses()
{
   datetime from=DayStartTime();
   if(!HistorySelect(from,TimeCurrent())) return 0;
   int consec=0;
   int total=HistoryDealsTotal();
   for(int i=0;i<total;i++)
   {
      ulong ticket=HistoryDealGetTicket(i);
      if(ticket==0) continue;
      if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol) continue;
      if((int)HistoryDealGetInteger(ticket,DEAL_MAGIC)!=MagicNumber) continue;
      if((int)HistoryDealGetInteger(ticket,DEAL_ENTRY)!=DEAL_ENTRY_OUT) continue;
      double profit=HistoryDealGetDouble(ticket,DEAL_PROFIT)
                   +HistoryDealGetDouble(ticket,DEAL_SWAP)
                   +HistoryDealGetDouble(ticket,DEAL_COMMISSION);
      if(profit<0.0) consec++;
      else consec=0;
   }
   return consec;
}

bool ConsecutiveLossLockReached()
{
   if(MaxConsecutiveLossesPerDay<=0) return false;
   return TodayConsecutiveLosses()>=MaxConsecutiveLossesPerDay;
}

bool NeedsRiskCut()
{
   return TodayConsecutiveLosses()>=1;
}

double TodayClosedPnL()
{
   datetime from=DayStartTime();
   if(!HistorySelect(from,TimeCurrent())) return 0.0;
   double pnl=0.0;
   int total=HistoryDealsTotal();
   for(int i=0;i<total;i++)
   {
      ulong ticket=HistoryDealGetTicket(i);
      if(ticket==0) continue;
      if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol) continue;
      if((int)HistoryDealGetInteger(ticket,DEAL_MAGIC)!=MagicNumber) continue;
      if((int)HistoryDealGetInteger(ticket,DEAL_ENTRY)!=DEAL_ENTRY_OUT) continue;
      pnl+=HistoryDealGetDouble(ticket,DEAL_PROFIT)
          +HistoryDealGetDouble(ticket,DEAL_SWAP)
          +HistoryDealGetDouble(ticket,DEAL_COMMISSION);
   }
   return pnl;
}

bool DailyLossEntryCapReached()
{
   if(MaxDailyLossEntry<=0.0) return false;
   if(dayStart<=0.0) return false;
   double closed=TodayClosedPnL();
   return (closed/dayStart*100.0) <= -MaxDailyLossEntry;
}

double LotFromSL(double slDist)
{
   if(slDist<=0) return 0;
   double riskPct=RiskPercent;
   if(NeedsRiskCut() && LossRiskMult>0.0 && LossRiskMult<1.0)
      riskPct=RiskPercent*LossRiskMult;
   double risk=AccountInfoDouble(ACCOUNT_BALANCE)*riskPct/100.0;
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

double AtrMedian(int period)
{
   double buf[];
   int n=period;
   if(n<5) n=5;
   ArraySetAsSeries(buf,true);
   if(CopyBuffer(hATR,0,0,n,buf)<n) return 0;
   double tmp[];
   ArrayResize(tmp,n);
   for(int i=0;i<n;i++) tmp[i]=buf[i];
   ArraySort(tmp);
   if((n%2)==1) return tmp[n/2];
   return 0.5*(tmp[n/2-1]+tmp[n/2]);
}

double SlMult(double atr)
{
   double med=AtrMedian(ATR_MedPeriod);
   if(med<=0 || atr<=0) return ATR_SL;
   double ratio=atr/med;
   if(ratio>=ATR_HighRatio) return ATR_SL_High;
   if(ratio<=ATR_LowRatio) return ATR_SL_Low;
   return ATR_SL;
}

bool ShockRegime(double atr)
{
   double med=AtrMedian(ATR_MedPeriod);
   if(med<=0 || atr<=0) return false;
   return (atr > ShockAtrMult * med);
}

double TrailMultFromR(double profitR)
{
   if(profitR < TrailStartR) return 0.0;
   if(profitR >= TrailTightR) return TrailTightMult;
   return TrailWideMult;
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

bool BwExpanding()
{
   double u0[1],m0[1],l0[1],u1[1],m1[1],l1[1];
   if(CopyBuffer(hBB,0,0,1,u0)<1||CopyBuffer(hBB,1,0,1,m0)<1||CopyBuffer(hBB,2,0,1,l0)<1) return false;
   if(CopyBuffer(hBB,0,1,1,u1)<1||CopyBuffer(hBB,1,1,1,m1)<1||CopyBuffer(hBB,2,1,1,l1)<1) return false;
   if(m0[0]==0||m1[0]==0) return false;
   double bw0=(u0[0]-l0[0])/m0[0];
   double bw1=(u1[0]-l1[0])/m1[0];
   return bw0>bw1;
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
   double slm=SlMult(atr[0]);
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
      double r=atr[0]*slm;
      if(r<=0) continue;
      if(type==POSITION_TYPE_BUY)
      {
         double profitR=(bid-open)/r;
         if(!partialDone && profitR>=PartialR && vol>SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN)*1.01)
         {
            trade.PositionClosePartial(t, NormalizeDouble(vol*0.5,2));
            partialDone=true;
            trade.PositionModify(t, MathMax(sl,open), tp);
         }
         else if(UseTrailing)
         {
            double tmult=TrailMultFromR(profitR);
            if(tmult>0)
            {
               double nsl=bid-atr[0]*tmult;
               if(nsl>sl && nsl>open) trade.PositionModify(t,nsl,tp);
            }
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
         else if(UseTrailing)
         {
            double tmult=TrailMultFromR(profitR);
            if(tmult>0)
            {
               double nsl=ask+atr[0]*tmult;
               if((sl==0||nsl<sl) && nsl<open) trade.PositionModify(t,nsl,tp);
            }
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
   if(InNewsWindow()) return;
   if(DayCapReached()) return;
   if(ConsecutiveLossLockReached()) return;
   if(DailyLossEntryCapReached()) return;

   double f[3],m[3],s[3],adx[3],atr[3],rsi[3];
   if(CopyBuffer(hFast,0,0,3,f)<3) return;
   if(CopyBuffer(hMid,0,0,3,m)<3) return;
   if(CopyBuffer(hSlow,0,0,3,s)<3) return;
   if(CopyBuffer(hADX,0,0,3,adx)<3) return;
   if(CopyBuffer(hATR,0,0,3,atr)<3) return;
   if(CopyBuffer(hRSI,0,0,3,rsi)<3) return;

   if(ShockRegime(atr[0])) return;

   bool squeeze=InSqueeze();
   bool trendUp=m[0]>s[0] && adx[0]>ADX_Min;
   bool trendDn=m[0]<s[0] && adx[0]>ADX_Min;
   bool alignedUp=f[0]>m[0] && f[1]>m[1];
   bool alignedDn=f[0]<m[0] && f[1]<m[1];
   double close0=iClose(_Symbol,PERIOD_CURRENT,0);
   double high0=iHigh(_Symbol,PERIOD_CURRENT,0);
   double low0=iLow(_Symbol,PERIOD_CURRENT,0);
   double band=PullbackAtr*atr[0];
   bool pullUp=alignedUp && (low0<=m[0]+band) && (close0>f[0]);
   bool pullDn=alignedDn && (high0>=m[0]-band) && (close0<f[0]);
   double slm=SlMult(atr[0]);
   int q=QualityScore(adx[0],adx[1], BwExpanding()?1.0:0.0, 0.0);
   if(q<MinQuality) return;

   if(trendUp && squeeze && pullUp && rsi[0]>=RSI_LongLow && rsi[0]<=RSI_LongHigh)
   {
      double sl=close0-atr[0]*slm;
      double tp=close0+atr[0]*ATR_TP;
      if(CostOk(close0-sl, atr[0]))
      {
         double lots=LotFromSL(close0-sl);
         if(lots>0) trade.Buy(lots,_Symbol,0,sl,tp,"XAU-GD-L-v2.1");
      }
   }
   else if(trendDn && squeeze && pullDn && rsi[0]>=RSI_ShortLow && rsi[0]<=RSI_ShortHigh)
   {
      double sl=close0+atr[0]*slm;
      double tp=close0-atr[0]*ATR_TP;
      if(CostOk(sl-close0, atr[0]))
      {
         double lots=LotFromSL(sl-close0);
         if(lots>0) trade.Sell(lots,_Symbol,0,sl,tp,"XAU-GD-S-v2.1");
      }
   }
}
