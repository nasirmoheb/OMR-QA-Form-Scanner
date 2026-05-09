# create_portable_zip.ps1
# Creates a portable ZIP distribution (no installer needed)
#
# Usage:
#   .\create_portable_zip.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot
$Version = "1.0.0"
$OutputName = "OMR_Scanner_Portable_v${Version}.zip"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  Creating Portable ZIP Distribution" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# Check if dist folder exists
$DistFolder = "$Root\dist\OMR_Scanner"
if (-not (Test-Path $DistFolder)) {
    Write-Host ""
    Write-Host "  ❌  Error: dist\OMR_Scanner folder not found" -ForegroundColor Red
    Write-Host "  Run .\build_installer.ps1 first to build the app" -ForegroundColor Yellow
    exit 1
}

# Create output directory
$OutputDir = "$Root\portable_output"
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

# Create ZIP
$ZipPath = "$OutputDir\$OutputName"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

Write-Host ""
Write-Host "  Compressing files..." -ForegroundColor Cyan
Compress-Archive -Path "$DistFolder\*" -DestinationPath $ZipPath -CompressionLevel Optimal

$ZipSize = [math]::Round((Get-Item $ZipPath).Length / 1MB, 2)

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  ✅  Portable ZIP created:" -ForegroundColor Green
Write-Host "  $ZipPath" -ForegroundColor Green
Write-Host "  Size: ${ZipSize} MB" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "  Users can:" -ForegroundColor Cyan
Write-Host "  1. Extract the ZIP to any folder" -ForegroundColor White
Write-Host "  2. Run OMR_Scanner.exe" -ForegroundColor White
Write-Host "  3. No installation required!" -ForegroundColor White
Write-Host ""
