from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit,
    QPushButton, QLabel, QFrame, QSplitter, QScrollArea, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
import json
import os
import re
import shlex
from .process import ProcessManager

from .utils import get_system_font, clean_ansi_codes
from .ansi_parser import ANSITextRenderer, ANSIParser
from .draggable_tab_widget import DraggableTabWidget
import uuid
from datetime import datetime

class ProcessTab(QWidget):
    process_stopped = Signal(str)
    
    def __init__(self, process_id, tool_name, theme_manager=None):
        super().__init__()
        self.process_id = process_id
        self.tool_name = tool_name
        self.theme_manager = theme_manager
        self.is_running = False
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(get_system_font())

        self.output_text.setObjectName("terminal_output")
        layout.addWidget(self.output_text)
        
    def append_output(self, text, color=None):
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if color:
            format = QTextCharFormat()
            if color == "error":
                if self.theme_manager:
                    format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_error")))
                else:
                    format.setForeground(QColor("#ff6b6b"))
            elif color == "success":
                if self.theme_manager:
                    format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_success")))
                else:
                    format.setForeground(QColor("#51cf66"))
            elif color == "warning":
                if self.theme_manager:
                    format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_warning")))
                else:
                    format.setForeground(QColor("#ffd43b"))
            else:
                if self.theme_manager:
                    format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_text")))
                else:
                    format.setForeground(QColor("#ffffff"))
            cursor.setCharFormat(format)
        
        cursor.insertText(text)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
        
    def set_running(self, running):
        self.is_running = running
        
    def set_completed(self, exit_code=0):
        self.is_running = False
        
    def stop_process(self):
        if self.is_running:
            self.process_stopped.emit(self.process_id)
            
    def clear_output(self):
        self.output_text.clear()
        
    def send_input(self, text=None):
        pass



class TerminalTab(QWidget):
    process_finished = Signal(str)
    output_received = Signal(str, str)
    
    def __init__(self, tab_name="进程", theme_manager=None):
        super().__init__()
        self.tab_name = tab_name
        self.tab_id = str(uuid.uuid4())
        self.theme_manager = theme_manager
        self.process_manager = ProcessManager()
        self.current_process = None
        self.command_history = []
        self.history_index = -1
        self.output_timer = None
        self.working_directory = os.getcwd()
        

        self.search_matches = []
        self.current_match_index = -1
        

        self.ansi_renderer = None
        self.ansi_parser = ANSIParser()
        
        self.init_ui()
        self.setup_connections()
        self.setup_process_connections()
        self.setup_ansi_renderer()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        toolbar_layout = QHBoxLayout()
        

        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("status_label")
        toolbar_layout.addWidget(self.status_label)
        

        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.clear_output)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)
        
        self.kill_button = QPushButton("强制终止")
        self.kill_button.clicked.connect(self.kill_process)
        self.kill_button.setEnabled(False)
        
        toolbar_layout.addWidget(self.clear_button)
        toolbar_layout.addWidget(self.stop_button)
        toolbar_layout.addWidget(self.kill_button)
        

        toolbar_layout.addSpacing(20)
        

        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(0, 0, 0, 0)
        search_container_layout.setSpacing(0)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索终端输出...")
        self.search_edit.setObjectName("search_edit")
        self.search_edit.setMaximumWidth(200)
        

        self.case_sensitive_btn = QPushButton("Aa")
        self.case_sensitive_btn.setCheckable(True)
        self.case_sensitive_btn.setToolTip("区分大小写")
        self.case_sensitive_btn.setObjectName("case_sensitive_btn")
        self.case_sensitive_btn.setFixedSize(24, 24)
        
        self.regex_btn = QPushButton(".*")
        self.regex_btn.setCheckable(True)
        self.regex_btn.setToolTip("正则表达式")
        self.regex_btn.setObjectName("regex_btn")
        self.regex_btn.setFixedSize(24, 24)
        

        search_container_layout.addWidget(self.search_edit)
        search_container_layout.addWidget(self.case_sensitive_btn)
        search_container_layout.addWidget(self.regex_btn)
        search_container.setObjectName("search_container")
        
        self.search_button = QPushButton("搜索")
        self.search_button.setObjectName("search_button")
        
        self.prev_button = QPushButton("上一个")
        self.prev_button.setEnabled(False)
        self.prev_button.setObjectName("prev_button")
        
        self.next_button = QPushButton("下一个")
        self.next_button.setEnabled(False)
        self.next_button.setObjectName("next_button")
        
        self.match_label = QLabel("0/0")
        self.match_label.setObjectName("match_label")
        
        self.export_button = QPushButton("导出结果")
        self.export_button.setEnabled(False)
        self.export_button.setObjectName("export_button")
        

        toolbar_layout.addWidget(search_container)
        toolbar_layout.addWidget(self.search_button)
        toolbar_layout.addWidget(self.prev_button)
        toolbar_layout.addWidget(self.next_button)
        toolbar_layout.addWidget(self.match_label)
        toolbar_layout.addWidget(self.export_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        

        from PySide6.QtWidgets import QListWidget, QListWidgetItem
        self.search_results_area = QListWidget()
        self.search_results_area.setMaximumHeight(400)
        self.search_results_area.setVisible(False)
        self.search_results_area.setObjectName("search_results_area")

        self.search_results_area.setWordWrap(True)
        self.search_results_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.search_results_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.search_results_area.itemClicked.connect(self.on_search_result_clicked)
        layout.addWidget(self.search_results_area)
        

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(get_system_font())
        self.output_area.setObjectName("output_area")
        layout.addWidget(self.output_area)
        

        input_layout = QHBoxLayout()
        

        self.prompt_label = QLabel("$")
        self.prompt_label.setObjectName("prompt_label")
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入命令...")
        self.input_line.setFont(get_system_font())
        self.input_line.setObjectName("input_line")
        
        self.send_button = QPushButton("执行")
        self.send_button.clicked.connect(self.execute_command)
        
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)
        
    def setup_connections(self):
        self.input_line.returnPressed.connect(self.execute_command)
        

        self.search_edit.returnPressed.connect(self.search_text)
        self.search_button.clicked.connect(self.search_text)


        self.prev_button.clicked.connect(self.find_previous)
        self.next_button.clicked.connect(self.find_next)
        self.export_button.clicked.connect(self.export_search_results)
        
    def setup_ansi_renderer(self):
        """设置ANSI渲染器"""
        try:
            self.ansi_renderer = ANSITextRenderer(self.output_area)

            if self.theme_manager:
                default_fg = self.theme_manager.get_theme_color("terminal_text")
                default_bg = self.theme_manager.get_theme_color("terminal_bg")
                self.ansi_renderer.set_default_colors(default_fg, default_bg)
            else:
                self.ansi_renderer.set_default_colors("#ffffff", "#1e1e1e")
        except Exception as e:

            print(f"ANSI渲染器初始化失败: {e}")
            self.ansi_renderer = None
        
    def keyPressEvent(self, event):
        """处理键盘事件，支持命令历史"""
        if event.key() == Qt.Key_Up:
            self.navigate_history(-1)
        elif event.key() == Qt.Key_Down:
            self.navigate_history(1)
        else:
            super().keyPressEvent(event)
            
    def navigate_history(self, direction):
        """导航命令历史"""
        if not self.command_history:
            return
            
        self.history_index += direction
        self.history_index = max(-1, min(len(self.command_history) - 1, self.history_index))
        
        if self.history_index >= 0:
            self.input_line.setText(self.command_history[self.history_index])
        else:
            self.input_line.clear()
            
    def execute_command(self):
        """执行命令"""
        command = self.input_line.text().strip()
        if not command:
            return
            

        if self.is_process_running():

            self.send_input(command)
            self.input_line.clear()
            return
            

        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = -1
        

        self.append_output(f"$ {command}", "command")
        self.input_line.clear()
        

        try:

            import shlex
            try:
                command_parts = shlex.split(command)
            except ValueError:

                command_parts = command.split()
                
            if not command_parts:
                return
                

            success = self.process_manager.execute_tool(
                process_id=self.tab_id,
                tool_path=self.working_directory,
                command_parts=command_parts,
                working_dir=self.working_directory
            )
            
            if success:
                if self.theme_manager:
                    running_color = self.theme_manager.get_theme_color("warning")
                    self.update_status("运行中", running_color)
                else:
                    self.update_status("运行中", "#d4a853")
                self.stop_button.setEnabled(True)
                self.kill_button.setEnabled(True)
            else:
                self.append_output("命令执行失败", "error")
                
        except Exception as e:
            self.append_output(f"执行错误: {str(e)}", "error")
            
    def setup_process_connections(self):
        """设置进程连接"""
        self.process_manager.output_received.connect(self.on_output_received)
        self.process_manager.process_finished.connect(self.on_process_finished)
        self.process_manager.process_started.connect(self.on_process_started)
        self.process_manager.error_occurred.connect(self.on_error_occurred)
        
    def on_output_received(self, process_id, text):
        """处理进程输出"""
        if process_id == self.tab_id:

            self.append_ansi_output(text, "stdout")
            
    def on_process_finished(self, process_id, exit_code):
        """处理进程完成"""
        if process_id == self.tab_id:
            self.handle_process_finished(exit_code)
            
    def on_process_started(self, process_id):
        """处理进程启动"""
        if process_id == self.tab_id:
            pass
                    
    def on_error_occurred(self, process_id, error_msg):
        """处理进程错误"""
        if process_id == self.tab_id:
            self.append_output(f"错误: {error_msg}", "error")
            
    def handle_process_finished(self, exit_code=0):
        """处理进程结束"""

        if hasattr(self, 'stop_check_timer'):
            self.stop_check_timer.stop()
            
        if exit_code == 0:
            self.append_output(f"\n进程完成 (退出码: {exit_code})", "success")
            if self.theme_manager:
                success_color = self.theme_manager.get_theme_color("success")
                self.update_status("完成", success_color)
            else:
                self.update_status("完成", "#2d5a2d")
        else:
            self.append_output(f"\n进程异常退出 (退出码: {exit_code})", "error")
            if self.theme_manager:
                error_color = self.theme_manager.get_theme_color("error")
                self.update_status("错误", error_color)
            else:
                self.update_status("错误", "#a85454")
            
        self.current_process = None
        self.stop_button.setEnabled(False)
        self.kill_button.setEnabled(False)
        

        self.process_finished.emit(self.tab_id)
        

        if exit_code == 0 and hasattr(self, 'tool_name'):

            main_window = self.window()
            if (hasattr(main_window, 'notification_manager') and 
                main_window.notification_manager):

                process_name = getattr(self, 'tab_name', '进程')
                main_window.notification_manager.process_completed(
                    self.tool_name, self.tab_id, self.tab_id, process_name
                )
        
    def append_output(self, text, output_type="normal"):
        """添加输出文本（传统方式，用于非ANSI文本）"""
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        

        format = QTextCharFormat()
        
        if output_type == "command":
            if self.theme_manager:
                format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_command")))
            else:
                format.setForeground(QColor("#00ff00"))
            format.setFontWeight(QFont.Bold)
        elif output_type == "error" or output_type == "stderr":
            if self.theme_manager:
                format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_error")))
            else:
                format.setForeground(QColor("#ff6b6b"))
        elif output_type == "success":
            if self.theme_manager:
                format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_success")))
            else:
                format.setForeground(QColor("#51cf66"))
        elif output_type == "stdout":
            if self.theme_manager:
                format.setForeground(QColor(self.theme_manager.get_theme_color("terminal_text")))
            else:
                format.setForeground(QColor("#ffffff"))
        else:
            if self.theme_manager:
                format.setForeground(QColor(self.theme_manager.get_theme_color("text_secondary")))
            else:
                format.setForeground(QColor("#cccccc"))
            
        cursor.setCharFormat(format)
        cursor.insertText(text + "\n")
        
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()
        

        self.output_received.emit(text, output_type)
    
    def append_ansi_output(self, text, output_type="stdout"):
        """添加ANSI格式的输出文本"""
        if not text:
            return
            

        if output_type in ["command", "error", "success"]:
            self.append_output(text, output_type)
            return
        
        try:

            if self.ansi_renderer:
                self.ansi_renderer.append_ansi_text(text)
            else:

                clean_text = self.ansi_parser.strip_ansi(text)
                self.append_output(clean_text, output_type)
        except Exception as e:

            try:
                clean_text = self.ansi_parser.strip_ansi(text)
                self.append_output(clean_text, output_type)
            except:

                self.append_output(text, output_type)
        

        try:
            clean_text = self.ansi_parser.strip_ansi(text)
            self.output_received.emit(clean_text, output_type)
        except:

            self.output_received.emit(text, output_type)
        
    def update_status(self, status, color):
        """更新状态显示"""
        self.status_label.setText(status)

            
    def clear_output(self):
        """清空输出"""
        if self.ansi_renderer:
            self.ansi_renderer.clear_and_reset()
        else:
            self.output_area.clear()
        self.append_output("终端已清空", "normal")
        
    def stop_process(self):
        """停止进程"""
        if self.tab_id in self.process_manager.processes:
            try:
                process = self.process_manager.processes[self.tab_id]
                if hasattr(process, 'terminate'):
                    process.terminate()
                elif hasattr(process, 'process'):
                    process.process.terminate()
                self.append_output("正在停止进程...", "normal")
                

                if self.theme_manager:
                    warning_color = self.theme_manager.get_theme_color("warning")
                    self.update_status("停止中", warning_color)
                else:
                    self.update_status("停止中", "#d4a853")
                    

                self.stop_check_timer = QTimer()
                self.stop_check_timer.timeout.connect(self.check_process_stopped)
                self.stop_check_timer.start(500)
                
            except Exception as e:
                self.append_output(f"停止进程失败: {str(e)}", "error")
                
    def check_process_stopped(self):
        """检查进程是否已经停止"""
        if not self.is_process_running():

            if hasattr(self, 'stop_check_timer'):
                self.stop_check_timer.stop()
                

            if self.tab_id not in self.process_manager.processes:
                return
                

            self.handle_process_finished(0)
                
    def kill_process(self):
        """强制终止进程"""
        if self.tab_id in self.process_manager.processes:
            try:
                process = self.process_manager.processes[self.tab_id]
                if hasattr(process, 'kill'):
                    process.kill()
                elif hasattr(process, 'process'):
                    process.process.kill()
                self.append_output("强制终止进程", "error")
                self.handle_process_finished(-1)
            except Exception as e:
                self.append_output(f"强制终止失败: {str(e)}", "error")
                
    def send_input(self, text):
        """向进程发送输入"""
        if self.tab_id in self.process_manager.processes:
            try:
                process = self.process_manager.processes[self.tab_id]
                

                self.append_output(f"> {text}", "input")
                

                success = False
                

                if self.process_manager.send_input(self.tab_id, text):
                    success = True

                elif hasattr(process, 'write'):
                    try:
                        process.write(text + "\r\n")
                        success = True
                    except Exception:
                        pass

                elif hasattr(process, 'stdin') and process.stdin:
                    try:
                        process.stdin.write(text + "\n")
                        process.stdin.flush()
                        success = True
                    except Exception:
                        pass
                
                if not success:
                    self.append_output("发送输入失败: 无法找到有效的输入方法", "error")
                    
            except Exception as e:
                self.append_output(f"发送输入失败: {str(e)}", "error")
                
    def is_process_running(self):
        """检查是否有进程在运行"""
        if self.tab_id in self.process_manager.processes:
            process = self.process_manager.processes[self.tab_id]
            if hasattr(process, 'poll'):
                return process.poll() is None
            elif hasattr(process, 'process'):
                return process.process.poll() is None
        return False
        
    def get_process_info(self):
        """获取进程信息"""
        if self.tab_id in self.process_manager.processes:
            return {
                'command': 'Unknown',
                'status': 'running' if self.is_process_running() else 'finished'
            }
        return None
        
    def set_working_directory(self, directory):
        """设置工作目录"""
        if os.path.exists(directory):
            self.working_directory = directory
            os.chdir(directory)
            return True
        return False
        
    def search_text(self):
        """搜索文本"""
        search_term = self.search_edit.text()
        if not search_term:
            self.clear_search_highlights()
            self.match_label.setText("0/0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.search_results_area.setVisible(False)
            return
            

        self.clear_search_highlights()
        

        case_sensitive = self.case_sensitive_btn.isChecked()
        use_regex = self.regex_btn.isChecked()
        

        matches = self.find_matches(search_term, case_sensitive, use_regex)
        
        if matches:
            self.search_matches = matches
            self.current_match_index = 0
            self.highlight_matches()
            self.show_search_results_summary()
            self.match_label.setText(f"1/{len(matches)}")
            self.prev_button.setEnabled(len(matches) > 1)
            self.next_button.setEnabled(len(matches) > 1)
            self.export_button.setEnabled(True)
            

            self.jump_to_match(0)
        else:
            self.search_matches = []
            self.match_label.setText("0/0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.export_button.setEnabled(False)
            self.search_results_area.setVisible(False)
            
    def find_matches(self, search_term, case_sensitive, use_regex):
        """查找匹配项 - 使用QTextDocument查找确保位置准确"""
        matches = []
        document = self.output_area.document()
        
        try:
            if use_regex:
                import re

                text = self.output_area.toPlainText()
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(search_term, flags)
                for match in pattern.finditer(text):
                    matches.append((match.start(), match.end()))
            else:

                from PySide6.QtGui import QTextDocument
                
                find_flags = QTextDocument.FindFlag(0)
                if case_sensitive:
                    find_flags |= QTextDocument.FindFlag.FindCaseSensitively
                
                cursor = QTextCursor(document)
                cursor.setPosition(0)
                
                while True:
                    cursor = document.find(search_term, cursor, find_flags)
                    if cursor.isNull():
                        break
                    
                    start = cursor.selectionStart()
                    end = cursor.selectionEnd()
                    matches.append((start, end))
                    

                    cursor.setPosition(start + 1)
                    
        except Exception as e:

            print(f"搜索错误: {e}")
            
        return matches
        
    def clear_search_highlights(self):
        """清除搜索高亮，保持ANSI格式"""
        if not hasattr(self, 'search_highlights') or not self.search_highlights:
            return
            

        document = self.output_area.document()
        cursor = QTextCursor(document)
        
        for start, end, original_format in self.search_highlights:
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)

            cursor.setCharFormat(original_format)
        

        self.search_highlights = []
        
    def highlight_matches(self):
        """高亮显示匹配项，保持ANSI格式"""
        if not hasattr(self, 'search_matches') or not self.search_matches:
            return
            

        self.clear_search_highlights()
        

        self.search_highlights = []
        

        document = self.output_area.document()
        cursor = QTextCursor(document)
        

        for i, (start, end) in enumerate(self.search_matches):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            

            original_format = cursor.charFormat()
            

            highlight_format = QTextCharFormat(original_format)
            
            if i == self.current_match_index:

                highlight_format.setBackground(QColor("#ff8c00"))

                if self._is_light_color(original_format.foreground().color()):
                    highlight_format.setForeground(QColor("#000000"))
                else:
                    highlight_format.setForeground(QColor("#ffffff"))
            else:

                highlight_format.setBackground(QColor("#ffff00"))

                highlight_format.setForeground(QColor("#000000"))
            

            cursor.setCharFormat(highlight_format)
            

            self.search_highlights.append((start, end, original_format))
        

        cursor.clearSelection()
        self.output_area.setTextCursor(cursor)
    
    def _is_light_color(self, color):
        """判断颜色是否为浅色"""
        if not color.isValid():
            return False

        r, g, b = color.red(), color.green(), color.blue()
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness > 128
            
    def jump_to_match(self, index):
         """跳转到指定匹配项"""
         if not hasattr(self, 'search_matches') or not self.search_matches:
             return
             
         if 0 <= index < len(self.search_matches):
             start, end = self.search_matches[index]
             cursor = self.output_area.textCursor()
             cursor.setPosition(start)
             cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
             
             self.output_area.setTextCursor(cursor)
             self.output_area.ensureCursorVisible()
            
    def update_search_results_selection(self):
        """更新搜索结果列表的选中状态"""
        if not hasattr(self, 'search_matches') or not self.search_matches:
            return
            

        for i in range(2, self.search_results_area.count()):
            item = self.search_results_area.item(i)
            match_index = item.data(Qt.ItemDataRole.UserRole)
            
            if match_index == self.current_match_index:
                item.setBackground(QColor("#fff3e0"))
                item.setForeground(QColor("#f57c00"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)

                self.search_results_area.setCurrentRow(i)
            else:
                item.setBackground(QColor("#ffffff"))
                item.setForeground(QColor("#333333"))
                font = item.font()
                font.setBold(False)
                item.setFont(font)
            
    def find_previous(self):
        """查找上一个匹配项"""
        if hasattr(self, 'search_matches') and self.search_matches:
            self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
            self.highlight_matches()
            self.jump_to_match(self.current_match_index)
            self.match_label.setText(f"{self.current_match_index + 1}/{len(self.search_matches)}")
            self.update_search_results_selection()
            
    def find_next(self):
        """查找下一个匹配项"""
        if hasattr(self, 'search_matches') and self.search_matches:
            self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
            self.highlight_matches()
            self.jump_to_match(self.current_match_index)
            self.match_label.setText(f"{self.current_match_index + 1}/{len(self.search_matches)}")
            self.update_search_results_selection()
    def show_search_results_summary(self):
        """显示搜索结果汇聚 - 显示所有匹配项"""
        if not hasattr(self, 'search_matches') or not self.search_matches:
            self.search_results_area.setVisible(False)
            return
            
        search_term = self.search_edit.text()
        text = self.output_area.toPlainText()
        

        self.search_results_area.clear()
        

        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import Qt
        
        title_item = QListWidgetItem(f"搜索词: '{search_term}' | 匹配数量: {len(self.search_matches)}")
        title_item.setFlags(Qt.ItemFlag.NoItemFlags)
        title_item.setBackground(QColor("#e3f2fd"))
        title_item.setForeground(QColor("#1976d2"))
        font = title_item.font()
        font.setBold(True)
        title_item.setFont(font)
        self.search_results_area.addItem(title_item)
        

        separator_item = QListWidgetItem("=" * 80)
        separator_item.setFlags(Qt.ItemFlag.NoItemFlags)
        separator_item.setBackground(QColor("#f5f5f5"))
        self.search_results_area.addItem(separator_item)
        

        for i, (start, end) in enumerate(self.search_matches):

            line_start = text.rfind('\n', 0, start) + 1
            line_end = text.find('\n', end)
            if line_end == -1:
                line_end = len(text)
                
            line_text = text[line_start:line_end].strip()
            line_number = text[:start].count('\n') + 1
            match_text = text[start:end]
            

            display_text = line_text
            

            highlighted_text = display_text
            

            item_text = f"匹配 {i+1} (行{line_number}): {highlighted_text}"
            item = QListWidgetItem(item_text)
            

            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            

            item.setData(Qt.ItemDataRole.UserRole, i)
            

            if i == self.current_match_index:
                item.setBackground(QColor("#fff3e0"))
                item.setForeground(QColor("#f57c00"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            else:
                item.setBackground(QColor("#ffffff"))
                item.setForeground(QColor("#333333"))
            
            self.search_results_area.addItem(item)
            
        self.search_results_area.setVisible(True)
        

        if self.current_match_index >= 0 and self.current_match_index < self.search_results_area.count() - 2:

            self.search_results_area.setCurrentRow(self.current_match_index + 2)
    
    def on_search_result_clicked(self, item):
        """处理搜索结果点击事件"""
        match_index = item.data(Qt.ItemDataRole.UserRole)
        if match_index is not None and isinstance(match_index, int):
            if 0 <= match_index < len(self.search_matches):
                self.current_match_index = match_index
                self.highlight_matches()
                self.jump_to_match(match_index)
                self.match_label.setText(f"{match_index + 1}/{len(self.search_matches)}")
                

                self.update_search_results_selection()
        
    def export_search_results(self):
         """导出搜索结果"""
         if not hasattr(self, 'search_matches') or not self.search_matches:
             return
             
         search_term = self.search_edit.text()
         text = self.output_area.toPlainText()
         lines = text.split('\n')
         
         results = []
         results.append(f"搜索词: {search_term}")
         results.append(f"匹配数量: {len(self.search_matches)}")
         results.append(f"搜索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
         results.append(f"区分大小写: {'是' if self.case_sensitive_btn.isChecked() else '否'}")
         results.append(f"正则表达式: {'是' if self.regex_btn.isChecked() else '否'}")
         results.append("=" * 60)
         
         for i, (start, end) in enumerate(self.search_matches):

             line_start = text.rfind('\n', 0, start) + 1
             line_end = text.find('\n', end)
             if line_end == -1:
                 line_end = len(text)
                 
             line_text = text[line_start:line_end]
             line_number = text[:start].count('\n') + 1
             

             match_start_in_line = start - line_start
             match_end_in_line = end - line_start
             match_text = text[start:end]
             
             results.append(f"\n匹配 {i+1}:")
             results.append(f"  行号: {line_number}")
             results.append(f"  匹配文本: '{match_text}'")
             results.append(f"  行内位置: {match_start_in_line}-{match_end_in_line}")
             results.append(f"  完整行内容: {line_text}")
             results.append("-" * 40)
             

         try:
             filename = f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
             with open(filename, 'w', encoding='utf-8') as f:
                 f.write('\n'.join(results))
             self.append_output(f"\n[搜索] 搜索结果已导出到: {filename}\n", "info")
         except Exception as e:
             self.append_output(f"\n[搜索] 导出失败: {str(e)}\n", "error")

class TerminalArea(QWidget):
    tool_execution_started = Signal(str, str)
    tool_execution_finished = Signal(str, int)
    
    def __init__(self, theme_manager=None):
        super().__init__()
        self.theme_manager = theme_manager
        self.tabs = {}
        self.tool_processes = {}
        self.current_filter_tool = None
        self.all_tabs = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        toolbar_layout = QHBoxLayout()
        

        self.run_mode_button = QPushButton("当前标签页")
        self.run_mode_button.setCheckable(True)
        self.run_mode_button.setToolTip("点击切换命令执行模式：当前标签页 / 新标签页")
        self.run_mode_button.clicked.connect(self.toggle_run_mode)
        self.run_mode_button.setObjectName("run_mode_button")
        self.run_in_new_tab = False
        
        self.show_all_button = QPushButton("显示所有")
        self.show_all_button.clicked.connect(self.show_all_tabs)
        
        self.clear_all_button = QPushButton("清空所有")
        self.clear_all_button.clicked.connect(self.clear_all_terminals)
        
        self.stop_all_button = QPushButton("停止所有")
        self.stop_all_button.clicked.connect(self.stop_all_processes)
        
        toolbar_layout.addWidget(self.run_mode_button)
        toolbar_layout.addWidget(self.show_all_button)
        toolbar_layout.addWidget(self.clear_all_button)
        toolbar_layout.addWidget(self.stop_all_button)
        toolbar_layout.addStretch()
        

        self.status_info = QLabel("就绪")
        self.status_info.setObjectName("terminal_status_info")
        toolbar_layout.addWidget(self.status_info)
        
        layout.addLayout(toolbar_layout)
        

        self.tab_widget = DraggableTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        

        self.tab_widget.tab_renamed.connect(self.on_tab_renamed)
        self.tab_widget.tab_moved.connect(self.on_tab_moved)
        self.tab_widget.tab_duplicated.connect(self.on_tab_duplicated)
        self.tab_widget.new_tab_requested.connect(self.add_terminal_tab)
        

        self.tab_widget.tab_clicked.connect(self.on_tab_clicked)
        

        self.add_terminal_tab("进程1")
        
        layout.addWidget(self.tab_widget)
    
    def toggle_run_mode(self):
        """切换命令执行模式"""
        self.run_in_new_tab = not self.run_in_new_tab
        if self.run_in_new_tab:
            self.run_mode_button.setText("新标签页")
            self.run_mode_button.setChecked(True)
            self.update_status_info("命令执行模式：新标签页")
        else:
            self.run_mode_button.setText("当前标签页")
            self.run_mode_button.setChecked(False)
            self.update_status_info("命令执行模式：当前标签页")
    
    def add_terminal_tab(self, name=None):
        """添加新的终端标签页"""
        if name is None:
            name = f"进程{len(self.tabs) + 1}"
            
        tab = TerminalTab(name, self.theme_manager)
        tab_index = self.tab_widget.addTab(tab, name)
        self.tabs[tab.tab_id] = tab
        

        tab.process_finished.connect(self.on_process_finished)
        tab.output_received.connect(self.on_output_received)
        

        self.tab_widget.setCurrentIndex(tab_index)
        
        self.update_status_info()
        return tab
    
    def on_tab_renamed(self, index, new_name):
        """标签页重命名事件处理"""
        if 0 <= index < self.tab_widget.count():
            tab = self.tab_widget.widget(index)
            if tab and hasattr(tab, 'tab_name'):
                old_name = tab.tab_name
                tab.tab_name = new_name
                self.update_status_info(f"标签页 '{old_name}' 已重命名为 '{new_name}'")
    
    def on_tab_moved(self, from_index, to_index):
        """标签页移动事件处理"""
        self.update_status_info(f"标签页已从位置 {from_index + 1} 移动到位置 {to_index + 1}")
    
    def on_tab_duplicated(self, index):
        """标签页复制事件处理"""
        if 0 <= index < self.tab_widget.count():
            original_tab = self.tab_widget.widget(index)
            if original_tab and hasattr(original_tab, 'tab_name'):

                new_tab = self.add_terminal_tab()
                

                if hasattr(original_tab, 'working_directory'):
                    new_tab.set_working_directory(original_tab.working_directory)
                
                self.update_status_info(f"已复制标签页: {new_tab.tab_name}")
    
    def add_new_tab_with_command(self, command, tab_name=None):
        """添加新标签页并执行命令 - 仅在运行工具时使用"""

        tab = self.get_current_tab()
        if not tab:
            tab = self.add_terminal_tab(tab_name)
        else:

            if tab_name:
                index = self.tab_widget.indexOf(tab)
                if index >= 0:
                    self.tab_widget.setTabText(index, tab_name)
                    tab.tab_name = tab_name
                    
        tab.input_line.setText(command)
        tab.execute_command()
        return tab
    
    def close_tab(self, index):
        """关闭标签页"""
        if self.tab_widget.count() <= 1:
            return
            
        tab = self.tab_widget.widget(index)
        if tab and hasattr(tab, 'tab_id'):

            if tab.is_process_running():
                reply = QMessageBox.question(
                    self, "确认关闭", 
                    f"终端 '{tab.tab_name}' 中有进程正在运行，确定要关闭吗？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
                    
                tab.kill_process()
            

            if tab.tab_id in self.all_tabs:
                del self.all_tabs[tab.tab_id]
            

            if tab.tab_id in self.tabs:
                del self.tabs[tab.tab_id]
                
        self.tab_widget.removeTab(index)
        self.update_status_info()
        
    def on_tab_changed(self, index):
        """标签页切换事件"""
        self.update_status_info()

        self.handle_tab_notification_clear(index)
        
    def on_tab_clicked(self, index):
        """标签页点击事件"""

        self.handle_tab_notification_clear(index)
        
    def handle_tab_notification_clear(self, index):
        """处理标签页通知清除"""
        if 0 <= index < self.tab_widget.count():
            tab = self.tab_widget.widget(index)
            if tab and hasattr(tab, 'tab_id'):

                main_window = self.window()
                if (hasattr(main_window, 'notification_manager') and 
                    main_window.notification_manager):
                    main_window.notification_manager.on_tab_clicked(tab.tab_id)
        
    def on_process_finished(self, tab_id):
        """进程完成事件"""
        if tab_id in self.tabs:
            tab = self.tabs[tab_id]

            for tool_name, process_tab_id in self.tool_processes.items():
                if process_tab_id == tab_id:
                    process_info = tab.get_process_info()
                    exit_code = process_info.get('exit_code', -1) if process_info else -1
                    self.tool_execution_finished.emit(tool_name, exit_code)
                    del self.tool_processes[tool_name]
                    break
                    
        self.update_status_info()
        
    def on_output_received(self, text, output_type):
        """输出接收事件"""

        pass
        

        
    def get_current_tab(self):
        """获取当前标签页"""
        return self.tab_widget.currentWidget()
        
    def filter_tabs_by_tool(self, tool_name):
        """按工具过滤显示标签页"""
        self.current_filter_tool = tool_name
        

        if not self.all_tabs:
            self.all_tabs = self.tabs.copy()
        else:

            for tab_id, tab in self.tabs.items():
                self.all_tabs[tab_id] = tab
        

        self.tab_widget.clear()
        self.tabs.clear()
        

        tool_tabs_found = False
        for tab_id, tab in self.all_tabs.items():
            if hasattr(tab, 'tool_name') and tab.tool_name == tool_name:
                self.tabs[tab_id] = tab
                self.tab_widget.addTab(tab, tab.tab_name)
                tool_tabs_found = True
        


        

        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(0)
        
        self.update_status_info(f"已切换到工具: {tool_name}")
        
    def create_tool_tab(self, tool_name):
        """为工具创建新的标签页 - 仅在执行工具时调用"""

        tool_tab_count = 0
        for tab in self.all_tabs.values():
            if hasattr(tab, 'tool_name') and tab.tool_name == tool_name:
                tool_tab_count += 1
        
        tab_name = f"进程{tool_tab_count + 1}"
        tab = TerminalTab(tab_name, self.theme_manager)
        tab.tool_name = tool_name
        return tab
        
    def show_all_tabs(self):
        """显示所有标签页 - 只显示已经存在的标签页，不创建新的"""

        current_tabs = {}
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab and hasattr(tab, 'tab_id'):
                current_tabs[tab.tab_id] = tab
            self.tab_widget.setTabVisible(i, True)
            
        self.current_filter_tool = None
        

        self.tab_widget.clear()
        

        if not self.all_tabs:
            self.all_tabs = {}
        

        for tab_id, tab in current_tabs.items():
            self.all_tabs[tab_id] = tab
            

        self.tabs.clear()
        

        if self.all_tabs:
            for tab_id, tab in self.all_tabs.items():

                self.tabs[tab_id] = tab
                self.tab_widget.addTab(tab, tab.tab_name)
        

        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.clear_tool_selection)
        
        self.update_status_info("显示所有标签页")
        
    def clear_tool_selection(self):
        """清除工具选择状态"""

        main_window = self.window()
        if hasattr(main_window, 'current_selected_tool'):
            main_window.current_selected_tool = None
        if hasattr(main_window, 'tool_selector'):
            main_window.tool_selector.clear_selection()
        
    def execute_tool(self, tool_info, parameters, working_dir=None):
        """执行工具"""
        tool_name = tool_info.name if hasattr(tool_info, 'name') else 'Unknown Tool'
        

        run_in_new_tab = self.run_in_new_tab
        
        if run_in_new_tab:

            tab = self.add_terminal_tab()
        else:

            tab = self.get_current_tab()
            if not tab:
                tab = self.add_terminal_tab()
        

        tab.tool_name = tool_name
        

        if not working_dir:
            working_dir = getattr(tool_info, 'path', None)
        
        if working_dir:

            tab.append_output(f"切换到目录: {working_dir}", "normal")
            tab.set_working_directory(working_dir)
            

        command = self.build_tool_command(tool_info, parameters)
        

        tab.append_output(f"⚡ 即将执行工具: {tool_name}", "normal")
        tab.append_output(f"📁 工作目录: {working_dir or '当前目录'}", "normal")
        tab.append_output(f"🔧 命令: {command}", "command")
        

        tab.input_line.setText(command)
        tab.execute_command()
        

        self.tool_processes[tool_name] = tab.tab_id
        self.tool_execution_started.emit(tool_name, tab.tab_id)
        

        tab_index = self.tab_widget.indexOf(tab)
        self.tab_widget.setCurrentIndex(tab_index)
        
        return tab.tab_id
        
    def build_tool_command(self, tool_info, parameters):
        """构建工具执行命令"""
        import sys
        from .utils import get_system_python_executable
        
        executable = getattr(tool_info, 'executable', 'python') or 'python'
        script_path = getattr(tool_info, 'script_path', None)
        
        configured_interpreter = None
        configured_program = None
        
        if hasattr(tool_info, 'config_data') and tool_info.config_data:
            configured_interpreter = tool_info.config_data.get('interpreter_path', '').strip()
            configured_program = tool_info.config_data.get('program_path', '').strip()
            interpreter_type = tool_info.config_data.get('interpreter_type', 'python')
            
            if configured_interpreter and configured_program:
                if interpreter_type == 'python':
                    command_parts = [f'"{configured_interpreter}"', configured_program]
                elif interpreter_type == 'java':
                    command_parts = [f'"{configured_interpreter}"', '-jar', configured_program]
                else:
                    command_parts = [f'"{configured_interpreter}"', configured_program]
            elif configured_program and not configured_interpreter:
                if configured_program.endswith('.exe'):
                    command_parts = [f'./{configured_program}']
                else:
                    if getattr(sys, 'frozen', False):
                        system_python = sys.executable
                    else:
                        system_python = get_system_python_executable()
                    command_parts = [f'"{system_python}"', configured_program]
            else:
                if executable.endswith('.exe') or executable == script_path:
                    command_parts = [f'./{executable}']
                else:
                    if not script_path:
                        script_path = 'main.py'
                    
                    if os.path.isabs(script_path) and hasattr(tool_info, 'path'):
                        script_path = os.path.relpath(script_path, tool_info.path)
                    
                    if executable == 'python' or executable == 'python3':
                        if getattr(sys, 'frozen', False):
                            system_python = sys.executable
                        else:
                            system_python = get_system_python_executable()
                        command_parts = [f'"{system_python}"', script_path]
                    else:
                        command_parts = [executable, script_path]
        else:
            if executable.endswith('.exe') or executable == script_path:
                command_parts = [f'./{executable}']
            else:
                if not script_path:
                    script_path = 'main.py'
                
                if os.path.isabs(script_path) and hasattr(tool_info, 'path'):
                    script_path = os.path.relpath(script_path, tool_info.path)
                
                if executable == 'python' or executable == 'python3':
                    if getattr(sys, 'frozen', False):
                        system_python = sys.executable
                    else:
                        system_python = get_system_python_executable()
                    command_parts = [f'"{system_python}"', script_path]
                else:
                    command_parts = [executable, script_path]
        

        for param_name, param_value in parameters.items():
            if param_value is not None and param_value != '':
                if isinstance(param_value, bool):
                    if param_value:

                        if param_name.startswith('-'):
                            command_parts.append(param_name)
                        else:
                            command_parts.append(f"--{param_name}")
                else:

                    if param_name.startswith('-'):
                        command_parts.append(param_name)
                    else:
                        command_parts.append(f"--{param_name}")
                    command_parts.append(str(param_value))
            elif isinstance(param_value, bool) and param_value:

                if param_name.startswith('-'):
                    command_parts.append(param_name)
                else:
                    command_parts.append(f"--{param_name}")
                    
        return ' '.join(command_parts)
        
    def execute_in_terminal(self, command, tab_name=None):
        """在指定终端中执行命令"""
        if tab_name:

            for tab in self.tabs.values():
                if tab.tab_name == tab_name:
                    tab.input_line.setText(command)
                    tab.execute_command()
                    return tab.tab_id

            tab = self.get_current_tab()
            if not tab:
                tab = self.add_terminal_tab(tab_name)
            tab.input_line.setText(command)
            tab.execute_command()
            return tab.tab_id
        else:

            current_tab = self.get_current_tab()
            if current_tab:
                current_tab.input_line.setText(command)
                current_tab.execute_command()
                return current_tab.tab_id
        return None
        
    def clear_all_terminals(self):
        """清空所有终端"""
        for tab in self.tabs.values():
            tab.clear_output()
            
    def stop_all_processes(self):
        """停止所有进程"""
        running_count = 0
        for tab in self.tabs.values():
            if tab.is_process_running():
                tab.stop_process()
                running_count += 1
                
        if running_count > 0:
            self.update_status_info(f"正在停止 {running_count} 个进程...")
        else:
            self.update_status_info("没有运行中的进程")
            
    def get_running_processes(self, tool_name=None):
        """获取运行中的进程信息
        
        Args:
            tool_name: 如果指定，只返回该工具的进程；否则返回所有进程
        """
        processes = []
        for tab in self.tabs.values():
            if tab.is_process_running():

                if tool_name and hasattr(tab, 'tool_name'):
                    if tab.tool_name != tool_name:
                        continue
                
                process_info = tab.get_process_info()
                if process_info:
                    process_info['tab_name'] = tab.tab_name
                    process_info['tab_id'] = tab.tab_id
                    process_info['tool_name'] = getattr(tab, 'tool_name', None)
                    processes.append(process_info)
        return processes
        
    def update_status_info(self, message=None):
        """更新状态信息"""
        if message:
            self.status_info.setText(message)
            QTimer.singleShot(3000, lambda: self.update_status_info())
            return
            

        current_tab = self.get_current_tab()
        current_tool_name = None
        if current_tab and hasattr(current_tab, 'tool_name'):
            current_tool_name = current_tab.tool_name
        

        all_processes = self.get_running_processes()
        current_tool_processes = self.get_running_processes(current_tool_name) if current_tool_name else []
        
        total_tabs = len(self.tabs)
        all_running_count = len(all_processes)
        current_tool_running_count = len(current_tool_processes)
        

        if current_tool_name:
            if current_tool_running_count > 0:
                self.status_info.setText(f"工具: {current_tool_name} | 运行中: {current_tool_running_count} | 总终端: {total_tabs}")
            else:
                self.status_info.setText(f"工具: {current_tool_name} | 就绪 | 总终端: {total_tabs}")
        else:
            if all_running_count > 0:
                self.status_info.setText(f"终端: {total_tabs} | 运行中: {all_running_count}")
            else:
                self.status_info.setText(f"终端: {total_tabs} | 就绪")
            
    def send_input_to_tab(self, tab_id, text):
        """向指定标签页发送输入"""
        if tab_id in self.tabs:
            self.tabs[tab_id].send_input(text)
            return True
        return False
        
    def get_tab_output(self, tab_id, lines=None):
        """获取指定标签页的输出"""
        if tab_id in self.tabs:
            output_text = self.tabs[tab_id].output_area.toPlainText()
            if lines:
                output_lines = output_text.split('\n')
                return '\n'.join(output_lines[-lines:])
            return output_text
        return None
        
    def create_process_tab(self, tool_name):
        """为兼容性保留的方法"""
        tab = self.add_terminal_tab(f"工具: {tool_name}")
        return tab, tab.tab_id
        
    def get_process_tab(self, process_id):
        """为兼容性保留的方法"""
        return self.tabs.get(process_id)
        
    def remove_process_tab(self, process_id):
        """为兼容性保留的方法"""
        if process_id in self.tabs:
            tab = self.tabs[process_id]
            tab_index = self.tab_widget.indexOf(tab)
            if tab_index >= 0:
                self.close_tab(tab_index)