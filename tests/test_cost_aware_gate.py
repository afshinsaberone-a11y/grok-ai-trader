from research.optimization.cost_aware_gate_v12 import pre_oos_gate, validation_gate


def m(year, pf, expectancy, trades=100, dd=20):
    return {"year": year, "metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades, "max_dd_pct": dd}}


def test_previous_false_champion_is_rejected():
    assert not pre_oos_gate([m(2022, 1.013, .01), m(2023, .795, -.03), m(2024, .605, -.05)])


def test_requires_all_three_pre_oos_years_to_pass():
    assert pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.10, .02), m(2024, 1.05, .01)])


def test_rejects_any_pre_oos_year_below_pf_floor():
    assert not pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.049, .02), m(2024, 1.10, .03)])


def test_rejects_non_positive_expectancy_in_any_pre_oos_year():
    assert not pre_oos_gate([m(2022, 1.10, .01), m(2023, 1.05, 0.0), m(2024, 1.10, .03)])


def test_rejects_insufficient_trades_in_any_year():
    assert not pre_oos_gate([m(2022, 1.05, .01, 99), m(2023, 1.10, .02), m(2024, 1.05, .01)])


def test_rejects_excessive_drawdown_in_any_year():
    assert not pre_oos_gate([m(2022, 1.05, .01, dd=35.01), m(2023, 1.10, .02), m(2024, 1.05, .01)])


def test_validation_gate_is_independent():
    assert validation_gate({"profit_factor": 1.10, "max_dd_pct": 35, "trades": 100})
    assert not validation_gate({"profit_factor": 1.09, "max_dd_pct": 20, "trades": 100})
    assert not validation_gate({"profit_factor": 1.10, "max_dd_pct": 35.01, "trades": 100})
    assert not validation_gate({"profit_factor": 1.10, "max_dd_pct": 35, "trades": 99})
