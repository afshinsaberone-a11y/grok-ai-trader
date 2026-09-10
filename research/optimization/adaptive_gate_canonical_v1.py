from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from research.optimization.regime_aware_event_discovery_g6 import prepare, signal
from research.optimization.execution_contract_v1 import ExecutionConfig, apply_entry_cost, apply_exit_cost, validate_ohlc

YEARS = (2022, 2023, 2024, 2025)
CALIBRATION_YEARS = (2022, 2023, 2024)
OOS_START = pd.Timestamp("2026-01-01", tz="UTC")
MAX_HOLD = 30
WARMUP = 500
PIP = 0.0001

OFFICIAL_GATES = {
    "min_profitable_years": 3,
    "min_pf_each_year": 1.05,
    "min_expectancy": 0.0,
    "min_trades_each_year": 100,
    "max_dd_pct": 35.0,
}

EXPECTED_VARIANT = {
    "name": "adx30_50_slope",
    "adx_q": 0.30,
    "trend_persist": 0.50,
    "require_slope": True,
}


def _sha(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_g12(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != "forexai.g12.adaptive_gate_calibration.v1":
        raise ValueError("invalid G12 artifact schema")
    if data.get("policy", {}).get("oos_2026_used") is not False:
        raise ValueError("G12 artifact violates 2026 holdout")
    rec = data.get("recommended_for_canonical_rerun")
    if rec != EXPECTED_VARIANT:
        raise ValueError(f"unexpected G12 recommendation: {rec!r}")
    return data


def _features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    tr = pd.concat(
        [(d.High - d.Low), (d.High - d.Close.shift()).abs(), (d.Low - d.Close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    d["ATR14"] = tr.rolling(14, min_periods=14).mean()
    plus = d.High.diff().clip(lower=0.0)
    minus = (-d.Low.diff()).clip(lower=0.0)
    pdi = 100 * plus.rolling(14).mean() / d.ATR14.replace(0, np.nan)
    mdi = 100 * minus.rolling(14).mean() / d.ATR14.replace(0, np.nan)
    d["DX14"] = (100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)).fillna(0)
    d["ADX14"] = d.DX14.rolling(14).mean()
    d["ADX_Q"] = d.ADX14.rolling(96, min_periods=48).rank(pct=True)
    d["EMA_SLOPE_ATR"] = (d.EMA16 - d.EMA16.shift(4)) / d.ATR14.replace(0, np.nan)
    d["TREND_PERSIST"] = (d.EMA16 > d.EMA50).astype(float).rolling(8).mean()
    return d


def _gate_row(side: int, adx_q: float, trend_persist: float, slope: float) -> bool:
    if not (np.isfinite(adx_q) and adx_q >= EXPECTED_VARIANT["adx_q"]):
        return False
    if not (np.isfinite(trend_persist) and trend_persist >= EXPECTED_VARIANT["trend_persist"]):
        return False
    if side == 1:
        return bool(np.isfinite(slope) and slope > 0)
    if side == -1:
        return bool(np.isfinite(slope) and slope < 0)
    return False


def _execute(d: pd.DataFrame) -> tuple[list[float], dict[str, object]]:
    cfg = ExecutionConfig(expiry_bars=MAX_HOLD)
    base = prepare(d.reset_index())
    base = _features(base)
    signals = [signal(base, i, {"family": "regime_momentum", "fast": 16, "slow": 50, "atr_pct": 0.50, "atr_mult": 1.0, "rr": 2.0}) for i in range(len(base))]
    rs: list[float] = []
    position = 0
    entry_px = stop = target = 0.0
    entry_i = -1
    entries = exits = 0
    for i in range(1, len(base) - 1):
        if position == 0:
            side = int(signals[i - 1])
            if side == 0:
                continue
            if not _gate_row(side, float(base.ADX_Q.iloc[i - 1]), float(base.TREND_PERSIST.iloc[i - 1]), float(base.EMA_SLOPE_ATR.iloc[i - 1])):
                continue
            atr = float(base.ATR14.iloc[i - 1])
            if not np.isfinite(atr) or atr <= 0:
                continue
            position = side
            entry_i = i
            entry_px = apply_entry_cost(float(base.Open.iloc[i]), position, cfg)
            risk = atr
            stop = entry_px - position * risk
            target = entry_px + position * 2.0 * risk
            entries += 1
            continue
        age = i - entry_i + 1
        hit_sl = float(base.Low.iloc[i]) <= stop if position == 1 else float(base.High.iloc[i]) >= stop
        hit_tp = float(base.High.iloc[i]) >= target if position == 1 else float(base.Low.iloc[i]) <= target
        reason = None
        if hit_sl and hit_tp:
            raw_exit = stop
            exit_px = apply_exit_cost(raw_exit, position, cfg)
            reason = "same_bar_sl_first"
        elif hit_sl:
            raw_exit = stop
            exit_px = apply_exit_cost(raw_exit, position, cfg)
            reason = "sl"
        elif hit_tp:
            raw_exit = target
            exit_px = apply_exit_cost(raw_exit, position, cfg)
            reason = "tp"
        elif int(signals[i]) == -position and i + 1 < len(base):
            exit_px = apply_exit_cost(float(base.Open.iloc[i + 1]), position, cfg)
            reason = "opposite_next_open"
        elif age >= MAX_HOLD and i + 1 < len(base):
            exit_px = apply_exit_cost(float(base.Open.iloc[i + 1]), position, cfg)
            reason = "expiry_next_open"
        if reason is None:
            continue
        risk_unit = float(base.ATR14.iloc[entry_i - 1])
        if not np.isfinite(risk_unit) or risk_unit <= 0:
            position = 0
            continue
        rs.append(float(position * (exit_px - entry_px) / risk_unit))
        exits += 1
        position = 0
    if position != 0:
        risk_unit = float(base.ATR14.iloc[max(entry_i - 1, 0)])
        if np.isfinite(risk_unit) and risk_unit > 0:
            exit_px = apply_exit_cost(float(base.Close.iloc[-1]), position, cfg)
            rs.append(float(position * (exit_px - entry_px) / risk_unit))
            exits += 1
        position = 0
    return rs, {
        "entries": entries,
        "exits": exits,
        "entries_equal_exits": entries == exits,
        "next_bar_open_entry": True,
        "actual_entry_price_for_stops": True,
        "adverse_exit_cost_applied": True,
        "same_bar_sl_first": True,
        "one_position_at_a_time": True,
        "round_trip_cost_pips": cfg.round_trip_cost_pips,
        "expiry_bars": MAX_HOLD,
    }


def _metrics(rs: list[float]) -> dict[str, float | int]:
    if not rs:
        return {"trades": 0, "win_rate_pct": 0.0, "total_R": 0.0, "expectancy_R": 0.0, "profit_factor": 0.0, "max_dd_pct": 0.0}
    arr = np.asarray(rs, dtype=float)
    gp = float(arr[arr > 0].sum())
    gl = float(-arr[arr < 0].sum())
    pf = gp / gl if gl > 0 else (3.0 if gp > 0 else 0.0)
    eq = peak = 10000.0
    dd = 0.0
    for r in arr:
        eq *= 1.0 + 0.005 * float(r)
        peak = max(peak, eq)
        dd = max(dd, (peak - eq) / peak)
    return {
        "trades": int(len(arr)),
        "win_rate_pct": float((arr > 0).mean() * 100.0),
        "total_R": float(arr.sum()),
        "expectancy_R": float(arr.mean()),
        "profit_factor": float(pf),
        "max_dd_pct": float(dd * 100.0),
    }


def _gate(m: dict[str, float | int]) -> bool:
    return (
        m["trades"] >= OFFICIAL_GATES["min_trades_each_year"]
        and m["profit_factor"] >= OFFICIAL_GATES["min_pf_each_year"]
        and m["expectancy_R"] > OFFICIAL_GATES["min_expectancy"]
        and m["max_dd_pct"] <= OFFICIAL_GATES["max_dd_pct"]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--g12-artifact", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    g12 = _load_g12(args.g12_artifact)
    raw = pd.read_csv(args.data)
    raw.columns = [str(c).strip() for c in raw.columns]
    if "timestamp" not in raw.columns and "Timestamp" in raw.columns:
        raw = raw.rename(columns={"Timestamp": "timestamp"})
    required = {"timestamp", "open", "high", "low", "close"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"REAL_DATA_REQUIRED: missing columns {sorted(missing)}")
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True)
    raw = raw.sort_values("timestamp").drop_duplicates("timestamp").copy()
    raw = raw[raw.timestamp.dt.year.isin(YEARS)].copy()
    raw = raw.rename(columns={"timestamp": "Timestamp", "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}).set_index("Timestamp")
    validate_ohlc(raw)
    raw = raw[raw.index < OOS_START]

    yearly = {}
    invariant_rows = {}
    for year in YEARS:
        y0 = pd.Timestamp(f"{year}-01-01", tz="UTC")
        y1 = pd.Timestamp(f"{year + 1}-01-01", tz="UTC")
        prior = raw.index[raw.index < y0]
        warm_start = prior[-WARMUP] if len(prior) >= WARMUP else raw.index.min()
        part = raw.loc[(raw.index >= warm_start) & (raw.index < y1)].copy()
        gated = _features(prepare(part.reset_index()))
        signals = [signal(gated, i, {"family": "regime_momentum", "fast": 16, "slow": 50, "atr_pct": 0.50, "atr_mult": 1.0, "rr": 2.0}) for i in range(len(gated))]
        rs: list[float] = []
        position = 0
        entry_px = stop = target = 0.0
        entry_i = -1
        entries = exits = 0
        for i in range(1, len(gated) - 1):
            current_ts = gated.index[i]
            if current_ts < y0:
                continue
            if position == 0:
                side = int(signals[i - 1])
                if side == 0 or not _gate_row(side, float(gated.ADX_Q.iloc[i - 1]), float(gated.TREND_PERSIST.iloc[i - 1]), float(gated.EMA_SLOPE_ATR.iloc[i - 1])):
                    continue
                atr = float(gated.ATR14.iloc[i - 1])
                if not np.isfinite(atr) or atr <= 0:
                    continue
                cfg = ExecutionConfig(expiry_bars=MAX_HOLD)
                position = side
                entry_i = i
                entry_px = apply_entry_cost(float(gated.Open.iloc[i]), position, cfg)
                risk = atr
                stop = entry_px - position * risk
                target = entry_px + position * 2.0 * risk
                entries += 1
                continue
            age = i - entry_i + 1
            hit_sl = float(gated.Low.iloc[i]) <= stop if position == 1 else float(gated.High.iloc[i]) >= stop
            hit_tp = float(gated.High.iloc[i]) >= target if position == 1 else float(gated.Low.iloc[i]) <= stop
            reason = None
            cfg = ExecutionConfig(expiry_bars=MAX_HOLD)
            if hit_sl and hit_tp:
                exit_px = apply_exit_cost(stop, position, cfg); reason = "same_bar_sl_first"
            elif hit_sl:
                exit_px = apply_exit_cost(stop, position, cfg); reason = "sl"
            elif hit_tp:
                exit_px = apply_exit_cost(target, position, cfg); reason = "tp"
            elif int(signals[i]) == -position and i + 1 < len(gated):
                exit_px = apply_exit_cost(float(gated.Open.iloc[i + 1]), position, cfg); reason = "opposite_next_open"
            elif age >= MAX_HOLD and i + 1 < len(gated):
                exit_px = apply_exit_cost(float(gated.Open.iloc[i + 1]), position, cfg); reason = "expiry_next_open"
            if reason is None:
                continue
            risk_unit = float(gated.ATR14.iloc[entry_i - 1])
            if not np.isfinite(risk_unit) or risk_unit <= 0:
                position = 0; continue
            rs.append(float(position * (exit_px - entry_px) / risk_unit))
            exits += 1; position = 0
        if position != 0:
            cfg = ExecutionConfig(expiry_bars=MAX_HOLD)
            risk_unit = float(gated.ATR14.iloc[max(entry_i - 1, 0)])
            if np.isfinite(risk_unit) and risk_unit > 0:
                exit_px = apply_exit_cost(float(gated.Close.iloc[-1]), position, cfg)
                rs.append(float(position * (exit_px - entry_px) / risk_unit)); exits += 1
            position = 0
        yearly[str(year)] = _metrics(rs)
        yearly[str(year)]["warmup_bars"] = min(WARMUP, len(prior))
        invariant_rows[str(year)] = {"entries": entries, "exits": exits, "entries_equal_exits": entries == exits}

    pre = {y: yearly[str(y)] for y in CALIBRATION_YEARS}
    pre_gate = {str(y): _gate(pre[y]) for y in CALIBRATION_YEARS}
    pre_qual = all(pre_gate.values()) and sum(pre_gate.values()) >= OFFICIAL_GATES["min_profitable_years"]
    validation_pass = _gate(yearly["2025"])

    payload = {
        "schema_version": "forexai.g12.adaptive_gate_canonical.v1",
        "source": {"g12_artifact": str(args.g12_artifact), "g12_artifact_sha256": _sha(args.g12_artifact)},
        "research_scope": {"symbol": "EURUSD", "timeframe": "M15", "calibration_years": list(CALIBRATION_YEARS), "validation_year": 2025},
        "selected_variant": EXPECTED_VARIANT,
        "base_candidate": {"family": "regime_momentum", "fast": 16, "slow": 50, "atr_pct": 0.50, "atr_mult": 1.0, "rr": 2.0},
        "execution_model": {"entry": "next_bar_open", "cost_pips_per_side": 0.7, "round_trip_cost_pips": 1.4, "same_bar_resolution": "SL first (conservative)", "expiry_bars": MAX_HOLD, "overlap": "one position at a time"},
        "policy": {"real_data_required": True, "synthetic_data": False, "oos_2026_used": False, "parameter_selection_used_2025": False, "gates_unchanged": True, "champion": None},
        "official_gates": OFFICIAL_GATES,
        "validation": {"pre_oos_yearly": pre, "pre_oos_gate_by_year": pre_gate, "pre_oos_qualified": bool(pre_qual), "year_2025": yearly["2025"], "validation_pass": bool(pre_qual and validation_pass), "yearly": yearly},
        "execution_invariants": invariant_rows,
        "canonical_status": "PASS" if (pre_qual and validation_pass) else "HOLD",
        "next_step": "Canonical robustness is permitted only if canonical validation_pass is true; otherwise reject and return to research.",
    }
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"canonical_status": payload["canonical_status"], "selected_variant": EXPECTED_VARIANT["name"], "pre_oos_qualified": pre_qual, "validation_pass": validation_pass, "champion": None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
