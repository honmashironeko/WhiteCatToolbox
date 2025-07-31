from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPalette, QColor
import json
from pathlib import Path
from .utils import get_project_root

class ThemeManager(QObject):
    theme_changed = Signal(str)
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self.current_theme = "blue_white"
        self.themes = {
            "blue_white": self._get_blue_white_theme(),
            "dark": self._get_dark_theme(),
            "light": self._get_light_theme()
        }
        
    def _get_blue_white_theme(self):
        return {
            "name": "蓝白主题",
            "colors": {
                "primary": "#2196F3",
                "primary_dark": "#1976D2",
                "primary_light": "#BBDEFB",
                "secondary": "#FFFFFF",
                "background": "#FAFAFA",
                "surface": "#FFFFFF",
                "text_primary": "#212121",
                "text_secondary": "#757575",
                "border": "#E0E0E0",
                "hover": "#E3F2FD",
                "selected": "#2196F3",
                "disabled": "#BDBDBD",
                "error": "#e74c3c",
                "warning": "#f39c12",
                "success": "#27ae60",
                "info": "#3498db",
                "highlight": "#ffff00",
                "highlight_current": "#ffa500",
                "terminal_bg": "#1e1e1e",
                "terminal_text": "#ffffff",
                "terminal_error": "#ff6b6b",
                "terminal_success": "#51cf66",
                "terminal_warning": "#ffd43b",
                "terminal_command": "#00ff00"
            },
            "stylesheet": self._get_blue_white_stylesheet()
        }
    
    def _get_dark_theme(self):
        return {
            "name": "深色主题",
            "colors": {
                "primary": "#2196F3",
                "primary_dark": "#1976D2",
                "primary_light": "#64B5F6",
                "secondary": "#424242",
                "background": "#303030",
                "surface": "#424242",
                "text_primary": "#FFFFFF",
                "text_secondary": "#BDBDBD",
                "border": "#616161",
                "hover": "#484848",
                "selected": "#2196F3",
                "disabled": "#757575",
                "error": "#ff6b6b",
                "warning": "#ffd43b",
                "success": "#51cf66",
                "info": "#64b5f6",
                "highlight": "#ffff00",
                "highlight_current": "#ffa500",
                "terminal_bg": "#1e1e1e",
                "terminal_text": "#ffffff",
                "terminal_error": "#ff6b6b",
                "terminal_success": "#51cf66",
                "terminal_warning": "#ffd43b",
                "terminal_command": "#00ff00"
            },
            "stylesheet": self._get_dark_stylesheet()
        }
    
    def _get_light_theme(self):
        return {
            "name": "浅色主题",
            "colors": {
                "primary": "#1976D2",
                "primary_dark": "#0D47A1",
                "primary_light": "#BBDEFB",
                "secondary": "#F5F5F5",
                "background": "#FFFFFF",
                "surface": "#FFFFFF",
                "text_primary": "#212121",
                "text_secondary": "#757575",
                "border": "#E0E0E0",
                "hover": "#F5F5F5",
                "selected": "#1976D2",
                "disabled": "#BDBDBD",
                "error": "#dc3545",
                "warning": "#ffc107",
                "success": "#28a745",
                "info": "#17a2b8",
                "highlight": "#ffff00",
                "highlight_current": "#ffa500",
                "terminal_bg": "#1e1e1e",
                "terminal_text": "#ffffff",
                "terminal_error": "#ff6b6b",
                "terminal_success": "#51cf66",
                "terminal_warning": "#ffd43b",
                "terminal_command": "#00ff00"
            },
            "stylesheet": self._get_light_stylesheet()
        }
    
    def _get_blue_white_stylesheet(self):
        return """
        QMainWindow {
            background-color: #FAFAFA;
            color: #212121;
        }
        
        QMenu {
            background-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            padding: 4px;
        }
        
        QMenu::item {
            padding: 6px 12px;
            border-radius: 4px;
        }
        
        QMenu::item:selected {
            background-color: #E3F2FD;
            color: #1976D2;
        }
        
        QTabWidget::pane {
            border: 1px solid #E0E0E0;
            background-color: white;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #F5F5F5;
            color: #757575;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #2196F3;
            color: white;
        }
        
        QTabBar::tab:hover {
            background-color: #E3F2FD;
            color: #1976D2;
        }
        
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #1976D2;
        }
        
        QPushButton:pressed {
            background-color: #0D47A1;
        }
        
        QPushButton:disabled {
            background-color: #BDBDBD;
            color: #757575;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: white;
            border: 2px solid #E0E0E0;
            border-radius: 4px;
            padding: 6px;
            color: #212121;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #2196F3;
        }
        
        QComboBox {
            background-color: white;
            border: 2px solid #E0E0E0;
            border-radius: 4px;
            padding: 6px;
            color: #212121;
        }
        
        QComboBox:focus {
            border-color: #2196F3;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #757575;
        }
        
        QCheckBox {
            color: #212121;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #E0E0E0;
            border-radius: 3px;
            background-color: white;
        }
        
        QCheckBox::indicator:checked {
            background-color: #2196F3;
            border-color: #2196F3;
        }
        
        QCheckBox::indicator:checked::after {
            content: "✓";
            color: white;
            font-weight: bold;
        }
        
        QScrollBar:vertical {
            background-color: #F5F5F5;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #BDBDBD;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #9E9E9E;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #F5F5F5;
            height: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #BDBDBD;
            border-radius: 6px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #9E9E9E;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        QSplitter::handle {
            background-color: #E0E0E0;
        }
        
        QSplitter::handle:hover {
            background-color: #BDBDBD;
        }
        
        QStatusBar {
            background-color: #F5F5F5;
            border-top: 1px solid #E0E0E0;
            color: #757575;
        }
        
        QProgressBar {
            border: 2px solid #E0E0E0;
            border-radius: 4px;
            background-color: #F5F5F5;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #2196F3;
            border-radius: 2px;
        }
        
        QTreeWidget, QListWidget {
            background-color: white;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
            alternate-background-color: #FAFAFA;
        }
        
        QTreeWidget::item:selected, QListWidget::item:selected {
            background-color: #E3F2FD;
            color: #1976D2;
        }
        
        QTreeWidget::item:hover, QListWidget::item:hover {
            background-color: #F5F5F5;
        }
        
        QHeaderView::section {
            background-color: #F5F5F5;
            border: 1px solid #E0E0E0;
            padding: 6px;
            color: #757575;
            font-weight: bold;
        }
        """
    
    def _get_dark_stylesheet(self):
        return """
        QMainWindow {
            background-color: #303030;
            color: #FFFFFF;
        }
        
        QTabWidget::pane {
            border: 1px solid #616161;
            background-color: #424242;
            border-radius: 4px;
        }
        
        QTabBar::tab {
            background-color: #616161;
            color: #BDBDBD;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #2196F3;
            color: white;
        }
        
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #1976D2;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #424242;
            border: 2px solid #616161;
            border-radius: 4px;
            padding: 6px;
            color: #FFFFFF;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border-color: #2196F3;
        }
        """
    
    def _get_light_stylesheet(self):
        return """
        QMainWindow {
            background-color: #FFFFFF;
            color: #212121;
        }
        
        QPushButton {
            background-color: #1976D2;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #0D47A1;
        }
        """
    
    def get_current_theme(self):
        return self.themes.get(self.current_theme, self.themes["blue_white"])
    
    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.apply_theme()
            self.theme_changed.emit(theme_name)
            
            if self.config_manager:
                self.config_manager.app_config["ui_settings"]["theme"] = theme_name
                self.config_manager.save_app_config()
    
    def apply_theme(self):
        """应用主题"""
        app = QApplication.instance()
        if app:

            theme_file = self.get_theme_css_file()
            if theme_file and theme_file.exists():
                with open(theme_file, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                app.setStyleSheet(css_content)
            else:

                theme = self.get_current_theme()
                app.setStyleSheet(theme["stylesheet"])
    
    def get_theme_css_file(self):
        """获取当前主题的CSS文件路径"""
        # 修复PyInstaller路径问题
        project_root = get_project_root()
        theme_dir = project_root / "assets" / "themes"
        theme_file = theme_dir / f"{self.current_theme}.css"
        return theme_file
    
    def get_theme_color(self, color_name):
        theme = self.get_current_theme()
        return theme["colors"].get(color_name, "#000000")
    
    def get_available_themes(self):
        return [(name, theme["name"]) for name, theme in self.themes.items()]
    
    def load_theme_from_config(self):
        if self.config_manager:
            theme_name = self.config_manager.app_config.get("ui_settings", {}).get("theme", "blue_white")
            self.current_theme = theme_name if theme_name in self.themes else "blue_white"
            self.apply_theme()