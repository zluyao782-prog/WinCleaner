#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口布局与导航
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QListWidget, QListWidgetItem,
    QLabel, QFrame, QStatusBar, QPlainTextEdit,
    QPushButton, QSplitter, QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

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
        self.log_records = []
        self.init_ui()
        self.setup_connections()
        self.activate_page(0)
        
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
        main_layout.addWidget(self.content_container, 1)
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置样式
        self.set_styles()
        
    def create_navigation(self):
        """创建导航栏"""
        self.nav_frame = QFrame()
        self.nav_frame.setFixedWidth(224)
        self.nav_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        
        nav_layout = QVBoxLayout(self.nav_frame)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        
        # 标题
        title_label = QLabel("WinCleaner")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        nav_layout.addWidget(title_label)

        subtitle_label = QLabel("Windows maintenance suite")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setObjectName("NavSubtitle")
        nav_layout.addWidget(subtitle_label)
        
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
        self.content_container = QWidget()
        self.content_container.setObjectName("ContentContainer")
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        self.page_header = QFrame()
        self.page_header.setObjectName("PageHeader")
        header_layout = QHBoxLayout(self.page_header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(10)

        self.page_title_label = QLabel("系统信息")
        self.page_title_label.setObjectName("PageTitle")
        header_layout.addWidget(self.page_title_label)
        header_layout.addStretch()

        self.page_hint_label = QLabel("查看系统状态与关键维护能力")
        self.page_hint_label.setObjectName("PageHint")
        header_layout.addWidget(self.page_hint_label)
        content_layout.addWidget(self.page_header)

        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setObjectName("ContentSplitter")
        content_layout.addWidget(self.content_splitter)

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

        self.content_splitter.addWidget(self.content_widget)
        self.create_log_panel()
        self.content_splitter.setSizes([560, 180])
            
        # 默认显示第一页
        self.content_widget.setCurrentIndex(0)
        self.nav_list.setCurrentRow(0)

    def create_log_panel(self):
        """创建全局日志面板"""
        log_panel = QFrame()
        log_layout = QVBoxLayout(log_panel)
        log_layout.setContentsMargins(12, 12, 12, 12)
        log_layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_label = QLabel("运行日志")
        header_font = QFont()
        header_font.setPointSize(13)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        self.log_level_filter = QComboBox()
        self.log_level_filter.addItems(["全部", "INFO", "WARNING", "ERROR"])
        self.log_level_filter.currentTextChanged.connect(self.refresh_global_log_view)
        header_layout.addWidget(self.log_level_filter)

        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_global_logs)
        header_layout.addWidget(export_btn)

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear_global_logs)
        header_layout.addWidget(clear_btn)
        log_layout.addLayout(header_layout)

        self.global_log_text = QPlainTextEdit()
        self.global_log_text.setReadOnly(True)
        self.global_log_text.setMaximumBlockCount(500)
        log_layout.addWidget(self.global_log_text)

        self.content_splitter.addWidget(log_panel)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 权限状态
        admin_status = "管理员权限" if engine.is_admin() else "普通用户"
        self.status_bar.addPermanentWidget(QLabel(f"权限: {admin_status}"))

        self.status_log_label = QLabel("就绪")
        self.status_log_label.setMinimumWidth(420)
        self.status_bar.addWidget(self.status_log_label, 1)
        
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
        engine.log_message.connect(self.append_global_log)
        
    def on_nav_changed(self, index):
        """导航切换事件"""
        self.activate_page(index)

    def activate_page(self, index: int):
        """激活当前页面，并停止隐藏页面的后台刷新。"""
        self.content_widget.setCurrentIndex(index)
        page_names = list(self.pages.keys())
        page_hints = {
            "系统信息": "查看系统状态与关键维护能力",
            "更新控制": "谨慎执行系统更新相关操作",
            "磁盘分析": "快速定位空间占用与大文件",
            "垃圾清理": "先预览，再排除，再清理",
            "进程管理": "仅处理你明确选择的高负荷进程",
        }

        for page in self.pages.values():
            if hasattr(page, "set_active"):
                page.set_active(False)

        current_name = page_names[index]
        current_page = self.pages[current_name]
        if hasattr(current_page, "set_active"):
            current_page.set_active(True)
        elif hasattr(current_page, "refresh"):
            current_page.refresh()

        self.page_title_label.setText(current_name)
        self.page_hint_label.setText(page_hints.get(current_name, ""))

    def append_global_log(self, level: str, message: str):
        """追加全局日志。"""
        line = f"[{level}] {message}"
        self.log_records.append((level, message, line))
        self.refresh_global_log_view()
        compact = line.replace("\n", " ")
        self.status_log_label.setText(compact[:120])

    def clear_global_logs(self):
        """清空全局日志面板。"""
        self.log_records.clear()
        self.global_log_text.clear()
        self.status_log_label.setText("日志已清空")

    def refresh_global_log_view(self):
        """按当前过滤条件刷新日志面板。"""
        current_filter = self.log_level_filter.currentText()
        self.global_log_text.clear()
        for level, _, line in self.log_records:
            if current_filter != "全部" and level != current_filter:
                continue
            self.global_log_text.appendPlainText(line)

    def export_global_logs(self):
        """导出当前日志面板内容。"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出运行日志",
            "wincleaner-log.txt",
            "Text Files (*.txt);;All Files (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.global_log_text.toPlainText())
            self.status_log_label.setText(f"日志已导出: {path}")
        except Exception as e:
            self.status_log_label.setText(f"日志导出失败: {e}")
            
    def set_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #eef2f6;
            }
            
            QFrame {
                background-color: white;
                border: 1px solid #d8e0ea;
                border-radius: 14px;
            }

            QFrame#ContentContainer {
                background: transparent;
                border: none;
            }

            QFrame#PageHeader {
                background-color: #f9fbfc;
                border: 1px solid #d8e0ea;
                border-radius: 16px;
            }

            QLabel#PageTitle {
                font-size: 28px;
                font-weight: 700;
                color: #18324a;
            }

            QLabel#PageHint {
                color: #66788a;
                font-size: 13px;
            }

            QLabel#NavSubtitle {
                color: #c6d3df;
                font-size: 11px;
                letter-spacing: 0.5px;
            }
            
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            
            QListWidget::item {
                padding: 14px 16px;
                border-radius: 10px;
                margin: 4px 2px;
                color: #d8e4ed;
                background-color: transparent;
            }
            
            QListWidget::item:selected {
                background-color: #f4f8fb;
                color: #153047;
                font-weight: 600;
            }

            QListWidget::item:selected:active {
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.12);
            }
            
            QLabel {
                color: #333;
            }

            QPushButton {
                background-color: #e7eef5;
                border: 1px solid #cfd9e3;
                border-radius: 10px;
                padding: 8px 14px;
                color: #18324a;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #dde7f0;
            }

            QPushButton:pressed {
                background-color: #d1dce7;
            }

            QPushButton#PrimaryButton {
                background-color: #2f6b9a;
                border: 1px solid #24597f;
                color: white;
            }

            QPushButton#PrimaryButton:hover {
                background-color: #255c86;
            }

            QPushButton#DangerButton {
                background-color: #c65443;
                border: 1px solid #a84435;
                color: white;
            }

            QPushButton#DangerButton:hover {
                background-color: #b64a3a;
            }

            QPushButton#SuccessButton {
                background-color: #2d7a57;
                border: 1px solid #236246;
                color: white;
            }

            QPushButton#SuccessButton:hover {
                background-color: #256a4c;
            }

            QPushButton#SubtleButton {
                background-color: #f4f7fa;
                border: 1px solid #d8e0ea;
                color: #31506a;
            }

            QPushButton#SubtleButton:hover {
                background-color: #eaf0f5;
            }

            QLineEdit, QComboBox, QSpinBox, QTextEdit, QTableWidget, QGroupBox {
                border-radius: 12px;
            }

            QGroupBox {
                margin-top: 10px;
                padding-top: 14px;
                font-weight: 600;
                color: #18324a;
                border: 1px solid #d8e0ea;
                background-color: #fbfcfd;
            }

            QPlainTextEdit {
                background-color: #FAFBFD;
                border: 1px solid #D8E0EA;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #d8e0ea;
                gridline-color: #edf2f7;
                selection-background-color: #e7f0f8;
                selection-color: #18324a;
            }

            QHeaderView::section {
                background-color: #f3f7fa;
                border: none;
                border-bottom: 1px solid #d8e0ea;
                padding: 8px;
                color: #526679;
                font-weight: 600;
            }

            QProgressBar {
                border: 1px solid #d8e0ea;
                border-radius: 8px;
                background-color: #f4f7fa;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #2f6b9a;
                border-radius: 7px;
            }

            QSplitter::handle {
                background-color: #d8e0ea;
                height: 2px;
            }
            
            QStatusBar {
                background-color: #f8fafc;
                border-top: 1px solid #d8e0ea;
            }
        """)

        self.nav_frame.setStyleSheet("""
            QFrame {
                background-color: #17324a;
                border: none;
                border-radius: 0;
            }
            QLabel {
                color: #f3f7fa;
            }
        """)
