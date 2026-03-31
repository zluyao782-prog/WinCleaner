#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理模块：实时列出所有后台进程，标记高负荷程序，支持一键终止
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List

import psutil

logger = logging.getLogger(__name__)
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "protected_procs.json"


DEFAULT_PROTECTED_PROCESSES = {
    "system", "smss.exe", "csrss.exe", "wininit.exe",
    "winlogon.exe", "lsass.exe", "services.exe",
    "dwm.exe", "explorer.exe", "svchost.exe"
}


def load_protected_processes() -> set[str]:
    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        processes = raw.get("protected_processes", [])
        return {str(name).lower() for name in processes}
    except Exception as e:
        logger.warning("加载受保护进程配置失败，使用默认配置: %s", e)
        return DEFAULT_PROTECTED_PROCESSES.copy()


PROTECTED_PROCESSES = load_protected_processes()


def get_processes(sort_by: str = "cpu") -> List[Dict]:
    """获取进程列表
    
    Args:
        sort_by: 排序方式，"cpu", "memory", "name"
        
    Returns:
        List[Dict]: 进程信息列表
    """
    processes = []
    
    for proc in psutil.process_iter([
        'pid', 'name', 'cpu_percent', 'memory_info', 
        'status', 'create_time', 'username'
    ]):
        try:
            info = proc.info
            
            # 获取内存使用量（MB）
            if info['memory_info'] is not None:
                memory_mb = round(info['memory_info'].rss / (1024**2), 1)
            else:
                memory_mb = 0.0
            
            # 获取CPU使用率
            cpu_percent = round(proc.cpu_percent(interval=None), 1)
            
            # 判断负荷级别
            level = get_load_level(cpu_percent, memory_mb)
            
            # 检查是否为保护进程
            process_name = info['name'] or 'Unknown'
            is_protected = is_protected_process(process_name)
            
            # 获取运行时间
            try:
                create_time = info['create_time']
                if create_time:
                    runtime = time.time() - create_time
                    runtime_str = format_runtime(runtime)
                else:
                    runtime_str = "未知"
            except:
                runtime_str = "未知"
            
            # 获取用户名
            try:
                username = info['username'] or "SYSTEM"
            except:
                username = "未知"
            
            process_info = {
                "pid": info['pid'],
                "name": process_name,
                "cpu_percent": cpu_percent,
                "memory_mb": memory_mb,
                "status": info['status'] or 'unknown',
                "level": level,
                "is_protected": is_protected,
                "runtime": runtime_str,
                "username": username
            }
            
            processes.append(process_info)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError, TypeError):
            continue
            
    # 排序
    if sort_by == "cpu":
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    elif sort_by == "memory":
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    elif sort_by == "name":
        processes.sort(key=lambda x: x['name'].lower())
        
    return processes


def get_load_level(cpu_percent: float, memory_mb: float) -> str:
    """判断进程负荷级别
    
    Args:
        cpu_percent: CPU使用率
        memory_mb: 内存使用量（MB）
        
    Returns:
        str: "normal", "warning", "high"
    """
    if cpu_percent > 80 or memory_mb > 1024:
        return "high"
    elif cpu_percent > 50 or memory_mb > 512:
        return "warning"
    else:
        return "normal"


def is_protected_process(process_name: str) -> bool:
    """检查是否为保护进程
    
    Args:
        process_name: 进程名
        
    Returns:
        bool: 是否为保护进程
    """
    return process_name.lower() in PROTECTED_PROCESSES


def get_high_load_processes() -> List[Dict]:
    """获取所有高负荷进程
    
    Returns:
        List[Dict]: 高负荷进程列表
    """
    all_processes = get_processes()
    return [p for p in all_processes if p['level'] in ['warning', 'high']]


def kill_process(pid: int, force: bool = False) -> bool:
    """终止进程
    
    Args:
        pid: 进程ID
        force: 是否强制终止
        
    Returns:
        bool: 是否成功
    """
    try:
        proc = psutil.Process(pid)
        
        # 检查是否为保护进程
        if is_protected_process(proc.name()):
            return False
            
        if force:
            # 强制终止
            proc.kill()
        else:
            # 优雅终止
            proc.terminate()
            try:
                # 等待3秒，如果还没退出就强制终止
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()
                
        return True
        
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    except Exception as e:
        logger.warning("终止进程失败: pid=%s error=%s", pid, e)
        return False


def kill_high_load_processes() -> Dict[str, int]:
    """批量终止高负荷进程
    
    Returns:
        Dict[str, int]: {"success": 成功数, "failed": 失败数}
    """
    high_load_procs = get_high_load_processes()
    success_count = 0
    failed_count = 0
    
    for proc in high_load_procs:
        if not proc['is_protected']:
            proc_name = (proc.get("name") or "").lower()
            username = (proc.get("username") or "").upper()
            if proc_name in {"code.exe", "pycharm64.exe", "idea64.exe"}:
                continue
            if username.startswith("NT AUTHORITY\\") or username == "SYSTEM":
                continue
            if kill_process(proc['pid']):
                success_count += 1
            else:
                failed_count += 1
                
    return {"success": success_count, "failed": failed_count}


def get_system_performance() -> Dict[str, float]:
    """获取系统性能概览
    
    Returns:
        Dict[str, float]: 系统性能指标
    """
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 进程数量
        process_count = len(psutil.pids())
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory.percent, 1),
            "memory_used_gb": round(memory.used / (1024**3), 1),
            "memory_total_gb": round(memory.total / (1024**3), 1),
            "process_count": process_count
        }
        
    except Exception as e:
        logger.warning("获取系统性能失败: %s", e)
        return {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "memory_used_gb": 0.0,
            "memory_total_gb": 0.0,
            "process_count": 0
        }


def format_runtime(seconds: float) -> str:
    """格式化运行时间
    
    Args:
        seconds: 运行秒数
        
    Returns:
        str: 格式化的时间字符串
    """
    try:
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}分钟"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}小时{minutes}分钟"
        else:
            days = int(seconds / 86400)
            hours = int((seconds % 86400) / 3600)
            return f"{days}天{hours}小时"
    except:
        return "未知"


def search_processes(keyword: str) -> List[Dict]:
    """搜索进程
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        List[Dict]: 匹配的进程列表
    """
    all_processes = get_processes()
    keyword_lower = keyword.lower()
    
    return [
        proc for proc in all_processes 
        if keyword_lower in proc['name'].lower()
    ]


def get_process_details(pid: int) -> Dict:
    """获取进程详细信息
    
    Args:
        pid: 进程ID
        
    Returns:
        Dict: 进程详细信息
    """
    try:
        proc = psutil.Process(pid)
        
        return {
            "pid": proc.pid,
            "name": proc.name(),
            "exe": proc.exe(),
            "cmdline": " ".join(proc.cmdline()),
            "status": proc.status(),
            "cpu_percent": proc.cpu_percent(),
            "memory_info": proc.memory_info()._asdict(),
            "create_time": proc.create_time(),
            "num_threads": proc.num_threads(),
            "username": proc.username()
        }
        
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        return {"error": str(e)}
