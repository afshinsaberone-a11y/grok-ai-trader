from datetime import datetime, timezone
import math
from datetime import datetime, timezone

import numpy as np
import pytest

from tools.mt5_xauusd_tick_spread_history_probe import (
    _extract_spreads_and_times,
    summarize_spread_by_utc_time,
    summarize_spread_points,
)


def test_spread_distribution_converts_points_to_price_and_lot_cost():
    result = summarize_spread_points(
        [8, 10, 12, 14],
        point=0.01,
        tick_size=0.01,
        tick_value=1.0,
    )

    assert result["spread_points"]["count"] == 4
    assert result["spread_points"]["mean"] == pytest.approx(11.0)
    assert result["spread_points"]["median"] == pytest.approx(11.0)
    assert result["spread_points"]["p95"] == pytest.approx(13.7)
    assert result["spread_price_per_oz_quote_currency"]["mean"] == pytest.approx(0.11)
    assert result["spread_cost_per_standard_lot_account_currency"]["mean"] == pytest.approx(11.0)


def test_invalid_or_negative_spread_values_are_excluded():
    result = summarize_spread_points(
        [8, None, -1, float("nan"), float("inf"), "not-a-number"],
        point=0.01,
        tick_size=0.01,
        tick_value=1.0,
    )

    assert result["spread_points"]["count"] == 1
    assert result["spread_points"]["mean"] == pytest.approx(8.0)


def test_empty_spread_sample_is_explicitly_empty():
    result = summarize_spread_points(
        [], point=0.01, tick_size=0.01, tick_value=1.0
    )

    assert result["spread_points"]["count"] == 0
    assert result["spread_points"]["p95"] is None
    assert result["spread_cost_per_standard_lot_account_currency"]["mean"] is None


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("point", 0.0, "POINT_INVALID"),
        ("tick_size", 0.0, "TICK_SIZE_INVALID"),
        ("tick_value", -1.0, "TICK_VALUE_INVALID"),
    ],
)
def test_invalid_symbol_units_fail_closed(field, value, message):
    units = {"point": 0.01, "tick_size": 0.01, "tick_value": 1.0}
    units[field] = value
    with pytest.raises(ValueError, match=message):
        summarize_spread_points([8], **units)


def test_weighted_spread_distribution_represents_segment_tick_volume():
    result = summarize_spread_points(
        [10, 20],
        point=0.01,
        tick_size=0.01,
        tick_value=1.0,
        weights=[9.0, 1.0],
    )

    stats = result["spread_points"]
    assert stats["count"] == 2
    assert stats["represented_tick_weight"] == pytest.approx(10.0)
    assert stats["mean"] == pytest.approx(11.0)
    assert stats["median"] == pytest.approx(10.0)
    assert stats["p95"] == pytest.approx(20.0)
    assert stats["p99"] == pytest.approx(20.0)
    assert result["statistical_weighting"] == "represented_quote_tick_count"


def test_weight_length_mismatch_fails_closed():
    with pytest.raises(ValueError, match="SAMPLE_WEIGHTS_LENGTH_MISMATCH"):
        summarize_spread_points(
            [8, 10], point=0.01, tick_size=0.01, tick_value=1.0, weights=[1.0]
        )


def test_tick_quotes_are_strictly_filtered_to_half_open_utc_segment():
    ticks = np.array(
        [
            (100.0, 101.0, 999),   # before start
            (100.0, 101.0, 1000),  # inclusive start
            (100.0, 103.0, 1500),  # inside
            (100.0, 99.0, 1750),   # crossed quote inside
            (100.0, 105.0, 2000),  # exclusive end
        ],
        dtype=[("bid", "f8"), ("ask", "f8"), ("time_msc", "i8")],
    )

    spreads, timestamps, outside = _extract_spreads_and_times(
        ticks, 1.0, start_ms=1000, end_ms=2000
    )

    assert spreads.tolist() == pytest.approx([1.0, 3.0])
    assert timestamps.tolist() == [1000, 1500]
    assert outside == 2


def test_spread_time_buckets_use_utc_and_represented_tick_weights():
    times = [
        int(datetime(2026, 1, 5, 0, 1, tzinfo=timezone.utc).timestamp() * 1000),
        int(datetime(2026, 1, 5, 0, 2, tzinfo=timezone.utc).timestamp() * 1000),
        int(datetime(2026, 1, 6, 1, 1, tzinfo=timezone.utc).timestamp() * 1000),
    ]
    result = summarize_spread_by_utc_time(
        [10, 20, 30], times, [9.0, 1.0, 2.0]
    )

    hour_zero = next(row for row in result["by_utc_hour"] if row["utc_hour"] == 0)
    assert hour_zero["sampled_quote_ticks"] == 2
    assert hour_zero["spread_points"]["represented_tick_weight"] == pytest.approx(10.0)
    assert hour_zero["spread_points"]["mean"] == pytest.approx(11.0)

    monday_midnight = next(
        row for row in result["by_utc_weekday_hour"]
        if row["utc_weekday"] == 0 and row["utc_hour"] == 0
    )
    assert monday_midnight["spread_points"]["mean"] == pytest.approx(11.0)
    assert result["weekday_numbering"].startswith("Monday=0")


def test_spread_time_buckets_reject_mismatched_input_lengths():
    with pytest.raises(ValueError, match="TIME_BUCKET_INPUT_LENGTH_MISMATCH"):
        summarize_spread_by_utc_time([10, 20], [1], [1.0, 1.0])
