import os
import re
import json
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QCheckBox, QFrame, QScrollArea,
    QGridLayout, QGroupBox, QMenu, QSpacerItem, QSizePolicy, QMessageBox, QApplication, QToolTip
)
from PySide6.QtCore import Qt, QMimeData, QPoint, QTimer, QByteArray
from PySide6.QtGui import QFont, QDrag, QPainter, QPixmap, QIcon, QCursor, QColor

from .utils import get_system_font, s
from .i18n import t
from .widgets import ClickableLabel
from .styles import get_modern_qmenu_stylesheet
class ParameterEditDialog(QDialog):
    def __init__(self, param_info, parent=None):
        super().__init__(parent)
        self.param_info = param_info.copy()
        self.setup_ui()
        
    def setup_ui(self):
        
        self.setWindowTitle(t("dialog.edit_param_title"))
        self.setMinimumSize(s(560), s(720))
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        layout = QVBoxLayout()
        layout.setContentsMargins(s(30), s(30), s(30), s(30))
        layout.setSpacing(s(25))
        title_label = QLabel(t("dialog.edit_param_title"))
        title_label.setFont(QFont(get_system_font(), s(16), QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                padding: {s(16)}px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #357abd);
                border: none;
                border-radius: {s(10)}px;
                font-weight: 700;
                font-size: {s(16)}pt;
                font-family: '{get_system_font()}';
            }}
        """)
        layout.addWidget(title_label)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(s(20))
        name_label = QLabel(t("labels.param_name"))
        name_label.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        name_label.setStyleSheet(f"""
            QLabel {{
                color: #1d1d1f;
                font-weight: 700;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
                padding: {s(6)}px 0px;
            }}
        """)
        self.name_edit = QLineEdit(self.param_info.get('param_name', ''))
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_edit)
        display_label = QLabel(t("labels.display_name"))
        display_label.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        display_label.setStyleSheet(f"""
            QLabel {{
                color: #1d1d1f;
                font-weight: 700;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
                padding: {s(6)}px 0px;
            }}
        """)
        self.display_edit = QLineEdit(self.param_info.get('display_name', ''))
        form_layout.addWidget(display_label)
        form_layout.addWidget(self.display_edit)
        desc_label = QLabel(t("labels.param_desc"))
        desc_label.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: #1d1d1f;
                font-weight: 700;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
                padding: {s(6)}px 0px;
            }}
        """)
        self.desc_edit = QTextEdit(self.param_info.get('description', ''))
        self.desc_edit.setMaximumHeight(s(160))
        self.desc_edit.setMinimumHeight(s(120))
        form_layout.addWidget(desc_label)
        form_layout.addWidget(self.desc_edit)
        type_label = QLabel(t("labels.param_type"))
        type_label.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        type_label.setStyleSheet(f"""
            QLabel {{
                color: #1d1d1f;
                font-weight: 700;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
                padding: {s(6)}px 0px;
            }}
        """)
        self.type_combo = QComboBox()
        self.type_combo.addItems([t("param_types.checkbox"), t("param_types.input")])
        current_type = self.param_info.get('type', '1')
        self.type_combo.setCurrentIndex(0 if current_type == '1' else 1)
        form_layout.addWidget(type_label)
        form_layout.addWidget(self.type_combo)
        self.required_checkbox = QCheckBox(t("labels.required_param"))
        self.required_checkbox.setChecked(self.param_info.get('required', False))
        self.required_checkbox.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        form_layout.addWidget(self.required_checkbox)
        
        layout.addLayout(form_layout)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(s(16))
        button_layout.addStretch()
        
        cancel_btn = QPushButton(t("buttons.cancel"))
        cancel_btn.setMinimumSize(s(100), s(45))
        cancel_btn.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton(t("buttons.save"))
        save_btn.setMinimumSize(s(100), s(45))
        save_btn.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        save_btn.clicked.connect(self.save_and_close)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafbfc);
                border: 2px solid #4a90e2;
                border-radius: {s(12)}px;
            }}
            QLineEdit, QTextEdit {{
                background-color: #ffffff;
                border: 2px solid #e5e5ea;
                border-radius: {s(8)}px;
                padding: {s(14)}px {s(16)}px;
                color: #1d1d1f;
                font-size: {s(12)}pt;
                font-weight: 600;
                font-family: '{get_system_font()}';
                min-height: {s(20)}px;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: #4a90e2;
                background-color: #ffffff;
            }}
            QLineEdit:hover, QTextEdit:hover {{
                border-color: #adb5bd;
            }}
            QComboBox {{
                background-color: #ffffff;
                border: 2px solid #e5e5ea;
                border-radius: {s(8)}px;
                padding: {s(12)}px {s(14)}px;
                color: #1d1d1f;
                font-size: {s(12)}pt;
                font-weight: 600;
                font-family: '{get_system_font()}';
                min-height: {s(28)}px;
            }}
            QComboBox:focus {{
                border-color: #4a90e2;
            }}
            QComboBox:hover {{
                border-color: #adb5bd;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {s(20)}px;
                border-left: 1px solid #e5e5ea;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: {s(8)}px;
                height: {s(8)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: {s(6)}px;
                color: #1d1d1f;
                font-weight: 600;
                font-family: '{get_system_font()}';
                selection-background-color: #4a90e2;
                selection-color: #ffffff;
            }}
            QCheckBox {{
                color: #1d1d1f;
                font-size: {s(12)}pt;
                font-weight: 700;
                font-family: '{get_system_font()}';
                padding: {s(12)}px;
                min-height: {s(24)}px;
            }}
            QCheckBox::indicator {{
                width: {s(18)}px;
                height: {s(18)}px;
                border: 2px solid #e5e5ea;
                border-radius: {s(4)}px;
                background-color: #ffffff;
            }}
            QCheckBox::indicator:checked {{
                background-color: #4a90e2;
                border-color: #4a90e2;
            }}
            QCheckBox::indicator:hover {{
                border-color: #adb5bd;
            }}
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #357abd);
                color: white;
                border: none;
                border-radius: {s(8)}px;
                padding: {s(10)}px {s(20)}px;
                font-weight: 700;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5ba0f2, stop: 1 #4a90e2);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357abd, stop: 1 #2c5aa0);
            }}
            QPushButton[text="取消"] {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                color: #495057;
                border: 1px solid #ced4da;
            }}
            QPushButton[text="取消"]:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
            }}
            QPushButton[text="取消"]:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
            }}
        """)
    
    def save_and_close(self):
        
        if not self.name_edit.text().strip() or not self.display_edit.text().strip():
            QMessageBox.warning(self, t("messages.warning"), t("messages.param_name_empty"))
            return
        self.accept()
    
    def get_param_info(self):
        
        return {
            'param_name': self.name_edit.text().strip(),
            'display_name': self.display_edit.text().strip(),
            'description': self.desc_edit.toPlainText().strip(),
            'type': '1' if self.type_combo.currentIndex() == 0 else '2',
            'required': self.required_checkbox.isChecked(),
            'default': self.param_info.get('default', ''),
            'help': self.param_info.get('help', '')
        }
class ParameterWidget(QWidget):
    def __init__(self, param_info):
        super().__init__()
        self.param_info = param_info
        self.control = None
        self.label = None
        self.drag_start_position = QPoint()
        self.start_drag_pos = None
        self.setup_ui()
        self.setup_context_menu()
        self.setup_drag_drop()
    
    def create_tooltip(self):
        
        tooltip_text = ""
        if self.param_info['description']:
            tooltip_text = f"<b style='color: #4a90e2; font-size: {s(10)}pt;'>{self.param_info['param_name']}</b><br/><span style='color: #6c757d; font-size: {s(9)}pt;'>{self.param_info['description']}</span>"
        
        if self.param_info.get('required', False):
            required_text = f"<br/><span style='color: #dc3545; font-size: {s(9)}pt; font-weight: bold;'>{t('tooltips.required_param')}</span>"
            tooltip_text += required_text
        
        drag_tip = f"<br/><span style='color: #17a2b8; font-size: {s(8)}pt;'>{t('tooltips.drag_reorder')}</span>"
        tooltip_text += drag_tip
        
        return tooltip_text
    
    def setup_ui(self):
        
        param_type = self.param_info['type']
        is_required = self.param_info.get('required', False)
        
        if param_type == '1':
            layout = QVBoxLayout()
            layout.setSpacing(s(1))
            layout.setContentsMargins(s(3), s(3), s(3), s(3))
            
            display_text = self.param_info['display_name']
            self.control = ClickableLabel(display_text)
            self.control.setAlignment(Qt.AlignCenter)
            if is_required:
                self.control.is_required = True  
                self.control.parent_widget = self  
                
                original_toggle = self.control.toggle
                def enhanced_toggle():
                    original_toggle()
                    self.update_required_style()
                self.control.toggle = enhanced_toggle
                
                self.update_required_style()
            
            tooltip = self.create_tooltip()
            if tooltip:
                self.control.setToolTip(tooltip)
            
            layout.addWidget(self.control)
            
        elif param_type == '2':
            layout = QHBoxLayout()
            layout.setSpacing(s(4))
            layout.setContentsMargins(s(4), s(2), s(4), s(2))
            
            label_text = self.param_info['display_name'] + ":"
            name_label = QLabel(label_text)
            name_label.setFont(QFont(get_system_font(), s(8), QFont.Medium))
            name_label.setWordWrap(True)  
            name_label.setMinimumWidth(s(60))
            name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)  
            
            label_style = f"""
                QLabel {{
                    color: #495057;
                    font-weight: 600;
                    font-size: {s(8)}pt;
                    padding: {s(2)}px {s(4)}px;
                }}
            """
            
            if is_required:
                label_style = f"""
                    QLabel {{
                        color: #495057;
                        font-weight: 700;
                        font-size: {s(8)}pt;
                        padding: {s(2)}px {s(4)}px;
                        border-left: 3px solid #dc3545;
                        padding-left: {s(6)}px;
                    }}
                """
            name_label.setStyleSheet(label_style)
            
            tooltip = self.create_tooltip()
            if tooltip:
                name_label.setToolTip(tooltip)
            layout.addWidget(name_label)
            
            self.control = QLineEdit()
            self.control.setFont(QFont(get_system_font(), s(8)))
            self.control.setMaximumHeight(s(28))
            
            placeholder_text = t("placeholders.input_value")
            if is_required:
                placeholder_text = t("placeholders.required_input")
                
            self.control.setPlaceholderText(placeholder_text)
            if is_required:
                self.control.textChanged.connect(self.update_required_style)
                self.update_required_style()
            else:
                normal_style = f"""
                    QLineEdit {{
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #ffffff, stop: 1 #f8f9fa);
                        border: 1px solid #e5e5ea;
                        border-radius: {s(6)}px;
                        padding: {s(4)}px {s(8)}px;
                        color: #495057;
                        font-size: {s(8)}pt;
                        font-weight: 600;
                        selection-background-color: #4a90e2;
                    }}
                    QLineEdit:focus {{
                        border: 2px solid #4a90e2;
                        background: #ffffff;
                    }}
                    QLineEdit:hover {{
                        border-color: #adb5bd;
                    }}
                """
                self.control.setStyleSheet(normal_style)
                
            tooltip = self.create_tooltip()
            if tooltip:
                self.control.setToolTip(tooltip)
            
            layout.addWidget(self.control)
        else:

            layout = QHBoxLayout()
            layout.setSpacing(s(2))
            layout.setContentsMargins(s(2), s(2), s(2), s(2))
            
            self.control = ClickableLabel(self.param_info['display_name'])
            tooltip = self.create_tooltip()
            if tooltip:
                self.control.setToolTip(tooltip)
            layout.addWidget(self.control)
        if param_type == '1':
            self.setMinimumHeight(s(28))
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  
        else:
            self.setMinimumHeight(s(30))
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  
        self.setStyleSheet(f"""
            ParameterWidget {{
                border-radius: {s(4)}px;
                background: transparent;
                border: 1px solid transparent;
                margin: {s(1)}px;
            }}
            ParameterWidget:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e3f2fd, stop: 1 #f3f9ff);
                border: 1px solid #4a90e2;
            }}
        """)
            
        self.setLayout(layout)
    
    def setup_drag_drop(self):
        
        self.setAcceptDrops(False)
    
    def update_required_style(self):
        
        is_required = self.is_required()
        is_filled = self.is_filled()
        param_type = self.param_info['type']
        
        if param_type == '1':

            if hasattr(self.control, 'is_required'):
                self.control.is_required = is_required
            if hasattr(self.control, 'parent_widget'):
                self.control.parent_widget = self
            if hasattr(self.control, 'update_style'):
                self.control.update_style()
        elif param_type == '2':

            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QLabel):
                    label = item.widget()
                    label_text = self.param_info['display_name'] + ":"
                    label.setText(label_text)
                    if is_required:
                        label_style = f"""
                            QLabel {{
                                color: #dc3545;
                                font-family: '{get_system_font()}';
                                font-weight: bold;
                                font-size: {s(8)}pt;
                                padding: {s(2)}px;
                            }}
                        """
                    else:
                        label_style = f"""
                            QLabel {{
                                color: #495057;
                                font-family: '{get_system_font()}';
                                font-weight: 500;
                                font-size: {s(8)}pt;
                                padding: {s(2)}px;
                            }}
                        """
                    label.setStyleSheet(label_style)
                    break
            placeholder_text = t("placeholders.input_value")
            if is_required:
                placeholder_text = t("placeholders.required_input")
            self.control.setPlaceholderText(placeholder_text)
            if is_required:
                if is_filled:

                    normal_style = f"""
                        QLineEdit {{
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                      stop: 0 #ffffff, stop: 1 #f8fff8);
                            border: 1px solid #28a745;
                            border-radius: {s(6)}px;
                            padding: {s(6)}px {s(10)}px;
                            color: #495057;
                            font-size: {s(8)}pt;
                            font-weight: 600;
                            selection-background-color: #4a90e2;
                            font-family: '{get_system_font()}';
                        }}
                        QLineEdit:focus {{
                            border: 2px solid #28a745;
                            background: #ffffff;
                        }}
                        QLineEdit:hover {{
                            border-color: #20c997;
                        }}
                    """
                    self.control.setStyleSheet(normal_style)
                else:

                    error_style = f"""
                        QLineEdit {{
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                      stop: 0 #fff5f5, stop: 1 #ffebee);
                            border: 2px solid #dc3545;
                            border-radius: {s(6)}px;
                            padding: {s(6)}px {s(10)}px;
                            color: #495057;
                            font-size: {s(8)}pt;
                            font-weight: 600;
                            selection-background-color: #4a90e2;
                            font-family: '{get_system_font()}';
                        }}
                        QLineEdit:focus {{
                            border: 2px solid #dc3545;
                            background: #ffffff;
                        }}
                        QLineEdit:hover {{
                            border-color: #c82333;
                        }}
                    """
                    self.control.setStyleSheet(error_style)
            else:

                normal_style = f"""
                    QLineEdit {{
                        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                  stop: 0 #ffffff, stop: 1 #f8f9fa);
                        border: 1px solid #e5e5ea;
                        border-radius: {s(6)}px;
                        padding: {s(6)}px {s(10)}px;
                        color: #495057;
                        font-size: {s(8)}pt;
                        font-weight: 600;
                        selection-background-color: #4a90e2;
                        font-family: '{get_system_font()}';
                    }}
                    QLineEdit:focus {{
                        border: 2px solid #4a90e2;
                        background: #ffffff;
                    }}
                    QLineEdit:hover {{
                        border-color: #adb5bd;
                    }}
                """
                self.control.setStyleSheet(normal_style)
    
    def setup_context_menu(self):
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        
        menu = QMenu(self)
        menu.setStyleSheet(get_modern_qmenu_stylesheet())
        
        edit_action = menu.addAction(t('context_menu.edit_param'))
        edit_action.triggered.connect(self.edit_parameter)
        
        required_text = t('context_menu.unset_required') if self.is_required() else t('context_menu.set_required')
        required_action = menu.addAction(required_text)
        required_action.triggered.connect(self.toggle_required)
        
        menu.addSeparator()
        
        section = self.get_section()
        if section:
            tool_page = section.get_tool_operation_page()
            if tool_page:

                current_type = self.param_info.get('type')
                if current_type == '1':
                    move_action = menu.addAction(t('context_menu.move_to_input'))
                    move_action.triggered.connect(
                        lambda: tool_page.move_parameter_between_sections(self.param_info, t('tabs.checkbox_params'), t('tabs.input_params'))
                    )
                else:
                    move_action = menu.addAction(t('context_menu.move_to_checkbox'))
                    move_action.triggered.connect(
                        lambda: tool_page.move_parameter_between_sections(self.param_info, t('tabs.input_params'), t('tabs.checkbox_params'))
                    )
                menu.addSeparator()

                current_tab = tool_page.param_tabs.tabText(tool_page.param_tabs.currentIndex())
                if current_tab == t('tabs.all_params'):
                    copy_action = menu.addAction(t('context_menu.copy_to_common'))
                    copy_action.triggered.connect(lambda: tool_page.copy_parameter_to_common(self.param_info))
                elif current_tab == t('tabs.common_params'):
                    remove_action = menu.addAction(t('context_menu.remove_from_common'))
                    remove_action.triggered.connect(lambda: tool_page.remove_parameter_from_common(self.param_info))
        menu.exec(self.mapToGlobal(position))
    
    def edit_parameter(self):
        
        old_param_name = self.param_info.get('param_name')
        dialog = ParameterEditDialog(self.param_info, self)
        if dialog.exec() == QDialog.Accepted:
            self.param_info = dialog.get_param_info()
            self.update_ui_from_param_info()
            section = self.get_section()
            if section:
                tool_page = section.get_tool_operation_page()
                if tool_page and hasattr(tool_page, 'update_parameter_in_config'):
                    tool_page.update_parameter_in_config(old_param_name, self.param_info)
                if tool_page and hasattr(tool_page, 'save_and_reload_ui'):
                    tool_page.save_and_reload_ui()
    
    def toggle_required(self):
        
        self.param_info['required'] = not self.param_info.get('required', False)
        self.update_required_style()
        section = self.get_section()
        if section:
            tool_page = section.get_tool_operation_page()
            if tool_page and hasattr(tool_page, 'sync_required_status'):
                tool_page.sync_required_status(self.param_info['param_name'], self.param_info['required'])
            if tool_page and hasattr(tool_page, 'save_and_reload_ui'):
                tool_page.save_and_reload_ui()
    
    def update_ui_from_param_info(self):
        
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
        self.setup_ui()
        
    def get_value(self):
        
        if isinstance(self.control, (QCheckBox, ClickableLabel)):
            return self.control.isChecked()
        elif isinstance(self.control, QLineEdit):
            return self.control.text()
        return None
            
    def is_filled(self):
        
        if not self.is_required():
            return True  
            
        if isinstance(self.control, (QCheckBox, ClickableLabel)):
            return self.control.isChecked()
        elif isinstance(self.control, QLineEdit):
            return bool(self.control.text().strip())
        return True
            
    def is_required(self):
        
        return self.param_info.get('required', False)
        
    def get_param_string(self):
        
        if isinstance(self.control, (QCheckBox, ClickableLabel)):
            if self.control.isChecked():
                return [self.param_info['param_name']]
            return []
        elif isinstance(self.control, QLineEdit):
            text = self.control.text().strip()
            if text:
                param_name = self.param_info['param_name']
                
                if text.startswith('"') and text.endswith('"'):
                    return [param_name, text]
                elif text.startswith("'") and text.endswith("'"):
                    return [param_name, text]
                elif any(char in text for char in [' ', '\t', '&', '|', '(', ')', '<', '>', '^']):
                    return [param_name, f'"{text}"']
                else:
                    return [param_name, text]
            return []
        return []
        
    def get_display_name(self):
        
        return self.param_info.get('display_name', '')

    def get_section(self):
        
        parent = self.parent()
        while parent:
            if isinstance(parent, ParameterSection):
                return parent
            parent = parent.parent()
        return None
    
    def get_tool_operation_page(self):
        
        parent = self.parent()
        while parent:

            if hasattr(parent, 'param_tabs') and hasattr(parent, 'tool_name'):
                return parent
            parent = parent.parent()
        return None
    
    def get_current_section_title(self):
        
        parent = self.parent()
        while parent:
            if isinstance(parent, ParameterSection):
                return parent.title
            parent = parent.parent()
        return "未知区域"
    
    def copy_parameter_info(self):
        
        param_info_text = f"""参数名称: {self.param_info['param_name']}
显示名称: {self.param_info['display_name']}
参数描述: {self.param_info.get('description', '无描述')}
参数类型: {t('tabs.checkbox_params') if self.param_info['type'] == '1' else t('tabs.input_params')}
是否必填: {'是' if self.param_info.get('required', False) else '否'}
当前值: {self.get_display_value()}"""
        
        clipboard = QApplication.clipboard()
        clipboard.setText(param_info_text)
        QToolTip.showText(
            self.mapToGlobal(self.rect().center()), 
            "参数信息已复制到剪贴板", 
            self, 
            self.rect(), 
            s(2000)
        )
    
    def get_display_value(self):
        
        param_type = self.param_info['type']
        
        if param_type == '1':
            return "已选中" if self.control.isChecked() else "未选中"
        elif param_type == '2':
            value = self.control.text().strip()
            return value if value else "未设置"
        
        return "未知"
    
    def move_parameter(self, from_tab, to_tab):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        if hasattr(tool_page, 'show_custom_question'):
            if tool_page.show_custom_question(
                "移动参数确认", 
                f"确定要将参数 '{self.param_info['display_name']}' 从{from_tab}移动到{to_tab}吗？"
            ):
                tool_page.move_parameter_between_tabs(self.param_info, from_tab, to_tab)
    
    def remove_from_common(self):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        if hasattr(tool_page, 'show_custom_question'):
            if tool_page.show_custom_question(
                "移除参数确认", 
                f"确定要将参数 '{self.param_info['display_name']}' 从常用参数中移除吗？\n\n注意：移除后该参数仍可在全部参数中找到。"
            ):
                tool_page.remove_parameter_from_common(self.param_info)
    
    def copy_to_common(self):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        if hasattr(tool_page, 'show_custom_question'):
            if tool_page.show_custom_question(
                "添加参数确认", 
                f"确定要将参数 '{self.param_info['display_name']}' 添加到常用参数吗？"
            ):
                tool_page.copy_parameter_to_common(self.param_info)

    def mousePressEvent(self, event):
        
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        self.start_drag()
    
    def start_drag(self):
        
        drag = QDrag(self)
        mime_data = QMimeData()

        drag_data = {
            'param_name': self.param_info['param_name'],
            'param_type': self.param_info['type'],
            'source_section': self.get_current_section_title(),
            'param_info': self.param_info.copy()
        }
        mime_data.setText(f"parameter_widget_data:{json.dumps(drag_data)}")
        drag.setMimeData(mime_data)

        pixmap = None
        try:
            if (self.isVisible() and self.width() > 0 and self.height() > 0 and 
                self.isEnabled() and not self.visibleRegion().isEmpty()):
                pixmap = self.grab()
            if not pixmap or pixmap.isNull() or pixmap.width() == 0 or pixmap.height() == 0:
                pixmap = self.create_simple_drag_icon()
        except Exception:
            pixmap = self.create_simple_drag_icon()
        drag.setPixmap(pixmap)

        if hasattr(self, 'drag_start_position'):
            drag.setHotSpot(self.drag_start_position)
        else:
            drag.setHotSpot(QPoint(10, 10))

        result = drag.exec(Qt.MoveAction)
        if result == Qt.MoveAction:
            pass
    
    def create_simple_drag_icon(self):
        pixmap = QPixmap(s(80), s(24))
        pixmap.fill(QColor(74, 144, 226, 200))
        return pixmap

class ParameterSection(QWidget):
    
    def __init__(self, title, params):
        super().__init__()
        self.title = title
        self.params = params
        self.param_widgets = []
        self.setAcceptDrops(True)
        self.setup_ui()
        self.setup_drag_drop()
        self.setup_context_menu()
    
    def setup_ui(self):
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_group = QGroupBox(self.title)
        main_group.setFont(QFont(get_system_font(), s(10), QFont.Bold))
        main_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #e5e5ea;
                border-radius: {s(8)}px;
                margin-top: {s(12)}px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                padding-top: {s(8)}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: {s(4)}px {s(12)}px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #357abd);
                color: #ffffff;
                border-radius: {s(4)}px;
                font-weight: 600;
                font-size: {s(9)}pt;
            }}
        """)

        section_content_layout = QVBoxLayout(main_group)
        section_content_layout.setContentsMargins(s(12), s(25), s(12), s(12))
        section_content_layout.setSpacing(s(8))

        search_widget = self.create_search_bar()
        section_content_layout.addWidget(search_widget)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(s(4))
        self.grid_layout.setContentsMargins(s(6), s(6), s(6), s(6))
        section_content_layout.addLayout(self.grid_layout)

        row, col = 0, 0
        self.param_widgets.clear()

        for param in self.params:
            param_widget = ParameterWidget(param)
            self.param_widgets.append(param_widget)

            if param.get('type') == '1':
                self.grid_layout.addWidget(param_widget, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
            else:
                self.grid_layout.addWidget(param_widget, row, col, 1, 2)
                col += 2
                if col >= 4:
                    col = 0
                    row += 1

        if col != 0:
            row += 1

        self.grid_layout.setRowStretch(row, 1)

        self.grid_layout.setColumnStretch(0, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 1)
        self.grid_layout.setColumnStretch(3, 1)

        main_layout.addWidget(main_group)
        self.setLayout(main_layout)

    def create_search_bar(self):
        
        search_container = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(s(4), s(4), s(4), s(8))
        search_layout.setSpacing(s(8))
        search_icon = QLabel("🔍")
        search_icon.setFont(QFont(get_system_font(), s(10)))
        search_icon.setFixedSize(s(20), s(24))
        search_icon.setAlignment(Qt.AlignCenter)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t('placeholders.search_params'))
        self.search_input.setFont(QFont(get_system_font(), s(9)))
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid #e5e5ea;
                border-radius: {s(6)}px;
                padding: {s(6)}px {s(12)}px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafbfc);
                font-size: {s(9)}pt;
                font-weight: 600;
                color: #495057;
                font-family: '{get_system_font()}';
            }}
            QLineEdit:focus {{
                border: 2px solid #4a90e2;
                background: #ffffff;
                outline: none;
            }}
            QLineEdit:hover {{
                border-color: #adb5bd;
                background: #ffffff;
            }}
        """)
        self.clear_search_btn = QPushButton("✕")
        self.clear_search_btn.setFont(QFont(get_system_font(), s(8)))
        self.clear_search_btn.setFixedSize(s(24), s(24))
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.clear_search_btn.setVisible(False)  
        self.clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: {s(12)}px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                color: #6c757d;
                font-weight: bold;
                font-size: {s(8)}pt;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                color: #495057;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
            }}
        """)
        self.search_result_label = QLabel()
        self.search_result_label.setFont(QFont(get_system_font(), s(8)))
        self.search_result_label.setStyleSheet(f"""
            QLabel {{
                color: #6c757d;
                padding: {s(4)}px;
                font-size: {s(8)}pt;
                background: transparent;
                border: none;
            }}
        """)
        self.search_result_label.setVisible(False)
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.clear_search_btn)
        search_layout.addWidget(self.search_result_label)
        
        search_container.setLayout(search_layout)
        return search_container
    
    def on_search_text_changed(self, text):
        
        self.clear_search_btn.setVisible(bool(text))
        
        if text.strip():
            self.filter_parameters(text.strip())
        else:
            self.show_all_parameters()
    
    def clear_search(self):
        
        self.search_input.clear()
        self.show_all_parameters()
    
    def filter_parameters(self, search_text):
        
        visible_count = 0
        for widget in self.param_widgets:
            if self.matches_search(widget.param_info, search_text):
                widget.setVisible(True)
                self.highlight_search_match(widget, search_text)
                visible_count += 1
            else:
                widget.setVisible(False)
        self.rebuild_layout_order()

        if visible_count > 0:
            self.search_result_label.setText(t('messages.search_found_matches', visible_count))
            self.search_result_label.setStyleSheet(f"""
                QLabel {{
                    color: #28a745;
                    padding: {s(4)}px;
                    font-size: {s(8)}pt;
                    background: transparent;
                    border: none;
                }}
            """)
        else:
            self.search_result_label.setText(t('messages.search_no_matches'))
            self.search_result_label.setStyleSheet(f"""
                QLabel {{
                    color: #dc3545;
                    padding: {s(4)}px;
                    font-size: {s(8)}pt;
                    background: transparent;
                    border: none;
                }}
            """)
        self.search_result_label.setVisible(True)
    
    def matches_search(self, param_info, search_text):
        
        search_text = search_text.lower()
        return (search_text in param_info.get('param_name', '').lower() or
                search_text in param_info.get('display_name', '').lower() or
                search_text in param_info.get('description', '').lower())
    
    def setup_drag_drop(self):
        
        self.setAcceptDrops(True)
    
    def setup_context_menu(self):
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_section_context_menu)
    
    def show_section_context_menu(self, position):
        
        menu = QMenu(self)
        menu.setStyleSheet(get_modern_qmenu_stylesheet())
        
        add_checkbox_action = menu.addAction("✅ " + t('actions.add_checkbox'))
        add_checkbox_action.triggered.connect(lambda: self.add_new_parameter('1'))
        
        add_input_action = menu.addAction("📝 " + t('actions.add_input'))
        add_input_action.triggered.connect(lambda: self.add_new_parameter('2'))
        
        menu.exec(self.mapToGlobal(position))
    
    def add_new_parameter(self, param_type):
        
        new_param = {
            'param_name': f'new_param_{len(self.param_widgets)}',
            'display_name': '新参数',
            'description': '',
            'type': param_type,
            'required': False,
            'default': '',
            'help': ''
        }
        
        dialog = ParameterEditDialog(new_param, self)
        if dialog.exec() == QDialog.Accepted:
            param_info = dialog.get_param_info()
            
            param_widget = ParameterWidget(param_info)
            self.param_widgets.append(param_widget)
            
            self.update_layout()
            
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.add_parameter_to_section(param_info, self.title)
    
    def get_tool_operation_page(self):
        
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == 'ToolOperationPage':
                return parent
            parent = parent.parent()
        return None
    
    def update_layout(self):
        
        self.setUpdatesEnabled(False)
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        self.param_widgets = []
        for param in self.params:
            param_widget = ParameterWidget(param)
            self.param_widgets.append(param_widget)
        self.setup_ui()
        self.setUpdatesEnabled(True)
    
    def get_all_params(self):
        
        all_params = []
        for widget in self.param_widgets:
            param_list = widget.get_param_string()
            if param_list:
                all_params.extend(param_list)
        return all_params
        
    def validate_required_params(self):
        
        missing_params = []
        for widget in self.param_widgets:
            if widget.is_required() and not widget.is_filled():
                missing_params.append(widget.get_display_name())
        return len(missing_params) == 0, missing_params
        
    def update_all_required_styles(self):
        
        for widget in self.param_widgets:
            widget.update_required_style()
            
    def show_all_parameters(self):
        
        if hasattr(self, 'search_result_label'):
            self.search_result_label.setVisible(False)
        for widget in self.param_widgets:
            widget.setVisible(True)
            self.clear_highlight(widget)
        self.rebuild_layout_order()
    
    def rebuild_layout_order(self):
        
        if not hasattr(self, 'grid_layout') or not self.grid_layout:
            return
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                self.grid_layout.removeItem(item)
        row, col = 0, 0
        for param in self.params:

            param_widget = None
            for widget in self.param_widgets:
                if widget.param_info['param_name'] == param['param_name']:
                    param_widget = widget
                    break
            
            if param_widget and param_widget.isVisible():
                if param.get('type') == '1':
                    self.grid_layout.addWidget(param_widget, row, col)
                    col += 1
                    if col >= 4:
                        col = 0
                        row += 1
                else:
                    self.grid_layout.addWidget(param_widget, row, col, 1, 2)
                    col += 2
                    if col >= 4:
                        col = 0
                        row += 1
        if col != 0:
            row += 1
        self.grid_layout.setRowStretch(row, 1)
        
    def highlight_search_match(self, param_widget, search_text):
        
        param_widget.setStyleSheet(f"""
            ParameterWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #fff8e1, stop: 1 #ffecb3);
                border: 1px solid #ffc107;
                border-radius: {s(4)}px;
                margin: {s(1)}px;
            }}
        """)
        
    def clear_highlight(self, param_widget):
        
        param_widget.setStyleSheet("")
        param_widget.update_required_style()
    
    def dragEnterEvent(self, event):
        
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("parameter_widget_data:"):
                event.acceptProposedAction()
            elif event.mimeData().hasFormat('application/x-wct-parameter'):
                event.acceptProposedAction()
        
    def dragMoveEvent(self, event):
        
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("parameter_widget_data:"):
                event.acceptProposedAction()
            elif event.mimeData().hasFormat('application/x-wct-parameter'):
                event.acceptProposedAction()

    def dropEvent(self, event):
        
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("parameter_widget_data:"):
                try:

                    json_data = text[len("parameter_widget_data:"):]
                    drag_data = json.loads(json_data)
                    
                    param_info = drag_data.get('param_info', {})
                    source_section = drag_data.get('source_section', '')
                    if source_section != self.title:
                        self.handle_cross_section_drop(param_info, source_section, event.position())
                    else:

                        self.reorder_parameters(param_info['param_name'], event.position())
                    
                    event.acceptProposedAction()
                except Exception as e:
                    print(f"拖拽处理失败: {e}")
                    event.ignore()
        elif event.mimeData().hasFormat('application/x-wct-parameter'):

            param_name = bytes(event.mimeData().data('application/x-wct-parameter')).decode()

            event.acceptProposedAction()
        else:
            event.ignore()
    
    def handle_cross_section_drop(self, param_info, source_section, drop_position):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        new_param_info = param_info.copy()
        if self.title == t('tabs.checkbox_params'):
            new_param_info['type'] = '1'
        elif self.title == t('tabs.input_params'):
            new_param_info['type'] = '2'
        target_index = self.calculate_drop_index(drop_position)
        self.params.insert(target_index, new_param_info)
        self.update_layout()
        if hasattr(tool_page, 'remove_parameter_from_section'):
            tool_page.remove_parameter_from_section(param_info['param_name'], source_section)
        if hasattr(tool_page, 'move_parameter_between_sections'):
            tool_page.move_parameter_between_sections(param_info, source_section, self.title)
        if hasattr(tool_page, 'save_and_reload_ui'):
            tool_page.save_and_reload_ui()

    def reorder_parameters(self, dragged_param_name, drop_position):
        
        dragged_index = -1
        for i, param in enumerate(self.params):
            if param['param_name'] == dragged_param_name:
                dragged_index = i
                break
        if dragged_index == -1:
            return
        target_index = self.calculate_drop_index(drop_position)
        if target_index == dragged_index:
            return
        if target_index > dragged_index:
            target_index -= 1
        param = self.params.pop(dragged_index)
        self.params.insert(target_index, param)
        self.update_layout()
        tool_page = self.get_tool_operation_page()
        if tool_page and hasattr(tool_page, 'sync_parameter_order'):
            new_order = [p['param_name'] for p in self.params]
            tool_page.sync_parameter_order(self.title, new_order)
        if tool_page and hasattr(tool_page, 'save_and_reload_ui'):
            tool_page.save_and_reload_ui()

    def calculate_drop_index(self, drop_position):
        
        drop_point = drop_position.toPoint() if hasattr(drop_position, 'toPoint') else drop_position
        if not self.param_widgets:
            return 0
        min_distance = float('inf')
        target_index = len(self.param_widgets)
        for i, widget in enumerate(self.param_widgets):
            widget_center = widget.rect().center()
            widget_global_center = widget.mapToGlobal(widget_center)
            widget_local_center = self.mapFromGlobal(widget_global_center)
            distance = (widget_local_center - drop_point).manhattanLength()
            if distance < min_distance:
                min_distance = distance
                if drop_point.y() < widget_local_center.y() or \
                   (drop_point.y() == widget_local_center.y() and drop_point.x() < widget_local_center.x()):
                    target_index = i
                else:
                    target_index = i + 1
        return min(target_index, len(self.param_widgets))
class ToolParameterTab(QWidget):
    def __init__(self, config_data):
        super().__init__()
        self.config_data = config_data or {}
        self.sections = []
        self.setup_ui()
    
    def setup_ui(self):
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(s(16), s(16), s(16), s(16))
        layout.setSpacing(s(12))
        
        section_created = False
        if self.config_data:
            for section_name, params in self.config_data.items():
                if section_name in ['勾选项区', '输入框区']:
                    if params:
                        section_title = t('tabs.checkbox_params') if section_name == '勾选项区' else t('tabs.input_params')
                        section = ParameterSection(section_title, params)
                        self.sections.append(section)
                        layout.addWidget(section)
                        section_created = True
                    
        if not section_created:
            empty_label = QLabel(t('messages.no_param_config'))
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"""
                QLabel {{
                    color: #6c757d;
                    font-size: {s(14)}pt;
                    padding: {s(50)}px;
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #f8f9fa, stop: 1 #f1f3f4);
                    border: 1px dashed #dee2e6;
                    border-radius: {s(8)}px;
                    font-family: '{get_system_font()}';
                }}
            """)
            layout.addWidget(empty_label)
                
        layout.addStretch()
        content_widget.setLayout(layout)
        
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
    def get_all_params(self):
        
        all_params = []
        for section in self.sections:
            section_params = section.get_all_params()
            all_params.extend(section_params)
        return all_params
    
    def validate_required_params(self):
        
        all_missing = []
        for section in self.sections:
            is_valid, missing = section.validate_required_params()
            if not is_valid:
                all_missing.extend(missing)
        return len(all_missing) == 0, all_missing
    
    def update_all_required_styles(self):
        
        for section in self.sections:
            section.update_all_required_styles()