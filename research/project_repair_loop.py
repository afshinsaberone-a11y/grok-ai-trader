#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, re
from pathlib import Path
BANNED = [(r"martingale","BANNED_MARTINGALE"),(r"martin\s*gale","BANNED_MARTINGALE"),(r"\bgrid\b","BANNED_GRID"),(r"averag(?:e|ing)\s*down","BANNED_AVERAGE_DOWN"),(r"lot\s*\*=\s*2","BANNED_DOUBLE_LOT")]
REQUIRED_EA_TOKENS = ["RiskPercent","MaxDailyLossPct","MaxSpreadPoints","CoolDownBars","ADX","ATR"]
def scan_text(path: Path, text: str):
    issues=[]
    lower=text.lower()
    for pat,code in BANNED:
        if re.search(pat, lower):
            issues.append({"file":str(path),"code":code,"severity":"blocker"})
    if path.suffix.lower()==".mq5":
        for tok in REQUIRED_EA_TOKENS:
            if tok not in text:
                issues.append({"file":str(path),"code":f"MISSING_{tok}","severity":"major"})
    return issues
def iter_targets(root: Path):
    files=[]
    for rel in ("ea","strategies","research"):
        d=root/rel
        if d.exists():
            files.extend(p for p in d.rglob("*") if p.is_file() and p.suffix in {".mq5",".py",".md"})
    return files
def write_report(root, issues, iteration):
    research=root/"research"; research.mkdir(exist_ok=True)
    path=research/"EA_AUDIT_LOOP_026.md"
    blockers=[i for i in issues if i["severity"]=="blocker"]
    majors=[i for i in issues if i["severity"]=="major"]
    status="PASS" if not blockers and not majors else "FAIL"
    lines=["# EA / Contract Audit Loop 026","",f"- time: {dt.datetime.utcnow().isoformat()}Z",f"- iteration: {iteration}",f"- status: **{status}**",f"- issues: {len(issues)}","","لوپ فقط قرارداد ایمنی را بررسی می‌کند. سود زنده تضمین نمی‌شود.","","## Issues",""]
    if not issues: lines.append("هیچ ایراد قرارداد ایمنی باقی نماند.")
    else:
        for i in issues: lines.append(f"- `{i['severity']}` `{i['code']}` — {i['file']}")
    path.write_text("\n".join(lines)+"\n", encoding="utf-8")
    (research/"audit_loop_026.json").write_text(json.dumps({"status":status,"issues":issues,"iteration":iteration},indent=2),encoding="utf-8")
    return path
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",default="."); ap.add_argument("--max-iter",type=int,default=5)
    args=ap.parse_args(); root=Path(args.root).resolve(); last=[]
    for i in range(1,args.max_iter+1):
        issues=[]
        for p in iter_targets(root):
            try: text=p.read_text(encoding="utf-8",errors="ignore")
            except OSError: continue
            issues.extend(scan_text(p,text))
        write_report(root,issues,i); last=issues
        blockers=[x for x in issues if x["severity"]=="blocker"]
        majors=[x for x in issues if x["severity"]=="major"]
        if not blockers and not majors:
            print(f"PASS on iteration {i}"); return 0
        print(f"FAIL iteration {i}: {len(issues)} issues")
    print("STOPPED with residual issues"); return 1
if __name__=="__main__":
    raise SystemExit(main())
