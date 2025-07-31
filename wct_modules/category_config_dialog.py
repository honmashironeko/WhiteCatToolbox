#!/usr/bin/env python3


from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QComboBox, QTextEdit, QColorDialog,
    QMessageBox, QHeaderView, QFrame, QGroupBox, QSplitter, QListWidget,
    QListWidgetItem, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from .category_manager import CategoryManager

class CategoryConfigDialog(QDialog):
    categories_updated = Signal()
    
    def __init__(self, category_manager: CategoryManager, tool_scanner=None, parent=None):
        super().__init__(parent)
        self.category_manager = category_manager
        self.tool_scanner = tool_scanner
        self.setWindowTitle("分类管理")
        self.setModal(True)
        self.resize(900, 600)
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        splitter = QSplitter(Qt.Horizontal)
        

        category_group = QGroupBox("分类管理")
        category_layout = QVBoxLayout(category_group)
        

        category_buttons = QHBoxLayout()
        self.add_category_btn = QPushButton("添加分类")
        self.edit_category_btn = QPushButton("编辑分类")
        self.delete_category_btn = QPushButton("删除分类")
        
        self.add_category_btn.clicked.connect(self.add_category)
        self.edit_category_btn.clicked.connect(self.edit_category)
        self.delete_category_btn.clicked.connect(self.delete_category)
        
        category_buttons.addWidget(self.add_category_btn)
        category_buttons.addWidget(self.edit_category_btn)
        category_buttons.addWidget(self.delete_category_btn)
        category_buttons.addStretch()
        
        category_layout.addLayout(category_buttons)
        

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(2)
        self.category_table.setHorizontalHeaderLabels(["分类名称", "描述"])
        header = self.category_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.category_table.selectionBehavior = QTableWidget.SelectRows
        
        category_layout.addWidget(self.category_table)
        

        tool_group = QGroupBox("工具分类配置")
        tool_layout = QVBoxLayout(tool_group)
        

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索工具:"))
        self.tool_search = QLineEdit()
        self.tool_search.setPlaceholderText("输入工具名称...")
        self.tool_search.textChanged.connect(self.filter_tools)
        search_layout.addWidget(self.tool_search)
        tool_layout.addLayout(search_layout)
        

        tool_splitter = QSplitter(Qt.Vertical)
        

        self.tool_list = QListWidget()
        self.tool_list.setSelectionMode(QListWidget.MultiSelection)
        self.tool_list.currentItemChanged.connect(self.on_tool_selected)
        tool_splitter.addWidget(QLabel("工具列表:"))
        tool_splitter.addWidget(self.tool_list)
        

        category_select_frame = QFrame()
        category_select_layout = QVBoxLayout(category_select_frame)
        
        category_select_layout.addWidget(QLabel("选择分类:"))
        self.tool_category_combo = QComboBox()
        self.tool_category_combo.currentTextChanged.connect(self.on_tool_category_changed)
        category_select_layout.addWidget(self.tool_category_combo)
        

        batch_layout = QHBoxLayout()
        self.batch_category_combo = QComboBox()
        self.batch_apply_btn = QPushButton("批量应用")
        self.batch_apply_btn.clicked.connect(self.batch_apply_category)
        batch_layout.addWidget(QLabel("批量设置:"))
        batch_layout.addWidget(self.batch_category_combo)
        batch_layout.addWidget(self.batch_apply_btn)
        category_select_layout.addLayout(batch_layout)
        
        tool_splitter.addWidget(category_select_frame)
        tool_layout.addWidget(tool_splitter)
        

        splitter.addWidget(category_group)
        splitter.addWidget(tool_group)
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
        

        buttons_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入配置")
        self.export_btn = QPushButton("导出配置")
        self.save_btn = QPushButton("保存")
        self.cancel_btn = QPushButton("取消")
        
        self.import_btn.clicked.connect(self.import_config)
        self.export_btn.clicked.connect(self.export_config)
        self.save_btn.clicked.connect(self.save_config)
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.import_btn)
        buttons_layout.addWidget(self.export_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def load_data(self):
        """加载数据"""
        self.load_categories()
        self.load_tools()
        self.update_category_combos()
        
    def load_categories(self):
        """加载分类到表格"""
        categories = self.category_manager.get_all_categories()
        self.category_table.setRowCount(len(categories))
        
        for row, (cat_id, cat_info) in enumerate(categories.items()):
            self.category_table.setItem(row, 0, QTableWidgetItem(cat_info.get('display_name', cat_id)))
            self.category_table.setItem(row, 1, QTableWidgetItem(cat_info.get('description', '')))
            
    def load_tools(self):
        """加载工具列表"""
        self.tool_list.clear()
        if self.tool_scanner:
            tools = self.tool_scanner.get_all_tools()
            for tool_info in tools:
                item = QListWidgetItem(f"{tool_info.display_name} ({tool_info.name})")
                item.setData(Qt.UserRole, tool_info.name)
                

                current_category = self.category_manager.get_tool_category(tool_info.name)
                category_display = self.category_manager.get_category_display_name(current_category)
                item.setText(f"{tool_info.display_name} ({tool_info.name}) - [{category_display}]")
                
                self.tool_list.addItem(item)
                
    def update_category_combos(self):
        """更新分类下拉框"""
        categories = self.category_manager.get_all_categories()
        

        self.tool_category_combo.clear()
        self.batch_category_combo.clear()
        

        for cat_id, cat_info in categories.items():
            display_name = cat_info.get('display_name', cat_id)
            self.tool_category_combo.addItem(display_name, cat_id)
            self.batch_category_combo.addItem(display_name, cat_id)
            
    def filter_tools(self):
        """筛选工具"""
        search_text = self.tool_search.text().lower()
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            item.setHidden(search_text not in item.text().lower())
            
    def on_tool_selected(self, current, previous):
        """工具选择改变"""
        if current:
            tool_name = current.data(Qt.UserRole)
            current_category = self.category_manager.get_tool_category(tool_name)
            

            for i in range(self.tool_category_combo.count()):
                if self.tool_category_combo.itemData(i) == current_category:
                    self.tool_category_combo.setCurrentIndex(i)
                    break
                    
    def on_tool_category_changed(self, text):
        """工具分类改变"""
        current_item = self.tool_list.currentItem()
        if current_item:
            tool_name = current_item.data(Qt.UserRole)
            category_id = self.tool_category_combo.currentData()
            self.category_manager.set_tool_category(tool_name, category_id)
            

            category_display = self.category_manager.get_category_display_name(category_id)
            tool_info = self.tool_scanner.get_tool_info(tool_name) if self.tool_scanner else None
            if tool_info:
                current_item.setText(f"{tool_info.display_name} ({tool_info.name}) - [{category_display}]")
                
    def batch_apply_category(self):
        """批量应用分类"""
        selected_items = self.tool_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要应用分类的工具")
            return
            
        category_id = self.batch_category_combo.currentData()
        category_display = self.category_manager.get_category_display_name(category_id)
        
        for item in selected_items:
            tool_name = item.data(Qt.UserRole)
            self.category_manager.set_tool_category(tool_name, category_id)
            

            tool_info = self.tool_scanner.get_tool_info(tool_name) if self.tool_scanner else None
            if tool_info:
                item.setText(f"{tool_info.display_name} ({tool_info.name}) - [{category_display}]")
                
        QMessageBox.information(self, "成功", f"已将{len(selected_items)}个工具设置为分类: {category_display}")
        
    def add_category(self):
        """添加分类"""
        dialog = CategoryEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            display_name, cat_info = dialog.get_category_data()
            self.category_manager.add_category(display_name, **cat_info)
            self.load_categories()
            self.update_category_combos()
            
    def edit_category(self):
        """编辑分类"""
        current_row = self.category_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要编辑的分类")
            return
            
        cat_name = self.category_table.item(current_row, 0).text()
        cat_info = self.category_manager.get_category_info(cat_name)
        
        dialog = CategoryEditDialog(self, cat_name, cat_info)
        if dialog.exec() == QDialog.Accepted:
            new_cat_name, new_cat_info = dialog.get_category_data()
            if new_cat_name != cat_name:

                tools = self.category_manager.get_tools_in_category(cat_name)
                self.category_manager.remove_category(cat_name)
                self.category_manager.add_category(new_cat_name, **new_cat_info)
                for tool in tools:
                    self.category_manager.set_tool_category(tool, new_cat_name)
            else:
                self.category_manager.update_category(cat_name, **new_cat_info)
            self.load_categories()
            self.update_category_combos()
            self.load_tools()
            
    def delete_category(self):
        """删除分类"""
        current_row = self.category_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "请先选择要删除的分类")
            return
            
        cat_name = self.category_table.item(current_row, 0).text()
        

        tools = self.category_manager.get_tools_in_category(cat_name)
        if tools:
            reply = QMessageBox.question(
                self, "确认删除", 
                f"分类 '{cat_name}' 下有 {len(tools)} 个工具，删除后这些工具将变为未分类。确定要删除吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
                
        self.category_manager.remove_category(cat_name)
        self.load_categories()
        self.update_category_combos()
        self.load_tools()
        
    def import_config(self):
        """导入配置"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入分类配置", "", "JSON文件 (*.json)"
        )
        if file_path:
            if self.category_manager.import_categories(file_path):
                QMessageBox.information(self, "成功", "分类配置导入成功")
                self.load_data()
            else:
                QMessageBox.warning(self, "失败", "分类配置导入失败")
                
    def export_config(self):
        """导出配置"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出分类配置", "categories.json", "JSON文件 (*.json)"
        )
        if file_path:
            if self.category_manager.export_categories(file_path):
                QMessageBox.information(self, "成功", "分类配置导出成功")
            else:
                QMessageBox.warning(self, "失败", "分类配置导出失败")
                
    def save_config(self):
        """保存配置"""
        self.category_manager.save_categories()
        self.categories_updated.emit()
        self.accept()


class CategoryEditDialog(QDialog):
    def __init__(self, parent=None, category_name="", category_info=None):
        super().__init__(parent)
        self.category_name = category_name
        self.category_info = category_info or {}
        self.setWindowTitle("编辑分类" if category_name else "添加分类")
        self.setModal(True)
        self.resize(400, 250)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        layout.addWidget(QLabel("分类名称:"))
        self.name_edit = QLineEdit(self.category_info.get('display_name', self.category_name))
        layout.addWidget(self.name_edit)
        

        layout.addWidget(QLabel("描述:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setText(self.category_info.get('description', ''))
        layout.addWidget(self.desc_edit)
        

        layout.addWidget(QLabel("图标 (可选):"))
        self.icon_edit = QLineEdit(self.category_info.get('icon', '📁'))
        layout.addWidget(self.icon_edit)
        

        buttons_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
            
    def get_category_data(self):
        """获取分类数据"""
        cat_name = self.name_edit.text().strip()
        cat_info = {
            'display_name': cat_name,
            'description': self.desc_edit.toPlainText().strip(),
            'icon': self.icon_edit.text().strip()
        }
        return cat_name, cat_info