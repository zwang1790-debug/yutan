$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$BuildCache = Join-Path $Root "build-cache\windows"
New-Item -ItemType Directory -Force $BuildCache | Out-Null
# Keep npm, pip, and PyInstaller temporary files off the nearly-full system drive.
$env:TEMP = $BuildCache
$env:TMP = $BuildCache
$env:PIP_CACHE_DIR = Join-Path $BuildCache "pip-cache"
$ProductName = "YuTanRadar"
$ProductExe = "$ProductName.exe"
$ReleaseRoot = Join-Path $Root "release"
$Release = Join-Path $ReleaseRoot $ProductName

Write-Host "[1/5] Checking required tools..." -ForegroundColor Cyan
if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.10+ was not found. Install Python from python.org or winget."
}
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "npm was not found. Install Node.js LTS." }

Write-Host "[2/5] Building the Vue frontend..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "web-ui")
npm ci
if ($LASTEXITCODE -ne 0) { throw "npm ci failed with exit code $LASTEXITCODE." }
npm run build
if ($LASTEXITCODE -ne 0) { throw "npm run build failed with exit code $LASTEXITCODE." }
Pop-Location

Write-Host "[3/5] Preparing the build environment..." -ForegroundColor Cyan
$Venv = Join-Path $Root ".venv-windows-build"
$PythonLauncher = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($Version in @('3.13', '3.12', '3.11', '3.10')) {
        & py -$Version -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $PythonLauncher = @('py', "-$Version"); break }
    }
}
if (-not $PythonLauncher) {
    $PythonLauncher = @((Get-Command python).Source, $null)
}
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }
    if ($PythonLauncher[1]) {
        & $PythonLauncher[0] $PythonLauncher[1] -m venv $Venv
    } else {
        & $PythonLauncher[0] -m venv $Venv
    }
}
$Python = Join-Path $Venv "Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements-runtime.txt pyinstaller
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $Root ".playwright-browsers"
& $Python -m playwright install chromium

Write-Host "[4/5] Building the Windows onedir package..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build-output")
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build-work")
$BuildDist = Join-Path $Root "build-output"
$BuildWork = Join-Path $Root "build-work"
& $Python -m PyInstaller --noconfirm --clean --distpath $BuildDist --workpath $BuildWork windows\ai-goofish-monitor.spec

Write-Host "[5/5] Creating first-run folders and package metadata..." -ForegroundColor Cyan
$BuiltPackage = Join-Path $Root "build-output\$ProductName"
New-Item -ItemType Directory -Force $ReleaseRoot | Out-Null

# Refresh only generated application files. Persistent user data and .env stay in place.
foreach ($path in @(
    (Join-Path $Release "_internal"),
    (Join-Path $Release ".playwright-browsers"),
    (Join-Path $Release "dist"),
    (Join-Path $Release "static"),
    (Join-Path $Release "prompts"),
    (Join-Path $Release $ProductExe),
    (Join-Path $Release "config.json.example"),
    (Join-Path $Release ".env.example"),
    (Join-Path $Release "FIRST_RUN.txt")
)) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $path
}

New-Item -ItemType Directory -Force $Release | Out-Null
Copy-Item -Recurse -Force (Join-Path $BuiltPackage "_internal") $Release
Copy-Item -Force (Join-Path $BuiltPackage $ProductExe) $Release
foreach ($dir in @('data','state','logs','images','jsonl','price_history')) { New-Item -ItemType Directory -Force (Join-Path $Release $dir) | Out-Null }
foreach ($resource in @('dist', 'static', 'prompts')) {
    Copy-Item -Recurse -Force (Join-Path $Root $resource) (Join-Path $Release $resource)
}
Copy-Item -Force (Join-Path $Root "config.json.example") $Release
Copy-Item -Force (Join-Path $Root ".env.example") $Release
if (Test-Path (Join-Path $Root ".playwright-browsers")) {
    Copy-Item -Recurse -Force (Join-Path $Root ".playwright-browsers") (Join-Path $Release ".playwright-browsers")
} else {
    throw "Playwright browsers were not found. Run 'python -m playwright install chromium' first."
}
Copy-Item -Force (Join-Path $Root "windows\FIRST_RUN.txt") (Join-Path $Release "FIRST_RUN.txt")
Write-Host "Build complete: $Release" -ForegroundColor Green
