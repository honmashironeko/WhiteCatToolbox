import platform
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QMenu, QSizePolicy, QApplication,
    QComboBox
)
from PySide6.QtCore import Qt, QProcess, QTimer
from PySide6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QTextDocument
from .theme import colors, fonts, params
from .utils import s
from .i18n import t, get_current_language
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
            elif event.key() == Qt.Key.Key_F:
                self.parent_tab.toggle_search()
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
    def __init__(self, process, process_name, parent_tabs):
        super().__init__()
        self.process = process
        self.process_name = process_name
        self.parent_tabs = parent_tabs
        self.prompt = "$ "  
        self.input_start_position = 0  
        self.history = []  
        self.history_index = 0  
        self.search_widget = None
        self.search_input = None
        self.search_mode = None
        self.current_match_display = None
        self.current_search_results = []
        self.current_highlight_index = -1
        self.search_highlights = []
        self.search_visible = False
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
        control_layout.setSpacing(s(10))
        self.status_label = QLabel(t("running"))
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
        clear_btn = QPushButton(t("clear_output"))
        clear_btn.setMinimumWidth(s(80))
        clear_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        clear_btn.setMinimumHeight(s(30))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["text_disabled"]};
                border: 1px solid {colors["text_disabled"]};
                border-radius: {s(4)}px;
                padding: 8px;
                color: white;
                font-weight: 500;
                font-size: {s(9)}pt;
                margin: 0px;
                text-align: center;
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
        search_toggle_btn = QPushButton("🔍")
        search_toggle_btn.setMinimumWidth(s(30))
        search_toggle_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        search_toggle_btn.setMinimumHeight(s(20))
        search_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["secondary"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {s(4)}px;
                padding: 8px;
                color: white;
                font-weight: 500;
                font-size: {s(9)}pt;
                margin: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {colors["secondary_hover"]};
                border-color: {colors["secondary_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["secondary_pressed"]};
            }}
        """)
        search_toggle_btn.clicked.connect(self.toggle_search)
        control_layout.addWidget(search_toggle_btn)
        stop_btn = QPushButton(t("stop_process"))
        stop_btn.setMinimumWidth(s(80))
        stop_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        stop_btn.setMinimumHeight(s(20))
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["danger"]};
                border: 1px solid {colors["danger"]};
                border-radius: {s(4)}px;
                padding: 8px;
                color: white;
                font-weight: 500;
                font-size: {s(9)}pt;
                margin: 0px;
                text-align: center;
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
        self.setup_search_ui()
        layout.addWidget(self.search_widget)
        layout.addWidget(self.current_match_display)
        self.terminal_output = TerminalTextEdit(self)
        self.terminal_output.setFont(QFont(fonts["monospace"], s(9)))
        self.terminal_output.setMinimumHeight(s(600))
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
        self.terminal_output.setReadOnly(False)
        self.terminal_output.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.terminal_output.customContextMenuRequested.connect(self.show_context_menu)
        self.terminal_output.append("💡 " + t("terminal_welcome"))
        self.terminal_output.append("💡 " + t("keyboard_shortcuts"))
        self.terminal_output.append("⚡ " + t("process_control_info"))
        self.terminal_output.append("📝 " + t("system_log_integrated"))
        self.terminal_output.append("🔍 " + t("search_modes_support"))
        self.append_system_log(t("terminal_initialized"), "success")
        self.show_prompt()
        layout.addWidget(self.terminal_output)
        self.search_widget.hide()
        self.current_match_display.hide()
        self.setLayout(layout)
    def setup_search_ui(self):
        self.search_widget = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(s(12), s(8), s(12), s(8))
        search_layout.setSpacing(s(10))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t("search_content_placeholder"))
        self.search_input.setMinimumHeight(s(24))
        self.search_input.setMinimumWidth(s(180))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {s(6)}px;
                padding: {s(8)}px {s(12)}px;
                font-size: {s(9)}pt;
                color: {colors["text"]};
            }}
            QLineEdit:focus {{
                border-color: {colors["secondary"]};
                outline: none;
            }}
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.returnPressed.connect(self.search_next)
        search_layout.addWidget(self.search_input, 1)
        self.search_mode = QComboBox()
        self.search_mode.addItems([t("fuzzy_match"), t("exact_match"), t("regex_match")])
        self.search_mode.setMinimumWidth(s(100))
        self.search_mode.setMinimumHeight(s(24))
        self.search_mode.setStyleSheet(f"""
            QComboBox {{
                background: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(6)}px {s(12)}px;
                font-size: {s(9)}pt;
                color: {colors["text"]};
                font-weight: 500;
                min-height: {s(20)}px;
            }}
            QComboBox:hover {{
                border-color: {colors["secondary"]};
                background: {colors["background_light"]};
            }}
            QComboBox:focus {{
                border-color: {colors["secondary"]};
                outline: none;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {s(20)}px;
                border: none;
                border-left: 1px solid {colors["background_gray"]};
                border-radius: 0 {params["border_radius_small"]} {params["border_radius_small"]} 0;
            }}
            QComboBox::drop-down:hover {{
                background: {colors["secondary"]};
                border-left-color: {colors["secondary"]};
            }}
            QComboBox QAbstractItemView {{
                background: {colors["white"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {params["border_radius_small"]};
                outline: none;
                padding: {s(2)}px;
            }}
            QComboBox QAbstractItemView::item {{
                background: transparent;
                border: none;
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(10)}px;
                margin: {s(1)}px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {colors["list_item_hover_background"]};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: {colors["secondary"]};
                color: {colors["text_on_primary"]};
            }}
        """)
        self.search_mode.currentTextChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_mode)
        search_btn = QPushButton(t("search"))
        search_btn.setMinimumWidth(s(60))
        search_btn.setMinimumHeight(s(24))
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["secondary"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {s(6)}px;
                padding: 8px;
                color: white;
                font-weight: 500;
                font-size: {s(9)}pt;
                margin: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {colors["secondary_hover"]};
                border-color: {colors["secondary_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["secondary_pressed"]};
            }}
        """)
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        clear_search_btn = QPushButton(t("clear_search"))
        clear_search_btn.setMinimumWidth(s(60))
        clear_search_btn.setMinimumHeight(s(24))
        clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["text_disabled"]};
                border: 1px solid {colors["text_disabled"]};
                border-radius: {s(6)}px;
                padding: 8px;
                color: white;
                font-weight: 500;
                font-size: {s(9)}pt;
                margin: 0px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {colors["text_secondary"]};
                border-color: {colors["text_secondary"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["tooltip_text"]};
            }}
        """)
        clear_search_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(clear_search_btn)
        self.match_count_label = QLabel("0/0")
        self.match_count_label.setMinimumWidth(s(60))
        self.match_count_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["text_disabled"]};
                font-size: {s(9)}pt;
                padding: {s(4)}px {s(8)}px;
                border: 1px solid {colors["background_gray"]};
                border-radius: {s(6)}px;
                background-color: {colors["background_light"]};
            }}
        """)
        search_layout.addWidget(self.match_count_label)
        self.search_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
            }}
        """)
        self.search_widget.setLayout(search_layout)
        self.current_match_display = QTextEdit()
        self.current_match_display.setReadOnly(True)
        font_metrics = QFont(fonts["monospace"], s(8))
        line_height = int(s(8) * 1.4 * 1.5)
        display_height = line_height * 15 + s(16)
        self.current_match_display.setFixedHeight(display_height)
        self.current_match_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.current_match_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {colors["background_very_light"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {s(6)}px;
                padding: {s(8)}px;
                font-family: '{fonts["monospace"]}', 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: {s(8)}pt;
                color: {colors["text_secondary"]};
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border-color: {colors["secondary"]};
                outline: none;
            }}
            QScrollBar:vertical {{
                background-color: {colors["background_light"]};
                width: {s(12)}px;
                border-radius: {s(6)}px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors["text_disabled"]};
                border-radius: {s(6)}px;
                min-height: {s(20)}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors["secondary"]};
            }}
        """)
        self.current_match_display.mousePressEvent = self.on_match_display_click
        self.current_match_display.wheelEvent = self.on_match_display_wheel
        self.current_match_display.hide()
    def clear_search(self):
        self.search_input.clear()
        self.clear_search_highlights()
        self.current_search_results = []
        self.current_highlight_index = -1
        self.match_count_label.setText("0/0")
        self.current_match_display.clear()
        self.current_match_display.hide()
    def show_search(self):
        self.search_widget.show()
        self.search_visible = True
        self.search_input.setFocus()
        cursor = self.terminal_output.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText().strip()
            if selected_text and len(selected_text) < 100:
                self.search_input.setText(selected_text)
    def hide_search(self):
        self.search_widget.hide()
        self.current_match_display.hide()
        self.search_visible = False
        self.clear_search_highlights()
        self.current_search_results = []
        self.current_highlight_index = -1
        self.match_count_label.setText("0/0")
        self.terminal_output.setFocus()
    def toggle_search(self):
        if self.search_visible:
            self.hide_search()
        else:
            self.show_search()
    def on_search_text_changed(self):
        search_text = self.search_input.text().strip()
        if search_text:
            QTimer.singleShot(300, self.perform_search)
        else:
            self.clear_search_highlights()
            self.current_search_results = []
            self.current_highlight_index = -1
            self.match_count_label.setText("0/0")
            self.current_match_display.clear()
            self.current_match_display.hide()
    def perform_search(self):
        search_text = self.search_input.text().strip()
        if not search_text:
            return
        self.clear_search_highlights()
        terminal_text = self.terminal_output.toPlainText()
        lines = terminal_text.split('\n')
        search_mode = self.search_mode.currentText()
        matches = []
        try:
            if search_mode == t("fuzzy_match"):
                for line_num, line in enumerate(lines):
                    if search_text.lower() in line.lower():
                        matches.append((line_num, line.strip()))
            elif search_mode == t("exact_match"):
                for line_num, line in enumerate(lines):
                    if search_text in line:
                        matches.append((line_num, line.strip()))
            elif search_mode == t("regex_match"):
                pattern = re.compile(search_text, re.IGNORECASE)
                for line_num, line in enumerate(lines):
                    if pattern.search(line):
                        matches.append((line_num, line.strip()))
        except re.error as e:
            self.append_system_log(f"{t('regex_error')}: {e}", "error")
            return
        self.current_search_results = matches
        self.highlight_search_results(search_text, search_mode)
        match_count = len(matches)
        self.match_count_label.setText(f"0/{match_count}" if match_count > 0 else "0/0")
        self.update_all_matches_display(matches)
        if match_count > 0:
            self.current_highlight_index = 0
            self.jump_to_match(0)
    def highlight_search_results(self, search_text, search_mode):
        if not search_text:
            return
        self.clear_search_highlights()
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor(colors["terminal_selection"]))
        highlight_format.setForeground(QColor("#000000"))
        document = self.terminal_output.document()
        self.search_highlights = []
        if search_mode == t("regex_match"):
            try:
                from PySide6.QtCore import QRegularExpression
                regex = QRegularExpression(search_text)
                regex.setPatternOptions(QRegularExpression.PatternOption.CaseInsensitiveOption)
                cursor = QTextCursor(document)
                while True:
                    cursor = document.find(regex, cursor)
                    if cursor.isNull():
                        break
                    cursor.mergeCharFormat(highlight_format)
                    self.search_highlights.append((cursor.selectionStart(), cursor.selectionEnd()))
            except Exception as e:
                self.perform_simple_search(document, search_text, highlight_format, case_sensitive=False)
        else:
            case_sensitive = (search_mode == t("exact_match"))
            self.perform_simple_search(document, search_text, highlight_format, case_sensitive)
    def perform_simple_search(self, document, search_text, highlight_format, case_sensitive):
        if case_sensitive:
            find_flags = QTextDocument.FindFlag.FindCaseSensitively
        else:
            find_flags = QTextDocument.FindFlag(0)
        cursor = QTextCursor(document)
        while True:
            cursor = document.find(search_text, cursor, options=find_flags)
            if cursor.isNull():
                break
            start_pos = cursor.selectionStart()
            end_pos = cursor.selectionEnd()
            cursor.mergeCharFormat(highlight_format)
            self.search_highlights.append((start_pos, end_pos))
            cursor.setPosition(end_pos)
    def clear_search_highlights(self):
        if not self.search_highlights:
            return
        document = self.terminal_output.document()
        for start_pos, end_pos in self.search_highlights:
            cursor = QTextCursor(document)
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
            default_format = QTextCharFormat()
            default_format.setBackground(QColor("transparent"))
            default_format.setForeground(QColor(colors["terminal_text"]))
            cursor.setCharFormat(default_format)
        self.search_highlights = []
    def search_next(self):
        if not self.current_search_results:
            return
        self.current_highlight_index = (self.current_highlight_index + 1) % len(self.current_search_results)
        self.jump_to_match(self.current_highlight_index)
    def jump_to_match(self, index):
        if 0 <= index < len(self.current_search_results):
            line_num, line_content = self.current_search_results[index]
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(line_num):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            self.terminal_output.setTextCursor(cursor)
            self.terminal_output.ensureCursorVisible()
            self.match_count_label.setText(f"{index + 1}/{len(self.current_search_results)}")
            self.highlight_current_match_in_display(index)
    def update_all_matches_display(self, matches):
        if not matches:
            self.current_match_display.hide()
            return
        content_lines = []
        current_lang = get_current_language()
        for i, (line_num, line_content) in enumerate(matches):
            if current_lang.startswith('zh'):
                line_prefix = f"第 {line_num + 1} 行"
            else:
                line_prefix = f"Line {line_num + 1}"
            result_line = f"{line_prefix}: {line_content.strip()}"
            content_lines.append(result_line)
        self.current_match_display.setPlainText("\n".join(content_lines))
        self.current_match_display.show()
        self.current_match_display.verticalScrollBar().setValue(0)
    def highlight_current_match_in_display(self, current_index):
        if not self.current_search_results or current_index < 0 or current_index >= len(self.current_search_results):
            return
        target_line_num, _ = self.current_search_results[current_index]
        document = self.current_match_display.document()
        cursor = QTextCursor(document)
        cursor.select(QTextCursor.SelectionType.Document)
        default_format = QTextCharFormat()
        default_format.setBackground(QColor("transparent"))
        cursor.mergeCharFormat(default_format)
        cursor.clearSelection()
        current_lang = get_current_language()
        if current_lang.startswith('zh'):
            target_pattern = f"第 {target_line_num + 1} 行:"
        else:
            target_pattern = f"Line {target_line_num + 1}:"
        block = document.firstBlock()
        while block.isValid():
            block_text = block.text()
            if target_pattern in block_text:
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                highlight_format = QTextCharFormat()
                highlight_format.setBackground(QColor(colors["terminal_selection"]))
                highlight_format.setForeground(QColor("#000000"))
                cursor.mergeCharFormat(highlight_format)
                self.current_match_display.setTextCursor(cursor)
                self.current_match_display.ensureCursorVisible()
                break
            block = block.next()
    def on_match_display_wheel(self, event):
        QTextEdit.wheelEvent(self.current_match_display, event)
    def on_match_display_click(self, event):
        cursor = self.current_match_display.cursorForPosition(event.pos())
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText().strip()
        if not line_text:
            QTextEdit.mousePressEvent(self.current_match_display, event)
            return
        line_number_match = None
        zh_pattern = r"第\s*(\d+)\s*行"
        line_number_match = re.search(zh_pattern, line_text)
        if not line_number_match:
            en_pattern = r"Line\s*(\d+)"
            line_number_match = re.search(en_pattern, line_text)
        if line_number_match:
            terminal_line_number = int(line_number_match.group(1)) - 1
            target_index = -1
            for i, (line_num, line_content) in enumerate(self.current_search_results):
                if line_num == terminal_line_number:
                    target_index = i
                    break
            if target_index >= 0:
                self.current_highlight_index = target_index
                self.jump_to_match(target_index)
        QTextEdit.mousePressEvent(self.current_match_display, event)
    def show_prompt(self):
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(self.prompt)
        self.input_start_position = cursor.position()
        self.terminal_output.setTextCursor(cursor)
        self.terminal_output.ensureCursorVisible()
    def execute_command(self):
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
                cursor.insertHtml(f"<span style='color: {colors['terminal_command']};'>{t('command_sent').format(user_input=user_input)}</span>\n")
            else:
                self.process.write(b"\n")
        else:
            if user_input:
                cursor.insertHtml(f"<span style='color: {colors['log_command_error']};'>{t('process_not_running_error').format(user_input=user_input)}</span>\n")
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
    def replace_current_input(self, text):
        cursor = self.terminal_output.textCursor()
        cursor.setPosition(self.input_start_position)
        cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(text)
        self.terminal_output.setTextCursor(cursor)
    def clear_terminal(self):
        self.terminal_output.clear()
        self.show_prompt()
    
    def reset_status_to_running(self):
        
        self.status_label.setText(t("running"))
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["success"]};
                background: transparent;
                border: none;
                padding: {s(2)}px {s(6)}px;
                font-weight: bold;
            }}
        """)
    
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
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            system = platform.system()
            if system == "Windows":
                try:
                    self.process.write(b'\x03')  
                    self.append_system_log(t("interrupt_signal_windows"), "warning")
                except Exception as e:
                    self.append_system_log(f"{t('interrupt_signal_failed')}: {e}", "error")
                    self.process.kill()
                    self.append_system_log(t("force_terminate_process"), "warning")
            else:
                try:
                    self.process.write(b'\x03')
                    self.append_system_log(t("interrupt_signal_unix"), "warning")
                except Exception as e:
                    self.append_system_log(f"{t('interrupt_signal_failed')}: {e}", "error")
                    self.process.terminate()
                    self.append_system_log(t("graceful_terminate_process"), "warning")
        else:
            self.append_system_log(t("no_running_process"), "warning")
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
        copy_action = menu.addAction("📋 " + t("copy"))
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(cursor.hasSelection())
        copy_action.triggered.connect(self.copy_selection)
        paste_action = menu.addAction("📌 " + t("paste"))
        paste_action.setShortcut("Ctrl+V")
        clipboard = QApplication.clipboard()
        paste_action.setEnabled(bool(clipboard.text()))
        paste_action.triggered.connect(self.paste_text)
        menu.addSeparator()
        select_all_action = menu.addAction("🔍 " + t("select_all"))
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.terminal_output.selectAll)
        menu.addSeparator()
        search_action = menu.addAction("🔍 " + t("search"))
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.toggle_search)
        clear_action = menu.addAction("🧹 " + t("clear_screen"))
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self.clear_terminal)
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            menu.addSeparator()
            interrupt_action = menu.addAction("⛔ " + t("interrupt_process"))
            interrupt_action.triggered.connect(self.interrupt_process)
        menu.exec(self.terminal_output.mapToGlobal(position))
    def append_system_log(self, text, log_type="info"):
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        if log_type == "error":
            color = colors["log_error"]
            icon = "❌"
            prefix = t("log_error")
        elif log_type == "warning":
            color = colors["log_warning"]
            icon = "⚠️"
            prefix = t("log_warn")
        elif log_type == "success":
            color = colors["log_success"]
            icon = "✅"
            prefix = t("log_success")
        elif log_type == "info":
            color = colors["log_info"]
            icon = "ℹ️"
            prefix = t("log_info")
        else:
            color = colors["terminal_text"]
            icon = "📝"
            prefix = t("log_general")
        current_text = self.terminal_output.toPlainText()
        user_input = ""
        if current_text.endswith(self.prompt) or (current_text.split('\n')[-1].startswith(self.prompt) if current_text else False):
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
            current_line = cursor.selectedText()
            if current_line.startswith(self.prompt):
                user_input = current_line[len(self.prompt):]
            cursor.removeSelectedText()
        log_html = f"""<span style='color: {colors["log_timestamp"]}; font-size: {s(8)}pt;'>[{timestamp}]</span> <span style='color: {color}; font-weight: bold;'>{icon} {prefix}</span> <span style='color: {colors["terminal_text"]};'>{text}</span>"""
        cursor.insertHtml(log_html + "<br/>")
        cursor.insertText(self.prompt + user_input)
        self.input_start_position = cursor.position() - len(user_input)
        self.terminal_output.setTextCursor(cursor)
        self.terminal_output.ensureCursorVisible()
    def append_output(self, text):
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
    def append_output_html(self, html_text):
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
            cursor.insertHtml(html_text)

            if not html_text.endswith('<br>') and not html_text.endswith('<br/>'):
                cursor.insertText("\n")
            cursor.insertText(self.prompt + user_input)
            self.input_start_position = cursor.position() - len(user_input)
        else:
            cursor.insertHtml(html_text)
            if not html_text.endswith('<br>') and not html_text.endswith('<br/>'):
                cursor.insertText("\n")
        self.terminal_output.setTextCursor(cursor)
        self.terminal_output.ensureCursorVisible()
    def stop_process(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.status_label.setText(t("stopped"))
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["danger"]};
                    background: transparent;
                    border: none;
                    padding: {s(2)}px {s(6)}px;
                    font-weight: bold;
                }}
            """)
            self.append_system_log(t("process_stopped_manually"), "warning")
    def process_finished(self, exit_code):
        if exit_code == 0:
            self.status_label.setText(t("completed"))
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["success"]};
                    background: transparent;
                    border: none;
                    padding: {s(2)}px {s(6)}px;
                    font-weight: bold;
                }}
            """)
            self.append_system_log(f"{t('process_completed_normally')}, {t('exit_code')}: {exit_code}", "success")
        else:
            self.status_label.setText(t("error"))
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["danger"]};
                    background: transparent;
                    border: none;
                    padding: {s(2)}px {s(6)}px;
                    font-weight: bold;
                }}
            """)
            self.append_system_log(f"{t('process_exited_abnormally')}, {t('exit_code')}: {exit_code}", "error")
        self.show_prompt()
