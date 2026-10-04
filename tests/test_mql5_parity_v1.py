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


def test_parity_requires_full_fill_and_order_ticket_for_success():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")

    broken_order = source.replace("if(order == 0 || deal == 0) return false;", "if(deal == 0) return false;")
    try:
        audit_source(broken_order, contract)
    except Exception as exc:
        assert "order_ticket_verified" in str(exc)
    else:
        raise AssertionError("accepted execution must require a broker order ticket")

    broken_fill = source.replace(
        "if(MathAbs(confirmed_volume - requested_volume) > 1e-9) return false;",
        "if(false) return false;",
    )
    try:
        audit_source(broken_fill, contract)
    except Exception as exc:
        assert "full_fill_volume_verified" in str(exc)
    else:
        raise AssertionError("accepted execution must require full broker-confirmed volume")


def test_parity_rejects_partial_fill_as_success():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace(
        "return (rc == TRADE_RETCODE_DONE) && deal > 0;",
        "return (rc == TRADE_RETCODE_DONE || rc == TRADE_RETCODE_DONE_PARTIAL) && deal > 0;",
    )
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "partial_fill_not_accepted_as_success" in str(exc)
    else:
        raise AssertionError("partial broker execution must never be promoted to full success")


def test_parity_requires_consumption_persistence_result_check():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace(
        "if(!MarkRuntimeAuthorizationConsumed(trace_trade_id))",
        "MarkRuntimeAuthorizationConsumed(trace_trade_id)",
    )
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "consumption_failure_blocks_new_orders" in str(exc)
    else:
        raise AssertionError("authorization consumption persistence failure must block new orders")


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


def test_parity_requires_trade_permissions_and_close_verification():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("TradeModeAllows", "TradeModeRemoved").replace(
        "Protective closes are counted only after broker ResultRetcode confirmation.",
        "Protective closes use best effort."
    )
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "trade_mode_permission_checked" in str(exc) or "close_retcode_verified" in str(exc)
    else:
        raise AssertionError("trade permission and close-result checks must fail closed")


def test_parity_requires_runtime_trace_emitter():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("FOREXAI-RUNTIME-TRACE-V1", "FOREXAI-RUNTIME-TRACE-REMOVED")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_trace_schema" in str(exc)
    else:
        raise AssertionError("runtime trace emission must fail closed when removed")


def test_parity_rejects_runtime_trace_authority_tokens():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source + "\nstring forbidden_authority = \"CAPITAL_AUTHORIZATION_ISSUED\";\n"
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_trace_observational_only" in str(exc)
    else:
        raise AssertionError("runtime trace must not contain capital authority events")


def test_parity_requires_fail_closed_runtime_trace():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("if(!runtime_trace_healthy) return;", "if(runtime_trace_healthy) return;")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_trace_fail_closed" in str(exc)
    else:
        raise AssertionError("runtime trace failure must block new orders")


def test_runtime_trace_submission_is_recorded_before_result_verification():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    submit = source.index('"ORDER_SUBMITTED"', source.index('bool SendBuy'))
    result_check = source.index('if(!TradeExecutionAccepted())', submit)
    assert submit < result_check

    submit_sell = source.index('"ORDER_SUBMITTED"', source.index('bool SendSell'))
    result_check_sell = source.index('if(!TradeExecutionAccepted())', submit_sell)
    assert submit_sell < result_check_sell


def test_parity_rejects_malformed_runtime_trace_string_literals():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace('\\\"side', '"side', 1)
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "mql5_trace_string_literal_sanity" in str(exc)
    else:
        raise AssertionError("malformed MQL5 trace string literals must fail closed")

def test_parity_requires_result_order_evidence():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("trade.ResultOrder()", "trade.ResultOrderRemoved()")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "order_ticket_verified" in str(exc)
    else:
        raise AssertionError("broker order ticket must be recorded")


def test_parity_requires_runtime_authorization_record_binding():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("FOREXAI-AUTH-V1", "FOREXAI-AUTH-REMOVED")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_record_schema" in str(exc)
    else:
        raise AssertionError("runtime authorization record must be required")


def test_parity_requires_runtime_authorization_fail_closed():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("VerifyRuntimeAuthorization", "RuntimeAuthorizationRemoved")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_fail_closed" in str(exc)
    else:
        raise AssertionError("missing runtime authorization gate must fail closed")


def test_parity_requires_runtime_authorization_risk_cap():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("runtime_reserved_risk)", "runtime_reserved_risk_removed)")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_risk_cap" in str(exc)
    else:
        raise AssertionError("EA risk must remain capped by reserved authorization risk")


def test_parity_requires_consumed_authorization_persistence():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("MarkRuntimeAuthorizationConsumed", "MarkRuntimeAuthorizationRemoved")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_consumed" in str(exc)
    else:
        raise AssertionError("successful entry must consume its authorization record")


def test_parity_requires_pinned_runtime_execution_contract_version():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace('"forexai.execution.v1"', '"forexai.execution.forged.v1"')
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_execution_contract_version" in str(exc)
    else:
        raise AssertionError("runtime authorization must pin the execution contract version")


def test_parity_rejects_disablable_runtime_authorization_input():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("if(!RequireRuntimeAuthorization) return INIT_FAILED;", "if(RequireRuntimeAuthorization) return INIT_FAILED;")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_fail_closed" in str(exc)
    else:
        raise AssertionError("runtime authorization must not be user-disableable")


def test_parity_requires_authorization_symbol_binding():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("if(parts[5] != _Symbol)", "if(true)")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_symbol_binding" in str(exc)
    else:
        raise AssertionError("runtime authorization must bind to the chart symbol")


def test_parity_requires_authorization_timeframe_binding():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("if(parts[6] != current_timeframe)", "if(true)")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_timeframe_binding" in str(exc)
    else:
        raise AssertionError("runtime authorization must bind to the chart timeframe")


def test_parity_requires_single_attempt_authorization_lock():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("GlobalVariableSetOnCondition", "GlobalVariableSetRemoved")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_single_attempt" in str(exc)
    else:
        raise AssertionError("authorization must be single-attempt and atomically locked")


def test_parity_requires_fail_closed_consumption_persistence():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("GlobalVariablesFlush()", "GlobalVariablesFlushRemoved()")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_consumed" in str(exc)
    else:
        raise AssertionError("authorization consumption persistence must be verified")


def test_parity_requires_bounded_authorization_state_keys():
    source = (ROOT / "ea" / "GRK_Hybrid_Regime_EA.mq5").read_text(encoding="utf-8")
    contract = load_contract(ROOT / "config" / "forexai_execution_parity_v1.json")
    broken = source.replace("StringSubstr(digest, 0, 32)", "digest")
    try:
        audit_source(broken, contract)
    except Exception as exc:
        assert "runtime_authorization_state_key_bounded" in str(exc)
    else:
        raise AssertionError("authorization state keys must remain within MQL5 limits")
