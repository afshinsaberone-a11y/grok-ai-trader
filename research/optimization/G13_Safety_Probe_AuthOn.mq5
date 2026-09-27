//+------------------------------------------------------------------+
//| ForexAI G13 Execution Safety Probe - Authorization ON           |
//| No trading code. Reads only MT5 account/control state.            |
//+------------------------------------------------------------------+
#property strict
#property version "1.00"

bool DemoKillSwitchAllowed()
{
   int h=FileOpen("g13_demo_kill_switch.txt",FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(h==INVALID_HANDLE) return false;
   string state=FileReadString(h);
   FileClose(h);
   return state=="ALLOW";
}

bool HasOtherG13Position(long current_magic)
{
   for(int i=PositionsTotal()-1;i>=0;--i)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0) continue;
      long magic=PositionGetInteger(POSITION_MAGIC);
      if(magic>=130000+2 && magic<=130000+48 && magic!=current_magic) return true;
   }
   return false;
}

void WriteProbe(const string label,const long mode,const bool auth,const bool kill_switch,const bool other,
               const bool terminal_connected,const bool terminal_trade_allowed,const bool mql_trade_allowed,
               const bool account_trade_allowed,const bool account_trade_expert,const bool allowed)
{
   string file="g13_safety_probe_"+label+".done.txt";
   int h=FileOpen(file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(h==INVALID_HANDLE) return;
   FileWrite(h,"status,PASS");
   FileWrite(h,"probe,"+label);
   FileWrite(h,"account_mode,"+IntegerToString((int)mode));
   FileWrite(h,"demo_account,"+(string)(mode==ACCOUNT_TRADE_MODE_DEMO ? "true" : "false"));
   FileWrite(h,"live_blocked,"+(string)(mode!=ACCOUNT_TRADE_MODE_DEMO ? "true" : "false"));
   FileWrite(h,"authorization,"+(string)(auth ? "true" : "false"));
   FileWrite(h,"kill_switch_allow,"+(string)(kill_switch ? "true" : "false"));
   FileWrite(h,"other_g13_position,"+(string)(other ? "true" : "false"));
   FileWrite(h,"terminal_connected,"+(string)(terminal_connected ? "true" : "false"));
   FileWrite(h,"terminal_trade_allowed,"+(string)(terminal_trade_allowed ? "true" : "false"));
   FileWrite(h,"mql_trade_allowed,"+(string)(mql_trade_allowed ? "true" : "false"));
   FileWrite(h,"account_trade_allowed,"+(string)(account_trade_allowed ? "true" : "false"));
   FileWrite(h,"account_trade_expert,"+(string)(account_trade_expert ? "true" : "false"));
   FileWrite(h,"execution_allowed,"+(string)(allowed ? "true" : "false"));
   FileWrite(h,"orders_submitted,false");
   FileWrite(h,"probe_only,true");
   FileClose(h);
}

void OnStart()
{
   const long mode=AccountInfoInteger(ACCOUNT_TRADE_MODE);
   const bool authorized=true;
   const bool kill_switch=DemoKillSwitchAllowed();
   const bool other=HasOtherG13Position(130000+2);
   const bool terminal_connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);
   const bool terminal_trade_allowed=(bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);
   const bool mql_trade_allowed=(bool)MQLInfoInteger(MQL_TRADE_ALLOWED);
   const bool account_trade_allowed=(bool)AccountInfoInteger(ACCOUNT_TRADE_ALLOWED);
   const bool account_trade_expert=(bool)AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
   const bool allowed=authorized &&
                      mode==ACCOUNT_TRADE_MODE_DEMO &&
                      terminal_connected &&
                      terminal_trade_allowed &&
                      mql_trade_allowed &&
                      account_trade_allowed &&
                      account_trade_expert &&
                      kill_switch &&
                      !other;

   WriteProbe("auth_on",mode,authorized,kill_switch,other,
              terminal_connected,terminal_trade_allowed,mql_trade_allowed,
              account_trade_allowed,account_trade_expert,allowed);
}
//+------------------------------------------------------------------+
