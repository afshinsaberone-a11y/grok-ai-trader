[CmdletBinding()]
param(
    [string]$OutputPath = ''
)

# Bounded, read-only discovery of likely ForexAI Control Plane files.
# This script checks filenames and filesystem metadata only. It never reads
# candidate file contents, secrets, key material, ledger rows, or JSON payloads.
# A filename match is not evidence of authority and must never authorize trading.

$ErrorActionPreference = 'Stop'
$maxDirectories = 1500
$maxFiles = 12000
$skipDirectoryNames = @(
    '.git', '.venv', 'venv', 'node_modules', '__pycache__',
    'site-packages', 'pip-cache', 'cache', 'logs', 'temp', 'tmp'
)

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    if ([string]::IsNullOrWhiteSpace($env:TEMP)) {
        throw 'CONTROL_PLANE_INVENTORY_TEMP_DIRECTORY_UNAVAILABLE'
    }
    $OutputPath = Join-Path $env:TEMP (
        'forexai-control-plane-storage-inventory-' +
        [Guid]::NewGuid().ToString('N') + '.json'
    )
}
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)

$roots = New-Object System.Collections.Generic.List[object]
# Use PowerShell's case-insensitive hashtable rather than a generic HashSet
# constructor; this is compatible with Windows PowerShell 5.1 binder behavior.
$seenRoots = @{}

function Add-InventoryRoot {
    param(
        [string]$Label,
        [string]$Path,
        [int]$MaxDepth = 4
    )
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if ($Path -notmatch '^[A-Za-z]:\\') { return }
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        if ($seenRoots.ContainsKey($full)) { return }
        $seenRoots[$full] = $true
        $exists = Test-Path -LiteralPath $full -PathType Container -ErrorAction SilentlyContinue
        $roots.Add([pscustomobject]@{
            label = $Label
            path = $full
            exists = [bool]$exists
            max_depth = $MaxDepth
        })
    } catch {
        # Do not echo exception text: it may contain machine-specific paths.
    }
}

# Deliberately bounded allowlist of plausible app data directories.
Add-InventoryRoot -Label 'ProgramData_ForexAI' -Path (Join-Path $env:ProgramData 'ForexAI')
Add-InventoryRoot -Label 'ProgramData_ForexAI_Provider' -Path (Join-Path $env:ProgramData 'ForexAI-Provider')
Add-InventoryRoot -Label 'ProgramData_ForexAIProvider' -Path (Join-Path $env:ProgramData 'ForexAIProvider')
Add-InventoryRoot -Label 'SystemDrive_ForexAI' -Path (Join-Path $env:SystemDrive 'ForexAI')
Add-InventoryRoot -Label 'SystemDrive_ForexAI_Provider' -Path (Join-Path $env:SystemDrive 'ForexAI-Provider')
Add-InventoryRoot -Label 'SystemDrive_ForexAIProvider' -Path (Join-Path $env:SystemDrive 'ForexAIProvider')
Add-InventoryRoot -Label 'UserProfile_ForexAI' -Path (Join-Path $env:USERPROFILE 'ForexAI')
Add-InventoryRoot -Label 'Documents_ForexAI' -Path (Join-Path $env:USERPROFILE 'Documents\ForexAI')
Add-InventoryRoot -Label 'AppDataRoaming_ForexAI' -Path (Join-Path $env:APPDATA 'ForexAI')
Add-InventoryRoot -Label 'AppDataLocal_ForexAI' -Path (Join-Path $env:LOCALAPPDATA 'ForexAI')
Add-InventoryRoot -Label 'Dropbox_ForexAI' -Path (Join-Path $env:USERPROFILE 'Dropbox\ForexAI')
Add-InventoryRoot -Label 'DropboxPersonal_ForexAI' -Path (Join-Path $env:USERPROFILE 'Dropbox (Personal)\ForexAI')
Add-InventoryRoot -Label 'UserOneDrive_ForexAI' -Path (Join-Path $env:USERPROFILE 'OneDrive\ForexAI')
if (-not [string]::IsNullOrWhiteSpace($env:OneDrive)) {
    Add-InventoryRoot -Label 'ConfiguredOneDrive_ForexAI' -Path (Join-Path $env:OneDrive 'ForexAI')
}
Add-InventoryRoot -Label 'MT5_Common_Files' -Path (Join-Path $env:APPDATA 'MetaQuotes\Terminal\Common\Files') -MaxDepth 3

# Check the configured environment-variable scopes without emitting their values.
$targetSpecs = @(
    @{ name = 'FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH'; kind = 'admission_request' },
    @{ name = 'FOREXAI_TRADE_LEDGER_PATH'; kind = 'trade_ledger' },
    @{ name = 'FOREXAI_AUTHENTICATED_ENVELOPE_PATH'; kind = 'authenticated_envelope' }
)
$targetReport = New-Object System.Collections.Generic.List[object]
foreach ($spec in $targetSpecs) {
    $scopeValues = @{}
    foreach ($scope in @('Process', 'User', 'Machine')) {
        switch ($scope) {
            'Process' { $target = [System.EnvironmentVariableTarget]::Process }
            'User' { $target = [System.EnvironmentVariableTarget]::User }
            'Machine' { $target = [System.EnvironmentVariableTarget]::Machine }
        }
        $value = [Environment]::GetEnvironmentVariable($spec.name, $target)
        $scopeValues[$scope] = $value
    }

    $processValue = [string]$scopeValues['Process']
    $machineValue = [string]$scopeValues['Machine']
    $userValue = [string]$scopeValues['User']
    $processExists = $false
    $machineExists = $false
    $userExists = $false
    foreach ($entry in @(
        @{ scope = 'Process'; value = $processValue },
        @{ scope = 'Machine'; value = $machineValue },
        @{ scope = 'User'; value = $userValue }
    )) {
        $value = [string]$entry.value
        if ([string]::IsNullOrWhiteSpace($value)) { continue }
        $fileExists = $false
        try {
            if ($value -match '^[A-Za-z]:\\') {
                $fileExists = [bool](Test-Path -LiteralPath $value -PathType Leaf -ErrorAction SilentlyContinue)
                $parent = Split-Path -Parent $value
                if ($parent -and (Test-Path -LiteralPath $parent -PathType Container -ErrorAction SilentlyContinue)) {
                    # Scan only one level beneath an existing configured parent.
                    Add-InventoryRoot -Label 'ConfiguredTargetParent' -Path $parent -MaxDepth 1
                }
            }
        } catch { }
        switch ($entry.scope) {
            'Process' { $processExists = $fileExists }
            'Machine' { $machineExists = $fileExists }
            'User' { $userExists = $fileExists }
        }
    }
    $targetReport.Add([pscustomobject]@{
        variable = $spec.name
        process_configured = -not [string]::IsNullOrWhiteSpace($processValue)
        user_configured = -not [string]::IsNullOrWhiteSpace($userValue)
        machine_configured = -not [string]::IsNullOrWhiteSpace($machineValue)
        process_target_file_exists = $processExists
        user_target_file_exists = $userExists
        machine_target_file_exists = $machineExists
    })
}

function Get-CandidateCategory {
    param([string]$Name)
    if ($Name -match '(?i)^trade[-_.]?ledger.*\.(jsonl|ndjson|json|db|sqlite)$') {
        return 'trade_ledger_filename_candidate'
    }
    if ($Name -match '(?i)(authenticated[-_.]?envelope|runtime[-_.]?authorization[-_.]?envelope|auth[-_.]?envelope).*\.json$') {
        return 'authenticated_envelope_filename_candidate'
    }
    if ($Name -match '(?i)(admission[-_.]?request|demo[-_.]?admission).*\.json$') {
        return 'admission_request_filename_candidate'
    }
    if ($Name -match '(?i)^ForexAI_Authorization_[0-9]+_EURUSD\.auth$') {
        return 'mql5_authorization_filename_candidate'
    }
    if ($Name -match '(?i)(source[-_.]?packet|promotion[-_.]?attestation|risk[-_.]?attestation|operator[-_.]?approval|capital[-_.]?firewall.*grant).*\.json$') {
        return 'source_attestation_or_grant_filename_candidate'
    }
    return $null
}

$candidates = New-Object System.Collections.Generic.List[object]
$rootResults = New-Object System.Collections.Generic.List[object]
$totalDirectories = 0
$totalFiles = 0
$scanErrors = 0
$truncated = $false

foreach ($root in $roots) {
    $visited = 0
    $filesSeen = 0
    $rootErrors = 0
    if (-not $root.exists) {
        $rootResults.Add([pscustomobject]@{
            root_label = $root.label
            root_exists = $false
            directories_visited = 0
            files_examined = 0
            scan_errors = 0
        })
        continue
    }

    $queue = New-Object 'System.Collections.Generic.Queue[object]'
    $queue.Enqueue([pscustomobject]@{ path = $root.path; depth = 0 })
    while ($queue.Count -gt 0) {
        if ($totalDirectories -ge $maxDirectories -or $totalFiles -ge $maxFiles) {
            $truncated = $true
            break
        }
        $node = $queue.Dequeue()
        try {
            $dirInfo = Get-Item -LiteralPath $node.path -Force -ErrorAction Stop
            if (($dirInfo.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
            $visited++
            $totalDirectories++
            $items = Get-ChildItem -LiteralPath $node.path -Force -ErrorAction Stop
        } catch {
            $rootErrors++
            $scanErrors++
            continue
        }

        foreach ($item in $items) {
            if ($totalFiles -ge $maxFiles -or $totalDirectories -ge $maxDirectories) {
                $truncated = $true
                break
            }
            if ($item.PSIsContainer) {
                if ($node.depth -lt $root.max_depth -and $item.Name -notin $skipDirectoryNames) {
                    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
                        $queue.Enqueue([pscustomobject]@{
                            path = $item.FullName
                            depth = $node.depth + 1
                        })
                    }
                }
                continue
            }
            $totalFiles++
            $filesSeen++
            $category = Get-CandidateCategory -Name $item.Name
            if ($null -eq $category) { continue }
            $exampleName = $item.Name -match '(?i)(^|[._-])(example|sample|fixture|template|test|backup|bak|old|disabled)([._-]|$)'
            $candidates.Add([pscustomobject]@{
                category = if ($exampleName) { 'example_or_test_filename_only' } else { $category }
                filename = $item.Name
                local_path = $item.FullName
                size_bytes = [long]$item.Length
                modified_utc = $item.LastWriteTimeUtc.ToString('o')
                example_or_test_name = [bool]$exampleName
                authority_verified = $false
            })
        }
    }
    $rootResults.Add([pscustomobject]@{
        root_label = $root.label
        root_exists = $true
        directories_visited = $visited
        files_examined = $filesSeen
        scan_errors = $rootErrors
    })
}

$status = 'INVENTORY_COMPLETE_DISCOVERY_ONLY'
if ($truncated -or $scanErrors -gt 0) { $status = 'INVENTORY_PARTIAL_DISCOVERY_ONLY' }
$report = [ordered]@{
    schema = 'forexai.control_plane_storage_inventory.v1'
    checked_at_utc = [DateTime]::UtcNow.ToString('o')
    status = $status
    scan_limits = [ordered]@{
        max_directories = $maxDirectories
        max_files = $maxFiles
        maximum_depth = 4
        truncated = [bool]$truncated
    }
    configured_targets = @($targetReport)
    scanned_roots = @($rootResults)
    filename_candidates = @($candidates)
    summary = [ordered]@{
        directory_count = $totalDirectories
        file_count = $totalFiles
        candidate_count = $candidates.Count
        scan_errors = $scanErrors
    }
    safety = [ordered]@{
        authority_verified = $false
        secrets_read = $false
        private_key_contents_read = $false
        candidate_file_contents_read = $false
        ledger_mutated = $false
        authorization_created = $false
        kill_switch_changed = $false
        orders_submitted = $false
    }
}

$reportDirectory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $reportDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8

Write-Output ("CONTROL_PLANE_INVENTORY_STATUS=" + $status)
Write-Output ("CONTROL_PLANE_INVENTORY_CANDIDATE_COUNT=" + $candidates.Count)
Write-Output 'CONTROL_PLANE_AUTHORITY_VERIFIED=false'
Write-Output 'CONTROL_PLANE_FILE_CONTENTS_READ=false'
Write-Output 'ORDER_SUBMISSION_PERFORMED=false'
Write-Output ("CONTROL_PLANE_INVENTORY_REPORT_PATH=" + $OutputPath)
