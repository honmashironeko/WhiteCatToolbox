import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, 
    QGroupBox, QCheckBox, QLineEdit, QLabel, QPushButton,
    QTabWidget, QFrame, QSizePolicy, QTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QSlider, QProgressBar, QFileDialog,
    QMessageBox, QSplitter, QTreeWidget, QTreeWidgetItem, QDialog,
    QGridLayout, QRadioButton, QInputDialog, QListWidget, QListWidgetItem,
    QDialogButtonBox, QFormLayout, QApplication, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer, QMimeData, QEvent
from PySide6.QtGui import QFont, QIcon, QPalette, QDrag, QAction

class ParameterManager:
    """参数管理器，负责统一管理参数的分类和操作规则"""
    
    def __init__(self, tool_info):
        self.tool_info = tool_info
        self.config_file_path = Path(tool_info.path) / "wct_config.txt"
        
    def get_common_parameters(self) -> List[Dict]:
        """获取常用参数列表"""
        return self._get_parameters_by_section('常用参数')
        
    def get_all_parameters(self) -> List[Dict]:
        """获取全部参数列表"""
        return self._get_parameters_by_section('全部参数')
        
    def _get_parameters_by_section(self, section_name: str) -> List[Dict]:
        """根据配置文件段名获取参数列表"""
        if not self.config_file_path.exists():
            return []
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return self._parse_section_parameters(content, section_name)
        except Exception as e:
            print(f"解析参数配置失败: {e}")
            return []
            
    def _parse_section_parameters(self, content: str, target_section: str) -> List[Dict]:
        """解析指定段的参数"""
        parameters = []
        current_section = None
        current_param_type = None
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                

            if line.startswith('%') and not line.startswith('%%'):
                current_section = line[1:].strip()
                continue
                

            if line.startswith('%%'):
                current_param_type = line[2:].strip()
                continue
                

            if current_section != target_section:
                continue
                

            if '=' in line:
                param_info = self._parse_parameter_line(line, current_param_type)
                if param_info:
                    parameters.append(param_info)
                    
        return parameters
        
    def _parse_parameter_line(self, line: str, param_type: str) -> Optional[Dict]:
        """解析单个参数行"""
        parts = line.split('=')
        if len(parts) < 4:
            return None
            
        param_name = parts[0].strip()
        display_name = parts[1].strip()
        description = parts[2].strip()
        required_str = parts[3].strip()
        

        param_data_type = 'boolean' if param_type == '勾选项' else 'string'
        

        required = required_str == '1'
        

        default_value = False if param_data_type == 'boolean' else ''
        
        return {
            'name': param_name,
            'type': param_data_type,
            'display_name': display_name,
            'description': description,
            'default': default_value,
            'required': required
        }
        
    def move_parameter_between_sections(self, param_name: str, from_section: str, to_section: str) -> bool:
        """在配置文件中移动参数到不同段"""
        if not self.config_file_path.exists():
            return False
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                

            param_line = None
            param_type = None
            new_lines = []
            current_section = None
            current_param_type = None
            
            for line in lines:
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                    new_lines.append(line)
                elif line_strip.startswith('%%'):
                    current_param_type = line_strip[2:].strip()
                    new_lines.append(line)
                elif '=' in line_strip and line_strip.split('=')[0].strip() == param_name:
                    if current_section == from_section:
                        param_line = line
                        param_type = current_param_type
                        continue
                    new_lines.append(line)
                else:
                    new_lines.append(line)
                    
            if not param_line:
                return False
                

            final_lines = []
            current_section = None
            current_param_type = None
            inserted = False
            
            for line in new_lines:
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                    final_lines.append(line)
                elif line_strip.startswith('%%'):
                    current_param_type = line_strip[2:].strip()
                    final_lines.append(line)
                    

                    if (current_section == to_section and 
                        current_param_type == param_type and 
                        not inserted):
                        final_lines.append(param_line)
                        inserted = True
                else:
                    final_lines.append(line)
                    

            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                f.writelines(final_lines)
                
            return inserted
        except Exception as e:
            print(f"移动参数失败: {e}")
            return False
            
    def copy_parameter_to_section(self, param_name: str, from_section: str, to_section: str) -> bool:
        """复制参数到另一个段"""
        if not self.config_file_path.exists():
            return False
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                

            param_line = None
            param_type = None
            current_section = None
            current_param_type = None
            
            for line in lines:
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                elif line_strip.startswith('%%'):
                    current_param_type = line_strip[2:].strip()
                elif '=' in line_strip and line_strip.split('=')[0].strip() == param_name:
                    if current_section == from_section:
                        param_line = line
                        param_type = current_param_type
                        break
                        
            if not param_line:
                return False
                

            current_section = None
            param_exists = False
            
            for line in lines:
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                elif '=' in line_strip and line_strip.split('=')[0].strip() == param_name:
                    if current_section == to_section:
                        param_exists = True
                        break
                        
            if param_exists:
                return False
                

            new_lines = []
            current_section = None
            current_param_type = None
            inserted = False
            
            for line in lines:
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                    new_lines.append(line)
                elif line_strip.startswith('%%'):
                    current_param_type = line_strip[2:].strip()
                    new_lines.append(line)
                    

                    if (current_section == to_section and 
                        current_param_type == param_type and 
                        not inserted):
                        new_lines.append(param_line)
                        inserted = True
                else:
                    new_lines.append(line)
                    

            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
            return inserted
        except Exception as e:
            print(f"复制参数失败: {e}")
            return False
            
    def remove_parameter_from_section(self, param_name: str, section: str) -> bool:
        """从指定段移除参数"""
        if not self.config_file_path.exists():
            return False
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            new_lines = []
            current_section = None
            removed = False
            
            for line in lines:
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                    new_lines.append(line)
                elif '=' in line_strip and line_strip.split('=')[0].strip() == param_name:
                    if current_section == section:
                        removed = True
                        continue
                    new_lines.append(line)
                else:
                    new_lines.append(line)
                    
            if removed:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                    
            return removed
        except Exception as e:
            print(f"删除参数失败: {e}")
            return False
            
    def reorder_parameter_in_section(self, param_name: str, target_param_name: str, section: str, insert_position: int) -> bool:
        """在同一段内重新排序参数"""
        if not self.config_file_path.exists():
            return False
            
        if param_name == target_param_name:
            return True
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                

            param_line = None
            param_line_index = -1
            target_line_index = -1
            current_section = None
            
            for i, line in enumerate(lines):
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                elif '=' in line_strip:
                    line_param = line_strip.split('=')[0].strip()
                    if line_param == param_name and current_section == section:
                        param_line = line
                        param_line_index = i
                    elif line_param == target_param_name and current_section == section:
                        target_line_index = i
                        
            if param_line_index == -1 or target_line_index == -1:
                print(f"找不到参数: {param_name} 或 {target_param_name}")
                return False
                

            new_lines = lines[:param_line_index] + lines[param_line_index + 1:]
            

            if target_line_index > param_line_index:
                target_line_index -= 1
                

            if insert_position == 0:
                insert_index = target_line_index
            else:
                insert_index = target_line_index + 1
                

            new_lines.insert(insert_index, param_line)
            

            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
            return True
        except Exception as e:
            print(f"重新排序参数失败: {e}")
            return False
            
    def change_parameter_type(self, param_name: str, new_type: str) -> bool:
        """更改参数类型（boolean <-> string）"""
        if not self.config_file_path.exists():
            return False
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                

            param_line = None
            param_line_index = -1
            param_section = None
            current_section = None
            current_param_type = None
            
            for i, line in enumerate(lines):
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                elif line_strip.startswith('%%'):
                    current_param_type = line_strip[2:].strip()
                elif '=' in line_strip and line_strip.split('=')[0].strip() == param_name:
                    param_line = line
                    param_line_index = i
                    param_section = current_section
                    break
                    
            if not param_line:
                print(f"找不到参数: {param_name}")
                return False
                

            new_lines = lines[:param_line_index] + lines[param_line_index + 1:]
            

            target_section_name = '勾选项' if new_type == 'boolean' else '输入项'
            final_lines = []
            current_section = None
            current_param_type = None
            inserted = False
            
            for line in new_lines:
                line_strip = line.strip()
                
                if line_strip.startswith('%') and not line_strip.startswith('%%'):
                    current_section = line_strip[1:].strip()
                    final_lines.append(line)
                elif line_strip.startswith('%%'):
                    current_param_type = line_strip[2:].strip()
                    final_lines.append(line)
                    

                    if (current_section == param_section and 
                        current_param_type == target_section_name and 
                        not inserted):
                        final_lines.append(param_line)
                        inserted = True
                else:
                    final_lines.append(line)
                    
            if not inserted:
                print(f"未能在正确位置插入参数 {param_name}")
                return False
                

            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                f.writelines(final_lines)
                
            return True
        except Exception as e:
            print(f"更改参数类型失败: {e}")
            return False
            
    def update_parameter_info(self, param_name: str, display_name: str, description: str) -> bool:
        """更新参数信息"""
        if not self.config_file_path.exists():
            return False
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            new_lines = []
            updated = False
            
            for line in lines:
                line_strip = line.strip()
                if '=' in line_strip and line_strip.split('=')[0].strip() == param_name:
                    parts = line_strip.split('=')
                    if len(parts) >= 4:
                        parts[1] = display_name
                        parts[2] = description
                        new_line = '='.join(parts) + '\n'
                        new_lines.append(new_line)
                        updated = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
                    
            if updated:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                    
            return updated
        except Exception as e:
            print(f"更新参数信息失败: {e}")
            return False
            
    def set_parameter_required(self, param_name: str, required: bool) -> bool:
        """设置参数是否必填"""
        if not self.config_file_path.exists():
            return False
            
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            new_lines = []
            updated = False
            
            for line in lines:
                line_strip = line.strip()
                if '=' in line_strip and line_strip.split('=')[0].strip() == param_name:
                    parts = line_strip.split('=')
                    if len(parts) >= 4:
                        parts[3] = '1' if required else '0'
                        new_line = '='.join(parts) + '\n'
                        new_lines.append(new_line)
                        updated = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
                    
            if updated:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                    
            return updated
        except Exception as e:
            print(f"设置参数必填状态失败: {e}")
            return False

class ParameterWidget(QWidget):
    value_changed = Signal(str, object)
    parameter_moved = Signal(str, str, str, str, int)
    parameter_context_menu = Signal(str, object, object)
    
    def __init__(self, param_name, param_config, section_name="common"):
        super().__init__()
        self.param_name = param_name
        self.param_config = param_config
        self.section_name = section_name
        self.input_widget = None
        

        self.setAcceptDrops(True)
        

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        

        self.drag_active = False
        
        self.setup_ui()
        self.set_default_value()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        

        param_type = self.param_config.get('type', 'string')
        
        if param_type == 'boolean':

            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.input_widget = self._create_input_widget(param_type)
            if self.input_widget:
                layout.addWidget(self.input_widget)
                self._connect_signals()

                self.input_widget.installEventFilter(self)
        else:

            layout.setContentsMargins(5, 5, 5, 5)
            display_name = self.param_config.get('display_name', self.param_name)
            label_text = display_name
            if self.param_config.get('required', False):
                label_text += ' *'
                
            label = QLabel(label_text)
            label.setWordWrap(True)
            if self.param_config.get('required', False):
                label.setProperty("class", "required_param")
            

            tooltip_text = f"原参数: {self.param_name}\n参数名: {display_name}\n参数介绍: {self.param_config.get('description', '无描述')}"
            label.setToolTip(tooltip_text)
            self.setToolTip(tooltip_text)
            
            layout.addWidget(label)
            

            self.input_widget = self._create_input_widget(param_type)
            
            if self.input_widget:
                layout.addWidget(self.input_widget)
                self._connect_signals()

                self.input_widget.installEventFilter(self)
            
    def _create_input_widget(self, param_type):
        if param_type == 'boolean':

            display_name = self.param_config.get('display_name', self.param_name)
            
            widget = QPushButton()
            widget.setCheckable(True)
            widget.setProperty("toggle_style", "default")
            

            def update_toggle_style():
                if widget.isChecked():
                    widget.setProperty("toggle_style", "checked")
                else:
                    widget.setProperty("toggle_style", "default")

                widget.style().unpolish(widget)
                widget.style().polish(widget)
            
            widget.toggled.connect(update_toggle_style)
            

            widget.setText(display_name)
            

            tooltip_text = f"原参数: {self.param_name}\n参数名: {display_name}\n参数介绍: {self.param_config.get('description', '无描述')}"
            widget.setToolTip(tooltip_text)
            
            return widget
        elif param_type == 'integer':
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            return widget
        elif param_type == 'float':
            widget = QDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.setDecimals(2)
            return widget
        elif param_type == 'choice':
            widget = QComboBox()
            choices = self.param_config.get('choices', [])
            widget.addItems(choices)
            return widget
        elif param_type == 'file':
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            line_edit = QLineEdit()
            browse_btn = QPushButton('浏览...')
            browse_btn.clicked.connect(lambda: self._browse_file(line_edit))
            
            layout.addWidget(line_edit)
            layout.addWidget(browse_btn)
            
            container.line_edit = line_edit
            return container
        elif param_type == 'directory':
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            
            line_edit = QLineEdit()
            browse_btn = QPushButton('浏览...')
            browse_btn.clicked.connect(lambda: self._browse_directory(line_edit))
            
            layout.addWidget(line_edit)
            layout.addWidget(browse_btn)
            
            container.line_edit = line_edit
            return container
        elif param_type == 'text':
            widget = QTextEdit()
            widget.setMaximumHeight(100)
            return widget
        else:
            widget = QLineEdit()
            return widget
            
    def _connect_signals(self):
        if isinstance(self.input_widget, QPushButton) and self.input_widget.isCheckable():
            self.input_widget.toggled.connect(self._emit_value_changed)
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            self.input_widget.valueChanged.connect(self._emit_value_changed)
        elif isinstance(self.input_widget, QComboBox):
            self.input_widget.currentTextChanged.connect(self._emit_value_changed)
        elif isinstance(self.input_widget, QLineEdit):
            self.input_widget.textChanged.connect(self._emit_value_changed)
        elif isinstance(self.input_widget, QTextEdit):
            self.input_widget.textChanged.connect(self._emit_value_changed)
        elif hasattr(self.input_widget, 'line_edit'):
            self.input_widget.line_edit.textChanged.connect(self._emit_value_changed)
            
    def _emit_value_changed(self):
        self.value_changed.emit(self.param_name, self.get_value())

        self.update_validation_status()
        
    def update_validation_status(self):
        """更新验证状态，为必选项添加红色标记"""
        if not self.param_config.get('required', False):

            self.clear_error_style()
            return
        

        value = self.get_value()
        is_empty = False
        
        if isinstance(value, str):
            is_empty = not value.strip()
        elif isinstance(value, bool):

            is_empty = not value
        else:
            is_empty = not value
        
        if is_empty:
            self.set_error_style()
        else:
            self.clear_error_style()
    
    def set_error_style(self):
        """设置错误样式（红色边框）"""
        if self.input_widget:

            self.input_widget.setProperty("validation_error", True)

            self.input_widget.style().unpolish(self.input_widget)
            self.input_widget.style().polish(self.input_widget)
            

            if hasattr(self.input_widget, 'line_edit'):
                self.input_widget.line_edit.setProperty("validation_error", True)
                self.input_widget.line_edit.style().unpolish(self.input_widget.line_edit)
                self.input_widget.line_edit.style().polish(self.input_widget.line_edit)
    
    def clear_error_style(self):
        """清除错误样式"""
        if self.input_widget:

            self.input_widget.setProperty("validation_error", False)

            self.input_widget.style().unpolish(self.input_widget)
            self.input_widget.style().polish(self.input_widget)
            

            if hasattr(self.input_widget, 'line_edit'):
                self.input_widget.line_edit.setProperty("validation_error", False)
                self.input_widget.line_edit.style().unpolish(self.input_widget.line_edit)
                self.input_widget.line_edit.style().polish(self.input_widget.line_edit)
        
    def _browse_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(self, '选择文件')
        if file_path:
            line_edit.setText(file_path)
            
    def _browse_directory(self, line_edit):
        dir_path = QFileDialog.getExistingDirectory(self, '选择目录')
        if dir_path:
            line_edit.setText(dir_path)
            
    def set_default_value(self):
        default_value = self.param_config.get('default')
        if default_value is not None:
            self.set_value(default_value)
        else:

            self.update_validation_status()
            
    def set_value(self, value):
        if isinstance(self.input_widget, QPushButton) and self.input_widget.isCheckable():
            self.input_widget.setChecked(bool(value))
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            self.input_widget.setValue(value)
        elif isinstance(self.input_widget, QComboBox):
            index = self.input_widget.findText(str(value))
            if index >= 0:
                self.input_widget.setCurrentIndex(index)
        elif isinstance(self.input_widget, QLineEdit):
            self.input_widget.setText(str(value))
        elif isinstance(self.input_widget, QTextEdit):
            self.input_widget.setPlainText(str(value))
        elif hasattr(self.input_widget, 'line_edit'):
            self.input_widget.line_edit.setText(str(value))
        

        self.update_validation_status()
        
    def get_value(self):
        if isinstance(self.input_widget, QPushButton) and self.input_widget.isCheckable():
            return self.input_widget.isChecked()
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            return self.input_widget.value()
        elif isinstance(self.input_widget, QComboBox):
            return self.input_widget.currentText()
        elif isinstance(self.input_widget, QLineEdit):
            return self.input_widget.text()
        elif isinstance(self.input_widget, QTextEdit):
            return self.input_widget.toPlainText()
        elif hasattr(self.input_widget, 'line_edit'):
            return self.input_widget.line_edit.text()
        return ''
        
    def validate(self):
        if self.param_config.get('required', False):
            value = self.get_value()
            if not value or (isinstance(value, str) and not value.strip()):
                return False, f"参数 '{self.param_name}' 是必需的"
        return True, ''
        
    def eventFilter(self, obj, event):
        """事件过滤器，处理子控件的鼠标事件以支持拖拽"""
        if obj == self.input_widget:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.drag_start_position = event.position().toPoint()
                    self.mousePressEvent(event)
                    return False
            elif event.type() == QEvent.MouseMove:
                if hasattr(self, 'drag_start_position') and (event.buttons() & Qt.LeftButton):
                    self.mouseMoveEvent(event)
                    return True
        return super().eventFilter(obj, event)
        
    def mousePressEvent(self, event):
        """鼠标按下事件，准备拖拽"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """鼠标移动事件，开始拖拽"""
        if not (event.buttons() & Qt.LeftButton):
            return
            
        if not hasattr(self, 'drag_start_position'):
            return
            

        drag_distance = (event.position().toPoint() - self.drag_start_position).manhattanLength()
        min_drag_distance = 10
        
        if drag_distance < min_drag_distance:
            return
            
        self._start_drag()
        
    def _start_drag(self):
        """开始拖拽操作"""
        drag = QDrag(self)
        mime_data = QMimeData()
        

        drag_data = {
            'param_name': self.param_name,
            'param_config': self.param_config,
            'section_name': self.section_name,
            'param_type': self.param_config.get('type', 'string')
        }
        
        mime_data.setText(json.dumps(drag_data, ensure_ascii=False))
        drag.setMimeData(mime_data)
        

        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(200, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        drag.setHotSpot(pixmap.rect().center())
        

        drop_action = drag.exec(Qt.MoveAction | Qt.CopyAction)
        
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText():
            try:
                drag_data = json.loads(event.mimeData().text())
                if 'param_name' in drag_data:
                    event.acceptProposedAction()
                    self.setStyleSheet("border: 2px dashed #0078d4;")
                    return
            except Exception as e:
                pass
        event.ignore()
        
    def dragLeaveEvent(self, event):
        """拖拽离开事件"""
        self.setStyleSheet("")
        
    def dropEvent(self, event):
        """拖拽放下事件"""
        self.setStyleSheet("")
        
        if event.mimeData().hasText():
            try:
                drag_data = json.loads(event.mimeData().text())
                if 'param_name' in drag_data:

                    drop_pos = event.position()
                    widget_height = self.height()
                    insert_position = 0
                    
                    if drop_pos.y() > widget_height / 2:
                        insert_position = 1
                

                    self.parameter_moved.emit(
                        drag_data['param_name'],
                        drag_data['section_name'],
                        self.section_name,
                        self.param_name,
                        insert_position
                    )
                    event.acceptProposedAction()
                    return
            except Exception as e:
                print(f"处理拖拽放下失败: {e}")
        event.ignore()
        
    def _show_context_menu(self, position):
        """显示右键菜单"""
        global_pos = self.mapToGlobal(position)
        self.parameter_context_menu.emit(self.param_name, self, global_pos)



class ToolOperationWidget(QWidget):
    tool_execution_requested = Signal(object, dict)
    
    def __init__(self):
        super().__init__()
        self.current_tool = None
        self.parameter_widgets = {}
        self.param_manager = None
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        

        info_frame = QFrame()
        info_frame.setProperty("class", "tool_info_frame")
        info_layout = QHBoxLayout(info_frame)
        

        self.tool_name_label = QLabel("请选择工具")
        self.tool_name_label.setProperty("class", "tool_name_label")
        info_layout.addWidget(self.tool_name_label)
        
        info_layout.addStretch()
        

        self.config_exec_button = QPushButton("配置执行文件")
        self.config_exec_button.setProperty("class", "config_exec_button")
        info_layout.addWidget(self.config_exec_button)
        
        layout.addWidget(info_frame)
        

        params_frame = QFrame()
        params_frame_layout = QVBoxLayout(params_frame)
        
        params_header = QLabel("参数配置")
        params_header.setProperty("class", "params_header")
        params_frame_layout.addWidget(params_header)
        

        search_layout = QHBoxLayout()
        self.param_search_edit = QLineEdit()
        self.param_search_edit.setPlaceholderText("搜索参数（支持参数名、参数介绍）...")
        self.param_search_edit.setProperty("class", "param_search")
        search_layout.addWidget(self.param_search_edit)
        
        self.clear_search_button = QPushButton("清除")
        self.clear_search_button.setProperty("class", "clear_search")
        search_layout.addWidget(self.clear_search_button)
        
        params_frame_layout.addLayout(search_layout)
        

        self.params_tab_widget = QTabWidget()
        self.params_tab_widget.setProperty("class", "params_tab")
        

        self.common_params_widget = QWidget()
        self.common_params_scroll = QScrollArea()
        self.common_params_scroll.setWidgetResizable(True)
        self.common_params_scroll.setWidget(self.common_params_widget)
        self.common_params_layout = QVBoxLayout(self.common_params_widget)
        self.params_tab_widget.addTab(self.common_params_scroll, "常用参数")
        

        self.all_params_widget = QWidget()
        self.all_params_scroll = QScrollArea()
        self.all_params_scroll.setWidgetResizable(True)
        self.all_params_scroll.setWidget(self.all_params_widget)
        self.all_params_layout = QVBoxLayout(self.all_params_widget)
        self.params_tab_widget.addTab(self.all_params_scroll, "全部参数")
        
        params_frame_layout.addWidget(self.params_tab_widget)
        

        command_layout = QHBoxLayout()
        command_layout.setContentsMargins(0, 5, 0, 5)
        command_layout.setSpacing(5)
        
        self.command_preview = QTextEdit()
        self.command_preview.setProperty("class", "command_preview")
        self.command_preview.setReadOnly(True)
        self.command_preview.setMaximumHeight(40)
        self.command_preview.setMinimumHeight(40)
        self.command_preview.setPlaceholderText("选择工具并配置参数后，这里将显示最终的命令行...")
        command_layout.addWidget(self.command_preview)
        

        self.copy_command_button = QPushButton("📋")
        self.copy_command_button.setProperty("class", "copy_command_button")
        self.copy_command_button.setEnabled(False)
        self.copy_command_button.setMaximumWidth(35)
        self.copy_command_button.setMaximumHeight(35)
        self.copy_command_button.setToolTip("复制命令到剪贴板")
        command_layout.addWidget(self.copy_command_button)
        
        params_frame_layout.addLayout(command_layout)
        layout.addWidget(params_frame)
        

        self.status_frame = QFrame()
        self.status_frame.setVisible(False)
        status_layout = QVBoxLayout(self.status_frame)
        
        self.status_label = QLabel("就绪")
        self.status_label.setProperty("class", "status_label")
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(self.status_frame)
        

        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        self.run_button = QPushButton("运行工具")
        self.run_button.setEnabled(False)
        self.run_button.setProperty("class", "run_button")
        button_layout.addWidget(self.run_button)
        
        self.reset_button = QPushButton("重置参数")
        self.reset_button.setEnabled(False)
        self.reset_button.setProperty("class", "reset_button")
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        

        self.template_save_button = QPushButton("💾 保存模板")
        self.template_save_button.setEnabled(False)
        self.template_save_button.setProperty("class", "template_save_button")
        button_layout.addWidget(self.template_save_button)
        
        self.template_load_button = QPushButton("📂 加载模板")
        self.template_load_button.setEnabled(False)
        self.template_load_button.setProperty("class", "template_load_button")
        button_layout.addWidget(self.template_load_button)
        
        self.template_manage_button = QPushButton("🛠️ 管理模板")
        self.template_manage_button.setEnabled(False)
        self.template_manage_button.setProperty("class", "template_manage_button")
        button_layout.addWidget(self.template_manage_button)
        
        layout.addWidget(button_frame)
        
    def connect_signals(self):
        self.run_button.clicked.connect(self.run_tool)
        self.reset_button.clicked.connect(self.reset_parameters)
        self.template_save_button.clicked.connect(self.save_template)
        self.template_load_button.clicked.connect(self.load_template)
        self.template_manage_button.clicked.connect(self.manage_templates)
        self.config_exec_button.clicked.connect(self.configure_executable)
        self.copy_command_button.clicked.connect(self.copy_command)
        

        self.param_search_edit.textChanged.connect(self.filter_parameters)
        self.clear_search_button.clicked.connect(self.clear_parameter_search)
        

        self.params_tab_widget.currentChanged.connect(self.on_tab_changed)
        
    def load_tool(self, tool_info):
        self.current_tool = tool_info
        self.tool_name_label.setText(tool_info.display_name)
        

        if not tool_info.has_required_files():
            self.config_exec_button.setText("⚠️ 缺少执行文件，请配置")
            self.config_exec_button.setProperty("status", "missing")
        else:
            self.config_exec_button.setText("✅ 执行文件已配置，点击重新配置")
            self.config_exec_button.setProperty("status", "configured")
        

        self.param_manager = ParameterManager(tool_info)
        

        self.clear_parameters()
        

        self.create_parameter_widgets()
        

        self.run_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.template_save_button.setEnabled(True)
        self.template_load_button.setEnabled(True)
        self.template_manage_button.setEnabled(True)
        self.copy_command_button.setEnabled(True)
        

        self.status_frame.setVisible(False)
        self._update_command_preview()
        
    def clear_parameters(self):
        for widget in self.parameter_widgets.values():
            widget.deleteLater()
        self.parameter_widgets.clear()
        

        while self.common_params_layout.count():
            child = self.common_params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                

        while self.all_params_layout.count():
            child = self.all_params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def create_parameter_widgets(self):
        if not self.current_tool:
            return
            

        self.param_manager = ParameterManager(self.current_tool)
        

        common_params = self.param_manager.get_common_parameters()
        all_params = self.param_manager.get_all_parameters()
        
        if not common_params and not all_params:
            self._show_no_params_message()
            return
            

        if all_params:
            self._create_params_section(all_params, self.all_params_layout, "全部参数")
        else:
            self._show_empty_section_message(self.all_params_layout, "无全部参数")
            

        if common_params:
            self._create_params_section(common_params, self.common_params_layout, "常用参数")
        else:
            self._show_empty_section_message(self.common_params_layout, "无常用参数")
            
        self.common_params_layout.addStretch()
        self.all_params_layout.addStretch()
        
    def _create_params_section(self, params, target_layout, section_name):
        """创建参数区域（使用新的分类逻辑）"""
        if not params:
            return
            

        checkbox_params = [p for p in params if p.get('type') == 'boolean']
        input_params = [p for p in params if p.get('type') != 'boolean']
        

        main_container = QWidget()
        main_layout = QHBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        

        if checkbox_params:
            checkbox_frame = self._create_checkbox_frame(checkbox_params, section_name)
            main_layout.addWidget(checkbox_frame, 0, Qt.AlignTop)
        

        if input_params:
            input_frame = self._create_input_frame(input_params, section_name)
            main_layout.addWidget(input_frame)
        
        target_layout.addWidget(main_container)
        
    def _create_checkbox_frame(self, checkbox_params, section_name):
        """创建勾选项框架"""
        checkbox_frame = QFrame()
        checkbox_frame.setProperty("class", "checkbox_frame")
        checkbox_frame.setAcceptDrops(True)
        
        checkbox_grid = QGridLayout(checkbox_frame)
        checkbox_grid.setContentsMargins(10, 10, 10, 10)
        checkbox_grid.setSpacing(10)
        checkbox_grid.setVerticalSpacing(5)
        
        for i, param in enumerate(checkbox_params):
            param_widget = self._create_parameter_widget(param, section_name)
            row = i // 2
            col = i % 2
            checkbox_grid.addWidget(param_widget, row, col)
        
        checkbox_grid.setRowStretch(checkbox_grid.rowCount(), 1)
        checkbox_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        return checkbox_frame
        
    def _create_input_frame(self, input_params, section_name):
        """创建输入项框架"""
        input_frame = QFrame()
        input_frame.setProperty("class", "input_frame")
        input_frame.setAcceptDrops(True)
        
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        for param in input_params:
            param_widget = self._create_parameter_widget(param, section_name)
            input_layout.addWidget(param_widget)
        
        return input_frame
        
    def _create_parameter_widget(self, param, section_name):
        """创建单个参数控件"""
        param_name = param['name']
        section_type = "common" if section_name == "常用参数" else "all"
        
        param_widget = ParameterWidget(param_name, param, section_type)
        param_widget.value_changed.connect(self.on_parameter_changed)
        param_widget.parameter_moved.connect(self.on_parameter_moved)
        param_widget.parameter_context_menu.connect(self.on_parameter_context_menu)
        

        widget_key = f"{section_type}_{param_name}"
        self.parameter_widgets[widget_key] = param_widget
            
        param_widget.update_validation_status()
        
        return param_widget
        
    def _show_no_params_message(self):
        """显示无参数消息"""
        for layout in [self.common_params_layout, self.all_params_layout]:
            label = QLabel("此工具无需配置参数")
            label.setAlignment(Qt.AlignCenter)
            label.setProperty("class", "no_params_label")
            layout.addWidget(label)
            
    def _show_empty_section_message(self, layout, message):
        """显示空区域消息"""
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        label.setProperty("class", "no_params_label")
        layout.addWidget(label)
    
    def on_tab_changed(self, index):
        """标签页切换时的处理"""

        self._update_command_preview()
    

        
    def on_parameter_changed(self, param_name, value):

        self._update_command_preview()
        
    def on_parameter_moved(self, param_name, from_section, to_section, target_param_name, insert_position):
        """处理参数拖拽移动（使用新的参数管理器）"""
        
        if from_section == to_section:

            self._handle_parameter_reorder(param_name, target_param_name, from_section, insert_position)
            return
            

        from_section_name = "常用参数" if from_section == "common" else "全部参数"
        to_section_name = "常用参数" if to_section == "common" else "全部参数"
        
        if from_section == "common" and to_section == "all":

            if self.param_manager.remove_parameter_from_section(param_name, from_section_name):
                self._reload_parameters()
                QMessageBox.information(self, "成功", f"参数 '{param_name}' 已从常用参数中移除")
            else:
                QMessageBox.warning(self, "失败", f"移除参数 '{param_name}' 失败")
        elif from_section == "all" and to_section == "common":

            if self.param_manager.copy_parameter_to_section(param_name, "全部参数", "常用参数"):
                self._reload_parameters()
                QMessageBox.information(self, "成功", f"参数 '{param_name}' 已复制到常用参数")
            else:
                QMessageBox.information(self, "提示", f"参数 '{param_name}' 已存在于常用参数中")
            
    def on_parameter_context_menu(self, param_name, widget, global_pos):
        """处理参数右键菜单"""
        menu = QMenu(self)
        

        param_config = widget.param_config
        is_in_common = widget.section_name == "common"
        is_required = param_config.get('required', False)
        

        if is_in_common:

            remove_action = QAction("从常用参数中删除", self)
            remove_action.triggered.connect(lambda: self._remove_from_common_params(param_name))
            menu.addAction(remove_action)
        else:

            add_action = QAction("复制到常用参数", self)
            add_action.triggered.connect(lambda: self._copy_to_common_params(param_name))
            menu.addAction(add_action)
            
        menu.addSeparator()
        

        type_menu = menu.addMenu("更换参数类型")
        if param_config.get('type') != 'boolean':
            to_checkbox_action = QAction("更改为勾选项", self)
            to_checkbox_action.triggered.connect(lambda: self._change_parameter_type(param_name, 'boolean'))
            type_menu.addAction(to_checkbox_action)
            
        if param_config.get('type') == 'boolean':
            to_input_action = QAction("更改为输入项", self)
            to_input_action.triggered.connect(lambda: self._change_parameter_type(param_name, 'string'))
            type_menu.addAction(to_input_action)
            
        menu.addSeparator()
        

        if is_required:
            optional_action = QAction("设置为可选项", self)
            optional_action.triggered.connect(lambda: self._set_parameter_required(param_name, False))
            menu.addAction(optional_action)
        else:
            required_action = QAction("设置为必填项", self)
            required_action.triggered.connect(lambda: self._set_parameter_required(param_name, True))
            menu.addAction(required_action)
            
        menu.addSeparator()
        

        edit_action = QAction("编辑参数信息", self)
        edit_action.triggered.connect(lambda: self._edit_parameter_info(param_name))
        menu.addAction(edit_action)
        

        menu.exec(global_pos)
        
            
    def _handle_parameter_reorder(self, param_name, target_param_name, section, insert_position):
        """处理同一区域内的参数重新排序（使用新的参数管理器）"""
        try:

            section_name = "常用参数" if section == "common" else "全部参数"
            

            if self.param_manager.reorder_parameter_in_section(param_name, target_param_name, section_name, insert_position):

                self._reload_parameters()
                QMessageBox.information(self, "成功", f"参数 '{param_name}' 已重新排序")
            else:
                QMessageBox.warning(self, "失败", f"重新排序参数 '{param_name}' 失败")
            
        except Exception as e:
            print(f"排序失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"重新排序失败: {str(e)}")
            
    def _copy_to_common_params(self, param_name):
        """将参数复制到常用参数（使用新的参数管理器）"""
        try:
            if self.param_manager.copy_parameter_to_section(param_name, "全部参数", "常用参数"):
                self._reload_parameters()
                QMessageBox.information(self, "成功", f"参数 '{param_name}' 已复制到常用参数")
            else:
                QMessageBox.information(self, "提示", f"参数 '{param_name}' 已存在于常用参数中，无需重复添加")
        except Exception as e:
            print(f"复制参数失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"复制参数失败: {str(e)}")
            
    def _remove_from_common_params(self, param_name):
        """从常用参数中删除参数（使用新的参数管理器）"""
        reply = QMessageBox.question(self, "确认删除", f"确定要从常用参数中删除 '{param_name}' 吗？")
        if reply == QMessageBox.Yes:
            try:
                if self.param_manager.remove_parameter_from_section(param_name, "常用参数"):
                    self._reload_parameters()
                    QMessageBox.information(self, "成功", f"参数 '{param_name}' 已从常用参数中删除")
                else:
                    QMessageBox.warning(self, "失败", f"删除参数 '{param_name}' 失败")
            except Exception as e:
                print(f"删除参数失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除参数失败: {str(e)}")
                
    def _change_parameter_type(self, param_name, new_type):
        """更改参数类型（使用新的参数管理器）"""
        try:

            reply = QMessageBox.question(self, "确认更改", 
                f"确定要将参数 '{param_name}' 的类型更改为 {'勾选项' if new_type == 'boolean' else '输入项'} 吗？")
            if reply == QMessageBox.Yes:

                if self.param_manager.change_parameter_type(param_name, new_type):

                    self._reload_parameters()
                    QMessageBox.information(self, "成功", f"参数 '{param_name}' 类型已更改")
                else:
                    QMessageBox.warning(self, "失败", f"更改参数 '{param_name}' 类型失败")
        except Exception as e:
            print(f"更改参数类型失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"更改参数类型失败: {str(e)}")
            
    def _set_parameter_required(self, param_name, required):
        """设置参数是否必填（使用新的参数管理器）"""
        try:
            status = "必填项" if required else "可选项"

            reply = QMessageBox.question(self, "确认更改", 
                f"确定要将参数 '{param_name}' 设置为 {status} 吗？")
            if reply == QMessageBox.Yes:

                if self.param_manager.set_parameter_required(param_name, required):

                    self._reload_parameters()
                    QMessageBox.information(self, "成功", f"参数 '{param_name}' 已设置为 {status}")
                else:
                    QMessageBox.warning(self, "失败", f"设置参数 '{param_name}' 状态失败")
        except Exception as e:
            print(f"设置参数状态失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"设置参数状态失败: {str(e)}")
            
    def _edit_parameter_info(self, param_name):
        """编辑参数信息（使用新的参数管理器）"""
        try:

            current_widget = self.parameter_widgets.get(param_name)
            if not current_widget:
                QMessageBox.warning(self, "错误", f"找不到参数 '{param_name}'")
                return
            
            param_config = current_widget.param_config
            current_display_name = param_config.get('display_name', param_name)
            current_description = param_config.get('description', '')
            

            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"编辑参数信息 - {param_name}")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            

            layout.addWidget(QLabel("显示名称:"))
            display_name_edit = QLineEdit(current_display_name)
            layout.addWidget(display_name_edit)
            

            layout.addWidget(QLabel("描述信息:"))
            description_edit = QTextEdit(current_description)
            description_edit.setMaximumHeight(120)
            layout.addWidget(description_edit)
            

            button_layout = QHBoxLayout()
            save_button = QPushButton("保存")
            cancel_button = QPushButton("取消")
            
            save_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_display_name = display_name_edit.text().strip()
                new_description = description_edit.toPlainText().strip()
                
                if not new_display_name:
                    QMessageBox.warning(dialog, "警告", "显示名称不能为空")
                    return
                

                if self.param_manager.update_parameter_info(param_name, new_display_name, new_description):

                    self._reload_parameters()
                    QMessageBox.information(self, "成功", f"参数 '{param_name}' 信息已更新")
                else:
                    QMessageBox.warning(self, "失败", f"更新参数 '{param_name}' 信息失败")
                    
        except Exception as e:
            print(f"编辑参数信息时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"编辑参数信息时发生错误: {str(e)}")
        
    def validate_parameters(self):
        if not self.current_tool:
            return False
            
        errors = []
        for param_name, widget in self.parameter_widgets.items():
            is_valid, error_msg = widget.validate()
            if not is_valid:
                errors.append(error_msg)
                
        if errors:
            error_text = "\n".join(errors)
            QMessageBox.warning(self, "参数验证失败", error_text)
            self.update_status("参数验证失败", "error")
            return False
        else:
            self.update_status("参数验证通过", "success")
            return True
            
    def run_tool(self):
        if not self.validate_parameters():
            return
            
        parameters = self.get_parameter_values()
        self._update_command_preview()
        
        self.tool_execution_requested.emit(self.current_tool, parameters)
        
    def reset_parameters(self):
        for widget in self.parameter_widgets.values():
            widget.set_default_value()
        self.update_status("参数已重置", "info")
        
    def update_status(self, message, status_type="info"):
        """更新状态显示
        Args:
            message: 状态消息
            status_type: 状态类型 - "success", "error", "warning", "info"
        """
        self.status_label.setText(message)

        self.status_label.setProperty("status", status_type)

        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        
    def _update_command_preview(self):
        """更新命令预览"""
        if not self.current_tool:
            self.command_preview.clear()
            self.copy_command_button.setEnabled(False)
            return
            
        try:

            command_parts = []
            
            if self.current_tool.executable == 'python':
                command_parts.append('python')
                command_parts.append(self.current_tool.script_path)
            else:
                command_parts.append(self.current_tool.executable)
                

            parameters = self.get_parameter_values()
            for param_name, value in parameters.items():
                if value is not None and value != '':
                    if isinstance(value, bool):
                        if value:
                            command_parts.append(param_name)
                    else:
                        command_parts.append(param_name)
                        command_parts.append(str(value))
                        
            command = ' '.join(command_parts)
            self.command_preview.setPlainText(command)
            self.copy_command_button.setEnabled(True)
            

            self.update_status(f"即将运行: {command}", "info")
        except Exception as e:
            self.command_preview.setPlainText("命令构建失败，请检查参数配置")
            self.copy_command_button.setEnabled(False)
            self.update_status("准备运行命令...", "info")
        
    def set_execution_finished(self):
        self.update_status("工具执行完成", "success")
        
    def set_execution_failed(self, error_msg):
        self.update_status(f"执行失败: {error_msg}", "error")
        
    def get_parameter_values(self):
        values = {}
        

        current_tab_index = self.params_tab_widget.currentIndex()
        current_tab_text = self.params_tab_widget.tabText(current_tab_index)
        
        if current_tab_text == "常用参数":

            for param_name, widget in self.parameter_widgets.items():
                if param_name.startswith('common_'):

                    original_param_name = param_name[7:]
                    values[original_param_name] = widget.get_value()
        else:

            for param_name, widget in self.parameter_widgets.items():
                if param_name.startswith('all_'):

                    original_param_name = param_name[4:]
                    values[original_param_name] = widget.get_value()
        
        return values
        
    def save_template(self):
        """保存参数模板"""
        if not self.current_tool:
            return
            
        from PySide6.QtWidgets import QInputDialog
        import json
        import time
        from pathlib import Path
        

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("保存模板")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("模板名称:"))
        name_edit = QLineEdit(f"{self.current_tool.name}_模板")
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        

        layout.addWidget(QLabel("模板备注:"))
        remark_edit = QTextEdit()
        remark_edit.setPlaceholderText("请输入模板的用途说明、注意事项等备注信息...")
        remark_edit.setMaximumHeight(120)
        layout.addWidget(remark_edit)
        

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("保存")
        save_button.clicked.connect(lambda: self._save_template_with_data(dialog, name_edit.text().strip(), remark_edit.toPlainText().strip()))
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
        
    def _create_interpreter_tab(self):
        """创建解释器配置标签页"""
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
            QComboBox, QListWidget, QGroupBox, QGridLayout, QTextEdit
        )
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        

        interpreter_group = QGroupBox("解释器配置")
        interpreter_layout = QGridLayout(interpreter_group)
        

        interpreter_layout.addWidget(QLabel("解释器类型:"), 0, 0)
        self.interpreter_type_combo = QComboBox()
        self.interpreter_type_combo.addItems(["python", "java", "其他"])
        self.interpreter_type_combo.currentTextChanged.connect(self._on_interpreter_type_changed)
        interpreter_layout.addWidget(self.interpreter_type_combo, 0, 1, 1, 2)
        

        interpreter_layout.addWidget(QLabel("解释器路径:"), 1, 0)
        self.interpreter_path_edit = QLineEdit()
        self.interpreter_path_edit.setPlaceholderText("解释器可执行文件路径（可选）")
        interpreter_layout.addWidget(self.interpreter_path_edit, 1, 1)
        
        self.browse_interpreter_button = QPushButton("浏览")
        self.browse_interpreter_button.clicked.connect(self._browse_interpreter_path)
        interpreter_layout.addWidget(self.browse_interpreter_button, 1, 2)
        

        interpreter_layout.addWidget(QLabel("程序路径:"), 2, 0)
        self.program_path_edit = QLineEdit()
        self.program_path_edit.setPlaceholderText("程序文件路径")
        interpreter_layout.addWidget(self.program_path_edit, 2, 1)
        
        self.browse_program_button = QPushButton("浏览")
        self.browse_program_button.clicked.connect(self._browse_program_path)
        interpreter_layout.addWidget(self.browse_program_button, 2, 2)
        

        buttons_layout = QHBoxLayout()
        
        scan_button = QPushButton("🔍 扫描解释器")
        scan_button.clicked.connect(self._scan_interpreters)
        buttons_layout.addWidget(scan_button)
        
        test_button = QPushButton("🧪 测试配置")
        test_button.clicked.connect(self._test_interpreter_config)
        buttons_layout.addWidget(test_button)
        
        interpreter_layout.addLayout(buttons_layout, 3, 0, 1, 3)
        
        layout.addWidget(interpreter_group)
        

        history_group = QGroupBox("最近使用的解释器")
        history_layout = QVBoxLayout(history_group)
        
        self.interpreter_history_list = QListWidget()
        self.interpreter_history_list.itemDoubleClicked.connect(self._load_interpreter_from_history)
        history_layout.addWidget(self.interpreter_history_list)
        
        history_buttons_layout = QHBoxLayout()
        add_to_history_button = QPushButton("➕ 添加到历史")
        add_to_history_button.clicked.connect(self._add_interpreter_to_history)
        history_buttons_layout.addWidget(add_to_history_button)
        
        remove_from_history_button = QPushButton("➖ 从历史移除")
        remove_from_history_button.clicked.connect(self._remove_interpreter_from_history)
        history_buttons_layout.addWidget(remove_from_history_button)
        
        history_layout.addLayout(history_buttons_layout)
        layout.addWidget(history_group)
        
        layout.addStretch()
        return widget
        
    def _create_environment_tab(self):
        """创建环境管理标签页"""
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
            QComboBox, QListWidget, QGroupBox, QTextEdit, QCheckBox
        )
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        

        info_label = QLabel(f"当前工具: {self.current_tool.display_name if self.current_tool else '未选择'}")
        info_label.setProperty("class", "tool_info_label")
        layout.addWidget(info_label)
        

        env_group = QGroupBox("虚拟环境配置")
        env_layout = QVBoxLayout(env_group)
        

        env_select_layout = QHBoxLayout()
        env_select_layout.addWidget(QLabel("选择环境:"))
        
        self.env_combo = QComboBox()
        self.env_combo.currentTextChanged.connect(self._on_env_selected)
        env_select_layout.addWidget(self.env_combo)
        

        refresh_env_button = QPushButton("🔄 刷新")
        refresh_env_button.clicked.connect(self._load_all_environments)
        env_select_layout.addWidget(refresh_env_button)
        
        env_layout.addLayout(env_select_layout)
        

        env_path_layout = QHBoxLayout()
        env_path_layout.addWidget(QLabel("环境路径:"))
        
        self.env_path_edit = QLineEdit()
        self.env_path_edit.setReadOnly(True)
        self.env_path_edit.setPlaceholderText("选择环境后自动显示路径")
        env_path_layout.addWidget(self.env_path_edit)
        
        self.browse_env_button = QPushButton("浏览自定义")
        self.browse_env_button.clicked.connect(self._browse_custom_env)
        env_path_layout.addWidget(self.browse_env_button)
        
        env_layout.addLayout(env_path_layout)
        

        self._load_all_environments()
        

        env_buttons_layout = QHBoxLayout()
        
        detect_env_button = QPushButton("🔍 自动检测环境")
        detect_env_button.clicked.connect(self._detect_environments)
        env_buttons_layout.addWidget(detect_env_button)
        
        test_env_button = QPushButton("🧪 测试环境")
        test_env_button.clicked.connect(self._test_environment)
        env_buttons_layout.addWidget(test_env_button)
        
        env_buttons_layout.addStretch()
        env_layout.addLayout(env_buttons_layout)
        
        layout.addWidget(env_group)
        

        env_vars_group = QGroupBox("环境变量设置")
        env_vars_layout = QVBoxLayout(env_vars_group)
        
        env_vars_info = QLabel("为当前工具设置专用环境变量（仅在运行此工具时生效）")
        env_vars_info.setProperty("class", "env_vars_info")
        env_vars_layout.addWidget(env_vars_info)
        
        self.env_vars_text = QTextEdit()
        self.env_vars_text.setPlaceholderText("每行一个环境变量，格式: KEY=VALUE\n例如:\nPATH=/usr/local/bin\nPYTHONPATH=/path/to/modules")
        self.env_vars_text.setMaximumHeight(120)
        env_vars_layout.addWidget(self.env_vars_text)
        

        common_vars_layout = QHBoxLayout()
        
        add_env_var_button = QPushButton("+ 快捷创建 KEY=VALUE")
        add_env_var_button.clicked.connect(self._add_custom_env_var)
        common_vars_layout.addWidget(add_env_var_button)
        
        clear_env_vars_button = QPushButton("🗑️ 清空")
        clear_env_vars_button.clicked.connect(lambda: self.env_vars_text.clear())
        common_vars_layout.addWidget(clear_env_vars_button)
        
        common_vars_layout.addStretch()
        env_vars_layout.addLayout(common_vars_layout)
        
        layout.addWidget(env_vars_group)
        
        layout.addStretch()
        return widget
        
    def _create_default_params_tab(self):
        """创建默认参数标签页"""
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
            QScrollArea, QGroupBox, QTextEdit, QCheckBox
        )
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        

        params_group = QGroupBox("默认参数配置")
        params_layout = QVBoxLayout(params_group)
        

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.default_params_widget = QWidget()
        self.default_params_layout = QVBoxLayout(self.default_params_widget)
        
        scroll_area.setWidget(self.default_params_widget)
        params_layout.addWidget(scroll_area)
        

        params_buttons_layout = QHBoxLayout()
        
        load_current_button = QPushButton("📥 加载当前参数")
        load_current_button.clicked.connect(self._load_current_params_as_default)
        params_buttons_layout.addWidget(load_current_button)
        
        clear_defaults_button = QPushButton("🗑️ 清除默认值")
        clear_defaults_button.clicked.connect(self._clear_default_params)
        params_buttons_layout.addWidget(clear_defaults_button)
        
        params_buttons_layout.addStretch()
        params_layout.addLayout(params_buttons_layout)
        
        layout.addWidget(params_group)
        

        template_group = QGroupBox("参数模板")
        template_layout = QVBoxLayout(template_group)
        
        template_buttons_layout = QHBoxLayout()
        
        save_template_button = QPushButton("💾 保存为模板")
        save_template_button.clicked.connect(self._save_params_template)
        template_buttons_layout.addWidget(save_template_button)
        
        load_template_button = QPushButton("📂 加载模板")
        load_template_button.clicked.connect(self._load_params_template)
        template_buttons_layout.addWidget(load_template_button)
        
        template_layout.addLayout(template_buttons_layout)
        layout.addWidget(template_group)
        
        layout.addStretch()
        return widget
        
    def _create_workdir_tab(self):
        """创建工作目录标签页"""
        from PySide6.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
            QGroupBox, QCheckBox, QListWidget
        )
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        

        workdir_group = QGroupBox("工作目录配置")
        workdir_layout = QVBoxLayout(workdir_group)
        

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("工作目录:"))
        
        self.workdir_edit = QLineEdit()
        dir_layout.addWidget(self.workdir_edit)
        
        browse_workdir_button = QPushButton("浏览")
        browse_workdir_button.clicked.connect(self._browse_workdir)
        dir_layout.addWidget(browse_workdir_button)
        
        workdir_layout.addLayout(dir_layout)
        

        self.use_tool_dir_checkbox = QCheckBox("使用工具所在目录作为工作目录")
        workdir_layout.addWidget(self.use_tool_dir_checkbox)
        
        self.create_output_dir_checkbox = QCheckBox("自动创建输出目录")
        workdir_layout.addWidget(self.create_output_dir_checkbox)
        
        layout.addWidget(workdir_group)
        

        common_dirs_group = QGroupBox("常用工作目录")
        common_dirs_layout = QVBoxLayout(common_dirs_group)
        
        self.common_dirs_list = QListWidget()
        self.common_dirs_list.itemDoubleClicked.connect(self._load_common_dir)
        common_dirs_layout.addWidget(self.common_dirs_list)
        
        dirs_buttons_layout = QHBoxLayout()
        
        add_current_dir_button = QPushButton("➕ 添加当前目录")
        add_current_dir_button.clicked.connect(self._add_current_dir_to_common)
        dirs_buttons_layout.addWidget(add_current_dir_button)
        
        remove_dir_button = QPushButton("➖ 移除选中目录")
        remove_dir_button.clicked.connect(self._remove_common_dir)
        dirs_buttons_layout.addWidget(remove_dir_button)
        
        common_dirs_layout.addLayout(dirs_buttons_layout)
        layout.addWidget(common_dirs_group)
        
        layout.addStretch()
        return widget
        

    def _on_interpreter_type_changed(self, interpreter_type):
        """解释器类型改变时的处理"""
        if interpreter_type == "python":
            import sys
            self.interpreter_path_edit.setText(sys.executable)
            self.interpreter_path_edit.setPlaceholderText("Python解释器路径")
            self.program_path_edit.setPlaceholderText("Python脚本文件路径 (.py)")
            self.browse_interpreter_button.setEnabled(True)
        elif interpreter_type == "java":
            java_path = self._find_java_executable()
            if java_path:
                self.interpreter_path_edit.setText(java_path)
            else:
                self.interpreter_path_edit.clear()
            self.interpreter_path_edit.setPlaceholderText("Java解释器路径 (java.exe)")
            self.program_path_edit.setPlaceholderText("Java程序文件路径 (.jar)")
            self.browse_interpreter_button.setEnabled(True)
        else:
            self.interpreter_path_edit.clear()
            self.interpreter_path_edit.setPlaceholderText("解释器路径（可选）")
            self.program_path_edit.setPlaceholderText("程序文件路径")
            self.browse_interpreter_button.setEnabled(True)
            
    def _browse_interpreter_path(self):
        """浏览解释器路径"""
        from PySide6.QtWidgets import QFileDialog
        
        interpreter_type = self.interpreter_type_combo.currentText()
        
        if interpreter_type == "java":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择Java可执行文件", "", "Java可执行文件 (java.exe);;可执行文件 (*.exe);;所有文件 (*.*)"
            )
        elif interpreter_type == "其他":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择解释器可执行文件", "", "可执行文件 (*.exe);;批处理文件 (*.bat);;所有文件 (*.*)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择Python解释器", "", "Python可执行文件 (python.exe);;可执行文件 (*.exe);;所有文件 (*.*)"
            )
        
        if file_path:
            self.interpreter_path_edit.setText(file_path)
            
    def _browse_program_path(self):
        """浏览程序路径"""
        from PySide6.QtWidgets import QFileDialog
        
        interpreter_type = self.interpreter_type_combo.currentText()
        

        start_dir = self.current_tool.path if self.current_tool else ""
        
        if interpreter_type == "java":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择Java程序文件", start_dir, "Java文件 (*.jar *.class *.java);;JAR文件 (*.jar);;Class文件 (*.class);;Java源文件 (*.java);;所有文件 (*.*)"
            )
        elif interpreter_type == "其他":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择程序文件", start_dir, "所有文件 (*.*);;脚本文件 (*.js *.rb *.php *.pl *.go *.sh *.bat);;可执行文件 (*.exe)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择Python脚本文件", start_dir, "Python文件 (*.py);;所有文件 (*.*)"
            )
        
        if file_path:

            if self.current_tool:
                from pathlib import Path
                tool_path = Path(self.current_tool.path)
                file_path_obj = Path(file_path)
                try:
                    rel_path = file_path_obj.relative_to(tool_path)
                    self.program_path_edit.setText(str(rel_path))
                except ValueError:

                    self.program_path_edit.setText(file_path)
            else:
                self.program_path_edit.setText(file_path)
            
    def _test_interpreter_config(self):
        """测试解释器配置"""
        from PySide6.QtWidgets import QMessageBox
        import subprocess
        import os
        
        interpreter_path = self.interpreter_path_edit.text().strip()
        program_path = self.program_path_edit.text().strip()
        interpreter_type = self.interpreter_type_combo.currentText()
        
        if not interpreter_path:
            QMessageBox.warning(self, "警告", "请先设置解释器路径")
            return
            
        if not os.path.exists(interpreter_path):
            QMessageBox.warning(self, "警告", "解释器路径不存在")
            return
            
        try:

            if interpreter_type == "java":

                result = subprocess.run([interpreter_path, "-version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stderr.strip()
                    message = f"Java版本: {version_info}"
                    

                    if program_path and os.path.exists(program_path):
                        if program_path.endswith('.jar'):
                            test_result = subprocess.run([interpreter_path, "-jar", program_path, "--help"], 
                                                        capture_output=True, text=True, timeout=10)
                        elif program_path.endswith('.class'):

                            class_dir = os.path.dirname(program_path)
                            class_name = os.path.splitext(os.path.basename(program_path))[0]
                            test_result = subprocess.run([interpreter_path, "-cp", class_dir, class_name], 
                                                        capture_output=True, text=True, timeout=10)
                        else:
                            message += "\n注意: Java源文件需要先编译"
                            
                    QMessageBox.information(self, "测试成功", message)
                else:
                    QMessageBox.warning(self, "测试失败", f"错误: {result.stderr}")
                    
            elif interpreter_type == "其他":

                if interpreter_path:

                    version_commands = ["--version", "-v", "-version", "version"]
                    version_info = "未知版本"
                    
                    for cmd in version_commands:
                        try:
                            result = subprocess.run([interpreter_path, cmd], 
                                                  capture_output=True, text=True, timeout=10)
                            if result.returncode == 0 and result.stdout.strip():
                                version_info = result.stdout.strip()
                                break
                        except:
                            continue
                    
                    message = f"解释器测试成功\n版本信息: {version_info}"
                    

                    if program_path and os.path.exists(program_path):
                        try:
                            test_result = subprocess.run([interpreter_path, program_path, "--help"], 
                                                        capture_output=True, text=True, timeout=10)
                            message += "\n程序路径有效"
                        except:
                            message += "\n注意: 无法测试程序执行"
                else:

                    if program_path and os.path.exists(program_path):
                        try:
                            test_result = subprocess.run([program_path, "--help"], 
                                                        capture_output=True, text=True, timeout=10)
                            message = "程序文件测试成功"
                        except:
                            message = "程序文件存在但无法执行测试"
                    else:
                        QMessageBox.warning(self, "警告", "请设置程序路径")
                        return
                        
                QMessageBox.information(self, "测试成功", message)
                
            else:

                result = subprocess.run([interpreter_path, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    message = f"Python版本: {version_info}"
                    

                    if program_path and os.path.exists(program_path):
                        try:
                            test_result = subprocess.run([interpreter_path, program_path, "--help"], 
                                                        capture_output=True, text=True, timeout=10)
                            message += "\n程序路径有效"
                        except:
                            message += "\n注意: 无法测试程序执行"
                            
                    QMessageBox.information(self, "测试成功", message)
                else:
                    QMessageBox.warning(self, "测试失败", f"错误: {result.stderr}")
                    
        except Exception as e:
            QMessageBox.critical(self, "测试失败", f"无法执行解释器: {str(e)}")
            
    def _load_interpreter_from_history(self, item):
        """从历史记录加载解释器"""
        interpreter_info = item.data(32)
        if interpreter_info:
            self.interpreter_path_edit.setText(interpreter_info.get('python_path', ''))
            self.program_path_edit.setText(interpreter_info.get('script_path', ''))
            
    def _add_interpreter_to_history(self):
        """添加当前解释器到历史记录"""
        from PySide6.QtWidgets import QListWidgetItem, QMessageBox
        
        interpreter_path = self.interpreter_path_edit.text().strip()
        program_path = self.program_path_edit.text().strip()
        
        if not interpreter_path and not program_path:
            QMessageBox.warning(self, "警告", "请先设置解释器路径或程序路径")
            return
            
        interpreter_info = {
            'python_path': interpreter_path,
            'script_path': program_path,
            'type': self.interpreter_type_combo.currentText()
        }
        
        display_text = f"{interpreter_info['type']}: {interpreter_path or program_path}"
        item = QListWidgetItem(display_text)
        item.setData(32, interpreter_info)
        self.interpreter_history_list.addItem(item)
        
    def _remove_interpreter_from_history(self):
        """从历史记录移除解释器"""
        current_item = self.interpreter_history_list.currentItem()
        if current_item:
            self.interpreter_history_list.takeItem(self.interpreter_history_list.row(current_item))
            
    def _scan_interpreters(self):
        """扫描系统中的解释器"""
        from PySide6.QtWidgets import QProgressDialog, QMessageBox
        import subprocess
        import os
        import sys
        from pathlib import Path
        

        progress = QProgressDialog("正在扫描解释器...", "取消", 0, 100, self)
        progress.setWindowTitle("扫描解释器")
        progress.setModal(True)
        progress.show()
        
        found_interpreters = []
        
        try:

            progress.setLabelText("正在扫描Python解释器...")
            progress.setValue(10)
            

            if sys.executable:
                found_interpreters.append({
                    'type': '系统Python',
                    'path': sys.executable,
                    'version': self._get_interpreter_version(sys.executable)
                })
            

            common_python_paths = [
                r"C:\Python*\python.exe",
                r"C:\Program Files\Python*\python.exe",
                r"C:\Program Files (x86)\Python*\python.exe",
                os.path.expanduser("~\\AppData\\Local\\Programs\\Python\\Python*\\python.exe")
            ]
            
            import glob
            for pattern in common_python_paths:
                for path in glob.glob(pattern):
                    if os.path.exists(path) and path not in [i['path'] for i in found_interpreters]:
                        found_interpreters.append({
                            'type': '自定义路径',
                            'path': path,
                            'version': self._get_interpreter_version(path)
                        })
            
            progress.setValue(40)
            

            progress.setLabelText("正在扫描Java...")
            java_path = self._find_java_executable()
            if java_path:
                found_interpreters.append({
                    'type': 'Java',
                    'path': java_path,
                    'version': self._get_interpreter_version(java_path, ['-version'])
                })
            
            progress.setValue(60)
            

            progress.setLabelText("正在扫描其他解释器...")
            other_interpreters = {
                'Node.js': ['node', 'node.exe'],
                'Ruby': ['ruby', 'ruby.exe'],
                'PHP': ['php', 'php.exe'],
                'Perl': ['perl', 'perl.exe'],
                'Go': ['go', 'go.exe']
            }
            
            for name, executables in other_interpreters.items():
                for exe in executables:
                    path = self._find_executable_in_path(exe)
                    if path:
                        found_interpreters.append({
                            'type': '其他可执行文件',
                            'path': path,
                            'version': f"{name} - {self._get_interpreter_version(path, ['--version'])}"
                        })
                        break
            
            progress.setValue(90)
            

            progress.setLabelText("正在添加到历史记录...")
            for interpreter in found_interpreters:

                exists = False
                for i in range(self.interpreter_history_list.count()):
                    item = self.interpreter_history_list.item(i)
                    if item.data(32) and item.data(32).get('python_path') == interpreter['path']:
                        exists = True
                        break
                
                if not exists:
                    from PySide6.QtWidgets import QListWidgetItem
                    interpreter_info = {
                        'python_path': interpreter['path'],
                        'script_path': '',
                        'type': interpreter['type']
                    }
                    
                    display_text = f"{interpreter['type']}: {interpreter['path']} ({interpreter['version']})"
                    item = QListWidgetItem(display_text)
                    item.setData(32, interpreter_info)
                    self.interpreter_history_list.addItem(item)
            
            progress.setValue(100)
            progress.close()
            
            if found_interpreters:
                QMessageBox.information(self, "扫描完成", f"找到 {len(found_interpreters)} 个解释器，已添加到历史记录")
            else:
                QMessageBox.warning(self, "扫描完成", "未找到任何解释器")
                
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "扫描失败", f"扫描解释器时出错: {str(e)}")
    
    def _get_interpreter_version(self, path, args=['--version']):
        """获取解释器版本信息"""
        try:
            result = subprocess.run([path] + args, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip() or result.stderr.strip()
            else:
                return result.stderr.strip() or "未知版本"
        except:
            return "未知版本"
    
    def _find_java_executable(self):
        """查找Java可执行文件"""

        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            java_exe = os.path.join(java_home, 'bin', 'java.exe')
            if os.path.exists(java_exe):
                return java_exe
        

        return self._find_executable_in_path('java.exe') or self._find_executable_in_path('java')
    
    def _find_executable_in_path(self, executable):
        """在PATH中查找可执行文件"""
        import shutil
        return shutil.which(executable)
            

    def _load_all_environments(self):
        """加载所有可用环境"""
        self.env_combo.clear()
        

        self.env_combo.addItem("系统默认 Python", {"type": "system", "path": "python"})
        

        self._add_conda_environments()
        

        self._add_virtual_environments()
        

        self.env_combo.addItem("浏览自定义路径...", {"type": "custom", "path": ""})
    
    def _add_conda_environments(self):
        """添加Conda环境到下拉列表"""
        try:
            import subprocess
            result = subprocess.run(['conda', 'env', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if parts and len(parts) >= 2:
                            env_name = parts[0]
                            env_path = parts[-1] if len(parts) > 1 else ""
                            if env_name != 'base' and env_path:
                                display_name = f"Conda: {env_name}"
                                self.env_combo.addItem(display_name, {"type": "conda", "name": env_name, "path": env_path})
        except Exception:
            pass
    
    def _add_virtual_environments(self):
        """添加虚拟环境到下拉列表"""
        try:
            from .virtual_env import VirtualEnvManager
            manager = VirtualEnvManager()
            environments = manager.load_environments()
            
            for env in environments:
                if os.path.exists(env.path):
                    display_name = f"虚拟环境: {env.name}"
                    self.env_combo.addItem(display_name, {"type": "venv", "name": env.name, "path": env.path})
        except Exception as e:
            print(f"加载虚拟环境失败: {e}")
    
    def _on_env_selected(self, env_name):
        """环境选择改变时的处理"""
        current_index = self.env_combo.currentIndex()
        if current_index >= 0:
            env_data = self.env_combo.itemData(current_index)
            if env_data:
                if env_data["type"] == "system":
                    self.env_path_edit.setText("系统默认 Python")
                elif env_data["type"] == "conda":
                    self.env_path_edit.setText(f"Conda环境: {env_data['name']} ({env_data['path']})")
                elif env_data["type"] == "venv":
                    self.env_path_edit.setText(env_data["path"])
                elif env_data["type"] == "custom":
                    self._browse_custom_env()
    
    def _browse_custom_env(self):
        """浏览自定义环境路径"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import os
        

        reply = QMessageBox.question(
            self, "选择类型", 
            "请选择要添加的环境类型：\n\n点击 'Yes' 选择虚拟环境目录\n点击 'No' 选择Python解释器文件",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:

            dir_path = QFileDialog.getExistingDirectory(
                self, "选择虚拟环境目录", 
                os.path.expanduser("~")
            )
            if dir_path:

                import platform
                if platform.system() == "Windows":
                    python_exe = os.path.join(dir_path, 'Scripts', 'python.exe')
                else:
                    python_exe = os.path.join(dir_path, 'bin', 'python')
                
                if os.path.exists(python_exe):
                    self.env_path_edit.setText(dir_path)

                    env_name = os.path.basename(dir_path)
                    display_name = f"自定义虚拟环境: {env_name}"
                    self.env_combo.addItem(display_name, {"type": "custom_venv", "name": env_name, "path": dir_path})
                    self.env_combo.setCurrentText(display_name)
                else:
                    QMessageBox.warning(self, "错误", "选择的目录不是有效的虚拟环境目录")
        elif reply == QMessageBox.No:

            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择Python解释器", 
                os.path.expanduser("~"),
                "Python解释器 (python.exe python);;所有文件 (*.*)"
            )
            if file_path:
                self.env_path_edit.setText(file_path)

                env_name = os.path.basename(file_path)
                display_name = f"自定义解释器: {env_name}"
                self.env_combo.addItem(display_name, {"type": "custom_python", "name": env_name, "path": file_path})
                self.env_combo.setCurrentText(display_name)
                    
    def _detect_environments(self):
        """自动检测可用环境"""
        from PySide6.QtWidgets import QMessageBox
        import subprocess
        import os
        import platform
        
        detected_envs = []
        

        try:
            result = subprocess.run(['conda', 'env', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                conda_envs = []
                for line in lines:
                    if line and not line.startswith('#') and '*' not in line:
                        parts = line.split()
                        if parts and parts[0] != 'base':
                            conda_envs.append(parts[0])
                if conda_envs:
                    detected_envs.append(f"Conda环境: {', '.join(conda_envs)}")
        except Exception:
            pass
        

        venv_dirs = [
            os.path.expanduser('~/.virtualenvs'),
            os.path.expanduser('~/venvs'),
            os.path.expanduser('~/envs'),
            os.path.expanduser('~/Envs'),
            os.path.expanduser('~/.wct_venvs'),
        ]
        

        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        wct_venv_dir = os.path.join(app_dir, "config", "venvs")
        if os.path.exists(wct_venv_dir):
            venv_dirs.append(wct_venv_dir)
        
        found_venvs = []
        for venv_dir in venv_dirs:
            if os.path.exists(venv_dir):
                try:
                    for item in os.listdir(venv_dir):
                        item_path = os.path.join(venv_dir, item)
                        if os.path.isdir(item_path):

                            is_venv = False
                            if platform.system() == "Windows":
                                is_venv = os.path.exists(os.path.join(item_path, 'Scripts', 'python.exe'))
                            else:
                                is_venv = os.path.exists(os.path.join(item_path, 'bin', 'python'))
                            
                            if is_venv:
                                found_venvs.append(f"{item} ({venv_dir})")
                except Exception:
                    pass
        
        if found_venvs:
            detected_envs.append(f"虚拟环境: {', '.join(found_venvs)}")
        

        if detected_envs:
            message = "检测到以下环境:\n\n" + "\n".join(detected_envs)
            message += "\n\n请在上方选择相应的环境类型并配置路径。"
        else:
            message = "未检测到Conda或虚拟环境。\n\n您可以：\n1. 使用系统默认环境\n2. 手动指定自定义路径"
        
        QMessageBox.information(self, "环境检测结果", message)
            
    def _test_environment(self):
        """测试当前配置的环境"""
        from PySide6.QtWidgets import QMessageBox
        import subprocess
        import os
        import platform
        
        current_index = self.env_combo.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "错误", "请先选择一个环境")
            return
            
        env_data = self.env_combo.itemData(current_index)
        if not env_data:
            QMessageBox.warning(self, "错误", "无效的环境选择")
            return
        
        python_path = None
        env_type = env_data["type"]
        
        try:
            if env_type == "system":
                python_path = "python"
            elif env_type == "conda":
                env_name = env_data["name"]

                result = subprocess.run(['conda', 'run', '-n', env_name, 'python', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    QMessageBox.information(self, "环境测试成功", 
                                          f"Conda环境 '{env_name}' 可用\n{version_info}")
                    return
                else:
                    QMessageBox.warning(self, "环境测试失败", 
                                      f"Conda环境 '{env_name}' 不可用\n{result.stderr}")
                    return
            elif env_type in ["venv", "custom_venv"]:
                env_path = env_data["path"]
                if not os.path.exists(env_path):
                    QMessageBox.warning(self, "错误", "虚拟环境路径不存在")
                    return

                if platform.system() == "Windows":
                    python_path = os.path.join(env_path, 'Scripts', 'python.exe')
                else:
                    python_path = os.path.join(env_path, 'bin', 'python')
            elif env_type == "custom_python":
                python_path = env_data["path"]
                if not os.path.exists(python_path):
                    QMessageBox.warning(self, "错误", "Python解释器路径不存在")
                    return
            

            if python_path:
                result = subprocess.run([python_path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    QMessageBox.information(self, "环境测试成功", 
                                          f"Python解释器可用\n{version_info}\n路径: {python_path}")
                else:
                    QMessageBox.warning(self, "环境测试失败", 
                                      f"Python解释器不可用\n{result.stderr}")
        
        except subprocess.TimeoutExpired:
            QMessageBox.warning(self, "环境测试失败", "测试超时，请检查环境配置")
        except Exception as e:
            QMessageBox.warning(self, "环境测试失败", f"测试过程中出现错误: {str(e)}")
    

        
    def _add_custom_env_var(self):
        """添加自定义环境变量"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("创建环境变量")
        dialog.setModal(True)
        dialog.resize(400, 150)
        
        layout = QVBoxLayout(dialog)
        

        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("变量名(KEY):"))
        key_edit = QLineEdit()
        key_edit.setPlaceholderText("例如: PATH, PYTHONPATH, JAVA_HOME")
        key_layout.addWidget(key_edit)
        layout.addLayout(key_layout)
        

        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("变量值(VALUE):"))
        value_edit = QLineEdit()
        value_edit.setPlaceholderText("例如: /usr/local/bin, C:\\Python39")
        value_layout.addWidget(value_edit)
        layout.addLayout(value_layout)
        

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            key = key_edit.text().strip()
            value = value_edit.text().strip()
            
            if not key:
                QMessageBox.warning(self, "警告", "请输入变量名")
                return
                
            if not value:
                QMessageBox.warning(self, "警告", "请输入变量值")
                return
                
            current_text = self.env_vars_text.toPlainText()
            new_line = f"{key}={value}"
            if current_text:
                self.env_vars_text.setPlainText(current_text + "\n" + new_line)
            else:
                self.env_vars_text.setPlainText(new_line)
                

    def _load_current_params_as_default(self):
        """加载当前参数作为默认值"""

        for i in reversed(range(self.default_params_layout.count())):
            child = self.default_params_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                

        for param_name, widget in self.parameter_widgets.items():
            param_value = widget.get_value()
            

            from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
            
            param_widget = QWidget()
            param_layout = QHBoxLayout(param_widget)
            
            label = QLabel(f"{param_name}:")
            param_layout.addWidget(label)
            

            default_widget = self._create_default_param_widget(widget, param_value)
            param_layout.addWidget(default_widget)
            
            self.default_params_layout.addWidget(param_widget)
            
    def _create_default_param_widget(self, original_widget, current_value):
        """根据原始控件创建默认参数控件"""
        from PySide6.QtWidgets import QLineEdit, QCheckBox, QComboBox
        
        if hasattr(original_widget, 'checkbox'):
            widget = QCheckBox()
            widget.setChecked(current_value)
            return widget
        elif hasattr(original_widget, 'combo'):
            widget = QComboBox()
            widget.addItems(original_widget.combo.items())
            widget.setCurrentText(str(current_value))
            return widget
        else:
            widget = QLineEdit()
            widget.setText(str(current_value))
            return widget
            
    def _clear_default_params(self):
        """清除默认参数"""
        for i in reversed(range(self.default_params_layout.count())):
            child = self.default_params_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                
    def _save_params_template(self):
        """保存参数模板"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        
        template_name, ok = QInputDialog.getText(self, "保存模板", "模板名称:")
        if not ok or not template_name.strip():
            return
            

        params = {}
        for param_name, widget in self.parameter_widgets.items():
            params[param_name] = widget.get_value()
            

        try:
            config_manager = self.parent().parent().config_manager
            if not hasattr(config_manager.config, 'param_templates'):
                config_manager.config['param_templates'] = {}
                
            config_manager.config['param_templates'][template_name] = {
                'tool_name': self.current_tool['name'] if self.current_tool else '',
                'params': params,
                'created_time': str(datetime.now())
            }
            
            config_manager.save_config()
            QMessageBox.information(self, "成功", f"参数模板 '{template_name}' 保存成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存模板失败: {str(e)}")
            
    def _load_params_template(self):
        """加载参数模板"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QMessageBox
        
        try:
            config_manager = self.parent().parent().config_manager
            templates = config_manager.config.get('param_templates', {})
            
            if not templates:
                QMessageBox.information(self, "提示", "没有保存的参数模板")
                return
                

            dialog = QDialog(self)
            dialog.setWindowTitle("选择参数模板")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            template_list = QListWidget()
            for template_name, template_data in templates.items():
                tool_name = template_data.get('tool_name', '')
                created_time = template_data.get('created_time', '')
                display_text = f"{template_name} ({tool_name}) - {created_time}"
                template_list.addItem(display_text)
                
            layout.addWidget(template_list)
            
            button_layout = QHBoxLayout()
            load_button = QPushButton("加载")
            cancel_button = QPushButton("取消")
            
            load_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            button_layout.addWidget(load_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                current_item = template_list.currentItem()
                if current_item:
                    template_name = current_item.text().split(' (')[0]
                    template_data = templates[template_name]
                    

                    params = template_data.get('params', {})
                    for param_name, param_value in params.items():
                        if param_name in self.parameter_widgets:
                            self.parameter_widgets[param_name].set_value(param_value)
                            
                    QMessageBox.information(self, "成功", f"参数模板 '{template_name}' 加载成功")
                    
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板失败: {str(e)}")
            

    def _browse_workdir(self):
        """浏览工作目录"""
        from PySide6.QtWidgets import QFileDialog
        
        dir_path = QFileDialog.getExistingDirectory(self, "选择工作目录")
        if dir_path:
            self.workdir_edit.setText(dir_path)
            
    def _load_common_dir(self, item):
        """加载常用目录"""
        dir_path = item.text()
        self.workdir_edit.setText(dir_path)
        
    def _add_current_dir_to_common(self):
        """添加当前目录到常用目录"""
        current_dir = self.workdir_edit.text().strip()
        if current_dir and current_dir not in [self.common_dirs_list.item(i).text() 
                                              for i in range(self.common_dirs_list.count())]:
            self.common_dirs_list.addItem(current_dir)
            
    def _remove_common_dir(self):
        """移除常用目录"""
        current_item = self.common_dirs_list.currentItem()
        if current_item:
            self.common_dirs_list.takeItem(self.common_dirs_list.row(current_item))
        
    def _save_template_with_data(self, dialog, template_name, remark):
        """使用指定的名称和备注保存模板"""
        if not template_name:
            QMessageBox.warning(dialog, "警告", "请输入模板名称")
            return
        
        import json
        import time
        from pathlib import Path
        
        try:

             templates_dir = Path.home() / '.wct' / 'templates'
             templates_dir.mkdir(parents=True, exist_ok=True)
             

             template_data = {
                 'name': template_name,
                 'tool_name': self.current_tool.name,
                 'tool_display_name': self.current_tool.display_name,
                 'parameters': self.get_parameter_values(),
                 'created_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                 'remark': remark,
                 'description': f"{self.current_tool.display_name} 的参数配置模板"
             }
             

             template_file = templates_dir / f"{template_name}.json"
             with open(template_file, 'w', encoding='utf-8') as f:
                 json.dump(template_data, f, ensure_ascii=False, indent=2)
                 
             QMessageBox.information(dialog, "保存成功", f"模板 '{template_name}' 已保存")
             self.update_status(f"模板 '{template_name}' 已保存", "success")
             dialog.accept()
             
        except Exception as e:
            QMessageBox.critical(dialog, "保存失败", f"保存模板时出错: {str(e)}")
            
    def load_template(self):
        """加载参数模板"""
        if not self.current_tool:
            return
            
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
        import json
        from pathlib import Path
        
        templates_dir = Path.home() / '.wct' / 'templates'
        if not templates_dir.exists():
            QMessageBox.information(self, "提示", "暂无保存的模板")
            return
            

        templates = []
        for template_file in templates_dir.glob('*.json'):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    if template_data.get('tool_name') == self.current_tool.name:
                        templates.append((template_file, template_data))
            except Exception:
                continue
                
        if not templates:
            QMessageBox.information(self, "提示", f"暂无 {self.current_tool.display_name} 的模板")
            return
            

        dialog = QDialog(self)
        dialog.setWindowTitle("加载模板")
        dialog.setModal(True)
        dialog.resize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"选择 {self.current_tool.display_name} 的模板:"))
        
        template_list = QListWidget()
        for template_file, template_data in templates:
            remark = template_data.get('remark', '')
            if remark:
                item_text = f"{template_data['name']} - {remark[:30]}{'...' if len(remark) > 30 else ''} ({template_data['created_time']})"
            else:
                item_text = f"{template_data['name']} ({template_data['created_time']})"
            template_list.addItem(item_text)
            
        layout.addWidget(template_list)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        load_button = QPushButton("加载")
        load_button.clicked.connect(lambda: self._load_selected_template(dialog, templates, template_list.currentRow()))
        button_layout.addWidget(load_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
        
    def _load_selected_template(self, dialog, templates, selected_index):
        """加载选中的模板"""
        if selected_index < 0 or selected_index >= len(templates):
            QMessageBox.warning(dialog, "警告", "请选择一个模板")
            return
            
        try:
            template_file, template_data = templates[selected_index]
            parameters = template_data.get('parameters', {})
            
            for param_name, value in parameters.items():
                if param_name in self.parameter_widgets:
                    self.parameter_widgets[param_name].set_value(value)
                    
            QMessageBox.information(dialog, "加载成功", f"模板 '{template_data['name']}' 已加载")
            self.update_status(f"模板 '{template_data['name']}' 已加载", "success")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "加载失败", f"加载模板时出错: {str(e)}")
            
    def copy_command(self):
        """复制命令到剪贴板"""
        try:
            command_text = self.command_preview.toPlainText()
            if command_text:
                clipboard = QApplication.clipboard()
                clipboard.setText(command_text)
                

                original_text = self.copy_command_button.text()
                self.copy_command_button.setText("✅ 已复制")
                self.copy_command_button.setEnabled(False)
                

                QTimer.singleShot(1000, lambda: [
                    self.copy_command_button.setText(original_text),
                    self.copy_command_button.setEnabled(True)
                ])
            else:
                QMessageBox.warning(self, "警告", "没有可复制的命令")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"复制命令失败: {str(e)}")
    
    def manage_templates(self):
        """管理模板 - 简约设计版本"""
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                                       QPushButton, QLabel, QMessageBox, QInputDialog, QTextEdit, QFrame, QGroupBox, QSplitter)
        from PySide6.QtCore import Qt
        import json
        from pathlib import Path
        
        templates_dir = Path.home() / '.wct' / 'templates'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        dialog = QDialog(self)
        dialog.setWindowTitle("模板管理")
        dialog.setModal(True)
        dialog.resize(850, 650)
        

        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        

        header_layout = QHBoxLayout()
        
        title_label = QLabel("🗂️ 模板管理")
        title_label.setProperty("class", "simple_title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        

        quick_refresh_btn = QPushButton("🔄")
        quick_refresh_btn.setToolTip("刷新列表")
        quick_refresh_btn.setProperty("class", "icon_button")
        quick_refresh_btn.clicked.connect(lambda: self._refresh_template_list())
        header_layout.addWidget(quick_refresh_btn)
        
        main_layout.addLayout(header_layout)
        

        splitter = QSplitter(Qt.Horizontal)
        

        left_widget = QFrame()
        left_widget.setProperty("class", "list_container")
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        

        list_title = QLabel("📋 模板列表")
        list_title.setProperty("class", "edit_dialog_label")
        left_layout.addWidget(list_title)
        

        self.template_list_widget = QListWidget()
        self.template_list_widget.setProperty("class", "simple_template_list")
        

        self.template_list_widget.itemDoubleClicked.connect(lambda: self._edit_template())
        self.template_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.template_list_widget.customContextMenuRequested.connect(self._show_template_context_menu)
        left_layout.addWidget(self.template_list_widget)
        
        splitter.addWidget(left_widget)
        

        right_widget = QFrame()
        right_widget.setProperty("class", "action_container")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        

        action_title = QLabel("⚙️ 操作面板")
        action_title.setProperty("class", "edit_dialog_label")
        right_layout.addWidget(action_title)
        

        edit_button = QPushButton("✏️ 编辑模板")
        edit_button.setProperty("class", "template_edit_button")
        edit_button.clicked.connect(lambda: self._edit_template())
        right_layout.addWidget(edit_button)
        

        delete_button = QPushButton("🗑️ 删除模板")
        delete_button.setProperty("class", "template_delete_button")
        delete_button.clicked.connect(lambda: self._delete_template())
        right_layout.addWidget(delete_button)
        

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setProperty("class", "separator_line")
        right_layout.addWidget(separator)
        

        export_button = QPushButton("📤 导出模板")
        export_button.setProperty("class", "template_export_button")
        export_button.clicked.connect(lambda: self._export_templates())
        right_layout.addWidget(export_button)
        
        import_button = QPushButton("📥 导入模板")
        import_button.setProperty("class", "template_import_button")
        import_button.clicked.connect(lambda: self._import_templates())
        right_layout.addWidget(import_button)
        

        right_layout.addStretch()
        

        help_label = QLabel("💡 双击模板快速编辑\n右键查看更多选项")
        help_label.setProperty("class", "template_help_hint")
        right_layout.addWidget(help_label)
        
        splitter.addWidget(right_widget)
        

        splitter.setSizes([500, 300])
        main_layout.addWidget(splitter)
        

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        close_button = QPushButton("关闭")
        close_button.setProperty("class", "dialog_cancel_button")
        close_button.clicked.connect(dialog.accept)
        close_layout.addWidget(close_button)
        main_layout.addLayout(close_layout)
        

        self.template_dialog = dialog
        self._refresh_template_list()
        
        dialog.exec()
        
    def _show_template_context_menu(self, position):
        """显示模板右键菜单 - 简约版本"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        

        item = self.template_list_widget.itemAt(position)
        if item is None or item.text().startswith("📄 暂无"):
            return
            
        menu = QMenu(self.template_list_widget)
        menu.setProperty("class", "context_menu")
        

        edit_action = QAction("✏️ 编辑模板", self.template_list_widget)
        edit_action.triggered.connect(self._edit_template)
        menu.addAction(edit_action)
        

        delete_action = QAction("🗑️ 删除模板", self.template_list_widget)
        delete_action.triggered.connect(self._delete_template)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        

        detail_action = QAction("📋 查看详情", self.template_list_widget)
        detail_action.triggered.connect(self._show_template_detail)
        menu.addAction(detail_action)
        

        copy_action = QAction("📄 复制模板", self.template_list_widget)
        copy_action.triggered.connect(self._copy_template)
        menu.addAction(copy_action)
        

        menu.exec(self.template_list_widget.mapToGlobal(position))
        
    def _show_template_detail(self):
        """显示模板详情 - 简约版本"""
        current_item = self.template_list_widget.currentItem()
        if not current_item or current_item.text().startswith("📄 暂无"):
            QMessageBox.warning(self.template_dialog, "提示", "请选择一个模板")
            return
            
        template_data = current_item.data(32)
        if not template_data:
            QMessageBox.warning(self.template_dialog, "错误", "无法获取模板数据")
            return
            
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
        import json
        
        template_file, template_info = template_data
        
        dialog = QDialog(self.template_dialog)
        dialog.setWindowTitle(f"模板详情 - {template_info['name']}")
        dialog.setModal(True)
        dialog.resize(550, 450)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        

        dialog.setProperty("class", "styled_dialog")
        

        detail_text.setProperty("class", "styled_text_readonly")
        
        detail_info = f"""📋 模板名称: {template_info['name']}
🛠️ 工具名称: {template_info.get('tool_display_name', template_info.get('tool_name', '未知'))}
💬 备注信息: {template_info.get('remark', '无')}
📅 创建时间: {template_info['created_time']}
📄 描述信息: {template_info.get('description', '无')}

⚙️ 参数配置:
{json.dumps(template_info.get('parameters', {}), ensure_ascii=False, indent=2)}"""
        
        detail_text.setPlainText(detail_info)
        layout.addWidget(detail_text)
        

        close_button = QPushButton("关闭")
        close_button.setProperty("class", "dialog_cancel_button")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()
        
    def _copy_template(self):
        """复制模板 - 简约版本"""
        current_item = self.template_list_widget.currentItem()
        if not current_item or current_item.text().startswith("📄 暂无"):
            QMessageBox.warning(self.template_dialog, "提示", "请选择一个模板")
            return
            
        template_data = current_item.data(32)
        if not template_data:
            QMessageBox.warning(self.template_dialog, "错误", "无法获取模板数据")
            return
            
        from PySide6.QtWidgets import QInputDialog
        import json
        import time
        from pathlib import Path
        
        template_file, template_info = template_data
        

        new_name, ok = QInputDialog.getText(self.template_dialog, "复制模板", 
                                          f"输入新模板名称:\n(原名称: {template_info['name']})")
        if not ok or not new_name.strip():
            return
            
        try:

            new_template_info = template_info.copy()
            new_template_info['name'] = new_name.strip()
            new_template_info['created_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
            new_template_info['remark'] = f"复制自: {template_info['name']} - {template_info.get('remark', '')}"
            

            templates_dir = Path.home() / '.wct' / 'templates'
            new_template_file = templates_dir / f"{new_name.strip()}.json"
            
            with open(new_template_file, 'w', encoding='utf-8') as f:
                json.dump(new_template_info, f, ensure_ascii=False, indent=2)
                
            QMessageBox.information(self.template_dialog, "成功", f"模板已复制为 '{new_name.strip()}'")
            self._refresh_template_list()
            
        except Exception as e:
            QMessageBox.critical(self.template_dialog, "失败", f"复制模板时出错: {str(e)}")
          
    def _refresh_template_list(self):
        """刷新模板列表 - 简约版本"""
        import json
        from pathlib import Path
        from PySide6.QtWidgets import QListWidgetItem
        
        self.template_list_widget.clear()
        self.template_files = []
        
        templates_dir = Path.home() / '.wct' / 'templates'
        if not templates_dir.exists():

            empty_item = QListWidgetItem("📄 暂无模板，点击导入或创建模板")
            empty_item.setProperty("class", "empty_state")
            self.template_list_widget.addItem(empty_item)
            return
            
        template_count = 0
        for template_file in templates_dir.glob('*.json'):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    
                tool_name = template_data.get('tool_display_name', template_data.get('tool_name', '未知工具'))
                template_name = template_data.get('name', '未命名模板')
                remark = template_data.get('remark', '无备注')
                created_time = template_data.get('created_time', '未知时间')
                

                if len(remark) > 50:
                    remark = remark[:47] + "..."
                
                display_text = f"📋 {template_name}\n🛠️ {tool_name}\n💬 {remark}\n📅 {created_time}"
                
                item = QListWidgetItem(display_text)
                item.setData(32, (template_file, template_data))
                self.template_list_widget.addItem(item)
                
                self.template_files.append((template_file, template_data))
                template_count += 1
                
            except Exception:
                continue
                
        if template_count == 0:

            empty_item = QListWidgetItem("📄 暂无有效模板")
            empty_item.setProperty("class", "empty_state")
            self.template_list_widget.addItem(empty_item)
                
    def _edit_template(self):
        """编辑模板 - 简约版本"""
        current_item = self.template_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self.template_dialog, "提示", "请选择一个模板")
            return
            

        if current_item.text().startswith("📄 暂无"):
            return
            

        template_data = current_item.data(32)
        if not template_data:
            QMessageBox.warning(self.template_dialog, "错误", "无法获取模板数据")
            return
            
        template_file, template_info = template_data
        

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton
        
        dialog = QDialog(self.template_dialog)
        dialog.setWindowTitle("编辑模板")
        dialog.setModal(True)
        dialog.resize(450, 350)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        

        dialog.setProperty("class", "edit_dialog")
        

        name_label = QLabel("📋 模板名称:")
        name_label.setProperty("class", "edit_dialog_label")
        layout.addWidget(name_label)
        name_edit = QLineEdit(template_info['name'])
        name_edit.setProperty("class", "edit_dialog_input")
        layout.addWidget(name_edit)
        

        remark_label = QLabel("💬 备注说明:")
        remark_label.setProperty("class", "edit_dialog_label")
        layout.addWidget(remark_label)
        remark_edit = QTextEdit(template_info.get('remark', ''))
        remark_edit.setProperty("class", "edit_dialog_input")
        remark_edit.setMaximumHeight(120)
        remark_edit.setPlaceholderText("请输入模板的用途说明、注意事项等...")
        layout.addWidget(remark_edit)
        

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("💾 保存")
        save_button.setProperty("class", "dialog_save_button")
        
        cancel_button = QPushButton("❌ 取消")
        cancel_button.setProperty("class", "dialog_cancel_button")
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = name_edit.text().strip()
            new_remark = remark_edit.toPlainText().strip()
            
            if not new_name:
                QMessageBox.warning(dialog, "警告", "模板名称不能为空")
                return
                
            try:
                import json
                template_info['name'] = new_name
                template_info['remark'] = new_remark
                

                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template_info, f, ensure_ascii=False, indent=2)
                    
                QMessageBox.information(self.template_dialog, "成功", "模板已更新")
                self._refresh_template_list()
                
            except Exception as e:
                QMessageBox.critical(self.template_dialog, "失败", f"编辑模板时出错: {str(e)}")
                
    def _delete_template(self):
        """删除模板 - 简约版本"""
        current_item = self.template_list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self.template_dialog, "提示", "请选择一个模板")
            return
            

        if current_item.text().startswith("📄 暂无"):
            return
            

        template_data = current_item.data(32)
        if not template_data:
            QMessageBox.warning(self.template_dialog, "错误", "无法获取模板数据")
            return
            
        template_file, template_info = template_data
        
        reply = QMessageBox.question(
            self.template_dialog, "确认删除", 
            f"确定要删除模板 '{template_info['name']}' 吗？\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                template_file.unlink()
                QMessageBox.information(self.template_dialog, "成功", "模板已删除")
                self._refresh_template_list()
                
            except Exception as e:
                QMessageBox.critical(self.template_dialog, "失败", f"删除模板时出错: {str(e)}")
                
    def _export_templates(self):
        """导出模板"""
        from PySide6.QtWidgets import QFileDialog
        import json
        import zipfile
        from pathlib import Path
        
        templates_dir = Path.home() / '.wct' / 'templates'
        if not templates_dir.exists() or not list(templates_dir.glob('*.json')):
            QMessageBox.information(self.template_dialog, "提示", "暂无模板可导出")
            return
            
        export_path, _ = QFileDialog.getSaveFileName(
            self.template_dialog, "导出模板", "wct_templates.zip", "ZIP Files (*.zip)"
        )
        
        if export_path:
            try:
                with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for template_file in templates_dir.glob('*.json'):
                        zipf.write(template_file, template_file.name)
                        
                QMessageBox.information(self.template_dialog, "导出成功", f"模板已导出到: {export_path}")
                
            except Exception as e:
                QMessageBox.critical(self.template_dialog, "导出失败", f"导出模板时出错: {str(e)}")
                
    def _import_templates(self):
        """导入模板"""
        from PySide6.QtWidgets import QFileDialog
        import json
        import zipfile
        from pathlib import Path
        
        import_path, _ = QFileDialog.getOpenFileName(
            self.template_dialog, "导入模板", "", "ZIP Files (*.zip);;JSON Files (*.json)"
        )
        
        if not import_path:
            return
            
        templates_dir = Path.home() / '.wct' / 'templates'
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            import_path = Path(import_path)
            
            if import_path.suffix.lower() == '.zip':

                with zipfile.ZipFile(import_path, 'r') as zipf:
                    for file_info in zipf.filelist:
                        if file_info.filename.endswith('.json'):
                            zipf.extract(file_info, templates_dir)
                            
            elif import_path.suffix.lower() == '.json':

                import shutil
                shutil.copy2(import_path, templates_dir / import_path.name)
                
            QMessageBox.information(self.template_dialog, "导入成功", "模板已导入")
            self._refresh_template_list()
            
        except Exception as e:
            QMessageBox.critical(self.template_dialog, "导入失败", f"导入模板时出错: {str(e)}")
                 
    def configure_executable(self):
        """配置工具执行环境和参数"""
        if not self.current_tool:
            return
            
        self._show_tool_config_dialog()
        
    def _show_tool_config_dialog(self):
        """显示工具配置对话框"""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
            QFileDialog, QComboBox, QTabWidget, QListWidget, QListWidgetItem,
            QTextEdit, QCheckBox, QSpinBox, QGroupBox, QGridLayout
        )
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"配置工具: {self.current_tool.display_name}")
        dialog.setModal(True)
        dialog.resize(700, 500)
        
        layout = QVBoxLayout(dialog)
        

        tab_widget = QTabWidget()
        

        interpreter_tab = self._create_interpreter_tab()
        tab_widget.addTab(interpreter_tab, "🐍 解释器配置")
        

        env_tab = self._create_environment_tab()
        tab_widget.addTab(env_tab, "🌍 环境管理")
        

        
        layout.addWidget(tab_widget)
        

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("💾 保存配置")
        save_button.setProperty("class", "config_save_button")
        save_button.clicked.connect(lambda: self._save_tool_config_advanced(dialog))
        button_layout.addWidget(save_button)
        
        reset_button = QPushButton("🔄 重置配置")
        reset_button.setProperty("class", "config_reset_button")
        reset_button.clicked.connect(self._reset_tool_config)
        button_layout.addWidget(reset_button)
        
        cancel_button = QPushButton("❌ 取消")
        cancel_button.setProperty("class", "config_cancel_button")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        

        self._load_current_tool_config()
        
        dialog.exec()
        
    def _browse_executable(self):
        """浏览选择执行文件"""
        if self.interpreter_type_combo.currentText() == "python":
            file_path, _ = QFileDialog.getOpenFileName(self, '选择Python脚本', self.current_tool.path, 'Python Files (*.py)')
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, '选择可执行文件', self.current_tool.path, 'Executable Files (*.exe);;All Files (*)')
            
        if file_path:

            tool_path = Path(self.current_tool.path)
            file_path_obj = Path(file_path)
            try:
                rel_path = file_path_obj.relative_to(tool_path)
                self.path_edit.setText(str(rel_path))
            except ValueError:

                self.path_edit.setText(file_path)
                
    def _save_executable_config(self, dialog):
        """保存执行文件配置"""

        interpreter_type = self.interpreter_type_combo.currentText()
        interpreter_path = self.interpreter_path_edit.text().strip()
        program_path = self.program_path_edit.text().strip()
        

        if interpreter_type == "其他" and not interpreter_path and not program_path:
            QMessageBox.warning(dialog, "警告", "请至少选择解释器路径或程序路径")
            return
        elif interpreter_type in ["python", "java"] and not program_path:
            QMessageBox.warning(dialog, "警告", "请选择程序路径")
            return
        

        if not hasattr(self.current_tool, 'config_data'):
            self.current_tool.config_data = {}
            

        self.current_tool.config_data['interpreter_type'] = interpreter_type
        self.current_tool.config_data['interpreter_path'] = interpreter_path
        self.current_tool.config_data['program_path'] = program_path
        

        if hasattr(self, 'env_type_combo'):
            self.current_tool.config_data['env_type'] = self.env_type_combo.currentText()
        if hasattr(self, 'env_path_edit'):
            self.current_tool.config_data['env_path'] = self.env_path_edit.text().strip()
        if hasattr(self, 'env_vars_text'):
            self.current_tool.config_data['env_vars'] = self.env_vars_text.toPlainText().strip()
        

        if interpreter_type == "python":
            self.current_tool.config_data['executable'] = 'python'
            self.current_tool.config_data['script_path'] = program_path
            self.current_tool.executable = 'python'
            self.current_tool.script_path = program_path
        elif interpreter_type == "java":
            self.current_tool.config_data['executable'] = interpreter_path if interpreter_path else 'java'
            self.current_tool.config_data['script_path'] = program_path
            self.current_tool.executable = interpreter_path if interpreter_path else 'java'
            self.current_tool.script_path = program_path
        else:
            if interpreter_path:
                self.current_tool.config_data['executable'] = interpreter_path
                self.current_tool.config_data['script_path'] = program_path
                self.current_tool.executable = interpreter_path
                self.current_tool.script_path = program_path
            else:
                self.current_tool.config_data['executable'] = program_path
                self.current_tool.config_data['script_path'] = program_path
                self.current_tool.executable = program_path
                self.current_tool.script_path = program_path
            

        self._save_tool_config()
        

        if self.current_tool.has_required_files():
            if hasattr(self, 'exec_status_label'):
                self.exec_status_label.setText("✅ 执行文件已配置")
                self.exec_status_label.setProperty("status", "success")

                self.exec_status_label.style().unpolish(self.exec_status_label)
                self.exec_status_label.style().polish(self.exec_status_label)
            if hasattr(self, 'update_status'):
                self.update_status("执行文件配置成功", "success")
        else:
            if hasattr(self, 'update_status'):
                 self.update_status("执行文件配置失败，请检查路径", "error")
        
    def _save_tool_config(self):
        """保存工具配置到app_config.json"""
        try:
            from pathlib import Path
            import json
            

            from .utils import get_resource_path
            config_dir = get_resource_path('config')
            app_config_file = config_dir / 'app_config.json'
            

            if app_config_file.exists():
                with open(app_config_file, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
            else:
                app_config = {}
            

            if 'tool_command' not in app_config:
                app_config['tool_command'] = {}
            

            tool_name = self.current_tool.name
            tool_config = {
                'executable': self.current_tool.executable,
                'script_path': self.current_tool.script_path
            }
            

            if hasattr(self.current_tool, 'config_data'):
                if 'interpreter_type' in self.current_tool.config_data:
                    tool_config['interpreter_type'] = self.current_tool.config_data['interpreter_type']
                if 'interpreter_path' in self.current_tool.config_data:
                    tool_config['interpreter_path'] = self.current_tool.config_data['interpreter_path']
                if 'program_path' in self.current_tool.config_data:
                    tool_config['program_path'] = self.current_tool.config_data['program_path']

                if 'env_type' in self.current_tool.config_data:
                    tool_config['env_type'] = self.current_tool.config_data['env_type']
                if 'env_path' in self.current_tool.config_data:
                    tool_config['env_path'] = self.current_tool.config_data['env_path']
                if 'env_vars' in self.current_tool.config_data:
                    tool_config['env_vars'] = self.current_tool.config_data['env_vars']
            
            app_config['tool_command'][tool_name] = tool_config
            

            with open(app_config_file, 'w', encoding='utf-8') as f:
                json.dump(app_config, f, indent=2, ensure_ascii=False)
                        
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置时出错: {str(e)}")
    
    def _reset_tool_config(self):
        """重置工具配置"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(self, "确认重置", "确定要重置工具配置吗？这将清除所有自定义设置。",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:

                if hasattr(self, 'interpreter_type_combo'):
                    self.interpreter_type_combo.setCurrentText("python")
                if hasattr(self, 'interpreter_path_edit'):
                    self.interpreter_path_edit.clear()
                if hasattr(self, 'program_path_edit'):
                    self.program_path_edit.clear()
                    

                if hasattr(self, 'env_type_combo'):
                    self.env_type_combo.setCurrentText("系统默认")
                if hasattr(self, 'env_path_edit'):
                    self.env_path_edit.clear()
                if hasattr(self, 'env_vars_text'):
                    self.env_vars_text.clear()
                    

                if self.current_tool:
                    self.current_tool.executable = 'python'
                    self.current_tool.script_path = ''
                    if hasattr(self.current_tool, 'config_data'):
                        self.current_tool.config_data['interpreter_type'] = 'python'
                        self.current_tool.config_data['interpreter_path'] = ''
                        self.current_tool.config_data['program_path'] = ''
                        self.current_tool.config_data['env_type'] = '系统默认'
                        self.current_tool.config_data['env_path'] = ''
                        self.current_tool.config_data['env_vars'] = ''
                    
                QMessageBox.information(self, "重置成功", "工具配置已重置为默认值")
                
            except Exception as e:
                 QMessageBox.critical(self, "重置失败", f"重置配置时出错: {str(e)}")
    
    def _load_current_tool_config(self):
        """加载当前工具配置"""
        if not self.current_tool:
            return
            
        try:

            from pathlib import Path
            import json
            
            from .utils import get_resource_path
            config_dir = get_resource_path('config')
            app_config_file = config_dir / 'app_config.json'
            
            if app_config_file.exists():
                with open(app_config_file, 'r', encoding='utf-8') as f:
                    app_config = json.load(f)
                    
                tool_name = self.current_tool.name
                if 'tool_command' in app_config and tool_name in app_config['tool_command']:
                    tool_config = app_config['tool_command'][tool_name]
                    

                    interpreter_type = tool_config.get('interpreter_type', 'python')
                    interpreter_path = tool_config.get('interpreter_path', '')
                    program_path = tool_config.get('program_path', '')
                    

                    env_type = tool_config.get('env_type', '系统默认')
                    env_path = tool_config.get('env_path', '')
                    env_vars = tool_config.get('env_vars', '')
                    

                    if not hasattr(self.current_tool, 'config_data'):
                        self.current_tool.config_data = {}
                    self.current_tool.config_data['interpreter_type'] = interpreter_type
                    self.current_tool.config_data['interpreter_path'] = interpreter_path
                    self.current_tool.config_data['program_path'] = program_path
                    self.current_tool.config_data['env_type'] = env_type
                    self.current_tool.config_data['env_path'] = env_path
                    self.current_tool.config_data['env_vars'] = env_vars
                    

                    if hasattr(self, 'interpreter_type_combo'):
                        self.interpreter_type_combo.setCurrentText(interpreter_type)
                        
                    if hasattr(self, 'interpreter_path_edit'):
                        self.interpreter_path_edit.setText(interpreter_path)
                        
                    if hasattr(self, 'program_path_edit'):
                        self.program_path_edit.setText(program_path)
                        

                    if hasattr(self, 'env_type_combo'):
                        self.env_type_combo.setCurrentText(env_type)
                        
                    if hasattr(self, 'env_path_edit'):
                        self.env_path_edit.setText(env_path)
                        
                    if hasattr(self, 'env_vars_text'):
                        self.env_vars_text.setPlainText(env_vars)
                        
                    return
            

            if hasattr(self, 'interpreter_type_combo'):
                self.interpreter_type_combo.setCurrentText("python")
                
            if hasattr(self, 'interpreter_path_edit'):
                self.interpreter_path_edit.clear()
                
            if hasattr(self, 'program_path_edit'):
                if self.current_tool.script_path:
                    self.program_path_edit.setText(self.current_tool.script_path)
                else:
                    self.program_path_edit.clear()
                    
        except Exception as e:
             print(f"加载工具配置失败: {str(e)}")
    
    def _save_tool_config_advanced(self, dialog):
        """保存高级工具配置"""
        from PySide6.QtWidgets import QMessageBox
        
        try:
            if not self.current_tool:
                QMessageBox.warning(dialog, "警告", "没有选择工具")
                return
                

            self._save_executable_config(dialog)
            
            QMessageBox.information(dialog, "成功", "配置已保存")
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(dialog, "保存失败", f"保存配置时出错: {str(e)}")
            
    def filter_parameters(self, search_text):
        """根据搜索文本过滤参数"""
        search_text = search_text.lower().strip()
        

        if not search_text:
            self._show_all_parameters()
            return
            

        for param_name, widget in self.parameter_widgets.items():
            param_config = widget.param_config
            

            name_match = search_text in param_name.lower()
            

            description = param_config.get('description', '')
            desc_match = search_text in description.lower()
            

            help_text = param_config.get('help', '')
            help_match = search_text in help_text.lower()
            

            should_show = name_match or desc_match or help_match
            widget.setVisible(should_show)
            

        self._refresh_parameter_layout()
            
    def clear_parameter_search(self):
        """清除参数搜索"""
        self.param_search_edit.clear()
        self._show_all_parameters()
        
    def _show_all_parameters(self):
        """显示所有参数控件"""
        for widget in self.parameter_widgets.values():
            widget.setVisible(True)

        self._refresh_parameter_layout()
        
    def _refresh_parameter_layout(self):
        """刷新参数布局"""

        if hasattr(self, 'common_params_scroll'):
            self.common_params_scroll.widget().updateGeometry()
            self.common_params_scroll.update()
            

        if hasattr(self, 'all_params_scroll'):
            self.all_params_scroll.widget().updateGeometry()
            self.all_params_scroll.update()
            

        self.params_tab_widget.updateGeometry()
        self.params_tab_widget.update()
    
    def _clear_env_vars(self):
        """清空环境变量"""
        self.env_vars_text.clear()
        
    def _reload_parameters(self):
        """重新加载参数界面（使用新的参数管理器）"""
        if self.current_tool:

            current_values = self.get_parameter_values()
            

            self.param_manager = ParameterManager(self.current_tool)
            

            self.clear_parameters()
            self.create_parameter_widgets()
            

            for param_name, value in current_values.items():
                if param_name in self.parameter_widgets:
                    try:
                        self.parameter_widgets[param_name].set_value(value)
                    except Exception as e:
                        print(f"恢复参数 {param_name} 的值失败: {e}")
            

            for param_widget in self.parameter_widgets.values():
                param_widget.update_validation_status()
                        

            self.update()
            if hasattr(self, 'params_tab_widget'):
                self.params_tab_widget.update()
            

            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
        
                        
            
