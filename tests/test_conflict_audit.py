import pandas as pd
import pytest

from research.real_data.conflict_audit import audit_timestamp_conflicts


def test_exact_duplicate_is_not_a_conflict():
    ts = pd.Timestamp("2026-07-01T00:00:00Z")
    frame = pd.DataFrame([
        [ts, 1.1, 1.2, 1.0, 1.15, 10.0],
        [ts, 1.1, 1.2, 1.0, 1.15, 10.0],
    ], columns=["timestamp", "open", "high", "low", "close", "volume"])
    report, summary = audit_timestamp_conflicts(frame)
    assert summary.duplicate_timestamps == 1
    assert summary.conflicting_timestamps == 0
    assert report.empty


def test_conflicting_duplicate_is_a_conflict():
    ts = pd.Timestamp("2026-07-05T22:31:00Z")
    frame = pd.DataFrame([
        [ts, 1.1, 1.2, 1.0, 1.15, 10.0],
        [ts, 1.1, 1.21, 1.0, 1.15, 11.0],
    ], columns=["timestamp", "open", "high", "low", "close", "volume"])
    report, summary = audit_timestamp_conflicts(frame)
    assert summary.duplicate_timestamps == 1
    assert summary.conflicting_timestamps == 1
    assert len(report) == 2
    assert summary.max_abs_ohlc_diff == pytest.approx(0.21)


def test_non_duplicate_data_has_empty_audit():
    ts = pd.date_range("2026-07-05T22:30:00Z", periods=2, freq="min")
    frame = pd.DataFrame([
        [ts[0], 1.1, 1.2, 1.0, 1.15, 10.0],
        [ts[1], 1.15, 1.25, 1.1, 1.2, 12.0],
    ], columns=["timestamp", "open", "high", "low", "close", "volume"])
    report, summary = audit_timestamp_conflicts(frame)
    assert summary.conflicting_timestamps == 0
    assert report.empty
