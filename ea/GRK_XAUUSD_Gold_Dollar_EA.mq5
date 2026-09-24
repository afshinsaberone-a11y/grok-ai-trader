//+------------------------------------------------------------------+
//|                    GRK_XAUUSD_Gold_Dollar_EA.mq5                 |
//|     شناسه: GRK-XAUUSD-GOLD-DOLLAR-001  |  نسخه: 3.00             |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - XAUUSD Gold Dollar"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "3.00"

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
input int    NyOpenHour=12;
input int    NyOpenEndHour=13;
input double NyWideSpreadAtr=0.10;
input double NyThinVolRatio=0.70;
input int    NyVolLookback=20;
input double MinSLSpreadMult=1.8;
input double MaxSpreadATRRatio=0.25;
input bool   UseTrailing=true;
input double TrailStartR=1.0;
input double TrailTightR=1.8;
input double TrailWideMult=1.2;
input double TrailTightMult=0.80;
input int    MagicNumber=20260922;
