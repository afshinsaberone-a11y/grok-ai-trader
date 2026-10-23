[CmdletBinding()]
param([string]$GrantRoot = 'C:\ProgramData\ForexAI-CapitalFirewall')
$ErrorActionPreference = 'Continue'
$roles = [ordered]@{
    Admission = 'FOREXAI_CONTROL_PLANE_ADMISSION_PUBLIC_KEY'
    Promotion = 'FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY'
    Signal = 'FOREXAI_PROVIDER_SIGNAL_PUBLIC_KEY'
    Risk = 'FOREXAI_PROVIDER_RISK_PUBLIC_KEY'
    Operator = 'FOREXAI_PROVIDER_OPERATOR_PUBLIC_KEY'
    Grant = 'FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY'
}
$scopes = @('Process', 'User', 'Machine')

function Get-PublicKeyInfo {
    param([AllowNull()][string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return [PSCustomObject]@{ status = 'NOT_CONFIGURED'; fingerprint = $null } }
    try {
        $trimmed = $Value.Trim()
        $raw = [Convert]::FromBase64String($trimmed)
        if ($raw.Length -ne 32 -or [Convert]::ToBase64String($raw) -cne $trimmed) { return [PSCustomObject]@{ status = 'INVALID_BASE64_OR_LENGTH'; fingerprint = $null } }
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try { $fingerprint = ([BitConverter]::ToString($sha.ComputeHash($raw))).Replace('-', '').ToLowerInvariant() }
        finally { $sha.Dispose() }
        return [PSCustomObject]@{ status = 'VALID_32_BYTE_ED25519_SHAPE'; fingerprint = $fingerprint }
    } catch { return [PSCustomObject]@{ status = 'INVALID_BASE64_OR_LENGTH'; fingerprint = $null } }
}

function Get-AclInventory {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return [PSCustomObject]@{ path = $Path; status = 'NOT_FOUND'; owner = $null; rules = @(); broad_write_access_present_in_acl = $null; effective_access_evaluated = $false } }
    try {
        $acl = Get-Acl -LiteralPath $Path -ErrorAction Stop
        $rules = @(
            foreach ($rule in $acl.Access) {
                $identity = [string]$rule.IdentityReference.Value
                $rights = [string]$rule.FileSystemRights
                $broad = $identity -match '(?i)(^Everyone$|Authenticated Users|BUILTIN\\Users|\\Users$)'
                $writeRisk = $broad -and $rights -match '(?i)(FullControl|Modify|Write|Delete|ChangePermissions|TakeOwnership)'
                [PSCustomObject]@{ identity = $identity; rights = $rights; access_type = [string]$rule.AccessControlType; inherited = [bool]$rule.IsInherited; broad_principal = [bool]$broad; broad_write_rights = [bool]$writeRisk }
            }
        )
        return [PSCustomObject]@{
            path = $Path; status = 'ACL_READ'; owner = [string]$acl.Owner
            are_access_rules_protected = [bool]$acl.AreAccessRulesProtected
            broad_write_access_present_in_acl = (@($rules | Where-Object { $_.broad_write_rights }).Count -gt 0)
            effective_access_evaluated = $false; rules = $rules
        }
    } catch { return [PSCustomObject]@{ path = $Path; status = 'ACL_READ_FAILED'; owner = $null; rules = @(); broad_write_access_present_in_acl = $null; effective_access_evaluated = $false } }
}

$anchorChecks = [ordered]@{}
foreach ($role in $roles.Keys) {
    $anchorChecks[$role] = [ordered]@{ environment_variable = $roles[$role] }
    foreach ($scope in $scopes) {
        $enumScope = [System.Enum]::Parse([System.EnvironmentVariableTarget], $scope)
        $value = [System.Environment]::GetEnvironmentVariable($roles[$role], $enumScope)
        $info = Get-PublicKeyInfo -Value $value
        $anchorChecks[$role][$scope] = [PSCustomObject]@{ status = $info.status; fingerprint = $info.fingerprint }
    }
}

$distinctness = [ordered]@{}
foreach ($scope in $scopes) {
    $validEntries = @()
    foreach ($role in $roles.Keys) {
        $info = $anchorChecks[$role][$scope]
        if ($info.status -eq 'VALID_32_BYTE_ED25519_SHAPE') { $validEntries += [PSCustomObject]@{ role = $role; fingerprint = $info.fingerprint } }
    }
    $duplicates = @($validEntries | Group-Object fingerprint | Where-Object { $_.Count -gt 1 } | ForEach-Object { [PSCustomObject]@{ fingerprint = $_.Name; roles = @($_.Group | ForEach-Object { $_.role }) } })
    $distinctness[$scope] = [PSCustomObject]@{
        status = if ($duplicates.Count -eq 0) { 'NO_DUPLICATES_AMONG_CONFIGURED_KEYS' } else { 'DUPLICATES_FOUND' }
        missing_roles = @($roles.Keys | Where-Object { $anchorChecks[$_][$scope].status -eq 'NOT_CONFIGURED' })
        invalid_roles = @($roles.Keys | Where-Object { $anchorChecks[$_][$scope].status -eq 'INVALID_BASE64_OR_LENGTH' })
        duplicate_groups = $duplicates
    }
}

$keyDir = Join-Path $GrantRoot 'keys'
$grantPrivateKey = Join-Path $keyDir 'capital-firewall-grant.pem'
$grantPublicKey = Join-Path $keyDir 'capital-firewall-grant-public.txt'
$privateStatus = if (Test-Path -LiteralPath $grantPrivateKey -PathType Leaf) { 'EXISTS_FILE' } else { 'NOT_FOUND' }
$privateHeader = 'NOT_CHECKED'
if ($privateStatus -eq 'EXISTS_FILE') {
    try {
        $header = [string](Get-Content -LiteralPath $grantPrivateKey -TotalCount 1 -ErrorAction Stop)
        if ($header.Trim() -ceq '-----BEGIN ENCRYPTED PRIVATE KEY-----') { $privateHeader = 'ENCRYPTED_PKCS8' }
        elseif ($header.Trim() -ceq '-----BEGIN PRIVATE KEY-----') { $privateHeader = 'UNENCRYPTED_PKCS8_HEADER' }
        else { $privateHeader = 'OTHER_OR_UNKNOWN_HEADER' }
    } catch { $privateHeader = 'HEADER_READ_FAILED' }
}
$pubFileStatus = if (Test-Path -LiteralPath $grantPublicKey -PathType Leaf) { 'EXISTS_FILE' } else { 'NOT_FOUND' }
$pubFileInfo = $null
if ($pubFileStatus -eq 'EXISTS_FILE') {
    try { $pubFileInfo = Get-PublicKeyInfo -Value ([string](Get-Content -LiteralPath $grantPublicKey -Raw -ErrorAction Stop)); $pubFileStatus = $pubFileInfo.status }
    catch { $pubFileStatus = 'READ_FAILED' }
}
$grantFileEnvMatch = [ordered]@{}
foreach ($scope in $scopes) {
    $envInfo = $anchorChecks['Grant'][$scope]
    if ($null -eq $pubFileInfo -or $pubFileInfo.status -ne 'VALID_32_BYTE_ED25519_SHAPE') { $match = 'PUBLIC_FILE_INVALID_OR_MISSING' }
    elseif ($envInfo.status -ne 'VALID_32_BYTE_ED25519_SHAPE') { $match = "ENV_$($envInfo.status)" }
    elseif ($pubFileInfo.fingerprint -ceq $envInfo.fingerprint) { $match = 'MATCH' }
    else { $match = 'MISMATCH' }
    $grantFileEnvMatch[$scope] = $match
}

$registryCandidates = [System.Collections.Generic.List[string]]::new()
$envRegistry = [Environment]::GetEnvironmentVariable('FOREXAI_CAPITAL_FIREWALL_GRANT_REGISTRY_PATH', 'Process')
if (-not [string]::IsNullOrWhiteSpace($envRegistry)) { $registryCandidates.Add($envRegistry) }
$registryCandidates.Add((Join-Path $GrantRoot 'state\grant-registry.sqlite'))
$registryCandidates.Add((Join-Path $GrantRoot 'state\grant-registry.sqlite3'))
$registryCandidates.Add((Join-Path $GrantRoot 'state\capital-firewall-grant-registry.sqlite'))
try {
    $stateDir = Join-Path $GrantRoot 'state'
    if (Test-Path -LiteralPath $stateDir -PathType Container) {
        Get-ChildItem -LiteralPath $stateDir -File -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '(?i)(grant.*registry|registry.*grant).*\.(sqlite|sqlite3|db)$' } |
            ForEach-Object { $registryCandidates.Add($_.FullName) }
    }
} catch { }
$registryCandidates = @($registryCandidates | Select-Object -Unique)
$python = Get-Command python -ErrorAction SilentlyContinue
$pythonCode = @'
import json, pathlib, sqlite3, sys
p = pathlib.Path(sys.argv[1])
out = {"read_only": True, "file_exists": p.is_file(), "status": "NOT_FOUND", "integrity": "NOT_RUN", "schema": "NOT_RUN", "registry_mutated": False}
if p.is_file():
    try:
        db = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=3.0)
        try:
            check = db.execute("PRAGMA integrity_check").fetchone()
            out["integrity"] = "PASS" if check and check[0] == "ok" else "FAIL"
            meta = db.execute("SELECT value FROM registry_meta WHERE key='schema'").fetchone()
            version = db.execute("PRAGMA user_version").fetchone()
            cols = [r[1] for r in db.execute("PRAGMA table_info(issued_grants)").fetchall()]
            expected = ["grant_id","signal_id","reservation_id","authorization_id","trade_id","commit_sha","candidate_id","candidate_config_hash","issued_at_utc","grant_sha256"]
            schema_ok = meta == ("forexai.capital_firewall.grant_registry.v1",) and version == (1,) and cols == expected
            out["schema"] = "PASS" if schema_ok else "FAIL"
            out["status"] = "READ_ONLY_SCHEMA_PASS" if out["integrity"] == "PASS" and schema_ok else "REGISTRY_INVALID"
        finally:
            db.close()
    except Exception as exc:
        out["status"] = "READ_ONLY_CHECK_FAILED"
        out["error_type"] = type(exc).__name__
print(json.dumps(out, sort_keys=True))
'@
$registryChecks = @()
foreach ($path in $registryCandidates) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $registryChecks += [PSCustomObject]@{ path = $path; status = 'NOT_FOUND'; read_only = $true; integrity = 'NOT_RUN'; schema = 'NOT_RUN'; registry_mutated = $false }; continue }
    if ($null -eq $python) { $registryChecks += [PSCustomObject]@{ path = $path; status = 'EXISTS_PYTHON_UNAVAILABLE'; read_only = $true; integrity = 'NOT_RUN'; schema = 'NOT_RUN'; registry_mutated = $false }; continue }
    try {
        $raw = @(& $python.Source -c $pythonCode $path 2>$null)
        $parsed = ($raw -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop
        $registryChecks += [PSCustomObject]@{ path = $path; status = $parsed.status; read_only = [bool]$parsed.read_only; integrity = $parsed.integrity; schema = $parsed.schema; registry_mutated = [bool]$parsed.registry_mutated; error_type = $parsed.error_type }
    } catch { $registryChecks += [PSCustomObject]@{ path = $path; status = 'READ_ONLY_CHECK_FAILED'; read_only = $true; integrity = 'NOT_RUN'; schema = 'NOT_RUN'; registry_mutated = $false; error_type = 'PowerShellOrPythonInvocationError' } }
}

$aclInventory = [ordered]@{
    private_key = Get-AclInventory -Path $grantPrivateKey
    public_key = Get-AclInventory -Path $grantPublicKey
    keys_directory = Get-AclInventory -Path $keyDir
}
$localServices = @()
try {
    $localServices = @(Get-Service -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '(?i)ForexAI|CapitalFirewall|Grant|Signal|Risk|Operator|Promotion|Admission' } | ForEach-Object { [PSCustomObject]@{ name = $_.Name; status = [string]$_.Status; start_type = [string]$_.StartType } })
} catch { }

$report = [PSCustomObject]@{
    schema = 'forexai.capital_firewall_laptop_readonly_diagnostic.v1'
    status = 'READ_ONLY_DIAGNOSTIC_COMPLETE_NOT_AN_AUTHORIZATION'
    observed_at_local = (Get-Date).ToString('o')
    host = [PSCustomObject]@{ computer_name = $env:COMPUTERNAME; current_identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name; powershell_version = $PSVersionTable.PSVersion.ToString() }
    read_only = $true
    key_values_printed = $false
    private_key_contents_read = $false
    passphrase_values_read_or_printed = $false
    public_anchor_checks_by_scope = $anchorChecks
    distinctness_by_scope = $distinctness
    grant_key_files = [PSCustomObject]@{
        private_key_status = $privateStatus
        private_key_header = $privateHeader
        public_key_file_status = $pubFileStatus
        public_key_file_fingerprint = if ($pubFileInfo) { $pubFileInfo.fingerprint } else { $null }
        public_key_file_match_by_scope = $grantFileEnvMatch
        private_key_path = $grantPrivateKey
        public_key_path = $grantPublicKey
    }
    acl_review = $aclInventory
    registry_checks = $registryChecks
    local_related_windows_services = $localServices
    independent_administration_verified = $false
    source_services_operational_verified = $false
    promotion_remote_trust_anchor_mismatch_resolved = $false
    production_grant_issuance_authorized = $false
    grant_issued = $false
    orders_submitted = $false
    demo_trading_authorized = $false
    live_trading_allowed = $false
    note = 'ACL rules are not a Windows effective-access calculation. No key values, private-key bytes or passphrases are printed or loaded.'
}
$report | ConvertTo-Json -Depth 12
exit 0
