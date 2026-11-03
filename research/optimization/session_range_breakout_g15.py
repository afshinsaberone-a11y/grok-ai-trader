"""G15 fail-closed Session Range Breakout discovery on real EURUSD M5.

IS (2022-2024) alone ranks candidates. Validation 2025 is pass/fail only
for the locked IS-qualified finalist set. 2026+ data is rejected at input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.cost_aware_discovery_v15_2 import _signals, catalog
from research.optimization.multi_family_discovery import indicators
from research.real_data.manifest import sha256_file

SCHEMA = "forexai.g15.session_range_breakout.v1"
FAMILY = "session_range_breakout"
YEARS = (2022, 2023, 2024)
VALIDATION_YEAR = 2025
INITIAL_EQUITY = 10_000.0
RISK_PCT = 0.005
MAX_HOLD_BARS = 30
MAX_FINALISTS = 50
PIP_SIZE = 0.0001

BASE_SPREAD = 0.5
BASE_SLIPPAGE = 0.2
MODERATE_SPREAD = 0.75
MODERATE_SLIPPAGE = 0.30
SEVERE_SPREAD = 1.0
SEVERE_SLIPPAGE = 0.50

IS_MIN_TRADES = 100
IS_MIN_PF = 1.05
IS_MAX_DD = 35.0
VALIDATION_MIN_TRADES = 100
VALIDATION_MIN_PF = 1.10
VALIDATION_MAX_DD = 35.0
STRESS_MIN_TRADES = 100
STRESS_MIN_PF = 1.0
STRESS_MAX_DD = 35.0


def _pf(metrics: dict[str, Any]) -> float:
    value = metrics.get("profit_factor", 0.0)
    return 3.0 if value == "inf" else float(value)


def _close_trade(raw_exit, pos, entry, risk_distance, equity, peak, max_dd, trades_r, adverse):
    exit_price = float(raw_exit) - pos * adverse
    trade_r = pos * (exit_price - entry) / risk_distance
    factor = 1.0 + RISK_PCT * trade_r
    if not np.isfinite(trade_r) or not np.isfinite(factor) or factor <= 0.0:
        raise RuntimeError("G15_EXECUTION_BANKRUPTCY_OR_NONFINITE_TRADE")
    equity *= factor
    trades_r.append(float(trade_r))
    peak = max(peak, equity)
    max_dd = max(max_dd, (peak - equity) / peak if peak > 0 else 1.0)
    return equity, peak, max_dd


def backtest_session_range(df, params, *, spread_pips=BASE_SPREAD, slippage_pips=BASE_SLIPPAGE):
    if spread_pips < 0 or slippage_pips < 0:
        raise ValueError("G15_NEGATIVE_EXECUTION_COST")
    if df.empty:
        return {
            "trades": 0, "win_rate": 0.0, "total_R": 0.0,
            "expectancy_R": 0.0, "profit_factor": 0.0,
            "max_dd_pct": 0.0, "final_equity": INITIAL_EQUITY,
            "net_return_pct": 0.0, "entries": 0, "exits": 0,
            "open_position_end": False,
        }
    required = {"Open", "High", "Low", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"G15_REQUIRED_COLUMNS_MISSING:{sorted(missing)}")
    if df.index.has_duplicates or not df.index.is_monotonic_increasing:
        raise ValueError("G15_BAD_CHRONOLOGICAL_INDEX")
    if not (
        (df["High"] >= df[["Open", "Close"]].max(axis=1))
        & (df["Low"] <= df[["Open", "Close"]].min(axis=1))
        & (df["High"] >= df["Low"])
    ).all():
        raise ValueError("G15_OHLC_INVARIANT_FAIL")

    d = indicators(df, params)
    signals = _signals(d, FAMILY, params)
    opens = d["Open"].to_numpy(dtype=float)
    highs = d["High"].to_numpy(dtype=float)
    lows = d["Low"].to_numpy(dtype=float)
    closes = d["Close"].to_numpy(dtype=float)
    atr = d["atr"].to_numpy(dtype=float)
    adverse = (float(spread_pips) + float(slippage_pips)) * PIP_SIZE

    equity = peak = INITIAL_EQUITY
    max_dd = 0.0
    pos = 0
    entry = stop = target = 0.0
    entry_index = -1
    trades_r = []
    entries = exits = 0
    same_bar_stop_first = opposite_open_exits = expiry_open_exits = 0

    for i in range(1, len(d)):
        signal = int(signals[i - 1])
        opened_now = False

        # Opposite signal and expiry are known before this bar opens.
        if pos != 0:
            if i - entry_index >= MAX_HOLD_BARS:
                equity, peak, max_dd = _close_trade(
                    opens[i], pos, entry, abs(entry - stop),
                    equity, peak, max_dd, trades_r, adverse,
                )
                pos = 0
                exits += 1
                expiry_open_exits += 1
                continue
            if signal == -pos:
                equity, peak, max_dd = _close_trade(
                    opens[i], pos, entry, abs(entry - stop),
                    equity, peak, max_dd, trades_r, adverse,
                )
                pos = 0
                exits += 1
                opposite_open_exits += 1
                continue

        if pos == 0:
            if signal == 0 or not np.isfinite(atr[i - 1]) or atr[i - 1] <= 0:
                continue
            pos = signal
            entry = opens[i] + pos * adverse
            stop_distance = float(params["atr_stop"]) * float(atr[i - 1])
            if not np.isfinite(stop_distance) or stop_distance <= 0:
                pos = 0
                continue
            stop = entry - pos * stop_distance
            target = entry + pos * float(params["rr"]) * stop_distance
            entry_index = i
            entries += 1
            opened_now = True

        # Inspect entry-bar intraday range. Ambiguous stop/target is SL first.
        hit_stop = (lows[i] <= stop) if pos == 1 else (highs[i] >= stop)
        hit_target = (highs[i] >= target) if pos == 1 else (lows[i] <= target)
        if hit_stop or hit_target:
            if hit_stop:
                raw_exit = stop
                if hit_target:
                    same_bar_stop_first += 1
            else:
                raw_exit = target
            equity, peak, max_dd = _close_trade(
                raw_exit, pos, entry, abs(entry - stop),
                equity, peak, max_dd, trades_r, adverse,
            )
            pos = 0
            exits += 1
            continue
        if opened_now:
            continue

    if pos != 0:
        equity, peak, max_dd = _close_trade(
            closes[-1], pos, entry, abs(entry - stop),
            equity, peak, max_dd, trades_r, adverse,
        )
        pos = 0
        exits += 1

    if entries != exits or pos != 0:
        raise RuntimeError(f"G15_EXECUTION_INTEGRITY_FAIL:{entries}:{exits}:{pos}")
    expected = INITIAL_EQUITY
    for value in trades_r:
        expected *= 1.0 + RISK_PCT * value
    if not np.isclose(equity, expected, rtol=1e-12, atol=1e-8):
        raise RuntimeError(f"G15_EQUITY_RECONCILIATION_FAIL:{equity}:{expected}")

    values = np.asarray(trades_r, dtype=float)
    winners = values[values > 0]
    losers = values[values <= 0]
    gross_loss = abs(float(losers.sum()))
    pf = float(winners.sum()) / gross_loss if gross_loss > 0 else ("inf" if winners.size else 0.0)
    total_r = float(values.sum())
    count = int(values.size)
    return {
        "trades": count,
        "win_rate": round(float((values > 0).mean() * 100), 3) if count else 0.0,
        "total_R": round(total_r, 6),
        "expectancy_R": round(total_r / count, 6) if count else 0.0,
        "profit_factor": round(float(pf), 6) if pf != "inf" and np.isfinite(pf) else pf,
        "max_dd_pct": round(float(max_dd * 100), 6),
        "final_equity": round(float(equity), 2),
        "net_return_pct": round((float(equity) / INITIAL_EQUITY - 1.0) * 100.0, 6),
        "entries": entries,
        "exits": exits,
        "open_position_end": bool(pos),
        "same_bar_stop_first_count": same_bar_stop_first,
        "opposite_signal_open_exits": opposite_open_exits,
        "expiry_open_exits": expiry_open_exits,
        "spread_pips": float(spread_pips),
        "slippage_pips": float(slippage_pips),
        "round_trip_cost_pips": 2.0 * (float(spread_pips) + float(slippage_pips)),
        "execution_model": "next_bar_open_entry_sl_first_intrabar_exit",
    }


def _is_reasons(metrics_by_year):
    rejected = {}
    for year in YEARS:
        m = metrics_by_year[str(year)]
        reasons = []
        if int(m["trades"]) < IS_MIN_TRADES:
            reasons.append(f"trades<{IS_MIN_TRADES}")
        if _pf(m) < IS_MIN_PF:
            reasons.append(f"profit_factor<{IS_MIN_PF}")
        if float(m["expectancy_R"]) <= 0:
            reasons.append("expectancy_R<=0")
        if float(m["total_R"]) <= 0:
            reasons.append("total_R<=0")
        if float(m["final_equity"]) <= INITIAL_EQUITY:
            reasons.append("final_equity<=initial_equity")
        if float(m["max_dd_pct"]) > IS_MAX_DD:
            reasons.append(f"max_dd_pct>{IS_MAX_DD}")
        if reasons:
            rejected[str(year)] = reasons
    return rejected


def _validation_reasons(m):
    reasons = []
    if int(m["trades"]) < VALIDATION_MIN_TRADES:
        reasons.append(f"trades<{VALIDATION_MIN_TRADES}")
    if _pf(m) < VALIDATION_MIN_PF:
        reasons.append(f"profit_factor<{VALIDATION_MIN_PF}")
    if float(m["expectancy_R"]) <= 0:
        reasons.append("expectancy_R<=0")
    if float(m["total_R"]) <= 0:
        reasons.append("total_R<=0")
    if float(m["final_equity"]) <= INITIAL_EQUITY:
        reasons.append("final_equity<=initial_equity")
    if float(m["max_dd_pct"]) > VALIDATION_MAX_DD:
        reasons.append(f"max_dd_pct>{VALIDATION_MAX_DD}")
    return reasons


def _stress_reasons(m):
    reasons = []
    if int(m["trades"]) < STRESS_MIN_TRADES:
        reasons.append(f"trades<{STRESS_MIN_TRADES}")
    if _pf(m) < STRESS_MIN_PF:
        reasons.append(f"profit_factor<{STRESS_MIN_PF}")
    if float(m["expectancy_R"]) <= 0:
        reasons.append("expectancy_R<=0")
    if float(m["total_R"]) <= 0:
        reasons.append("total_R<=0")
    if float(m["final_equity"]) <= INITIAL_EQUITY:
        reasons.append("final_equity<=initial_equity")
    if float(m["max_dd_pct"]) > STRESS_MAX_DD:
        reasons.append(f"max_dd_pct>{STRESS_MAX_DD}")
    return reasons


def _is_score(by_year):
    import math
    pfs = [_pf(by_year[str(y)]) for y in YEARS]
    exps = [float(by_year[str(y)]["expectancy_R"]) for y in YEARS]
    total_r = sum(float(by_year[str(y)]["total_R"]) for y in YEARS)
    worst_dd = max(float(by_year[str(y)]["max_dd_pct"]) for y in YEARS)
    return round(float(
        2.0 * min(min(pfs), 2.0) / 2.0
        + min(sum(pfs) / len(pfs), 2.0) / 2.0
        + math.tanh(total_r / 150.0)
        + 0.75 * math.tanh((sum(exps) / len(exps)) * 20.0)
        - 2.0 * min(max(worst_dd, 0.0), 100.0) / 100.0
    ), 8)


def _canonical_sha256(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_verified_data(data_path, manifest_path):
    if not data_path.is_file() or data_path.stat().st_size == 0:
        raise ValueError("REAL_DATA_REQUIRED: M5 dataset missing or empty")
    if not manifest_path.is_file():
        raise ValueError("REAL_DATA_REQUIRED: M5 manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    data_sha = sha256_file(data_path)
    manifest_sha = sha256_file(manifest_path)
    if manifest.get("symbol") != "EURUSD":
        raise ValueError("G15_MANIFEST_SYMBOL_MISMATCH")
    if manifest.get("timeframe") != "M5":
        raise ValueError("G15_MANIFEST_TIMEFRAME_MISMATCH")
    if manifest.get("quality_status") != "PASS":
        raise ValueError("G15_MANIFEST_QUALITY_NOT_PASS")
    if "HistData" not in str(manifest.get("source", "")):
        raise ValueError("G15_SOURCE_NOT_VERIFIED_HISTDATA")
    if manifest.get("data_sha256") != data_sha:
        raise ValueError("G15_DATA_SHA256_MISMATCH")
    if not manifest.get("source_hash"):
        raise ValueError("G15_SOURCE_HASH_MISSING")

    raw = pd.read_csv(data_path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"G15_REQUIRED_COLUMNS_MISSING:{sorted(missing)}")
    ts = pd.to_datetime(raw["timestamp"], format="mixed", utc=True, errors="raise")
    if ts.isna().any() or ts.duplicated().any() or not ts.is_monotonic_increasing:
        raise ValueError("G15_INVALID_TIMESTAMP_SEQUENCE")
    if len(raw) != int(manifest.get("rows", -1)):
        raise ValueError("G15_MANIFEST_ROW_COUNT_MISMATCH")
    if ts.max() >= pd.Timestamp("2026-01-01T00:00:00Z"):
        raise ValueError("G15_OOS_POLICY_VIOLATION_2026_DATA_PRESENT")
    if ts.min() >= pd.Timestamp("2022-01-08T00:00:00Z"):
        raise ValueError("G15_DATA_START_TOO_LATE")
    if not ((ts.dt.minute % 5 == 0) & (ts.dt.second == 0) & (ts.dt.microsecond == 0)).all():
        raise ValueError("G15_M5_ALIGNMENT_FAIL")
    if not {2022, 2023, 2024, 2025}.issubset(set(ts.dt.year.astype(int))):
        raise ValueError("G15_REQUIRED_YEAR_MISSING")

    raw["timestamp"] = ts
    for column in ("open", "high", "low", "close", "volume"):
        raw[column] = pd.to_numeric(raw[column], errors="raise")
        if not np.isfinite(raw[column].to_numpy(dtype=float)).all():
            raise ValueError(f"G15_NONFINITE_COLUMN:{column}")
    if not (
        (raw["high"] >= raw[["open", "close"]].max(axis=1))
        & (raw["low"] <= raw[["open", "close"]].min(axis=1))
        & (raw["high"] >= raw["low"])
    ).all():
        raise ValueError("G15_RAW_OHLC_INVARIANT_FAIL")

    frame = raw.rename(columns={
        "timestamp": "Timestamp",
        "open": "Open", "high": "High", "low": "Low",
        "close": "Close", "volume": "Volume",
    }).set_index("Timestamp").sort_index()
    return frame, manifest, data_sha, manifest_sha


def run_discovery(data_path, manifest_path):
    frame, manifest, data_sha, manifest_sha = _load_verified_data(Path(data_path), Path(manifest_path))
    years = {
        year: frame.loc[
            (frame.index >= pd.Timestamp(f"{year}-01-01", tz="UTC"))
            & (frame.index < pd.Timestamp(f"{year+1}-01-01", tz="UTC"))
        ].copy()
        for year in (*YEARS, VALIDATION_YEAR)
    }
    for year, part in years.items():
        if part.empty:
            raise ValueError(f"G15_EMPTY_YEAR:{year}")

    ranked = []
    for candidate_id, candidate in enumerate(catalog()[FAMILY], start=1):
        is_metrics = {
            str(year): backtest_session_range(years[year], candidate)
            for year in YEARS
        }
        reasons = _is_reasons(is_metrics)
        ranked.append({
            "candidate_id": candidate_id,
            "candidate": candidate,
            "is_metrics": is_metrics,
            "is_gate_pass": not reasons,
            "is_rejection_reasons": reasons,
            "is_score": _is_score(is_metrics),
        })
    total_is_trades = sum(
        int(metrics["trades"])
        for row in ranked
        for metrics in row["is_metrics"].values()
    )
    if total_is_trades <= 0:
        raise RuntimeError("G15_NO_IS_TRADES: session range signal/reference or data integrity failure")

    ranked.sort(key=lambda row: (-row["is_score"], row["candidate_id"]))
    is_passed = [row for row in ranked if row["is_gate_pass"]]
    finalists = is_passed[:MAX_FINALISTS]
    evaluated = []

    for row in finalists:
        candidate = row["candidate"]
        validation = backtest_session_range(years[VALIDATION_YEAR], candidate)
        validation_reasons = _validation_reasons(validation)
        moderate = {
            str(year): backtest_session_range(
                years[year], candidate,
                spread_pips=MODERATE_SPREAD,
                slippage_pips=MODERATE_SLIPPAGE,
            )
            for year in (*YEARS, VALIDATION_YEAR)
        }
        moderate_rejections = {
            year: _stress_reasons(metrics)
            for year, metrics in moderate.items()
            if _stress_reasons(metrics)
        }
        severe_validation = backtest_session_range(
            years[VALIDATION_YEAR], candidate,
            spread_pips=SEVERE_SPREAD,
            slippage_pips=SEVERE_SLIPPAGE,
        )
        evaluated.append({
            **row,
            "validation_2025": validation,
            "validation_pass": not validation_reasons,
            "validation_rejection_reasons": validation_reasons,
            "moderate_cost_stress": {
                "spread_pips": MODERATE_SPREAD,
                "slippage_pips": MODERATE_SLIPPAGE,
                "round_trip_cost_pips": 2 * (MODERATE_SPREAD + MODERATE_SLIPPAGE),
                "metrics_by_year": moderate,
                "gate_pass": not moderate_rejections,
                "rejections_by_year": moderate_rejections,
            },
            "severe_cost_diagnostic_2025": {
                "spread_pips": SEVERE_SPREAD,
                "slippage_pips": SEVERE_SLIPPAGE,
                "round_trip_cost_pips": 2 * (SEVERE_SPREAD + SEVERE_SLIPPAGE),
                "metrics": severe_validation,
                "promotion_gate": False,
            },
        })

    qualified = [
        row for row in evaluated
        if row["validation_pass"] and row["moderate_cost_stress"]["gate_pass"]
    ]
    frozen = None
    if qualified:
        selected = qualified[0]
        frozen = {
            "schema": "forexai.g15.frozen_candidate.v1",
            "family": FAMILY,
            "symbol": "EURUSD",
            "timeframe": "M5",
            "candidate_id": selected["candidate_id"],
            "params": selected["candidate"],
            "risk_pct": RISK_PCT,
            "discovery_years": list(YEARS),
            "validation_year": VALIDATION_YEAR,
            "baseline_cost": {
                "spread_pips": BASE_SPREAD,
                "slippage_pips": BASE_SLIPPAGE,
                "round_trip_cost_pips": 2 * (BASE_SPREAD + BASE_SLIPPAGE),
            },
            "moderate_stress_cost": {
                "spread_pips": MODERATE_SPREAD,
                "slippage_pips": MODERATE_SLIPPAGE,
                "round_trip_cost_pips": 2 * (MODERATE_SPREAD + MODERATE_SLIPPAGE),
            },
            "max_hold_bars": MAX_HOLD_BARS,
            "session_timezone_assumption": "UTC",
            "data_sha256": data_sha,
            "manifest_sha256": manifest_sha,
            "oos_start": "2026-01-01",
            "oos_read_during_discovery": False,
        }
        frozen["config_sha256"] = _canonical_sha256(frozen)

    return {
        "schema_version": SCHEMA,
        "strategy": "Session Range Breakout",
        "symbol": "EURUSD",
        "research_timeframe": "M5",
        "real_data_required": True,
        "synthetic_fallback": False,
        "source_data": {
            "dataset_id": manifest.get("dataset_id"),
            "source": manifest.get("source"),
            "rows": int(manifest["rows"]),
            "start": pd.Timestamp(frame.index.min()).isoformat(),
            "end": pd.Timestamp(frame.index.max()).isoformat(),
            "data_sha256": data_sha,
            "manifest_sha256": manifest_sha,
            "quality_status": manifest["quality_status"],
        },
        "protocol": {
            "discovery_period": "2022-01-01/2025-01-01",
            "validation_period": "2025-01-01/2026-01-01",
            "oos_period": "2026-01-01 onward",
            "is_ranking_basis": "2022-2024 only",
            "validation_used_for_ranking": False,
            "validation_role": "pass/fail only after IS finalist lock",
            "max_finalists": MAX_FINALISTS,
            "session_timezone_assumption": "UTC (not broker-verified)",
        },
        "cost_policy": {
            "baseline": {
                "spread_pips": BASE_SPREAD,
                "slippage_pips": BASE_SLIPPAGE,
                "round_trip_cost_pips": 2 * (BASE_SPREAD + BASE_SLIPPAGE),
            },
            "moderate_stress": {
                "spread_pips": MODERATE_SPREAD,
                "slippage_pips": MODERATE_SLIPPAGE,
                "round_trip_cost_pips": 2 * (MODERATE_SPREAD + MODERATE_SLIPPAGE),
                "gate_required_for_freeze": True,
            },
            "severe_stress_diagnostic": {
                "spread_pips": SEVERE_SPREAD,
                "slippage_pips": SEVERE_SLIPPAGE,
                "round_trip_cost_pips": 2 * (SEVERE_SPREAD + SEVERE_SLIPPAGE),
                "gate_required_for_freeze": False,
            },
            "commission_swap_included": False,
        },
        "gate_policy": {
            "is_each_year": {
                "minimum_trades": IS_MIN_TRADES,
                "minimum_profit_factor": IS_MIN_PF,
                "expectancy_R_strictly_positive": True,
                "total_R_strictly_positive": True,
                "final_equity_above_initial": True,
                "maximum_drawdown_pct": IS_MAX_DD,
                "all_years_required": True,
            },
            "validation_2025": {
                "minimum_trades": VALIDATION_MIN_TRADES,
                "minimum_profit_factor": VALIDATION_MIN_PF,
                "expectancy_R_strictly_positive": True,
                "total_R_strictly_positive": True,
                "final_equity_above_initial": True,
                "maximum_drawdown_pct": VALIDATION_MAX_DD,
            },
            "moderate_cost_stress": {
                "years_required": [*YEARS, VALIDATION_YEAR],
                "minimum_trades": STRESS_MIN_TRADES,
                "minimum_profit_factor": STRESS_MIN_PF,
                "expectancy_R_strictly_positive": True,
                "total_R_strictly_positive": True,
                "final_equity_above_initial": True,
                "maximum_drawdown_pct": STRESS_MAX_DD,
            },
        },
        "catalog": {
            "candidate_total": len(ranked),
            "is_qualified_count": len(is_passed),
            "finalists_evaluated_on_validation": len(finalists),
            "validation_qualified_count": sum(bool(row["validation_pass"]) for row in evaluated),
            "moderate_stress_qualified_count": sum(bool(row["moderate_cost_stress"]["gate_pass"]) for row in evaluated),
            "fully_qualified_count": len(qualified),
        },
        "top_20_is_diagnostics": ranked[:20],
        "evaluated_finalists": evaluated,
        "frozen_candidate": frozen,
        "selection_frozen": frozen is not None,
        "promotion_decision": "HOLDOUT_NOT_RUN_NO_PROMOTION",
        "demo_authorized": False,
        "live_authorized": False,
        "orders_submitted": False,
        "oos_policy": {
            "loaded": False,
            "status": "HELD_OUT",
            "start": "2026-01-01",
            "oos_optimization_allowed": False,
            "oos_runner_invoked": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Fail-closed G15 session range breakout discovery")
    parser.add_argument("--data", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_discovery(args.data, args.manifest)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "candidate_total": report["catalog"]["candidate_total"],
        "is_qualified_count": report["catalog"]["is_qualified_count"],
        "finalists_evaluated_on_validation": report["catalog"]["finalists_evaluated_on_validation"],
        "fully_qualified_count": report["catalog"]["fully_qualified_count"],
        "selection_frozen": report["selection_frozen"],
        "oos_loaded": report["oos_policy"]["loaded"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
