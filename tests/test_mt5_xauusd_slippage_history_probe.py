from types import SimpleNamespace

import pytest

from tools.mt5_xauusd_slippage_history_probe import (
    aggregate_quote_to_fill_slippage,
    capture_pre_order_quotes,
    order_setup_time_ms,
)


def order(ticket, side, volume=0.10, symbol="XAUUSD", setup_ms=1_700_000_000_000):
    return SimpleNamespace(
        ticket=ticket,
        type=side,
        price_open=0.0,  # Market Execution does not need a request price.
        volume_initial=volume,
        symbol=symbol,
        time_setup_msc=setup_ms,
        time_setup=setup_ms // 1000,
    )


def deal(order_ticket, side, volume, price, symbol="XAUUSD"):
    return SimpleNamespace(
        order=order_ticket, type=side, volume=volume,
        price=price, symbol=symbol,
    )


def aggregate(orders, deals, quotes):
    return aggregate_quote_to_fill_slippage(
        orders, deals, quotes, symbol="XAUUSD",
        point=0.01, tick_size=0.01, tick_value=1.0,
        buy_order_type=0, sell_order_type=1,
        buy_deal_type=0, sell_deal_type=1,
    )


def test_market_orders_without_price_open_use_side_specific_pre_order_quotes():
    orders = [
        order(10, 0, volume=0.20),
        order(20, 1, volume=0.10),
    ]
    deals = [
        deal(10, 0, 0.10, 2000.10),
        deal(10, 0, 0.10, 2000.20),
        deal(20, 1, 0.10, 1999.80),
    ]
    quotes = {
        10: {"bid": 1999.90, "ask": 2000.00, "age_ms": 10},
        20: {"bid": 2000.00, "ask": 2000.10, "age_ms": 20},
    }

    result = aggregate(orders, deals, quotes)
    buy = result["by_order_side"]["BUY"]
    sell = result["by_order_side"]["SELL"]

    assert result["matched_filled_order_count"] == 2
    assert buy["signed_quote_to_fill_deviation_usd_per_oz"]["mean"] == pytest.approx(0.15)
    assert sell["signed_quote_to_fill_deviation_usd_per_oz"]["mean"] == pytest.approx(0.20)
    assert buy["volume_weighted_adverse_quote_to_fill_cost_per_standard_lot_account_currency"] == pytest.approx(15.0)
    assert sell["volume_weighted_adverse_quote_to_fill_cost_per_standard_lot_account_currency"] == pytest.approx(20.0)
    assert buy["quote_age_at_order_setup_ms"]["mean"] == pytest.approx(10.0)


def test_favorable_fill_is_reported_as_improvement_not_adverse_cost():
    result = aggregate(
        [order(10, 0)],
        [deal(10, 0, 0.10, 2000.00)],
        {10: {"bid": 2000.00, "ask": 2000.10, "age_ms": 0}},
    )
    buy = result["by_order_side"]["BUY"]
    assert buy["signed_quote_to_fill_deviation_usd_per_oz"]["mean"] == pytest.approx(-0.10)
    assert buy["adverse_quote_to_fill_deviation_usd_per_oz"]["mean"] == pytest.approx(0.0)
    assert buy["favorable_price_improvement_usd_per_oz"]["mean"] == pytest.approx(0.10)


def test_order_without_fresh_pre_order_quote_is_excluded_not_zero():
    result = aggregate(
        [order(10, 0)],
        [deal(10, 0, 0.10, 2000.10)],
        {},
    )
    assert result["matched_filled_order_count"] == 0
    assert result["counters"]["orders_missing_valid_pre_order_quote"] == 1
    assert result["by_order_side"]["BUY"]["signed_quote_to_fill_deviation_usd_per_oz"]["count"] == 0


def test_pending_orders_and_other_symbols_are_ignored():
    result = aggregate(
        [order(10, 2), order(11, 0, symbol="EURUSD")],
        [deal(10, 0, 0.10, 2000.10)],
        {},
    )
    assert result["market_order_count"] == 0
    assert result["matched_filled_order_count"] == 0


def test_duplicate_partial_fills_are_weighted_by_volume():
    result = aggregate(
        [order(10, 0, volume=0.20)],
        [
            deal(10, 0, 0.10, 2000.10),
            deal(10, 0, 0.10, 2000.20),
        ],
        {10: {"bid": 1999.90, "ask": 2000.00, "age_ms": 1}},
    )
    buy = result["by_order_side"]["BUY"]
    assert result["counters"]["multi_deal_fill_orders"] == 1
    assert buy["signed_quote_to_fill_deviation_usd_per_oz"]["mean"] == pytest.approx(0.15)


def test_order_setup_time_prefers_millisecond_timestamp():
    item = order(10, 0, setup_ms=1_700_000_000_123)
    assert order_setup_time_ms(item) == 1_700_000_000_123


def test_sample_review_requires_both_sides_and_minimum_count():
    orders = [order(i, 0 if i < 30 else 1) for i in range(35)]
    deals = [
        deal(i, 0 if i < 30 else 1, 0.10, 2000.10 if i < 30 else 1999.90)
        for i in range(35)
    ]
    quotes = {
        i: {"bid": 1999.90, "ask": 2000.00, "age_ms": 1}
        for i in range(35)
    }
    result = aggregate(orders, deals, quotes)
    assert result["sample_is_adequate_for_review"] is False  # SELL count is only 5


def test_invalid_price_units_are_rejected():
    with pytest.raises(ValueError, match="POINT_INVALID"):
        aggregate_quote_to_fill_slippage(
            [], [], {}, symbol="XAUUSD",
            point=0.0, tick_size=0.01, tick_value=1.0,
            buy_order_type=0, sell_order_type=1,
            buy_deal_type=0, sell_deal_type=1,
        )


class FakeMT5:
    COPY_TICKS_INFO = 1

    def __init__(self, ticks):
        self.ticks = ticks

    def copy_ticks_range(self, symbol, start, end, flags):
        return self.ticks

    def last_error(self):
        return (0, "ok")


def test_pre_order_quote_capture_uses_last_valid_tick_at_or_before_setup():
    import numpy as np

    item = order(10, 0, setup_ms=1_700_000_000_500)
    ticks = np.array([
        (1_700_000_000_000, 2000.00, 2000.10),
        (1_700_000_000_450, 2000.01, 2000.11),
        (1_700_000_000_600, 2000.02, 2000.12),  # After setup: must be ignored.
        (1_700_000_000_490, 0.0, 2000.13),     # Invalid BID: must be ignored.
    ], dtype=[("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")])

    result = capture_pre_order_quotes(
        FakeMT5(ticks), "XAUUSD", [item], max_quote_age_ms=1000
    )
    quote = result["quotes_by_order_ticket"][10]
    assert quote["bid"] == pytest.approx(2000.01)
    assert quote["ask"] == pytest.approx(2000.11)
    assert quote["age_ms"] == 50
    assert result["counters"]["orders_with_valid_pre_order_quote"] == 1


def test_invalid_max_quote_age_is_rejected():
    with pytest.raises(ValueError, match="MAX_QUOTE_AGE_INVALID"):
        capture_pre_order_quotes(FakeMT5([]), "XAUUSD", [], max_quote_age_ms=0)
