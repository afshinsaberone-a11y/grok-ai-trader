//+------------------------------------------------------------------+
//| Robust_Regime_Momentum_V1.mq5                                    |
//| Research EA matching the Python Robust Regime-Momentum v1 rules.  |
//| No grid / martingale / averaging down. Research only.             |
//+------------------------------------------------------------------+
#property strict
#property version   "1.00"

#include <Trade/Trade.mqh>

input double RiskPercent       = 0.50;
input double MaxDailyLossPct   = 2.00;
input int    MaxTradesDay      = 3;
input int    MaxConsecutiveLoss= 2;
input int    CooldownBars      = 8;
input int    ADX_Period        = 14;
input double ADX_Min           = 22.0;
input int    ATR_Period        = 14;
input int    EMA_Fast          = 20;
input int    EMA_Slow          = 50;
input int    H1_EMA_Fast       = 50;
input int    H1_EMA_Slow       = 200;
input int    PullbackBars      = 3;
input double TouchATR          = 0.20;
input double ATR_Stop          = 1.60;
input double RR                = 2.20;
input double VolMin            = 0.70;
input double VolMax            = 1.80;
input double CostATR           = 0.10;
input double SlippageATR       = 0.02;
input int    Magic             = 20260925;

CTrade trade;
int h_adx, h_atr, h_ema_f, h_ema_s, h_h1_f, h_h1_s;
datetime last_bar=0, day_start=0;
double day_start_eq=0.0;
int trades_today=0, consec_loss=0, cooldown=0;

bool NewBar()
{
   datetime t=iTime(_Symbol,PERIOD_M5,0);
   if(t==last_bar) return false;
   last_bar=t; return true;
}

double Buf(int h,int b,int shift)
{
   double a[];
   if(CopyBuffer(h,b,shift,1,a)!=1) return EMPTY_VALUE;
   return a[0];
}

double ATRAt(int shift){ return Buf(h_atr,0,shift); }

void ResetDay()
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(),dt);
   datetime d=StringToTime(StringFormat("%04d.%02d.%02d 00:00",dt.year,dt.mon,dt.day));
   if(d!=day_start){ day_start=d; day_start_eq=AccountInfoDouble(ACCOUNT_EQUITY); trades_today=0; consec_loss=0; }
}

bool SafetyOK()
{
   if(trades_today>=MaxTradesDay || consec_loss>=MaxConsecutiveLoss || cooldown>0) return false;
   if(PositionSelect(_Symbol)) return false;
   if(day_start_eq>0 && 100.0*(day_start_eq-AccountInfoDouble(ACCOUNT_EQUITY))/day_start_eq>=MaxDailyLossPct) return false;
   return true;
}

double LotsForStop(double entry,double sl)
{
   double risk=AccountInfoDouble(ACCOUNT_EQUITY)*RiskPercent/100.0;
   double tv=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
   double ts=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   double dist=MathAbs(entry-sl);
   if(risk<=0 || tv<=0 || ts<=0 || dist<=0) return 0;
   double lots=risk/((dist/ts)*tv);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   if(step<=0) return 0;
   lots=MathFloor(lots/step)*step;
   if(lots<vmin) return 0;
   if(lots>vmax) lots=vmax;
   return lots;
}

bool RecentLongTouch()
{
   for(int s=1;s<=PullbackBars;s++)
   {
      double atr=ATRAt(s), ema=Buf(h_ema_f,0,s), low=iLow(_Symbol,PERIOD_M5,s);
      if(atr>0 && ema!=EMPTY_VALUE && low<=ema+TouchATR*atr) return true;
   }
   return false;
}

bool RecentShortTouch()
{
   for(int s=1;s<=PullbackBars;s++)
   {
      double atr=ATRAt(s), ema=Buf(h_ema_f,0,s), high=iHigh(_Symbol,PERIOD_M5,s);
      if(atr>0 && ema!=EMPTY_VALUE && high>=ema-TouchATR*atr) return true;
   }
   return false;
}

void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &req,const MqlTradeResult &res)
{
   if(trans.type!=TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if((int)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=Magic) return;
   long e=HistoryDealGetInteger(trans.deal,DEAL_ENTRY);
   if(e!=DEAL_ENTRY_OUT && e!=DEAL_ENTRY_INOUT) return;
   double p=HistoryDealGetDouble(trans.deal,DEAL_PROFIT)+HistoryDealGetDouble(trans.deal,DEAL_SWAP)+HistoryDealGetDouble(trans.deal,DEAL_COMMISSION);
   if(p<0) consec_loss++; else consec_loss=0;
   if(p<0) cooldown=CooldownBars;
}

void OnInit()
{
   trade.SetExpertMagicNumber(Magic);
   h_adx=iADX(_Symbol,PERIOD_M5,ADX_Period);
   h_atr=iATR(_Symbol,PERIOD_M5,ATR_Period);
   h_ema_f=iMA(_Symbol,PERIOD_M5,EMA_Fast,0,MODE_EMA,PRICE_CLOSE);
   h_ema_s=iMA(_Symbol,PERIOD_M5,EMA_Slow,0,MODE_EMA,PRICE_CLOSE);
   h_h1_f=iMA(_Symbol,PERIOD_H1,H1_EMA_Fast,0,MODE_EMA,PRICE_CLOSE);
   h_h1_s=iMA(_Symbol,PERIOD_H1,H1_EMA_Slow,0,MODE_EMA,PRICE_CLOSE);
}

void OnDeinit(const int r)
{
   IndicatorRelease(h_adx); IndicatorRelease(h_atr); IndicatorRelease(h_ema_f); IndicatorRelease(h_ema_s); IndicatorRelease(h_h1_f); IndicatorRelease(h_h1_s);
}

void OnTick()
{
   ResetDay();
   if(!NewBar()) return;
   if(cooldown>0) cooldown--;

   double atr=ATRAt(1);
   double atrbase=0; for(int s=1;s<=20;s++) atrbase+=ATRAt(s);
   atrbase/=20.0;
   double adx=Buf(h_adx,0,1), emaf=Buf(h_ema_f,0,1), emas=Buf(h_ema_s,0,1);
   double h1f=Buf(h_h1_f,0,1), h1s=Buf(h_h1_s,0,1);
   if(atr<=0 || atrbase<=0 || adx==EMPTY_VALUE || emaf==EMPTY_VALUE || emas==EMPTY_VALUE || h1f==EMPTY_VALUE || h1s==EMPTY_VALUE) return;
   double ratio=atr/atrbase;
   if(ratio<VolMin || ratio>VolMax || adx<ADX_Min || !SafetyOK()) return;

   double c=iClose(_Symbol,PERIOD_M5,1), o=iOpen(_Symbol,PERIOD_M5,1);
   bool long_sig=(h1f>h1s && emaf>emas && c>o && RecentLongTouch() && c>emaf);
   bool short_sig=(h1f<h1s && emaf<emas && c<o && RecentShortTouch() && c<emaf);
   if(!long_sig && !short_sig) return;

   bool buy=long_sig;
   double ask=SymbolInfoDouble(_Symbol,SYMBOL_ASK), bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double entry=buy?ask:bid;
   double dist=ATR_Stop*atr;
   double sl=buy?entry-dist:entry+dist;
   double tp=buy?entry+RR*dist:entry-RR*dist;
   int digits=(int)SymbolInfoInteger(_Symbol,SYMBOL_DIGITS);
   sl=NormalizeDouble(sl,digits); tp=NormalizeDouble(tp,digits);
   double lots=LotsForStop(entry,sl);
   if(lots<=0) return;

   bool ok=buy?trade.Buy(lots,_Symbol,entry,sl,tp,"RRM-v1"):trade.Sell(lots,_Symbol,entry,sl,tp,"RRM-v1");
   if(ok && (trade.ResultRetcode()==TRADE_RETCODE_DONE || trade.ResultRetcode()==TRADE_RETCODE_PLACED)) trades_today++;
}
//+------------------------------------------------------------------+
