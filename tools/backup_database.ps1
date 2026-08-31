<#
.SYNOPSIS
Maakt een tijdgestempelde back-up van de lokale FNO-database.
#>

[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "common.ps1")

$backupPath = New-FnoDatabaseBackup -Reason "manual"

if (-not $backupPath) {
    throw "Er is nog geen lokale FNO-database om te back-uppen."
}

Write-Host ""
Write-Host "Databaseback-up gemaakt:" -ForegroundColor Green
Write-Host $backupPath
