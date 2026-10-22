#Requires -Version 5.1
#Requires -RunAsAdministrator
# First-run layout bootstrap only. Does not provision a cloud VM or activate signing.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Stop-Blocked([string]$Reason) {
    Write-Host "CAPITAL_FIREWALL_WORKSTATION_BOOTSTRAP=BLOCKED reason=$Reason" -ForegroundColor Red
    exit 2
}

$DataRoot = Join-Path $env:ProgramData "ForexAI-CapitalFirewall"
$RuntimeUser = "capital-firewall"
$RuntimeIdentity = "$env:COMPUTERNAME\$RuntimeUser"

try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    if ([int]$os.ProductType -ne 1) {
        Stop-Blocked "WINDOWS_CLIENT_OS_REQUIRED_SERVER_OS_FORBIDDEN"
    }
    # Read the release identity and cumulative-update revision from the local OS registry.
    # Matrix current at 2026-10: 24H2 only for supported Enterprise/Education/LTSC editions;
    # 25H2 and 26H2 accepted when at least the October 2026 security baseline is installed.
    $currentVersion = Get-ItemProperty -LiteralPath "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" -ErrorAction Stop
    $build = [int]$os.BuildNumber
    $ubr = [int]$currentVersion.UBR
    $displayVersion = [string]$currentVersion.DisplayVersion
    $editionId = [string]$currentVersion.EditionID
    $supported24H2Editions = @(
        "Enterprise", "EnterpriseN", "Education", "EducationN",
        "EnterpriseS", "IoTEnterprise", "IoTEnterpriseS"
    )
    $supportedWindowsRelease = $false
    switch ($displayVersion) {
        "24H2" {
            if ($build -eq 26100 -and $ubr -ge 9711 -and $editionId -in $supported24H2Editions) {
                $supportedWindowsRelease = $true
            }
        }
        "25H2" {
            if ($build -eq 26200 -and $ubr -ge 9711) {
                $supportedWindowsRelease = $true
            }
        }
        "26H2" {
            if ($build -eq 26300 -and $ubr -ge 9711) {
                $supportedWindowsRelease = $true
            }
        }
    }
    if (-not $supportedWindowsRelease) {
        Stop-Blocked "WINDOWS_RELEASE_OR_PATCH_BASELINE_UNSUPPORTED_FOR_SIGNER_HOST"
    }
    try {
        $tpm = Get-Tpm -ErrorAction Stop
        if (-not $tpm.TpmPresent -or -not $tpm.TpmReady) {
            Stop-Blocked "TPM_NOT_PRESENT_OR_READY"
        }
    } catch {
        Stop-Blocked "TPM_STATUS_UNAVAILABLE"
    }
    try {
        $secureBootEnabled = Confirm-SecureBootUEFI -ErrorAction Stop
        if (-not $secureBootEnabled) {
            Stop-Blocked "SECURE_BOOT_DISABLED"
        }
    } catch {
        Stop-Blocked "SECURE_BOOT_STATUS_UNAVAILABLE"
    }
    try {
        $systemVolume = Get-BitLockerVolume -MountPoint $env:SystemDrive -ErrorAction Stop
        if ($systemVolume.ProtectionStatus -ne "On" -or $systemVolume.VolumeStatus -ne "FullyEncrypted") {
            Stop-Blocked "SYSTEM_VOLUME_NOT_FULLY_ENCRYPTED_AND_PROTECTED"
        }
    } catch {
        Stop-Blocked "SYSTEM_VOLUME_ENCRYPTION_STATUS_UNAVAILABLE"
    }
    if ($env:COMPUTERNAME -ieq "WIN-P7MA35DRF6Q") {
        Stop-Blocked "KNOWN_PROVIDER_HOST_FORBIDDEN"
    }
    if (Get-Service -Name "actions.runner.*" -ErrorAction SilentlyContinue) {
        Stop-Blocked "SELF_HOSTED_ACTIONS_RUNNER_HOST_FORBIDDEN"
    }
    if (Get-Process -Name "terminal64" -ErrorAction SilentlyContinue) {
        Stop-Blocked "ACTIVE_MT5_TERMINAL_HOST_FORBIDDEN"
    }
    if (-not (Get-Command Get-LocalUser -ErrorAction SilentlyContinue)) {
        Stop-Blocked "LOCAL_ACCOUNT_MANAGEMENT_CMDLETS_UNAVAILABLE"
    }
    if (Get-LocalUser -Name $RuntimeUser -ErrorAction SilentlyContinue) {
        Stop-Blocked "RUNTIME_IDENTITY_ALREADY_EXISTS_MANUAL_REVIEW_REQUIRED"
    }
    if (Test-Path -LiteralPath $DataRoot) {
        Stop-Blocked "DATA_ROOT_ALREADY_EXISTS_MANUAL_REVIEW_REQUIRED"
    }
    if (-not [Environment]::UserInteractive) {
        Stop-Blocked "INTERACTIVE_CONFIRMATION_REQUIRED"
    }

    $targetHost = [Environment]::MachineName
    Write-Host "Target workstation: $targetHost"
    Write-Host "This creates a local non-admin runtime user and empty protected directories only."
    Write-Host "It does not create keys, registry/database, source packet, Grant, service, or trading permission."
    $typedHost = Read-Host "Type the exact workstation hostname to confirm"
    if ($typedHost -cne $targetHost) {
        Stop-Blocked "HOSTNAME_CONFIRMATION_MISMATCH"
    }
    $password = Read-Host "Create a strong password for the local non-admin capital-firewall account" -AsSecureString
    if ($null -eq $password -or $password.Length -lt 16) {
        Stop-Blocked "RUNTIME_PASSWORD_MUST_BE_AT_LEAST_16_CHARACTERS"
    }

    # From this point, failures require manual inspection; never blindly rerun.
    $null = New-LocalUser -Name $RuntimeUser -Password $password -Description "ForexAI one-shot Capital Firewall signer runtime; not an administrator"
    $null = New-Item -ItemType Directory -Path $DataRoot
    $aclArgs = @(
        $DataRoot,
        "/inheritance:r",
        "/grant:r",
        "*S-1-5-18:(OI)(CI)F",
        "*S-1-5-32-544:(OI)(CI)F",
        ($RuntimeIdentity + ":(OI)(CI)M")
    )
    & "$env:WINDIR\System32\icacls.exe" @aclArgs | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Stop-Blocked "DATA_ROOT_ACL_CONFIGURATION_FAILED_MANUAL_REVIEW_REQUIRED"
    }

    foreach ($child in @("keys", "in", "out", "state")) {
        $null = New-Item -ItemType Directory -Path (Join-Path $DataRoot $child)
    }
    $children = @(Get-ChildItem -LiteralPath $DataRoot -Force | Select-Object -ExpandProperty Name | Sort-Object)
    $expected = @("in", "keys", "out", "state")
    if (($children -join "|") -cne ($expected -join "|")) {
        Stop-Blocked "UNEXPECTED_DATA_ROOT_CONTENT_MANUAL_REVIEW_REQUIRED"
    }
    foreach ($child in @("", "keys", "in", "out", "state")) {
        $path = if ($child) { Join-Path $DataRoot $child } else { $DataRoot }
        if (-not (Test-Path -LiteralPath $path -PathType Container)) {
            Stop-Blocked "PROTECTED_DIRECTORY_MISSING"
        }
        $entries = @(Get-ChildItem -LiteralPath $path -Force -ErrorAction Stop)
        if ($child -and $entries.Count -ne 0) {
            Stop-Blocked "UNEXPECTED_PREEXISTING_CONTENT"
        }
    }

    Write-Output "CAPITAL_FIREWALL_WORKSTATION_BOOTSTRAP=PASS_EMPTY_LAYOUT_ONLY"
    Write-Output "HOSTNAME=$targetHost"
    Write-Output "RUNTIME_IDENTITY=$RuntimeIdentity"
    Write-Output "DATA_ROOT=$DataRoot"
    Write-Output "KEYS_CREATED=0"
    Write-Output "REGISTRY_CREATED=0"
    Write-Output "SOURCE_PACKET_CREATED=0"
    Write-Output "GRANT_ISSUED=0"
    Write-Output "SERVICE_INSTALLED=0"
    Write-Output "ORDERS_SUBMITTED=0"
    Write-Output "DEMO_AUTHORIZED=0"
    Write-Output "LIVE_ENABLED=0"
}
catch {
    Write-Host "CAPITAL_FIREWALL_WORKSTATION_BOOTSTRAP=BLOCKED reason=UNEXPECTED_FAILURE_MANUAL_REVIEW_REQUIRED" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 2
}
