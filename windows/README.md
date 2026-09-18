# 鱼探 Radar Windows 本地版交付

## 构建

在项目根目录使用 PowerShell 执行：

```powershell
.\windows\build_windows.ps1
```

构建完成后，交付目录为 `release\YuTanRadar`。该目录是 Windows onedir 便携版，包含可执行文件和运行资源。

构建过程会把 PyInstaller 临时产物放在 `build-output` 和 `build-work`，不会与前端的 `dist` 目录混用。

## 运行

```powershell
.\windows\run_windows.ps1
```

也可以直接双击 `release\YuTanRadar\YuTanRadar.exe`。

## 授权交付

首次启动默认开启 7 天试用。正式授权时，让客户在“设备授权”页复制设备指纹，卖家使用仓库外的私钥签发授权码；客户粘贴授权码后即可在本机使用。私钥绝不能进入安装包、客户备份或 Git 仓库。

卖家不需要每次使用命令行。双击执行：

```powershell
.\windows\open_license_issuer.ps1
```

更推荐直接双击 `windows\open_license_issuer.bat`，从任意目录启动都可以，不会受当前命令提示符目录影响。也可以在项目根目录运行 `python tools\license_issuer_gui.pyw`。工具支持选择私钥、输入设备指纹、选择套餐和有效期，并自动复制授权码。该工具只放在卖家授权电脑上，不要随客户安装包一起交付。

如需生成独立的卖家专用 exe，在项目根目录执行：

```powershell
.\windows\build_license_issuer.ps1
```

生成目录为 `release\license-issuer`，双击其中的 `YuTanRadar-LicenseIssuer.exe` 即可。请把私钥放在该目录的 `license-keys\private.key`，不要把整个卖家工具目录交付给客户。

## 生成安装包

先安装 Inno Setup 6，然后执行：

```powershell
.\windows\build_installer.ps1
```

安装包会生成在 `release` 目录，默认安装到当前用户可写的 `%LOCALAPPDATA%\Programs\YuTanRadar`。升级或卸载时默认保留 `data`、`state`、`logs`、`images`、`jsonl` 和 `price_history`，避免误删客户登录态和历史结果。

## 交付建议

- 首批客户交付整个 `YuTanRadar` 文件夹并附带 `FIRST_RUN.txt`。
- 不要把开发机的 `.env`、`state`、`data`、`logs` 和 `images` 一起打包。
- 后续增加授权码时，授权校验应放在本地启动流程和关键 API 两处，而不是只在前端隐藏按钮。
- 当前先采用便携目录版；用户数量稳定后，再用 Inno Setup 或 WiX 包装安装、卸载和桌面快捷方式。
- 当前已提供 Inno Setup 脚本；正式发版前建议给安装包签名，并在干净 Windows 虚拟机验证安装、升级、卸载和数据保留。
