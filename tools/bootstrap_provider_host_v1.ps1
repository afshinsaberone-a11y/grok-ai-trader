[CmdletBinding()]
param(
    [string]$ProviderRoot = 'C:\ProgramData\ForexAI-Provider',
    [string]$ExpectedCommit = '41883f30d32747d07d7b7772f8ee7c656a95e4a1'
)

# One-time clean-host bootstrap for the external Provider.
# It installs verified tools, checks out a reviewed source SHA, builds a venv,
# and runs focused software-contract tests. It does NOT install a service,
# configure authority keys/secrets, initialize any production registry,
# create source packets/ledger/envelope/auth records, or authorize trading.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$repositoryUrl = 'https://github.com/afshinsaberone-a11y/grok-ai-trader.git'
$pythonVersion = '3.13.17'
$pythonInstallRoot = 'C:\Program Files\ForexAI-Pinned-Python-3.13.17'
$pythonExe = Join-Path $pythonInstallRoot 'python.exe'
$pythonInstallerUrl = 'https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.exe'
$pythonInstallerSha256 = '5da012101ba2e17113a9a1cd901e9ce1441086f2b7ecb5de06ec94163899a190'
$gitInstallRoot = 'C:\Program Files\ForexAI-Pinned-Git-2.56.0.3'
$gitExe = Join-Path $gitInstallRoot 'cmd\git.exe'
$gitInstallerUrl = 'https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.3/Git-2.56.0.3-64-bit.exe'
$gitInstallerSha256 = 'dc6d3db061999136e139f31376c5582a9ed6f36a4ea12f15e54ad7fa2bfc0bf2'

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'BOOTSTRAP_REQUIRES_ELEVATED_ADMINISTRATOR'
    }
}

function New-ProtectedWorkRoot {
    # Elevated installers must not be downloaded under a potentially user-writable TEMP.
    $programData = [Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)
    if ([string]::IsNullOrWhiteSpace($programData) -or -not (Test-Path -LiteralPath $programData -PathType Container)) {
        throw 'BOOTSTRAP_PROTECTED_WORK_ROOT_PARENT_UNAVAILABLE'
    }

    for ($attempt = 0; $attempt -lt 3; $attempt++) {
        $candidate = Join-Path $programData ('ForexAI-Provider-Bootstrap-' + [Guid]::NewGuid().ToString('N'))
        try {
            New-Item -ItemType Directory -Path $candidate -ErrorAction Stop | Out-Null
        }
        catch {
            if (Test-Path -LiteralPath $candidate) { continue }
            throw 'BOOTSTRAP_PROTECTED_WORK_ROOT_CREATE_FAILED'
        }

        $item = Get-Item -LiteralPath $candidate -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'BOOTSTRAP_WORK_ROOT_REPARSE_POINT'
        }
        $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
        & icacls.exe $candidate /inheritance:r /grant:r "*$($sid):(OI)(CI)F" /grant '*S-1-5-18:(OI)(CI)F' | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'BOOTSTRAP_WORK_ROOT_ACL_SETUP_FAILED' }
        foreach ($extraSid in @('*S-1-5-32-544', '*S-1-3-4')) {
            & icacls.exe $candidate /remove $extraSid | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'BOOTSTRAP_WORK_ROOT_ACL_SETUP_FAILED' }
        }

        $acl = Get-Acl -LiteralPath $candidate
        if (-not $acl.AreAccessRulesProtected) { throw 'BOOTSTRAP_WORK_ROOT_INHERITANCE_ENABLED' }
        $rules = @($acl.Access)
        if ($rules.Count -ne 2) { throw 'BOOTSTRAP_WORK_ROOT_UNEXPECTED_ACL_COUNT' }
        $allowed = @($sid, 'S-1-5-18')
        foreach ($rule in $rules) {
            $ruleSid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
            if ($ruleSid -notin $allowed -or
                $rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or
                $rule.IsInherited -or
                $rule.FileSystemRights -ne [Security.AccessControl.FileSystemRights]::FullControl) {
                throw 'BOOTSTRAP_WORK_ROOT_UNEXPECTED_ACL'
            }
        }
        $item = Get-Item -LiteralPath $candidate -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'BOOTSTRAP_WORK_ROOT_REPARSE_POINT'
        }
        return $candidate
    }
    throw 'BOOTSTRAP_WORK_ROOT_COLLISION'
}

function Get-VerifiedInstaller {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$Destination,
        [Parameter(Mandatory = $true)][string]$ExpectedSha256,
        [string]$RequiredSignerSubstring
    )

    # WorkRoot is newly-created and ACL-verified; never remove/adopt an unexpected path.
    if (Test-Path -LiteralPath $Destination) {
        throw 'INSTALLER_DESTINATION_ALREADY_EXISTS'
    }

    Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $Destination

    $actualHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $ExpectedSha256.ToLowerInvariant()) {
        throw 'INSTALLER_SHA256_MISMATCH'
    }

    $signature = Get-AuthenticodeSignature -LiteralPath $Destination
    if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
        throw 'INSTALLER_AUTHENTICODE_SIGNATURE_INVALID'
    }
    if ($RequiredSignerSubstring -and $signature.SignerCertificate.Subject -notmatch [regex]::Escape($RequiredSignerSubstring)) {
        throw 'INSTALLER_SIGNER_SUBJECT_MISMATCH'
    }

    return [PSCustomObject]@{
        path = $Destination
        sha256 = $actualHash
        signature_status = [string]$signature.Status
        signer_subject = [string]$signature.SignerCertificate.Subject
    }
}

try {
    Assert-Administrator

    if (-not [Environment]::Is64BitOperatingSystem) {
        throw 'BOOTSTRAP_REQUIRES_64_BIT_WINDOWS'
    }

    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    if ([int]$os.BuildNumber -lt 20348 -or [int]$os.ProductType -eq 1) {
        throw 'BOOTSTRAP_EXPECTS_WINDOWS_SERVER_2022_OR_NEWER'
    }

    if ($ExpectedCommit -notmatch '^[0-9a-f]{40}$') {
        throw 'EXPECTED_COMMIT_MUST_BE_FULL_SHA'
    }

    if (Test-Path -LiteralPath $gitInstallRoot) {
        throw 'GIT_INSTALL_ROOT_ALREADY_EXISTS_INSPECT_BEFORE_RESUME'
    }
    if (Test-Path -LiteralPath $pythonInstallRoot) {
        throw 'PYTHON_INSTALL_ROOT_ALREADY_EXISTS_INSPECT_BEFORE_RESUME'
    }

    # Never overlay a previous install or silently adopt existing state.
    if (Test-Path -LiteralPath $ProviderRoot) {
        throw 'PROVIDER_ROOT_ALREADY_EXISTS_INSPECT_BEFORE_RESUME'
    }

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    $workRoot = New-ProtectedWorkRoot
    $installerRoot = Join-Path $workRoot 'installers'
    New-Item -ItemType Directory -Path $installerRoot -ErrorAction Stop | Out-Null

    $gitInstaller = Join-Path $installerRoot 'Git-2.56.0.3-64-bit.exe'
    $pythonInstaller = Join-Path $installerRoot 'python-3.13.17-amd64.exe'
    $gitInstallerReport = $null
    $pythonInstallerReport = $null

    # Always install the pinned tool into the dedicated, previously absent path.
    # Never adopt an existing executable based only on its reported version.
    $gitInstallerReport = Get-VerifiedInstaller -Uri $gitInstallerUrl -Destination $gitInstaller -ExpectedSha256 $gitInstallerSha256
    if (Test-Path -LiteralPath $gitInstallRoot) {
        throw 'GIT_INSTALL_ROOT_APPEARED_DURING_BOOTSTRAP'
    }
    $gitArgs = '/VERYSILENT /NORESTART /SP- /SUPPRESSMSGBOXES /DIR="' + $gitInstallRoot + '"'
    $gitProcess = Start-Process -FilePath $gitInstaller -ArgumentList $gitArgs -Wait -PassThru
    if ($gitProcess.ExitCode -ne 0) {
        throw 'GIT_FOR_WINDOWS_INSTALL_FAILED'
    }

    if (-not (Test-Path -LiteralPath $gitExe -PathType Leaf)) {
        throw 'PINNED_GIT_EXECUTABLE_NOT_FOUND_AFTER_INSTALL'
    }

    $gitVersion = (& $gitExe --version | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $gitVersion -notmatch '^git version 2\.56\.0\.windows\.3(?:\s|$)') {
        throw 'GIT_VERSION_NOT_THE_REVIEWED_PIN'
    }

    $pythonInstallerReport = Get-VerifiedInstaller -Uri $pythonInstallerUrl -Destination $pythonInstaller -ExpectedSha256 $pythonInstallerSha256 -RequiredSignerSubstring 'Python Software Foundation'
    if (Test-Path -LiteralPath $pythonInstallRoot) {
        throw 'PYTHON_INSTALL_ROOT_APPEARED_DURING_BOOTSTRAP'
    }
    $pythonArgs = '/quiet InstallAllUsers=1 TargetDir="' + $pythonInstallRoot + '" Include_pip=1 Include_test=0 PrependPath=0 AppendPath=0 InstallLauncherAllUsers=1 Shortcuts=0'
    $pythonProcess = Start-Process -FilePath $pythonInstaller -ArgumentList $pythonArgs -Wait -PassThru
    if ($pythonProcess.ExitCode -ne 0) {
        throw 'PYTHON_INSTALL_FAILED'
    }

    if (-not (Test-Path -LiteralPath $pythonExe -PathType Leaf)) {
        throw 'PINNED_PYTHON_EXECUTABLE_NOT_FOUND_AFTER_INSTALL'
    }

    $detectedPython = (& $pythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $detectedPython -ne $pythonVersion) {
        throw 'PYTHON_VERSION_NOT_THE_REVIEWED_PIN'
    }

    # Create the target only after installer verification and tool checks.
    New-Item -ItemType Directory -Path $ProviderRoot | Out-Null
    $sourceRoot = Join-Path $ProviderRoot 'source'
    $venvRoot = Join-Path $ProviderRoot 'venv'

    & $gitExe -c core.longpaths=true clone --quiet --no-checkout $repositoryUrl $sourceRoot
    if ($LASTEXITCODE -ne 0) {
        throw 'GITHUB_SOURCE_CLONE_FAILED'
    }

    & $gitExe -C $sourceRoot checkout --quiet --detach $ExpectedCommit
    if ($LASTEXITCODE -ne 0) {
        throw 'PINNED_SOURCE_CHECKOUT_FAILED'
    }

    $actualCommit = (& $gitExe -C $sourceRoot rev-parse HEAD | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualCommit -ne $ExpectedCommit) {
        throw 'CHECKED_OUT_SOURCE_SHA_MISMATCH'
    }

    $gitStatus = @(& $gitExe -C $sourceRoot status --porcelain=v1)
    if ($LASTEXITCODE -ne 0 -or $gitStatus.Count -gt 0) {
        throw 'SOURCE_CHECKOUT_NOT_CLEAN'
    }

    & $pythonExe -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) {
        throw 'PROVIDER_VENV_CREATION_FAILED'
    }

    $venvPython = Join-Path $venvRoot 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw 'PROVIDER_VENV_PYTHON_NOT_FOUND'
    }

    & $venvPython -m pip install --disable-pip-version-check --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw 'PIP_BOOTSTRAP_FAILED'
    }

    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $sourceRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) {
        throw 'PROJECT_DEPENDENCY_INSTALL_FAILED'
    }

    & $venvPython -c "import cryptography, numpy, pandas, backtesting, pytest; print('PYTHON_DEPENDENCIES=PASS'); print('CRYPTOGRAPHY=' + cryptography.__version__)"
    if ($LASTEXITCODE -ne 0) {
        throw 'PROJECT_DEPENDENCY_IMPORT_FAILED'
    }

    $focusedTests = @(
        'tests/test_control_plane_provider_host_preflight_v1.py',
        'tests/test_control_plane_admission_provider_v1.py',
        'tests/test_control_plane_provider_service_v1.py',
        'tests/test_control_plane_service_v1.py'
    )
    $testPaths = $focusedTests | ForEach-Object { Join-Path $sourceRoot $_ }
    & $venvPython -m pytest -q -p no:cacheprovider $testPaths
    if ($LASTEXITCODE -ne 0) {
        throw 'FOCUSED_PROVIDER_CONTRACT_TESTS_FAILED'
    }

    $report = [ordered]@{
        schema = 'forexai.provider_clean_host_bootstrap.v1'
        status = 'BOOTSTRAP_COMPLETE_AUTHORITY_SETUP_STILL_BLOCKED'
        host = $env:COMPUTERNAME
        os_caption = [string]$os.Caption
        os_build = [string]$os.BuildNumber
        git_version = $gitVersion
        python_version = $detectedPython
        repository_url = $repositoryUrl
        source_commit = $actualCommit
        provider_root = $ProviderRoot
        source_directory_created = $true
        virtual_environment_created = $true
        git_installer = $gitInstallerReport
        python_installer = $pythonInstallerReport
        focused_provider_contract_tests = 'PASS'
        provider_service_installed = $false
        issuance_registry_created = $false
        public_trust_anchors_configured = $false
        private_keys_or_passphrases_migrated = $false
        source_packet_created = $false
        ledger_envelope_or_mql5_auth_record_created = $false
        demo_trading_authorized = $false
        live_trading_allowed = $false
        orders_submitted = $false
        next_gate = 'OWNER_APPROVED_KEY_CUSTODY_SOURCE_AUTHORITIES_AND_REGISTRY_PLAN'
    }

    $reportPath = Join-Path $workRoot 'bootstrap-result.json'
    $report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    $report | ConvertTo-Json -Depth 6
    Write-Output "BOOTSTRAP_REPORT=$reportPath"
    Write-Output 'PROVIDER_SERVICE_NOT_INSTALLED'
    Write-Output 'PRODUCTION_REGISTRY_NOT_CREATED'
    Write-Output 'TRADING_AUTHORIZATION_NOT_GRANTED'
}
catch {
    Write-Error ("PROVIDER_BOOTSTRAP_ABORTED: " + $_.Exception.Message)
    throw
}
