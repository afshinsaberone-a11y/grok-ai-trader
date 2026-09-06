from research_ai.scientist import ResearchScientist


def test_empty_or_invalid_data_does_not_invent_results():
    report = ResearchScientist().analyze([{"strategy_id": "x"}])
    assert report.experiments == 1
    assert report.valid_experiments == 0
    assert report.hypotheses
    assert "insufficient" in report.hypotheses[0].lower()


def test_research_gate_is_based_only_on_observed_records():
    rows = [
        {"strategy_id": "a", "profit_factor": 1.8, "max_drawdown": 9.0, "trades": 100},
        {"strategy_id": "b", "profit_factor": 1.1, "max_drawdown": 12.0, "trades": 100},
    ]
    report = ResearchScientist().analyze(rows)
    cluster = [f for f in report.findings if f.kind == "candidate_cluster"]
    assert len(cluster) == 1
    assert cluster[0].evidence["count"] == 1
    assert "out-of-sample" in report.hypotheses[0]


def test_min_trade_filter_is_enforced():
    rows = [{"strategy_id": "a", "profit_factor": 3.0, "max_drawdown": 2.0, "trades": 5}]
    report = ResearchScientist(min_trades=30).analyze(rows)
    assert report.valid_experiments == 1
    assert report.findings == []
