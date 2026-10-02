"""Tests for the MQL5 execution parity static audit."""
from pathlib import Path

from tools.validate_mql5_parity_v1 import audit_source, load_contract


ROOT = Path(__file__).resolve().parents[1]


def test_current_mql5_adapter_passes_static_parity_contract():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    result = audit_source(source, contract)
    assert result["status"] == "PASS"
    assert result["semantic_execution_identity"] == "required"
    assert result["market_price_identity"] == "not_required"


def test_parity_rejects_hardcoded_noncanonical_expiry():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("input int    MaxHoldBars        = 30;", "input int    MaxHoldBars        = 48;")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "max_hold_bars_30" in str(exc)
    else:
        raise AssertionError("noncanonical MQL5 expiry must fail closed")


def test_parity_requires_restart_safe_state():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("GlobalVariableSet", "TerminalVariableSet")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "restart_state_persistence" in str(exc)
    else:
        raise AssertionError("restart safety persistence must fail closed")
