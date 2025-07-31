# -*- coding: utf-8 -*-
"""
White Cat Toolbox - 主模块包

这个包包含了WCT应用程序的所有核心模块：
- main_window: 主窗口界面
- floating_toolbar: 浮动工具栏
- tool_operation: 工具操作界面
- terminal_area: 终端区域
- process: 进程管理
- tool_scanner: 工具扫描器
- config: 配置管理
- utils: 工具函数
"""

__version__ = '1.0.0'
__author__ = 'WCT Team'
__description__ = 'White Cat Toolbox - 多功能工具集成平台'

# 导入主要类和函数
from .main_window import MainWindow
from .floating_toolbar import FloatingToolBar
from .tool_operation import ToolOperationWidget
from .terminal_area import TerminalArea
from .process import ProcessManager, OutputProcessor
from .tool_scanner import ToolScanner, ToolInfo
from .config import ConfigManager
from .utils import (
    is_windows, is_linux, is_macos,
    get_system_font, normalize_path,
    get_temp_dir, get_config_dir,
    clean_ansi_codes, clean_html_tags
)

__all__ = [
    'MainWindow',
    'FloatingToolBar', 
    'ToolOperationWidget',
    'TerminalArea',
    'ProcessManager',
    'OutputProcessor',
    'ToolScanner',
    'ToolInfo',
    'ConfigManager',
    'is_windows',
    'is_linux', 
    'is_macos',
    'get_system_font',
    'normalize_path',
    'get_temp_dir',
    'get_config_dir',
    'clean_ansi_codes',
    'clean_html_tags'
]