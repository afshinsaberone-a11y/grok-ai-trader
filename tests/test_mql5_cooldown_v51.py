"""Regression guard for the V51 consecutive-loss cooldown.

These tests inspect the MQL5 control-flow contract. They do not claim trading
performance or replace MetaTrader compilation / broker-side validation.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EA_PATH = ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5"


def test_v51_loss_cooldown_can_reach_its_countdown():
    source = EA_PATH.read_text(encoding="utf-8")

    on_tick = source.split("void OnTick()", 1)[1].split(
        "// FOREXAI-EXECUTION-CONTRACT-V1", 1
    )[0]

    # A permanent loss-count return before the cooldown used to make the
    # countdown unreachable after ConsecutiveHalt was reached.
    assert "if(consec_losses >= ConsecutiveHalt) return;" not in on_tick

    new_bar_gate = on_tick.index("if(t == last_bar) return;")
    cooldown_gate = on_tick.index("if(halt_bars_left > 0)")
    decrement = on_tick.index("halt_bars_left--;")
    spread_gate = on_tick.index("if(!SpreadOk()) return;")
    strategy_dispatch = on_tick.index("int rg = Regime();")

    # Cooldown advances once per new chart bar, before spread/session entry
    # filters, and a halted bar cannot reach strategy signal dispatch.
    assert new_bar_gate < cooldown_gate < decrement < spread_gate
    assert decrement < strategy_dispatch
    assert on_tick.count("halt_bars_left--;") == 1


def test_v51_three_losses_arm_cooldown_and_a_winning_close_resets_count():
    source = EA_PATH.read_text(encoding="utf-8")
    on_transaction = source.split("void OnTradeTransaction", 1)[1].split(
        "void OnTick()", 1
    )[0]

    assert "if(consec_losses >= ConsecutiveHalt) halt_bars_left = HaltCooldownBars;" in on_transaction
    assert "else consec_losses = 0;" in on_transaction
    assert "input int    ConsecutiveHalt    = 3;" in source
    assert "input int    HaltCooldownBars   = 8;" in source
