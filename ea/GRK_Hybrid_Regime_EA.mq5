//+------------------------------------------------------------------+
//| GRK_Hybrid_Regime_EA.mq5  GRK-FX-2026-041                        |
//+------------------------------------------------------------------+
#property copyright "grok-ai-trader"
#property version   "41.0"
input double RiskPercent=0.5;
input double DailyLossLimit=2.0;
input int MaxPositions=1;
input int ADX_Period=14;
input int ADX_Trend=22;
input int ADX_Range=18;
input int MA200_Period=200;
input int ATR_Period=14;
input double SpreadMultMax=1.4;
input long Magic=2026041;
int adx_h,ma_h,atr_h;
int OnInit(){
  if(RiskPercent>0.6) return INIT_FAILED;
  adx_h=iADX(_Symbol,PERIOD_CURRENT,ADX_Period);
  ma_h=iMA(_Symbol,PERIOD_CURRENT,MA200_Period,0,MODE_SMA,PRICE_CLOSE);
  atr_h=iATR(_Symbol,PERIOD_CURRENT,ATR_Period);
  if(adx_h==INVALID_HANDLE||ma_h==INVALID_HANDLE||atr_h==INVALID_HANDLE) return INIT_FAILED;
  return INIT_SUCCEEDED;
}
bool SpreadOk(){
  double atr[];
  if(CopyBuffer(atr_h,0,1,20,atr)<20) return false;
  double mid=atr[10];
  double spr=(double)SymbolInfoInteger(_Symbol,SYMBOL_SPREAD)*SymbolInfoDouble(_Symbol,SYMBOL_POINT);
  return spr<=SpreadMultMax*mid*0.15;
}
int Regime(){
  double adx[],ma[];
  if(CopyBuffer(adx_h,0,0,2,adx)<2) return 0;
  if(CopyBuffer(ma_h,0,0,2,ma)<2) return 0;
  if(adx[0]>=ADX_Trend) return 1;
  if(adx[0]<=ADX_Range) return -1;
  return 2;
}
double PositionSize(double sl_points){
  double risk_money=AccountInfoDouble(ACCOUNT_EQUITY)*RiskPercent/100.0;
  double tick_val=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
  double tick_sz=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
  if(sl_points<=0||tick_val<=0) return 0;
  return risk_money/(sl_points*tick_val/tick_sz);
}
void OnTick(){
  if(!SpreadOk()) return;
  if(PositionsTotal()>=MaxPositions) return;
  int rg=Regime();
  if(rg==0) return;
}
// GRK-SAFETY-CONTRACT-041
// No grid/martingale. Hard SL required. Risk<=0.6%. Spread+daily loss filters required.
