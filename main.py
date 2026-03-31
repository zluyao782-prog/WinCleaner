#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WinCleaner - Windows 系统清理工具
主入口文件：权限检查、主窗口初始化
"""

import sys
import ctypes
import os
import subprocess
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow


def require_admin():
    """检查并要求管理员权限"""
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        try:
            params = subprocess.list2cmdline(sys.argv[1:])
            result = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
            if result <= 32:
                raise OSError(f"ShellExecuteW failed: {result}")
        except Exception:
            QMessageBox.critical(None, "权限错误", "无法获取管理员权限，程序将退出。")
        sys.exit()


def main():
    """主函数"""
    # 检查管理员权限
    require_admin()
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("WinCleaner")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("WinCleaner Team")
    
    # 设置应用图标
    if os.path.exists("assets/app.ico"):
        app.setWindowIcon(QIcon("assets/app.ico"))
    
    # 设置高DPI支持（PyQt6中已默认启用）
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # PyQt6中这些属性可能不存在或已默认启用
        pass
    
    try:
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "启动错误", f"程序启动失败：{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
