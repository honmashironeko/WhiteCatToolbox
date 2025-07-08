import re
import os
import sys
import threading
import time
from typing import Dict, List, Tuple, Optional
from PySide6.QtWidgets import (QTextEdit, QApplication, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLineEdit, QPushButton, QComboBox, 
                               QListWidget, QListWidgetItem, QSplitter, QLabel)
from PySide6.QtCore import Qt, QTimer, QMutex, QMutexLocker, Signal
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QTextDocument, QBrush
from .theme import colors, fonts
from .i18n import t
from .utils import s
class ANSIParser:
    def __init__(self):
        self.reset_attributes()
        self.cursor_row = 0
        self.cursor_col = 0
        
    def reset_attributes(self):
        
        self.foreground_color = None
        self.background_color = None
        self.bold = False
        self.italic = False
        self.underline = False
        self.strikethrough = False
        self.inverse = False
        
    def parse_ansi_codes(self, text: str) -> List[Tuple[str, Dict]]:
        
        result = []
        ansi_pattern = r'\x1b\[[0-9;]*[mHJKABCDEFGnsuhl]'
        
        last_end = 0
        for match in re.finditer(ansi_pattern, text):

            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    result.append((plain_text, self._get_current_format()))
            ansi_code = match.group()
            self._process_ansi_code(ansi_code)
            
            last_end = match.end()
        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text:
                result.append((remaining_text, self._get_current_format()))
        
        return result
    
    def _process_ansi_code(self, ansi_code: str):
        
        if ansi_code.endswith('m'):

            params = ansi_code[2:-1]
            if not params:
                params = '0'
            
            for param in params.split(';'):
                if not param:
                    continue
                try:
                    code = int(param)
                    self._process_sgr_code(code)
                except ValueError:
                    continue
        elif ansi_code.endswith('H'):

            params = ansi_code[2:-1]
            if params:
                parts = params.split(';')
                if len(parts) >= 2:
                    try:
                        self.cursor_row = int(parts[0]) - 1
                        self.cursor_col = int(parts[1]) - 1
                    except ValueError:
                        pass
        elif ansi_code.endswith('J'):
            pass
        elif ansi_code.endswith('K'):
            pass
    
    def _process_sgr_code(self, code: int):
        
        if code == 0:

            self.reset_attributes()
        elif code == 1:

            self.bold = True
        elif code == 3:

            self.italic = True
        elif code == 4:

            self.underline = True
        elif code == 7:

            self.inverse = True
        elif code == 9:

            self.strikethrough = True
        elif code == 22:

            self.bold = False
        elif code == 23:

            self.italic = False
        elif code == 24:

            self.underline = False
        elif code == 27:

            self.inverse = False
        elif code == 29:

            self.strikethrough = False
        elif 30 <= code <= 37:

            self.foreground_color = self._get_color_from_code(code - 30)
        elif 40 <= code <= 47:

            self.background_color = self._get_color_from_code(code - 40)
        elif code == 39:

            self.foreground_color = None
        elif code == 49:

            self.background_color = None
        elif 90 <= code <= 97:

            self.foreground_color = self._get_bright_color_from_code(code - 90)
        elif 100 <= code <= 107:

            self.background_color = self._get_bright_color_from_code(code - 100)
    
    def _get_color_from_code(self, code: int) -> QColor:
        
        color_map = {
            0: QColor(0, 0, 0),
            1: QColor(128, 0, 0),
            2: QColor(0, 128, 0),
            3: QColor(128, 128, 0),
            4: QColor(0, 0, 128),
            5: QColor(128, 0, 128),
            6: QColor(0, 128, 128),
            7: QColor(192, 192, 192),
        }
        return color_map.get(code, QColor(192, 192, 192))
    
    def _get_bright_color_from_code(self, code: int) -> QColor:
        
        color_map = {
            0: QColor(128, 128, 128),
            1: QColor(255, 0, 0),
            2: QColor(0, 255, 0),
            3: QColor(255, 255, 0),
            4: QColor(0, 0, 255),
            5: QColor(255, 0, 255),
            6: QColor(0, 255, 255),
            7: QColor(255, 255, 255),
        }
        return color_map.get(code, QColor(255, 255, 255))
    
    def _get_current_format(self) -> Dict:
        
        format_dict = {
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'bold': self.bold,
            'italic': self.italic,
            'underline': self.underline,
            'strikethrough': self.strikethrough,
            'inverse': self.inverse,
        }
        return format_dict
class SearchResult:
    
    def __init__(self, line_number: int, content: str, start_pos: int, end_pos: int):
        self.line_number = line_number
        self.content = content
        self.start_pos = start_pos
        self.end_pos = end_pos
class TerminalSearchPanel(QWidget):
    search_requested = Signal(str, int)
    jump_to_line = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_results = []
        self.current_highlight_format = None
        self.setup_ui()
    
    def setup_ui(self):
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(6), s(6), s(6), s(6))
        layout.setSpacing(s(4))
        search_layout = QHBoxLayout()
        search_layout.setSpacing(s(4))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("process.search_placeholder"))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {s(3)}px;
                padding: {s(4)}px {s(8)}px;
                font-size: {s(8)}pt;
                color: {colors["text_secondary"]};
                height: {s(24)}px;
            }}
            QLineEdit:focus {{
                border-color: {colors["secondary"]};
            }}
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        self.match_mode = QComboBox()
        self.match_mode.addItems([t("search_modes.fuzzy"), t("search_modes.exact"), t("search_modes.regex")])
        self.match_mode.setCurrentIndex(0)
        self.match_mode.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {s(3)}px;
                padding: {s(4)}px {s(6)}px;
                font-size: {s(8)}pt;
                color: {colors["text_secondary"]};
                min-width: {s(35)}px;
                max-width: {s(50)}px;
                height: {s(24)}px;
                font-weight: 500;
                text-align: center;
            }}
            QComboBox::drop-down {{
                width: 0px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }}
            QComboBox:hover {{
                border-color: {colors["secondary"]};
                background-color: {colors["background_very_light"]};
            }}
            QComboBox:focus {{
                border-color: {colors["secondary"]};
                outline: none;
            }}
            QComboBox:pressed {{
                background-color: {colors["background_light"]};
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors["white"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {s(6)}px;
                selection-background-color: {colors["secondary"]};
                selection-color: {colors["white"]};
                padding: {s(6)}px;
                outline: none;
                font-size: {s(8)}pt;
                show-decoration-selected: 1;
                min-width: {s(60)}px;
                alternate-background-color: transparent;
                gridline-color: transparent;
            }}
            QComboBox QAbstractItemView QScrollBar {{
                border: none;
                background: transparent;
            }}
            QComboBox QFrame {{
                border: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: {s(10)}px {s(12)}px;
                border: none;
                border-radius: {s(4)}px;
                font-weight: 500;
                min-height: {s(16)}px;
                margin: {s(2)}px;
                background: transparent;
                color: {colors["text"]};
                text-align: center;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 {colors["secondary"]}, stop: 1 {colors["secondary_hover"]});
                color: {colors["white"]};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 {colors["primary"]}, stop: 1 {colors["primary_hover"]});
                color: {colors["white"]};
                font-weight: 600;
            }}
        """)
        search_layout.addWidget(self.match_mode)
        self.search_btn = QPushButton(t("buttons.search"))
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["secondary"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {s(3)}px;
                padding: {s(4)}px {s(12)}px;
                color: white;
                font-weight: 500;
                font-size: {s(8)}pt;
                height: {s(24)}px;
            }}
            QPushButton:hover {{
                background-color: {colors["secondary_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["secondary_pressed"]};
            }}
        """)
        self.search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_btn)
        self.clear_btn = QPushButton(t("buttons.clear"))
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["text_disabled"]};
                border: 1px solid {colors["text_disabled"]};
                border-radius: {s(3)}px;
                padding: {s(4)}px {s(12)}px;
                color: white;
                font-weight: 500;
                font-size: {s(8)}pt;
                height: {s(24)}px;
            }}
            QPushButton:hover {{
                background-color: {colors["text_secondary"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["tooltip_text"]};
            }}
        """)
        self.clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.clear_btn)
        
        layout.addLayout(search_layout)
        self.result_label = QLabel()
        self.result_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["text_secondary"]};
                font-size: {s(7)}pt;
                padding: {s(2)}px {s(4)}px;
                background: transparent;
            }}
        """)
        layout.addWidget(self.result_label)
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {s(3)}px;
                padding: {s(2)}px;
                font-family: '{fonts["monospace"]}', 'Consolas', 'Monaco', monospace;
                font-size: {s(7)}pt;
                color: {colors["text_secondary"]};
            }}
            QListWidget::item {{
                border: none;
                padding: {s(2)}px {s(4)}px;
                border-radius: {s(2)}px;
                margin: 1px;
            }}
            QListWidget::item:hover {{
                background-color: {colors["list_item_hover_background"]};
            }}
            QListWidget::item:selected {{
                background-color: {colors["secondary"]};
                color: white;
            }}
        """)
        self.results_list.itemClicked.connect(self.on_result_clicked)
        layout.addWidget(self.results_list)
        
        self.setLayout(layout)
    
    def perform_search(self):
        
        keyword = self.search_input.text().strip()
        if not keyword:
            return
        
        match_mode = self.match_mode.currentIndex()
        self.search_requested.emit(keyword, match_mode)
    
    def clear_search(self):
        
        self.search_input.clear()
        self.results_list.clear()
        self.search_results.clear()
        if hasattr(self.parent(), 'terminal_output'):
            self.parent().terminal_output.clear_search_highlights()
    
    def update_search_results(self, results: List[SearchResult]):
        
        self.search_results = results
        self.results_list.clear()
        
        if not results:
            self.result_label.setText(t("messages.search_no_matches"))
            return
        
        self.result_label.setText(t("messages.search_found_matches", len(results)))
        
        for i, result in enumerate(results):

            display_content = result.content.strip()
            if len(display_content) > 80:

                keyword_pos = result.start_pos
                start_display = max(0, keyword_pos - 20)
                end_display = min(len(display_content), keyword_pos + 60)
                display_content = display_content[start_display:end_display]
                if start_display > 0:
                    display_content = "..." + display_content
                if end_display < len(result.content.strip()):
                    display_content = display_content + "..."
            
            item_text = t('messages.search_line_format', result.line_number, display_content)
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)
            item.setToolTip(t('messages.search_line_format', result.line_number, result.content))
            
            self.results_list.addItem(item)
    
    def on_result_clicked(self, item):
        
        result_index = item.data(Qt.UserRole)
        if result_index is not None and result_index < len(self.search_results):
            result = self.search_results[result_index]
            self.jump_to_line.emit(result.line_number)
class RealTerminal(QTextEdit):
    command_executed = Signal(str)
    
    def __init__(self, parent_tab):
        super().__init__()
        self.parent_tab = parent_tab
        self.ansi_parser = ANSIParser()
        self.buffer_mutex = QMutex()
        self.output_buffer = []
        self.prompt = "$ "
        self.input_start_position = 0
        self.history = []
        self.history_index = 0
        self.search_highlights = []
        self.current_search_keyword = ""
        self.current_search_mode = 0
        self.last_update_time = 0
        self.update_interval = 100
        self.buffer_size_threshold = 1000
        self.is_progress_mode = False

        self.progress_pattern = re.compile(
            r'\r.*?\d+%|'
            r'\[.*?\].*?\d+%|'
            r'█+.*?\d+%|'
            r'#+.*?\d+%|'
            r'=+>.*?\d+%|'
            r'\.+.*?\d+%|'
            r'Progress:.*?\d+%|'
            r'进度:.*?\d+%'
        )
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._process_buffer)
        self.update_timer.start(30)
        self.setFont(QFont(fonts["monospace"], 9))
        self.setAcceptRichText(True)
        self.setReadOnly(False)
        self._initialize_terminal()
    
    def _initialize_terminal(self):
        
        self.clear()
        self.append_colored_text(t("terminal.welcome"), colors["log_success"])
        self.append_colored_text(t("terminal.ansi_support"), colors["log_info"])
        self.append_colored_text(t("terminal.shortcuts"), colors["log_info"])
        self.append_colored_text(t("terminal.process_control"), colors["log_warning"])
        self.append_colored_text(t("terminal.new_features"), colors["log_success"])
        self.show_prompt()
    
    def append_colored_text(self, text: str, color: str = None):
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if color:
            format = QTextCharFormat()
            format.setForeground(QColor(color))
            cursor.setCharFormat(format)
        
        cursor.insertText(text + "\n")
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    
    def show_prompt(self):
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(self.prompt)
        self.input_start_position = cursor.position()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    
    def append_ansi_text(self, text: str):
        if hasattr(self.parent_tab, 'is_current_tab') and not self.parent_tab.is_current_tab:

            if hasattr(self.parent_tab, '_cache_output'):
                self.parent_tab._cache_output(text)
                return
        with QMutexLocker(self.buffer_mutex):
            self.output_buffer.append(text)
    
    def _process_buffer(self):
        
        if not self.output_buffer:
            return
        
        current_time = time.time() * 1000
        time_since_last_update = current_time - self.last_update_time
        with QMutexLocker(self.buffer_mutex):
            buffer_content = ''.join(self.output_buffer)
            buffer_size = len(buffer_content)
            has_progress = bool(self.progress_pattern.search(buffer_content))
            if has_progress:
                self.is_progress_mode = True

                min_interval = 200
            else:

                if self.is_progress_mode and '\n' in buffer_content:
                    self.is_progress_mode = False
                min_interval = 50 if not self.is_progress_mode else 200
        should_update = False
        if time_since_last_update >= min_interval:
            should_update = True
        elif buffer_size > self.buffer_size_threshold:
            should_update = True
        elif not self.is_progress_mode and '\n' in buffer_content:
            should_update = True
        
        if should_update:
            with QMutexLocker(self.buffer_mutex):
                buffer_to_process = ''.join(self.output_buffer)
                self.output_buffer.clear()
            
            if buffer_to_process:
                self._insert_ansi_text(buffer_to_process)
                self.last_update_time = current_time
    
    def _insert_ansi_text(self, text: str):
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        if self.is_progress_mode:

            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        current_text = self.toPlainText()
        user_input = ""
        if current_text.endswith(self.prompt) or current_text.split('\n')[-1].startswith(self.prompt):
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            current_line = cursor.selectedText()
            if current_line.startswith(self.prompt):
                user_input = current_line[len(self.prompt):]
            cursor.removeSelectedText()
        cursor.beginEditBlock()
        parsed_content = self.ansi_parser.parse_ansi_codes(text)
        for text_part, format_info in parsed_content:
            if text_part:
                char_format = self._create_char_format(format_info)
                cursor.setCharFormat(char_format)
                cursor.insertText(text_part)
        
        cursor.endEditBlock()
        cursor.insertText(self.prompt + user_input)
        self.input_start_position = cursor.position() - len(user_input)
        
        self.setTextCursor(cursor)
        if self.is_progress_mode:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.ensureCursorVisible()
    
    def _create_char_format(self, format_info: Dict) -> QTextCharFormat:
        
        char_format = QTextCharFormat()
        if format_info.get('foreground_color'):
            char_format.setForeground(format_info['foreground_color'])
        else:
            char_format.setForeground(QColor(colors["terminal_text"]))
        if format_info.get('background_color'):
            char_format.setBackground(format_info['background_color'])
        if format_info.get('bold'):
            char_format.setFontWeight(QFont.Bold)
        if format_info.get('italic'):
            char_format.setFontItalic(True)
        if format_info.get('underline'):
            char_format.setFontUnderline(True)
        if format_info.get('strikethrough'):
            char_format.setFontStrikeOut(True)
        if format_info.get('inverse'):

            fg = char_format.foreground()
            bg = char_format.background()
            char_format.setForeground(bg.color() if bg.style() != Qt.BrushStyle.NoBrush else QColor(colors["terminal_background_start"]))
            char_format.setBackground(fg.color() if fg.style() != Qt.BrushStyle.NoBrush else QColor(colors["terminal_text"]))
        
        return char_format
    
    def keyPressEvent(self, event):
        
        cursor = self.textCursor()
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                if cursor.hasSelection():
                    self.copy()
                return
            elif event.key() == Qt.Key_V:
                self.paste()
                return
            elif event.key() == Qt.Key_A:
                self.selectAll()
                return
            elif event.key() == Qt.Key_L:
                self.clear_terminal()
                return
        if cursor.position() < self.input_start_position:
            if event.key() not in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown]:
                cursor.setPosition(self.input_start_position)
                self.setTextCursor(cursor)
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.execute_command()
            return
        if event.key() == Qt.Key_Backspace:
            if cursor.position() <= self.input_start_position and not cursor.hasSelection():
                return
        if event.key() == Qt.Key_Up:
            self.show_previous_command()
            return
        elif event.key() == Qt.Key_Down:
            self.show_next_command()
            return
        
        super().keyPressEvent(event)
    
    def execute_command(self):
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        command_text = self.toPlainText()
        last_prompt_pos = command_text.rfind(self.prompt)
        if last_prompt_pos != -1:
            user_input = command_text[last_prompt_pos + len(self.prompt):].strip()
        else:
            user_input = ""
        if user_input and (not self.history or self.history[-1] != user_input):
            self.history.append(user_input)
        self.history_index = len(self.history)
        cursor.insertText("\n")
        if hasattr(self.parent_tab, 'send_command'):
            self.parent_tab.send_command(user_input)
        self.command_executed.emit(user_input)
        self.show_prompt()
    
    def show_previous_command(self):
        
        if self.history and self.history_index > 0:
            self.history_index -= 1
            self.replace_current_input(self.history[self.history_index])
    
    def show_next_command(self):
        
        if self.history and self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.replace_current_input(self.history[self.history_index])
        elif self.history_index >= len(self.history) - 1:
            self.history_index = len(self.history)
            self.replace_current_input("")
    
    def replace_current_input(self, text: str):
        
        cursor = self.textCursor()
        cursor.setPosition(self.input_start_position)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(text)
        self.setTextCursor(cursor)
    
    def clear_terminal(self):
        
        self.clear()
        self.ansi_parser.reset_attributes()
        self.append_colored_text(t("messages.terminal_cleared"), colors["log_info"])
        self.show_prompt()
    
    def set_update_interval(self, interval: int):
        
        self.update_interval = max(50, interval)
    
    def set_progress_mode(self, enabled: bool):
        
        self.is_progress_mode = enabled
    
    def closeEvent(self, event):
        
        if self.update_timer.isActive():
            self.update_timer.stop()
        super().closeEvent(event)
    
    def search_text(self, keyword: str, match_mode: int) -> List[SearchResult]:
        """在终端文本中搜索关键词
        
        Args:
            keyword: 搜索关键词
            match_mode: 匹配模式 (0=大小写模糊, 1=大小写严格, 2=正则匹配)
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        if not keyword:
            return []
        
        self.current_search_keyword = keyword
        self.current_search_mode = match_mode
        self.clear_search_highlights()
        document = self.document()
        results = []
        
        try:
            if match_mode == 0:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            elif match_mode == 1:
                pattern = re.compile(re.escape(keyword))
            elif match_mode == 2:
                pattern = re.compile(keyword)
            else:
                return results
            block = document.firstBlock()
            line_number = 1
            
            while block.isValid():
                line_content = block.text()
                if line_content:
                    matches = pattern.finditer(line_content)
                    for match in matches:
                        result = SearchResult(
                            line_number=line_number,
                            content=line_content,
                            start_pos=match.start(),
                            end_pos=match.end()
                        )
                        results.append(result)
                block = block.next()
                line_number += 1
            if results:
                self._add_search_highlights(results)
                    
        except re.error:

            return []
            
        return results
    
    def _add_search_highlights(self, results: List[SearchResult]):
        
        document = self.document()
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("#FFFF00"))
        highlight_format.setForeground(QColor("#000000"))
        for result in results:
            try:
                line_number = result.line_number
                block = document.findBlockByLineNumber(line_number - 1)
                if not block.isValid():
                    continue
                cursor = QTextCursor(block)
                block_start = cursor.position()
                start_pos = block_start + result.start_pos
                end_pos = block_start + result.end_pos
                if start_pos >= 0 and end_pos <= document.characterCount() and start_pos < end_pos:
                    cursor.setPosition(start_pos)
                    cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
                    cursor.mergeCharFormat(highlight_format)
                    self.search_highlights.append({
                        'line': result.line_number,
                        'start': result.start_pos,
                        'end': result.end_pos,
                        'abs_start': start_pos,
                        'abs_end': end_pos
                    })
                    
            except Exception as e:

                continue
    
    def clear_search_highlights(self):
        
        if not self.search_highlights:
            return
        
        document = self.document()
        cursor = QTextCursor(document)
        highlights_sorted = sorted(self.search_highlights, key=lambda x: x['abs_start'], reverse=True)
        for highlight in highlights_sorted:
            try:

                start_pos = highlight['abs_start']
                end_pos = highlight['abs_end']
                if start_pos >= 0 and end_pos <= document.characterCount() and start_pos < end_pos:
                    cursor.setPosition(start_pos)
                    cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
                    selected_text = cursor.selectedText()
                    cursor.removeSelectedText()
                    default_format = QTextCharFormat()
                    default_format.setForeground(QColor(colors["terminal_text"]))
                    cursor.setCharFormat(default_format)
                    cursor.insertText(selected_text)
                    
            except Exception:

                continue
        
        self.search_highlights.clear()
    
    def jump_to_line(self, line_number: int):
        
        if line_number < 1:
            return
        document = self.document()
        if line_number > document.blockCount():
            return
        block = document.findBlockByLineNumber(line_number - 1)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self._highlight_current_line(cursor)
    
    def _highlight_current_line(self, cursor: QTextCursor):
        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()
        temp_format = QTextCharFormat()
        temp_format.setBackground(QColor(colors["secondary"]))
        temp_format.setForeground(QColor("white"))
        cursor.setCharFormat(temp_format)
        QTimer.singleShot(1000, lambda: self._restore_line_format(start_pos, end_pos))
    
    def _restore_line_format(self, start_pos: int, end_pos: int):
        
        try:
            document = self.document()
            cursor = QTextCursor(document)
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.KeepAnchor)
            selected_text = cursor.selectedText()
            cursor.removeSelectedText()
            default_format = QTextCharFormat()
            default_format.setForeground(QColor(colors["terminal_text"]))
            cursor.setCharFormat(default_format)
            cursor.insertText(selected_text)
            
        except Exception:

            pass