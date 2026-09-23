//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5                                         |
//| ID: GRK-FX-HYBRID-014 version 2.90                              |
//| TREND/RANGE/COMPRESS/SHOCK + freeze/volume/Monday skip           |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "2.90"
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
input int    MagicNumber  = 20260923;
input int    Slippage     = 20;
input int    MaxSpreadPts = 25;
input int    NewsBlackoutMin = 15;
input int    MaxConsecLoss   = 3;
input double MaxLot         = 5.0;
input int    MondaySkipBars = 2;
input int    MaxPositions    = 1;
input int    ShockLockBars   = 3;
input bool   HalfRiskAfterLoss = true;

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
int shockLockLeft = 0;
bool tradingLocked = false;
bool halfRiskActive = false;

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
   shockLockLeft = 0;
   tradingLocked = false;
   halfRiskActive = false;
   return INIT_SUCCEEDED;
}
