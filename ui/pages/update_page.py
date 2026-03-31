#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新控制页面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QTextEdit, QMessageBox,
    QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from core.update_ctrl import (
    get_update_service_status, disable_windows_update,
    enable_windows_update
)
from core.sysinfo import get_update_status
from core.engine import engine


class UpdateWorker(QThread):
    """更新操作工作线程"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, enable: bool):
        super().__init__()
        self.enable = enable
        
    def run(self):
        try:
            if self.enable:
                result = enable_windows_update()
            else:
                result = disable_windows_update()
            result["requested_action"] = "启用" if self.enable else "禁用"
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class UpdatePage(QWidget):
    """更新控制页面"""
    
    def __init__(self):
        super().__init__()
        self.is_active = False
        self.worker = None
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 页面标题
        title = QLabel("Windows更新控制")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 当前状态区域
        self.create_status_section(layout)
        
        # 控制按钮区域
        self.create_control_section(layout)
        
        # 服务状态区域
        self.create_service_section(layout)
        
        # 操作日志区域
        self.create_log_section(layout)
        
        layout.addStretch()
        
    def create_status_section(self, parent_layout):
        """创建状态显示区域"""
        status_group = QGroupBox("当前状态")
        status_layout = QVBoxLayout(status_group)
        
        # 状态显示
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_frame.setFixedHeight(80)
        
        status_inner_layout = QHBoxLayout(status_frame)
        status_inner_layout.setContentsMargins(20, 20, 20, 20)
        
        status_inner_layout.addWidget(QLabel("Windows更新状态:"))
        self.status_label = QLabel("检查中...")
        status_font = QFont()
        status_font.setPointSize(16)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        status_inner_layout.addWidget(self.status_label)
        status_inner_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新状态")
        refresh_btn.setObjectName("SubtleButton")
        refresh_btn.clicked.connect(self.refresh)
        status_inner_layout.addWidget(refresh_btn)
        
        status_layout.addWidget(status_frame)
        parent_layout.addWidget(status_group)
        
    def create_control_section(self, parent_layout):
        """创建控制按钮区域"""
        control_group = QGroupBox("更新控制")
        control_layout = QVBoxLayout(control_group)
        
        # 警告信息
        warning_label = QLabel("⚠️ 警告：禁用Windows更新可能导致安全风险，请谨慎操作！")
        warning_label.setStyleSheet("color: #C05000; font-weight: bold; padding: 10px;")
        control_layout.addWidget(warning_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.disable_btn = QPushButton("禁用Windows更新")
        self.disable_btn.setObjectName("DangerButton")
        self.disable_btn.setFixedHeight(40)
        self.disable_btn.clicked.connect(self.disable_update)
        
        self.enable_btn = QPushButton("启用Windows更新")
        self.enable_btn.setObjectName("SuccessButton")
        self.enable_btn.setFixedHeight(40)
        self.enable_btn.clicked.connect(self.enable_update)
        
        button_layout.addWidget(self.disable_btn)
        button_layout.addWidget(self.enable_btn)
        button_layout.addStretch()
        
        control_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(control_group)
        
    def create_service_section(self, parent_layout):
        """创建服务状态区域"""
        service_group = QGroupBox("相关服务状态")
        service_layout = QGridLayout(service_group)
        
        self.service_labels = {}
        services = ["wuauserv", "UsoSvc", "WaaSMedicSvc"]
        service_names = ["Windows Update", "更新编排服务", "Windows更新医疗服务"]
        
        for i, (service, name) in enumerate(zip(services, service_names)):
            service_layout.addWidget(QLabel(f"{name}:"), i, 0)
            status_label = QLabel("检查中...")
            self.service_labels[service] = status_label
            service_layout.addWidget(status_label, i, 1)
            
        parent_layout.addWidget(service_group)
        
    def create_log_section(self, parent_layout):
        """创建日志区域"""
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        parent_layout.addWidget(log_group)
        
    def refresh(self):
        """刷新状态"""
        if not self.is_active:
            return
        try:
            # 更新主状态
            status = get_update_status()
            self.status_label.setText(status)
            
            if status == "已启用":
                self.status_label.setStyleSheet("color: #1D7A4A;")
            else:
                self.status_label.setStyleSheet("color: #C00000;")
                
            # 更新服务状态
            service_status = get_update_service_status()
            for service, status in service_status.items():
                if service in self.service_labels:
                    label = self.service_labels[service]
                    label.setText(status)
                    
                    if status == "运行中":
                        label.setStyleSheet("color: #1D7A4A;")
                    elif status == "已停止":
                        label.setStyleSheet("color: #C00000;")
                    else:
                        label.setStyleSheet("color: #666;")
                        
        except Exception as e:
            self.log(f"刷新状态失败: {e}")

    def set_active(self, active: bool):
        """统一页面激活入口。"""
        self.is_active = active
        if active:
            self.refresh()
            
    def disable_update(self):
        """禁用更新"""
        reply = QMessageBox.question(
            self, "确认操作",
            "确定要禁用Windows更新吗？\n\n这将停止自动下载和安装更新，可能导致安全风险。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_update_operation(False)
            
    def enable_update(self):
        """启用更新"""
        reply = QMessageBox.question(
            self, "确认操作",
            "确定要启用Windows更新吗？\n\n这将恢复自动下载和安装更新。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_update_operation(True)
            
    def start_update_operation(self, enable: bool):
        """开始更新操作"""
        if self.worker and self.worker.isRunning():
            return
            
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 禁用按钮
        self.disable_btn.setEnabled(False)
        self.enable_btn.setEnabled(False)
        
        # 记录日志
        action = "启用" if enable else "禁用"
        self.log(f"开始{action}Windows更新...")
        
        # 启动工作线程
        self.worker = UpdateWorker(enable)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.error.connect(self.on_operation_error)
        self.worker.start()
        
    def on_operation_finished(self, result):
        """操作完成"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 启用按钮
        self.disable_btn.setEnabled(True)
        self.enable_btn.setEnabled(True)
        
        # 处理结果
        if result.get("success", False):
            action = result.get("requested_action", "执行")
            self.log(f"✅ {action}Windows更新成功")
            
            if result.get("service_failures"):
                failed_services = ", ".join(result["service_failures"])
                self.log(f"⚠️ 部分服务操作失败: {failed_services}")
        else:
            self.log("❌ 操作失败")
            
            if not result.get("policy_success"):
                self.log("- 注册表策略设置失败")
                
            if result.get("service_failures"):
                failed_services = ", ".join(result["service_failures"])
                self.log(f"- 服务操作失败: {failed_services}")
                
        # 刷新状态
        self.refresh()
        
    def on_operation_error(self, error_msg):
        """操作错误"""
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 启用按钮
        self.disable_btn.setEnabled(True)
        self.enable_btn.setEnabled(True)
        
        # 记录错误
        self.log(f"❌ 操作失败: {error_msg}")
        
        # 显示错误对话框
        QMessageBox.critical(self, "操作失败", f"操作失败：{error_msg}")
        
    def log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        engine.log("INFO", f"[更新控制] {message}")
        
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
