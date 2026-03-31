#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
垃圾清理页面
"""

import os
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QCheckBox, QTextEdit, QProgressBar, QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from core.cleaner import (
    get_junk_categories, scan_junk, clean_junk,
    get_recycle_bin_size, empty_recycle_bin
)
from core.disk import format_size
from core.engine import engine


class CleanWorker(QThread):
    """清理工作线程"""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, operation: str, data=None):
        super().__init__()
        self.operation = operation
        self.data = data
        
    def run(self):
        try:
            if self.operation == "scan":
                self.progress.emit("正在扫描垃圾文件...")
                result = scan_junk(self.data)
                self.finished.emit({"type": "scan", "result": result})
                
            elif self.operation == "clean":
                self.progress.emit("正在清理文件...")
                success, failed = clean_junk(self.data)
                self.finished.emit({
                    "type": "clean", 
                    "result": {"success": success, "failed": failed}
                })
                
            elif self.operation == "recycle":
                self.progress.emit("正在清空回收站...")
                result = empty_recycle_bin()
                self.finished.emit({"type": "recycle", "result": result})
                
        except Exception as e:
            self.error.emit(str(e))


class CleanerPage(QWidget):
    """垃圾清理页面"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.scan_results = {}
        self.result_checkboxes = {}
        self.init_ui()
        self.refresh()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 页面标题
        title = QLabel("垃圾清理")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 清理类别选择
        self.create_category_section(layout)
        
        # 扫描结果
        self.create_results_section(layout)
        
        # 回收站清理
        self.create_recycle_section(layout)
        
        # 操作日志
        self.create_log_section(layout)
        
        layout.addStretch()
        
    def create_category_section(self, parent_layout):
        """创建清理类别选择区域"""
        category_group = QGroupBox("清理类别")
        category_layout = QVBoxLayout(category_group)
        
        # 全选/全不选
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self.select_all)
        select_none_btn = QPushButton("全不选")
        select_none_btn.clicked.connect(self.select_none)
        
        select_layout.addWidget(select_all_btn)
        select_layout.addWidget(select_none_btn)
        select_layout.addStretch()
        
        # 扫描按钮
        self.scan_btn = QPushButton("扫描垃圾文件")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setStyleSheet("QPushButton { background-color: #2E75B6; color: white; font-weight: bold; }")
        select_layout.addWidget(self.scan_btn)
        
        category_layout.addLayout(select_layout)
        
        # 类别复选框
        self.category_checkboxes = {}
        categories = get_junk_categories()
        
        checkbox_layout = QGridLayout()
        for i, category in enumerate(categories):
            checkbox = QCheckBox(category)
            checkbox.setChecked(True)  # 默认全选
            self.category_checkboxes[category] = checkbox
            
            row = i // 3
            col = i % 3
            checkbox_layout.addWidget(checkbox, row, col)
            
        category_layout.addLayout(checkbox_layout)
        
        # 进度显示
        self.scan_progress = QLabel("就绪")
        category_layout.addWidget(self.scan_progress)
        
        parent_layout.addWidget(category_group)
        
    def create_results_section(self, parent_layout):
        """创建扫描结果区域"""
        results_group = QGroupBox("扫描结果")
        results_layout = QVBoxLayout(results_group)
        
        # 结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "类别", "文件数量", "占用空间", "操作"
        ])
        self.results_table.verticalHeader().setVisible(False)
        
        # 设置列宽
        self.results_table.setColumnWidth(0, 150)
        self.results_table.setColumnWidth(1, 100)
        self.results_table.setColumnWidth(2, 120)
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        results_layout.addWidget(self.results_table)
        
        # 清理按钮
        clean_layout = QHBoxLayout()
        clean_layout.addStretch()
        
        self.clean_btn = QPushButton("清理选中项")
        self.clean_btn.clicked.connect(self.start_clean)
        self.clean_btn.setEnabled(False)
        self.clean_btn.setStyleSheet("QPushButton { background-color: #C00000; color: white; font-weight: bold; }")
        clean_layout.addWidget(self.clean_btn)
        
        results_layout.addLayout(clean_layout)
        parent_layout.addWidget(results_group)
        
    def create_recycle_section(self, parent_layout):
        """创建回收站清理区域"""
        recycle_group = QGroupBox("回收站清理")
        recycle_layout = QHBoxLayout(recycle_group)
        
        self.recycle_label = QLabel("回收站大小: 计算中...")
        recycle_layout.addWidget(self.recycle_label)
        recycle_layout.addStretch()
        
        self.empty_recycle_btn = QPushButton("清空回收站")
        self.empty_recycle_btn.clicked.connect(self.empty_recycle)
        recycle_layout.addWidget(self.empty_recycle_btn)
        
        parent_layout.addWidget(recycle_group)
        
    def create_log_section(self, parent_layout):
        """创建日志区域"""
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        parent_layout.addWidget(log_group)
        
    def refresh(self):
        """刷新页面"""
        self.update_recycle_size()
        
    def update_recycle_size(self):
        """更新回收站大小"""
        try:
            size = get_recycle_bin_size()
            self.recycle_label.setText(f"回收站大小: {format_size(size)}")
        except Exception as e:
            self.recycle_label.setText("回收站大小: 获取失败")
            from logging import getLogger
            getLogger(__name__).warning("获取回收站大小失败: %s", e)
            
    def select_all(self):
        """全选"""
        for checkbox in self.category_checkboxes.values():
            checkbox.setChecked(True)
            
    def select_none(self):
        """全不选"""
        for checkbox in self.category_checkboxes.values():
            checkbox.setChecked(False)
            
    def start_scan(self):
        """开始扫描"""
        if self.worker and self.worker.isRunning():
            return
            
        # 获取选中的类别
        selected_categories = [
            category for category, checkbox in self.category_checkboxes.items()
            if checkbox.isChecked()
        ]
        
        if not selected_categories:
            QMessageBox.warning(self, "提示", "请至少选择一个清理类别")
            return
            
        # 禁用按钮
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")
        
        # 清空结果
        self.results_table.setRowCount(0)
        self.clean_btn.setEnabled(False)
        
        # 启动扫描线程
        self.worker = CleanWorker("scan", selected_categories)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.error.connect(self.on_operation_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()
        
    def start_clean(self):
        """开始清理"""
        if not self.scan_results:
            return

        selected_categories = self.get_selected_result_categories()
        if not selected_categories:
            QMessageBox.warning(self, "提示", "请先勾选需要清理的扫描结果")
            return
            
        total_files = sum(self.scan_results[category]["count"] for category in selected_categories)
        total_size = sum(self.scan_results[category]["size_mb"] for category in selected_categories)
        
        reply = QMessageBox.question(
            self, "确认清理",
            f"确定要清理 {total_files} 个文件，释放 {total_size:.1f} MB 空间吗？\n\n"
            f"已选择类别：{', '.join(selected_categories)}\n\n"
            "此操作不可撤销，请确认文件不再需要。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 收集所有要清理的文件
        all_files = []
        for category in selected_categories:
            all_files.extend(self.scan_results[category]["files"])
            
        # 禁用按钮
        self.clean_btn.setEnabled(False)
        self.clean_btn.setText("清理中...")
        
        # 启动清理线程
        self.worker = CleanWorker("clean", all_files)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.error.connect(self.on_operation_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()
        
    def empty_recycle(self):
        """清空回收站"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空回收站吗？\n\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 禁用按钮
        self.empty_recycle_btn.setEnabled(False)
        self.empty_recycle_btn.setText("清空中...")
        
        # 启动清理线程
        self.worker = CleanWorker("recycle")
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.error.connect(self.on_operation_error)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()
        
    def on_progress_update(self, message):
        """进度更新"""
        self.scan_progress.setText(message)
        
    def on_operation_finished(self, data):
        """操作完成"""
        op_type = data["type"]
        result = data["result"]
        
        if op_type == "scan":
            self.on_scan_finished(result)
        elif op_type == "clean":
            self.on_clean_finished(result)
        elif op_type == "recycle":
            self.on_recycle_finished(result)
            
    def on_scan_finished(self, results):
        """扫描完成"""
        # 启用按钮
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("扫描垃圾文件")
        
        # 保存结果
        self.scan_results = results
        self.result_checkboxes = {}
        
        self.refresh_results_table()
            
        # 记录日志
        total_files = sum(result["count"] for result in results.values())
        total_size = sum(result["size_mb"] for result in results.values())
        self.log(f"扫描完成：{len(results)} 个类别，{total_files} 个文件，{total_size:.1f} MB")
        
    def on_clean_finished(self, result):
        """清理完成"""
        # 启用按钮
        self.clean_btn.setEnabled(True)
        self.clean_btn.setText("清理选中项")
        
        # 更新进度
        success = result["success"]
        failed = result["failed"]
        self.scan_progress.setText(f"✅ 清理完成，成功 {success} 个，失败 {failed} 个")
        
        # 记录日志
        self.log(f"清理完成：成功 {success} 个文件，失败 {failed} 个文件")
        
        # 清空结果
        self.scan_results = {}
        self.result_checkboxes = {}
        self.results_table.setRowCount(0)
        self.clean_btn.setEnabled(False)
        
        # 更新回收站大小
        self.update_recycle_size()
        
    def on_recycle_finished(self, result):
        """回收站清理完成"""
        # 启用按钮
        self.empty_recycle_btn.setEnabled(True)
        self.empty_recycle_btn.setText("清空回收站")
        
        if result:
            self.scan_progress.setText("✅ 回收站清空成功")
            self.log("回收站清空成功")
        else:
            self.scan_progress.setText("❌ 回收站清空失败")
            self.log("回收站清空失败")
            
        # 更新回收站大小
        self.update_recycle_size()
        
    def on_operation_error(self, error_msg):
        """操作错误"""
        # 启用所有按钮
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("扫描垃圾文件")
        self.clean_btn.setEnabled(True)
        self.clean_btn.setText("清理选中项")
        self.empty_recycle_btn.setEnabled(True)
        self.empty_recycle_btn.setText("清空回收站")
        
        # 显示错误
        self.scan_progress.setText(f"❌ 操作失败: {error_msg}")
        self.log(f"操作失败: {error_msg}")
        
    def view_files(self, category):
        """查看文件列表"""
        if category not in self.scan_results:
            return
            
        files = self.scan_results[category]["files"]
        
        # 创建文件列表对话框
        from PyQt6.QtWidgets import QAbstractItemView, QDialog, QListWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{category} - 文件列表")
        dialog.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(dialog)
        
        file_list = QListWidget()
        file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        for file_path in files[:100]:  # 最多显示100个
            file_list.addItem(file_path)
            
        layout.addWidget(file_list)
        
        if len(files) > 100:
            layout.addWidget(QLabel(f"... 还有 {len(files) - 100} 个文件"))

        actions_layout = QHBoxLayout()
        open_btn = QPushButton("打开位置")
        exclude_btn = QPushButton("排除所选文件")
        close_btn = QPushButton("关闭")

        open_btn.clicked.connect(
            lambda: self.open_selected_file_location(file_list.currentItem().text() if file_list.currentItem() else "")
        )
        exclude_btn.clicked.connect(
            lambda: self.exclude_selected_files(category, file_list, dialog)
        )
        close_btn.clicked.connect(dialog.accept)

        actions_layout.addWidget(open_btn)
        actions_layout.addWidget(exclude_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(close_btn)
        layout.addLayout(actions_layout)
            
        dialog.exec()

    def get_selected_result_categories(self):
        """获取结果表格中勾选的类别。"""
        return [
            category for category, checkbox in self.result_checkboxes.items()
            if checkbox.isChecked() and self.scan_results.get(category, {}).get("count", 0) > 0
        ]

    def refresh_results_table(self):
        """根据当前扫描结果刷新表格统计。"""
        total_files = sum(result["count"] for result in self.scan_results.values())
        total_size = sum(result["size_mb"] for result in self.scan_results.values())
        self.scan_progress.setText(f"✅ 扫描完成，找到 {total_files} 个文件，共 {total_size:.1f} MB")

        self.results_table.setRowCount(len(self.scan_results))
        for i, (category, result) in enumerate(self.scan_results.items()):
            category_widget = QWidget()
            category_layout = QHBoxLayout(category_widget)
            category_layout.setContentsMargins(5, 0, 5, 0)

            checkbox = self.result_checkboxes.get(category)
            if checkbox is None:
                checkbox = QCheckBox(category)
                checkbox.setChecked(result["count"] > 0)
                self.result_checkboxes[category] = checkbox
            checkbox.setEnabled(result["count"] > 0)
            if result["count"] == 0:
                checkbox.setChecked(False)

            category_layout.addWidget(checkbox)
            category_layout.addStretch()
            self.results_table.setCellWidget(i, 0, category_widget)
            self.results_table.setItem(i, 1, QTableWidgetItem(str(result["count"])))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{result['size_mb']:.1f} MB"))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 5, 5, 5)

            view_btn = QPushButton("查看文件")
            view_btn.setEnabled(result["count"] > 0)
            view_btn.clicked.connect(lambda checked, cat=category: self.view_files(cat))
            action_layout.addWidget(view_btn)

            self.results_table.setCellWidget(i, 3, action_widget)

        self.clean_btn.setEnabled(total_files > 0)

    def open_selected_file_location(self, filepath: str):
        """打开所选文件位置。"""
        if not filepath:
            QMessageBox.information(self, "提示", "请先选择一个文件")
            return
        if not os.path.exists(filepath):
            QMessageBox.warning(self, "提示", "文件已不存在")
            return

        try:
            subprocess.run(["explorer", "/select,", filepath], check=False)
        except Exception as e:
            self.log(f"打开文件位置失败: {e}")

    def exclude_selected_files(self, category, file_list, dialog):
        """从本次清理结果中排除所选文件。"""
        selected_items = file_list.selectedItems()
        if not selected_items:
            QMessageBox.information(dialog, "提示", "请先选择要排除的文件")
            return

        excluded_files = {item.text() for item in selected_items}
        current_files = self.scan_results.get(category, {}).get("files", [])
        remaining_files = [file_path for file_path in current_files if file_path not in excluded_files]
        removed_count = len(current_files) - len(remaining_files)
        if removed_count <= 0:
            return

        remaining_size_mb = round(
            sum(os.path.getsize(file_path) for file_path in remaining_files if os.path.isfile(file_path)) / (1024 ** 2),
            1,
        )
        self.scan_results[category]["files"] = remaining_files
        self.scan_results[category]["count"] = len(remaining_files)
        self.scan_results[category]["size_mb"] = remaining_size_mb

        self.refresh_results_table()
        self.log(f"已从 {category} 排除 {removed_count} 个文件")
        dialog.accept()
        
    def log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        engine.log("INFO", f"[垃圾清理] {message}")
        
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
