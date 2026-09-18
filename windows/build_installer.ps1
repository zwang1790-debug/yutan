$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$ProductName = "YuTanRadar"
$ProductExe = "$ProductName.exe"
$Release = Join-Path $Root "release\$ProductName"

if (-not (Test-Path (Join-Path $Release $ProductExe))) {
    throw "Release package not found. Run windows\build_windows.ps1 first."
}

$Candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\InnoSetup6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$Iscc = $Candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $Iscc) {
    throw "Inno Setup 6 was not found. Install it, then run this script again."
}

& $Iscc (Join-Path $Root "windows\installer.iss")
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE." }

Write-Host "Installer created under $Root\release" -ForegroundColor Green
