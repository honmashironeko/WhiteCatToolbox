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
from .widgets import ClickableLabel
from .styles import get_modern_qmenu_stylesheet, get_parameter_section_style, get_parameter_search_style
from .theme import colors, fonts, params
from .i18n import t
class ParameterEditDialog(QDialog):
    
    
    def __init__(self, param_info, parent=None):
        super().__init__(parent)
        self.param_info = param_info.copy()

        self.name_edit = None
        self.display_edit = None
        self.desc_edit = None
        self.type_combo = None
        self.required_checkbox = None
        self.setup_ui()
        
    def setup_ui(self):
        
        self.setWindowTitle(t("edit_param_info"))
        self.setFixedSize(s(460), s(480))
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        main_container = QWidget()
        main_container.setObjectName("main_container")
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(s(24), s(20), s(24), s(20))
        layout.setSpacing(s(20))
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(t("edit_param_info"))
        title_label.setObjectName("title")
        title_label.setFont(QFont(get_system_font(), s(14), QFont.Bold))
        
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(s(28), s(28))
        close_btn.setFont(QFont(get_system_font(), s(12)))
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        layout.addLayout(header_layout)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(s(16))

        name_container = self.create_simple_field(
            t("param_name_label"), 
            self.param_info.get('param_name', ''),
            "--output-file"
        )
        form_layout.addWidget(name_container)
        
        display_container = self.create_simple_field(
            t("display_name_label"), 
            self.param_info.get('display_name', ''),
            "Output File"
        )
        form_layout.addWidget(display_container)
        
        desc_container = self.create_textarea_field(
            t("param_desc_label"),
            self.param_info.get('description', ''),
            "Describe what this parameter does..."
        )
        form_layout.addWidget(desc_container)
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(s(12))
        type_container = self.create_combo_field(
            t("param_type_label"),
            [t("checkbox_option"), t("input_option")],
            0 if self.param_info.get('type', '1') == '1' else 1
        )
        settings_layout.addWidget(type_container)
        self.required_checkbox = QCheckBox(t("required_param_checkbox"))
        self.required_checkbox.setObjectName("required_checkbox")
        self.required_checkbox.setChecked(self.param_info.get('required', False))
        self.required_checkbox.setFont(QFont(get_system_font(), s(10)))
        settings_layout.addWidget(self.required_checkbox)
        
        form_layout.addLayout(settings_layout)
        layout.addLayout(form_layout)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(s(10))
        button_layout.addStretch()
        
        cancel_btn = QPushButton(t("cancel_button"))
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setFixedSize(s(80), s(32))
        cancel_btn.setFont(QFont(get_system_font(), s(9)))
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton(t("save_button"))
        save_btn.setObjectName("save_btn") 
        save_btn.setFixedSize(s(80), s(32))
        save_btn.setFont(QFont(get_system_font(), s(9), QFont.Bold))
        save_btn.clicked.connect(self.save_and_close)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(s(12), s(12), s(12), s(12))
        dialog_layout.addWidget(main_container)
        self.apply_clean_styles()
    
    def create_simple_field(self, label, value, placeholder):
        
        container = QWidget()
        container.setObjectName("field_container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(s(6))
        label_widget = QLabel(label)
        label_widget.setObjectName("field_label")
        label_widget.setFont(QFont(get_system_font(), s(10), QFont.Medium))
        input_widget = QLineEdit(value)
        input_widget.setObjectName("field_input")
        input_widget.setPlaceholderText(placeholder)
        input_widget.setFixedHeight(s(32))
        input_widget.setMinimumWidth(s(250))
        input_widget.setFont(QFont(get_system_font(), s(9)))
        
        layout.addWidget(label_widget)
        layout.addWidget(input_widget)

        label_text = label.lower()
        if "param_name" in label_text or "参数名" in label_text:
            self.name_edit = input_widget
        elif "display_name" in label_text or "显示名" in label_text:
            self.display_edit = input_widget
            
        return container
    
    def create_textarea_field(self, label, value, placeholder):
        
        container = QWidget()
        container.setObjectName("field_container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(s(6))
        label_widget = QLabel(label)
        label_widget.setObjectName("field_label")
        label_widget.setFont(QFont(get_system_font(), s(10), QFont.Medium))
        self.desc_edit = QTextEdit(value)
        self.desc_edit.setObjectName("field_textarea")
        self.desc_edit.setPlaceholderText(placeholder)
        self.desc_edit.setFixedHeight(s(70))
        self.desc_edit.setFont(QFont(get_system_font(), s(9)))
        
        layout.addWidget(label_widget)
        layout.addWidget(self.desc_edit)
        
        return container
    
    def create_combo_field(self, label, items, current_index):
        
        container = QWidget()
        container.setObjectName("field_container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(s(6))
        label_widget = QLabel(label)
        label_widget.setObjectName("field_label")
        label_widget.setFont(QFont(get_system_font(), s(10), QFont.Medium))
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("field_combo")
        self.type_combo.addItems(items)
        self.type_combo.setCurrentIndex(current_index)
        self.type_combo.setFixedHeight(s(32))
        self.type_combo.setFont(QFont(get_system_font(), s(9)))
        self.type_combo.setStyleSheet("")
        
        layout.addWidget(label_widget)
        layout.addWidget(self.type_combo)
        
        return container
    
    def apply_clean_styles(self):
        
        self.setStyleSheet(f"""
            
            QWidget#main_container {{
                background: {colors["white"]};
                border: 1px solid {colors["border_light"]};
                border-radius: {s(8)}px;
            }}
            
            
            QLabel#title {{
                color: {colors["text"]};
                font-weight: 600;
            }}
            
            
            QPushButton#close_btn {{
                background: transparent;
                border: 1px solid {colors["border_light"]};
                border-radius: {s(14)}px;
                color: {colors["text_secondary"]};
                font-weight: bold;
            }}
            
            QPushButton#close_btn:hover {{
                background: {colors["background_light"]};
                border-color: {colors["border"]};
                color: {colors["text"]};
            }}
            
            
            QLabel#field_label {{
                color: {colors["text"]};
                font-weight: 500;
            }}
            
            
            QLineEdit#field_input {{
                background: {colors["white"]};
                border: 1px solid {colors["border_light"]};
                border-radius: {s(4)}px;
                padding: {s(8)}px {s(10)}px;
                color: {colors["text"]};
                selection-background-color: {colors["secondary"]};
            }}
            
            QLineEdit#field_input:focus {{
                border-color: {colors["secondary"]};
                outline: none;
            }}
            
            QLineEdit#field_input:hover {{
                border-color: {colors["border"]};
            }}
            
            
            QTextEdit#field_textarea {{
                background: {colors["white"]};
                border: 1px solid {colors["border_light"]};
                border-radius: {s(4)}px;
                padding: {s(8)}px {s(10)}px;
                color: {colors["text"]};
                selection-background-color: {colors["secondary"]};
            }}
            
            QTextEdit#field_textarea:focus {{
                border-color: {colors["secondary"]};
                outline: none;
            }}
            
            QTextEdit#field_textarea:hover {{
                border-color: {colors["border"]};
            }}
            
            
            QComboBox#field_combo {{
                background: {colors["white"]};
                border: 1px solid {colors["border_light"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(8)}px {s(10)}px;
                color: {colors["text"]};
                font-size: {s(9)}pt;
                font-weight: normal;
                min-height: {s(16)}px;
            }}
            
            QComboBox#field_combo:hover {{
                border-color: {colors["secondary"]};
                background: {colors["background_light"]};
            }}
            
            QComboBox#field_combo:focus {{
                border-color: {colors["secondary"]};
                outline: none;
            }}
            
            QComboBox#field_combo::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: {s(20)}px;
                border: none;
                border-left: 1px solid {colors["border_light"]};
                border-radius: 0 {params["border_radius_small"]} {params["border_radius_small"]} 0;
                background: transparent;
            }}
            
            QComboBox#field_combo::drop-down:hover {{
                background: {colors["secondary"]};
                border-left-color: {colors["secondary"]};
            }}
            
            QComboBox#field_combo::down-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw1IDVMOSAxIiBzdHJva2U9IiM2NjciIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
                width: {s(10)}px;
                height: {s(6)}px;
            }}
            
            QComboBox#field_combo::down-arrow:hover {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw1IDVMOSAxIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMS41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
            }}
            
            QComboBox#field_combo QAbstractItemView {{
                border: 0px;
                outline: 0px;
                background: {colors["white"]};
                border-radius: {params["border_radius_small"]};
                padding: 0px;
                margin: 0px;
                alternate-background-color: transparent;
                show-decoration-selected: 0;
            }}
            
            QComboBox#field_combo QAbstractItemView:focus {{
                outline: 0;
            }}
            
            QComboBox#field_combo QAbstractItemView::item {{
                background: transparent;
                border: none;
                border-radius: {params["border_radius_very_small"]};
                padding: {s(8)}px {s(10)}px;
                margin: {s(1)}px;
                font-size: {s(9)}pt;
            }}
            
            QComboBox#field_combo QAbstractItemView::item:hover {{
                background: {colors["list_item_hover_background"]};
            }}
            
            QComboBox#field_combo QAbstractItemView::item:selected {{
                background: {colors["secondary"]};
                color: {colors["text_on_primary"]};
            }}
            
            
            QCheckBox#required_checkbox {{
                color: {colors["text"]};
                font-weight: 500;
                spacing: {s(8)}px;
            }}
            
            QCheckBox#required_checkbox::indicator {{
                width: {s(16)}px;
                height: {s(16)}px;
                border-radius: {s(3)}px;
                border: 1px solid {colors["border"]};
                background: {colors["white"]};
            }}
            
            QCheckBox#required_checkbox::indicator:hover {{
                border-color: {colors["secondary"]};
                background: {colors["background_very_light"]};
            }}
            
            QCheckBox#required_checkbox::indicator:checked {{
                background: {colors["secondary"]};
                border-color: {colors["secondary"]};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEwIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgM0wzIDZMOSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
            }}
            
            
            QPushButton#cancel_btn {{
                background: {colors["white"]};
                color: {colors["text_secondary"]};
                border: 1px solid {colors["border"]};
                border-radius: {s(4)}px;
                font-weight: 500;
            }}
            
            QPushButton#cancel_btn:hover {{
                background: {colors["background_light"]};
                color: {colors["text"]};
            }}
            
            QPushButton#cancel_btn:pressed {{
                background: {colors["background_gray"]};
            }}
            
            QPushButton#save_btn {{
                background: {colors["secondary"]};
                color: white;
                border: none;
                border-radius: {s(4)}px;
                font-weight: 600;
            }}
            
            QPushButton#save_btn:hover {{
                background: {colors["secondary_hover"]};
            }}
            
            QPushButton#save_btn:pressed {{
                background: {colors["secondary_pressed"]};
            }}
        """)
    
    def create_header(self):
        
        header = QWidget()
        header.setFixedHeight(s(70))
        header.setObjectName("header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(s(30), s(20), s(20), s(20))
        title_container = QVBoxLayout()
        title_container.setSpacing(s(2))
        
        title_label = QLabel(t("edit_param_info"))
        title_label.setObjectName("title")
        title_label.setFont(QFont(get_system_font(), s(18), QFont.Bold))
        
        subtitle_label = QLabel("Configure parameter settings")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setFont(QFont(get_system_font(), s(10)))
        
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(s(36), s(36))
        close_btn.setFont(QFont(get_system_font(), s(16)))
        close_btn.clicked.connect(self.reject)
        
        layout.addLayout(title_container)
        layout.addStretch()
        layout.addWidget(close_btn)
        
        return header
    
    def create_content_area(self):
        
        content = QWidget()
        content.setObjectName("content")
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(s(30), s(30), s(30), s(20))
        layout.setSpacing(s(24))
        self.name_edit = self.create_input_field(
            "🏷️", t("param_name_label"), 
            self.param_info.get('param_name', ''),
            "e.g., --output-file"
        )
        layout.addWidget(self.name_edit)
        self.display_edit = self.create_input_field(
            "📝", t("display_name_label"), 
            self.param_info.get('display_name', ''),
            "e.g., Output File"
        )
        layout.addWidget(self.display_edit)
        desc_container = self.create_textarea_field(
            "📋", t("param_desc_label"),
            self.param_info.get('description', ''),
            "Describe what this parameter does..."
        )
        layout.addWidget(desc_container)
        settings_row = QHBoxLayout()
        settings_row.setSpacing(s(16))
        type_container = self.create_combo_field(
            "⚙️", t("param_type_label"),
            [t("checkbox_option"), t("input_option")],
            0 if self.param_info.get('type', '1') == '1' else 1
        )
        settings_row.addWidget(type_container)
        required_container = self.create_checkbox_field(
            "🔒", t("required_param_checkbox"),
            self.param_info.get('required', False)
        )
        settings_row.addWidget(required_container)
        
        layout.addLayout(settings_row)
        layout.addStretch()
        
        return content
    
    def create_footer(self):
        
        footer = QWidget()
        footer.setFixedHeight(s(80))
        footer.setObjectName("footer")
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(s(30), s(20), s(30), s(20))
        layout.setSpacing(s(12))
        
        layout.addStretch()
        cancel_btn = QPushButton(t("cancel_button"))
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setFixedSize(s(100), s(40))
        cancel_btn.setFont(QFont(get_system_font(), s(10), QFont.Medium))
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton(t("save_button"))
        save_btn.setObjectName("save_btn") 
        save_btn.setFixedSize(s(100), s(40))
        save_btn.setFont(QFont(get_system_font(), s(10), QFont.Bold))
        save_btn.clicked.connect(self.save_and_close)
        
        layout.addWidget(cancel_btn)
        layout.addWidget(save_btn)
        
        return footer
    
    def create_input_field(self, icon, label, value, placeholder):
        
        container = QWidget()
        container.setObjectName("field_container")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(s(8))
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setFixedSize(s(20), s(20))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont(get_system_font(), s(12)))
        
        label_widget = QLabel(label)
        label_widget.setObjectName("field_label")
        label_widget.setFont(QFont(get_system_font(), s(11), QFont.Medium))
        
        label_layout.addWidget(icon_label)
        label_layout.addWidget(label_widget)
        label_layout.addStretch()
        input_widget = QLineEdit(value)
        input_widget.setObjectName("field_input")
        input_widget.setPlaceholderText(placeholder)
        input_widget.setFixedHeight(s(44))
        input_widget.setMinimumWidth(s(280))
        input_widget.setFont(QFont(get_system_font(), s(10)))
        
        layout.addLayout(label_layout)
        layout.addWidget(input_widget)
        if "param_name" in label:
            self.name_edit = input_widget
        elif "display_name" in label:
            self.display_edit = input_widget
            
        return container
    
    def save_and_close(self):

        if not self.name_edit or not self.display_edit:
            QMessageBox.warning(self, t("warning"), t("controls_not_initialized"))
            return
            
        if not self.name_edit.text().strip() or not self.display_edit.text().strip():
            QMessageBox.warning(self, t("warning"), t("warning_empty_name"))
            return
        self.accept()
    
    def get_param_info(self):

        if not all([self.name_edit, self.display_edit, self.desc_edit, self.type_combo, self.required_checkbox]):
            return self.param_info.copy()
            
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
            description = self.param_info['description']

            from PySide6.QtGui import QFontMetrics
            font = QFont(get_system_font(), s(9))
            fm = QFontMetrics(font)
            max_width = s(400)
            wrapped_lines = []
            words = description.split(' ')
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if fm.horizontalAdvance(test_line) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        wrapped_lines.append(current_line)
                        current_line = word
                    else:

                        wrapped_lines.append(word)
                        current_line = ""
            
            if current_line:
                wrapped_lines.append(current_line)
            
            description = "<br/>".join(wrapped_lines)
            
            tooltip_text = f"<b style='color: #4a90e2; font-size: {s(10)}pt;'>{self.param_info['param_name']}</b><br/><span style='color: #6c757d; font-size: {s(9)}pt;'>{description}</span>"
        
        if self.param_info.get('required', False):
            required_text = f"<br/><span style='color: #dc3545; font-size: {s(9)}pt; font-weight: bold;'>{t('required_param_tip')}</span>"
            tooltip_text += required_text
        
        drag_tip = f"<br/><span style='color: #17a2b8; font-size: {s(8)}pt;'>{t('drag_reorder_tip')}</span>"
        tooltip_text += drag_tip
        
        return tooltip_text
    
    def setup_ui(self):
        
        layout = QHBoxLayout()  
        layout.setSpacing(s(2))  
        layout.setContentsMargins(s(2), s(2), s(2), s(2))  
        drag_icon = QLabel("")
        drag_icon.setFixedSize(0, 0)
        drag_icon.setAlignment(Qt.AlignCenter)
        drag_icon.setStyleSheet(f"""
            QLabel {{
                color: {colors["text_disabled"]};
                font-weight: bold;
                font-size: {s(8)}pt;
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        drag_icon.setToolTip(t("drag_reorder_tooltip"))
        layout.addWidget(drag_icon)
        
        param_type = self.param_info['type']
        is_required = self.param_info.get('required', False)
        
        if param_type == '1':
            display_text = self.param_info['display_name']
            self.control = ClickableLabel(display_text)
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
                
        elif param_type == '2':
            label_text = self.param_info['display_name'] + ":"
                
            name_label = QLabel(label_text)
            name_label.setFont(QFont(get_system_font(), s(8), QFont.Bold))
            name_label.setWordWrap(True)  
            name_label.setMinimumWidth(s(80))
            name_label.setMaximumWidth(s(120))
            name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)  
            
            label_style = f"""
                QLabel {{
                    color: {colors["text_secondary"]};
                    font-weight: 900;
                    padding: {s(2)}px {s(4)}px;
                }}
            """
            
            if is_required:
                label_style = f"""
                    QLabel {{
                        color: {colors["text_secondary"]};
                        font-weight: 900;
                        padding: {s(2)}px {s(4)}px;
                        border-left: 3px solid {colors["danger"]};
                        padding-left: {s(6)}px;
                    }}
                """
            name_label.setStyleSheet(label_style)
            
            tooltip = self.create_tooltip()
            if tooltip:
                name_label.setToolTip(tooltip)
            layout.addWidget(name_label, 0)
            
            self.control = QLineEdit()
            self.control.setFont(QFont(get_system_font(), s(8)))
            self.control.setMinimumHeight(s(32))
            self.control.setMinimumWidth(s(150))
            self.control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            
            placeholder_text = t("input_value_placeholder")
            if is_required:
                placeholder_text = t("required_input_placeholder")
                
            self.control.setPlaceholderText(placeholder_text)
            if is_required:
                self.control.textChanged.connect(self.update_required_style)
                self.update_required_style()
            else:
                normal_style = f"""
                    QLineEdit {{
                        background-color: {colors["white"]};
                        border: 1px solid {colors["border"]};
                        border-radius: {params["border_radius_very_small"]};
                        padding: {s(6)}px {s(10)}px;
                        color: {colors["text"]};
                        font-size: {s(8)}pt;
                        selection-background-color: {colors["secondary"]};
                    }}
                    QLineEdit:focus {{
                        border-color: {colors["secondary"]};
                        background-color: {colors["background_very_light"]};
                    }}
                    QLineEdit:hover {{
                        border-color: {colors["border_light"]};
                    }}
                """
                self.control.setStyleSheet(normal_style)
                
            tooltip = self.create_tooltip()
            if tooltip:
                self.control.setToolTip(tooltip)
        else:

            self.control = ClickableLabel(self.param_info['display_name'])
            tooltip = self.create_tooltip()
            if tooltip:
                self.control.setToolTip(tooltip)
            
        layout.addWidget(self.control, 1)
        if param_type == '1':
            self.setMinimumHeight(s(36))  
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  
        else:
            self.setMinimumHeight(s(32))  
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  
        self.setStyleSheet("""
            ParameterWidget {
                border-radius: 4px;
                background: transparent;
            }
            ParameterWidget:hover {
                background-color: rgba(74, 144, 226, 0.08);
                border: 1px dashed #4a90e2;
            }
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
                                color: {colors["danger"]};
                                font-family: '{get_system_font()}';
                                font-weight: 900;
                                font-size: {s(8)}pt;
                                padding: {s(2)}px;
                            }}
                        """
                    else:
                        label_style = f"""
                            QLabel {{
                                color: {colors["text_secondary"]};
                                font-family: '{get_system_font()}';
                                font-weight: 900;
                                font-size: {s(8)}pt;
                                padding: {s(2)}px;
                            }}
                        """
                    label.setStyleSheet(label_style)
                    break
            placeholder_text = t("input_value_placeholder")
            if is_required:
                placeholder_text = t("required_input_placeholder")
            self.control.setPlaceholderText(placeholder_text)
            if is_required:
                if is_filled:

                    normal_style = f"""
                        QLineEdit {{
                            background-color: {colors["white"]};
                            border: 1px solid {colors["success"]};
                            border-radius: {params["border_radius_very_small"]};
                            padding: {s(6)}px {s(10)}px;
                            color: {colors["text"]};
                            font-size: {s(8)}pt;
                            selection-background-color: {colors["secondary"]};
                            font-family: '{get_system_font()}';
                        }}
                        QLineEdit:focus {{
                            border-color: {colors["success"]};
                            background-color: {colors["background_very_light"]};
                        }}
                        QLineEdit:hover {{
                            border-color: {colors["success_hover"]};
                        }}
                    """
                    self.control.setStyleSheet(normal_style)
                else:

                    error_style = f"""
                        QLineEdit {{
                            background-color: {colors["danger_very_light"]};
                            border: 2px solid {colors["danger"]};
                            border-radius: {params["border_radius_very_small"]};
                            padding: {s(6)}px {s(10)}px;
                            color: {colors["text"]};
                            font-size: {s(8)}pt;
                            selection-background-color: {colors["secondary"]};
                            font-family: '{get_system_font()}';
                        }}
                        QLineEdit:focus {{
                            border-color: {colors["danger"]};
                            background-color: {colors["white"]};
                        }}
                        QLineEdit:hover {{
                            border-color: {colors["danger_hover"]};
                        }}
                    """
                    self.control.setStyleSheet(error_style)
            else:

                normal_style = f"""
                    QLineEdit {{
                        background-color: {colors["white"]};
                        border: 1px solid {colors["border_light"]};
                        border-radius: {params["border_radius_very_small"]};
                        padding: {s(6)}px {s(10)}px;
                        color: {colors["text"]};
                        font-size: {s(8)}pt;
                        selection-background-color: {colors["secondary"]};
                        font-family: '{get_system_font()}';
                    }}
                    QLineEdit:focus {{
                        border-color: {colors["secondary"]};
                        background-color: {colors["background_very_light"]};
                    }}
                    QLineEdit:hover {{
                        border-color: {colors["border"]};
                    }}
                """
                self.control.setStyleSheet(normal_style)
    
    def setup_context_menu(self):
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        
        menu = QMenu(self)
        menu.setStyleSheet(get_modern_qmenu_stylesheet())
        menu.setFixedWidth(s(200))
        edit_action = menu.addAction("✏️  " + t("edit_param_action"))
        edit_action.triggered.connect(self.edit_parameter)
        
        required_text = t("unset_required_action") if self.is_required() else t("set_required_action")
        required_icon = "🔓  " if self.is_required() else "🔒  "
        required_action = menu.addAction(required_icon + required_text)
        required_action.triggered.connect(self.toggle_required)
        
        menu.addSeparator()
        
        section = self.get_section()
        if section:
            tool_page = section.get_tool_operation_page()
            if tool_page:
                current_type = self.param_info.get('type')
                if current_type == '1':
                    move_action = menu.addAction("📝  " + t("move_to_input_action"))
                    move_action.triggered.connect(
                        lambda: tool_page.move_parameter_between_sections(self.param_info, t("checkbox_section_title"), t("input_section_title"))
                    )
                else:
                    move_action = menu.addAction("☑️  " + t("move_to_checkbox_action"))
                    move_action.triggered.connect(
                        lambda: tool_page.move_parameter_between_sections(self.param_info, t("input_section_title"), t("checkbox_section_title"))
                    )
                    
                menu.addSeparator()

                current_tab = tool_page.param_tabs.tabText(tool_page.param_tabs.currentIndex())
                if current_tab == t("all_params"):
                    copy_action = menu.addAction("📋  " + t("copy_to_common_action"))
                    copy_action.triggered.connect(lambda: tool_page.copy_parameter_to_common(self.param_info))
                elif current_tab == t("common_params"):
                    remove_action = menu.addAction("🗑️  " + t("remove_from_common_action"))
                    remove_action.triggered.connect(lambda: tool_page.remove_parameter_from_common(self.param_info))
                    
                menu.addSeparator()
                
        menu.exec(self.mapToGlobal(position))
    
    def edit_parameter(self):
        
        old_param_name = self.param_info.get('param_name')
        old_param_info = self.param_info.copy()
        dialog = ParameterEditDialog(self.param_info, self)
        if dialog.exec() == QDialog.Accepted:
            new_param_info = dialog.get_param_info()
            if new_param_info:

                params_changed = False
                for key in ['param_name', 'display_name', 'description', 'type', 'required']:
                    if old_param_info.get(key) != new_param_info.get(key):
                        params_changed = True
                        break
                
                if params_changed:
                    self.param_info.update(new_param_info)

                    self.update_ui_from_param_info()

                    section = self.get_section()
                    if section:
                        tool_page = section.get_tool_operation_page()
                        if tool_page and hasattr(tool_page, 'sync_required_status'):

                            from PySide6.QtCore import QTimer
                            QTimer.singleShot(50, lambda: tool_page.sync_required_status(self.param_info['param_name'], self.param_info.get('required', False)))

                        if tool_page and hasattr(tool_page, 'update_parameter_in_config'):

                            from PySide6.QtCore import QTimer
                            QTimer.singleShot(100, lambda: tool_page.update_parameter_in_config(old_param_name, self.param_info))
                else:

                    section = self.get_section()
                    if section:
                        tool_page = section.get_tool_operation_page()
                        if tool_page and hasattr(tool_page, 'system_log_tab'):
                            tool_page.system_log_tab.append_system_log(t("param_no_changes"), "info")
    
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

        try:
            current_type = self.param_info.get('type', '1')

            if hasattr(self, '_last_type') and self._last_type != current_type:
                self._last_type = current_type
                self._rebuild_ui()
                return

            self._last_type = current_type

            tooltip_text = self.create_tooltip()
            
            if current_type == '1':
                if hasattr(self, 'control') and self.control:
                    display_text = self.param_info.get('display_name', '')
                    self.control.setText(display_text)
                    self.control.setToolTip(tooltip_text)
            elif current_type == '2':

                layout = self.layout()
                if layout:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, QLabel) and hasattr(widget, 'text'):

                                label_text = self.param_info.get('display_name', '') + ":"
                                widget.setText(label_text)
                                widget.setToolTip(tooltip_text)
                                break

                if hasattr(self, 'control') and self.control:
                    self.control.setToolTip(tooltip_text)

            self.update_required_style()
            
        except Exception as e:

            print(f"优化更新失败，回退到完全重建: {e}")
            self._rebuild_ui()
    
    def _rebuild_ui(self):
        
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
        return t("unknown_area_text")
    
    def get_display_value(self):
        
        param_type = self.param_info['type']
        
        if param_type == '1':
            return t("selected_text") if self.control.isChecked() else t("unselected_text")
        elif param_type == '2':
            value = self.control.text().strip()
            return value if value else t("not_set_text")
        
        return t("unknown_text")
    
    def move_parameter(self, from_tab, to_tab):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        if hasattr(tool_page, 'show_custom_question'):
            if tool_page.show_custom_question(
                t("move_confirm"), 
                t("move_question").format(param=self.param_info['display_name'], from_tab=from_tab, to_tab=to_tab)
            ):
                tool_page.move_parameter_between_tabs(self.param_info, from_tab, to_tab)
    
    def remove_from_common(self):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        if hasattr(tool_page, 'show_custom_question'):
            if tool_page.show_custom_question(
                t("remove_confirm"), 
                t("remove_question").format(param=self.param_info['display_name'])
            ):
                tool_page.remove_parameter_from_common(self.param_info)
    
    def copy_to_common(self):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        if hasattr(tool_page, 'show_custom_question'):
            if tool_page.show_custom_question(
                t("add_confirm"), 
                t("add_question").format(param=self.param_info['display_name'])
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
            if self.isVisible() and self.width() > 0 and self.height() > 0:
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
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_group = QGroupBox(self.title)
        main_group.setFont(QFont(get_system_font(), s(10), QFont.Bold))
        main_group.setStyleSheet(get_parameter_section_style())

        section_content_layout = QVBoxLayout(main_group)
        section_content_layout.setContentsMargins(s(8), s(25), s(8), s(12))
        section_content_layout.setSpacing(s(8))

        search_widget = self.create_search_bar()
        section_content_layout.addWidget(search_widget)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(s(8))
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
                if col % 2 != 0:
                    row += 1
                    col = 0
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
        self.search_input.setPlaceholderText(t("search_params_placeholder"))
        self.search_input.setFont(QFont(get_system_font(), s(9)))
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.search_input.setStyleSheet(get_parameter_search_style())
        self.clear_search_btn = QPushButton("✕")
        self.clear_search_btn.setFont(QFont(get_system_font(), s(8)))
        self.clear_search_btn.setFixedSize(s(24), s(24))
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.clear_search_btn.setVisible(False)  
        self.clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-radius: {s(12)}px;
                background-color: {colors["background_gray"]};
                color: {colors["text_secondary"]};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors["border_light"]};
                color: {colors["text"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["border"]};
            }}
        """)
        self.search_result_label = QLabel()
        self.search_result_label.setFont(QFont(get_system_font(), s(8)))
        self.search_result_label.setStyleSheet(f"color: {colors['text_secondary']}; padding: {s(4)}px;")
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
        visible_widgets = []
        
        for widget in self.param_widgets:
            if self.matches_search(widget.param_info, search_text):
                widget.setVisible(True)
                self.highlight_search_match(widget, search_text)
                visible_widgets.append(widget)
                visible_count += 1
            else:
                widget.setVisible(False)
        
        self.reorganize_layout(visible_widgets)
        
        if visible_count > 0:
            self.search_result_label.setText(t("found_matches").format(count=visible_count))
            self.search_result_label.setStyleSheet(f"color: {colors['success']}; padding: {s(4)}px;")
        else:
            self.search_result_label.setText(t("no_matches"))
            self.search_result_label.setStyleSheet(f"color: {colors['danger']}; padding: {s(4)}px;")
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
        menu.setFixedWidth(s(200))
        
        add_checkbox_action = menu.addAction("☑️  " + t("add_checkbox_action"))
        add_checkbox_action.triggered.connect(lambda: self.add_new_parameter('1'))
        
        add_input_action = menu.addAction("📝  " + t("add_input_action"))
        add_input_action.triggered.connect(lambda: self.add_new_parameter('2'))
        
        menu.exec(self.mapToGlobal(position))
    
    def add_new_parameter(self, param_type):
        
        new_param = {
            'param_name': f'new_param_{len(self.param_widgets)}',
            'display_name': t('new_param_name'),
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
    
    def reorganize_visible_widgets(self, visible_widgets):
        
        self.reorganize_layout(visible_widgets)
            
    def show_all_parameters(self):
        
        if hasattr(self, 'search_result_label'):
            self.search_result_label.setVisible(False)

        for widget in self.param_widgets:
            widget.setVisible(True)
            self.clear_highlight(widget)
        
        self.reorganize_layout()
        
    def highlight_search_match(self, param_widget, search_text):
        
        param_widget.setStyleSheet(f"""
            ParameterWidget {{
                background-color: {colors["background_very_light"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {params["border_radius_very_small"]};
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
                    print(f"{t('drag_failed_error')}: {e}")
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
        if self.title == t("checkbox_section_title"):
            new_param_info['type'] = '1'
        elif self.title == t("input_section_title"):
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
    
    def reorganize_layout(self, visible_widgets=None):
        
        if visible_widgets is None:
            visible_widgets = [widget for widget in self.param_widgets if widget.isVisible()]
        
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                self.grid_layout.removeWidget(item.widget())
        
        row, col = 0, 0
        for widget in visible_widgets:
            if widget.param_info.get('type') == '1':
                self.grid_layout.addWidget(widget, row, col)
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
            else:
                if col % 2 != 0:
                    row += 1
                    col = 0
                self.grid_layout.addWidget(widget, row, col, 1, 2)
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
        layout.setContentsMargins(s(8), s(16), s(8), s(16))
        layout.setSpacing(s(12))
        global_search_container = self.create_global_search_bar()
        layout.addWidget(global_search_container)
        
        section_created = False
        if self.config_data:
            for section_name, params in self.config_data.items():
                if section_name in ["勾选项区", "输入框区"]:
                    if params:
                        section_title = t("checkbox_section_title") if section_name == "勾选项区" else t("input_section_title")
                        section = ParameterSection(section_title, params)
                        self.sections.append(section)
                        layout.addWidget(section)
                        section_created = True
                    
        if not section_created:
            empty_label = QLabel(t("no_param_config"))
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["text_secondary"]};
                    font-size: {s(14)}pt;
                    padding: {s(50)}px;
                    background-color: {colors["background_very_light"]};
                    border: 1px dashed {colors["border_light"]};
                    border-radius: {params["border_radius_small"]};
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
    
    def create_global_search_bar(self):
        
        search_container = QWidget()
        search_container.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(8)}px;
            }}
        """)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_icon = QLabel(t("global_search"))
        search_icon.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        search_icon.setStyleSheet(f"color: {colors['text_secondary']}; border: none; background: transparent;")
        search_icon.setMinimumWidth(s(60))
        search_icon.setMaximumWidth(s(100))
        search_icon.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText(t("global_search_placeholder"))
        self.global_search_input.setFont(QFont(fonts["system"], s(10)))
        self.global_search_input.setMinimumHeight(s(36))
        self.global_search_input.setMinimumWidth(s(200))
        self.global_search_input.textChanged.connect(self.on_global_search_changed)
        self.global_search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(4)}px {s(12)}px;
                font-size: {s(10)}pt;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors["secondary"]};
                background-color: {colors["white"]};
            }}
        """)
        
        self.global_clear_btn = QPushButton(t("clear_search"))
        self.global_clear_btn.setFont(QFont(get_system_font(), s(8)))
        self.global_clear_btn.setMinimumSize(s(60), s(28))
        self.global_clear_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.global_clear_btn.clicked.connect(self.clear_global_search)
        self.global_clear_btn.setVisible(False)  
        
        self.global_clear_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #6c757d;
                border-radius: 4px;
                background-color: #ffffff;
                color: #6c757d;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #495057;
                color: #495057;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)
        
        self.global_result_label = QLabel()
        self.global_result_label.setFont(QFont(get_system_font(), s(8)))
        self.global_result_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        self.global_result_label.setVisible(False)
        
        search_mode_label = QLabel(t("search_mode"))
        search_mode_label.setFont(QFont(get_system_font(), s(8)))
        search_mode_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems([t("smart_search"), t("exact_search"), t("regex_search")])
        self.search_mode_combo.setFont(QFont(get_system_font(), s(9)))
        self.search_mode_combo.setMinimumHeight(s(36))
        self.search_mode_combo.currentIndexChanged.connect(self.on_search_mode_changed)
        self.search_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(6)}px {s(12)}px;
                min-width: {s(80)}px;
                color: {colors["text_secondary"]};
                font-weight: 500;
                min-height: {s(20)}px;
            }}
            
            QComboBox:hover {{
                border-color: {colors["secondary"]};
                background: {colors["list_item_hover_background"]};
                color: {colors["text"]};
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
                background: transparent;
            }}
            
            QComboBox::drop-down:hover {{
                background: {colors["secondary"]};
                border-left-color: {colors["secondary"]};
            }}
            
            QComboBox QAbstractItemView {{
                border: 0px;
                outline: 0px;
                background: {colors["white"]};
                border-radius: {params["border_radius_small"]};
                padding: 0px;
                margin: 0px;
                alternate-background-color: transparent;
                show-decoration-selected: 0;
            }}
            
            QComboBox QAbstractItemView:focus {{
                outline: 0;
            }}
            
            QComboBox QAbstractItemView::item {{
                background: transparent;
                border: none;
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(8)}px;
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
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.global_search_input, 1)
        search_layout.addWidget(self.global_clear_btn)
        search_layout.addWidget(search_mode_label)
        search_layout.addWidget(self.search_mode_combo)
        search_layout.addWidget(self.global_result_label)
        
        search_container.setLayout(search_layout)
        return search_container
    
    def on_global_search_changed(self, text):
        
        self.global_clear_btn.setVisible(bool(text))
        
        if text.strip():
            self.perform_global_search(text.strip())
        else:
            self.clear_all_search_highlights()
    
    def clear_global_search(self):
        
        self.global_search_input.clear()
        self.clear_all_search_highlights()
    
    def on_search_mode_changed(self, mode):
        
        search_text = self.global_search_input.text().strip()
        if search_text:
            self.perform_global_search(search_text)
    
    def perform_global_search(self, search_text):
        
        total_matches = 0
        total_params = 0
        search_mode = self.search_mode_combo.currentText()

        for section in self.sections:
            section_matches = self.search_in_section(section, search_text, search_mode)
            total_matches += section_matches
            total_params += len(section.param_widgets)

        if total_matches == 0:
            self.global_result_label.setText(t("no_match_found"))
            self.global_result_label.setStyleSheet("color: #dc3545; border: none; background: transparent; font-weight: 500;")
        else:
            self.global_result_label.setText(f"{t('found_count')} {total_matches}/{total_params} {t('parameters_count')}")
            self.global_result_label.setStyleSheet("color: #28a745; border: none; background: transparent; font-weight: 500;")
        
        self.global_result_label.setVisible(True)
    
    def search_in_section(self, section, search_text, search_mode):
        
        matches = 0
        visible_widgets = []
        
        for param_widget in section.param_widgets:
            is_match = False
            
            if search_mode == t("smart_search"):
                is_match = self.smart_search_match(param_widget.param_info, search_text.lower())
            elif search_mode == t("exact_search"):
                is_match = self.exact_search_match(param_widget.param_info, search_text)
            elif search_mode == t("regex_search"):
                is_match = self.regex_search_match(param_widget.param_info, search_text)
            
            if is_match:
                param_widget.setVisible(True)
                section.highlight_search_match(param_widget, search_text.lower())
                visible_widgets.append(param_widget)
                matches += 1
            else:
                param_widget.setVisible(False)
                section.clear_highlight(param_widget)
        
        section.reorganize_layout(visible_widgets)
        return matches
    
    def smart_search_match(self, param_info, search_text):

        fields_to_search = [
            param_info.get('param_name', ''),
            param_info.get('display_name', ''),
            param_info.get('description', ''),
            param_info.get('help', ''),
            str(param_info.get('default', ''))
        ]
        
        for field in fields_to_search:
            if search_text in field.lower():
                return True
        return False
    
    def exact_search_match(self, param_info, search_text):
        
        fields_to_search = [
            param_info.get('param_name', ''),
            param_info.get('display_name', ''),
            param_info.get('description', ''),
            param_info.get('help', ''),
            str(param_info.get('default', ''))
        ]
        
        for field in fields_to_search:
            if search_text == field:
                return True
        return False
    
    def regex_search_match(self, param_info, search_text):
        
        try:
            import re
            pattern = re.compile(search_text, re.IGNORECASE)
            
            fields_to_search = [
                param_info.get('param_name', ''),
                param_info.get('display_name', ''),
                param_info.get('description', ''),
                param_info.get('help', ''),
                str(param_info.get('default', ''))
            ]
            
            for field in fields_to_search:
                if pattern.search(field):
                    return True
        except re.error:
            
            return self.smart_search_match(param_info, search_text.lower())
        
        return False
    
    def clear_all_search_highlights(self):

        for section in self.sections:
            section.show_all_parameters()
        
        self.global_result_label.setVisible(False)