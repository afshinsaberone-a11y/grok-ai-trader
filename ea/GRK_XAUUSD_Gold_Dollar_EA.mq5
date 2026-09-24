//+------------------------------------------------------------------+
//|                    GRK_XAUUSD_Gold_Dollar_EA.mq5                 |
//|     شناسه: GRK-XAUUSD-GOLD-DOLLAR-001  |  نسخه: 4.30             |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - XAUUSD Gold Dollar"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "4.30"

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
input int    BW_Lookback=30;
input double BB_Dev=2.0;
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
input int    TimeStopBars=16;
input int    FlattenLeadHours=1;
input int    WeekendFlattenHour=18;
input double MondayGapAtrMult=0.80;
input int    MondayGapBlockHour=10;
input int    AsiaReopenEndHour=2;
input int    MondayWideSpreadHour=8;
input double WideSpreadAtrRatio=0.12;
input double PreNewsVolRatio=0.65;
input int    PreNewsVolLookback=20;
input int    LondonOpenHour=7;
input int    LondonOpenEndHour=8;
input double LondonThinVolRatio=0.70;
input int    LondonVolLookback=20;
input double LondonWideSpreadAtr=0.10;
input double MondayLondonWideSpreadAtr=0.10;
input double MondayLondonThinVolRatio=0.70;
input int    MondayLondonVolLookback=20;
input double MondayLondonSpreadAtrMedMult=1.50;
input int    MondayLondonSpreadAtrLookback=20;
input double TuesdayLondonSpreadAtrMedMult=1.50;
input int    TuesdayLondonSpreadAtrLookback=20;
input double TuesdayLondonThinVolRatio=0.70;
input int    TuesdayLondonVolLookback=20;
input double WednesdayLondonSpreadAtrMedMult=1.50;
input int    WednesdayLondonSpreadAtrLookback=20;
input double WednesdayLondonThinVolRatio=0.70;
input int    WednesdayLondonVolLookback=20;
input double ThursdayLondonSpreadAtrMedMult=1.50;
input int    ThursdayLondonSpreadAtrLookback=20;
input int    NyOpenHour=12;
input int    NyOpenEndHour=13;
input double NyWideSpreadAtr=0.10;
input double NyThinVolRatio=0.70;
input int    NyVolLookback=20;
input int    SessionCloseHour=19;
input int    SessionCloseEndHour=20;
input double SessionCloseWideSpreadAtr=0.10;
input double SessionCloseThinVolRatio=0.70;
input int    SessionCloseVolLookback=20;
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
   Print("GRK XAUUSD Gold-Dollar EA v4.30 ready");
   return INIT_SUCCEEDED;
}
