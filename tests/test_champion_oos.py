import pandas as pd

from research.optimization.run_champion_oos import CHAMPION, run


def test_champion_parameters_are_frozen():
    assert CHAMPION == {
        "candidate_id": 56,
        "fast": 13,
        "slow": 89,
        "trend_period": 200,
        "atr_mult": 2.0,
        "rr": 3.5,
        "risk_pct": 0.01,
    }


def test_oos_runner_rejects_pre_2026_start(tmp_path):
    path = tmp_path / "m5.csv"
    pd.DataFrame({
        "timestamp": ["2026-01-01T00:00:00Z"],
        "open": [1.1], "high": [1.2], "low": [1.0], "close": [1.1], "volume": [0],
    }).to_csv(path, index=False)
    try:
        run(path, tmp_path / "out.json", start="2025-12-01", end="2026-02-01")
    except ValueError as exc:
        assert "2026-01-01" in str(exc)
    else:
        raise AssertionError("pre-2026 OOS start was accepted")
