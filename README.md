# WinCleaner - Windows 系统清理工具

<div align="center">

![WinCleaner Logo](https://img.shields.io/badge/WinCleaner-v1.0-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey?style=for-the-badge)
![License](https://img.shields.io/badge/License-Educational-green?style=for-the-badge)

![Windows Build](https://github.com/zluyao782-prog/WinCleaner/workflows/Build%20Windows%20Release/badge.svg)
![Release](https://github.com/zluyao782-prog/WinCleaner/workflows/Create%20Release/badge.svg)

**🧹 专业的Windows系统清理和优化工具，让您的电脑重获新生**

[功能特色](#-功能特色) • [快速开始](#-快速开始) • [系统要求](#-系统要求) • [安全提示](#️-安全提示) • [技术架构](#️-技术架构)

</div>

---

## ✨ 功能特色

### 🖥️ 系统信息监控
- 📊 实时显示操作系统版本、CPU、内存等硬件信息
- ⏱️ 监控系统运行时间和性能状态
- 🔄 查看 Windows 更新状态

### 🔄 Windows更新控制
- 🛑 一键禁用/启用 Windows 自动更新
- 🔒 通过注册表策略和服务控制双重保障
- 📋 实时显示相关服务状态

### 💾 磁盘空间分析
- 📈 显示所有磁盘分区的使用情况
- 🔍 扫描指定目录下的大文件排名
- 📊 可视化磁盘空间分布

### 🗑️ 智能垃圾清理
支持清理多种类型的垃圾文件：
- 🗂️ 系统临时文件
- 💬 微信/QQ 缓存文件
- 🌐 浏览器缓存（Chrome、Edge、Firefox）
- 🖼️ 缩略图和图标缓存
- 📝 系统日志文件
- 👀 先扫描预览，确认后清理

### ⚙️ 进程管理
- 🔍 实时监控所有运行进程
- 🚨 智能标记高负荷进程（CPU/内存占用高）
- 🔎 支持搜索和排序功能
- ⚡ 一键终止高负荷进程
- 🛡️ 系统关键进程保护机制

## 🚀 快速开始

### 📥 下载使用

#### 方式一：下载发布版本
1. 前往 [Releases](../../releases) 页面
2. 下载最新版本的 `WinCleaner.exe`
3. 右键选择"以管理员身份运行"
4. 在UAC提示中点击"是"

#### 方式二：从源码构建
```bash
# 克隆仓库
git clone https://github.com/zluyao782-prog/WinCleaner.git
cd WinCleaner

# 安装依赖
pip install -r requirements.txt

# Windows环境构建
build.bat

# 或者直接运行源码（需要管理员权限）
python main.py
```

## 💻 系统要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Windows 10 (1903+) / Windows 11，64位 |
| **权限要求** | 管理员权限 |
| **磁盘空间** | 至少 50MB 可用空间 |
| **Python版本** | 3.10+ (仅源码运行需要) |

## ⚠️ 安全提示

| ⚠️ 重要警告 |
|-------------|
| 🔒 **更新风险**: 禁用Windows更新会阻止安全补丁安装 |
| ⚡ **进程风险**: 终止进程可能导致程序异常或数据丢失 |
| 🗑️ **清理风险**: 清理文件前请确认不再需要 |
| 🛡️ **系统保护**: 系统关键进程受保护，无法终止 |

## 🛠️ 技术架构

- **界面框架**: PyQt6 - 现代化桌面GUI
- **系统监控**: psutil - 跨平台系统资源监控  
- **Windows API**: pywin32, wmi - Windows系统深度集成
- **打包工具**: PyInstaller - 单文件可执行程序

### 项目结构
```
WinCleaner/
├── main.py                  # 程序入口
├── core/                    # 核心功能模块
│   ├── engine.py           # 统一调度引擎
│   ├── sysinfo.py          # 系统信息获取
│   ├── update_ctrl.py      # Windows更新控制
│   ├── disk.py             # 磁盘分析功能
│   ├── cleaner.py          # 垃圾文件清理
│   └── process_mgr.py      # 进程管理
├── ui/                     # 用户界面
│   ├── main_window.py      # 主窗口框架
│   └── pages/              # 功能页面
├── config/                 # 配置文件
├── assets/                 # 资源文件
└── requirements.txt        # 依赖清单
```

## 📸 界面预览

> 注：实际界面截图将在Windows环境下补充

## 🔧 开发指南

### 环境配置
```bash
# 克隆项目
git clone https://github.com/zluyao782-prog/WinCleaner.git
cd WinCleaner

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt
```

### 构建说明
- **Windows**: 运行 `build.bat`
- **Unix系统**: 运行 `./build.sh` (功能受限)

### 发布流程
1. 确保本地改动已经提交，并且 `main` 分支内容可发布。
2. 创建并推送版本标签，例如 `git tag v1.0.1` 和 `git push origin v1.0.1`。
3. GitHub Actions 会自动执行 `Build Windows Release` 工作流：
   - 安装依赖
   - 执行 Python 语法校验
   - 运行 `tests/` 下的单元测试
   - 使用 PyInstaller 构建 `WinCleaner.exe`
   - 生成 ZIP 发布包并上传到 workflow artifacts
   - 将 ZIP、`WinCleaner.exe`、`README.md`、`发布说明.md` 发布到 GitHub Release
4. 构建完成后，前往 GitHub 仓库的 Releases 页面下载正式发布资产。

建议：
- 标签命名统一使用 `v*`，例如 `v1.0.1`
- 发布前先在本地执行 `python -m unittest discover -s tests -p "test_*.py"`
- 如需更新发布说明，优先修改 `发布说明.md`

## 📋 版本历史

- **v1.0** (2026-03-31): 初始版本
  - ✅ 五大核心功能模块
  - ✅ 现代化PyQt6界面
  - ✅ 完整的安全保护机制
  - ✅ 详细的操作日志

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目仅供学习和个人使用。使用本工具产生的任何后果由用户自行承担。

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户。

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给它一个星标！**

Made with ❤️ by [zluyao782-prog](https://github.com/zluyao782-prog)

</div>
