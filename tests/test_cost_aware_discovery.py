import pytest

from research.optimization.cost_aware_discovery import pre_oos_gate_pass, round_trip_cost_price


def test_round_trip_cost_price():
    assert round_trip_cost_price(0.5, 0.2) == pytest.approx(0.00014)


def test_negative_cost_rejected():
    with pytest.raises(ValueError):
        round_trip_cost_price(-0.1, 0.2)


def _m(pf, expectancy=0.01, trades=100):
    return {"metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades}}


def test_pre_oos_gate_requires_all_years_pf_at_least_one():
    metrics = [_m(1.05), _m(1.01), _m(0.99)]
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_accepts_three_profitable_years():
    metrics = [_m(1.05), _m(1.01), _m(1.02)]
    assert pre_oos_gate_pass(metrics) is True


def test_pre_oos_gate_rejects_low_trade_year():
    metrics = [_m(1.05), _m(1.01), _m(1.02, trades=99)]
    assert pre_oos_gate_pass(metrics) is False
