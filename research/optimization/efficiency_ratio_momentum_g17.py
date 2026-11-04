"""G17: independent fail-closed Efficiency-Ratio Time-Series Momentum research."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA = "forexai.g17.efficiency_ratio_momentum.v1"
YEARS = (2022, 2023, 2024)
VALIDATION_YEAR = 2025
ALL_YEARS = (*YEARS, VALIDATION_YEAR)
OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
DATA_START_MIN = pd.Timestamp("2022-01-08", tz="UTC")
INITIAL_EQUITY, RISK_PCT, PIP = 10_000.0, 0.005, 0.0001
BASE_COST, STRESS_COST, SEVERE_COST = (0.50, 0.20), (0.75, 0.30), (1.00, 0.50)
IS_TRADES, IS_PF, IS_DD = 100, 1.05, 35.0
VAL_TRADES, VAL_PF, VAL_DD = 100, 1.10, 35.0
STRESS_TRADES, STRESS_PF, STRESS_DD = 100, 1.00, 35.0
MAX_FINALISTS = 25


def catalog() -> list[dict]:
    keys = ("lookback", "entry_momentum", "efficiency_min", "atr_stop", "max_hold_bars")
    values = ((24, 48, 96), (0.75, 1.00, 1.25), (0.25, 0.35, 0.45), (2.0, 2.5), (24, 48))
    return [dict(zip(keys, item)) | {"exit_momentum": 0.0} for item in itertools.product(*values)]


def _entry_fill(bid_open: float, side: int, spread: float, slip: float) -> float:
    return bid_open + (spread + slip) * PIP if side == 1 else bid_open - slip * PIP


def _exit_fill(quote: float, side: int, slip: float) -> float:
    return quote - slip * PIP if side == 1 else quote + slip * PIP


def _round_trip_cost_pips(spread: float, slip: float) -> float:
    return float(spread) + 2.0 * float(slip)


def _stop_hit(side: int, high_bid: float, low_bid: float, stop: float, spread: float) -> bool:
    return low_bid <= stop if side == 1 else high_bid + spread * PIP >= stop


def _stop_quote(side: int, stop: float, open_bid: float, spread: float) -> float:
    return min(stop, open_bid) if side == 1 else max(stop, open_bid + spread * PIP)


def _features(frame: pd.DataFrame, lookback: int) -> pd.DataFrame:
    required = {"Open", "High", "Low", "Close"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"G17_REQUIRED_COLUMNS_MISSING:{sorted(missing)}")
    if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("G17_BAD_CHRONOLOGICAL_INDEX")
    op, hi, lo, cl = (frame[c].astype(float) for c in ("Open", "High", "Low", "Close"))
    if not ((hi >= frame[["Open", "Close"]].max(axis=1)) &
            (lo <= frame[["Open", "Close"]].min(axis=1)) & (hi >= lo)).all():
        raise ValueError("G17_OHLC_INVARIANT_FAIL")
    if not np.isfinite(frame[["Open", "High", "Low", "Close"]].to_numpy(float)).all():
        raise ValueError("G17_NONFINITE_OHLC")
    tr = pd.concat([hi - lo, (hi - cl.shift()).abs(), (lo - cl.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    net = cl - cl.shift(lookback)
    path = cl.diff().abs().rolling(lookback, min_periods=lookback).sum().replace(0, np.nan)
    efficiency = net.abs() / path
    momentum = net / (atr * np.sqrt(float(lookback)))
    return pd.DataFrame({"Open": op, "High": hi, "Low": lo, "Close": cl,
                         "atr": atr, "momentum": momentum, "efficiency": efficiency}, index=frame.index)


def _signal(now: float, prior: float, efficiency: float, p: dict) -> int:
    if not np.isfinite([now, prior, efficiency]).all() or efficiency < p["efficiency_min"]:
        return 0
    threshold = float(p["entry_momentum"])
    if now >= threshold > prior:
        return 1
    if now <= -threshold < prior:
        return -1
    return 0


def backtest(frame: pd.DataFrame, p: dict, costs=BASE_COST) -> dict:
    spread, slip = map(float, costs)
    if not np.isfinite([spread, slip]).all() or spread < 0 or slip < 0:
        raise ValueError("G17_INVALID_COST_ASSUMPTION")
    if frame.empty:
        return {"trades": 0, "total_R": 0.0, "expectancy_R": 0.0, "profit_factor": 0.0,
                "max_adverse_dd_pct": 0.0, "final_equity": INITIAL_EQUITY,
                "round_trip_cost_pips": _round_trip_cost_pips(spread, slip),
                "entries": 0, "exits": 0, "open_position_end": False,
                "drawdown_basis": "CLOSED_EQUITY_PEAK_PLUS_ADVERSE_INTRABAR_MARK"}

    d = _features(frame, int(p["lookback"]))
    op, hi, lo, cl = (d[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
    atr, mom, er = (d[c].to_numpy(float) for c in ("atr", "momentum", "efficiency"))
    equity = peak = INITIAL_EQUITY
    max_dd = 0.0
    side = 0
    entry = stop = unit = 0.0
    entry_i = -1
    rs: list[float] = []
    entries = same_bar_stops = 0

    def mark_adverse(quote: float) -> None:
        nonlocal max_dd
        adverse_fill = _exit_fill(quote, side, slip)
        unrealized_r = side * (adverse_fill - entry) / unit
        adverse_equity = equity * (1.0 + RISK_PCT * unrealized_r)
        if not np.isfinite(adverse_equity) or adverse_equity <= 0:
            raise RuntimeError("G17_NONFINITE_OR_BANKRUPTCY")
        max_dd = max(max_dd, (peak - adverse_equity) / peak)

    def close(quote: float) -> None:
        nonlocal equity, peak, max_dd, side
        fill = _exit_fill(quote, side, slip)
        r = side * (fill - entry) / unit
        factor = 1.0 + RISK_PCT * r
        if not np.isfinite(r) or not np.isfinite(factor) or factor <= 0:
            raise RuntimeError("G17_NONFINITE_OR_BANKRUPTCY")
        equity *= factor
        rs.append(float(r))
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
        side = 0

    for i in range(2, len(d)):
        if side:
            prior_momentum = mom[i - 1]
            exit_signal = ((side == 1 and prior_momentum <= p["exit_momentum"]) or
                           (side == -1 and prior_momentum >= -p["exit_momentum"]))
            time_exit = i - entry_i >= int(p["max_hold_bars"])
            if exit_signal or time_exit:
                close(op[i] if side == 1 else op[i] + spread * PIP)
                continue
            if _stop_hit(side, hi[i], lo[i], stop, spread):
                close(_stop_quote(side, stop, op[i], spread))
                continue
            mark_adverse(lo[i] if side == 1 else hi[i] + spread * PIP)
            continue

        new_side = _signal(mom[i - 1], mom[i - 2], er[i - 1], p)
        if not new_side or not np.isfinite(atr[i - 1]) or atr[i - 1] <= 0:
            continue
        side = new_side
        entry = _entry_fill(op[i], side, spread, slip)
        unit = float(p["atr_stop"]) * atr[i - 1]
        if not np.isfinite(unit) or unit <= 0:
            side = 0
            continue
        stop = entry - side * unit
        entry_i = i
        entries += 1
        if _stop_hit(side, hi[i], lo[i], stop, spread):
            same_bar_stops += 1
            close(_stop_quote(side, stop, op[i], spread))
        else:
            mark_adverse(lo[i] if side == 1 else hi[i] + spread * PIP)

    if side:
        close(cl[-1] if side == 1 else cl[-1] + spread * PIP)
    if side or entries != len(rs):
        raise RuntimeError("G17_EXECUTION_INTEGRITY_FAIL")
    reconstructed = INITIAL_EQUITY
    for r in rs:
        reconstructed *= 1.0 + RISK_PCT * r
    if not np.isclose(equity, reconstructed, rtol=1e-12, atol=1e-8):
        raise RuntimeError("G17_EQUITY_RECONCILIATION_FAIL")

    a = np.asarray(rs, dtype=float)
    gains, losses = float(a[a > 0].sum()), abs(float(a[a <= 0].sum()))
    pf = gains / losses if losses else ("inf" if gains else 0.0)
    n, total = len(a), float(a.sum())
    return {"trades": n, "total_R": round(total, 6),
            "expectancy_R": round(total / n, 6) if n else 0.0,
            "profit_factor": round(pf, 6) if pf != "inf" else pf,
            "win_rate_pct": round(float((a > 0).mean() * 100), 3) if n else 0.0,
            "max_adverse_dd_pct": round(max_dd * 100, 6), "final_equity": round(equity, 2),
            "net_return_pct": round((equity / INITIAL_EQUITY - 1) * 100, 6),
            "entries": entries, "exits": n, "open_position_end": False,
            "spread_pips": spread, "slippage_pips": slip,
            "round_trip_cost_pips": _round_trip_cost_pips(spread, slip),
            "same_bar_stop_first_count": same_bar_stops, "price_basis": "BID_OHLC_ASK_RECONSTRUCTED",
            "drawdown_basis": "CLOSED_EQUITY_PEAK_PLUS_ADVERSE_INTRABAR_MARK"}


def _pf(m: dict) -> float:
    return 3.0 if m.get("profit_factor") == "inf" else float(m.get("profit_factor", 0.0))


def _gate(m: dict, trades: int, pf: float, dd: float) -> list[str]:
    failures = []
    if m["trades"] < trades:
        failures.append(f"trades<{trades}")
    if _pf(m) < pf:
        failures.append(f"profit_factor<{pf}")
    if m["expectancy_R"] <= 0:
        failures.append("expectancy_R<=0")
    if m["total_R"] <= 0:
        failures.append("total_R<=0")
    if m["final_equity"] <= INITIAL_EQUITY:
        failures.append("final_equity<=initial_equity")
    if m["max_adverse_dd_pct"] > dd:
        failures.append(f"max_adverse_dd_pct>{dd}")
    return failures


def _verified_load(data_path: str | Path, manifest_path: str | Path):
    """Verify real HistData EURUSD M5 BID bars; reject 2026+ before any strategy work."""
    data, mf = Path(data_path), Path(manifest_path)
    if not data.is_file() or not data.stat().st_size:
        raise ValueError("G17_DATA_MISSING")
    if not mf.is_file():
        raise ValueError("G17_MANIFEST_MISSING")
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    data_hash = hashlib.sha256(data.read_bytes()).hexdigest()
    manifest_hash = hashlib.sha256(mf.read_bytes()).hexdigest()
    if manifest.get("symbol") != "EURUSD":
        raise ValueError("G17_SYMBOL_MISMATCH")
    if str(manifest.get("timeframe", "")).upper() != "M5":
        raise ValueError("G17_TIMEFRAME_MISMATCH")
    if manifest.get("quality_status") != "PASS":
        raise ValueError("G17_QUALITY_NOT_PASS")
    if "HistData" not in str(manifest.get("source", "")):
        raise ValueError("G17_SOURCE_NOT_HISTDATA")
    if manifest.get("data_sha256") != data_hash:
        raise ValueError("G17_DATA_SHA256_MISMATCH")
    if not manifest.get("source_hash"):
        raise ValueError("G17_SOURCE_HASH_MISSING")
    raw = pd.read_csv(data)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    if required - set(raw.columns):
        raise ValueError(f"G17_REQUIRED_COLUMNS_MISSING:{sorted(required - set(raw.columns))}")
    ts = pd.to_datetime(raw.timestamp, format="mixed", utc=True, errors="raise")
    if ts.isna().any() or ts.duplicated().any() or not ts.is_monotonic_increasing:
        raise ValueError("G17_TIMESTAMP_SEQUENCE_INVALID")
    if len(raw) != int(manifest.get("rows", -1)):
        raise ValueError("G17_ROW_COUNT_MISMATCH")
    if ts.max() >= OOS_START:
        raise ValueError("G17_OOS_POLICY_VIOLATION_2026_DATA_PRESENT")
    if ts.min() >= DATA_START_MIN:
        raise ValueError("G17_DATA_START_TOO_LATE")
    if not ((ts.dt.minute % 5 == 0) & (ts.dt.second == 0) &
            (ts.dt.microsecond == 0)).all():
        raise ValueError("G17_M5_ALIGNMENT_FAIL")
    if not set(ALL_YEARS).issubset(set(ts.dt.year.astype(int))):
        raise ValueError("G17_REQUIRED_YEAR_MISSING")
    raw["timestamp"] = ts
    for col in ("open", "high", "low", "close", "volume"):
        raw[col] = pd.to_numeric(raw[col], errors="raise")
        if not np.isfinite(raw[col].to_numpy(float)).all():
            raise ValueError(f"G17_NONFINITE:{col}")
    if not ((raw.high >= raw[["open", "close"]].max(axis=1)) &
            (raw.low <= raw[["open", "close"]].min(axis=1)) & (raw.high >= raw.low)).all():
        raise ValueError("G17_RAW_OHLC_INVALID")
    if manifest.get("start") and pd.to_datetime(manifest["start"], utc=True) != ts.min():
        raise ValueError("G17_MANIFEST_START_MISMATCH")
    if manifest.get("end") and pd.to_datetime(manifest["end"], utc=True) != ts.max():
        raise ValueError("G17_MANIFEST_END_MISMATCH")
    frame = raw.rename(columns={"timestamp": "Timestamp", "open": "Open", "high": "High",
                                "low": "Low", "close": "Close", "volume": "Volume"}).set_index("Timestamp")
    return frame, manifest, data_hash, manifest_hash


def run_discovery(data_path: str | Path, manifest_path: str | Path) -> dict:
    frame, manifest, data_hash, manifest_hash = _verified_load(data_path, manifest_path)
    years = {y: frame.loc[(frame.index >= pd.Timestamp(f"{y}-01-01", tz="UTC")) &
                          (frame.index < pd.Timestamp(f"{y + 1}-01-01", tz="UTC"))] for y in ALL_YEARS}
    if any(part.empty for part in years.values()):
        raise ValueError("G17_EMPTY_REQUIRED_YEAR")

    ranked, total_is_trades = [], 0
    for cid, params in enumerate(catalog(), 1):
        metrics = {str(y): backtest(years[y], params) for y in YEARS}
        total_is_trades += sum(m["trades"] for m in metrics.values())
        rejects = {str(y): reasons for y in YEARS
                   if (reasons := _gate(metrics[str(y)], IS_TRADES, IS_PF, IS_DD))}
        pfs = [_pf(metrics[str(y)]) for y in YEARS]
        exps = [metrics[str(y)]["expectancy_R"] for y in YEARS]
        dds = [metrics[str(y)]["max_adverse_dd_pct"] for y in YEARS]
        score = (0.50 * min(min(pfs), 2.0) / 2.0 +
                 0.35 * min(float(np.mean(pfs)), 2.0) / 2.0 +
                 0.15 * np.tanh(float(np.mean(exps)) * 10.0) - 0.50 * max(dds) / 100.0)
        ranked.append({"candidate_id": cid, "params": params, "is_metrics_by_year": metrics,
                       "is_gate_pass": not rejects, "is_rejections_by_year": rejects,
                       "is_score": round(float(score), 8)})
    if total_is_trades <= 0:
        raise RuntimeError("G17_NO_IS_TRADES_SIGNAL_INTEGRITY_FAILURE")
    ranked.sort(key=lambda x: (-x["is_score"], x["candidate_id"]))
    passed = [x for x in ranked if x["is_gate_pass"]]
    finalists = passed[:MAX_FINALISTS]
    evaluated = []
    for item in finalists:
        params = item["params"]
        val = backtest(years[VALIDATION_YEAR], params)
        val_rejects = _gate(val, VAL_TRADES, VAL_PF, VAL_DD)
        stress = {str(y): backtest(years[y], params, STRESS_COST) for y in ALL_YEARS}
        stress_rejects = {y: reasons for y, result in stress.items()
                          if (reasons := _gate(result, STRESS_TRADES, STRESS_PF, STRESS_DD))}
        severe = backtest(years[VALIDATION_YEAR], params, SEVERE_COST)
        evaluated.append({**item, "confirmation_2025": val, "confirmation_pass": not val_rejects,
                          "confirmation_rejections": val_rejects, "moderate_stress_by_year": stress,
                          "moderate_stress_pass": not stress_rejects,
                          "moderate_stress_rejections": stress_rejects,
                          "severe_cost_2025_diagnostic": severe})
    qualified = [x for x in evaluated if x["confirmation_pass"] and x["moderate_stress_pass"]]
    frozen = None
    if qualified:
        w = qualified[0]
        frozen = {"family": "efficiency_ratio_time_series_momentum", "symbol": "EURUSD",
                  "timeframe": "M5", "candidate_id": w["candidate_id"], "params": w["params"],
                  "risk_pct": RISK_PCT, "data_sha256": data_hash, "manifest_sha256": manifest_hash,
                  "is_years": list(YEARS), "confirmation_year": VALIDATION_YEAR,
                  "baseline_cost": BASE_COST, "moderate_stress_cost": STRESS_COST,
                  "oos_start": "2026-01-01", "oos_read_during_discovery": False}
        frozen["config_sha256"] = hashlib.sha256(
            json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    decision = ("NO_GO_NO_IS_QUALIFIED_CANDIDATES" if not passed else
                ("NO_GO_CONFIRMATION_OR_COST_STRESS_FAILED" if not qualified else
                 "FROZEN_CANDIDATE_HOLDOUT_PENDING"))
    return {
        "schema_version": SCHEMA, "strategy": "Efficiency-Ratio Time-Series Momentum",
        "symbol": "EURUSD", "timeframe": "M5", "real_data_required": True, "synthetic_fallback": False,
        "source_data": {"source": manifest.get("source"), "dataset_id": manifest.get("dataset_id"),
                        "rows": len(frame), "start": str(frame.index.min()), "end": str(frame.index.max()),
                        "data_sha256": data_hash, "manifest_sha256": manifest_hash,
                        "quality_status": manifest["quality_status"], "price_basis": "BID_OHLC",
                        "ask_reconstruction": "bid_plus_assumed_spread"},
        "protocol": {"catalog_locked": True, "catalog_total": len(ranked), "is_ranks_candidates": True,
                     "is_used_for_ranking": True, "confirmation_2025_pass_fail_only": True,
                     "confirmation_used_for_ranking": False,
                     "validation_status": "CROSS_FAMILY_REUSED_NOT_PRISTINE",
                     "validation_previous_access_disclosure":
                         "2025 EURUSD M5 was inspected in prior research families; confirmation only, not pristine.",
                     "max_confirmation_finalists": MAX_FINALISTS,
                     "signal": "closed-bar normalized multi-bar return crossing with path-efficiency gate; next-open entry",
                     "normalization": "net close change / (prior ATR(14) * sqrt(lookback))",
                     "exit": "normalized momentum returns through zero, BID/ASK-aware ATR stop, or max hold",
                     "2026_loaded": False},
        "costs": {"baseline_round_trip_pips": _round_trip_cost_pips(*BASE_COST),
                  "moderate_stress_round_trip_pips": _round_trip_cost_pips(*STRESS_COST),
                  "severe_diagnostic_round_trip_pips": _round_trip_cost_pips(*SEVERE_COST),
                  "spread_paid_once": True, "slippage_paid_each_side": True,
                  "commission_included": False, "swap_included": False},
        "gates": {"is_each_year": {"trades": IS_TRADES, "pf": IS_PF, "max_adverse_dd_pct": IS_DD,
                                   "all_years_required": True},
                  "confirmation_2025": {"trades": VAL_TRADES, "pf": VAL_PF, "max_adverse_dd_pct": VAL_DD},
                  "moderate_stress_2022_2025": {"trades": STRESS_TRADES, "pf": STRESS_PF,
                                                "max_adverse_dd_pct": STRESS_DD}},
        "catalog": {"candidate_total": len(ranked), "is_qualified_count": len(passed),
                    "confirmation_finalists_evaluated": len(finalists),
                    "fully_qualified_count": len(qualified),
                    "total_is_trades_across_catalog": total_is_trades},
        "decision": decision, "top_20_is_diagnostics": ranked[:20], "evaluated_finalists": evaluated,
        "frozen_candidate": frozen, "selection_frozen": frozen is not None,
        "promotion_decision": "HOLDOUT_NOT_RUN_NO_PROMOTION",
        "demo_authorized": False, "live_authorized": False, "orders_submitted": False,
        "oos_policy": {"loaded": False, "status": "HELD_OUT", "start": "2026-01-01",
                       "oos_runner_invoked": False, "optimization_allowed": False,
                       "oos_optimization_allowed": False},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail-closed G17 real-data EURUSD M5 discovery")
    ap.add_argument("--data", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    report = run_discovery(args.data, args.manifest)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"catalog": report["catalog"], "decision": report["decision"],
                      "costs": report["costs"], "oos_loaded": report["oos_policy"]["loaded"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
