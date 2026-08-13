from datetime import date

import pandas as pd

from research.real_data.histdata_ingest import _hidden_form, _parse_csv, _years_for_range


def test_histdata_hidden_form_parses_token_fields():
    html = '''
    <form method="POST" action="/get.php">
      <input type="hidden" name="tk" value="abc123" />
      <input type="hidden" name="date" value="2022" />
      <input type="hidden" name="datemonth" value="2022" />
      <input type="hidden" name="platform" value="ASCII" />
      <input type="hidden" name="timeframe" value="M1" />
      <input type="hidden" name="fxpair" value="EURUSD" />
    </form>
    '''
    fields = _hidden_form(html)
    assert fields["tk"] == "abc123"
    assert fields["datemonth"] == "2022"
    assert fields["platform"] == "ASCII"
    assert fields["timeframe"] == "M1"
    assert fields["fxpair"] == "EURUSD"


def test_histdata_parse_csv_converts_fixed_est_to_utc():
    payload = (
        b"20220103 070000;1.13000;1.13100;1.12900;1.13050;0\n"
        b"20220103 070100;1.13050;1.13200;1.13000;1.13150;0\n"
    )
    df = _parse_csv(payload)
    assert len(df) == 2
    assert df.loc[0, "timestamp"] == pd.Timestamp("2022-01-03T12:00:00Z")
    assert df.loc[1, "close"] == 1.1315
    assert pd.isna(df.loc[0, "spread"])


def test_histdata_year_range_excludes_exclusive_end_year():
    assert _years_for_range(date(2022, 1, 1), date(2026, 1, 1)) == [2022, 2023, 2024, 2025]


def test_histdata_year_range_includes_partial_end_year():
    assert _years_for_range(date(2022, 1, 1), date(2026, 2, 1)) == [2022, 2023, 2024, 2025, 2026]
