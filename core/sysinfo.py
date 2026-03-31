#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统信息模块：读取OS版本、CPU、内存、主板信息，查询更新状态
"""

import platform
import logging
import psutil
from typing import Dict

logger = logging.getLogger(__name__)

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


def get_system_info() -> Dict[str, str]:
    """获取系统信息"""
    info = {
        "os_name": "Unknown",
        "os_version": "Unknown", 
        "os_arch": platform.architecture()[0],
        "cpu": "Unknown",
        "ram_gb": "0",
        "hostname": platform.node(),
    }
    
    try:
        # 基础系统信息
        info["os_name"] = platform.system() + " " + platform.release()
        info["os_version"] = platform.version()
        
        # CPU信息
        info["cpu"] = platform.processor()
        
        # 内存信息
        memory = psutil.virtual_memory()
        info["ram_gb"] = f"{round(memory.total / (1024**3), 1)} GB"
        
        # 如果WMI可用，获取更详细信息
        if WMI_AVAILABLE:
            try:
                c = wmi.WMI()
                
                # 操作系统信息
                os_info = c.Win32_OperatingSystem()[0]
                info["os_name"] = os_info.Caption
                info["os_version"] = os_info.Version
                
                # CPU信息
                cpu_info = c.Win32_Processor()[0]
                info["cpu"] = cpu_info.Name.strip()
                
            except Exception as e:
                logger.warning("WMI查询失败: %s", e)
                
    except Exception as e:
        logger.warning("获取系统信息失败: %s", e)
        
    return info


def get_update_status() -> str:
    """获取Windows更新状态"""
    if not WINREG_AVAILABLE:
        return "不支持"
        
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
        )
        val, _ = winreg.QueryValueEx(key, "NoAutoUpdate")
        winreg.CloseKey(key)
        return "已禁用" if val == 1 else "已启用"
    except FileNotFoundError:
        return "已启用"
    except Exception as e:
        logger.warning("查询更新状态失败: %s", e)
        return "未知"


def get_last_update_time() -> str:
    """获取最后更新时间"""
    try:
        if WMI_AVAILABLE:
            patches = wmi.WMI().Win32_QuickFixEngineering()
            installed_dates = []
            for patch in patches:
                installed_on = getattr(patch, "InstalledOn", "") or ""
                if installed_on:
                    installed_dates.append(installed_on)
            if installed_dates:
                return max(installed_dates)
    except Exception as e:
        logger.warning("获取最后更新时间失败: %s", e)
        return "未知"
    return "未知"


def get_system_uptime() -> str:
    """获取系统运行时间"""
    try:
        import datetime
        boot_time = psutil.boot_time()
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        else:
            return f"{minutes}分钟"
            
    except Exception:
        return "未知"


def get_cpu_usage() -> float:
    """获取CPU使用率"""
    try:
        return psutil.cpu_percent(interval=None)
    except Exception:
        return 0.0


def get_memory_usage() -> Dict[str, float]:
    """获取内存使用情况"""
    try:
        memory = psutil.virtual_memory()
        return {
            "total": round(memory.total / (1024**3), 1),
            "used": round(memory.used / (1024**3), 1),
            "available": round(memory.available / (1024**3), 1),
            "percent": memory.percent
        }
    except Exception:
        return {"total": 0, "used": 0, "available": 0, "percent": 0}
