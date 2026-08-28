from research.optimization.cost_aware_discovery import pre_oos_gate_pass


def m(year, pf, expectancy, trades=100, dd=20):
    return {"year": year, "metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades, "max_dd_pct": dd}}


def test_requires_all_three_pre_oos_years_to_pass():
    metrics = [m(2022, 1.05, .01), m(2023, 1.10, .02), m(2024, 1.05, .01)]
    assert pre_oos_gate_pass(metrics)


def test_rejects_any_pre_oos_year_below_pf_floor():
    metrics = [m(2022, 1.05, .01), m(2023, 1.049, .02), m(2024, 1.10, .03)]
    assert not pre_oos_gate_pass(metrics)


def test_rejects_non_positive_expectancy_in_any_pre_oos_year():
    metrics = [m(2022, 1.10, .01), m(2023, 1.05, 0.0), m(2024, 1.10, .03)]
    assert not pre_oos_gate_pass(metrics)


def test_rejects_insufficient_trades_in_any_year():
    metrics = [m(2022, 1.05, .01, 99), m(2023, 1.10, .02), m(2024, 1.05, .01)]
    assert not pre_oos_gate_pass(metrics)


def test_rejects_excessive_drawdown_in_any_year():
    metrics = [m(2022, 1.05, .01, dd=35.01), m(2023, 1.10, .02), m(2024, 1.05, .01)]
    assert not pre_oos_gate_pass(metrics)
