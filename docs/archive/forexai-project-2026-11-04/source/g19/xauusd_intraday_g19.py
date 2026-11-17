"""Pre-registered G19 XAUUSD H1 intraday trend-pullback research.

Research only. Uses the immutable G18 Dukascopy BID/ASK dataset, WM Markets
Demo account's observed round-turn commission/fee sample, and explicitly
labelled slippage stress cases. Every position is flattened before the broker
server rollover and at data gaps; no financing cost is inferred or charged.
No broker orders are sent.
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
SERVER_TIMEZONE = "Europe/Athens"  # WM Markets publishes UTC+2 winter / UTC+3 summer.
COMMISSION_USD_PER_OZ_ROUND_TURN = 0.08  # Derived from 99 closed Demo positions.
DISCOVERY_YEARS = (2021, 2022, 2023)
VALIDATION_YEAR = 2024


class G19Error(RuntimeError):
    """Raised when immutable data or intraday execution constraints fail."""


@dataclass(frozen=True)
class StrategySpec:
    ema_pullback: int = 20
    ema_regime: int = 50
    ema_trend: int = 200
    rsi_period: int = 14
    rsi_long_min: float = 52.0
    rsi_short_max: float = 48.0
    atr_period: int = 14
    atr_stop_multiple: float = 1.5
    reward_risk: float = 2.0
    max_holding_bars: int = 8
    first_server_hour: int = 2
    last_entry_server_hour: int = 22
    flatten_server_hour: int = 23
    risk_fraction: float = 0.0025


SPEC = StrategySpec()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_qualified_dataset(data_path: str | Path, manifest_path: str | Path) -> pd.DataFrame:
    data_path, manifest_path = Path(data_path), Path(manifest_path)
    if _sha256(data_path) != EXPECTED_DATA_SHA256:
        raise G19Error("G19_DATA_SHA256_DOES_NOT_MATCH_FROZEN_G18_DATASET")
    if _sha256(manifest_path) != EXPECTED_MANIFEST_SHA256:
        raise G19Error("G19_MANIFEST_SHA256_DOES_NOT_MATCH_FROZEN_G18_MANIFEST")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "schema": "forexai.real_data.xauusd_bidask_h1.v1",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "data_sha256": EXPECTED_DATA_SHA256,
        "synthetic_data": False,
        "backtest_run": False,
    }
    for key, value in required.items():
        if manifest.get(key) != value:
            raise G19Error(f"G19_MANIFEST_FIELD_MISMATCH:{key}")
    if manifest.get("source") != "Dukascopy historical BID/ASK BI5 bars":
        raise G19Error("G19_SOURCE_NOT_DUKASCOPY_BIDASK")
    frame = pd.read_csv(data_path)
    if len(frame) != EXPECTED_ROWS:
        raise G19Error("G19_ROW_COUNT_MISMATCH")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    if frame["timestamp"].duplicated().any() or not frame["timestamp"].is_monotonic_increasing:
        raise G19Error("G19_TIMESTAMP_SEQUENCE_INVALID")
    if set(frame["timestamp"].dt.year.unique()) != {2021, 2022, 2023, 2024}:
        raise G19Error("G19_YEAR_SCOPE_INVALID")
    if (frame[["spread_open", "spread_close"]] < 0).any().any():
        raise G19Error("G19_NEGATIVE_SPREAD")
    for point in ("open", "close"):
        if not np.allclose(
            frame[f"spread_{point}"].to_numpy(dtype=float),
            frame[f"ask_{point}"].to_numpy(dtype=float) - frame[f"bid_{point}"].to_numpy(dtype=float),
            atol=1e-9,
            rtol=0.0,
        ):
            raise G19Error(f"G19_SPREAD_RECONCILIATION_FAILED:{point}")
    return frame


def make_signals(bars: pd.DataFrame, spec: StrategySpec = SPEC) -> pd.DataFrame:
    """Create causal, close-of-bar EMA-regime / EMA20-pullback signals."""
    frame = bars.copy().reset_index(drop=True)
    mid_close = (frame["bid_close"].astype(float) + frame["ask_close"].astype(float)) / 2.0
    mid_high = (frame["bid_high"].astype(float) + frame["ask_high"].astype(float)) / 2.0
    mid_low = (frame["bid_low"].astype(float) + frame["ask_low"].astype(float)) / 2.0

    ema_pullback = mid_close.ewm(span=spec.ema_pullback, adjust=False, min_periods=spec.ema_pullback).mean()
    ema_regime = mid_close.ewm(span=spec.ema_regime, adjust=False, min_periods=spec.ema_regime).mean()
    ema_trend = mid_close.ewm(span=spec.ema_trend, adjust=False, min_periods=spec.ema_trend).mean()

    delta = mid_close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    avg_gain = gains.ewm(alpha=1.0 / spec.rsi_period, adjust=False, min_periods=spec.rsi_period).mean()
    avg_loss = losses.ewm(alpha=1.0 / spec.rsi_period, adjust=False, min_periods=spec.rsi_period).mean()
    relative_strength = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + relative_strength))
    rsi = rsi.where(avg_loss.ne(0.0), 100.0)

    previous_close = mid_close.shift(1)
    true_range = pd.concat(
        [mid_high - mid_low, (mid_high - previous_close).abs(), (mid_low - previous_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = true_range.ewm(alpha=1.0 / spec.atr_period, adjust=False, min_periods=spec.atr_period).mean()

    prior_timestamp = frame["timestamp"].shift(1)
    consecutive = (frame["timestamp"] - prior_timestamp) == pd.Timedelta(hours=1)
    cross_up = (mid_close.shift(1) <= ema_pullback.shift(1)) & (mid_close > ema_pullback)
    cross_down = (mid_close.shift(1) >= ema_pullback.shift(1)) & (mid_close < ema_pullback)

    long_signal = (
        consecutive
        & (ema_regime > ema_trend)
        & cross_up
        & (rsi >= spec.rsi_long_min)
        & atr.gt(0)
    )
    short_signal = (
        consecutive
        & (ema_regime < ema_trend)
        & cross_down
        & (rsi <= spec.rsi_short_max)
        & atr.gt(0)
    )
    frame["signal"] = np.select([long_signal, short_signal], [1, -1], default=0).astype(int)
    frame["ATR"] = atr
    frame["mid_close"] = mid_close
    frame["server_time"] = frame["timestamp"].dt.tz_convert(ZoneInfo(SERVER_TIMEZONE))
    frame["server_date"] = frame["server_time"].dt.date
    frame["server_hour"] = frame["server_time"].dt.hour
    return frame


def _metrics(rows: list[dict], *, risk_fraction: float) -> dict:
    if not rows:
        return {
            "trades": 0, "wins": 0, "losses": 0, "win_rate": None,
            "profit_factor": None, "expectancy_net_r": None, "total_net_r": 0.0,
            "max_drawdown_pct": 0.0, "all_trades_same_server_date": True,
            "all_trades_flat_before_rollover": True,
        }
    net = np.asarray([float(r["net_r"]) for r in rows], dtype=float)
    gains = float(net[net > 0].sum())
    losses = float(-net[net < 0].sum())
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for value in net:
        equity *= max(0.0, 1.0 + value * risk_fraction)
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    return {
        "trades": len(rows),
        "wins": int((net > 0).sum()),
        "losses": int((net < 0).sum()),
        "win_rate": round(float((net > 0).mean()), 6),
        "profit_factor": round(gains / losses, 6) if losses > 0 else None,
        "expectancy_net_r": round(float(net.mean()), 8),
        "total_net_r": round(float(net.sum()), 8),
        "max_drawdown_pct": round(max_dd, 6),
        "all_trades_same_server_date": all(r["entry_server_date"] == r["exit_server_date"] for r in rows),
        "all_trades_flat_before_rollover": all(r["exit_server_hour"] <= 23 for r in rows),
    }


def run_intraday_scenario(
    bars: pd.DataFrame,
    *,
    slippage_usd_per_oz_per_side: float,
    commission_usd_per_oz_round_turn: float = COMMISSION_USD_PER_OZ_ROUND_TURN,
    spec: StrategySpec = SPEC,
) -> dict:
    """Run one conservative H1 BID/ASK scenario with strict intraday flattening."""
    if not math.isfinite(slippage_usd_per_oz_per_side) or slippage_usd_per_oz_per_side < 0:
        raise G19Error("G19_SLIPPAGE_INPUT_INVALID")
    if not math.isfinite(commission_usd_per_oz_round_turn) or commission_usd_per_oz_round_turn < 0:
        raise G19Error("G19_COMMISSION_INPUT_INVALID")

    frame = make_signals(bars, spec)
    rows: list[dict] = []
    position = 0
    entry_idx = -1
    entry_fill = stop = target = risk_distance = 0.0
    entry_date = None
    entry_server_hour = None

    def close_position(exit_idx: int, raw_exit: float, reason: str, exit_field: str) -> None:
        nonlocal position, entry_idx, entry_fill, stop, target, risk_distance
        nonlocal entry_date, entry_server_hour
        if position not in (-1, 1):
            raise G19Error("G19_INTERNAL_POSITION_STATE_INVALID")
        bar_open_time = frame.at[exit_idx, "timestamp"]
        is_bar_close = exit_field.endswith("_close")
        actual_exit_time = bar_open_time + pd.Timedelta(hours=1) if is_bar_close else bar_open_time
        exit_server = actual_exit_time.tz_convert(ZoneInfo(SERVER_TIMEZONE))
        exit_date = exit_server.date()
        if exit_date != entry_date:
            raise G19Error("G19_OVERNIGHT_POSITION_DETECTED")
        if int(exit_server.hour) > spec.flatten_server_hour:
            raise G19Error("G19_POSITION_CLOSED_AFTER_ROLLOVER_BUFFER")
        exit_fill = raw_exit - slippage_usd_per_oz_per_side if position == 1 else raw_exit + slippage_usd_per_oz_per_side
        gross_r = position * (exit_fill - entry_fill) / risk_distance
        financing_usd_per_oz = 0.0
        net_r = gross_r - (commission_usd_per_oz_round_turn + financing_usd_per_oz) / risk_distance
        rows.append({
            "side": "LONG" if position == 1 else "SHORT",
            "entry_time_utc": frame.at[entry_idx, "timestamp"].isoformat(),
            "exit_time_utc": actual_exit_time.isoformat(),
            "exit_time_precision": "h1_bar_close" if is_bar_close else ("h1_bar_interval_unknown" if exit_field in {"stop", "target_limit"} else "h1_bar_open"),
            "entry_server_date": str(entry_date),
            "exit_server_date": str(exit_date),
            "entry_server_hour": int(entry_server_hour),
            "exit_server_hour": int(exit_server.hour),
            "entry_fill": round(entry_fill, 6),
            "exit_fill": round(exit_fill, 6),
            "exit_reason": reason,
            "exit_price_field": exit_field,
            "holding_bars": max(1, exit_idx - entry_idx + 1),
            "risk_distance_usd_per_oz": round(risk_distance, 6),
            "gross_r_after_bidask_slippage": round(gross_r, 8),
            "commission_usd_per_oz_round_turn": round(commission_usd_per_oz_round_turn, 8),
            "financing_usd_per_oz": financing_usd_per_oz,
            "net_r": round(net_r, 8),
            "spread_double_charged": False,
            "intraday_no_rollover_rule_satisfied": True,
        })
        position = 0
        entry_idx = -1
        entry_fill = stop = target = risk_distance = 0.0
        entry_date = None
        entry_server_hour = None

    for i in range(1, len(frame)):
        ts = frame.at[i, "timestamp"]
        server = frame.at[i, "server_time"]
        server_date = server.date()
        server_hour = int(server.hour)
        gap_before = ts - frame.at[i - 1, "timestamp"]

        if position and server_date != entry_date:
            previous_idx = i - 1
            previous_field = "bid_close" if position == 1 else "ask_close"
            close_position(previous_idx, float(frame.at[previous_idx, previous_field]), "server_date_guard", previous_field)
            continue

        if position and server_hour >= spec.flatten_server_hour:
            open_field = "bid_open" if position == 1 else "ask_open"
            close_position(i, float(frame.at[i, open_field]), "pre_rollover_flatten", open_field)
            continue

        if position and gap_before > pd.Timedelta(hours=1):
            previous_field = "bid_close" if position == 1 else "ask_close"
            close_position(i - 1, float(frame.at[i - 1, previous_field]), "data_gap_flatten", previous_field)
            continue

        exited_this_bar = False
        if position:
            if position == 1:
                op, hi, lo = (float(frame.at[i, key]) for key in ("bid_open", "bid_high", "bid_low"))
                stop_open, target_open = op <= stop, op >= target
                hit_stop, hit_target = lo <= stop, hi >= target
                open_field = "bid_open"
            else:
                op, hi, lo = (float(frame.at[i, key]) for key in ("ask_open", "ask_high", "ask_low"))
                stop_open, target_open = op >= stop, op <= target
                hit_stop, hit_target = hi >= stop, lo <= target
                open_field = "ask_open"

            age = i - entry_idx + 1
            if stop_open:
                close_position(i, op, "stop_gap_open", open_field)
                exited_this_bar = True
            elif target_open:
                close_position(i, target, "target_gap_open", "target_limit")
                exited_this_bar = True
            elif hit_stop and hit_target:
                close_position(i, stop, "same_bar_stop_first", "stop")
                exited_this_bar = True
            elif hit_stop:
                close_position(i, stop, "stop", "stop")
                exited_this_bar = True
            elif hit_target:
                close_position(i, target, "target", "target_limit")
                exited_this_bar = True
            elif age >= spec.max_holding_bars:
                close_key = "bid_close" if position == 1 else "ask_close"
                close_position(i, float(frame.at[i, close_key]), "time_stop_close", close_key)
                exited_this_bar = True
            elif int(frame.at[i, "signal"]) == -position:
                close_key = "bid_close" if position == 1 else "ask_close"
                close_position(i, float(frame.at[i, close_key]), "opposite_signal_close", close_key)
                exited_this_bar = True

        if position == 0 and not exited_this_bar:
            previous_signal = int(frame.at[i - 1, "signal"])
            previous_atr = frame.at[i - 1, "ATR"]
            is_consecutive = gap_before == pd.Timedelta(hours=1)
            permitted_hour = spec.first_server_hour <= server_hour <= spec.last_entry_server_hour
            if is_consecutive and permitted_hour and previous_signal in (-1, 1) and np.isfinite(previous_atr) and float(previous_atr) > 0:
                position = previous_signal
                entry_idx = i
                entry_date = server_date
                entry_server_hour = server_hour
                risk_distance = spec.atr_stop_multiple * float(previous_atr)
                if position == 1:
                    entry_fill = float(frame.at[i, "ask_open"]) + slippage_usd_per_oz_per_side
                else:
                    entry_fill = float(frame.at[i, "bid_open"]) - slippage_usd_per_oz_per_side
                stop = entry_fill - position * risk_distance
                target = entry_fill + position * spec.reward_risk * risk_distance

                if position == 1:
                    op, hi, lo = (float(frame.at[i, key]) for key in ("bid_open", "bid_high", "bid_low"))
                    stop_open, target_open = op <= stop, op >= target
                    hit_stop, hit_target = lo <= stop, hi >= target
                    open_field = "bid_open"
                else:
                    op, hi, lo = (float(frame.at[i, key]) for key in ("ask_open", "ask_high", "ask_low"))
                    stop_open, target_open = op >= stop, op <= target
                    hit_stop, hit_target = hi >= stop, lo <= target
                    open_field = "ask_open"
                if stop_open:
                    close_position(i, op, "entry_bar_stop_gap", open_field)
                elif target_open:
                    close_position(i, target, "entry_bar_target_gap", "target_limit")
                elif hit_stop and hit_target:
                    close_position(i, stop, "entry_bar_same_bar_stop_first", "stop")
                elif hit_stop:
                    close_position(i, stop, "entry_bar_stop", "stop")
                elif hit_target:
                    close_position(i, target, "entry_bar_target", "target_limit")

        if position and i + 1 < len(frame):
            next_gap = frame.at[i + 1, "timestamp"] - ts
            if next_gap > pd.Timedelta(hours=1):
                close_key = "bid_close" if position == 1 else "ask_close"
                close_position(i, float(frame.at[i, close_key]), "data_gap_flatten", close_key)

    if position:
        i = len(frame) - 1
        close_key = "bid_close" if position == 1 else "ask_close"
        close_position(i, float(frame.at[i, close_key]), "end_of_data_flatten", close_key)

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        year = str(pd.Timestamp(row["entry_time_utc"]).year)
        grouped.setdefault(year, []).append(row)
    yearly = {year: _metrics(items, risk_fraction=spec.risk_fraction) for year, items in sorted(grouped.items())}
    discovery_trades = [r for r in rows if int(pd.Timestamp(r["entry_time_utc"]).year) in DISCOVERY_YEARS]
    validation_trades = [r for r in rows if int(pd.Timestamp(r["entry_time_utc"]).year) == VALIDATION_YEAR]
    discovery = _metrics(discovery_trades, risk_fraction=spec.risk_fraction)
    validation = _metrics(validation_trades, risk_fraction=spec.risk_fraction)
    return {
        "slippage_usd_per_oz_per_side": slippage_usd_per_oz_per_side,
        "commission_usd_per_oz_round_turn": commission_usd_per_oz_round_turn,
        "financing_usd_per_oz": 0.0,
        "financing_zero_basis": "all positions are force-closed on the same WM Markets server date before the rollover buffer; no overnight carry is modelled",
        "server_timezone_model": SERVER_TIMEZONE,
        "server_utc_offsets_expected": [2, 3],
        "entry_hours_server_inclusive": [spec.first_server_hour, spec.last_entry_server_hour],
        "flatten_server_hour": spec.flatten_server_hour,
        "yearly": yearly,
        "discovery_2021_2023": discovery,
        "validation_2024": validation,
        "trades": rows,
    }


def evaluate_gate(scenarios: list[dict]) -> dict:
    """Apply fixed pre-registered research criteria; no parameter selection."""
    checks: list[dict] = []
    for index, scenario in enumerate(scenarios, start=1):
        isr = scenario["discovery_2021_2023"]
        oos = scenario["validation_2024"]
        checks.append({
            "scenario": index,
            "discovery_min_100_trades": isr["trades"] >= 100,
            "discovery_positive_expectancy": isr["expectancy_net_r"] is not None and isr["expectancy_net_r"] > 0,
            "discovery_pf_at_least_1_10": isr["profit_factor"] is not None and isr["profit_factor"] >= 1.10,
            "validation_min_30_trades": oos["trades"] >= 30,
            "validation_positive_expectancy": oos["expectancy_net_r"] is not None and oos["expectancy_net_r"] > 0,
            "validation_pf_above_1": oos["profit_factor"] is not None and oos["profit_factor"] > 1.0,
            "no_overnight_positions": all(t["intraday_no_rollover_rule_satisfied"] for t in scenario["trades"]),
        })
    all_pass = bool(checks) and all(all(item.values()) for item in checks)
    return {
        "status": "RESEARCH_SCREEN_PASS" if all_pass else "NO_GO_FIXED_INTRADAY_SCREEN",
        "all_slippage_scenarios_pass": all_pass,
        "checks": checks,
        "criteria_pre_registered_before_run": True,
        "2024_used_for_parameter_selection": False,
    }


def run_research(data_path: str | Path, manifest_path: str | Path, output_path: str | Path) -> dict:
    frame = load_qualified_dataset(data_path, manifest_path)
    slippage_scenarios = (0.05, 0.10, 0.20)
    scenarios = [run_intraday_scenario(frame, slippage_usd_per_oz_per_side=value) for value in slippage_scenarios]
    gate = evaluate_gate(scenarios)
    report = {
        "schema": "forexai.g19.xauusd_intraday_trend_pullback.v1",
        "status": gate["status"],
        "data": {
            "source": "Dukascopy real paired XAUUSD H1 BID/ASK",
            "data_sha256": EXPECTED_DATA_SHA256,
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "rows": len(frame),
            "years": [2021, 2022, 2023, 2024],
            "synthetic_data": False,
            "filled_bars": 0,
            "2025_loaded": False,
        },
        "broker_cost_inputs": {
            "broker": "WM Markets Ltd / WMMarkets-Demo",
            "account_currency": "USD",
            "contract_size_oz_per_lot": 100.0,
            "commission_fee_usd_per_oz_round_turn": COMMISSION_USD_PER_OZ_ROUND_TURN,
            "commission_fee_usd_per_lot_round_turn": COMMISSION_USD_PER_OZ_ROUND_TURN * 100.0,
            "closed_position_sample_count": 99,
            "sample_total_round_turn_lots": 1.08,
            "realized_swap_cost_per_oz_mean": 0.0,
            "swap_mode": "POINTS",
            "current_swap_long_usd_per_lot_per_rollover": -37.20,
            "current_swap_short_usd_per_lot_per_rollover": 21.15,
            "triple_rollover_weekday": "Wednesday",
            "current_mt5_spread_snapshot_points": 15,
            "current_mt5_spread_snapshot_usd_per_oz": 0.15,
            "current_mt5_spread_is_floating": True,
            "terminal_trade_allowed": False,
            "symbol_trade_mode": 4,
            "current_swap_terms_are_not_historical_schedule": True,
        },
        "strategy_spec": {
            **SPEC.__dict__,
            "strategy": "H1 EMA50/EMA200 regime + EMA20 pullback recross + RSI14 filter",
            "signal_timing": "closed H1 bar, execute next bar open",
            "stop": "1.5 * ATR14",
            "target": "2.0R",
            "max_holding_bars": SPEC.max_holding_bars,
            "discovery_years": list(DISCOVERY_YEARS),
            "validation_year": VALIDATION_YEAR,
        },
        "cost_policy": {
            "observed_bid_ask_spread_paid_once_in_quotes": True,
            "spread_history_source": "Dukascopy; not historical WM Markets account quotes",
            "spread_history_is_target_broker_exact": False,
            "current_wm_mt5_spread_snapshot_usd_per_oz": 0.15,
            "extra_spread_charge": 0.0,
            "commission_inferred": False,
            "commission_observed_from_demo_closed_positions": True,
            "slippage_scenarios_usd_per_oz_per_side": list(slippage_scenarios),
            "slippage_values_are_stress_assumptions_not_observed": True,
            "financing_charge": 0.0,
            "financing_zero_only_under_enforced_same_server_day_flat_rule": True,
            "server_time_zone_model": SERVER_TIMEZONE,
            "flatten_buffer_hours_before_rollover": 1,
            "entry_disabled_server_hours": [0, 1, 23],
            "positions_carried_across_data_gaps": False,
        },
        "gate": gate,
        "scenarios": scenarios,
        "backtest_scope": "research only; no order submission, Demo/Live authorization, or production EA change",
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run preregistered G19 intraday XAUUSD research")
    parser.add_argument("--data", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", default="artifacts/g19-xauusd-intraday-report.json")
    args = parser.parse_args(argv)
    report = run_research(args.data, args.manifest, args.output)
    print(json.dumps({
        "status": report["status"],
        "data_rows": report["data"]["rows"],
        "commission_usd_per_oz_round_turn": report["broker_cost_inputs"]["commission_fee_usd_per_oz_round_turn"],
        "discovery": [scenario["discovery_2021_2023"] for scenario in report["scenarios"]],
        "validation_2024": [scenario["validation_2024"] for scenario in report["scenarios"]],
        "gate": report["gate"],
        "output": str(args.output),
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
