"""
Terminal Log Manager for WhiteCat Toolbox
处理终端输出和系统日志的保存功能
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class TerminalLogManager:
    """终端日志管理器"""
    
    def __init__(self, tool_name: str, process_name: str, project_root: Optional[str] = None):
        """
        初始化日志管理器
        
        Args:
            tool_name: 工具名称
            process_name: 进程标签名称
            project_root: 项目根目录，默认为当前工作目录的父级
        """
        self.tool_name = tool_name
        self.process_name = process_name
        
        # 确定项目根目录
        if project_root is None:
            # 获取当前文件的父级目录的父级目录作为项目根目录
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 创建日志目录结构
        self.log_base_dir = self.project_root / "logs"
        self.tool_log_dir = self.log_base_dir / self.tool_name
        self.process_log_dir = self.tool_log_dir / self.process_name
        
        # 创建目录
        self._create_log_directories()
        
        # 生成日志文件名（基于时间）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = self.process_log_dir / f"terminal_log_{timestamp}.txt"
        self.system_log_file_path = self.process_log_dir / f"system_log_{timestamp}.txt"
        
        # 日志文件句柄
        self.log_file = None
        self.system_log_file = None
        
        # 初始化日志文件
        self._initialize_log_files()
    
    def _create_log_directories(self):
        """创建日志目录结构"""
        try:
            self.process_log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create log directories: {e}")
    
    def _initialize_log_files(self):
        """初始化日志文件"""
        try:
            # 创建终端日志文件
            self.log_file = open(self.log_file_path, 'w', encoding='utf-8')
            self.log_file.write(f"=== Terminal Log for {self.tool_name} - {self.process_name} ===\n")
            self.log_file.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log_file.write("=" * 60 + "\n\n")
            self.log_file.flush()
            
            # 创建系统日志文件
            self.system_log_file = open(self.system_log_file_path, 'w', encoding='utf-8')
            self.system_log_file.write(f"=== System Log for {self.tool_name} - {self.process_name} ===\n")
            self.system_log_file.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.system_log_file.write("=" * 60 + "\n\n")
            self.system_log_file.flush()
            
        except Exception as e:
            print(f"Failed to initialize log files: {e}")
    
    def log_terminal_output(self, text: str, output_type: str = "output"):
        """
        记录终端输出
        
        Args:
            text: 输出文本
            output_type: 输出类型 (output, input, error)
        """
        if not self.log_file or not text.strip():
            return
        
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 清理ANSI转义序列和HTML标签（保存纯文本）
            clean_text = self._clean_ansi_codes(text)
            clean_text = self._clean_html_tags(clean_text)
            
            # 跳过空行或只有空格的内容
            if not clean_text.strip():
                return
            
            # 格式化日志条目
            if output_type == "input":
                log_entry = f"[{timestamp}] INPUT: {clean_text}\n"
            elif output_type == "error":
                log_entry = f"[{timestamp}] ERROR: {clean_text}\n"
            else:
                log_entry = f"[{timestamp}] OUTPUT: {clean_text}\n"
            
            self.log_file.write(log_entry)
            self.log_file.flush()
            
        except Exception as e:
            print(f"Failed to log terminal output: {e}")
    
    def _clean_html_tags(self, text: str) -> str:
        """清理HTML标签"""
        import re
        # 移除HTML标签
        html_tag_pattern = re.compile(r'<[^>]+>')
        clean_text = html_tag_pattern.sub('', text)
        # 替换HTML实体
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        clean_text = clean_text.replace('<br>', '\n').replace('<br/>', '\n')
        return clean_text
    
    def log_system_event(self, message: str, level: str = "info"):
        """
        记录系统事件
        
        Args:
            message: 系统消息
            level: 日志级别 (info, warning, error, success)
        """
        if not self.system_log_file:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level.upper()}] {message}\n"
            
            self.system_log_file.write(log_entry)
            self.system_log_file.flush()
            
        except Exception as e:
            print(f"Failed to log system event: {e}")
    
    def _clean_ansi_codes(self, text: str) -> str:
        """清理ANSI转义序列"""
        import re
        # 移除ANSI转义序列
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def close(self):
        """关闭日志文件"""
        try:
            if self.log_file:
                self.log_file.write(f"\n=== Session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                self.log_file.flush()  # 确保数据写入磁盘
                self.log_file.close()
                self.log_file = None
            
            if self.system_log_file:
                self.system_log_file.write(f"\n=== Session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                self.system_log_file.flush()  # 确保数据写入磁盘
                self.system_log_file.close()
                self.system_log_file = None
                
        except Exception as e:
            print(f"Failed to close log files: {e}")
    
    def force_flush(self):
        """强制刷新所有日志文件到磁盘"""
        try:
            if self.log_file:
                self.log_file.flush()
            if self.system_log_file:
                self.system_log_file.flush()
        except Exception as e:
            print(f"Failed to flush log files: {e}")
    
    def get_log_info(self) -> Dict[str, Any]:
        """获取日志信息"""
        return {
            "tool_name": self.tool_name,
            "process_name": self.process_name,
            "log_directory": str(self.process_log_dir),
            "terminal_log_file": str(self.log_file_path),
            "system_log_file": str(self.system_log_file_path),
            "created_at": datetime.now().isoformat()
        }
    
    def __del__(self):
        """析构函数，确保文件被关闭"""
        self.close() 