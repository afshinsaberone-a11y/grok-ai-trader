[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$TerminalRoot,
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [Parameter(Mandatory = $true)][ValidatePattern('^\d+$')][string]$RunId,
    [ValidateRange(10, 600)][int]$StartupTimeoutSeconds = 180,
    [ValidateRange(30, 1200)][int]$CompletionTimeoutSeconds = 600
)

$ErrorActionPreference = 'Stop'
$portableRoot = [System.IO.Path]::GetFullPath($TerminalRoot)
if ((Split-Path -Leaf $portableRoot) -notmatch '^g13-mt5-parity-portable-\d+$') {
    throw 'G13_PORTABLE_ROOT_NAME_REJECTED'
}
$terminal = Join-Path $portableRoot 'terminal64.exe'
if (!(Test-Path -LiteralPath $terminal -PathType Leaf)) {
    throw 'G13_PORTABLE_TERMINAL_MISSING'
}
$config = [System.IO.Path]::GetFullPath($ConfigPath)
$configPrefix = $portableRoot.TrimEnd('\') + '\'
if (!$config.StartsWith($configPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'G13_PORTABLE_CONFIG_OUTSIDE_RUNTIME_ROOT'
}
if (!(Test-Path -LiteralPath $config -PathType Leaf)) {
    throw 'G13_PORTABLE_CONFIG_MISSING'
}

$common = Join-Path $env:APPDATA 'MetaQuotes\Terminal\Common\Files'
New-Item -ItemType Directory -Path $common -Force | Out-Null
$started = Join-Path $common "g13_mql5_parity.started_$($RunId).txt"
$done = Join-Path $common "g13_mql5_parity.done_$($RunId).txt"
$status = Join-Path $common "g13_mt5_launcher_$($RunId).status.txt"

function Write-State([string]$State, [string]$Detail = '') {
    $lines = @("state,$State")
    if ($Detail) {
        $safeDetail = $Detail -replace '[\r\n,]', ' '
        $lines += "detail,$safeDetail"
    }
    $temp = "$status.tmp"
    $lines | Set-Content -LiteralPath $temp -Encoding ascii
    Move-Item -LiteralPath $temp -Destination $status -Force
}

function Stop-OnlyPortableTerminal {
    $rootExe = [System.IO.Path]::GetFullPath($terminal)
    $found = @(Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath).Equals(
                $rootExe, [System.StringComparison]::OrdinalIgnoreCase
            )
        })
    foreach ($item in $found) {
        Stop-Process -Id ([int]$item.ProcessId) -Force -ErrorAction SilentlyContinue
    }
}

$process = $null
try {
    Remove-Item -LiteralPath $started,$done,$status -Force -ErrorAction SilentlyContinue
    Write-State 'launching'
    $configArg = '/config:"' + $config + '"'
    $process = Start-Process -FilePath $terminal -WorkingDirectory $portableRoot -ArgumentList @('/portable', $configArg, '/skipupdate') -PassThru
    $startupDeadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
    while ((Get-Date) -lt $startupDeadline) {
        if (Test-Path -LiteralPath $started -PathType Leaf) {
            Write-State 'started' "pid=$($process.Id)"
            break
        }
        if ($process.HasExited) {
            throw "G13_MT5_EXITED_BEFORE_SCRIPT_START exit_code=$($process.ExitCode)"
        }
        Start-Sleep -Seconds 2
    }
    if (!(Test-Path -LiteralPath $started -PathType Leaf)) {
        throw "G13_MT5_SCRIPT_START_TIMEOUT seconds=$StartupTimeoutSeconds"
    }

    Write-State 'running' "pid=$($process.Id)"
    $completionDeadline = (Get-Date).AddSeconds($CompletionTimeoutSeconds)
    while ((Get-Date) -lt $completionDeadline) {
        if (Test-Path -LiteralPath $done -PathType Leaf) {
            Write-State 'success' "pid=$($process.Id)"
            $exitDeadline = (Get-Date).AddSeconds(10)
            while ((Get-Date) -lt $exitDeadline -and !$process.HasExited) {
                Start-Sleep -Milliseconds 500
                try { $process.Refresh() } catch {}
            }
            if (!$process.HasExited) { Stop-OnlyPortableTerminal }
            exit 0
        }
        if ($process.HasExited) {
            throw "G13_MT5_EXITED_WITHOUT_COMPLETION_MARKER exit_code=$($process.ExitCode)"
        }
        Start-Sleep -Seconds 2
    }
    throw "G13_MT5_COMPLETION_TIMEOUT seconds=$CompletionTimeoutSeconds"
}
catch {
    try { Write-State 'failed' $_.Exception.Message } catch {}
    Stop-OnlyPortableTerminal
    exit 1
}
