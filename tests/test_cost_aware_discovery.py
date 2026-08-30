import pytest

from research.optimization.cost_aware_discovery import pre_oos_gate_pass, round_trip_cost_price


def test_round_trip_cost_price():
    assert round_trip_cost_price(0.5, 0.2) == pytest.approx(0.00014)


def test_negative_cost_rejected():
    with pytest.raises(ValueError):
        round_trip_cost_price(-0.1, 0.2)


def _m(pf, expectancy=0.01, trades=100, dd=10.0, total_r=10.0, year=None):
    row = {"metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades, "max_dd_pct": dd, "total_R": total_r}}
    if year is not None:
        row["year"] = year
    return row


def _years(*rows):
    return [dict(row, year=year) for year, row in zip((2022, 2023, 2024), rows)]


def test_pre_oos_gate_requires_all_years_pf_at_least_1_05():
    metrics = _years(_m(1.05), _m(1.04), _m(1.10))
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_requires_positive_expectancy_and_total_r_in_all_pre_oos_years():
    metrics = _years(
        _m(1.05, expectancy=0.01, total_r=1.0),
        _m(1.08, expectancy=0.02, total_r=2.0),
        _m(1.06, expectancy=0.001, total_r=0.1),
    )
    assert pre_oos_gate_pass(metrics) is True

    metrics = _years(
        _m(1.05, expectancy=0.01, total_r=1.0),
        _m(1.08, expectancy=0.02, total_r=2.0),
        _m(1.06, expectancy=-0.01, total_r=-1.0),
    )
    assert pre_oos_gate_pass(metrics) is False

    metrics = _years(
        _m(1.05, expectancy=0.01, total_r=1.0),
        _m(1.08, expectancy=0.02, total_r=2.0),
        _m(1.06, expectancy=0.001, total_r=0.0),
    )
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_rejects_low_trade_year():
    metrics = _years(_m(1.05), _m(1.08), _m(1.06, trades=99))
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_rejects_high_drawdown_year():
    metrics = _years(_m(1.05, dd=10), _m(1.08, dd=36), _m(1.06, dd=12))
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_rejects_missing_years():
    metrics = [_m(1.05, year=2022), _m(1.08, year=2023), _m(1.06, year=2025)]
    assert pre_oos_gate_pass(metrics) is False


def test_pre_oos_gate_rejects_previous_false_champion_profile():
    metrics = _years(
        _m(1.013, expectancy=0.01, trades=100, total_r=1.88),
        _m(0.795, expectancy=-0.03, trades=100, total_r=-28.72),
        _m(0.605, expectancy=-0.05, trades=100, total_r=-71.75),
    )
    assert pre_oos_gate_pass(metrics) is False
