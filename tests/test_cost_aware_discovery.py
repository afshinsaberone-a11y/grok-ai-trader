import pytest

from research.optimization.cost_aware_discovery import round_trip_cost_price


def test_round_trip_cost_price():
    assert round_trip_cost_price(0.5, 0.2) == pytest.approx(0.00014)


def test_negative_cost_rejected():
    with pytest.raises(ValueError):
        round_trip_cost_price(-0.1, 0.2)
