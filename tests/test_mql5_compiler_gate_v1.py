"""Contract tests for the real MetaEditor MQL5 compiler gate."""
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]


def _load():
    return json.loads(
        (ROOT / "config/forexai_mql5_compiler_gate_v1.json").read_text(
            encoding="utf-8"
        )
    )


def _workflow():
    return (
        ROOT / ".github/workflows/forexai-mql5-compiler.yml"
    ).read_text(encoding="utf-8")


def test_compiler_contract_is_fail_closed():
    c = _load()
    assert c["schema_version"] == "forexai.mql5_compiler_gate.v1"
    assert c["source"] == "ea/GRK_Hybrid_Regime_EA.mq5"
    assert c["runner"]["labels"] == ["self-hosted", "windows", "mt5"]
    assert c["compiler"]["executable"] == "metaeditor64.exe"
    assert c["compiler"]["flags"] == ["/compile", "/include", "/log"]
    assert c["compiler"]["isolated_workspace"] is True
    assert c["success"]["process_exit_code"] == 0
    assert c["success"]["compilation_log_required"] is True
    assert c["success"]["compiled_ex5_required"] is True
    assert c["success"]["zero_errors_required"] is True
    assert all(v == "FAIL_CLOSED" for v in c["failure_policy"].values())
    assert c["live_trading"]["enabled_by_gate"] is False
    assert c["live_trading"]["account_mode"] == "DEMO_ONLY"


def test_compiler_workflow_uses_real_metaeditor_and_is_manual():
    workflow = _workflow()
    assert "workflow_dispatch:" in workflow
    assert "runs-on: [self-hosted, windows, mt5]" in workflow
    assert "/compile:" in workflow
    assert "/include:" in workflow
    assert "/log" in workflow
    assert "GRK_Hybrid_Regime_EA.ex5" in workflow
    assert "MQL5_COMPILER_ERRORS_REPORTED" in workflow
    assert "MQL5_COMPILER_SUCCESS_NOT_PROVABLE" in workflow
    assert "forexai-mql5-compiler-evidence" in workflow


def test_compiler_workflow_cannot_enable_real_trading():
    workflow = _workflow()
    assert "FOREXAI_ALLOW_REAL_TRADING" not in workflow
    assert "REAL_ALLOWED" not in workflow
    assert "REAL_ALLOWED" not in workflow
