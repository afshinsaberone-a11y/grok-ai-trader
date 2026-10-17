from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_profile_wrapper_falls_back_only_when_mt5_process_is_absent():
    helper = (
        ROOT / "tools/resolve_mt5_profile_or_desktop_v1.ps1"
    ).read_text(encoding="utf-8")

    assert "resolve_mt5_common_files_v1.ps1" in helper
    assert "resolve_mt5_interactive_profile_v1.ps1" in helper
    assert "G13_MT5_TERMINAL_PROCESS_NOT_FOUND:" in helper
    assert "if ($resolutionError -notmatch '^G13_MT5_TERMINAL_PROCESS_NOT_FOUND:')" in helper
    assert "G13_MT5_TERMINAL_PROCESS_PATH_MISMATCH" not in helper or (
        "G13_MT5_PROFILE_RESOLUTION_FAILED" in helper
    )
    assert "G13_MT5_CONFIGURED_DATA_ROOT_MISSING" in helper
    assert "G13_MT5_INTERACTIVE_SESSION_REQUIRED" in helper
    assert "G13_MT5_COMMON_FILES_PATH_MISMATCH" in helper
    assert "G13_MT5_INTERACTIVE_PROFILE_OUTPUT_INCOMPLETE" in helper
    assert "Win32_UserProfile" not in helper  # delegated to the audited desktop resolver
    assert "APPDATA=$appData" in helper
    assert "FOREXAI_MT5_COMMON_FILES=$canonicalCommonFiles" in helper


def test_closed_terminal_preflight_keeps_kill_switch_deny_and_never_starts_mt5():
    helper = (
        ROOT / "tools/resolve_mt5_profile_or_desktop_v1.ps1"
    ).read_text(encoding="utf-8")

    assert "SetDenyKillSwitch" in helper
    assert "'DENY'" in helper
    assert "G13_KILL_SWITCH_INITIAL_DENY_VERIFICATION_FAILED" in helper
    assert "G13_MT5_COMMON_FILES_WRITE_ACCESS_DENIED" in helper
    assert "'ALLOW'" not in helper
    assert "Start-Process" not in helper
    assert "order_send" not in helper.lower()
    assert "orders_submitted" not in helper.lower()


def test_capital_preflight_and_control_plane_producer_use_exact_desktop_fallback():
    preflight = (
        ROOT
        / ".github/workflows/forexai-capital-firewall-authorization-preflight.yml"
    ).read_text(encoding="utf-8")
    producer = (
        ROOT / ".github/workflows/forexai-control-plane-producer-v1.yml"
    ).read_text(encoding="utf-8")

    for workflow in (preflight, producer):
        assert "resolve_mt5_profile_or_desktop_v1.ps1" in workflow
        assert "MT5_DATA_ROOT:" in workflow
        assert "D0E8209F77C8CF37AD8BF550E51FF075" in workflow
        assert '-DataRoot "$env:MT5_DATA_ROOT" -SetDenyKillSwitch' in workflow
        assert "I_CONFIRM_G13_DEMO_ONLY" not in workflow or (
            "ORDER_SUBMISSION_ENABLED=false" in workflow
        )

    assert "INTERACTIVE_SESSION_REQUIRED" in preflight
    assert "MT5_PROFILE_RESOLUTION_FAILED" in preflight
    assert "$resolverExit = $LASTEXITCODE" not in producer
