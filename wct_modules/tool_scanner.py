import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .utils import normalize_path, get_system_font

class ToolInfo:
    def __init__(self, name: str, path: str, config_data: Dict[str, Any]):
        self.name = name
        self.path = path
        self.config_data = config_data
        self.display_name = config_data.get('display_name', name)
        self.description = config_data.get('description', '')
        self.category = config_data.get('category', '未分类')
        self.version = config_data.get('version', '1.0.0')
        self.author = config_data.get('author', '')
        self.icon = config_data.get('icon', '')
        self.executable = config_data.get('executable', '')
        self.script_path = config_data.get('script_path', 'main.py')
        self.parameters = config_data.get('parameters', {})
        self.parameter_order = config_data.get('parameter_order', {})
        self.environment = config_data.get('environment', {})
        self.dependencies = config_data.get('dependencies', [])
        self.tags = config_data.get('tags', [])
        self.enabled = config_data.get('enabled', True)
        
    def get_executable_path(self) -> str:
        if os.path.isabs(self.executable):
            return self.executable
        return os.path.join(self.path, self.executable)
        
    def get_icon_path(self) -> str:
        if not self.icon:
            return ''
        if os.path.isabs(self.icon):
            return self.icon
        return os.path.join(self.path, self.icon)
        
    def has_required_files(self) -> bool:
        if self.executable.endswith('.py') or self.executable == 'python':
            if os.path.isabs(self.script_path):
                return os.path.exists(self.script_path)
            else:
                return os.path.exists(os.path.join(self.path, self.script_path))
        else:
            executable_path = self.get_executable_path()
            return os.path.exists(executable_path)
        
    def get_parameter_groups(self) -> Dict[str, List[Dict]]:
        groups = {}
        

        for group_name, param_order in self.parameter_order.items():
            if group_name not in groups:
                groups[group_name] = []
            

            for param_name in param_order:
                if param_name in self.parameters:
                    param_config = self.parameters[param_name]
                    

                    param_copy = param_config.copy()
                    param_copy['name'] = param_name
                    

                    should_add = False
                    if param_config.get('group') == group_name:

                        should_add = True
                    elif param_config.get('original_group') == group_name:

                        param_copy['group'] = group_name
                        should_add = True
                    
                    if should_add:
                        groups[group_name].append(param_copy)
        

        for param_name, param_config in self.parameters.items():
            group = param_config.get('group', '基本参数')
            

            if group not in groups:
                groups[group] = []
            

            param_exists = any(p['name'] == param_name for p in groups[group])
            if not param_exists:
                param_copy = param_config.copy()
                param_copy['name'] = param_name
                groups[group].append(param_copy)
            

            original_group = param_config.get('original_group')
            if original_group and original_group != group:
                if original_group not in groups:
                    groups[original_group] = []
                

                param_exists_in_original = any(p['name'] == param_name for p in groups[original_group])
                if not param_exists_in_original:
                    original_param_copy = param_config.copy()
                    original_param_copy['name'] = param_name
                    original_param_copy['group'] = original_group
                    groups[original_group].append(original_param_copy)
                
        return groups
        
class ToolScanner:
    def __init__(self, tools_directory: str = None):
        self.tools_directory = Path(tools_directory) if tools_directory else None
        self.tools: Dict[str, ToolInfo] = {}
        self.categories: Dict[str, List[str]] = {}
        
    def scan_tools(self, tools_directory: str = None) -> Dict[str, ToolInfo]:
        if tools_directory:
            self.tools_directory = Path(tools_directory)
            
        self.tools.clear()
        self.categories.clear()
        
        if not self.tools_directory or not self.tools_directory.exists():
            print(f"工具目录不存在: {self.tools_directory}")
            return self.tools
        

        app_config_file = self.tools_directory.parent / 'config' / 'app_config.json'
        tool_commands = {}
        if app_config_file.exists():
            try:
                with open(app_config_file, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
                    tool_commands = app_config.get('tool_command', {})
            except Exception:
                pass
            
        for tool_dir in self.tools_directory.iterdir():
            if tool_dir.is_dir():
                self._scan_tool_directory(tool_dir, tool_commands)
                
        self._organize_categories()
        return self.tools
        

            
    def _parse_config_file(self, config_file: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if content.startswith('{'):
                return json.loads(content)
            elif content.startswith('%'):
                return self._parse_wct_style_config(content)
            else:
                return self._parse_ini_style_config(content)
                
        except Exception as e:
            print(f"解析配置文件 {config_file} 失败: {e}")
            return None
            
    def _parse_ini_style_config(self, content: str) -> Dict[str, Any]:
        config = {
            'parameters': {},
            'environment': {},
            'dependencies': [],
            'tags': []
        }
        
        current_section = None
        current_param = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].lower()
                continue
                
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if current_section == 'tool':
                    config[key] = value
                elif current_section == 'parameters':
                    if key.startswith('param_'):
                        param_name = key[6:]
                        current_param = param_name
                        config['parameters'][param_name] = {'type': value}
                    elif current_param and key in ['description', 'default', 'required', 'group']:
                        if key == 'required':
                            value = value.lower() in ['true', '1', 'yes']
                        config['parameters'][current_param][key] = value
                elif current_section == 'environment':
                    config['environment'][key] = value
                elif current_section == 'dependencies':
                    if value:
                        config['dependencies'].append(value)
                elif current_section == 'tags':
                    if value:
                        config['tags'].extend([tag.strip() for tag in value.split(',')])
                        
        return config
        
    def _parse_wct_style_config(self, content: str) -> Dict[str, Any]:
        """解析WCT自定义格式的配置文件"""
        config = {
            'display_name': '',
            'description': '',
            'category': '未分类',
            'version': '1.0.0',
            'author': 'Unknown',
            'executable': 'python',
            'script_path': 'main.py',
            'parameters': {},
            'parameter_order': {},
            'environment': {},
            'dependencies': [],
            'tags': []
        }
        
        current_group = None
        current_section = None
        group_param_order = {}
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                

            if line.startswith('%') and not line.startswith('%%'):
                current_group = line[1:].strip()
                if current_group not in group_param_order:
                    group_param_order[current_group] = []
                continue
                

            if line.startswith('%%'):
                current_section = line[2:].strip()
                continue
                

            if '=' in line:
                parts = line.split('=')
                if len(parts) >= 4:
                    param_name = parts[0].strip()
                    display_name = parts[1].strip()
                    description = parts[2].strip()
                    required_str = parts[3].strip()
                    

                    if current_group and current_group in group_param_order:
                        if param_name not in group_param_order[current_group]:
                            group_param_order[current_group].append(param_name)
                    

                    param_key = f"{param_name}_{current_group}" if current_group else param_name
                    


                    param_key = param_name
                    

                    param_type = 'boolean' if current_section == '勾选项' else 'string'
                    

                    required = required_str == '1'
                    

                    default_value = False if param_type == 'boolean' else ''
                    

                    if param_name in config['parameters']:
                        existing_param = config['parameters'][param_name]

                        if existing_param.get('group') != '常用参数' and current_group == '常用参数':

                            existing_param['original_group'] = existing_param.get('group', '默认')
                            existing_param['group'] = current_group or '默认'

                        elif existing_param.get('group') == '常用参数' and current_group != '常用参数':

                            if not existing_param.get('original_group'):
                                existing_param['original_group'] = current_group or '默认'
                            continue

                        else:
                            config['parameters'][param_name] = {
                                'type': param_type,
                                'display_name': display_name,
                                'description': description,
                                'default': default_value,
                                'required': required,
                                'group': current_group or '默认'
                            }
                    else:

                        config['parameters'][param_name] = {
                            'type': param_type,
                            'display_name': display_name,
                            'description': description,
                            'default': default_value,
                            'required': required,
                            'group': current_group or '默认'
                        }
        

        config['parameter_order'] = group_param_order
        return config
    
    def _scan_tool_directory(self, tool_dir: Path, tool_commands: Dict = None):
        config_file = tool_dir / 'wct_config.txt'
        if not config_file.exists():
            return
            
        try:
            config_data = self._parse_config_file(config_file)
            if config_data:
                tool_name = tool_dir.name
                

                if not config_data.get('display_name'):
                    config_data['display_name'] = tool_name
                

                if tool_commands and tool_name in tool_commands:
                    tool_cmd_config = tool_commands[tool_name]
                    config_data['executable'] = tool_cmd_config.get('executable', config_data.get('executable', 'python'))
                    config_data['script_path'] = tool_cmd_config.get('script_path', config_data.get('script_path', 'main.py'))
                
                tool_info = ToolInfo(tool_name, str(tool_dir), config_data)
                
                self._load_tool_app_config(tool_info)
                

                self.tools[tool_name] = tool_info
                if tool_info.has_required_files():
                    print(f"扫描到工具: {tool_info.display_name} ({tool_name})")
                else:
                    print(f"扫描到工具: {tool_info.display_name} ({tool_name}) - 需要配置执行文件")
                    
        except Exception as e:
            print(f"扫描工具 {tool_dir.name} 时出错: {e}")
    
    def _load_tool_app_config(self, tool_info):
        """从app_config.json加载工具配置数据"""
        try:
            from .utils import get_resource_path
            import json
            
            config_dir = get_resource_path('config')
            app_config_file = config_dir / 'app_config.json'
            
            if app_config_file.exists():
                with open(app_config_file, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
                    
                tool_name = tool_info.name
                if 'tool_command' in app_config and tool_name in app_config['tool_command']:
                    tool_config = app_config['tool_command'][tool_name]
                    
                    if not hasattr(tool_info, 'config_data') or not tool_info.config_data:
                        tool_info.config_data = {}
                    
                    if 'interpreter_type' in tool_config:
                        tool_info.config_data['interpreter_type'] = tool_config['interpreter_type']
                    if 'interpreter_path' in tool_config:
                        tool_info.config_data['interpreter_path'] = tool_config['interpreter_path']
                    if 'program_path' in tool_config:
                        tool_info.config_data['program_path'] = tool_config['program_path']
                    if 'env_type' in tool_config:
                        tool_info.config_data['env_type'] = tool_config['env_type']
                    if 'env_path' in tool_config:
                        tool_info.config_data['env_path'] = tool_config['env_path']
                    if 'env_vars' in tool_config:
                        tool_info.config_data['env_vars'] = tool_config['env_vars']
                        
        except Exception as e:
            print(f"加载工具 {tool_info.name} 的配置数据失败: {e}")
        
    def _organize_categories(self):
        for tool_name, tool_info in self.tools.items():
            category = tool_info.category
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(tool_name)
            
    def get_tools_by_category(self, category: str) -> List[ToolInfo]:
        if category not in self.categories:
            return []
        return [self.tools[tool_name] for tool_name in self.categories[category]]
        
    def get_tool(self, tool_name: str) -> Optional[ToolInfo]:
        return self.tools.get(tool_name)
        
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        return self.tools.get(tool_name)
        
    def get_all_tools(self) -> List[ToolInfo]:
        return list(self.tools.values())
        
    def get_all_categories(self) -> List[str]:
        return list(self.categories.keys())
        
    def search_tools(self, query: str) -> List[ToolInfo]:
        query = query.lower()
        results = []
        
        for tool_info in self.tools.values():
            if (query in tool_info.name.lower() or 
                query in tool_info.display_name.lower() or 
                query in tool_info.description.lower() or 
                any(query in tag.lower() for tag in tool_info.tags)):
                results.append(tool_info)
                
        return results
        
    def get_tools_count(self) -> int:
        return len(self.tools)
        
    def refresh_tool(self, tool_name: str) -> bool:
        if tool_name not in self.tools:
            return False
            
        tool_dir = Path(self.tools[tool_name].path)
        self._scan_tool_directory(tool_dir)
        return tool_name in self.tools
        
    def validate_tool_dependencies(self, tool_name: str) -> List[str]:
        if tool_name not in self.tools:
            return ["工具不存在"]
            
        tool_info = self.tools[tool_name]
        missing_deps = []
        
        for dep in tool_info.dependencies:
            if not self._check_dependency(dep):
                missing_deps.append(dep)
                
        return missing_deps
        
    def _check_dependency(self, dependency: str) -> bool:
        try:
            if dependency.startswith('python:'):
                module_name = dependency[7:]
                __import__(module_name)
                return True
            elif dependency.startswith('system:'):
                command = dependency[7:]
                import shutil
                return shutil.which(command) is not None
            else:
                return os.path.exists(dependency)
        except Exception:
            return False
            
    def export_tools_info(self, output_file: str):
        tools_data = {}
        for tool_name, tool_info in self.tools.items():
            tools_data[tool_name] = {
                'display_name': tool_info.display_name,
                'description': tool_info.description,
                'category': tool_info.category,
                'version': tool_info.version,
                'author': tool_info.author,
                'path': tool_info.path,
                'executable': tool_info.executable,
                'parameters': tool_info.parameters,
                'environment': tool_info.environment,
                'dependencies': tool_info.dependencies,
                'tags': tool_info.tags,
                'enabled': tool_info.enabled
            }
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tools_data, f, ensure_ascii=False, indent=2)
            
    def create_sample_tool(self, tool_name: str, tool_dir: str):
        tool_path = Path(tool_dir) / tool_name
        tool_path.mkdir(parents=True, exist_ok=True)
        
        config_content = f'''[tool]
display_name={tool_name}
description=示例工具
category=示例
version=1.0.0
author=WCT
executable=main.py

[parameters]
param_input=string
description=输入参数
default=
required=false
group=基本参数

[environment]
PYTHONUNBUFFERED=1

[dependencies]
python:sys

[tags]
tags=示例,测试
'''
        
        config_file = tool_path / 'wct_config.txt'
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
            
        main_file = tool_path / 'main.py'
        main_content = '''#!/usr/bin/env python3


import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='示例工具')
    parser.add_argument('--input', help='输入参数', default='')
    
    args = parser.parse_args()
    
    print(f"Hello from {sys.argv[0]}!")
    if args.input:
        print(f"输入参数: {args.input}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
'''
        
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
            
        print(f"示例工具已创建: {tool_path}")
        return str(tool_path)