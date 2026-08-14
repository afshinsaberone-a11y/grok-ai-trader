"""Multi-family real-data strategy discovery.

Families are evaluated on pre-OOS data only. OOS is never loaded here.
This module provides deterministic, rule-based baselines for cross-family
comparison; it does not fabricate bars or fills.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


SEED = 20260814
RISK_PCT = 0.01
FAMILIES = ("trend_following", "momentum", "mean_reversion", "breakout", "london_breakout")


def load(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("REAL_DATA_REQUIRED: empty dataset")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for c in ("open", "high", "low", "close"):
        df[c] = pd.to_numeric(df[c], errors="raise")
    return df.sort_values("timestamp").reset_index(drop=True)


def indicators(df: pd.DataFrame) -> pd.DataFrame:
    x = df.copy()
    x["ema20"] = x.close.ewm(span=20, adjust=False).mean()
    x["ema50"] = x.close.ewm(span=50, adjust=False).mean()
    x["ema200"] = x.close.ewm(span=200, adjust=False).mean()
    x["roc20"] = x.close.pct_change(20)
    x["mean20"] = x.close.rolling(20).mean()
    x["std20"] = x.close.rolling(20).std()
    x["atr14"] = pd.concat([
        x.high - x.low,
        (x.high - x.close.shift()).abs(),
        (x.low - x.close.shift()).abs(),
    ], axis=1).max(axis=1).rolling(14).mean()
    x["hour"] = x.timestamp.dt.hour
    return x


def signals(x: pd.DataFrame, family: str) -> tuple[pd.Series, pd.Series, float, float]:
    s = pd.Series(0, index=x.index, dtype=int)
    if family == "trend_following":
        long_ = (x.ema20 > x.ema50) & (x.ema50 > x.ema200) & (x.close > x.ema20)
        short_ = (x.ema20 < x.ema50) & (x.ema50 < x.ema200) & (x.close < x.ema20)
        atr_mult, rr = 2.0, 2.0
    elif family == "momentum":
        long_ = (x.roc20 > 0.002) & (x.close > x.ema50)
        short_ = (x.roc20 < -0.002) & (x.close < x.ema50)
        atr_mult, rr = 1.5, 2.5
    elif family == "mean_reversion":
        long_ = (x.close < x.mean20 - 1.5 * x.std20) & (x.close > x.close.shift(1))
        short_ = (x.close > x.mean20 + 1.5 * x.std20) & (x.close < x.close.shift(1))
        atr_mult, rr = 1.5, 1.5
    elif family == "breakout":
        hi = x.high.shift(1).rolling(20).max()
        lo = x.low.shift(1).rolling(20).min()
        long_ = x.close > hi
        short_ = x.close < lo
        atr_mult, rr = 1.8, 2.5
    elif family == "london_breakout":
        in_window = (x.hour >= 7) & (x.hour < 10)
        prior = x[(x.hour >= 0) & (x.hour < 7)]
        range_hi = prior.groupby(prior.timestamp.dt.date).high.transform("max")
        range_lo = prior.groupby(prior.timestamp.dt.date).low.transform("min")
        # Map the overnight range back onto the full index by calendar date.
        daily = x.assign(day=x.timestamp.dt.date).groupby("day").agg(hi=("high", "max"), lo=("low", "min"))
        session = x.timestamp.dt.date.map(daily.hi).to_numpy(), x.timestamp.dt.date.map(daily.lo).to_numpy()
        hi, lo = pd.Series(session[0], index=x.index), pd.Series(session[1], index=x.index)
        long_ = in_window & (x.close > hi.shift(1))
        short_ = in_window & (x.close < lo.shift(1))
        atr_mult, rr = 1.5, 2.0
    else:
        raise ValueError(f"unknown family: {family}")
    s.loc[long_.fillna(False)] = 1
    s.loc[short_.fillna(False)] = -1
    return s, x["atr14"], atr_mult, rr


def backtest(df: pd.DataFrame, family: str) -> dict:
    x = indicators(df)
    sig, atr, atr_mult, rr = signals(x, family)
    position = 0
    entry = stop = tp = 0.0
    rs: list[float] = []
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for i in range(1, len(x)):
        a = atr.iloc[i]
        if not np.isfinite(a) or a <= 0:
            continue
        row = x.iloc[i]
        if position == 0:
            if sig.iloc[i] == 1:
                position = 1; entry = row.close; stop = entry - atr_mult * a; tp = entry + rr * (entry - stop)
            elif sig.iloc[i] == -1:
                position = -1; entry = row.close; stop = entry + atr_mult * a; tp = entry - rr * (stop - entry)
        elif position == 1 and (row.low <= stop or row.high >= tp or sig.iloc[i] == -1):
            exit_ = stop if row.low <= stop else (tp if row.high >= tp else row.close)
            r = (exit_ - entry) / (entry - stop)
            rs.append(r); equity *= 1 + r * RISK_PCT; position = 0
        elif position == -1 and (row.high >= stop or row.low <= tp or sig.iloc[i] == 1):
            exit_ = stop if row.high >= stop else (tp if row.low <= tp else row.close)
            r = (entry - exit_) / (stop - entry)
            rs.append(r); equity *= 1 + r * RISK_PCT; position = 0
        peak = max(peak, equity); max_dd = max(max_dd, (peak - equity) / peak)
    wins = sum(r > 0 for r in rs); losses = sum(r <= 0 for r in rs)
    gp = sum(r for r in rs if r > 0); gl = -sum(r for r in rs if r <= 0)
    pf = gp / gl if gl else (float("inf") if gp else 0.0)
    return {
        "family": family,
        "trades": len(rs),
        "win_rate": round(100 * wins / len(rs), 2) if rs else 0.0,
        "profit_factor": round(pf, 3) if math.isfinite(pf) else "inf",
        "total_R": round(sum(rs), 3),
        "expectancy_R": round(sum(rs) / len(rs), 4) if rs else 0.0,
        "max_dd_pct": round(max_dd * 100, 3),
        "final_equity": round(equity, 6),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--output", default="artifacts/all_strategy_discovery_v1.json")
    args = p.parse_args()
    df = load(args.data)
    parts = {
        "2022_2024": df[(df.timestamp >= "2022-01-01") & (df.timestamp < "2025-01-01")],
        "2025_validation": df[(df.timestamp >= "2025-01-01") & (df.timestamp < "2026-01-01")],
    }
    report = {
        "schema_version": "forexai.all_strategy_discovery.v1",
        "seed": SEED,
        "families": list(FAMILIES),
        "oos_policy": {"loaded": False, "start": "2026-01-01"},
        "results": {},
    }
    for segment, part in parts.items():
        if part.empty:
            raise ValueError(f"REAL_DATA_REQUIRED: empty segment {segment}")
        report["results"][segment] = sorted((backtest(part, fam) for fam in FAMILIES), key=lambda r: (-float(r["profit_factor"] if r["profit_factor"] != "inf" else 999), r["max_dd_pct"]))
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
