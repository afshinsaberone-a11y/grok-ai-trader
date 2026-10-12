from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from disable_mt5_internal_mcp_v1 import disable_internal_mcp  # noqa: E402


PROFILE_HASH = "D0E8209F77C8CF37AD8BF550E51FF075"


def make_profile(tmp_path: Path) -> Path:
    profile = tmp_path / "MetaQuotes" / "Terminal" / PROFILE_HASH
    (profile / "Config").mkdir(parents=True)
    return profile


def read_ini(profile: Path) -> str:
    return (profile / "Config" / "assistant.ini").read_text(encoding="utf-8-sig")


def section_enable_values(text: str, section: str) -> list[str]:
    active = False
    values = []
    for line in text.splitlines():
        if line.strip().startswith("[") and line.strip().endswith("]"):
            active = line.strip()[1:-1].casefold() == section.casefold()
        elif active and line.lstrip().casefold().startswith("enable"):
            key, sep, value = line.partition("=")
            if sep and key.strip().casefold() == "enable":
                values.append(value.split(";", 1)[0].split("#", 1)[0].strip())
    return values


def test_disables_only_mcp_endpoints_and_preserves_other_settings(tmp_path: Path):
    profile = make_profile(tmp_path)
    config = profile / "Config" / "assistant.ini"
    config.write_text(
        "; preserve header\r\n"
        "[General]\r\n"
        "Theme=dark\r\n"
        "[MCP.MetaTrader]\r\n"
        "Enable=1 ; endpoint setting\r\n"
        "Port=22346\r\n"
        "APIKey=do-not-touch\r\n"
        "[MCP.MetaEditor]\r\n"
        "Enable = 1\r\n"
        "Port=22345\r\n"
        "[Other]\r\n"
        "Enable=1\r\n",
        encoding="utf-8",
    )

    result = disable_internal_mcp(profile)
    text = result.read_text(encoding="utf-8")

    assert section_enable_values(text, "MCP.MetaTrader") == ["0"]
    assert section_enable_values(text, "MCP.MetaEditor") == ["0"]
    assert "Theme=dark" in text
    assert "Port=22346" in text
    assert "Port=22345" in text
    assert "APIKey=do-not-touch" in text
    assert "[Other]\nEnable=1" in text or "[Other]\r\nEnable=1" in text
    assert "Enable=0 ; endpoint setting" in text


def test_creates_missing_mcp_sections_and_is_idempotent(tmp_path: Path):
    profile = make_profile(tmp_path)
    config = profile / "Config" / "assistant.ini"
    config.write_text("[General]\nTheme=dark\n", encoding="utf-8")

    first = disable_internal_mcp(profile).read_bytes()
    second = disable_internal_mcp(profile).read_bytes()

    assert first == second
    text = config.read_text(encoding="utf-8")
    assert section_enable_values(text, "MCP.MetaTrader") == ["0"]
    assert section_enable_values(text, "MCP.MetaEditor") == ["0"]
    assert "Theme=dark" in text


def test_all_duplicate_mcp_sections_are_disabled(tmp_path: Path):
    profile = make_profile(tmp_path)
    config = profile / "Config" / "assistant.ini"
    config.write_text(
        "[MCP.MetaTrader]\nEnable=1\n"
        "[MCP.MetaEditor]\nEnable=1\n"
        "[MCP.MetaTrader]\nEnable=1\n"
        "[MCP.MetaEditor]\nEnable=1\n",
        encoding="utf-8",
    )

    disable_internal_mcp(profile)
    text = config.read_text(encoding="utf-8")

    assert section_enable_values(text, "MCP.MetaTrader") == ["0", "0"]
    assert section_enable_values(text, "MCP.MetaEditor") == ["0", "0"]


def test_refuses_non_mt5_profile_path_without_creating_files(tmp_path: Path):
    profile = tmp_path / "not-an-mt5-profile"
    profile.mkdir()

    with pytest.raises(ValueError, match="32-character hexadecimal"):
        disable_internal_mcp(profile)

    assert not (profile / "Config").exists()


def test_refuses_symlinked_assistant_ini(tmp_path: Path):
    profile = make_profile(tmp_path)
    external = tmp_path / "external.ini"
    external.write_text("[MCP.MetaTrader]\nEnable=1\n", encoding="utf-8")
    (profile / "Config" / "assistant.ini").symlink_to(external)

    with pytest.raises(ValueError, match="must not be a symlink"):
        disable_internal_mcp(profile)

    assert "Enable=1" in external.read_text(encoding="utf-8")


def test_refuses_unsupported_encoding_without_mutating_file(tmp_path: Path):
    profile = make_profile(tmp_path)
    config = profile / "Config" / "assistant.ini"
    original = b"\xff\xfe\x00\x00not-a-supported-config"
    config.write_bytes(original)

    with pytest.raises(ValueError, match="encoding is unsupported"):
        disable_internal_mcp(profile)

    assert config.read_bytes() == original


def test_compile_parity_workflow_disables_only_its_profile_mcp_before_launch():
    workflow = (
        ROOT / ".github/workflows/forexai-g13-mt5-compile-parity.yml"
    ).read_text(encoding="utf-8")

    step_start = workflow.index("- name: Run MQL5 real-data parity script")
    step_end = workflow.index("      - name: Collect MT5 parity diagnostics", step_start)
    launch_step = workflow[step_start:step_end]
    helper_call = "disable_mt5_internal_mcp_v1.py"
    assert helper_call in launch_step
    assert launch_step.index(helper_call) < launch_step.index("$procInfo = @(")
    # MT5 startup scripts require a chart context; the runner profile may have no valid saved chart.
    assert "Symbol=EURUSD" in launch_step
    assert "Period=M15" in launch_step
    assert launch_step.index("Symbol=EURUSD") < launch_step.index("Script=ForexAI_G13_Parity_Harness.ex5")
    helper = (ROOT / "tools/disable_mt5_internal_mcp_v1.py").read_text(encoding="utf-8")
    assert "MCP.MetaTrader" in helper
    assert "MCP.MetaEditor" in helper
    assert "if (-not $isSystemOwner -and $isBareTerminal)" in workflow
    assert "MT5_EXTERNAL_BARE_TERMINAL_PRESERVED" in workflow
    assert "A MetaTrader terminal instance is already running with the current G13 parity config." in workflow
    assert "Stop-Process -Id ([int]$p.ProcessId) -Force" in workflow
    assert "Stop-Process -Name terminal64.exe" not in workflow
    assert "AllowLiveTrading=0" in workflow
    assert "SetDenyKillSwitch" not in workflow  # This workflow is compile/parity-only and never changes the switch.
