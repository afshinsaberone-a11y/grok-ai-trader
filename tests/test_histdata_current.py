from research.real_data.histdata_current import _hidden_form_current_year, month_starts


def test_current_year_form_parser_is_attribute_order_independent():
    html = '''
    <form method="POST" action="/get.php">
      <input value="token-2026-07" id="tk" type="hidden" />
      <input id="date" value="2026" type="hidden" />
      <input value="202607" name="datemonth" type="hidden" />
      <input value="ASCII" name="platform" type="hidden" />
      <input value="M1" name="timeframe" type="hidden" />
      <input value="EURUSD" name="fxpair" type="hidden" />
    </form>
    '''
    fields = _hidden_form_current_year(html)
    assert fields["tk"] == "token-2026-07"
    assert fields["date"] == "2026"
    assert fields["datemonth"] == "202607"
    assert fields["platform"] == "ASCII"
    assert fields["timeframe"] == "M1"
    assert fields["fxpair"] == "EURUSD"


def test_current_year_month_range_is_monthly():
    assert month_starts(__import__('datetime').date(2026, 1, 1), __import__('datetime').date(2026, 8, 1)) == [
        (2026, 1),
        (2026, 2),
        (2026, 3),
        (2026, 4),
        (2026, 5),
        (2026, 6),
        (2026, 7),
    ]
