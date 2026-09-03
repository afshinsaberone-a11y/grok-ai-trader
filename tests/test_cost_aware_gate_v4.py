from research.optimization.cost_aware_gate_v4 import pre_oos_gate, validation_gate


def m(year, pf, ex, trades=100, dd=10, total_r=1.0):
    return {"year": year, "metrics": {"profit_factor": pf, "expectancy_R": ex, "trades": trades, "max_dd_pct": dd, "total_R": total_r}}


def test_previous_false_champion_rejected():
    assert not pre_oos_gate([m(2022, 1.013, .01), m(2023, .795, -.03), m(2024, .605, -.05)])


def test_strict_gate_requires_positive_expectancy_in_all_pre_oos_years():
    assert pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.12, .02), m(2024, 1.05, .01)])
    assert not pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.04, .02), m(2024, 1.05, .01)])
    assert not pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.12, .02), m(2024, 1.05, -.01)])


def test_rejects_high_dd_or_low_trades():
    assert not pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.12, .02, dd=36), m(2024, 1.05, .01)])
    assert not pre_oos_gate([m(2022, 1.05, .01), m(2023, 1.12, .02, trades=99), m(2024, 1.05, .01)])


def test_validation_gate():
    assert validation_gate({"profit_factor": 1.10, "max_dd_pct": 35, "trades": 100})
    assert not validation_gate({"profit_factor": 1.09, "max_dd_pct": 20, "trades": 100})
