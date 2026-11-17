"""G17: fail-closed Trend Pullback Continuation discovery on real EURUSD M5.

Discovery uses calendar years 2022-2024 only. 2025 is deliberately excluded
because it has already been examined in prior strategy research; 2026+ remains
a separate untouched holdout. No validation, promotion, or trading is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA = "forexai.g17.trend_pullback_continuation.v1"
IS_YEARS = (2022, 2023, 2024)
DATA_END = pd.Timestamp("2025-01-01", tz="UTC")
OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
INITIAL_EQUITY = 10_000.0
RISK_PCT = 0.005
PIP = 0.0001
BASE_COST = (0.50, 0.20)  # spread, adverse slippage per side, in pips
STRESS_COST = (0.75, 0.30)
SEVERE_COST = (1.00, 0.50)
MIN_TRADES = 50
MIN_PF = 1.05
MAX_DD_PCT = 35.0
MAX_SHORTLIST = 10


def catalog() -> list[dict]:
    keys = ("pullback_ema", "rsi_trigger", "adx_min", "atr_stop", "reward_risk", "max_hold_bars")
    values = ((20, 30), (45.0, 50.0), (15.0, 20.0), (1.5, 2.0), (1.5, 2.0), (48, 96))
    return [dict(zip(keys, combo)) for combo in itertools.product(*values)]


def _entry_fill(bid_open: float, side: int, spread_pips: float, slippage_pips: float) -> float:
    """BUY enters at reconstructed ASK; SELL enters at BID."""
    if side == 1:
        return float(bid_open) + (spread_pips + slippage_pips) * PIP
    return float(bid_open) - slippage_pips * PIP


def _exit_fill(side_quote: float, side: int, slippage_pips: float) -> float:
    """side_quote is BID for a long exit and ASK for a short cover."""
    if side == 1:
        return float(side_quote) - slippage_pips * PIP
    return float(side_quote) + slippage_pips * PIP


def _round_trip_cost_pips(spread_pips: float, slippage_pips: float) -> float:
    return float(spread_pips) + 2.0 * float(slippage_pips)


def _features(frame: pd.DataFrame, pullback_ema: int) -> pd.DataFrame:
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

    tr = pd.concat([hi - lo, (hi - cl.shift()).abs(), (lo - cl.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()

    up, down = hi.diff(), -lo.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=frame.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=frame.index)
    plus_sm = plus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    minus_sm = minus_dm.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    pdi = 100.0 * plus_sm / atr.replace(0, np.nan)
    mdi = 100.0 * minus_sm / atr.replace(0, np.nan)
    dx = 100.0 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()

    delta = cl.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = rsi.mask((loss == 0) & (gain > 0), 100.0)
    rsi = rsi.mask((gain == 0) & (loss > 0), 0.0)
    rsi = rsi.mask((gain == 0) & (loss == 0), 50.0)

    return pd.DataFrame({
        "Open": op, "High": hi, "Low": lo, "Close": cl,
        "atr": atr,
        "ema_pullback": cl.ewm(span=int(pullback_ema), adjust=False, min_periods=int(pullback_ema)).mean(),
        "ema50": cl.ewm(span=50, adjust=False, min_periods=50).mean(),
        "ema200": cl.ewm(span=200, adjust=False, min_periods=200).mean(),
        "adx": adx, "pdi": pdi, "mdi": mdi, "rsi": rsi,
    }, index=frame.index)


def _signal_values(values: tuple[np.ndarray, ...], signal_i: int, p: dict) -> int:
    if signal_i < 1:
        return 0
    high, low, close, atr, ema_pullback, ema50, ema200, adx, pdi, mdi, rsi = values
    i = signal_i
    required = [ema_pullback[i], ema50[i], ema200[i], atr[i], adx[i],
                pdi[i], mdi[i], rsi[i], rsi[i - 1], ema50[i - 1],
                high[i], low[i], close[i]]
    if not np.isfinite(required).all() or atr[i] <= 0:
        return 0

    long_trend = ema50[i] > ema200[i] and ema50[i] > ema50[i - 1] and close[i] > ema200[i]
    short_trend = ema50[i] < ema200[i] and ema50[i] < ema50[i - 1] and close[i] < ema200[i]
    threshold = float(p["rsi_trigger"])
    strength_ok = adx[i] >= float(p["adx_min"])

    if (long_trend and strength_ok and pdi[i] > mdi[i] and
            low[i] <= ema_pullback[i] < close[i] and
            rsi[i - 1] <= threshold < rsi[i]):
        return 1
    if (short_trend and strength_ok and mdi[i] > pdi[i] and
            high[i] >= ema_pullback[i] > close[i] and
            rsi[i - 1] >= 100.0 - threshold > rsi[i]):
        return -1
    return 0


def _signal(d: pd.DataFrame, signal_i: int, p: dict) -> int:
    columns = ("High", "Low", "Close", "atr", "ema_pullback", "ema50",
               "ema200", "adx", "pdi", "mdi", "rsi")
    values = tuple(d[column].to_numpy(dtype=float) for column in columns)
    return _signal_values(values, signal_i, p)


def _stop_hit(side: int, high_bid: float, low_bid: float, stop: float, spread_pips: float) -> bool:
    if side == 1:
        return float(low_bid) <= float(stop)
    return float(high_bid) + float(spread_pips) * PIP >= float(stop)


def _target_hit(side: int, high_bid: float, low_bid: float, target: float, spread_pips: float) -> bool:
    if side == 1:
        return float(high_bid) >= float(target)
    return float(low_bid) + float(spread_pips) * PIP <= float(target)


def _stop_quote(side: int, stop: float, open_bid: float, spread_pips: float) -> float:
    if side == 1:
        return min(float(stop), float(open_bid))
    open_ask = float(open_bid) + float(spread_pips) * PIP
    return max(float(stop), open_ask)


def _target_quote(side: int, target: float, open_bid: float, spread_pips: float) -> float:
    if side == 1:
        return max(float(target), float(open_bid))
    open_ask = float(open_bid) + float(spread_pips) * PIP
    return min(float(target), open_ask)


def _empty_metrics(spread: float, slip: float) -> dict:
    return {
        "trades": 0, "total_R": 0.0, "expectancy_R": 0.0, "profit_factor": 0.0,
        "win_rate_pct": 0.0, "max_dd_pct": 0.0, "final_equity": INITIAL_EQUITY,
        "net_return_pct": 0.0, "round_trip_cost_pips": _round_trip_cost_pips(spread, slip),
    }


def backtest(frame: pd.DataFrame, p: dict, costs=BASE_COST, prepared: pd.DataFrame | None = None) -> dict:
    spread, slip = map(float, costs)
    if spread < 0 or slip < 0:
        raise ValueError("G17_NEGATIVE_COST")
    if frame.empty:
        return _empty_metrics(spread, slip)
    d = prepared if prepared is not None else _features(frame, int(p["pullback_ema"]))
    op, hi, lo, cl = (d[c].to_numpy(float) for c in ("Open", "High", "Low", "Close"))
    atr = d["atr"].to_numpy(float)
    signal_values = tuple(d[column].to_numpy(dtype=float) for column in (
        "High", "Low", "Close", "atr", "ema_pullback", "ema50", "ema200",
        "adx", "pdi", "mdi", "rsi",
    ))

    equity = peak = INITIAL_EQUITY
    max_dd = 0.0
    side = 0
    entry = stop = target = unit = 0.0
    entry_i = -1
    entries = 0
    stop_exits = target_exits = time_exits = 0
    returns: list[float] = []

    def close(side_quote: float) -> None:
        nonlocal equity, peak, max_dd, side
        fill = _exit_fill(side_quote, side, slip)
        r = side * (fill - entry) / unit
        factor = 1.0 + RISK_PCT * r
        if not np.isfinite(r) or not np.isfinite(factor) or factor <= 0:
            raise RuntimeError("G17_NONFINITE_OR_BANKRUPTCY")
        equity *= factor
        returns.append(float(r))
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak)
        side = 0

    for i in range(2, len(d)):
        if side:
            # Time exits execute at this bar's open before observing its range.
            if i - entry_i >= int(p["max_hold_bars"]):
                quote = op[i] if side == 1 else op[i] + spread * PIP
                close(quote)
                time_exits += 1
                continue
            stop_hit = _stop_hit(side, hi[i], lo[i], stop, spread)
            target_hit = _target_hit(side, hi[i], lo[i], target, spread)
            if stop_hit:  # conservative stop-first resolution when both are touched
                close(_stop_quote(side, stop, op[i], spread))
                stop_exits += 1
                continue
            if target_hit:
                close(_target_quote(side, target, op[i], spread))
                target_exits += 1
                continue
            continue

        direction = _signal_values(signal_values, i - 1, p)
        if not direction or not np.isfinite(atr[i - 1]) or atr[i - 1] <= 0:
            continue
        side = direction
        entry = _entry_fill(op[i], side, spread, slip)
        unit = float(p["atr_stop"]) * atr[i - 1]
        if not np.isfinite(unit) or unit <= 0:
            side = 0
            continue
        stop = entry - side * unit
        target = entry + side * unit * float(p["reward_risk"])
        entry_i = i
        entries += 1

        # Same-bar stop/target checks are conservative and use BID/ASK sides.
        stop_hit = _stop_hit(side, hi[i], lo[i], stop, spread)
        target_hit = _target_hit(side, hi[i], lo[i], target, spread)
        if stop_hit:
            close(_stop_quote(side, stop, op[i], spread))
            stop_exits += 1
        elif target_hit:
            close(_target_quote(side, target, op[i], spread))
            target_exits += 1

    if side:
        quote = cl[-1] if side == 1 else cl[-1] + spread * PIP
        close(quote)
        time_exits += 1

    if side or entries != len(returns):
        raise RuntimeError("G17_EXECUTION_INTEGRITY_FAIL")
    expected = INITIAL_EQUITY
    for r in returns:
        expected *= 1.0 + RISK_PCT * r
    if not np.isclose(equity, expected, rtol=1e-12, atol=1e-8):
        raise RuntimeError("G17_EQUITY_RECONCILIATION_FAIL")

    arr = np.asarray(returns, dtype=float)
    wins, losses = arr[arr > 0], arr[arr <= 0]
    gross_loss = abs(float(losses.sum()))
    pf = float(wins.sum()) / gross_loss if gross_loss else ("inf" if len(wins) else 0.0)
    total = float(arr.sum())
    n = len(arr)
    return {
        "trades": n, "total_R": round(total, 6),
        "expectancy_R": round(total / n, 6) if n else 0.0,
        "profit_factor": round(pf, 6) if pf != "inf" else pf,
        "win_rate_pct": round(float((arr > 0).mean() * 100), 3) if n else 0.0,
        "max_dd_pct": round(max_dd * 100, 6), "final_equity": round(equity, 2),
        "net_return_pct": round((equity / INITIAL_EQUITY - 1) * 100, 6),
        "entries": entries, "exits": n, "open_position_end": False,
        "stop_exits": stop_exits, "target_exits": target_exits, "time_exits": time_exits,
        "spread_pips": spread, "slippage_pips": slip,
        "round_trip_cost_pips": _round_trip_cost_pips(spread, slip),
        "price_basis": "BID_OHLC_ASK_RECONSTRUCTED",
        "same_bar_collision_policy": "STOP_FIRST",
    }


def _pf(metrics: dict) -> float:
    return 3.0 if metrics.get("profit_factor") == "inf" else float(metrics.get("profit_factor", 0.0))


def _gate(metrics: dict) -> list[str]:
    rejects = []
    if metrics["trades"] < MIN_TRADES:
        rejects.append(f"trades<{MIN_TRADES}")
    if _pf(metrics) < MIN_PF:
        rejects.append(f"profit_factor<{MIN_PF}")
    if metrics["expectancy_R"] <= 0:
        rejects.append("expectancy_R<=0")
    if metrics["total_R"] <= 0:
        rejects.append("total_R<=0")
    if metrics["final_equity"] <= INITIAL_EQUITY:
        rejects.append("final_equity<=initial_equity")
    if metrics["max_dd_pct"] > MAX_DD_PCT:
        rejects.append(f"max_dd_pct>{MAX_DD_PCT}")
    return rejects


def _hash(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _load(data_path: str | Path, manifest_path: str | Path):
    data, manifest_file = Path(data_path), Path(manifest_path)
    if not data.is_file() or not data.stat().st_size:
        raise ValueError("G17_DATA_MISSING")
    if not manifest_file.is_file():
        raise ValueError("G17_MANIFEST_MISSING")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    data_hash = hashlib.sha256(data.read_bytes()).hexdigest()
    manifest_hash = hashlib.sha256(manifest_file.read_bytes()).hexdigest()

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
    ts = pd.to_datetime(raw["timestamp"], format="mixed", utc=True, errors="raise")
    if ts.isna().any() or ts.duplicated().any() or not ts.is_monotonic_increasing:
        raise ValueError("G17_TIMESTAMP_SEQUENCE_INVALID")
    if len(raw) != int(manifest.get("rows", -1)):
        raise ValueError("G17_ROW_COUNT_MISMATCH")
    if ts.min() < pd.Timestamp("2022-01-01", tz="UTC") or ts.max() >= DATA_END:
        raise ValueError("G17_DATA_WINDOW_VIOLATION_2025_OR_OUT_OF_RANGE_ROW")
    if len(ts) == 0 or not set(IS_YEARS).issubset(set(ts.dt.year.astype(int))):
        raise ValueError("G17_REQUIRED_YEAR_MISSING")
    if not ((ts.dt.minute % 5 == 0) & (ts.dt.second == 0) & (ts.dt.microsecond == 0)).all():
        raise ValueError("G17_M5_ALIGNMENT_FAIL")

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

    raw["timestamp"] = ts
    frame = raw.rename(columns={
        "timestamp": "Timestamp", "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "volume": "Volume",
    }).set_index("Timestamp")
    return frame, manifest, data_hash, manifest_hash


def run_discovery(data_path: str | Path, manifest_path: str | Path) -> dict:
    frame, manifest, data_hash, manifest_hash = _load(data_path, manifest_path)
    years = {
        year: frame.loc[(frame.index >= pd.Timestamp(f"{year}-01-01", tz="UTC")) &
                        (frame.index < pd.Timestamp(f"{year + 1}-01-01", tz="UTC"))]
        for year in IS_YEARS
    }
    if any(part.empty for part in years.values()):
        raise ValueError("G17_EMPTY_REQUIRED_YEAR")

    prepared = {
        period: {year: _features(year_frame, period) for year, year_frame in years.items()}
        for period in (20, 30)
    }
    ranked = []
    total_trades = 0
    for candidate_id, params in enumerate(catalog(), start=1):
        base_by_year = {
            str(year): backtest(years[year], params, BASE_COST, prepared[params["pullback_ema"]][year])
            for year in IS_YEARS
        }
        stress_by_year = {
            str(year): backtest(years[year], params, STRESS_COST, prepared[params["pullback_ema"]][year])
            for year in IS_YEARS
        }
        total_trades += sum(item["trades"] for item in base_by_year.values())
        rejects = {str(year): _gate(base_by_year[str(year)]) for year in IS_YEARS}
        rejects = {year: reasons for year, reasons in rejects.items() if reasons}
        stress_rejects = {str(year): _gate(stress_by_year[str(year)]) for year in IS_YEARS}
        stress_rejects = {year: reasons for year, reasons in stress_rejects.items() if reasons}
        pfs = [_pf(base_by_year[str(year)]) for year in IS_YEARS]
        score = (
            1.0 * min(float(np.mean(pfs)), 3.0) / 3.0
            + np.tanh(sum(base_by_year[str(year)]["total_R"] for year in IS_YEARS) / 100.0)
            - 2.0 * max(base_by_year[str(year)]["max_dd_pct"] for year in IS_YEARS) / 100.0
        )
        ranked.append({
            "candidate_id": candidate_id, "params": params,
            "is_metrics_by_year": base_by_year, "moderate_stress_by_year": stress_by_year,
            "is_gate_pass": not rejects, "is_rejections_by_year": rejects,
            "moderate_stress_pass": not stress_rejects,
            "moderate_stress_rejections_by_year": stress_rejects,
            "discovery_score": round(float(score), 8),
        })

    if total_trades <= 0:
        raise RuntimeError("G17_NO_TRADES_SIGNAL_OR_FEATURE_INTEGRITY_FAILURE")
    ranked.sort(key=lambda item: (-item["discovery_score"], item["candidate_id"]))
    is_qualified = [item for item in ranked if item["is_gate_pass"]]
    cost_resilient = [item for item in is_qualified if item["moderate_stress_pass"]]
    shortlist = cost_resilient[:MAX_SHORTLIST]

    return {
        "schema_version": SCHEMA,
        "strategy": "Trend Pullback Continuation",
        "symbol": "EURUSD", "timeframe": "M5",
        "real_data_required": True, "synthetic_fallback": False,
        "source_data": {
            "source": manifest.get("source"), "dataset_id": manifest.get("dataset_id"),
            "rows": len(frame), "start": str(frame.index.min()), "end": str(frame.index.max()),
            "data_sha256": data_hash, "manifest_sha256": manifest_hash,
            "quality_status": manifest["quality_status"], "price_basis": "BID_OHLC",
            "ask_reconstruction": "bid_plus_assumed_spread",
        },
        "protocol": {
            "catalog_locked": True, "catalog_total": len(ranked),
            "is_years": list(IS_YEARS), "is_used_for_ranking": True,
            "year_2025_loaded": False, "year_2025_excluded_due_to_prior_cross_family_reuse": True,
            "oos_start": "2026-01-01", "oos_loaded": False,
            "validation_performed": False, "fresh_validation_required_before_freeze_or_promotion": True,
            "signal": "closed-bar EMA50/EMA200 trend alignment; pullback EMA reclaim; RSI rebound; ADX and DI confirmation; next-open entry",
            "exits": "ATR stop; fixed R-multiple target; max holding period; stop-first intrabar collision handling",
            "one_position_at_a_time": True,
        },
        "costs": {
            "baseline_round_trip_pips": _round_trip_cost_pips(*BASE_COST),
            "moderate_stress_round_trip_pips": _round_trip_cost_pips(*STRESS_COST),
            "severe_diagnostic_round_trip_pips": _round_trip_cost_pips(*SEVERE_COST),
            "spread_paid_once": True, "slippage_paid_each_side": True,
            "commission_included": False, "swap_included": False,
        },
        "gates": {
            "each_is_year": {"trades": MIN_TRADES, "profit_factor": MIN_PF,
                             "positive_expectancy": True, "final_equity_above_initial": True,
                             "max_dd_pct": MAX_DD_PCT, "all_years_required": True},
            "moderate_stress_each_is_year": {"same_trade_and_risk_gates": True,
                                             "round_trip_cost_pips": 1.35},
        },
        "catalog": {
            "candidate_total": len(ranked), "is_qualified_count": len(is_qualified),
            "cost_resilient_count": len(cost_resilient), "shortlist_count": len(shortlist),
            "total_is_trades_across_catalog": total_trades,
        },
        "decision": ("DISCOVERY_ONLY_REQUIRES_UNSEEN_VALIDATION" if shortlist else
                     ("IS_QUALIFIED_BUT_COST_STRESS_FAILED" if is_qualified else "NO_GO_NO_IS_QUALIFIED_CANDIDATES")),
        "selection_frozen": False, "frozen_candidate": None,
        "shortlist": shortlist,
        "top_20_is_diagnostics": ranked[:20],
        "promotion_decision": "HOLDOUT_NOT_RUN_NO_PROMOTION",
        "demo_authorized": False, "live_authorized": False, "orders_submitted": False,
        "oos_policy": {"loaded": False, "status": "HELD_OUT", "start": "2026-01-01",
                       "oos_runner_invoked": False, "optimization_allowed": False,
                       "oos_optimization_allowed": False},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed G17 real-data EURUSD M5 discovery")
    parser.add_argument("--data", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    report = run_discovery(args.data, args.manifest)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "candidate_total": report["catalog"]["candidate_total"],
        "is_qualified": report["catalog"]["is_qualified_count"],
        "cost_resilient": report["catalog"]["cost_resilient_count"],
        "shortlist": report["catalog"]["shortlist_count"],
        "decision": report["decision"], "oos_loaded": report["oos_policy"]["loaded"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
