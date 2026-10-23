# Read-only audit of the Provider service identity, issuance-registry ACLs, and
# backup inventory. This script never opens SQLite or changes files/services/ACLs.
$ErrorActionPreference = 'Stop'
$schema = 'forexai.provider_registry_access_recovery_diagnostic.v1'
$scopes = @('Process', 'User', 'Machine')
$expectedServiceIdentity = 'NT SERVICE\ForexAIProviderSvc'
$registryVariable = 'FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH'
$backupVariable = 'FOREXAI_PROVIDER_ISSUANCE_REGISTRY_BACKUP_DIR'

function Get-ConfiguredPath {
    param([Parameter(Mandatory = $true)][string]$EnvironmentName)

    $selectedValue = $null
    $selectedScope = 'NOT_CONFIGURED'
    # Process takes precedence when this diagnostic runs in the target runtime;
    # Machine is the fallback for an elevated inventory shell.
    foreach ($scope in @('Process', 'Machine', 'User')) {
        $value = [Environment]::GetEnvironmentVariable($EnvironmentName, $scope)
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            $selectedValue = [Environment]::ExpandEnvironmentVariables($value.Trim())
            $selectedScope = $scope
            break
        }
    }

    if ([string]::IsNullOrWhiteSpace($selectedValue)) {
        return [PSCustomObject]@{
            configured = $false
            selected_scope = $selectedScope
            absolute_path = $false
            path = $null
            status = 'NOT_CONFIGURED'
        }
    }

    if (-not [System.IO.Path]::IsPathRooted($selectedValue)) {
        return [PSCustomObject]@{
            configured = $true
            selected_scope = $selectedScope
            absolute_path = $false
            path = $null
            status = 'PATH_NOT_ABSOLUTE'
        }
    }

    try {
        $fullPath = [System.IO.Path]::GetFullPath($selectedValue)
        return [PSCustomObject]@{
            configured = $true
            selected_scope = $selectedScope
            absolute_path = $true
            path = $fullPath
            status = 'PATH_RESOLVED'
        }
    }
    catch {
        return [PSCustomObject]@{
            configured = $true
            selected_scope = $selectedScope
            absolute_path = $false
            path = $null
            status = 'PATH_RESOLUTION_FAILED'
        }
    }
}

function Get-PathDetails {
    param([AllowNull()][string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return [PSCustomObject]@{
            status = 'NOT_CONFIGURED'
            exists_file = $false
            exists_directory = $false
            is_reparse_point = $false
        }
    }

    try {
        $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
        $isReparse = (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
        return [PSCustomObject]@{
            status = if ($isReparse) { 'REPARSE_POINT' } elseif ($item.PSIsContainer) { 'EXISTS_DIRECTORY' } else { 'EXISTS_FILE' }
            exists_file = (-not $item.PSIsContainer) -and (-not $isReparse)
            exists_directory = [bool]$item.PSIsContainer -and (-not $isReparse)
            is_reparse_point = [bool]$isReparse
        }
    }
    catch [System.UnauthorizedAccessException] {
        return [PSCustomObject]@{
            status = 'ACCESS_DENIED'
            exists_file = $false
            exists_directory = $false
            is_reparse_point = $false
        }
    }
    catch {
        return [PSCustomObject]@{
            status = 'NOT_FOUND_OR_INACCESSIBLE'
            exists_file = $false
            exists_directory = $false
            is_reparse_point = $false
        }
    }
}

function Get-AclSnapshot {
    param([AllowNull()][string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return [PSCustomObject]@{
            status = 'NOT_AVAILABLE'
            owner = $null
            entries = @()
            broad_write_allow_detected = $null
            effective_access_calculated = $false
        }
    }

    try {
        $acl = Get-Acl -LiteralPath $Path -ErrorAction Stop
        $entries = @()
        $broadWrite = $false
        $broadPrincipalPattern = '^(Everyone|BUILTIN\\Users|NT AUTHORITY\\Authenticated Users|Authenticated Users|BUILTIN\\Power Users|NT AUTHORITY\\INTERACTIVE)$'
        $writePattern = 'Write|Modify|FullControl|CreateFiles|CreateDirectories|AppendData'

        foreach ($rule in $acl.Access) {
            $principal = [string]$rule.IdentityReference
            $rights = [string]$rule.FileSystemRights
            if ($rule.AccessControlType -eq 'Allow' -and
                $principal -match $broadPrincipalPattern -and
                $rights -match $writePattern) {
                $broadWrite = $true
            }
            if ($entries.Count -lt 100) {
                $entries += [PSCustomObject]@{
                    identity = $principal
                    access_type = [string]$rule.AccessControlType
                    rights = $rights
                    inherited = [bool]$rule.IsInherited
                }
            }
        }

        return [PSCustomObject]@{
            status = 'READ_OK'
            owner = [string]$acl.Owner
            entries = @($entries)
            broad_write_allow_detected = [bool]$broadWrite
            effective_access_calculated = $false
        }
    }
    catch [System.UnauthorizedAccessException] {
        return [PSCustomObject]@{
            status = 'ACCESS_DENIED'
            owner = $null
            entries = @()
            broad_write_allow_detected = $null
            effective_access_calculated = $false
        }
    }
    catch {
        return [PSCustomObject]@{
            status = 'ACL_READ_FAILED'
            owner = $null
            entries = @()
            broad_write_allow_detected = $null
            effective_access_calculated = $false
        }
    }
}

function Get-BackupInventory {
    param([AllowNull()][string]$Path)

    $pathDetails = Get-PathDetails -Path $Path
    if ($pathDetails.status -ne 'EXISTS_DIRECTORY') {
        return [PSCustomObject]@{
            status = $pathDetails.status
            candidate_count = 0
            newest_backup_utc = $null
            newest_backup_age_hours = $null
        }
    }

    try {
        $files = @(
            Get-ChildItem -LiteralPath $Path -File -Force -ErrorAction Stop |
                Where-Object { $_.Extension -match '^\.(sqlite3?|db|bak)$' }
        )
        $newest = $null
        $ageHours = $null
        if ($files.Count -gt 0) {
            $newest = $files | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
            $ageHours = [Math]::Round(([DateTime]::UtcNow - $newest.LastWriteTimeUtc).TotalHours, 2)
        }
        return [PSCustomObject]@{
            status = if ($files.Count -gt 0) { 'CANDIDATES_FOUND_NOT_VALIDATED' } else { 'NO_BACKUP_CANDIDATES' }
            candidate_count = [int]$files.Count
            newest_backup_utc = if ($null -ne $newest) { $newest.LastWriteTimeUtc.ToString('o') } else { $null }
            newest_backup_age_hours = $ageHours
        }
    }
    catch [System.UnauthorizedAccessException] {
        return [PSCustomObject]@{
            status = 'ACCESS_DENIED'
            candidate_count = 0
            newest_backup_utc = $null
            newest_backup_age_hours = $null
        }
    }
    catch {
        return [PSCustomObject]@{
            status = 'INVENTORY_FAILED'
            candidate_count = 0
            newest_backup_utc = $null
            newest_backup_age_hours = $null
        }
    }
}

$configurationBlockers = [System.Collections.Generic.List[string]]::new()
$manualRequirements = [System.Collections.Generic.List[string]]::new()

$currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$service = $null
$serviceQueryFailed = $false
try {
    $service = Get-CimInstance Win32_Service -Filter "Name='ForexAIProviderSvc'" -ErrorAction Stop
}
catch {
    $serviceQueryFailed = $true
}

if ($serviceQueryFailed) {
    $serviceSummary = [PSCustomObject]@{
        registered = $false
        status = 'QUERY_FAILED'
        expected_start_name = $expectedServiceIdentity
        actual_start_name = $null
        identity_check = 'NOT_VERIFIED'
    }
    $configurationBlockers.Add('PROVIDER_SERVICE_QUERY_FAILED')
}
elseif ($null -eq $service) {
    $serviceSummary = [PSCustomObject]@{
        registered = $false
        status = 'NOT_REGISTERED'
        expected_start_name = $expectedServiceIdentity
        actual_start_name = $null
        identity_check = 'NOT_VERIFIED'
    }
    $configurationBlockers.Add('PROVIDER_SERVICE_NOT_REGISTERED')
}
else {
    $actualStartName = [string]$service.StartName
    $identityMatches = [string]::Equals(
        $actualStartName,
        $expectedServiceIdentity,
        [System.StringComparison]::OrdinalIgnoreCase
    )
    $serviceSummary = [PSCustomObject]@{
        registered = $true
        status = [string]$service.State
        expected_start_name = $expectedServiceIdentity
        actual_start_name = $actualStartName
        identity_check = if ($identityMatches) { 'MATCH' } else { 'MISMATCH' }
    }
    if (-not $identityMatches) {
        $configurationBlockers.Add('PROVIDER_SERVICE_IDENTITY_MISMATCH')
    }
}

$registryConfig = Get-ConfiguredPath -EnvironmentName $registryVariable
$registryPath = [string]$registryConfig.path
if (-not $registryConfig.configured) {
    $configurationBlockers.Add('PROVIDER_REGISTRY_PATH_NOT_CONFIGURED')
}
elseif (-not $registryConfig.absolute_path) {
    $configurationBlockers.Add('PROVIDER_REGISTRY_PATH_NOT_ABSOLUTE')
}

$registryDetails = Get-PathDetails -Path $registryPath
$registryParentPath = if ($registryPath) { Split-Path -Parent $registryPath } else { $null }
$registryParentDetails = Get-PathDetails -Path $registryParentPath
if ($registryParentDetails.status -ne 'EXISTS_DIRECTORY') {
    $configurationBlockers.Add('PROVIDER_REGISTRY_PARENT_NOT_AVAILABLE')
}
if ($registryDetails.status -eq 'NOT_FOUND_OR_INACCESSIBLE') {
    $configurationBlockers.Add('PROVIDER_REGISTRY_FILE_NOT_FOUND_OR_INACCESSIBLE')
}
elseif ($registryDetails.status -eq 'REPARSE_POINT') {
    $configurationBlockers.Add('PROVIDER_REGISTRY_REPARSE_POINT_FORBIDDEN')
}
elseif ($registryDetails.status -ne 'EXISTS_FILE') {
    $configurationBlockers.Add('PROVIDER_REGISTRY_NOT_REGULAR_FILE')
}

$registryParentAcl = Get-AclSnapshot -Path $registryParentPath
$registryTargetAcl = if ($registryDetails.status -eq 'EXISTS_FILE') {
    Get-AclSnapshot -Path $registryPath
} else {
    $null
}
if ($registryParentAcl.status -ne 'READ_OK') {
    $configurationBlockers.Add('PROVIDER_REGISTRY_PARENT_ACL_UNREADABLE')
}
if ($registryParentAcl.broad_write_allow_detected -eq $true) {
    $configurationBlockers.Add('PROVIDER_REGISTRY_PARENT_BROAD_WRITE_ACE_REVIEW')
}
if ($null -ne $registryTargetAcl) {
    if ($registryTargetAcl.status -ne 'READ_OK') {
        $configurationBlockers.Add('PROVIDER_REGISTRY_FILE_ACL_UNREADABLE')
    }
    if ($registryTargetAcl.broad_write_allow_detected -eq $true) {
        $configurationBlockers.Add('PROVIDER_REGISTRY_FILE_BROAD_WRITE_ACE_REVIEW')
    }
}

$backupConfig = Get-ConfiguredPath -EnvironmentName $backupVariable
$backupPath = [string]$backupConfig.path
if (-not $backupConfig.configured) {
    $configurationBlockers.Add('PROVIDER_REGISTRY_BACKUP_DIRECTORY_NOT_CONFIGURED')
}
elseif (-not $backupConfig.absolute_path) {
    $configurationBlockers.Add('PROVIDER_REGISTRY_BACKUP_PATH_NOT_ABSOLUTE')
}
$backupDetails = Get-PathDetails -Path $backupPath
$backupInventory = Get-BackupInventory -Path $backupPath
$backupAcl = if ($backupDetails.status -eq 'EXISTS_DIRECTORY') {
    Get-AclSnapshot -Path $backupPath
} else {
    $null
}
if ($backupDetails.status -ne 'EXISTS_DIRECTORY') {
    $configurationBlockers.Add('PROVIDER_REGISTRY_BACKUP_DIRECTORY_NOT_AVAILABLE')
}
elseif ($backupInventory.candidate_count -eq 0) {
    $configurationBlockers.Add('PROVIDER_REGISTRY_BACKUP_CANDIDATE_MISSING')
}
if ($null -ne $backupAcl) {
    if ($backupAcl.status -ne 'READ_OK') {
        $configurationBlockers.Add('PROVIDER_REGISTRY_BACKUP_ACL_UNREADABLE')
    }
    if ($backupAcl.broad_write_allow_detected -eq $true) {
        $configurationBlockers.Add('PROVIDER_REGISTRY_BACKUP_BROAD_WRITE_ACE_REVIEW')
    }
}

# ACL snapshots do not prove effective access through group membership/deny ACEs.
# A successful restore drill is separately required before issuance is considered.
$manualRequirements.Add('EFFECTIVE_ACCESS_TEST_UNDER_PROVIDER_IDENTITY_REQUIRED')
$manualRequirements.Add('REGISTRY_BACKUP_RESTORE_REHEARSAL_AND_REPLAY_RECONCILIATION_REQUIRED')

$report = [PSCustomObject]@{
    schema = $schema
    status = if ($configurationBlockers.Count -gt 0) { 'BLOCKED' } else { 'REVIEW_REQUIRED' }
    read_only = $true
    diagnostic_process_identity = $currentIdentity
    expected_provider_service_identity = $expectedServiceIdentity
    provider_service = $serviceSummary
    registry = [PSCustomObject]@{
        environment_variable = $registryVariable
        selected_environment_scope = $registryConfig.selected_scope
        configured = [bool]$registryConfig.configured
        absolute_path = [bool]$registryConfig.absolute_path
        target_status = $registryDetails.status
        target_is_reparse_point = [bool]$registryDetails.is_reparse_point
        parent_status = $registryParentDetails.status
        parent_acl = $registryParentAcl
        target_acl = $registryTargetAcl
        path_printed = $false
        database_opened = $false
        database_modified = $false
    }
    backup = [PSCustomObject]@{
        environment_variable = $backupVariable
        selected_environment_scope = $backupConfig.selected_scope
        configured = [bool]$backupConfig.configured
        absolute_path = [bool]$backupConfig.absolute_path
        directory_status = $backupDetails.status
        inventory = $backupInventory
        acl = $backupAcl
        path_printed = $false
        backup_database_opened = $false
        backup_modified = $false
        restore_rehearsal_verified = $false
    }
    manual_requirements = @($manualRequirements)
    blockers = @($configurationBlockers) + @($manualRequirements)
    private_keys_read = $false
    passphrase_values_printed = $false
    key_values_printed = $false
    signed_request_created = $false
    ledger_mutated = $false
    authenticated_envelope_created = $false
    orders_submitted = $false
    demo_trading_authorized = $false
    live_trading_allowed = $false
}

$report | ConvertTo-Json -Depth 9
if ($configurationBlockers.Count -gt 0 -or $manualRequirements.Count -gt 0) { exit 2 }
exit 0
