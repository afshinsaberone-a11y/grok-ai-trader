from research.optimization.cost_aware_gate_v12 import pre_oos_gate, validation_gate, candidate_gate


def m(year, pf, expectancy=0.01, trades=100, dd=10.0):
    return {"year": year, "metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades, "max_dd_pct": dd}}


def test_three_pre_oos_years_are_required_and_each_must_pass():
    assert pre_oos_gate([m(2022, 1.05), m(2023, 1.05), m(2024, 1.05)])
    assert not pre_oos_gate([m(2022, 1.05), m(2023, 1.05)])
    assert not pre_oos_gate([m(2022, 1.05), m(2023, 0.99), m(2024, 1.05)])


def test_candidate_239_style_failure_is_rejected():
    pre = [m(2022, 1.013), m(2023, 0.795, expectancy=-0.03), m(2024, 0.605, expectancy=-0.05)]
    validation = {"profit_factor": 1.109, "max_dd_pct": 11.57, "trades": 1000}
    assert not candidate_gate(pre, validation)


def test_validation_gate_remains_independent():
    pre = [m(2022, 1.05), m(2023, 1.05), m(2024, 1.05)]
    assert not validation_gate({"profit_factor": 1.09, "max_dd_pct": 10, "trades": 1000})
    assert candidate_gate(pre, {"profit_factor": 1.10, "max_dd_pct": 35, "trades": 100})
