import os
import sys
import subprocess
import threading
import queue
import signal
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from .utils import is_windows, is_linux, is_macos, create_startup_info, clean_ansi_codes

class ProcessManager(QObject):
    output_received = Signal(str, str)
    process_finished = Signal(str, int)
    process_started = Signal(str)
    error_occurred = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.processes = {}
        self.output_threads = {}
        
    def execute_tool(self, process_id, tool_path, command_parts, working_dir=None):
        try:
            if working_dir is None:
                working_dir = tool_path
                

            print(f"执行命令: {command_parts}")
            print(f"工作目录: {working_dir}")
                
            process = self._create_process_with_pty(command_parts, working_dir)
            
            if process:
                self.processes[process_id] = process
                self._start_output_monitoring(process_id, process)
                self.process_started.emit(process_id)
                return True
            else:
                self.error_occurred.emit(process_id, "无法创建进程")
                return False
                
        except Exception as e:
            self.error_occurred.emit(process_id, f"执行失败: {str(e)}")
            return False
            
    def _create_process_with_pty(self, command_parts, working_dir):
        try:
            if is_windows():
                return self._create_windows_pty_process(command_parts, working_dir)
            else:
                return self._create_unix_pty_process(command_parts, working_dir)
        except Exception as e:
            print(f"创建PTY进程失败: {e}")
            return self._create_fallback_process(command_parts, working_dir)
            
    def _create_windows_pty_process(self, command_parts, working_dir):
        try:
            import winpty
            
            # 尝试使用 pywinpty
            if not command_parts or not isinstance(command_parts, list):
                raise ValueError("Invalid command_parts")
                
            # 构建命令字符串
            command_str = ' '.join(f'"{part}"' if ' ' in str(part) else str(part) for part in command_parts)
            
            pty_process = winpty.PtyProcess.spawn(
                command_str,
                cwd=str(working_dir),
                env=os.environ.copy()
            )
            
            class WinptyWrapper:
                def __init__(self, pty_process):
                    self.pty_process = pty_process
                    
                def read(self, size=1024):
                    return self.pty_process.read(size)
                    
                def poll(self):
                    return None if self.pty_process.isalive() else 0
                    
                def wait(self):
                    self.pty_process.wait()
                    return 0
                    
                def terminate(self):
                    self.pty_process.terminate()
                    
                def kill(self):
                    self.pty_process.terminate()
                    
                def write(self, data):
                    self.pty_process.write(data)
                    
                def isalive(self):
                    return self.pty_process.isalive()
            
            return WinptyWrapper(pty_process)
            
        except ImportError:
            try:
                return self._create_conpty_process(command_parts, working_dir)
            except Exception:
                return self._create_fallback_process(command_parts, working_dir)
        except Exception as e:
            print(f"winpty创建失败: {e}")
            return self._create_fallback_process(command_parts, working_dir)
            
    def _create_conpty_process(self, command_parts, working_dir):
        import subprocess
        
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'
        env['FORCE_COLOR'] = '1'
        
        startupinfo = create_startup_info()
        
        process = subprocess.Popen(
            command_parts,
            cwd=str(working_dir),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if is_windows() else 0
        )
        
        return process
        
    def _create_unix_pty_process(self, command_parts, working_dir):
        import pty
        import select
        
        master_fd, slave_fd = pty.openpty()
        
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'
        env['FORCE_COLOR'] = '1'
        
        process = subprocess.Popen(
            command_parts,
            cwd=str(working_dir),
            env=env,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid
        )
        
        os.close(slave_fd)
        
        class PtyProcess:
            def __init__(self, process, master_fd):
                self.process = process
                self.master_fd = master_fd
                self.stdin = process.stdin
                self.stdout = master_fd
                self.stderr = None
                
            def poll(self):
                return self.process.poll()
                
            def terminate(self):
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                except Exception:
                    self.process.terminate()
                    
            def kill(self):
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except Exception:
                    self.process.kill()
                    
            def wait(self):
                return self.process.wait()
                
            def read_output(self, size=1024):
                try:
                    if select.select([self.master_fd], [], [], 0)[0]:
                        return os.read(self.master_fd, size).decode('utf-8', errors='ignore')
                except Exception:
                    pass
                return ''
                
        return PtyProcess(process, master_fd)
        
    def _create_fallback_process(self, command_parts, working_dir):
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'
        env['FORCE_COLOR'] = '1'
        env['PYTHONUNBUFFERED'] = '1'
        
        startupinfo = create_startup_info()
        

        class FallbackProcess:
            def __init__(self, process):
                self.process = process
                self.stdin = process.stdin
                self.stdout = process.stdout
                self.stderr = process.stderr
                
            def poll(self):
                return self.process.poll()
                
            def terminate(self):
                return self.process.terminate()
                
            def kill(self):
                return self.process.kill()
                
            def wait(self):
                return self.process.wait()
                
            def read_combined_output(self, size=4096):
                """读取合并的stdout和stderr输出"""
                output = ''
                try:
                    if self.stdout:

                        import select
                        import sys
                        
                        if sys.platform == 'win32':

                            try:

                                stdout_data = self.stdout.read(size)
                                if stdout_data:
                                    output += stdout_data
                            except:

                                try:
                                    line = self.stdout.readline()
                                    if line:
                                        output += line.rstrip()
                                except:
                                    pass
                        else:

                            if hasattr(self.stdout, 'fileno'):
                                ready, _, _ = select.select([self.stdout.fileno()], [], [], 0)
                                if ready:
                                    stdout_data = self.stdout.read(size)
                                    if stdout_data:
                                        output += stdout_data
                except Exception:
                    pass
                return output
        
        process = subprocess.Popen(
            command_parts,
            cwd=str(working_dir),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            startupinfo=startupinfo
        )
        
        return FallbackProcess(process)
        
    def _start_output_monitoring(self, process_id, process):
        def monitor_output():
            try:
                while True:
                    output = None
                    has_output = False
                    

                    if hasattr(process, 'read_output'):

                        output = process.read_output(4096)
                        if output:
                            has_output = True
                    elif hasattr(process, 'read'):

                        try:

                            output = process.read(4096)
                            if output:
                                if isinstance(output, bytes):
                                    output = output.decode('utf-8', errors='ignore')
                                has_output = True
                        except Exception as e:

                            try:
                                import select
                                if hasattr(process, 'fileno'):
                                    ready, _, _ = select.select([process.fileno()], [], [], 0)
                                    if ready:
                                        output = process.read(1024)
                                        if output:
                                            if isinstance(output, bytes):
                                                output = output.decode('utf-8', errors='ignore')
                                            has_output = True
                            except Exception:
                                pass
                    elif hasattr(process, 'read_combined_output'):

                        try:
                            output = process.read_combined_output(4096)
                            if output:
                                has_output = True
                        except Exception:

                            try:
                                if hasattr(process, 'stdout') and process.stdout:
                                    line = process.stdout.readline()
                                    if line:
                                        output = line.rstrip()
                                        has_output = True
                            except Exception:
                                pass
                    elif hasattr(process, 'stdout') and process.stdout:

                        try:

                            lines = []
                            while True:
                                line = process.stdout.readline()
                                if not line:
                                    break
                                lines.append(line.rstrip())

                                if len(lines) >= 10:
                                    break
                            if lines:
                                output = '\n'.join(lines)
                                has_output = True
                        except Exception:
                            pass
                    
                    if has_output and output:
                        self.output_received.emit(process_id, output)
                    

                    if process.poll() is not None:

                        try:

                            for _ in range(5):
                                remaining_output = None
                                if hasattr(process, 'read'):
                                    remaining_output = process.read(8192)
                                    if remaining_output:
                                        if isinstance(remaining_output, bytes):
                                            remaining_output = remaining_output.decode('utf-8', errors='ignore')
                                elif hasattr(process, 'read_combined_output'):

                                    remaining_output = process.read_combined_output(8192)
                                elif hasattr(process, 'stdout') and process.stdout:
                                    remaining_output = process.stdout.read()
                                    if remaining_output:
                                        remaining_output = remaining_output.rstrip()
                                
                                if remaining_output:
                                    self.output_received.emit(process_id, remaining_output)
                                else:
                                    break
                                    

                                import time
                                time.sleep(0.001)
                        except Exception:
                            pass
                        break
                        

                    import time
                    time.sleep(0.005)
                        
                exit_code = process.wait()
                self.process_finished.emit(process_id, exit_code)
                
                if process_id in self.processes:
                    del self.processes[process_id]
                if process_id in self.output_threads:
                    del self.output_threads[process_id]
                    
            except Exception as e:
                self.error_occurred.emit(process_id, f"输出监控错误: {str(e)}")
                
        thread = threading.Thread(target=monitor_output, daemon=True)
        thread.start()
        self.output_threads[process_id] = thread
        
    def send_input(self, process_id, text):
        if process_id in self.processes:
            try:
                process = self.processes[process_id]
                

                if hasattr(process, 'write'):
                    try:
                        process.write(text + '\r\n')
                        return True
                    except Exception as e:
                        print(f"winpty写入失败: {e}")
                        

                elif hasattr(process, 'stdin') and process.stdin:
                    try:
                        process.stdin.write(text + '\n')
                        process.stdin.flush()
                        return True
                    except Exception as e:
                        print(f"标准stdin写入失败: {e}")
                        

                elif hasattr(process, 'process') and hasattr(process.process, 'stdin'):
                    try:
                        process.process.stdin.write(text + '\n')
                        process.process.stdin.flush()
                        return True
                    except Exception as e:
                        print(f"包装进程stdin写入失败: {e}")
                        
            except Exception as e:
                self.error_occurred.emit(process_id, f"发送输入失败: {str(e)}")
        return False
        
    def terminate_process(self, process_id):
        if process_id in self.processes:
            try:
                process = self.processes[process_id]
                process.terminate()
                return True
            except Exception as e:
                self.error_occurred.emit(process_id, f"终止进程失败: {str(e)}")
        return False
        
    def kill_process(self, process_id):
        if process_id in self.processes:
            try:
                process = self.processes[process_id]
                if hasattr(process, 'kill'):
                    process.kill()
                else:
                    process.terminate()
                return True
            except Exception as e:
                self.error_occurred.emit(process_id, f"强制终止进程失败: {str(e)}")
        return False
        
    def is_process_running(self, process_id):
        if process_id in self.processes:
            return self.processes[process_id].poll() is None
        return False
        
    def get_process_count(self):
        return len(self.processes)
        
    def cleanup(self):
        for process_id in list(self.processes.keys()):
            self.terminate_process(process_id)
            
class OutputProcessor:
    @staticmethod
    def process_ansi_output(text):
        ansi_color_map = {
            '\033[30m': '<span style="color: #2c3e50;">',
            '\033[31m': '<span style="color: #e74c3c;">',
            '\033[32m': '<span style="color: #27ae60;">',
            '\033[33m': '<span style="color: #f39c12;">',
            '\033[34m': '<span style="color: #3498db;">',
            '\033[35m': '<span style="color: #9b59b6;">',
            '\033[36m': '<span style="color: #1abc9c;">',
            '\033[37m': '<span style="color: #ecf0f1;">',
            '\033[0m': '</span>',
            '\033[1m': '<strong>',
            '\033[22m': '</strong>',
        }
        
        processed_text = text
        for ansi_code, html_tag in ansi_color_map.items():
            processed_text = processed_text.replace(ansi_code, html_tag)
            
        return processed_text
        
    @staticmethod
    def clean_output_for_log(text):
        cleaned = clean_ansi_codes(text)
        return cleaned.strip()