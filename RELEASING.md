# 发布 Windows 安装包

Windows 安装包通过 GitHub Actions 自动构建并发布到本仓库的 Releases 页面，不提交到源码仓库。

## 发布新版本

1. 在 `src/services/release_info_service.py` 更新 `VERSION` 和 `RELEASE_DATE`，并补充发布说明。
2. 提交并推送代码到 `master`。
3. 创建并推送符合 `v主版本.次版本.修订版本` 格式的标签，例如：

   ```bash
   git tag v2.1.2
   git push origin v2.1.2
   ```

4. GitHub Actions 会在 Windows runner 上构建安装包，生成 SHA256 文件，并创建对应的 GitHub Release。
5. 在仓库的 **Releases** 页面复制安装包下载链接发给用户。

工作流会校验 Git 标签版本和 `release_info_service.py` 中的版本一致，避免安装包文件名、应用内版本和 Release 标题不一致。

## 当前版本

- 版本：`2.1.1`
- 安装包：`YuTanRadar-Setup-2.1.1.exe`
- 购买与激活：微信 `wgviptop`
- 用户交流群：[Telegram](https://t.me/+wyTMBj6IuRBjN2U1)
