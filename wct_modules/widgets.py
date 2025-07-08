from PySide6.QtWidgets import QLabel, QTabWidget, QTabBar, QLineEdit
from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QFont
from .theme import fonts
from .styles import get_clickable_label_style
from .utils import s

class ClickableLabel(QLabel):

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.checked = False
        self.setFont(QFont(fonts["system"], s(8), QFont.Bold))
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
        self.setStyleSheet(get_clickable_label_style(self.checked, is_required)) 

class EditableTabWidget(QTabWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.custom_tab_bar = EditableTabBar(self)
        self.setTabBar(self.custom_tab_bar)

        self.custom_tab_bar.tab_rename_requested.connect(self.start_rename_tab)

        self.tab_editor = QLineEdit(self)
        self.tab_editor.hide()
        self.tab_editor.setFixedHeight(s(25))
        self.tab_editor.editingFinished.connect(self.finish_rename_tab)

        self.editing_index = -1
    
    def start_rename_tab(self, index):
        
        if index < 0 or index >= self.count():
            return
            
        self.editing_index = index
        current_text = self.tabText(index)

        tab_rect = self.tabBar().tabRect(index)

        self.tab_editor.setGeometry(
            tab_rect.x() + s(5),
            tab_rect.y() + s(2),
            tab_rect.width() - s(10),
            tab_rect.height() - s(4)
        )

        self.tab_editor.setText(current_text)
        self.tab_editor.selectAll()
        self.tab_editor.setStyleSheet(f"""
            QLineEdit {{
                background-color: white;
                border: 1px solid #4a90e2;
                border-radius: {s(3)}px;
                padding: {s(2)}px {s(4)}px;
                font-size: {s(9)}pt;
            }}
        """)

        self.tab_editor.show()
        self.tab_editor.setFocus()
    
    def finish_rename_tab(self):
        
        if self.editing_index >= 0:
            new_name = self.tab_editor.text().strip()
            if new_name:
                self.setTabText(self.editing_index, new_name)
            
            self.tab_editor.hide()
            self.editing_index = -1
    
    def resizeEvent(self, event):
        
        super().resizeEvent(event)
        if self.tab_editor.isVisible():
            self.tab_editor.hide()
            self.editing_index = -1

class EditableTabBar(QTabBar):

    tab_rename_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def mouseDoubleClickEvent(self, event):
        
        if event.button() == Qt.LeftButton:

            index = self.tabAt(event.position().toPoint())
            if index >= 0:
                self.tab_rename_requested.emit(index)
                return
        
        super().mouseDoubleClickEvent(event) 