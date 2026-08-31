<#
.SYNOPSIS
Controleert of het FNO-project gereed is voor commit.

.DESCRIPTION
Voert de standaard kwaliteitscontrole uit:

- Git status
- Ruff check
- Ruff format
- Pytest

Bij een fout stopt het script direct.

Gebruik:

    .\tools\verify_project.ps1
#>

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

function Invoke-Step {
    param(
        [string]$Title,
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "===================================================="
    Write-Host $Title
    Write-Host "===================================================="

    & $Action

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Mislukt: $Title" -ForegroundColor Red
        exit $LASTEXITCODE
    }

    Write-Host "✔ Gereed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Foto Nummeraar Online"
Write-Host "Projectcontrole"
Write-Host ""

Invoke-Step "Git status" {
    git status
}

Invoke-Step "Ruff check" {
    ruff check .
}

Invoke-Step "Ruff formatter" {
    ruff format .
}

Invoke-Step "Pytest" {
    pytest
}

Write-Host ""
Write-Host "===================================================="
Write-Host "PROJECT GEREED VOOR COMMIT"
Write-Host "====================================================" -ForegroundColor Green

Write-Host ""
Write-Host "Volgende stappen:"
Write-Host ""

Write-Host "git add ."
Write-Host 'git commit -m "..."'
Write-Host "git push"

Write-Host ""