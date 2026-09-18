$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ProductName = "YuTanRadar"
$ProductExe = "$ProductName.exe"
$Release = Join-Path $Root "release\$ProductName"
if (-not (Test-Path (Join-Path $Release $ProductExe))) {
    throw "Release package not found. Run windows\build_windows.ps1 first."
}
Set-Location $Release
Start-Process -FilePath (Join-Path $Release $ProductExe) -WorkingDirectory $Release
Write-Host "YuTanRadar started. Open http://127.0.0.1:8000 if the browser does not open automatically." -ForegroundColor Green
