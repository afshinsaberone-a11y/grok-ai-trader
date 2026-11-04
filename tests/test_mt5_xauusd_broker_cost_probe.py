from types import SimpleNamespace

import pytest

from tools.mt5_xauusd_broker_cost_probe import aggregate_closed_positions


def deal(position_id, entry, volume, commission=0.0, fee=0.0, swap=0.0, symbol="XAUUSD"):
    return SimpleNamespace(
        position_id=position_id, entry=entry, volume=volume,
        commission=commission, fee=fee, swap=swap, symbol=symbol,
    )


def test_closed_position_costs_are_converted_to_cost_per_ounce():
    rows = [
        deal(11, 0, 0.10, commission=-0.20, fee=-0.02, swap=-0.15),
        deal(11, 1, 0.10, commission=-0.20, fee=0.00, swap=0.00),
    ]
    result = aggregate_closed_positions(
        rows, symbol="XAUUSD", contract_size=100.0,
        entry_codes={0}, exit_codes={1},
    )

    assert result["closed_position_count"] == 1
    assert result["total_round_turn_lots"] == pytest.approx(0.10)
    assert result["commission_fee_cost_per_oz_account_currency"]["mean"] == pytest.approx(0.042)
    assert result["realized_financing_cost_per_oz_account_currency"]["mean"] == pytest.approx(0.015)
    assert result["per_bar_financing_schedule_available"] is False
    assert result["raw_deal_ids_exported"] is False


def test_open_or_partially_closed_positions_are_excluded():
    rows = [
        deal(11, 0, 0.10, commission=-0.20, swap=-0.1),
        deal(12, 0, 0.20, commission=-0.20, swap=-0.1),
        deal(12, 1, 0.10, commission=-0.10, swap=0.0),
    ]
    result = aggregate_closed_positions(
        rows, symbol="XAUUSD", contract_size=100.0,
        entry_codes={0}, exit_codes={1},
    )
    assert result["closed_position_count"] == 0
    assert result["sample_is_adequate_for_cost_review"] is False


def test_other_symbols_are_ignored_and_rebates_keep_signed_direction():
    rows = [
        deal(11, 0, 0.10, commission=0.20, symbol="EURUSD"),
        deal(11, 1, 0.10, commission=0.20, symbol="EURUSD"),
    ]
    result = aggregate_closed_positions(
        rows, symbol="XAUUSD", contract_size=100.0,
        entry_codes={0}, exit_codes={1},
    )
    assert result["closed_position_count"] == 0


def test_invalid_contract_size_is_rejected():
    with pytest.raises(ValueError, match="CONTRACT_SIZE_INVALID"):
        aggregate_closed_positions(
            [deal(11, 0, 0.1), deal(11, 1, 0.1)],
            symbol="XAUUSD", contract_size=0,
            entry_codes={0}, exit_codes={1},
        )
