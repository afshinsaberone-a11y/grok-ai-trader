import pytest

from research.optimization.cost_aware_discovery import pre_oos_gate_pass, round_trip_cost_price


def test_round_trip_cost_price():
    assert round_trip_cost_price(0.5, 0.2) == pytest.approx(0.00014)


def test_negative_cost_rejected():
    with pytest.raises(ValueError):
        round_trip_cost_price(-0.1, 0.2)


def _m(pf, expectancy=0.01, trades=100, year=None):
    row = {"metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades}}
    if year is not None:
        row["year"] = year
    return row


def _years(*rows):
    return [dict(row, year=year) for year, row in zip((2022, 2023, 2024), rows)]


def test_pre_oos_gate_requires_all_years_pf_at_least_one():
    metrics = _years(_m(1.05), _m(1.01), _m(0.99))
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_accepts_two_profitable_years():
    metrics = _years(_m(1.05, expectancy=0.01), _m(1.01, expectancy=0.02), _m(1.02, expectancy=-0.01))
    assert pre_oos_gate_pass(metrics) is True


def test_pre_oos_gate_rejects_low_trade_year():
    metrics = _years(_m(1.05), _m(1.01), _m(1.02, trades=99))
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_rejects_missing_years():
    metrics = [_m(1.05, year=2022), _m(1.01, year=2023), _m(1.02, year=2025)]
    assert pre_oos_gate_pass(metrics) is False
