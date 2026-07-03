param(
    [Parameter(Mandatory=$true)]
    [string]$SpaceUrl,

    [Parameter(Mandatory=$true)]
    [string]$VercelUrl
)

$ErrorActionPreference = "Stop"

function Normalize-Origin([string]$Url) {
    return $Url.TrimEnd("/")
}

function Assert-Status([string]$Label, [scriptblock]$Request) {
    try {
        $result = & $Request
        Write-Host "ok: $Label"
        return $result
    } catch {
        throw "failed: $Label - $($_.Exception.Message)"
    }
}

$space = Normalize-Origin $SpaceUrl
$vercel = Normalize-Origin $VercelUrl
$foreignOrigin = "https://example.invalid"

Assert-Status "Vercel landing" {
    Invoke-WebRequest -Uri $vercel -Method Get -UseBasicParsing
} | Out-Null

Assert-Status "Vercel tool page" {
    Invoke-WebRequest -Uri "$vercel/app" -Method Get -UseBasicParsing
} | Out-Null

$health = Assert-Status "Space health" {
    Invoke-RestMethod -Uri "$space/api/v1/health" -Method Get
}
if (-not $health.asr_ready) {
    throw "failed: Space health returned asr_ready=false"
}

$allowed = Assert-Status "CORS allows Vercel origin" {
    Invoke-WebRequest `
        -Uri "$space/api/v1/soap-notes" `
        -Method Options `
        -Headers @{
            Origin = $vercel
            "Access-Control-Request-Method" = "POST"
        } `
        -UseBasicParsing
}
if ($allowed.Headers["Access-Control-Allow-Origin"] -ne $vercel) {
    throw "failed: CORS did not echo Vercel origin"
}

try {
    $blocked = Invoke-WebRequest `
        -Uri "$space/api/v1/health" `
        -Method Get `
        -Headers @{
            Origin = $foreignOrigin
        } `
        -UseBasicParsing
    if ($blocked.Headers["Access-Control-Allow-Origin"]) {
        throw "CORS echoed unexpected origin $foreignOrigin"
    }
} catch {
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode.value__ -eq 400) {
        Write-Host "ok: CORS rejects foreign origin"
    } else {
        throw
    }
}

Write-Host "ok: Goal 5 deploy checks passed"
