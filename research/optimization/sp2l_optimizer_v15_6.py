"""Bounded, deterministic SP2L v15.6 optimizer.

Real data only; train ends 2025-01-01. The public CLI/schema is kept compatible
with the existing workflow, while the search is made computationally bounded.
No synthetic data is created.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.sp2l_v15_3 import Params


def fast_signals(df: pd.DataFrame, p: Params) -> np.ndarray:
    """Numerically equivalent SP2L state machine using NumPy arrays.

    The old implementation called ``DataFrame.iloc`` once per bar and rebuilt
    the whole signal series for every candidate. This keeps the same state
    transitions but removes the per-row pandas indexing overhead.
    """
    need = {"Open", "High", "Low", "Close"}
    if not need.issubset(df.columns):
        raise ValueError(f"missing columns: {need - set(df.columns)}")

    d = df.sort_index()
    o = d["Open"].to_numpy(dtype=np.float64)
    h = d["High"].to_numpy(dtype=np.float64)
    l = d["Low"].to_numpy(dtype=np.float64)
    c = d["Close"].to_numpy(dtype=np.float64)
    n = len(d)
    out = np.zeros(n, dtype=np.int8)
    if n <= p.atr_period:
        return out

    tr = np.maximum.reduce(
        [
            h - l,
            np.abs(h - np.r_[np.nan, c[:-1]]),
            np.abs(l - np.r_[np.nan, c[:-1]]),
        ]
    )
    atr = pd.Series(tr).rolling(p.atr_period, min_periods=p.atr_period).mean().to_numpy()

    state = 0
    direction = 0
    hi = lo = size = 0.0
    pb = age = 0
    confirm = 0.0

    for i in range(p.atr_period, n):
        a = atr[i]
        if not np.isfinite(a) or a <= 0:
            continue
        oi, hi_i, lo_i, ci = o[i], h[i], l[i], c[i]
        rng = hi_i - lo_i
        body = abs(ci - oi)
        spike = rng >= p.spike_atr * a and rng > 0 and body / rng >= p.spike_body_ratio

        if state == 0:
            if spike:
                direction = 1 if ci > oi else -1
                hi, lo, size = hi_i, lo_i, rng
                pb = age = 0
                state = 1
            continue

        age += 1
        if age > p.expiry_bars:
            state = 0
            direction = 0
            continue

        pb += 1
        if state == 1:
            if pb > p.max_pullback_bars:
                state = 0
                direction = 0
                continue
            retrace = (hi - lo_i) / size if direction == 1 else (hi_i - lo) / size
            if retrace > p.pullback_max_frac:
                state = 0
                direction = 0
                continue
            if retrace >= p.pullback_min_frac:
                confirm = (
                    lo + p.confirmation_frac * size
                    if direction == 1
                    else hi - p.confirmation_frac * size
                )
                state = 2

        if state == 2:
            if direction == 1 and ci > confirm:
                out[i] = 1
                state = 0
                direction = 0
            elif direction == -1 and ci < confirm:
                out[i] = -1
                state = 0
                direction = 0

    return out


def bt_arrays(signals: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray,
              expiry_bars: int, spread: float, slippage: float, rr: float = 1.5) -> dict:
    """Backtest one signal vector with bounded forward scanning."""
    idx = np.flatnonzero(signals)
    pip = 0.0001
    trades = []
    n = len(close)
    for i in idx:
        if i + 1 >= n:
            continue
        entry = close[i + 1]
        risk = max(high[i] - low[i], pip)
        long = signals[i] > 0
        sl = entry - risk if long else entry + risk
        tp = entry + rr * risk if long else entry - rr * risk
        hit = None
        end = min(n, i + 1 + expiry_bars)
        for j in range(i + 1, end):
            if long:
                if low[j] <= sl:
                    hit = -risk
                    break
                if high[j] >= tp:
                    hit = rr * risk
                    break
            else:
                if high[j] >= sl:
                    hit = -risk
                    break
                if low[j] <= tp:
                    hit = rr * risk
                    break
        if hit is not None:
            trades.append(hit / pip - 2 * (spread + slippage))

    if not trades:
        return {"trades": 0, "pf": 0.0, "win_rate": 0.0, "net_pips": 0.0,
                "max_dd_pips": 0.0, "expectancy_pips": 0.0}
    a = np.asarray(trades, dtype=np.float64)
    wins = a[a > 0]
    losses = -a[a < 0]
    eq = np.cumsum(a)
    dd = np.maximum.accumulate(eq) - eq
    return {
        "trades": int(a.size),
        "pf": float(wins.sum() / losses.sum()) if losses.sum() else 999.0,
        "win_rate": float((a > 0).mean() * 100),
        "net_pips": float(a.sum()),
        "max_dd_pips": float(dd.max()),
        "expectancy_pips": float(a.mean()),
    }


def norm(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    d = df.rename(columns={cols[k]: k.title() for k in ("open", "high", "low", "close") if k in cols})
    ts = next((c for c in d.columns if c.lower() in ("timestamp", "time", "datetime")), None)
    if ts is None:
        raise ValueError("TIMESTAMP_REQUIRED")
    d[ts] = pd.to_datetime(d[ts], utc=True)
    return d.set_index(ts).sort_index()


def score_key(row: dict):
    r = row["result"]
    return (r["pf"], r["expectancy_pips"], -r["max_dd_pips"], r["trades"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--output", default="artifacts/sp2l-v15-6.json")
    ap.add_argument("--spread-pips", type=float, default=0.5)
    ap.add_argument("--slippage-pips", type=float, default=0.2)
    ap.add_argument("--stage-a-limit", type=int, default=576)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--fine-limit", type=int, default=972)
    a = ap.parse_args()

    d = norm(pd.read_csv(a.data))
    d = d[d.index < pd.Timestamp("2025-01-01", tz="UTC")]
    if d.empty:
        raise RuntimeError("REAL_DATA_REQUIRED: empty training dataset")

    high = d.High.to_numpy(dtype=np.float64)
    low = d.Low.to_numpy(dtype=np.float64)
    close = d.Close.to_numpy(dtype=np.float64)

    # Stage A deliberately uses a bounded coarse grid. This is deterministic
    # and covers the main ranges without exploding the number of full backtests.
    A = {
        "atr_period": [10, 14, 20],
        "spike_atr": [1.2, 1.5, 1.8],
        "spike_body_ratio": [0.55, 0.65],
        "pullback_min_frac": [0.2, 0.4],
        "pullback_max_frac": [0.6, 0.9],
        "max_pullback_bars": [2, 5],
        "confirmation_frac": [0.4, 0.6],
        "expiry_bars": [6, 12],
    }
    keys = list(A)
    all_values = list(product(*[A[k] for k in keys]))
    if len(all_values) > a.stage_a_limit:
        # Stable deterministic subsampling; never random and never data-dependent.
        stride = int(np.ceil(len(all_values) / a.stage_a_limit))
        all_values = all_values[::stride][:a.stage_a_limit]

    rows = []
    for vals in all_values:
        p = Params(**dict(zip(keys, vals)))
        sig = fast_signals(d, p)
        rows.append({"params": asdict(p), "result": bt_arrays(
            sig, high, low, close, p.expiry_bars, a.spread_pips, a.slippage_pips
        )})

    rows.sort(key=score_key, reverse=True)
    seeds = rows[: min(a.seeds, len(rows))]

    fine = []
    seen = set()
    for z in seeds:
        q = z["params"]
        grid = product(
            [q["atr_period"]], [q["spike_atr"]], [q["spike_body_ratio"]],
            [max(0.1, q["pullback_min_frac"] - 0.1), q["pullback_min_frac"], min(0.5, q["pullback_min_frac"] + 0.1)],
            [max(0.5, q["pullback_max_frac"] - 0.1), q["pullback_max_frac"], min(0.95, q["pullback_max_frac"] + 0.1)],
            [q["max_pullback_bars"]],
            [max(0.3, q["confirmation_frac"] - 0.1), q["confirmation_frac"], min(0.7, q["confirmation_frac"] + 0.1)],
            [max(4, q["expiry_bars"] - 2), q["expiry_bars"], q["expiry_bars"] + 2],
        )
        for vals in grid:
            if vals[3] >= vals[4]:
                continue
            p = Params(*vals)
            key = tuple(asdict(p).values())
            if key in seen:
                continue
            seen.add(key)
            sig = fast_signals(d, p)
            fine.append({"params": asdict(p), "result": bt_arrays(
                sig, high, low, close, p.expiry_bars, a.spread_pips, a.slippage_pips
            )})
            if len(fine) >= a.fine_limit:
                break
        if len(fine) >= a.fine_limit:
            break

    fine.sort(key=score_key, reverse=True)
    report = {
        "schema_version": "forexai.sp2l_optimizer.v15.6",
        "train_end_exclusive": "2025-01-01",
        "holdout_2025_2026_excluded": True,
        "real_data_required": True,
        "synthetic_fallback": False,
        "search_policy": {
            "stage_a": "bounded_coarse_grid",
            "stage_a_candidates": len(rows),
            "stage_a_limit": a.stage_a_limit,
            "seed_count": len(seeds),
            "stage_b_candidates": len(fine),
            "stage_b_limit": a.fine_limit,
        },
        "stage_a_candidates": len(rows),
        "stage_b_candidates": len(fine),
        "top10": fine[:10],
    }
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
