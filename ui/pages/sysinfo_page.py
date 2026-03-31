#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统信息页面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.sysinfo import (
    get_system_info, get_update_status, get_system_uptime,
    get_cpu_usage, get_memory_usage
)


class InfoCard(QFrame):
    """信息卡片组件"""
    
    def __init__(self, title: str, value: str, subtitle: str = ""):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setFixedHeight(120)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(title_label)
        
        # 主要值
        self.value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #1F3864;")
        layout.addWidget(self.value_label)
        
        # 副标题
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #999; font-size: 11px;")
            layout.addWidget(subtitle_label)
            
        layout.addStretch()
        
    def update_value(self, value: str):
        """更新显示值"""
        self.value_label.setText(value)


class SystemInfoPage(QWidget):
    """系统信息页面"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_timer()
        self.refresh()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 页面标题
        title = QLabel("系统信息")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 系统基本信息卡片
        self.create_system_cards(layout)
        
        # 实时性能监控
        self.create_performance_section(layout)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新信息")
        refresh_btn.clicked.connect(self.refresh)
        refresh_btn.setFixedWidth(120)
        layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addStretch()
        
    def create_system_cards(self, parent_layout):
        """创建系统信息卡片"""
        cards_layout = QGridLayout()
        cards_layout.setSpacing(15)
        
        # 创建信息卡片
        self.os_card = InfoCard("操作系统", "加载中...")
        self.cpu_card = InfoCard("处理器", "加载中...")
        self.memory_card = InfoCard("内存", "加载中...")
        self.uptime_card = InfoCard("运行时间", "加载中...")
        self.update_card = InfoCard("Windows更新", "加载中...")
        self.hostname_card = InfoCard("计算机名", "加载中...")
        
        # 布局卡片
        cards_layout.addWidget(self.os_card, 0, 0)
        cards_layout.addWidget(self.cpu_card, 0, 1)
        cards_layout.addWidget(self.memory_card, 0, 2)
        cards_layout.addWidget(self.uptime_card, 1, 0)
        cards_layout.addWidget(self.update_card, 1, 1)
        cards_layout.addWidget(self.hostname_card, 1, 2)
        
        parent_layout.addLayout(cards_layout)
        
    def create_performance_section(self, parent_layout):
        """创建性能监控区域"""
        perf_frame = QFrame()
        perf_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        perf_layout = QVBoxLayout(perf_frame)
        perf_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        perf_title = QLabel("实时性能监控")
        perf_title_font = QFont()
        perf_title_font.setPointSize(16)
        perf_title_font.setBold(True)
        perf_title.setFont(perf_title_font)
        perf_layout.addWidget(perf_title)
        
        # CPU使用率
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU使用率:"))
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        cpu_layout.addWidget(self.cpu_progress, 1)
        cpu_layout.addWidget(self.cpu_label)
        perf_layout.addLayout(cpu_layout)
        
        # 内存使用率
        mem_layout = QHBoxLayout()
        mem_layout.addWidget(QLabel("内存使用率:"))
        self.mem_progress = QProgressBar()
        self.mem_progress.setRange(0, 100)
        self.mem_label = QLabel("0%")
        mem_layout.addWidget(self.mem_progress, 1)
        mem_layout.addWidget(self.mem_label)
        perf_layout.addLayout(mem_layout)
        
        parent_layout.addWidget(perf_frame)
        
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_performance)
        self.timer.start(3000)  # 每3秒更新一次
        
    def refresh(self):
        """刷新系统信息"""
        try:
            # 获取系统信息
            sys_info = get_system_info()
            
            # 更新卡片
            self.os_card.update_value(sys_info.get("os_name", "未知"))
            self.cpu_card.update_value(sys_info.get("cpu", "未知"))
            self.memory_card.update_value(sys_info.get("ram_gb", "未知"))
            self.hostname_card.update_value(sys_info.get("hostname", "未知"))
            
            # 更新运行时间
            uptime = get_system_uptime()
            self.uptime_card.update_value(uptime)
            
            # 更新Windows更新状态
            update_status = get_update_status()
            self.update_card.update_value(update_status)
            
            # 更新性能监控
            self.update_performance()
            
        except Exception as e:
            print(f"刷新系统信息失败: {e}")
            
    def update_performance(self):
        """更新性能监控"""
        try:
            # CPU使用率
            cpu_usage = get_cpu_usage()
            self.cpu_progress.setValue(int(cpu_usage))
            self.cpu_label.setText(f"{cpu_usage:.1f}%")
            
            # 内存使用情况
            mem_info = get_memory_usage()
            mem_percent = mem_info.get("percent", 0)
            self.mem_progress.setValue(int(mem_percent))
            self.mem_label.setText(f"{mem_percent:.1f}% ({mem_info.get('used', 0):.1f}GB / {mem_info.get('total', 0):.1f}GB)")
            
        except Exception as e:
            print(f"更新性能监控失败: {e}")