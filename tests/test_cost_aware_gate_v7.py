from research.optimization.cost_aware_gate_v7 import pre_oos_gate, validation_gate


def m(year, pf, ex, trades=100, dd=10):
    return {"year": year, "metrics": {"profit_factor": pf, "expectancy_R": ex, "trades": trades, "max_dd_pct": dd}}


def test_candidate_239_style_failure_is_rejected():
    assert not pre_oos_gate([
        m(2022, 1.013, 0.01),
        m(2023, 0.795, -0.03),
        m(2024, 0.605, -0.05),
    ])


def test_requires_all_pre_oos_years_to_clear_pf_trade_dd_and_expectancy():
    assert pre_oos_gate([
        m(2022, 1.05, 0.01),
        m(2023, 1.12, 0.02),
        m(2024, 1.05, 0.001),
    ])
    assert not pre_oos_gate([
        m(2022, 1.05, 0.01),
        m(2023, 1.049, 0.02),
        m(2024, 1.05, 0.01),
    ])
    assert not pre_oos_gate([
        m(2022, 1.05, 0.01),
        m(2023, 1.12, 0.02, dd=35.01),
        m(2024, 1.05, 0.01),
    ])
    assert not pre_oos_gate([
        m(2022, 1.05, 0.01),
        m(2023, 1.12, 0.02),
        m(2024, 1.05, -0.001),
    ])


def test_validation_gate_remains_independent():
    assert validation_gate({"profit_factor": 1.10, "max_dd_pct": 35, "trades": 100})
    assert not validation_gate({"profit_factor": 1.09, "max_dd_pct": 20, "trades": 100})
    assert not validation_gate({"profit_factor": 1.10, "max_dd_pct": 35.01, "trades": 100})
    assert not validation_gate({"profit_factor": 1.10, "max_dd_pct": 35, "trades": 99})
