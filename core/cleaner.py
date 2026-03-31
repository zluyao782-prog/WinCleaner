#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
垃圾清理模块：按软件类别扫描缓存文件，先预览后确认，再执行删除
"""

import os
import shutil
import glob
from pathlib import Path
from typing import Dict, List, Tuple
import tempfile


# 垃圾文件清理配置
JUNK_PROFILES = {
    "系统临时文件": [
        os.path.join(tempfile.gettempdir(), "*"),
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
        str(Path.home() / "AppData/Local/Mozilla/Firefox/Profiles/*/cache2/*"),
    ],
    "缩略图缓存": [
        str(Path.home() / "AppData/Local/Microsoft/Windows/Explorer/thumbcache_*.db"),
        str(Path.home() / "AppData/Local/Microsoft/Windows/Explorer/iconcache_*.db"),
    ],
    "系统日志": [
        r"C:\Windows\Logs\*\*.log",
        r"C:\Windows\System32\LogFiles\*\*.log",
    ],
    "下载临时文件": [
        str(Path.home() / "Downloads/*.tmp"),
        str(Path.home() / "Downloads/*.temp"),
        str(Path.home() / "Downloads/*.crdownload"),
    ]
}


def scan_junk(categories: List[str]) -> Dict[str, Dict]:
    """扫描垃圾文件
    
    Args:
        categories: 要扫描的类别列表
        
    Returns:
        Dict: 扫描结果，格式为 {类别: {"files": [文件列表], "size_mb": 总大小MB}}
    """
    result = {}
    
    for category in categories:
        if category not in JUNK_PROFILES:
            continue
            
        files = []
        total_size = 0
        
        for pattern in JUNK_PROFILES[category]:
            try:
                # 使用glob匹配文件
                matched_files = glob.glob(pattern, recursive=True)
                
                for file_path in matched_files:
                    try:
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            files.append(file_path)
                            total_size += size
                        elif os.path.isdir(file_path):
                            # 对于目录，计算其总大小
                            dir_size = get_directory_size(file_path)
                            files.append(file_path)
                            total_size += dir_size
                    except (OSError, PermissionError):
                        # 跳过无法访问的文件
                        continue
                        
            except Exception as e:
                print(f"扫描模式 {pattern} 失败: {e}")
                continue
                
        result[category] = {
            "files": files,
            "size_mb": round(total_size / (1024**2), 1),
            "count": len(files)
        }
        
    return result


def clean_junk(files: List[str]) -> Tuple[int, int]:
    """清理垃圾文件
    
    Args:
        files: 要删除的文件列表
        
    Returns:
        Tuple[int, int]: (成功删除数, 失败数)
    """
    success_count = 0
    failed_count = 0
    
    for file_path in files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                success_count += 1
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=True)
                success_count += 1
            else:
                # 文件不存在，可能已被删除
                continue
                
        except Exception as e:
            print(f"删除文件 {file_path} 失败: {e}")
            failed_count += 1
            
    return success_count, failed_count


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
        print(f"计算目录 {path} 大小失败: {e}")
        
    return total_size


def get_recycle_bin_size() -> int:
    """获取回收站大小
    
    Returns:
        int: 回收站占用字节数
    """
    try:
        # Windows回收站路径
        recycle_paths = []
        
        # 获取所有驱动器的回收站
        import string
        for drive in string.ascii_uppercase:
            recycle_path = f"{drive}:\\$Recycle.Bin"
            if os.path.exists(recycle_path):
                recycle_paths.append(recycle_path)
                
        total_size = 0
        for path in recycle_paths:
            total_size += get_directory_size(path)
            
        return total_size
        
    except Exception as e:
        print(f"获取回收站大小失败: {e}")
        return 0


def empty_recycle_bin() -> bool:
    """清空回收站
    
    Returns:
        bool: 是否成功
    """
    try:
        import ctypes
        from ctypes import wintypes
        
        # 使用Windows API清空回收站
        SHEmptyRecycleBin = ctypes.windll.shell32.SHEmptyRecycleBinW
        SHEmptyRecycleBin.argtypes = [
            wintypes.HWND,
            wintypes.LPCWSTR, 
            wintypes.DWORD
        ]
        SHEmptyRecycleBin.restype = wintypes.HRESULT
        
        # SHERB_NOCONFIRMATION = 0x00000001
        # SHERB_NOPROGRESSUI = 0x00000002
        result = SHEmptyRecycleBin(None, None, 0x00000001 | 0x00000002)
        
        return result == 0  # S_OK
        
    except Exception as e:
        print(f"清空回收站失败: {e}")
        return False


def scan_duplicate_files(path: str, min_size: int = 1024*1024) -> Dict[str, List[str]]:
    """扫描重复文件
    
    Args:
        path: 扫描路径
        min_size: 最小文件大小（字节），默认1MB
        
    Returns:
        Dict[str, List[str]]: {文件哈希: [重复文件路径列表]}
    """
    import hashlib
    
    file_hashes = {}
    duplicates = {}
    
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                filepath = os.path.join(root, file)
                
                try:
                    # 跳过小文件
                    if os.path.getsize(filepath) < min_size:
                        continue
                        
                    # 计算文件哈希
                    hash_md5 = hashlib.md5()
                    with open(filepath, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    
                    file_hash = hash_md5.hexdigest()
                    
                    if file_hash in file_hashes:
                        # 发现重复文件
                        if file_hash not in duplicates:
                            duplicates[file_hash] = [file_hashes[file_hash]]
                        duplicates[file_hash].append(filepath)
                    else:
                        file_hashes[file_hash] = filepath
                        
                except (OSError, PermissionError):
                    continue
                    
    except Exception as e:
        print(f"扫描重复文件失败: {e}")
        
    return duplicates


def get_junk_categories() -> List[str]:
    """获取所有垃圾清理类别
    
    Returns:
        List[str]: 类别名称列表
    """
    return list(JUNK_PROFILES.keys())