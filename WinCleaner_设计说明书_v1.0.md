# WinCleaner — Windows 系统清理工具设计说明书

> 版本：v1.0 　｜　日期：2026-03-31 　｜　状态：草稿 　｜　作者：开发团队

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统要求](#2-系统要求)
3. [功能模块设计](#3-功能模块设计)
   - 3.1 [模块总览](#31-模块总览)
   - 3.2 [系统信息模块](#32-系统信息模块)
   - 3.3 [更新控制模块](#33-更新控制模块)
   - 3.4 [磁盘分析模块](#34-磁盘分析模块)
   - 3.5 [垃圾清理模块](#35-垃圾清理模块)
   - 3.6 [进程管理模块（新增）](#36-进程管理模块新增)
4. [整体技术架构](#4-整体技术架构)
5. [界面设计规范](#5-界面设计规范)
6. [依赖清单](#6-依赖清单)
7. [打包与分发](#7-打包与分发)
8. [版本计划](#8-版本计划)
9. [修订记录](#9-修订记录)

---

## 1. 项目概述

### 1.1 背景与目标

Windows 日常使用过程中，微信、QQ 等即时通讯软件会持续积累图片、视频缓存，系统也会产生大量临时文件，导致磁盘空间被悄无声息地蚕食。与此同时，Windows Update 强制后台下载更新、后台进程抢占 CPU/内存，都是造成电脑卡顿的常见原因。

WinCleaner 旨在将上述日常维护操作集中在一个桌面工具内，让非技术用户也能一键完成：

- 查看当前系统版本与硬件配置
- 可控地停用 / 恢复 Windows 自动更新
- 直观地了解磁盘空间分布
- 一键扫描并清理各类垃圾文件
- 实时监控后台进程，一键关闭高负荷程序

### 1.2 适用范围

本说明书适用于 WinCleaner 1.0 版本的设计、开发与测试阶段，面向项目开发人员及技术评审人员。

### 1.3 术语说明

| 术语 | 含义 |
|------|------|
| WMI | Windows Management Instrumentation，Windows 系统信息查询接口 |
| 注册表 | Windows 配置数据库，控制系统与软件行为 |
| UAC | User Account Control，用户账户控制，提权授权弹窗 |
| psutil | Python 跨平台进程与系统资源监控库 |
| PyQt6 | Python Qt6 图形界面框架，用于构建桌面 GUI |

---

## 2. 系统要求

### 2.1 运行环境

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 (1903+) / Windows 11，64 位 |
| 权限要求 | 需以管理员身份运行（UAC 提权），否则注册表写入与服务控制操作将失败 |
| 运行时依赖 | 打包版：无需安装 Python；开发版：Python 3.10+，见第 6 节依赖清单 |

### 2.2 开发环境

- Python 3.10 或更高版本
- PyInstaller 6.x（打包工具）
- Git（版本控制）

---

## 3. 功能模块设计

### 3.1 模块总览

| 模块名称 | 核心功能 | 调用接口 | 优先级 |
|----------|----------|----------|--------|
| 系统信息模块 | 读取 OS 版本、CPU、内存、主板信息，查询更新状态 | `wmi` / `winreg` / `platform` | P0 |
| 更新控制模块 | 通过注册表策略 + 服务控制双路径停用或恢复自动更新 | `winreg` / `subprocess` / `sc.exe` | P0 |
| 磁盘分析模块 | 扫描所有分区用量，支持大文件排名，输出可视化饼图 | `psutil` / `os` / `shutil` | P0 |
| 垃圾清理模块 | 按软件类别扫描缓存文件，先预览后确认，再执行删除 | `pathlib` / `glob` / `shutil` | P0 |
| 进程管理模块 | 实时列出所有后台进程，标记高 CPU/内存占用，支持一键终止 | `psutil` / `subprocess` | P0 |

---

### 3.2 系统信息模块

#### 3.2.1 功能描述

启动时自动采集当前设备的系统与硬件信息，展示在主界面顶部信息栏。数据仅读取，不做任何修改。

#### 3.2.2 采集字段

- 操作系统名称及版本号（如 Windows 11 Pro 23H2，Build 22631）
- 系统架构（x64 / ARM64）
- CPU 型号、核心数、当前主频
- 物理内存总量与当前可用量
- Windows Update 当前状态（启用 / 已禁用）
- 上次更新日期

#### 3.2.3 关键接口

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_system_info()` | 无 | `dict` | 返回系统信息字典，含 os_name / version / cpu / ram_gb 等字段 |
| `get_update_status()` | 无 | `str` | 返回 '已启用' / '已禁用'，读取注册表 NoAutoUpdate 值 |

#### 3.2.4 核心实现

```python
import platform, winreg, wmi

def get_system_info():
    c = wmi.WMI()
    os_info = c.Win32_OperatingSystem()[0]
    cpu = c.Win32_Processor()[0]

    return {
        "os_name":    os_info.Caption,           # Windows 11 Pro
        "os_version": os_info.Version,            # 10.0.22631
        "os_arch":    platform.architecture()[0],
        "cpu":        cpu.Name,
        "ram_gb":     round(int(os_info.TotalVisibleMemorySize) / 1024 / 1024, 1),
        "hostname":   platform.node(),
    }

def get_update_status():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
        )
        val, _ = winreg.QueryValueEx(key, "NoAutoUpdate")
        return "已禁用" if val == 1 else "已启用"
    except FileNotFoundError:
        return "已启用"
```

---

### 3.3 更新控制模块

#### 3.3.1 功能描述

通过两种互补路径，可靠地停用或恢复 Windows 自动更新。操作前弹出确认对话框，并在操作日志中记录每次变更。

#### 3.3.2 双路径策略

**路径一 — 注册表策略（主要）：**

- 写入路径：`HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU`
- 键名：`NoAutoUpdate`，类型 `REG_DWORD`，值 `1` 表示禁用，`0` 表示启用
- 该路径属于组策略管理范围，优先级高于用户设置，效果持久

**路径二 — 服务控制（辅助）：**

- 目标服务：`wuauserv`（Windows Update）、`UsoSvc`（更新编排）、`WaaSMedicSvc`（自我修复守护）
- 禁用时：`sc stop` + `sc config start=disabled`
- 恢复时：`sc config start=auto` + `sc start`
- 注：`WaaSMedicSvc` 有自保护机制，1.0 版本仅做 stop 处理

#### 3.3.3 关键接口

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `set_windows_update(enable)` | `enable: bool` | `bool` | 设置更新状态；True 启用，False 禁用 |
| `get_update_service_status()` | 无 | `dict` | 返回三个服务的当前运行状态 |
| `stop_update_services()` | 无 | `list[str]` | 停止并禁用更新服务，返回操作失败的服务名列表 |
| `restore_update_services()` | 无 | `list[str]` | 恢复并启动更新服务，返回操作失败的服务名列表 |

#### 3.3.4 核心实现

```python
import subprocess, winreg

def set_windows_update(enable: bool) -> bool:
    key_path = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
    try:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path,
                                 0, winreg.KEY_SET_VALUE)
        except FileNotFoundError:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        winreg.SetValueEx(key, "NoAutoUpdate", 0, winreg.REG_DWORD,
                          0 if enable else 1)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

UPDATE_SERVICES = ["wuauserv", "UsoSvc", "WaaSMedicSvc"]

def stop_update_services() -> list[str]:
    failed = []
    for svc in UPDATE_SERVICES:
        r1 = subprocess.run(["sc", "stop", svc], capture_output=True)
        r2 = subprocess.run(["sc", "config", svc, "start=", "disabled"],
                            capture_output=True)
        if r2.returncode != 0:
            failed.append(svc)
    return failed
```

> **安全提示**：禁用自动更新会导致安全补丁无法及时安装，建议用户定期手动检查更新。工具会在禁用后显示风险提示弹窗。

---

### 3.4 磁盘分析模块

#### 3.4.1 功能描述

枚举系统中所有已挂载磁盘分区，展示总容量、已用空间、可用空间及占用百分比，并以饼图直观呈现。额外提供大文件扫描功能，找出指定目录下占用空间最多的前 N 个文件。

#### 3.4.2 核心功能点

- 自动过滤无法访问的分区（如光驱空盘、网络驱动器等）
- 实时显示磁盘读写速度（基于 `psutil.disk_io_counters` 差值计算）
- 大文件排名支持自定义扫描根路径，默认扫描用户主目录
- 可视化饼图：已用空间用蓝色系标注，可用空间用灰色标注

#### 3.4.3 关键接口

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_disk_usage()` | 无 | `list[dict]` | 返回所有分区的用量信息列表 |
| `scan_large_files(path, top_n)` | `path: str, top_n: int=20` | `list[tuple]` | 返回 (size_bytes, filepath) 降序列表 |
| `get_disk_io_speed()` | 无 | `dict` | 返回读写速度（KB/s），需采样间隔 1s |

#### 3.4.4 核心实现

```python
import psutil, os

def get_disk_usage() -> list[dict]:
    result = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            result.append({
                "device":     part.device,
                "mountpoint": part.mountpoint,
                "total_gb":   round(usage.total / 1e9, 1),
                "used_gb":    round(usage.used  / 1e9, 1),
                "free_gb":    round(usage.free  / 1e9, 1),
                "percent":    usage.percent,
            })
        except PermissionError:
            continue
    return result

def scan_large_files(path: str, top_n: int = 20) -> list[tuple]:
    files = []
    for root, _, fnames in os.walk(path, onerror=lambda e: None):
        for f in fnames:
            fp = os.path.join(root, f)
            try:
                files.append((os.path.getsize(fp), fp))
            except OSError:
                pass
    return sorted(files, reverse=True)[:top_n]
```

---

### 3.5 垃圾清理模块

#### 3.5.1 功能描述

按预定义的软件类别，扫描并清理各类缓存、临时文件与垃圾数据。采用「先扫描预览、用户确认后再删除」的两步流程，防止误删重要文件。

#### 3.5.2 清理路径配置

| 软件 / 类别 | 清理路径（通配符） | 典型大小 |
|-------------|-------------------|----------|
| 系统 Temp | `%TEMP%\*` \| `C:\Windows\Temp\*` | 几十 MB ~ 数 GB |
| 微信图片缓存 | `Documents\WeChat Files\*\FileStorage\Image\*\*` | 数百 MB ~ 数 GB |
| 微信视频缓存 | `Documents\WeChat Files\*\FileStorage\Video\*\*` | 数 GB |
| 微信通用缓存 | `Documents\WeChat Files\*\FileStorage\Cache\*` | 数十 MB |
| QQ 图片缓存 | `Documents\Tencent Files\*\Image\*` | 数百 MB |
| QQ 视频缓存 | `Documents\Tencent Files\*\Video\*` | 数 GB |
| QQ 临时文件 | `AppData\Roaming\Tencent\QQ\Temp\*` | 数十 MB |
| Chrome 缓存 | `AppData\Local\Google\Chrome\User Data\Default\Cache\*` | 数百 MB |
| Edge 缓存 | `AppData\Local\Microsoft\Edge\User Data\Default\Cache\*` | 数百 MB |
| 缩略图缓存 | `AppData\Local\Microsoft\Windows\Explorer\thumbcache_*.db` | 数十 MB |
| 回收站 | `C:\$Recycle.Bin\*`（当前用户） | 不定 |

#### 3.5.3 执行流程

1. 用户勾选需清理的类别，点击「扫描」
2. 后台遍历所有匹配路径，统计文件数量与总大小
3. 界面展示扫描结果预览，列出文件列表与可释放空间
4. 用户确认后点击「清理」，执行删除操作
5. 清理完成，展示成功数、失败数与释放空间统计

#### 3.5.4 关键接口

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `scan_junk(categories)` | `categories: list[str]` | `dict` | 扫描并返回各类别的文件列表与大小，不执行删除 |
| `clean_junk(files)` | `files: list[str]` | `tuple[int, int]` | 执行删除，返回 (成功数, 失败数) |
| `get_recycle_bin_size()` | 无 | `int` | 返回回收站占用字节数 |
| `empty_recycle_bin()` | 无 | `bool` | 清空当前用户回收站，返回是否成功 |

#### 3.5.5 核心实现

```python
import os, shutil, glob
from pathlib import Path

JUNK_PROFILES = {
    "系统临时文件": [
        r"C:\Windows\Temp\*",
        str(Path.home() / "AppData/Local/Temp/*"),
    ],
    "微信缓存": [
        str(Path.home() / "Documents/WeChat Files/*/FileStorage/Image/*/*"),
        str(Path.home() / "Documents/WeChat Files/*/FileStorage/Video/*/*"),
        str(Path.home() / "Documents/WeChat Files/*/FileStorage/Cache/*"),
    ],
    "QQ缓存": [
        str(Path.home() / "Documents/Tencent Files/*/Image/*"),
        str(Path.home() / "Documents/Tencent Files/*/Video/*"),
        str(Path.home() / "AppData/Roaming/Tencent/QQ/Temp/*"),
    ],
    "浏览器缓存": [
        str(Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Cache/*"),
        str(Path.home() / "AppData/Local/Microsoft/Edge/User Data/Default/Cache/*"),
    ],
}

def scan_junk(categories: list) -> dict:
    result = {}
    for key in categories:
        files, total = [], 0
        for pattern in JUNK_PROFILES.get(key, []):
            for f in glob.glob(pattern, recursive=True):
                try:
                    size = os.path.getsize(f)
                    files.append(f)
                    total += size
                except OSError:
                    pass
        result[key] = {"files": files, "size_mb": round(total / 1e6, 1)}
    return result

def clean_junk(files: list) -> tuple[int, int]:
    ok, fail = 0, 0
    for f in files:
        try:
            if os.path.isfile(f):
                os.remove(f)
            elif os.path.isdir(f):
                shutil.rmtree(f, ignore_errors=True)
            ok += 1
        except Exception:
            fail += 1
    return ok, fail
```

---

### 3.6 进程管理模块（新增）

#### 3.6.1 功能背景

后台进程是导致电脑卡顿的核心原因之一。部分程序在最小化或关闭窗口后仍驻留后台持续消耗资源，用户往往无从感知。本模块提供实时进程监控与智能高负荷识别，帮助用户快速定位并关闭拖慢系统的程序。

#### 3.6.2 功能描述

- 实时列出所有后台进程，包含进程名、PID、CPU 占用率、内存占用、运行时长
- 按 CPU 或内存占用排序，支持关键词搜索与过滤
- 自动标记高负荷进程：CPU > 20% 标橙色警示，CPU > 50% 或内存 > 500MB 标红色
- 系统关键进程（System、csrss.exe、lsass.exe 等）加锁保护，不可操作
- 一键终止选中进程（先发送 SIGTERM，若 3s 内未退出再强制 SIGKILL）
- 支持批量选择高负荷进程一键全部关闭
- 刷新间隔可调（1s / 3s / 5s），默认 3s

#### 3.6.3 高负荷判断阈值

| 级别 | CPU 占用 | 内存占用 | 界面标注 |
|------|----------|----------|----------|
| 正常 | < 20% | < 200 MB | 无标注（白底） |
| 警告 | 20% ~ 50% | 200 ~ 500 MB | 橙色底色 |
| 高危 | > 50% | > 500 MB | 红色底色 + 警告图标 |

#### 3.6.4 系统保护名单

以下进程被列入保护名单，界面显示锁形图标，不提供终止操作：

- **Windows 系统核心**：`System`、`smss.exe`、`csrss.exe`、`wininit.exe`、`winlogon.exe`
- **安全与认证**：`lsass.exe`、`services.exe`、`svchost.exe`（部分子服务除外）
- **WinCleaner 自身进程**（防止自杀）
- 用户可在设置中追加自定义保护名单

#### 3.6.5 关键接口

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_processes(sort_by)` | `sort_by: str='cpu'` | `list[dict]` | 返回进程列表，含 pid/name/cpu_pct/mem_mb/status/is_protected |
| `get_high_load_processes()` | 无 | `list[dict]` | 返回所有标记为警告或高危的进程 |
| `kill_process(pid, force)` | `pid: int, force: bool=False` | `bool` | 终止指定进程；force=True 时跳过 SIGTERM 直接 SIGKILL |
| `kill_high_load_all()` | 无 | `dict` | 批量终止所有高危进程，返回成功/失败统计 |
| `is_protected(pid)` | `pid: int` | `bool` | 检查进程是否在保护名单中 |
| `set_refresh_interval(sec)` | `sec: int` | `None` | 设置进程列表刷新间隔（1/3/5 秒） |

#### 3.6.6 核心实现

```python
import psutil, time

PROTECTED_NAMES = {
    "system", "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "lsass.exe", "services.exe",
}

def get_processes(sort_by: str = "cpu") -> list[dict]:
    result = []
    for proc in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_info", "status", "create_time"]
    ):
        try:
            info = proc.info
            mem_mb = round(info["memory_info"].rss / 1e6, 1)
            cpu    = round(info["cpu_percent"], 1)
            level  = (
                "high"    if cpu > 50 or mem_mb > 500 else
                "warning" if cpu > 20 or mem_mb > 200 else
                "normal"
            )
            result.append({
                "pid":          info["pid"],
                "name":         info["name"],
                "cpu_pct":      cpu,
                "mem_mb":       mem_mb,
                "status":       info["status"],
                "level":        level,
                "is_protected": info["name"].lower() in PROTECTED_NAMES,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_pct" if sort_by == "cpu" else "mem_mb"
    return sorted(result, key=lambda x: x[key], reverse=True)

def kill_process(pid: int, force: bool = False) -> bool:
    try:
        proc = psutil.Process(pid)
        if is_protected(pid):
            return False
        if force:
            proc.kill()
        else:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def kill_high_load_all() -> dict:
    targets = get_high_load_processes()
    ok, fail = 0, 0
    for p in targets:
        if not p["is_protected"]:
            (ok if kill_process(p["pid"]) else fail)
            ok += 1 if kill_process(p["pid"]) else 0
            fail += 0 if kill_process(p["pid"]) else 1
    return {"success": ok, "failed": fail}

def is_protected(pid: int) -> bool:
    try:
        name = psutil.Process(pid).name().lower()
        return name in PROTECTED_NAMES
    except psutil.NoSuchProcess:
        return False
```

#### 3.6.7 异常处理

- **进程在操作过程中已退出**：捕获 `psutil.NoSuchProcess`，标记为「已退出」，不报错
- **权限不足（系统保护进程）**：捕获 `psutil.AccessDenied`，弹出提示，建议以管理员权限重启
- **强制终止超时（> 5s）**：记录日志，提示用户手动重启

---

## 4. 整体技术架构

### 4.1 分层结构

WinCleaner 采用三层架构：

- **表现层**：PyQt6 构建的桌面窗口，负责数据展示与用户交互
- **调度层**：统一的 Core Engine，管理权限检查、任务队列、日志记录与错误处理
- **功能层**：五个独立模块，各自封装相应的业务逻辑，模块间通过 Core Engine 通信
- **系统层**：`winreg`、`wmi`、`psutil`、`subprocess` 等直接与 Windows 交互

### 4.2 项目目录结构

```
WinCleaner/
├── main.py                  # 入口：权限检查、主窗口初始化
├── core/
│   ├── engine.py            # 核心调度层：任务队列、日志、异常处理
│   ├── sysinfo.py           # 系统信息模块
│   ├── update_ctrl.py       # 更新控制模块
│   ├── disk.py              # 磁盘分析模块
│   ├── cleaner.py           # 垃圾清理模块
│   └── process_mgr.py       # 进程管理模块
├── ui/
│   ├── main_window.py       # 主窗口布局与导航
│   ├── pages/               # 各模块对应的界面页
│   │   ├── sysinfo_page.py
│   │   ├── update_page.py
│   │   ├── disk_page.py
│   │   ├── cleaner_page.py
│   │   └── process_page.py  # 进程管理界面
│   └── widgets/             # 复用控件（进度条、饼图、进程表格等）
├── config/
│   ├── junk_profiles.json   # 垃圾文件路径配置
│   └── protected_procs.json # 进程保护名单
├── logs/                    # 运行日志（自动生成）
└── assets/
    └── app.ico
```

### 4.3 权限处理

程序入口 `main.py` 执行时立即检测当前权限级别：

```python
import ctypes, sys

def require_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()
```

1. 检测 `IsUserAnAdmin()` 返回值
2. 若非管理员，调用 `ShellExecuteW` 以 `runas` 动词重新启动自身，弹出 UAC 提权弹窗
3. 用户拒绝提权时，程序以受限模式启动，禁用需要管理员权限的操作按钮，并显示提示

---

## 5. 界面设计规范

### 5.1 整体风格

- **风格**：扁平化，白底深蓝主色，与 Windows 11 系统风格保持一致
- **导航**：左侧纵向图标 + 文字菜单，五个模块对应五个导航项
- **主内容区**：右侧，随导航切换对应页面
- **顶部状态栏**：显示操作系统名称、当前时间、权限状态

### 5.2 进程管理页面布局

- **顶部操作栏**：搜索框（关键词过滤）、排序选择器（CPU / 内存 / 名称）、刷新间隔选择器、「一键关闭高危」按钮
- **资源概览卡**：三个小卡片分别显示 CPU 总体占用、内存总体占用、当前进程总数
- **进程列表表格**：列包含进程名称、PID、CPU%、内存(MB)、状态、操作。高负荷行按阈值着色，锁图标标注受保护进程
- **底部日志栏**：滚动文本框，记录所有终止操作的时间、进程名、结果

### 5.3 色彩规范

| 用途 | 色值 | 使用场景 |
|------|------|----------|
| 主色（深蓝） | `#1F3864` | 标题、导航底色、表头 |
| 辅色（中蓝） | `#2E75B6` | 副标题、按钮、图表主色 |
| 背景浅蓝 | `#EBF3FB` | 信息提示框底色 |
| 成功（绿） | `#1D7A4A` | 正常进程、清理成功 |
| 警告（橙） | `#C05000` | CPU 20~50% 进程行 |
| 高危（红） | `#C00000` | CPU > 50% 或内存 > 500MB 进程行 |
| 中性灰 | `#F2F2F2` | 表格隔行底色 |

---

## 6. 依赖清单

| 包名 | 版本要求 | 用途 | 安装命令 |
|------|----------|------|----------|
| PyQt6 | `>=6.4` | GUI 框架 | `pip install PyQt6` |
| psutil | `>=5.9` | 进程与资源监控 | `pip install psutil` |
| pywin32 | `>=305` | Windows API 封装 | `pip install pywin32` |
| wmi | `>=1.5` | WMI 系统信息查询 | `pip install wmi` |
| PyInstaller | `>=6.0` | 打包为 exe | `pip install pyinstaller` |
| pyqtgraph | `>=0.13` | 磁盘饼图与实时图表 | `pip install pyqtgraph` |

`requirements.txt`：

```
PyQt6>=6.4
psutil>=5.9
pywin32>=305
wmi>=1.5
pyinstaller>=6.0
pyqtgraph>=0.13
```

---

## 7. 打包与分发

### 7.1 打包命令

```bash
pyinstaller --onefile --windowed --uac-admin \
  --name WinCleaner \
  --icon assets/app.ico \
  --add-data "config;config" \
  main.py
```

### 7.2 关键参数说明

| 参数 | 说明 |
|------|------|
| `--onefile` | 将所有依赖打包为单个 .exe，便于分发 |
| `--windowed` | 不显示控制台窗口（GUI 程序必须） |
| `--uac-admin` | 在 exe 清单中声明需要管理员权限，启动时自动触发 UAC 弹窗 |
| `--add-data` | 将 config/ 目录中的 JSON 配置文件一并打包 |

### 7.3 输出产物

- `dist/WinCleaner.exe`（单文件，约 30~50 MB）
- 建议配合代码签名证书（EV 证书）对 exe 进行数字签名，避免触发 Windows Defender 安全警告

---

## 8. 版本计划

| 版本 | 预计时间 | 主要内容 |
|------|----------|----------|
| v1.0 | 2026 Q2 | 五大核心模块上线：系统信息、更新控制、磁盘分析、垃圾清理、进程管理 |
| v1.1 | 2026 Q3 | 增加启动项管理（禁用 / 启用开机自启），优化进程管理的 CPU 图表 |
| v1.2 | 2026 Q4 | 支持自定义清理规则（用户可添加第三方软件路径），增加清理历史记录 |
| v2.0 | 2027 Q1 | 引入定时清理任务调度，支持远程监控（局域网内多机管理） |

---

## 9. 修订记录

| 版本 | 日期 | 修改人 | 变更内容 |
|------|------|--------|----------|
| v1.0 | 2026-03-31 | 开发团队 | 初稿，包含全部五大功能模块设计说明 |

---

*— 文档结束 —*
