#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁盘分析模块：扫描所有分区用量，支持大文件排名，输出可视化饼图
"""

import os
import logging
import psutil
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def get_disk_usage() -> List[Dict]:
    """获取所有磁盘分区的使用情况
    
    Returns:
        List[Dict]: 分区信息列表
    """
    result = []
    
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            
            partition_info = {
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "percent": round(usage.percent, 1),
            }
            
            result.append(partition_info)
            
        except PermissionError:
            continue
        except Exception as e:
            logger.warning("获取分区信息失败: device=%s error=%s", partition.device, e)
            continue
            
    return result


def scan_large_files(path: str, top_n: int = 20) -> List[Tuple[int, str]]:
    """扫描指定路径下的大文件
    
    Args:
        path: 扫描路径
        top_n: 返回前N个最大文件
        
    Returns:
        List[Tuple[int, str]]: (文件大小字节, 文件路径) 的列表，按大小降序
    """
    files = []
    
    try:
        for root, dirs, filenames in os.walk(path):
            # 跳过系统保护目录
            dirs[:] = [d for d in dirs if not d.startswith('$') and d not in [
                'System Volume Information', 'Recovery', 'Windows'
            ]]
            
            for filename in filenames:
                filepath = os.path.join(root, filename)
                try:
                    size = os.path.getsize(filepath)
                    files.append((size, filepath))
                except (OSError, PermissionError):
                    # 跳过无法访问的文件
                    continue
                    
    except Exception as e:
        logger.warning("扫描大文件失败: path=%s error=%s", path, e)
        
    # 按大小降序排序，返回前N个
    return sorted(files, reverse=True)[:top_n]


def get_disk_io_speed() -> Dict[str, float]:
    """获取磁盘IO速度
    
    Returns:
        Dict[str, float]: 包含读写速度的字典 (KB/s)
    """
    try:
        # 获取第一次IO统计
        io_1 = psutil.disk_io_counters()
        if io_1 is None:
            return {"read_speed": 0.0, "write_speed": 0.0}
            
        import time
        time.sleep(1)  # 等待1秒
        
        # 获取第二次IO统计
        io_2 = psutil.disk_io_counters()
        if io_2 is None:
            return {"read_speed": 0.0, "write_speed": 0.0}
            
        # 计算速度 (字节/秒 -> KB/秒)
        read_speed = (io_2.read_bytes - io_1.read_bytes) / 1024
        write_speed = (io_2.write_bytes - io_1.write_bytes) / 1024
        
        return {
            "read_speed": round(read_speed, 1),
            "write_speed": round(write_speed, 1)
        }
        
    except Exception as e:
        logger.warning("获取磁盘IO速度失败: %s", e)
        return {"read_speed": 0.0, "write_speed": 0.0}


def get_directory_size(path: str) -> int:
    """获取目录总大小
    
    Args:
        path: 目录路径
        
    Returns:
        int: 目录大小（字节）
    """
    total_size = 0
    
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, PermissionError):
                    continue
    except Exception as e:
        logger.warning("计算目录大小失败: path=%s error=%s", path, e)
        
    return total_size


def analyze_disk_space(drive: str) -> Dict[str, any]:
    """分析磁盘空间分布
    
    Args:
        drive: 驱动器路径，如 "C:\\"
        
    Returns:
        Dict: 空间分析结果
    """
    result = {
        "total_size": 0,
        "used_size": 0,
        "free_size": 0,
        "categories": {}
    }
    
    try:
        usage = psutil.disk_usage(drive)
        result["total_size"] = usage.total
        result["used_size"] = usage.used
        result["free_size"] = usage.free
        
        # 分析主要目录占用
        major_dirs = ["Windows", "Program Files", "Program Files (x86)", "Users"]
        
        for dir_name in major_dirs:
            dir_path = os.path.join(drive, dir_name)
            if os.path.exists(dir_path):
                size = get_directory_size(dir_path)
                result["categories"][dir_name] = size
                
    except Exception as e:
        logger.warning("分析磁盘失败: drive=%s error=%s", drive, e)
        
    return result


def format_size(size_bytes: int) -> str:
    """格式化文件大小显示
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"
