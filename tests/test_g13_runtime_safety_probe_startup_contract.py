from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
)


def test_runtime_probe_uses_extensionless_mt5_startup_script_names():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert (
        '"G13_AUTH_OFF_SCRIPT=G13_Safety_Probe_AuthOff_$($env:GITHUB_RUN_ID)"'
        in workflow
    )
    assert (
        '"G13_AUTH_ON_SCRIPT=G13_Safety_Probe_AuthOn_$($env:GITHUB_RUN_ID)"'
        in workflow
    )
    assert "Script=$scriptRel" in workflow
    assert "Dest=($env:G13_AUTH_OFF_SCRIPT + '.ex5')" in workflow
    assert "Dest=($env:G13_AUTH_ON_SCRIPT + '.ex5')" in workflow
    assert "($scriptRel + '.ex5')" in workflow
    assert "Script=$scriptRel.ex5" not in workflow
    assert (
        '"G13_AUTH_OFF_SCRIPT=G13_Safety_Probe_AuthOff_$($env:GITHUB_RUN_ID).ex5"'
        not in workflow
    )



def test_runtime_probe_resolves_configured_profile_when_mt5_is_closed():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    start = workflow.index("      - name: Resolve MT5 service paths\\n")
    end = workflow.index("      - name: Static no-order preflight\\n", start)
    step = workflow[start:end]

    assert "$interactiveTerminals = @(Get-CimInstance Win32_Process -Filter \\"Name='terminal64.exe'\\"" in step
    assert "$configuredDataRoot = [System.IO.Path]::GetFullPath($env:MT5_DATA_ROOT)" in step
    assert "$desktopShells = @(Get-CimInstance Win32_Process -Filter \\"Name='explorer.exe'\\"" in step
    assert "G13_MT5_CONFIGURED_DATA_ROOT_INVALID" in step
    assert "G13_MT5_CONFIGURED_PROFILE_UNRESOLVED" in step
    assert "G13_MT5_INTERACTIVE_DESKTOP_REQUIRED" in step
    assert "G13_MT5_PROFILE_RESOLUTION_SOURCE=CONFIGURED_PROFILE_MATCHING_DESKTOP" in step
    assert "SessionId -gt 0" in step
    assert "AllowLiveTrading=0" not in step  # no configs are generated in the resolver itself


def test_runtime_probe_requires_identity_verified_connected_demo_markers():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for required in (
        "G13_RUNTIME_AUTH_OFF_ACCOUNT_IDENTITY_UNVERIFIED",
        "G13_RUNTIME_AUTH_OFF_TERMINAL_DISCONNECTED",
        "G13_RUNTIME_AUTH_OFF_DEMO_ACCOUNT_UNVERIFIED",
        "G13_RUNTIME_AUTH_ON_ACCOUNT_IDENTITY_UNVERIFIED",
        "G13_RUNTIME_AUTH_ON_TERMINAL_DISCONNECTED",
        "G13_RUNTIME_AUTH_ON_DEMO_ACCOUNT_UNVERIFIED",
    ):
        assert required in workflow

    for probe_name in (
        "research/optimization/G13_Safety_Probe_AuthOff.mq5",
        "research/optimization/G13_Safety_Probe_AuthOn.mq5",
    ):
        probe = Path(probe_name).read_text(encoding="utf-8")
        assert "AccountInfoInteger(ACCOUNT_LOGIN)" in probe
        assert "AccountInfoString(ACCOUNT_SERVER)" in probe
        assert "account_identity_verified" in probe
        assert "terminal_connected" in probe
        assert 'FileWrite(h,"orders_submitted,false")' in probe
