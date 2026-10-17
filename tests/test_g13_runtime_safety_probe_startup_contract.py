from pathlib import Path


def test_runtime_probe_uses_extensionless_mt5_startup_script_names():
    workflow = Path(
        ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
    ).read_text(encoding="utf-8")

    # MT5's [StartUp] Script setting is a relative name under MQL5/Scripts,
    # without the compiled .ex5 suffix. Deployment still needs the .ex5 file.
    assert (
        '"G13_AUTH_OFF_SCRIPT=G13_Safety_Probe_AuthOff_$($env:GITHUB_RUN_ID)"'
        in workflow
    )
    assert (
        '"G13_AUTH_ON_SCRIPT=G13_Safety_Probe_AuthOn_$($env:GITHUB_RUN_ID)"'
        in workflow
    )
    assert "Script=$scriptRel" in workflow
    assert "($pair.ScriptBase + '.ex5')" in workflow
    assert "Script=$scriptRel.ex5" not in workflow
    assert (
        '"G13_AUTH_OFF_SCRIPT=G13_Safety_Probe_AuthOff_$($env:GITHUB_RUN_ID).ex5"'
        not in workflow
    )


def test_runtime_probe_remains_non_trading_and_fail_closed():
    workflow = Path(
        ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
    ).read_text(encoding="utf-8")
    for required in (
        "G13_RUNTIME_AUTH_OFF_MARKER_MISSING",
        "G13_RUNTIME_AUTH_ON_MARKER_MISSING",
        "orders_submitted,false",
        "Enforce shared Kill Switch DENY",
        "ShutdownTerminal=1",
        "AllowLiveTrading=0",
    ):
        assert required in workflow
