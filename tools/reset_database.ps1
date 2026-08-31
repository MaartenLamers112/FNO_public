<#
.SYNOPSIS
Maakt de lokale FNO-ontwikkeldatabase volledig leeg en opnieuw aan.

.DESCRIPTION
Maakt eerst automatisch een back-up, verwijdert daarna de lokale SQLite-
database, voert alle Alembic-migraties uit en start ten slotte het bestaande
Flask-commando om een beheerder aan te maken.
#>

[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "common.ps1")

$databasePath = Get-FnoDatabasePath

Write-Host ""
Write-Host "FNO-database resetten" -ForegroundColor Cyan
Write-Host "======================"
Write-Host "Database: $databasePath"
Write-Host ""
Write-Host "Hiermee worden alle lokale foto's, labels, namen, opmerkingen," 
Write-Host "metadata, importhistorie en wijzigingshistorie verwijderd."

if (-not (Confirm-FnoAction -Message "Deze actie kan niet ongedaan worden gemaakt zonder back-up.")) {
    Write-Host "Reset geannuleerd."
    exit 0
}

$backupPath = New-FnoDatabaseBackup -Reason "before_reset"
if ($backupPath) {
    Write-Host "Back-up gemaakt: $backupPath" -ForegroundColor Green
}
else {
    Write-Host "Er bestond nog geen database; er is geen back-up gemaakt."
}

if (Test-Path $databasePath) {
    Remove-Item -Path $databasePath -Force
}

$databaseDirectory = Split-Path $databasePath -Parent
New-Item -ItemType Directory -Path $databaseDirectory -Force | Out-Null

Write-Host "Migraties uitvoeren..."
Invoke-FnoFlask -Arguments @("db", "upgrade")

Write-Host ""
Write-Host "Database is opnieuw aangemaakt." -ForegroundColor Green
Write-Host "Maak nu de eerste beheerder aan."
Invoke-FnoFlask -Arguments @("create-admin")

Write-Host ""
Write-Host "Reset voltooid." -ForegroundColor Green
