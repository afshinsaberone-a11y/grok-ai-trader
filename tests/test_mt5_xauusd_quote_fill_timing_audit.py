from types import SimpleNamespace

import pytest

from tools import mt5_xauusd_quote_fill_timing_audit as timing_audit


def test_millisecond_timestamp_is_preferred_and_seconds_are_fallback():
    item = SimpleNamespace(time_setup_msc=1_700_000_000_123, time_setup=1_700_000_000)
    assert timing_audit._ms(item, "time_setup_msc", "time_setup") == 1_700_000_000_123

    fallback = SimpleNamespace(time_setup_msc=0, time_setup=1_700_000_000)
    assert timing_audit._ms(fallback, "time_setup_msc", "time_setup") == 1_700_000_000_000

    missing = SimpleNamespace(time_setup_msc=0, time_setup=0)
    assert timing_audit._ms(missing, "time_setup_msc", "time_setup") is None


def test_stats_report_latency_distribution_and_empty_values():
    assert timing_audit._stats([])["count"] == 0
    result = timing_audit._stats([10.0, 20.0, 30.0])
    assert result["count"] == 3
    assert result["median"] == pytest.approx(20.0)
    assert result["mean"] == pytest.approx(20.0)


def test_audit_compares_setup_done_and_deal_execution_timestamps(monkeypatch):
    order = SimpleNamespace(
        symbol="XAUUSD",
        type=0,
        ticket=1001,
        time_setup_msc=1_700_000_000_100,
        time_setup=1_700_000_000,
        time_done_msc=1_700_000_000_200,
        time_done=1_700_000_000,
        volume_initial=0.10,
    )
    deal = SimpleNamespace(
        symbol="XAUUSD",
        order=1001,
        type=0,
        volume=0.10,
        price=2000.11,
        time_msc=1_700_000_000_200,
        time=1_700_000_000,
    )

    import numpy as np

    class FakeMT5:
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        DEAL_TYPE_BUY = 0
        DEAL_TYPE_SELL = 1
        COPY_TICKS_INFO = 1

        def initialize(self):
            return True

        def terminal_info(self):
            return SimpleNamespace(connected=True)

        def account_info(self):
            return SimpleNamespace(currency="USD")

        def symbol_info(self, symbol):
            return SimpleNamespace(point=0.01)

        def history_orders_get(self, start, end, group):
            return [order]

        def history_deals_get(self, start, end, group):
            return [deal]

        def copy_ticks_range(self, symbol, start, end, flags):
            return np.array(
                [(1_700_000_000_199, 2000.00, 2000.11)],
                dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")],
            )

        def shutdown(self):
            return None

        def last_error(self):
            return (0, "ok")

    monkeypatch.setattr(
        timing_audit,
        "capture_pre_order_quotes",
        lambda *args, **kwargs: {
            "quotes_by_order_ticket": {
                1001: {
                    "bid": 2000.00,
                    "ask": 2000.10,
                    "timestamp_ms": 1_700_000_000_000,
                    "age_ms": 100,
                }
            }
        },
    )

    result = timing_audit.audit(FakeMT5(), "XAUUSD", 180, 3000)

    assert result["matched_orders"] == 1
    assert result["counters"]["deals_after_order_setup"] == 1
    assert result["counters"]["deals_at_or_after_order_done"] == 1
    assert result["timing_ms"]["setup_to_first_fill"]["mean"] == pytest.approx(100.0)
    assert result["timing_ms"]["reference_quote_to_first_fill"]["mean"] == pytest.approx(200.0)
    assert result["price_check"]["signed_deviation_points"]["mean"] == pytest.approx(1.0)
    assert result["execution_quote_check"]["orders_with_vwap_equal_to_execution_quote"] == 1
    assert result["execution_quote_check"]["orders_with_strict_pre_fill_execution_tick"] == 1
    assert result["execution_quote_check"]["orders_with_same_millisecond_tick_tie"] == 0
    assert result["execution_quote_check"]["execution_quote_signed_deviation_points"]["mean"] == pytest.approx(0.0)
    assert result["execution_quote_check"]["setup_to_execution_quote_adverse_move_points"]["mean"] == pytest.approx(1.0)
    assert result["interpretation"] == "ZERO_DEVIATION_VS_STRICT_PRE_FILL_EXECUTION_QUOTE"
    assert result["no_orders_submitted"] is True


def test_execution_quote_falls_back_to_fresh_setup_quote_when_no_new_ticks():
    import numpy as np

    class EmptyTicks:
        COPY_TICKS_INFO = 1

        def copy_ticks_range(self, symbol, start, end, flags):
            return np.array(
                [],
                dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")],
            )

    setup_ms = 1_700_000_000_100
    result = timing_audit._quote_at_fill_time(
        EmptyTicks(),
        "XAUUSD",
        setup_ms,
        setup_ms + 2,
        {
            "bid": 2000.00,
            "ask": 2000.10,
            "timestamp_ms": setup_ms - 100,
            "age_ms": 100,
        },
        "ASK",
        3000,
    )

    assert result["query_error"] is False
    assert result["query_empty"] is True
    assert result["quote"]["ask"] == pytest.approx(2000.10)
    assert result["quote"]["age_ms"] == pytest.approx(102)


def test_execution_quote_does_not_fall_back_after_unusable_newer_tick():
    import numpy as np

    class InvalidNewerTick:
        COPY_TICKS_INFO = 1

        def copy_ticks_range(self, symbol, start, end, flags):
            return np.array(
                [(1_700_000_000_101, 0.0, 2000.20)],
                dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")],
            )

    setup_ms = 1_700_000_000_100
    result = timing_audit._quote_at_fill_time(
        InvalidNewerTick(),
        "XAUUSD",
        setup_ms,
        setup_ms + 2,
        {
            "bid": 2000.00,
            "ask": 2000.10,
            "timestamp_ms": setup_ms - 100,
            "age_ms": 100,
        },
        "ASK",
        3000,
    )

    assert result["query_error"] is False
    assert result["post_setup_tick_records_seen"] == 1
    assert result["post_setup_valid_tick_count"] == 0
    assert result["quote"] is None


def test_same_millisecond_tick_is_ambiguous_and_not_used_as_pre_fill_quote():
    import numpy as np

    class SameMillisecondTick:
        COPY_TICKS_INFO = 1

        def copy_ticks_range(self, symbol, start, end, flags):
            return np.array(
                [(1_700_000_000_102, 2000.00, 2000.20)],
                dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")],
            )

    setup_ms = 1_700_000_000_100
    result = timing_audit._quote_at_fill_time(
        SameMillisecondTick(),
        "XAUUSD",
        setup_ms,
        setup_ms + 2,
        {
            "bid": 2000.00,
            "ask": 2000.10,
            "timestamp_ms": setup_ms - 100,
            "age_ms": 100,
        },
        "ASK",
        3000,
    )

    assert result["fill_millisecond_ordering_ambiguous"] is True
    assert result["fill_millisecond_tick_records_seen"] == 1
    assert result["fill_millisecond_valid_tick_count"] == 1
    assert result["quote_source"] == "SETUP_QUOTE_FALLBACK"
    assert result["quote"]["ask"] == pytest.approx(2000.10)

