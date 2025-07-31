"""
可拖拽标签页组件
支持标签页拖拽排序、双击重命名等功能
"""

from PySide6.QtWidgets import (
    QTabWidget, QTabBar, QLineEdit, QWidget, QApplication,
    QMenu, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer, QMimeData
from PySide6.QtGui import QDrag, QPainter, QPixmap, QCursor, QAction
import sys

class DraggableTabBar(QTabBar):
    """可拖拽的标签栏"""
    

    tab_moved_signal = Signal(int, int)
    tab_rename_requested = Signal(int, str)
    tab_duplicate_requested = Signal(int)
    tab_clicked_signal = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMovable(True)
        

        self.drag_start_position = QPoint()
        self.dragging = False
        self.drag_index = -1
        

        self.double_click_timer = QTimer()
        self.double_click_timer.setSingleShot(True)
        self.double_click_timer.timeout.connect(self.handle_single_click)
        self.last_click_index = -1
        self.rename_editor = None
        

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position().toPoint()
            self.drag_index = self.tabAt(event.position().toPoint())
            

            if self.drag_index >= 0:
                if self.last_click_index == self.drag_index and self.double_click_timer.isActive():

                    self.double_click_timer.stop()
                    self.start_rename(self.drag_index)
                else:

                    self.last_click_index = self.drag_index
                    self.double_click_timer.start(300)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.position().toPoint() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        if self.drag_index >= 0 and not self.dragging:
            self.start_drag()
        
        super().mouseMoveEvent(event)
    
    def handle_single_click(self):
        """处理单击事件"""

        if self.last_click_index >= 0:
            self.tab_clicked_signal.emit(self.last_click_index)
    
    def start_drag(self):
        """开始拖拽操作"""
        if self.drag_index < 0:
            return
        
        self.dragging = True
        

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"tab_{self.drag_index}")
        drag.setMimeData(mime_data)
        

        tab_rect = self.tabRect(self.drag_index)
        pixmap = QPixmap(tab_rect.size())
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setOpacity(0.8)
        self.render(painter, QPoint(), tab_rect)
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(tab_rect.width() // 2, tab_rect.height() // 2))
        

        drop_action = drag.exec(Qt.MoveAction)
        
        self.dragging = False
        self.drag_index = -1
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("tab_"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("tab_"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """拖拽放下事件"""
        if not (event.mimeData().hasText() and event.mimeData().text().startswith("tab_")):
            event.ignore()
            return
        

        drag_text = event.mimeData().text()
        try:
            from_index = int(drag_text.split("_")[1])
        except (ValueError, IndexError):
            event.ignore()
            return
        

        drop_position = event.position().toPoint()
        to_index = self.tabAt(drop_position)
        
        if to_index < 0:
            to_index = self.count() - 1
        
        if from_index != to_index and 0 <= from_index < self.count() and 0 <= to_index < self.count():

            self.tab_moved_signal.emit(from_index, to_index)
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def start_rename(self, index):
        """开始重命名标签页"""
        if index < 0 or index >= self.count():
            return
        

        tab_rect = self.tabRect(index)
        current_text = self.tabText(index)
        

        self.rename_editor = QLineEdit(self)
        self.rename_editor.setText(current_text)
        self.rename_editor.setGeometry(tab_rect)
        self.rename_editor.selectAll()
        self.rename_editor.show()
        self.rename_editor.setFocus()
        

        self.rename_editor.editingFinished.connect(lambda: self.finish_rename(index))
        self.rename_editor.returnPressed.connect(lambda: self.finish_rename(index))
    
    def finish_rename(self, index):
        """完成重命名"""
        if not self.rename_editor:
            return
        
        new_name = self.rename_editor.text().strip()
        self.rename_editor.deleteLater()
        self.rename_editor = None
        
        if new_name and new_name != self.tabText(index):

            self.tab_rename_requested.emit(index, new_name)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        index = self.tabAt(position)
        if index < 0:
            return
        
        menu = QMenu(self)
        

        rename_action = QAction("重命名标签页", self)
        rename_action.triggered.connect(lambda: self.start_rename(index))
        menu.addAction(rename_action)
        

        duplicate_action = QAction("复制标签页", self)
        duplicate_action.triggered.connect(lambda: self.tab_duplicate_requested.emit(index))
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        

        if self.count() > 1:
            close_action = QAction("关闭标签页", self)
            close_action.triggered.connect(lambda: self.parent().close_tab_by_index(index))
            menu.addAction(close_action)
        

        if self.count() > 1:
            close_others_action = QAction("关闭其他标签页", self)
            close_others_action.triggered.connect(lambda: self.parent().close_other_tabs(index))
            menu.addAction(close_others_action)
        
        menu.exec(self.mapToGlobal(position))

class DraggableTabWidget(QTabWidget):
    """可拖拽的标签页控件"""
    

    tab_renamed = Signal(int, str)
    tab_moved = Signal(int, int)
    tab_duplicated = Signal(int)
    new_tab_requested = Signal()
    tab_clicked = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        

        self.draggable_tab_bar = DraggableTabBar(self)
        self.setTabBar(self.draggable_tab_bar)
        

        self.draggable_tab_bar.tab_moved_signal.connect(self.move_tab)
        self.draggable_tab_bar.tab_rename_requested.connect(self.rename_tab)
        self.draggable_tab_bar.tab_duplicate_requested.connect(self.duplicate_tab)
        self.draggable_tab_bar.tab_clicked_signal.connect(self.tab_clicked.emit)
        

        self.setTabsClosable(True)
        

        self.setup_new_tab_button()
    
    def setup_new_tab_button(self):
        """设置新建标签页按钮"""

        pass
    
    def move_tab(self, from_index, to_index):
        """移动标签页"""
        if from_index == to_index:
            return
        

        widget = self.widget(from_index)
        text = self.tabText(from_index)
        icon = self.tabIcon(from_index)
        tooltip = self.tabToolTip(from_index)
        

        self.removeTab(from_index)
        

        self.insertTab(to_index, widget, icon, text)
        self.setTabToolTip(to_index, tooltip)
        

        self.setCurrentIndex(to_index)
        

        self.tab_moved.emit(from_index, to_index)
    
    def rename_tab(self, index, new_name):
        """重命名标签页"""
        if 0 <= index < self.count():
            old_name = self.tabText(index)
            self.setTabText(index, new_name)
            

            widget = self.widget(index)
            if hasattr(widget, 'tab_name'):
                widget.tab_name = new_name
            

            self.tab_renamed.emit(index, new_name)
    
    def duplicate_tab(self, index):
        """复制标签页"""
        if 0 <= index < self.count():

            self.tab_duplicated.emit(index)
    
    def close_tab_by_index(self, index):
        """通过索引关闭标签页"""
        if 0 <= index < self.count():
            self.tabCloseRequested.emit(index)
    
    def close_other_tabs(self, keep_index):
        """关闭除指定索引外的其他标签页"""
        if self.count() <= 1:
            return
        
        reply = QMessageBox.question(
            self, "确认关闭", 
            "确定要关闭其他所有标签页吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:

            for i in range(self.count() - 1, -1, -1):
                if i != keep_index:
                    self.tabCloseRequested.emit(i)
    
    def add_new_tab_button(self):
        """添加新建标签页按钮"""

        plus_widget = QWidget()
        plus_index = self.addTab(plus_widget, "+")
        

        self.tabBar().setTabButton(plus_index, QTabBar.RightSide, None)
        
        return plus_index
    
    def handle_tab_click(self, index):
        """处理标签页点击"""
        if self.tabText(index) == "+":

            self.new_tab_requested.emit()
            return False
        return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    

    tab_widget = DraggableTabWidget()
    

    for i in range(3):
        widget = QWidget()
        tab_widget.addTab(widget, f"标签页 {i+1}")
    

    tab_widget.tab_renamed.connect(lambda idx, name: print(f"标签页 {idx} 重命名为: {name}"))
    tab_widget.tab_moved.connect(lambda from_idx, to_idx: print(f"标签页从 {from_idx} 移动到 {to_idx}"))
    
    tab_widget.show()
    tab_widget.resize(600, 400)
    
    sys.exit(app.exec())