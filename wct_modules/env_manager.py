"""
Environment Manager for WhiteCat Toolbox
Handles Python environment isolation for packaged executables
"""

import os
import sys
import subprocess
import json
import tempfile
import time
import platform
from pathlib import Path
from .i18n import t

class EnvironmentManager:
    
    def __init__(self, logger=None):
        self.logger = logger
        self.is_frozen = hasattr(sys, 'frozen') and getattr(sys, 'frozen', False)
        self.system_python_path = None
        self.manual_python_path = None

        self._python_cache = {}
        self._cache_expiry = 300
        self._last_check_time = {}
        
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

        if self.is_frozen:
            if self.logger:
                self.logger.append_system_log(
                    f"{t('python_not_found_attempting_fallback')}", 
                    "warning"
                )

            self._init_system_python()
            if self.system_python_path:
                return self.system_python_path

            if self.logger:
                self.logger.append_system_log(
                    f"{t('python_detection_completely_failed')}", 
                    "error"
                )
            return None

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
                return

        if not self.system_python_path:
            extended_candidates = self._get_extended_python_candidates()
            for candidate in extended_candidates:
                if self._test_python_executable(candidate):
                    self.system_python_path = candidate
                    if self.logger:
                        self.logger.append_system_log(
                            f"{t('using_system_python_extended')}: {candidate}", 
                            "info"
                        )
                    return

        if not self.system_python_path:

            fallback_python = self._find_fallback_python()
            if fallback_python:
                self.system_python_path = fallback_python
                if self.logger:
                    self.logger.append_system_log(
                        f"{t('using_fallback_python')}: {fallback_python}", 
                        "warning"
                    )
            else:

                self.system_python_path = None
                if self.logger:
                    self.logger.append_system_log(
                        f"{t('python_auto_detection_failed')}", 
                        "error"
                    )
    
    def _get_python_candidates(self):
        candidates = []

        candidates.extend(["python", "python3", "python.exe"])

        if not self.is_frozen:
            return candidates
        
        if os.name == "nt":

            version_dirs = ["313", "312", "311", "310"]

            base_paths = [
                "{appdata}\\Local\\Programs\\Python\\Python{version}\\python.exe",
                "C:\\Python{version}\\python.exe",
                "C:\\Program Files\\Python {version}\\python.exe",
            ]
            
            appdata = os.getenv("LOCALAPPDATA", "")
            
            for version in version_dirs:
                for base_path in base_paths:
                    if "{appdata}" in base_path:
                        path = base_path.format(version=version, appdata=appdata)
                    else:
                        path = base_path.format(version=version)

                    try:
                        if os.path.isfile(path):
                            candidates.append(path)

                            break
                    except (OSError, PermissionError):
                        continue

                if len(candidates) > 3:
                    break
        else:

            unix_paths = [
                "/usr/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python3",
                "/opt/homebrew/bin/python3",
            ]

            for path in unix_paths:
                try:
                    if os.path.isfile(os.path.expanduser(path)):
                        candidates.append(os.path.expanduser(path))
                except (OSError, PermissionError):
                    continue
        
        return candidates
    
    def _get_extended_python_candidates(self):
        
        candidates = []
        
        if os.name == "nt":

            extended_paths = [

                "{appdata}\\Local\\Programs\\Python\\Python*\\python.exe",
                "{appdata}\\Local\\Microsoft\\WindowsApps\\python.exe",
                "{appdata}\\Local\\Microsoft\\WindowsApps\\python3.exe",

                "C:\\Python*\\python.exe",
                "C:\\Program Files\\Python*\\python.exe",
                "C:\\Program Files (x86)\\Python*\\python.exe",

                "{userprofile}\\Anaconda3\\python.exe",
                "{userprofile}\\Miniconda3\\python.exe",
                "C:\\ProgramData\\Anaconda3\\python.exe",
                "C:\\ProgramData\\Miniconda3\\python.exe",

                "{programfiles}\\Python\\Python*\\python.exe",
                "{programfiles(x86)}\\Python\\Python*\\python.exe",
            ]

            appdata = os.getenv("LOCALAPPDATA", "")
            userprofile = os.getenv("USERPROFILE", "")
            programfiles = os.getenv("PROGRAMFILES", "")
            programfiles_x86 = os.getenv("PROGRAMFILES(X86)", "")

            import glob
            for path_template in extended_paths:
                try:

                    path = path_template.format(
                        appdata=appdata,
                        userprofile=userprofile,
                        programfiles=programfiles,
                        **{"programfiles(x86)": programfiles_x86}
                    )

                    matches = glob.glob(path)
                    for match in matches:
                        if os.path.isfile(match) and match not in candidates:
                            candidates.append(match)
                            
                except Exception:
                    continue
        else:

            extended_paths = [

                "/usr/bin/python3.13", "/usr/bin/python3.12", "/usr/bin/python3.11", "/usr/bin/python3.10",
                "/usr/local/bin/python3.13", "/usr/local/bin/python3.12", "/usr/local/bin/python3.11",

                "/opt/homebrew/bin/python3", "/usr/local/bin/python3",

                "~/.pyenv/versions/*/bin/python3", "~/.pyenv/shims/python3",

                "~/anaconda3/bin/python", "~/miniconda3/bin/python",
                "/opt/anaconda3/bin/python", "/opt/miniconda3/bin/python",

                "/opt/python*/bin/python3", "/usr/local/python*/bin/python3",
            ]
            
            import glob
            for path_template in extended_paths:
                try:
                    expanded_path = os.path.expanduser(path_template)
                    matches = glob.glob(expanded_path)
                    for match in matches:
                        if os.path.isfile(match) and match not in candidates:
                            candidates.append(match)
                except Exception:
                    continue
        
        return candidates
    
    def _find_fallback_python(self):
        
        if os.name == "nt":

            fallback_attempts = [

                self._find_python_from_registry(),

                self._find_python_in_path(),

                "C:\\Python39\\python.exe",
                "C:\\Python38\\python.exe",
                "C:\\Python37\\python.exe",
            ]
        else:

            fallback_attempts = [
                "/usr/bin/python3",
                "/usr/bin/python",
                "/usr/local/bin/python3",
                "/usr/local/bin/python",
            ]
        
        for attempt in fallback_attempts:
            if attempt and self._test_python_executable(attempt):
                return attempt
        
        return None
    
    def _find_python_from_registry(self):
        
        if os.name != "nt":
            return None
        
        try:
            import winreg

            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\Python\PythonCore")
                subkey_count = winreg.QueryInfoKey(key)[0]
                
                for i in range(subkey_count):
                    version = winreg.EnumKey(key, i)
                    try:
                        install_key = winreg.OpenKey(key, f"{version}\\InstallPath")
                        install_path = winreg.QueryValue(install_key, "")
                        python_exe = os.path.join(install_path, "python.exe")
                        if os.path.isfile(python_exe):
                            return python_exe
                    except (OSError, WindowsError):
                        continue
            except (OSError, WindowsError):
                pass
                
        except ImportError:
            pass
        
        return None
    
    def _find_python_in_path(self):
        
        import shutil

        for cmd in ["python", "python3", "python.exe"]:
            python_path = shutil.which(cmd)
            if python_path and self._test_python_executable(python_path):
                return python_path
        
        return None
    
    def validate_python_availability(self):
        
        effective_python = self.get_effective_python_path()
        
        if effective_python is None:
            return False, f"{t('no_python_interpreter_found')}"
        
        if not os.path.exists(effective_python):
            return False, f"{t('python_path_not_exist')}: {effective_python}"
        
        if not self._test_python_executable(effective_python):
            return False, f"{t('python_not_executable')}: {effective_python}"
        
        return True, f"{t('python_available')}: {effective_python}"
    
    def get_python_info(self, python_path):
        if not python_path or not os.path.exists(python_path):
            return None
            
        try:

            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                [python_path, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); print(sys.executable); print(sys.platform)"],
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo
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

        current_time = time.time()
        if python_path in self._python_cache:
            last_check = self._last_check_time.get(python_path, 0)
            if current_time - last_check < self._cache_expiry:
                return self._python_cache[python_path]
        
        try:

            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                [python_path, "-c", "import sys; print(sys.version)"], 
                capture_output=True, 
                text=True, 
                timeout=5,
                startupinfo=startupinfo
            )

            is_valid = result.returncode == 0
            self._python_cache[python_path] = is_valid
            self._last_check_time[python_path] = current_time
            
            return is_valid
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):

            self._python_cache[python_path] = False
            self._last_check_time[python_path] = current_time
            return False
    
    def get_python_command(self, original_command, tool_name=None):
        if not original_command:
            return original_command
            
        command = original_command.copy()

        if command[0] in ["python", "python3", "python.exe"]:
            if tool_name:
                effective_python = self.get_effective_python_for_tool(tool_name)
            else:
                effective_python = self.get_effective_python_path()
                
            if effective_python is None:

                raise RuntimeError(f"{t('python_interpreter_not_found')}")
            command[0] = effective_python
            
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
    
    def create_subprocess_wrapper(self, tool_path, user_command, params, venv_path=None, custom_env_str=None, tool_name=None):
        from .utils import build_cross_platform_command
        from .isatty_fix import get_python_command_with_isatty_fix

        command = build_cross_platform_command(tool_path, user_command, params)

        command = self.get_python_command(command, tool_name)

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

            startupinfo = None
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            result = subprocess.run(
                pip_command,
                capture_output=True,
                text=True,
                timeout=300,
                startupinfo=startupinfo
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
    
    def get_all_available_pythons(self):
        
        pythons = []
        seen_paths = set()

        all_candidates = []
        all_candidates.extend(self._get_python_candidates())
        all_candidates.extend(self._get_extended_python_candidates())

        if self.system_python_path and self.system_python_path not in all_candidates:
            all_candidates.insert(0, self.system_python_path)

        if self.manual_python_path and self.manual_python_path not in all_candidates:
            all_candidates.insert(0, self.manual_python_path)

        for candidate in all_candidates:
            if not candidate or candidate in seen_paths:
                continue
                
            seen_paths.add(candidate)

            python_info = self.get_python_info(candidate)
            if python_info and python_info.get('valid', False):
                pythons.append({
                    'path': candidate,
                    'version': python_info.get('version', 'Unknown'),
                    'platform': python_info.get('platform', 'Unknown'),
                    'display_name': f"Python {python_info.get('version', 'Unknown')} ({candidate})",
                    'is_current_system': candidate == self.system_python_path,
                    'is_manual': candidate == self.manual_python_path
                })
        
        return pythons
    
    def set_tool_specific_python(self, tool_name, python_path):
        
        if not hasattr(self, 'tool_specific_pythons'):
            self.tool_specific_pythons = {}
        
        if python_path and self._test_python_executable(python_path):
            self.tool_specific_pythons[tool_name] = python_path
            if self.logger:
                self.logger.append_system_log(
                    f"{t('tool_python_set')}: {tool_name} -> {python_path}", 
                    "info"
                )
            return True
        elif python_path is None or python_path == "":

            self.tool_specific_pythons.pop(tool_name, None)
            if self.logger:
                self.logger.append_system_log(
                    f"{t('tool_python_cleared')}: {tool_name}", 
                    "info"
                )
            return True
        else:
            if self.logger:
                self.logger.append_system_log(
                    f"{t('invalid_tool_python')}: {tool_name} -> {python_path}", 
                    "error"
                )
            return False
    
    def get_tool_specific_python(self, tool_name):
        
        if not hasattr(self, 'tool_specific_pythons'):
            self.tool_specific_pythons = {}
        
        return self.tool_specific_pythons.get(tool_name, None)
    
    def get_effective_python_for_tool(self, tool_name):

        tool_python = self.get_tool_specific_python(tool_name)
        if tool_python and os.path.exists(tool_python) and self._test_python_executable(tool_python):
            return tool_python

        return self.get_effective_python_path()