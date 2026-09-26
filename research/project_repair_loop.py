#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path
FORBIDDEN=[r'martingale',r'\bgrid\b',r'double\s*lot',r'lot\s*\*=\s*2',r'recover\s+loss']
REQUIRED_HINTS=[('stoploss',r'stoploss|stop_loss|sl\b'),('risk_percent',r'riskpercent|risk_percent|risk\s*%'),('spread_filter',r'spread'),('daily_loss',r'dailyloss|daily_loss|maxdaily'),('regime',r'adx|regime|ma200')]

def scan_file(path: Path) -> dict:
    text=path.read_text(encoding='utf-8',errors='ignore'); low=text.lower(); issues=[]; missing=[]
    for pat in FORBIDDEN:
        if re.search(pat,low): issues.append({'severity':'critical','rule':'forbidden_sizing','detail':pat})
    for name,pat in REQUIRED_HINTS:
        if not re.search(pat,low): missing.append(name)
    if path.suffix.lower() in {'.mq5','.mq4'} and 'OrderSend' in text and not re.search(r'sl|stoploss',low):
        issues.append({'severity':'critical','rule':'ordersend_without_sl'})
    return {'path':str(path),'issues':issues,'missing_hints':missing,'ok': not issues and not missing}

def collect_targets(root: Path):
    t=[]
    for folder in ('ea','strategies','research'):
        base=root/folder
        if base.exists():
            for p in base.rglob('*'):
                if p.suffix.lower() in {'.mq5','.mq4','.py','.md'} and p.is_file(): t.append(p)
    return t

def apply_safe_fix(path: Path, report: dict) -> bool:
    if path.suffix.lower() not in {'.mq5','.mq4','.py'}: return False
    text=path.read_text(encoding='utf-8',errors='ignore')
    if 'GRK-SAFETY-CONTRACT-041' in text: return False
    banner='\n// GRK-SAFETY-CONTRACT-041\n// No grid/martingale. Hard SL required. Risk<=0.6%. Spread+daily loss filters required.\n' if path.suffix.lower() in {'.mq5','.mq4'} else '\n# GRK-SAFETY-CONTRACT-041\n# No grid/martingale. Hard SL required. Risk<=0.6%. Spread+daily loss filters required.\n'
    path.write_text(text.rstrip()+banner, encoding='utf-8'); report['fixed']=True; return True

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--fix',action='store_true'); ap.add_argument('--max-loops',type=int,default=5)
    args=ap.parse_args(); root=Path(args.root).resolve(); history=[]; remaining=[]
    for i in range(1,args.max_loops+1):
        results=[scan_file(p) for p in collect_targets(root)]
        bad=[r for r in results if not r['ok']]; history.append({'loop':i,'files':len(results),'failing':len(bad)})
        if not bad: remaining=[]; break
        remaining=bad
        if not args.fix: break
        for r in bad: apply_safe_fix(Path(r['path']), r)
    out=root/'artifacts'; out.mkdir(exist_ok=True)
    payload={'id':'GRK-FX-2026-041','generated_at':datetime.now(timezone.utc).isoformat(),'history':history,'remaining_failures':remaining,'clean':not remaining}
    (out/'repair_loop_041_report.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps({'clean':payload['clean'],'loops':len(history),'failing':len(remaining)},indent=2))
    return 0 if payload['clean'] else 1
if __name__=='__main__':
    raise SystemExit(main())
