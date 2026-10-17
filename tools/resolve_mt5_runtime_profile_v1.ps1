[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TerminalPath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Fa-f0-9]{32}$')]
    [string]$DataDirectoryName
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $TerminalPath -PathType Leaf)) {
    throw 'G13_MT5_TERMINAL_EXECUTABLE_NOT_FOUND'
}
$commonResolver = Join-Path $PSScriptRoot 'resolve_mt5_common_files_v1.ps1'
if (-not (Test-Path -LiteralPath $commonResolver -PathType Leaf)) {
    throw 'G13_MT5_COMMON_FILES_RESOLVER_MISSING'
}

# Preserve the stricter process-backed resolver whenever any MT5 terminal is
# running. In particular, do not guess between multiple installations/profiles.
$terminalProcesses = @(
    Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" -ErrorAction SilentlyContinue
)
if ($terminalProcesses.Count -gt 0) {
    $resolved = @(& $commonResolver -TerminalPath $TerminalPath)
    foreach ($line in $resolved) {
        Write-Output ([string]$line)
    }
    return
}

# MT5 may legitimately be closed between parity and this read-only safety
# probe. In that case, resolve only the one Windows profile that already owns
# the exact configured MT5 data-directory hash; never fall back to runner
# APPDATA, a guessed username, or Session 0.
$matchingProfiles = @()
foreach ($mt5Profile in @(Get-CimInstance Win32_UserProfile -ErrorAction SilentlyContinue)) {
    if ([string]::IsNullOrWhiteSpace([string]$mt5Profile.SID) -or
        [string]::IsNullOrWhiteSpace([string]$mt5Profile.LocalPath)) {
        continue
    }

    $appData = Join-Path ([string]$mt5Profile.LocalPath) 'AppData\Roaming'
    $dataRoot = Join-Path $appData ("MetaQuotes\Terminal\$DataDirectoryName")
    $commonFiles = Join-Path $appData 'MetaQuotes\Terminal\Common\Files'
    $scriptsRoot = Join-Path $dataRoot 'MQL5\Scripts'
    if ((Test-Path -LiteralPath $dataRoot -PathType Container) -and
        (Test-Path -LiteralPath $commonFiles -PathType Container) -and
        (Test-Path -LiteralPath $scriptsRoot -PathType Container)) {
        $matchingProfiles += [PSCustomObject]@{
            Sid         = [string]$mt5Profile.SID
            AppData     = [System.IO.Path]::GetFullPath($appData)
            DataRoot    = [System.IO.Path]::GetFullPath($dataRoot)
            CommonFiles = [System.IO.Path]::GetFullPath($commonFiles)
        }
    }
}
if ($matchingProfiles.Count -ne 1) {
    throw 'G13_MT5_CLOSED_TERMINAL_PROFILE_UNRESOLVED'
}
$mt5Profile = $matchingProfiles[0]

$explorerPath = [System.IO.Path]::GetFullPath((Join-Path $env:WINDIR 'explorer.exe'))
$matchingShells = @()
foreach ($shell in @(Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" -ErrorAction SilentlyContinue)) {
    if ([int]$shell.SessionId -le 0 -or
        [string]::IsNullOrWhiteSpace([string]$shell.ExecutablePath)) {
        continue
    }
    try {
        $shellPath = [System.IO.Path]::GetFullPath([string]$shell.ExecutablePath)
    } catch {
        continue
    }
    if (-not [System.String]::Equals(
        $shellPath, $explorerPath, [System.StringComparison]::OrdinalIgnoreCase
    )) {
        continue
    }

    $sidResult = Invoke-CimMethod -InputObject $shell -MethodName GetOwnerSid -ErrorAction SilentlyContinue
    $ownerResult = Invoke-CimMethod -InputObject $shell -MethodName GetOwner -ErrorAction SilentlyContinue
    if ($null -eq $sidResult -or $sidResult.ReturnValue -ne 0 -or
        [string]::IsNullOrWhiteSpace([string]$sidResult.Sid) -or
        -not [System.String]::Equals(
            [string]$sidResult.Sid, [string]$mt5Profile.Sid,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -or
        $null -eq $ownerResult -or $ownerResult.ReturnValue -ne 0 -or
        [string]::IsNullOrWhiteSpace([string]$ownerResult.User) -or
        $ownerResult.User -in @('SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE')) {
        continue
    }

    $matchingShells += [PSCustomObject]@{
        Process = $shell
        Owner   = $ownerResult
    }
}

$matchingSessions = @(
    $matchingShells |
        ForEach-Object { [int]$_.Process.SessionId } |
        Sort-Object -Unique
)
if ($matchingSessions.Count -ne 1) {
    throw 'G13_INTERACTIVE_MT5_SESSION_REQUIRED'
}
$selectedShell = $matchingShells |
    Where-Object { [int]$_.Process.SessionId -eq [int]$matchingSessions[0] } |
    Sort-Object { [DateTime]$_.Process.CreationDate } -Descending |
    Select-Object -First 1
if ($null -eq $selectedShell) {
    throw 'G13_INTERACTIVE_MT5_OWNER_UNRESOLVED'
}
$account = "$($selectedShell.Owner.Domain)\$($selectedShell.Owner.User)"
if ([string]::IsNullOrWhiteSpace($account)) {
    throw 'G13_INTERACTIVE_MT5_OWNER_UNRESOLVED'
}

Write-Output "APPDATA=$($mt5Profile.AppData)"
Write-Output "FOREXAI_MT5_COMMON_FILES=$($mt5Profile.CommonFiles)"
Write-Output 'G13_MT5_PROFILE_RESOLVED=true'
Write-Output "G13_MT5_TERMINAL_OWNER=$account"
Write-Output 'G13_MT5_TERMINAL_PIDS=DESKTOP_SHELL_PROFILE_FALLBACK'
Write-Output "G13_MT5_COMMON_FILES=$($mt5Profile.CommonFiles)"
Write-Output 'G13_MT5_SESSION_RESOLUTION_SOURCE=desktop_shell_profile'
