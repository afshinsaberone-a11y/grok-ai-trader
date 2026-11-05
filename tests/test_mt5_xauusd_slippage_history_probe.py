from types import SimpleNamespace

import pytest

from tools.mt5_xauusd_slippage_history_probe import (
    aggregate_requested_to_fill_slippage,
)


def order(ticket, side, requested, volume=0.10, symbol="XAUUSD"):
    return SimpleNamespace(
        ticket=ticket, type=side, price_open=requested,
        volume_initial=volume, symbol=symbol,
    )


def deal(order_ticket, side, volume, price, symbol="XAUUSD"):
    return SimpleNamespace(
        order=order_ticket, type=side, volume=volume,
        price=price, symbol=symbol,
    )


def aggregate(orders, deals):
    return aggregate_requested_to_fill_slippage(
        orders, deals, symbol="XAUUSD",
        point=0.01, tick_size=0.01, tick_value=1.0,
        buy_order_type=0, sell_order_type=1,
        buy_deal_type=0, sell_deal_type=1,
    )


def test_buy_and_sell_adverse_slippage_use_correct_direction_and_weight_partial_fills():
    orders = [
        order(10, 0, 2000.00, volume=0.20),
        order(20, 1, 2000.00, volume=0.10),
    ]
    deals = [
        deal(10, 0, 0.10, 2000.10),
        deal(10, 0, 0.10, 2000.20),
        deal(20, 1, 0.10, 1999.80),
    ]

    result = aggregate(orders, deals)

    buy = result["by_order_side"]["BUY"]
    sell = result["by_order_side"]["SELL"]
    assert result["matched_filled_order_count"] == 2
    assert result["counters"]["multi_deal_fill_orders"] == 1
    assert buy["signed_deviation_usd_per_oz"]["mean"] == pytest.approx(0.15)
    assert sell["signed_deviation_usd_per_oz"]["mean"] == pytest.approx(0.20)
    assert buy["volume_weighted_adverse_slippage_cost_per_standard_lot_account_currency"] == pytest.approx(15.0)
    assert sell["volume_weighted_adverse_slippage_cost_per_standard_lot_account_currency"] == pytest.approx(20.0)


def test_favorable_fill_is_not_misreported_as_adverse_slippage():
    result = aggregate(
        [order(10, 0, 2000.10)],
        [deal(10, 0, 0.10, 2000.00)],
    )
    buy = result["by_order_side"]["BUY"]
    assert buy["signed_deviation_usd_per_oz"]["mean"] == pytest.approx(-0.10)
    assert buy["adverse_slippage_usd_per_oz"]["mean"] == pytest.approx(0.0)
    assert buy["favorable_price_improvement_usd_per_oz"]["mean"] == pytest.approx(0.10)


def test_zero_or_missing_requested_price_is_excluded_not_assumed_zero_slippage():
    result = aggregate(
        [order(10, 0, 0.0), order(11, 1, None)],
        [deal(10, 0, 0.10, 2000.10), deal(11, 1, 0.10, 1999.90)],
    )
    assert result["matched_filled_order_count"] == 0
    assert result["counters"]["missing_or_invalid_specified_price_orders"] == 2
    assert result["by_order_side"]["BUY"]["signed_deviation_usd_per_oz"]["count"] == 0


def test_pending_orders_and_other_symbols_are_ignored():
    result = aggregate(
        [order(10, 2, 2000.00), order(11, 0, 2000.00, symbol="EURUSD")],
        [deal(10, 0, 0.10, 2000.10)],
    )
    assert result["market_order_count"] == 0
    assert result["matched_filled_order_count"] == 0


def test_invalid_price_units_are_rejected():
    with pytest.raises(ValueError, match="POINT_INVALID"):
        aggregate_requested_to_fill_slippage(
            [], [], symbol="XAUUSD",
            point=0.0, tick_size=0.01, tick_value=1.0,
            buy_order_type=0, sell_order_type=1,
            buy_deal_type=0, sell_deal_type=1,
        )
