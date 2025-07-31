import sys
import os
import platform
from pathlib import Path
from PySide6.QtGui import QFont
from PySide6.QtCore import QStandardPaths

def get_system_font():
    system = platform.system()
    if system == "Windows":
        return QFont("Microsoft YaHei", 9)
    elif system == "Darwin":
        return QFont("PingFang SC", 12)
    else:
        return QFont("Noto Sans CJK SC", 9)

def normalize_path(path):
    return str(Path(path).resolve())

def get_executable_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

def get_project_root():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

def ensure_directory(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def get_temp_dir():
    temp_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
    return Path(temp_dir) / "white_cat_toolbox"

def is_windows():
    return platform.system() == "Windows"

def is_macos():
    return platform.system() == "Darwin"

def is_linux():
    return platform.system() == "Linux"

def get_shell_command():
    if is_windows():
        return "cmd.exe"
    else:
        return "/bin/bash"

def build_command(tool_path, tool_command, parameters):
    command_parts = []
    
    if tool_command:
        if is_windows() and tool_command.endswith('.py'):
            command_parts.extend(["python", tool_command])
        else:
            command_parts.append(tool_command)
    else:
        command_parts.append(str(tool_path))
    
    for param_name, value in parameters.items():
        if isinstance(value, bool) and value:
            command_parts.append(param_name)
        elif isinstance(value, str) and value.strip():
            if ' ' in value:
                command_parts.extend([param_name, f'"{value}"'])
            else:
                command_parts.extend([param_name, value])
    
    return command_parts

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def clean_ansi_codes(text):
    """移除文本中的所有ANSI转义序列"""
    import re

    ansi_escape = re.compile(r'(?:'
                            r'\x1b\[[0-?]*[ -/]*[@-~]|'
                            r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|'
                            r'\x1b[@-Z\\-_]'
                            r')')
    return ansi_escape.sub('', text)

def clean_html_tags(text):
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def get_available_fonts():
    from PySide6.QtGui import QFontDatabase
    font_db = QFontDatabase()
    return font_db.families()

def scale_size(size, scale_factor=1.0):
    return int(size * scale_factor)

def get_config_dir():
    config_dir = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
    return ensure_directory(Path(config_dir) / "white_cat_toolbox")

def get_app_data_dir():
    """获取应用数据目录"""
    app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    return ensure_directory(Path(app_data_dir) / "white_cat_toolbox")

def get_cache_dir():
    cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    return ensure_directory(Path(cache_dir) / "white_cat_toolbox")

def validate_python_path(python_path):
    try:
        import subprocess
        result = subprocess.run(
            [python_path, "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def get_python_version(python_path):
    try:
        import subprocess
        result = subprocess.run(
            [python_path, "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "Unknown"

def create_startup_info():
    if is_windows():
        import subprocess
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None