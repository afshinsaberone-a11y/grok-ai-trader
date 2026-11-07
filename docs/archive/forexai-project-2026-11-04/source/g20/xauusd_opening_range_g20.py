"""G20 XAUUSD H1 opening-range breakout research, preregistered and research-only.

Uses the frozen G18 real paired BID/ASK data, Demo-observed round-turn fee sample,
and declared slippage stress assumptions. Positions are closed on the same broker
server date and before the rollover buffer. No MT5 orders are sent.
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
COMMISSION_USD_PER_OZ_ROUND_TURN = 0.08
DISCOVERY_YEARS = (2021, 2022, 2023)
VALIDATION_YEAR = 2024


class G20Error(RuntimeError):
    """Raised when the frozen data or execution constraints fail."""


@dataclass(frozen=True)
class OpeningRangeSpec:
    range_start_hour_server: int = 0
    range_last_hour_server: int = 6
    first_breakout_bar_hour_server: int = 7
    last_breakout_bar_hour_server: int = 18
    first_entry_hour_server: int = 8
    last_entry_hour_server: int = 19
    flatten_hour_server: int = 23
    target_r_multiple: float = 1.5
    max_holding_bars: int = 8
    risk_fraction: float = 0.0025


SPEC = OpeningRangeSpec()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_qualified_dataset(data_path: str | Path, manifest_path: str | Path) -> pd.DataFrame:
    data_path, manifest_path = Path(data_path), Path(manifest_path)
    if _sha256(data_path) != EXPECTED_DATA_SHA256:
        raise G20Error("G20_DATA_SHA256_MISMATCH")
    if _sha256(manifest_path) != EXPECTED_MANIFEST_SHA256:
        raise G20Error("G20_MANIFEST_SHA256_MISMATCH")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "schema": "forexai.real_data.xauusd_bidask_h1.v1",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "data_sha256": EXPECTED_DATA_SHA256,
        "rows": EXPECTED_ROWS,
        "synthetic_data": False,
        "backtest_run": False,
    }
    for key, value in required.items():
        if manifest.get(key) != value:
            raise G20Error(f"G20_MANIFEST_FIELD_MISMATCH:{key}")
    if manifest.get("source") != "Dukascopy historical BID/ASK BI5 bars":
        raise G20Error("G20_SOURCE_MISMATCH")
    frame = pd.read_csv(data_path)
    if len(frame) != EXPECTED_ROWS:
        raise G20Error("G20_ROW_COUNT_MISMATCH")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    if frame["timestamp"].duplicated().any() or not frame["timestamp"].is_monotonic_increasing:
        raise G20Error("G20_TIMESTAMP_SEQUENCE_INVALID")
    if set(frame["timestamp"].dt.year.unique()) != {2021, 2022, 2023, 2024}:
        raise G20Error("G20_YEAR_SCOPE_INVALID")
    for side in ("bid", "ask"):
        for px in ("open", "high", "low", "close"):
            col = f"{side}_{px}"
            if not np.isfinite(frame[col].to_numpy(dtype=float)).all() or (frame[col] <= 0).any():
                raise G20Error(f"G20_PRICE_INVALID:{col}")
    if (frame[["spread_open", "spread_close"]] < 0).any().any():
        raise G20Error("G20_NEGATIVE_SPREAD")
    for point in ("open", "close"):
        if not np.allclose(
            frame[f"spread_{point}"].to_numpy(dtype=float),
            frame[f"ask_{point}"].to_numpy(dtype=float) - frame[f"bid_{point}"].to_numpy(dtype=float),
            atol=1e-9, rtol=0.0,
        ):
            raise G20Error(f"G20_SPREAD_RECONCILIATION_FAILED:{point}")
    return frame


def prepare_ranges(bars: pd.DataFrame, spec: OpeningRangeSpec = SPEC) -> pd.DataFrame:
    frame = bars.copy().reset_index(drop=True)
    frame["server_time"] = frame["timestamp"].dt.tz_convert(ZoneInfo(SERVER_TIMEZONE))
    frame["server_date"] = frame["server_time"].dt.date
    frame["server_hour"] = frame["server_time"].dt.hour
    # Mid-quote opening range; executable fills remain native ASK/BID.
    frame["mid_high"] = (frame["bid_high"].astype(float) + frame["ask_high"].astype(float)) / 2.0
    frame["mid_low"] = (frame["bid_low"].astype(float) + frame["ask_low"].astype(float)) / 2.0
    ranges: dict[object, tuple[float, float]] = {}
    required_hours = list(range(spec.range_start_hour_server, spec.range_last_hour_server + 1))
    for day, group in frame.groupby("server_date", sort=False):
        opening = group[group["server_hour"].isin(required_hours)].sort_values("server_time")
        if opening["server_hour"].tolist() != required_hours:
            continue
        timestamps = opening["timestamp"].tolist()
        if any(timestamps[i] - timestamps[i - 1] != pd.Timedelta(hours=1) for i in range(1, len(timestamps))):
            continue
        ranges[day] = (float(opening["mid_high"].max()), float(opening["mid_low"].min()))
    frame["range_high"] = frame["server_date"].map(lambda day: ranges.get(day, (np.nan, np.nan))[0])
    frame["range_low"] = frame["server_date"].map(lambda day: ranges.get(day, (np.nan, np.nan))[1])
    return frame


def _summarize(trades: list[dict], risk_fraction: float) -> dict:
    if not trades:
        return {
            "trades": 0, "wins": 0, "losses": 0, "win_rate": None,
            "profit_factor": None, "expectancy_net_r": None, "total_net_r": 0.0,
            "max_drawdown_pct": 0.0, "all_trades_same_server_date": True,
            "all_trades_before_rollover": True,
        }
    net = np.asarray([trade["net_r"] for trade in trades], dtype=float)
    gross_win = float(net[net > 0].sum())
    gross_loss = float(-net[net < 0].sum())
    equity = peak = 1.0
    max_dd = 0.0
    for value in net:
        equity *= max(0.0, 1.0 + value * risk_fraction)
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak * 100.0 if peak else 0.0)
    return {
        "trades": len(trades),
        "wins": int((net > 0).sum()),
        "losses": int((net < 0).sum()),
        "win_rate": round(float((net > 0).mean()), 6),
        "profit_factor": round(gross_win / gross_loss, 6) if gross_loss > 0 else None,
        "expectancy_net_r": round(float(net.mean()), 8),
        "total_net_r": round(float(net.sum()), 8),
        "max_drawdown_pct": round(max_dd, 6),
        "all_trades_same_server_date": all(
            trade["entry_server_date"] == trade["exit_server_date"] for trade in trades
        ),
        "all_trades_before_rollover": all(
            trade["exit_server_hour"] <= 23 for trade in trades
        ),
    }


def run_scenario(
    bars: pd.DataFrame,
    *,
    slippage_usd_per_oz_per_side: float,
    commission_usd_per_oz_round_turn: float = COMMISSION_USD_PER_OZ_ROUND_TURN,
    spec: OpeningRangeSpec = SPEC,
) -> dict:
    if not math.isfinite(slippage_usd_per_oz_per_side) or slippage_usd_per_oz_per_side < 0:
        raise G20Error("G20_SLIPPAGE_INVALID")
    if not math.isfinite(commission_usd_per_oz_round_turn) or commission_usd_per_oz_round_turn < 0:
        raise G20Error("G20_COMMISSION_INVALID")
    frame = prepare_ranges(bars, spec)
    trades: list[dict] = []
    position = 0
    entry_i = -1
    entry_fill = stop = target = risk_distance = 0.0
    entry_day = None
    entry_hour = None
    attempted_days: set[object] = set()

    def close(exit_i: int, raw_exit: float, exit_field: str, reason: str) -> None:
        nonlocal position, entry_i, entry_fill, stop, target, risk_distance, entry_day, entry_hour
        if position not in (-1, 1):
            raise G20Error("G20_POSITION_STATE_INVALID")
        is_bar_close = exit_field.endswith("_close")
        actual_exit_time = frame.at[exit_i, "timestamp"] + (
            pd.Timedelta(hours=1) if is_bar_close else pd.Timedelta(0)
        )
        exit_server = actual_exit_time.tz_convert(ZoneInfo(SERVER_TIMEZONE))
        exit_day = exit_server.date()
        if exit_day != entry_day:
            raise G20Error("G20_OVERNIGHT_POSITION")
        if exit_server.hour > spec.flatten_hour_server:
            raise G20Error("G20_AFTER_ROLLOVER_BUFFER")
        exit_fill = (
            raw_exit - slippage_usd_per_oz_per_side
            if position == 1
            else raw_exit + slippage_usd_per_oz_per_side
        )
        gross_r = position * (exit_fill - entry_fill) / risk_distance
        financing = 0.0  # Same server day and before rollover; no overnight carry.
        net_r = gross_r - (commission_usd_per_oz_round_turn + financing) / risk_distance
        trades.append({
            "side": "LONG" if position == 1 else "SHORT",
            "entry_time_utc": frame.at[entry_i, "timestamp"].isoformat(),
            "exit_time_utc": actual_exit_time.isoformat(),
            "exit_time_precision": (
                "h1_bar_close" if is_bar_close else "h1_bar_open_or_intrabar_limit_assumption"
            ),
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
        day = frame.at[i, "server_date"]
        hour = int(frame.at[i, "server_hour"])
        gap = timestamp - frame.at[i - 1, "timestamp"]

        if position and day != entry_day:
            previous_i = i - 1
            field = "bid_close" if position == 1 else "ask_close"
            close(previous_i, float(frame.at[previous_i, field]), field, "server_day_flatten")
            continue
        if position and gap > pd.Timedelta(hours=1):
            previous_i = i - 1
            field = "bid_close" if position == 1 else "ask_close"
            close(previous_i, float(frame.at[previous_i, field]), field, "data_gap_flatten")
            continue
        if position and hour >= spec.flatten_hour_server:
            field = "bid_open" if position == 1 else "ask_open"
            close(i, float(frame.at[i, field]), field, "pre_rollover_flatten")
            continue

        exited = False
        if position:
            if position == 1:
                op, high, low = (
                    float(frame.at[i, column]) for column in ("bid_open", "bid_high", "bid_low")
                )
                open_field = "bid_open"
                stop_gap, target_gap = op <= stop, op >= target
                hit_stop, hit_target = low <= stop, high >= target
            else:
                op, high, low = (
                    float(frame.at[i, column]) for column in ("ask_open", "ask_high", "ask_low")
                )
                open_field = "ask_open"
                stop_gap, target_gap = op >= stop, op <= target
                hit_stop, hit_target = high >= stop, low <= target
            age = i - entry_i + 1
            if stop_gap:
                close(i, op, open_field, "stop_gap_open")
                exited = True
            elif target_gap:
                close(i, target, "target_limit", "target_gap_open")
                exited = True
            elif hit_stop and hit_target:
                close(i, stop, "stop", "same_bar_stop_first")
                exited = True
            elif hit_stop:
                close(i, stop, "stop", "stop")
                exited = True
            elif hit_target:
                close(i, target, "target_limit", "target")
                exited = True
            elif age >= spec.max_holding_bars:
                field = "bid_close" if position == 1 else "ask_close"
                close(i, float(frame.at[i, field]), field, "time_stop_close")
                exited = True

        if not position and not exited:
            # The signal is evaluated only after the previous H1 bar closes.
            signal_i = i - 1
            signal_day = frame.at[signal_i, "server_date"]
            signal_hour = int(frame.at[signal_i, "server_hour"])
            if signal_day != day or signal_day in attempted_days:
                continue
            if not (spec.first_breakout_bar_hour_server <= signal_hour <= spec.last_breakout_bar_hour_server):
                continue
            if not (spec.first_entry_hour_server <= hour <= spec.last_entry_hour_server):
                continue
            if gap != pd.Timedelta(hours=1):
                continue
            range_high = frame.at[signal_i, "range_high"]
            range_low = frame.at[signal_i, "range_low"]
            if not np.isfinite(range_high) or not np.isfinite(range_low) or range_high <= range_low:
                continue
            bid_close = float(frame.at[signal_i, "bid_close"])
            ask_close = float(frame.at[signal_i, "ask_close"])
            side = 1 if bid_close > range_high else (-1 if ask_close < range_low else 0)
            if side == 0:
                continue

            attempted_days.add(day)
            if side == 1:
                fill = float(frame.at[i, "ask_open"]) + slippage_usd_per_oz_per_side
                stop_price = range_low
                distance = fill - stop_price
            else:
                fill = float(frame.at[i, "bid_open"]) - slippage_usd_per_oz_per_side
                stop_price = range_high
                distance = stop_price - fill
            if not math.isfinite(distance) or distance <= 0:
                continue

            position = side
            entry_i = i
            entry_fill = fill
            stop = stop_price
            risk_distance = distance
            target = fill + side * spec.target_r_multiple * distance
            entry_day = day
            entry_hour = hour

            # The entry bar can hit a protective level; a same-bar double-touch
            # resolves to stop first because H1 intrabar order is unknown.
            if side == 1:
                op, high, low = (
                    float(frame.at[i, column]) for column in ("bid_open", "bid_high", "bid_low")
                )
                open_field = "bid_open"
                stop_gap, target_gap = op <= stop, op >= target
                hit_stop, hit_target = low <= stop, high >= target
            else:
                op, high, low = (
                    float(frame.at[i, column]) for column in ("ask_open", "ask_high", "ask_low")
                )
                open_field = "ask_open"
                stop_gap, target_gap = op >= stop, op <= target
                hit_stop, hit_target = high >= stop, low <= target
            if stop_gap:
                close(i, op, open_field, "entry_bar_stop_gap")
            elif target_gap:
                close(i, target, "target_limit", "entry_bar_target_gap")
            elif hit_stop and hit_target:
                close(i, stop, "stop", "entry_bar_same_bar_stop_first")
            elif hit_stop:
                close(i, stop, "stop", "entry_bar_stop")
            elif hit_target:
                close(i, target, "target_limit", "entry_bar_target")

        # If the next bar is missing, liquidate at the last observed close.
        if position and i + 1 < len(frame):
            if frame.at[i + 1, "timestamp"] - timestamp > pd.Timedelta(hours=1):
                field = "bid_close" if position == 1 else "ask_close"
                close(i, float(frame.at[i, field]), field, "data_gap_flatten")

    if position:
        final_i = len(frame) - 1
        field = "bid_close" if position == 1 else "ask_close"
        close(final_i, float(frame.at[final_i, field]), field, "end_of_data_flatten")

    yearly = {
        str(year): _summarize(
            [trade for trade in trades if pd.Timestamp(trade["entry_time_utc"]).year == year],
            spec.risk_fraction,
        )
        for year in (2021, 2022, 2023, 2024)
    }
    discovery = [trade for trade in trades if pd.Timestamp(trade["entry_time_utc"]).year in DISCOVERY_YEARS]
    validation = [trade for trade in trades if pd.Timestamp(trade["entry_time_utc"]).year == VALIDATION_YEAR]
    return {
        "slippage_usd_per_oz_per_side": slippage_usd_per_oz_per_side,
        "commission_usd_per_oz_round_turn": commission_usd_per_oz_round_turn,
        "financing_usd_per_oz": 0.0,
        "server_timezone_model": SERVER_TIMEZONE,
        "opening_range_server_hours": [spec.range_start_hour_server, spec.range_last_hour_server],
        "breakout_bar_server_hours": [spec.first_breakout_bar_hour_server, spec.last_breakout_bar_hour_server],
        "entry_server_hours": [spec.first_entry_hour_server, spec.last_entry_hour_server],
        "flatten_server_hour": spec.flatten_hour_server,
        "yearly": yearly,
        "discovery_2021_2023": _summarize(discovery, spec.risk_fraction),
        "validation_2024": _summarize(validation, spec.risk_fraction),
        "trades": trades,
    }


def gate(scenarios: list[dict]) -> dict:
    checks = []
    for index, scenario in enumerate(scenarios, 1):
        discovery = scenario["discovery_2021_2023"]
        validation = scenario["validation_2024"]
        checks.append({
            "scenario": index,
            "discovery_min_100_trades": discovery["trades"] >= 100,
            "discovery_positive_expectancy": (
                discovery["expectancy_net_r"] is not None and discovery["expectancy_net_r"] > 0
            ),
            "discovery_pf_at_least_1_10": (
                discovery["profit_factor"] is not None and discovery["profit_factor"] >= 1.10
            ),
            "validation_min_30_trades": validation["trades"] >= 30,
            "validation_positive_expectancy": (
                validation["expectancy_net_r"] is not None and validation["expectancy_net_r"] > 0
            ),
            "validation_pf_above_1": (
                validation["profit_factor"] is not None and validation["profit_factor"] > 1.0
            ),
            "all_trades_same_day": all(
                trade["entry_server_date"] == trade["exit_server_date"] for trade in scenario["trades"]
            ),
            "all_trades_before_rollover": all(
                trade["exit_server_hour"] <= 23 for trade in scenario["trades"]
            ),
        })
    passed = bool(checks) and all(all(check.values()) for check in checks)
    return {
        "status": "RESEARCH_SCREEN_PASS" if passed else "NO_GO_FIXED_OPENING_RANGE",
        "all_scenarios_pass": passed,
        "checks": checks,
        "criteria_pre_registered_before_run": True,
        "2024_used_for_parameter_selection": False,
    }


def run_research(data: str | Path, manifest: str | Path, output: str | Path) -> dict:
    bars = load_qualified_dataset(data, manifest)
    scenarios = [run_scenario(bars, slippage_usd_per_oz_per_side=value) for value in (0.05, 0.10, 0.20)]
    decision = gate(scenarios)
    report = {
        "schema": "forexai.g20.xauusd_opening_range_breakout.v1",
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
            "commission_fee_usd_per_oz_round_turn": COMMISSION_USD_PER_OZ_ROUND_TURN,
            "closed_position_sample_count": 99,
            "sample_total_round_turn_lots": 1.08,
            "current_swap_long_usd_per_lot_per_rollover": -37.20,
            "current_swap_short_usd_per_lot_per_rollover": 21.15,
            "triple_rollover_weekday": "Wednesday",
            "historical_financing_schedule_available": False,
        },
        "strategy_spec": {
            **SPEC.__dict__,
            "strategy": "H1 00:00–06:59 server opening-range breakout; first close beyond range, next-open fill",
            "stop": "opposite opening-range boundary",
            "target": f"{SPEC.target_r_multiple}R",
            "max_holding_bars": SPEC.max_holding_bars,
            "one_trade_per_server_day": True,
            "discovery_years": list(DISCOVERY_YEARS),
            "validation_year": VALIDATION_YEAR,
        },
        "cost_policy": {
            "actual_bid_ask_quotes_used": True,
            "spread_double_charged": False,
            "historical_spread_is_wm_exact": False,
            "commission_observed_from_demo_closed_positions": True,
            "slippage_stress_assumptions_per_side": [0.05, 0.10, 0.20],
            "financing_zero_only_under_enforced_same_server_day_flat_rule": True,
            "server_timezone_assumption": SERVER_TIMEZONE,
            "flatten_before_server_hour": 23,
            "data_gap_flatten": True,
        },
        "gate": decision,
        "scenarios": scenarios,
        "backtest_scope": "research-only diagnostic; no orders; no demo/live authorization",
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G20 fixed XAUUSD H1 opening-range breakout screen")
    parser.add_argument("--data", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", default="artifacts/g20-xauusd-opening-range-report.json")
    args = parser.parse_args(argv)
    report = run_research(args.data, args.manifest, args.output)
    print(json.dumps({
        "status": report["status"],
        "rows": report["data"]["rows"],
        "scenarios": [
            {
                "slippage": scenario["slippage_usd_per_oz_per_side"],
                "discovery": scenario["discovery_2021_2023"],
                "validation": scenario["validation_2024"],
            }
            for scenario in report["scenarios"]
        ],
        "gate": report["gate"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
