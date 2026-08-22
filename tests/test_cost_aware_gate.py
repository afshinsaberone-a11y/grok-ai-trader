from research.optimization.cost_aware_discovery import pre_oos_gate_pass


def m(pf, expectancy, trades=100, dd=20):
    return {"metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades, "max_dd_pct": dd}}


def test_requires_all_three_pre_oos_years_and_two_profitable():
    assert pre_oos_gate_pass([m(1.01, .01), m(1.10, .02), m(1.02, .01)])
    assert not pre_oos_gate_pass([m(1.01, .01), m(.99, -.01), m(1.02, .01)])


def test_rejects_any_pre_oos_year_below_pf_one():
    assert not pre_oos_gate_pass([m(1.01, .01), m(0.99, .02), m(1.10, .03)])


def test_rejects_insufficient_trades_in_any_year():
    assert not pre_oos_gate_pass([m(1.01, .01, 99), m(1.10, .02), m(1.02, .01)])
