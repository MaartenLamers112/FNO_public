<#
.SYNOPSIS
Interactief menu voor lokale FNO-ontwikkeltools.

.DESCRIPTION
Start vanuit de projectmap met:

    .\tools\FNO-Tools.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-ToolScript {
    param(
        [Parameter(Mandatory)]
        [string]$ScriptName
    )

    $scriptPath = Join-Path $PSScriptRoot $ScriptName
    if (-not (Test-Path $scriptPath)) {
        throw "Tool niet gevonden: $scriptPath"
    }

    & $scriptPath
}

while ($true) {
    Clear-Host
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host " Foto Nummeraar Online - Tools"
    Write-Host "==================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Support-ZIP maken"
    Write-Host "2. Database resetten"
    Write-Host "3. Beheerder aanmaken"
    Write-Host "4. Database back-uppen"
    Write-Host "5. Database herstellen"
    Write-Host "6. Project controleren (Ruff en Pytest)"
    Write-Host ""
    Write-Host "0. Afsluiten"
    Write-Host ""

    $choice = Read-Host "Maak een keuze"

    try {
        switch ($choice) {
            "1" { Invoke-ToolScript "create_support_zip.ps1" }
            "2" { Invoke-ToolScript "reset_database.ps1" }
            "3" { Invoke-ToolScript "create_admin.ps1" }
            "4" { Invoke-ToolScript "backup_database.ps1" }
            "5" { Invoke-ToolScript "restore_database.ps1" }
            "6" { Invoke-ToolScript "verify_project.ps1" }
            "0" { return }
            default {
                Write-Host "Ongeldige keuze." -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host ""
        Write-Host "Fout: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host ""
    Read-Host "Druk op Enter om terug te keren naar het menu"
}
