"""Generate a standalone MQL5 parity harness from the frozen G13 handoff.

The harness reads the REAL EURUSD M15 CSV directly in MQL5 FILE_COMMON and
recomputes the canonical G13 RSI/ATR/pivot logic without using broker history.
No synthetic bars or fallback data are created.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "forexai.g13.candidate_handoff.frozen.v1"


TEMPLATE = r'''//+------------------------------------------------------------------+
//| ForexAI G13 MQL5 Real-Data Signal Parity Harness                 |
//| Generated from frozen candidate handoff; research-only.          |
//+------------------------------------------------------------------+
#property strict
#property version "1.00"

input string InputFile = "g13_real_eurusd_m15.csv";
input string OutputFile = "g13_mql5_parity.csv";
input string DoneFile = "g13_mql5_parity.done.txt";

struct Bar
{
   string ts;
   double open;
   double high;
   double low;
   double close;
};

const int CANDIDATE_COUNT=15;
const int CIDS[CANDIDATE_COUNT]={__CIDS__};
const int PIVOTS[CANDIDATE_COUNT]={__PIVOTS__};
const double MIN_DELTAS[CANDIDATE_COUNT]={__DELTAS__};
const double ATR_MULTS[CANDIDATE_COUNT]={__ATR_MULTS__};
const double RRS[CANDIDATE_COUNT]={__RRS__};
const double RSI_HIGHS[CANDIDATE_COUNT]={__RSI_HIGHS__};

bool FiniteValue(const double x)
{
   return(MathIsValidNumber(x) && x!=EMPTY_VALUE);
}

string IsoTimestamp(const string ts)
{
   if(StringLen(ts)<16) return "";
   return StringSubstr(ts,0,4)+"-"+StringSubstr(ts,5,2)+"-"+StringSubstr(ts,8,2)
      +"T"+StringSubstr(ts,11,5)+":00+00:00";
}

bool ReadRealM15(Bar &bars[])
{
   ArrayResize(bars,0);
   ResetLastError();
   int h=FileOpen(InputFile,FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
   if(h==INVALID_HANDLE)
   {
      PrintFormat("PARITY_HARNESS_FAIL file_open error=%d",GetLastError());
      return false;
   }

   // Header: timestamp,Open,High,Low,Close,Volume
   string h0=FileReadString(h);
   string h1=FileReadString(h);
   string h2=FileReadString(h);
   string h3=FileReadString(h);
   string h4=FileReadString(h);
   string h5=FileReadString(h);
   if(StringToLower(h0)!="timestamp")
   {
      PrintFormat("PARITY_HARNESS_FAIL bad_header=%s",h0);
      FileClose(h);
      return false;
   }

   int cap=100000;
   ArrayResize(bars,cap);
   int n=0;
   string prevTs="";

   while(!FileIsEnding(h))
   {
      string ts=FileReadString(h);
      if(ts=="") break;
      string so=FileReadString(h);
      string sh=FileReadString(h);
      string sl=FileReadString(h);
      string sc=FileReadString(h);
      string sv=FileReadString(h);
      if(ts=="" || so=="" || sh=="" || sl=="" || sc=="")
         break;

      if(prevTs!="" && ts<prevTs)
      {
         PrintFormat("PARITY_HARNESS_FAIL non_monotonic timestamp=%s prev=%s",ts,prevTs);
         FileClose(h);
         return false;
      }
      prevTs=ts;

      int year=(int)StringToInteger(StringSubstr(ts,0,4));
      if(year<2022 || year>2025)
      {
         PrintFormat("PARITY_HARNESS_FAIL out_of_scope_timestamp=%s",ts);
         FileClose(h);
         return false;
      }

      if(n>=cap)
      {
         cap+=50000;
         ArrayResize(bars,cap);
      }
      bars[n].ts=ts;
      bars[n].open=StringToDouble(so);
      bars[n].high=StringToDouble(sh);
      bars[n].low=StringToDouble(sl);
      bars[n].close=StringToDouble(sc);
      ++n;
   }
   FileClose(h);
   ArrayResize(bars,n);

   if(n<100)
   {
      PrintFormat("PARITY_HARNESS_FAIL insufficient_rows=%d",n);
      return false;
   }
   PrintFormat("PARITY_INPUT_ROWS=%d FIRST=%s LAST=%s",n,bars[0].ts,bars[n-1].ts);
   return true;
}

void BuildIndicators(const Bar &b[],const int n,double &atr[],double &rsi[])
{
   ArrayResize(atr,n);
   ArrayResize(rsi,n);

   for(int i=0;i<n;i++)
   {
      atr[i]=EMPTY_VALUE;
      rsi[i]=EMPTY_VALUE;
   }

   for(int i=13;i<n;i++)
   {
      double sum=0.0;
      for(int k=i-13;k<=i;k++)
      {
         double prev=(k>0 ? b[k-1].close : b[k].close);
         double tr=MathMax(b[k].high-b[k].low,
                  MathMax(MathAbs(b[k].high-prev),MathAbs(b[k].low-prev)));
         sum+=tr;
      }
      atr[i]=sum/14.0;
   }

   // pandas rolling(14) over diff() first becomes valid at index 14.
   for(int i=14;i<n;i++)
   {
      double gain=0.0,loss=0.0;
      for(int k=i-13;k<=i;k++)
      {
         double delta=b[k].close-b[k-1].close;
         if(delta>0.0) gain+=delta;
         else if(delta<0.0) loss-=delta;
      }
      gain/=14.0;
      loss/=14.0;
      if(loss>0.0)
         rsi[i]=100.0-100.0/(1.0+gain/loss);
   }
}

bool IsPivotHigh(const Bar &b[],const int n,const int idx,const int p)
{
   if(idx<p || idx+p>=n) return false;
   double v=b[idx].high;
   for(int j=idx-p;j<=idx+p;j++)
      if(b[j].high>v) return false;
   return true;
}

int CountSignals(
   const Bar &b[],const int n,
   const double &atr[],const double &rsi[],
   const int pivot,const double minDelta,const double atrMult,
   const double rr,const double rsiHigh,const int cid,
   int &outRows)
{
   outRows=0;
   if(n<=2*pivot+2) return 0;

   double newerHigh=0.0,olderHigh=0.0,newerRsi=0.0,olderRsi=0.0;
   int highCount=0;

   int outHandle=FileOpen(OutputFile,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|
                                     FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
   if(outHandle==INVALID_HANDLE)
   {
      PrintFormat("PARITY_HARNESS_FAIL output_open cid=%d error=%d",cid,GetLastError());
      return -1;
   }
   FileSeek(outHandle,0,SEEK_END);

   for(int i=pivot;i<n-pivot;i++)
   {
      if(!FiniteValue(rsi[i]) || !FiniteValue(atr[i]))
         continue;

      int pi=i-pivot;
      if(IsPivotHigh(b,n,pi,pivot))
      {
         if(highCount==0)
         {
            newerHigh=b[pi].high;
            newerRsi=rsi[pi];
            highCount=1;
         }
         else
         {
            olderHigh=newerHigh;
            olderRsi=newerRsi;
            newerHigh=b[pi].high;
            newerRsi=rsi[pi];
            highCount=2;
         }
      }

      if(highCount>=2 &&
         newerHigh>olderHigh+minDelta &&
         newerRsi<olderRsi &&
         newerRsi>=rsiHigh)
      {
         int next=i+1;
         if(next<n)
         {
            double risk=atr[i]*atrMult;
            double entry=b[next].open;
            double sl=entry+risk;
            double tp=entry-rr*risk;
            string iso=IsoTimestamp(b[next].ts);
            if(iso=="")
            {
               FileClose(outHandle);
               PrintFormat("PARITY_HARNESS_FAIL bad_output_timestamp cid=%d index=%d",cid,next);
               return -1;
            }
            FileWrite(outHandle,cid,"SIGNAL",iso,-1,
                      DoubleToString(entry,10),DoubleToString(sl,10),
                      DoubleToString(tp,10),DoubleToString(atr[i],10));
            ++outRows;
         }
      }
   }

   FileClose(outHandle);
   return outRows;
}

void OnStart()
{
   Bar bars[];
   if(!ReadRealM15(bars))
      return;

   double atr[],rsi[];
   BuildIndicators(bars,ArraySize(bars),atr,rsi);

   // Always start a fresh output for deterministic parity evidence.
   int trunc=FileOpen(OutputFile,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
   if(trunc==INVALID_HANDLE)
   {
      PrintFormat("PARITY_HARNESS_FAIL truncate_output error=%d",GetLastError());
      return;
   }
   FileWrite(trunc,"candidate_id","event","timestamp","side","entry","sl","tp","atr");
   FileClose(trunc);

   int totalRows=0;
   for(int c=0;c<CANDIDATE_COUNT;c++)
   {
      int rows=0;
      int rc=CountSignals(bars,ArraySize(bars),atr,rsi,
                          PIVOTS[c],MIN_DELTAS[c],ATR_MULTS[c],
                          RRS[c],RSI_HIGHS[c],CIDS[c],rows);
      if(rc<0) return;
      PrintFormat("PARITY_CANDIDATE=%d SIGNAL_ROWS=%d",CIDS[c],rows);
      totalRows+=rows;
   }

   int done=FileOpen(DoneFile,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ|FILE_SHARE_WRITE,',');
   if(done==INVALID_HANDLE)
   {
      PrintFormat("PARITY_HARNESS_FAIL done_open error=%d",GetLastError());
      return;
   }
   FileWrite(done,"status","PASS");
   FileWrite(done,"real_data_only","true");
   FileWrite(done,"synthetic_data","false");
   FileWrite(done,"candidate_count",CANDIDATE_COUNT);
   FileWrite(done,"signal_rows",totalRows);
   FileWrite(done,"first_timestamp",IsoTimestamp(bars[0].ts));
   FileWrite(done,"last_timestamp",IsoTimestamp(bars[ArraySize(bars)-1].ts));
   FileClose(done);

   PrintFormat("PARITY_HARNESS_OK candidates=%d signal_rows=%d",CANDIDATE_COUNT,totalRows);
}
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handoff", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()

    handoff = json.loads(args.handoff.read_text(encoding="utf-8"))
    assert handoff["schema_version"] == SCHEMA
    policy = handoff["handoff_policy"]
    assert policy["parameters_are_frozen"] is True
    assert policy["oos_optimization_disabled"] is True

    ids = [2,6,10,12,14,22,26,28,30,32,34,38,42,46,48]
    cands = {int(c["candidate_id"]): c for c in handoff["candidates"]}
    assert all(cid in cands for cid in ids)

    def nums(key: str, fmt: str) -> str:
        return ",".join(fmt.format(cands[cid]["params"][key]) for cid in ids)

    src = (
        TEMPLATE
        .replace("__CIDS__", ",".join(str(x) for x in ids))
        .replace("__PIVOTS__", ",".join(str(cands[x]["params"]["pivot"]) for x in ids))
        .replace("__DELTAS__", nums("min_delta", "{:.10f}"))
        .replace("__ATR_MULTS__", nums("atr_mult", "{:.3f}"))
        .replace("__RRS__", nums("rr", "{:.3f}"))
        .replace("__RSI_HIGHS__", nums("rsi_high", "{:.1f}"))
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(src, encoding="utf-8")
    print(json.dumps({
        "generated": args.output.name,
        "candidate_count": len(ids),
        "real_data_only": True,
        "synthetic_data": False
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
