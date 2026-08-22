from research.optimization.cost_aware_discovery import pre_oos_gate_pass


def _m(pf, expectancy=0.01, trades=100):
    return {"metrics": {"profit_factor": pf, "expectancy_R": expectancy, "trades": trades}}


def test_previous_candidate_239_cannot_pass_pre_oos_gate():
    metrics = [
        _m(1.013, expectancy=0.01),
        _m(0.795, expectancy=-0.01),
        _m(0.605, expectancy=-0.02),
    ]
    assert pre_oos_gate_pass(metrics) is False
