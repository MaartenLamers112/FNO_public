<#
.SYNOPSIS
Herstelt de lokale FNO-database vanuit een bestaande back-up.
#>

[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "common.ps1")

$databasePath = Get-FnoDatabasePath
$backupDirectory = Get-FnoBackupDirectory
$backups = @(Get-ChildItem -Path $backupDirectory -Filter "*.db" -File |
    Sort-Object LastWriteTime -Descending)

if ($backups.Count -eq 0) {
    throw "Er zijn geen databaseback-ups gevonden in $backupDirectory."
}

Write-Host ""
Write-Host "FNO-database herstellen" -ForegroundColor Cyan
Write-Host "========================"
Write-Host ""

for ($index = 0; $index -lt $backups.Count; $index++) {
    $backup = $backups[$index]
    Write-Host ("{0}. {1} ({2:N2} MB)" -f (
        $index + 1),
        $backup.Name,
        ($backup.Length / 1MB)
    )
}

Write-Host "0. Annuleren"
Write-Host ""
$choice = Read-Host "Kies een back-up"

$selectedNumber = 0
if (-not [int]::TryParse($choice, [ref]$selectedNumber)) {
    throw "Ongeldige keuze."
}

if ($selectedNumber -eq 0) {
    Write-Host "Herstel geannuleerd."
    exit 0
}

if ($selectedNumber -lt 1 -or $selectedNumber -gt $backups.Count) {
    throw "Ongeldige keuze."
}

$selectedBackup = $backups[$selectedNumber - 1]

if (-not (Confirm-FnoAction -Message (
    "De huidige database wordt vervangen door $($selectedBackup.Name)."
))) {
    Write-Host "Herstel geannuleerd."
    exit 0
}

$currentBackup = New-FnoDatabaseBackup -Reason "before_restore"
if ($currentBackup) {
    Write-Host "Back-up van huidige database gemaakt: $currentBackup"
}

$databaseDirectory = Split-Path $databasePath -Parent
New-Item -ItemType Directory -Path $databaseDirectory -Force | Out-Null
Copy-Item -Path $selectedBackup.FullName -Destination $databasePath -Force

Write-Host "Migraties controleren..."
Invoke-FnoFlask -Arguments @("db", "upgrade")

Write-Host ""
Write-Host "Database hersteld vanuit:" -ForegroundColor Green
Write-Host $selectedBackup.FullName
