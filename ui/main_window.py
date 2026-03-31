#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口布局与导航
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QStackedWidget, QListWidget, QListWidgetItem,
    QLabel, QFrame, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon

from ui.pages.sysinfo_page import SystemInfoPage
from ui.pages.update_page import UpdatePage
from ui.pages.disk_page import DiskPage
from ui.pages.cleaner_page import CleanerPage
from ui.pages.process_page import ProcessPage
from core.engine import engine


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("WinCleaner - Windows 系统清理工具 v1.0")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建导航栏
        self.create_navigation()
        main_layout.addWidget(self.nav_frame)
        
        # 创建内容区域
        self.create_content_area()
        main_layout.addWidget(self.content_widget, 1)
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置样式
        self.set_styles()
        
    def create_navigation(self):
        """创建导航栏"""
        self.nav_frame = QFrame()
        self.nav_frame.setFixedWidth(200)
        self.nav_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        
        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        
        # 标题
        title_label = QLabel("WinCleaner")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        nav_layout.addWidget(title_label)
        
        nav_layout.addSpacing(20)
        
        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.setFrameStyle(QFrame.Shape.NoFrame)
        
        # 添加导航项
        nav_items = [
            ("系统信息", "📊"),
            ("更新控制", "🔄"),
            ("磁盘分析", "💾"),
            ("垃圾清理", "🗑️"),
            ("进程管理", "⚙️")
        ]
        
        for text, icon in nav_items:
            item = QListWidgetItem(f"{icon} {text}")
            item.setData(Qt.ItemDataRole.UserRole, text)
            self.nav_list.addItem(item)
            
        nav_layout.addWidget(self.nav_list)
        nav_layout.addStretch()
        
    def create_content_area(self):
        """创建内容区域"""
        self.content_widget = QStackedWidget()
        
        # 创建各个页面
        self.pages = {
            "系统信息": SystemInfoPage(),
            "更新控制": UpdatePage(),
            "磁盘分析": DiskPage(),
            "垃圾清理": CleanerPage(),
            "进程管理": ProcessPage()
        }
        
        # 添加页面到堆栈
        for page in self.pages.values():
            self.content_widget.addWidget(page)
            
        # 默认显示第一页
        self.content_widget.setCurrentIndex(0)
        self.nav_list.setCurrentRow(0)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 权限状态
        admin_status = "管理员权限" if engine.is_admin() else "普通用户"
        self.status_bar.addPermanentWidget(QLabel(f"权限: {admin_status}"))
        
        # 时间显示
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
        
        # 定时更新时间
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        
    def update_time(self):
        """更新时间显示"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
        
    def setup_connections(self):
        """设置信号连接"""
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        
    def on_nav_changed(self, index):
        """导航切换事件"""
        self.content_widget.setCurrentIndex(index)
        
        # 刷新当前页面
        current_page = list(self.pages.values())[index]
        if hasattr(current_page, 'refresh'):
            current_page.refresh()
            
    def set_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
            }
            
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
                color: #333;
            }
            
            QListWidget::item:selected {
                background-color: #1F3864;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #EBF3FB;
            }
            
            QLabel {
                color: #333;
            }
            
            QStatusBar {
                background-color: #f0f0f0;
                border-top: 1px solid #d0d0d0;
            }
        """)