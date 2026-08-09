//+------------------------------------------------------------------+
//|                              GRK_Hybrid_Trend_ATR_EA.mq5         |
//|                        شناسه: GRK-FX-HYBRID-001                   |
//|     استراتژی هیبرید ترند + ATR + ADX توسط Grok AI Trader         |
//|     ریپو: https://github.com/afshinsaberone-a11y/grok-ai-trader   |
//+------------------------------------------------------------------+
#property copyright "Grok AI Trader - GRK-FX-HYBRID-001"
#property link      "https://github.com/afshinsaberone-a11y/grok-ai-trader"
#property version   "1.00"
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

input group "=== ATR Risk Management ==="
input int      ATR_Period   = 14;     // ATR Period
input double   ATR_SL_Mult  = 1.5;    // SL = ATR * Mult
input double   ATR_TP_Mult  = 2.5;    // TP = ATR * Mult
input bool     UseTrailing  = true;   // Use ATR Trailing Stop
input double   Trail_Start_R= 1.0;    // Start trailing after X R

input group "=== Risk & Money Management ==="
input double   RiskPercent  = 1.0;    // Risk % per trade
input double   MaxDailyLoss = 3.0;    // Max daily loss % (stop trading)
input int      MagicNumber  = 20260809; // Magic Number

input group "=== Session Filter (UTC) ==="
input bool     UseSessionFilter = true;
input int      SessionStartHour = 7;  // Start hour UTC (approx London)
input int      SessionEndHour   = 20; // End hour UTC (after NY)

input group "=== General ==="
input bool     TradeLong    = true;
input bool     TradeShort   = true;
input int      Slippage     = 10;     // Max slippage points

//--- Global handles
int hEMA_Fast, hEMA_Mid, hEMA_Slow, hADX, hATR;
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

   if(hEMA_Fast==INVALID_HANDLE || hEMA_Mid==INVALID_HANDLE || hEMA_Slow==INVALID_HANDLE ||
      hADX==INVALID_HANDLE || hATR==INVALID_HANDLE)
   {
      Print("Error creating indicators");
      return INIT_FAILED;
   }

   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(Slippage);
   trade.SetTypeFilling(ORDER_FILLING_IOC);

   dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
   lastDay = TimeCurrent();

   Print("GRK Hybrid Trend-ATR EA initialized | ID: GRK-FX-HYBRID-001");
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
}

//+------------------------------------------------------------------+
void OnTick()
{
   // Daily loss check
   CheckDailyLoss();

   if(!IsNewBar()) return;  // Only on new bar for simplicity

   if(UseSessionFilter && !IsInSession()) return;

   if(CountOpenPositions() > 0)
   {
      ManageTrailing();
      return;
   }

   // Get indicator values
   double emaFast[3], emaMid[3], emaSlow[3], adx[3], atr[3];
   if(CopyBuffer(hEMA_Fast,0,0,3,emaFast)<3) return;
   if(CopyBuffer(hEMA_Mid,0,0,3,emaMid)<3) return;
   if(CopyBuffer(hEMA_Slow,0,0,3,emaSlow)<3) return;
   if(CopyBuffer(hADX,0,0,3,adx)<3) return;  // ADX main line
   if(CopyBuffer(hATR,0,0,3,atr)<3) return;

   double close0 = iClose(_Symbol, PERIOD_CURRENT, 0);
   double close1 = iClose(_Symbol, PERIOD_CURRENT, 1);

   bool trendUp   = emaMid[0] > emaSlow[0];
   bool trendDown = emaMid[0] < emaSlow[0];
   bool strongTrend = adx[0] > ADX_Threshold;

   // Long signal: EMA Fast cross above Mid + trend up + strong ADX
   bool longSignal = TradeLong && trendUp && strongTrend &&
                     emaFast[1] <= emaMid[1] && emaFast[0] > emaMid[0] &&
                     close0 > emaFast[0];

   // Short signal
   bool shortSignal = TradeShort && trendDown && strongTrend &&
                      emaFast[1] >= emaMid[1] && emaFast[0] < emaMid[0] &&
                      close0 < emaFast[0];

   if(longSignal)
   {
      double sl = close0 - atr[0] * ATR_SL_Mult;
      double tp = close0 + atr[0] * ATR_TP_Mult;
      double lots = CalculateLotSize(close0 - sl);
      if(lots > 0)
      {
         trade.Buy(lots, _Symbol, 0, sl, tp, "GRK-Hybrid-Long");
         Print("Long opened | Lot:", lots, " SL:", sl, " TP:", tp);
      }
   }
   else if(shortSignal)
   {
      double sl = close0 + atr[0] * ATR_SL_Mult;
      double tp = close0 - atr[0] * ATR_TP_Mult;
      double lots = CalculateLotSize(sl - close0);
      if(lots > 0)
      {
         trade.Sell(lots, _Symbol, 0, sl, tp, "GRK-Hybrid-Short");
         Print("Short opened | Lot:", lots, " SL:", sl, " TP:", tp);
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
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
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
   double point     = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   if(tickSize == 0 || tickValue == 0) return 0;

   double lossPerLot = (slDistance / tickSize) * tickValue;
   if(lossPerLot <= 0) return 0;

   double lots = riskMoney / lossPerLot;

   // Normalize lot
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
      if(!PositionSelectByTicket(PositionGetTicket(i))) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;

      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL = PositionGetDouble(POSITION_SL);
      double currentTP = PositionGetDouble(POSITION_TP);
      long type = PositionGetInteger(POSITION_TYPE);

      double newSL = 0;
      if(type == POSITION_TYPE_BUY)
      {
         newSL = SymbolInfoDouble(_Symbol, SYMBOL_BID) - atr[0] * ATR_SL_Mult;
         if(newSL > currentSL && newSL > openPrice)  // only move up and in profit
         {
            trade.PositionModify(PositionGetTicket(i), newSL, currentTP);
         }
      }
      else if(type == POSITION_TYPE_SELL)
      {
         newSL = SymbolInfoDouble(_Symbol, SYMBOL_ASK) + atr[0] * ATR_SL_Mult;
         if((currentSL == 0 || newSL < currentSL) && newSL < openPrice)
         {
            trade.PositionModify(PositionGetTicket(i), newSL, currentTP);
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
   double dailyPL = (currentBalance - dailyStartBalance) / dailyStartBalance * 100.0;

   if(dailyPL <= -MaxDailyLoss)
   {
      // Close all positions of this EA
      for(int i = PositionsTotal()-1; i >= 0; i--)
      {
         if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
            trade.PositionClose(PositionGetTicket(i));
      }
      Print("Daily loss limit reached. Trading stopped for today.");
   }
}
//+------------------------------------------------------------------+
