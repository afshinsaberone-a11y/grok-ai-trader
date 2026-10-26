from pathlib import Path


def test_provider_clean_host_bootstrap_is_pinned_and_fail_closed():
    root = Path(__file__).resolve().parents[1]
    script_path = root / "tools" / "bootstrap_provider_host_v1.ps1"
    script = script_path.read_text(encoding="utf-8")

    # The bootstrap must install only hash/signature-verified official tools
    # and checkout the exact SHA that has matching current-main G13 evidence.
    assert "41883f30d32747d07d7b7772f8ee7c656a95e4a1" in script
    # An elevated bootstrap runs the checked-out code and dependencies. A caller
    # must not be able to substitute an arbitrary commit at invocation time.
    assert "$expectedCommit = '41883f30d32747d07d7b7772f8ee7c656a95e4a1'" in script
    assert "[string]$ExpectedCommit" not in script
    assert "$ExpectedCommit =" not in script
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

    assert "import cryptography; print('PROVIDER_RUNTIME_DEPENDENCIES=PASS')" in script
    assert "import cryptography, pytest; print('PROVIDER_TEST_DEPENDENCIES=PASS')" in script
    assert "import cryptography, numpy, pandas, backtesting, pytest" not in script
    assert "provider_service_installed = $false" in script
    assert "issuance_registry_created = $false" in script
    assert "demo_trading_authorized = $false" in script
    assert "live_trading_allowed = $false" in script
    assert "orders_submitted = $false" in script
    # The elevated target is restricted to one fresh direct child of the actual
    # CommonApplicationData directory; reject relative/arbitrary/reparse paths.
    assert "PROVIDER_ROOT_MUST_BE_ABSOLUTE" in script
    assert "PROVIDER_ROOT_MUST_BE_DIRECT_PROGRAMDATA_CHILD" in script
    assert "PROVIDER_ROOT_PARENT_MUST_NOT_BE_REPARSE_POINT" in script
    assert "PROVIDER_ROOT_CREATED_AS_REPARSE_POINT" in script
    assert "New-Item -ItemType Directory -Path $ProviderRoot -ErrorAction Stop" in script

    # Do not adopt an executable that was already present and only claims the
    # expected version; install verified packages into dedicated empty paths.
    assert "ForexAI-Pinned-Git-2.56.0.3" in script
    assert "ForexAI-Pinned-Python-3.13.17" in script
    assert "GIT_INSTALL_ROOT_ALREADY_EXISTS_INSPECT_BEFORE_RESUME" in script
    assert "PYTHON_INSTALL_ROOT_ALREADY_EXISTS_INSPECT_BEFORE_RESUME" in script
    assert "GIT_INSTALL_ROOT_APPEARED_DURING_BOOTSTRAP" in script
    assert "PYTHON_INSTALL_ROOT_APPEARED_DURING_BOOTSTRAP" in script
    assert "if (-not (Test-Path -LiteralPath $gitExe -PathType Leaf)) {" + "\n        $gitInstallerReport" not in script
    assert "if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {" + "\n        $pythonInstallerReport" not in script


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



def test_elevated_bootstrap_requires_a_committed_hash_lock_and_never_upgrades_pip():
    root = Path(__file__).resolve().parents[1]
    script = (root / "tools" / "bootstrap_provider_host_v1.ps1").read_text(encoding="utf-8")

    # Dependency resolution must not happen on the elevated host. The fixed
    # reviewed source SHA must carry a reviewed complete lock or bootstrap stops.
    assert "$providerLockPath = Join-Path $sourceRoot 'requirements-provider.lock.txt'" in script
    assert "$providerTestLockPath = Join-Path $sourceRoot 'requirements-provider-test.lock.txt'" in script
    assert "HASH_LOCKED_PROVIDER_REQUIREMENTS_MISSING" in script
    assert "HASH_LOCKED_PROVIDER_TEST_REQUIREMENTS_MISSING" in script
    assert "HASH_LOCKED_PROVIDER_REQUIREMENTS_INVALID" in script
    assert script.index("$providerLockPath = Join-Path $sourceRoot") < script.index("& $pythonExe -m venv $venvRoot")
    assert "--require-hashes" in script
    assert "--only-binary=:all:" in script
    assert "dependency_lock_sha256 =" in script
    assert "test_dependency_lock_sha256 =" in script
    assert "& $venvPython -m pip install" in script
    assert "& $providerTestPython -m pip install" in script
    assert "Remove-Item -LiteralPath $providerTestVenvRoot -Recurse -Force" in script

    # pip shipped with the SHA-256-pinned Python installer remains in place;
    # don't upgrade to an unpinned latest release or use the range-based input.
    assert "--upgrade pip" not in script
    assert "-r (Join-Path $sourceRoot 'requirements.txt')" not in script
    assert "-r $providerLockPath" in script
    assert "PROJECT_HASH_LOCKED_DEPENDENCY_INSTALL_FAILED" in script
