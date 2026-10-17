[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DataRoot
)

$ErrorActionPreference = 'Stop'

# This resolver is a narrowly scoped fallback for a logged-on desktop whose
# MT5 terminal process is closed after the previous isolated parity run. It
# never starts a terminal, changes a kill switch, or grants trading authority.
if (-not (Test-Path -LiteralPath $DataRoot -PathType Container)) {
    throw 'G13_MT5_CONFIGURED_DATA_ROOT_MISSING'
}
$canonicalDataRoot = [System.IO.Path]::GetFullPath($DataRoot).TrimEnd('\')
$expectedProfileRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $canonicalDataRoot '..\..\..\..\..')
).TrimEnd('\')
if (-not (Test-Path -LiteralPath $expectedProfileRoot -PathType Container)) {
    throw 'G13_MT5_CONFIGURED_PROFILE_ROOT_MISSING'
}

$profiles = @(
    Get-CimInstance Win32_UserProfile -ErrorAction SilentlyContinue |
        Where-Object {
            $_.LocalPath -and $_.SID -and
            [System.String]::Equals(
                [System.IO.Path]::GetFullPath([string]$_.LocalPath).TrimEnd('\'),
                $expectedProfileRoot,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        }
)
if ($profiles.Count -ne 1) {
    throw 'G13_MT5_CONFIGURED_PROFILE_UNRESOLVED'
}
$profileSid = [string]$profiles[0].SID

# Require one unique, already logged-on Explorer desktop for this exact
# Windows profile. No Session 0 or unrelated-user fallback is permitted.
$explorerPath = [System.IO.Path]::GetFullPath((Join-Path $env:WINDIR 'explorer.exe'))
$shells = @(
    Get-CimInstance Win32_Process -Filter "Name='explorer.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            [int]$_.SessionId -gt 0 -and $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath([string]$_.ExecutablePath).Equals(
                $explorerPath,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        }
)
$matches = @()
foreach ($shell in $shells) {
    $owner = Invoke-CimMethod -InputObject $shell -MethodName GetOwner -ErrorAction SilentlyContinue
    if ($null -eq $owner -or $owner.ReturnValue -ne 0 -or
        [string]::IsNullOrWhiteSpace([string]$owner.User) -or
        $owner.User -in @('SYSTEM','LOCAL SERVICE','NETWORK SERVICE')) {
        continue
    }

    $account = "$($owner.Domain)\$($owner.User)"
    try {
        $sid = (New-Object System.Security.Principal.NTAccount($account)).Translate(
            [System.Security.Principal.SecurityIdentifier]
        )
    } catch {
        continue
    }

    if ([System.String]::Equals(
        [string]$sid.Value,
        $profileSid,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        $matches += [PSCustomObject]@{
            Process = $shell
            Owner = $owner
            Account = $account
        }
    }
}

$sessions = @($matches | ForEach-Object { [int]$_.Process.SessionId } | Sort-Object -Unique)
if ($sessions.Count -ne 1) {
    throw 'G13_MT5_INTERACTIVE_SESSION_REQUIRED: sign in to the configured MT5 desktop profile; refusing Session 0 launch'
}
$selected = $matches |
    Where-Object { [int]$_.Process.SessionId -eq [int]$sessions[0] } |
    Sort-Object { [DateTime]$_.Process.CreationDate } -Descending |
    Select-Object -First 1
if ($null -eq $selected) {
    throw 'G13_MT5_INTERACTIVE_SESSION_REQUIRED'
}

$appData = Join-Path $expectedProfileRoot 'AppData\Roaming'
$commonFiles = Join-Path $appData 'MetaQuotes\Terminal\Common\Files'
if (-not (Test-Path -LiteralPath $commonFiles -PathType Container)) {
    throw 'G13_MT5_COMMON_FILES_DIRECTORY_NOT_FOUND'
}

Write-Output "G13_MT5_COMMON_FILES=$commonFiles"
Write-Output "G13_MT5_TERMINAL_OWNER=$($selected.Account)"
Write-Output "G13_MT5_PROFILE_SOURCE=matching_interactive_desktop_shell"
Write-Output "G13_MT5_INTERACTIVE_SESSION=$($sessions[0])"
