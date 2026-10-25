from pathlib import Path


def test_provider_clean_host_bootstrap_is_pinned_and_fail_closed():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "tools" / "bootstrap_provider_host_v1.ps1"
    script = script_path.read_text(encoding="utf-8")

    # The bootstrap must install only hash/signature-verified official tools
    # and checkout the exact SHA that has matching current-main G13 evidence.
    assert "41883f30d32747d07d7b7772f8ee7c656a95e4a1" in script
    assert "python-3.13.17-amd64.exe" in script
    assert "5da012101ba2e17113a9a1cd901e9ce1441086f2b7ecb5de06ec94163899a190" in script
    assert "Git-2.56.0.3-64-bit.exe" in script
    assert "dc6d3db061999136e139f31376c5582a9ed6f36a4ea12f15e54ad7fa2bfc0bf2" in script
    assert "Get-AuthenticodeSignature" in script
    assert "INSTALLER_SHA256_MISMATCH" in script
    assert "CHECKED_OUT_SOURCE_SHA_MISMATCH" in script
    assert "SOURCE_CHECKOUT_NOT_CLEAN" in script

    # This is a software bootstrap only, never an authority or execution bootstrap.
    for forbidden in (
        "--initialize-registry",
        "New-Service",
        "sc.exe create",
        "FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE =",
        "FOREXAI_G13_ATTESTOR_KEY_PASSPHRASE =",
        "FOREXAI_CONTROL_PLANE_HMAC_SECRET =",
        "FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY =",
        "FOREXAI_PROVIDER_RISK_PUBLIC_KEY =",
        "FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY =",
        "FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY =",
        "order_send",
    ):
        assert forbidden not in script

    assert "provider_service_installed = $false" in script
    assert "issuance_registry_created = $false" in script
    assert "demo_trading_authorized = $false" in script
    assert "live_trading_allowed = $false" in script
    assert "orders_submitted = $false" in script


def test_elevated_bootstrap_installer_workspace_is_not_user_temp_and_is_acl_verified():
    root = Path(__file__).resolve().parents[1]
    script = (root / "tools" / "bootstrap_provider_host_v1.ps1").read_text(encoding="utf-8")

    # Installer downloads happen only after creation of a fresh, unpredictable
    # CommonApplicationData child with inheritance disabled and its final DACL
    # checked. The elevated script must not follow a user's TEMP junction.
    assert "$workRoot = New-ProtectedWorkRoot" in script
    assert "[Environment+SpecialFolder]::CommonApplicationData" in script
    assert "[Guid]::NewGuid().ToString('N')" in script
    assert "$workRoot = Join-Path $env:TEMP" not in script
    assert "/inheritance:r" in script
    assert "Get-Acl -LiteralPath $candidate" in script
    assert "AreAccessRulesProtected" in script
    assert "BOOTSTRAP_WORK_ROOT_UNEXPECTED_ACL" in script
    assert "[IO.FileAttributes]::ReparsePoint" in script
    assert "New-Item -ItemType Directory -Path $installerRoot -ErrorAction Stop" in script

    # Never delete a pre-existing installer-path occupant and then overwrite it.
    assert "INSTALLER_DESTINATION_ALREADY_EXISTS" in script
    assert "Remove-Item -LiteralPath $Destination -Force" not in script
