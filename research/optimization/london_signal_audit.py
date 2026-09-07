"""Signal-level audit for London Breakout G3.

Counts raw breakout events and next-bar entry opportunities separately from
stop/target outcomes. Real M5 data only; no profitability evaluation.
"""
from __future__ import annotations
import argparse,json
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
                ref=g[(g.local_minute>=start)&(g.local_minute<end)]
                at=g[g.local_minute==end]
                raw_up=raw_down=0
                entry_up=entry_down=0
                for idx in at.index:
                    loc=at.loc[idx]
                    if len(ref)==0: continue
                    hi=float(ref.high.max()); lo=float(ref.low.min()); c=float(loc.close)
                    if c>hi:
                        raw_up+=1
                        pos=d.index.get_loc(idx)+1
                        if pos<len(d.index): entry_up+=1
                    if c<lo:
                        raw_down+=1
                        pos=d.index.get_loc(idx)+1
                        if pos<len(d.index): entry_down+=1
                rows.append({
                    "local_date":str(day),"entry_hour":end_hour,"range_minutes":minutes,
                    "range_rows":len(ref),"entry_rows":len(at),
                    "raw_up":raw_up,"raw_down":raw_down,
                    "next_bar_up":entry_up,"next_bar_down":entry_down,
                })
    out=pd.DataFrame(rows)
    summary={
      "schema":"forexai.london_signal_audit.v1",
      "timezone":"Europe/London",
      "source_rows":len(d),
      "configs":{},
      "policy":{"real_data_only":True,"profitability_evaluated":False,"oos_2026_used":False}
    }
    for h in (8,9):
      for m in (30,60,90):
        x=out[(out.entry_hour==h)&(out.range_minutes==m)]
        summary["configs"][f"{h}:{m}"]={
          "days":int(len(x)),
          "raw_up":int(x.raw_up.sum()),
          "raw_down":int(x.raw_down.sum()),
          "next_bar_up":int(x.next_bar_up.sum()),
          "next_bar_down":int(x.next_bar_down.sum()),
        }
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
