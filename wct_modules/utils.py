import os
import sys
import platform
import json
import shlex
import subprocess
from pathlib import Path
from .i18n import t

def get_system_font():
    
    system = platform.system()
    if system == "Windows":
        return "Microsoft YaHei"
    elif system == "Darwin":  
        return "PingFang SC"
    else:  
        return "DejaVu Sans"

def get_monospace_font():
    
    system = platform.system()
    if system == "Windows":
        return "Consolas"
    elif system == "Darwin":  
        return "Monaco"
    else:  
        return "DejaVu Sans Mono"

def get_system_font_css():
    
    system_font = get_system_font()
    return f"font-family: '{system_font}', Arial, sans-serif;"

def get_monospace_font_css():
    
    mono_font = get_monospace_font()
    return f"font-family: '{mono_font}', 'Consolas', 'Monaco', 'Courier New', monospace;"

def normalize_path_separators(path, system):
    """
    Normalize path separators based on the operating system.
    Only converts paths that look like file paths (contain / or \).
    """
    if not path or not isinstance(path, str):
        return path

    if ('/' in path or '\\' in path) and not path.startswith(('http://', 'https://', 'ftp://')):
        if system == "Windows":

            return path.replace('/', '\\')
        else:

            return path.replace('\\', '/')
    
    return path

def build_cross_platform_command(tool_path, user_command, params):
    
    system = platform.system()

    BACKSLASH_PLACEHOLDER = "<<BACKSLASH>>"
    if system == "Windows":
        user_command_safe = user_command.replace('\\', BACKSLASH_PLACEHOLDER)
    else:
        user_command_safe = user_command
    
    try:
        command_parts = shlex.split(user_command_safe)
    except ValueError:
        command_parts = user_command_safe.split()

    if system == "Windows":
        command_parts = [part.replace(BACKSLASH_PLACEHOLDER, '\\') for part in command_parts]
    
    if len(command_parts) >= 2 and command_parts[0] in ["python", "python3", "python.exe"]:
        script_name = command_parts[1]

        if os.path.isabs(script_name):

            full_script_path = script_name
        else:

            full_script_path = script_name

        full_script_path = normalize_path_separators(full_script_path, system)

        processed_args = []
        for arg in command_parts[2:]:
            processed_args.append(normalize_path_separators(arg, system))
        
        command = [command_parts[0], full_script_path] + processed_args
        
        if params:

            normalized_params = [normalize_path_separators(p, system) for p in params]
            command.extend(normalized_params)
        
        return command
        
    elif len(command_parts) >= 1:
        exe_name = command_parts[0]

        if os.path.isabs(exe_name):

            full_exe_path = exe_name
        else:

            full_exe_path = exe_name

        full_exe_path = normalize_path_separators(full_exe_path, system)

        processed_args = []
        for arg in command_parts[1:]:
            processed_args.append(normalize_path_separators(arg, system))
        
        command = [full_exe_path] + processed_args
        
        if params:

            normalized_params = [normalize_path_separators(p, system) for p in params]
            command.extend(normalized_params)
        
        return command
    else:
        raise ValueError(t("unable_to_parse_command"))

def setup_workspace_path():
    
    _workspace_root = os.path.abspath(os.path.dirname(__file__))
    _existing_pythonpath = os.environ.get("PYTHONPATH", "")
    if _workspace_root not in _existing_pythonpath.split(os.pathsep):
        os.environ["PYTHONPATH"] = (
            _workspace_root + (os.pathsep + _existing_pythonpath if _existing_pythonpath else "")
        )
    try:
        import importlib
        importlib.import_module("sitecustomize")
    except Exception:
        pass

SCALE_FACTOR = 1.0

def load_scale_factor():
    
    global SCALE_FACTOR
    try:
        if os.path.exists("config/app_config.json"):
            with open("config/app_config.json", "r") as f:
                config = json.load(f)
                ui_settings = config.get("ui_settings", {})
                factor = ui_settings.get("scale_factor", 1.0)
        else:
            factor = 1.0
            
        if isinstance(factor, (int, float)) and factor > 0:
            SCALE_FACTOR = float(factor)
        else:
            SCALE_FACTOR = 1.0
    except (FileNotFoundError, json.JSONDecodeError):
        SCALE_FACTOR = 1.0
    return SCALE_FACTOR

def save_scale_factor(factor):
    
    global SCALE_FACTOR
    if isinstance(factor, (int, float)) and factor > 0:
        SCALE_FACTOR = float(factor)
        config = {}
        if os.path.exists("config/app_config.json"):
            try:
                with open("config/app_config.json", "r") as f:
                    config = json.load(f)
            except:
                config = {}
        if "ui_settings" not in config:
            config["ui_settings"] = {}
        config["ui_settings"]["scale_factor"] = SCALE_FACTOR
        os.makedirs("config", exist_ok=True)
        with open("config/app_config.json", "w") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

def s(value):
    
    return int(value * SCALE_FACTOR)

load_scale_factor() 

def get_optimized_subprocess_kwargs():
    """获取优化的subprocess启动参数"""
    kwargs = {}
    
    if platform.system() == "Windows":
        # Windows下隐藏控制台窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs['startupinfo'] = startupinfo
        
        # 设置创建标志
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    return kwargs 