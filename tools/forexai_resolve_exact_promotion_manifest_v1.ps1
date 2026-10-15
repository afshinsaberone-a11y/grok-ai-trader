[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) {
    throw 'G13_EXACT_PROMOTION_SOURCE_ROOT_MISSING'
}
if ([string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN) -or
    [string]::IsNullOrWhiteSpace($env:GITHUB_REPOSITORY) -or
    [string]::IsNullOrWhiteSpace($env:RUNNER_TEMP)) {
    throw 'G13_EXACT_PROMOTION_GITHUB_ENVIRONMENT_MISSING'
}

$headers = @{
    Authorization = "Bearer $env:GITHUB_TOKEN"
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
}

# The first checkout is pinned to trusted main. Bind this compile check to
# that SHA, not to a manifest committed in the feature branch.
# The persistent self-hosted runner may own its checkout as another service identity.
# Trust this exact freshly checked-out workspace for this single read-only Git command;
# do not change the runner account's global Git safe.directory configuration.
$trustedMainRoot = [System.IO.Path]::GetFullPath($env:GITHUB_WORKSPACE)
$trustedMainSha = (& git -c "safe.directory=$trustedMainRoot" -C $trustedMainRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $trustedMainSha -notmatch '^[0-9a-f]{40}$') {
    throw 'G13_EXACT_PROMOTION_TRUSTED_MAIN_SHA_UNRESOLVED'
}

$repo = $env:GITHUB_REPOSITORY
$runsUri = "https://api.github.com/repos/$repo/actions/workflows/forexai-g13-promotion-m15.yml/runs?branch=main&status=completed&per_page=100"
$runsResponse = Invoke-RestMethod -Method Get -Uri $runsUri -Headers $headers
$matchingRuns = @(
    $runsResponse.workflow_runs |
        Where-Object {
            $_.name -eq 'ForexAI G13 Final Promotion M15' -and
            $_.workflow_id -eq 356366824 -and
            $_.head_branch -eq 'main' -and
            $_.head_sha -eq $trustedMainSha -and
            $_.status -eq 'completed' -and
            $_.conclusion -eq 'success'
        } |
        Sort-Object -Property id -Descending
)
if ($matchingRuns.Count -lt 1) {
    throw "G13_EXACT_PROMOTION_RUN_NOT_FOUND:$trustedMainSha"
}
$promotionRun = $matchingRuns[0]

$artifactsUri = "https://api.github.com/repos/$repo/actions/runs/$($promotionRun.id)/artifacts?per_page=100"
$artifactResponse = Invoke-RestMethod -Method Get -Uri $artifactsUri -Headers $headers
$manifestArtifacts = @(
    $artifactResponse.artifacts |
        Where-Object { $_.name -eq 'g13-promotion-manifest-m15' -and -not $_.expired }
)
if ($manifestArtifacts.Count -ne 1) {
    throw "G13_EXACT_PROMOTION_ARTIFACT_COUNT_INVALID:$($manifestArtifacts.Count)"
}
$artifact = $manifestArtifacts[0]
if ([string]$artifact.digest -notmatch '^sha256:[0-9a-fA-F]{64}$') {
    throw 'G13_EXACT_PROMOTION_ARTIFACT_DIGEST_INVALID'
}

$tempRoot = Join-Path $env:RUNNER_TEMP 'g13-exact-main-promotion'
Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$zipPath = Join-Path $tempRoot 'promotion.zip'
$extractPath = Join-Path $tempRoot 'extracted'
$downloadUri = "https://api.github.com/repos/$repo/actions/artifacts/$($artifact.id)/zip"
Invoke-WebRequest -UseBasicParsing -Method Get -Uri $downloadUri -Headers $headers -OutFile $zipPath | Out-Null

$actualDigest = 'sha256:' + (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not [string]::Equals(
    $actualDigest,
    [string]$artifact.digest,
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    throw "G13_EXACT_PROMOTION_ARTIFACT_DIGEST_MISMATCH:$actualDigest"
}

Expand-Archive -LiteralPath $zipPath -DestinationPath $extractPath -Force
$manifestFiles = @(
    Get-ChildItem -LiteralPath $extractPath -Recurse -File -Filter 'g13-promotion-manifest-m15.json'
)
if ($manifestFiles.Count -ne 1) {
    throw "G13_EXACT_PROMOTION_MANIFEST_FILE_COUNT_INVALID:$($manifestFiles.Count)"
}
$manifest = Get-Content -LiteralPath $manifestFiles[0].FullName -Raw | ConvertFrom-Json

if ($manifest.schema_version -ne 'forexai.g13.promotion_manifest.m15.v1' -or
    $manifest.status -ne 'PROMOTION_READY' -or
    $manifest.symbol -ne 'EURUSD' -or
    $manifest.timeframe -ne 'M15' -or
    $manifest.decision_policy.ea_generation_allowed -ne $true -or
    $manifest.decision_policy.demo_trading_allowed -ne $false -or
    $manifest.decision_policy.live_trading_allowed -ne $false) {
    throw 'G13_EXACT_PROMOTION_MANIFEST_POLICY_INVALID'
}

$promotedIds = @($manifest.promoted_candidate_ids | ForEach-Object { [int]$_ })
$candidateIds = @($manifest.candidates | ForEach-Object { [int]$_.candidate_id })
$uniqueIds = @($promotedIds | Sort-Object -Unique)
$sortedPromotedIds = @($promotedIds | Sort-Object)
$sortedCandidateIds = @($candidateIds | Sort-Object)
$setDifference = @(
    Compare-Object -ReferenceObject $sortedPromotedIds -DifferenceObject $sortedCandidateIds
)
if ($promotedIds.Count -lt 1 -or
    $promotedIds.Count -ne $uniqueIds.Count -or
    $setDifference.Count -ne 0 -or
    [int]$manifest.counts.promoted -ne $promotedIds.Count) {
    throw 'G13_EXACT_PROMOTION_CANDIDATE_SET_INVALID'
}

$targetManifest = Join-Path $SourceRoot 'artifacts\g13\g13-promotion-manifest-m15.json'
if (-not (Test-Path -LiteralPath (Split-Path -Parent $targetManifest) -PathType Container)) {
    throw 'G13_EXACT_PROMOTION_TARGET_DIRECTORY_MISSING'
}
Copy-Item -LiteralPath $manifestFiles[0].FullName -Destination $targetManifest -Force

"EXPECTED_G13_CANDIDATE_COUNT=$($promotedIds.Count)" |
    Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"G13_PROMOTION_RUN_ID=$($promotionRun.id)" |
    Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"G13_PROMOTION_ARTIFACT_DIGEST=$actualDigest" |
    Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"Promotion run: $($promotionRun.id) (main SHA $trustedMainSha)" |
    Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append
"Verified artifact SHA-256: $actualDigest" |
    Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append
"Promoted candidate count: $($promotedIds.Count)" |
    Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append
Write-Output "G13_EXACT_PROMOTION_ARTIFACT_VERIFIED=true run=$($promotionRun.id) count=$($promotedIds.Count) digest=$actualDigest"
