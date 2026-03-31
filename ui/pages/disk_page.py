#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
磁盘分析页面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressBar, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from core.disk import get_disk_usage, scan_large_files, format_size
from core.engine import engine
import os


class DiskScanWorker(QThread):
    """磁盘扫描工作线程"""
    
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, path: str, top_n: int, min_size_bytes: int):
        super().__init__()
        self.path = path
        self.top_n = top_n
        self.min_size_bytes = min_size_bytes
        self._cancel_requested = False
        
    def run(self):
        try:
            self.progress.emit(f"正在扫描 {self.path}...")
            result = scan_large_files(
                self.path,
                self.top_n,
                self.min_size_bytes,
                self.progress.emit,
                self.is_cancel_requested,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        """请求取消扫描。"""
        self._cancel_requested = True

    def is_cancel_requested(self) -> bool:
        return self._cancel_requested


class DiskPage(QWidget):
    """磁盘分析页面"""
    
    def __init__(self):
        super().__init__()
        self.scan_worker = None
        self.init_ui()
        self.refresh()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 页面标题
        title = QLabel("磁盘分析")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 磁盘使用情况
        self.create_disk_usage_section(layout)
        
        # 大文件扫描
        self.create_large_files_section(layout)
        
        layout.addStretch()
        
    def create_disk_usage_section(self, parent_layout):
        """创建磁盘使用情况区域"""
        usage_group = QGroupBox("磁盘使用情况")
        usage_layout = QVBoxLayout(usage_group)
        
        # 刷新按钮
        refresh_layout = QHBoxLayout()
        refresh_layout.addStretch()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setObjectName("SubtleButton")
        refresh_btn.clicked.connect(self.refresh_disk_usage)
        refresh_layout.addWidget(refresh_btn)
        usage_layout.addLayout(refresh_layout)
        
        # 磁盘列表
        self.disk_table = QTableWidget()
        self.disk_table.setColumnCount(6)
        self.disk_table.setHorizontalHeaderLabels([
            "驱动器", "文件系统", "总容量", "已用空间", "可用空间", "使用率"
        ])
        
        # 设置列宽
        header = self.disk_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        usage_layout.addWidget(self.disk_table)
        parent_layout.addWidget(usage_group)
        
    def create_large_files_section(self, parent_layout):
        """创建大文件扫描区域"""
        files_group = QGroupBox("大文件扫描")
        files_layout = QVBoxLayout(files_group)
        
        # 扫描设置
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("扫描路径:"))
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.addItems([
            os.path.expanduser("~"),  # 用户主目录
            "C:\\",
            "D:\\",
            "E:\\"
        ])
        settings_layout.addWidget(self.path_combo, 1)
        
        settings_layout.addWidget(QLabel("显示数量:"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(10, 100)
        self.count_spin.setValue(20)
        settings_layout.addWidget(self.count_spin)

        settings_layout.addWidget(QLabel("最小大小:"))
        self.min_size_combo = QComboBox()
        self.min_size_combo.addItems(["10 MB", "50 MB", "100 MB", "500 MB", "1 GB"])
        self.min_size_combo.setCurrentText("100 MB")
        settings_layout.addWidget(self.min_size_combo)
        
        self.scan_btn = QPushButton("开始扫描")
        self.scan_btn.setObjectName("PrimaryButton")
        self.scan_btn.clicked.connect(self.start_scan)
        settings_layout.addWidget(self.scan_btn)

        self.cancel_btn = QPushButton("取消扫描")
        self.cancel_btn.setObjectName("SubtleButton")
        self.cancel_btn.clicked.connect(self.cancel_scan)
        self.cancel_btn.setEnabled(False)
        settings_layout.addWidget(self.cancel_btn)
        
        files_layout.addLayout(settings_layout)
        
        # 进度显示
        self.scan_progress = QLabel("就绪")
        files_layout.addWidget(self.scan_progress)
        
        # 文件列表
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(3)
        self.files_table.setHorizontalHeaderLabels([
            "文件大小", "文件路径", "操作"
        ])
        
        # 设置列宽
        self.files_table.setColumnWidth(0, 120)
        self.files_table.setColumnWidth(2, 100)
        header = self.files_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        files_layout.addWidget(self.files_table)
        parent_layout.addWidget(files_group)
        
    def refresh(self):
        """刷新页面"""
        self.refresh_disk_usage()
        
    def refresh_disk_usage(self):
        """刷新磁盘使用情况"""
        try:
            engine.log("INFO", "[磁盘分析] 刷新磁盘使用情况")
            disk_info = get_disk_usage()
            
            self.disk_table.setRowCount(len(disk_info))
            
            for i, disk in enumerate(disk_info):
                # 驱动器
                self.disk_table.setItem(i, 0, QTableWidgetItem(disk["device"]))
                
                # 文件系统
                self.disk_table.setItem(i, 1, QTableWidgetItem(disk["fstype"]))
                
                # 总容量
                self.disk_table.setItem(i, 2, QTableWidgetItem(f"{disk['total_gb']} GB"))
                
                # 已用空间
                self.disk_table.setItem(i, 3, QTableWidgetItem(f"{disk['used_gb']} GB"))
                
                # 可用空间
                self.disk_table.setItem(i, 4, QTableWidgetItem(f"{disk['free_gb']} GB"))
                
                # 使用率（带进度条）
                usage_widget = QWidget()
                usage_layout = QHBoxLayout(usage_widget)
                usage_layout.setContentsMargins(5, 5, 5, 5)
                
                progress = QProgressBar()
                progress.setRange(0, 100)
                progress.setValue(int(disk["percent"]))
                progress.setFormat(f"{disk['percent']:.1f}%")
                
                # 根据使用率设置颜色
                if disk["percent"] > 90:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: #C00000; }")
                elif disk["percent"] > 80:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: #C05000; }")
                else:
                    progress.setStyleSheet("QProgressBar::chunk { background-color: #1D7A4A; }")
                
                usage_layout.addWidget(progress)
                self.disk_table.setCellWidget(i, 5, usage_widget)
                
        except Exception as e:
            from logging import getLogger
            getLogger(__name__).warning("刷新磁盘信息失败: %s", e)
            engine.log("ERROR", f"[磁盘分析] 刷新磁盘信息失败: {e}")
            
    def start_scan(self):
        """开始扫描大文件"""
        if self.scan_worker and self.scan_worker.isRunning():
            return
            
        path = self.path_combo.currentText().strip()
        if not path or not os.path.exists(path):
            self.scan_progress.setText("❌ 路径不存在")
            engine.log("WARNING", f"[磁盘分析] 扫描路径不存在: {path}")
            return
            
        count = self.count_spin.value()
        min_size_text = self.min_size_combo.currentText()
        min_size_bytes = self.parse_min_size(min_size_text)
        
        # 禁用按钮
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")
        self.cancel_btn.setEnabled(True)
        
        # 清空表格
        self.files_table.setRowCount(0)
        
        # 启动扫描线程
        engine.log(
            "INFO",
            f"[磁盘分析] 开始扫描大文件: path={path}, top_n={count}, min_size={min_size_text}",
        )
        self.scan_worker = DiskScanWorker(path, count, min_size_bytes)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.progress.connect(self.on_scan_progress)
        self.scan_worker.start()
        
    def on_scan_progress(self, message):
        """扫描进度更新"""
        self.scan_progress.setText(message)
        
    def on_scan_finished(self, files):
        """扫描完成"""
        # 启用按钮
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("开始扫描")
        self.cancel_btn.setEnabled(False)

        # 更新进度
        if self.scan_worker and self.scan_worker.is_cancel_requested():
            self.scan_progress.setText(f"⚠️ 扫描已取消，当前结果 {len(files)} 个文件")
            engine.log("WARNING", f"[磁盘分析] 大文件扫描已取消: partial_count={len(files)}")
        else:
            self.scan_progress.setText(f"✅ 扫描完成，找到 {len(files)} 个文件")
            engine.log("INFO", f"[磁盘分析] 大文件扫描完成: count={len(files)}")
        
        # 填充表格
        self.files_table.setRowCount(len(files))
        
        for i, (size, filepath) in enumerate(files):
            # 文件大小
            size_item = QTableWidgetItem(format_size(size))
            size_item.setData(Qt.ItemDataRole.UserRole, size)  # 存储原始大小用于排序
            self.files_table.setItem(i, 0, size_item)
            
            # 文件路径
            self.files_table.setItem(i, 1, QTableWidgetItem(filepath))
            
            # 操作按钮
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 5, 5, 5)
            
            open_btn = QPushButton("打开位置")
            open_btn.setObjectName("SubtleButton")
            open_btn.clicked.connect(lambda checked, path=filepath: self.open_file_location(path))
            action_layout.addWidget(open_btn)
            
            self.files_table.setCellWidget(i, 2, action_widget)
            
        # 按大小排序
        self.files_table.sortItems(0, Qt.SortOrder.DescendingOrder)
        
    def on_scan_error(self, error_msg):
        """扫描错误"""
        # 启用按钮
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("开始扫描")
        self.cancel_btn.setEnabled(False)
        
        # 显示错误
        self.scan_progress.setText(f"❌ 扫描失败: {error_msg}")
        engine.log("ERROR", f"[磁盘分析] 大文件扫描失败: {error_msg}")

    def cancel_scan(self):
        """取消当前扫描。"""
        if not self.scan_worker or not self.scan_worker.isRunning():
            return
        self.scan_worker.cancel()
        self.cancel_btn.setEnabled(False)
        self.scan_progress.setText("⚠️ 正在取消扫描...")
        engine.log("WARNING", "[磁盘分析] 用户请求取消扫描")

    def parse_min_size(self, text: str) -> int:
        """解析最小文件大小设置。"""
        mapping = {
            "10 MB": 10 * 1024 * 1024,
            "50 MB": 50 * 1024 * 1024,
            "100 MB": 100 * 1024 * 1024,
            "500 MB": 500 * 1024 * 1024,
            "1 GB": 1024 * 1024 * 1024,
        }
        return mapping.get(text, 100 * 1024 * 1024)
        
    def open_file_location(self, filepath):
        """打开文件位置"""
        try:
            import subprocess
            subprocess.run(["explorer", "/select,", filepath])
            engine.log("INFO", f"[磁盘分析] 打开文件位置: {filepath}")
        except Exception as e:
            from logging import getLogger
            getLogger(__name__).warning("打开文件位置失败: %s", e)
            engine.log("ERROR", f"[磁盘分析] 打开文件位置失败: {e}")
