from pathlib import Path
import pytest

from tools.g13_demo_execution_collector_v1 import (
    CONTEXT_SCHEMA,
    CONFIRMATION,
    build_context,
)


def _snap():
    return {
        "account_login": 1,
        "account_server": "Demo",
        "account_mode": "DEMO",
        "terminal_connected": True,
        "account_trade_allowed": True,
        "account_trade_expert": True,
        "symbol_visible": True,
        "symbol_trade_mode": 4,
        "bid": 1.1,
        "ask": 1.2,
        "terminal_build": "1",
    }


def test_context_is_demo_only():
    payload = build_context(
        mt5_snapshot=_snap(),
        candidate_id=2,
        confirmation=CONFIRMATION,
        kill_switch="ALLOW",
        terminal_path="C:/MT5/terminal64.exe",
        audit_path=Path("g13_demo_execution_audit.csv"),
    )
    assert payload["schema"] == CONTEXT_SCHEMA
    assert payload["account_mode"] == "DEMO"
    assert payload["live_enabled"] is False
    assert payload["explicit_demo_authorization"] is True
    assert payload["collector_policy"]["order_submission_performed"] is False
    assert payload["collector_policy"]["retry_performed"] is False
    assert payload["collector_policy"]["python_order_send_used"] is False
    assert payload["collector_policy"]["kill_switch_modified"] is False


def test_wrong_confirmation_rejected():
    with pytest.raises(Exception, match="EXPLICIT_CONFIRMATION_REQUIRED"):
        build_context(
            mt5_snapshot=_snap(),
            candidate_id=2,
            confirmation="NOPE",
            kill_switch="ALLOW",
            terminal_path=None,
            audit_path=Path("audit.csv"),
        )


def test_non_allow_kill_switch_rejected():
    with pytest.raises(Exception, match="KILL_SWITCH_NOT_ALLOW"):
        build_context(
            mt5_snapshot=_snap(),
            candidate_id=2,
            confirmation=CONFIRMATION,
            kill_switch="BLOCK",
            terminal_path=None,
            audit_path=Path("audit.csv"),
        )


def test_non_demo_context_rejected():
    snap = _snap()
    snap["account_mode"] = "REAL"
    with pytest.raises(Exception, match="CONTEXT_NOT_DEMO"):
        build_context(
            mt5_snapshot=snap,
            candidate_id=2,
            confirmation=CONFIRMATION,
            kill_switch="ALLOW",
            terminal_path=None,
            audit_path=Path("audit.csv"),
        )


def test_wait_requires_done_order_deal_and_full_fill(tmp_path):
    from tools.g13_demo_execution_collector_v1 import _wait_for_candidate
    path = tmp_path / "audit.csv"
    header = "candidate_id,event,order,deal,retcode,requested_volume,executed_volume\n"
    path.write_text(
        header
        + "2,ORDER_ATTEMPT,0,0,10030,0.10,0.10\n"
        + "2,ORDER_ATTEMPT,7001,8001,10009,0.10,0.10\n",
        encoding="utf-8",
    )
    rows = _wait_for_candidate(
        path,
        candidate_id=2,
        timeout_seconds=1,
        poll_seconds=0.01,
        done_retcode=10009,
    )
    assert len(rows) == 2


def test_wait_rejects_partial_fill(tmp_path):
    from tools.g13_demo_execution_collector_v1 import _wait_for_candidate
    path = tmp_path / "audit.csv"
    path.write_text(
        "candidate_id,event,order,deal,retcode,requested_volume,executed_volume\n"
        "2,ORDER_ATTEMPT,7001,8001,10010,0.10,0.05\n",
        encoding="utf-8",
    )
    with pytest.raises(Exception, match="NO_ORDER_ATTEMPT"):
        _wait_for_candidate(
            path,
            candidate_id=2,
            timeout_seconds=1,
            poll_seconds=0.01,
            done_retcode=10009,
        )
