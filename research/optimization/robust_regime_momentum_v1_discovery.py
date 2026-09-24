"""Nested walk-forward optimizer for Robust Regime-Momentum v1.

2026-01-01 onward is treated as blind OOS. Parameter selection never reads OOS.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.robust_regime_momentum_v1 import Params, backtest, load_real_m5

OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
DISCOVERY_START = pd.Timestamp("2022-01-01", tz="UTC")
DISCOVERY_END = OOS_START

GRID = [
    Params(adx_min=adx, atr_stop=stop, rr=rr, touch_atr=touch, vol_min=vmin, vol_max=vmax)
    for adx in (20.0, 22.0, 24.0, 26.0)
    for stop in (1.4, 1.6, 1.8, 2.0)
    for rr in (1.8, 2.2, 2.6, 3.0)
    for touch in (0.10, 0.20, 0.30)
    for vmin in (0.60, 0.70, 0.80)
    for vmax in (1.50, 1.80, 2.10)
]


def _pf(x: dict[str, Any]) -> float:
    return 3.0 if x["profit_factor"] == "inf" else float(x["profit_factor"])


def _score(m: dict[str, Any]) -> float:
    trades = int(m["trades"])
    pf = _pf(m)
    exp = float(m["expectancy_R"])
    dd = float(m["max_dd_pct"])
    if trades < 40:
        return -10.0
    # Prefer robust expectancy and PF while explicitly penalising drawdown.
    return (
        1.6 * min(pf, 2.0)
        + 2.0 * exp
        + 0.25 * min(math.log1p(trades), 6.0)
        - 0.06 * dd
    )


def _windows() -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    # 270d inner train -> 90d inner validation -> 90d outer test; step 90d.
    out = []
    start = DISCOVERY_START
    while True:
        inner_train_end = start + pd.Timedelta(days=270)
        inner_val_end = inner_train_end + pd.Timedelta(days=90)
        outer_test_end = inner_val_end + pd.Timedelta(days=90)
        if outer_test_end > DISCOVERY_END:
            break
        out.append((start, inner_train_end, inner_val_end, outer_test_end, outer_test_end))
        start += pd.Timedelta(days=90)
    return out


def _slice(df: pd.DataFrame, a: pd.Timestamp, b: pd.Timestamp) -> pd.DataFrame:
    return df.loc[(df.index >= a) & (df.index < b)].copy()


def _candidate_key(p: Params) -> str:
    return json.dumps(p.__dict__, sort_keys=True, separators=(",", ":"))


def _select(inner_train: pd.DataFrame, inner_val: pd.DataFrame, cost_atr: float, slip_atr: float) -> tuple[Params, list[dict[str, Any]]]:
    scored = []
    for p in GRID:
        train = backtest(inner_train, p, cost_atr=cost_atr, slippage_atr=slip_atr)
        val = backtest(inner_val, p, cost_atr=cost_atr, slippage_atr=slip_atr)
        score = _score(val) + 0.25 * _score(train)
        scored.append({"params": p.__dict__, "train": train, "validation": val, "selection_score": round(score, 6)})
    scored.sort(key=lambda x: (-x["selection_score"], x["params"]["atr_stop"], x["params"]["rr"]))
    return Params(**scored[0]["params"]), scored[:20]


def _monte_carlo(net_r: list[float], trials: int = 2000, seed: int = 20260925) -> dict[str, float]:
    if len(net_r) < 20:
        return {"trials": float(trials), "p95_max_drawdown_pct": 100.0, "p50_final_R": 0.0}
    rng = np.random.default_rng(seed)
    dd = []
    finals = []
    arr = np.asarray(net_r, dtype=float)
    for _ in range(trials):
        sample = rng.choice(arr, size=len(arr), replace=True)
        eq = np.cumprod(1.0 + 0.005 * sample)
        peak = np.maximum.accumulate(eq)
        dd.append(float(np.max(1.0 - eq / peak) * 100.0))
        finals.append(float(np.sum(sample)))
    return {
        "trials": float(trials),
        "p95_max_drawdown_pct": float(np.quantile(dd, 0.95)),
        "p50_final_R": float(np.quantile(finals, 0.50)),
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tests = [r["outer_test"] for r in rows]
    pfs = [_pf(x) for x in tests]
    ex = [float(x["expectancy_R"]) for x in tests]
    dd = [float(x["max_dd_pct"]) for x in tests]
    return {
        "window_count": len(rows),
        "positive_windows": int(sum(x > 0 for x in ex)),
        "positive_window_ratio": round(sum(x > 0 for x in ex) / len(ex), 4) if ex else 0.0,
        "median_test_pf": round(float(np.median(pfs)), 4) if pfs else 0.0,
        "median_test_expectancy_R": round(float(np.median(ex)), 5) if ex else 0.0,
        "worst_window_dd_pct": round(max(dd), 3) if dd else 100.0,
        "total_test_R": round(sum(float(x["total_R"]) for x in tests), 4),
        "total_test_trades": int(sum(int(x["trades"]) for x in tests)),
    }


def discover(df: pd.DataFrame, cost_atr: float, slip_atr: float) -> dict[str, Any]:
    pre = _slice(df, DISCOVERY_START, DISCOVERY_END)
    rows = []
    selected = []
    for i, (start, train_end, val_end, test_end, _) in enumerate(_windows(), 1):
        train = _slice(pre, start, train_end)
        val = _slice(pre, train_end, val_end)
        test = _slice(pre, val_end, test_end)
        if min(len(train), len(val), len(test)) == 0:
            continue
        p, top = _select(train, val, cost_atr, slip_atr)
        outer = backtest(test, p, cost_atr=cost_atr, slippage_atr=slip_atr)
        selected.append(p)
        rows.append(
            {
                "window": i,
                "inner_train": [str(start), str(train_end)],
                "inner_validation": [str(train_end), str(val_end)],
                "outer_test": outer,
                "selected_params": p.__dict__,
                "inner_top20": top,
            }
        )

    freq = Counter(_candidate_key(p) for p in selected)
    mode = freq.most_common(1)[0][0] if freq else _candidate_key(Params())
    final_params = Params(**json.loads(mode))

    return {
        "schema": "forexai.robust_regime_momentum.discovery.v1",
        "real_data_only": True,
        "oos_start": str(OOS_START),
        "oos_loaded": False,
        "grid_size": len(GRID),
        "nested_protocol": {"inner_train_days": 270, "inner_validation_days": 90, "outer_test_days": 90, "step_days": 90},
        "windows": rows,
        "aggregate": _aggregate(rows),
        "selected_parameter_frequency": dict(freq),
        "frozen_candidate": final_params.__dict__,
        "cost_model": {"cost_atr": cost_atr, "slippage_atr": slip_atr},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--output", default="artifacts/robust-regime-momentum-v1-discovery.json")
    ap.add_argument("--cost-atr", type=float, default=0.10)
    ap.add_argument("--slippage-atr", type=float, default=0.02)
    args = ap.parse_args()

    df = load_real_m5(args.data)
    if df.index.min() >= DISCOVERY_START:
        raise RuntimeError("REAL_DATA_REQUIRED: discovery history starts too late")
    # This discovery run is intentionally pre-OOS only.
    result = discover(df[df.index < OOS_START], args.cost_atr, args.slippage_atr)

    # Blind OOS: only evaluate after frozen parameters exist, and only when data is present.
    oos = df[df.index >= OOS_START]
    if not oos.empty:
        result["blind_oos"] = backtest(
            oos,
            Params(**result["frozen_candidate"]),
            cost_atr=args.cost_atr,
            slippage_atr=args.slippage_atr,
        )
        # Monte Carlo is applied to the blind OOS trade stream only.
        f = result["blind_oos"]
        result["blind_oos_mc"] = "trade-sequence bootstrap requires trade returns to be retained; rerun with audit artifact"
        result["oos_loaded"] = True
    else:
        result["blind_oos"] = {"status": "HELD_OUT_NOT_AVAILABLE"}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
