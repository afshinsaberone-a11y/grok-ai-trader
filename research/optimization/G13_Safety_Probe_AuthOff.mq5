//+------------------------------------------------------------------+
//| ForexAI G13 Execution Safety Probe - Authorization OFF           |
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

void WriteProbe(const string label,const long mode,const bool account_identity_verified,const bool account_login_present,const bool account_server_present,const bool auth,const bool kill_switch,const bool other,
               const bool terminal_connected,const bool terminal_trade_allowed,const bool mql_trade_allowed,
               const bool account_trade_allowed,const bool account_trade_expert,
               const int symbol_trade_mode,const bool symbol_market,const bool symbol_sl,const bool symbol_tp,
               const long stops_level,const bool allowed)
{
   string file="g13_safety_probe_"+label+".done.txt";
   int h=FileOpen(file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ);
   if(h==INVALID_HANDLE) return;
   FileWrite(h,"status,PASS");
   FileWrite(h,"probe,"+label);
   FileWrite(h,"account_mode,"+IntegerToString((int)mode));
   FileWrite(h,"account_identity_verified,"+(string)(account_identity_verified ? "true" : "false"));
   FileWrite(h,"account_login_present,"+(string)(account_login_present ? "true" : "false"));
   FileWrite(h,"account_server_present,"+(string)(account_server_present ? "true" : "false"));
   FileWrite(h,"demo_account,"+(string)((mode==ACCOUNT_TRADE_MODE_DEMO && account_identity_verified) ? "true" : "false"));
   FileWrite(h,"real_account_detected,"+(string)((mode==ACCOUNT_TRADE_MODE_REAL && account_identity_verified) ? "true" : "false"));
   FileWrite(h,"authorization,"+(string)(auth ? "true" : "false"));
   FileWrite(h,"kill_switch_allow,"+(string)(kill_switch ? "true" : "false"));
   FileWrite(h,"other_g13_position,"+(string)(other ? "true" : "false"));
   FileWrite(h,"terminal_connected,"+(string)(terminal_connected ? "true" : "false"));
   FileWrite(h,"terminal_trade_allowed,"+(string)(terminal_trade_allowed ? "true" : "false"));
   FileWrite(h,"mql_trade_allowed,"+(string)(mql_trade_allowed ? "true" : "false"));
   FileWrite(h,"account_trade_allowed,"+(string)(account_trade_allowed ? "true" : "false"));
   FileWrite(h,"account_trade_expert,"+(string)(account_trade_expert ? "true" : "false"));
   FileWrite(h,"symbol_trade_mode,"+IntegerToString(symbol_trade_mode));
   FileWrite(h,"symbol_market_order_allowed,"+(string)(symbol_market ? "true" : "false"));
   FileWrite(h,"symbol_sl_allowed,"+(string)(symbol_sl ? "true" : "false"));
   FileWrite(h,"symbol_tp_allowed,"+(string)(symbol_tp ? "true" : "false"));
   FileWrite(h,"stops_level_points,"+IntegerToString((int)stops_level));
   FileWrite(h,"execution_allowed,"+(string)(allowed ? "true" : "false"));
   FileWrite(h,"orders_submitted,false");
   FileWrite(h,"probe_only,true");
   FileClose(h);
}

void OnStart()
{
   // One live MT5 session supplies a consistent read-only snapshot for
   // both authorization states. The authorization flag is only a predicate
   // input; this script contains no order APIs and always records no orders.
   const bool authorized_off=false;
   const bool authorized_on=true;
   bool terminal_connected=false;
   long account_login=0;
   string account_server="";
   bool account_identity_verified=false;
   const int identity_wait_seconds=45;

   // MT5 can launch the startup script before the saved Demo session has
   // completed its connection handshake. Wait boundedly for the account
   // identity; never infer a login/server or accept an unverified account.
   for(int wait_second=0; wait_second<identity_wait_seconds; ++wait_second)
   {
      terminal_connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);
      account_login=AccountInfoInteger(ACCOUNT_LOGIN);
      account_server=AccountInfoString(ACCOUNT_SERVER);
      account_identity_verified=terminal_connected && account_login>0 && StringLen(account_server)>0;
      if(account_identity_verified || IsStopped()) break;
      Sleep(1000);
   }
   // Refresh once after the last bounded wait so the emitted marker reflects
   // the latest real terminal state, including a just-completed connection.
   terminal_connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);
   account_login=AccountInfoInteger(ACCOUNT_LOGIN);
   account_server=AccountInfoString(ACCOUNT_SERVER);
   account_identity_verified=terminal_connected && account_login>0 && StringLen(account_server)>0;

   const long mode=AccountInfoInteger(ACCOUNT_TRADE_MODE);
   const bool kill_switch=DemoKillSwitchAllowed();
   const bool other_off=HasOtherG13Position(0);
   const bool other_on=HasOtherG13Position(130002);
   const bool terminal_trade_allowed=(bool)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED);
   const bool mql_trade_allowed=(bool)MQLInfoInteger(MQL_TRADE_ALLOWED);
   const bool account_trade_allowed=(bool)AccountInfoInteger(ACCOUNT_TRADE_ALLOWED);
   const bool account_trade_expert=(bool)AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
   const int symbol_trade_mode=(int)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE);
   const long symbol_order_mode=SymbolInfoInteger(_Symbol,SYMBOL_ORDER_MODE);
   const bool symbol_market=(symbol_order_mode & SYMBOL_ORDER_MARKET)!=0;
   const bool symbol_sl=(symbol_order_mode & SYMBOL_ORDER_SL)!=0;
   const bool symbol_tp=(symbol_order_mode & SYMBOL_ORDER_TP)!=0;
   const long stops_level=(long)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   const bool symbol_sell=(symbol_trade_mode==SYMBOL_TRADE_MODE_FULL || symbol_trade_mode==SYMBOL_TRADE_MODE_SHORTONLY);

   // Authorization ON/OFF are two evaluations of the same actual account
   // and terminal snapshot. This avoids restarting MT5 (which can discard the
   // saved session), while keeping Kill Switch DENY as the independent blocker.
   const bool shared_gate_open=(mode==ACCOUNT_TRADE_MODE_DEMO &&
                                account_identity_verified &&
                                terminal_connected &&
                                terminal_trade_allowed &&
                                mql_trade_allowed &&
                                account_trade_allowed &&
                                account_trade_expert &&
                                symbol_sell &&
                                symbol_market &&
                                symbol_sl &&
                                symbol_tp &&
                                stops_level>=0 &&
                                kill_switch);
   const bool allowed_off=authorized_off && shared_gate_open && !other_off;
   const bool allowed_on=authorized_on && shared_gate_open && !other_on;

   // Write Auth ON first and Auth OFF last. The workflow waits for the Auth OFF
   // marker, so its appearance proves that both same-session markers are ready.
   WriteProbe("auth_on",mode,account_identity_verified,account_login>0,StringLen(account_server)>0,authorized_on,kill_switch,other_on,
              terminal_connected,terminal_trade_allowed,mql_trade_allowed,
              account_trade_allowed,account_trade_expert,
              symbol_trade_mode,symbol_market,symbol_sl,symbol_tp,stops_level,allowed_on);
   WriteProbe("auth_off",mode,account_identity_verified,account_login>0,StringLen(account_server)>0,authorized_off,kill_switch,other_off,
              terminal_connected,terminal_trade_allowed,mql_trade_allowed,
              account_trade_allowed,account_trade_expert,
              symbol_trade_mode,symbol_market,symbol_sl,symbol_tp,stops_level,allowed_off);
}
//+------------------------------------------------------------------+
