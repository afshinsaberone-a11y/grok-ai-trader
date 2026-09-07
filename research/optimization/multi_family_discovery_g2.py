"""ForexAI Discovery Generation 2 (G2).

Purpose:
- Search several genuinely different, transparent rule-based M5 strategy families.
- Use only real OHLC data.
- Preserve the existing execution contract and statistical gates.
- Never load or optimize on 2026 OOS.
- Record rejection attribution for every candidate.

Families:
1. session_breakout
2. momentum
3. trend_pullback
4. mean_reversion
5. volatility_expansion

This module does not select a Champion. It only creates discovery evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.cost_aware_gate_v14 import (
    MIN_EXPECTANCY_R,
    MIN_PF_EACH_YEAR,
    MIN_PROFITABLE_YEARS,
    MIN_TRADES_EACH_YEAR,
    PRE_OOS_MAX_DD_PCT,
    PRE_OOS_YEARS,
    VALIDATION_MAX_DD_PCT,
    VALIDATION_MIN_PF,
    VALIDATION_MIN_TRADES,
)
from research.optimization.execution_contract_v1 import (
    ExecutionConfig,
    apply_entry_cost,
    apply_exit_cost,
    validate_ohlc,
)

PIP = 0.0001
MAX_HOLD = 30
SPREAD = 0.5
SLIPPAGE = 0.2


def catalog() -> list[dict]:
    out: list[dict] = []
    grids = {
        "session_breakout": {
            "range_minutes": (30, 60),
            "buffer_atr": (0.05, 0.10),
            "atr_mult": (1.0, 1.5),
            "rr": (1.2, 1.5, 2.0),
        },
        "momentum": {
            "fast_ema": (8, 12),
            "slow_ema": (26, 34),
            "roc_bars": (3, 6),
            "atr_mult": (1.0, 1.5),
            "rr": (1.2, 1.5, 2.0),
        },
        "trend_pullback": {
            "fast_ema": (20, 30),
            "slow_ema": (50, 80),
            "rsi_trigger": (45, 50, 55),
            "atr_mult": (1.0, 1.5),
            "rr": (1.2, 1.5, 2.0),
        },
        "mean_reversion": {
            "z_window": (20, 40),
            "z_entry": (1.5, 2.0, 2.5),
            "atr_mult": (1.0, 1.5),
            "rr": (1.2, 1.5),
        },
        "volatility_expansion": {
            "range_window": (20, 40),
            "expansion_mult": (1.2, 1.5),
            "atr_mult": (1.0, 1.5),
            "rr": (1.2, 1.5, 2.0),
        },
    }
    for family, g in grids.items():
        keys = list(g)
        def rec(i: int, cur: dict) -> None:
            if i == len(keys):
                out.append({"family": family, **cur})
                return
            k = keys[i]
            for v in g[k]:
                rec(i + 1, {**cur, k: v})
        rec(0, {})
    return out


def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.rename(
        columns={
            "timestamp": "Timestamp",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    ).copy()
    d["Timestamp"] = pd.to_datetime(d["Timestamp"], utc=True)
    d = d.set_index("Timestamp").sort_index()
    validate_ohlc(d)

    prev = d.Close.shift(1)
    tr = pd.concat(
        [
            d.High - d.Low,
            (d.High - prev).abs(),
            (d.Low - prev).abs(),
        ],
        axis=1,
    ).max(axis=1)
    d["ATR"] = tr.rolling(14, min_periods=14).mean()
    d["EMA8"] = d.Close.ewm(span=8, adjust=False).mean()
    d["EMA12"] = d.Close.ewm(span=12, adjust=False).mean()
    d["EMA20"] = d.Close.ewm(span=20, adjust=False).mean()
    d["EMA30"] = d.Close.ewm(span=30, adjust=False).mean()
    d["EMA50"] = d.Close.ewm(span=50, adjust=False).mean()
    d["EMA80"] = d.Close.ewm(span=80, adjust=False).mean()
    delta = d.Close.diff()
    up = delta.clip(lower=0)
    dn = -delta.clip(upper=0)
    rs = up.rolling(14).mean() / dn.rolling(14).mean().replace(0, np.nan)
    d["RSI"] = 100 - 100 / (1 + rs)
    d["ROC3"] = d.Close.pct_change(3)
    d["ROC6"] = d.Close.pct_change(6)
    d["ROLL20"] = d.Close.rolling(20).mean()
    d["STD20"] = d.Close.rolling(20).std(ddof=0)
    d["ROLL40"] = d.Close.rolling(40).mean()
    d["STD40"] = d.Close.rolling(40).std(ddof=0)
    d["day"] = d.index.date
    d["hour"] = d.index.hour
    d["minute"] = d.index.minute
    d["range"] = d.High - d.Low
    d["range20"] = d["range"].rolling(20).mean()
    d["range40"] = d["range"].rolling(40).mean()
    return d


def metrics(rs: list[float]) -> dict:
    n = len(rs)
    gross_profit = sum(x for x in rs if x > 0)
    gross_loss = abs(sum(x for x in rs if x <= 0))
    pf = gross_profit / gross_loss if gross_loss else (3.0 if gross_profit > 0 else 0.0)
    equity, peak, dd = 10000.0, 10000.0, 0.0
    for r in rs:
        equity *= 1 + 0.005 * r
        peak = max(peak, equity)
        dd = max(dd, (peak - equity) / peak)
    return {
        "trades": n,
        "win_rate_pct": round(100 * sum(x > 0 for x in rs) / n, 2) if n else 0.0,
        "total_R": round(float(sum(rs)), 4),
        "expectancy_R": round(float(sum(rs)) / n, 6) if n else 0.0,
        "profit_factor": round(float(pf), 4),
        "max_dd_pct": round(100 * dd, 4),
        "final_equity": round(equity, 4),
    }


def _session_breakout_side(g: pd.DataFrame, i: int, p: dict) -> int:
    ts = g.index[i]
    if ts.hour != 8 or ts.minute != 0:
        return 0
    bars = max(1, int(p["range_minutes"]) // 5)
    if i < bars + 1:
        return 0
    ref = g.iloc[i - bars:i]
    atr = float(g.iloc[i]["ATR"])
    if not np.isfinite(atr) or atr <= 0:
        return 0
    hi = float(ref.High.max()) + float(p["buffer_atr"]) * atr
    lo = float(ref.Low.min()) - float(p["buffer_atr"]) * atr
    c = float(g.iloc[i]["Close"])
    return 1 if c > hi else -1 if c < lo else 0


def _signal(d: pd.DataFrame, i: int, p: dict) -> tuple[int, float, float]:
    c = float(d.iloc[i].Close)
    atr = float(d.iloc[i].ATR)
    if not np.isfinite(atr) or atr <= 0:
        return 0, 0.0, 0.0
    family = p["family"]
    side = 0
    rr = float(p["rr"])
    if family == "session_breakout":
        side = _session_breakout_side(d, i, p)
    elif family == "momentum":
        fast = d.iloc[i].EMA8 if p["fast_ema"] == 8 else d.iloc[i].EMA12
        slow = d.iloc[i].EMA26 if "EMA26" in d.columns else d.iloc[i].EMA30
        # Slow EMA is deterministically constructed below if needed.
        if p["slow_ema"] == 34:
            slow = d.iloc[i].EMA34
        side = 1 if fast > slow and d.iloc[i][f"ROC{p['roc_bars']}"] > 0 else -1 if fast < slow and d.iloc[i][f"ROC{p['roc_bars']}"] < 0 else 0
    elif family == "trend_pullback":
        fast = d.iloc[i].EMA20 if p["fast_ema"] == 20 else d.iloc[i].EMA30
        slow = d.iloc[i].EMA50 if p["slow_ema"] == 50 else d.iloc[i].EMA80
        rsi = float(d.iloc[i].RSI)
        prev_close = float(d.iloc[i - 1].Close)
        if fast > slow and prev_close <= fast and c > fast and rsi >= p["rsi_trigger"]:
            side = 1
        elif fast < slow and prev_close >= fast and c < fast and rsi <= 100 - p["rsi_trigger"]:
            side = -1
    elif family == "mean_reversion":
        w = int(p["z_window"])
        mean = float(d.iloc[i][f"ROLL{w}"] if f"ROLL{w}" in d.columns else d.Close.iloc[i-w+1:i+1].mean())
        std = float(d.iloc[i][f"STD{w}"] if f"STD{w}" in d.columns else d.Close.iloc[i-w+1:i+1].std(ddof=0))
        if std > 0:
            z = (c - mean) / std
            if z <= -p["z_entry"]:
                side = 1
            elif z >= p["z_entry"]:
                side = -1
    elif family == "volatility_expansion":
        w = int(p["range_window"])
        ref = float(d.iloc[i][f"range{w}"].mean()) if False else float(d.iloc[i][f"range{w}"])
        curr = float(d.iloc[i]["range"])
        if ref > 0 and curr >= p["expansion_mult"] * ref:
            side = 1 if c > float(d.iloc[i].Open) else -1

    return side, atr, rr


def backtest(d: pd.DataFrame, p: dict, cfg: ExecutionConfig) -> dict:
    rs: list[float] = []
    for _, g0 in d.groupby("day", sort=True):
        g = g0.copy()
        pos = 0
        entry = stop = target = 0.0
        entry_i = -1
        warmup = 100
        for i in range(warmup, len(g) - 1):
            if pos == 0:
                side, atr, rr = _signal(g, i, p)
                if side:
                    entry_i = i + 1
                    entry = apply_entry_cost(float(g.Open.iloc[entry_i]), side, cfg)
                    risk = float(p.get("atr_mult", 1.0)) * atr
                    stop = entry - side * risk
                    target = entry + side * rr * risk
                    if (target - entry) * side <= 0:
                        pos = 0
                        continue
                    pos = side
                    continue
            else:
                age = i - entry_i + 1
                hit_sl = float(g.Low.iloc[i]) <= stop if pos == 1 else float(g.High.iloc[i]) >= stop
                hit_tp = float(g.High.iloc[i]) >= target if pos == 1 else float(g.Low.iloc[i]) <= target
                unit = float(p.get("atr_mult", 1.0)) * float(g.ATR.iloc[entry_i - 1])
                if not np.isfinite(unit) or unit <= 0:
                    continue
                r = None
                if hit_sl:
                    r = pos * (apply_exit_cost(stop, pos, cfg) - entry) / unit
                elif hit_tp:
                    r = pos * (apply_exit_cost(target, pos, cfg) - entry) / unit
                elif age >= MAX_HOLD:
                    ex = float(g.Open.iloc[min(i + 1, len(g) - 1)])
                    r = pos * (apply_exit_cost(ex, pos, cfg) - entry) / unit
                if r is not None:
                    rs.append(float(r))
                    pos = 0
        if pos != 0:
            ex = float(g.Open.iloc[-1])
            unit = float(p.get("atr_mult", 1.0)) * float(g.ATR.iloc[max(entry_i - 1, 0)])
            if np.isfinite(unit) and unit > 0:
                rs.append(float(pos * (apply_exit_cost(ex, pos, cfg) - entry) / unit))
    return metrics(rs)


def rejection_reasons(year_metrics: list[dict]) -> list[str]:
    by_year = {int(x["year"]): x["metrics"] for x in year_metrics}
    bad: list[str] = []
    for y in PRE_OOS_YEARS:
        m = by_year[y]
        if m["trades"] < MIN_TRADES_EACH_YEAR:
            bad.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if float(m["profit_factor"]) < MIN_PF_EACH_YEAR:
            bad.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if float(m["expectancy_R"]) <= MIN_EXPECTANCY_R:
            bad.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
        if float(m["max_dd_pct"]) > PRE_OOS_MAX_DD_PCT:
            bad.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
    if sum(float(by_year[y]["expectancy_R"]) > 0 for y in PRE_OOS_YEARS) < MIN_PROFITABLE_YEARS:
        bad.append("profitable_years<3")
    return bad


def ensure_indicators(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for span in (26, 34):
        d[f"EMA{span}"] = d.Close.ewm(span=span, adjust=False).mean()
    for w in (20, 40):
        d[f"ROLL{w}"] = d.Close.rolling(w).mean()
        d[f"STD{w}"] = d.Close.rolling(w).std(ddof=0)
        d[f"range{w}"] = d["range"].rolling(w).mean()
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--timeframe", required=True, choices=("M1", "M5", "M15"))
    ap.add_argument("--spread-pips", type=float, default=SPREAD)
    ap.add_argument("--slippage-pips", type=float, default=SLIPPAGE)
    args = ap.parse_args()

    d = ensure_indicators(prepare(pd.read_csv(args.data)))
    cfg = ExecutionConfig(spread_pips=args.spread_pips, slippage_pips=args.slippage_pips)
    years = {
        y: d[(d.index >= f"{y}-01-01") & (d.index < f"{y+1}-01-01")]
        for y in (2022, 2023, 2024, 2025)
    }

    catalog_rows = []
    gate_counter = Counter()
    for cid, p in enumerate(catalog(), 1):
        pre = [{"year": y, "metrics": backtest(years[y], p, cfg)} for y in PRE_OOS_YEARS]
        reasons = rejection_reasons(pre)
        for reason in reasons:
            gate_counter[reason] += 1
        catalog_rows.append({
            "candidate_id": cid,
            "family": p["family"],
            "params": p,
            "pre_oos": pre,
            "pre_oos_pass": not reasons,
            "rejection_reasons": reasons,
        })

    ranked = sorted(
        catalog_rows,
        key=lambda x: (x["pre_oos_pass"], sum(m["metrics"]["expectancy_R"] for m in x["pre_oos"])),
        reverse=True,
    )
    pre_oos = [x for x in ranked if x["pre_oos_pass"]]
    validated = []
    for x in pre_oos:
        vm = backtest(years[2025], x["params"], cfg)
        vr = []
        if float(vm["profit_factor"]) < VALIDATION_MIN_PF:
            vr.append(f"validation_pf<{VALIDATION_MIN_PF}")
        if float(vm["max_dd_pct"]) > VALIDATION_MAX_DD_PCT:
            vr.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
        if int(vm["trades"]) < VALIDATION_MIN_TRADES:
            vr.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
        if float(vm["expectancy_R"]) <= 0 or float(vm["total_R"]) <= 0:
            vr.append("validation_nonpositive_return")
        validated.append({**x, "validation_2025": vm, "validation_pass": not vr, "validation_rejection_reasons": vr})

    payload = {
        "schema_version": "forexai.multi_family_discovery.g2",
        "research_timeframe": args.timeframe,
        "real_data_required": True,
        "synthetic_fallback": False,
        "execution_model": {
            "entry": "next_bar_open",
            "cost_pips_per_side": args.spread_pips + args.slippage_pips,
            "round_trip_cost_pips": 2 * (args.spread_pips + args.slippage_pips),
            "same_bar_resolution": "SL first (conservative)",
            "expiry_bars": MAX_HOLD,
            "overlap": "one position at a time",
            "adverse_exit_cost_applied": True,
        },
        "oos_policy": {"loaded": False, "status": "HELD_OUT", "start": "2026-01-01"},
        "catalog": {
            "candidate_total": len(catalog_rows),
            "family_counts": dict(Counter(x["family"] for x in catalog_rows)),
        },
        "result": {
            "candidate_total": len(catalog_rows),
            "pre_oos_qualified_count": len(pre_oos),
            "validation_qualified_count": sum(1 for x in validated if x["validation_pass"]),
            "validated_candidates": validated,
            "top_50_diagnostics": ranked[:50],
            "gate_rejection_counts_all_candidates": dict(gate_counter),
            "champion": None,
        },
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "candidate_total": len(catalog_rows),
        "pre_oos_qualified": len(pre_oos),
        "validation_qualified": sum(1 for x in validated if x["validation_pass"]),
        "family_counts": dict(Counter(x["family"] for x in catalog_rows)),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
