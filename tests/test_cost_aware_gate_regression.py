from research.optimization.cost_aware_discovery import pre_oos_gate_pass, score_cost_aware


def _m(year, pf, expectancy=0.01, trades=100, dd=10.0, total_r=10.0):
    return {
        "year": year,
        "metrics": {
            "profit_factor": pf,
            "expectancy_R": expectancy,
            "trades": trades,
            "max_dd_pct": dd,
            "total_R": total_r,
        },
    }


def test_previous_candidate_239_cannot_pass_pre_oos_gate():
    metrics = [
        _m(2022, 1.013, expectancy=0.01),
        _m(2023, 0.795, expectancy=-0.01),
        _m(2024, 0.605, expectancy=-0.02),
    ]
    assert pre_oos_gate_pass(metrics) is False
    assert score_cost_aware(metrics) == -999.0


def test_all_three_pre_oos_years_must_clear_pf_and_expectancy_floors():
    metrics = [
        _m(2022, 1.08, expectancy=0.03),
        _m(2023, 1.05, expectancy=0.02),
        _m(2024, 1.00, expectancy=0.01),
    ]
    assert pre_oos_gate_pass(metrics) is False
    assert score_cost_aware(metrics) == -999.0


def test_all_three_profitable_pre_oos_years_are_required():
    metrics = [
        _m(2022, 1.08, expectancy=0.03),
        _m(2023, 1.05, expectancy=0.02),
        _m(2024, 1.05, expectancy=0.01),
    ]
    assert pre_oos_gate_pass(metrics) is True
    assert score_cost_aware(metrics) > -999.0


def test_missing_pre_oos_year_fails_closed():
    metrics = [_m(2022, 1.08, expectancy=0.03), _m(2023, 1.05, expectancy=0.02)]
    assert pre_oos_gate_pass(metrics) is False


def test_low_trade_count_fails_closed():
    metrics = [
        _m(2022, 1.08, expectancy=0.03, trades=99),
        _m(2023, 1.05, expectancy=0.02, trades=150),
        _m(2024, 1.05, expectancy=0.01, trades=150),
    ]
    assert pre_oos_gate_pass(metrics) is False
