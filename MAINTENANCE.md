# GitHub 维护手册

本仓库面向鱼探 Radar 的 Windows 商业版交付。源码、安装包和公开说明分开管理：源码进入 Git，Windows 安装包只作为 GitHub Release 附件发布，不把大型二进制文件提交到 `master`。

## 公开入口

- 仓库：<https://github.com/zwang1790-debug/yutan>
- 安装包：<https://github.com/zwang1790-debug/yutan/releases>
- 商务微信：`wgviptop`
- 用户群与更新通知：<https://t.me/+wyTMBj6IuRBjN2U1>

## 每次改动

1. 在功能分支完成改动并检查 `git status`，确认没有 `.env`、`state`、`data`、`logs`、`images`、`license-keys` 或本机登录态。
2. 修改功能对应的测试和文档；产品版本只在 `src/services/release_info_service.py` 的 `VERSION` 维护。
3. 在仓库根目录执行 `python tools/check_release.py`。
4. 运行 `python -m pytest -m "not live"` 和 `npm --prefix web-ui run build`。需要完整依赖时，先按 `requirements-runtime.txt` 安装 Python 依赖，再执行测试。
5. 提交清晰的 commit，推送分支并通过 GitHub Actions 的 `Quality checks`。

## 发布新版本

1. 更新 `VERSION`、`RELEASE_DATE` 和 `release_notes`；同步检查 `windows/installer.iss` 的默认 `AppVersion`。
2. 先执行 `python tools/check_release.py --version 2.1.3`，再运行本地测试和前端构建。
3. 合并到 `master` 后创建一次新的标准版本标签：

   ```powershell
   git tag -a v2.1.3 -m "release: YuTan Radar 2.1.3"
   git push origin master --follow-tags
   ```

4. 标签推送后，`Windows installer release` 会在 Windows runner 上构建前端、PyInstaller 目录包和 Inno Setup 安装包，并自动创建 GitHub Release。
5. 在 Release 页面确认存在 `YuTanRadar-Setup-2.1.3.exe` 和同名 `.sha256` 文件，下载后用 `Get-FileHash` 核对 SHA256。
6. 用干净的 Windows 用户环境验证安装、首次启动、升级和卸载；升级/卸载不得删除 `data`、`state`、`logs`、`images`、`jsonl` 和 `price_history`。

版本号必须使用 `MAJOR.MINOR.PATCH`，已经发布的标签不要复用或强行改写。若发版失败，修复 `master` 后使用新的补丁版本；不要把私钥、授权码、API Key 或客户登录态上传到仓库。

## 日常巡检

- 每次新版本发布后检查 README 的安装包链接、微信号和 Telegram 链接仍然有效。
- 检查 GitHub Actions 的 `Quality checks` 与 `Windows installer release` 均为绿色。
- 检查 Release 资产名称、版本号和 SHA256 文件一致。
- 发现严重问题时，先在 Release 说明中标记受影响版本，再发布修复版本；保留历史 Release 便于客户回滚。

## 凭证与权限

GitHub 登录凭证只保存在本机 Git Credential Manager 或 GitHub CLI 中，不要写入脚本、README、Issue 或聊天记录。仓库 Actions 只使用 `contents: write` 发布 Release；卖家授权私钥继续放在仓库外的 `license-keys/private.key`。
