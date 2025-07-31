from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QTextEdit, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QSplitter, QTabWidget,
    QSpinBox, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QTextCursor
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SearchResult:
    type: str
    title: str
    content: str
    source: str
    line_number: int = 0
    score: float = 0.0
    context: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SearchHighlighter:
    def __init__(self, text_edit: QTextEdit, theme_manager=None):
        self.text_edit = text_edit
        self.theme_manager = theme_manager
        self.current_matches = []
        self.current_index = -1
        
    def highlight_text(self, pattern: str, case_sensitive: bool = False, 
                      use_regex: bool = False) -> int:
        self.clear_highlights()
        
        if not pattern:
            return 0
            
        document = self.text_edit.document()
        cursor = QTextCursor(document)
        

        highlight_format = QTextCharFormat()
        if self.theme_manager:
            highlight_color = QColor(self.theme_manager.get_theme_color("highlight"))
            highlight_color.setAlpha(100)
            highlight_format.setBackground(highlight_color)
        else:
            highlight_format.setBackground(QColor(255, 255, 0, 100))
        
        current_format = QTextCharFormat()
        if self.theme_manager:
            current_color = QColor(self.theme_manager.get_theme_color("highlight_current"))
            current_color.setAlpha(150)
            current_format.setBackground(current_color)
        else:
            current_format.setBackground(QColor(255, 165, 0, 150))
        
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            if use_regex:
                regex = re.compile(pattern, flags)
            else:
                escaped_pattern = re.escape(pattern)
                regex = re.compile(escaped_pattern, flags)
        except re.error:
            return 0
            
        text = document.toPlainText()
        matches = list(regex.finditer(text))
        
        for match in matches:
            start = match.start()
            length = match.end() - start
            
            cursor.setPosition(start)
            cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
            cursor.setCharFormat(highlight_format)
            
            self.current_matches.append((start, length))
            
        if self.current_matches:
            self.current_index = 0
            self.highlight_current_match()
            
        return len(self.current_matches)
        
    def highlight_current_match(self):
        if not self.current_matches or self.current_index < 0:
            return
            

        for i, (start, length) in enumerate(self.current_matches):
            cursor = QTextCursor(self.text_edit.document())
            cursor.setPosition(start)
            cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
            
            if i == self.current_index:

                current_format = QTextCharFormat()
                if self.theme_manager:
                    current_color = QColor(self.theme_manager.get_theme_color("highlight_current"))
                    current_color.setAlpha(150)
                    current_format.setBackground(current_color)
                else:
                    current_format.setBackground(QColor(255, 165, 0, 150))
                cursor.setCharFormat(current_format)
            else:

                highlight_format = QTextCharFormat()
                if self.theme_manager:
                    highlight_color = QColor(self.theme_manager.get_theme_color("highlight"))
                    highlight_color.setAlpha(100)
                    highlight_format.setBackground(highlight_color)
                else:
                    highlight_format.setBackground(QColor(255, 255, 0, 100))
                cursor.setCharFormat(highlight_format)
                

        if self.current_index < len(self.current_matches):
            start, _ = self.current_matches[self.current_index]
            cursor = QTextCursor(self.text_edit.document())
            cursor.setPosition(start)
            self.text_edit.setTextCursor(cursor)
            self.text_edit.ensureCursorVisible()
            
    def next_match(self) -> bool:
        if not self.current_matches:
            return False
            
        self.current_index = (self.current_index + 1) % len(self.current_matches)
        self.highlight_current_match()
        return True
        
    def previous_match(self) -> bool:
        if not self.current_matches:
            return False
            
        self.current_index = (self.current_index - 1) % len(self.current_matches)
        self.highlight_current_match()
        return True
        
    def clear_highlights(self):
        cursor = QTextCursor(self.text_edit.document())
        cursor.select(QTextCursor.SelectionType.Document)
        
        default_format = QTextCharFormat()
        cursor.setCharFormat(default_format)
        
        self.current_matches.clear()
        self.current_index = -1
        
    def get_match_info(self) -> Tuple[int, int]:
        return (self.current_index + 1 if self.current_matches else 0, 
                len(self.current_matches))

class SearchWorker(QThread):
    search_progress = Signal(int)
    search_result = Signal(list)
    search_finished = Signal()
    
    def __init__(self, query: str, search_options: Dict[str, Any], 
                 data_sources: Dict[str, Any]):
        super().__init__()
        self.query = query
        self.search_options = search_options
        self.data_sources = data_sources
        self.results = []
        
    def run(self):
        try:
            self.results.clear()
            total_sources = len(self.data_sources)
            
            for i, (source_name, source_data) in enumerate(self.data_sources.items()):
                if source_name == 'tools' and self.search_options.get('search_tools', True):
                    self.search_tools(source_data)
                elif source_name == 'parameters' and self.search_options.get('search_parameters', True):
                    self.search_parameters(source_data)
                elif source_name == 'outputs' and self.search_options.get('search_outputs', True):
                    self.search_outputs(source_data)
                    
                progress = int((i + 1) / total_sources * 100)
                self.search_progress.emit(progress)
                

            self.results.sort(key=lambda x: x.score, reverse=True)
            
            self.search_result.emit(self.results)
            
        except Exception as e:
            print(f"搜索出错: {e}")
        finally:
            self.search_finished.emit()
            
    def search_tools(self, tools_data):
        case_sensitive = self.search_options.get('case_sensitive', False)
        use_regex = self.search_options.get('use_regex', False)
        
        for tool_info in tools_data:
            score = 0
            matches = []
            

            if self.match_text(self.query, tool_info.name, case_sensitive, use_regex):
                score += 10
                matches.append('name')
                

            if self.match_text(self.query, tool_info.display_name, case_sensitive, use_regex):
                score += 8
                matches.append('display_name')
                

            if self.match_text(self.query, tool_info.description, case_sensitive, use_regex):
                score += 5
                matches.append('description')
                

            for tag in tool_info.tags:
                if self.match_text(self.query, tag, case_sensitive, use_regex):
                    score += 3
                    matches.append('tags')
                    

            if self.match_text(self.query, tool_info.category, case_sensitive, use_regex):
                score += 4
                matches.append('category')
                
            if score > 0:
                result = SearchResult(
                    type='tool',
                    title=tool_info.display_name or tool_info.name,
                    content=tool_info.description,
                    source=f"工具: {tool_info.name}",
                    score=score,
                    metadata={
                        'tool_info': tool_info,
                        'matches': matches
                    }
                )
                self.results.append(result)
                
    def search_parameters(self, parameters_data):
        case_sensitive = self.search_options.get('case_sensitive', False)
        use_regex = self.search_options.get('use_regex', False)
        
        for tool_name, params in parameters_data.items():
            for param_name, param_config in params.items():
                score = 0
                matches = []
                

                if self.match_text(self.query, param_name, case_sensitive, use_regex):
                    score += 8
                    matches.append('name')
                    

                description = param_config.get('description', '')
                if self.match_text(self.query, description, case_sensitive, use_regex):
                    score += 5
                    matches.append('description')
                    

                default_value = str(param_config.get('default', ''))
                if self.match_text(self.query, default_value, case_sensitive, use_regex):
                    score += 3
                    matches.append('default')
                    
                if score > 0:
                    result = SearchResult(
                        type='parameter',
                        title=f"{param_name} ({tool_name})",
                        content=description,
                        source=f"参数: {tool_name}.{param_name}",
                        score=score,
                        metadata={
                            'tool_name': tool_name,
                            'param_name': param_name,
                            'param_config': param_config,
                            'matches': matches
                        }
                    )
                    self.results.append(result)
                    
    def search_outputs(self, outputs_data):
        case_sensitive = self.search_options.get('case_sensitive', False)
        use_regex = self.search_options.get('use_regex', False)
        
        for output_info in outputs_data:
            content = output_info.get('content', '')
            source = output_info.get('source', '')
            timestamp = output_info.get('timestamp', '')
            
            if self.match_text(self.query, content, case_sensitive, use_regex):

                lines = content.split('\n')
                matching_lines = []
                
                for i, line in enumerate(lines):
                    if self.match_text(self.query, line, case_sensitive, use_regex):
                        matching_lines.append((i + 1, line.strip()))
                        
                for line_num, line_content in matching_lines:
                    result = SearchResult(
                        type='output',
                        title=f"输出匹配 (第{line_num}行)",
                        content=line_content,
                        source=f"输出: {source}",
                        line_number=line_num,
                        score=2,
                        context=self.get_context(lines, line_num - 1, 2),
                        metadata={
                            'full_content': content,
                            'timestamp': timestamp,
                            'source': source
                        }
                    )
                    self.results.append(result)
                    
    def match_text(self, query: str, text: str, case_sensitive: bool, use_regex: bool) -> bool:
        if not text:
            return False
            
        try:
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(query, text, flags))
            else:
                if case_sensitive:
                    return query in text
                else:
                    return query.lower() in text.lower()
        except re.error:
            return False
            
    def get_context(self, lines: List[str], target_line: int, context_size: int) -> str:
        start = max(0, target_line - context_size)
        end = min(len(lines), target_line + context_size + 1)
        
        context_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == target_line else "    "
            context_lines.append(f"{prefix}{lines[i]}")
            
        return '\n'.join(context_lines)

class SearchWidget(QWidget):
    search_requested = Signal(str, dict)
    result_selected = Signal(SearchResult)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_worker = None
        self.current_results = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        search_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入搜索关键词...")
        self.search_edit.returnPressed.connect(self.start_search)
        search_layout.addWidget(self.search_edit)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.start_search)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        

        options_group = QGroupBox("搜索选项")
        options_layout = QHBoxLayout(options_group)
        
        self.case_sensitive_cb = QCheckBox("区分大小写")
        options_layout.addWidget(self.case_sensitive_cb)
        
        self.regex_cb = QCheckBox("正则表达式")
        options_layout.addWidget(self.regex_cb)
        
        self.search_tools_cb = QCheckBox("搜索工具")
        self.search_tools_cb.setChecked(True)
        options_layout.addWidget(self.search_tools_cb)
        
        self.search_params_cb = QCheckBox("搜索参数")
        self.search_params_cb.setChecked(True)
        options_layout.addWidget(self.search_params_cb)
        
        self.search_outputs_cb = QCheckBox("搜索输出")
        self.search_outputs_cb.setChecked(True)
        options_layout.addWidget(self.search_outputs_cb)
        
        options_layout.addStretch()
        layout.addWidget(options_group)
        

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        

        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.on_result_selected)
        layout.addWidget(self.results_list)
        

        self.status_label = QLabel("准备搜索")
        layout.addWidget(self.status_label)
        
    def start_search(self):
        query = self.search_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "警告", "请输入搜索关键词")
            return
            
        search_options = {
            'case_sensitive': self.case_sensitive_cb.isChecked(),
            'use_regex': self.regex_cb.isChecked(),
            'search_tools': self.search_tools_cb.isChecked(),
            'search_parameters': self.search_params_cb.isChecked(),
            'search_outputs': self.search_outputs_cb.isChecked()
        }
        
        self.search_requested.emit(query, search_options)
        
    def perform_search(self, query: str, search_options: Dict[str, Any], 
                      data_sources: Dict[str, Any]):
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.search_btn.setEnabled(False)
        self.status_label.setText("搜索中...")
        
        self.search_worker = SearchWorker(query, search_options, data_sources)
        self.search_worker.search_progress.connect(self.progress_bar.setValue)
        self.search_worker.search_result.connect(self.display_results)
        self.search_worker.search_finished.connect(self.search_finished)
        self.search_worker.start()
        
    def display_results(self, results: List[SearchResult]):
        self.current_results = results
        self.results_list.clear()
        
        for result in results:
            item = QListWidgetItem()
            item.setText(f"[{result.type.upper()}] {result.title}")
            item.setData(Qt.UserRole, result)
            
            tooltip = f"来源: {result.source}\n内容: {result.content}"
            if result.line_number > 0:
                tooltip += f"\n行号: {result.line_number}"
            if result.context:
                tooltip += f"\n\n上下文:\n{result.context}"
                
            item.setToolTip(tooltip)
            self.results_list.addItem(item)
            
        self.status_label.setText(f"找到 {len(results)} 个结果")
        
    def search_finished(self):
        self.progress_bar.setVisible(False)
        self.search_btn.setEnabled(True)
        
    def on_result_selected(self, item: QListWidgetItem):
        result = item.data(Qt.UserRole)
        if result:
            self.result_selected.emit(result)
            
    def clear_results(self):
        self.results_list.clear()
        self.current_results.clear()
        self.status_label.setText("准备搜索")

class OutputSearchWidget(QWidget):
    def __init__(self, text_edit: QTextEdit, theme_manager=None, parent=None):
        super().__init__(parent)
        self.text_edit = text_edit
        self.theme_manager = theme_manager
        self.highlighter = SearchHighlighter(text_edit, theme_manager)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("在输出中搜索...")
        self.search_edit.textChanged.connect(self.search_text)
        self.search_edit.returnPressed.connect(self.next_match)
        layout.addWidget(self.search_edit)
        
        self.case_cb = QCheckBox("Aa")
        self.case_cb.setToolTip("区分大小写")
        self.case_cb.toggled.connect(self.search_text)
        layout.addWidget(self.case_cb)
        
        self.regex_cb = QCheckBox(".*")
        self.regex_cb.setToolTip("正则表达式")
        self.regex_cb.toggled.connect(self.search_text)
        layout.addWidget(self.regex_cb)
        
        self.prev_btn = QPushButton("↑")
        self.prev_btn.setMaximumWidth(30)
        self.prev_btn.clicked.connect(self.previous_match)
        layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("↓")
        self.next_btn.setMaximumWidth(30)
        self.next_btn.clicked.connect(self.next_match)
        layout.addWidget(self.next_btn)
        
        self.match_label = QLabel("0/0")
        self.match_label.setMinimumWidth(40)
        layout.addWidget(self.match_label)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setMaximumWidth(25)
        self.close_btn.clicked.connect(self.close_search)
        layout.addWidget(self.close_btn)
        
        self.update_buttons()
        
    def search_text(self):
        pattern = self.search_edit.text()
        if not pattern:
            self.highlighter.clear_highlights()
            self.update_buttons()
            return
            
        case_sensitive = self.case_cb.isChecked()
        use_regex = self.regex_cb.isChecked()
        
        count = self.highlighter.highlight_text(pattern, case_sensitive, use_regex)
        self.update_buttons()
        
    def next_match(self):
        self.highlighter.next_match()
        self.update_buttons()
        
    def previous_match(self):
        self.highlighter.previous_match()
        self.update_buttons()
        
    def update_buttons(self):
        current, total = self.highlighter.get_match_info()
        self.match_label.setText(f"{current}/{total}")
        
        has_matches = total > 0
        self.prev_btn.setEnabled(has_matches)
        self.next_btn.setEnabled(has_matches)
        
    def close_search(self):
        self.highlighter.clear_highlights()
        self.setVisible(False)
        
    def show_search(self):
        self.setVisible(True)
        self.search_edit.setFocus()
        self.search_edit.selectAll()

class AdvancedSearchDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级搜索")
        self.resize(800, 600)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        conditions_group = QGroupBox("搜索条件")
        conditions_layout = QVBoxLayout(conditions_group)
        

        basic_layout = QHBoxLayout()
        basic_layout.addWidget(QLabel("关键词:"))
        self.keyword_edit = QLineEdit()
        basic_layout.addWidget(self.keyword_edit)
        conditions_layout.addLayout(basic_layout)
        

        tool_layout = QHBoxLayout()
        tool_layout.addWidget(QLabel("工具:"))
        self.tool_combo = QComboBox()
        self.tool_combo.addItem("所有工具")
        tool_layout.addWidget(self.tool_combo)
        conditions_layout.addLayout(tool_layout)
        

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("时间范围:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["不限", "最近1小时", "最近1天", "最近1周", "最近1月"])
        time_layout.addWidget(self.time_combo)
        conditions_layout.addLayout(time_layout)
        
        layout.addWidget(conditions_group)
        

        self.search_widget = SearchWidget()
        layout.addWidget(self.search_widget)