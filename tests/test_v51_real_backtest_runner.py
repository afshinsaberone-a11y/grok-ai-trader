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
    design_diagnostic = report["is_only_design_diagnostics"]
    assert design_diagnostic["schema"] == "forexai.v51.is_only_design_diagnostics.v1"
    assert design_diagnostic["scope"] == "IS_2022_2024_ONLY"
    assert design_diagnostic["minimum_net_reward_risk"] == 1.0
    assert design_diagnostic["full_engine_rerun"] is True
    assert design_diagnostic["post_hoc_trade_log_filtering"] is False
    assert design_diagnostic["validation_and_oos_used"] is False
    assert design_diagnostic["mql5_parity_status"] == "NOT_IMPLEMENTED_RESEARCH_ONLY_VARIANT"
    assert design_diagnostic["production_ea_changed"] is False
    directional = report["is_only_directional_diagnostics"]
    assert directional["schema"] == "forexai.v51.is_only_directional_diagnostics.v1"
    assert directional["scope"] == "IS_2022_2024_ONLY"
    assert directional["excluded_branch_sides"] == ["A-trend:LONG", "C-range:SHORT"]
    assert directional["enabled_branch_sides"] == [
        "A-trend:SHORT", "B-squeeze:LONG", "B-squeeze:SHORT", "C-range:LONG",
    ]
    assert directional["full_engine_rerun"] is True
    assert directional["post_hoc_trade_log_filtering"] is False
    assert directional["validation_and_oos_used"] is False
    assert directional["branch_set_changed"] is False
    assert directional["other_strategy_parameters_changed"] is False
    assert directional["mql5_parity_status"] == "NOT_IMPLEMENTED_RESEARCH_ONLY_VARIANT"
    assert directional["production_ea_changed"] is False
    assert directional["candidate"]["status"] == "NO_CLOSED_TRADES"
    confirmation = report["validation_directional_confirmation"]
    assert confirmation["schema"] == "forexai.v51.validation_directional_confirmation.v1"
    assert confirmation["status"] == "NO_DATA"
    assert confirmation["scope"] == "VALIDATION_2025_ONLY"
    assert confirmation["validation_used_for_parameter_selection"] is False
    assert confirmation["oos_used"] is False
    assert design_diagnostic["candidate"]["status"] == "NO_CLOSED_TRADES"
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



def test_v51_locked_directional_candidate_validation_is_confirmation_only(tmp_path):
    rows = 80
    timestamps = pd.date_range("2025-01-02T00:00:00Z", periods=rows, freq="15min")
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
    dataset = tmp_path / "real_eurusd_m15_validation.csv"
    output = tmp_path / "validation_report.json"
    data.to_csv(dataset, index=False)

    report = run(dataset, output_path=output)
    confirmation = report["validation_directional_confirmation"]

    assert confirmation["status"] == "COMPLETED"
    assert confirmation["scope"] == "VALIDATION_2025_ONLY"
    assert confirmation["locked_candidate"] is True
    assert confirmation["enabled_branch_sides"] == [
        "A-trend:SHORT", "B-squeeze:LONG", "B-squeeze:SHORT", "C-range:LONG",
    ]
    assert confirmation["validation_used_for_parameter_selection"] is False
    assert confirmation["validation_is_confirmation_only"] is True
    assert confirmation["oos_used"] is False
    assert confirmation["mql5_parity_status"] == "NOT_IMPLEMENTED_RESEARCH_ONLY_VARIANT"
    assert confirmation["production_ea_changed"] is False
    assert confirmation["demo_live_eligibility"] == "NOT_ELIGIBLE_RESEARCH_ONLY"
    assert confirmation["candidate"]["status"] == "NO_CLOSED_TRADES"
    assert confirmation["confirmation_passed"] is False
    oos_confirmation = report["oos_directional_confirmation"]
    assert oos_confirmation["schema"] == "forexai.v51.oos_directional_confirmation.v1"
    assert oos_confirmation["status"] == "NO_DATA"
    assert oos_confirmation["scope"] == "OOS_2026_ONLY"
    assert oos_confirmation["is_used"] is False
    assert oos_confirmation["validation_used"] is False
    assert output.is_file()



def test_v51_locked_directional_candidate_oos_is_one_time_and_fail_closed(tmp_path):
    rows = 80
    timestamps = pd.date_range("2026-01-02T00:00:00Z", periods=rows, freq="15min")
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
    dataset = tmp_path / "real_eurusd_m15_oos.csv"
    output = tmp_path / "oos_report.json"
    data.to_csv(dataset, index=False)

    report = run(dataset, output_path=output)
    confirmation = report["oos_directional_confirmation"]

    assert confirmation["status"] == "COMPLETED"
    assert confirmation["scope"] == "OOS_2026_ONLY"
    assert confirmation["locked_candidate"] is True
    assert confirmation["enabled_branch_sides"] == [
        "A-trend:SHORT", "B-squeeze:LONG", "B-squeeze:SHORT", "C-range:LONG",
    ]
    assert confirmation["is_used"] is False
    assert confirmation["validation_used"] is False
    assert confirmation["oos_used_for_candidate_evaluation"] is True
    assert confirmation["oos_used_for_parameter_selection"] is False
    assert confirmation["candidate_may_be_retuned_after_oos"] is False
    assert confirmation["baseline_oos_previously_inspected"] is True
    assert confirmation["mql5_parity_status"] == "NOT_IMPLEMENTED_RESEARCH_ONLY_VARIANT"
    assert confirmation["production_ea_changed"] is False
    assert confirmation["demo_live_eligibility"] == "NOT_ELIGIBLE_RESEARCH_ONLY"
    assert confirmation["candidate"]["status"] == "NO_CLOSED_TRADES"
    assert confirmation["confirmation_passed"] is False
    assert output.is_file()
