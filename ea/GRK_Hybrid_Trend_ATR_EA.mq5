//+------------------------------------------------------------------+
//|                              GRK_Hybrid_Trend_ATR_EA.mq5         |
//|                        شناسه: GRK-FX-HYBRID-002                   |
//|     استراتژی هیبرید ترند + ATR + ADX + Bollinger Squeeze         |
//|     توسط Grok (استاد تریدر فارکس و نابغه برنامه‌نویسی)             |
//|     ریپو: https://github.com/afshinsaberone-a11y/grok-ai-trader   |
//|     نسخه: 1.10 (بهبود یافته از 1.00)                               |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - GRK-FX-HYBRID-002"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "1.10"
#property strict

#include <Trade\Trade.mqh>
CTrade trade;

//--- Input parameters
input group "=== Moving Averages ==="
input int      EMA_Fast     = 20;     // Fast EMA
input int      EMA_Mid      = 50;     // Mid EMA
input int      EMA_Slow     = 200;    // Slow EMA (trend filter)

input group "=== ADX Filter ==="
input int      ADX_Period   = 14;     // ADX Period
input double   ADX_Threshold= 25.0;   // Minimum ADX for trend

input group "=== Bollinger Squeeze ==="
input int      BB_Period    = 20;     // Bollinger Period
input double   BB_Deviation = 2.0;    // Bollinger Deviation
input int      BW_Lookback  = 20;     // Bandwidth percentile lookback
input double   BW_Percentile= 25.0;   // Enter only if BW in lowest X%

input group "=== ATR Risk Management ==="
input int      ATR_Period   = 14;     // ATR Period
input double   ATR_SL_Mult  = 1.5;    // SL = ATR * Mult
input double   ATR_TP_Mult  = 2.5;    // TP = ATR * Mult
input bool     UseTrailing  = true;   // Use ATR Trailing Stop
input double   Trail_Start_R= 1.0;    // Start trailing after X R

input group "=== Risk & Money Management ==="
input double   RiskPercent  = 1.0;    // Risk % per trade
input double   MaxDailyLoss = 3.0;    // Max daily loss % (stop trading)
input int      MagicNumber  = 20260810; // Magic Number

input group "=== Session Filter (UTC) ==="
input bool     UseSessionFilter = true;
input int      SessionStartHour = 7;  // Start hour UTC (approx London)
input int      SessionEndHour   = 20; // End hour UTC (after NY)

input group "=== General ==="
input bool     TradeLong    = true;
input bool     TradeShort   = true;
input int      Slippage     = 10;     // Max slippage points
input bool     OnlyOneTrade = true;   // Only one position at a time

//--- Global handles
int hEMA_Fast, hEMA_Mid, hEMA_Slow, hADX, hATR, hBB;
double dailyStartBalance = 0;
datetime lastDay = 0;

//+------------------------------------------------------------------+
int OnInit()
{
   hEMA_Fast = iMA(_Symbol, PERIOD_CURRENT, EMA_Fast, 0, MODE_EMA, PRICE_CLOSE);
   hEMA_Mid  = iMA(_Symbol, PERIOD_CURRENT, EMA_Mid,  0, MODE_EMA, PRICE_CLOSE);
   hEMA_Slow = iMA(_Symbol, PERIOD_CURRENT, EMA_Slow, 0, MODE_EMA, PRICE_CLOSE);
   hADX      = iADX(_Symbol, PERIOD_CURRENT, ADX_Period);
   hATR      = iATR(_Symbol, PERIOD_CURRENT, ATR_Period);
   hBB       = iBands(_Symbol, PERIOD_CURRENT, BB_Period, 0, BB_Deviation, PRICE_CLOSE);

   if(hEMA_Fast==INVALID_HANDLE || hEMA_Mid==INVALID_HANDLE || hEMA_Slow==INVALID_HANDLE ||
      hADX==INVALID_HANDLE || hATR==INVALID_HANDLE || hBB==INVALID_HANDLE)
   {
      Print("Error creating indicators");
      return INIT_FAILED;
   }

   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);

   dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   lastDay = TimeCurrent();

   Print("GRK Hybrid Trend-ATR-Squeeze EA v1.10 initialized | ID: GRK-FX-HYBRID-002");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(hEMA_Fast);
   IndicatorRelease(hEMA_Mid);
   IndicatorRelease(hEMA_Slow);
   IndicatorRelease(hADX);
   IndicatorRelease(hATR);
   IndicatorRelease(hBB);
}

//+------------------------------------------------------------------+
void OnTick()
{
   CheckDailyLoss();

   if(!IsNewBar()) return;

   if(UseSessionFilter && !IsInSession()) return;

   int openPos = CountOpenPositions();
   if(openPos > 0)
   {
      ManageTrailing();
      if(OnlyOneTrade) return;
   }

   // Get indicator values
   double emaFast[3], emaMid[3], emaSlow[3], adx[3], atr[3];
   double bbUpper[3], bbMid[3], bbLower[3];
   if(CopyBuffer(hEMA_Fast,0,0,3,emaFast)<3) return;
   if(CopyBuffer(hEMA_Mid,0,0,3,emaMid)<3) return;
   if(CopyBuffer(hEMA_Slow,0,0,3,emaSlow)<3) return;
   if(CopyBuffer(hADX,0,0,3,adx)<3) return;
   if(CopyBuffer(hATR,0,0,3,atr)<3) return;
   if(CopyBuffer(hBB,0,0,3,bbUpper)<3) return; // Upper
   if(CopyBuffer(hBB,1,0,3,bbMid)<3) return;   // Middle
   if(CopyBuffer(hBB,2,0,3,bbLower)<3) return; // Lower

   // Bandwidth calculation for current and history
   double bw[50];
   ArraySetAsSeries(bw, true);
   int copied = MathMin(BW_Lookback + 5, 50);
   for(int i=0; i<copied; i++)
   {
      double u[], m[], l[];
      if(CopyBuffer(hBB,0,i,1,u)<1 || CopyBuffer(hBB,1,i,1,m)<1 || CopyBuffer(hBB,2,i,1,l)<1) continue;
      if(m[0] == 0) continue;
      bw[i] = (u[0] - l[0]) / m[0]; // relative bandwidth
   }

   // Check if current BW is in lowest BW_Percentile of lookback
   bool inSqueeze = false;
   if(copied >= BW_Lookback)
   {
      double currentBW = bw[0];
      int belowCount = 0;
      for(int i=1; i<=BW_Lookback; i++)
      {
         if(bw[i] > 0 && currentBW <= bw[i]) belowCount++;
      }
      double pct = (double)belowCount / BW_Lookback * 100.0;
      inSqueeze = (pct <= BW_Percentile);
   }

   double close0 = iClose(_Symbol, PERIOD_CURRENT, 0);

   bool trendUp   = emaMid[0] > emaSlow[0];
   bool trendDown = emaMid[0] < emaSlow[0];
   bool strongTrend = adx[0] > ADX_Threshold;

   // Long: trend + strong + squeeze recent + cross
   bool longSignal = TradeLong && trendUp && strongTrend && inSqueeze &&
                     emaFast[1] <= emaMid[1] && emaFast[0] > emaMid[0] &&
                     close0 > emaFast[0];

   bool shortSignal = TradeShort && trendDown && strongTrend && inSqueeze &&
                      emaFast[1] >= emaMid[1] && emaFast[0] < emaMid[0] &&
                      close0 < emaFast[0];

   if(longSignal && openPos == 0)
   {
      double sl = close0 - atr[0] * ATR_SL_Mult;
      double tp = close0 + atr[0] * ATR_TP_Mult;
      double lots = CalculateLotSize(close0 - sl);
      if(lots > 0)
      {
         if(trade.Buy(lots, _Symbol, 0, sl, tp, "GRK-Hybrid-Long-v2"))
            Print("Long opened | Lot:", lots, " SL:", sl, " TP:", tp, " Squeeze:", inSqueeze);
      }
   }
   else if(shortSignal && openPos == 0)
   {
      double sl = close0 + atr[0] * ATR_SL_Mult;
      double tp = close0 - atr[0] * ATR_TP_Mult;
      double lots = CalculateLotSize(sl - close0);
      if(lots > 0)
      {
         if(trade.Sell(lots, _Symbol, 0, sl, tp, "GRK-Hybrid-Short-v2"))
            Print("Short opened | Lot:", lots, " SL:", sl, " TP:", tp, " Squeeze:", inSqueeze);
      }
   }
}

//+------------------------------------------------------------------+
bool IsNewBar()
{
   static datetime lastBar = 0;
   datetime curBar = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(curBar == lastBar) return false;
   lastBar = curBar;
   return true;
}

//+------------------------------------------------------------------+
bool IsInSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int hour = dt.hour;
   return (hour >= SessionStartHour && hour < SessionEndHour);
}

//+------------------------------------------------------------------+
int CountOpenPositions()
{
   int count = 0;
   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
         count++;
   }
   return count;
}

//+------------------------------------------------------------------+
double CalculateLotSize(double slDistance)
{
   if(slDistance <= 0) return 0;

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskMoney = balance * RiskPercent / 100.0;

   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);

   if(tickSize == 0 || tickValue == 0) return 0;

   double lossPerLot = (slDistance / tickSize) * tickValue;
   if(lossPerLot <= 0) return 0;

   double lots = riskMoney / lossPerLot;

   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lots = MathFloor(lots / lotStep) * lotStep;
   lots = MathMax(minLot, MathMin(maxLot, lots));

   return NormalizeDouble(lots, 2);
}

//+------------------------------------------------------------------+
void ManageTrailing()
{
   if(!UseTrailing) return;

   double atr[];
   if(CopyBuffer(hATR,0,0,1,atr)<1) return;

   for(int i = PositionsTotal()-1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL = PositionGetDouble(POSITION_SL);
      double currentTP = PositionGetDouble(POSITION_TP);
      long type = PositionGetInteger(POSITION_TYPE);
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      double rDistance = atr[0] * ATR_SL_Mult; // approximate 1R

      if(type == POSITION_TYPE_BUY)
      {
         double profitR = (bid - openPrice) / rDistance;
         if(profitR >= Trail_Start_R)
         {
            double newSL = bid - atr[0] * ATR_SL_Mult;
            if(newSL > currentSL && newSL > openPrice)
            {
               trade.PositionModify(ticket, newSL, currentTP);
            }
         }
      }
      else if(type == POSITION_TYPE_SELL)
      {
         double profitR = (openPrice - ask) / rDistance;
         if(profitR >= Trail_Start_R)
         {
            double newSL = ask + atr[0] * ATR_SL_Mult;
            if((currentSL == 0 || newSL < currentSL) && newSL < openPrice)
            {
               trade.PositionModify(ticket, newSL, currentTP);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
void CheckDailyLoss()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   datetime today = StringToTime(IntegerToString(dt.year)+"."+IntegerToString(dt.mon)+"."+IntegerToString(dt.day));

   if(today != lastDay)
   {
      dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      lastDay = today;
   }

   double currentBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(dailyStartBalance <= 0) return;
   double dailyPL = (currentBalance - dailyStartBalance) / dailyStartBalance * 100.0;

   if(dailyPL <= -MaxDailyLoss)
   {
      for(int i = PositionsTotal()-1; i >= 0; i--)
      {
         ulong ticket = PositionGetTicket(i);
         if(ticket == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            trade.PositionClose(ticket);
      }
      Print("Daily loss limit reached. Trading stopped for today.");
   }
}
//+------------------------------------------------------------------+
