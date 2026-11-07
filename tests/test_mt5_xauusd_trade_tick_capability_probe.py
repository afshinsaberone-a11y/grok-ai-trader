import numpy as np
import pytest

from tools.mt5_xauusd_trade_tick_capability_probe import (
    summarize_tick_capabilities,
)


def ticks(rows):
    return np.array(
        rows,
        dtype=[
            ("time_msc", "i8"),
            ("bid", "f8"),
            ("ask", "f8"),
            ("last", "f8"),
            ("volume", "u8"),
            ("volume_real", "f8"),
            ("flags", "u4"),
        ],
    )


def test_quote_only_ticks_do_not_claim_trade_side_flow():
    data = ticks([
        (1000, 2000.0, 2000.2, 0.0, 0, 0.0, 2),
        (1500, 2000.0, 2000.3, 0.0, 0, 0.0, 4),
        (1900, 2000.1, 2000.3, 0.0, 0, 0.0, 6),
    ])
    result = summarize_tick_capabilities(data, start_ms=1000, end_ms=2000)

    assert result["ticks_in_segment"] == 3
    assert result["valid_two_sided_quote_ticks"] == 3
    assert result["bid_update_ticks"] == 2
    assert result["ask_update_ticks"] == 2
    assert result["both_quote_update_ticks"] == 1
    assert result["buy_side_flag_ticks"] == 0
    assert result["sell_side_flag_ticks"] == 0
    assert result["buy_volume_real_sum"] == 0.0
    assert result["sell_volume_real_sum"] == 0.0


def test_buy_and_sell_trade_flags_and_volume_are_separated():
    data = ticks([
        (1000, 2000.0, 2000.2, 2000.1, 2, 2.5, 8 | 16 | 32),
        (1500, 2000.1, 2000.3, 2000.2, 3, 3.25, 8 | 16 | 64),
    ])
    result = summarize_tick_capabilities(data, start_ms=1000, end_ms=2000)

    assert result["buy_side_flag_ticks"] == 1
    assert result["sell_side_flag_ticks"] == 1
    assert result["buy_volume_update_ticks"] == 1
    assert result["sell_volume_update_ticks"] == 1
    assert result["buy_volume_real_sum"] == pytest.approx(2.5)
    assert result["sell_volume_real_sum"] == pytest.approx(3.25)
    assert result["volume_basis"] == "volume_real"


def test_ambiguous_flags_and_out_of_range_ticks_are_reported_not_relabelled():
    data = ticks([
        (999, 2000.0, 2000.2, 0.0, 0, 0.0, 2),
        (1000, 2000.0, 2000.2, 2000.1, 1, 1.0, 8 | 16 | 32 | 64),
        (2000, 2000.0, 2000.2, 0.0, 0, 0.0, 2),
    ])
    result = summarize_tick_capabilities(data, start_ms=1000, end_ms=2000)

    assert result["ticks_outside_segment_filtered"] == 2
    assert result["ambiguous_buy_and_sell_flag_ticks"] == 1
    assert result["buy_side_flag_ticks"] == 0
    assert result["sell_side_flag_ticks"] == 0


def test_missing_flags_fail_closed():
    data = np.array([(1000, 2000.0, 2000.2)], dtype=[
        ("time_msc", "i8"), ("bid", "f8"), ("ask", "f8")
    ])
    with pytest.raises(RuntimeError, match="MT5_TICK_FIELD_MISSING:flags"):
        summarize_tick_capabilities(data, start_ms=1000, end_ms=2000)



from tools.mt5_xauusd_trade_tick_capability_probe import summarize_market_book_snapshot


def test_dom_snapshot_aggregates_limit_and_market_levels_separately():
    result = summarize_market_book_snapshot([
        {"type": 1, "price": 2025.0, "volume_dbl": 3.0, "volume": 3},
        {"type": 2, "price": 2024.9, "volume_dbl": 4.0, "volume": 4},
        {"type": 3, "price": 2025.1, "volume_dbl": 0.5, "volume": 1},
        {"type": 4, "price": 2024.8, "volume_dbl": 0.25, "volume": 1},
    ])
    assert result["sell_limit_levels"] == 1
    assert result["buy_limit_levels"] == 1
    assert result["sell_market_levels"] == 1
    assert result["buy_market_levels"] == 1
    assert result["sell_limit_volume"] == pytest.approx(3.0)
    assert result["buy_limit_volume"] == pytest.approx(4.0)
    assert result["sell_market_volume"] == pytest.approx(0.5)
    assert result["buy_market_volume"] == pytest.approx(0.25)
    assert result["best_ask_price"] == pytest.approx(2025.0)
    assert result["best_bid_price"] == pytest.approx(2024.9)
    assert result["displayed_limit_depth_imbalance"] == pytest.approx(1 / 7)


def test_empty_dom_snapshot_is_reported_without_fake_depth():
    result = summarize_market_book_snapshot([])
    assert result["levels_returned"] == 0
    assert result["buy_limit_volume"] == 0.0
    assert result["sell_limit_volume"] == 0.0
    assert result["displayed_limit_depth_imbalance"] is None


def test_dom_unknown_and_invalid_levels_are_not_classified():
    result = summarize_market_book_snapshot([
        {"type": 99, "price": 2025.0, "volume_dbl": 10.0},
        {"type": 1, "price": 0.0, "volume_dbl": 5.0},
    ])
    assert result["unknown_type_levels"] == 1
    assert result["invalid_price_or_volume_levels"] == 1
    assert result["sell_limit_levels"] == 0
