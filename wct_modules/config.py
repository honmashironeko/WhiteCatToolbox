import os
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .utils import get_project_root, get_resource_path, get_app_data_dir, ensure_directory

class ConfigManager:
    def __init__(self):
        self.project_root = get_project_root()
        self.tools_dir = self._find_tools_dir()
        self.config_dir = self._find_config_dir()
        self.user_config_dir = get_app_data_dir()
        
        self.app_config_path = self.user_config_dir / "app_config.json"
        
        self.ensure_directories()
        self.load_app_config()
        
    def _find_tools_dir(self):
        potential_paths = [
            self.project_root / "tools",
            get_resource_path("tools"),
            Path(os.path.dirname(__file__)).parent / "tools"
        ]
        
        for path in potential_paths:
            if path.exists() and path.is_dir():
                return path
        
        return self.project_root / "tools"
    
    def _find_config_dir(self):
        potential_paths = [
            self.project_root / "config",
            get_resource_path("config"),
            Path(os.path.dirname(__file__)).parent / "config"
        ]
        
        for path in potential_paths:
            if path.exists() and path.is_dir():
                return path
        
        return self.project_root / "config"
        
    def ensure_directories(self):
        ensure_directory(self.user_config_dir)
        if not self.tools_dir.exists():
            ensure_directory(self.tools_dir)
        if not self.config_dir.exists():
            ensure_directory(self.config_dir)
        
    def load_app_config(self):
        default_config = {
            "ui_settings": {
                "scale_factor": 1.0,
                "theme": "blue_white",
                "language": "zh_CN",
                "font_scale": 1.0
            },
            "tool_command": {},
            "paths": {
                "tools_dir": str(self.tools_dir),
                "config_dir": str(self.config_dir)
            }
        }
        
        if self.app_config_path.exists():
            try:
                with open(self.app_config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                for key, value in default_config.items():
                    if key not in loaded_config:
                        loaded_config[key] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in loaded_config[key]:
                                loaded_config[key][sub_key] = sub_value
                
                self.app_config = loaded_config
            except Exception as e:
                print(f"加载配置失败，使用默认配置: {e}")
                self.app_config = default_config
        else:
            self.app_config = default_config
            self.save_app_config()
            
    def save_app_config(self):
        try:
            ensure_directory(self.app_config_path.parent)
            with open(self.app_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
            
    def scan_tools(self) -> Dict[str, Dict[str, Any]]:
        tools = {}
        
        if not self.tools_dir.exists():
            print(f"工具目录不存在: {self.tools_dir}")
            return tools
            
        try:
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
        except Exception as e:
            print(f"扫描工具目录失败: {e}")
                        
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