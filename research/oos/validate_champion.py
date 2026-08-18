from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CANDIDATES = {
    30: {
        "family": "rsi_mean_reversion",
        "params": {"atr": 14, "atr_stop": 1.4, "rr": 2.0, "fast": 13, "slow": 89, "trend": 200, "rsi": 14, "rsi_low": 20, "rsi_high": 80, "don": 20, "bb": 20},
    }
}


def indicators(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    d = df.copy()
    c, h, l = d.Close, d.High, d.Low
    d["atr"] = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1).rolling(p["atr"]).mean()
    d["ema_t"] = c.ewm(span=p["trend"], adjust=False).mean()
    delta = c.diff(); gain = delta.clip(lower=0).rolling(p["rsi"]).mean(); loss = (-delta.clip(upper=0)).rolling(p["rsi"]).mean()
    rs = gain / loss.replace(0, np.nan)
    d["rsi"] = 100 - (100/(1+rs))
    d["hour"] = d.index.hour
    return d


def backtest(df: pd.DataFrame, p: dict) -> dict:
    d = indicators(df, p)
    equity = 10000.0; peak = equity; max_dd = 0.0
    pos = 0; entry = stop = tp = 0.0; rs = []
    for i in range(1, len(d)):
        r = d.iloc[i]
        atr = r.atr
        if pd.isna(atr) or atr <= 0:
            continue
        # Candidate 30 frozen RSI mean-reversion logic from discovery.
        signal = 0
        if (r.rsi < p["rsi_low"]) and (r.Close > r.ema_t):
            signal = 1
        elif (r.rsi > p["rsi_high"]) and (r.Close < r.ema_t):
            signal = -1
        if pos == 0 and signal:
            pos = signal; entry = float(r.Close)
            stop = entry - pos * p["atr_stop"] * atr
            tp = entry + pos * p["rr"] * abs(entry-stop)
            continue
        if pos == 1 and (r.Low <= stop or r.High >= tp or signal == -1):
            ex = stop if r.Low <= stop else (tp if r.High >= tp else r.Close)
            rr = (ex-entry)/abs(entry-stop); rs.append(float(rr)); equity *= 1 + 0.005*rr; pos = 0
        elif pos == -1 and (r.High >= stop or r.Low <= tp or signal == 1):
            ex = stop if r.High >= stop else (tp if r.Low <= tp else r.Close)
            rr = (entry-ex)/abs(stop-entry); rs.append(float(rr)); equity *= 1 + 0.005*rr; pos = 0
        peak = max(peak, equity); max_dd = max(max_dd, (peak-equity)/peak)
    n = len(rs); wins = sum(x > 0 for x in rs); gp = sum(x for x in rs if x > 0); gl = abs(sum(x for x in rs if x <= 0))
    total = sum(rs); pf = gp/gl if gl else (float("inf") if gp > 0 else 0.0)
    return {"trades": n, "win_rate": round(100*wins/n,2) if n else 0.0, "total_R": round(total,2), "expectancy_R": round(total/n,3) if n else 0.0, "profit_factor": round(pf,2) if np.isfinite(pf) else "inf", "max_dd_pct": round(100*max_dd,2), "final_equity": round(equity,2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True)
    ap.add_argument("--candidate", required=True, type=int)
    ap.add_argument("--symbol", default="EURUSD")
    ap.add_argument("--timeframe", default="M5")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--optimization", default="off")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    if args.optimization.lower() != "off":
        raise SystemExit("FROZEN_OOS_REQUIRED: optimization must be off")
    if args.family != "rsi_mean_reversion" or args.candidate != 30:
        raise SystemExit("FROZEN_OOS_REQUIRED: only frozen RSI mean-reversion Candidate 30 is supported")
    path = Path(args.data)
    if not path.exists():
        raise SystemExit(f"REAL_DATA_REQUIRED: missing OOS dataset: {path}")
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    df = df[(df.timestamp >= pd.Timestamp(args.start, tz="UTC")) & (df.timestamp < pd.Timestamp(args.end, tz="UTC"))].copy()
    if df.empty:
        raise SystemExit("REAL_DATA_REQUIRED: OOS dataset is empty")
    data = df.rename(columns={"open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"}).set_index("timestamp")
    metrics = backtest(data, CANDIDATES[30]["params"])
    report = {"schema_version":"forexai.frozen_oos.v1","candidate":30,"family":"rsi_mean_reversion","symbol":args.symbol,"timeframe":args.timeframe,"oos_start":args.start,"oos_end":args.end,"optimization":"off","dataset":str(path),"metrics":metrics,"status":"OOS_EVALUATED"}
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
