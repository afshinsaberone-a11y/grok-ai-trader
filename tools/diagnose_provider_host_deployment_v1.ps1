[CmdletBinding()]
param(
    [string]$ProviderRoot = 'C:\ProgramData\ForexAI-Provider'
)

# Read-only deployment inventory for ForexAI's external Provider host.
# Never print key/passphrase values, change ACLs/environment/services, or create authority.
$ErrorActionPreference = 'Stop'
$schema = 'forexai.provider_host_deployment_diagnostic.v1'
$scopes = @('Process', 'User', 'Machine')

function Get-PathStatus {
    param([Parameter(Mandatory = $true)][string]$Path)
    try {
        $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
        if ($item.PSIsContainer) { return 'EXISTS_DIRECTORY' }
        return 'EXISTS_FILE'
    }
    catch [System.UnauthorizedAccessException] { return 'ACCESS_DENIED' }
    catch {
        if ($_.FullyQualifiedErrorId -match 'PathNotFound|ItemNotFound' -or $_.CategoryInfo.Category -eq 'ObjectNotFound') {
            return 'NOT_FOUND'
        }
        return 'CHECK_FAILED'
    }
}

function Get-DirectoryInventory {
    param([Parameter(Mandatory = $true)][string]$Path)
    try {
        $entries = @(
            Get-ChildItem -LiteralPath $Path -Force -ErrorAction Stop |
                ForEach-Object {
                    [PSCustomObject]@{
                        name = $_.Name
                        type = if ($_.PSIsContainer) { 'DIRECTORY' } else { 'FILE' }
                        size_bytes = if ($_.PSIsContainer) { $null } else { [long]$_.Length }
                    }
                }
        )
        return [PSCustomObject]@{
            status = if ($entries.Count -eq 0) { 'EMPTY' } else { 'LISTED' }
            entries = $entries
        }
    }
    catch [System.UnauthorizedAccessException] {
        return [PSCustomObject]@{ status = 'ACCESS_DENIED'; entries = @() }
    }
    catch {
        return [PSCustomObject]@{ status = (Get-PathStatus -Path $Path); entries = @() }
    }
}

function Get-CanonicalPublicKey {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
    try {
        $trimmed = $Value.Trim()
        $bytes = [Convert]::FromBase64String($trimmed)
        if ($bytes.Length -ne 32) { return $null }
        $canonical = [Convert]::ToBase64String($bytes)
        if (-not [string]::Equals($canonical, $trimmed, [System.StringComparison]::Ordinal)) { return $null }
        return $canonical
    }
    catch { return $null }
}

function Get-PemHeaderType {
    param([Parameter(Mandatory = $true)][string]$Path)
    try {
        $header = [string](Get-Content -LiteralPath $Path -TotalCount 1 -ErrorAction Stop)
        switch -Regex ($header.Trim()) {
            '^-----BEGIN ENCRYPTED PRIVATE KEY-----$' { return 'ENCRYPTED_PKCS8' }
            '^-----BEGIN PRIVATE KEY-----$' { return 'PKCS8_HEADER' }
            '^-----BEGIN OPENSSH PRIVATE KEY-----$' { return 'OPENSSH_PRIVATE_KEY' }
            '^-----BEGIN RSA PRIVATE KEY-----$' { return 'RSA_PRIVATE_KEY' }
            '^-----BEGIN EC PRIVATE KEY-----$' { return 'EC_PRIVATE_KEY' }
            default { return 'UNKNOWN_HEADER' }
        }
    }
    catch [System.UnauthorizedAccessException] { return 'ACCESS_DENIED' }
    catch { return (Get-PathStatus -Path $Path) }
}

function Get-EnvironmentPresence {
    param([Parameter(Mandatory = $true)][string]$Name)
    $result = [ordered]@{}
    foreach ($scope in $scopes) {
        $value = [Environment]::GetEnvironmentVariable($Name, $scope)
        $result[$scope] = -not [string]::IsNullOrWhiteSpace($value)
    }
    return [PSCustomObject]$result
}

function Get-PublicKeyConsistency {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string]$EnvironmentName
    )
    $fileStatus = Get-PathStatus -Path $FilePath
    $fileKey = $null
    if ($fileStatus -eq 'EXISTS_FILE') {
        try {
            $fileText = Get-Content -LiteralPath $FilePath -Raw -ErrorAction Stop
            $fileKey = Get-CanonicalPublicKey -Value ([string]$fileText)
        }
        catch {
            $fileStatus = if ($_.Exception -is [System.UnauthorizedAccessException]) { 'ACCESS_DENIED' } else { 'READ_FAILED' }
        }
    }
    if ($fileStatus -eq 'EXISTS_FILE') {
        $fileStatus = if ($null -eq $fileKey) { 'INVALID_FORMAT' } else { 'VALID_32_BYTE_KEY' }
    }

    $scopeChecks = [ordered]@{}
    foreach ($scope in $scopes) {
        $envValue = [Environment]::GetEnvironmentVariable($EnvironmentName, $scope)
        $envKey = Get-CanonicalPublicKey -Value $envValue
        if ([string]::IsNullOrWhiteSpace($envValue)) {
            $scopeStatus = 'NOT_CONFIGURED'
        }
        elseif ($null -eq $envKey) {
            $scopeStatus = 'INVALID_FORMAT'
        }
        elseif ($null -eq $fileKey) {
            $scopeStatus = 'PUBLIC_FILE_NOT_VALID'
        }
        elseif ([string]::Equals($fileKey, $envKey, [System.StringComparison]::Ordinal)) {
            $scopeStatus = 'MATCH'
        }
        else {
            $scopeStatus = 'MISMATCH'
        }
        $scopeChecks[$scope] = $scopeStatus
    }

    return [PSCustomObject]@{
        role = $Name
        public_file_name = [System.IO.Path]::GetFileName($FilePath)
        public_file_status = $fileStatus
        environment_variable_name = $EnvironmentName
        match_status_by_scope = [PSCustomObject]$scopeChecks
    }
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isElevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

$service = Get-CimInstance Win32_Service -Filter "Name='ForexAIProviderSvc'" -ErrorAction SilentlyContinue
$serviceSummary = if ($null -eq $service) {
    [PSCustomObject]@{ registered = $false; status = 'NOT_INSTALLED_OR_NOT_REGISTERED'; start_name = $null }
} else {
    [PSCustomObject]@{ registered = $true; status = [string]$service.State; start_name = [string]$service.StartName }
}

$keysDirectory = Join-Path $ProviderRoot 'keys'
$inputDirectory = Join-Path $ProviderRoot 'in'
$outputDirectory = Join-Path $ProviderRoot 'out'

$inventory = [ordered]@{
    keys = Get-DirectoryInventory -Path $keysDirectory
    in = Get-DirectoryInventory -Path $inputDirectory
    out = Get-DirectoryInventory -Path $outputDirectory
}

$criticalFiles = [ordered]@{}
foreach ($relativePath in @(
    'venv\Scripts\python.exe',
    'source\tools\control_plane_provider_host_preflight_v1.py',
    'source\tools\control_plane_admission_provider_v1.py',
    'source\tools\g13_capital_firewall_promotion_attestor_v1.py'
)) {
    $criticalFiles[$relativePath] = Get-PathStatus -Path (Join-Path $ProviderRoot $relativePath)
}

$publicKeyChecks = @(
    Get-PublicKeyConsistency -Name 'Admission Provider' -FilePath (Join-Path $keysDirectory 'admission-provider-public-key.txt') -EnvironmentName 'FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY'
    Get-PublicKeyConsistency -Name 'Promotion Attestor' -FilePath (Join-Path $keysDirectory 'promotion-attestor-public-key.txt') -EnvironmentName 'FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY'
)

$privateKeyHeaders = [ordered]@{
    admission = Get-PemHeaderType -Path (Join-Path $keysDirectory 'admission-provider-ed25519.pem')
    promotion_attestor = Get-PemHeaderType -Path (Join-Path $keysDirectory 'promotion-attestor-ed25519.pem')
}
$promotionPrivateKeyOnProviderHost = (Get-PathStatus -Path (Join-Path $keysDirectory 'promotion-attestor-ed25519.pem')) -eq 'EXISTS_FILE'

$publicEnvironmentNames = @(
    'FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY',
    'FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY',
    'FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY',
    'FOREXAI_PROVIDER_RISK_PUBLIC_KEY',
    'FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY',
    'FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY'
)
$environmentPresence = [ordered]@{}
foreach ($name in $publicEnvironmentNames) {
    $environmentPresence[$name] = Get-EnvironmentPresence -Name $name
}

$passphraseNames = @(
    'FOREXAI_PROVIDER_SIGNING_KEY_PASSPHRASE',
    'FOREXAI_G13_ATTESTOR_KEY_PASSPHRASE'
)
$passphrasePresence = [ordered]@{}
foreach ($name in $passphraseNames) {
    $passphrasePresence[$name] = Get-EnvironmentPresence -Name $name
}

$registryPresence = Get-EnvironmentPresence -Name 'FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH'
$registryPath = [Environment]::GetEnvironmentVariable('FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH', 'Process')
if ([string]::IsNullOrWhiteSpace($registryPath)) {
    $registryPath = [Environment]::GetEnvironmentVariable('FOREXAI_PROVIDER_ISSUANCE_REGISTRY_PATH', 'Machine')
}
$registryParentStatus = 'NOT_CONFIGURED'
if (-not [string]::IsNullOrWhiteSpace($registryPath)) {
    try {
        $registryParent = Split-Path -Parent $registryPath
        $registryParentStatus = if ((Get-PathStatus -Path $registryParent) -eq 'EXISTS_DIRECTORY') { 'EXISTS_DIRECTORY' } else { 'MISSING_OR_INACCESSIBLE' }
    }
    catch { $registryParentStatus = 'INVALID_PATH' }
}

$blockers = [System.Collections.Generic.List[string]]::new()
if (-not $serviceSummary.registered) { $blockers.Add('PROVIDER_SERVICE_NOT_REGISTERED') }
foreach ($name in $publicEnvironmentNames) {
    $presence = $environmentPresence[$name]
    if (-not $presence.Process) { $blockers.Add("PUBLIC_TRUST_ANCHOR_NOT_CONFIGURED:$name") }
}
foreach ($check in $publicKeyChecks) {
    if ($check.public_file_status -ne 'VALID_32_BYTE_KEY') { $blockers.Add("PUBLIC_KEY_FILE_INVALID:$($check.role)") }
    if ($check.match_status_by_scope.Process -eq 'MISMATCH') { $blockers.Add("PUBLIC_KEY_ENV_FILE_MISMATCH:$($check.role)") }
    if ($check.match_status_by_scope.Process -ne 'MATCH') { $blockers.Add("PUBLIC_KEY_PROCESS_SCOPE_NOT_MATCHED:$($check.role)") }
}
foreach ($relativePath in $criticalFiles.Keys) {
    if ($criticalFiles[$relativePath] -ne 'EXISTS_FILE') { $blockers.Add("CRITICAL_FILE_NOT_PRESENT:$relativePath") }
}
if ($inventory.in.status -eq 'EMPTY') { $blockers.Add('PROVIDER_INPUT_DIRECTORY_EMPTY') }
if ($registryParentStatus -ne 'EXISTS_DIRECTORY') { $blockers.Add('PROVIDER_REGISTRY_PARENT_NOT_AVAILABLE') }
if ($privateKeyHeaders.admission -ne 'ENCRYPTED_PKCS8') { $blockers.Add('ADMISSION_PRIVATE_KEY_HEADER_UNEXPECTED') }
if ($privateKeyHeaders.promotion_attestor -eq 'ENCRYPTED_PKCS8' -and $promotionPrivateKeyOnProviderHost) {
    $blockers.Add('PROMOTION_PRIVATE_KEY_PRESENT_ON_PROVIDER_HOST_VERIFY_TRUST_BOUNDARY')
}
foreach ($name in $passphraseNames) {
    $presence = $passphrasePresence[$name]
    if (-not $presence.Process) { $blockers.Add("PASSPHRASE_NOT_IN_CURRENT_PROCESS_ENVIRONMENT:$name") }
    if ($presence.Machine) { $blockers.Add("PASSPHRASE_MACHINE_SCOPE_CONFIGURED_REVIEW:$name") }
}

$report = [PSCustomObject]@{
    schema = $schema
    status = if ($blockers.Count -eq 0) { 'DIAGNOSTIC_PASS_SOURCE_EVIDENCE_STILL_REQUIRED' } else { 'BLOCKED' }
    read_only = $true
    private_key_contents_read = $false
    private_key_header_only = $true
    key_values_printed = $false
    passphrase_values_printed = $false
    orders_submitted = $false
    signed_request_created = $false
    ledger_mutated = $false
    authenticated_envelope_created = $false
    demo_trading_authorized = $false
    live_trading_allowed = $false
    host = [PSCustomObject]@{ computer_name = $env:COMPUTERNAME; elevated = $isElevated }
    provider_service = $serviceSummary
    critical_files = [PSCustomObject]$criticalFiles
    directory_inventory = [PSCustomObject]$inventory
    public_key_checks = $publicKeyChecks
    private_key_headers = [PSCustomObject]$privateKeyHeaders
    public_environment_presence = [PSCustomObject]$environmentPresence
    passphrase_environment_presence = [PSCustomObject]$passphrasePresence
    registry = [PSCustomObject]@{
        environment_presence = $registryPresence
        parent_status = $registryParentStatus
        path_printed = $false
        production_registry_opened = $false
    }
    blockers = @($blockers)
}

$report | ConvertTo-Json -Depth 9
if ($blockers.Count -gt 0) { exit 2 }
exit 0
