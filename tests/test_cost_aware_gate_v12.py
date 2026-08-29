from research.optimization.cost_aware_gate_v12 import candidate_gate, pre_oos_gate


def m(pf=1.10, exp=0.01, trades=100, dd=20):
    return {"profit_factor": pf, "expectancy_R": exp, "trades": trades, "max_dd_pct": dd}


def test_all_pre_oos_years_must_pass():
    good = [{"year": y, "metrics": m()} for y in (2022, 2023, 2024)]
    assert pre_oos_gate(good)
    bad = good.copy()
    bad[1] = {"year": 2023, "metrics": m(pf=0.99)}
    assert not pre_oos_gate(bad)


def test_pre_oos_pf_floor_is_1_05():
    good = [{"year": y, "metrics": m(pf=1.05)} for y in (2022, 2023, 2024)]
    assert pre_oos_gate(good)
    bad = good.copy()
    bad[1] = {"year": 2023, "metrics": m(pf=1.049)}
    assert not pre_oos_gate(bad)


def test_validation_gate_is_required():
    pre = [{"year": y, "metrics": m()} for y in (2022, 2023, 2024)]
    assert candidate_gate(pre, m(pf=1.10))
    assert not candidate_gate(pre, m(pf=1.09))


def test_dd_and_trade_floors():
    pre = [{"year": y, "metrics": m()} for y in (2022, 2023, 2024)]
    assert not candidate_gate(pre, m(dd=35.01))
    assert not candidate_gate(pre, m(trades=99))
