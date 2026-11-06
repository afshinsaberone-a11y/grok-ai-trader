"""Acquire and qualify fresh XAUUSD M5 BID/ASK data for 2025-2026.

Each shard starts from real Dukascopy M1 BID/ASK source files, aggregates only
five complete consecutive M1 bars, and independently reconciles persisted M5
prices and volumes back to those M1 observations. No bars are synthesized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

M5_PRICE_VOLUME_COLUMNS = (
    "bid_open", "bid_high", "bid_low", "bid_close", "bid_volume",
    "ask_open", "ask_high", "ask_low", "ask_close", "ask_volume",
)
SHARDS = {
    "2025-Q1": ("2025-01-01", "2025-04-01"),
    "2025-Q2": ("2025-04-01", "2025-07-01"),
    "2025-Q3": ("2025-07-01", "2025-10-01"),
    "2025-Q4": ("2025-10-01", "2026-01-01"),
    "2026-Q1": ("2026-01-01", "2026-04-01"),
    "2026-Q2": ("2026-04-01", "2026-07-01"),
    "2026-Q3": ("2026-07-01", "2026-10-01"),
    "2026-Q4-to-2026-11": ("2026-10-01", "2026-11-01"),
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gap_audit(data: pd.DataFrame, timeframe: str) -> dict[str, Any]:
    expected_minutes = {"M1": 1, "M5": 5}.get(timeframe)
    if expected_minutes is None:
        raise ValueError("G24_GAP_AUDIT_TIMEFRAME_INVALID")
    ts = pd.to_datetime(data["timestamp"], utc=True).reset_index(drop=True)
    gaps = []
    same_day = 0
    for previous, current in zip(ts.iloc[:-1], ts.iloc[1:]):
        delta = current - previous
        if delta > pd.Timedelta(minutes=expected_minutes):
            within_day = current.date() == previous.date()
            same_day += int(within_day)
            if len(gaps) < 50:
                gaps.append({
                    "previous_utc": previous.isoformat(),
                    "next_utc": current.isoformat(),
                    "elapsed_minutes": int(delta.total_seconds() // 60),
                    "same_utc_date": within_day,
                })
    gap_count = sum(
        1 for a, b in zip(ts.iloc[:-1], ts.iloc[1:])
        if b - a > pd.Timedelta(minutes=expected_minutes)
    )
    return {
        "gap_count": int(gap_count),
        "same_utc_date_gap_count": same_day,
        "examples": gaps,
    }


def coverage_thresholds(start: date, end: date) -> dict[str, int]:
    days = (end - start).days
    if days < 1:
        raise ValueError("G24_INVALID_DATE_RANGE")
    if days >= 80:
        return {"min_m1_rows": 45_000, "min_m5_rows": 9_000, "min_paired_days": 45}
    return {"min_m1_rows": 12_000, "min_m5_rows": 2_200, "min_paired_days": 15}


def reconcile_m5_to_m1(
    m1: pd.DataFrame,
    m5: pd.DataFrame,
    *,
    tolerance: float = 1.1e-5,
) -> dict[str, Any]:
    """Independently compare every M5 BID/ASK OHLCV value with its five M1 bars."""
    required_m1 = {"timestamp", *M5_PRICE_VOLUME_COLUMNS}
    required_m5 = {"timestamp", *M5_PRICE_VOLUME_COLUMNS, "spread_open", "spread_close"}
    if required_m1.difference(m1.columns) or required_m5.difference(m5.columns):
        raise ValueError("G24_RECONCILIATION_COLUMNS_MISSING")
    src = m1.copy()
    dst = m5.copy()
    src["timestamp"] = pd.to_datetime(src["timestamp"], utc=True, errors="raise")
    dst["timestamp"] = pd.to_datetime(dst["timestamp"], utc=True, errors="raise")
    if (
        src.empty
        or dst.empty
        or src["timestamp"].duplicated().any()
        or dst["timestamp"].duplicated().any()
    ):
        raise ValueError("G24_RECONCILIATION_EMPTY_OR_DUPLICATE")
    if not src["timestamp"].is_monotonic_increasing or not dst["timestamp"].is_monotonic_increasing:
        raise ValueError("G24_RECONCILIATION_ORDER_INVALID")
    if (
        not dst["timestamp"].dt.minute.mod(5).eq(0).all()
        or not dst["timestamp"].dt.second.eq(0).all()
    ):
        raise ValueError("G24_RECONCILIATION_M5_ALIGNMENT_INVALID")

    indexed = src.set_index("timestamp", drop=False)
    compared = 0
    max_delta = 0.0
    for row in dst.itertuples(index=False):
        stamp = pd.Timestamp(row.timestamp)
        expected_times = pd.date_range(stamp, periods=5, freq="min", tz="UTC")
        if not expected_times.isin(indexed.index).all():
            raise ValueError(f"G24_M5_SOURCE_MINUTES_MISSING:{stamp.isoformat()}")
        source = indexed.loc[expected_times]
        expected = {
            "bid_open": source["bid_open"].iloc[0],
            "bid_high": source["bid_high"].max(),
            "bid_low": source["bid_low"].min(),
            "bid_close": source["bid_close"].iloc[-1],
            "bid_volume": source["bid_volume"].sum(),
            "ask_open": source["ask_open"].iloc[0],
            "ask_high": source["ask_high"].max(),
            "ask_low": source["ask_low"].min(),
            "ask_close": source["ask_close"].iloc[-1],
            "ask_volume": source["ask_volume"].sum(),
        }
        for column, expected_value in expected.items():
            delta = abs(float(getattr(row, column)) - float(expected_value))
            max_delta = max(max_delta, delta)
            if delta > tolerance:
                raise ValueError(
                    f"G24_M5_RECONCILIATION_FAILED:{stamp.isoformat()}:{column}:{delta}"
                )
        if abs(float(row.ask_open) - float(row.bid_open) - float(row.spread_open)) > tolerance:
            raise ValueError(f"G24_M5_OPEN_SPREAD_RECONCILIATION_FAILED:{stamp.isoformat()}")
        if abs(float(row.ask_close) - float(row.bid_close) - float(row.spread_close)) > tolerance:
            raise ValueError(f"G24_M5_CLOSE_SPREAD_RECONCILIATION_FAILED:{stamp.isoformat()}")
        compared += 1
    return {"compared_bars": compared, "max_abs_delta": max_delta, "tolerance": tolerance}


def build_shard(
    *,
    shard: str,
    start: date,
    end: date,
    output_root: Path,
    timeout: int = 60,
    retries: int = 8,
    throttle_retries: int = 12,
) -> dict[str, Any]:
    if shard not in SHARDS or SHARDS[shard] != (start.isoformat(), end.isoformat()):
        raise ValueError("G24_SHARD_DATE_BINDING_MISMATCH")
    from research.real_data.dukascopy_xauusd_ingest import ingest, resample_m1_to_m5

    output_root.mkdir(parents=True, exist_ok=True)
    ingest_root = output_root / "m1-ingest"
    result = ingest(
        start,
        end,
        ingest_root,
        timeframe="M1",
        timeout=timeout,
        retries=retries,
        throttle_retries=throttle_retries,
    )
    m1_path = Path(result["dataset"])
    m1_manifest_path = Path(result["manifest"])
    m1_manifest = json.loads(m1_manifest_path.read_text(encoding="utf-8"))
    if m1_manifest.get("symbol") != "XAUUSD" or m1_manifest.get("timeframe") != "M1":
        raise ValueError("G24_M1_MANIFEST_SCOPE_MISMATCH")
    if (
        m1_manifest.get("requested_start_utc") != start.isoformat()
        or m1_manifest.get("requested_end_exclusive_utc") != end.isoformat()
    ):
        raise ValueError("G24_M1_MANIFEST_DATE_SCOPE_MISMATCH")
    if (
        m1_manifest.get("synthetic_data") is not False
        or m1_manifest.get("backtest_run") is not False
    ):
        raise ValueError("G24_M1_SYNTHETIC_OR_BACKTEST_ARTIFACT_REJECTED")
    if m1_manifest.get("data_sha256") != sha256_file(m1_path):
        raise ValueError("G24_M1_MANIFEST_HASH_MISMATCH")

    m1 = pd.read_csv(m1_path)
    m1["timestamp"] = pd.to_datetime(m1["timestamp"], utc=True, errors="raise")
    thresholds = coverage_thresholds(start, end)
    if len(m1) < thresholds["min_m1_rows"]:
        raise ValueError(f"G24_M1_COVERAGE_TOO_LOW:{len(m1)}:{thresholds['min_m1_rows']}")
    if m1["timestamp"].duplicated().any() or not m1["timestamp"].is_monotonic_increasing:
        raise ValueError("G24_M1_TIMESTAMP_INVARIANT_FAILED")
    within_range = (
        (m1["timestamp"] >= pd.Timestamp(start, tz="UTC"))
        & (m1["timestamp"] < pd.Timestamp(end, tz="UTC"))
    )
    if not within_range.all():
        raise ValueError("G24_M1_OUTSIDE_REQUESTED_RANGE")
    for point in ("open", "high", "low", "close"):
        if (m1[f"ask_{point}"] < m1[f"bid_{point}"]).any():
            raise ValueError(f"G24_M1_CROSSED_{point.upper()}_QUOTE")
    if (m1[["spread_open", "spread_close"]] < 0).any().any():
        raise ValueError("G24_M1_NEGATIVE_SPREAD")
    paired_days = sum(
        1 for item in m1_manifest.get("period_audit", [])
        if item.get("status") == "PAIRED"
    )
    if paired_days < thresholds["min_paired_days"]:
        raise ValueError(f"G24_PAIRED_SOURCE_DAYS_TOO_LOW:{paired_days}")

    m5, aggregation = resample_m1_to_m5(m1)
    if len(m5) < thresholds["min_m5_rows"]:
        raise ValueError(f"G24_M5_COVERAGE_TOO_LOW:{len(m5)}:{thresholds['min_m5_rows']}")
    if aggregation.get("filled_bars") != 0 or aggregation.get("synthetic_data") is not False:
        raise ValueError("G24_SYNTHETIC_M5_REJECTED")
    m5_root = output_root / "normalized"
    m5_root.mkdir(parents=True, exist_ok=True)
    dates = f"{start:%Y%m%d}_{end:%Y%m%d}"
    m5_path = m5_root / f"XAUUSD_M5_BIDASK_{dates}.csv"
    m5.to_csv(m5_path, index=False, float_format="%.5f", date_format="%Y-%m-%dT%H:%M:%SZ")
    m5 = pd.read_csv(m5_path)
    m5["timestamp"] = pd.to_datetime(m5["timestamp"], utc=True, errors="raise")
    audit = reconcile_m5_to_m1(m1, m5)
    if audit["compared_bars"] != len(m5):
        raise ValueError("G24_M5_RECONCILIATION_COUNT_MISMATCH")

    m1_gaps = gap_audit(m1, "M1")
    m5_gaps = gap_audit(m5, "M5")
    manifest = {
        "schema": "forexai.real_data.xauusd_bidask_m5_fresh_oos_shard.v1",
        "status": "REAL_M5_SHARD_PASS_GAPS_PRESERVED",
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "source_timeframe": "M1",
        "shard": shard,
        "requested_start_utc": start.isoformat(),
        "requested_end_exclusive_utc": end.isoformat(),
        "rows": int(len(m5)),
        "first_utc": m5.timestamp.min().isoformat(),
        "last_utc": m5.timestamp.max().isoformat(),
        "m1_rows": int(len(m1)),
        "paired_source_days": paired_days,
        "source_m1_data_sha256": sha256_file(m1_path),
        "source_m1_manifest_sha256": sha256_file(m1_manifest_path),
        "data_sha256": sha256_file(m5_path),
        "aggregation_audit": aggregation,
        "reconciliation_audit": audit,
        "m1_gap_audit": m1_gaps,
        "m5_gap_audit": m5_gaps,
        "synthetic_data": False,
        "filled_bars": 0,
        "backtest_run": False,
        "strategy_research_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "orders_submitted": False,
    }
    manifest_path = m5_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    report = {
        "schema": "forexai.g24.xauusd_m5_fresh_oos_shard.v1",
        "status": "REAL_XAUUSD_M5_FRESH_OOS_SHARD_PASS",
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "shard": shard,
        "m1_path": str(m1_path.relative_to(output_root)),
        "m1_manifest_path": str(m1_manifest_path.relative_to(output_root)),
        "m5_path": str(m5_path.relative_to(output_root)),
        "m5_manifest_path": str(manifest_path.relative_to(output_root)),
        "m1_rows": int(len(m1)),
        "m5_rows": int(len(m5)),
        "paired_source_days": paired_days,
        "m1_sha256": sha256_file(m1_path),
        "m1_manifest_sha256": sha256_file(m1_manifest_path),
        "m5_sha256": sha256_file(m5_path),
        "m5_manifest_sha256": sha256_file(manifest_path),
        "reconciliation_audit": audit,
        "m1_gap_audit": m1_gaps,
        "m5_gap_audit": m5_gaps,
        "synthetic_data": False,
        "filled_bars": 0,
        "backtest_run": False,
        "orders_submitted": False,
    }
    report_path = output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def assemble(data_root: Path, output_root: Path) -> dict[str, Any]:
    reports: dict[str, dict[str, Any]] = {}
    report_paths = list(data_root.rglob("report.json"))
    for shard in SHARDS:
        matches = []
        for path in report_paths:
            item = json.loads(path.read_text(encoding="utf-8"))
            if item.get("shard") == shard:
                matches.append((path, item))
        if len(matches) != 1:
            raise FileNotFoundError(f"G24_SHARD_REPORT_MISSING_OR_DUPLICATE:{shard}")
        report_path, item = matches[0]
        base = report_path.parent
        m1_path = base / item["m1_path"]
        m1_manifest_path = base / item["m1_manifest_path"]
        m5_path = base / item["m5_path"]
        manifest_path = base / item["m5_manifest_path"]
        if (
            sha256_file(m1_path) != item["m1_sha256"]
            or sha256_file(m1_manifest_path) != item["m1_manifest_sha256"]
            or sha256_file(m5_path) != item["m5_sha256"]
            or sha256_file(manifest_path) != item["m5_manifest_sha256"]
        ):
            raise ValueError(f"G24_SHARD_HASH_MISMATCH:{shard}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("symbol") != "XAUUSD" or manifest.get("timeframe") != "M5":
            raise ValueError(f"G24_SHARD_MANIFEST_SCOPE_MISMATCH:{shard}")
        if (
            manifest.get("synthetic_data") is not False
            or manifest.get("filled_bars") != 0
            or manifest.get("backtest_run") is not False
        ):
            raise ValueError(f"G24_SHARD_SYNTHETIC_DATA_REJECTED:{shard}")
        reports[shard] = {"report": item, "data_path": m5_path}

    output_root.mkdir(parents=True, exist_ok=True)
    windows = {
        "2025": (
            pd.Timestamp("2025-01-01T00:00:00Z"),
            pd.Timestamp("2026-01-01T00:00:00Z"),
        ),
        "2026-01-01_to_2026-11-01": (
            pd.Timestamp("2026-01-01T00:00:00Z"),
            pd.Timestamp("2026-11-01T00:00:00Z"),
        ),
    }
    annual_records: dict[str, Any] = {}
    for label, (start, end) in windows.items():
        frames = []
        used = []
        for shard, entry in reports.items():
            shard_start, shard_end = (
                pd.Timestamp(value, tz="UTC") for value in SHARDS[shard]
            )
            if shard_start < end and shard_end > start:
                frame = pd.read_csv(entry["data_path"])
                frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
                frames.append(frame)
                used.append(shard)
        if not frames:
            raise ValueError(f"G24_ANNUAL_WINDOW_EMPTY:{label}")
        combined = (
            pd.concat(frames, ignore_index=True)
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        combined = combined.loc[
            (combined.timestamp >= start) & (combined.timestamp < end)
        ].copy()
        if (
            combined.empty
            or combined.timestamp.duplicated().any()
            or not combined.timestamp.is_monotonic_increasing
        ):
            raise ValueError(f"G24_ANNUAL_TIMESTAMP_INVARIANT_FAIL:{label}")
        target = output_root / f"XAUUSD_M5_BIDASK_{start:%Y%m%d}_{end:%Y%m%d}.csv"
        combined.to_csv(
            target,
            index=False,
            float_format="%.5f",
            date_format="%Y-%m-%dT%H:%M:%SZ",
        )
        gaps = gap_audit(combined, "M5")
        manifest = {
            "schema": "forexai.real_data.xauusd_bidask_m5_fresh_oos.v1",
            "status": "FRESH_REAL_XAUUSD_M5_DATASET_READY_FOR_PREREGISTERED_RESEARCH",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "start_inclusive_utc": start.isoformat(),
            "end_exclusive_utc": end.isoformat(),
            "first_utc": combined.timestamp.min().isoformat(),
            "last_utc": combined.timestamp.max().isoformat(),
            "rows": int(len(combined)),
            "data_sha256": sha256_file(target),
            "gap_audit": gaps,
            "source_shards": used,
            "synthetic_data": False,
            "filled_bars": 0,
            "backtest_run": False,
            "strategy_research_authorized": False,
            "demo_authorized": False,
            "live_authorized": False,
            "orders_submitted": False,
        }
        manifest_path = target.with_suffix(".manifest.json")
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        annual_records[label] = {
            **manifest,
            "manifest_sha256": sha256_file(manifest_path),
            "file": target.name,
        }

    summary = {
        "schema": "forexai.g24.xauusd_m5_fresh_oos_assembly.v1",
        "status": "FRESH_XAUUSD_M5_2025_2026_READY_GAP_REVIEW_REQUIRED",
        "datasets": annual_records,
        "all_eight_shards_verified": True,
        "synthetic_data": False,
        "filled_bars": 0,
        "backtest_run": False,
        "strategy_research_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "orders_submitted": False,
        "interpretation": (
            "Fresh 2025 and 2026-through-October XAUUSD BID/ASK M5 datasets are "
            "assembled from real M1 source bars. This is data qualification only; "
            "a new preregistered candidate must be frozen before any holdout evaluation."
        ),
    }
    summary_path = output_root / "g24-xauusd-m5-fresh-oos-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    shard_parser = sub.add_parser("shard")
    shard_parser.add_argument("--shard", choices=sorted(SHARDS), required=True)
    shard_parser.add_argument("--start", required=True)
    shard_parser.add_argument("--end", required=True)
    shard_parser.add_argument("--output", type=Path, required=True)
    shard_parser.add_argument("--timeout", type=int, default=60)
    shard_parser.add_argument("--retries", type=int, default=8)
    shard_parser.add_argument("--throttle-retries", type=int, default=12)
    assemble_parser = sub.add_parser("assemble")
    assemble_parser.add_argument("--data-root", type=Path, required=True)
    assemble_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "shard":
        report = build_shard(
            shard=args.shard,
            start=date.fromisoformat(args.start),
            end=date.fromisoformat(args.end),
            output_root=args.output,
            timeout=args.timeout,
            retries=args.retries,
            throttle_retries=args.throttle_retries,
        )
    else:
        report = assemble(args.data_root, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
