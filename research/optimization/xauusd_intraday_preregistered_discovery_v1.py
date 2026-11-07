"""Small, preregistered XAUUSD M5 discovery using the Gold BID/ASK execution kernel.

Training: 2021-2023 only (G22 annual datasets).
Validation: 2025 only (fresh G24 annual dataset).
2024 is deliberately excluded because it was consumed by G23; 2026 is never loaded.
This module reports research evidence only and cannot authorize Demo/Live trading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from research.optimization.xauusd_execution_contract_v1 import XAUUSDExecutionConfig
from research.optimization.xauusd_intraday_execution_adapter_v1 import run_xauusd_intraday

TRAIN_YEARS = (2021, 2022, 2023)
VALIDATION_START = "2025-01-01"
VALIDATION_END = "2026-01-01"
MAX_INDICATOR_WARMUP_AFTER_GAP = 200
RISK_FRACTION = 0.0025
FLATTEN_BY_UTC = "20:50"
EARLIEST_ROLLOVER_UTC = "20:59"

# This is a fixed, deliberately small hypothesis set, not a parameter optimizer.
CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "id": "trend_pullback_50_200",
        "family": "trend_pullback",
        "ema_fast": 50,
        "ema_slow": 200,
        "pullback_ema": 20,
        "rsi_min": 50,
        "adx_min": 18,
        "atr_stop_mult": 1.5,
        "reward_risk": 2.0,
        "max_holding_bars": 36,
    },
    {
        "id": "trend_pullback_34_144",
        "family": "trend_pullback",
        "ema_fast": 34,
        "ema_slow": 144,
        "pullback_ema": 20,
        "rsi_min": 52,
        "adx_min": 20,
        "atr_stop_mult": 2.0,
        "reward_risk": 2.0,
        "max_holding_bars": 36,
    },
    {
        "id": "donchian_20_trend",
        "family": "donchian_breakout",
        "channel_window": 20,
        "ema_fast": 50,
        "ema_slow": 200,
        "adx_min": 20,
        "atr_stop_mult": 1.5,
        "reward_risk": 2.0,
        "max_holding_bars": 24,
    },
    {
        "id": "donchian_55_trend",
        "family": "donchian_breakout",
        "channel_window": 55,
        "ema_fast": 50,
        "ema_slow": 200,
        "adx_min": 18,
        "atr_stop_mult": 2.0,
        "reward_risk": 2.5,
        "max_holding_bars": 36,
    },
    {
        "id": "bollinger_reentry_20",
        "family": "bollinger_mean_reversion",
        "bb_window": 20,
        "bb_z": 2.0,
        "rsi_long_max": 45,
        "rsi_short_min": 55,
        "adx_max": 18,
        "atr_stop_mult": 1.5,
        "reward_risk": 1.0,
        "max_holding_bars": 12,
    },
    {
        "id": "bollinger_reentry_40",
        "family": "bollinger_mean_reversion",
        "bb_window": 40,
        "bb_z": 2.0,
        "rsi_long_max": 40,
        "rsi_short_min": 60,
        "adx_max": 15,
        "atr_stop_mult": 1.5,
        "reward_risk": 1.2,
        "max_holding_bars": 12,
    },
    {
        # Exit-only sensitivity check: identical Donchian 55 entry logic,
        # stop distance and holding limit; only target multiple changes.
        "id": "donchian_55_trend_rr15_exit_only",
        "family": "donchian_breakout",
        "channel_window": 55,
        "ema_fast": 50,
        "ema_slow": 200,
        "adx_min": 18,
        "atr_stop_mult": 2.0,
        "reward_risk": 1.5,
        "max_holding_bars": 36,
    },
    {
        # One distinct, fixed-time hypothesis; no parameter sweep.
        "id": "london_opening_range_breakout",
        "family": "opening_range_breakout",
        "atr_stop_mult": 1.5,
        "reward_risk": 2.0,
        "max_holding_bars": 36,
    },
    {
        # Port of the repository's Robust Regime-Momentum v1 entry rules.
        # Execution is re-evaluated by the XAUUSD BID/ASK kernel; the large
        # holding cap disables the old model's synthetic time exit because
        # this intraday adapter already flattens before UTC rollover.
        "id": "robust_regime_momentum_v1",
        "family": "robust_regime_momentum",
        "ema_fast": 20,
        "ema_slow": 50,
        "h1_ema_fast": 50,
        "h1_ema_slow": 200,
        "adx_min": 22.0,
        "pullback_bars": 3,
        "touch_atr": 0.20,
        "vol_min": 0.70,
        "vol_max": 1.80,
        "atr_stop_mult": 1.6,
        "reward_risk": 2.2,
        "max_holding_bars": 999,
    },
)

REQUIRED_PRICE_COLUMNS = (
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _period_timestamp(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def read_verified_dataset(
    csv_path: str | Path,
    manifest_path: str | Path,
    *,
    start: str,
    end: str,
    expected_year: int | None = None,
    require_fresh_validation: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read one annual M5 file only after its manifest, hash and scope pass."""
    data_path = Path(csv_path)
    manifest_file = Path(manifest_path)
    if not data_path.is_file() or not manifest_file.is_file():
        raise FileNotFoundError(f"XAUUSD_DATA_OR_MANIFEST_MISSING:{data_path}")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("timeframe") != "M5":
        raise ValueError("XAUUSD_DISCOVERY_TIMEFRAME_NOT_M5")
    if manifest.get("symbol") not in (None, "XAUUSD"):
        raise ValueError("XAUUSD_DISCOVERY_SYMBOL_MISMATCH")
    if manifest.get("synthetic_data") is not False or manifest.get("filled_bars") != 0:
        raise ValueError("XAUUSD_DISCOVERY_SYNTHETIC_OR_FILLED_DATA_REJECTED")
    if manifest.get("backtest_run") is not False:
        raise ValueError("XAUUSD_DISCOVERY_SOURCE_ALREADY_BACKTESTED")
    if manifest.get("data_sha256") != sha256_file(data_path):
        raise ValueError("XAUUSD_DISCOVERY_DATA_HASH_MISMATCH")

    if require_fresh_validation:
        if manifest.get("status") != "FRESH_REAL_XAUUSD_M5_DATASET_READY_FOR_PREREGISTERED_RESEARCH":
            raise ValueError("XAUUSD_VALIDATION_MANIFEST_STATUS_INVALID")
        if manifest.get("symbol") != "XAUUSD":
            raise ValueError("XAUUSD_VALIDATION_SYMBOL_NOT_EXPLICIT")
        manifest_start = manifest.get("start_inclusive_utc")
        manifest_end = manifest.get("end_exclusive_utc")
    else:
        if manifest.get("status") != "FULL_YEAR_DATASET_ASSEMBLED_GAP_REVIEW_REQUIRED":
            raise ValueError("XAUUSD_TRAIN_MANIFEST_STATUS_INVALID")
        manifest_start = manifest.get("start_inclusive_utc")
        manifest_end = manifest.get("end_exclusive_utc")

    expected_start = _period_timestamp(start)
    expected_end = _period_timestamp(end)
    if manifest_start is None or manifest_end is None:
        raise ValueError("XAUUSD_DISCOVERY_MANIFEST_DATE_SCOPE_MISSING")
    if pd.Timestamp(manifest_start) != expected_start or pd.Timestamp(manifest_end) != expected_end:
        raise ValueError("XAUUSD_DISCOVERY_MANIFEST_DATE_SCOPE_MISMATCH")

    frame = pd.read_csv(data_path)
    required = {"timestamp", *REQUIRED_PRICE_COLUMNS, "spread_open", "spread_close"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"XAUUSD_DISCOVERY_COLUMNS_MISSING:{sorted(missing)}")
    if len(frame) != int(manifest.get("rows", -1)):
        raise ValueError("XAUUSD_DISCOVERY_ROW_COUNT_MISMATCH")

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    if frame.empty or frame["timestamp"].duplicated().any():
        raise ValueError("XAUUSD_DISCOVERY_EMPTY_OR_DUPLICATE_TIMESTAMPS")
    if not frame["timestamp"].is_monotonic_increasing:
        raise ValueError("XAUUSD_DISCOVERY_TIMESTAMP_ORDER_INVALID")
    if (
        frame["timestamp"].dt.minute.mod(5).ne(0).any()
        or frame["timestamp"].dt.second.ne(0).any()
    ):
        raise ValueError("XAUUSD_DISCOVERY_M5_ALIGNMENT_INVALID")
    if not (
        (frame["timestamp"] >= expected_start)
        & (frame["timestamp"] < expected_end)
    ).all():
        raise ValueError("XAUUSD_DISCOVERY_ROWS_OUTSIDE_MANIFEST_PERIOD")

    for side in ("bid", "ask"):
        op, hi, lo, cl = (frame[f"{side}_{name}"] for name in ("open", "high", "low", "close"))
        if ((hi < np.maximum(op, cl)) | (lo > np.minimum(op, cl)) | (hi < lo)).any():
            raise ValueError(f"XAUUSD_DISCOVERY_{side.upper()}_OHLC_INVALID")
    if (frame["ask_open"] < frame["bid_open"]).any() or (frame["ask_close"] < frame["bid_close"]).any():
        raise ValueError("XAUUSD_DISCOVERY_CROSSED_QUOTES")
    if (frame[["spread_open", "spread_close"]] < 0).any().any():
        raise ValueError("XAUUSD_DISCOVERY_NEGATIVE_SPREAD")
    if not np.allclose(frame["ask_open"] - frame["bid_open"], frame["spread_open"], atol=1.1e-5, rtol=0):
        raise ValueError("XAUUSD_DISCOVERY_OPEN_SPREAD_MISMATCH")
    if not np.allclose(frame["ask_close"] - frame["bid_close"], frame["spread_close"], atol=1.1e-5, rtol=0):
        raise ValueError("XAUUSD_DISCOVERY_CLOSE_SPREAD_MISMATCH")

    if expected_year is not None and set(frame["timestamp"].dt.year.unique()) != {expected_year}:
        raise ValueError(f"XAUUSD_DISCOVERY_EXPECTED_YEAR_MISMATCH:{expected_year}")
    if frame["timestamp"].min().isoformat() != pd.Timestamp(manifest["first_utc"]).isoformat():
        raise ValueError("XAUUSD_DISCOVERY_FIRST_TIMESTAMP_MISMATCH")
    if frame["timestamp"].max().isoformat() != pd.Timestamp(manifest["last_utc"]).isoformat():
        raise ValueError("XAUUSD_DISCOVERY_LAST_TIMESTAMP_MISMATCH")

    audit = {
        "csv": data_path.name,
        "manifest": manifest_file.name,
        "data_sha256": manifest["data_sha256"],
        "manifest_sha256": sha256_file(manifest_file),
        "rows": int(len(frame)),
        "first_utc": frame["timestamp"].min().isoformat(),
        "last_utc": frame["timestamp"].max().isoformat(),
        "gap_count_from_manifest": manifest.get("gap_count", manifest.get("gap_audit", {}).get("gap_count")),
        "source_status": manifest.get("status"),
    }
    return frame, audit


def load_training(root: str | Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    root = Path(root)
    frames, audits = [], []
    for year in TRAIN_YEARS:
        start, end = f"{year}-01-01", f"{year + 1}-01-01"
        stem = f"XAUUSD_M5_BIDASK_{year}0101_{year + 1}0101"
        frame, audit = read_verified_dataset(
            root / f"{stem}.csv",
            root / f"{stem}.manifest.json",
            start=start,
            end=end,
            expected_year=year,
        )
        frames.append(frame)
        audits.append(audit)
    combined = pd.concat(frames, ignore_index=True).sort_values("timestamp").reset_index(drop=True)
    if combined["timestamp"].duplicated().any() or not combined["timestamp"].is_monotonic_increasing:
        raise ValueError("XAUUSD_TRAINING_ANNUAL_DATASETS_OVERLAP")
    if set(combined["timestamp"].dt.year.unique()) != set(TRAIN_YEARS):
        raise ValueError("XAUUSD_TRAINING_PERIOD_NOT_EXACTLY_2021_2023")
    return combined, audits


def load_validation(root: str | Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load the fresh 2025 annual file or assemble it from only four G24 2025 shards."""
    root = Path(root)
    stem = "XAUUSD_M5_BIDASK_20250101_20260101"
    annual_csv = root / f"{stem}.csv"
    annual_manifest = root / f"{stem}.manifest.json"
    if annual_csv.is_file() and annual_manifest.is_file():
        return read_verified_dataset(
            annual_csv,
            annual_manifest,
            start=VALIDATION_START,
            end=VALIDATION_END,
            expected_year=2025,
            require_fresh_validation=True,
        )

    expected_shards = {
        "2025-Q1": ("2025-01-01", "2025-04-01"),
        "2025-Q2": ("2025-04-01", "2025-07-01"),
        "2025-Q3": ("2025-07-01", "2025-10-01"),
        "2025-Q4": ("2025-10-01", "2026-01-01"),
    }
    report_paths = list(root.rglob("report.json"))
    selected: dict[str, tuple[Path, dict[str, Any]]] = {}
    for report_path in report_paths:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        shard = report.get("shard")
        if shard in expected_shards:
            if shard in selected:
                raise ValueError(f"XAUUSD_VALIDATION_DUPLICATE_SHARD_REPORT:{shard}")
            selected[shard] = (report_path, report)
    if set(selected) != set(expected_shards):
        missing = sorted(set(expected_shards).difference(selected))
        raise FileNotFoundError(f"XAUUSD_VALIDATION_2025_SHARDS_MISSING:{missing}")

    frames = []
    audits = []
    for shard, (start, end) in expected_shards.items():
        report_path, report = selected[shard]
        base = report_path.parent
        if (
            report.get("status") != "REAL_XAUUSD_M5_FRESH_OOS_SHARD_PASS"
            or report.get("synthetic_data") is not False
            or report.get("filled_bars") != 0
            or report.get("backtest_run") is not False
            or report.get("orders_submitted") is not False
        ):
            raise ValueError(f"XAUUSD_VALIDATION_SHARD_REPORT_REJECTED:{shard}")

        paths = {
            "m1": base / report["m1_path"],
            "m1_manifest": base / report["m1_manifest_path"],
            "m5": base / report["m5_path"],
            "m5_manifest": base / report["m5_manifest_path"],
        }
        expected_hashes = {
            "m1": report["m1_sha256"],
            "m1_manifest": report["m1_manifest_sha256"],
            "m5": report["m5_sha256"],
            "m5_manifest": report["m5_manifest_sha256"],
        }
        for label, path in paths.items():
            if not path.is_file() or sha256_file(path) != expected_hashes[label]:
                raise ValueError(f"XAUUSD_VALIDATION_SHARD_HASH_MISMATCH:{shard}:{label}")

        m1_manifest = json.loads(paths["m1_manifest"].read_text(encoding="utf-8"))
        if (
            m1_manifest.get("symbol") != "XAUUSD"
            or m1_manifest.get("timeframe") != "M1"
            or m1_manifest.get("synthetic_data") is not False
            or m1_manifest.get("backtest_run") is not False
            or m1_manifest.get("data_sha256") != expected_hashes["m1"]
        ):
            raise ValueError(f"XAUUSD_VALIDATION_M1_MANIFEST_REJECTED:{shard}")

        manifest = json.loads(paths["m5_manifest"].read_text(encoding="utf-8"))
        if (
            manifest.get("status") != "REAL_M5_SHARD_PASS_GAPS_PRESERVED"
            or manifest.get("symbol") != "XAUUSD"
            or manifest.get("timeframe") != "M5"
            or manifest.get("shard") != shard
            or manifest.get("requested_start_utc") != start
            or manifest.get("requested_end_exclusive_utc") != end
            or manifest.get("synthetic_data") is not False
            or manifest.get("filled_bars") != 0
            or manifest.get("backtest_run") is not False
            or manifest.get("data_sha256") != expected_hashes["m5"]
            or manifest.get("source_m1_data_sha256") != expected_hashes["m1"]
            or manifest.get("source_m1_manifest_sha256") != expected_hashes["m1_manifest"]
        ):
            raise ValueError(f"XAUUSD_VALIDATION_SHARD_MANIFEST_REJECTED:{shard}")

        reconciliation = report.get("reconciliation_audit", {})
        if (
            int(reconciliation.get("compared_bars", -1)) != int(report.get("m5_rows", -2))
            or float(reconciliation.get("max_abs_delta", float("inf"))) > 1.1e-5
            or float(reconciliation.get("tolerance", 0.0)) > 1.1e-5
        ):
            raise ValueError(f"XAUUSD_VALIDATION_SHARD_RECONCILIATION_REJECTED:{shard}")

        frame = pd.read_csv(paths["m5"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
        if (
            len(frame) != int(report["m5_rows"])
            or len(frame) != int(manifest.get("rows", -1))
            or frame["timestamp"].duplicated().any()
            or not frame["timestamp"].is_monotonic_increasing
        ):
            raise ValueError(f"XAUUSD_VALIDATION_SHARD_DATA_INVARIANT_FAILED:{shard}")
        if (
            frame["timestamp"].dt.minute.mod(5).ne(0).any()
            or frame["timestamp"].dt.second.ne(0).any()
        ):
            raise ValueError(f"XAUUSD_VALIDATION_SHARD_M5_ALIGNMENT_FAILED:{shard}")
        if not (
            (frame["timestamp"] >= _period_timestamp(start))
            & (frame["timestamp"] < _period_timestamp(end))
        ).all():
            raise ValueError(f"XAUUSD_VALIDATION_SHARD_DATE_RANGE_FAILED:{shard}")
        frames.append(frame)
        audits.append({
            "shard": shard,
            "report_sha256": sha256_file(report_path),
            "m1_sha256": expected_hashes["m1"],
            "m1_manifest_sha256": expected_hashes["m1_manifest"],
            "m5_sha256": expected_hashes["m5"],
            "m5_manifest_sha256": expected_hashes["m5_manifest"],
            "rows": int(len(frame)),
            "reconciliation_audit": reconciliation,
        })

    combined = pd.concat(frames, ignore_index=True).sort_values("timestamp").reset_index(drop=True)
    if (
        combined.empty
        or combined["timestamp"].duplicated().any()
        or not combined["timestamp"].is_monotonic_increasing
        or set(combined["timestamp"].dt.year.unique()) != {2025}
        or not (
            (combined["timestamp"] >= _period_timestamp(VALIDATION_START))
            & (combined["timestamp"] < _period_timestamp(VALIDATION_END))
        ).all()
    ):
        raise ValueError("XAUUSD_VALIDATION_2025_ASSEMBLY_INVARIANT_FAILED")
    required = {"timestamp", *REQUIRED_PRICE_COLUMNS, "spread_open", "spread_close"}
    missing = required.difference(combined.columns)
    if missing:
        raise ValueError(f"XAUUSD_VALIDATION_2025_COLUMNS_MISSING:{sorted(missing)}")
    for side in ("bid", "ask"):
        op, hi, lo, cl = (combined[f"{side}_{name}"] for name in ("open", "high", "low", "close"))
        if ((hi < np.maximum(op, cl)) | (lo > np.minimum(op, cl)) | (hi < lo)).any():
            raise ValueError(f"XAUUSD_VALIDATION_2025_{side.upper()}_OHLC_INVALID")
    if (combined["ask_open"] < combined["bid_open"]).any() or (combined["ask_close"] < combined["bid_close"]).any():
        raise ValueError("XAUUSD_VALIDATION_2025_CROSSED_QUOTES")
    if (combined[["spread_open", "spread_close"]] < 0).any().any():
        raise ValueError("XAUUSD_VALIDATION_2025_NEGATIVE_SPREAD")
    if not np.allclose(combined["ask_open"] - combined["bid_open"], combined["spread_open"], atol=1.1e-5, rtol=0):
        raise ValueError("XAUUSD_VALIDATION_2025_OPEN_SPREAD_MISMATCH")
    if not np.allclose(combined["ask_close"] - combined["bid_close"], combined["spread_close"], atol=1.1e-5, rtol=0):
        raise ValueError("XAUUSD_VALIDATION_2025_CLOSE_SPREAD_MISMATCH")
    annual_csv_bytes = combined.to_csv(
        index=False,
        float_format="%.5f",
        date_format="%Y-%m-%dT%H:%M:%SZ",
    ).encode("utf-8")
    audit = {
        "source_mode": "four_immutable_G24_2025_shards_only",
        "source_shards": audits,
        "rows": int(len(combined)),
        "first_utc": combined["timestamp"].min().isoformat(),
        "last_utc": combined["timestamp"].max().isoformat(),
        "assembled_annual_csv_sha256": hashlib.sha256(annual_csv_bytes).hexdigest(),
        "2026_shards_downloaded": False,
    }
    return combined, audit


def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    """Calculate indicators on mid quotes; executable fills still use BID/ASK."""
    d = raw.copy()
    d["mid_open"] = (d["bid_open"] + d["ask_open"]) / 2.0
    d["mid_high"] = (d["bid_high"] + d["ask_high"]) / 2.0
    d["mid_low"] = (d["bid_low"] + d["ask_low"]) / 2.0
    d["mid_close"] = (d["bid_close"] + d["ask_close"]) / 2.0

    previous_close = d["mid_close"].shift(1)
    tr = pd.concat(
        [
            d["mid_high"] - d["mid_low"],
            (d["mid_high"] - previous_close).abs(),
            (d["mid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    alpha = 1.0 / 14.0
    d["ATR"] = tr.ewm(alpha=alpha, adjust=False, min_periods=14).mean()
    d["ATR_BASE20"] = d["ATR"].rolling(20, min_periods=20).mean()
    d["ATR_RATIO"] = d["ATR"] / d["ATR_BASE20"].replace(0, np.nan)

    # Higher-timeframe context: use only fully complete UTC H1 candles.
    # A missing M5 bar makes that H1 candle unusable rather than silently
    # accepting a partial hour as a completed regime candle.
    m5_close = d.set_index("timestamp")["mid_close"]
    h1 = m5_close.resample("1h", label="left", closed="left").agg(["last", "count"])
    h1_complete = h1["count"].eq(12)
    h1_close = h1["last"].where(h1_complete)
    h1_fast = h1_close.ewm(
        span=50, adjust=False, min_periods=50, ignore_na=False
    ).mean()
    h1_slow = h1_close.ewm(
        span=200, adjust=False, min_periods=200, ignore_na=False
    ).mean()
    h1_valid = h1_complete & h1_fast.notna() & h1_slow.notna()
    h1_up = (h1_fast > h1_slow).where(h1_valid).shift(1)
    h1_down = (h1_fast < h1_slow).where(h1_valid).shift(1)
    hour_key = d["timestamp"].dt.floor("h")
    d["H1_TREND_UP"] = hour_key.map(h1_up)
    d["H1_TREND_DOWN"] = hour_key.map(h1_down)

    up_move = d["mid_high"].diff()
    down_move = -d["mid_low"].diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    plus_di = 100.0 * plus_dm.ewm(alpha=alpha, adjust=False, min_periods=14).mean() / d["ATR"].replace(0, np.nan)
    minus_di = 100.0 * minus_dm.ewm(alpha=alpha, adjust=False, min_periods=14).mean() / d["ATR"].replace(0, np.nan)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    d["ADX"] = dx.ewm(alpha=alpha, adjust=False, min_periods=14).mean()

    delta = d["mid_close"].diff()
    gains = delta.clip(lower=0).ewm(alpha=alpha, adjust=False, min_periods=14).mean()
    losses = (-delta.clip(upper=0)).ewm(alpha=alpha, adjust=False, min_periods=14).mean()
    rs = gains / losses.replace(0, np.nan)
    d["RSI"] = 100.0 - (100.0 / (1.0 + rs))

    for span in (20, 34, 50, 144, 200):
        d[f"EMA{span}"] = d["mid_close"].ewm(span=span, adjust=False, min_periods=span).mean()

    for window in (20, 40, 55):
        d[f"BB_MID_{window}"] = d["mid_close"].rolling(window, min_periods=window).mean()
        d[f"BB_STD_{window}"] = d["mid_close"].rolling(window, min_periods=window).std(ddof=0)
        d[f"CHANNEL_HIGH_{window}"] = d["mid_high"].rolling(window, min_periods=window).max().shift(1)
        d[f"CHANNEL_LOW_{window}"] = d["mid_low"].rolling(window, min_periods=window).min().shift(1)

    # Fixed London opening range: all twelve M5 bars from 07:00 through
    # 07:55 UTC must exist. Incomplete days are excluded, not filled.
    utc_date = d["timestamp"].dt.strftime("%Y-%m-%d")
    opening = d.loc[d["timestamp"].dt.hour.eq(7), ["timestamp", "mid_high", "mid_low"]].copy()
    opening["_utc_date"] = utc_date.loc[opening.index]
    opening_range = opening.groupby("_utc_date").agg(
        bars=("timestamp", "size"),
        high=("mid_high", "max"),
        low=("mid_low", "min"),
    )
    incomplete = opening_range["bars"].ne(12)
    opening_range.loc[incomplete, ["high", "low"]] = np.nan
    d["OPENING_RANGE_HIGH"] = utc_date.map(opening_range["high"])
    d["OPENING_RANGE_LOW"] = utc_date.map(opening_range["low"])
    return d


def build_signals(features: pd.DataFrame, candidate: dict[str, Any]) -> pd.Series:
    close = features["mid_close"]
    adx = features["ADX"]
    rsi = features["RSI"]
    family = candidate["family"]
    signal = pd.Series(0, index=features.index, dtype="int64")

    if family == "trend_pullback":
        fast = features[f"EMA{candidate['ema_fast']}"]
        slow = features[f"EMA{candidate['ema_slow']}"]
        pullback = features[f"EMA{candidate['pullback_ema']}"]
        long = (
            (fast > slow)
            & (close.shift(1) <= pullback.shift(1))
            & (close > pullback)
            & (rsi >= candidate["rsi_min"])
            & (adx >= candidate["adx_min"])
        )
        short = (
            (fast < slow)
            & (close.shift(1) >= pullback.shift(1))
            & (close < pullback)
            & (rsi <= 100 - candidate["rsi_min"])
            & (adx >= candidate["adx_min"])
        )
    elif family == "donchian_breakout":
        window = int(candidate["channel_window"])
        upper = features[f"CHANNEL_HIGH_{window}"]
        lower = features[f"CHANNEL_LOW_{window}"]
        fast = features[f"EMA{candidate['ema_fast']}"]
        slow = features[f"EMA{candidate['ema_slow']}"]
        long = (close > upper) & (fast > slow) & (adx >= candidate["adx_min"])
        short = (close < lower) & (fast < slow) & (adx >= candidate["adx_min"])
    elif family == "bollinger_mean_reversion":
        window = int(candidate["bb_window"])
        mid = features[f"BB_MID_{window}"]
        std = features[f"BB_STD_{window}"].replace(0, np.nan)
        z = (close - mid) / std
        edge = float(candidate["bb_z"])
        long = (
            (z.shift(1) < -edge)
            & (z >= -edge)
            & (rsi <= candidate["rsi_long_max"])
            & (adx <= candidate["adx_max"])
        )
        short = (
            (z.shift(1) > edge)
            & (z <= edge)
            & (rsi >= candidate["rsi_short_min"])
            & (adx <= candidate["adx_max"])
        )
    elif family == "opening_range_breakout":
        # One first-close breakout per UTC day after a complete 07:00-08:00 range.
        upper = features["OPENING_RANGE_HIGH"]
        lower = features["OPENING_RANGE_LOW"]
        after_opening_range = features["timestamp"].dt.hour.ge(8)
        long = (
            after_opening_range
            & upper.notna()
            & (close.shift(1) <= upper)
            & (close > upper)
        )
        short = (
            after_opening_range
            & lower.notna()
            & (close.shift(1) >= lower)
            & (close < lower)
        )
        utc_date = features["timestamp"].dt.strftime("%Y-%m-%d")
        first_breakout = (long | short).fillna(False).astype(int).groupby(utc_date).cumsum().eq(1)
        long = long & first_breakout
        short = short & first_breakout
    elif family == "robust_regime_momentum":
        fast = features[f"EMA{candidate['ema_fast']}"]
        slow = features[f"EMA{candidate['ema_slow']}"]
        atr = features["ATR"]
        touch_atr = float(candidate["touch_atr"])
        pullback_bars = int(candidate["pullback_bars"])
        touch_long = features["mid_low"] <= (fast + touch_atr * atr)
        touch_short = features["mid_high"] >= (fast - touch_atr * atr)
        recent_touch_long = (
            touch_long.rolling(pullback_bars, min_periods=1)
            .max().shift(1).fillna(0).astype(bool)
        )
        recent_touch_short = (
            touch_short.rolling(pullback_bars, min_periods=1)
            .max().shift(1).fillna(0).astype(bool)
        )
        h1_up = features["H1_TREND_UP"].fillna(False).astype(bool)
        h1_down = features["H1_TREND_DOWN"].fillna(False).astype(bool)
        atr_ratio = features["ATR_RATIO"]
        long = (
            h1_up
            & (fast > slow)
            & (adx >= float(candidate["adx_min"]))
            & (close > features["mid_open"])
            & recent_touch_long
            & (close > fast)
            & atr_ratio.between(
                float(candidate["vol_min"]),
                float(candidate["vol_max"]),
                inclusive="both",
            )
        )
        short = (
            h1_down
            & (fast < slow)
            & (adx >= float(candidate["adx_min"]))
            & (close < features["mid_open"])
            & recent_touch_short
            & (close < fast)
            & atr_ratio.between(
                float(candidate["vol_min"]),
                float(candidate["vol_max"]),
                inclusive="both",
            )
        )
    else:
        raise ValueError(f"XAUUSD_DISCOVERY_UNKNOWN_FAMILY:{family}")

    signal.loc[long.fillna(False)] = 1
    signal.loc[short.fillna(False)] = -1
    # London / New York day-session only. The adapter separately enforces a
    # hard flat before the configured broker rollover.
    allowed_hour = features["timestamp"].dt.hour.between(7, 19)
    signal.loc[~allowed_hour] = 0
    return signal


def _profit_factor(value: Any) -> float:
    if value == "inf":
        return 3.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(number, 3.0) if math.isfinite(number) else 3.0


def run_passes(metrics: dict[str, Any], *, min_trades: int, min_pf: float, max_dd_pct: float) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if int(metrics.get("trades", 0)) < min_trades:
        reasons.append(f"trades<{min_trades}")
    if _profit_factor(metrics.get("profit_factor", 0.0)) < min_pf:
        reasons.append(f"profit_factor<{min_pf}")
    if float(metrics.get("expectancy_R", 0.0)) <= 0:
        reasons.append("expectancy_not_positive")
    if float(metrics.get("max_dd_pct", 100.0)) > max_dd_pct:
        reasons.append(f"max_dd_pct>{max_dd_pct}")
    if int(metrics.get("gap_exit_assumption_trades", 0)) != 0:
        reasons.append("gap_exit_assumptions_present")
    if metrics.get("entries_equal_exits") is not True:
        reasons.append("entries_exits_mismatch")
    return not reasons, reasons


def _execution_frame(raw: pd.DataFrame, features: pd.DataFrame, candidate: dict[str, Any]) -> pd.DataFrame:
    frame = raw.copy()
    frame["signal"] = build_signals(features, candidate).to_numpy(dtype=int)
    frame["ATR"] = features["ATR"].to_numpy(dtype=float)
    # The adapter guarantees no position crosses a UTC session or an intraday
    # gap. Zero financing is valid only under that explicitly intraday contract.
    frame["financing_long_usd_per_oz"] = 0.0
    frame["financing_short_usd_per_oz"] = 0.0
    return frame


def evaluate_year(
    raw: pd.DataFrame,
    features: pd.DataFrame,
    candidate: dict[str, Any],
    *,
    year: int,
    commission_usd_per_oz: float,
    slippage_usd_per_oz_per_side: float,
) -> dict[str, Any]:
    frame = _execution_frame(raw, features, candidate)
    mask = frame["timestamp"].dt.year.eq(year)
    if not mask.any():
        raise ValueError(f"XAUUSD_DISCOVERY_YEAR_EMPTY:{year}")
    cfg = XAUUSDExecutionConfig(
        slippage_usd_per_oz_per_side=slippage_usd_per_oz_per_side,
        commission_usd_per_oz_round_turn=commission_usd_per_oz,
        atr_stop_mult=float(candidate["atr_stop_mult"]),
        reward_risk=float(candidate["reward_risk"]),
        risk_fraction=RISK_FRACTION,
        max_holding_bars=int(candidate["max_holding_bars"]),
        blocked_entry_utc_hours=(20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6),
    )
    result, _trades = run_xauusd_intraday(
        frame.loc[mask].reset_index(drop=True),
        cfg,
        flatten_by_utc=FLATTEN_BY_UTC,
        earliest_rollover_utc=EARLIEST_ROLLOVER_UTC,
        indicator_warmup_bars_after_gap=MAX_INDICATOR_WARMUP_AFTER_GAP,
    )
    return result


def _candidate_training_results(
    raw: pd.DataFrame,
    features: pd.DataFrame,
    candidate: dict[str, Any],
    *,
    commission_usd_per_oz: float,
    base_slippage: float,
) -> dict[str, Any]:
    stress_slippage = max(base_slippage * 2.0, base_slippage + 0.10)
    scenarios = {
        "base": base_slippage,
        "stress": stress_slippage,
    }
    output: dict[str, Any] = {"candidate": candidate, "scenarios": {}}
    for scenario, slippage in scenarios.items():
        yearly = {}
        for year in TRAIN_YEARS:
            result = evaluate_year(
                raw,
                features,
                candidate,
                year=year,
                commission_usd_per_oz=commission_usd_per_oz,
                slippage_usd_per_oz_per_side=slippage,
            )
            passed, reasons = run_passes(result, min_trades=50, min_pf=1.05, max_dd_pct=20.0)
            yearly[str(year)] = {"metrics": result, "gate_pass": passed, "rejection_reasons": reasons}
        output["scenarios"][scenario] = {
            "slippage_usd_per_oz_per_side": slippage,
            "years": yearly,
            "all_years_pass": all(item["gate_pass"] for item in yearly.values()),
        }
    output["train_qualified"] = all(item["all_years_pass"] for item in output["scenarios"].values())
    return output


def _rank_key(item: dict[str, Any]) -> tuple[float, float, float, float]:
    metrics = [
        record["metrics"]
        for scenario in item["scenarios"].values()
        for record in scenario["years"].values()
    ]
    minimum_expectancy = min(float(m["expectancy_R"]) for m in metrics)
    minimum_pf = min(_profit_factor(m["profit_factor"]) for m in metrics)
    maximum_dd = max(float(m["max_dd_pct"]) for m in metrics)
    total_r = sum(float(m["total_R"]) for m in metrics)
    return (minimum_expectancy, minimum_pf, -maximum_dd, total_r)


def run_discovery(
    train_raw: pd.DataFrame,
    validation_raw: pd.DataFrame,
    *,
    commission_usd_per_oz: float,
    slippage_usd_per_oz_per_side: float,
) -> dict[str, Any]:
    if not math.isfinite(commission_usd_per_oz) or commission_usd_per_oz < 0:
        raise ValueError("XAUUSD_COMMISSION_INPUT_INVALID")
    if not math.isfinite(slippage_usd_per_oz_per_side) or slippage_usd_per_oz_per_side < 0:
        raise ValueError("XAUUSD_SLIPPAGE_INPUT_INVALID")
    if set(train_raw["timestamp"].dt.year.unique()) != set(TRAIN_YEARS):
        raise ValueError("XAUUSD_DISCOVERY_TRAINING_YEARS_MUST_BE_2021_2023")
    if set(validation_raw["timestamp"].dt.year.unique()) != {2025}:
        raise ValueError("XAUUSD_DISCOVERY_VALIDATION_MUST_BE_2025_ONLY")

    train_features = build_features(train_raw)
    validation_features = build_features(validation_raw)
    candidates = [
        _candidate_training_results(
            train_raw,
            train_features,
            candidate,
            commission_usd_per_oz=commission_usd_per_oz,
            base_slippage=slippage_usd_per_oz_per_side,
        )
        for candidate in CANDIDATES
    ]
    candidates.sort(key=_rank_key, reverse=True)
    eligible = [item for item in candidates if item["train_qualified"]]

    validation_result = None
    selected = None
    status = "NO_TRAIN_CANDIDATE_PASSED_BASE_AND_STRESS_GATES"
    if eligible:
        # Only the top candidate selected entirely on 2021-2023 is opened on
        # 2025. A failed validation is final; no runner-up is tried.
        selected = eligible[0]
        candidate = selected["candidate"]
        stress_slippage = max(
            slippage_usd_per_oz_per_side * 2.0,
            slippage_usd_per_oz_per_side + 0.10,
        )
        scenarios = {}
        for name, slippage in (
            ("base", slippage_usd_per_oz_per_side),
            ("stress", stress_slippage),
        ):
            result = evaluate_year(
                validation_raw,
                validation_features,
                candidate,
                year=2025,
                commission_usd_per_oz=commission_usd_per_oz,
                slippage_usd_per_oz_per_side=slippage,
            )
            passed, reasons = run_passes(result, min_trades=50, min_pf=1.05, max_dd_pct=25.0)
            scenarios[name] = {
                "slippage_usd_per_oz_per_side": slippage,
                "metrics": result,
                "gate_pass": passed,
                "rejection_reasons": reasons,
            }
        validation_result = {
            "candidate_id": candidate["id"],
            "scenarios": scenarios,
            "validation_pass": all(item["gate_pass"] for item in scenarios.values()),
            "runner_up_tested": False,
            "policy": "one_train_selected_candidate_only_no_validation_fallback",
        }
        status = (
            "VALIDATION_PASS_FREEZE_AND_CODE_PARITY_REQUIRED"
            if validation_result["validation_pass"]
            else "VALIDATION_NO_GO_NO_RUNNER_UP"
        )

    return {
        "schema": "forexai.xauusd_intraday_preregistered_discovery.v1",
        "status": status,
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "training_period_utc": ["2021-01-01", "2024-01-01"],
        "validation_period_utc": [VALIDATION_START, VALIDATION_END],
        "excluded_periods": {
            "2024": "excluded_from_candidate_selection_G23_already_consumed_holdout",
            "2026": "untouched_one_time_blind_holdout_not_loaded",
        },
        "candidate_count": len(CANDIDATES),
        "candidate_set": candidates,
        "selected_on_training_only": selected["candidate"] if selected else None,
        "validation": validation_result,
        "cost_model": {
            "commission_usd_per_oz_round_turn": commission_usd_per_oz,
            "base_slippage_usd_per_oz_per_side": slippage_usd_per_oz_per_side,
            "stress_slippage_usd_per_oz_per_side": max(slippage_usd_per_oz_per_side * 2.0, slippage_usd_per_oz_per_side + 0.10),
            "spread_source": "observed BID/ASK quotes in Dukascopy data; not charged a second time",
            "commission_and_slippage_basis": "explicit workflow inputs; slippage stress is a scenario, not a measured fill statistic",
            "financing": "zero only because the adapter forces intraday liquidation before UTC rollover",
        },
        "execution_model": {
            "signal": "fully_closed_M5_bar",
            "entry": "next_bar_open_executable_quote_side",
            "exit": "opposite_executable_quote_side",
            "same_bar_stop_target": "stop_first",
            "stop_gap": "worse_open",
            "position_limit": 1,
            "risk_fraction": RISK_FRACTION,
            "flatten_by_utc": FLATTEN_BY_UTC,
            "blocked_entry_utc_hours": [20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6],
            "indicator_warmup_bars_after_intraday_gap": MAX_INDICATOR_WARMUP_AFTER_GAP,
            "gap_exit_assumption_trades_must_equal": 0,
        },
        "data_policy": {
            "real_data_required": True,
            "synthetic_data": False,
            "filled_bars": 0,
            "backtest_periods_loaded": ["2021-2023", "2025"],
            "2024_loaded": False,
            "2026_loaded": False,
        },
        "promotion": {
            "research_only": True,
            "demo_authorized": False,
            "live_authorized": False,
            "orders_submitted": False,
        },
        "code_sha256": sha256_file(Path(__file__)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preregistered cost-aware XAUUSD M5 discovery")
    parser.add_argument("--train-root", type=Path, required=True)
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--commission-usd-per-oz-round-turn", type=float, required=True)
    parser.add_argument("--slippage-usd-per-oz-per-side", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    train, train_audit = load_training(args.train_root)
    validation, validation_audit = load_validation(args.validation_root)
    report = run_discovery(
        train,
        validation,
        commission_usd_per_oz=args.commission_usd_per_oz_round_turn,
        slippage_usd_per_oz_per_side=args.slippage_usd_per_oz_per_side,
    )
    report["data_audit"] = {
        "training_annual_files": train_audit,
        "validation_annual_file": validation_audit,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "candidate_count": report["candidate_count"],
        "train_qualified": sum(bool(item["train_qualified"]) for item in report["candidate_set"]),
        "selected_candidate": (report["selected_on_training_only"] or {}).get("id"),
        "validation_pass": (report["validation"] or {}).get("validation_pass"),
        "2024_loaded": report["data_policy"]["2024_loaded"],
        "2026_loaded": report["data_policy"]["2026_loaded"],
        "demo_authorized": report["promotion"]["demo_authorized"],
        "orders_submitted": report["promotion"]["orders_submitted"],
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
