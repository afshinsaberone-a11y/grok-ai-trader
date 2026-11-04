import math

import pytest

from tools.mt5_xauusd_tick_spread_history_probe import summarize_spread_points


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
