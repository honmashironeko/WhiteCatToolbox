import os
import json
import platform
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QMenu, QSizePolicy, QApplication, QSplitter
)
from PySide6.QtCore import Qt, QProcess
from PySide6.QtGui import QFont, QTextCursor, QClipboard
from .theme import colors, fonts, params
from .real_terminal import RealTerminal, TerminalSearchPanel
from .real_terminal_process import RealTerminalProcess
from .utils import s
from .i18n import t

class TerminalTextEdit(QTextEdit):
    def __init__(self, parent_tab):
        super().__init__()
        self.parent_tab = parent_tab

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                if cursor.hasSelection():
                    self.parent_tab.copy_selection()
                return
            elif event.key() == Qt.Key.Key_V:
                self.parent_tab.paste_text()
                return
            elif event.key() == Qt.Key.Key_A:
                self.selectAll()
                return
            elif event.key() == Qt.Key.Key_L:
                self.parent_tab.clear_terminal()
                return

        if cursor.position() < self.parent_tab.input_start_position:
            if event.key() not in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown]:
                cursor.setPosition(self.parent_tab.input_start_position)
                self.setTextCursor(cursor)

        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.parent_tab.execute_command()
            return

        if event.key() == Qt.Key.Key_Backspace:
            if cursor.position() <= self.parent_tab.input_start_position and not cursor.hasSelection():
                return

        if event.key() == Qt.Key.Key_Up:
            self.parent_tab.show_previous_command()
            return
        elif event.key() == Qt.Key.Key_Down:
            self.parent_tab.show_next_command()
            return

        super().keyPressEvent(event)
class ProcessTab(QWidget):
    def __init__(self, process, process_name, parent_tabs, use_real_terminal=True):
        super().__init__()
        self.process = process
        self.process_name = process_name
        self.parent_tabs = parent_tabs
        self.use_real_terminal = use_real_terminal
        self.prompt = "$ "  
        self.input_start_position = 0  
        self.history = []  
        self.history_index = 0
        self.real_terminal_process = None
        self.is_current_tab = False
        self.cached_output = []
        self.output_cache_enabled = True
        self.max_cache_size = 5000
        self.cache_batch_size = 1000
        self.cache_flush_threshold = 4000
        self.last_refresh_time = 0
        self.refresh_interval = 50
        self.auto_flush_enabled = True
        self.cache_compression_enabled = True
        self.compression_threshold = 1000
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(s(8), s(8), s(8), s(8))
        layout.setSpacing(s(8))
        control_widget = QWidget()
        control_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px;
            }}
        """)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(s(8), s(4), s(8), s(4))
        control_layout.setSpacing(s(8))
        
        self.status_label = QLabel(t("process.running"))
        self.status_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["success"]};
                background: transparent;
                border: none;
                padding: {s(2)}px {s(6)}px;
            }}
        """)
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        clear_btn = QPushButton(t("process.clear_output"))
        clear_btn.setMinimumWidth(s(60))
        clear_btn.setMinimumHeight(s(28))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["text_disabled"]};
                border: 1px solid {colors["text_disabled"]};
                border-radius: {s(4)}px;
                padding: {s(4)}px {s(12)}px;
                color: white;
                font-weight: 500;
                font-size: {s(8)}pt;
            }}
            QPushButton:hover {{
                background-color: {colors["text_secondary"]};
                border-color: {colors["text_secondary"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["tooltip_text"]};
            }}
        """)
        clear_btn.clicked.connect(self.clear_terminal)
        control_layout.addWidget(clear_btn)
        if self.use_real_terminal:
            self.search_toggle_btn = QPushButton("🔍")
            self.search_toggle_btn.setMinimumWidth(s(32))
            self.search_toggle_btn.setMinimumHeight(s(28))
            self.search_toggle_btn.setToolTip(t("process.search_toggle"))
            self.search_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors["secondary"]};
                    border: 1px solid {colors["secondary"]};
                    border-radius: {s(4)}px;
                    padding: {s(4)}px;
                    color: white;
                    font-weight: 500;
                    font-size: {s(10)}pt;
                }}
                QPushButton:hover {{
                    background-color: {colors["secondary_hover"]};
                    border-color: {colors["secondary_hover"]};
                }}
                QPushButton:pressed {{
                    background-color: {colors["secondary_pressed"]};
                }}
                QPushButton:checked {{
                    background-color: {colors["secondary_pressed"]};
                }}
            """)
            self.search_toggle_btn.setCheckable(True)
            self.search_toggle_btn.setChecked(True)
            self.search_toggle_btn.clicked.connect(self.toggle_search_panel)
            control_layout.addWidget(self.search_toggle_btn)
        
        stop_btn = QPushButton(t("process.stop_process"))
        stop_btn.setMinimumWidth(s(60))
        stop_btn.setMinimumHeight(s(28))
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["danger"]};
                border: 1px solid {colors["danger"]};
                border-radius: {s(4)}px;
                padding: {s(4)}px {s(12)}px;
                color: white;
                font-weight: 500;
                font-size: {s(8)}pt;
            }}
            QPushButton:hover {{
                background-color: {colors["danger_hover"]};
                border-color: {colors["danger_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["danger_pressed"]};
            }}
        """)
        stop_btn.clicked.connect(self.stop_process)
        control_layout.addWidget(stop_btn)
        
        control_widget.setLayout(control_layout)
        layout.addWidget(control_widget)
        main_container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(s(8))
        if self.use_real_terminal:
            self.terminal_output = RealTerminal(self)

            self.terminal_output.command_executed.connect(self.send_command)
            self.real_terminal_process = RealTerminalProcess(self)
            self.real_terminal_process.output_ready.connect(self.terminal_output.append_ansi_text)
            self.real_terminal_process.error_ready.connect(self.terminal_output.append_ansi_text)
            self.real_terminal_process.finished.connect(self.process_finished)
            self.search_panel = TerminalSearchPanel(self)
            self.search_panel.search_requested.connect(self.perform_terminal_search)
            self.search_panel.jump_to_line.connect(self.terminal_output.jump_to_line)
            self.search_panel.setMaximumHeight(s(200))
            
        else:
            self.terminal_output = TerminalTextEdit(self)
            self.search_panel = None
            
        self.terminal_output.setFont(QFont(fonts["monospace"], s(9)))
        self.terminal_output.setMinimumHeight(s(400))  
        terminal_style = f"""
            QTextEdit {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 {colors["terminal_background_start"]}, stop: 1 {colors["terminal_background_end"]});
                color: {colors["terminal_text"]};
                border: 1px solid {colors["terminal_border"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(12)}px;
                font-family: '{fonts["monospace"]}', 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: {s(9)}pt;
                line-height: 1.5;
                selection-background-color: {colors["terminal_selection"]};
            }}
            QTextEdit:focus {{
                border-color: {colors["secondary"]};
            }}
        """
        self.terminal_output.setStyleSheet(terminal_style)
        if self.search_panel:

            main_layout.addWidget(self.search_panel)
            main_layout.addWidget(self.terminal_output)
        else:

            main_layout.addWidget(self.terminal_output)
        
        main_container.setLayout(main_layout)
        
        if not self.use_real_terminal:

            self.terminal_output.setReadOnly(False)
            self.terminal_output.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.terminal_output.customContextMenuRequested.connect(self.show_context_menu)
            self.terminal_output.append(t("messages.welcome_terminal"))
            self.terminal_output.append(t("messages.terminal_features"))
            self.terminal_output.append(t("messages.terminal_control"))
            self.terminal_output.append(t("messages.terminal_logs"))
            self.append_system_log(t("messages.terminal_init"), "success")
            self.show_prompt()
        else:

            self.terminal_output.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.terminal_output.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(main_container)
        
        self.setLayout(layout)
    
    def send_command(self, command: str):
        
        if self.use_real_terminal and self.real_terminal_process:
            if self.real_terminal_process.is_running():
                self.real_terminal_process.send_input(command + "\n")
            else:
                self.append_system_log(t("messages.process_not_running", command), "error")
        else:

            if self.process and self.process.state() == QProcess.Running:
                command_bytes = (command + "\n").encode('utf-8')
                self.process.write(command_bytes)
            else:
                self.append_system_log(t("messages.process_not_running", command), "error")
    
    def start_real_terminal_process(self, program: str, arguments: list = None, working_directory: str = None):
        
        if self.use_real_terminal and self.real_terminal_process:
            self.real_terminal_process.start_process(program, arguments, working_directory)
            self.status_label.setText(t("process.running"))
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["success"]};
                    background: transparent;
                    border: none;
                    padding: {s(2)}px {s(6)}px;
                    font-weight: bold;
                }}
            """)
            self.append_system_log(t("messages.process_started", program), "success")
    
    def show_prompt(self):
        
        if not self.use_real_terminal:
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertText(self.prompt)
            self.input_start_position = cursor.position()
            self.terminal_output.setTextCursor(cursor)
            self.terminal_output.ensureCursorVisible()
    
    def execute_command(self):
        
        if self.use_real_terminal:

            return
            
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        command_text = self.terminal_output.toPlainText()
        last_prompt_pos = command_text.rfind(self.prompt)
        if last_prompt_pos != -1:
            user_input = command_text[last_prompt_pos + len(self.prompt):].strip()
        else:
            user_input = ""
        if user_input and (not self.history or self.history[-1] != user_input):
            self.history.append(user_input)
        self.history_index = len(self.history)
        cursor.insertText("\n")
        if self.process and self.process.state() == QProcess.Running:
            if user_input:
                
                command_bytes = (user_input + "\n").encode('utf-8')
                self.process.write(command_bytes)
                cursor.insertHtml(f"<span style='color: {colors['terminal_command']};'>{t('messages.command_sent', user_input)}</span>\n")
            else:
                
                self.process.write(b"\n")
        else:
            
            if user_input:
                cursor.insertHtml(f"<span style='color: {colors['log_command_error']};'>{t('messages.process_not_running', user_input)}</span>\n")
        self.show_prompt()
    
    def show_previous_command(self):
        
        if self.use_real_terminal:
            return
            
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.replace_current_input(self.history[self.history_index])
    
    def show_next_command(self):
        
        if self.use_real_terminal:
            return
            
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.replace_current_input(self.history[self.history_index])
        elif self.history_index >= len(self.history) - 1:
            self.history_index = len(self.history)
            self.replace_current_input("")
    
    def replace_current_input(self, text):
        
        if self.use_real_terminal:
            return
            
        cursor = self.terminal_output.textCursor()
        cursor.setPosition(self.input_start_position)
        cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(text)
        
        self.terminal_output.setTextCursor(cursor)
    
    def clear_terminal(self):
        
        if self.use_real_terminal:
            self.terminal_output.clear_terminal()
        else:
            self.terminal_output.clear()
            self.show_prompt()
    
    def copy_selection(self):
        
        cursor = self.terminal_output.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            clipboard = QApplication.clipboard()
            clipboard.setText(selected_text)
    
    def paste_text(self):
        
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return
        
        cursor = self.terminal_output.textCursor()
        if cursor.position() < self.input_start_position:
            cursor.setPosition(self.input_start_position)
            self.terminal_output.setTextCursor(cursor)
        clean_text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
        lines = clean_text.splitlines()
        if lines:
            
            first_line = lines[0].strip()
            if first_line:
                cursor.insertText(first_line)
            if len(lines) > 1:
                
                self.execute_command()
                for line in lines[1:]:
                    line = line.strip()
                    if line:  
                        cursor = self.terminal_output.textCursor()
                        cursor.movePosition(cursor.MoveOperation.End)
                        cursor.insertText(line)
                        self.execute_command()
            self.terminal_output.setTextCursor(cursor)
            self.terminal_output.ensureCursorVisible()
    
    def interrupt_process(self):
        
        if self.use_real_terminal and self.real_terminal_process:
            if self.real_terminal_process.is_running():
                self.real_terminal_process.send_interrupt()
                self.append_system_log(t('messages.send_interrupt_signal'), "warning")
            else:
                self.append_system_log(t('messages.no_running_terminal'), "warning")
        else:

            if self.process and self.process.state() == QProcess.ProcessState.Running:
                
                system = platform.system()
                
                if system == "Windows":
                    
                    try:
                        self.process.write(b'\x03')  
                        self.append_system_log(t('messages.send_interrupt_windows'), "warning")
                    except Exception as e:
                        self.append_system_log(f"发送中断信号失败: {e}", "error")
                        
                        self.process.kill()
                        self.append_system_log(t('messages.force_terminate'), "warning")
                else:
                    
                    try:
                        
                        self.process.write(b'\x03')
                        self.append_system_log(t('messages.send_interrupt_unix'), "warning")
                    except Exception as e:
                        self.append_system_log(f"发送中断信号失败: {e}", "error")
                        
                        self.process.terminate()
                        self.append_system_log(t('messages.graceful_terminate'), "warning")
            else:
                self.append_system_log(t('messages.no_running_process'), "warning")
    
    def show_context_menu(self, position):
        
        menu = QMenu(self.terminal_output)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(6)}px;
                font-family: '{fonts["system"]}';
                font-size: {s(10)}pt;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: {s(8)}px {s(24)}px {s(8)}px {s(32)}px;
                border-radius: {s(4)}px;
                color: {colors["text_secondary"]};
            }}
            QMenu::item:hover {{
                background-color: {colors["list_item_hover_background"]};
                color: {colors["list_item_hover_text"]};
            }}
            QMenu::item:selected {{
                background-color: {colors["secondary"]};
                color: {colors["white"]};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {colors["background_gray"]};
                margin: {s(4)}px {s(8)}px;
            }}
        """)
        
        cursor = self.terminal_output.textCursor()
        copy_action = menu.addAction(t('context_menu.copy'))
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(cursor.hasSelection())
        copy_action.triggered.connect(self.copy_selection)
        paste_action = menu.addAction(t('context_menu.paste'))
        paste_action.setShortcut("Ctrl+V")
        clipboard = QApplication.clipboard()
        paste_action.setEnabled(bool(clipboard.text()))
        paste_action.triggered.connect(self.paste_text)
        
        menu.addSeparator()
        select_all_action = menu.addAction(t('context_menu.select_all'))
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.terminal_output.selectAll)
        
        menu.addSeparator()
        clear_action = menu.addAction(t('context_menu.clear_screen'))
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self.clear_terminal)
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            menu.addSeparator()
            interrupt_action = menu.addAction("⛔ " + t('process.stop_process'))
            interrupt_action.triggered.connect(self.interrupt_process)
        menu.exec(self.terminal_output.mapToGlobal(position))
    
    def append_system_log(self, text, log_type="info"):
        
        if self.use_real_terminal:

            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            
            if log_type == "error":
                color = colors["log_error"]
                icon = "❌"
                prefix = "ERROR"
            elif log_type == "warning":
                color = colors["log_warning"]
                icon = "⚠️"
                prefix = "WARN"
            elif log_type == "success":
                color = colors["log_success"]
                icon = "✅"
                prefix = "SUCCESS"
            elif log_type == "info":
                color = colors["log_info"]
                icon = "ℹ️"
                prefix = "INFO"
            else:
                color = colors["terminal_text"]
                icon = "📝"
                prefix = "LOG"
            log_text = f"[{timestamp}] {icon} {prefix} {text}"
            self.terminal_output.append_ansi_text(f"\033[38;2;{self._color_to_rgb(color)}m{log_text}\033[0m\n")
        else:

            cursor = self.terminal_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            if log_type == "error":
                color = colors["log_error"]
                icon = "❌"
                prefix = "ERROR"
            elif log_type == "warning":
                color = colors["log_warning"]
                icon = "⚠️"
                prefix = "WARN"
            elif log_type == "success":
                color = colors["log_success"]
                icon = "✅"
                prefix = "SUCCESS"
            elif log_type == "info":
                color = colors["log_info"]
                icon = "ℹ️"
                prefix = "INFO"
            else:
                color = colors["terminal_text"]
                icon = "📝"
                prefix = "LOG"
            current_text = self.terminal_output.toPlainText()
            user_input = ""
            if current_text.endswith(self.prompt) or (current_text.split('\n')[-1].startswith(self.prompt) if current_text else False):
                cursor.movePosition(cursor.MoveOperation.StartOfLine)
                cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
                current_line = cursor.selectedText()
                if current_line.startswith(self.prompt):
                    user_input = current_line[len(self.prompt):]
                cursor.removeSelectedText()
            log_html = f"""<span style='color: {colors["log_timestamp"]}; font-size: {s(8)}pt;'>[{timestamp}]</span> <span style='color: {color}; font-weight: normal;'>{icon} {prefix}</span> <span style='color: {colors["terminal_text"]};'>{text}</span>"""
            cursor.insertHtml(log_html + "<br/>")
            cursor.insertText(self.prompt + user_input)
            self.input_start_position = cursor.position() - len(user_input)
            
            self.terminal_output.setTextCursor(cursor)
            self.terminal_output.ensureCursorVisible()
    
    def _color_to_rgb(self, color_str):
        if color_str.startswith('#'):
            color_str = color_str[1:]
        try:
            r = int(color_str[0:2], 16)
            g = int(color_str[2:4], 16)
            b = int(color_str[4:6], 16)
            return f"{r};{g};{b}"
        except:
            return "255;255;255"
    
    def append_output(self, text):
        
        if self.use_real_terminal:

            self._append_ansi_text_optimized(text)
        else:

            cursor = self.terminal_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            current_text = self.terminal_output.toPlainText()
            if current_text.endswith(self.prompt) or current_text.split('\n')[-1].startswith(self.prompt):
                
                cursor.movePosition(cursor.MoveOperation.StartOfLine)
                cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
                user_input = cursor.selectedText()
                if user_input.startswith(self.prompt):
                    user_input = user_input[len(self.prompt):]
                cursor.removeSelectedText()
                cursor.insertText(text + "\n")
                cursor.insertText(self.prompt + user_input)
                self.input_start_position = cursor.position() - len(user_input)
            else:
                
                cursor.insertText(text + "\n")
            
            self.terminal_output.setTextCursor(cursor)
            self.terminal_output.ensureCursorVisible()
    
    def stop_process(self):
        
        if self.use_real_terminal and self.real_terminal_process:
            if self.real_terminal_process.is_running():
                self.real_terminal_process.stop_process()
                self.status_label.setText(t('process.stopped'))
                self.status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors["danger"]};
                        background: transparent;
                        border: none;
                        padding: {s(2)}px {s(6)}px;
                        font-weight: bold;
                    }}
                """)
                self.append_system_log(t('process.process_stopped'), "warning")
        else:

            if self.process and self.process.state() != QProcess.NotRunning:
                self.process.kill()
                self.status_label.setText(t('process.stopped'))
                self.status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors["danger"]};
                        background: transparent;
                        border: none;
                        padding: {s(2)}px {s(6)}px;
                        font-weight: bold;
                    }}
                """)
                self.append_system_log(t('process.process_stopped'), "warning")
    
    def process_finished(self, exit_code):
        
        if exit_code == 0:
            self.status_label.setText(t('process.finished'))
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["success"]};
                    background: transparent;
                    border: none;
                    padding: {s(2)}px {s(6)}px;
                    font-weight: bold;
                }}
            """)
            self.append_system_log(f"{t('process.process_finished')}, {t('process.exit_code')}: {exit_code}", "success")
        else:
            self.status_label.setText(t('process.error'))
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["danger"]};
                    background: transparent;
                    border: none;
                    padding: {s(2)}px {s(6)}px;
                    font-weight: bold;
                }}
            """)
            self.append_system_log(f"{t('process.process_error')}, {t('process.exit_code')}: {exit_code}", "error")
        if not self.use_real_terminal:
            self.show_prompt()
    
    def _append_ansi_text_optimized(self, text):
        
        if self.is_current_tab:

            self.terminal_output.append_ansi_text(text)
        else:

            if self.output_cache_enabled:
                self._cache_output(text)
    
    def _cache_output(self, text):
        
        import time
        current_time = time.time() * 1000
        compressed_text = self._compress_text_if_needed(text)
        self.cached_output.append({
            'text': compressed_text['data'],
            'compressed': compressed_text['compressed'],
            'original_size': len(text),
            'timestamp': current_time
        })
        if len(self.cached_output) >= self.cache_flush_threshold and self.auto_flush_enabled:

            self._auto_flush_cache()
        elif len(self.cached_output) > self.max_cache_size:

            self._force_cleanup_cache()
    
    def set_as_current_tab(self, is_current=True):
        
        was_current = self.is_current_tab
        self.is_current_tab = is_current
        
        if is_current and not was_current:

            if self.cached_output:
                cache_size = len(self.cached_output)
                if cache_size > 2000:
                    self._async_flush_cached_output()
                    if hasattr(self, 'append_system_log'):
                        self.append_system_log(
                            t('messages.loading_cache', cache_size), 
                            "info"
                        )
                else:

                    self._flush_cached_output()
        elif not is_current and was_current:

            self._optimize_cache_for_background()
    
    def _async_flush_cached_output(self):
        
        import threading
        
        def flush_worker():

            batch_count = 0
            total_items = len(self.cached_output)
            
            while self.cached_output and batch_count < 20:
                batch_count += 1
                batch_size = min(500, len(self.cached_output))
                batch_items = self.cached_output[:batch_size]
                self.cached_output = self.cached_output[batch_size:]
                try:
                    batch_text = self._decompress_batch_text(batch_items)
                    self._output_to_terminal(batch_text)
                    
                except Exception as e:
                    if hasattr(self, 'append_system_log'):
                        self.append_system_log(t('messages.async_flush_error', str(e)), "error")
                    break
                import time
                time.sleep(0.01)
            if hasattr(self, 'append_system_log'):
                remaining = len(self.cached_output)
                processed = total_items - remaining
                self.append_system_log(
                    t('messages.async_load_complete', processed, remaining), 
                    "info"
                )
        thread = threading.Thread(target=flush_worker, daemon=True)
        thread.start()
    
    def _optimize_cache_for_background(self):
        if len(self.cached_output) > self.max_cache_size * 0.6:

            keep_size = int(self.max_cache_size * 0.4)
            removed_count = len(self.cached_output) - keep_size
            self.cached_output = self.cached_output[-keep_size:]
            
            if hasattr(self, 'append_system_log'):
                self.append_system_log(
                    f"后台优化: 清理{removed_count}条缓存，保留{keep_size}条", 
                    "info"
                )
    
    def _flush_cached_output(self):
        
        import time
        current_time = time.time() * 1000
        if current_time - self.last_refresh_time < self.refresh_interval:
            return
        
        if self.cached_output:

            self._process_cache_in_batches()
            self.last_refresh_time = current_time
    
    def _process_cache_in_batches(self):
        
        total_items = len(self.cached_output)
        
        if total_items <= self.cache_batch_size:

            batch_text = self._decompress_batch_text(self.cached_output)
            self._output_to_terminal(batch_text)
            self.cached_output.clear()
        else:

            self._process_large_cache(total_items)
    
    def _process_large_cache(self, total_items):
        
        processed = 0
        batch_count = 0
        
        while processed < total_items and batch_count < 10:
            batch_count += 1
            end_index = min(processed + self.cache_batch_size, total_items)
            batch_items = self.cached_output[processed:end_index]
            batch_text = self._decompress_batch_text(batch_items)
            self._output_to_terminal(batch_text)
            
            processed = end_index
            if processed < total_items:
                import time
                time.sleep(0.001)
        self.cached_output = self.cached_output[processed:]
        if hasattr(self, 'append_system_log'):
            self.append_system_log(
                f"分批处理缓存: {batch_count}批次, 共{processed}条数据", 
                "info"
            )
    
    def _append_traditional_output(self, text):
        
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        current_text = self.terminal_output.toPlainText()
        if current_text.endswith(self.prompt) or current_text.split('\n')[-1].startswith(self.prompt):
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
            user_input = cursor.selectedText()
            if user_input.startswith(self.prompt):
                user_input = user_input[len(self.prompt):]
            cursor.removeSelectedText()
            
            cursor.insertText(text + "\n")
            cursor.insertText(self.prompt + user_input)
            self.input_start_position = cursor.position() - len(user_input)
        else:
            cursor.insertText(text + "\n")
        
        self.terminal_output.setTextCursor(cursor)
        self.terminal_output.ensureCursorVisible()
    
    def _output_to_terminal(self, text):
        
        if self.use_real_terminal:
            self.terminal_output.append_ansi_text(text)
        else:
            self._append_traditional_output(text)
    
    def _auto_flush_cache(self):
        
        if not self.is_current_tab and self.cached_output:

            flush_count = min(self.cache_batch_size, len(self.cached_output))
            self.cached_output = self.cached_output[flush_count:]
            if hasattr(self, 'append_system_log'):
                self.append_system_log(
                    f"自动刷新缓存: {flush_count}条数据，剩余{len(self.cached_output)}条", 
                    "info"
                )
    
    def _force_cleanup_cache(self):
        if self.cached_output:

            self._emergency_output_cache_to_terminal()
        keep_size = int(self.max_cache_size * 0.8)
        removed_count = len(self.cached_output) - keep_size
        
        self.cached_output = self.cached_output[-keep_size:]
        if hasattr(self, 'append_system_log'):
            self.append_system_log(
                f"强制清理缓存: 删除{removed_count}条旧数据，保留{keep_size}条", 
                "warning"
            )
    
    def get_cache_status(self):
        
        total_text_size = 0
        compressed_items = 0
        original_size = 0
        
        for item in self.cached_output:
            if item.get('compressed', False):
                compressed_items += 1
                total_text_size += len(item['text'])
                original_size += item.get('original_size', 0)
            else:
                if isinstance(item['text'], str):
                    size = len(item['text'])
                else:
                    size = len(item['text'])
                total_text_size += size
                original_size += size
        
        compression_ratio = (1 - total_text_size / original_size) if original_size > 0 else 0
        
        return {
            'is_current_tab': self.is_current_tab,
            'cached_items': len(self.cached_output),
            'cache_enabled': self.output_cache_enabled,
            'cache_size_limit': self.max_cache_size,
            'cache_batch_size': self.cache_batch_size,
            'cache_flush_threshold': self.cache_flush_threshold,
            'auto_flush_enabled': self.auto_flush_enabled,
            'total_text_size': total_text_size,
            'original_size': original_size,
            'compressed_items': compressed_items,
            'compression_ratio': round(compression_ratio * 100, 2),
            'cache_usage_percent': round((len(self.cached_output) / self.max_cache_size) * 100, 2) if self.max_cache_size > 0 else 0,
            'needs_flush': len(self.cached_output) >= self.cache_flush_threshold,
            'compression_enabled': self.cache_compression_enabled
        }
    
    def set_cache_enabled(self, enabled):
        
        self.output_cache_enabled = enabled
        if not enabled and self.cached_output:

            self._flush_cached_output()
    
    def clear_cache(self):
        
        cleared_count = len(self.cached_output)
        self.cached_output.clear()
        
        if hasattr(self, 'append_system_log') and cleared_count > 0:
            self.append_system_log(
                f"手动清空缓存: {cleared_count}条数据", 
                "info"
            )
    
    def optimize_cache_settings(self):
        
        cache_status = self.get_cache_status()
        if cache_status['cache_usage_percent'] > 90:

            self.cache_batch_size = max(500, self.cache_batch_size - 100)
            self.cache_flush_threshold = max(3000, self.cache_flush_threshold - 200)
        elif cache_status['cache_usage_percent'] < 30:

            self.cache_batch_size = min(1500, self.cache_batch_size + 100)
            self.cache_flush_threshold = min(4500, self.cache_flush_threshold + 200)
        
        if hasattr(self, 'append_system_log'):
            self.append_system_log(
                f"缓存优化: 批处理大小={self.cache_batch_size}, 刷新阈值={self.cache_flush_threshold}", 
                "info"
            )
    
    def get_cache_memory_usage(self):
        
        total_chars = sum(len(item['text']) for item in self.cached_output)

        estimated_bytes = total_chars * 4 + len(self.cached_output) * 200
        return {
            'total_characters': total_chars,
            'estimated_bytes': estimated_bytes,
            'estimated_mb': round(estimated_bytes / (1024 * 1024), 2)
        }
    
    def _compress_text_if_needed(self, text):
        
        if not self.cache_compression_enabled or len(text) < self.compression_threshold:
            return {'data': text, 'compressed': False}
        
        try:
            import zlib
            compressed = zlib.compress(text.encode('utf-8'))

            if len(compressed) < len(text.encode('utf-8')):
                return {'data': compressed, 'compressed': True}
            else:
                return {'data': text, 'compressed': False}
        except Exception:

            return {'data': text, 'compressed': False}
    
    def _decompress_text(self, data, compressed=False):
        
        if not compressed:
            return data
        
        try:
            import zlib
            return zlib.decompress(data).decode('utf-8')
        except Exception:

            return ""
    
    def _decompress_batch_text(self, batch_items):
        
        result = []
        for item in batch_items:
            text = self._decompress_text(
                item['text'], 
                item.get('compressed', False)
            )
            result.append(text)
        return ''.join(result)
    
    def _emergency_output_cache_to_terminal(self):
        
        if not self.cached_output:
            return
        try:

            batch_text = self._decompress_batch_text(self.cached_output)
            self._output_to_terminal(batch_text)
            if hasattr(self, 'append_system_log'):
                self.append_system_log(
                    f"[缓存满] 紧急输出{len(self.cached_output)}条缓存到终端，避免消息遗漏", 
                    "warning"
                )
            self.cached_output.clear()
            
        except Exception as e:

            if hasattr(self, 'append_system_log'):
                self.append_system_log(
                    f"[错误] 紧急输出缓存失败: {str(e)}", 
                    "error"
                )

            self.cached_output = self.cached_output[-int(self.max_cache_size * 0.5):]

    def perform_terminal_search(self, keyword: str, match_mode: int):
        
        if not self.use_real_terminal or not self.search_panel:
            return
        self.terminal_output.clear_search_highlights()
        results = self.terminal_output.search_text(keyword, match_mode)
        self.search_panel.update_search_results(results)

    def toggle_search_panel(self):
        
        if not self.use_real_terminal or not self.search_panel:
            return
        
        if self.search_panel.isVisible():
            self.search_panel.hide()
            self.search_toggle_btn.setChecked(False)
            self.search_toggle_btn.setToolTip(t('messages.show_search_panel'))
        else:
            self.search_panel.show()
            self.search_toggle_btn.setChecked(True)
            self.search_toggle_btn.setToolTip(t('messages.hide_search_panel'))

