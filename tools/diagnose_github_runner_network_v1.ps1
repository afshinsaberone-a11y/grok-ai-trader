[CmdletBinding()]
param(
    [ValidateRange(3, 30)]
    [int]$TimeoutSeconds = 10
)

# Read-only outbound HTTPS diagnostic for a self-hosted GitHub Actions runner.
# It sends no authorization headers, reads no environment secrets, and changes
# no files, services, firewall rules, runner settings, or trading permissions.
$ErrorActionPreference = 'Stop'
$schema = 'forexai.github_runner_network_diagnostic.v1'

$targets = @(
    [PSCustomObject]@{
        label = 'github-web'
        url = 'https://github.com/'
        codeload_required = $false
    },
    [PSCustomObject]@{
        label = 'github-api'
        url = 'https://api.github.com/'
        codeload_required = $false
    },
    [PSCustomObject]@{
        label = 'checkout-action-archive'
        url = 'https://codeload.github.com/actions/checkout/zip/11d5960a326750d5838078e36cf38b85af677262'
        codeload_required = $true
    },
    [PSCustomObject]@{
        label = 'download-artifact-action-archive'
        url = 'https://codeload.github.com/actions/download-artifact/zip/d3f86a106a0bac45b974a628896c90dbdf5c8093'
        codeload_required = $true
    }
)

function Test-HttpsTarget {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][int]$Timeout
    )

    $uri = [Uri]$Url
    $dnsStatus = 'PASS'
    try {
        $addresses = [System.Net.Dns]::GetHostAddresses($uri.DnsSafeHost)
        if ($addresses.Count -eq 0) { $dnsStatus = 'NO_ADDRESSES' }
    }
    catch {
        return [PSCustomObject]@{
            target = $Label
            host = $uri.DnsSafeHost
            dns_status = 'FAILED'
            https_status = 'NOT_TESTED'
            http_status_code = $null
            elapsed_ms = 0
        }
    }

    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $httpStatus = 'FAILED'
    $statusCode = $null
    $response = $null
    try {
        $request = [System.Net.HttpWebRequest]::Create($uri)
        $request.Method = 'HEAD'
        $request.Timeout = $Timeout * 1000
        $request.ReadWriteTimeout = $Timeout * 1000
        $request.AllowAutoRedirect = $true
        $request.MaximumAutomaticRedirections = 8
        $request.UserAgent = 'ForexAI-GitHub-Runner-Network-Diagnostic/1.0'
        # Do not attach GitHub tokens, cookies, proxy credentials, or environment values.
        $response = $request.GetResponse()
        $statusCode = [int]$response.StatusCode
        if ($statusCode -ge 200 -and $statusCode -lt 400) {
            $httpStatus = 'PASS'
        }
        else {
            $httpStatus = 'HTTP_STATUS_NOT_ACCEPTED'
        }
    }
    catch [System.Net.WebException] {
        if ($null -ne $_.Exception.Response) {
            $response = $_.Exception.Response
            try { $statusCode = [int]$response.StatusCode } catch { $statusCode = $null }
            $httpStatus = if ($null -ne $statusCode) {
                "HTTP_STATUS_$statusCode"
            } else {
                'HTTP_RESPONSE_ERROR'
            }
        }
        elseif ($_.Exception.Status -eq [System.Net.WebExceptionStatus]::Timeout) {
            $httpStatus = 'TIMEOUT'
        }
        else {
            $httpStatus = 'HTTPS_FAILED'
        }
    }
    catch {
        $httpStatus = 'HTTPS_FAILED'
    }
    finally {
        if ($null -ne $response) { $response.Close() }
        $watch.Stop()
    }

    return [PSCustomObject]@{
        target = $Label
        host = $uri.DnsSafeHost
        dns_status = $dnsStatus
        https_status = $httpStatus
        http_status_code = $statusCode
        elapsed_ms = [long]$watch.ElapsedMilliseconds
    }
}

$results = @()
foreach ($target in $targets) {
    $results += Test-HttpsTarget -Label $target.label -Url $target.url -Timeout $TimeoutSeconds
}

$codeloadResults = @($results | Where-Object {
    $_.target -in @('checkout-action-archive', 'download-artifact-action-archive')
})
$codeloadPass = $codeloadResults.Count -eq 2 -and @(
    $codeloadResults | Where-Object { $_.dns_status -ne 'PASS' -or $_.https_status -ne 'PASS' }
).Count -eq 0

$report = [PSCustomObject]@{
    schema = $schema
    status = if ($codeloadPass) { 'PASS' } else { 'BLOCKED' }
    read_only = $true
    credentials_sent = $false
    secrets_read = $false
    files_changed = $false
    firewall_changed = $false
    runner_configuration_changed = $false
    orders_submitted = $false
    demo_trading_authorized = $false
    live_trading_allowed = $false
    targets = @($results)
    guidance = if ($codeloadPass) {
        'Codeload HTTPS probes passed. If Actions still time out, inspect runner proxy/TLS and GitHub Actions allow-list logs.'
    } else {
        'Codeload HTTPS is blocked or timing out. Check DNS, outbound TCP 443, TLS inspection/proxy policy, and allow-list codeload.github.com on this runner host.'
    }
}
$report | ConvertTo-Json -Depth 6
if (-not $codeloadPass) { exit 2 }
exit 0
