[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$TerminalPath,
    [switch]$SetDenyKillSwitch
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $TerminalPath -PathType Leaf)) {
    throw "G13_MT5_TERMINAL_EXECUTABLE_NOT_FOUND:$TerminalPath"
}
$expectedExe = [System.IO.Path]::GetFullPath($TerminalPath)

$terminalProcesses = @(
    Get-CimInstance Win32_Process -Filter "Name='terminal64.exe'"
)
if ($terminalProcesses.Count -lt 1) {
    throw "G13_MT5_TERMINAL_PROCESS_NOT_FOUND:$expectedExe"
}

# Win32_Process.ExecutablePath requires SeDebugPrivilege. Use the limited
# PROCESS_QUERY_LIMITED_INFORMATION right and QueryFullProcessImageName instead,
# so the runner does not need elevated debug privileges just to identify MT5.
if ($null -eq ('ForexAI_NativeProcessPath' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class ForexAI_NativeProcessPath
{
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint desiredAccess, bool inheritHandle, int processId);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true,
        EntryPoint = "QueryFullProcessImageNameW")]
    private static extern bool QueryFullProcessImageNameW(
        IntPtr process, uint flags, StringBuilder exeName, ref uint size);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);

    public static string TryGetPath(int processId, out int errorCode)
    {
        const uint PROCESS_QUERY_LIMITED_INFORMATION = 0x1000;
        IntPtr handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, false, processId);
        if (handle == IntPtr.Zero)
        {
            errorCode = Marshal.GetLastWin32Error();
            return null;
        }
        try
        {
            StringBuilder path = new StringBuilder(32768);
            uint size = (uint)path.Capacity;
            if (!QueryFullProcessImageNameW(handle, 0, path, ref size))
            {
                errorCode = Marshal.GetLastWin32Error();
                return null;
            }
            errorCode = 0;
            return path.ToString();
        }
        finally
        {
            CloseHandle(handle);
        }
    }
}
'@
}

$matchingProcesses = @()
$unresolvedProcessPathCount = 0
$accessDeniedProcessPathCount = 0
foreach ($process in $terminalProcesses) {
    $processPathErrorCode = 0
    $processPath = [ForexAI_NativeProcessPath]::TryGetPath(
        [int]$process.ProcessId,
        [ref]$processPathErrorCode
    )
    if ([string]::IsNullOrWhiteSpace([string]$processPath)) {
        $unresolvedProcessPathCount++
        if ($processPathErrorCode -eq 5) {
            # Emit only this allowlisted classification later; never log raw
            # Win32 error details, PIDs, or local filesystem paths.
            $accessDeniedProcessPathCount++
        }
        continue
    }

    $isExpectedPath = $false
    try {
        $isExpectedPath = [System.String]::Equals(
            [System.IO.Path]::GetFullPath([string]$processPath),
            $expectedExe,
            [System.StringComparison]::OrdinalIgnoreCase
        )
    } catch {
        $isExpectedPath = $false
    }
    if ($isExpectedPath) {
        $matchingProcesses += $process
    }
}

if ($matchingProcesses.Count -lt 1) {
    if ($accessDeniedProcessPathCount -gt 0) {
        throw 'G13_MT5_TERMINAL_PROCESS_ACCESS_DENIED'
    }
    if ($unresolvedProcessPathCount -gt 0) {
        throw 'G13_MT5_TERMINAL_PROCESS_PATH_UNAVAILABLE'
    }
    throw 'G13_MT5_TERMINAL_PROCESS_PATH_MISMATCH'
}

$resolvedOwners = @()
foreach ($process in $matchingProcesses) {
    $sidResult = Invoke-CimMethod -InputObject $process -MethodName GetOwnerSid
    if ($null -eq $sidResult -or $sidResult.ReturnValue -ne 0 -or
        [string]::IsNullOrWhiteSpace([string]$sidResult.Sid)) {
        throw "G13_MT5_TERMINAL_OWNER_SID_UNRESOLVED:PID=$($process.ProcessId)"
    }

    $ownerResult = Invoke-CimMethod -InputObject $process -MethodName GetOwner
    if ($null -eq $ownerResult -or $ownerResult.ReturnValue -ne 0) {
        throw "G13_MT5_TERMINAL_OWNER_UNRESOLVED:PID=$($process.ProcessId)"
    }

    $profiles = @(
        Get-CimInstance Win32_UserProfile |
            Where-Object { $_.SID -eq $sidResult.Sid -and
                -not [string]::IsNullOrWhiteSpace([string]$_.LocalPath) }
    )
    if ($profiles.Count -ne 1) {
        throw "G13_MT5_USER_PROFILE_UNRESOLVED:PID=$($process.ProcessId):SID=$($sidResult.Sid)"
    }

    $resolvedOwners += [PSCustomObject]@{
        Pid      = [int]$process.ProcessId
        Sid      = [string]$sidResult.Sid
        Account  = "$($ownerResult.Domain)\$($ownerResult.User)"
        AppData  = Join-Path ([string]$profiles[0].LocalPath) 'AppData\Roaming'
    }
}

$distinctSids = @($resolvedOwners | Select-Object -ExpandProperty Sid -Unique)
$distinctAppData = @($resolvedOwners | Select-Object -ExpandProperty AppData -Unique)
if ($distinctSids.Count -ne 1 -or $distinctAppData.Count -ne 1) {
    throw 'G13_MT5_MULTIPLE_TERMINAL_PROFILES_MATCH_EXECUTABLE'
}

$appData = [System.IO.Path]::GetFullPath([string]$distinctAppData[0])
$commonFiles = Join-Path $appData 'MetaQuotes\Terminal\Common\Files'
if (-not (Test-Path -LiteralPath $commonFiles -PathType Container)) {
    throw "G13_MT5_COMMON_FILES_DIRECTORY_NOT_FOUND:$commonFiles"
}

if ($SetDenyKillSwitch) {
    $killSwitch = Join-Path $commonFiles 'g13_demo_kill_switch.txt'
    try {
        Set-Content -LiteralPath $killSwitch -Value 'DENY' -NoNewline -Encoding ascii
        if ((Get-Content -LiteralPath $killSwitch -Raw) -ne 'DENY') {
            throw 'G13_KILL_SWITCH_INITIAL_DENY_VERIFICATION_FAILED'
        }
    } catch {
        throw "G13_KILL_SWITCH_INITIAL_DENY_FAILED:$commonFiles; stop and restore access before any Demo execution. InnerError=$($_.Exception.Message)"
    }
    Write-Output 'G13_KILL_SWITCH_INITIAL_DENY=true'
}

$probe = Join-Path $commonFiles (".forexai-write-probe-$([Guid]::NewGuid().ToString('N')).tmp")
try {
    [System.IO.File]::WriteAllText(
        $probe,
        'ForexAI Common Files permission probe',
        [System.Text.Encoding]::ASCII
    )
} catch {
    throw "G13_MT5_COMMON_FILES_WRITE_ACCESS_DENIED:$commonFiles; grant Modify to NT AUTHORITY\NETWORK SERVICE for this directory or run the runner under the terminal owner; never fabricate an authorization record. InnerError=$($_.Exception.Message)"
} finally {
    Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
}

# APPDATA is used by the Python MetaTrader gateway and by Windows workflows
# that read/write MT5 Common\Files. Align all later steps to the actual terminal
# owner, not the GitHub Actions service identity.
"APPDATA=$appData" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"FOREXAI_MT5_COMMON_FILES=$commonFiles" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append

Write-Output "G13_MT5_PROFILE_RESOLVED=true"
Write-Output "G13_MT5_TERMINAL_OWNER=$($resolvedOwners[0].Account)"
Write-Output "G13_MT5_TERMINAL_PIDS=$(@($resolvedOwners | Select-Object -ExpandProperty Pid) -join ',')"
Write-Output "G13_MT5_COMMON_FILES=$commonFiles"
