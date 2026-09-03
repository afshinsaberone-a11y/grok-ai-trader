"""Execution-equivalent cost-aware discovery on REAL pre-OOS data only.

v30 aligns discovery execution with the v28 integrity baseline:
- signal observed on bar i, entry at next bar open i+1
- 0.7 pip adverse entry + 0.7 pip adverse exit (1.4 pip round trip)
- actual entry price anchors SL/TP
- SL-first on same-bar stop/target ambiguity
- opposite-signal exit at next bar open
- 30-bar maximum holding period
- one position at a time
- 2022-2024 discovery, 2025 validation, 2026 held out
- no synthetic fallback
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from research.optimization.multi_family_discovery import FAMILIES, _native, catalog, indicators, signal_family
from research.optimization.cost_aware_gate_v14 import (
    PRE_OOS_YEARS, MIN_PROFITABLE_YEARS, MIN_PF_EACH_YEAR,
    MIN_EXPECTANCY_R, MIN_TRADES_EACH_YEAR, PRE_OOS_MAX_DD_PCT,
    VALIDATION_MIN_PF, VALIDATION_MAX_DD_PCT, VALIDATION_MIN_TRADES,
    pre_oos_gate,
)

PIP_SIZE = 0.0001
DEFAULT_SPREAD_PIPS = 0.5
DEFAULT_SLIPPAGE_PIPS = 0.2
RISK_PCT = 0.005
MAX_HOLD_BARS = 30


def round_trip_cost_price(spread_pips: float, slippage_pips: float) -> float:
    if spread_pips < 0 or slippage_pips < 0:
        raise ValueError("execution costs cannot be negative")
    return 2.0 * (float(spread_pips) + float(slippage_pips)) * PIP_SIZE


def backtest_execution_equivalent(
    df: pd.DataFrame,
    family: str,
    params: dict[str, Any],
    *,
    spread_pips: float = DEFAULT_SPREAD_PIPS,
    slippage_pips: float = DEFAULT_SLIPPAGE_PIPS,
) -> dict[str, Any]:
    d = indicators(df, params)
    sig = signal_family(d, family, params)
    opens = d["Open"].to_numpy(float, copy=False)
    high = d["High"].to_numpy(float, copy=False)
    low = d["Low"].to_numpy(float, copy=False)
    close = d["Close"].to_numpy(float, copy=False)
    atr = d["atr"].to_numpy(float, copy=False)
    signals = sig.to_numpy(copy=False)
    equity = peak = 10000.0
    maxdd = 0.0
    pos = 0
    entry = stop = tp = 0.0
    entry_bar = -1
    rs: list[float] = []
    cost = round_trip_cost_price(spread_pips, slippage_pips)

    # Signal at i is tradable only from i+1 open onward.
    for j in range(1, len(d)):
        prev_signal = signals[j - 1]
        a = atr[j]
        if not np.isfinite(a) or a <= 0:
            continue

        if pos == 0:
            if prev_signal == 0:
                continue
            pos = int(prev_signal)
            entry = opens[j]
            sd = float(params["atr_stop"]) * a
            stop = entry - pos * sd
            tp = entry + pos * float(params["rr"]) * sd
            entry_bar = j
            continue

        held = j - entry_bar
        # Opposite signal is acted on at this bar's open. It is a next-bar
        # execution of the signal observed on j-1, matching entry timing.
        if (pos == 1 and prev_signal == -1) or (pos == -1 and prev_signal == 1):
            ex = opens[j]
            r = ((ex - entry) / abs(entry - stop) if pos == 1 else (entry - ex) / abs(stop - entry))
            rs.append(r - cost / abs(entry - stop))
            equity *= 1.0 + RISK_PCT * rs[-1]
            pos = 0
            peak = max(peak, equity)
            maxdd = max(maxdd, (peak - equity) / peak)
            continue

        # Stops/targets are evaluated intrabar. If both are touched, stop wins.
        if pos == 1 and (low[j] <= stop or high[j] >= tp):
            ex = stop if low[j] <= stop else tp
            rs.append((ex - entry) / abs(entry - stop) - cost / abs(entry - stop))
            equity *= 1.0 + RISK_PCT * rs[-1]
            pos = 0
        elif pos == -1 and (high[j] >= stop or low[j] <= tp):
            ex = stop if high[j] >= stop else tp
            rs.append((entry - ex) / abs(stop - entry) - cost / abs(stop - entry))
            equity *= 1.0 + RISK_PCT * rs[-1]
            pos = 0
        elif held >= MAX_HOLD_BARS:
            ex = close[j]
            r = ((ex - entry) / abs(entry - stop) if pos == 1 else (entry - ex) / abs(stop - entry))
            rs.append(r - cost / abs(entry - stop))
            equity *= 1.0 + RISK_PCT * rs[-1]
            pos = 0

        peak = max(peak, equity)
        maxdd = max(maxdd, (peak - equity) / peak)

    # Fail closed: a year-level backtest must not silently carry an open trade.
    if pos != 0:
        ex = close[-1]
        r = ((ex - entry) / abs(entry - stop) if pos == 1 else (entry - ex) / abs(stop - entry))
        rs.append(r - cost / abs(entry - stop))
        equity *= 1.0 + RISK_PCT * rs[-1]
        peak = max(peak, equity)
        maxdd = max(maxdd, (peak - equity) / peak)

    n = len(rs)
    wins = sum(x > 0 for x in rs)
    gross_profit = sum(x for x in rs if x > 0)
    gross_loss = abs(sum(x for x in rs if x <= 0))
    pf = gross_profit / gross_loss if gross_loss else ("inf" if gross_profit > 0 else 0.0)
    return {
        "trades": n,
        "win_rate": round(100.0 * wins / n, 2) if n else 0.0,
        "total_R": round(sum(rs), 2),
        "expectancy_R": round(sum(rs) / n, 4) if n else 0.0,
        "profit_factor": round(pf, 3) if pf != "inf" and np.isfinite(pf) else pf,
        "max_dd_pct": round(100.0 * maxdd, 2),
        "final_equity": round(equity, 2),
        "spread_pips": float(spread_pips),
        "slippage_pips": float(slippage_pips),
        "round_trip_cost_pips": round(2.0 * (spread_pips + slippage_pips), 4),
        "execution_model": {
            "entry": "next_bar_open",
            "exit_stop_target": "intrabar_actual_level",
            "opposite_signal_exit": "next_bar_open",
            "same_bar_ambiguity": "SL_first",
            "max_hold_bars": MAX_HOLD_BARS,
            "one_position_at_a_time": True,
        },
    }


def _pf(m: dict[str, Any]) -> float:
    return 3.0 if m["profit_factor"] == "inf" else float(m["profit_factor"])


def score_cost_aware(metrics: list[dict[str, Any]]) -> float:
    if not pre_oos_gate(metrics):
        return -999.0
    pfs = [_pf(x["metrics"]) for x in metrics]
    ex = [float(x["metrics"]["expectancy_R"]) for x in metrics]
    dd = [float(x["metrics"]["max_dd_pct"]) for x in metrics]
    avg_pf = sum(pfs) / 3.0
    total = sum(float(x["metrics"]["total_R"]) for x in metrics)
    return round(
        2.5 * min(max(min(pfs), 0), 2) / 2
        + 1.5 * min(max(avg_pf, 0), 2) / 2
        + sum(v > 0 for v in ex) / 3
        + 1.5 * np.tanh(total / 150)
        - 2.5 * min(max(max(dd), 0), 100) / 100,
        6,
    )


def _pre_oos_reasons(pre: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    by_year = {int(x["year"]): x["metrics"] for x in pre}
    for y in PRE_OOS_YEARS:
        m = by_year[y]
        if int(m.get("trades", 0)) < MIN_TRADES_EACH_YEAR:
            reasons.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if _pf(m) < MIN_PF_EACH_YEAR:
            reasons.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if float(m.get("max_dd_pct", 100)) > PRE_OOS_MAX_DD_PCT:
            reasons.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
        if float(m.get("expectancy_R", 0)) <= MIN_EXPECTANCY_R:
            reasons.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
    profitable = sum(float(by_year[y].get("expectancy_R", 0)) > MIN_EXPECTANCY_R for y in PRE_OOS_YEARS)
    if profitable < MIN_PROFITABLE_YEARS:
        reasons.append(f"profitable_years<{MIN_PROFITABLE_YEARS}")
    return reasons


def _validation_reasons(m: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if _pf(m) < VALIDATION_MIN_PF:
        reasons.append(f"validation_pf<{VALIDATION_MIN_PF}")
    if float(m.get("max_dd_pct", 100)) > VALIDATION_MAX_DD_PCT:
        reasons.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
    if int(m.get("trades", 0)) < VALIDATION_MIN_TRADES:
        reasons.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
    return reasons


def discover_family(df: pd.DataFrame, family: str, *, spread_pips: float, slippage_pips: float) -> dict[str, Any]:
    years = {y: df[(df.index >= f"{y}-01-01") & (df.index < f"{y+1}-01-01")] for y in (2022, 2023, 2024, 2025)}
    results = []
    reject_counts: Counter[str] = Counter()
    validation_reject_counts: Counter[str] = Counter()
    examples = []
    for j, params in enumerate(catalog()[family]):
        pre = [{"year": y, "metrics": backtest_execution_equivalent(years[y], family, params, spread_pips=spread_pips, slippage_pips=slippage_pips)} for y in PRE_OOS_YEARS]
        reasons = _pre_oos_reasons(pre)
        for reason in reasons:
            reject_counts[reason] += 1
        results.append({
            "family": family,
            "candidate": j + 1,
            "params": params,
            "cost_aware_robustness_score": score_cost_aware(pre),
            "pre_oos_gate": {"pass": not reasons, "years": list(PRE_OOS_YEARS), "min_trades_each_year": MIN_TRADES_EACH_YEAR, "min_pf_each_year": MIN_PF_EACH_YEAR, "min_profitable_years": MIN_PROFITABLE_YEARS, "min_expectancy_R": MIN_EXPECTANCY_R, "max_dd_pct": PRE_OOS_MAX_DD_PCT},
            "pre_oos_cost_aware": pre,
        })
        if reasons and len(examples) < 20:
            examples.append({"candidate": j + 1, "reasons": reasons})

    results.sort(key=lambda x: (-x["cost_aware_robustness_score"], x["candidate"]))
    finalists = [x for x in results if x["pre_oos_gate"]["pass"]][:50]
    validated = []
    for x in finalists:
        vm = backtest_execution_equivalent(years[2025], family, x["params"], spread_pips=spread_pips, slippage_pips=slippage_pips)
        vr = _validation_reasons(vm)
        for reason in vr:
            validation_reject_counts[reason] += 1
        validated.append({**x, "validation_2025_cost_aware": vm, "validation_qualifies": not vr})
    qualified = [x for x in validated if x["validation_qualifies"]]
    qualified.sort(key=lambda x: (-x["cost_aware_robustness_score"], x["candidate"]))
    return {
        "family": family,
        "candidate_total": len(results),
        "cost_profile": {"spread_pips": spread_pips, "slippage_pips": slippage_pips, "round_trip_cost_pips": 2 * (spread_pips + slippage_pips)},
        "qualified_count": len(qualified),
        "champion": qualified[0] if qualified else None,
        "top_50": validated,
        "reject_diagnostics": {
            "pre_oos_rejections": dict(sorted(reject_counts.items(), key=lambda x: (-x[1], x[0]))),
            "pre_oos_rejected_candidates": sum(1 for x in results if not x["pre_oos_gate"]["pass"]),
            "pre_oos_passed_candidates": len(finalists),
            "validation_rejections": dict(sorted(validation_reject_counts.items(), key=lambda x: (-x[1], x[0]))),
            "validation_rejected_candidates": sum(1 for x in validated if not x["validation_qualifies"]),
            "validation_qualified_candidates": len(qualified),
            "examples": examples,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--family", choices=FAMILIES, required=True)
    ap.add_argument("--output", default="artifacts/cost_aware_family_v30.json")
    ap.add_argument("--spread-pips", type=float, default=DEFAULT_SPREAD_PIPS)
    ap.add_argument("--slippage-pips", type=float, default=DEFAULT_SLIPPAGE_PIPS)
    args = ap.parse_args()
    if args.spread_pips < 0 or args.slippage_pips < 0:
        raise SystemExit("execution costs cannot be negative")
    df = pd.read_csv(args.data)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"INVALID_REAL_DATA_SCHEMA: missing={sorted(missing)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}).set_index("timestamp").sort_index()
    if df.empty:
        raise SystemExit("REAL_DATA_REQUIRED: empty dataset")
    if df.index.year.max() >= 2026:
        raise SystemExit("OOS_POLICY_VIOLATION: discovery input contains 2026+")
    result = discover_family(df, args.family, spread_pips=args.spread_pips, slippage_pips=args.slippage_pips)
    report = {
        "schema_version": "forexai.cost_aware_discovery.v30",
        "result": result,
        "execution_model": {"entry": "next_bar_open", "exit_stop_target": "intrabar_actual_level", "opposite_signal_exit": "next_bar_open", "same_bar_ambiguity": "SL_first", "max_hold_bars": MAX_HOLD_BARS, "one_position_at_a_time": True},
        "oos_policy": {"loaded": False, "start": "2026-01-01", "status": "HELD_OUT"},
        "real_data_required": True,
        "synthetic_fallback": False,
        "gate_policy": {"pre_oos_years": list(PRE_OOS_YEARS), "pre_oos_min_profitable_years": MIN_PROFITABLE_YEARS, "pre_oos_min_pf_each_year": MIN_PF_EACH_YEAR, "pre_oos_min_expectancy_R": MIN_EXPECTANCY_R, "pre_oos_min_trades_each_year": MIN_TRADES_EACH_YEAR, "pre_oos_max_dd_pct": PRE_OOS_MAX_DD_PCT, "validation_min_pf": VALIDATION_MIN_PF, "validation_max_dd_pct": VALIDATION_MAX_DD_PCT, "validation_min_trades": VALIDATION_MIN_TRADES, "fail_closed": True},
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_native(report), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(_native({"family": args.family, "qualified_count": result["qualified_count"], "champion": result["champion"], "execution_model": report["execution_model"], "cost_profile": result["cost_profile"], "reject_diagnostics": result["reject_diagnostics"]}), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
