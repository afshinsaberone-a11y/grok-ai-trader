//+------------------------------------------------------------------+
//|                    GRK_XAUUSD_Gold_Dollar_EA.mq5                 |
//|     شناسه: GRK-XAUUSD-GOLD-DOLLAR-001  |  نسخه: 5.50             |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - XAUUSD Gold Dollar"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "5.50"

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
input double ThursdaySessionCloseSpreadAtrMedMult=1.50;
input int    ThursdaySessionCloseSpreadAtrLookback=20;
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
   Print("GRK XAUUSD Gold-Dollar EA v5.50 ready");
   return INIT_SUCCEEDED;
}

bool ThursdaySessionCloseSpreadAtrMedBlock()
{
   MqlDateTime gt; TimeToStruct(TimeGMT(), gt);
   if(gt.day_of_week != 4) return false;
   if(gt.hour < SessionCloseHour || gt.hour >= SessionCloseEndHour) return false;
   double atr[1];
   if(CopyBuffer(hATR,0,0,1,atr)<1 || atr[0]<=0.0) return false;
   double ask = SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double spread = ask-bid;
   if(spread<=0.0) return false;
   double ratio_now = spread / atr[0];
   double sample[]; ArrayResize(sample, ThursdaySessionCloseSpreadAtrLookback);
   int n=0;
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(point<=0.0) return false;
   for(int i=1; i<=ThursdaySessionCloseSpreadAtrLookback*30 && n<ThursdaySessionCloseSpreadAtrLookback; i++)
   {
      datetime bar_time = iTime(_Symbol,PERIOD_H1,i);
      if(bar_time==0) continue;
      MqlDateTime bt; TimeToStruct(bar_time, bt);
      if(bt.day_of_week != 4) continue;
      if(bt.hour<SessionCloseHour || bt.hour>=SessionCloseEndHour) continue;
      int spr_pts = (int)iSpread(_Symbol,PERIOD_H1,i);
      if(spr_pts<=0) continue;
      double hist_spread = (double)spr_pts * point;
      if(atr[0]<=0.0) continue;
      sample[n++] = hist_spread / atr[0];
   }
   if(n<5) return false;
   ArrayResize(sample,n); ArraySort(sample);
   double med = sample[n/2];
   if(med<=0.0) return false;
   return (ratio_now >= ThursdaySessionCloseSpreadAtrMedMult * med);
}
