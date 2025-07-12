import os
import platform
import json
import shlex
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

def build_cross_platform_command(tool_path, user_command, params):
    
    try:
        command_parts = shlex.split(user_command)
    except ValueError:
        command_parts = user_command.split()
    
    system = platform.system()
    
    if len(command_parts) >= 2 and command_parts[0] in ["python", "python3", "python.exe"]:
        script_name = command_parts[1]
        full_script_path = os.path.join(tool_path, script_name)
        
        if system == "Windows":
            full_script_path = full_script_path.replace('/', '\\')
        
        command = [command_parts[0], full_script_path] + command_parts[2:]
        
        if params:
            command.extend(params)
        
        return command
        
    elif len(command_parts) >= 1:
        exe_name = command_parts[0]
        full_exe_path = os.path.join(tool_path, exe_name)
        
        if system == "Windows":
            full_exe_path = full_exe_path.replace('/', '\\')
        
        command = [full_exe_path] + command_parts[1:]
        
        if params:
            command.extend(params)
        
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