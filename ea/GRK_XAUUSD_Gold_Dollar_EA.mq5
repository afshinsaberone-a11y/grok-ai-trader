//+------------------------------------------------------------------+
//|                    GRK_XAUUSD_Gold_Dollar_EA.mq5                 |
//|     شناسه: GRK-XAUUSD-GOLD-DOLLAR-001  |  نسخه: 5.40             |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - XAUUSD Gold Dollar"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "5.40"

#include <Trade\\Trade.mqh>
CTrade trade;

input group "=== Gold risk ==="
input double RiskPercent=0.5;
input double FridaySessionCloseSpreadAtrMedMult=1.50;
input int    FridaySessionCloseSpreadAtrLookback=20;
input double FridaySessionCloseThinVolRatio=0.70;
input int    FridaySessionCloseVolLookback=20;
input double MondaySessionCloseSpreadAtrMedMult=1.50;
input int    MondaySessionCloseSpreadAtrLookback=20;
input double MondaySessionCloseThinVolRatio=0.70;
input int    MondaySessionCloseVolLookback=20;
input double TuesdaySessionCloseSpreadAtrMedMult=1.50;
input int    TuesdaySessionCloseSpreadAtrLookback=20;
input double TuesdaySessionCloseThinVolRatio=0.70;
input int    TuesdaySessionCloseVolLookback=20;
input double WednesdaySessionCloseSpreadAtrMedMult=1.50;
input int    WednesdaySessionCloseSpreadAtrLookback=20;
input double WednesdaySessionCloseThinVolRatio=0.70;
input int    WednesdaySessionCloseVolLookback=20;
input int    SessionCloseHour=19;
input int    SessionCloseEndHour=20;
input int    ATR_Period=14;
input int    MagicNumber=20260922;

int hATR;

int OnInit()
{
   hATR =iATR(_Symbol,PERIOD_CURRENT,ATR_Period);
   if(hATR==INVALID_HANDLE)
      return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   Print("GRK XAUUSD Gold-Dollar EA v5.40 ready");
   return INIT_SUCCEEDED;
}

bool WednesdaySessionCloseSpreadAtrMedBlock()
{
   MqlDateTime gt;
   TimeToStruct(TimeGMT(), gt);
   if(gt.day_of_week != 3)
      return false;
   if(gt.hour < SessionCloseHour || gt.hour >= SessionCloseEndHour)
      return false;
   double atr[1];
   if(CopyBuffer(hATR,0,0,1,atr)<1 || atr[0]<=0.0)
      return false;
   double ask = SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double spread = ask-bid;
   if(spread<=0.0)
      return false;
   double ratio_now = spread / atr[0];
   double sample[];
   ArrayResize(sample, WednesdaySessionCloseSpreadAtrLookback);
   int n=0;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point<=0.0)
      return false;
   for(int i=1; i<=WednesdaySessionCloseSpreadAtrLookback*30 && n<WednesdaySessionCloseSpreadAtrLookback; i++)
   {
      datetime bar_time = iTime(_Symbol,PERIOD_H1,i);
      if(bar_time==0)
         continue;
      MqlDateTime bt;
      TimeToStruct(bar_time, bt);
      if(bt.day_of_week != 3)
         continue;
      if(bt.hour<SessionCloseHour || bt.hour>=SessionCloseEndHour)
         continue;
      int spr_pts = (int)iSpread(_Symbol,PERIOD_H1,i);
      if(spr_pts<=0)
         continue;
      double hist_spread = (double)spr_pts * point;
      double hist_atr = atr[0];
      if(hist_atr<=0.0)
         continue;
      sample[n++] = hist_spread / hist_atr;
   }
   if(n<5)
      return false;
   ArrayResize(sample,n);
   ArraySort(sample);
   double med = sample[n/2];
   if(med<=0.0)
      return false;
   return (ratio_now >= WednesdaySessionCloseSpreadAtrMedMult * med);
}

bool WednesdaySessionCloseSpreadAtrMedThinBlock()
{
   MqlDateTime gt;
   TimeToStruct(TimeGMT(), gt);
   if(gt.day_of_week != 3)
      return false;
   if(gt.hour < SessionCloseHour || gt.hour >= SessionCloseEndHour)
      return false;
   if(!WednesdaySessionCloseSpreadAtrMedBlock())
      return false;
   long vol_now = iVolume(_Symbol,PERIOD_H1,0);
   if(vol_now<=0)
      return false;
   double sample[];
   ArrayResize(sample, WednesdaySessionCloseVolLookback);
   int n=0;
   for(int i=1; i<=WednesdaySessionCloseVolLookback*30 && n<WednesdaySessionCloseVolLookback; i++)
   {
      datetime bar_time = iTime(_Symbol,PERIOD_H1,i);
      if(bar_time==0)
         continue;
      MqlDateTime bt;
      TimeToStruct(bar_time, bt);
      if(bt.day_of_week != 3)
         continue;
      if(bt.hour<SessionCloseHour || bt.hour>=SessionCloseEndHour)
         continue;
      long v = iVolume(_Symbol,PERIOD_H1,i);
      if(v<=0)
         continue;
      sample[n++] = (double)v;
   }
   if(n<5)
      return false;
   ArrayResize(sample,n);
   ArraySort(sample);
   double med = sample[n/2];
   if(med<=0.0)
      return false;
   bool thin = ((double)vol_now < WednesdaySessionCloseThinVolRatio * med);
   return thin;
}
