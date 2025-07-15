"""
Environment Manager for WhiteCat Toolbox
Handles Python environment isolation for packaged executables
"""

import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path
from .i18n import t


class EnvironmentManager:
    
    def __init__(self, logger=None):
        self.logger = logger
        self.is_frozen = hasattr(sys, 'frozen') and getattr(sys, 'frozen', False)
        self.system_python_path = None
        self.manual_python_path = None
        self._init_system_python()
    
    def set_manual_python_path(self, python_path):
        if python_path and os.path.exists(python_path):
            if self._test_python_executable(python_path):
                self.manual_python_path = python_path
                if self.logger:
                    self.logger.append_system_log(
                        f"{t('manual_python_set')}: {python_path}", 
                        "info"
                    )
                return True
            else:
                if self.logger:
                    self.logger.append_system_log(
                        f"{t('invalid_python_path')}: {python_path}", 
                        "error"
                    )
                return False
        return False
    
    def get_effective_python_path(self):
        if self.manual_python_path and os.path.exists(self.manual_python_path):
            if self._test_python_executable(self.manual_python_path):
                return self.manual_python_path
            else:

                if self.logger:
                    self.logger.append_system_log(
                        f"{t('manual_python_invalid')}: {self.manual_python_path}", 
                        "warning"
                    )
                self.manual_python_path = None
        

        if self.system_python_path:
            return self.system_python_path
            

        return sys.executable
    
    def get_current_python_display_path(self):
        
        if self.manual_python_path and os.path.exists(self.manual_python_path):
            if self._test_python_executable(self.manual_python_path):
                return self.manual_python_path
            else:

                return ""
        

        return ""
    
    def get_auto_detected_python_path(self):
        
        if self.system_python_path:
            return self.system_python_path
        return sys.executable
    
    def reset_manual_python_path(self):
        
        self.manual_python_path = None
        if self.logger:
            self.logger.append_system_log(
                f"{t('python_path_updated')}: {t('auto_detected_system_python')}", 
                "info"
            )
    
    def _init_system_python(self):
        if not self.is_frozen:
            self.system_python_path = sys.executable
            return
            

        python_candidates = self._get_python_candidates()
        
        for candidate in python_candidates:
            if self._test_python_executable(candidate):
                self.system_python_path = candidate
                if self.logger:
                    self.logger.append_system_log(
                        f"{t('using_system_python')}: {candidate}", 
                        "info"
                    )
                break
        
        if not self.system_python_path:
            self.system_python_path = sys.executable
            if self.logger:
                self.logger.append_system_log(
                    f"{t('system_python_not_found')}, {t('using_current_python')}", 
                    "warning"
                )
    
    def _get_python_candidates(self):
        candidates = []
        

        candidates.extend(["python", "python3", "python.exe"])
        
        if os.name == "nt":

            version_dirs = ["313", "312", "311", "310", "39", "38"]
            base_paths = [
                "C:\\Python{version}\\python.exe",
                "C:\\Program Files\\Python {version}\\python.exe",
                "C:\\Program Files (x86)\\Python {version}\\python.exe",
                "{appdata}\\Local\\Programs\\Python\\Python{version}\\python.exe"
            ]
            
            appdata = os.getenv("LOCALAPPDATA", "")
            
            for version in version_dirs:
                for base_path in base_paths:
                    if "{appdata}" in base_path:
                        path = base_path.format(version=version, appdata=appdata)
                    else:
                        path = base_path.format(version=version)
                    
                    if os.path.exists(path):
                        candidates.append(path)
        else:

            unix_paths = [
                "/usr/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python3",
                "/usr/local/bin/python",
                "/opt/python/bin/python3",
                "/opt/homebrew/bin/python3",
                "~/.pyenv/shims/python3"
            ]
            candidates.extend([os.path.expanduser(p) for p in unix_paths])
        
        return candidates
    
    def get_python_info(self, python_path):
        if not python_path or not os.path.exists(python_path):
            return None
            
        try:

            result = subprocess.run(
                [python_path, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); print(sys.executable); print(sys.platform)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 3:
                    return {
                        'version': lines[0],
                        'executable': lines[1],
                        'platform': lines[2],
                        'valid': True
                    }
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
            
        return {'valid': False}
    
    def suggest_python_paths(self):
        suggestions = []
        candidates = self._get_python_candidates()
        
        for candidate in candidates:
            info = self.get_python_info(candidate)
            if info and info.get('valid'):
                suggestions.append({
                    'path': candidate,
                    'version': info.get('version', 'Unknown'),
                    'platform': info.get('platform', 'Unknown')
                })
                
        return suggestions
    
    def _test_python_executable(self, python_path):
        try:
            result = subprocess.run(
                [python_path, "-c", "import sys; print(sys.version)"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def get_python_command(self, original_command):
        if not original_command:
            return original_command
            
        command = original_command.copy()
        

        if command[0] in ["python", "python3", "python.exe"]:
            command[0] = self.get_effective_python_path()
            
        return command
    
    def create_isolated_environment(self, custom_env=None):
        env = os.environ.copy()
        

        if self.is_frozen:
            python_vars_to_remove = [
                'PYTHONPATH',
                'PYTHONHOME', 
                'PYTHONSTARTUP',
                'PYTHONOPTIMIZE',
                'PYTHONDEBUG'
            ]
            
            for var in python_vars_to_remove:
                env.pop(var, None)
        

        if custom_env:
            env.update(custom_env)
            
        return env
    
    def create_subprocess_wrapper(self, tool_path, user_command, params, venv_path=None, custom_env_str=None):
        from .utils import build_cross_platform_command
        from .isatty_fix import get_python_command_with_isatty_fix
        

        command = build_cross_platform_command(tool_path, user_command, params)
        

        command = self.get_python_command(command)
        

        if venv_path and os.path.exists(venv_path):
            if os.name == "nt":
                venv_python = os.path.join(venv_path, "Scripts", "python.exe")
            else:
                venv_python = os.path.join(venv_path, "bin", "python")
                
            if os.path.exists(venv_python) and command[0] in [self.get_effective_python_path(), "python", "python3", "python.exe"]:
                command[0] = venv_python
        
        command = get_python_command_with_isatty_fix(command)

        custom_env = {}
        

        if venv_path and os.path.exists(venv_path):
            if os.name == "nt":
                venv_bin = os.path.join(venv_path, "Scripts")
            else:
                venv_bin = os.path.join(venv_path, "bin")
            
            custom_env["VIRTUAL_ENV"] = venv_path
            custom_env["PATH"] = venv_bin + os.pathsep + os.environ.get("PATH", "")
        

        if custom_env_str:
            for pair in custom_env_str.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    

                    if k.upper() == "PATH":
                        if "%PATH%" in v:
                            v = v.replace("%PATH%", os.environ.get("PATH", ""))
                        if "$PATH" in v:
                            v = v.replace("$PATH", os.environ.get("PATH", ""))
                    
                    custom_env[k] = v
        

        environment = self.create_isolated_environment(custom_env)
        
        return command, environment
    
    def get_tool_requirements_path(self, tool_path):
        requirements_files = [
            "requirements.txt",
            "requirements-dev.txt", 
            "requirements_dev.txt",
            "req.txt"
        ]
        
        for req_file in requirements_files:
            req_path = os.path.join(tool_path, req_file)
            if os.path.exists(req_path):
                return req_path
        
        return None
    
    def install_tool_dependencies(self, tool_path, python_path=None):
        if not python_path:
            python_path = self.system_python_path
            
        requirements_path = self.get_tool_requirements_path(tool_path)
        if not requirements_path:
            return True, t("no_requirements_file")
        
        try:
            pip_command = [python_path, "-m", "pip", "install", "-r", requirements_path]
            result = subprocess.run(
                pip_command,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return True, t("dependencies_installed_successfully")
            else:
                return False, f"{t('install_dependencies_failed')}: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, t("install_timeout")
        except Exception as e:
            return False, f"{t('install_error')}: {str(e)}"
    
    def create_tool_launcher_script(self, tool_path, script_name, python_args=None):
        if not python_args:
            python_args = []
            

        script_dir = tempfile.mkdtemp(prefix="wct_launcher_")
        
        if os.name == "nt":
            launcher_path = os.path.join(script_dir, "launcher.bat")
            script_content = f"""@echo off
cd /d "{tool_path}"
"{self.system_python_path}" {' '.join(python_args)} "{script_name}" %*
"""
        else:
            launcher_path = os.path.join(script_dir, "launcher.sh")
            script_content = f"""#!/bin/bash
cd "{tool_path}"
"{self.system_python_path}" {' '.join(python_args)} "{script_name}" "$@"
"""
        
        try:
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
                

            if os.name != "nt":
                os.chmod(launcher_path, 0o755)
                
            return launcher_path
        except Exception as e:
            if self.logger:
                self.logger.append_system_log(f"{t('create_launcher_failed')}: {e}", "error")
            return None