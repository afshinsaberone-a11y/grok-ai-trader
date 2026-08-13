from datetime import date, datetime
from pathlib import Path
import json
import pandas as pd
from .conflict_audit import audit_timestamp_conflicts
from .histdata_current import fetch_month_archive, month_starts, _extract_year_csv, _parse_csv

def run(start: str, end: str, out: str = "data/real") -> int:
    s=date.fromisoformat(start); e=date.fromisoformat(end); frames=[]
    for y,m in month_starts(s,e):
        x=fetch_month_archive(y,m,Path(out)/"raw"/"histdata"); _,p=_extract_year_csv(x.archive); f=_parse_csv(p); f["_source_month"]=f"{y:04d}-{m:02d}"; frames.append(f)
    df=pd.concat(frames,ignore_index=True); df=df[(df.timestamp>=pd.Timestamp(s,tz="UTC"))&(df.timestamp<pd.Timestamp(e,tz="UTC"))]
    rows,summary=audit_timestamp_conflicts(df); d=Path(out)/"conflicts"; d.mkdir(parents=True,exist_ok=True); (d/"oos_conflicts.json").write_text(json.dumps({"summary":summary.to_dict(),"conflicts":rows.to_dict(orient="records")},default=str,indent=2))
    print(summary.to_dict()); return summary.conflicting_timestamps

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--start",required=True); p.add_argument("--end",required=True); a=p.parse_args(); raise SystemExit(min(run(a.start,a.end),1))
