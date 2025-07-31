import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .utils import get_project_root

class ConfigManager:
    def __init__(self):
        # 修复PyInstaller路径问题
        self.project_root = get_project_root()
        self.tools_dir = self.project_root / "tools"
        self.config_dir = self.project_root / "config"
        self.app_config_path = self.config_dir / "app_config.json"
        
        self.ensure_directories()
        self.load_app_config()
        
    def ensure_directories(self):
        self.tools_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
    def load_app_config(self):
        default_config = {
            "ui_settings": {
                "scale_factor": 1.0,
                "theme": "blue_white",
                "language": "zh_CN",
                "font_scale": 1.0
            },
            "tool_command": {}
        }
        
        if self.app_config_path.exists():
            try:
                with open(self.app_config_path, 'r', encoding='utf-8') as f:
                    self.app_config = json.load(f)
            except Exception:
                self.app_config = default_config
        else:
            self.app_config = default_config
            self.save_app_config()
            
    def save_app_config(self):
        try:
            with open(self.app_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
            
    def scan_tools(self) -> Dict[str, Dict[str, Any]]:
        tools = {}
        
        if not self.tools_dir.exists():
            return tools
            
        for item in self.tools_dir.iterdir():
            if item.is_dir():
                config_file = item / "wct_config.txt"
                if config_file.exists():
                    tool_config = self.parse_tool_config(config_file)
                    if tool_config:
                        tools[item.name] = {
                            'display_name': item.name,
                            'path': str(item),
                            'config': tool_config
                        }
                        
        return tools
        
    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        tool_path = self.tools_dir / tool_name
        config_file = tool_path / "wct_config.txt"
        
        if config_file.exists():
            return self.parse_tool_config(config_file)
        return {}
        
    def parse_tool_config(self, config_path: Path) -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._parse_config_content(content)
        except Exception as e:
            print(f"解析配置文件失败 {config_path}: {e}")
            return {}
            
    def _parse_config_content(self, content: str) -> Dict[str, Any]:
        config = {
            'common_params': {'checkboxes': [], 'inputs': []},
            'all_params': {'checkboxes': [], 'inputs': []}
        }
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        current_section = None
        current_type = None
        
        for line in lines:
            if line.startswith('%常用参数'):
                current_section = 'common_params'
                continue
            elif line.startswith('%全部参数'):
                current_section = 'all_params'
                continue
            elif line.startswith('%%勾选项'):
                current_type = 'checkboxes'
                continue
            elif line.startswith('%%输入项'):
                current_type = 'inputs'
                continue
            elif line.startswith('%') or line.startswith('%%'):
                continue
                
            if current_section and current_type and '=' in line:
                param_info = self._parse_param_line(line)
                if param_info:
                    config[current_section][current_type].append(param_info)
                    
        return config
        
    def _parse_param_line(self, line: str) -> Dict[str, str]:
        parts = line.split('=')
        if len(parts) >= 4:
            return {
                'param': parts[0].strip(),
                'display_name': parts[1].strip(),
                'description': parts[2].strip(),
                'required': parts[3].strip() == '1'
            }
        return None
        
    def get_tool_command(self, tool_name: str) -> str:
        return self.app_config.get('tool_command', {}).get(tool_name, '')
        
    def set_tool_command(self, tool_name: str, command: str):
        if 'tool_command' not in self.app_config:
            self.app_config['tool_command'] = {}
        self.app_config['tool_command'][tool_name] = command
        self.save_app_config()