from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CANDIDATE_10 = {
    "family": "bollinger_mean_reversion",
    "params": {"atr": 14, "atr_stop": 1.8, "rr": 1.0, "bb": 14, "bb_k": 1.5, "rsi": 14, "rsi_low": 30, "rsi_high": 70},
}


def indicators(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    d = df.copy()
    c, h, l = d.Close, d.High, d.Low
    d["atr"] = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1).rolling(p["atr"]).mean()
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(p["rsi"]).mean()
    loss = (-delta.clip(upper=0)).rolling(p["rsi"]).mean()
    rs = gain / loss.replace(0, np.nan)
    d["rsi"] = 100 - (100/(1+rs))
    d["bb_mid"] = c.rolling(p["bb"]).mean()
    d["bb_std"] = c.rolling(p["bb"]).std(ddof=0)
    d["bb_upper"] = d["bb_mid"] + p["bb_k"] * d["bb_std"]
    d["bb_lower"] = d["bb_mid"] - p["bb_k"] * d["bb_std"]
    return d


def metrics(rs: list[float]) -> dict:
    equity = 10000.0
    peak = equity
    max_dd = 0.0
    for x in rs:
        equity *= 1 + 0.005 * x
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
    n = len(rs)
    wins = sum(x > 0 for x in rs)
    gp = sum(x for x in rs if x > 0)
    gl = abs(sum(x for x in rs if x <= 0))
    pf = gp / gl if gl else (float("inf") if gp > 0 else 0.0)
    total = sum(rs)
    return {
        "trades": n,
        "win_rate": round(100 * wins / n, 2) if n else 0.0,
        "total_R": round(total, 2),
        "expectancy_R": round(total / n, 3) if n else 0.0,
        "profit_factor": round(pf, 3) if np.isfinite(pf) else "inf",
        "max_dd_pct": round(100 * max_dd, 2),
        "final_equity": round(equity, 2),
    }


def run(df: pd.DataFrame, spread_pips: float, slippage_pips: float) -> tuple[dict, list[float]]:
    p = CANDIDATE_10["params"]
    d = indicators(df, p)
    rs: list[float] = []
    pos = 0
    entry = stop = tp = 0.0
    cost_price = (spread_pips + 2 * slippage_pips) * 0.0001
    for i in range(1, len(d)):
        r = d.iloc[i]
        atr = r.atr
        if pd.isna(atr) or atr <= 0:
            continue
        signal = 0
        if pd.notna(r.bb_lower) and r.Close < r.bb_lower and r.rsi < p["rsi_low"]:
            signal = 1
        elif pd.notna(r.bb_upper) and r.Close > r.bb_upper and r.rsi > p["rsi_high"]:
            signal = -1
        if pos == 0 and signal:
            pos = signal
            # Conservative execution: adverse cost on entry.
            entry = float(r.Close) + pos * cost_price / 2
            stop = entry - pos * p["atr_stop"] * atr
            tp = entry + pos * p["rr"] * abs(entry - stop)
            continue
        if pos == 1 and (r.Low <= stop or r.High >= tp or signal == -1):
            ex = stop if r.Low <= stop else (tp if r.High >= tp else r.Close)
            ex -= cost_price / 2
            rs.append(float((ex-entry) / abs(entry-stop)))
            pos = 0
        elif pos == -1 and (r.High >= stop or r.Low <= tp or signal == 1):
            ex = stop if r.High >= stop else (tp if r.Low <= tp else r.Close)
            ex += cost_price / 2
            rs.append(float((entry-ex) / abs(stop-entry)))
            pos = 0
    return metrics(rs), rs


def bootstrap(rs: list[float], n: int = 5000, seed: int = 10) -> dict:
    if not rs:
        return {"samples": 0}
    rng = np.random.default_rng(seed)
    arr = np.asarray(rs, dtype=float)
    totals = np.empty(n)
    max_dds = np.empty(n)
    for j in range(n):
        sample = rng.choice(arr, size=len(arr), replace=True)
        eq = 1.0
        peak = 1.0
        dd = 0.0
        for x in sample:
            eq *= 1 + 0.005 * x
            peak = max(peak, eq)
            dd = max(dd, (peak-eq)/peak)
        totals[j] = sample.sum()
        max_dds[j] = dd * 100
    return {
        "samples": n,
        "seed": seed,
        "prob_total_R_negative": round(float((totals < 0).mean()), 4),
        "total_R_p05": round(float(np.quantile(totals, .05)), 2),
        "total_R_median": round(float(np.quantile(totals, .50)), 2),
        "total_R_p95": round(float(np.quantile(totals, .95)), 2),
        "max_dd_p50": round(float(np.quantile(max_dds, .50)), 2),
        "max_dd_p95": round(float(np.quantile(max_dds, .95)), 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    path = Path(args.data)
    if not path.exists():
        raise SystemExit(f"REAL_DATA_REQUIRED: missing OOS dataset: {path}")
    raw = pd.read_csv(path)
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True)
    for c in ["open", "high", "low", "close", "volume"]:
        raw[c] = pd.to_numeric(raw[c], errors="raise")
    if raw.empty or raw["timestamp"].duplicated().any():
        raise SystemExit("REAL_DATA_REQUIRED: OOS dataset invalid or duplicated")
    df = raw.rename(columns={"open":"Open", "high":"High", "low":"Low", "close":"Close", "volume":"Volume"}).set_index("timestamp")

    scenarios = [
        (0.0, 0.0), (0.5, 0.2), (1.0, 0.2), (1.5, 0.5), (2.0, 1.0),
    ]
    stress = {}
    for spread, slip in scenarios:
        key = f"spread_{spread:g}_pips_slippage_{slip:g}_pips"
        stress[key], _ = run(df, spread, slip)

    baseline_metrics, baseline_rs = run(df, 0.0, 0.0)
    subperiods = {}
    bounds = [
        ("2026_H1", "2026-01-01", "2026-07-01"),
        ("2026_Jan_Mar", "2026-01-01", "2026-04-01"),
        ("2026_Apr_Jun", "2026-04-01", "2026-07-01"),
        ("2026_Jul", "2026-07-01", "2026-08-01"),
    ]
    for name, start, end in bounds:
        part = df[(df.index >= pd.Timestamp(start, tz="UTC")) & (df.index < pd.Timestamp(end, tz="UTC"))]
        if len(part) > 100:
            subperiods[name], _ = run(part, 1.0, 0.5)

    report = {
        "schema_version": "forexai.candidate10_stress.v1",
        "candidate": 10,
        "family": "bollinger_mean_reversion",
        "symbol": "EURUSD",
        "timeframe": "M5",
        "oos_start": "2026-01-01",
        "oos_end": "2026-08-01",
        "optimization": "off",
        "real_data_only": True,
        "dataset": str(path),
        "baseline": baseline_metrics,
        "execution_cost_stress": stress,
        "subperiod_stress_spread_1pips_slippage_0.5pips": subperiods,
        "trade_order_bootstrap_baseline": bootstrap(baseline_rs),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
