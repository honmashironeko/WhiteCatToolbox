from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QScrollArea, QPushButton, 
    QFrame, QSizePolicy, QLabel, QLineEdit, QComboBox,
    QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPalette
from .category_manager import CategoryManager
from .category_config_dialog import CategoryConfigDialog

class ToolButton(QPushButton):
    def __init__(self, tool_name, display_name):
        super().__init__()
        self.tool_name = tool_name
        self.display_name = display_name
        self.setText(display_name)
        self.setCheckable(True)

        self.setObjectName("ToolButton")

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

class FloatingToolBar(QFrame):
    tool_selected = Signal(str)
    promotion_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.tools = []
        self.tool_buttons = []
        self.current_tool = None
        self.filtered_tools = []
        self.tool_scanner = None
        self.category_manager = CategoryManager()
        self.init_ui()
        
    def init_ui(self):

        self.setObjectName("FloatingToolBar")
        

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)
        

        search_layout = QHBoxLayout()
        

        search_label = QLabel("搜索:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入工具名称、描述或标签...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        

        category_label = QLabel("分类:")
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部分类")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        

        self.clear_button = QPushButton("清除筛选")
        self.clear_button.clicked.connect(self.clear_filters)
        

        self.manage_categories_btn = QPushButton("分类管理")
        self.manage_categories_btn.clicked.connect(self.open_category_manager)
        

        self.promotion_btn = QPushButton("推广信息")
        self.promotion_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff9a9e, stop:1 #fecfef);
                color: #333;
                border: 1px solid #ff6b6b;
                border-radius: 4px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffb3ba, stop:1 #ffdfdf);
                border-color: #ff5252;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ff8a8a, stop:1 #ffc0cb);
            }
        """)
        self.promotion_btn.clicked.connect(self.show_promotion)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(category_label)
        search_layout.addWidget(self.category_combo)
        search_layout.addWidget(self.clear_button)
        search_layout.addWidget(self.manage_categories_btn)
        search_layout.addWidget(self.promotion_btn)
        search_layout.addStretch()
        
        main_layout.addLayout(search_layout)
        

        tools_layout = QHBoxLayout()
        
        title_label = QLabel("工具选择:")
        tools_layout.addWidget(title_label)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)

        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(5)

        self.scroll_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.scroll_area.setWidget(self.scroll_widget)
        tools_layout.addWidget(self.scroll_area)
        
        main_layout.addLayout(tools_layout)
        
    def set_tools(self, tools):
        self.tools = tools
        self.clear_buttons()
        
        for tool_name, tool_info in tools.items():
            display_name = tool_info.get('display_name', tool_name)
            button = ToolButton(tool_name, display_name)
            button.clicked.connect(lambda checked, name=tool_name: self.on_tool_clicked(name))
            
            self.tool_buttons.append(button)
            self.scroll_layout.addWidget(button)
            
        self.scroll_layout.addStretch()
            
    def update_tools(self, tool_infos, tool_scanner=None):
        self.tools = tool_infos
        self.tool_scanner = tool_scanner
        self.filtered_tools = tool_infos.copy()
        

        self.update_categories()
        

        self.display_tools(self.filtered_tools)
        
    def update_categories(self):
        self.category_combo.clear()
        self.category_combo.addItem("全部分类")
        

        categories = self.category_manager.get_all_categories()
        for category_id, category_info in sorted(categories.items()):
            display_name = category_info.get('display_name', category_id)
            self.category_combo.addItem(display_name, category_id)
    
    def get_tool_display_category(self, tool_info):
        """获取工具的显示分类"""

        custom_category = self.category_manager.get_tool_category(tool_info.name, None)
        if custom_category:
            return custom_category

        return tool_info.category
    
    def display_tools(self, tool_infos):
        self.clear_buttons()
        
        for tool_info in tool_infos:
            display_name = tool_info.display_name or tool_info.name
            button = ToolButton(tool_info.name, display_name)
            button.clicked.connect(lambda checked, name=tool_info.name: self.on_tool_clicked(name))
            
            self.tool_buttons.append(button)
            self.scroll_layout.addWidget(button)
            
        self.scroll_layout.addStretch()

    def on_search_text_changed(self, text):
        self.filter_tools()
        
    def on_category_changed(self, category_display):
        self.filter_tools()
        
    def filter_tools(self):
        search_text = self.search_input.text().lower()
        selected_category_display = self.category_combo.currentText()
        selected_category_id = self.category_combo.currentData()
        

        filtered = []
        for tool_info in self.tools:

            text_match = True
            if search_text:
                text_match = (
                    search_text in tool_info.name.lower() or
                    search_text in tool_info.display_name.lower() or
                    search_text in tool_info.description.lower() or
                    any(search_text in tag.lower() for tag in tool_info.tags)
                )
            

            category_match = True
            if selected_category_display != "全部分类" and selected_category_id:
                tool_category = self.get_tool_display_category(tool_info)
                category_match = tool_category == selected_category_id
            
            if text_match and category_match:
                filtered.append(tool_info)
        
        self.filtered_tools = filtered
        self.display_tools(self.filtered_tools)
        
    def clear_filters(self):
        self.search_input.clear()
        self.category_combo.setCurrentText("全部分类")
        self.filter_tools()
        
    def open_category_manager(self):
        """打开分类管理对话框"""
        dialog = CategoryConfigDialog(self.category_manager, self.tool_scanner, self)
        dialog.categories_updated.connect(self.on_categories_updated)
        dialog.exec()
        
    def on_categories_updated(self):
        """分类更新后的处理"""
        self.update_categories()
        self.filter_tools()
            
    def clear_buttons(self):

        for button in self.tool_buttons:
            button.deleteLater()
        self.tool_buttons.clear()
        

        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.spacerItem():
                del child
        
    def on_tool_clicked(self, tool_name):

        for button in self.tool_buttons:
            button.setChecked(button.tool_name == tool_name)
            

        main_window = self.window()
        if (hasattr(main_window, 'notification_manager') and 
            main_window.notification_manager):


            pass
            

        if self.current_tool == tool_name:
            return
            
        self.current_tool = tool_name
        self.tool_selected.emit(tool_name)
        
    def clear_selection(self):
        """清除当前工具选择状态"""
        for button in self.tool_buttons:
            button.setChecked(False)
        self.current_tool = None
        
    def show_promotion(self):
        """显示推广界面"""
        self.promotion_requested.emit()