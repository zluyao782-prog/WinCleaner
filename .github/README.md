# GitHub Actions 工作流说明

本项目包含以下 GitHub Actions 工作流：

## 🔄 CI/CD Pipeline (`ci.yml`)
- **触发条件**: 推送到 main/develop 分支，Pull Request
- **功能**: 
  - 代码质量检查 (Black, isort, Flake8)
  - 跨平台测试 (Ubuntu, macOS)
  - Windows 构建测试

## 🏗️ Windows Build (`build-windows.yml`)
- **触发条件**: 推送到 main 分支，标签推送，手动触发
- **功能**:
  - 在 Windows 环境下构建可执行文件
  - 自动上传构建产物
  - 标签推送时自动创建 Release

## 🚀 Release (`release.yml`)
- **触发条件**: 推送版本标签 (v*), 手动触发
- **功能**:
  - 创建完整的发布包
  - 自动更新版本信息
  - 创建 GitHub Release
  - 上传发布文件

## 📊 状态徽章

在 README.md 中可以使用以下徽章：

```markdown
![Build Status](https://github.com/zluyao782-prog/WinCleaner/workflows/CI%2FCD%20Pipeline/badge.svg)
![Windows Build](https://github.com/zluyao782-prog/WinCleaner/workflows/Build%20Windows%20Release/badge.svg)
![Release](https://github.com/zluyao782-prog/WinCleaner/workflows/Create%20Release/badge.svg)
```

## 🏷️ 创建发布版本

### 方法一：推送标签
```bash
git tag v1.0.1
git push origin v1.0.1
```

### 方法二：手动触发
1. 进入 GitHub 仓库页面
2. 点击 "Actions" 标签
3. 选择 "Create Release" 工作流
4. 点击 "Run workflow"
5. 输入版本号 (如 v1.0.1)
6. 点击 "Run workflow"

## 📁 构建产物

- **Artifacts**: 每次构建的临时文件，保存 30-90 天
- **Releases**: 正式发布版本，永久保存
- **文件类型**:
  - `WinCleaner.exe` - 单个可执行文件
  - `WinCleaner_vX.X.X.zip` - 完整发布包（包含文档）