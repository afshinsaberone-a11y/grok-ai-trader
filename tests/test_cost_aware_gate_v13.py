from research.optimization.cost_aware_gate_v13 import candidate_gate, pre_oos_gate, validation_gate


def m(year, pf, ex, trades=100, dd=10):
    return {"year": year, "metrics": {"profit_factor": pf, "expectancy_R": ex, "trades": trades, "max_dd_pct": dd}}


def test_candidate_239_is_rejected_pre_oos():
    pre = [m(2022, 1.013, 0.01), m(2023, 0.795, -0.03), m(2024, 0.605, -0.05)]
    assert not pre_oos_gate(pre)


def test_every_pre_oos_year_must_pass():
    assert not pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.12, .02, dd=36), m(2024, 1.06, .01)])
    assert not pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.12, .02), m(2024, 1.02, .01)])
    assert pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.12, .02), m(2024, 1.06, .01)])


def test_validation_gate():
    assert validation_gate({"profit_factor": 1.10, "max_dd_pct": 35, "trades": 100})
    assert not validation_gate({"profit_factor": 1.099, "max_dd_pct": 35, "trades": 100})
    assert not validation_gate({"profit_factor": 1.10, "max_dd_pct": 35.01, "trades": 100})
    assert not validation_gate({"profit_factor": 1.10, "max_dd_pct": 35, "trades": 99})


def test_candidate_gate_requires_both():
    pre = [m(2022, 1.05, .01), m(2023, 1.12, .02), m(2024, 1.06, .01)]
    assert candidate_gate(pre, {"profit_factor": 1.10, "max_dd_pct": 35, "trades": 100})
    assert not candidate_gate(pre, {"profit_factor": 1.09, "max_dd_pct": 35, "trades": 100})
