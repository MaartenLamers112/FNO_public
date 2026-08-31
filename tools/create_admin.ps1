<#
.SYNOPSIS
Maakt interactief een FNO-beheerder aan.
#>

[CmdletBinding()]
param()

. (Join-Path $PSScriptRoot "common.ps1")

Write-Host ""
Write-Host "FNO-beheerder aanmaken" -ForegroundColor Cyan
Write-Host "======================="
Invoke-FnoFlask -Arguments @("create-admin")
