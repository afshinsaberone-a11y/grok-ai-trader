import hashlib
import re
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

    # Before the bootstrap writes source or creates a venv under the elevated
    # Provider root, it must break inheritance and read back an exact two-ACE DACL.
    assert "function Set-ProtectedProviderRootAcl" in script
    assert "PROVIDER_ROOT_ACL_INHERITANCE_ENABLED" in script
    assert "PROVIDER_ROOT_ACL_UNEXPECTED_ACE_COUNT" in script
    assert "PROVIDER_ROOT_ACL_UNEXPECTED_ACE" in script
    assert "PROVIDER_ROOT_ACL_PRINCIPAL_SET_MISMATCH" in script
    assert "provider_root_acl = $providerRootAclReport" in script
    assert script.index("$providerRootAclReport = Set-ProtectedProviderRootAcl -Path $ProviderRoot") < script.index("$sourceRoot = Join-Path $ProviderRoot 'source'")

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




def test_elevated_bootstrap_requires_committed_hash_locks_and_never_upgrades_pip():
    root = Path(__file__).resolve().parents[1]
    script = (root / "tools" / "bootstrap_provider_host_v1.ps1").read_text(encoding="utf-8")

    expected_locks = {
        "requirements-provider.lock.txt": "7df03080328bd565c1bb20dbdc4d9dfb90c39d86c4d1f8be35e46f452552af9a",
        "requirements-provider-test.lock.txt": "f6fb8ead273fa7416c8bdecce16eb7c18ff554503525fb9e656e0059788e0394",
    }
    for filename, expected_sha256 in expected_locks.items():
        lock_path = root / filename
        assert lock_path.is_file()
        lock_text = lock_path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        assert hashlib.sha256(lock_text.encode("utf-8")).hexdigest() == expected_sha256
        assert re.search(r"(?m)^\s*[A-Za-z0-9][A-Za-z0-9._-]*==[^\s\\]+", lock_text)
        assert re.search(r"(?m)--hash=sha256:[0-9a-f]{64}", lock_text)

    # Lock files travel with the reviewed bootstrap revision, not the old
    # pinned application checkout. The elevated copy is made under the
    # protected workspace and its canonical LF hash is verified before installs.
    assert "$providerLockSource = Join-Path $bootstrapRoot 'requirements-provider.lock.txt'" in script
    assert "$providerTestLockSource = Join-Path $bootstrapRoot 'requirements-provider-test.lock.txt'" in script
    assert "$providerLockPath = Join-Path $workRoot 'requirements-provider.lock.txt'" in script
    assert "$providerTestLockPath = Join-Path $workRoot 'requirements-provider-test.lock.txt'" in script
    assert "Copy-Item -LiteralPath $providerLockSource -Destination $providerLockPath -ErrorAction Stop" in script
    assert "Copy-Item -LiteralPath $providerTestLockSource -Destination $providerTestLockPath -ErrorAction Stop" in script
    assert "Get-CanonicalTextSha256" in script
    assert expected_locks["requirements-provider.lock.txt"] in script
    assert expected_locks["requirements-provider-test.lock.txt"] in script
    assert "PROVIDER_DEPENDENCY_LOCK_SHA256_MISMATCH" in script
    assert "PROVIDER_TEST_DEPENDENCY_LOCK_SHA256_MISMATCH" in script
    assert "HASH_LOCKED_PROVIDER_REQUIREMENTS_MISSING" in script
    assert "HASH_LOCKED_PROVIDER_TEST_REQUIREMENTS_MISSING" in script
    assert "HASH_LOCKED_PROVIDER_REQUIREMENTS_INVALID" in script
    assert script.index("$providerLockCanonicalSha256 = Get-CanonicalTextSha256") < script.index("& $pythonExe -m venv $venvRoot")
    assert script.index("Copy-Item -LiteralPath $providerLockSource") < script.index("& $pythonExe -m venv $venvRoot")
    assert "--require-hashes" in script
    assert "--only-binary=:all:" in script
    assert "dependency_lock_sha256 = $providerLockCanonicalSha256" in script
    assert "test_dependency_lock_sha256 = $providerTestLockCanonicalSha256" in script
    assert "& $venvPython -m pip install" in script
    assert "& $providerTestPython -m pip install" in script
    assert "Remove-Item -LiteralPath $providerTestVenvRoot -Recurse -Force" in script

    # pip bundled with the hash-pinned Python installer is kept; no floating
    # pip upgrade or range-based project requirements are used by the Provider.
    assert "--upgrade pip" not in script
    assert "-r (Join-Path $sourceRoot 'requirements.txt')" not in script
    assert "-r $providerLockPath" in script
    assert "PROJECT_HASH_LOCKED_DEPENDENCY_INSTALL_FAILED" in script
