# build_installer.ps1
# One-click script: installs PyInstaller, builds the exe, then runs Inno Setup.
#
# Usage (from project root in PowerShell):
#   .\build_installer.ps1
#
# Prerequisites:
#   - Python venv at .\venv\  (already set up)
#   - Inno Setup installed at default path  OR  set $InnoSetup below

param(
    [string]$InnoSetup = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = $PSScriptRoot

function Step($msg) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

# ── Step 1: Install / upgrade PyInstaller ──────────────────────────────────
Step "1/4  Installing PyInstaller into venv"
& "$Root\venv\Scripts\pip.exe" install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { throw "pip install pyinstaller failed" }

# ── Step 2: Clean previous build ──────────────────────────────────────────
Step "2/4  Cleaning previous build artefacts"
$toRemove = @("$Root\dist", "$Root\build", "$Root\installer_output")
foreach ($d in $toRemove) {
    if (Test-Path $d) {
        Remove-Item -Recurse -Force $d
        Write-Host "  Removed $d"
    }
}

# ── Step 3: PyInstaller — build the exe folder ────────────────────────────
Step "3/4  Running PyInstaller (this takes 1-3 minutes)"
& "$Root\venv\Scripts\pyinstaller.exe" "$Root\build.spec" --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$exePath = "$Root\dist\Tadris_QA\Tadris_QA.exe"
if (-not (Test-Path $exePath)) {
    throw "Expected exe not found at: $exePath"
}
Write-Host "  EXE built: $exePath" -ForegroundColor Green

# ── Step 4: Inno Setup — wrap into installer ──────────────────────────────
Step "4/4  Running Inno Setup compiler"

if (-not (Test-Path $InnoSetup)) {
    Write-Host ""
    Write-Host "  ⚠  Inno Setup not found at:" -ForegroundColor Yellow
    Write-Host "     $InnoSetup" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Download and install it from:" -ForegroundColor Yellow
    Write-Host "  https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Then re-run this script, or compile manually:" -ForegroundColor Yellow
    Write-Host "  iscc installer.iss" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  The PyInstaller output is ready at:" -ForegroundColor Green
    Write-Host "  $Root\dist\Tadris_QA\" -ForegroundColor Green
    exit 0
}

New-Item -ItemType Directory -Path "$Root\installer_output" -Force | Out-Null
& $InnoSetup "$Root\installer.iss"
if ($LASTEXITCODE -ne 0) { throw "Inno Setup compilation failed" }

$installer = Get-ChildItem "$Root\installer_output\*.exe" | Select-Object -First 1
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  ✅  Installer ready:" -ForegroundColor Green
Write-Host "  $($installer.FullName)" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
