import pandas as pd

from research.real_data.session_quality import validate_forex_weekend_windows


def test_saturday_is_closed():
    frame = pd.DataFrame({"timestamp": ["2026-07-04T12:00:00Z"]})
    report = validate_forex_weekend_windows(frame)
    assert report.saturday_rows == 1
    assert report.rows_in_weekend_closed_window == 1


def test_sunday_before_open_is_closed():
    frame = pd.DataFrame({"timestamp": ["2026-07-05T20:59:00Z"]})
    report = validate_forex_weekend_windows(frame)
    assert report.sunday_preopen_rows == 1
    assert report.rows_in_weekend_closed_window == 1


def test_sunday_open_is_retained():
    frame = pd.DataFrame({"timestamp": ["2026-07-05T22:31:00Z"]})
    report = validate_forex_weekend_windows(frame)
    assert report.sunday_open_rows == 1
    assert report.rows_in_weekend_closed_window == 0
