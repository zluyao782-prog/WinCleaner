#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新控制模块：通过注册表策略 + 服务控制双路径停用或恢复自动更新
"""

import subprocess
from typing import List, Dict

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False


# Windows更新相关服务
UPDATE_SERVICES = ["wuauserv", "UsoSvc", "WaaSMedicSvc"]


def set_windows_update(enable: bool) -> bool:
    """设置Windows更新状态
    
    Args:
        enable: True启用更新，False禁用更新
        
    Returns:
        bool: 操作是否成功
    """
    if not WINREG_AVAILABLE:
        print("Windows注册表模块不可用")
        return False
        
    key_path = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
    
    try:
        # 尝试打开现有键，如果不存在则创建
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, 
                key_path,
                0, 
                winreg.KEY_SET_VALUE
            )
        except FileNotFoundError:
            # 创建完整路径
            parent_key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
            )
            key = winreg.CreateKey(parent_key, "AU")
            winreg.CloseKey(parent_key)
        
        # 设置NoAutoUpdate值：0=启用，1=禁用
        winreg.SetValueEx(
            key, 
            "NoAutoUpdate", 
            0, 
            winreg.REG_DWORD,
            0 if enable else 1
        )
        winreg.CloseKey(key)
        
        return True
        
    except Exception as e:
        print(f"设置更新策略失败: {e}")
        return False


def get_update_service_status() -> Dict[str, str]:
    """获取更新服务状态"""
    status = {}
    
    for service in UPDATE_SERVICES:
        try:
            result = subprocess.run(
                ["sc", "query", service],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                if "RUNNING" in output:
                    status[service] = "运行中"
                elif "STOPPED" in output:
                    status[service] = "已停止"
                else:
                    status[service] = "未知"
            else:
                status[service] = "不存在"
                
        except Exception as e:
            print(f"查询服务 {service} 状态失败: {e}")
            status[service] = "查询失败"
            
    return status


def stop_update_services() -> List[str]:
    """停止并禁用更新服务
    
    Returns:
        List[str]: 操作失败的服务名列表
    """
    failed = []
    
    for service in UPDATE_SERVICES:
        try:
            # 停止服务
            stop_result = subprocess.run(
                ["sc", "stop", service],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 禁用服务
            config_result = subprocess.run(
                ["sc", "config", service, "start=", "disabled"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 如果配置失败，记录到失败列表
            if config_result.returncode != 0:
                failed.append(service)
                print(f"禁用服务 {service} 失败: {config_result.stderr}")
                
        except Exception as e:
            print(f"操作服务 {service} 失败: {e}")
            failed.append(service)
            
    return failed


def restore_update_services() -> List[str]:
    """恢复并启动更新服务
    
    Returns:
        List[str]: 操作失败的服务名列表
    """
    failed = []
    
    for service in UPDATE_SERVICES:
        try:
            # 设置为自动启动
            config_result = subprocess.run(
                ["sc", "config", service, "start=", "auto"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if config_result.returncode == 0:
                # 启动服务
                start_result = subprocess.run(
                    ["sc", "start", service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if start_result.returncode != 0:
                    # 启动失败不一定是错误，可能服务已在运行
                    print(f"启动服务 {service}: {start_result.stderr}")
            else:
                failed.append(service)
                print(f"配置服务 {service} 失败: {config_result.stderr}")
                
        except Exception as e:
            print(f"恢复服务 {service} 失败: {e}")
            failed.append(service)
            
    return failed


def disable_windows_update() -> Dict[str, any]:
    """完全禁用Windows更新
    
    Returns:
        Dict: 操作结果，包含策略设置和服务操作结果
    """
    result = {
        "policy_success": False,
        "service_failures": [],
        "success": False
    }
    
    # 设置注册表策略
    result["policy_success"] = set_windows_update(False)
    
    # 停止相关服务
    result["service_failures"] = stop_update_services()
    
    # 判断整体是否成功
    result["success"] = result["policy_success"] and len(result["service_failures"]) == 0
    
    return result


def enable_windows_update() -> Dict[str, any]:
    """启用Windows更新
    
    Returns:
        Dict: 操作结果，包含策略设置和服务操作结果
    """
    result = {
        "policy_success": False,
        "service_failures": [],
        "success": False
    }
    
    # 设置注册表策略
    result["policy_success"] = set_windows_update(True)
    
    # 恢复相关服务
    result["service_failures"] = restore_update_services()
    
    # 判断整体是否成功
    result["success"] = result["policy_success"] and len(result["service_failures"]) == 0
    
    return result