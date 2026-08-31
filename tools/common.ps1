<#+
.SYNOPSIS
Gedeelde hulpfuncties voor de lokale FNO-ontwikkeltools.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-FnoProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Get-FnoPython {
    $projectRoot = Get-FnoProjectRoot
    $venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

    if (Test-Path $venvPython) {
        return $venvPython
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        throw "Python is niet gevonden. Maak of activeer eerst de virtuele omgeving."
    }

    return $python.Source
}

function Invoke-FnoFlask {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $projectRoot = Get-FnoProjectRoot
    $python = Get-FnoPython

    Push-Location $projectRoot
    try {
        & $python -m flask @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Flask-commando is mislukt: flask $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Get-FnoDatabasePath {
    $projectRoot = Get-FnoProjectRoot
    $envFile = Join-Path $projectRoot ".env"

    if (Test-Path $envFile) {
        $databaseLine = Get-Content $envFile |
            Where-Object { $_ -match '^\s*DATABASE_URL\s*=' } |
            Select-Object -Last 1

        if ($databaseLine) {
            $databaseUrl = ($databaseLine -split '=', 2)[1].Trim().Trim('"').Trim("'")

            if ($databaseUrl -and -not $databaseUrl.StartsWith("sqlite:///")) {
                throw (
                    "Deze tool ondersteunt uitsluitend een lokale SQLite-database. " +
                    "De ingestelde DATABASE_URL is: $databaseUrl"
                )
            }

            if ($databaseUrl) {
                $databaseValue = $databaseUrl.Substring("sqlite:///".Length)
                if ([System.IO.Path]::IsPathRooted($databaseValue)) {
                    return [System.IO.Path]::GetFullPath($databaseValue)
                }

                return [System.IO.Path]::GetFullPath(
                    (Join-Path $projectRoot $databaseValue)
                )
            }
        }
    }

    return Join-Path $projectRoot "instance\fno.db"
}

function Get-FnoBackupDirectory {
    $projectRoot = Get-FnoProjectRoot
    $backupDirectory = Join-Path $projectRoot "backups"
    New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
    return $backupDirectory
}

function New-FnoDatabaseBackup {
    param(
        [string]$Reason = "manual"
    )

    $databasePath = Get-FnoDatabasePath
    if (-not (Test-Path $databasePath)) {
        return $null
    }

    $backupDirectory = Get-FnoBackupDirectory
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $safeReason = $Reason -replace '[^a-zA-Z0-9_-]', '_'
    $backupPath = Join-Path $backupDirectory "fno_${timestamp}_${safeReason}.db"

    Copy-Item -Path $databasePath -Destination $backupPath -Force
    return $backupPath
}

function Confirm-FnoAction {
    param(
        [Parameter(Mandatory)]
        [string]$Message,
        [string]$RequiredText = "JA"
    )

    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    $answer = Read-Host "Typ $RequiredText om door te gaan"
    return $answer -ceq $RequiredText
}
