import pandas as pd

from research.optimization.run_v51_real_backtest import run


def test_v51_runner_reports_empty_validation_and_oos_instead_of_fabricating_data(tmp_path):
    rows = 80
    timestamps = pd.date_range("2024-01-02T00:00:00Z", periods=rows, freq="15min")
    close = [1.10 + i * 0.00001 for i in range(rows)]
    data = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": close,
            "high": [value + 0.00005 for value in close],
            "low": [value - 0.00005 for value in close],
            "close": close,
            "volume": [1.0] * rows,
            "spread": [float("nan")] * rows,
        }
    )
    dataset = tmp_path / "real_eurusd_m15.csv"
    output = tmp_path / "report.json"
    data.to_csv(dataset, index=False)

    report = run(dataset, output_path=output)

    assert report["data"]["synthetic_data"] is False
    assert report["data"]["price_side"] == "BID"
    assert report["data"]["rows"] == rows
    assert report["execution_assumptions"]["round_trip_adverse_cost_pips"] == 0.9
    assert report["execution_assumptions"]["bid_ohlc_fill_model"]["spread_is_charged_once_per_round_trip"] is True
    assert report["splits"]["IS_2022_2024"]["rows"] == rows
    assert report["splits"]["VALIDATION_2025"]["status"] == "NO_DATA"
    assert report["splits"]["OOS_2026"]["status"] == "NO_DATA"
    ablation = report["branch_ablation"]
    assert ablation["schema"] == "forexai.v51.branch_ablation.v1"
    assert ablation["selection_policy"]["full_engine_rerun"] is True
    assert ablation["selection_policy"]["post_hoc_trade_log_filtering"] is False
    assert ablation["selection_policy"]["OOS_2026"].startswith("Excluded entirely")
    assert "OOS_2026" not in ablation["splits"]
    assert ablation["splits"]["VALIDATION_2025"]["status"] == "NO_DATA"
    scenarios = ablation["splits"]["IS_2022_2024"]["scenarios"]
    assert {
        "only_A-trend", "only_B-squeeze", "only_C-range",
        "without_A-trend", "without_B-squeeze", "without_C-range",
        "only_C-range_LONG", "without_A-trend_and_C-range_SHORT",
    }.issubset(set(scenarios))
    assert scenarios["only_A-trend"]["status"] == "NO_CLOSED_TRADES"
    side_scenarios = ablation["branch_side_scenarios"]
    assert side_scenarios["only_C-range_LONG"] == ["C-range:LONG"]
    assert "C-range:SHORT" not in side_scenarios["without_A-trend_and_C-range_SHORT"]
    assert "A-trend:LONG" not in side_scenarios["without_A-trend_and_C-range_SHORT"]
    baseline_breakdown = ablation["splits"]["IS_2022_2024"]["baseline_all_branches"]["closed_trades_by_branch_side"]
    assert "C-range:LONG" in baseline_breakdown
    assert "C-range:SHORT" in baseline_breakdown
    assert output.is_file()
