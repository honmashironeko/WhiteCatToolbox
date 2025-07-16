import sys
import os
from types import MethodType

ISATTY_FIX_CODE = '''
import sys
import os
from types import MethodType

def _always_true(*args, **kwargs):
    return True

for stream_name in ("stdout", "stderr", "stdin", "__stdout__", "__stderr__", "__stdin__"):
    stream = getattr(sys, stream_name, None)
    if stream is not None and hasattr(stream, "isatty"):
        try:
            setattr(stream, "isatty", MethodType(lambda self: True, stream))
        except Exception:
            pass

try:
    os.isatty = _always_true
except Exception:
    pass
'''

def apply_isatty_fix():
    def _always_true(*args, **kwargs):
        return True

    for stream_name in ("stdout", "stderr", "stdin", "__stdout__", "__stderr__", "__stdin__"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "isatty"):
            try:
                setattr(stream, "isatty", MethodType(lambda self: True, stream))
            except Exception:
                pass

    try:
        os.isatty = _always_true
    except Exception:
        pass

def get_python_command_with_isatty_fix(original_command):
    if not original_command:
        return original_command

    try:
        import json
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'app_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if not config.get('system_settings', {}).get('enable_isatty_fix', True):
                    return original_command
    except Exception:

        pass

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

    if len(original_command) >= 2 and original_command[1] == '-c':
        return original_command

    if len(original_command) == 1:

        return [original_command[0], '-c', ISATTY_FIX_CODE + '\nimport code; code.interact()']

    script_arg_index = 1
    python_flags = []

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

        if script_path.endswith('.py') or os.path.isfile(script_path):
            exec_code = wrap_python_script_with_isatty_fix(script_path, script_args)
            return [original_command[0]] + python_flags + ['-c', exec_code]

    if len(original_command) >= 3 and original_command[1] == '-m':
        module_name = original_command[2]
        module_args = original_command[3:] if len(original_command) > 3 else []
        
        exec_code = f'''
{ISATTY_FIX_CODE}

import sys
import runpy
sys.argv = {repr([module_name] + module_args)}
try:
    runpy.run_module({repr(module_name)}, run_name='__main__', alter_sys=True)
except SystemExit as e:
    sys.exit(e.code)
'''
        return [original_command[0], '-c', exec_code]

    exec_code = f'''
{ISATTY_FIX_CODE}

import sys
import subprocess
import os
sys.exit(subprocess.call({repr(original_command[1:])}, env=os.environ))
'''
    return [original_command[0], '-c', exec_code]

def wrap_python_script_with_isatty_fix(script_path, script_args=None):
    if script_args is None:
        script_args = []

    if os.path.isabs(script_path):

        abs_script_path = os.path.abspath(script_path)
        script_dir = os.path.dirname(abs_script_path)
        should_change_dir = True
    else:

        abs_script_path = script_path
        script_dir = None
        should_change_dir = False

    if should_change_dir:
        exec_code = f'''
{ISATTY_FIX_CODE}

import sys
import os
sys.argv = {repr([script_path] + script_args)}

script_dir = {repr(script_dir)}
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

original_cwd = os.getcwd()
try:
    os.chdir(script_dir)

    with open({repr(abs_script_path)}, 'r', encoding='utf-8') as f:
        script_content = f.read()

    compiled = compile(script_content, {repr(abs_script_path)}, 'exec')
    exec(compiled)
    
finally:

    os.chdir(original_cwd)
'''
    else:

        exec_code = f'''
{ISATTY_FIX_CODE}

import sys
import os
sys.argv = {repr([script_path] + script_args)}

current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

with open({repr(script_path)}, 'r', encoding='utf-8') as f:
    script_content = f.read()

compiled = compile(script_content, {repr(script_path)}, 'exec')
exec(compiled)
'''
    
    return exec_code 