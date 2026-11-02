"""Run the V51 research simulator on a validated real EURUSD dataset.

No download or fallback is performed here. The input dataset must already have
passed the repository's real-data validation pipeline.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

from research.optimization.v51_hybrid_regime import V51Config, backtest_v51, prepare_v51_features
from research.real_data.manifest import sha256_file
from research.real_data.research_pipeline import load_real_dataset


IS_START = pd.Timestamp("2022-01-01T00:00:00Z")
VALIDATION_START = pd.Timestamp("2025-01-01T00:00:00Z")
OOS_START = pd.Timestamp("2026-01-01T00:00:00Z")


def _json_default(value: Any) -> Any:
    item = getattr(value, "item", None)
    if callable(item):
        return item()
    if isinstance(value, (pd.Timestamp, Path)):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _ablation_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Keep the comparison report compact while retaining per-branch trade counts."""
    fields = (
        "status", "simulation_status", "performance_status", "rows", "trades",
        "entries", "win_rate_pct", "expectancy_R", "profit_factor", "total_R",
        "final_equity", "max_dd_pct", "average_holding_bars",
        "round_trip_cost_pips", "skipped",
    )
    summary = {key: report[key] for key in fields if key in report}
    trade_log = report.get("trade_log", [])
    summary["closed_trades_by_branch"] = {
        branch: sum(1 for trade in trade_log if trade.get("setup") == branch)
        for branch in ("A-trend", "B-squeeze", "C-range")
    }
    side_breakdown: dict[str, Any] = {}
    for branch in ("A-trend", "B-squeeze", "C-range"):
        for side in ("LONG", "SHORT"):
            rows = [
                trade for trade in trade_log
                if trade.get("setup") == branch and trade.get("side") == side
            ]
            wins = sum(float(trade["R"]) for trade in rows if float(trade["R"]) > 0)
            losses = abs(sum(float(trade["R"]) for trade in rows if float(trade["R"]) < 0))
            count = len(rows)
            side_breakdown[f"{branch}:{side}"] = {
                "trades": count,
                "win_rate_pct": round(100.0 * sum(float(trade["R"]) > 0 for trade in rows) / count, 3) if count else 0.0,
                "expectancy_R": round(sum(float(trade["R"]) for trade in rows) / count, 6) if count else 0.0,
                "total_R": round(sum(float(trade["R"]) for trade in rows), 6),
                "profit_factor": round(wins / losses, 6) if losses > 0 else (3.0 if wins > 0 else 0.0),
                "exit_reasons": {
                    reason: sum(1 for trade in rows if trade.get("exit_reason") == reason)
                    for reason in sorted({str(trade.get("exit_reason")) for trade in rows})
                },
            }
    summary["closed_trades_by_branch_side"] = side_breakdown
    return summary


def _build_branch_ablation(
    features: pd.DataFrame,
    config: V51Config,
    baseline_reports: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Rerun the complete simulator with branches enabled/disabled.

    Only IS and Validation bars are passed to this function. OOS is intentionally
    excluded so its results remain untouched by branch exploration.
    """
    branch_names = ("A-trend", "B-squeeze", "C-range")
    all_sides = (
        "A-trend:LONG", "A-trend:SHORT",
        "B-squeeze:LONG", "B-squeeze:SHORT",
        "C-range:LONG", "C-range:SHORT",
    )
    scenarios: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        f"only_{branch}": ((branch,), all_sides) for branch in branch_names
    }
    scenarios.update({
        f"without_{branch}": (
            tuple(name for name in branch_names if name != branch),
            all_sides,
        )
        for branch in branch_names
    })
    # These two directional hypotheses are fixed before the new Validation run.
    scenarios["only_C-range_LONG"] = (("C-range",), ("C-range:LONG",))
    scenarios["without_A-trend_and_C-range_SHORT"] = (
        ("B-squeeze", "C-range"),
        ("B-squeeze:LONG", "B-squeeze:SHORT", "C-range:LONG"),
    )
    split_ranges = {
        "IS_2022_2024": (IS_START, VALIDATION_START),
        "VALIDATION_2025": (VALIDATION_START, OOS_START),
    }
    utc = pd.to_datetime(features["utc_timestamp"], utc=True)
    result: dict[str, Any] = {
        "schema": "forexai.v51.branch_ablation.v1",
        "selection_policy": {
            "IS_2022_2024": "Exploration only; branch comparisons may be inspected here.",
            "VALIDATION_2025": "Confirmation only; do not tune thresholds or parameters on this split.",
            "OOS_2026": "Excluded entirely from branch ablation and remains held out.",
            "parameters_changed": False,
            "full_engine_rerun": True,
            "post_hoc_trade_log_filtering": False,
        },
        "branch_scenarios": {name: list(enabled) for name, (enabled, _) in scenarios.items()},
        "branch_side_scenarios": {name: list(enabled_sides) for name, (_, enabled_sides) in scenarios.items()},
        "splits": {},
    }
    for split_name, (start, end) in split_ranges.items():
        mask = (utc >= start) & (utc < end)
        part = features.loc[mask]
        if part.empty:
            result["splits"][split_name] = {"status": "NO_DATA", "rows": 0}
            continue

        split_result: dict[str, Any] = {
            "status": "COMPLETED",
            "rows": int(len(part)),
            "baseline_all_branches": _ablation_summary(baseline_reports[split_name]),
            "scenarios": {},
        }
        for scenario_name, (enabled, enabled_sides) in scenarios.items():
            scenario_config = replace(
                config,
                enabled_branches=enabled,
                enabled_branch_sides=enabled_sides,
            )
            scenario_report = backtest_v51(part, scenario_config)
            split_result["scenarios"][scenario_name] = _ablation_summary(scenario_report)
        result["splits"][split_name] = split_result
    return result


def _build_is_only_design_diagnostics(
    features: pd.DataFrame,
    config: V51Config,
    baseline_reports: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Run one predeclared quote-aware C-range RR hypothesis on IS only."""
    utc = pd.to_datetime(features["utc_timestamp"], utc=True)
    mask = (utc >= IS_START) & (utc < VALIDATION_START)
    is_features = features.loc[mask]
    if is_features.empty:
        return {
            "schema": "forexai.v51.is_only_design_diagnostics.v1",
            "status": "NO_DATA",
            "validation_and_oos_used": False,
        }

    candidate_config = replace(config, range_min_net_rr=1.0)
    candidate_report = backtest_v51(is_features, candidate_config)
    return {
        "schema": "forexai.v51.is_only_design_diagnostics.v1",
        "status": "COMPLETED",
        "hypothesis": (
            "Require C-range target/stop reward-risk >= 1.0 using modeled executable "
            "entry, stop and target fills after the configured spread and adverse slippage."
        ),
        "scope": "IS_2022_2024_ONLY",
        "minimum_net_reward_risk": 1.0,
        "execution_assumptions": {
            "spread_pips": config.spread_pips,
            "slippage_pips_per_side": config.slippage_pips,
            "commission_included": False,
            "swap_included": False,
        },
        "baseline": _ablation_summary(baseline_reports["IS_2022_2024"]),
        "candidate": _ablation_summary(candidate_report),
        "full_engine_rerun": True,
        "post_hoc_trade_log_filtering": False,
        "validation_and_oos_used": False,
        "mql5_parity_status": "NOT_IMPLEMENTED_RESEARCH_ONLY_VARIANT",
        "production_ea_changed": False,
        "other_strategy_parameters_changed": False,
    }



def _build_is_only_directional_diagnostics(
    features: pd.DataFrame,
    config: V51Config,
    baseline_reports: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Test one predeclared side-ablation hypothesis with a full IS-only rerun.

    The candidate disables A-trend LONG and C-range SHORT, the two weakest
    directional groups in the IS baseline attribution. All other branches,
    sides, strategy parameters, execution assumptions and simulator state
    rules remain unchanged. Validation and OOS are never passed to this test.
    """
    utc = pd.to_datetime(features["utc_timestamp"], utc=True)
    mask = (utc >= IS_START) & (utc < VALIDATION_START)
    is_features = features.loc[mask]
    if is_features.empty:
        return {
            "schema": "forexai.v51.is_only_directional_diagnostics.v1",
            "status": "NO_DATA",
            "scope": "IS_2022_2024_ONLY",
            "validation_and_oos_used": False,
        }

    excluded_sides = ("A-trend:LONG", "C-range:SHORT")
    all_sides = (
        "A-trend:LONG", "A-trend:SHORT",
        "B-squeeze:LONG", "B-squeeze:SHORT",
        "C-range:LONG", "C-range:SHORT",
    )
    enabled_sides = tuple(side for side in all_sides if side not in excluded_sides)
    candidate_config = replace(config, enabled_branch_sides=enabled_sides)
    candidate_report = backtest_v51(is_features, candidate_config)
    baseline = _ablation_summary(baseline_reports["IS_2022_2024"])

    return {
        "schema": "forexai.v51.is_only_directional_diagnostics.v1",
        "status": "COMPLETED",
        "hypothesis": (
            "Disabling A-trend LONG and C-range SHORT may reduce the negative "
            "IS contribution of those two directional groups. This is a single "
            "side-ablation hypothesis, not parameter optimization."
        ),
        "scope": "IS_2022_2024_ONLY",
        "selection_evidence": {
            side: baseline["closed_trades_by_branch_side"][side]
            for side in excluded_sides
        },
        "excluded_branch_sides": list(excluded_sides),
        "enabled_branch_sides": list(enabled_sides),
        "baseline": baseline,
        "candidate": _ablation_summary(candidate_report),
        "full_engine_rerun": True,
        "post_hoc_trade_log_filtering": False,
        "validation_and_oos_used": False,
        "branch_set_changed": False,
        "other_strategy_parameters_changed": False,
        "mql5_parity_status": "NOT_IMPLEMENTED_RESEARCH_ONLY_VARIANT",
        "production_ea_changed": False,
    }


def run(
    data_path: str | Path,
    *,
    timeframe: str = "M15",
    output_path: str | Path = "artifacts/v51_real_backtest.json",
    server_utc_offset_hours: float = 0.0,
    spread_pips: float = 0.5,
    slippage_pips: float = 0.2,
) -> dict[str, Any]:
    if timeframe.upper() != "M15":
        raise ValueError("V51_RESEARCH_RUNNER_REQUIRES_M15")
    path = Path(data_path)
    real = load_real_dataset(path, symbol="EURUSD", timeframe="M15")
    if real.empty:
        raise ValueError("REAL_DATA_REQUIRED: validated dataset is empty")

    config = V51Config(
        server_utc_offset_hours=server_utc_offset_hours,
        spread_pips=spread_pips,
        slippage_pips=slippage_pips,
    )
    features = prepare_v51_features(real, config)
    utc = pd.to_datetime(features["utc_timestamp"], utc=True)
    max_utc = utc.max()
    oos_end = max_utc + pd.Timedelta(minutes=15)

    periods = {
        "IS_2022_2024": (IS_START, VALIDATION_START),
        "VALIDATION_2025": (VALIDATION_START, OOS_START),
        "OOS_2026": (OOS_START, oos_end),
    }

    split_reports: dict[str, Any] = {}
    for name, (start, end) in periods.items():
        mask = (utc >= start) & (utc < end)
        part = features.loc[mask]
        if part.empty:
            split_reports[name] = {
                "status": "NO_DATA",
                "rows": 0,
                "start_utc": start.isoformat(),
                "end_utc_exclusive": end.isoformat(),
            }
            continue
        report = backtest_v51(part, config)
        report["start_utc"] = utc.loc[mask].min().isoformat()
        report["end_utc"] = utc.loc[mask].max().isoformat()
        split_reports[name] = report

    branch_ablation = _build_branch_ablation(features, config, split_reports)
    is_only_design_diagnostics = _build_is_only_design_diagnostics(
        features, config, split_reports
    )
    is_only_directional_diagnostics = _build_is_only_directional_diagnostics(
        features, config, split_reports
    )

    payload: dict[str, Any] = {
        "schema": "forexai.v51.real_backtest.v1",
        "status": "COMPLETED_WITH_REAL_DATA",
        "strategy": "GRK-FX-2026-051",
        "symbol": "EURUSD",
        "timeframe": "M15",
        "data": {
            "path": str(path),
            "sha256": sha256_file(path),
            "rows": int(len(real)),
            "start_utc": pd.to_datetime(real["timestamp"], utc=True).min().isoformat(),
            "end_utc": pd.to_datetime(real["timestamp"], utc=True).max().isoformat(),
            "source": "Dukascopy validated by research.real_data.load_real_dataset",
            "price_side": "BID",
            "synthetic_data": False,
        },
        "execution_assumptions": {
            "spread_pips": spread_pips,
            "slippage_pips_per_side": slippage_pips,
            "round_trip_adverse_cost_pips": spread_pips + 2.0 * slippage_pips,
            "bid_ohlc_fill_model": {
                "long_entry": "BID open + assumed spread + adverse slippage",
                "long_exit": "BID exit - adverse slippage",
                "short_entry": "BID open - adverse slippage",
                "short_exit": "BID exit + assumed spread + adverse slippage",
                "spread_is_charged_once_per_round_trip": True,
            },
            "server_utc_offset_hours": server_utc_offset_hours,
            "server_offset_status": "USER_OR_OPERATOR_ASSUMPTION_NOT_BROKER_VERIFIED",
            "commission_included": False,
            "swap_included": False,
        },
        "selection_policy": {
            "optimization_performed": False,
            "IS_period": "2022-01-01 through 2024-12-31",
            "validation_period": "2025-01-01 through 2025-12-31",
            "OOS_period": "2026-01-01 through latest available input bar",
            "OOS_used_for_parameter_selection": False,
        },
        "splits": split_reports,
        "branch_ablation": branch_ablation,
        "is_only_design_diagnostics": is_only_design_diagnostics,
        "is_only_directional_diagnostics": is_only_directional_diagnostics,
        "config": config.__dict__,
        "limitations": [
            "This runner does not optimize parameters or select a champion.",
            "The Python indicator implementation is a research approximation; MT5-exported signal parity remains a separate required check.",
            "The broker server UTC offset must be verified before interpreting session-filter results.",
            "Bid-OHLC cost treatment applies the assumed spread once per round trip and adverse slippage on both sides; values are not historical tick-by-tick costs.",
            "Commission and swap are omitted because no verified account-specific schedule was supplied.",
            "The research simulator does not read or issue runtime authorization and cannot submit orders.",
        ],
    }

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default),
        encoding="utf-8",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Validated REAL EURUSD M15 CSV or Parquet file")
    parser.add_argument("--timeframe", default="M15", choices=["M15"])
    parser.add_argument("--output", default="artifacts/v51_real_backtest.json")
    parser.add_argument("--server-utc-offset-hours", type=float, default=0.0)
    parser.add_argument("--spread-pips", type=float, default=0.5)
    parser.add_argument("--slippage-pips", type=float, default=0.2)
    args = parser.parse_args()
    report = run(
        args.data,
        timeframe=args.timeframe,
        output_path=args.output,
        server_utc_offset_hours=args.server_utc_offset_hours,
        spread_pips=args.spread_pips,
        slippage_pips=args.slippage_pips,
    )
    print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
