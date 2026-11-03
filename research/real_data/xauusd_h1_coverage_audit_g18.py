"""Fail-closed coverage and quote-quality audit for real XAUUSD H1 BID/ASK bars.

This is a data qualification stage only. It does not generate trading signals,
estimate profitability, infer broker commission, or invent swap/financing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA = "forexai.g18.xauusd_h1_coverage_audit.v1"
YEARS = (2021, 2022, 2023, 2024)
PRICE_COLUMNS = (
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
)
REQUIRED_COLUMNS = {"timestamp", *PRICE_COLUMNS, "bid_volume", "ask_volume",
                    "spread_open", "spread_close"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_hash(manifest: dict) -> str:
    source_files = manifest.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        raise ValueError("G18_SOURCE_FILE_INVENTORY_MISSING")
    raw = json.dumps(source_files, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _year_summary(frame: pd.DataFrame) -> dict:
    result = {}
    for year in YEARS:
        part = frame.loc[frame["timestamp"].dt.year == year]
        if part.empty:
            raise ValueError(f"G18_REQUIRED_YEAR_MISSING:{year}")
        months = sorted(part["timestamp"].dt.month.unique().astype(int).tolist())
        result[str(year)] = {
            "rows": int(len(part)),
            "months_present": months,
            "month_count": len(months),
            "first_utc": part["timestamp"].min().isoformat(),
            "last_utc": part["timestamp"].max().isoformat(),
        }
        if len(months) < 10:
            raise ValueError(f"G18_YEAR_COVERAGE_BELOW_10_MONTHS:{year}:{len(months)}")
        if len(part) < 3500:
            raise ValueError(f"G18_YEAR_COVERAGE_TOO_FEW_H1_BARS:{year}:{len(part)}")
    return result


def _spread_summary(values: pd.Series) -> dict:
    x = values.to_numpy(dtype=float)
    return {
        "median_usd_per_oz": round(float(np.median(x)), 6),
        "p90_usd_per_oz": round(float(np.quantile(x, 0.90)), 6),
        "p95_usd_per_oz": round(float(np.quantile(x, 0.95)), 6),
        "max_usd_per_oz": round(float(np.max(x)), 6),
        "min_usd_per_oz": round(float(np.min(x)), 6),
    }


def audit(data_path: str | Path, manifest_path: str | Path) -> dict:
    data, manifest_file = Path(data_path), Path(manifest_path)
    if not data.is_file() or not data.stat().st_size:
        raise ValueError("G18_DATA_MISSING")
    if not manifest_file.is_file():
        raise ValueError("G18_MANIFEST_MISSING")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    if manifest.get("schema") != "forexai.real_data.xauusd_bidask_h1.v1":
        raise ValueError("G18_MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("status") != "INGESTION_ONLY_COVERAGE_REVIEW_REQUIRED":
        raise ValueError("G18_INTAKE_STATUS_UNEXPECTED")
    if manifest.get("symbol") != "XAUUSD" or manifest.get("timeframe") != "H1":
        raise ValueError("G18_SYMBOL_OR_TIMEFRAME_MISMATCH")
    if manifest.get("synthetic_data") is not False or manifest.get("backtest_run") is not False:
        raise ValueError("G18_SOURCE_FLAGS_INVALID")
    if "Dukascopy" not in str(manifest.get("source", "")):
        raise ValueError("G18_SOURCE_NOT_DUKASCOPY")

    data_hash = _sha256(data)
    if manifest.get("data_sha256") != data_hash:
        raise ValueError("G18_DATA_SHA256_MISMATCH")
    source_hash = _source_hash(manifest)
    if manifest.get("source_hash_sha256") != source_hash:
        raise ValueError("G18_SOURCE_SHA256_MISMATCH")

    frame = pd.read_csv(data)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"G18_REQUIRED_COLUMNS_MISSING:{sorted(missing)}")
    if len(frame) != int(manifest.get("rows", -1)):
        raise ValueError("G18_ROW_COUNT_MISMATCH")

    timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    if timestamps.isna().any() or timestamps.duplicated().any() or not timestamps.is_monotonic_increasing:
        raise ValueError("G18_TIMESTAMP_SEQUENCE_INVALID")
    start = pd.Timestamp(manifest["requested_start_utc"], tz="UTC")
    end = pd.Timestamp(manifest["requested_end_exclusive_utc"], tz="UTC")
    if timestamps.min() < start or timestamps.max() >= end:
        raise ValueError("G18_REQUESTED_DATE_WINDOW_VIOLATION")
    if tuple(sorted(set(timestamps.dt.year.astype(int)))) != YEARS:
        raise ValueError("G18_YEAR_SET_MISMATCH")

    frame["timestamp"] = timestamps
    for column in (*PRICE_COLUMNS, "bid_volume", "ask_volume", "spread_open", "spread_close"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if not np.isfinite(frame[column].to_numpy(dtype=float)).all():
            raise ValueError(f"G18_NONFINITE_FIELD:{column}")
    if (frame[list(PRICE_COLUMNS)] <= 0).any().any():
        raise ValueError("G18_NONPOSITIVE_PRICE")
    if (frame[["bid_volume", "ask_volume"]] < 0).any().any():
        raise ValueError("G18_NEGATIVE_VOLUME")
    if (frame[["spread_open", "spread_close"]] < 0).any().any():
        raise ValueError("G18_NEGATIVE_SPREAD")

    for side in ("bid", "ask"):
        op, hi, lo, cl = (frame[f"{side}_{field}"] for field in ("open", "high", "low", "close"))
        if ((hi < np.maximum(op, cl)) | (lo > np.minimum(op, cl)) | (hi < lo)).any():
            raise ValueError(f"G18_{side.upper()}_OHLC_INVARIANT_FAIL")

    open_spread = frame["ask_open"] - frame["bid_open"]
    close_spread = frame["ask_close"] - frame["bid_close"]
    if not np.allclose(open_spread.to_numpy(), frame["spread_open"].to_numpy(), atol=1e-8, rtol=0):
        raise ValueError("G18_OPEN_SPREAD_RECONCILIATION_FAIL")
    if not np.allclose(close_spread.to_numpy(), frame["spread_close"].to_numpy(), atol=1e-8, rtol=0):
        raise ValueError("G18_CLOSE_SPREAD_RECONCILIATION_FAIL")

    delta = frame["timestamp"].diff().dropna()
    gap_mask = delta > pd.Timedelta(hours=1)
    gap_positions = np.flatnonzero(gap_mask.to_numpy()) + 1
    gaps = []
    for idx in gap_positions[:100]:
        previous, next_ = frame.at[idx - 1, "timestamp"], frame.at[idx, "timestamp"]
        gaps.append({
            "previous_utc": previous.isoformat(),
            "next_utc": next_.isoformat(),
            "elapsed_minutes": int((next_ - previous).total_seconds() // 60),
            "same_utc_date": previous.date() == next_.date(),
        })

    daily_gaps = int(sum(
        frame.at[idx - 1, "timestamp"].date() == frame.at[idx, "timestamp"].date()
        for idx in gap_positions
    ))
    long_closure_gaps = int((delta > pd.Timedelta(hours=12)).sum())

    if manifest.get("gap_audit", {}).get("gap_count") != int(gap_mask.sum()):
        raise ValueError("G18_GAP_COUNT_MANIFEST_MISMATCH")

    year_summary = _year_summary(frame)
    result = {
        "schema": SCHEMA,
        "status": "REAL_DATA_COVERAGE_AUDIT_PASS",
        "symbol": "XAUUSD",
        "timeframe": "H1",
        "source": manifest["source"],
        "dataset_id": f"{manifest['requested_start_utc']}_{manifest['requested_end_exclusive_utc']}",
        "rows": int(len(frame)),
        "start_utc": timestamps.min().isoformat(),
        "end_utc": timestamps.max().isoformat(),
        "years": year_summary,
        "data_sha256": data_hash,
        "manifest_sha256": _sha256(manifest_file),
        "source_sha256": source_hash,
        "spread_open": _spread_summary(frame["spread_open"]),
        "spread_close": _spread_summary(frame["spread_close"]),
        "coverage": {
            "gap_count_gt_1h": int(gap_mask.sum()),
            "same_utc_date_gap_count": daily_gaps,
            "long_closure_gap_count_gt_12h": long_closure_gaps,
            "max_gap_minutes": int(delta.max().total_seconds() // 60),
            "gaps_examples_first_100": gaps,
            "missing_bars_filled": 0,
        },
        "data_policy": {
            "real_bid_ask_bars": True,
            "synthetic_data": False,
            "backtest_run": False,
            "commission_inferred": False,
            "financing_inferred": False,
            "2025_loaded": False,
            "2026_plus_loaded": False,
        },
        "next_gate": "BROKER_COST_AND_FINANCING_SOURCE_REQUIRED_BEFORE_STRATEGY_BACKTEST",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit real XAUUSD H1 data coverage and BID/ASK quality")
    parser.add_argument("--data", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(args.data, args.manifest)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "rows": result["rows"],
        "years": result["years"],
        "coverage": {key: value for key, value in result["coverage"].items() if key != "gaps_examples_first_100"},
        "spread_open": result["spread_open"],
        "next_gate": result["next_gate"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
