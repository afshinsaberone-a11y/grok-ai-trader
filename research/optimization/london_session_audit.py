"""Audit London session logic without trading evaluation.

Counts session-range rows, breakout signals, and next-bar entries using real M5 data.
Does not compute profitability, tune parameters, or use 2026.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd

LONDON=ZoneInfo("Europe/London")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    d=pd.read_csv(args.data)
    d["timestamp"]=pd.to_datetime(d["timestamp"],utc=True)
    d=d.set_index("timestamp").sort_index()
    local=d.index.tz_convert(LONDON)
    d["local_date"]=local.date
    d["local_minute"]=local.hour*60+local.minute
    rows=[]
    for day,g in d.groupby("local_date",sort=True):
        for end_hour in (8,9):
            end=end_hour*60
            for minutes in (30,60,90):
                start=end-minutes
                ref=g[(g["local_minute"]>=start)&(g["local_minute"]<end)]
                at=g[g["local_minute"]==end]
                if len(ref)>0 and len(at)>0:
                    c=float(at["close"].iloc[0])
                    hi=float(ref["high"].max()); lo=float(ref["low"].min())
                    rows.append({
                      "local_date":str(day),"entry_hour":end_hour,"range_minutes":minutes,
                      "range_rows":len(ref),"entry_rows":len(at),
                      "range_high":hi,"range_low":lo,"close_at_end":c,
                      "breakout_up":c>hi,"breakout_down":c<lo,
                    })
    out=pd.DataFrame(rows)
    summary={
      "schema":"forexai.london_session_audit.v1",
      "rows_analyzed":len(d),
      "timezone":"Europe/London",
      "date_min":str(d["local_date"].min()),
      "date_max":str(d["local_date"].max()),
      "session_configurations":len(out),
      "config_signal_counts":{
        f"{h}:{m}":{
          "days_with_range_and_entry":int(((out.entry_hour==h)&(out.range_minutes==m)).sum()),
          "up_breakouts":int(out[(out.entry_hour==h)&(out.range_minutes==m)]["breakout_up"].sum()),
          "down_breakouts":int(out[(out.entry_hour==h)&(out.range_minutes==m)]["breakout_down"].sum())
        } for h in (8,9) for m in (30,60,90)
      },
      "policy":{"real_data_only":True,"oos_2026_used":False,"profitability_evaluated":False}
    }
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
