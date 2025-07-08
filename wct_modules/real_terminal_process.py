import os
import sys
import subprocess
import threading
import time
import platform
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal, QProcess, QIODevice
from .i18n import t
class RealTerminalProcess(QObject):
    output_ready = Signal(str)
    error_ready = Signal(str)
    finished = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.use_pty = False
        self.output_thread = None
        self.error_thread = None
        self.running = False
        self._check_pty_support()
    
    def _check_pty_support(self):
        
        try:
            if platform.system() != "Windows":
                import pty
                self.use_pty = True
        except ImportError:
            self.use_pty = False
    
    def start_process(self, program: str, arguments: list = None, working_directory: str = None, environment: dict = None):
        
        if self.running:
            self.stop_process()
        
        if arguments is None:
            arguments = []
        
        if working_directory is None:
            working_directory = os.getcwd()
        
        if environment is None:
            environment = os.environ.copy()
        terminal_env = {
            'TERM': 'xterm-256color',
            'COLORTERM': 'truecolor',
            'FORCE_COLOR': '1',
            'CLICOLOR': '1',
            'CLICOLOR_FORCE': '1',
            'LANG': 'zh_CN.UTF-8',
            'LC_ALL': 'zh_CN.UTF-8',
            'PYTHONIOENCODING': 'utf-8',
        }
        if platform.system() == "Windows":
            terminal_env.update({
                'PYTHONUTF8': '1',
                'PYTHONIOENCODING': 'utf-8:surrogateescape',
                'CHCP': '65001',
            })
        
        environment.update(terminal_env)
        
        try:
            if self.use_pty:
                self._start_with_pty(program, arguments, working_directory, environment)
            else:
                self._start_without_pty(program, arguments, working_directory, environment)
            
            self.running = True
            
        except Exception as e:
            self.error_ready.emit(t('messages.process_start_failed', str(e)))
    
    def _start_with_pty(self, program: str, arguments: list, working_directory: str, environment: dict):
        
        import pty
        import select
        master_fd, slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            [program] + arguments,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=working_directory,
            env=environment,
            preexec_fn=os.setsid,
            close_fds=True
        )
        os.close(slave_fd)
        self.master_fd = master_fd
        self.output_thread = threading.Thread(target=self._pty_output_reader, daemon=True)
        self.output_thread.start()
        self.monitor_thread = threading.Thread(target=self._process_monitor, daemon=True)
        self.monitor_thread.start()
    
    def _start_without_pty(self, program: str, arguments: list, working_directory: str, environment: dict):
        self.process = subprocess.Popen(
            [program] + arguments,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=working_directory,
            env=environment,
            text=False,
            bufsize=0,
            universal_newlines=False
        )
        self.output_thread = threading.Thread(target=self._stdout_reader, daemon=True)
        self.output_thread.start()
        
        self.error_thread = threading.Thread(target=self._stderr_reader, daemon=True)
        self.error_thread.start()
        self.monitor_thread = threading.Thread(target=self._process_monitor, daemon=True)
        self.monitor_thread.start()
    
    def _pty_output_reader(self):
        
        import select
        
        while self.running and self.process and self.process.poll() is None:
            try:

                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                if ready:
                    data = os.read(self.master_fd, 4096)
                    if data:

                        try:
                            output = data.decode('utf-8')
                        except UnicodeDecodeError:
                            try:
                                output = data.decode('gbk')
                            except UnicodeDecodeError:
                                try:
                                    output = data.decode('cp936')
                                except UnicodeDecodeError:
                                    output = data.decode('utf-8', errors='replace')
                        self.output_ready.emit(output)
                    else:
                        break
            except (OSError, ValueError):
                break
        try:
            os.close(self.master_fd)
        except:
            pass
    
    def _stdout_reader(self):
        
        while self.running and self.process and self.process.poll() is None:
            try:
                data = self.process.stdout.read(4096)
                if data:

                    try:
                        output = data.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            output = data.decode('gbk')
                        except UnicodeDecodeError:
                            try:
                                output = data.decode('cp936')
                            except UnicodeDecodeError:
                                output = data.decode('utf-8', errors='replace')
                    self.output_ready.emit(output)
                else:
                    break
            except (OSError, ValueError):
                break
    
    def _stderr_reader(self):
        
        while self.running and self.process and self.process.poll() is None:
            try:
                data = self.process.stderr.read(4096)
                if data:

                    try:
                        output = data.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            output = data.decode('gbk')
                        except UnicodeDecodeError:
                            try:
                                output = data.decode('cp936')
                            except UnicodeDecodeError:
                                output = data.decode('utf-8', errors='replace')
                    self.error_ready.emit(output)
                else:
                    break
            except (OSError, ValueError):
                break
    
    def _process_monitor(self):
        
        if self.process:
            self.process.wait()
            self.running = False
            self.finished.emit(self.process.returncode)
    
    def send_input(self, text: str):
        
        if not self.process or self.process.poll() is not None:
            return
        
        try:
            if self.use_pty:

                os.write(self.master_fd, text.encode('utf-8'))
            else:

                self.process.stdin.write(text.encode('utf-8'))
                self.process.stdin.flush()
        except (OSError, ValueError, BrokenPipeError):
            pass
    
    def send_interrupt(self):
        
        if not self.process or self.process.poll() is not None:
            return
        
        try:
            if self.use_pty:

                os.write(self.master_fd, b'\x03')
            else:

                if platform.system() == "Windows":
                    self.process.terminate()
                else:
                    self.process.send_signal(2)
        except (OSError, ValueError, BrokenPipeError):
            pass
    
    def stop_process(self):
        
        self.running = False
        
        if self.process and self.process.poll() is None:
            try:
                if platform.system() == "Windows":
                    self.process.terminate()
                else:
                    self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                    
            except (OSError, ValueError):
                pass
        if hasattr(self, 'master_fd'):
            try:
                os.close(self.master_fd)
            except:
                pass
        
        self.process = None
    
    def is_running(self) -> bool:
        
        return self.running and self.process and self.process.poll() is None
    
    def get_exit_code(self) -> Optional[int]:
        
        if self.process:
            return self.process.poll()
        return None