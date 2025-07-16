import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
class TerminalLogManager:
    
    
    def __init__(self, tool_name: str, process_name: str, project_root: Optional[str] = None):
        self.tool_name = tool_name
        self.process_name = process_name
        if project_root is None:

            current_file = Path(__file__)
            self.project_root = current_file.parent.parent
        else:
            self.project_root = Path(project_root)
        self.log_base_dir = self.project_root / "logs"
        self.tool_log_dir = self.log_base_dir / self.tool_name
        self.process_log_dir = self.tool_log_dir / self.process_name
        self._create_log_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = self.process_log_dir / f"terminal_log_{timestamp}.txt"
        self.system_log_file_path = self.process_log_dir / f"system_log_{timestamp}.txt"
        self.log_file = None
        self.system_log_file = None
        self._initialize_log_files()
    
    def _create_log_directories(self):
        
        try:
            self.process_log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create log directories: {e}")
    
    def _initialize_log_files(self):
        
        try:

            self.log_file = open(self.log_file_path, 'w', encoding='utf-8')
            self.log_file.write(f"=== Terminal Log for {self.tool_name} - {self.process_name} ===\n")
            self.log_file.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.log_file.write("=" * 60 + "\n\n")
            self.log_file.flush()
            self.system_log_file = open(self.system_log_file_path, 'w', encoding='utf-8')
            self.system_log_file.write(f"=== System Log for {self.tool_name} - {self.process_name} ===\n")
            self.system_log_file.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.system_log_file.write("=" * 60 + "\n\n")
            self.system_log_file.flush()
            
        except Exception as e:
            print(f"Failed to initialize log files: {e}")
    
    def log_terminal_output(self, text: str, output_type: str = "output"):
        if not self.log_file or not text.strip():
            return
        
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            clean_text = self._clean_ansi_codes(text)
            clean_text = self._clean_html_tags(clean_text)
            if not clean_text.strip():
                return
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
        
        import re

        html_tag_pattern = re.compile(r'<[^>]+>')
        clean_text = html_tag_pattern.sub('', text)

        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        clean_text = clean_text.replace('<br>', '\n').replace('<br/>', '\n')
        return clean_text
    
    def log_system_event(self, message: str, level: str = "info"):
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
        
        import re

        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def close(self):
        
        try:
            if self.log_file:
                self.log_file.write(f"\n=== Session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                self.log_file.flush()
                self.log_file.close()
                self.log_file = None
            
            if self.system_log_file:
                self.system_log_file.write(f"\n=== Session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                self.system_log_file.flush()
                self.system_log_file.close()
                self.system_log_file = None
                
        except Exception as e:
            print(f"Failed to close log files: {e}")
    
    def force_flush(self):
        
        try:
            if self.log_file:
                self.log_file.flush()
            if self.system_log_file:
                self.system_log_file.flush()
        except Exception as e:
            print(f"Failed to flush log files: {e}")
    
    def get_log_info(self) -> Dict[str, Any]:
        
        return {
            "tool_name": self.tool_name,
            "process_name": self.process_name,
            "log_directory": str(self.process_log_dir),
            "terminal_log_file": str(self.log_file_path),
            "system_log_file": str(self.system_log_file_path),
            "created_at": datetime.now().isoformat()
        }
    
    def __del__(self):
        
        self.close() 