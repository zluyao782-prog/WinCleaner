#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心调度层：任务队列、日志记录、异常处理
"""

import logging
import os
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List
from PyQt6.QtCore import QObject, pyqtSignal


class CoreEngine(QObject):
    """核心引擎类，负责统一调度和管理"""
    
    # 信号定义
    task_started = pyqtSignal(str)  # 任务开始
    task_completed = pyqtSignal(str, object)  # 任务完成
    task_failed = pyqtSignal(str, str)  # 任务失败
    log_message = pyqtSignal(str, str)  # 日志消息 (level, message)
    
    def __init__(self):
        super().__init__()
        self.setup_logging()
        self.task_queue = []
        self.is_running = False
        
    def setup_logging(self):
        """设置日志系统"""
        # 创建logs目录
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        # 配置日志
        log_filename = f"logs/wincleaner_{datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log(self, level: str, message: str):
        """记录日志"""
        if level.upper() == "INFO":
            self.logger.info(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        elif level.upper() == "ERROR":
            self.logger.error(message)
        elif level.upper() == "DEBUG":
            self.logger.debug(message)
            
        # 发送信号到UI
        self.log_message.emit(level, message)
        
    def execute_task(self, task_name: str, func: Callable, *args, **kwargs) -> Any:
        """执行任务"""
        self.task_started.emit(task_name)
        self.log("INFO", f"开始执行任务: {task_name}")
        
        try:
            result = func(*args, **kwargs)
            self.task_completed.emit(task_name, result)
            self.log("INFO", f"任务完成: {task_name}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.task_failed.emit(task_name, error_msg)
            self.log("ERROR", f"任务失败: {task_name} - {error_msg}")
            raise
            
    def execute_async(self, task_name: str, func: Callable, *args, **kwargs):
        """异步执行任务"""
        def worker():
            self.execute_task(task_name, func, *args, **kwargs)
            
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        
    def is_admin(self) -> bool:
        """检查是否具有管理员权限"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False


# 全局引擎实例
engine = CoreEngine()