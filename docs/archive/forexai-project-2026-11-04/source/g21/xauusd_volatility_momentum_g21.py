"""G21 XAUUSD H1 volatility-expansion / momentum-continuation research.

Pre-registered, research-only screen on the immutable G18 real Dukascopy
BID/ASK dataset. Costs are from the WM Markets Demo sample; slippage cases
are declared stress assumptions. No broker orders are submitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

EXPECTED_DATA_SHA256 = "85d505a69a062552847f4aa39c31161c6c1206610dc83c3815cce0d77796cbcb"
EXPECTED_MANIFEST_SHA256 = "1df7d7cf3d04fce8702859eda98de08b5ba103d8d4ef8e35d174a6121fb776aa"
EXPECTED_ROWS = 23650
SERVER_TIMEZONE = "Europe/Athens"
COMMISSION_FEE_USD_PER_OZ_ROUND_TURN = 0.08
DISCOVERY_YEARS = (2021, 2022, 2023)
VALIDATION_YEAR = 2024


class G21Error(RuntimeError):
    """Raised when source evidence or intraday execution constraints fail."""


@dataclass(frozen=True)
class VolatilityMomentumSpec:
    breakout_lookback: int = 20
    atr_period: int = 14
    adx_period: int = 14
    atr_baseline_lookback: int = 96
    min_atr_expansion_ratio: float = 1.15
    min_adx: float = 18.0
    stop_atr_multiple: float = 1.75
    target_r_multiple: float = 2.5
    max_holding_bars: int = 12
    first_entry_server_hour: int = 2
    last_entry_server_hour: int = 21
    flatten_server_hour: int = 22
    risk_fraction: float = 0.0025


SPEC = VolatilityMomentumSpec()
SLIPPAGE_SCENARIOS = (0.05, 0.10, 0.20)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_qualified_dataset(data_path: str | Path, manifest_path: str | Path) -> pd.DataFrame:
    data_path, manifest_path = Path(data_path), Path(manifest_path)
    if _sha256(data_path) != EXPECTED_DATA_SHA256:
        raise G21Error("G21_DATA_SHA256_MISMATCH")
    if _sha256(manifest_path) != EXPECTED_MANIFEST_SHA256:
        raise G21Error("G21_MANIFEST_SHA256_MISMATCH")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "schema": "forexai.real_data.xauusd_bidask_h1.v1",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "source": "Dukascopy historical BID/ASK BI5 bars",
        "data_sha256": EXPECTED_DATA_SHA256,
        "rows": EXPECTED_ROWS,
        "synthetic_data": False,
        "backtest_run": False,
    }
    for key, value in required.items():
        if manifest.get(key) != value:
            raise G21Error(f"G21_MANIFEST_FIELD_MISMATCH:{key}")

    frame = pd.read_csv(data_path)
    if len(frame) != EXPECTED_ROWS:
        raise G21Error("G21_ROW_COUNT_MISMATCH")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    if frame["timestamp"].isna().any() or frame["timestamp"].duplicated().any():
        raise G21Error("G21_TIMESTAMP_INVALID_OR_DUPLICATED")
    if not frame["timestamp"].is_monotonic_increasing:
        raise G21Error("G21_TIMESTAMP_NOT_SORTED")
    if set(frame["timestamp"].dt.year.unique()) != {2021, 2022, 2023, 2024}:
        raise G21Error("G21_YEAR_SCOPE_INVALID")

    price_columns = [f"{side}_{part}" for side in ("bid", "ask") for part in ("open", "high", "low", "close")]
    prices = frame[price_columns].apply(pd.to_numeric, errors="coerce")
    if prices.isna().any().any() or not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any():
        raise G21Error("G21_PRICE_VALUES_INVALID")
    if (frame[["spread_open", "spread_close"]] < 0).any().any():
        raise G21Error("G21_NEGATIVE_SPREAD")
    for point in ("open", "close"):
        if not np.allclose(
            frame[f"spread_{point}"].to_numpy(dtype=float),
            frame[f"ask_{point}"].to_numpy(dtype=float) - frame[f"bid_{point}"].to_numpy(dtype=float),
            atol=1e-9,
            rtol=0.0,
        ):
            raise G21Error(f"G21_SPREAD_RECONCILIATION_FAILED:{point}")
    for side in ("bid", "ask"):
        op, hi, lo, cl = (prices[f"{side}_{c}"] for c in ("open", "high", "low", "close"))
        if ((hi < np.maximum(op, cl)) | (lo > np.minimum(op, cl)) | (hi < lo)).any():
            raise G21Error(f"G21_{side.upper()}_OHLC_INVARIANT_FAILED")
    return frame


def make_signals(bars: pd.DataFrame, spec: VolatilityMomentumSpec = SPEC) -> pd.DataFrame:
    """Build a causal Donchian breakout with volatility expansion and ADX confirmation."""
    frame = bars.copy().reset_index(drop=True)
    mid_close = (frame["bid_close"].astype(float) + frame["ask_close"].astype(float)) / 2.0
    mid_high = (frame["bid_high"].astype(float) + frame["ask_high"].astype(float)) / 2.0
    mid_low = (frame["bid_low"].astype(float) + frame["ask_low"].astype(float)) / 2.0

    previous_close = mid_close.shift(1)
    true_range = pd.concat(
        [
            mid_high - mid_low,
            (mid_high - previous_close).abs(),
            (mid_low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / spec.atr_period, adjust=False, min_periods=spec.atr_period).mean()

    up_move = mid_high.diff()
    down_move = -mid_low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0.0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0.0), 0.0)
    atr_safe = atr.replace(0.0, np.nan)
    plus_di = 100.0 * plus_dm.ewm(alpha=1.0 / spec.adx_period, adjust=False, min_periods=spec.adx_period).mean() / atr_safe
    minus_di = 100.0 * minus_dm.ewm(alpha=1.0 / spec.adx_period, adjust=False, min_periods=spec.adx_period).mean() / atr_safe
    di_sum = (plus_di + minus_di).replace(0.0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / di_sum
    adx = dx.ewm(alpha=1.0 / spec.adx_period, adjust=False, min_periods=spec.adx_period).mean()

    # Channel boundaries use only bars strictly before the signal bar.
    prior_upper = mid_high.shift(1).rolling(spec.breakout_lookback, min_periods=spec.breakout_lookback).max()
    prior_lower = mid_low.shift(1).rolling(spec.breakout_lookback, min_periods=spec.breakout_lookback).min()
    previous_upper = prior_upper.shift(1)
    previous_lower = prior_lower.shift(1)

    # Expansion compares current ATR to the median of the prior 96 completed ATR values.
    atr_baseline = atr.shift(1).rolling(spec.atr_baseline_lookback, min_periods=spec.atr_baseline_lookback).median()
    expansion_ratio = atr / atr_baseline.replace(0.0, np.nan)

    long_breakout = (mid_close > prior_upper) & (previous_close <= previous_upper)
    short_breakout = (mid_close < prior_lower) & (previous_close >= previous_lower)
    volatility_expansion = expansion_ratio >= spec.min_atr_expansion_ratio
    trend_strength = adx >= spec.min_adx

    long_signal = long_breakout & volatility_expansion & trend_strength & (plus_di > minus_di) & atr.gt(0.0)
    short_signal = short_breakout & volatility_expansion & trend_strength & (minus_di > plus_di) & atr.gt(0.0)

    frame["signal"] = np.select([long_signal, short_signal], [1, -1], default=0).astype(int)
    frame["atr"] = atr
    frame["adx"] = adx
    frame["plus_di"] = plus_di
    frame["minus_di"] = minus_di
    frame["atr_expansion_ratio"] = expansion_ratio
    frame["prior_upper"] = prior_upper
    frame["prior_lower"] = prior_lower
    frame["server_time"] = frame["timestamp"].dt.tz_convert(ZoneInfo(SERVER_TIMEZONE))
    frame["server_date"] = frame["server_time"].dt.date
    frame["server_hour"] = frame["server_time"].dt.hour
    return frame


def _summarize(trades: list[dict], risk_fraction: float) -> dict:
    if not trades:
        return {
            "trades": 0, "wins": 0, "losses": 0, "win_rate": None,
            "profit_factor": None, "expectancy_net_r": None, "total_net_r": 0.0,
            "max_drawdown_pct": 0.0, "all_trades_same_server_date": True,
            "all_trades_before_rollover": True,
        }
    net = np.asarray([float(t["net_r"]) for t in trades], dtype=float)
    wins, losses = float(net[net > 0].sum()), float(-net[net < 0].sum())
    equity = peak = 1.0
    max_dd = 0.0
    for value in net:
        equity *= max(0.0, 1.0 + value * risk_fraction)
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    return {
        "trades": len(trades),
        "wins": int((net > 0).sum()),
        "losses": int((net < 0).sum()),
        "win_rate": round(float((net > 0).mean()), 6),
        "profit_factor": round(wins / losses, 6) if losses > 0 else None,
        "expectancy_net_r": round(float(net.mean()), 8),
        "total_net_r": round(float(net.sum()), 8),
        "max_drawdown_pct": round(max_dd, 6),
        "all_trades_same_server_date": all(t["entry_server_date"] == t["exit_server_date"] for t in trades),
        "all_trades_before_rollover": all(t["exit_server_hour"] <= 22 for t in trades),
    }


def run_scenario(
    bars: pd.DataFrame,
    *,
    slippage_usd_per_oz_per_side: float,
    commission_usd_per_oz_round_turn: float = COMMISSION_FEE_USD_PER_OZ_ROUND_TURN,
    spec: VolatilityMomentumSpec = SPEC,
) -> dict:
    if not math.isfinite(slippage_usd_per_oz_per_side) or slippage_usd_per_oz_per_side < 0:
        raise G21Error("G21_SLIPPAGE_INVALID")
    if not math.isfinite(commission_usd_per_oz_round_turn) or commission_usd_per_oz_round_turn < 0:
        raise G21Error("G21_COMMISSION_INVALID")

    frame = make_signals(bars, spec)
    trades: list[dict] = []
    position = 0
    entry_i = -1
    entry_fill = stop = target = risk_distance = 0.0
    entry_day = None
    entry_hour = None

    def close(exit_i: int, raw_exit: float, exit_field: str, reason: str) -> None:
        nonlocal position, entry_i, entry_fill, stop, target, risk_distance, entry_day, entry_hour
        if position not in (-1, 1):
            raise G21Error("G21_POSITION_STATE_INVALID")
        is_close = exit_field.endswith("_close")
        exit_time = frame.at[exit_i, "timestamp"] + (pd.Timedelta(hours=1) if is_close else pd.Timedelta(0))
        exit_server = exit_time.tz_convert(ZoneInfo(SERVER_TIMEZONE))
        exit_day = exit_server.date()
        if exit_day != entry_day:
            raise G21Error("G21_OVERNIGHT_POSITION")
        if exit_server.hour > spec.flatten_server_hour:
            raise G21Error("G21_EXIT_AFTER_ROLLOVER_BUFFER")
        exit_fill = raw_exit - slippage_usd_per_oz_per_side if position == 1 else raw_exit + slippage_usd_per_oz_per_side
        gross_r = position * (exit_fill - entry_fill) / risk_distance
        financing = 0.0  # valid only because same-server-date/no-rollover is enforced
        net_r = gross_r - (commission_usd_per_oz_round_turn + financing) / risk_distance
        trades.append({
            "side": "LONG" if position == 1 else "SHORT",
            "entry_time_utc": frame.at[entry_i, "timestamp"].isoformat(),
            "exit_time_utc": exit_time.isoformat(),
            "exit_time_precision": "h1_bar_close" if is_close else "h1_bar_open_or_intrabar_limit_assumption",
            "entry_server_date": str(entry_day),
            "exit_server_date": str(exit_day),
            "entry_server_hour": int(entry_hour),
            "exit_server_hour": int(exit_server.hour),
            "entry_fill": round(entry_fill, 6),
            "exit_fill": round(exit_fill, 6),
            "stop": round(stop, 6),
            "target": round(target, 6),
            "exit_reason": reason,
            "exit_price_field": exit_field,
            "holding_bars": max(1, exit_i - entry_i + 1),
            "risk_distance_usd_per_oz": round(risk_distance, 6),
            "gross_r_after_bidask_slippage": round(gross_r, 8),
            "commission_fee_usd_per_oz_round_turn": round(commission_usd_per_oz_round_turn, 8),
            "financing_usd_per_oz": financing,
            "net_r": round(net_r, 8),
            "spread_double_charged": False,
            "intraday_no_rollover_rule_satisfied": True,
        })
        position = 0
        entry_i = -1
        entry_fill = stop = target = risk_distance = 0.0
        entry_day = None
        entry_hour = None

    for i in range(1, len(frame)):
        timestamp = frame.at[i, "timestamp"]
        server_day = frame.at[i, "server_date"]
        server_hour = int(frame.at[i, "server_hour"])
        gap_before = timestamp - frame.at[i - 1, "timestamp"]

        if position and server_day != entry_day:
            previous_i = i - 1
            field = "bid_close" if position == 1 else "ask_close"
            close(previous_i, float(frame.at[previous_i, field]), field, "server_date_guard")
            continue
        if position and gap_before > pd.Timedelta(hours=1):
            previous_i = i - 1
            field = "bid_close" if position == 1 else "ask_close"
            close(previous_i, float(frame.at[previous_i, field]), field, "data_gap_flatten")
            continue
        if position and server_hour >= spec.flatten_server_hour:
            field = "bid_open" if position == 1 else "ask_open"
            close(i, float(frame.at[i, field]), field, "pre_rollover_flatten")
            continue

        exited_this_bar = False
        if position:
            if position == 1:
                op, hi, lo = (float(frame.at[i, key]) for key in ("bid_open", "bid_high", "bid_low"))
                field = "bid_open"
                stop_gap, target_gap = op <= stop, op >= target
                hit_stop, hit_target = lo <= stop, hi >= target
            else:
                op, hi, lo = (float(frame.at[i, key]) for key in ("ask_open", "ask_high", "ask_low"))
                field = "ask_open"
                stop_gap, target_gap = op >= stop, op <= target
                hit_stop, hit_target = hi >= stop, lo <= target
            age = i - entry_i + 1
            if stop_gap:
                close(i, op, field, "stop_gap_open")
                exited_this_bar = True
            elif target_gap:
                close(i, target, "target_limit", "target_gap_open")
                exited_this_bar = True
            elif hit_stop and hit_target:
                close(i, stop, "stop", "same_bar_stop_first")
                exited_this_bar = True
            elif hit_stop:
                close(i, stop, "stop", "stop")
                exited_this_bar = True
            elif hit_target:
                close(i, target, "target_limit", "target")
                exited_this_bar = True
            elif age >= spec.max_holding_bars:
                close_field = "bid_close" if position == 1 else "ask_close"
                close(i, float(frame.at[i, close_field]), close_field, "time_stop_close")
                exited_this_bar = True

        if position == 0 and not exited_this_bar:
            signal_i = i - 1
            signal_day = frame.at[signal_i, "server_date"]
            if signal_day != server_day or gap_before != pd.Timedelta(hours=1):
                continue
            if not (spec.first_entry_server_hour <= server_hour <= spec.last_entry_server_hour):
                continue
            signal = int(frame.at[signal_i, "signal"])
            signal_atr = frame.at[signal_i, "atr"]
            if signal not in (-1, 1) or not np.isfinite(signal_atr) or float(signal_atr) <= 0.0:
                continue
            position = signal
            entry_i = i
            entry_day = server_day
            entry_hour = server_hour
            risk_distance = spec.stop_atr_multiple * float(signal_atr)
            if position == 1:
                entry_fill = float(frame.at[i, "ask_open"]) + slippage_usd_per_oz_per_side
                stop = entry_fill - risk_distance
                target = entry_fill + spec.target_r_multiple * risk_distance
                op, hi, lo = (float(frame.at[i, key]) for key in ("bid_open", "bid_high", "bid_low"))
                field = "bid_open"
                stop_gap, target_gap = op <= stop, op >= target
                hit_stop, hit_target = lo <= stop, hi >= target
            else:
                entry_fill = float(frame.at[i, "bid_open"]) - slippage_usd_per_oz_per_side
                stop = entry_fill + risk_distance
                target = entry_fill - spec.target_r_multiple * risk_distance
                op, hi, lo = (float(frame.at[i, key]) for key in ("ask_open", "ask_high", "ask_low"))
                field = "ask_open"
                stop_gap, target_gap = op >= stop, op <= target
                hit_stop, hit_target = hi >= stop, lo <= target
            if stop_gap:
                close(i, op, field, "entry_bar_stop_gap")
                exited_this_bar = True
            elif target_gap:
                close(i, target, "target_limit", "entry_bar_target_gap")
                exited_this_bar = True
            elif hit_stop and hit_target:
                close(i, stop, "stop", "entry_bar_same_bar_stop_first")
                exited_this_bar = True
            elif hit_stop:
                close(i, stop, "stop", "entry_bar_stop")
                exited_this_bar = True
            elif hit_target:
                close(i, target, "target_limit", "entry_bar_target")
                exited_this_bar = True

        if position and i + 1 < len(frame):
            next_gap = frame.at[i + 1, "timestamp"] - timestamp
            if next_gap > pd.Timedelta(hours=1):
                close_field = "bid_close" if position == 1 else "ask_close"
                close(i, float(frame.at[i, close_field]), close_field, "data_gap_flatten")

    if position:
        last_i = len(frame) - 1
        field = "bid_close" if position == 1 else "ask_close"
        close(last_i, float(frame.at[last_i, field]), field, "end_of_data_flatten")

    yearly = {
        str(year): _summarize(
            [t for t in trades if pd.Timestamp(t["entry_time_utc"]).year == year], spec.risk_fraction
        )
        for year in (2021, 2022, 2023, 2024)
    }
    discovery = [t for t in trades if pd.Timestamp(t["entry_time_utc"]).year in DISCOVERY_YEARS]
    validation = [t for t in trades if pd.Timestamp(t["entry_time_utc"]).year == VALIDATION_YEAR]
    return {
        "slippage_usd_per_oz_per_side": slippage_usd_per_oz_per_side,
        "commission_fee_usd_per_oz_round_turn": commission_usd_per_oz_round_turn,
        "financing_usd_per_oz": 0.0,
        "server_timezone_model": SERVER_TIMEZONE,
        "entry_server_hours": [spec.first_entry_server_hour, spec.last_entry_server_hour],
        "flatten_server_hour": spec.flatten_server_hour,
        "yearly": yearly,
        "discovery_2021_2023": _summarize(discovery, spec.risk_fraction),
        "validation_2024": _summarize(validation, spec.risk_fraction),
        "trades": trades,
    }


def evaluate_gate(scenarios: list[dict]) -> dict:
    checks = []
    for index, scenario in enumerate(scenarios, 1):
        discovery = scenario["discovery_2021_2023"]
        validation = scenario["validation_2024"]
        checks.append({
            "scenario": index,
            "discovery_min_100_trades": discovery["trades"] >= 100,
            "discovery_positive_expectancy": discovery["expectancy_net_r"] is not None and discovery["expectancy_net_r"] > 0,
            "discovery_pf_at_least_1_10": discovery["profit_factor"] is not None and discovery["profit_factor"] >= 1.10,
            "validation_min_30_trades": validation["trades"] >= 30,
            "validation_positive_expectancy": validation["expectancy_net_r"] is not None and validation["expectancy_net_r"] > 0,
            "validation_pf_above_1": validation["profit_factor"] is not None and validation["profit_factor"] > 1.0,
            "no_overnight_positions": all(t["intraday_no_rollover_rule_satisfied"] for t in scenario["trades"]),
        })
    passed = bool(checks) and all(all(check.values()) for check in checks)
    return {
        "status": "RESEARCH_SCREEN_PASS" if passed else "NO_GO_FIXED_VOLATILITY_MOMENTUM",
        "all_scenarios_pass": passed,
        "checks": checks,
        "criteria_pre_registered_before_run": True,
        "2024_used_for_parameter_selection": False,
    }


def run_research(data_path: str | Path, manifest_path: str | Path, output_path: str | Path) -> dict:
    bars = load_qualified_dataset(data_path, manifest_path)
    scenarios = [run_scenario(bars, slippage_usd_per_oz_per_side=value) for value in SLIPPAGE_SCENARIOS]
    decision = evaluate_gate(scenarios)
    report = {
        "schema": "forexai.g21.xauusd_volatility_momentum.v1",
        "status": decision["status"],
        "data": {
            "source": "Dukascopy real paired XAUUSD H1 BID/ASK",
            "rows": len(bars),
            "data_sha256": EXPECTED_DATA_SHA256,
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "years": [2021, 2022, 2023, 2024],
            "synthetic_data": False,
            "filled_bars": 0,
            "2025_loaded": False,
        },
        "broker_cost_inputs": {
            "broker": "WM Markets Ltd / WMMarkets-Demo",
            "account_currency": "USD",
            "contract_size_oz_per_lot": 100.0,
            "commission_fee_usd_per_oz_round_turn": COMMISSION_FEE_USD_PER_OZ_ROUND_TURN,
            "commission_fee_usd_per_lot_round_turn": 8.0,
            "closed_position_sample_count": 99,
            "sample_total_round_turn_lots": 1.08,
            "current_swap_long_usd_per_lot_per_rollover": -37.20,
            "current_swap_short_usd_per_lot_per_rollover": 21.15,
            "historical_financing_schedule_available": False,
        },
        "strategy_spec": {
            **SPEC.__dict__,
            "strategy": "H1 20-bar Donchian close breakout + ATR14 expansion >= 1.15x prior 96-ATR median + ADX14 >= 18 + directional DI",
            "signal_timing": "closed H1 bar; next consecutive H1 open entry",
            "stop": "1.75 x ATR14",
            "target": "2.5R",
            "max_holding_bars": SPEC.max_holding_bars,
            "discovery_years": list(DISCOVERY_YEARS),
            "validation_year": VALIDATION_YEAR,
        },
        "cost_policy": {
            "native_bid_ask_used": True,
            "spread_double_charged": False,
            "historical_spread_source": "Dukascopy; not WM Markets historical account quotes",
            "commission_observed_from_demo_closed_positions": True,
            "slippage_scenarios_usd_per_oz_per_side": list(SLIPPAGE_SCENARIOS),
            "slippage_values_are_stress_assumptions_not_observed": True,
            "financing_zero_only_under_same_server_date_flat_rule": True,
            "server_timezone_model": SERVER_TIMEZONE,
            "flatten_server_hour": SPEC.flatten_server_hour,
            "data_gap_flatten": True,
        },
        "gate": decision,
        "scenarios": scenarios,
        "backtest_scope": "research-only diagnostic; no order submission; no Demo/Live authorization",
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G21 fixed XAUUSD H1 volatility-momentum screen")
    parser.add_argument("--data", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", default="artifacts/g21-xauusd-volatility-momentum-report.json")
    args = parser.parse_args(argv)
    report = run_research(args.data, args.manifest, args.output)
    print(json.dumps({
        "status": report["status"],
        "rows": report["data"]["rows"],
        "scenarios": [{
            "slippage": s["slippage_usd_per_oz_per_side"],
            "discovery": s["discovery_2021_2023"],
            "validation": s["validation_2024"],
        } for s in report["scenarios"]],
        "gate": report["gate"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
