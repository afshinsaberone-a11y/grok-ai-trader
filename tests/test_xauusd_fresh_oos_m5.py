from __future__ import annotations

import pandas as pd
import pytest

from research.real_data.xauusd_fresh_oos_m5 import (
    SHARDS,
    coverage_thresholds,
    reconcile_m5_to_m1,
)


def fixture_m1() -> pd.DataFrame:
    ts = pd.date_range("2026-10-05T07:00:00Z", periods=5, freq="min")
    return pd.DataFrame({
        "timestamp": ts,
        "bid_open": [2300.00, 2300.10, 2300.20, 2300.15, 2300.25],
        "bid_high": [2300.20, 2300.30, 2300.35, 2300.28, 2300.40],
        "bid_low": [2299.90, 2300.00, 2300.05, 2300.02, 2300.10],
        "bid_close": [2300.10, 2300.20, 2300.15, 2300.25, 2300.30],
        "bid_volume": [1.0, 2.0, 3.0, 4.0, 5.0],
        "ask_open": [2300.20, 2300.30, 2300.40, 2300.35, 2300.45],
        "ask_high": [2300.40, 2300.50, 2300.55, 2300.48, 2300.60],
        "ask_low": [2300.10, 2300.20, 2300.25, 2300.22, 2300.30],
        "ask_close": [2300.30, 2300.40, 2300.35, 2300.45, 2300.50],
        "ask_volume": [1.0, 2.0, 3.0, 4.0, 5.0],
    })


def m5_fixture(m1: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "timestamp": [m1.timestamp.iloc[0]],
        "bid_open": [m1.bid_open.iloc[0]],
        "bid_high": [m1.bid_high.max()],
        "bid_low": [m1.bid_low.min()],
        "bid_close": [m1.bid_close.iloc[-1]],
        "bid_volume": [m1.bid_volume.sum()],
        "ask_open": [m1.ask_open.iloc[0]],
        "ask_high": [m1.ask_high.max()],
        "ask_low": [m1.ask_low.min()],
        "ask_close": [m1.ask_close.iloc[-1]],
        "ask_volume": [m1.ask_volume.sum()],
        "spread_open": [m1.ask_open.iloc[0] - m1.bid_open.iloc[0]],
        "spread_close": [m1.ask_close.iloc[-1] - m1.bid_close.iloc[-1]],
    })


def test_fresh_oos_shards_cover_2025_through_october_2026() -> None:
    assert len(SHARDS) == 8
    assert SHARDS["2025-Q1"] == ("2025-01-01", "2025-04-01")
    assert SHARDS["2026-Q4-to-2026-11"] == ("2026-10-01", "2026-11-01")


def test_partial_month_uses_lower_but_nontrivial_coverage_gate() -> None:
    q = coverage_thresholds(
        pd.Timestamp("2026-10-01").date(),
        pd.Timestamp("2026-11-01").date(),
    )
    assert q == {"min_m1_rows": 12000, "min_m5_rows": 2200, "min_paired_days": 15}


def test_quarter_uses_full_coverage_gate() -> None:
    q = coverage_thresholds(
        pd.Timestamp("2025-01-01").date(),
        pd.Timestamp("2025-04-01").date(),
    )
    assert q == {"min_m1_rows": 45000, "min_m5_rows": 9000, "min_paired_days": 45}


def test_every_persisted_m5_bar_reconciles_to_exact_five_m1_bars() -> None:
    m1 = fixture_m1()
    audit = reconcile_m5_to_m1(m1, m5_fixture(m1))
    assert audit["compared_bars"] == 1
    assert audit["max_abs_delta"] == pytest.approx(0.0)


def test_reconciliation_rejects_modified_persisted_m5_price() -> None:
    m1 = fixture_m1()
    m5 = m5_fixture(m1)
    m5.loc[0, "bid_close"] += 0.01
    m5.loc[0, "spread_close"] -= 0.01
    with pytest.raises(ValueError, match="G24_M5_RECONCILIATION_FAILED"):
        reconcile_m5_to_m1(m1, m5)


def test_reconciliation_rejects_missing_source_minute() -> None:
    m1 = fixture_m1().drop(index=2).reset_index(drop=True)
    with pytest.raises(ValueError, match="G24_M5_SOURCE_MINUTES_MISSING"):
        reconcile_m5_to_m1(fixture_m1().drop(index=2).reset_index(drop=True), m5_fixture(fixture_m1()))
