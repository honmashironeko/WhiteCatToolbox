import sys
import os
import subprocess
import threading
import platform
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget,
    QListWidget, QTabWidget, QLabel, QPushButton, QCheckBox, QLineEdit,
    QTextEdit, QGroupBox, QScrollArea, QGridLayout,
    QSplitter, QFrame, QToolTip, QSizePolicy, QDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QMenu, QComboBox,
    QSpacerItem, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QProcess, QTimer, QMimeData, QPoint, QUrl
from PySide6.QtGui import QFont, QPalette, QColor, QDrag, QPainter, QPixmap, QDesktopServices, QIcon
import json
import configparser
import zipfile
import datetime
import shutil

def get_system_font():
    
    system = platform.system()
    if system == "Windows":
        return "Microsoft YaHei"
    elif system == "Darwin":  
        return "PingFang SC"
    else:  
        return "DejaVu Sans"

def get_monospace_font():
    
    system = platform.system()
    if system == "Windows":
        return "Consolas"
    elif system == "Darwin":  
        return "Monaco"
    else:  
        return "DejaVu Sans Mono"

def get_system_font_css():
    
    system_font = get_system_font()
    return f"font-family: '{system_font}', Arial, sans-serif;"

def get_monospace_font_css():
    
    mono_font = get_monospace_font()
    return f"font-family: '{mono_font}', 'Consolas', 'Monaco', 'Courier New', monospace;"

def build_cross_platform_command(tool_path, user_command, params):
    
    command_parts = user_command.split()
    system = platform.system()
    
    if len(command_parts) >= 2 and command_parts[0] in ["python", "python3"]:
        
        script_name = command_parts[1]
        full_script_path = os.path.join(tool_path, script_name)
        return [command_parts[0], full_script_path] + command_parts[2:] + params
    elif len(command_parts) >= 1:
        
        exe_name = command_parts[0]
        
        
        if system == "Windows" and not exe_name.endswith(('.exe', '.bat', '.cmd')):
            
            exe_with_ext = exe_name + '.exe'
            exe_path_with_ext = os.path.join(tool_path, exe_with_ext)
            if os.path.exists(exe_path_with_ext):
                full_exe_path = exe_path_with_ext
            else:
                full_exe_path = os.path.join(tool_path, exe_name)
        else:
            full_exe_path = os.path.join(tool_path, exe_name)
        
        return [full_exe_path] + command_parts[1:] + params
    else:
        raise ValueError("无法解析运行命令")

class ClickableLabel(QLabel):
    
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.checked = False
        self.setFont(QFont(get_system_font(), 8, QFont.Medium))
        self.setCursor(Qt.PointingHandCursor)
        self.setWordWrap(True)  
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  
        self.update_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
        super().mousePressEvent(event)
    
    def toggle(self):
        
        self.checked = not self.checked
        self.update_style()
    
    def isChecked(self):
        
        return self.checked
    
    def setChecked(self, checked):
        
        self.checked = checked
        self.update_style()
        
        if hasattr(self, 'parent_widget') and hasattr(self.parent_widget, 'update_required_style'):
            self.parent_widget.update_required_style()
    
    def update_style(self):
        
        is_required = hasattr(self, 'is_required') and self.is_required
        
        if self.checked:
            if is_required:
                
                base_style = """
                    QLabel {
                        background-color: #28a745;
                        border: 1px solid #28a745;
                        border-left: 3px solid #155724;
                        border-radius: 6px;
                        padding: 8px 12px;
                        color: white;
                        font-weight: 600;
                        min-height: 20px;
                    }
                    QLabel:hover {
                        background-color: #218838;
                        border-color: #1e7e34;
                        border-left: 3px solid #155724;
                    }
                """
            else:
                
                base_style = """
                    QLabel {
                        background-color: #4a90e2;
                        border: 1px solid #4a90e2;
                        border-radius: 6px;
                        padding: 8px 12px;
                        color: white;
                        font-weight: 600;
                        min-height: 20px;
                    }
                """
            self.setStyleSheet(base_style)
        else:
            if is_required:
                
                base_style = """
                    QLabel {
                        background-color: #fff5f5;
                        border: 2px solid #dc3545;
                        border-left: 4px solid #dc3545;
                        border-radius: 6px;
                        padding: 8px 12px;
                        color: #721c24;
                        font-weight: 600;
                        min-height: 20px;

                    }
                    QLabel:hover {
                        background-color: #ffe6e6;
                        border-color: #c82333;
                        border-left: 4px solid #c82333;
                        color: #5a1a1f;
                    }
                """
            else:
                
                base_style = """
                    QLabel {
                        background-color: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 6px;
                        padding: 8px 12px;
                        color: #495057;
                        font-weight: 500;
                        min-height: 20px;
                    }
                    QLabel:hover {
                        background-color: #e3f2fd;
                        border-color: #4a90e2;
                        color: #2c5aa0;
                    }
                """
            self.setStyleSheet(base_style)

class TemplateManager(QDialog):
    
    
    def __init__(self, tool_name, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.parent_page = parent
        self.templates = self.load_templates()
        self.setup_ui()
        self.load_template_list()
        self.setup_global_styles()
    
    def setup_ui(self):
        self.setWindowTitle(f"模板管理")
        self.setGeometry(150, 150, 900, 600)
        self.setModal(True)
        
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        
        main_card = QWidget()
        main_card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafbfc);
                border-radius: 16px;
                border: 1px solid #e1e8ed;
            }
        """)
        
        
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(20)
        
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        
        title_label = QLabel("📋 模板管理")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                font-weight: 700;
                padding: 4px 0px;
            }
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        
        add_btn = QPushButton("✨ 添加模板")
        add_btn.setMinimumSize(110, 38)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: 10px;
                padding: 8px 16px;
                color: white;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }
        """)
        add_btn.clicked.connect(self.save_current_params)
        header_layout.addWidget(add_btn)
        
        card_layout.addLayout(header_layout)
        
        
        self.template_table = QTableWidget()
        self.template_table.setColumnCount(3)
        self.template_table.setHorizontalHeaderLabels(["模板名称", "模板备注", "操作"])
        
        
        self.template_table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafafa);
                border: 1px solid #e1e8ed;
                border-radius: 12px;
                gridline-color: #f0f0f0;
                selection-background-color: transparent;
                font-size: 13pt;
                outline: none;
                alternate-background-color: #f9f9fa;
            }
            QTableWidget::item {
                padding: 18px 16px;
                border-bottom: 1px solid #f0f0f0;
                border-right: none;
                border-left: none;
                border-top: none;
                background-color: transparent;
            }
            QTableWidget::item:hover {
                background-color: rgba(74, 144, 226, 0.05);
            }
            QTableWidget::item:selected {
                background-color: rgba(74, 144, 226, 0.1);
                border-radius: 6px;
            }
            /* 确保按钮容器不受表格样式影响 */
            QTableWidget QWidget {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QHeaderView::section {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                color: #495057;
                padding: 14px 16px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-right: 1px solid #e5e5ea;
                font-weight: 600;
                font-size: 12pt;
                text-align: center;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QHeaderView::section:first {
                border-top-left-radius: 12px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 12px;
            }
            QHeaderView::section:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
            }
        """)
        
        
        self.template_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.template_table.setSelectionMode(QTableWidget.NoSelection)
        self.template_table.verticalHeader().setVisible(False)
        self.template_table.horizontalHeader().setStretchLastSection(False)
        self.template_table.setShowGrid(False)
        self.template_table.setSortingEnabled(False)
        
        
        self.template_table.verticalHeader().setDefaultSectionSize(76)
        
        
        header = self.template_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)             
        header.setSectionResizeMode(1, QHeaderView.Stretch)           
        header.setSectionResizeMode(2, QHeaderView.Fixed)             
        header.resizeSection(0, 200)  
        header.resizeSection(2, 120)  
        
        card_layout.addWidget(self.template_table)
        
        main_card.setLayout(card_layout)
        layout.addWidget(main_card)
        
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)
        
        
        import_btn = QPushButton("📥 导入模板")
        import_btn.setMinimumSize(110, 38)
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: 10px;
                padding: 8px 16px;
                color: #495057;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #343a40;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #6c757d;
}
        """)
        import_btn.clicked.connect(self.import_template)
        bottom_layout.addWidget(import_btn)
        
        
        export_btn = QPushButton("📤 导出模板")
        export_btn.setMinimumSize(110, 38)
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: 10px;
                padding: 8px 16px;
                color: #495057;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #343a40;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #6c757d;
}
        """)
        export_btn.clicked.connect(self.export_template)
        bottom_layout.addWidget(export_btn)
        
        bottom_layout.addStretch()
        
        
        close_btn = QPushButton("❌ 关闭")
        close_btn.setMinimumSize(90, 38)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: 10px;
                padding: 8px 16px;
                color: #6c757d;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #495057;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #6c757d;
}
        """)
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
    
    def setup_global_styles(self):
        
        
        app_style = """
            /* 修复QMessageBox黑框问题 */
            QMessageBox {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 12px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                color: #1d1d1f;
            }
            QMessageBox QLabel {
                background-color: transparent;
                color: #1d1d1f;
                font-size: 13pt;
                padding: 16px;
                border: none;
            }
            QMessageBox QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                color: white;
                font-weight: 500;
                font-size: 13pt;
                min-width: 80px;
                min-height: 32px;
                margin: 4px;
            }
            QMessageBox QPushButton:hover {
                background-color: #0056CC;
            }
            QMessageBox QPushButton:pressed {
                background-color: #004499;
            }
            QMessageBox QPushButton[text="取消"], 
            QMessageBox QPushButton[text="Cancel"],
            QMessageBox QPushButton[text="No"] {
                background-color: #f2f2f7;
                color: #007AFF;
                border: 1px solid #d1d1d6;
            }
            QMessageBox QPushButton[text="取消"]:hover,
            QMessageBox QPushButton[text="Cancel"]:hover,
            QMessageBox QPushButton[text="No"]:hover {
                background-color: #e5e5ea;
                border-color: #007AFF;
            }
            
            /* 修复QInputDialog黑框问题 */
            QInputDialog {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 12px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
                color: #1d1d1f;
            }
            QInputDialog QLabel {
                background-color: transparent;
                color: #1d1d1f;
                font-size: 13pt;
                padding: 16px 16px 8px 16px;
                border: none;
            }
            QInputDialog QLineEdit {
                background-color: #f2f2f7;
                border: 1px solid #d1d1d6;
                border-radius: 8px;
                padding: 8px 12px;
                color: #1d1d1f;
                font-size: 13pt;
                margin: 8px 16px;
                selection-background-color: #007AFF;
            }
            QInputDialog QLineEdit:focus {
                border-color: #007AFF;
                background-color: #ffffff;
            }
            QInputDialog QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                color: white;
                font-weight: 500;
                font-size: 13pt;
                min-width: 80px;
                min-height: 32px;
                margin: 4px;
            }
            QInputDialog QPushButton:hover {
                background-color: #0056CC;
            }
            QInputDialog QPushButton:pressed {
                background-color: #004499;
            }
            QInputDialog QPushButton[text="取消"],
            QInputDialog QPushButton[text="Cancel"] {
                background-color: #f2f2f7;
                color: #007AFF;
                border: 1px solid #d1d1d6;
            }
            QInputDialog QPushButton[text="取消"]:hover,
            QInputDialog QPushButton[text="Cancel"]:hover {
                background-color: #e5e5ea;
                border-color: #007AFF;
            }
            
            /* 修复QFileDialog黑框问题 */
            QFileDialog {
                background-color: #ffffff;
                color: #1d1d1f;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
            QFileDialog QListView {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                color: #1d1d1f;
            }
            QFileDialog QTreeView {
                background-color: #ffffff;
                border: 1px solid #e5e5ea;
                border-radius: 6px;
                color: #1d1d1f;
            }
            QFileDialog QPushButton {
                background-color: #007AFF;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-weight: 500;
                min-height: 28px;
            }
            QFileDialog QPushButton:hover {
                background-color: #0056CC;
            }
            QFileDialog QPushButton[text="取消"],
            QFileDialog QPushButton[text="Cancel"] {
                background-color: #f2f2f7;
                color: #007AFF;
                border: 1px solid #d1d1d6;
            }
        """
        
        
        if self.parent():
            app = self.parent().parentWidget().parent() if hasattr(self.parent(), 'parentWidget') else QApplication.instance()
        else:
            app = QApplication.instance()
        
        if app:
            current_style = app.styleSheet()
            app.setStyleSheet(current_style + app_style)
    
    def create_shadow_effect(self):
        
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 40))
        return shadow
    
    def show_custom_message(self, title, message, msg_type="info"):
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(450, 240)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: 16px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
        """)
        layout.addWidget(title_label)
        
        
        msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(12)
        
        
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        if "成功" in title or "完成" in title:
            icon_label.setText("✅")
            icon_label.setStyleSheet("font-size: 20pt;")
        elif "错误" in title or "失败" in title:
            icon_label.setText("❌")
            icon_label.setStyleSheet("font-size: 20pt;")
        elif "提示" in title or "信息" in title:
            icon_label.setText("💡")
            icon_label.setStyleSheet("font-size: 20pt;")
        else:
            icon_label.setText("ℹ️")
            icon_label.setStyleSheet("font-size: 20pt;")
        
        msg_layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Microsoft YaHei", 11))
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setStyleSheet("""
            QLabel {
                color: #495057;
                background: transparent;
                border: none;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        msg_layout.addWidget(msg_label, 1)
        
        msg_container.setLayout(msg_layout)
        layout.addWidget(msg_container)
        
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(100, 40)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        
        
        
        dialog.exec()
    
    def show_custom_question(self, title, message):
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(500, 260)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: 16px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
        """)
        layout.addWidget(title_label)
        
        
        msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(12)
        
        
        icon_label = QLabel("❓")
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 20pt;")
        msg_layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Microsoft YaHei", 11))
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setStyleSheet("""
            QLabel {
                color: #495057;
                background: transparent;
                border: none;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        msg_layout.addWidget(msg_label, 1)
        
        msg_container.setLayout(msg_layout)
        layout.addWidget(msg_container)
        
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumSize(90, 40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: 10px;
                color: #6c757d;
                font-weight: 500;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #495057;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #6c757d;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(90, 40)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        
        
        
        return dialog.exec() == QDialog.Accepted
    
    def show_custom_input(self, title, label_text, placeholder="", default_text=""):
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(520, 300)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: 16px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
        """)
        layout.addWidget(title_label)
        
        
        label = QLabel(label_text)
        label.setFont(QFont("Microsoft YaHei", 11))
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignLeft)
        label.setStyleSheet("""
            QLabel {
                color: #495057;
                background: transparent;
                border: none;
                padding: 8px 0px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(label)
        
        
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #ffffff);
                border: 2px solid #e9ecef;
                border-radius: 12px;
                padding: 4px;
            }
        """)
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(8, 8, 8, 8)
        
        input_edit = QLineEdit()
        input_edit.setPlaceholderText(placeholder)
        input_edit.setText(default_text)
        input_edit.setFont(QFont("Microsoft YaHei", 11))
        input_edit.setMinimumHeight(44)
        input_edit.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 12px 16px;
                color: #2c3e50;
                font-size: 12pt;
                selection-background-color: #4A90E2;
                selection-color: white;
            }
            QLineEdit:focus {
                background-color: #ffffff;
            }
        """)
        
        input_layout.addWidget(input_edit)
        input_container.setLayout(input_layout)
        layout.addWidget(input_container)
        
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumSize(90, 40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: 10px;
                color: #6c757d;
                font-weight: 500;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #495057;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #6c757d;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(90, 40)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        
        
        
        
        input_edit.setFocus()
        input_edit.selectAll()
        
        
        def on_focus_in():
            input_container.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #ffffff, stop: 1 #f8f9fa);
                    border: 2px solid #4A90E2;
                    border-radius: 12px;
                    padding: 4px;
                }
            """)
        
        def on_focus_out():
            input_container.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #f8f9fa, stop: 1 #ffffff);
                    border: 2px solid #e9ecef;
                    border-radius: 12px;
                    padding: 4px;
                }
            """)
        
        
        input_edit.focusInEvent = lambda e: (on_focus_in(), QLineEdit.focusInEvent(input_edit, e))[1]
        input_edit.focusOutEvent = lambda e: (on_focus_out(), QLineEdit.focusOutEvent(input_edit, e))[1]
        
        if dialog.exec() == QDialog.Accepted:
            return input_edit.text().strip(), True
        return "", False
    
    def load_templates(self):
        
        try:
            import json
            import os
            
            
            templates_dir = "templates"
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            
            template_file = os.path.join(templates_dir, f"templates_{self.tool_name}.json")
            with open(template_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"加载模板失败: {e}")
            return {}
    
    def save_templates(self):
        
        try:
            import json
            import os
            
            
            templates_dir = "templates"
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            
            template_file = os.path.join(templates_dir, f"templates_{self.tool_name}.json")
            with open(template_file, "w", encoding="utf-8") as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存模板失败: {e}")
            self.show_custom_message("错误", f"保存模板失败: {e}")
    
    def load_template_list(self):
        
        self.template_table.setRowCount(len(self.templates))
        
        for row, (template_id, template_data) in enumerate(self.templates.items()):
            
            name_text = template_data.get('name', '未命名模板')
            name_item = QTableWidgetItem(name_text)
            name_item.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
            name_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            name_item.setForeground(QColor("#2c3e50"))
            name_item.setToolTip("双击可编辑模板名称")
            self.template_table.setItem(row, 0, name_item)
            
            
            remark_text = template_data.get('remark', '暂无备注')
            if not remark_text.strip():
                remark_text = '暂无备注'
            remark_item = QTableWidgetItem(remark_text)
            remark_item.setFont(QFont("Microsoft YaHei", 11, QFont.Normal))
            remark_item.setForeground(QColor("#8e8e93"))
            remark_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            remark_item.setToolTip("双击可编辑模板备注")
            self.template_table.setItem(row, 1, remark_item)
            
            
            button_container = QWidget()
            button_container.setStyleSheet("""
                QWidget { 
                    background: transparent; 
                    border: none; 
                    margin: 0px; 
                    padding: 0px;
                }
            """)
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(2, 2, 2, 2)
            button_layout.setSpacing(3)
            button_layout.setAlignment(Qt.AlignCenter)
            
            
            apply_btn = QPushButton("应用")
            apply_btn.setFixedSize(42, 28)
            apply_btn.setCursor(Qt.PointingHandCursor)
            apply_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #4A90E2, stop: 1 #357ABD);
                    border: 1px solid #2C5AA0;
                    border-radius: 6px;
                    color: white;
                    font-size: 9pt;
                    font-weight: 600;
                    font-family: 'Microsoft YaHei';
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #5BA0F2, stop: 1 #4A90E2);
                    border-color: #4A90E2;
}
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #357ABD, stop: 1 #2C5AA0);
                    border-color: #1E3A5F;
}
            """)
            apply_btn.setToolTip("应用此模板")
            apply_btn.clicked.connect(lambda checked, tid=template_id: self.apply_template_by_id(tid))
            button_layout.addWidget(apply_btn)
            
            
            delete_btn = QPushButton("删除")
            delete_btn.setFixedSize(42, 28)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #FF3B30, stop: 1 #D70015);
                    border: 1px solid #C5001A;
                    border-radius: 6px;
                    color: white;
                    font-size: 9pt;
                    font-weight: 600;
                    font-family: 'Microsoft YaHei';
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #FF5544, stop: 1 #FF3B30);
                    border-color: #FF3B30;
}
                QPushButton:pressed {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #D70015, stop: 1 #A30000);
                    border-color: #8B0000;
}
            """)
            delete_btn.setToolTip("删除此模板")
            delete_btn.clicked.connect(lambda checked, tid=template_id: self.delete_template_by_id(tid))
            button_layout.addWidget(delete_btn)
            
            self.template_table.setCellWidget(row, 2, button_container)
            
            
            name_item.setData(Qt.UserRole, template_id)
        
        
        self.template_table.itemDoubleClicked.connect(self.on_item_double_clicked)
    
    def on_item_double_clicked(self, item):
        
        column = item.column()
        row = item.row()
        name_item = self.template_table.item(row, 0)
        
        if not name_item:
            return
            
        template_id = name_item.data(Qt.UserRole)
        if template_id not in self.templates:
            return
            
        if column == 0:  
            self.edit_template_name(template_id)
        elif column == 1:  
            self.edit_template_remark(template_id)
        elif column == 2:  
            self.apply_template_by_id(template_id)
    
    def save_current_params(self):
        
        if not self.parent_page:
            self.show_custom_message("错误", "无法获取当前参数")
            return
        
        
        name, ok = self.show_custom_input("保存模板", "请输入模板名称:", "请输入模板名称")
        if not ok or not name.strip():
            return
        
        
        remark, ok = self.show_custom_input("保存模板", "请输入备注 (可选):", "可选，描述模板用途")
        if not ok:
            remark = ""
        
        
        current_params = {}
        if hasattr(self.parent_page, 'param_tabs'):
            current_tab = self.parent_page.param_tabs.currentWidget()
            if current_tab:
                for section in current_tab.sections:
                    for param_widget in section.param_widgets:
                        param_name = param_widget.param_info['param_name']
                        if isinstance(param_widget.control, (QCheckBox, ClickableLabel)):
                            current_params[param_name] = {
                                'type': 'checkbox',
                                'value': param_widget.control.isChecked()
                            }
                        elif isinstance(param_widget.control, QLineEdit):
                            current_params[param_name] = {
                                'type': 'text',
                                'value': param_widget.control.text()
                            }

        
        import datetime
        template_id = f"template_{int(datetime.datetime.now().timestamp())}"
        
        
        self.templates[template_id] = {
            'name': name.strip(),
            'remark': remark.strip(),
            'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'params': current_params
        }
        
        self.save_templates()
        self.load_template_list()
        
        self.show_custom_message("成功", f"模板 '{name}' 保存成功！")
    
    def apply_template(self):
        
        current_row = self.template_table.currentRow()
        if current_row < 0:
            self.show_custom_message("提示", "请先选择要应用的模板")
            return
        
        
        name_item = self.template_table.item(current_row, 0)
        template_id = name_item.data(Qt.UserRole)
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        template_data = self.templates[template_id]
        params = template_data.get('params', {})
        
        
        if not self.show_custom_question("确认应用", 
                                        f"确定要应用模板 '{template_data['name']}' 吗？\n这将覆盖当前的参数设置。"):
            return
        
        
        applied_count = 0
        if hasattr(self.parent_page, 'param_tabs'):
            current_tab = self.parent_page.param_tabs.currentWidget()
            if current_tab:
                for section in current_tab.sections:
                    for param_widget in section.param_widgets:
                        param_name = param_widget.param_info['param_name']
                        if param_name in params:
                            param_data = params[param_name]
                            param_type = param_data['type']
                            param_value = param_data['value']
                            
                            if param_type == 'checkbox' and isinstance(param_widget.control, (QCheckBox, ClickableLabel)):
                                param_widget.control.setChecked(param_value)
                                applied_count += 1
                            elif param_type == 'text' and isinstance(param_widget.control, QLineEdit):
                                param_widget.control.setText(str(param_value))
                                applied_count += 1
                
                
                current_tab.update_all_required_styles()
        
        
        import datetime
        self.templates[template_id]['last_used'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        self.save_templates()
        self.load_template_list()
        
        self.show_custom_message("应用成功", 
                                f"模板 '{template_data['name']}' 应用成功！\n共应用了 {applied_count} 个参数。")
        self.close()
    
    def refresh_template_list(self):
        
        self.templates = self.load_templates()
        self.load_template_list()
    
    def apply_template_by_id(self, template_id):
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        template_data = self.templates[template_id]
        params = template_data.get('params', {})
        
        
        if not self.show_custom_question("确认应用", 
                                        f"确定要应用模板 '{template_data['name']}' 吗？\n这将覆盖当前的参数设置。"):
            return
        
        
        applied_count = 0
        if hasattr(self.parent_page, 'param_tabs'):
            current_tab = self.parent_page.param_tabs.currentWidget()
            if current_tab:
                for section in current_tab.sections:
                    for param_widget in section.param_widgets:
                        param_name = param_widget.param_info['param_name']
                        if param_name in params:
                            param_data = params[param_name]
                            param_type = param_data['type']
                            param_value = param_data['value']
                            
                            if param_type == 'checkbox' and isinstance(param_widget.control, (QCheckBox, ClickableLabel)):
                                param_widget.control.setChecked(param_value)
                                applied_count += 1
                            elif param_type == 'text' and isinstance(param_widget.control, QLineEdit):
                                param_widget.control.setText(str(param_value))
                                applied_count += 1
                
                
                current_tab.update_all_required_styles()
        
        
        import datetime
        self.templates[template_id]['last_used'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        self.save_templates()
        self.load_template_list()
        
        self.show_custom_message("应用成功", 
                                f"模板 '{template_data['name']}' 应用成功！\n共应用了 {applied_count} 个参数。")
        self.close()
    
    def edit_template_by_id(self, template_id):
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        template_data = self.templates[template_id]
        
        
        new_name, ok = self.show_custom_input("编辑模板", 
                                             "请输入新的模板名称:", 
                                             "请输入模板名称",
                                             template_data.get('name', ''))
        if not ok or not new_name.strip():
            return
        
        
        new_remark, ok = self.show_custom_input("编辑模板", 
                                               "请输入新的备注 (可选):", 
                                               "可选，描述模板用途",
                                               template_data.get('remark', ''))
        if not ok:
            new_remark = template_data.get('remark', '')
        
        
        self.templates[template_id]['name'] = new_name.strip()
        self.templates[template_id]['remark'] = new_remark.strip()
        
        
        self.save_templates()
        self.load_template_list()
        
        self.show_custom_message("编辑成功", f"模板 '{new_name}' 编辑成功！")
    
    def edit_template_name(self, template_id):
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        template_data = self.templates[template_id]
        current_name = template_data.get('name', '')
        
        
        new_name, ok = self.show_custom_input("编辑模板名称", 
                                             "请输入新的模板名称:", 
                                             "请输入模板名称",
                                             current_name)
        if not ok or not new_name.strip():
            return
        
        
        self.templates[template_id]['name'] = new_name.strip()
        
        
        self.save_templates()
        self.load_template_list()
        
        self.show_custom_message("编辑成功", f"模板名称已更新为 '{new_name.strip()}'")
    
    def edit_template_remark(self, template_id):
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        template_data = self.templates[template_id]
        current_remark = template_data.get('remark', '')
        
        
        new_remark, ok = self.show_custom_input("编辑模板备注", 
                                               "请输入新的备注信息:", 
                                               "可选，描述模板用途",
                                               current_remark)
        if not ok:
            return
        
        
        self.templates[template_id]['remark'] = new_remark.strip()
        
        
        self.save_templates()
        self.load_template_list()
        
        remark_text = new_remark.strip() if new_remark.strip() else "暂无备注"
        self.show_custom_message("编辑成功", f"模板备注已更新为 '{remark_text}'")
    
    def delete_template_by_id(self, template_id):
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        template_name = self.templates[template_id].get('name', '未命名')
        
        
        if not self.show_custom_question("确认删除", 
                                        f"确定要删除模板 '{template_name}' 吗？\n此操作不可恢复！"):
            return
        
        
        del self.templates[template_id]
        self.save_templates()
        self.load_template_list()
        
        self.show_custom_message("删除成功", f"模板 '{template_name}' 删除成功！")
    
    def edit_template(self):
        
        current_row = self.template_table.currentRow()
        if current_row < 0:
            self.show_custom_message("提示", "请先选择要编辑的模板")
            return
        
        
        name_item = self.template_table.item(current_row, 0)
        template_id = name_item.data(Qt.UserRole)
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        template_data = self.templates[template_id]
        
        
        new_name, ok = self.show_custom_input("编辑模板", 
                                             "请输入新的模板名称:", 
                                             "请输入模板名称",
                                             template_data.get('name', ''))
        if not ok or not new_name.strip():
            return
        
        
        new_remark, ok = self.show_custom_input("编辑模板", 
                                               "请输入新的备注 (可选):", 
                                               "可选，描述模板用途",
                                               template_data.get('remark', ''))
        if not ok:
            new_remark = template_data.get('remark', '')
        
        
        self.templates[template_id]['name'] = new_name.strip()
        self.templates[template_id]['remark'] = new_remark.strip()
        
        
        self.save_templates()
        self.load_template_list()
        
        self.show_custom_message("编辑成功", f"模板 '{new_name}' 编辑成功！")
    
    def show_template_info(self, template_id):
        
        if template_id not in self.templates:
            return
            
        template_data = self.templates[template_id]
        param_count = len(template_data.get('params', {}))
        
        info_text = f"""
模板名称: {template_data.get('name', '未命名')}
模板备注: {template_data.get('remark', '暂无备注')}
创建时间: {template_data.get('create_time', '未知')}
参数数量: {param_count} 个
最后使用: {template_data.get('last_used', '从未使用')}
        """.strip()
        
        self.show_custom_message("模板信息", info_text)
    
    def import_template(self):
        
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模板文件", "", 
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                imported_data = json.load(f)
            
            
            if not isinstance(imported_data, dict):
                self.show_custom_message("导入失败", "文件格式不正确")
                return
            
            import_count = 0
            import datetime
            
            for template_id, template_data in imported_data.items():
                if isinstance(template_data, dict) and 'name' in template_data:
                    
                    new_template_id = f"template_{int(datetime.datetime.now().timestamp())}_{import_count}"
                    
                    
                    original_name = template_data.get('name', '导入的模板')
                    new_name = original_name
                    counter = 1
                    while any(t.get('name') == new_name for t in self.templates.values()):
                        counter += 1
                        new_name = f"{original_name}({counter})"
                    
                    
                    template_data['name'] = new_name
                    template_data['create_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    template_data['last_used'] = '从未使用'
                    if 'remark' not in template_data:
                        template_data['remark'] = '从文件导入'
                    
                    self.templates[new_template_id] = template_data
                    import_count += 1
            
            if import_count > 0:
                self.save_templates()
                self.load_template_list()
                self.show_custom_message("导入成功", f"成功导入 {import_count} 个模板！")
            else:
                self.show_custom_message("导入失败", "未找到有效的模板数据")
                
        except Exception as e:
            self.show_custom_message("导入失败", f"导入模板时发生错误: {str(e)}")
    
    def export_template(self):
        
        current_row = self.template_table.currentRow()
        if current_row < 0:
            self.show_custom_message("提示", "请先选择要导出的模板")
            return
        
        
        name_item = self.template_table.item(current_row, 0)
        template_id = name_item.data(Qt.UserRole)
        
        if template_id not in self.templates:
            self.show_custom_message("错误", "模板数据不存在")
            return
        
        from PySide6.QtWidgets import QFileDialog
        
        template_name = self.templates[template_id].get('name', '模板')
        default_filename = f"{template_name}_{self.tool_name}_模板.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出模板", default_filename, 
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            import json
            export_data = {template_id: self.templates[template_id]}
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.show_custom_message("导出成功", f"模板 '{template_name}' 导出成功！")
            
        except Exception as e:
            self.show_custom_message("导出失败", f"导出模板时发生错误: {str(e)}")

class ToolProcess(QProcess):
    
    
    def __init__(self, parent=None, process_tab=None):
        super().__init__(parent)
        self.process_tab = process_tab
        self.readyReadStandardOutput.connect(self.handle_stdout)
        self.readyReadStandardError.connect(self.handle_stderr)
        self.finished.connect(self.handle_finished)
    
    def handle_stdout(self):
        data = self.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8", errors="ignore")
        if self.process_tab and hasattr(self.process_tab, 'append_output'):
            self.process_tab.append_output(stdout)
    
    def handle_stderr(self):
        data = self.readAllStandardError()
        stderr = bytes(data).decode("utf-8", errors="ignore")
        if self.process_tab and hasattr(self.process_tab, 'append_output'):
            self.process_tab.append_output(f"[ERROR] {stderr}")
    
    def handle_finished(self, exit_code, exit_status):
        if hasattr(self.parent(), 'process_finished'):
            self.parent().process_finished(self, exit_code, exit_status)

class ToolConfigParser:
    
    
    @staticmethod
    def parse_config(config_path):
        
        config = {
            '常用参数': {
                '勾选项区': [],
                '输入框区': []
            },
            '全部参数': {
                '勾选项区': [],
                '输入框区': []
            }
        }
        
        if not os.path.exists(config_path):
            return config
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_section = None
            current_subsection = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('%') and not line.startswith('%%'):
                    
                    current_section = line[1:]
                elif line.startswith('%%'):
                    
                    subsection_name = line[2:]
                    if subsection_name == '勾选项':
                        current_subsection = '勾选项区'
                    elif subsection_name == '输入项':
                        current_subsection = '输入框区'
                    else:
                        
                        current_subsection = None
                elif '=' in line and current_section and current_subsection:
                    
                    try:
                        
                        parts = line.split('=')
                        if len(parts) >= 3:
                            param_name = parts[0].strip()
                            display_name = parts[1].strip()
                            
                            
                            last_part = parts[-1].strip()
                            if last_part in ['0', '1'] and len(parts) >= 4:
                                
                                required = last_part
                                
                                description = '='.join(parts[2:-1]).strip()
                            else:
                                
                                description = '='.join(parts[2:]).strip()
                                required = '0'

                            
                            if current_subsection == '勾选项区':
                                param_type = '1'  
                            elif current_subsection == '输入框区':
                                param_type = '2'  
                            else:
                                continue  
                            
                            param_info = {
                                'param_name': param_name,
                                'display_name': display_name,
                                'description': description,
                                'type': param_type,
                                'required': required == '1'  
                            }
                            
                            if current_section in config and current_subsection in config[current_section]:
                                config[current_section][current_subsection].append(param_info)
                    except Exception as e:
                        
                        print(f"警告：解析配置文件行时出错: {line.strip()}, 错误: {e}")
                        continue
        except Exception as e:
            print(f"配置文件解析错误: {e}")
            
        return config

class ParameterEditDialog(QDialog):
    
    def __init__(self, param_info, parent=None):
        super().__init__(parent)
        self.param_info = param_info.copy()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("编辑参数信息")
        self.setMinimumSize(480, 480)
        self.setMaximumSize(600, 600)
        self.resize(480, 520)
        self.setModal(True)
        
        
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                {get_system_font_css()}
            }}
        """)
        
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        title_icon = QLabel("📝")
        title_icon.setStyleSheet("font-size: 20px; color: #4a90e2;")
        title_icon.setAlignment(Qt.AlignCenter)
        
        title_text = QLabel("编辑参数信息")
        title_text.setFont(QFont(get_system_font(), 14, QFont.Bold))
        title_text.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                font-weight: bold;
            }
        """)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameStyle(QFrame.Sunken)
        line.setStyleSheet("""
            QFrame {
                color: #e9ecef;
                background-color: #e9ecef;
                border: none;
                height: 1px;
            }
        """)
        main_layout.addWidget(line)
        
        
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidgetResizable(True)
        
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)
        
        
        self.create_form_group(scroll_layout)
        
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #6c757d;
                border-radius: 6px;
                color: #6c757d;
                font-weight: 500;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        
        save_btn = QPushButton("保存")
        save_btn.setFixedSize(80, 36)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border: 1px solid #4a90e2;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #357abd;
                border-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2c5aa0;
            }
        """)
        save_btn.clicked.connect(self.save_and_close)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
    
    def create_form_group(self, parent_layout):
        
        
        
        self.create_input_field(parent_layout, "参数名称", "name_edit", 
                               self.param_info.get('param_name', ''),
                               "例如：--target, -u, --url")
        
        
        self.create_input_field(parent_layout, "显示名称", "display_edit",
                               self.param_info.get('display_name', ''),
                               "例如：目标域名, 用户名, 输出文件")
        
        
        self.create_textarea_field(parent_layout, "参数描述", "desc_edit",
                                  self.param_info.get('description', ''),
                                  "详细描述参数的用途和用法...")
        
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(16)
        
        
        type_layout = QVBoxLayout()
        type_layout.setSpacing(6)
        
        type_label = QLabel("参数类型")
        type_label.setFont(QFont(get_system_font(), 10, QFont.Bold))
        type_label.setStyleSheet("color: #495057; font-weight: bold;")
        type_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["勾选项", "输入项"])
        self.type_combo.setCurrentIndex(0 if self.param_info.get('type', '1') == '1' else 1)
        self.type_combo.setMinimumHeight(28)
        self.type_combo.setStyleSheet(f"""
            QComboBox {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 6px 12px;
                {get_system_font_css()}
                font-size: 9pt;
                color: #495057;
                min-width: 100px;
            }}
            QComboBox:focus {{
                border-color: #4a90e2;
                border-width: 2px;
                background-color: #ffffff;
            }}
            QComboBox:hover {{
                border-color: #4a90e2;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left-width: 1px;
                border-left-color: #e9ecef;
                border-left-style: solid;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
            }}
            QComboBox::drop-down:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
            }}
            QComboBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #6c757d;
                margin-left: 2px;
            }}
            QComboBox::down-arrow:hover {{
                border-top-color: #4a90e2;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                border: 2px solid #4a90e2;
                border-radius: 6px;
                selection-background-color: #4a90e2;
                selection-color: white;
                color: #495057;
                outline: none;
                padding: 2px;
            }}
            QComboBox QAbstractItemView::item {{
                height: 28px;
                padding: 4px 8px;
                border-radius: 4px;
                margin: 1px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: #e3f2fd;
                color: #2c5aa0;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: #4a90e2;
                color: white;
            }}
        """)
        type_layout.addWidget(self.type_combo)
        
        
        required_layout = QVBoxLayout()
        required_layout.setSpacing(6)
        
        required_label = QLabel("参数设置")
        required_label.setFont(QFont(get_system_font(), 10, QFont.Bold))
        required_label.setStyleSheet("color: #495057; font-weight: bold;")
        required_layout.addWidget(required_label)
        
        self.required_checkbox = QCheckBox("设为必填参数")
        self.required_checkbox.setChecked(self.param_info.get('required', False))
        self.required_checkbox.setFont(QFont(get_system_font(), 9))
        self.required_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: #495057;
                spacing: 8px;
                {get_system_font_css()}
                font-size: 9pt;
                background: transparent;
                padding: 6px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #ced4da;
                background-color: #ffffff;
            }}
            QCheckBox::indicator:hover {{
                border-color: #4a90e2;
                background-color: #f8f9fa;
            }}
            QCheckBox::indicator:checked {{
                background-color: #4a90e2;
                border-color: #4a90e2;
                border: 2px solid #4a90e2;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #357abd);
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: #357abd;
                border-color: #357abd;
            }}
        """)
        required_layout.addWidget(self.required_checkbox)
        
        bottom_layout.addLayout(type_layout)
        bottom_layout.addLayout(required_layout)
        bottom_layout.addStretch()
        
        parent_layout.addLayout(bottom_layout)
    
    def create_input_field(self, parent_layout, title, edit_name, value, placeholder):
        
        
        label = QLabel(title)
        label.setFont(QFont(get_system_font(), 10, QFont.Bold))
        label.setStyleSheet("color: #495057; font-weight: bold; margin-bottom: 4px;")
        parent_layout.addWidget(label)
        
        
        edit = QLineEdit()
        edit.setText(value)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(32)
        edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 6px 12px;
                {get_system_font_css()}
                font-size: 9pt;
                color: #495057;
                selection-background-color: #4a90e2;
            }}
            QLineEdit:focus {{
                border-color: #4a90e2;
                background-color: #ffffff;
                border-width: 2px;
            }}
            QLineEdit:hover {{
                border-color: #ced4da;
            }}
        """)
        
        setattr(self, edit_name, edit)
        parent_layout.addWidget(edit)
        
        
        parent_layout.addSpacing(6)
    
    def create_textarea_field(self, parent_layout, title, edit_name, value, placeholder):
        
        
        label = QLabel(title)
        label.setFont(QFont(get_system_font(), 10, QFont.Bold))
        label.setStyleSheet("color: #495057; font-weight: bold; margin-bottom: 4px;")
        parent_layout.addWidget(label)
        
        
        edit = QTextEdit()
        edit.setPlainText(value)
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(70)
        edit.setMaximumHeight(70)
        edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 6px 12px;
                {get_system_font_css()}
                font-size: 9pt;
                color: #495057;
                selection-background-color: #4a90e2;
            }}
            QTextEdit:focus {{
                border-color: #4a90e2;
                background-color: #ffffff;
                border-width: 2px;
            }}
            QTextEdit:hover {{
                border-color: #ced4da;
            }}
        """)
        
        setattr(self, edit_name, edit)
        parent_layout.addWidget(edit)
        
        
        parent_layout.addSpacing(6)


    

    
    def save_and_close(self):
        
        if not self.name_edit.text().strip():
            self.show_warning("验证失败", "参数名称不能为空")
            return
        
        if not self.display_edit.text().strip():
            self.show_warning("验证失败", "显示名称不能为空")
            return
        
        
        self.param_info['param_name'] = self.name_edit.text().strip()
        self.param_info['display_name'] = self.display_edit.text().strip()
        self.param_info['description'] = self.desc_edit.toPlainText().strip()
        self.param_info['type'] = '1' if self.type_combo.currentIndex() == 0 else '2'
        self.param_info['required'] = self.required_checkbox.isChecked()
        
        self.accept()
    
    def show_warning(self, title, message):
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 200)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        dialog.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #fff3cd, stop: 1 #ffeaa7);
                border: 2px solid #f39c12;
                border-radius: 12px;
                {get_system_font_css()}
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title_label = QLabel(title)
        title_label.setFont(QFont(get_system_font(), 13, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #d68910; padding: 8px;")
        layout.addWidget(title_label)
        
        msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(12)
        
        icon_label = QLabel("⚠️")
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 16pt;")
        msg_layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont(get_system_font(), 10))
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setStyleSheet("color: #8b4513; padding: 4px;")
        msg_layout.addWidget(msg_label, 1)
        
        msg_container.setLayout(msg_layout)
        layout.addWidget(msg_container)
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(80, 32)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f39c12, stop: 1 #e67e22);
                border: 1px solid #d68910;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                font-size: 10pt;
                {get_system_font_css()}
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e67e22, stop: 1 #d68910);
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def get_param_info(self):
        return self.param_info

class ParameterWidget(QWidget):
    
    
    def __init__(self, param_info):
        super().__init__()
        self.param_info = param_info
        self.drag_start_position = QPoint()
        self.setup_ui()
        self.setup_context_menu()
        self.setup_drag_drop()
    
    def create_tooltip(self):
        
        tooltip_text = ""
        if self.param_info['description']:
            tooltip_text = f"<b style='color: #4a90e2; font-size: 10pt;'>{self.param_info['param_name']}</b><br/><span style='color: #6c757d; font-size: 9pt;'>{self.param_info['description']}</span>"
        
        
        if self.param_info.get('required', False):
            required_text = "<br/><span style='color: #dc3545; font-size: 9pt; font-weight: bold;'>* 此参数为必填项</span>"
            tooltip_text += required_text
        
        
        drag_tip = "<br/><span style='color: #17a2b8; font-size: 8pt;'>💡 提示：拖拽此参数可以重新排序</span>"
        tooltip_text += drag_tip
        
        return tooltip_text
    
    def setup_ui(self):
        layout = QHBoxLayout()  
        layout.setSpacing(2)  
        layout.setContentsMargins(2, 2, 2, 2)  
        
        
        drag_icon = QLabel("")
        drag_icon.setFixedSize(0, 0)
        drag_icon.setAlignment(Qt.AlignCenter)
        drag_icon.setStyleSheet("""
            QLabel {
                color: #adb5bd;
                font-weight: bold;
                font-size: 8pt;
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        drag_icon.setToolTip("拖拽此参数来重新排序")
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
            name_label.setFont(QFont("Microsoft YaHei", 8, QFont.Medium))
            name_label.setWordWrap(True)  
            name_label.setMinimumWidth(80)  
            name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)  
            
            label_style = """
                QLabel {
                    color: #495057;
                    font-weight: 500;
                    padding: 2px 4px;
                }
            """
            
            if is_required:
                label_style = """
                    QLabel {
                        color: #495057;
                        font-weight: 600;
                        padding: 2px 4px;
                        border-left: 3px solid #dc3545;
                        padding-left: 6px;
                    }
                """
            name_label.setStyleSheet(label_style)
            
            tooltip = self.create_tooltip()
            if tooltip:
                name_label.setToolTip(tooltip)
            layout.addWidget(name_label)
            
            self.control = QLineEdit()
            self.control.setFont(QFont("Microsoft YaHei", 8))
            self.control.setMaximumHeight(32)
            
            placeholder_text = "输入值"
            if is_required:
                placeholder_text = "必填 - 请输入值"
                
            self.control.setPlaceholderText(placeholder_text)
            
            
            if is_required:
                self.control.textChanged.connect(self.update_required_style)
                
                self.update_required_style()
            else:
                
                normal_style = """
                    QLineEdit {
                        background-color: #ffffff;
                        border: 1px solid #e9ecef;
                        border-radius: 6px;
                        padding: 6px 10px;
                        color: #495057;
                        font-size: 8pt;
                        selection-background-color: #4a90e2;
                    }
                    QLineEdit:focus {
                        border-color: #4a90e2;
                        background-color: #f8f9fa;
                    }
                    QLineEdit:hover {
                        border-color: #ced4da;
                    }
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
            
        layout.addWidget(self.control)
        
        
        if param_type == '1':
            self.setMinimumHeight(36)  
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  
        else:
            self.setMinimumHeight(32)  
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  
            
        
        self.setStyleSheet("""
            ParameterWidget {
                border-radius: 4px;
                background: transparent;
            }
            ParameterWidget:hover {
                background-color: rgba(74, 144, 226, 0.05);
                border: 1px dashed #4a90e2;
            }
        """)
            
        self.setLayout(layout)
    
    def setup_context_menu(self):
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: 12px;
                padding: 8px;
                {get_system_font_css()}
                font-size: 11pt;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 12px 30px 12px 16px;
                border-radius: 8px;
                color: #495057;
                margin: 2px 4px;
                font-weight: 500;
                min-height: 20px;
            }}
            QMenu::item:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e3f2fd, stop: 1 #bbdefb);
                color: #1976d2;
                font-weight: 600;
                border: 1px solid #90caf9;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #2c5aa0);
                color: white;
                font-weight: 600;
                border: 1px solid #1976d2;
            }}
            QMenu::separator {{
                height: 2px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 transparent, stop: 0.5 #e1e8ed, stop: 1 transparent);
                margin: 8px 12px;
                border-radius: 1px;
            }}
        """)
        
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        
        current_tab_widget = tool_page.param_tabs.currentWidget()
        if not current_tab_widget:
            return
        
        current_tab_name = tool_page.param_tabs.tabText(tool_page.param_tabs.currentIndex())
        
        
        edit_action = menu.addAction("✏️ 编辑参数信息")
        edit_action.triggered.connect(self.edit_parameter)
        
        menu.addSeparator()
        
        
        required_text = "❌ 取消必填" if self.param_info.get('required', False) else "⭐ 设为必填"
        required_action = menu.addAction(required_text)
        required_action.triggered.connect(self.toggle_required)
        
        menu.addSeparator()
        
        
        if current_tab_name == "常用参数":
            
            remove_action = menu.addAction("➖ 从常用参数中移除")
            remove_action.triggered.connect(self.remove_from_common)
        elif current_tab_name == "全部参数":
            
            add_action = menu.addAction("➕ 添加到常用参数")
            add_action.triggered.connect(self.copy_to_common)
        

        
        
        menu.exec(self.mapToGlobal(position))
    
    def get_tool_operation_page(self):
        
        parent = self.parent()
        while parent:
            if isinstance(parent, ToolOperationPage):
                return parent
            parent = parent.parent()
        return None
    
    def edit_parameter(self):
        
        dialog = ParameterEditDialog(self.param_info, self)
        if dialog.exec() == QDialog.Accepted:
            
            new_param_info = dialog.get_param_info()
            old_param_name = self.param_info['param_name']
            
            
            self.param_info.update(new_param_info)
            
            
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.update_parameter_in_config(old_param_name, new_param_info)
                
                tool_page.save_config_to_file()
                
                tool_page.reload_config()
    
    def toggle_required(self):
        
        current_required = self.param_info.get('required', False)
        new_required = not current_required
        
        
        self.param_info['required'] = new_required
        
        
        self.update_ui_from_param_info()
        
        
        tool_page = self.get_tool_operation_page()
        if tool_page:
            tool_page.save_config_to_file()
            
            tool_page.sync_required_status(self.param_info['param_name'], new_required)
    
    def move_parameter(self, from_tab, to_tab):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        
        
        if tool_page.show_custom_question(
            "移动参数确认", 
            f"确定要将参数 '{self.param_info['display_name']}' 从{from_tab}移动到{to_tab}吗？"
        ):
            tool_page.move_parameter_between_tabs(self.param_info, from_tab, to_tab)
    
    def remove_from_common(self):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        
        
        if tool_page.show_custom_question(
            "移除参数确认", 
            f"确定要将参数 '{self.param_info['display_name']}' 从常用参数中移除吗？\n\n注意：移除后该参数仍可在全部参数中找到。"
        ):
            tool_page.remove_parameter_from_common(self.param_info)
    
    def copy_to_common(self):
        
        tool_page = self.get_tool_operation_page()
        if not tool_page:
            return
        
        
        if tool_page.show_custom_question(
            "添加参数确认", 
            f"确定要将参数 '{self.param_info['display_name']}' 添加到常用参数吗？"
        ):
            tool_page.copy_parameter_to_common(self.param_info)
    
    def update_ui_from_param_info(self):
        
        param_type = self.param_info['type']
        is_required = self.param_info.get('required', False)
        
        if param_type == '1':  
            self.control.setText(self.param_info['display_name'])
            
            self.control.is_required = is_required
            self.control.parent_widget = self
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
                                {get_system_font_css()}
                                font-weight: bold;
                                font-size: 8pt;
                                padding: 2px;
                            }}
                            QLabel:before {{
                                content: "*";
                                color: #dc3545;
                                font-weight: bold;
                            }}
                        """
                    else:
                        label_style = f"""
                            QLabel {{
                                color: #495057;
                                {get_system_font_css()}
                                font-weight: 500;
                                font-size: 8pt;
                                padding: 2px;
                            }}
                        """
                    label.setStyleSheet(label_style)
                    break
            
            
            placeholder_text = "输入值"
            if is_required:
                placeholder_text = "必填 - 请输入值"
            self.control.setPlaceholderText(placeholder_text)
            
            
            self.update_required_style()
        
        
        tooltip = self.create_tooltip()
        if tooltip:
            self.control.setToolTip(tooltip)
    
    def copy_parameter_info(self):
        
        param_info_text = f"""参数名称: {self.param_info['param_name']}
显示名称: {self.param_info['display_name']}
参数描述: {self.param_info.get('description', '无描述')}
参数类型: {'勾选项' if self.param_info['type'] == '1' else '输入项'}
是否必填: {'是' if self.param_info.get('required', False) else '否'}
当前值: {self.get_display_value()}"""
        
        clipboard = QApplication.clipboard()
        clipboard.setText(param_info_text)
        
        
        QToolTip.showText(
            self.mapToGlobal(self.rect().center()), 
            "参数信息已复制到剪贴板", 
            self, 
            self.rect(), 
            2000
        )
    
    def reset_parameter_value(self):
        
        param_type = self.param_info['type']
        
        if param_type == '1':  
            self.control.setChecked(False)
        elif param_type == '2':  
            self.control.clear()
        
        
        if self.param_info.get('required', False):
            self.update_required_style()
        
        
        QToolTip.showText(
            self.mapToGlobal(self.rect().center()), 
            "参数值已重置", 
            self, 
            self.rect(), 
            1500
        )
    
    def get_display_value(self):
        
        param_type = self.param_info['type']
        
        if param_type == '1':  
            return "已选中" if self.control.isChecked() else "未选中"
        elif param_type == '2':  
            value = self.control.text().strip()
            return value if value else "未设置"
        
        return "未知"
    
    def get_value(self):
        
        if isinstance(self.control, (QCheckBox, ClickableLabel)):
            return self.control.isChecked()
        elif isinstance(self.control, QLineEdit):
            return self.control.text()
        return None
    
    def get_param_string(self):
        
        if isinstance(self.control, (QCheckBox, ClickableLabel)):
            if self.control.isChecked():
                return self.param_info['param_name']
            return ""
        elif isinstance(self.control, QLineEdit):
            text = self.control.text().strip()
            if text:
                return f"{self.param_info['param_name']} {text}"
            return ""
        return ""
    
    def is_required(self):
        
        return self.param_info.get('required', False)
    
    def is_filled(self):
        
        if not self.is_required():
            return True  
            
        if isinstance(self.control, (QCheckBox, ClickableLabel)):
            return self.control.isChecked()
        elif isinstance(self.control, QLineEdit):
            return bool(self.control.text().strip())
        return True
    
    def get_display_name(self):
        
        return self.param_info.get('display_name', '未知参数')
    
    def update_required_style(self):
        
        is_required = self.is_required()
        is_filled = self.is_filled()
        param_type = self.param_info['type']
        
        if param_type == '1':  
            
            if hasattr(self.control, 'update_style'):
                self.control.update_style()
        elif param_type == '2':  
            
            if is_required:
                if is_filled:
                    
                    normal_style = f"""
                        QLineEdit {{
                            background-color: #ffffff;
                            border: 1px solid #28a745;
                            border-radius: 6px;
                            padding: 6px 10px;
                            color: #495057;
                            font-size: 8pt;
                            selection-background-color: #4a90e2;
                            {get_system_font_css()}
                        }}
                        QLineEdit:focus {{
                            border-color: #28a745;
                            background-color: #f8fff8;
                        }}
                        QLineEdit:hover {{
                            border-color: #20c997;
                        }}
                    """
                    self.control.setStyleSheet(normal_style)
                else:
                    
                    error_style = f"""
                        QLineEdit {{
                            background-color: #fff5f5;
                            border: 2px solid #dc3545;
                            border-radius: 6px;
                            padding: 6px 10px;
                            color: #495057;
                            font-size: 8pt;
                            selection-background-color: #4a90e2;
                            {get_system_font_css()}
                        }}
                        QLineEdit:focus {{
                            border-color: #dc3545;
                            background-color: #ffffff;
                        }}
                        QLineEdit:hover {{
                            border-color: #c82333;
                        }}
                    """
                    self.control.setStyleSheet(error_style)
            else:
                
                normal_style = f"""
                    QLineEdit {{
                        background-color: #ffffff;
                        border: 1px solid #ced4da;
                        border-radius: 6px;
                        padding: 6px 10px;
                        color: #495057;
                        font-size: 8pt;
                        selection-background-color: #4a90e2;
                        {get_system_font_css()}
                    }}
                    QLineEdit:focus {{
                        border-color: #4a90e2;
                        background-color: #f8f9fa;
                    }}
                    QLineEdit:hover {{
                        border-color: #adb5bd;
                    }}
                """
                self.control.setStyleSheet(normal_style)
    
    def setup_drag_drop(self):
        
        self.setAcceptDrops(False)  
        
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
        
        import json
        mime_data.setText(f"parameter_widget_data:{json.dumps(drag_data)}")
        drag.setMimeData(mime_data)
        
        
        try:
            
            pixmap = self.grab()
            if not pixmap.isNull() and pixmap.width() > 0 and pixmap.height() > 0:
                drag.setPixmap(pixmap)
            else:
                
                drag.setPixmap(self.create_simple_drag_icon())
        except Exception:
            
            drag.setPixmap(self.create_simple_drag_icon())
        
        
        if hasattr(self, 'drag_start_position'):
            drag.setHotSpot(self.drag_start_position)
        else:
            drag.setHotSpot(QPoint(10, 10))
        
        
        result = drag.exec(Qt.MoveAction)
        
        if result == Qt.MoveAction:
            
            pass
    
    def create_simple_drag_icon(self):
        
        
        pixmap = QPixmap(80, 24)
        pixmap.fill(QColor(74, 144, 226, 200))  
        return pixmap
    
    def get_current_section_title(self):
        
        parent = self.parent()
        while parent:
            if isinstance(parent, ParameterSection):
                return parent.title
            parent = parent.parent()
        return "未知区域"

class ParameterSection(QWidget):
    
    
    def __init__(self, title, params):
        super().__init__()
        self.title = title
        self.params = params
        self.param_widgets = []
        self.setup_ui()
        self.setup_context_menu()
        self.setup_drag_drop()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        
        if self.params:  
            group_box = QGroupBox(self.title)
            group_box.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
            group_box.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #e1e8ed;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 16px;
                    background-color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 12px;
                    top: 6px;
                    padding: 4px 12px;
                    background-color: #4a90e2;
                    color: white;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 9pt;
                }
            """)
            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(8, 8, 8, 8)
            group_layout.setSpacing(4)
            
            
            search_container = self.create_search_bar()
            group_layout.addWidget(search_container)
            
            
            scroll_area = QScrollArea()
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setFrameShape(QFrame.NoFrame)
            
            scroll_widget = QWidget()
            scroll_layout = QGridLayout()
            
            
            scroll_layout.setSpacing(2)  
            scroll_layout.setContentsMargins(2, 2, 2, 2)  
            
            
            if self.title == "勾选项区":
                cols_per_row = 3  
            elif self.title == "输入框区":
                cols_per_row = 1  
            else:
                cols_per_row = 2  
                
            row = 0
            col = 0
            
            for param in self.params:
                param_widget = ParameterWidget(param)
                self.param_widgets.append(param_widget)
                
                
                if param['type'] == '2' and cols_per_row > 1:  
                    scroll_layout.addWidget(param_widget, row, col, 1, 2)  
                    col += 2
                else:
                    scroll_layout.addWidget(param_widget, row, col)
                col += 1
                
                if col >= cols_per_row:  
                    col = 0
                    row += 1
            
            
            for i in range(cols_per_row):
                scroll_layout.setColumnStretch(i, 1)
            
            
            for r in range(row + 1):
                scroll_layout.setRowStretch(r, 0)  
            
            scroll_widget.setLayout(scroll_layout)
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            
            group_layout.addWidget(scroll_area)
            group_box.setLayout(group_layout)
            layout.addWidget(group_box)
        
        self.setLayout(layout)
    
    def create_search_bar(self):
        
        search_container = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(4, 4, 4, 8)
        search_layout.setSpacing(8)
        
        
        search_icon = QLabel("🔍")
        search_icon.setFont(QFont(get_system_font(), 10))
        search_icon.setFixedSize(20, 24)
        search_icon.setAlignment(Qt.AlignCenter)
        
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索参数（支持参数名、显示名、介绍）...")
        self.search_input.setFont(QFont(get_system_font(), 9))
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 6px 12px;
                background-color: #fafafa;
                font-size: 9pt;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
                background-color: #ffffff;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #aaa;
                background-color: #f5f5f5;
            }
        """)
        
        
        self.clear_search_btn = QPushButton("✕")
        self.clear_search_btn.setFont(QFont(get_system_font(), 8))
        self.clear_search_btn.setFixedSize(24, 24)
        self.clear_search_btn.clicked.connect(self.clear_search)
        self.clear_search_btn.setVisible(False)  
        
        
        self.clear_search_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                background-color: #e0e0e0;
                color: #666;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                color: #444;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        
        
        self.search_result_label = QLabel()
        self.search_result_label.setFont(QFont(get_system_font(), 8))
        self.search_result_label.setStyleSheet("color: #666; padding: 4px;")
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
        
        search_text_lower = search_text.lower()
        visible_count = 0
        
        for param_widget in self.param_widgets:
            
            if self.matches_search(param_widget.param_info, search_text_lower):
                param_widget.setVisible(True)
                self.highlight_search_match(param_widget, search_text_lower)
                visible_count += 1
            else:
                param_widget.setVisible(False)
                self.clear_highlight(param_widget)
        
        
        total_count = len(self.param_widgets)
        if visible_count == 0:
            self.search_result_label.setText("❌ 未找到匹配的参数")
            self.search_result_label.setStyleSheet("color: #dc3545; padding: 4px; font-weight: 500;")
        else:
            self.search_result_label.setText(f"✅ 找到 {visible_count}/{total_count} 个参数")
            self.search_result_label.setStyleSheet("color: #28a745; padding: 4px; font-weight: 500;")
        
        self.search_result_label.setVisible(True)
    
    def show_all_parameters(self):
        
        for param_widget in self.param_widgets:
            param_widget.setVisible(True)
            self.clear_highlight(param_widget)
        
        self.search_result_label.setVisible(False)
    
    def matches_search(self, param_info, search_text):
        
        
        if search_text in param_info.get('param_name', '').lower():
            return True
        
        
        if search_text in param_info.get('display_name', '').lower():
            return True
        
        
        if search_text in param_info.get('description', '').lower():
            return True
        
        
        if search_text in param_info.get('help', '').lower():
            return True
        
        
        if search_text in str(param_info.get('default', '')).lower():
            return True
        
        return False
    
    def highlight_search_match(self, param_widget, search_text):
        
        
        current_style = param_widget.styleSheet()
        highlight_style = """
            ParameterWidget {
                border: 2px solid #ffc107 !important;
                border-radius: 6px !important;
                background-color: rgba(255, 193, 7, 0.1) !important;
            }
        """
        param_widget.setStyleSheet(current_style + highlight_style)
    
    def clear_highlight(self, param_widget):
        
        
        param_widget.setStyleSheet("""
            ParameterWidget {
                border-radius: 4px;
                background: transparent;
            }
            ParameterWidget:hover {
                background-color: rgba(74, 144, 226, 0.05);
                border: 1px dashed #4a90e2;
            }
        """)
    
    def get_all_params(self):
        
        params = []
        for widget in self.param_widgets:
            param_str = widget.get_param_string()
            if param_str:
                params.append(param_str)
        return params
    
    def validate_required_params(self):
        
        missing_params = []
        for widget in self.param_widgets:
            if widget.is_required() and not widget.is_filled():
                missing_params.append(widget.get_display_name())
        
        return len(missing_params) == 0, missing_params
    
    def update_all_required_styles(self):
        
        for widget in self.param_widgets:
            
            widget.update_required_style()
    
    def setup_context_menu(self):
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_section_context_menu)
    
    def show_section_context_menu(self, position):
        
        
        child_widget = self.childAt(position)
        if child_widget and self.is_parameter_widget(child_widget):
            return  
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: 12px;
                padding: 8px;
                {get_system_font_css()}
                font-size: 11pt;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 12px 30px 12px 16px;
                border-radius: 8px;
                color: #495057;
                margin: 2px 4px;
                font-weight: 500;
                min-height: 20px;
            }}
            QMenu::item:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e3f2fd, stop: 1 #bbdefb);
                color: #1976d2;
                font-weight: 600;
                border: 1px solid #90caf9;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #2c5aa0);
                color: white;
                font-weight: 600;
                border: 1px solid #1976d2;
            }}
            QMenu::separator {{
                height: 2px;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                          stop: 0 transparent, stop: 0.5 #e1e8ed, stop: 1 transparent);
                margin: 8px 12px;
                border-radius: 1px;
            }}
        """)
        
        
        add_checkbox_action = menu.addAction("➕ 添加勾选项参数")
        add_checkbox_action.triggered.connect(lambda: self.add_new_parameter('1'))
        
        add_input_action = menu.addAction("📝 添加输入项参数")
        add_input_action.triggered.connect(lambda: self.add_new_parameter('2'))
        
        
        menu.exec(self.mapToGlobal(position))
    
    def is_parameter_widget(self, widget):
        
        parent = widget.parent()
        while parent:
            if isinstance(parent, ParameterWidget):
                return True
            parent = parent.parent()
        return False
    
    def add_new_parameter(self, param_type):
        
        
        param_count = len(self.param_widgets) + 1
        default_param = {
            'param_name': f'--new-param-{param_count}',
            'display_name': f'新参数{param_count}',
            'description': '新添加的参数',
            'type': param_type,
            'required': False
        }
        
        
        dialog = ParameterEditDialog(default_param, self)
        if dialog.exec() == QDialog.Accepted:
            new_param_info = dialog.get_param_info()
            
            
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.add_parameter_to_section(new_param_info, self.title)
    
    def get_tool_operation_page(self):
        
        parent = self.parent()
        while parent:
            if isinstance(parent, ToolOperationPage):
                return parent
            parent = parent.parent()
        return None
    
    def setup_drag_drop(self):
        
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("parameter_widget_data:"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("parameter_widget_data:"):
                try:
                    import json
                    drag_data_str = text.split(":", 1)[1]
                    drag_data = json.loads(drag_data_str)
                    source_section = drag_data['source_section']
                    
                    
                    if not hasattr(self, '_drag_style_applied'):
                        
                        if source_section != self.title:
                            
                            self.show_conversion_hint(True)
                        else:
                            
                            self.show_conversion_hint(False)
                        
                        self._drag_style_applied = True
                    
                    event.acceptProposedAction()
                except:
                    event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def show_conversion_hint(self, is_conversion):
        
        try:
            if is_conversion:
                
                target_type = "勾选项" if self.title == "勾选项区" else "输入项"
                hint_text = f"🔄 将转换为{target_type}"
                
                
                self.setStyleSheet("""
                    QGroupBox {
                        border: 2px dashed #17a2b8;
                        border-radius: 8px;
                        background-color: rgba(23, 162, 184, 0.1);
                        margin-top: 12px;
                        padding-top: 16px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        left: 12px;
                        top: 6px;
                        padding: 4px 12px;
                        background-color: #17a2b8;
                        color: white;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 9pt;
                    }
                """)
            else:
                
                self.setStyleSheet("""
                    QGroupBox {
                        border: 2px dashed #28a745;
                        border-radius: 8px;
                        background-color: rgba(40, 167, 69, 0.1);
                        margin-top: 12px;
                        padding-top: 16px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        left: 12px;
                        top: 6px;
                        padding: 4px 12px;
                        background-color: #28a745;
                        color: white;
                        border-radius: 6px;
                        font-weight: 600;
                        font-size: 9pt;
                    }
                """)
        except Exception:
            pass
    
    def dragLeaveEvent(self, event):
        
        try:
            self.restore_original_style()
            
            if hasattr(self, '_drag_style_applied'):
                delattr(self, '_drag_style_applied')
        except Exception:
            pass
    
    def restore_original_style(self):
        
        
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #c0c0c0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: rgba(248, 249, 250, 0.6);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                top: 6px;
                padding: 4px 12px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-weight: 600;
                color: #495057;
                font-size: 9pt;
            }
        """)
     
    def dropEvent(self, event):
        
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("parameter_widget_data:"):
                try:
                    import json
                    drag_data_str = text.split(":", 1)[1]
                    drag_data = json.loads(drag_data_str)
                    
                    param_name = drag_data['param_name']
                    source_param_type = drag_data['param_type']
                    source_section = drag_data['source_section']
                    param_info = drag_data['param_info']
                    
                    
                    drop_position = event.position().toPoint()
                    
                    
                    if source_section != self.title:
                        
                        self.handle_cross_section_drop(param_info, source_section, drop_position)
                    else:
                        
                        self.reorder_parameters(param_name, drop_position)
                    
                    
                    self.restore_original_style()
                    
                    if hasattr(self, '_drag_style_applied'):
                        delattr(self, '_drag_style_applied')
                    
                    event.acceptProposedAction()
                except Exception as e:
                    tool_page = self.get_tool_operation_page()
                    if tool_page:
                        tool_page.system_log_tab.append_system_log(f"拖拽处理失败: {e}", "error")
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def reorder_parameters(self, dragged_param_name, drop_position):
        
        try:
            
            dragged_index = -1
            dragged_param = None
            for i, param_widget in enumerate(self.param_widgets):
                if param_widget.param_info['param_name'] == dragged_param_name:
                    dragged_index = i
                    dragged_param = param_widget
                    break
            
            if dragged_index == -1 or dragged_param is None:
                return
            
            
            target_index = self.calculate_drop_index(drop_position)
            
            
            if target_index == dragged_index:
                return
            
            
            if target_index > dragged_index:
                target_index -= 1
            
            
            self.param_widgets.pop(dragged_index)
            self.param_widgets.insert(target_index, dragged_param)
            
            
            self.params.pop(dragged_index)
            self.params.insert(target_index, dragged_param.param_info)
            
            
            self.update_layout()
            
            
            tool_page = self.get_tool_operation_page()
            if tool_page:
                
                tool_page.sync_parameter_order(self.title, self.params)
                
                tool_page.save_config_to_file()
                
                tool_page.system_log_tab.append_system_log(
                    f"参数 '{dragged_param.param_info['display_name']}' 已重新排序", 
                    "success"
                )
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"参数排序失败: {e}", "error")
    
    def calculate_drop_index(self, drop_position):
        
        
        if not self.param_widgets:
            return 0
        
        
        if self.title == "勾选项区":
            cols_per_row = 3
        elif self.title == "输入框区":
            cols_per_row = 1
        else:
            cols_per_row = 2
        
        
        min_distance = float('inf')
        target_index = len(self.param_widgets)
        
        for i, widget in enumerate(self.param_widgets):
            widget_center = widget.rect().center()
            widget_global_center = widget.mapToGlobal(widget_center)
            widget_local_center = self.mapFromGlobal(widget_global_center)
            
            distance = (widget_local_center - drop_position).manhattanLength()
            
            if distance < min_distance:
                min_distance = distance
                
                if drop_position.y() < widget_local_center.y() or \
                   (drop_position.y() == widget_local_center.y() and drop_position.x() < widget_local_center.x()):
                    target_index = i
                else:
                    target_index = i + 1
        
        return min(target_index, len(self.param_widgets))
    
    def update_layout(self):
        
        
        layout = self.layout()
        if layout:
            
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, QGroupBox):
                        group_layout = widget.layout()
                        if group_layout:
                            
                            for j in range(group_layout.count()):
                                scroll_item = group_layout.itemAt(j)
                                if scroll_item and scroll_item.widget():
                                    scroll_widget = scroll_item.widget()
                                    if isinstance(scroll_widget, QScrollArea):
                                        
                                        scroll_content = scroll_widget.widget()
                                        if scroll_content:
                                            content_layout = scroll_content.layout()
                                            if content_layout and isinstance(content_layout, QGridLayout):
                                                
                                                while content_layout.count():
                                                    child = content_layout.takeAt(0)
                                                    if child.widget():
                                                        child.widget().setParent(None)
                                                
                                                
                                                self.rebuild_grid_layout(content_layout)
                                                return
        
        
        self.rebuild_section_ui()
    
    def rebuild_grid_layout(self, grid_layout):
        
        if self.title == "勾选项区":
            cols_per_row = 3
        elif self.title == "输入框区":
            cols_per_row = 1
        else:
            cols_per_row = 2
        
        row = 0
        col = 0
        
        for param_widget in self.param_widgets:
            param_type = param_widget.param_info['type']
            
            if param_type == '2' and cols_per_row > 1:  
                grid_layout.addWidget(param_widget, row, col, 1, 2)
                col += 2
            else:
                grid_layout.addWidget(param_widget, row, col)
                col += 1
            
            if col >= cols_per_row:
                col = 0
                row += 1
        
        
        for i in range(cols_per_row):
            grid_layout.setColumnStretch(i, 1)
        
        
        for r in range(row + 1):
            grid_layout.setRowStretch(r, 0)
    
    def rebuild_section_ui(self):
        
        
        layout = self.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        
        self.setup_ui()
    
    def handle_cross_section_drop(self, param_info, source_section, drop_position):
        
        try:
            tool_page = self.get_tool_operation_page()
            if not tool_page:
                return
            
            
            new_param_info = self.convert_parameter_type(param_info)
            
            
            target_index = self.calculate_drop_index(drop_position)
            
            
            self.optimized_cross_section_move(param_info, new_param_info, source_section, target_index)
            
            
            tool_page.save_config_to_file()
            
            
            type_text = "勾选项" if new_param_info['type'] == '1' else "输入项"
            tool_page.system_log_tab.append_system_log(
                f"参数 '{param_info['display_name']}' 已从 {source_section} 移动到 {self.title} 并转换为 {type_text}", 
                "success"
            )
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"跨区域拖拽失败: {e}", "error")
    
    def optimized_cross_section_move(self, old_param_info, new_param_info, source_section, target_index):
        
        try:
            tool_page = self.get_tool_operation_page()
            if not tool_page:
                return
            
            
            source_section_widget = self.find_source_section_widget(source_section)
            if source_section_widget:
                source_section_widget.remove_parameter_widget_direct(old_param_info['param_name'])
            
            
            self.add_converted_parameter_direct(new_param_info, target_index)
            
            
            self.update_config_data_direct(old_param_info, new_param_info, source_section)
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"优化跨区域移动失败: {e}", "error")
    
    def find_source_section_widget(self, source_section):
        
        try:
            tool_page = self.get_tool_operation_page()
            if not tool_page:
                return None
            
            
            current_tab_widget = tool_page.param_tabs.currentWidget()
            if current_tab_widget:
                
                for child in current_tab_widget.findChildren(ParameterSection):
                    if child.title == source_section:
                        return child
            return None
            
        except Exception:
            return None
    
    def remove_parameter_widget_direct(self, param_name):
        
        try:
            
            widget_to_remove = None
            for i, param_widget in enumerate(self.param_widgets):
                if param_widget.param_info['param_name'] == param_name:
                    widget_to_remove = param_widget
                    self.param_widgets.pop(i)
                    self.params.pop(i)
                    break
            
            if widget_to_remove:
                
                widget_to_remove.setParent(None)
                widget_to_remove.deleteLater()
                
                
                self.update_layout_fast()
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"移除参数控件失败: {e}", "error")
    
    def add_converted_parameter_direct(self, param_info, target_index):
        
        try:
            
            param_widget = ParameterWidget(param_info)
            
            
            if target_index >= len(self.params):
                self.params.append(param_info)
                self.param_widgets.append(param_widget)
            else:
                self.params.insert(target_index, param_info)
                self.param_widgets.insert(target_index, param_widget)
            
            
            self.update_layout_fast()
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"添加转换参数控件失败: {e}", "error")
    
    def update_config_data_direct(self, old_param_info, new_param_info, source_section):
        
        try:
            tool_page = self.get_tool_operation_page()
            if not tool_page:
                return
            
            current_tab_name = tool_page.param_tabs.tabText(tool_page.param_tabs.currentIndex())
            
            
            if (current_tab_name in tool_page.config_data and 
                source_section in tool_page.config_data[current_tab_name]):
                source_params = tool_page.config_data[current_tab_name][source_section]
                for i, param in enumerate(source_params):
                    if param['param_name'] == old_param_info['param_name']:
                        source_params.pop(i)
                        break
            
            
            if current_tab_name in tool_page.config_data:
                if self.title not in tool_page.config_data[current_tab_name]:
                    tool_page.config_data[current_tab_name][self.title] = []
                tool_page.config_data[current_tab_name][self.title] = self.params.copy()
            
            
            self.sync_config_to_other_tabs(old_param_info, new_param_info, source_section, current_tab_name)
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"更新配置数据失败: {e}", "error")
    
    def sync_config_to_other_tabs(self, old_param_info, new_param_info, source_section, current_tab):
        
        try:
            tool_page = self.get_tool_operation_page()
            if not tool_page:
                return
            
            for tab_name in ['常用参数', '全部参数']:
                if tab_name != current_tab and tab_name in tool_page.config_data:
                    
                    if source_section in tool_page.config_data[tab_name]:
                        source_params = tool_page.config_data[tab_name][source_section]
                        for i, param in enumerate(source_params):
                            if param['param_name'] == old_param_info['param_name']:
                                source_params.pop(i)
                                break
                    
                    
                    if self.title not in tool_page.config_data[tab_name]:
                        tool_page.config_data[tab_name][self.title] = []
                    
                    
                    target_params = tool_page.config_data[tab_name][self.title]
                    if not any(p['param_name'] == new_param_info['param_name'] for p in target_params):
                        target_params.append(new_param_info.copy())
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"同步配置到其他选项卡失败: {e}", "error")
    
    def update_layout_fast(self):
        
        try:
            
            layout = self.layout()
            if not layout:
                return
            
            
            param_container = None
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, QGroupBox):
                        scroll_area = widget.findChild(QScrollArea)
                        if scroll_area:
                            param_container = scroll_area.widget()
                            break
            
            if not param_container:
                return
            
            
            container_layout = param_container.layout()
            if container_layout:
                
                while container_layout.count():
                    child = container_layout.takeAt(0)
                
                
                if self.title == "勾选项区":
                    
                    for i, param_widget in enumerate(self.param_widgets):
                        row = i // 3
                        col = i % 3
                        container_layout.addWidget(param_widget, row, col)
                else:
                    
                    for param_widget in self.param_widgets:
                        container_layout.addWidget(param_widget)
                
                
                if self.title == "勾选项区":
                    container_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), 
                                           len(self.param_widgets) // 3 + 1, 0)
                else:
                    container_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"快速更新布局失败: {e}", "error")
    
    def convert_parameter_type(self, param_info):
        
        new_param_info = param_info.copy()
        
        
        if self.title == "勾选项区":
            
            new_param_info['type'] = '1'
        elif self.title == "输入框区":
            
            new_param_info['type'] = '2'
        
        return new_param_info
    
    def add_converted_parameter(self, param_info, target_index):
        
        try:
            
            if target_index >= len(self.params):
                self.params.append(param_info)
            else:
                self.params.insert(target_index, param_info)
            
            
            param_widget = ParameterWidget(param_info)
            
            
            if target_index >= len(self.param_widgets):
                self.param_widgets.append(param_widget)
            else:
                self.param_widgets.insert(target_index, param_widget)
            
            
            self.update_layout()
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"添加转换参数失败: {e}", "error")
    
    def add_converted_parameter_with_sync(self, param_info, target_index):
        
        try:
            tool_page = self.get_tool_operation_page()
            if not tool_page:
                return
            
            
            self.add_converted_parameter(param_info, target_index)
            
            
            current_tab_name = tool_page.param_tabs.tabText(tool_page.param_tabs.currentIndex())
            
            
            if current_tab_name not in tool_page.config_data:
                tool_page.config_data[current_tab_name] = {}
            if self.title not in tool_page.config_data[current_tab_name]:
                tool_page.config_data[current_tab_name][self.title] = []
            
            
            tool_page.config_data[current_tab_name][self.title] = self.params.copy()
            
            
            tool_page.sync_parameter_addition(param_info, self.title, current_tab_name)
            
        except Exception as e:
            tool_page = self.get_tool_operation_page()
            if tool_page:
                tool_page.system_log_tab.append_system_log(f"添加并同步转换参数失败: {e}", "error")

class ToolParameterTab(QWidget):
    
    
    def __init__(self, config_data):
        super().__init__()
        self.config_data = config_data
        self.sections = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(2, 2, 2, 2)
        scroll_layout.setSpacing(4)
        
        
        sections = ['勾选项区', '输入框区']
        for section_name in sections:
            if section_name in self.config_data and self.config_data[section_name]:
                section = ParameterSection(section_name, self.config_data[section_name])
                self.sections.append(section)
                scroll_layout.addWidget(section)
        
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        self.setLayout(layout)
    
    def get_all_params(self):
        
        all_params = []
        for section in self.sections:
            all_params.extend(section.get_all_params())
        return all_params
    
    def validate_required_params(self):
        
        all_missing_params = []
        for section in self.sections:
            is_valid, missing_params = section.validate_required_params()
            if not is_valid:
                all_missing_params.extend(missing_params)
        
        return len(all_missing_params) == 0, all_missing_params
    
    def update_all_required_styles(self):
        
        for section in self.sections:
            section.update_all_required_styles()

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
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        
        control_widget = QWidget()
        control_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(8, 4, 8, 4)
        control_layout.setSpacing(8)
        
        self.status_label = QLabel("运行中")
        self.status_label.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #28a745;
                background: transparent;
                border: none;
                padding: 2px 6px;
            }
        """)
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        
        
        clear_btn = QPushButton("清屏")
        clear_btn.setMaximumWidth(60)
        clear_btn.setMinimumHeight(28)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                border: 1px solid #6c757d;
                border-radius: 4px;
                padding: 4px 12px;
                color: white;
                font-weight: 500;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #5a6268;
                border-color: #545b62;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        clear_btn.clicked.connect(self.clear_terminal)
        control_layout.addWidget(clear_btn)
        
        stop_btn = QPushButton("停止")
        stop_btn.setMaximumWidth(60)
        stop_btn.setMinimumHeight(28)
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                border: 1px solid #dc3545;
                border-radius: 4px;
                padding: 4px 12px;
                color: white;
                font-weight: 500;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #c82333;
                border-color: #bd2130;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
            }
        """)
        stop_btn.clicked.connect(self.stop_process)
        control_layout.addWidget(stop_btn)
        
        control_widget.setLayout(control_layout)
        layout.addWidget(control_widget)
        
        
        terminal_label = QLabel("交互式终端")
        terminal_label.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        terminal_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 4px 0px;
                margin-bottom: 4px;
            }
        """)
        layout.addWidget(terminal_label)
        
        self.terminal_output = QTextEdit()
        self.terminal_output.setFont(QFont(get_monospace_font(), 9))
        self.terminal_output.setMinimumHeight(400)  
        terminal_style = f"""
            QTextEdit {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2d3748, stop: 1 #1a202c);
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 12px;
                font-family: '{get_monospace_font()}', 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 9pt;
                line-height: 1.5;
                selection-background-color: #4a90e2;
            }}
            QTextEdit:focus {{
                border-color: #4a90e2;
            }}
        """
        self.terminal_output.setStyleSheet(terminal_style)
        
        self.terminal_output.setReadOnly(False)
        
        
        self.terminal_output.keyPressEvent = self.handle_key_press
        
        
        self.terminal_output.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.terminal_output.customContextMenuRequested.connect(self.show_context_menu)
        
        
        self.terminal_output.append("🎯 欢迎使用白猫工具箱交互式终端！")
        self.terminal_output.append("💡 快捷键：Ctrl+C复制 | Ctrl+V粘贴 | Ctrl+A全选 | Ctrl+L清屏")
        self.terminal_output.append("⚡ 进程控制：右键菜单或点击停止按钮可中断进程")
        self.terminal_output.append("📝 系统日志已集成，支持彩色标签分类显示")
        self.append_system_log("[系统] 终端初始化完成", "success")
        self.show_prompt()
        
        layout.addWidget(self.terminal_output)
        
        self.setLayout(layout)
    
    def show_prompt(self):
        
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(self.prompt)
        self.input_start_position = cursor.position()
        self.terminal_output.setTextCursor(cursor)
        self.terminal_output.ensureCursorVisible()
    
    def handle_key_press(self, event):
        
        cursor = self.terminal_output.textCursor()
        
        
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                
                if cursor.hasSelection():
                    self.copy_selection()
                
                return
            elif event.key() == Qt.Key.Key_V:
                
                self.paste_text()
                return
            elif event.key() == Qt.Key.Key_A:
                
                self.terminal_output.selectAll()
                return
            elif event.key() == Qt.Key.Key_L:
                
                self.clear_terminal()
                return
        
        
        if cursor.position() < self.input_start_position:
            cursor.setPosition(self.input_start_position)
            self.terminal_output.setTextCursor(cursor)
        
        
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.execute_command()
            return
        
        
        if event.key() == Qt.Key.Key_Backspace:
            if cursor.position() <= self.input_start_position:
                return  
        
        
        if event.key() == Qt.Key.Key_Up:
            self.show_previous_command()
            return
        elif event.key() == Qt.Key.Key_Down:
            self.show_next_command()
            return
        
        
        if event.key() == Qt.Key.Key_Home:
            cursor.setPosition(self.input_start_position)
            self.terminal_output.setTextCursor(cursor)
            return
        
        
        QTextEdit.keyPressEvent(self.terminal_output, event)
    
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
                
                
                cursor.insertHtml(f"<span style='color: #66d9ef;'>[发送] {user_input}</span>\n")
            else:
                
                self.process.write(b"\n")
        else:
            
            if user_input:
                cursor.insertHtml(f"<span style='color: #f92672;'>[错误] 进程未运行，无法执行命令: {user_input}</span>\n")
        
        
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
                    self.append_system_log("发送中断信号到进程 (Windows)", "warning")
                except Exception as e:
                    self.append_system_log(f"发送中断信号失败: {e}", "error")
                    
                    self.process.kill()
                    self.append_system_log("强制终止进程", "warning")
            else:
                
                try:
                    
                    self.process.write(b'\x03')
                    self.append_system_log("发送中断信号到进程 (Unix)", "warning")
                except Exception as e:
                    self.append_system_log(f"发送中断信号失败: {e}", "error")
                    
                    self.process.terminate()
                    self.append_system_log("尝试优雅终止进程", "warning")
        else:
            self.append_system_log("没有正在运行的进程", "warning")
    
    def show_context_menu(self, position):
        
        menu = QMenu(self.terminal_output)
        
        
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Microsoft YaHei';
                font-size: 10pt;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 24px 8px 32px;
                border-radius: 4px;
                color: #495057;
            }
            QMenu::item:hover {
                background-color: #e3f2fd;
                color: #2c5aa0;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e9ecef;
                margin: 4px 8px;
            }
        """)
        
        cursor = self.terminal_output.textCursor()
        
        
        copy_action = menu.addAction("📋 复制")
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(cursor.hasSelection())
        copy_action.triggered.connect(self.copy_selection)
        
        
        paste_action = menu.addAction("📌 粘贴")
        paste_action.setShortcut("Ctrl+V")
        clipboard = QApplication.clipboard()
        paste_action.setEnabled(bool(clipboard.text()))
        paste_action.triggered.connect(self.paste_text)
        
        menu.addSeparator()
        
        
        select_all_action = menu.addAction("🔍 全选")
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.terminal_output.selectAll)
        
        menu.addSeparator()
        
        
        clear_action = menu.addAction("🧹 清屏")
        clear_action.setShortcut("Ctrl+L")
        clear_action.triggered.connect(self.clear_terminal)
        
        
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            menu.addSeparator()
            interrupt_action = menu.addAction("⛔ 中断进程")
            interrupt_action.triggered.connect(self.interrupt_process)
        
        
        menu.exec(self.terminal_output.mapToGlobal(position))
    
    def append_system_log(self, text, log_type="info"):
        
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        
        if log_type == "error":
            color = "#ff6b6b"
            icon = "❌"
            prefix = "ERROR"
        elif log_type == "warning":
            color = "#ffa726"
            icon = "⚠️"
            prefix = "WARN"
        elif log_type == "success":
            color = "#66bb6a"
            icon = "✅"
            prefix = "SUCCESS"
        elif log_type == "info":
            color = "#42a5f5"
            icon = "ℹ️"
            prefix = "INFO"
        else:
            color = "#e2e8f0"
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
        
        
        log_html = f"""<span style='color: #718096; font-size: 8pt;'>[{timestamp}]</span> <span style='color: {color}; font-weight: bold;'>{icon} {prefix}</span> <span style='color: #e2e8f0;'>{text}</span>"""
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
    
    def stop_process(self):
        
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.status_label.setText("已停止")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    background: transparent;
                    border: none;
                    padding: 2px 6px;
                    font-weight: bold;
                }
            """)
            self.append_system_log("进程已被用户手动停止", "warning")
    
    def process_finished(self, exit_code):
        
        if exit_code == 0:
            self.status_label.setText("完成")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    background: transparent;
                    border: none;
                    padding: 2px 6px;
                    font-weight: bold;
                }
            """)
            self.append_system_log(f"进程正常完成，退出代码: {exit_code}", "success")
        else:
            self.status_label.setText("错误")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    background: transparent;
                    border: none;
                    padding: 2px 6px;
                    font-weight: bold;
                }
            """)
            self.append_system_log(f"进程异常退出，退出代码: {exit_code}", "error")
        
        
        self.show_prompt()

class ToolOperationPage(QWidget):
    
    
    def __init__(self, tool_name):
        super().__init__()
        self.tool_name = tool_name
        self.config_data = None
        self.processes = []
        self.command_history = {}  
        self.setup_ui()
        self.load_config()
        self.load_command_history()
    
    def setup_ui(self):
        
        main_splitter = QSplitter(Qt.Horizontal)
        
        
        left_widget = self.create_parameter_page()
        main_splitter.addWidget(left_widget)
        
        
        right_widget = self.create_runtime_page()
        main_splitter.addWidget(right_widget)
        
        
        main_splitter.setSizes([400, 600])
        
        layout = QHBoxLayout()
        layout.addWidget(main_splitter)
        self.setLayout(layout)
    
    def create_parameter_page(self):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        
        top_widget = QWidget()
        top_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(8, 8, 8, 8)
        top_layout.setSpacing(12)
        
        tool_label = QLabel(self.tool_name)
        tool_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        tool_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 4px 0px;
            }
        """)
        top_layout.addWidget(tool_label)
        
        top_layout.addStretch()
        
        
        clear_btn = QPushButton("清空选项")
        clear_btn.setMaximumWidth(90)
        clear_btn.setMinimumHeight(36)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #ff9500;
                border-radius: 6px;
                padding: 8px 16px;
                color: #ff9500;
                font-weight: 500;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #fff7e6;
                border-color: #e6850e;
            }
            QPushButton:pressed {
                background-color: #ffe6cc;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_params)
        top_layout.addWidget(clear_btn)
        
        custom_btn = QPushButton("自定义模板")
        custom_btn.setMaximumWidth(100)
        custom_btn.setMinimumHeight(36)
        custom_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #4a90e2;
                border-radius: 6px;
                padding: 8px 16px;
                color: #4a90e2;
                font-weight: 500;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #f0f7ff;
                border-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #e3f2fd;
            }
        """)
        custom_btn.clicked.connect(self.open_template_manager)
        top_layout.addWidget(custom_btn)
        
        run_btn = QPushButton("开始运行")
        run_btn.setMaximumWidth(100)
        run_btn.setMinimumHeight(36)
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                border: 1px solid #4a90e2;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: 600;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #357abd;
                border-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2c5aa0;
            }
        """)
        run_btn.clicked.connect(self.start_tool)
        top_layout.addWidget(run_btn)
        
        top_widget.setLayout(top_layout)
        layout.addWidget(top_widget)
        
        
        cmd_widget = QWidget()
        cmd_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        cmd_layout = QHBoxLayout()
        cmd_layout.setContentsMargins(8, 8, 8, 8)
        cmd_layout.setSpacing(12)
        
        cmd_label = QLabel("运行命令:")
        cmd_label.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
        cmd_label.setFixedWidth(80)
        cmd_label.setStyleSheet("""
            QLabel {
                color: #495057;
                background: transparent;
                border: none;
                padding: 4px 0px;
            }
        """)
        cmd_layout.addWidget(cmd_label)
        
        self.command_input = QLineEdit()
        self.command_input.setMinimumHeight(32)
        self.command_input.setPlaceholderText("请输入工具运行命令，如: python tool.py 或 tool.exe")
        self.command_input.setToolTip("输入完整的工具运行命令，支持任何可执行文件或脚本")
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 8px 12px;
                color: #495057;
                font-size: 9pt;
                selection-background-color: #4a90e2;
            }
            QLineEdit:focus {
                border-color: #4a90e2;
                background-color: #ffffff;
            }
            QLineEdit:hover {
                border-color: #ced4da;
            }
        """)
        self.command_input.textChanged.connect(self.save_command)
        cmd_layout.addWidget(self.command_input)
        
        cmd_widget.setLayout(cmd_layout)
        layout.addWidget(cmd_widget)
        
        
        self.param_tabs = QTabWidget()
        self.param_tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 4px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-bottom: none;
                border-radius: 6px 6px 0px 0px;
                padding: 8px 16px;
                margin: 0px 2px;
                color: #6c757d;
                font-weight: 500;
                font-size: 9pt;
                min-width: 80px;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
                color: #495057;
            }
            QTabBar::tab:selected {
                background-color: #4a90e2;
                color: white;
                font-weight: 600;
                border-color: #4a90e2;
            }
        """)
        
        
        global_search_container = self.create_global_search_bar()
        layout.addWidget(global_search_container)
        
        layout.addWidget(self.param_tabs)
        
        widget.setLayout(layout)
        return widget
    
    def create_global_search_bar(self):
        
        search_container = QWidget()
        search_container.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 6, 8, 6)
        search_layout.setSpacing(12)
        
        
        search_icon = QLabel("🔍 全局搜索:")
        search_icon.setFont(QFont(get_system_font(), 9, QFont.Bold))
        search_icon.setStyleSheet("color: #495057; border: none; background: transparent;")
        search_icon.setFixedWidth(90)
        
        
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText("在所有参数中搜索（参数名、显示名、介绍等）...")
        self.global_search_input.setFont(QFont(get_system_font(), 9))
        self.global_search_input.textChanged.connect(self.on_global_search_changed)
        
        
        self.global_search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #ffffff;
                font-size: 9pt;
                color: #495057;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
                background-color: #ffffff;
                outline: none;
            }
            QLineEdit:hover {
                border-color: #adb5bd;
                background-color: #ffffff;
            }
        """)
        
        
        self.global_clear_btn = QPushButton("清除")
        self.global_clear_btn.setFont(QFont(get_system_font(), 8))
        self.global_clear_btn.setFixedSize(50, 28)
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
        self.global_result_label.setFont(QFont(get_system_font(), 8))
        self.global_result_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        self.global_result_label.setVisible(False)
        
        
        search_mode_label = QLabel("搜索模式:")
        search_mode_label.setFont(QFont(get_system_font(), 8))
        search_mode_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems(["智能搜索", "精确匹配", "正则表达式"])
        self.search_mode_combo.setCurrentText("智能搜索")
        self.search_mode_combo.setFont(QFont(get_system_font(), 8))
        self.search_mode_combo.setFixedWidth(100)
        self.search_mode_combo.currentTextChanged.connect(self.on_search_mode_changed)
        
        self.search_mode_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #ffffff;
                color: #495057;
                font-size: 8pt;
            }
            QComboBox:hover {
                border-color: #adb5bd;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                border: none;
                background: transparent;
            }
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
        
        
        for tab_index in range(self.param_tabs.count()):
            tab_widget = self.param_tabs.widget(tab_index)
            if isinstance(tab_widget, ToolParameterTab):
                
                for section in tab_widget.findChildren(ParameterSection):
                    section_matches = self.search_in_section(section, search_text, search_mode)
                    total_matches += section_matches
                    total_params += len(section.param_widgets)
        
        
        if total_matches == 0:
            self.global_result_label.setText("❌ 未找到匹配的参数")
            self.global_result_label.setStyleSheet("color: #dc3545; border: none; background: transparent; font-weight: 500;")
        else:
            self.global_result_label.setText(f"✅ 找到 {total_matches}/{total_params} 个参数")
            self.global_result_label.setStyleSheet("color: #28a745; border: none; background: transparent; font-weight: 500;")
        
        self.global_result_label.setVisible(True)
        
        
        self.system_log_tab.append_system_log(
            f"全局搜索 '{search_text}' ({search_mode}): 找到 {total_matches} 个匹配参数",
            "info"
        )
    
    def search_in_section(self, section, search_text, search_mode):
        
        matches = 0
        
        for param_widget in section.param_widgets:
            is_match = False
            
            if search_mode == "智能搜索":
                is_match = self.smart_search_match(param_widget.param_info, search_text.lower())
            elif search_mode == "精确匹配":
                is_match = self.exact_search_match(param_widget.param_info, search_text)
            elif search_mode == "正则表达式":
                is_match = self.regex_search_match(param_widget.param_info, search_text)
            
            if is_match:
                param_widget.setVisible(True)
                section.highlight_search_match(param_widget, search_text.lower())
                matches += 1
            else:
                param_widget.setVisible(False)
                section.clear_highlight(param_widget)
        
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
        
        
        for tab_index in range(self.param_tabs.count()):
            tab_widget = self.param_tabs.widget(tab_index)
            if isinstance(tab_widget, ToolParameterTab):
                for section in tab_widget.findChildren(ParameterSection):
                    section.show_all_parameters()
        
        self.global_result_label.setVisible(False)
    
    def create_runtime_page(self):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        
        self.process_tabs = QTabWidget()
        self.process_tabs.setTabsClosable(True)
        self.process_tabs.tabCloseRequested.connect(self.close_process_tab)
        
        
        self.system_log_tab = ProcessTab(None, "系统日志", self.process_tabs)
        self.system_log_tab.terminal_output.setHtml("""
        <div style='color: #e2e8f0; background: transparent;'>
        🎯 <b>白猫工具箱系统日志</b><br/>
        📝 此标签页集成了所有系统日志信息<br/>
        💡 包括工具启动、参数验证、进程管理等操作记录<br/>
        ⚡ 实时显示系统运行状态和错误信息<br/>
        </div>
        """)
        self.system_log_tab.append_system_log("系统日志模块初始化完成", "success")
        system_tab_index = self.process_tabs.addTab(self.system_log_tab, "📊 系统日志")
        
        
        self.process_tabs.tabBar().setTabButton(system_tab_index, self.process_tabs.tabBar().ButtonPosition.RightSide, None)
        self.process_tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-bottom: none;
                border-radius: 6px 6px 0px 0px;
                padding: 6px 12px;
                margin: 0px 1px;
                color: #6c757d;
                font-weight: 500;
                font-size: 8pt;
                min-width: 60px;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
                color: #495057;
            }
            QTabBar::tab:selected {
                background-color: #4a90e2;
                color: white;
                font-weight: 600;
                border-color: #4a90e2;
            }
            QTabBar::close-button {
                background-color: rgba(108, 117, 125, 0.1);
                border: none;
                border-radius: 6px;
                width: 14px;
                height: 14px;
                margin: 2px;
                subcontrol-position: right;
            }
            QTabBar::close-button:hover {
                background-color: #dc3545;
                border-radius: 6px;
            }
            QTabBar::close-button:pressed {
                background-color: #a71e2a;
            }
        """)
        layout.addWidget(self.process_tabs)
        
        widget.setLayout(layout)
        return widget
    
    def load_config(self):
        
        config_path = os.path.join("tools", self.tool_name, "wct_config.txt")
        self.config_data = ToolConfigParser.parse_config(config_path)
        
        
        self.param_tabs.clear()
        
        
        if '常用参数' in self.config_data:
            common_tab = ToolParameterTab(self.config_data['常用参数'])
            self.param_tabs.addTab(common_tab, "常用参数")
        
        
        if '全部参数' in self.config_data:
            all_tab = ToolParameterTab(self.config_data['全部参数'])
            self.param_tabs.addTab(all_tab, "全部参数")
    
    def start_tool(self):
        
        
        current_tab = self.param_tabs.currentWidget()
        if not current_tab:
            self.system_log_tab.append_system_log("没有选择参数选项卡", "error")
            return
        
        
        is_valid, missing_params = current_tab.validate_required_params()
        if not is_valid:
            missing_list = "\n• ".join(missing_params)
            error_msg = f"以下必填参数尚未填写，请检查后重试：\n\n• {missing_list}"
            self.system_log_tab.append_system_log(f"必填参数验证失败: {', '.join(missing_params)}", "error")
            
            
            if hasattr(self, 'show_custom_message'):
                self.show_custom_message("参数验证失败", error_msg)
            else:
                
                from PySide6.QtWidgets import QMessageBox
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("参数验证失败")
                msg_box.setText(error_msg)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.exec()
            return
        
        params = current_tab.get_all_params()
        
        
        user_command = self.command_input.text().strip()
        if not user_command:
            self.system_log_tab.append_system_log("请输入工具运行命令", "error")
            return
        
        
        tool_path = os.path.join("tools", self.tool_name)
        
        try:
            command = build_cross_platform_command(tool_path, user_command, params)
        except ValueError as e:
            self.system_log_tab.append_system_log(str(e), "error")
            return
        except Exception as e:
            self.system_log_tab.append_system_log(f"构建命令时发生错误: {e}", "error")
            return
        
        self.system_log_tab.append_system_log(f"工具 {self.tool_name} 启动", "info")
        self.system_log_tab.append_system_log(f"执行命令: {' '.join(command)}", "info")
        
        
        process_tab = ProcessTab(None, f"进程{len(self.processes) + 1}", self.process_tabs)
        tab_index = self.process_tabs.addTab(process_tab, f"进程{len(self.processes) + 1}")
        self.process_tabs.setCurrentIndex(tab_index)
        
        
        process_tab.append_system_log(f"开始运行工具: {self.tool_name}", "info")
        process_tab.append_system_log(f"执行命令: {' '.join(command)}", "info")
        process_tab.append_system_log("您可以在下方输入命令与程序交互", "info")
        
        
        process = ToolProcess(self, process_tab)
        process_tab.process = process
        process.start(command[0], command[1:])
        
        
        process_tab.show_prompt()
        
        self.processes.append(process)
        
        
        process.finished.connect(lambda code, status: self.process_finished(process, code, status))
    
    def process_finished(self, process, exit_code, exit_status):
        
        if exit_code == 0:
            self.system_log_tab.append_system_log(f"进程完成，退出代码: {exit_code}", "success")
        else:
            self.system_log_tab.append_system_log(f"进程完成，退出代码: {exit_code}", "error")
        
        
        for i in range(self.process_tabs.count()):
            tab_widget = self.process_tabs.widget(i)
            if isinstance(tab_widget, ProcessTab) and tab_widget.process == process:
                tab_widget.process_finished(exit_code)
                break
    
    def close_process_tab(self, index):
        
        tab_widget = self.process_tabs.widget(index)
        if isinstance(tab_widget, ProcessTab):
            
            tab_widget.stop_process()
            self.system_log_tab.append_system_log("进程标签页关闭，进程已终止", "warning")
        
        
        self.process_tabs.removeTab(index)
    
    def save_command(self):
        
        command = self.command_input.text().strip()
        self.command_history[self.tool_name] = command
        
        try:
            import json
            with open("command_history.json", "w", encoding="utf-8") as f:
                json.dump(self.command_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存命令历史失败: {e}")
    
    def load_command_history(self):
        
        try:
            import json
            with open("command_history.json", "r", encoding="utf-8") as f:
                self.command_history = json.load(f)
            
            
            if self.tool_name in self.command_history:
                self.command_input.setText(self.command_history[self.tool_name])
            else:
                
                default_commands = {
                    "OneForAll": "python oneforall.py"
                }
                if self.tool_name in default_commands:
                    self.command_input.setText(default_commands[self.tool_name])
        except FileNotFoundError:
            
            default_commands = {
                "OneForAll": "python oneforall.py"
            }
            if self.tool_name in default_commands:
                self.command_input.setText(default_commands[self.tool_name])
        except Exception as e:
            print(f"加载命令历史失败: {e}")
    
    def open_template_manager(self):
        
        template_manager = TemplateManager(self.tool_name, self)
        template_manager.exec()
    
    def clear_all_params(self):
        
        
        current_tab = self.param_tabs.currentWidget()
        if not current_tab:
            self.system_log_tab.append_system_log("没有选择参数选项卡", "warning")
            return
        
        cleared_count = 0
        
        for section in current_tab.sections:
            for param_widget in section.param_widgets:
                if isinstance(param_widget.control, (QCheckBox, ClickableLabel)):
                    if param_widget.control.isChecked():
                        param_widget.control.setChecked(False)
                        cleared_count += 1
                elif isinstance(param_widget.control, QLineEdit):
                    if param_widget.control.text().strip():
                        param_widget.control.clear()
                        cleared_count += 1
        
        self.system_log_tab.append_system_log(f"已清空 {cleared_count} 个参数选项", "info")
        
        
        current_tab.update_all_required_styles()
    
    def save_config_to_file(self):
        
        try:
            config_path = os.path.join("tools", self.tool_name, "wct_config.txt")
            
            
            backup_path = config_path + ".bak"
            if os.path.exists(config_path):
                import shutil
                shutil.copy2(config_path, backup_path)
                self.system_log_tab.append_system_log(f"配置文件已备份到: {backup_path}", "info")
            
            
            with open(config_path, 'w', encoding='utf-8') as f:
                
                if '常用参数' in self.config_data:
                    f.write("%常用参数\n")
                    self._write_section_to_file(f, self.config_data['常用参数'])
                    f.write("\n")
                
                
                if '全部参数' in self.config_data:
                    f.write("%全部参数\n")
                    self._write_section_to_file(f, self.config_data['全部参数'])
            
            self.system_log_tab.append_system_log(f"配置文件已保存到: {config_path}", "success")
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"保存配置文件失败: {e}", "error")
            import traceback
            self.system_log_tab.append_system_log(f"详细错误: {traceback.format_exc()}", "error")
    
    def _write_section_to_file(self, file, section_data):
        
        for subsection_name, params in section_data.items():
            if subsection_name in ['勾选项区', '输入框区']:
                if subsection_name == '勾选项区':
                    file.write("%%勾选项\n")
                elif subsection_name == '输入框区':
                    file.write("%%输入项\n")
                
                for param in params:
                    required_flag = '1' if param.get('required', False) else '0'
                    
                    param_name = str(param.get('param_name', '')).replace('\n', ' ').strip()
                    display_name = str(param.get('display_name', '')).replace('\n', ' ').strip()
                    description = str(param.get('description', '')).replace('\n', ' ').strip()
                    
                    
                    if not param_name or not display_name:
                        continue
                    
                    line = f"{param_name}={display_name}={description}={required_flag}\n"
                    file.write(line)
                file.write("\n")
    
    def reload_config(self):
        
        self.load_config()
        
        for i in range(self.param_tabs.count()):
            tab = self.param_tabs.widget(i)
            if hasattr(tab, 'update_all_required_styles'):
                tab.update_all_required_styles()
    
    def sync_required_status(self, param_name, required_status):
        
        
        for section_name in ['常用参数', '全部参数']:
            if section_name in self.config_data:
                for subsection_name in ['勾选项区', '输入框区']:
                    if subsection_name in self.config_data[section_name]:
                        for param in self.config_data[section_name][subsection_name]:
                            if param['param_name'] == param_name:
                                param['required'] = required_status
        
        
        for i in range(self.param_tabs.count()):
            tab_widget = self.param_tabs.widget(i)
            if hasattr(tab_widget, 'sections'):
                for section in tab_widget.sections:
                    for param_widget in section.param_widgets:
                        if param_widget.param_info['param_name'] == param_name:
                            param_widget.param_info['required'] = required_status
                            param_widget.update_ui_from_param_info()
    
    def move_parameter_between_tabs(self, param_info, from_tab, to_tab):
        
        try:
            
            from_section = from_tab
            to_section = to_tab
            
            
            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'
            
            
            if (from_section in self.config_data and 
                subsection in self.config_data[from_section]):
                
                params_list = self.config_data[from_section][subsection]
                for i, param in enumerate(params_list):
                    if param['param_name'] == param_info['param_name']:
                        removed_param = params_list.pop(i)
                        break
                else:
                    self.system_log_tab.append_system_log(f"在{from_section}中未找到参数", "error")
                    return
            
            
            if to_section not in self.config_data:
                self.config_data[to_section] = {}
            if subsection not in self.config_data[to_section]:
                self.config_data[to_section][subsection] = []
            
            
            target_params = self.config_data[to_section][subsection]
            for param in target_params:
                if param['param_name'] == param_info['param_name']:
                    self.system_log_tab.append_system_log(f"目标区域已存在同名参数", "warning")
                    
                    self.config_data[from_section][subsection].append(removed_param)
                    return
            
            
            self.config_data[to_section][subsection].append(removed_param)
            
            
            self.save_config_to_file()
            
            
            self.reload_config()
            
            
            for i in range(self.param_tabs.count()):
                if self.param_tabs.tabText(i) == to_section:
                    self.param_tabs.setCurrentIndex(i)
                    break
            
            self.system_log_tab.append_system_log(
                f"参数 '{param_info['display_name']}' 已从{from_section}移动到{to_section}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"移动参数失败: {e}", "error")
    
    def add_parameter_to_section(self, param_info, section_title):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())
            
            
            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'
            
            
            if current_tab_name in self.config_data:
                if subsection in self.config_data[current_tab_name]:
                    for existing_param in self.config_data[current_tab_name][subsection]:
                        if existing_param['param_name'] == param_info['param_name']:
                            self.system_log_tab.append_system_log(f"参数名 '{param_info['param_name']}' 已存在", "error")
                            return
            
            
            if current_tab_name not in self.config_data:
                self.config_data[current_tab_name] = {}
            if subsection not in self.config_data[current_tab_name]:
                self.config_data[current_tab_name][subsection] = []
            
            self.config_data[current_tab_name][subsection].append(param_info)
            
            
            self.save_config_to_file()
            
            
            self.reload_config()
            
            self.system_log_tab.append_system_log(
                f"新参数 '{param_info['display_name']}' 已添加到{current_tab_name}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"添加参数失败: {e}", "error")
    
    def update_parameter_in_config(self, old_param_name, new_param_info):
        
        try:
            
            param_type = new_param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'
            
            
            for section_name in ['常用参数', '全部参数']:
                if section_name in self.config_data:
                    for subsection_name in ['勾选项区', '输入框区']:
                        if subsection_name in self.config_data[section_name]:
                            params_list = self.config_data[section_name][subsection_name]
                            for i, param in enumerate(params_list):
                                if param['param_name'] == old_param_name:
                                    
                                    if subsection_name != subsection:
                                        
                                        removed_param = params_list.pop(i)
                                        
                                        if subsection not in self.config_data[section_name]:
                                            self.config_data[section_name][subsection] = []
                                        self.config_data[section_name][subsection].append(new_param_info.copy())
                                    else:
                                        
                                        params_list[i] = new_param_info.copy()
                                    break
            
            self.system_log_tab.append_system_log(
                f"参数 '{new_param_info['display_name']}' 信息已更新", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"更新参数信息失败: {e}", "error")
    
    def remove_parameter_from_common(self, param_info):
        
        try:
            
            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'
            
            
            if ('常用参数' in self.config_data and 
                subsection in self.config_data['常用参数']):
                
                params_list = self.config_data['常用参数'][subsection]
                for i, param in enumerate(params_list):
                    if param['param_name'] == param_info['param_name']:
                        removed_param = params_list.pop(i)
                        break
                else:
                    self.system_log_tab.append_system_log(f"在常用参数中未找到参数", "error")
                    return
            
            
            self.save_config_to_file()
            
            
            self.reload_config()
            
            self.system_log_tab.append_system_log(
                f"参数 '{param_info['display_name']}' 已从常用参数中移除", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"移除参数失败: {e}", "error")
    
    def copy_parameter_to_common(self, param_info):
        
        try:
            
            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'
            
            
            if '常用参数' not in self.config_data:
                self.config_data['常用参数'] = {}
            if subsection not in self.config_data['常用参数']:
                self.config_data['常用参数'][subsection] = []
            
            
            params_list = self.config_data['常用参数'][subsection]
            for param in params_list:
                if param['param_name'] == param_info['param_name']:
                    self.system_log_tab.append_system_log(f"常用参数中已存在该参数", "warning")
                    return
            
            
            param_copy = param_info.copy()
            params_list.append(param_copy)
            
            
            self.save_config_to_file()
            
            
            self.reload_config()
            
            
            for i in range(self.param_tabs.count()):
                if self.param_tabs.tabText(i) == "常用参数":
                    self.param_tabs.setCurrentIndex(i)
                    break
            
            self.system_log_tab.append_system_log(
                f"参数 '{param_info['display_name']}' 已添加到常用参数", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"添加参数到常用参数失败: {e}", "error")
    
    def show_custom_question(self, title, message):
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(500, 260)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        dialog.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: 16px;
                {get_system_font_css()}
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        title_label = QLabel(title)
        title_label.setFont(QFont(get_system_font(), 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 8px; font-weight: 700;")
        layout.addWidget(title_label)
        
        msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(12)
        
        icon_label = QLabel("❓")
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 20pt;")
        msg_layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont(get_system_font(), 11))
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setStyleSheet("color: #495057; padding: 8px; line-height: 1.4;")
        msg_layout.addWidget(msg_label, 1)
        
        msg_container.setLayout(msg_layout)
        layout.addWidget(msg_container)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumSize(90, 40)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: 10px;
                color: #6c757d;
                font-weight: 500;
                font-size: 12pt;
                {get_system_font_css()}
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #495057;
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(90, 40)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                font-size: 12pt;
                {get_system_font_css()}
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        return dialog.exec() == QDialog.Accepted

    def sync_parameter_order(self, section_title, new_params_order):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())
            
            
            subsection = section_title
            
            
            if current_tab_name in self.config_data:
                if subsection in self.config_data[current_tab_name]:
                    self.config_data[current_tab_name][subsection] = new_params_order.copy()
                    
                    
                    for other_tab_name in ['常用参数', '全部参数']:
                        if (other_tab_name != current_tab_name and 
                            other_tab_name in self.config_data and 
                            subsection in self.config_data[other_tab_name]):
                            
                            
                            param_map = {param['param_name']: param for param in new_params_order}
                            other_params = self.config_data[other_tab_name][subsection]
                            
                            
                            reordered_other_params = []
                            remaining_params = other_params.copy()
                            
                            
                            for param in new_params_order:
                                param_name = param['param_name']
                                for other_param in remaining_params:
                                    if other_param['param_name'] == param_name:
                                        reordered_other_params.append(other_param)
                                        remaining_params.remove(other_param)
                                        break
                            
                            
                            reordered_other_params.extend(remaining_params)
                            
                            
                            self.config_data[other_tab_name][subsection] = reordered_other_params
            
            self.system_log_tab.append_system_log(
                f"已同步 {section_title} 的参数顺序到全局配置", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"同步参数顺序失败: {e}", "error")
    
    def remove_parameter_from_section(self, param_name, section_name):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())
            
            
            for subsection_name in ['勾选项区', '输入框区']:
                if (current_tab_name in self.config_data and 
                    subsection_name in self.config_data[current_tab_name]):
                    
                    params_list = self.config_data[current_tab_name][subsection_name]
                    for i, param in enumerate(params_list):
                        if param['param_name'] == param_name:
                            removed_param = params_list.pop(i)
                            
                            
                            self.sync_parameter_removal(param_name, subsection_name, current_tab_name)
                            
                            self.system_log_tab.append_system_log(
                                f"参数 '{param['display_name']}' 已从 {section_name} 中移除", 
                                "info"
                            )
                            return removed_param
            
            return None
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"移除参数失败: {e}", "error")
            return None
    
    def sync_parameter_removal(self, param_name, subsection_name, exclude_tab):
        
        try:
            for tab_name in ['常用参数', '全部参数']:
                if (tab_name != exclude_tab and 
                    tab_name in self.config_data and 
                    subsection_name in self.config_data[tab_name]):
                    
                    params_list = self.config_data[tab_name][subsection_name]
                    for i, param in enumerate(params_list):
                        if param['param_name'] == param_name:
                            params_list.pop(i)
                            break
        except Exception as e:
            self.system_log_tab.append_system_log(f"同步移除参数失败: {e}", "error")
    
    def sync_parameter_addition(self, param_info, target_section, exclude_tab):
        
        try:
            
            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'
            
            for tab_name in ['常用参数', '全部参数']:
                if (tab_name != exclude_tab and 
                    tab_name in self.config_data):
                    
                    
                    if subsection not in self.config_data[tab_name]:
                        self.config_data[tab_name][subsection] = []
                    
                    
                    params_list = self.config_data[tab_name][subsection]
                    param_exists = any(p['param_name'] == param_info['param_name'] for p in params_list)
                    
                    if not param_exists:
                        
                        param_copy = param_info.copy()
                        params_list.append(param_copy)
                        
        except Exception as e:
            self.system_log_tab.append_system_log(f"同步添加参数失败: {e}", "error")

    def show_custom_message(self, title, message):
        
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(450, 240)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: 16px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 8px;
                font-weight: 700;
            }
        """)
        layout.addWidget(title_label)
        
        
        msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(12)
        
        
        icon_label = QLabel("⚠️")
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 20pt;")
        msg_layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Microsoft YaHei", 11))
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setStyleSheet("""
            QLabel {
                color: #495057;
                background: transparent;
                border: none;
                padding: 8px;
                line-height: 1.4;
            }
        """)
        msg_layout.addWidget(msg_label, 1)
        
        msg_container.setLayout(msg_layout)
        layout.addWidget(msg_container)
        
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(100, 40)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                font-size: 12pt;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
}
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec()

class PromotionPage(QWidget):
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_file = "promotion_config.json"
        self.ads_enabled = self.load_ads_config()
        
        QTimer.singleShot(0, self.setup_ui)
    
    def load_ads_config(self):
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('ads_enabled', True)
        except:
            pass
        return True
    
    def save_ads_config(self):
        
        try:
            config = {'ads_enabled': self.ads_enabled}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存推广配置失败: {e}")
    
    def setup_ui(self):
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        
        top_layout = QHBoxLayout()
        
        
        title_label = QLabel("推广信息")
        title_label.setFont(QFont(get_system_font(), 14, QFont.Bold))
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 12px 8px;
                background: transparent;
                border: none;
            }
        """)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        
        self.ads_toggle_btn = QPushButton("关闭推广" if self.ads_enabled else "开启推广")
        self.ads_toggle_btn.setFont(QFont(get_system_font(), 9))
        self.ads_toggle_btn.setFixedHeight(32)
        self.ads_toggle_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ads_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
            }
        
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.ads_toggle_btn.clicked.connect(self.toggle_ads)
        top_layout.addWidget(self.ads_toggle_btn)
        
        layout.addLayout(top_layout)
        
        
        self.content_widget = QWidget()
        self.setup_content()
        layout.addWidget(self.content_widget)
        
        self.setLayout(layout)
    
    def setup_content(self):
        
        
        if self.content_widget.layout():
            old_layout = self.content_widget.layout()
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            QWidget().setLayout(old_layout)
        
        if not self.ads_enabled:
            
            layout = QVBoxLayout()
            layout.setAlignment(Qt.AlignCenter)
            
            info_label = QLabel("推广已关闭")
            info_label.setFont(QFont(get_system_font(), 14, QFont.Bold))
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("""
                QLabel {
                    color: #6c757d;
                    padding: 50px;
                    background-color: transparent;
                    border: none;
                }
            """)
            layout.addWidget(info_label)
            
            self.content_widget.setLayout(layout)
            return
        
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        
        left_ad = self.create_ad_widget("promotion/xm.txt")
        layout.addWidget(left_ad)
        
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("""
            QFrame {
                color: #dee2e6;
                background-color: #dee2e6;
                border: none;
                width: 2px;
            }
        """)
        layout.addWidget(separator1)
        
        
        sponsor_widget = self.create_sponsor_widget("promotion/zz.txt")
        layout.addWidget(sponsor_widget)
        
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("""
            QFrame {
                color: #dee2e6;
                background-color: #dee2e6;
                border: none;
                width: 2px;
            }
        """)
        layout.addWidget(separator2)
        
        
        right_ad = self.create_ad_widget("promotion/gg.txt")
        layout.addWidget(right_ad)
        
        self.content_widget.setLayout(layout)
    
    def create_ad_widget(self, file_path):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        scroll_content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignTop)
        
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    if lines:
                        for line in lines:
                            line = line.strip()
                            if line:  
                                item_widget = self.create_promotion_item(line)
                                if item_widget:
                                    layout.addWidget(item_widget)
                    else:
                        
                        empty_label = QLabel("暂无推广内容")
                        empty_label.setFont(QFont(get_system_font(), 10))
                        empty_label.setAlignment(Qt.AlignCenter)
                        empty_label.setStyleSheet("""
                            QLabel {
                                color: #6c757d;
                                padding: 20px;
                            }
                        """)
                        layout.addWidget(empty_label)
            else:
                
                error_label = QLabel(f"推广文件 {file_path} 不存在")
                error_label.setFont(QFont(get_system_font(), 10))
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("""
                    QLabel {
                        color: #dc3545;
                        padding: 20px;
                    }
                """)
                layout.addWidget(error_label)
        
        except Exception as e:
            
            error_label = QLabel(f"读取推广内容失败: {str(e)}")
            error_label.setFont(QFont(get_system_font(), 10))
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    padding: 20px;
                }
            """)
            layout.addWidget(error_label)
        
        layout.addStretch()
        scroll_content.setLayout(layout)
        scroll_area.setWidget(scroll_content)
        
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll_area)
        widget.setLayout(main_layout)
        
        return widget
    
    def create_sponsor_widget(self, file_path):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        
        title_label = QLabel("🎉 赞助榜")
        title_label.setFont(QFont(get_system_font(), 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background-color: #f8f9fa;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 8px;
            }
        """)
        main_layout.addWidget(title_label)
        
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        scroll_content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setAlignment(Qt.AlignTop)
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if lines:
                    
                    ranking_data, history_data = self.parse_sponsor_data(lines)
                    
                    
                    if ranking_data:
                        ranking_widget = self.create_ranking_widget(ranking_data)
                        content_layout.addWidget(ranking_widget)
                    
                    
                    if history_data:
                        history_widget = self.create_history_widget(history_data[:8])  
                        content_layout.addWidget(history_widget)
                else:
                    
                    empty_label = QLabel("暂无赞助信息")
                    empty_label.setFont(QFont(get_system_font(), 10))
                    empty_label.setAlignment(Qt.AlignCenter)
                    empty_label.setStyleSheet("""
                        QLabel {
                            color: #6c757d;
                            padding: 20px;
                        }
                    """)
                    content_layout.addWidget(empty_label)
            else:
                
                error_label = QLabel(f"赞助文件 {file_path} 不存在")
                error_label.setFont(QFont(get_system_font(), 10))
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("""
                    QLabel {
                        color: #dc3545;
                        padding: 20px;
                    }
                """)
                content_layout.addWidget(error_label)
        
        except Exception as e:
            
            error_label = QLabel(f"读取赞助信息失败: {str(e)}")
            error_label.setFont(QFont(get_system_font(), 10))
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    padding: 20px;
                }
            """)
            content_layout.addWidget(error_label)
        
        content_layout.addStretch()
        scroll_content.setLayout(content_layout)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        widget.setLayout(main_layout)
        return widget
    
    def parse_sponsor_data(self, lines):
        
        ranking_data = []
        history_data = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            
            if line.startswith("排名"):
                current_section = "ranking"
                continue
            elif line.startswith("赞助历史"):
                current_section = "history"
                continue
            elif line.startswith("时间"):
                continue  
            
            
            parts = line.split('\t')
            if len(parts) >= 3:
                if current_section == "ranking":
                    ranking_data.append({
                        'rank': parts[0],
                        'name': parts[1], 
                        'amount': parts[2]
                    })
                elif current_section == "history":
                    history_data.append({
                        'time': parts[0],
                        'name': parts[1],
                        'amount': parts[2]
                    })
        
        return ranking_data, history_data
    
    def create_ranking_widget(self, ranking_data):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 6px;
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        
        title = QLabel("🏆 排行榜")
        title.setFont(QFont(get_system_font(), 10, QFont.Bold))
        title.setStyleSheet("""
            QLabel {
                color: #495057;
                background: transparent;
                padding: 4px 0px;
            }
        """)
        layout.addWidget(title)
        
        
        for item in ranking_data[:5]:  
            rank_widget = QWidget()
            rank_widget.setFixedHeight(32)
            rank_widget.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    border-radius: 4px;
                    margin: 2px;
                }
            """)
            
            rank_layout = QHBoxLayout()
            rank_layout.setContentsMargins(8, 4, 8, 4)
            rank_layout.setSpacing(8)
            
            
            rank_icon = QLabel()
            rank_num = item['rank']
            if rank_num == '1':
                rank_icon.setText("🥇")
            elif rank_num == '2':
                rank_icon.setText("🥈")
            elif rank_num == '3':
                rank_icon.setText("🥉")
            else:
                rank_icon.setText(f"{rank_num}.")
            rank_icon.setFixedWidth(25)
            rank_icon.setFont(QFont(get_system_font(), 8))
            rank_layout.addWidget(rank_icon)
            
            
            name_label = QLabel(item['name'])
            name_label.setFont(QFont(get_system_font(), 8))
            name_label.setStyleSheet("QLabel { color: #495057; }")
            rank_layout.addWidget(name_label)
            
            rank_layout.addStretch()
            
            
            amount_label = QLabel(f"¥{item['amount']}")
            amount_label.setFont(QFont(get_system_font(), 8, QFont.Bold))
            amount_label.setStyleSheet("QLabel { color: #28a745; }")
            rank_layout.addWidget(amount_label)
            
            rank_widget.setLayout(rank_layout)
            layout.addWidget(rank_widget)
        
        widget.setLayout(layout)
        return widget
    
    def create_history_widget(self, history_data):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 6px;
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        
        
        title = QLabel("📝 最近赞助")
        title.setFont(QFont(get_system_font(), 10, QFont.Bold))
        title.setStyleSheet("""
            QLabel {
                color: #495057;
                background: transparent;
                padding: 4px 0px;
            }
        """)
        layout.addWidget(title)
        
        
        for item in history_data:
            history_widget = QWidget()
            history_widget.setFixedHeight(38)
            history_widget.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    border-radius: 4px;
                    margin: 2px;
                }
            """)
            
            history_layout = QVBoxLayout()
            history_layout.setContentsMargins(8, 4, 8, 4)
            history_layout.setSpacing(2)
            
            
            top_layout = QHBoxLayout()
            top_layout.setSpacing(8)
            
            name_label = QLabel(item['name'])
            name_label.setFont(QFont(get_system_font(), 8, QFont.Bold))
            name_label.setStyleSheet("QLabel { color: #495057; }")
            top_layout.addWidget(name_label)
            
            top_layout.addStretch()
            
            amount_label = QLabel(f"¥{item['amount']}")
            amount_label.setFont(QFont(get_system_font(), 8, QFont.Bold))
            amount_label.setStyleSheet("QLabel { color: #28a745; }")
            top_layout.addWidget(amount_label)
            
            
            time_label = QLabel(item['time'])
            time_label.setFont(QFont(get_system_font(), 7))
            time_label.setStyleSheet("QLabel { color: #6c757d; }")
            
            history_layout.addLayout(top_layout)
            history_layout.addWidget(time_label)
            
            history_widget.setLayout(history_layout)
            layout.addWidget(history_widget)
        
        widget.setLayout(layout)
        return widget
    
    def create_promotion_item(self, line):
        
        try:
            parts = line.split(' ', 2)  
            if len(parts) >= 3:
                name, url, description = parts[0], parts[1], parts[2]
                
                
                item_widget = QWidget()
                item_widget.setMinimumHeight(70)  
                item_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                item_widget.setStyleSheet("""
                    QWidget {
                        background-color: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        margin: 3px;
                    }
                    QWidget:hover {
                        background-color: #e3f2fd;
                        border-color: #4a90e2;
                    }
                """)
                
                layout = QVBoxLayout()
                layout.setSpacing(8)
                layout.setContentsMargins(15, 12, 15, 12)
                
                
                header_layout = QHBoxLayout()
                header_layout.setSpacing(12)
                
                
                name_label = QLabel(name)
                name_label.setFont(QFont(get_system_font(), 10, QFont.Bold))
                name_label.setWordWrap(True)  
                name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                name_label.setStyleSheet("""
                    QLabel {
                        color: #2c3e50;
                        background: transparent;
                        border: none;
                        padding: 4px 0px;
                        line-height: 1.3;
                    }
                """)
                header_layout.addWidget(name_label)
                
                header_layout.addStretch()
                
                
                link_btn = QPushButton("访问")
                link_btn.setFont(QFont(get_system_font(), 9))
                link_btn.setFixedSize(55, 30)  
                link_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                link_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: 6px 10px;
                        font-weight: 600;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #357abd;
                    }
                    QPushButton:pressed {
                        background-color: #2c5aa0;
                    }
                """)
                link_btn.clicked.connect(lambda: self.open_url(url))
                header_layout.addWidget(link_btn)
                
                layout.addLayout(header_layout)
                
                
                if description:
                    desc_label = QLabel(description)
                    desc_label.setFont(QFont(get_system_font(), 9))
                    desc_label.setWordWrap(True)
                    desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                    desc_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                    desc_label.setMinimumHeight(20)  
                    desc_label.setStyleSheet("""
                        QLabel {
                            color: #6c757d;
                            background: transparent;
                            border: none;
                            padding: 4px 0px 2px 0px;
                            line-height: 1.5;
                        }
                    """)
                    layout.addWidget(desc_label)
                
                item_widget.setLayout(layout)
                return item_widget
            else:
                
                error_widget = QWidget()
                error_widget.setMinimumHeight(40)
                error_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                error_widget.setStyleSheet("""
                    QWidget {
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 6px;
                        margin: 3px;
                    }
                """)
                layout = QVBoxLayout()
                layout.setContentsMargins(12, 10, 12, 10)
                
                error_label = QLabel(f"格式错误: {line}")
                error_label.setFont(QFont(get_system_font(), 9))
                error_label.setStyleSheet("""
                    QLabel {
                        color: #856404;
                        background: transparent;
                        border: none;
                    }
                """)
                layout.addWidget(error_label)
                error_widget.setLayout(layout)
                return error_widget
                
        except Exception as e:
            return None
    
    def open_url(self, url):
        
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"打开链接失败: {e}")
    
    def toggle_ads(self):
        
        self.ads_enabled = not self.ads_enabled
        self.save_ads_config()
        
        
        self.ads_toggle_btn.setText("关闭推广" if self.ads_enabled else "开启推广")
        self.ads_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #a71e2a;
            }
        
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        
        
        self.setup_content()

class MainWindow(QMainWindow):
    
    
    def __init__(self):
        super().__init__()
        self.tool_pages = {}
        self.promotion_page = PromotionPage()
        self.setup_ui()
        self.init_tools()
    
    def setup_ui(self):
        self.setWindowTitle("白猫工具箱-v0.0.1_beta")
        self.setGeometry(100, 100, 1400, 900)
        
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                color: #212529;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
        """)
        
        
        central_widget = QWidget()
        central_widget.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.setCentralWidget(central_widget)
        
        
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setStyleSheet("""
            QSplitter {
                background: transparent;
            }
            QSplitter::handle {
                background-color: #dee2e6;
                width: 3px;
                margin: 4px 0;
                border-radius: 1px;
            }
            QSplitter::handle:hover {
                background-color: #4a90e2;
            }
        """)
        
        
        left_widget = self.create_tool_list()
        main_splitter.addWidget(left_widget)
        
        
        self.right_stack = QTabWidget()
        self.right_stack.setTabsClosable(False)
        self.right_stack.tabBar().hide()  
        self.right_stack.setStyleSheet("""
            QTabWidget {
                background: transparent;
            }
            QTabWidget::pane {
                background: transparent;
                border: none;
            }
        """)
        
        
        self.right_stack.addTab(self.promotion_page, "推广")
        
        main_splitter.addWidget(self.right_stack)
        
        
        main_splitter.setSizes([280, 1120])
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        layout.addWidget(main_splitter)
        central_widget.setLayout(layout)
    
    def create_tool_list(self):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(8, 8, 8, 8)
        
        
        title_button_layout = QHBoxLayout()
        
        title_label = QLabel("工具列表")
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
                padding: 4px 8px;
            }
        """)
        title_button_layout.addWidget(title_label)
        
        
        home_btn = QPushButton("🏠")
        home_btn.setFont(QFont("Microsoft YaHei", 10))
        home_btn.setToolTip("返回推广页面")
        home_btn.setFixedSize(30, 30)
        home_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2c5aa0;
            }
        """)
        home_btn.clicked.connect(self.clear_selection)
        title_button_layout.addWidget(home_btn)
        
        
        backup_btn = QPushButton("💾")
        backup_btn.setFont(QFont("Microsoft YaHei", 10))
        backup_btn.setToolTip("备份配置")
        backup_btn.setFixedSize(30, 30)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        backup_btn.clicked.connect(self.backup_config)
        title_button_layout.addWidget(backup_btn)
        
        title_layout.addLayout(title_button_layout)
        title_widget.setLayout(title_layout)
        layout.addWidget(title_widget)
        
        
        list_widget = QWidget()
        list_widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(8, 8, 8, 8)
        
        self.tool_list = QListWidget()
        self.tool_list.currentRowChanged.connect(self.on_tool_selected)
        
        self.tool_list.setSelectionMode(QListWidget.SingleSelection)
        
        self.tool_list.itemClicked.connect(self.on_item_clicked)
        
        self.tool_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tool_list.customContextMenuRequested.connect(self.show_tool_list_context_menu)
        self.tool_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 12px 16px;
                margin: 2px 0px;
                color: #495057;
                font-weight: 500;
                font-size: 9pt;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
                border-color: #4a90e2;
                color: #2c5aa0;
            }
            QListWidget::item:selected {
                background-color: #4a90e2;
                border-color: #4a90e2;
                color: white;
                font-weight: 600;
            }
        """)
        list_layout.addWidget(self.tool_list)
        list_widget.setLayout(list_layout)
        layout.addWidget(list_widget)
        
        widget.setLayout(layout)
        return widget
    
    def init_tools(self):
        
        tools_dir = "tools"
        tools = []
        
        
        if os.path.exists(tools_dir):
            for item in os.listdir(tools_dir):
                item_path = os.path.join(tools_dir, item)
                if os.path.isdir(item_path):
                    
                    config_path = os.path.join(item_path, "wct_config.txt")
                    if os.path.exists(config_path):
                        tools.append(item)

        for tool in tools:
            self.tool_list.addItem(tool)
            
            tool_page = ToolOperationPage(tool)
            self.tool_pages[tool] = tool_page
            self.right_stack.addTab(tool_page, "")
        
        
        self.right_stack.setCurrentIndex(0)
        self.tool_list.setCurrentRow(-1)
    
    def on_tool_selected(self, row):
        
        if row >= 0:
            tool_name = self.tool_list.item(row).text()
            if tool_name in self.tool_pages:
                
                page_index = list(self.tool_pages.keys()).index(tool_name) + 1
                self.right_stack.setCurrentIndex(page_index)
        else:
            
            self.right_stack.setCurrentIndex(0)
    
    def on_item_clicked(self, item):
        
        
        
        pass
    
    def clear_selection(self):
        
        self.tool_list.clearSelection()
        self.tool_list.setCurrentRow(-1)
        self.right_stack.setCurrentIndex(0)
    
    def show_tool_list_context_menu(self, position):
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 4px;
                color: #495057;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        
        
        show_ads_action = menu.addAction("🏠 返回推广页面")
        show_ads_action.triggered.connect(self.clear_selection)
        
        
        menu.addSeparator()
        backup_action = menu.addAction("💾 备份配置")
        backup_action.triggered.connect(self.backup_config)
        
        restore_action = menu.addAction("📁 恢复配置")
        restore_action.triggered.connect(self.restore_config)
        
        
        current_item = self.tool_list.currentItem()
        if current_item:
            menu.addSeparator()
            open_tool_action = menu.addAction(f"🔧 打开 {current_item.text()}")
            open_tool_action.triggered.connect(lambda: self.on_tool_selected(self.tool_list.currentRow()))
            
            
            open_folder_action = menu.addAction(f"📂 打开 {current_item.text()} 文件夹")
            open_folder_action.triggered.connect(lambda: self.open_tool_folder(current_item.text()))
        
        menu.exec(self.tool_list.mapToGlobal(position))

    def open_tool_folder(self, tool_name):
        
        try:
            tool_path = os.path.join("tools", tool_name)
            if os.path.exists(tool_path):
                
                abs_tool_path = os.path.abspath(tool_path)
                
                
                if platform.system() == "Windows":
                    
                    subprocess.run(["explorer", abs_tool_path], check=True)
                elif platform.system() == "Darwin":
                    
                    subprocess.run(["open", abs_tool_path], check=True)
                else:
                    
                    subprocess.run(["xdg-open", abs_tool_path], check=True)
            else:
                self.show_error_message("文件夹不存在", f"工具文件夹不存在：\n{tool_path}")
        except subprocess.CalledProcessError:
            self.show_error_message("打开失败", f"无法打开工具文件夹：\n{tool_path}")
        except Exception as e:
            self.show_error_message("打开失败", f"打开工具文件夹时发生错误：\n{str(e)}")

    def backup_config(self):
        
        try:
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"白猫工具箱配置备份_{timestamp}.zip"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "备份配置文件",
                default_filename,
                "ZIP文件 (*.zip)"
            )
            
            if not file_path:
                return
            
            
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                
                
                templates_dir = "templates"
                if os.path.exists(templates_dir):
                    for root, dirs, files in os.walk(templates_dir):
                        for file in files:
                            file_path_full = os.path.join(root, file)
                            arcname = os.path.relpath(file_path_full, ".")
                            backup_zip.write(file_path_full, arcname)
                
                
                promotion_dir = "promotion"
                if os.path.exists(promotion_dir):
                    for root, dirs, files in os.walk(promotion_dir):
                        for file in files:
                            file_path_full = os.path.join(root, file)
                            arcname = os.path.relpath(file_path_full, ".")
                            backup_zip.write(file_path_full, arcname)
                
                
                if os.path.exists("promotion_config.json"):
                    backup_zip.write("promotion_config.json", "promotion_config.json")
                
                
                if os.path.exists("command_history.json"):
                    backup_zip.write("command_history.json", "command_history.json")
                
                
                tools_dir = "tools"
                if os.path.exists(tools_dir):
                    for tool_name in os.listdir(tools_dir):
                        tool_path = os.path.join(tools_dir, tool_name)
                        if os.path.isdir(tool_path):
                            config_file = os.path.join(tool_path, "wct_config.txt")
                            if os.path.exists(config_file):
                                arcname = os.path.relpath(config_file, ".")
                                backup_zip.write(config_file, arcname)
                            
                            
                            custom_cmd_file = os.path.join(tool_path, "custom_command.txt")
                            if os.path.exists(custom_cmd_file):
                                arcname = os.path.relpath(custom_cmd_file, ".")
                                backup_zip.write(custom_cmd_file, arcname)
                
                
                if os.path.exists("help.txt"):
                    backup_zip.write("help.txt", "help.txt")
                
                
                backup_info = {
                    "backup_time": datetime.datetime.now().isoformat(),
                    "version": "v0.0.1_beta",
                    "description": "白猫工具箱配置备份文件",
                    "includes": [
                        "templates/",
                        "promotion/",
                        "promotion_config.json",
                        "command_history.json", 
                        "tools/*/wct_config.txt",
                        "tools/*/custom_command.txt",
                        "help.txt"
                    ]
                }
                
                backup_zip.writestr("backup_info.json", json.dumps(backup_info, ensure_ascii=False, indent=2))
            
            self.show_success_message("备份成功", f"配置已成功备份到：\n{file_path}")
            
        except Exception as e:
            self.show_error_message("备份失败", f"备份过程中发生错误：\n{str(e)}")

    def restore_config(self):
        
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择配置备份文件",
                "",
                "ZIP文件 (*.zip)"
            )
            
            if not file_path:
                return
            
            
            try:
                with zipfile.ZipFile(file_path, 'r') as backup_zip:
                    file_list = backup_zip.namelist()
                    
                    
                    if "backup_info.json" in file_list:
                        backup_info_data = backup_zip.read("backup_info.json")
                        backup_info = json.loads(backup_info_data.decode('utf-8'))
                        
                        
                        info_text = f"备份时间: {backup_info.get('backup_time', '未知')}\n"
                        info_text += f"版本: {backup_info.get('version', '未知')}\n"
                        info_text += f"描述: {backup_info.get('description', '无')}\n\n"
                        info_text += "包含的内容:\n"
                        for item in backup_info.get('includes', []):
                            info_text += f"- {item}\n"
                        
                        reply = QMessageBox.question(
                            self,
                            "确认恢复配置",
                            f"即将恢复以下配置：\n\n{info_text}\n是否继续？",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        
                        if reply != QMessageBox.Yes:
                            return
                    else:
                        reply = QMessageBox.question(
                            self,
                            "确认恢复配置", 
                            "这个备份文件可能不是白猫工具箱的配置备份，是否继续恢复？",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        
                        if reply != QMessageBox.Yes:
                            return
            
            except zipfile.BadZipFile:
                self.show_error_message("文件错误", "选择的文件不是有效的ZIP文件")
                return
            
            
            with zipfile.ZipFile(file_path, 'r') as backup_zip:
                extracted_files = []
                backup_files = []
                
                for file_info in backup_zip.infolist():
                    
                    if file_info.is_dir() or file_info.filename == "backup_info.json":
                        continue
                    
                    
                    target_path = file_info.filename
                    target_dir = os.path.dirname(target_path)
                    
                    if target_dir and not os.path.exists(target_dir):
                        os.makedirs(target_dir, exist_ok=True)
                    
                    
                    if os.path.exists(target_path):
                        backup_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = f"{target_path}.restore_backup_{backup_timestamp}"
                        shutil.copy2(target_path, backup_path)
                        backup_files.append(backup_path)
                    
                    
                    backup_zip.extract(file_info, ".")
                    extracted_files.append(target_path)
                
                success_text = "配置恢复成功！\n\n"
                success_text += f"✅ 已恢复 {len(extracted_files)} 个文件：\n"
                for file in extracted_files[:8]:  
                    success_text += f"- {file}\n"
                
                if len(extracted_files) > 8:
                    success_text += f"... 以及其他 {len(extracted_files) - 8} 个文件\n"
                
                if backup_files:
                    success_text += f"\n💾 已备份 {len(backup_files)} 个原文件：\n"
                    for backup_file in backup_files[:5]:  
                        original_name = backup_file.split('.restore_backup_')[0]
                        success_text += f"- {original_name} → {os.path.basename(backup_file)}\n"
                    
                    if len(backup_files) > 5:
                        success_text += f"... 以及其他 {len(backup_files) - 5} 个备份文件\n"
                
                self.show_success_message("恢复成功", success_text)
                
        except Exception as e:
            self.show_error_message("恢复失败", f"恢复过程中发生错误：\n{str(e)}")

    def show_success_message(self, title, message):
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

    def show_error_message(self, title, message):
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

def get_cross_platform_app_stylesheet():
    
    system_font = get_system_font()
    mono_font = get_monospace_font()
    
    return f"""
        /* 修复QMessageBox黑框问题 */
        QMessageBox {{
            background-color: #ffffff;
            border: 1px solid #e5e5ea;
            border-radius: 12px;
            font-family: '{system_font}', Arial, sans-serif;
            color: #1d1d1f;
        }}
        QMessageBox QLabel {{
            background-color: transparent;
            color: #1d1d1f;
            font-size: 13pt;
            padding: 16px;
            border: none;
        }}
        QMessageBox QPushButton {{
            background-color: #007AFF;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            color: white;
            font-weight: 500;
            font-size: 13pt;
            min-width: 80px;
            min-height: 32px;
            margin: 4px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: #0056CC;
        }}
        QMessageBox QPushButton:pressed {{
            background-color: #004499;
        }}
        QMessageBox QPushButton[text="取消"], 
        QMessageBox QPushButton[text="Cancel"],
        QMessageBox QPushButton[text="No"] {{
            background-color: #f2f2f7;
            color: #007AFF;
            border: 1px solid #d1d1d6;
        }}
        QMessageBox QPushButton[text="取消"]:hover,
        QMessageBox QPushButton[text="Cancel"]:hover,
        QMessageBox QPushButton[text="No"]:hover {{
            background-color: #e5e5ea;
            border-color: #007AFF;
        }}
        
        /* 修复QInputDialog黑框问题 */
        QInputDialog {{
            background-color: #ffffff;
            border: 1px solid #e5e5ea;
            border-radius: 12px;
            font-family: '{system_font}', Arial, sans-serif;
            color: #1d1d1f;
        }}
        QInputDialog QLabel {{
            background-color: transparent;
            color: #1d1d1f;
            font-size: 13pt;
            padding: 16px 16px 8px 16px;
            border: none;
        }}
        QInputDialog QLineEdit {{
            background-color: #f2f2f7;
            border: 1px solid #d1d1d6;
            border-radius: 8px;
            padding: 8px 12px;
            color: #1d1d1f;
            font-size: 13pt;
            margin: 8px 16px;
            selection-background-color: #007AFF;
        }}
        QInputDialog QLineEdit:focus {{
            border-color: #007AFF;
            background-color: #ffffff;
        }}
        QInputDialog QPushButton {{
            background-color: #007AFF;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            color: white;
            font-weight: 500;
            font-size: 13pt;
            min-width: 80px;
            min-height: 32px;
            margin: 4px;
        }}
        QInputDialog QPushButton:hover {{
            background-color: #0056CC;
        }}
        QInputDialog QPushButton:pressed {{
            background-color: #004499;
        }}
        QInputDialog QPushButton[text="取消"],
        QInputDialog QPushButton[text="Cancel"] {{
            background-color: #f2f2f7;
            color: #007AFF;
            border: 1px solid #d1d1d6;
        }}
        QInputDialog QPushButton[text="取消"]:hover,
        QInputDialog QPushButton[text="Cancel"]:hover {{
            background-color: #e5e5ea;
            border-color: #007AFF;
        }}
        
        /* 修复QFileDialog黑框问题 */
        QFileDialog {{
            background-color: #ffffff;
            color: #1d1d1f;
            font-family: '{system_font}', Arial, sans-serif;
        }}
        QFileDialog QListView {{
            background-color: #ffffff;
            border: 1px solid #e5e5ea;
            border-radius: 6px;
            color: #1d1d1f;
        }}
        QFileDialog QTreeView {{
            background-color: #ffffff;
            border: 1px solid #e5e5ea;
            border-radius: 6px;
            color: #1d1d1f;
        }}
        QFileDialog QPushButton {{
            background-color: #007AFF;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            color: white;
            font-weight: 500;
            min-height: 28px;
        }}
        QFileDialog QPushButton:hover {{
            background-color: #0056CC;
        }}
        QFileDialog QPushButton[text="取消"],
        QFileDialog QPushButton[text="Cancel"] {{
            background-color: #f2f2f7;
            color: #007AFF;
            border: 1px solid #d1d1d6;
        }}
        
        /* 垂直滚动条样式 */
        QScrollBar:vertical {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 #f8f9fa, stop: 1 #e9ecef);
            width: 12px;
            border-radius: 6px;
            margin: 2px;
            border: 1px solid #e9ecef;
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 #ced4da, stop: 1 #adb5bd);
            border-radius: 5px;
            min-height: 30px;
            margin: 1px;
            border: 1px solid #adb5bd;
        }}
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 #4a90e2, stop: 1 #357abd);
            border-color: #357abd;
        }}
        QScrollBar::handle:vertical:pressed {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 #2c5aa0, stop: 1 #1e3a5f);
            border-color: #1e3a5f;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}
        
        /* 水平滚动条样式 */
        QScrollBar:horizontal {{
            height: 0px;
            background: transparent;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: transparent;
            border: none;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
            height: 0;
            background: none;
        }}
        
        /* 滚动区域样式 */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        
        /* 工具提示样式 */
        QToolTip {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #ffffff, stop: 1 #f8f9fa);
            color: #2c3e50;
            border: 2px solid #4a90e2;
            border-radius: 8px;
            padding: 6px 10px;
            font-size: 9pt;
            font-family: '{system_font}', Arial, sans-serif;
            font-weight: 500;
            line-height: 1.2;
            max-width: 300px;
        }}
    """

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  
    
    
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    app.setStyleSheet(get_cross_platform_app_stylesheet())
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()