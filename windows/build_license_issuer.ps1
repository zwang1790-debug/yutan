$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$BuildCache = Join-Path $Root "build-cache\license-issuer"
New-Item -ItemType Directory -Force $BuildCache | Out-Null
# Keep pip and PyInstaller temporary files off the system drive.
$env:TEMP = $BuildCache
$env:TMP = $BuildCache
$env:PIP_CACHE_DIR = Join-Path $BuildCache "pip-cache"
$Python = Join-Path $Root ".venv-windows-build\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $Python -or -not (Test-Path $Python)) {
    throw "Python was not found. Install Python 3.10+ first."
}

Write-Host "[1/4] Checking build dependencies..." -ForegroundColor Cyan
& $Python -m pip install --disable-pip-version-check --quiet cryptography pyinstaller
if ($LASTEXITCODE -ne 0) { throw "Could not install the license issuer build dependencies." }

& $Python -c "import tkinter, cryptography; print('Python dependencies: PASS')"
if ($LASTEXITCODE -ne 0) { throw "Tkinter or cryptography is unavailable." }

$BuildWork = Join-Path $Root "build-license-issuer"
$BuildDist = Join-Path $Root "dist-license-issuer"
$Output = Join-Path $Root "release\license-issuer"

Write-Host "[2/4] Building the seller-only license issuer..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $BuildWork
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $BuildDist
& $Python -m PyInstaller --noconfirm --clean --distpath $BuildDist --workpath $BuildWork windows\license_issuer.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE." }

Write-Host "[3/4] Preparing the seller tool folder..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force $Output | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Output "YuTanRadar-LicenseIssuer.exe")
Copy-Item -Force (Join-Path $BuildDist "YuTanRadar-LicenseIssuer.exe") $Output
$OutputKeys = Join-Path $Output "license-keys"
New-Item -ItemType Directory -Force $OutputKeys | Out-Null
$SellerKey = Join-Path $Root "license-keys\private.key"
if (-not (Test-Path $SellerKey)) {
    throw "Seller private key was not found: $SellerKey"
}
# This is a seller-only package. The customer application package never receives this key.
Copy-Item -Force $SellerKey (Join-Path $OutputKeys "private.key")

$Readme = Join-Path $Output "README.txt"
@"
鱼探 Radar 授权码签发工具

使用方法：
1. 将卖家私钥文件 private.key 放入 license-keys 文件夹。
2. 双击 YuTanRadar-LicenseIssuer.exe。
3. 输入客户设备指纹，选择套餐和有效期，然后生成授权码。

安全提醒：
- private.key 只保存在卖家电脑，绝不能发给客户。
- 不要把 license-keys 文件夹加入客户安装包或上传到 Git。
- 如果默认私钥路径不存在，也可以在程序中手动选择私钥文件。
"@ | Set-Content -Path $Readme -Encoding UTF8

Write-Host "[4/4] Verifying the package..." -ForegroundColor Cyan
$Exe = Join-Path $Output "YuTanRadar-LicenseIssuer.exe"
if (-not (Test-Path $Exe)) { throw "License issuer executable was not created." }
$KeyInSellerPackage = Join-Path $Output "license-keys\private.key"
if (-not (Test-Path $KeyInSellerPackage)) {
    throw "Seller private key was not copied into the issuer package."
}

Write-Host "License issuer created: $Exe" -ForegroundColor Green
