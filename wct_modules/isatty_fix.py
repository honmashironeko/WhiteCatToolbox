"""
IsATTY Fix Module for WhiteCat Toolbox
提供 isatty() 修复功能，支持子进程注入
"""

import sys
import os
from types import MethodType

# isatty 修复代码字符串，用于子进程注入
ISATTY_FIX_CODE = '''
import sys
import os
from types import MethodType

def _always_true(*args, **kwargs):
    return True

# 修复 sys 标准流的 isatty 方法
for stream_name in ("stdout", "stderr", "stdin", "__stdout__", "__stderr__", "__stdin__"):
    stream = getattr(sys, stream_name, None)
    if stream is not None and hasattr(stream, "isatty"):
        try:
            setattr(stream, "isatty", MethodType(lambda self: True, stream))
        except Exception:
            pass

# 修复 os.isatty 函数
try:
    os.isatty = _always_true
except Exception:
    pass
'''

def apply_isatty_fix():
    """
    直接应用 isatty 修复到当前进程
    """
    def _always_true(*args, **kwargs):
        return True

    # 修复 sys 标准流的 isatty 方法
    for stream_name in ("stdout", "stderr", "stdin", "__stdout__", "__stderr__", "__stdin__"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "isatty"):
            try:
                setattr(stream, "isatty", MethodType(lambda self: True, stream))
            except Exception:
                pass

    # 修复 os.isatty 函数
    try:
        os.isatty = _always_true
    except Exception:
        pass

def get_python_command_with_isatty_fix(original_command):
    """
    将原始 Python 命令包装为带有 isatty 修复的命令
    
    Args:
        original_command (list): 原始命令列表
    
    Returns:
        list: 包装后的命令列表
    """
    if not original_command:
        return original_command
    
    # 检查是否启用了 isatty 修复
    try:
        import json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'app_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if not config.get('system_settings', {}).get('enable_isatty_fix', True):
                    return original_command
    except Exception:
        # 如果无法读取配置，默认启用
        pass
    
    # 检查是否是 Python 命令
    python_executables = ['python', 'python3', 'python.exe']
    first_command = os.path.basename(original_command[0]).lower()
    
    is_python_command = (
        first_command in python_executables or 
        first_command.startswith('python') or
        original_command[0].endswith('python') or
        original_command[0].endswith('python.exe')
    )
    
    if not is_python_command:
        return original_command
    
    # 检查是否已经有 -c 参数，避免重复处理
    if len(original_command) >= 2 and original_command[1] == '-c':
        return original_command
    
    # 处理不同类型的 Python 命令
    if len(original_command) == 1:
        # 纯 Python 解释器启动
        return [original_command[0], '-c', ISATTY_FIX_CODE + '\nimport code; code.interact()']
    
    # 检查是否是执行脚本文件
    script_arg_index = 1
    python_flags = []
    
    # 收集 Python 标志参数
    for i in range(1, len(original_command)):
        arg = original_command[i]
        if arg.startswith('-') and not arg.endswith('.py'):
            python_flags.append(arg)
            script_arg_index = i + 1
        else:
            break
    
    if script_arg_index < len(original_command):
        script_path = original_command[script_arg_index]
        script_args = original_command[script_arg_index + 1:]
        
        # 如果是脚本文件，使用脚本包装器
        if script_path.endswith('.py') or os.path.isfile(script_path):
            exec_code = wrap_python_script_with_isatty_fix(script_path, script_args)
            return [original_command[0]] + python_flags + ['-c', exec_code]
    
    # 对于模块执行（-m 参数），使用更安全的方式
    if len(original_command) >= 3 and original_command[1] == '-m':
        module_name = original_command[2]
        module_args = original_command[3:] if len(original_command) > 3 else []
        
        exec_code = f'''
{ISATTY_FIX_CODE}

# 执行模块
import sys
import runpy
sys.argv = {repr([module_name] + module_args)}
try:
    runpy.run_module({repr(module_name)}, run_name='__main__', alter_sys=True)
except SystemExit as e:
    sys.exit(e.code)
'''
        return [original_command[0], '-c', exec_code]
    
    # 其他情况，使用 subprocess 包装
    exec_code = f'''
{ISATTY_FIX_CODE}

# 执行原始命令
import sys
import subprocess
import os
sys.exit(subprocess.call({repr(original_command[1:])}, env=os.environ))
'''
    return [original_command[0], '-c', exec_code]

def wrap_python_script_with_isatty_fix(script_path, script_args=None):
    """
    包装 Python 脚本，使其在启动时应用 isatty 修复
    
    Args:
        script_path (str): Python 脚本路径
        script_args (list): 脚本参数
    
    Returns:
        str: 包装后的执行代码
    """
    if script_args is None:
        script_args = []
    
    # 获取脚本的绝对路径
    abs_script_path = os.path.abspath(script_path)
    script_dir = os.path.dirname(abs_script_path)
    
    # 构建执行代码
    exec_code = f'''
{ISATTY_FIX_CODE}

# 设置脚本参数和路径
import sys
import os
sys.argv = {repr([script_path] + script_args)}

# 将脚本目录添加到 sys.path
script_dir = {repr(script_dir)}
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 切换到脚本目录（保持相对路径的正确性）
original_cwd = os.getcwd()
try:
    os.chdir(script_dir)
    
    # 执行脚本
    with open({repr(abs_script_path)}, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    # 使用 compile 和 exec 执行，保持正确的文件信息
    compiled = compile(script_content, {repr(abs_script_path)}, 'exec')
    exec(compiled)
    
finally:
    # 恢复原始工作目录
    os.chdir(original_cwd)
'''
    
    return exec_code 