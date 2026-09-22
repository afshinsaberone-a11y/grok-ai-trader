//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5                                         |
//| ID: GRK-FX-HYBRID-012 version 2.70                              |
//| TREND/RANGE/COMPRESS/SHOCK + freeze/volume/Monday skip           |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "2.70"
#property strict

#include <Trade\\Trade.mqh>
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
input double CompressRatio = 0.72;
input int    BB_Period  = 20;
input double BB_Dev     = 2.0;
input double BB_MaxWidth= 0.035;
input int    RSI_Period = 14;
input bool   UseHtfFilter = true;
input bool   UseDiFilter  = true;
input bool   UseCompress  = true;

input group "=== Risk ==="
input double RiskTrend    = 1.0;
input double RiskRange    = 0.7;
input double RiskCompress = 0.6;
input double ATR_SL_T     = 1.6;
input double ATR_TP_T     = 2.4;
input double RangeSL_ATR  = 1.2;
input double MinRangeRR   = 0.6;
input double MaxDailyLoss = 2.0;
input double MaxPeakDD    = 3.0;
input int    MaxTradesDay = 4;
input int    CooldownBars = 2;
input double MinTpSpread  = 3.0;
input double SpreadAtrMax = 0.35;
input double MinFreeMarginPct = 20.0;
input bool   UseTrailing  = true;
input double TrailStartR  = 1.0;
input int    MagicNumber  = 20260922;
input int    Slippage     = 20;
input int    MaxSpreadPts = 25;
input int    NewsBlackoutMin = 15;
input int    MaxConsecLoss   = 3;
input double MaxLot         = 5.0;
input int    MondaySkipBars = 2;

input group "=== Session (server + GMT offset hours) ==="
input bool UseSession = true;
input int  SessStart  = 7;
input int  SessEnd    = 20;
input int  GmtOffset  = 0;
input bool FridayCut  = true;
input int  FridayCutHour = 18;
input bool TradeLong  = true;
input bool TradeShort = true;

enum Regime { REG_NEUTRAL=0, REG_TREND=1, REG_RANGE=2, REG_SHOCK=3, REG_COMPRESS=4 };

int hFast,hMid,hSlow,hADX,hPlus,hMinus,hATR,hBB,hRSI,hHtf;
double dayStartEquity = 0;
double equityPeak = 0;
int lastYday = -1;
int lastYyear = -1;
int tradesToday = 0;
int cooldownLeft = 0;
int consecLoss = 0;
bool tradingLocked = false;

int OnInit()
{
   hFast = iMA(_Symbol,PERIOD_CURRENT,EMA_Fast,0,MODE_EMA,PRICE_CLOSE);
   hMid  = iMA(_Symbol,PERIOD_CURRENT,EMA_Mid,0,MODE_EMA,PRICE_CLOSE);
   hSlow = iMA(_Symbol,PERIOD_CURRENT,EMA_Slow,0,MODE_EMA,PRICE_CLOSE);
   hADX  = iADX(_Symbol,PERIOD_CURRENT,ADX_Period);
   hPlus = iADX(_Symbol,PERIOD_CURRENT,ADX_Period);
   hMinus= iADX(_Symbol,PERIOD_CURRENT,ADX_Period);
   hATR  = iATR(_Symbol,PERIOD_CURRENT,ATR_Period);
   hBB   = iBands(_Symbol,PERIOD_CURRENT,BB_Period,0,BB_Dev,PRICE_CLOSE);
   hRSI  = iRSI(_Symbol,PERIOD_CURRENT,RSI_Period,PRICE_CLOSE);
   hHtf  = iMA(_Symbol,PERIOD_H1,EMA_Slow,0,MODE_EMA,PRICE_CLOSE);
   if(hFast==INVALID_HANDLE||hMid==INVALID_HANDLE||hSlow==INVALID_HANDLE||
      hADX==INVALID_HANDLE||hPlus==INVALID_HANDLE||hMinus==INVALID_HANDLE||
      hATR==INVALID_HANDLE||hBB==INVALID_HANDLE||
      hRSI==INVALID_HANDLE||hHtf==INVALID_HANDLE)
      return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   ApplyFilling();
   dayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   equityPeak = dayStartEquity;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   lastYday = dt.day_of_year;
   lastYyear = dt.year;
   tradesToday = 0;
   cooldownLeft = 0;
   consecLoss = 0;
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
   IndicatorRelease(hADX); IndicatorRelease(hPlus); IndicatorRelease(hMinus);
   IndicatorRelease(hATR); IndicatorRelease(hBB);
   IndicatorRelease(hRSI); IndicatorRelease(hHtf);
}

void OnTick()
{
   CheckDailyLoss();
   ManageTrailing();
   if(tradingLocked) return;
   if(!IsNewBar()) return;
   if(cooldownLeft > 0) cooldownLeft--;
   if(UseSession && !InSession()) return;
   if(FridayBlocked()) return;
   if(MondaySkip()) return;
   if(NewsBlocked()) return;
   if(SpreadPoints() > MaxSpreadPts) return;
   if(!TradeAllowed()) return;

   double emaF[3],emaM[3],emaS[3],adx[3],pdi[3],mdi[3],atr[3],rsi[3],bbU[3],bbM[3],bbL[3],htf[3];
   if(CopyBuffer(hFast,0,1,3,emaF)<3) return;
   if(CopyBuffer(hMid,0,1,3,emaM)<3) return;
   if(CopyBuffer(hSlow,0,1,3,emaS)<3) return;
   if(CopyBuffer(hADX,0,1,3,adx)<3) return;
   if(CopyBuffer(hPlus,1,1,3,pdi)<3) return;
   if(CopyBuffer(hMinus,2,1,3,mdi)<3) return;
   if(CopyBuffer(hATR,0,1,3,atr)<3) return;
   if(CopyBuffer(hRSI,0,1,3,rsi)<3) return;
   if(CopyBuffer(hBB,1,1,3,bbU)<3) return;
   if(CopyBuffer(hBB,0,1,3,bbM)<3) return;
   if(CopyBuffer(hBB,2,1,3,bbL)<3) return;
   if(CopyBuffer(hHtf,0,1,3,htf)<3) return;
   if(atr[0] > 0 && SpreadPtsToPrice()/atr[0] > SpreadAtrMax) return;

   double atrSma = AtrSma(ATR_SMA);
   Regime reg = Classify(adx[0], atr[0], atrSma, bbU[0], bbL[0], bbM[0]);
   if(CountPos() > 0) { MaybeExitRange(reg, adx[0]); return; }
   if(reg==REG_SHOCK || reg==REG_NEUTRAL) return;
   if(tradesToday >= MaxTradesDay) return;
   if(cooldownLeft > 0) return;
   if(!HasFreeMargin()) return;

   double close1 = iClose(_Symbol,PERIOD_CURRENT,1);
   double close2 = iClose(_Symbol,PERIOD_CURRENT,2);
   double low1   = iLow(_Symbol,PERIOD_CURRENT,1);
   double high1  = iHigh(_Symbol,PERIOD_CURRENT,1);
   double high2  = iHigh(_Symbol,PERIOD_CURRENT,2);
   double low2   = iLow(_Symbol,PERIOD_CURRENT,2);
   double htfClose = iClose(_Symbol,PERIOD_H1,1);

   if(reg==REG_TREND)
   {
      bool htfUp = !UseHtfFilter || htfClose > htf[0];
      bool htfDn = !UseHtfFilter || htfClose < htf[0];
      bool diUp  = !UseDiFilter || pdi[0] > mdi[0];
      bool diDn  = !UseDiFilter || mdi[0] > pdi[0];
      bool up = emaM[0] > emaS[0] && htfUp && diUp;
      bool dn = emaM[0] < emaS[0] && htfDn && diDn;
      bool pullL = up && close1 > emaF[0] && low1 <= emaF[0] * 1.0015 && close1 > emaM[0];
      bool pullS = dn && close1 < emaF[0] && high1 >= emaF[0] * 0.9985 && close1 < emaM[0];
      if(TradeLong && pullL) OpenBuy(atr[0], RiskTrend, "GRK12-TREND-L");
      if(TradeShort && pullS) OpenSell(atr[0], RiskTrend, "GRK12-TREND-S");
   }
   else if(reg==REG_RANGE)
   {
      bool longR  = TradeLong && low1 <= bbL[0] && close1 > bbL[0] && close1 < bbM[0] && rsi[0] < 30.0;
      bool shortR = TradeShort && high1 >= bbU[0] && close1 < bbU[0] && close1 > bbM[0] && rsi[0] > 70.0;
      if(longR) OpenBuyRange(bbM[0], atr[0]);
      if(shortR) OpenSellRange(bbM[0], atr[0]);
   }
   else if(reg==REG_COMPRESS && UseCompress)
   {
      bool brkL = TradeLong && close1 > high2 && close1 > close2;
      bool brkS = TradeShort && close1 < low2 && close1 < close2;
      if(brkL) OpenBuy(atr[0], RiskCompress, "GRK12-CMP-L");
      if(brkS) OpenSell(atr[0], RiskCompress, "GRK12-CMP-S");
   }
}

Regime Classify(double adx, double atr, double atrSma, double up, double lo, double mid)
{
   if(atrSma > 0 && atr / atrSma >= ShockRatio) return REG_SHOCK;
   if(adx >= ADX_Trend) return REG_TREND;
   if(UseCompress && atrSma > 0 && atr / atrSma <= CompressRatio && adx < ADX_Trend)
      return REG_COMPRESS;
   if(adx < ADX_Range && mid > 0)
   {
      double bw = (up-lo)/mid;
      if(bw > 0 && bw <= BB_MaxWidth) return REG_RANGE;
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
   int hour = dt.hour + GmtOffset;
   while(hour < 0) hour += 24;
   while(hour >= 24) hour -= 24;
   return (hour>=SessStart && hour<SessEnd);
}

bool NewsBlocked()
{
   if(NewsBlackoutMin <= 0) return false;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   int hour = dt.hour + GmtOffset;
   while(hour < 0) hour += 24;
   while(hour >= 24) hour -= 24;
   int releaseHours[6] = {8,9,12,13,14,15};
   for(int i=0;i<6;i++)
      if(hour==releaseHours[i] && dt.min < NewsBlackoutMin) return true;
   return false;
}

bool FridayBlocked()
{
   if(!FridayCut) return false;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   int hour = dt.hour + GmtOffset;
   while(hour < 0) hour += 24;
   while(hour >= 24) hour -= 24;
   if(dt.day_of_week == 5 && hour >= FridayCutHour) return true;
   if(dt.day_of_week == 6 || dt.day_of_week == 0) return true;
   return false;
}

bool MondaySkip()
{
   if(MondaySkipBars <= 0) return false;
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   if(dt.day_of_week != 1) return false;
   datetime dayStart = StringToTime(StringFormat("%04d.%02d.%02d 00:00", dt.year, dt.mon, dt.day));
   int shift = iBarShift(_Symbol, PERIOD_CURRENT, dayStart, false);
   if(shift < 0) return false;
   int barsToday = shift + 1;
   return (barsToday <= MondaySkipBars);
}

bool TradeAllowed()
{
   long mode = SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE);
   return (mode == SYMBOL_TRADE_MODE_FULL);
}

int SpreadPoints() { return (int)SymbolInfoInteger(_Symbol,SYMBOL_SPREAD); }
double SpreadPtsToPrice() { return (double)SpreadPoints() * _Point; }

bool HasFreeMargin()
{
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double free = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(eq <= 0) return false;
   return (free / eq * 100.0) >= MinFreeMarginPct;
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
   long freeze = SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL);
   double dist = (double)MathMax(stops, freeze) * _Point;
   if(dist < Tick()) dist = Tick();
   return dist;
}

double NormLots(double lots)
{
   double minl=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double maxl=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double lim=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_LIMIT);
   if(step<=0) step=0.01;
   lots=MathFloor(lots/step)*step;
   lots=MathMax(minl,MathMin(maxl,lots));
   if(lim > 0) lots=MathMin(lots, lim);
   if(MaxLot > 0) lots=MathMin(lots, MaxLot);
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
   double minTp = MathMax(minD, SpreadPtsToPrice() * MinTpSpread);
   if(isBuy) { if(price - sl < minD) return false; if(tp > 0 && tp - price < minTp) return false; }
   else { if(sl - price < minD) return false; if(tp > 0 && price - tp < minTp) return false; }
   return true;
}

void NoteFill() { tradesToday++; }

void OpenBuy(double atr, double riskPct, string cmt)
{
   double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   double sl=Align(ask-atr*ATR_SL_T);
   double tp=Align(ask+atr*ATR_TP_T);
   if(!StopsValid(ask,sl,tp,true)) return;
   double lots=LotByRisk(ask-sl, riskPct);
   if(lots>0 && trade.Buy(lots,_Symbol,0,sl,tp,cmt)) NoteFill();
}

void OpenSell(double atr, double riskPct, string cmt)
{
   double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double sl=Align(bid+atr*ATR_SL_T);
   double tp=Align(bid-atr*ATR_TP_T);
   if(!StopsValid(bid,sl,tp,false)) return;
   double lots=LotByRisk(sl-bid, riskPct);
   if(lots>0 && trade.Sell(lots,_Symbol,0,sl,tp,cmt)) NoteFill();
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
   if(lots>0 && trade.Buy(lots,_Symbol,0,sl,tp,"GRK12-RANGE-L")) NoteFill();
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
   if(lots>0 && trade.Sell(lots,_Symbol,0,sl,tp,"GRK12-RANGE-S")) NoteFill();
}

void MaybeExitRange(Regime reg, double adx)
{
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong tk=PositionGetTicket(i);
      if(tk==0 || !PositionSelectByTicket(tk)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      string cmt=PositionGetString(POSITION_COMMENT);
      if(StringFind(cmt,"RANGE")>=0 && (adx>=ADX_Trend || reg==REG_SHOCK))
      {
         if(trade.PositionClose(tk))
            cooldownLeft = CooldownBars;
      }
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
   if(dt.year!=lastYyear || dt.day_of_year!=lastYday)
   {
      dayStartEquity=AccountInfoDouble(ACCOUNT_EQUITY);
      equityPeak=dayStartEquity;
      lastYday=dt.day_of_year;
      lastYyear=dt.year;
      tradesToday=0;
      cooldownLeft=0;
      consecLoss=0;
      tradingLocked=false;
   }
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq > equityPeak) equityPeak = eq;
   if(dayStartEquity<=0) return;
   double pl=(eq-dayStartEquity)/dayStartEquity*100.0;
   double dd=0;
   if(equityPeak>0) dd=(equityPeak-eq)/equityPeak*100.0;
   if(pl<=-MaxDailyLoss || dd>=MaxPeakDD)
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

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   ulong deal = trans.deal;
   if(deal == 0) return;
   if(!HistoryDealSelect(deal)) return;
   if(HistoryDealGetString(deal, DEAL_SYMBOL) != _Symbol) return;
   if((long)HistoryDealGetInteger(deal, DEAL_MAGIC) != MagicNumber) return;
   long entry = HistoryDealGetInteger(deal, DEAL_ENTRY);
   if(entry != DEAL_ENTRY_OUT && entry != DEAL_ENTRY_INOUT) return;
   double profit = HistoryDealGetDouble(deal, DEAL_PROFIT)
                 + HistoryDealGetDouble(deal, DEAL_SWAP)
                 + HistoryDealGetDouble(deal, DEAL_COMMISSION);
   if(profit < 0)
   {
      cooldownLeft = CooldownBars;
      consecLoss++;
      if(MaxConsecLoss > 0 && consecLoss >= MaxConsecLoss)
         tradingLocked = true;
   }
   else
      consecLoss = 0;
}
