"""Cost-aware multi-family discovery v15.1.

Diagnostics-first successor to v15. Uses the v28.1/v29.1 execution model:
next-bar-open entry, adverse entry/exit costs, SL-first ambiguity,
30-bar expiry, opposite-signal exit, one position at a time.
2022-2024 are discovery years, 2025 validation, 2026 held out.

Unlike v15, rejected candidates retain real metrics and transparent
ranking diagnostics, so a failed strict gate is still scientifically
inspectable without promoting a candidate.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.multi_family_discovery import FAMILIES, _native, catalog, indicators, signal_family
from research.optimization.cost_aware_gate_v14 import (
    PRE_OOS_YEARS,
    MIN_PROFITABLE_YEARS,
    MIN_PF_EACH_YEAR,
    MIN_EXPECTANCY_R,
    MIN_TRADES_EACH_YEAR,
    PRE_OOS_MAX_DD_PCT,
    VALIDATION_MIN_PF,
    VALIDATION_MAX_DD_PCT,
    VALIDATION_MIN_TRADES,
    pre_oos_gate,
)

PIP_SIZE = 0.0001
RISK_PCT = 0.005
MAX_HOLD_BARS = 30
DIAGNOSTIC_TOP_N = 20


def _cost_price(spread_pips: float, slippage_pips: float) -> float:
    if spread_pips < 0 or slippage_pips < 0:
        raise ValueError("execution costs cannot be negative")
    return (float(spread_pips) + float(slippage_pips)) * PIP_SIZE


def backtest_execution_equivalent(
    df: pd.DataFrame,
    family: str,
    params: dict[str, Any],
    *,
    spread_pips: float = 0.5,
    slippage_pips: float = 0.2,
) -> dict[str, Any]:
    """Run the v28.1 execution model and assert core accounting invariants."""
    if df.empty:
        return {
            "trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_R": 0.0,
            "expectancy_R": 0.0,
            "profit_factor": 0.0,
            "max_dd_pct": 0.0,
            "final_equity": 10000.0,
            "entries": 0,
            "exits": 0,
            "open_position_at_end": False,
            "ohlc_invariants_ok": True,
            "execution_invariants_ok": True,
        }

    required = {"Open", "High", "Low", "Close", "Volume"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    d = indicators(df, params)
    sig = signal_family(d, family, params).to_numpy(copy=False)
    op = d["Open"].to_numpy(float, copy=False)
    hi = d["High"].to_numpy(float, copy=False)
    lo = d["Low"].to_numpy(float, copy=False)
    cl = d["Close"].to_numpy(float, copy=False)
    atr = d["atr"].to_numpy(float, copy=False)

    ohlc_ok = bool(
        np.isfinite(op).all()
        and np.isfinite(hi).all()
        and np.isfinite(lo).all()
        and np.isfinite(cl).all()
        and (hi >= np.maximum(op, cl)).all()
        and (lo <= np.minimum(op, cl)).all()
        and (hi >= lo).all()
    )
    if not ohlc_ok:
        raise AssertionError("OHLC_INVARIANT_FAILED")

    adverse = _cost_price(spread_pips, slippage_pips)
    equity = peak = 10000.0
    maxdd = 0.0
    pos = 0
    entry = stop = tp = 0.0
    entry_i = -1
    rs: list[float] = []
    entries = 0
    exits = 0

    for i in range(1, len(d)):
        a = atr[i - 1]
        if pos == 0:
            s = sig[i - 1]
            if s == 0 or not np.isfinite(a) or a <= 0:
                continue
            pos = int(s)
            entry_raw = op[i]
            entry = entry_raw + (adverse if pos == 1 else -adverse)
            sd = float(params["atr_stop"]) * a
            stop = entry - pos * sd
            tp = entry + pos * float(params["rr"]) * sd
            entry_i = i
            entries += 1
            continue

        s = sig[i - 1]
        exit_price = None
        if pos == 1:
            # SL-first when both are touched in the same bar.
            if lo[i] <= stop and hi[i] >= tp:
                exit_price = stop
            elif lo[i] <= stop:
                exit_price = stop
            elif hi[i] >= tp:
                exit_price = tp
            elif s == -1:
                exit_price = cl[i] - adverse
            elif i - entry_i >= MAX_HOLD_BARS:
                exit_price = cl[i] - adverse
            if exit_price is not None:
                rs.append((exit_price - entry) / abs(entry - stop))
                pos = 0
                exits += 1
        else:
            if hi[i] >= stop and lo[i] <= tp:
                exit_price = stop
            elif hi[i] >= stop:
                exit_price = stop
            elif lo[i] <= tp:
                exit_price = tp
            elif s == 1:
                exit_price = cl[i] + adverse
            elif i - entry_i >= MAX_HOLD_BARS:
                exit_price = cl[i] + adverse
            if exit_price is not None:
                rs.append((entry - exit_price) / abs(stop - entry))
                pos = 0
                exits += 1

        if len(rs) > 0 and exits == len(rs):
            equity *= 1 + RISK_PCT * rs[-1]
            peak = max(peak, equity)
            maxdd = max(maxdd, (peak - equity) / peak)

    if pos:
        exit_price = cl[-1] - adverse if pos == 1 else cl[-1] + adverse
        rs.append(
            (exit_price - entry) / abs(entry - stop)
            if pos == 1
            else (entry - exit_price) / abs(stop - entry)
        )
        equity *= 1 + RISK_PCT * rs[-1]
        peak = max(peak, equity)
        maxdd = max(maxdd, (peak - equity) / peak)
        exits += 1
        pos = 0

    n = len(rs)
    wins = sum(x > 0 for x in rs)
    losses = sum(x <= 0 for x in rs)
    gp = sum(x for x in rs if x > 0)
    gl = abs(sum(x for x in rs if x <= 0))
    pf = gp / gl if gl else ("inf" if gp > 0 else 0.0)

    if entries != exits or pos != 0:
        raise AssertionError(f"EXECUTION_ACCOUNTING_FAILED: entries={entries} exits={exits} pos={pos}")

    return {
        "trades": n,
        "wins": wins,
        "losses": losses,
        "win_rate": round(100 * wins / n, 2) if n else 0.0,
        "total_R": round(float(sum(rs)), 2),
        "expectancy_R": round(float(sum(rs)) / n, 4) if n else 0.0,
        "profit_factor": round(float(pf), 3) if pf != "inf" and np.isfinite(pf) else pf,
        "max_dd_pct": round(100 * maxdd, 2),
        "final_equity": round(equity, 2),
        "spread_pips": float(spread_pips),
        "slippage_pips": float(slippage_pips),
        "round_trip_cost_pips": round(2 * (spread_pips + slippage_pips), 4),
        "execution_model": "v28.1_next_bar_open",
        "entries": entries,
        "exits": exits,
        "open_position_at_end": bool(pos != 0),
        "ohlc_invariants_ok": ohlc_ok,
        "execution_invariants_ok": bool(entries == exits and pos == 0),
    }


def _pf(m: dict[str, Any]) -> float:
    return 3.0 if m.get("profit_factor") == "inf" else float(m.get("profit_factor", 0.0))


def _pre_reasons(pre: list[dict[str, Any]]) -> list[str]:
    by = {int(x["year"]): x["metrics"] for x in pre}
    reasons: list[str] = []
    for y in PRE_OOS_YEARS:
        m = by[y]
        if int(m.get("trades", 0)) < MIN_TRADES_EACH_YEAR:
            reasons.append(f"trades<{MIN_TRADES_EACH_YEAR}:{y}")
        if _pf(m) < MIN_PF_EACH_YEAR:
            reasons.append(f"pf<{MIN_PF_EACH_YEAR}:{y}")
        if float(m.get("max_dd_pct", 100)) > PRE_OOS_MAX_DD_PCT:
            reasons.append(f"dd>{PRE_OOS_MAX_DD_PCT}:{y}")
        if float(m.get("expectancy_R", 0)) <= MIN_EXPECTANCY_R:
            reasons.append(f"expectancy<={MIN_EXPECTANCY_R}:{y}")
    if sum(float(by[y].get("expectancy_R", 0)) > MIN_EXPECTANCY_R for y in PRE_OOS_YEARS) < MIN_PROFITABLE_YEARS:
        reasons.append(f"profitable_years<{MIN_PROFITABLE_YEARS}")
    return reasons


def _diagnostic_score(pre: list[dict[str, Any]]) -> float:
    """Rank rejected candidates for inspection only; never used as a promotion gate."""
    ms = [x["metrics"] for x in pre]
    pfs = [_pf(m) for m in ms]
    exps = [float(m.get("expectancy_R", 0.0)) for m in ms]
    total_r = sum(float(m.get("total_R", 0.0)) for m in ms)
    max_dd = max(float(m.get("max_dd_pct", 100.0)) for m in ms)
    profitable_years = sum(e > MIN_EXPECTANCY_R for e in exps)
    trade_coverage = min(1.0, min(int(m.get("trades", 0)) for m in ms) / max(1, MIN_TRADES_EACH_YEAR))
    # Transparent, bounded diagnostic only. Strict gate remains authoritative.
    return round(
        2.0 * min(max(min(pfs), 0.0), 2.0) / 2.0
        + 1.5 * min(max(sum(pfs) / 3.0, 0.0), 2.0) / 2.0
        + 1.0 * min(profitable_years, 3) / 3.0
        + 0.5 * trade_coverage
        + 1.5 * np.tanh(total_r / 150.0)
        - 2.0 * min(max(max_dd, 0.0), 100.0) / 100.0,
        6,
    )


def _val_reasons(m: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if _pf(m) < VALIDATION_MIN_PF:
        reasons.append(f"validation_pf<{VALIDATION_MIN_PF}")
    if float(m.get("max_dd_pct", 100)) > VALIDATION_MAX_DD_PCT:
        reasons.append(f"validation_dd>{VALIDATION_MAX_DD_PCT}")
    if int(m.get("trades", 0)) < VALIDATION_MIN_TRADES:
        reasons.append(f"validation_trades<{VALIDATION_MIN_TRADES}")
    return reasons


def discover(df: pd.DataFrame, family: str, spread_pips: float, slippage_pips: float) -> dict[str, Any]:
    years = {y: df[(df.index >= f"{y}-01-01") & (df.index < f"{y + 1}-01-01")] for y in (2022, 2023, 2024, 2025)}
    results: list[dict[str, Any]] = []
    rejects = Counter()

    for j, params in enumerate(catalog()[family], 1):
        pre = [
            {
                "year": y,
                "metrics": backtest_execution_equivalent(
                    years[y], family, params, spread_pips=spread_pips, slippage_pips=slippage_pips
                ),
            }
            for y in PRE_OOS_YEARS
        ]
        reasons = _pre_reasons(pre)
        for r in reasons:
            rejects[r] += 1
        results.append(
            {
                "family": family,
                "candidate": j,
                "params": params,
                "diagnostic_score": _diagnostic_score(pre),
                "pre_oos_gate": {
                    "pass": not reasons,
                    "years": list(PRE_OOS_YEARS),
                    "fail_closed": True,
                },
                "pre_oos_cost_aware": pre,
                "pre_oos_rejection_reasons": reasons,
            }
        )

    # Diagnostic ranking is never a substitute for the strict gate.
    results.sort(key=lambda x: (-x["diagnostic_score"], x["candidate"]))
    diagnostic_top = results[:DIAGNOSTIC_TOP_N]
    finalists = [x for x in results if x["pre_oos_gate"]["pass"]][:50]

    validated: list[dict[str, Any]] = []
    vreject = Counter()
    for x in finalists:
        vm = backtest_execution_equivalent(
            years[2025], family, x["params"], spread_pips=spread_pips, slippage_pips=slippage_pips
        )
        rr = _val_reasons(vm)
        for r in rr:
            vreject[r] += 1
        validated.append({**x, "validation_2025_cost_aware": vm, "validation_qualifies": not rr, "validation_rejection_reasons": rr})

    qualified = [x for x in validated if x["validation_qualifies"]]
    qualified.sort(key=lambda x: (-x["diagnostic_score"], x["candidate"]))

    return {
        "family": family,
        "candidate_total": len(results),
        "execution_model": "v28.1_next_bar_open",
        "cost_profile": {
            "spread_pips": spread_pips,
            "slippage_pips": slippage_pips,
            "round_trip_cost_pips": 2 * (spread_pips + slippage_pips),
        },
        "qualified_count": len(qualified),
        "champion": qualified[0] if qualified else None,
        "diagnostic_top_rejected_or_unqualified": diagnostic_top,
        "top_50": validated,
        "reject_diagnostics": {
            "pre_oos_rejections": dict(sorted(rejects.items(), key=lambda x: (-x[1], x[0]))),
            "pre_oos_passed_candidates": len(finalists),
            "validation_rejections": dict(sorted(vreject.items(), key=lambda x: (-x[1], x[0]))),
            "validation_qualified_candidates": len(qualified),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--family", choices=FAMILIES, required=True)
    ap.add_argument("--output", default="artifacts/cost_aware_v15_1.json")
    ap.add_argument("--spread-pips", type=float, default=0.5)
    ap.add_argument("--slippage-pips", type=float, default=0.2)
    a = ap.parse_args()

    df = pd.read_csv(a.data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = (
        df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
        .set_index("timestamp")
        .sort_index()
    )
    if df.empty:
        raise SystemExit("REAL_DATA_REQUIRED: empty dataset")

    result = discover(df, a.family, a.spread_pips, a.slippage_pips)
    report = {
        "schema_version": "forexai.cost_aware_discovery.v15.1",
        "result": result,
        "oos_policy": {"loaded": False, "start": "2026-01-01", "status": "HELD_OUT"},
        "real_data_required": True,
        "synthetic_fallback": False,
        "execution_model": {
            "next_bar_open": True,
            "adverse_entry_cost_per_side_pips": a.spread_pips + a.slippage_pips,
            "adverse_exit_cost_per_side_pips": a.spread_pips + a.slippage_pips,
            "sl_first": True,
            "max_hold_bars": MAX_HOLD_BARS,
            "opposite_signal_exit": True,
            "one_position_at_a_time": True,
            "ohlc_invariants": True,
            "entries_equal_exits": True,
            "no_open_position_at_end": True,
        },
    }
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_native(report), indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "family": a.family,
                "candidate_total": result["candidate_total"],
                "qualified_count": result["qualified_count"],
                "diagnostic_top_candidate": result["diagnostic_top_rejected_or_unqualified"][0]["candidate"] if result["diagnostic_top_rejected_or_unqualified"] else None,
                "champion": result["champion"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
