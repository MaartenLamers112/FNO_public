<#
.SYNOPSIS
Maakt een platformonafhankelijke support-ZIP van het FNO-project.

.DESCRIPTION
Kopieert het project naar een tijdelijke map, verwijdert lokale en
gevoelige bestanden en maakt met tar.exe een ZIP met POSIX-paden.

Gebruik vanuit de FNO-projectmap:

    .\tools\create_support_zip.ps1

Resultaat:

    FNO_Support_YYYYMMDD_HHMMSS.zip
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$projectName = Split-Path $projectRoot -Leaf
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$tempBase = Join-Path $env:TEMP "fno-support-$timestamp"
$tempProject = Join-Path $tempBase $projectName
$zipFile = Join-Path (Split-Path $projectRoot -Parent) `
    "FNO_Support_$timestamp.zip"

$excludedDirectoryNames = @(
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".vscode",
    ".idea",
    "node_modules",
    "logs",
    "instance",
    "htmlcov",
    "backups",
    "ai_benchmark_output",
    "ai_benchmark_output_v2"
)

$excludedFileNames = @(
    ".env",
    ".coverage"
)

$excludedExtensions = @(
    ".pyc",
    ".pyo",
    ".log",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".zip"
)

function Test-IsExcludedDirectoryName {
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    return (
        $Name -in $excludedDirectoryNames -or
        $Name -like ".venv*"
    )
}

function Remove-ExcludedContent {
    param(
        [Parameter(Mandatory)]
        [string]$Root
    )

    Get-ChildItem `
        -Path $Root `
        -Recurse `
        -Directory `
        -Force `
        -ErrorAction SilentlyContinue |
    Where-Object {
        Test-IsExcludedDirectoryName -Name $_.Name
    } |
    Sort-Object FullName -Descending |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Get-ChildItem `
        -Path $Root `
        -Recurse `
        -File `
        -Force `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -in $excludedFileNames -or
        $_.Extension -in $excludedExtensions
    } |
    Remove-Item -Force -ErrorAction SilentlyContinue
}

try {
    Write-Host ""
    Write-Host "FNO support-ZIP maken"
    Write-Host "====================="
    Write-Host ""

    if (-not (Get-Command tar.exe -ErrorAction SilentlyContinue)) {
        throw "tar.exe is niet beschikbaar op dit systeem."
    }

    New-Item -ItemType Directory -Path $tempProject -Force |
        Out-Null

    Write-Host "Project kopiëren..."

    Get-ChildItem -Path $projectRoot -Force |
    ForEach-Object {
        if (
            -not (Test-IsExcludedDirectoryName -Name $_.Name) -and
            $_.Name -notin $excludedFileNames
        ) {
            Copy-Item `
                -Path $_.FullName `
                -Destination $tempProject `
                -Recurse `
                -Force
        }
    }

    Write-Host "Lokale bestanden verwijderen..."
    Remove-ExcludedContent -Root $tempProject

    $sourceFiles = @(
        Get-ChildItem `
            -Path $tempProject `
            -Recurse `
            -File `
            -Force
    )

    if ($sourceFiles.Count -eq 0) {
        throw "De tijdelijke projectmap bevat geen bestanden."
    }

    if (Test-Path $zipFile) {
        Remove-Item $zipFile -Force
    }

    Write-Host "Platformonafhankelijke ZIP maken..."

    & tar.exe `
        -a `
        -c `
        -f $zipFile `
        -C $tempProject `
        .

    if ($LASTEXITCODE -ne 0) {
        throw "tar.exe kon de ZIP niet maken."
    }

    if (-not (Test-Path $zipFile)) {
        throw "Het ZIP-bestand is niet aangemaakt."
    }

    $archiveEntries = @(& tar.exe -t -f $zipFile)

    if ($LASTEXITCODE -ne 0) {
        throw "Het aangemaakte ZIP-bestand kon niet worden gecontroleerd."
    }

    $requiredEntries = @(
        "./app/",
        "./tests/",
        "./tools/",
        "./requirements.txt"
    )

    foreach ($requiredEntry in $requiredEntries) {
        $found = $archiveEntries |
            Where-Object {
                $_.Replace("\", "/").StartsWith($requiredEntry)
            }

        if (-not $found) {
            throw "Verplicht onderdeel ontbreekt in de ZIP: $requiredEntry"
        }
    }

    $sourceSize = ($sourceFiles | Measure-Object Length -Sum).Sum
    $zipSize = (Get-Item $zipFile).Length

    Write-Host ""
    Write-Host "Klaar." -ForegroundColor Green
    Write-Host ""
    Write-Host "ZIP:"
    Write-Host $zipFile
    Write-Host ("Bronbestanden: {0}" -f $sourceFiles.Count)
    Write-Host ("Ongecomprimeerd: {0:N2} MB" -f ($sourceSize / 1MB))
    Write-Host ("ZIP-grootte: {0:N2} MB" -f ($zipSize / 1MB))
    Write-Host ("ZIP-items: {0}" -f $archiveEntries.Count)
    Write-Host ""
}
finally {
    if (Test-Path $tempBase) {
        Remove-Item $tempBase -Recurse -Force
    }
}
