from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QPushButton, QSpinBox, QGroupBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QKeySequence, QShortcut
import json

class FontScaleWidget(QWidget):
    scale_changed = Signal(float)
    
    def __init__(self, config_manager=None, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.current_scale = 1.0
        self.min_scale = 0.8
        self.max_scale = 3.0
        self.default_scale = 1.0
        
        self.init_ui()
        self.setup_shortcuts()
        self.load_scale_from_config()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        group_box = QGroupBox("字体缩放")
        group_layout = QVBoxLayout(group_box)
        
        info_layout = QHBoxLayout()
        self.scale_label = QLabel(f"当前缩放: {int(self.current_scale * 100)}%")
        info_layout.addWidget(self.scale_label)
        info_layout.addStretch()
        
        range_label = QLabel(f"范围: {int(self.min_scale * 100)}% - {int(self.max_scale * 100)}%")
        info_layout.addWidget(range_label)
        group_layout.addLayout(info_layout)
        
        slider_layout = QHBoxLayout()
        
        min_label = QLabel(f"{int(self.min_scale * 100)}%")
        slider_layout.addWidget(min_label)
        
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(int(self.min_scale * 100))
        self.scale_slider.setMaximum(int(self.max_scale * 100))
        self.scale_slider.setValue(int(self.current_scale * 100))
        self.scale_slider.setTickPosition(QSlider.TicksBelow)
        self.scale_slider.setTickInterval(20)
        self.scale_slider.valueChanged.connect(self.on_slider_changed)
        slider_layout.addWidget(self.scale_slider)
        
        max_label = QLabel(f"{int(self.max_scale * 100)}%")
        slider_layout.addWidget(max_label)
        
        group_layout.addLayout(slider_layout)
        
        spinbox_layout = QHBoxLayout()
        spinbox_layout.addWidget(QLabel("精确值:"))
        
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setMinimum(int(self.min_scale * 100))
        self.scale_spinbox.setMaximum(int(self.max_scale * 100))
        self.scale_spinbox.setValue(int(self.current_scale * 100))
        self.scale_spinbox.setSuffix("%")
        self.scale_spinbox.valueChanged.connect(self.on_spinbox_changed)
        spinbox_layout.addWidget(self.scale_spinbox)
        
        spinbox_layout.addStretch()
        group_layout.addLayout(spinbox_layout)
        
        button_layout = QHBoxLayout()
        
        self.decrease_btn = QPushButton("缩小 (Ctrl+-)")
        self.decrease_btn.clicked.connect(self.decrease_scale)
        button_layout.addWidget(self.decrease_btn)
        
        self.reset_btn = QPushButton("重置 (Ctrl+0)")
        self.reset_btn.clicked.connect(self.reset_scale)
        button_layout.addWidget(self.reset_btn)
        
        self.increase_btn = QPushButton("放大 (Ctrl++)")
        self.increase_btn.clicked.connect(self.increase_scale)
        button_layout.addWidget(self.increase_btn)
        
        group_layout.addLayout(button_layout)
        
        shortcut_label = QLabel("快捷键: Ctrl+Plus(放大), Ctrl+Minus(缩小), Ctrl+0(重置)")
        shortcut_label.setProperty("class", "shortcut_hint")
        group_layout.addWidget(shortcut_label)
        
        layout.addWidget(group_box)
        layout.addStretch()
        
    def setup_shortcuts(self):
        self.increase_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        self.increase_shortcut.activated.connect(self.increase_scale)
        
        self.increase_shortcut2 = QShortcut(QKeySequence("Ctrl+="), self)
        self.increase_shortcut2.activated.connect(self.increase_scale)
        
        self.decrease_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.decrease_shortcut.activated.connect(self.decrease_scale)
        
        self.reset_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        self.reset_shortcut.activated.connect(self.reset_scale)
        
    def on_slider_changed(self, value):
        new_scale = value / 100.0
        self.set_scale(new_scale, update_slider=False)
        
    def on_spinbox_changed(self, value):
        new_scale = value / 100.0
        self.set_scale(new_scale, update_spinbox=False)
        
    def set_scale(self, scale, update_slider=True, update_spinbox=True):
        scale = max(self.min_scale, min(self.max_scale, scale))
        
        if abs(scale - self.current_scale) < 0.01:
            return
        

        if scale == 1.0:
            self.reset_all_font_attributes()
            
        self.current_scale = scale
        
        if update_slider:
            self.scale_slider.setValue(int(scale * 100))
        if update_spinbox:
            self.scale_spinbox.setValue(int(scale * 100))
            
        self.scale_label.setText(f"当前缩放: {int(scale * 100)}%")
        
        self.apply_scale()
        self.save_scale_to_config()
        self.scale_changed.emit(scale)
    
    def reset_all_font_attributes(self):
        """重置所有组件的字体属性标记"""
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if widget and hasattr(widget, '_original_font_size'):
                    try:
                        delattr(widget, '_original_font_size')
                    except Exception:
                        pass
        
    def apply_scale(self):
        app = QApplication.instance()
        if app:
            from .utils import get_system_font
            

            system_font = get_system_font()
            base_size = system_font.pointSize() if system_font.pointSize() > 0 else 9
            

            new_size = max(6, int(base_size * self.current_scale))
            scaled_font = QFont(system_font)
            scaled_font.setPointSize(new_size)
            app.setFont(scaled_font)
            

            self._apply_scale_to_widgets(app.allWidgets(), base_size)
    
    def _apply_scale_to_widgets(self, widgets, base_size):
        """递归应用字体缩放到所有组件"""
        from .utils import get_system_font
        from PySide6.QtWidgets import QTabBar, QTabWidget
        system_font = get_system_font()
        
        for widget in widgets:
            if widget and hasattr(widget, 'font'):
                try:

                    if self.current_scale == 1.0:
                        if hasattr(widget, '_original_font_size'):
                            delattr(widget, '_original_font_size')
                    

                    if not hasattr(widget, '_original_font_size'):

                        widget._original_font_size = system_font.pointSize() if system_font.pointSize() > 0 else base_size
                    

                    original_size = widget._original_font_size
                    new_size = max(6, int(original_size * self.current_scale))
                    

                    new_font = QFont(system_font)
                    new_font.setPointSize(new_size)
                    

                    current_font = widget.font()
                    new_font.setBold(current_font.bold())
                    new_font.setItalic(current_font.italic())
                    new_font.setUnderline(current_font.underline())
                    
                    widget.setFont(new_font)
                    

                    if isinstance(widget, (QTabBar, QTabWidget)):

                        widget.setStyleSheet(widget.styleSheet())
                    elif hasattr(widget, 'setStyleSheet') and 'QTextEdit' in str(type(widget)):

                        widget.setStyleSheet(widget.styleSheet())

                        if hasattr(widget, 'document') and widget.document():
                            widget.document().setModified(True)
                            widget.viewport().update()
                    

                    widget.update()
                    widget.repaint()
                    

                    if hasattr(widget, 'children'):
                        self._apply_scale_to_widgets(widget.children(), base_size)
                    
                except Exception:
                    pass
                        
    def increase_scale(self):
        new_scale = min(self.max_scale, self.current_scale + 0.1)
        self.set_scale(new_scale)
        
    def decrease_scale(self):
        new_scale = max(self.min_scale, self.current_scale - 0.1)
        self.set_scale(new_scale)
        
    def reset_scale(self):
        self.set_scale(self.default_scale)
        
    def get_current_scale(self):
        return self.current_scale
        
    def save_scale_to_config(self):
        if self.config_manager:
            if "ui_settings" not in self.config_manager.app_config:
                self.config_manager.app_config["ui_settings"] = {}
            self.config_manager.app_config["ui_settings"]["font_scale"] = self.current_scale
            self.config_manager.save_app_config()
            
    def load_scale_from_config(self):
        if self.config_manager:
            scale = self.config_manager.app_config.get("ui_settings", {}).get("font_scale", self.default_scale)
            self.set_scale(scale)
            
class GlobalFontScaleManager:
    _instance = None
    
    def __new__(cls, config_manager=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config_manager = config_manager
            cls._instance.current_scale = 1.0
            cls._instance.min_scale = 0.8
            cls._instance.max_scale = 3.0
            cls._instance.default_scale = 1.0
            cls._instance._initialized = False
        return cls._instance
    
    def initialize(self):
        if not self._initialized:
            self.load_scale_from_config()
            self.apply_scale()
            self._initialized = True
    
    def set_scale(self, scale):
        scale = max(self.min_scale, min(self.max_scale, scale))
        

        if scale == 1.0:
            self.reset_all_font_attributes()
            
        self.current_scale = scale
        self.apply_scale()
        self.save_scale_to_config()
    
    def reset_all_font_attributes(self):
        """重置所有组件的字体属性标记"""
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if widget and hasattr(widget, '_original_font_size'):
                    try:
                        delattr(widget, '_original_font_size')
                    except Exception:
                        pass
    
    def apply_scale(self):
        app = QApplication.instance()
        if app:
            from .utils import get_system_font
            

            system_font = get_system_font()
            base_size = system_font.pointSize() if system_font.pointSize() > 0 else 9
            

            new_size = max(6, int(base_size * self.current_scale))
            scaled_font = QFont(system_font)
            scaled_font.setPointSize(new_size)
            app.setFont(scaled_font)
            

            self._apply_scale_to_widgets(app.allWidgets(), base_size)
    
    def _apply_scale_to_widgets(self, widgets, base_size):
         """递归应用字体缩放到所有组件"""
         from .utils import get_system_font
         from PySide6.QtWidgets import QTabBar, QTabWidget
         system_font = get_system_font()
         
         for widget in widgets:
             if widget and hasattr(widget, 'font'):
                 try:

                     if self.current_scale == 1.0:
                         if hasattr(widget, '_original_font_size'):
                             delattr(widget, '_original_font_size')
                     

                     if not hasattr(widget, '_original_font_size'):

                         widget._original_font_size = system_font.pointSize() if system_font.pointSize() > 0 else base_size
                     

                     original_size = widget._original_font_size
                     new_size = max(6, int(original_size * self.current_scale))
                     

                     new_font = QFont(system_font)
                     new_font.setPointSize(new_size)
                     

                     current_font = widget.font()
                     new_font.setBold(current_font.bold())
                     new_font.setItalic(current_font.italic())
                     new_font.setUnderline(current_font.underline())
                     
                     widget.setFont(new_font)
                     

                     if isinstance(widget, (QTabBar, QTabWidget)):

                         widget.setStyleSheet(widget.styleSheet())
                     elif hasattr(widget, 'setStyleSheet') and 'QTextEdit' in str(type(widget)):

                         widget.setStyleSheet(widget.styleSheet())

                         if hasattr(widget, 'document') and widget.document():
                             widget.document().setModified(True)
                             widget.viewport().update()
                     

                     widget.update()
                     widget.repaint()
                     

                     if hasattr(widget, 'children'):
                         self._apply_scale_to_widgets(widget.children(), base_size)
                     
                 except Exception:
                     pass
    
    def get_current_scale(self):
        return self.current_scale
    
    def save_scale_to_config(self):
        if self.config_manager:
            if "ui_settings" not in self.config_manager.app_config:
                self.config_manager.app_config["ui_settings"] = {}
            self.config_manager.app_config["ui_settings"]["font_scale"] = self.current_scale
            self.config_manager.save_app_config()
    
    def load_scale_from_config(self):
        if self.config_manager:
            scale = self.config_manager.app_config.get("ui_settings", {}).get("font_scale", self.default_scale)
            self.current_scale = scale