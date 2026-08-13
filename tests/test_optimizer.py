from research.optimization.optimize_existing_strategy import generate_candidates


def test_optimizer_generates_exactly_100_reproducible_candidates():
    left = generate_candidates(100)
    right = generate_candidates(100)
    assert left == right
    assert len(left) == 100
    assert len({tuple(sorted(item.items())) for item in left}) == 100


def test_optimizer_candidates_respect_parameter_relationships():
    for item in generate_candidates(100):
        assert item["fast"] < item["slow"] < item["trend_period"]
        assert 1.2 <= item["atr_mult"] <= 2.4
        assert 1.5 <= item["rr"] <= 3.5
        assert item["risk_pct"] == 0.01
