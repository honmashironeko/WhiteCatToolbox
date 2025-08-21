import sys
import os
import platform
from pathlib import Path
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import QStandardPaths

def get_system_font():
    system = platform.system()
    if system == "Windows":
        return QFont("Microsoft YaHei", 9)
    elif system == "Darwin":
        fonts = ['SF Pro Display', 'PingFang SC', 'Helvetica Neue']
        for font in fonts:
            if QFontDatabase().hasFamily(font):
                return QFont(font, 12)
        return QFont("Arial", 12)
    else:
        fonts = ['Noto Sans CJK SC', 'DejaVu Sans', 'Liberation Sans', 'Arial']
        for font in fonts:
            if QFontDatabase().hasFamily(font):
                return QFont(font, 9)
        return QFont("Arial", 9)

def normalize_path(path):
    return str(Path(path).resolve())

def get_executable_path():
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        else:
            return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

def get_project_root():
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(sys.executable).parent
        
        for potential_root in [base_path, base_path.parent]:
            if (potential_root / "tools").exists() or (potential_root / "config").exists():
                return potential_root
        return base_path
    else:
        return Path(__file__).parent.parent

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent.parent
    
    resource_path = base_path / relative_path
    if resource_path.exists():
        return resource_path
    
    fallback_path = Path(sys.executable).parent / relative_path
    if fallback_path.exists():
        return fallback_path
    
    return resource_path

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
    elif is_macos():
        return "/bin/zsh"
    else:
        return "/bin/bash"

def get_python_executable():
    if is_windows():
        return "python"
    else:
        return "python3"

def get_system_python_executable():
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return get_python_executable()

def build_command(tool_path, tool_command, parameters):
    command_parts = []
    
    if tool_command:
        if tool_command.endswith('.py'):
            python_exe = get_system_python_executable()
            command_parts.extend([python_exe, tool_command])
        elif tool_command.endswith('.sh') and not is_windows():
            command_parts.extend(["/bin/bash", tool_command])
        elif tool_command.endswith('.bat') and is_windows():
            command_parts.extend(["cmd.exe", "/c", tool_command])
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
    app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    return ensure_directory(Path(app_data_dir) / "white_cat_toolbox")

def get_cache_dir():
    cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    return ensure_directory(Path(cache_dir) / "white_cat_toolbox")

def validate_python_path(python_path):
    try:
        import subprocess
        startupinfo = create_startup_info()
        result = subprocess.run(
            [python_path, "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            startupinfo=startupinfo
        )
        return result.returncode == 0
    except Exception:
        return False

def detect_available_python_interpreters():
    import shutil
    interpreters = []
    
    if is_windows():
        candidates = ['python.exe', 'python3.exe', 'py.exe']
    else:
        candidates = ['python3', 'python', 'python3.9', 'python3.10', 'python3.11', 'python3.12']
    
    for candidate in candidates:
        python_path = shutil.which(candidate)
        if python_path and validate_python_path(python_path):
            version = get_python_version(python_path)
            interpreters.append({
                'path': python_path,
                'version': version,
                'name': candidate
            })
    
    if is_windows():
        common_paths = [
            r'C:\Python39\python.exe',
            r'C:\Python310\python.exe', 
            r'C:\Python311\python.exe',
            r'C:\Python312\python.exe'
        ]
        
        username = os.environ.get('USERNAME', '')
        if username:
            user_paths = [
                fr'C:\Users\{username}\AppData\Local\Programs\Python\Python39\python.exe',
                fr'C:\Users\{username}\AppData\Local\Programs\Python\Python310\python.exe',
                fr'C:\Users\{username}\AppData\Local\Programs\Python\Python311\python.exe',
                fr'C:\Users\{username}\AppData\Local\Programs\Python\Python312\python.exe'
            ]
            common_paths.extend(user_paths)
        
        for path in common_paths:
            if os.path.exists(path) and validate_python_path(path):
                if not any(interp['path'] == path for interp in interpreters):
                    version = get_python_version(path)
                    interpreters.append({
                        'path': path,
                        'version': version,
                        'name': os.path.basename(path)
                    })
    
    return interpreters

def get_best_python_interpreter():
    interpreters = detect_available_python_interpreters()
    if not interpreters:
        return get_python_executable()
    
    python3_interpreters = [i for i in interpreters if 'python3' in i['name'].lower() or 'Python3' in i['version']]
    if python3_interpreters:
        return python3_interpreters[0]['path']
    
    return interpreters[0]['path']

def get_python_version(python_path):
    try:
        import subprocess
        startupinfo = create_startup_info()
        result = subprocess.run(
            [python_path, "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5,
            startupinfo=startupinfo
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