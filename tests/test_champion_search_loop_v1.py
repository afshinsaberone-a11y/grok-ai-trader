from research.optimization.champion_search_loop_v1 import Gate, passes_gate, run_loop


def candidate(**overrides):
    base = {
        "candidate_id": "C1",
        "score": 10.0,
        "discovery_years": [{"pf": 1.05}, {"pf": 1.12}, {"pf": 1.08}],
        "validation": {"pf": 1.15, "max_dd_pct": 20, "trades": 500, "expectancy_r": 0.05},
        "stress": {"worst_pf": 1.02, "worst_dd_pct": 25},
        "config_hash": "abc123",
        "oos_loaded": False,
        "optimization_on_oos": False,
    }
    base.update(overrides)
    return base


def test_gate_requires_multiple_profitable_discovery_years():
    ok, reasons = passes_gate(candidate(discovery_years=[{"pf": 0.9}, {"pf": 1.1}, {"pf": 0.95}]), Gate())
    assert not ok
    assert any("profitable discovery years" in r for r in reasons)


def test_gate_rejects_oos_leak():
    ok, reasons = passes_gate(candidate(oos_loaded=True), Gate())
    assert not ok
    assert "OOS data loaded before freeze" in reasons


def test_gate_rejects_cost_stress_failure():
    ok, reasons = passes_gate(candidate(stress={"worst_pf": 0.8, "worst_dd_pct": 20}), Gate())
    assert not ok
    assert "worst stress PF below gate" in reasons


def test_loop_freezes_first_passing_candidate():
    result = run_loop([
        [candidate(candidate_id="bad", score=20, validation={"pf": 0.9, "max_dd_pct": 20, "trades": 500, "expectancy_r": 0.05})],
        [candidate(candidate_id="good", score=5)],
    ])
    assert result.status == "FROZEN_CANDIDATE"
    assert result.candidate_id == "good"
    assert result.iteration == 2


def test_loop_continues_when_nothing_passes():
    result = run_loop([[candidate(discovery_years=[{"pf": 0.8}, {"pf": 0.9}])]])
    assert result.status == "CONTINUE_DISCOVERY"
