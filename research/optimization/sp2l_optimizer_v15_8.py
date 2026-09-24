"""SP2L v15.8 research-repair optimizer.

Changes versus v15.7:
- one open position at a time; overlapping signals are skipped
- every accepted entry is resolved either by SL/TP or forced close at expiry
- explicit trade accounting for SL/TP/expiry and ambiguous bars
- real training data only; 2025-2026 holdout remains excluded
- preserves the v15.7 proxy signal generator; this is NOT an exact proprietary SP2L reproduction
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.sp2l_v15_7 import Params, signals


def bt(sig, high, low, close, expiry, spread, slippage, rr=1.5):
    """Backtest entries with single-position accounting and forced expiry exits.

    Entry remains next-bar close, matching v15.7. Exit is evaluated on each
    subsequent bar through the expiry horizon. When neither SL nor TP is hit,
    the position is forcibly closed on the last eligible bar at that close.
    If both SL and TP are touched in the same bar, SL is conservatively chosen.
    """
    idx = np.flatnonzero(sig)
    pip = 0.0001
    n = len(close)
    trades = []
    next_free_signal_bar = -1
    skipped_overlap = 0
    sl_hits = 0
    tp_hits = 0
    expiry_closes = 0
    ambiguous_bars = 0

    for i in idx:
        if i < next_free_signal_bar:
            skipped_overlap += 1
            continue
        if i + 1 >= n:
            continue

        entry = float(close[i + 1])
        risk = max(float(high[i] - low[i]), pip)
        long = int(sig[i]) > 0
        sl = entry - risk if long else entry + risk
        tp = entry + rr * risk if long else entry - rr * risk
        exit_bar = min(n - 1, i + expiry)
        hit = None
        exit_kind = None
        ambiguous = False

        for j in range(i + 1, exit_bar + 1):
            if long:
                hit_sl = low[j] <= sl
                hit_tp = high[j] >= tp
            else:
                hit_sl = high[j] >= sl
                hit_tp = low[j] <= tp

            if hit_sl and hit_tp:
                ambiguous = True
                hit = -risk
                exit_kind = "sl_ambiguous"
                break
            if hit_sl:
                hit = -risk
                exit_kind = "sl"
                break
            if hit_tp:
                hit = rr * risk
                exit_kind = "tp"
                break

        if hit is None:
            exit_price = float(close[exit_bar])
            hit = (exit_price - entry) if long else (entry - exit_price)
            exit_kind = "expiry"
            expiry_closes += 1

        cost = 2 * (spread + slippage)
        trades.append({
            "pnl_pips": hit / pip - cost,
            "exit_kind": exit_kind,
            "signal_bar": int(i),
            "exit_bar": int(exit_bar),
        })
        next_free_signal_bar = exit_bar + 1
        if exit_kind.startswith("sl"):
            sl_hits += 1
        elif exit_kind == "tp":
            tp_hits += 1
        if ambiguous:
            ambiguous_bars += 1

    if not trades:
        return {
            "signals": int(idx.size),
            "trades": 0,
            "skipped_overlap_signals": int(skipped_overlap),
            "sl_hits": 0,
            "tp_hits": 0,
            "expiry_closes": 0,
            "ambiguous_bars": 0,
            "pf": 0.0,
            "win_rate": 0.0,
            "net_pips": 0.0,
            "max_dd_pips": 0.0,
            "expectancy_pips": 0.0,
        }

    a = np.asarray([t["pnl_pips"] for t in trades], dtype=float)
    wins = a[a > 0]
    losses = -a[a < 0]
    equity = np.cumsum(a)
    drawdown = np.maximum.accumulate(equity) - equity

    return {
        "signals": int(idx.size),
        "trades": int(a.size),
        "skipped_overlap_signals": int(skipped_overlap),
        "sl_hits": int(sl_hits),
        "tp_hits": int(tp_hits),
        "expiry_closes": int(expiry_closes),
        "ambiguous_bars": int(ambiguous_bars),
        "pf": float(wins.sum() / losses.sum()) if losses.sum() else 999.0,
        "win_rate": float((a > 0).mean() * 100.0),
        "net_pips": float(a.sum()),
        "max_dd_pips": float(drawdown.max()),
        "expectancy_pips": float(a.mean()),
    }


def norm(df):
    cols = {c.lower(): c for c in df.columns}
    rename = {
        cols[k]: k.title()
        for k in ("open", "high", "low", "close")
        if k in cols
    }
    d = df.rename(columns=rename)
    ts = next(
        (c for c in d.columns if c.lower() in ("timestamp", "time", "datetime")),
        None,
    )
    if ts is None:
        raise ValueError("TIMESTAMP_REQUIRED")
    d[ts] = pd.to_datetime(d[ts], utc=True)
    d = d.set_index(ts).sort_index()
    required = {"Open", "High", "Low", "Close"}
    if not required.issubset(d.columns):
        raise ValueError(f"MISSING_OHLC: {required - set(d.columns)}")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--output", default="artifacts/sp2l-v15-8-optimization.json")
    ap.add_argument("--spread-pips", type=float, default=0.5)
    ap.add_argument("--slippage-pips", type=float, default=0.2)
    ap.add_argument("--stage-a-limit", type=int, default=576)
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--fine-limit", type=int, default=972)
    args = ap.parse_args()

    d = norm(pd.read_csv(args.data))
    d = d[d.index < pd.Timestamp("2025-01-01", tz="UTC")]
    if d.empty:
        raise RuntimeError("REAL_DATA_REQUIRED")

    H = d.High.to_numpy(float)
    L = d.Low.to_numpy(float)
    C = d.Close.to_numpy(float)

    grid = {
        "atr_period": [10, 14, 20],
        "spike_atr": [1.2, 1.5, 1.8],
        "spike_body_ratio": [0.55, 0.65],
        "pullback_min_frac": [0.2, 0.4],
        "pullback_max_frac": [0.6, 0.9],
        "max_pullback_bars": [2, 5],
        "confirmation_frac": [0.4, 0.6],
        "expiry_bars": [6, 12],
    }
    keys = list(grid)
    values = list(product(*[grid[k] for k in keys]))
    stride = max(1, int(np.ceil(len(values) / args.stage_a_limit)))
    values = values[::stride][: args.stage_a_limit]

    def evaluate(v):
        p = Params(*v)
        return {
            "params": asdict(p),
            "result": bt(
                signals(d, p).to_numpy(),
                H, L, C, p.expiry_bars,
                args.spread_pips, args.slippage_pips,
            ),
        }

    rows = [evaluate(v) for v in values]

    def rank_key(z):
        r = z["result"]
        return (
            r["pf"],
            r["expectancy_pips"],
            -r["max_dd_pips"],
            r["trades"],
        )

    rows.sort(key=rank_key, reverse=True)
    fine = []
    seen = set()

    for z in rows[: args.seeds]:
        q = z["params"]
        local = product(
            [q["atr_period"]],
            [q["spike_atr"]],
            [q["spike_body_ratio"]],
            [
                max(0.1, q["pullback_min_frac"] - 0.1),
                q["pullback_min_frac"],
                min(0.5, q["pullback_min_frac"] + 0.1),
            ],
            [
                max(0.5, q["pullback_max_frac"] - 0.1),
                q["pullback_max_frac"],
                min(0.95, q["pullback_max_frac"] + 0.1),
            ],
            [q["max_pullback_bars"]],
            [
                max(0.3, q["confirmation_frac"] - 0.1),
                q["confirmation_frac"],
                min(0.7, q["confirmation_frac"] + 0.1),
            ],
            [
                max(4, q["expiry_bars"] - 2),
                q["expiry_bars"],
                q["expiry_bars"] + 2,
            ],
        )
        for v in local:
            if v[3] >= v[4] or v in seen:
                continue
            seen.add(v)
            fine.append(evaluate(v))
            if len(fine) >= args.fine_limit:
                break
        if len(fine) >= args.fine_limit:
            break

    fine.sort(key=rank_key, reverse=True)

    report = {
        "schema_version": "forexai.sp2l_optimizer.v15.8",
        "engine_change": "single_position_forced_expiry_complete_accounting",
        "train_end_exclusive": "2025-01-01",
        "holdout_2025_2026_excluded": True,
        "real_data_required": True,
        "synthetic_fallback": False,
        "stage_a_candidates": len(rows),
        "stage_b_candidates": len(fine),
        "top10": fine[:10],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
