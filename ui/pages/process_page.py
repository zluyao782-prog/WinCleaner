#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理页面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QLineEdit, QComboBox, QTextEdit, QMessageBox,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.process_mgr import (
    get_processes, kill_process, get_system_performance, search_processes
)
from core.engine import engine


class ProcessPage(QWidget):
    """进程管理页面"""
    
    def __init__(self):
        super().__init__()
        self.current_processes = []
        self.refresh_timer = QTimer()
        self.init_ui()
        self.setup_timer()
        self.refresh()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 页面标题
        title = QLabel("进程管理")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 系统性能概览
        self.create_performance_section(layout)
        
        # 控制面板
        self.create_control_section(layout)
        
        # 进程列表
        self.create_process_table(layout)
        
        # 操作日志
        self.create_log_section(layout)
        
    def create_performance_section(self, parent_layout):
        """创建性能概览区域"""
        perf_group = QGroupBox("系统性能概览")
        perf_layout = QHBoxLayout(perf_group)
        
        # CPU卡片
        self.cpu_card = self.create_perf_card("CPU使用率", "0%")
        perf_layout.addWidget(self.cpu_card)
        
        # 内存卡片
        self.memory_card = self.create_perf_card("内存使用率", "0%")
        perf_layout.addWidget(self.memory_card)
        
        # 进程数卡片
        self.process_card = self.create_perf_card("进程总数", "0")
        perf_layout.addWidget(self.process_card)
        
        parent_layout.addWidget(perf_group)
        
    def create_perf_card(self, title: str, value: str) -> QFrame:
        """创建性能卡片"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setFixedHeight(80)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: #1F3864;")
        layout.addWidget(value_label)
        
        # 保存引用以便更新
        card.value_label = value_label
        
        return card
        
    def create_control_section(self, parent_layout):
        """创建控制面板"""
        control_group = QGroupBox("控制面板")
        control_layout = QVBoxLayout(control_group)
        
        # 第一行：搜索和排序
        row1_layout = QHBoxLayout()
        
        row1_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入进程名称...")
        self.search_input.textChanged.connect(self.on_search_changed)
        row1_layout.addWidget(self.search_input)
        
        row1_layout.addWidget(QLabel("排序:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["CPU使用率", "内存使用", "进程名称"])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        row1_layout.addWidget(self.sort_combo)
        
        row1_layout.addWidget(QLabel("刷新间隔:"))
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1秒", "3秒", "5秒"])
        self.interval_combo.setCurrentText("3秒")
        self.interval_combo.currentTextChanged.connect(self.on_interval_changed)
        row1_layout.addWidget(self.interval_combo)
        
        control_layout.addLayout(row1_layout)
        
        # 第二行：操作按钮
        row2_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("立即刷新")
        self.refresh_btn.clicked.connect(self.refresh)
        row2_layout.addWidget(self.refresh_btn)
        
        self.kill_high_btn = QPushButton("关闭所选高负荷进程")
        self.kill_high_btn.clicked.connect(self.kill_high_load)
        self.kill_high_btn.setStyleSheet("QPushButton { background-color: #C05000; color: white; }")
        row2_layout.addWidget(self.kill_high_btn)
        
        row2_layout.addStretch()
        
        # 暂停/恢复刷新
        self.pause_btn = QPushButton("暂停刷新")
        self.pause_btn.clicked.connect(self.toggle_refresh)
        row2_layout.addWidget(self.pause_btn)
        
        control_layout.addLayout(row2_layout)
        parent_layout.addWidget(control_group)
        
    def create_process_table(self, parent_layout):
        """创建进程表格"""
        table_group = QGroupBox("进程列表")
        table_layout = QVBoxLayout(table_group)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "进程名称", "PID", "CPU%", "内存(MB)", "状态", "运行时间", "操作"
        ])
        
        # 设置表格属性
        self.process_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.process_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.process_table.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 进程名称自适应
        self.process_table.setColumnWidth(1, 80)   # PID
        self.process_table.setColumnWidth(2, 80)   # CPU
        self.process_table.setColumnWidth(3, 100)  # 内存
        self.process_table.setColumnWidth(4, 80)   # 状态
        self.process_table.setColumnWidth(5, 120)  # 运行时间
        self.process_table.setColumnWidth(6, 120)  # 操作
        
        table_layout.addWidget(self.process_table)
        parent_layout.addWidget(table_group)
        
    def create_log_section(self, parent_layout):
        """创建日志区域"""
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        parent_layout.addWidget(log_group)
        
    def setup_timer(self):
        """设置定时器"""
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(3000)  # 默认3秒刷新
        
    def refresh(self):
        """刷新进程列表"""
        try:
            # 更新系统性能
            self.update_performance()
            
            # 获取进程列表
            sort_map = {"CPU使用率": "cpu", "内存使用": "memory", "进程名称": "name"}
            sort_by = sort_map.get(self.sort_combo.currentText(), "cpu")
            
            # 如果有搜索关键词，使用搜索功能
            search_text = self.search_input.text().strip()
            if search_text:
                self.current_processes = search_processes(search_text)
            else:
                self.current_processes = get_processes(sort_by)
                
            # 更新表格
            self.update_process_table()
            
        except Exception as e:
            self.log(f"刷新进程列表失败: {e}")
            
    def update_performance(self):
        """更新性能概览"""
        try:
            perf = get_system_performance()
            
            # 更新CPU
            cpu_percent = perf.get("cpu_percent", 0)
            self.cpu_card.value_label.setText(f"{cpu_percent}%")
            
            # 更新内存
            mem_percent = perf.get("memory_percent", 0)
            mem_used = perf.get("memory_used_gb", 0)
            mem_total = perf.get("memory_total_gb", 0)
            self.memory_card.value_label.setText(f"{mem_percent}% ({mem_used:.1f}/{mem_total:.1f}GB)")
            
            # 更新进程数
            proc_count = perf.get("process_count", 0)
            self.process_card.value_label.setText(str(proc_count))
            
        except Exception as e:
            from logging import getLogger
            getLogger(__name__).warning("更新性能概览失败: %s", e)
            
    def update_process_table(self):
        """更新进程表格"""
        self.process_table.setRowCount(len(self.current_processes))
        
        for i, proc in enumerate(self.current_processes):
            # 进程名称
            name_item = QTableWidgetItem(proc["name"])
            if proc["is_protected"]:
                name_item.setText(f"🔒 {proc['name']}")
            self.process_table.setItem(i, 0, name_item)
            
            # PID
            self.process_table.setItem(i, 1, QTableWidgetItem(str(proc["pid"])))
            
            # CPU使用率
            cpu_item = QTableWidgetItem(f"{proc['cpu_percent']}%")
            self.process_table.setItem(i, 2, cpu_item)
            
            # 内存使用
            mem_item = QTableWidgetItem(f"{proc['memory_mb']}")
            self.process_table.setItem(i, 3, mem_item)
            
            # 状态
            self.process_table.setItem(i, 4, QTableWidgetItem(proc["status"]))
            
            # 运行时间
            self.process_table.setItem(i, 5, QTableWidgetItem(proc["runtime"]))
            
            # 根据负荷级别设置行颜色
            if proc["level"] == "high":
                for col in range(6):
                    item = self.process_table.item(i, col)
                    if item:
                        item.setBackground(QColor("#FFE6E6"))  # 浅红色
            elif proc["level"] == "warning":
                for col in range(6):
                    item = self.process_table.item(i, col)
                    if item:
                        item.setBackground(QColor("#FFF3E0"))  # 浅橙色
                        
            # 操作按钮
            if not proc["is_protected"]:
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 5, 5, 5)
                
                kill_btn = QPushButton("终止")
                kill_btn.setFixedSize(50, 25)
                kill_btn.clicked.connect(lambda checked, pid=proc["pid"], name=proc["name"]: self.kill_process(pid, name))
                
                if proc["level"] == "high":
                    kill_btn.setStyleSheet("QPushButton { background-color: #C00000; color: white; }")
                elif proc["level"] == "warning":
                    kill_btn.setStyleSheet("QPushButton { background-color: #C05000; color: white; }")
                    
                action_layout.addWidget(kill_btn)
                self.process_table.setCellWidget(i, 6, action_widget)
            else:
                # 保护进程显示锁图标
                protected_widget = QWidget()
                protected_layout = QHBoxLayout(protected_widget)
                protected_layout.setContentsMargins(5, 5, 5, 5)
                protected_layout.addWidget(QLabel("🔒 受保护"))
                self.process_table.setCellWidget(i, 6, protected_widget)
                
    def kill_process(self, pid: int, name: str):
        """终止进程"""
        reply = QMessageBox.question(
            self, "确认终止",
            f"确定要终止进程 '{name}' (PID: {pid}) 吗？\n\n此操作可能导致数据丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = kill_process(pid)
                if success:
                    self.log(f"✅ 成功终止进程: {name} (PID: {pid})")
                else:
                    self.log(f"❌ 终止进程失败: {name} (PID: {pid})")
                    
                # 立即刷新
                self.refresh()
                
            except Exception as e:
                self.log(f"❌ 终止进程异常: {name} (PID: {pid}) - {e}")
                
    def kill_high_load(self):
        """终止所选高负荷进程"""
        selected_rows = sorted({index.row() for index in self.process_table.selectionModel().selectedRows()})
        selected_procs = []
        for row in selected_rows:
            if row >= len(self.current_processes):
                continue
            proc = self.current_processes[row]
            if proc["is_protected"]:
                continue
            if proc["level"] not in {"warning", "high"}:
                continue
            selected_procs.append(proc)
        
        if not selected_procs:
            QMessageBox.information(self, "提示", "请先在表格中选择要终止的高负荷进程")
            return
            
        proc_names = [f"{p['name']} (CPU: {p['cpu_percent']}%, 内存: {p['memory_mb']}MB)" 
                     for p in selected_procs[:5]]  # 最多显示5个
        
        reply = QMessageBox.question(
            self, "确认批量终止",
            f"将终止 {len(selected_procs)} 个已选高负荷进程：\n\n" +
            "\n".join(proc_names) +
            (f"\n... 还有 {len(selected_procs) - 5} 个" if len(selected_procs) > 5 else "") +
            "\n\n确定要全部终止吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = 0
                failed = 0
                for proc in selected_procs:
                    if kill_process(proc["pid"]):
                        success += 1
                    else:
                        failed += 1
                
                self.log(f"批量终止完成: 成功 {success} 个，失败 {failed} 个")
                
                # 立即刷新
                self.refresh()
                
            except Exception as e:
                self.log(f"❌ 批量终止异常: {e}")
                
    def on_search_changed(self, text):
        """搜索文本改变"""
        # 延迟搜索，避免频繁刷新
        if hasattr(self, 'search_timer'):
            self.search_timer.stop()
        else:
            self.search_timer = QTimer()
            self.search_timer.setSingleShot(True)
            self.search_timer.timeout.connect(self.refresh)
            
        self.search_timer.start(500)  # 500ms延迟
        
    def on_sort_changed(self, text):
        """排序方式改变"""
        self.refresh()
        
    def on_interval_changed(self, text):
        """刷新间隔改变"""
        interval_map = {"1秒": 1000, "3秒": 3000, "5秒": 5000}
        interval = interval_map.get(text, 3000)
        
        if self.refresh_timer.isActive():
            self.refresh_timer.start(interval)
            
    def toggle_refresh(self):
        """切换刷新状态"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            self.pause_btn.setText("恢复刷新")
            self.log("已暂停自动刷新")
        else:
            interval_map = {"1秒": 1000, "3秒": 3000, "5秒": 5000}
            interval = interval_map.get(self.interval_combo.currentText(), 3000)
            self.refresh_timer.start(interval)
            self.pause_btn.setText("暂停刷新")
            self.log("已恢复自动刷新")
            
    def log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        engine.log("INFO", f"[进程管理] {message}")
        
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
        # 限制日志行数
        if self.log_text.document().blockCount() > 100:
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10)
            cursor.removeSelectedText()
