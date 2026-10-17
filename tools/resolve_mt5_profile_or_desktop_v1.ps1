[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TerminalPath,

    [Parameter(Mandatory = $true)]
    [string]$DataRoot,

    [switch]$SetDenyKillSwitch
)

$ErrorActionPreference = 'Stop'

# Prefer the established resolver whenever MT5 is running. Its exact executable,
# process owner, profile, and Common Files checks remain authoritative.
if (-not (Test-Path -LiteralPath $TerminalPath -PathType Leaf)) {
    throw 'G13_MT5_TERMINAL_EXECUTABLE_NOT_FOUND'
}
$baseResolver = Join-Path $PSScriptRoot 'resolve_mt5_common_files_v1.ps1'
if (-not (Test-Path -LiteralPath $baseResolver -PathType Leaf)) {
    throw 'G13_MT5_COMMON_FILES_RESOLVER_MISSING'
}

try {
    $resolved = @(& $baseResolver -TerminalPath $TerminalPath -SetDenyKillSwitch:$SetDenyKillSwitch)
    foreach ($line in $resolved) {
        Write-Output ([string]$line)
    }
    return
} catch {
    $resolutionError = [string]$_.Exception.Message
    # Only this precise condition permits the closed-terminal fallback. A
    # path mismatch, access-denied condition, ambiguous owner, or write failure
    # remains a hard failure.
    if ($resolutionError -notmatch '^G13_MT5_TERMINAL_PROCESS_NOT_FOUND:') {
        throw 'G13_MT5_PROFILE_RESOLUTION_FAILED'
    }
}

$desktopResolver = Join-Path $PSScriptRoot 'resolve_mt5_interactive_profile_v1.ps1'
if (-not (Test-Path -LiteralPath $desktopResolver -PathType Leaf)) {
    throw 'G13_MT5_INTERACTIVE_PROFILE_RESOLVER_MISSING'
}
if (-not (Test-Path -LiteralPath $DataRoot -PathType Container)) {
    throw 'G13_MT5_CONFIGURED_DATA_ROOT_MISSING'
}

$desktopOutput = @()
try {
    $desktopOutput = @(& $desktopResolver -DataRoot $DataRoot)
} catch {
    $failureText = [string]$_.Exception.Message
    if ($failureText -match '^G13_MT5_CONFIGURED_DATA_ROOT_MISSING$') {
        throw 'G13_MT5_CONFIGURED_DATA_ROOT_MISSING'
    }
    if ($failureText -match '^G13_MT5_CONFIGURED_PROFILE_ROOT_MISSING$') {
        throw 'G13_MT5_CONFIGURED_PROFILE_ROOT_MISSING'
    }
    if ($failureText -match '^G13_MT5_CONFIGURED_PROFILE_UNRESOLVED$') {
        throw 'G13_MT5_CONFIGURED_PROFILE_UNRESOLVED'
    }
    if ($failureText -match '^G13_MT5_INTERACTIVE_SESSION_REQUIRED') {
        throw 'G13_MT5_INTERACTIVE_SESSION_REQUIRED'
    }
    if ($failureText -match '^G13_MT5_COMMON_FILES_DIRECTORY_NOT_FOUND$') {
        throw 'G13_MT5_COMMON_FILES_DIRECTORY_NOT_FOUND'
    }
    throw 'G13_MT5_INTERACTIVE_PROFILE_RESOLUTION_FAILED'
}

$commonLine = $desktopOutput |
    Where-Object { ([string]$_) -match '^G13_MT5_COMMON_FILES=' } |
    Select-Object -Last 1
$ownerLine = $desktopOutput |
    Where-Object { ([string]$_) -match '^G13_MT5_TERMINAL_OWNER=' } |
    Select-Object -Last 1
$sessionLine = $desktopOutput |
    Where-Object { ([string]$_) -match '^G13_MT5_INTERACTIVE_SESSION=' } |
    Select-Object -Last 1
if (-not $commonLine -or -not $ownerLine -or -not $sessionLine) {
    throw 'G13_MT5_INTERACTIVE_PROFILE_OUTPUT_INCOMPLETE'
}

$commonFiles = ([string]$commonLine) -replace '^G13_MT5_COMMON_FILES=', ''
$owner = ([string]$ownerLine) -replace '^G13_MT5_TERMINAL_OWNER=', ''
$sessionText = ([string]$sessionLine) -replace '^G13_MT5_INTERACTIVE_SESSION=', ''
$sessionId = 0
if (-not [int]::TryParse($sessionText, [ref]$sessionId) -or $sessionId -le 0) {
    throw 'G13_MT5_INTERACTIVE_SESSION_REQUIRED'
}
if ([string]::IsNullOrWhiteSpace($owner)) {
    throw 'G13_MT5_INTERACTIVE_OWNER_UNRESOLVED'
}

try {
    $canonicalDataRoot = [System.IO.Path]::GetFullPath($DataRoot)
    $appData = [System.IO.Path]::GetFullPath((Join-Path $canonicalDataRoot '..\..\..'))
    $expectedCommonFiles = [System.IO.Path]::GetFullPath(
        (Join-Path $appData 'MetaQuotes\Terminal\Common\Files')
    )
    $canonicalCommonFiles = [System.IO.Path]::GetFullPath($commonFiles)
} catch {
    throw 'G13_MT5_COMMON_FILES_PATH_INVALID'
}
if (-not [System.String]::Equals(
    $canonicalCommonFiles,
    $expectedCommonFiles,
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    throw 'G13_MT5_COMMON_FILES_PATH_MISMATCH'
}
if (-not (Test-Path -LiteralPath $canonicalCommonFiles -PathType Container)) {
    throw 'G13_MT5_COMMON_FILES_DIRECTORY_NOT_FOUND'
}

# For preflight callers, preserve the hard DENY invariant even when MT5 has
# been closed. This creates no authorization and never changes the switch to ALLOW.
if ($SetDenyKillSwitch) {
    $killSwitch = Join-Path $canonicalCommonFiles 'g13_demo_kill_switch.txt'
    try {
        [System.IO.File]::WriteAllText(
            $killSwitch,
            'DENY',
            [System.Text.Encoding]::ASCII
        )
    } catch {
        throw 'G13_KILL_SWITCH_INITIAL_DENY_FAILED'
    }
    if (([System.IO.File]::ReadAllText($killSwitch)).Trim() -ne 'DENY') {
        throw 'G13_KILL_SWITCH_INITIAL_DENY_VERIFICATION_FAILED'
    }

    $probe = Join-Path $canonicalCommonFiles ('.forexai-profile-write-probe-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [System.IO.File]::WriteAllText($probe, 'ForexAI Common Files permission probe', [System.Text.Encoding]::ASCII)
    } catch {
        throw 'G13_MT5_COMMON_FILES_WRITE_ACCESS_DENIED'
    } finally {
        Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
    }
    Write-Output 'G13_KILL_SWITCH_INITIAL_DENY=true'
}

if (-not [string]::IsNullOrWhiteSpace($env:GITHUB_ENV)) {
    "APPDATA=$appData" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
    "FOREXAI_MT5_COMMON_FILES=$canonicalCommonFiles" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
}

# Keep the legacy output contract so downstream workflow steps do not guess
# paths or depend on the GitHub runner service account's APPDATA.
Write-Output "APPDATA=$appData"
Write-Output "FOREXAI_MT5_COMMON_FILES=$canonicalCommonFiles"
Write-Output 'G13_MT5_PROFILE_RESOLVED=true'
Write-Output "G13_MT5_TERMINAL_OWNER=$owner"
Write-Output 'G13_MT5_TERMINAL_PIDS=DESKTOP_SHELL_PROFILE_FALLBACK'
Write-Output "G13_MT5_COMMON_FILES=$canonicalCommonFiles"
Write-Output 'G13_MT5_SESSION_RESOLUTION_SOURCE=desktop_shell_profile'
