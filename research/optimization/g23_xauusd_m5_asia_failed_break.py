from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.xauusd_execution_contract_v1 import (
    XAUUSDExecutionConfig,
    run_xauusd_backtest,
)

YEARS = (2021, 2022, 2023, 2024)
PRICE_COLUMNS = (
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
)
SOURCE_COLUMNS = [
    "timestamp", *PRICE_COLUMNS, "bid_volume", "ask_volume",
    "spread_open", "spread_close",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_annual_m5(data_root: Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    provenance: list[dict[str, Any]] = []
    for year in YEARS:
        start, end = f"{year}0101", f"{year + 1}0101"
        path = data_root / f"XAUUSD_M5_BIDASK_{start}_{end}.csv"
        manifest_path = path.with_suffix(".manifest.json")
        if not path.is_file() or not manifest_path.is_file():
            raise FileNotFoundError(f"REAL_DATA_REQUIRED:{year}:{path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        data_hash = sha256(path)
        if manifest.get("data_sha256") != data_hash:
            raise ValueError(f"XAUUSD_DATA_MANIFEST_HASH_MISMATCH:{year}")
        if manifest.get("synthetic_data") is not False or manifest.get("filled_bars") != 0:
            raise ValueError(f"XAUUSD_SYNTHETIC_OR_FILLED_DATA_REJECTED:{year}")
        if manifest.get("schema") != "forexai.real_data.xauusd_bidask_m5_annual.v1":
            raise ValueError(f"XAUUSD_M5_MANIFEST_SCHEMA_INVALID:{year}")
        frame = pd.read_csv(path, usecols=SOURCE_COLUMNS)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
        frame["dataset_year"] = year
        frames.append(frame)
        provenance.append({
            "year": year,
            "rows": int(len(frame)),
            "data_sha256": data_hash,
            "manifest_sha256": sha256(manifest_path),
            "synthetic_data": manifest["synthetic_data"],
            "filled_bars": manifest["filled_bars"],
        })

    bars = pd.concat(frames, ignore_index=True).sort_values("timestamp").reset_index(drop=True)
    if bars.empty or bars["timestamp"].duplicated().any() or not bars["timestamp"].is_monotonic_increasing:
        raise ValueError("XAUUSD_FULL_HISTORY_TIMESTAMP_INVARIANT_FAIL")
    for column in SOURCE_COLUMNS[1:]:
        bars[column] = pd.to_numeric(bars[column], errors="raise")
    for point in ("open", "high", "low", "close"):
        if (bars[f"ask_{point}"] < bars[f"bid_{point}"]).any():
            raise ValueError(f"XAUUSD_CROSSED_{point.upper()}_QUOTES")
    if (bars[["spread_open", "spread_close"]] < 0).any().any():
        raise ValueError("XAUUSD_NEGATIVE_SPREAD")
    if not bars["timestamp"].dt.minute.mod(5).eq(0).all() or not bars["timestamp"].dt.second.eq(0).all():
        raise ValueError("XAUUSD_M5_TIMESTAMP_ALIGNMENT_FAIL")
    return bars, provenance


def add_signals(bars: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = bars.copy()
    mid_high = (frame["bid_high"] + frame["ask_high"]) / 2.0
    mid_low = (frame["bid_low"] + frame["ask_low"]) / 2.0
    mid_close = (frame["bid_close"] + frame["ask_close"]) / 2.0
    previous_close = mid_close.shift(1)
    true_range = pd.concat([
        mid_high - mid_low,
        (mid_high - previous_close).abs(),
        (mid_low - previous_close).abs(),
    ], axis=1).max(axis=1)

    expected = pd.Timedelta(minutes=5)
    deltas = frame["timestamp"].diff()
    segment = (deltas > expected).cumsum()
    frame["ATR"] = true_range.groupby(segment).transform(
        lambda values: values.rolling(14, min_periods=14).mean()
    )
    frame["signal"] = 0
    minute_of_day = frame["timestamp"].dt.hour * 60 + frame["timestamp"].dt.minute
    day_key = frame["timestamp"].dt.strftime("%Y-%m-%d")

    eligible_dates = 0
    excluded_dates = 0
    signals = 0
    long_signals = 0
    short_signals = 0
    exclusion_reasons: dict[str, int] = {}

    for day, indices in frame.groupby(day_key, sort=False).groups.items():
        ids = np.asarray(list(indices), dtype=int)
        minute_values = minute_of_day.iloc[ids].to_numpy()
        asia_ids = ids[(minute_values >= 0) & (minute_values <= 415)]
        london_ids = ids[(minute_values >= 420) & (minute_values <= 595)]

        if len(asia_ids) != 84 or len(london_ids) != 36:
            excluded_dates += 1
            reason = "incomplete_asia_or_london_window"
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            continue

        setup_ids = np.concatenate([asia_ids, london_ids])
        actual = pd.DatetimeIndex(frame.loc[setup_ids, "timestamp"])
        required = pd.date_range(f"{day}T00:00:00Z", periods=120, freq="5min")
        if not actual.equals(required):
            excluded_dates += 1
            reason = "timestamp_gap_in_setup_window"
            exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
            continue

        eligible_dates += 1
        asia_bid_high = float(frame.loc[asia_ids, "bid_high"].max())
        asia_ask_low = float(frame.loc[asia_ids, "ask_low"].min())

        for index in london_ids:
            atr = frame.at[index, "ATR"]
            if not np.isfinite(atr) or atr <= 0:
                continue
            short_setup = (
                float(frame.at[index, "bid_high"]) >= asia_bid_high + 0.15 * float(atr)
                and float(frame.at[index, "bid_close"]) < asia_bid_high
            )
            long_setup = (
                float(frame.at[index, "ask_low"]) <= asia_ask_low - 0.15 * float(atr)
                and float(frame.at[index, "ask_close"]) > asia_ask_low
            )
            if short_setup and long_setup:
                continue
            if not (short_setup or long_setup):
                continue
            next_index = index + 1
            if next_index >= len(frame) or frame.at[next_index, "timestamp"] - frame.at[index, "timestamp"] != expected:
                continue
            frame.at[index, "signal"] = 1 if long_setup else -1
            signals += 1
            long_signals += int(long_setup)
            short_signals += int(short_setup)
            break  # exactly one signal per eligible UTC date

    # The execution kernel requires explicit directional financing columns.
    # This is an intraday-only candidate: no position may cross a feed gap or 20:50 UTC.
    frame["financing_long_usd_per_oz"] = 0.0
    frame["financing_short_usd_per_oz"] = 0.0
    audit = {
        "utc_dates_with_data": int(frame["timestamp"].dt.strftime("%Y-%m-%d").nunique()),
        "eligible_dates": eligible_dates,
        "excluded_dates": excluded_dates,
        "exclusion_reasons": exclusion_reasons,
        "signal_count": signals,
        "long_signals": long_signals,
        "short_signals": short_signals,
        "gap_intervals_over_5min": int((deltas > expected).sum()),
        "gap_policy": "kernel force-close at last observed executable close and block entries on both gap boundaries",
    }
    return frame, audit


def run_split(
    frame: pd.DataFrame,
    split_name: str,
    slippage: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if split_name == "train_2021_2023":
        selected = frame.loc[frame["dataset_year"].isin([2021, 2022, 2023])].copy()
    elif split_name == "oos_2024":
        selected = frame.loc[frame["dataset_year"].eq(2024)].copy()
    else:
        raise ValueError(f"UNKNOWN_SPLIT:{split_name}")

    config = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=slippage,
        commission_usd_per_oz_round_turn=0.10,
        atr_stop_mult=1.5,
        reward_risk=1.5,
        risk_fraction=0.0025,
        max_holding_bars=36,
        force_flat_utc_time="20:50",
        force_flat_bar_interval_minutes=5,
    )
    metrics, trades = run_xauusd_backtest(selected, config)
    metrics["split"] = split_name
    metrics["slippage_usd_per_oz_per_side"] = slippage
    metrics["commission_usd_per_oz_round_turn"] = 0.10
    metrics["signal_definition"] = "G23-ASIA-FAILED-BREAK-001"
    return metrics, trades


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    r = np.asarray([float(item["net_R"]) for item in trades], dtype=float)
    wins = r[r > 0]
    losses = r[r < 0]
    pf: float | str
    if len(losses) and abs(float(losses.sum())) > 0:
        pf = round(float(wins.sum() / abs(losses.sum())), 6)
    elif len(wins):
        pf = "inf"
    else:
        pf = 0.0
    equity = peak = 1.0
    drawdown = 0.0
    for value in r:
        equity *= max(0.0, 1.0 + 0.0025 * value)
        peak = max(peak, equity)
        drawdown = max(drawdown, (peak - equity) / peak * 100.0)
    return {
        "trades": int(len(r)),
        "win_rate_pct": round(100.0 * len(wins) / len(r), 4) if len(r) else 0.0,
        "expectancy_R": round(float(r.mean()), 8) if len(r) else 0.0,
        "total_R": round(float(r.sum()), 8) if len(r) else 0.0,
        "profit_factor": pf,
        "max_dd_pct": round(drawdown, 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    bars, provenance = load_annual_m5(args.data_root)
    signalled, signal_audit = add_signals(bars)
    kernel_results: list[dict[str, Any]] = []
    all_trades: list[dict[str, Any]] = []
    for slippage in (0.05, 0.10, 0.20):
        for split in ("train_2021_2023", "oos_2024"):
            metrics, trades = run_split(signalled, split, slippage)
            kernel_results.append(metrics)
            for trade in trades:
                trade.update({
                    "split": split,
                    "slippage_usd_per_oz_per_side": slippage,
                    "commission_usd_per_oz_round_turn": 0.10,
                })
            all_trades.extend(trades)

    lookup = {(item["slippage_usd_per_oz_per_side"], item["split"]): item for item in kernel_results}
    train = summarize_trades([
        trade for trade in all_trades
        if trade["split"] == "train_2021_2023" and trade["slippage_usd_per_oz_per_side"] == 0.05
    ])
    oos = summarize_trades([
        trade for trade in all_trades
        if trade["split"] == "oos_2024" and trade["slippage_usd_per_oz_per_side"] == 0.05
    ])
    stress = summarize_trades([
        trade for trade in all_trades
        if trade["split"] == "oos_2024" and trade["slippage_usd_per_oz_per_side"] == 0.10
    ])
    gates = {
        "train_min_200_trades": bool(train["trades"] >= 200),
        "train_positive_expectancy": bool(train["expectancy_R"] > 0),
        "oos_min_50_trades": bool(oos["trades"] >= 50),
        "oos_positive_expectancy": bool(oos["expectancy_R"] > 0),
        "oos_pf_at_least_1_10": bool(isinstance(oos["profit_factor"], (int, float)) and oos["profit_factor"] >= 1.10),
        "oos_max_drawdown_at_most_15pct": bool(oos["max_dd_pct"] <= 15.0),
        "oos_positive_expectancy_at_0_10_slippage": bool(stress["expectancy_R"] > 0),
    }
    decision = "GO_RESEARCH_ONLY" if all(gates.values()) else "NO_GO"

    code_path = Path(__file__).resolve()
    result = {
        "schema": "forexai.g23.xauusd_m5_asia_failed_break.v1",
        "candidate": "G23-ASIA-FAILED-BREAK-001",
        "status": decision,
        "execution_kernel": "research.optimization.xauusd_execution_contract_v1.run_xauusd_backtest",
        "execution_kernel_sha256": sha256(Path(__import__("research.optimization.xauusd_execution_contract_v1", fromlist=["__file__"]).__file__).resolve()),
        "runner_sha256": sha256(code_path),
        "data_provenance": provenance,
        "dataset_rows": int(len(bars)),
        "dataset_start_utc": bars["timestamp"].min().isoformat(),
        "dataset_end_utc": bars["timestamp"].max().isoformat(),
        "synthetic_data": False,
        "signal_audit": signal_audit,
        "frozen_cost_model": {
            "historical_spread": "paired Dukascopy BID/ASK quotes; charged once through executable-side prices",
            "commission_usd_per_oz_round_turn": 0.10,
            "slippage_scenarios_usd_per_oz_per_side": [0.05, 0.10, 0.20],
            "financing_usd_per_oz": 0.0,
            "financing_basis": "intraday-only; daily 20:50 UTC flat plus data-gap flattening",
            "broker_cost_limitation": "Dukascopy historical spread is not WM Markets historical spread; commission/slippage are declared scenarios, not measured WM fills",
        },
        "frozen_parameters": {
            "asia_window_utc": "00:00-06:55",
            "signal_window_utc": "07:00-09:55",
            "asia_bars_required": 84,
            "signal_bars_required": 36,
            "sweep_threshold_atr": 0.15,
            "atr_period": 14,
            "atr_method": "midpoint OHLC SMA true range; reset at each >5-minute timestamp gap",
            "stop_atr_mult": 1.5,
            "reward_risk": 1.5,
            "max_holding_bars": 36,
            "max_one_trade_per_utc_day": 1,
            "daily_flat_utc": "20:50",
            "risk_fraction": 0.0025,
            "post_oos_tuning": False,
        },
        "results": kernel_results,
        "decision_gates": gates,
        "limitations": [
            "Research-only simulation; not Python/MQL5 parity or Demo readiness.",
            "Historical Dukascopy spread does not establish historical WM Markets fills.",
            "No Demo/Live authorization or order submission.",
        ],
    }
    (args.output / "g23-report.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    pd.DataFrame(all_trades).to_csv(args.output / "g23-trades.csv", index=False)
    pd.DataFrame(kernel_results).to_csv(args.output / "g23-scenario-metrics.csv", index=False)
    print(json.dumps({
        "status": decision,
        "train_baseline": train,
        "oos_baseline": oos,
        "oos_stress_0_10_slippage": stress,
        "results": kernel_results,
        "gates": gates,
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
