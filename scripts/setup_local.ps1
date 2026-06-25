param(
    [string]$Python = "py -3.12"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

function Invoke-SelectedPython {
    param([string[]]$Arguments)

    $parts = $Python.Split(" ", 2, [System.StringSplitOptions]::RemoveEmptyEntries)
    if ($parts.Count -eq 1) {
        & $parts[0] @Arguments
    } else {
        & $parts[0] $parts[1] @Arguments
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed: $Python $($Arguments -join ' ')"
    }
}

function Invoke-Checked {
    param(
        [string]$FilePath,
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $FilePath $($Arguments -join ' ')"
    }
}

Invoke-SelectedPython @(
    "-c",
    "import sys; assert (3, 11) <= sys.version_info[:2] < (3, 14), f'HopeGait needs Python 3.11-3.13, got {sys.version}'"
)

Invoke-SelectedPython @("-m", "venv", ".venv")
Invoke-Checked ".\.venv\Scripts\python.exe" @("-m", "pip", "install", "--upgrade", "pip")
Invoke-Checked ".\.venv\Scripts\python.exe" @("-m", "pip", "install", "-e", ".[dev]")

if (-not (Test-Path ".env")) {
    Copy-Item ".env.local.example" ".env"
}

Invoke-Checked ".\.venv\Scripts\python.exe" @("scripts\smoke_backend.py")

Write-Host ""
Write-Host "Backend setup complete."
Write-Host "Run API: .\scripts\run_api.ps1"
