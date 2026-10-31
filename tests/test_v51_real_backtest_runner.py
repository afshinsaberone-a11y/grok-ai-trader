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
    assert report["data"]["rows"] == rows
    assert report["splits"]["IS_2022_2024"]["rows"] == rows
    assert report["splits"]["VALIDATION_2025"]["status"] == "NO_DATA"
    assert report["splits"]["OOS_2026"]["status"] == "NO_DATA"
    assert output.is_file()
