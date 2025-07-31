from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
    QGroupBox, QCheckBox, QComboBox, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QSplitter, QDialog,
    QDialogButtonBox, QMessageBox, QFileDialog, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread, QProcess, QTimer
from PySide6.QtGui import QFont, QIcon, QColor
import os
import sys
import json
import subprocess
import platform
from pathlib import Path

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        winreg = None
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class EnvVariable:
    name: str
    value: str
    scope: str
    original_value: str = ""
    is_modified: bool = False
    is_new: bool = False
    
class SystemEnvManager:
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        if self.is_windows and winreg:
            self.user_env_key = r"Environment"
            self.system_env_key = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        
    def get_environment_variables(self) -> Dict[str, EnvVariable]:
        """获取所有环境变量"""
        variables = {}
        
        # On non-Windows systems, use os.environ directly
        if not self.is_windows or not winreg:
            for name, value in os.environ.items():
                variables[name] = EnvVariable(
                    name=name,
                    value=value,
                    scope='system',
                    original_value=value
                )
            return variables
        
        # Windows-specific registry access
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.user_env_key) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        variables[name] = EnvVariable(
                            name=name,
                            value=value,
                            scope='user',
                            original_value=value
                        )
                        i += 1
                    except (WindowsError, OSError):
                        break
        except Exception as e:
            print(f"读取用户环境变量失败: {e}")
            
        # 读取系统环境变量
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self.system_env_key) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        if name not in variables:
                            variables[name] = EnvVariable(
                                name=name,
                                value=value,
                                scope='system',
                                original_value=value
                            )
                        i += 1
                    except (WindowsError, OSError):
                        break
        except Exception as e:
            print(f"读取系统环境变量失败: {e}")
            
        return variables
        
    def set_environment_variable(self, name: str, value: str, scope: str = 'user') -> bool:
        """设置环境变量"""
        if not self.is_windows or not winreg:
            # On non-Windows systems, only set in current process
            os.environ[name] = value
            return True
            
        try:
            if scope == 'user':
                key_path = self.user_env_key
                hkey = winreg.HKEY_CURRENT_USER
            else:
                key_path = self.system_env_key
                hkey = winreg.HKEY_LOCAL_MACHINE
                
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
                
            # 广播环境变量更改
            self.broadcast_env_change()
            return True
            
        except Exception as e:
            print(f"设置环境变量失败: {e}")
            return False
            
    def delete_environment_variable(self, name: str, scope: str = 'user') -> bool:
        """删除环境变量"""
        if not self.is_windows or not winreg:
            # On non-Windows systems, only delete from current process
            if name in os.environ:
                del os.environ[name]
            return True
            
        try:
            if scope == 'user':
                key_path = self.user_env_key
                hkey = winreg.HKEY_CURRENT_USER
            else:
                key_path = self.system_env_key
                hkey = winreg.HKEY_LOCAL_MACHINE
                
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
                
            # 广播环境变量更改
            self.broadcast_env_change()
            return True
            
        except Exception as e:
            print(f"删除环境变量失败: {e}")
            return False
            
    def broadcast_env_change(self):
        """通知系统环境变量已更改"""
        if not self.is_windows:
            # Non-Windows systems don't need broadcast notification
            return
            
        try:
            import ctypes
            from ctypes import wintypes
            
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            SMTO_ABORTIFHUNG = 0x0002
            
            result = ctypes.c_long()
            SendMessageTimeoutW = ctypes.windll.user32.SendMessageTimeoutW
            SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,
                ctypes.byref(result)
            )
        except Exception as e:
            print(f"广播环境变量更改失败: {e}")
            
    def backup_environment(self, file_path: str) -> bool:
        """备份环境变量到文件"""
        try:
            variables = self.get_environment_variables()
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'variables': {name: asdict(var) for name, var in variables.items()}
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            print(f"备份环境变量失败: {e}")
            return False
            
    def restore_environment(self, file_path: str) -> bool:
        """从文件恢复环境变量"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
                
            variables = backup_data.get('variables', {})
            
            for name, var_data in variables.items():
                var = EnvVariable(**var_data)
                self.set_environment_variable(var.name, var.value, var.scope)
                
            return True
            
        except Exception as e:
            print(f"恢复环境变量失败: {e}")
            return False
            


class EnvVariableDialog(QDialog):
    def __init__(self, variable: EnvVariable = None, parent=None):
        super().__init__(parent)
        self.variable = variable
        self.setWindowTitle("编辑环境变量" if variable else "新建环境变量")
        self.setModal(True)
        self.resize(500, 300)
        self.init_ui()
        
        if variable:
            self.load_variable()
            
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("变量名:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        

        layout.addWidget(QLabel("变量值:"))
        self.value_edit = QTextEdit()
        self.value_edit.setMaximumHeight(150)
        layout.addWidget(self.value_edit)
        

        scope_layout = QHBoxLayout()
        scope_layout.addWidget(QLabel("作用域:"))
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["用户变量", "系统变量"])
        scope_layout.addWidget(self.scope_combo)
        scope_layout.addStretch()
        layout.addLayout(scope_layout)
        

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def load_variable(self):
        self.name_edit.setText(self.variable.name)
        self.value_edit.setText(self.variable.value)
        self.scope_combo.setCurrentText(
            "用户变量" if self.variable.scope == 'user' else "系统变量"
        )
        
    def get_variable_data(self) -> Tuple[str, str, str]:
        name = self.name_edit.text().strip()
        value = self.value_edit.toPlainText().strip()
        scope = 'user' if self.scope_combo.currentText() == "用户变量" else 'system'
        
        return name, value, scope



class SystemEnvWidget(QWidget):
    environment_changed = Signal()
    
    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.manager = SystemEnvManager()
        self.variables = {}
        self.init_ui()
        self.load_variables()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        toolbar_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("新建")
        self.new_btn.clicked.connect(self.new_variable)
        toolbar_layout.addWidget(self.new_btn)
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self.edit_variable)
        toolbar_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_variable)
        toolbar_layout.addWidget(self.delete_btn)
        

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        toolbar_layout.addWidget(separator)
        
        self.backup_btn = QPushButton("备份")
        self.backup_btn.clicked.connect(self.backup_environment)
        toolbar_layout.addWidget(self.backup_btn)
        
        self.restore_btn = QPushButton("恢复")
        self.restore_btn.clicked.connect(self.restore_environment)
        toolbar_layout.addWidget(self.restore_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_variables)
        toolbar_layout.addWidget(self.refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_variables)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        

        self.env_tree = QTreeWidget()
        self.env_tree.setHeaderLabels(["变量名", "变量值", "作用域"])
        self.env_tree.currentItemChanged.connect(self.update_buttons)
        self.env_tree.itemDoubleClicked.connect(self.edit_variable)
        layout.addWidget(self.env_tree)
        
        self.update_buttons()
        
    def load_variables(self):
        self.variables = self.manager.get_environment_variables()
        self.update_tree()
        
    def update_tree(self):
        self.env_tree.clear()
        

        user_root = QTreeWidgetItem(["用户变量", "", ""])
        system_root = QTreeWidgetItem(["系统变量", "", ""])
        
        user_root.setExpanded(True)
        system_root.setExpanded(True)
        
        self.env_tree.addTopLevelItem(user_root)
        self.env_tree.addTopLevelItem(system_root)
        
        for name, variable in sorted(self.variables.items()):

            search_text = self.search_edit.text().lower()
            if search_text and search_text not in name.lower() and \
               search_text not in variable.value.lower():
                continue
                
            item = QTreeWidgetItem([
                variable.name,
                variable.value[:100] + "..." if len(variable.value) > 100 else variable.value,
                variable.scope
            ])
            
            item.setData(0, Qt.UserRole, variable)
            item.setToolTip(1, variable.value)
            
            if variable.scope == 'user':
                user_root.addChild(item)
            else:
                system_root.addChild(item)
                
    def filter_variables(self):
        self.update_tree()
        
    def new_variable(self):
        dialog = EnvVariableDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            name, value, scope = dialog.get_variable_data()
            
            if not name:
                QMessageBox.warning(self, "警告", "请输入变量名")
                return
                
            success = self.manager.set_environment_variable(name, value, scope)
            
            if success:
                QMessageBox.information(self, "成功", f"环境变量 '{name}' 已创建")
                self.load_variables()
                self.environment_changed.emit()
            else:
                QMessageBox.critical(self, "失败", f"创建环境变量 '{name}' 失败")
                
    def edit_variable(self):
        current_item = self.env_tree.currentItem()
        if not current_item or not current_item.data(0, Qt.UserRole):
            return
            
        variable = current_item.data(0, Qt.UserRole)
        
        dialog = EnvVariableDialog(variable, parent=self)
        if dialog.exec() == QDialog.Accepted:
            name, value, scope = dialog.get_variable_data()
            
            if not name:
                QMessageBox.warning(self, "警告", "请输入变量名")
                return
                
            success = self.manager.set_environment_variable(name, value, scope)
            
            if success:
                QMessageBox.information(self, "成功", f"环境变量 '{name}' 已更新")
                self.load_variables()
                self.environment_changed.emit()
            else:
                QMessageBox.critical(self, "失败", f"更新环境变量 '{name}' 失败")
                
    def delete_variable(self):
        current_item = self.env_tree.currentItem()
        if not current_item or not current_item.data(0, Qt.UserRole):
            return
            
        variable = current_item.data(0, Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除环境变量 '{variable.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.manager.delete_environment_variable(
                variable.name, variable.scope
            )
            
            if success:
                QMessageBox.information(self, "成功", f"环境变量 '{variable.name}' 已删除")
                self.load_variables()
                self.environment_changed.emit()
            else:
                QMessageBox.critical(self, "失败", f"删除环境变量 '{variable.name}' 失败")
                
    def backup_environment(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "备份环境变量",
            f"env_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            success = self.manager.backup_environment(file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"环境变量已备份到 {file_path}")
            else:
                QMessageBox.critical(self, "失败", "备份环境变量失败")
                
    def restore_environment(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "恢复环境变量",
            "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self, "确认恢复",
                "恢复环境变量将覆盖现有设置，确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.manager.restore_environment(file_path)
                
                if success:
                    QMessageBox.information(self, "成功", "环境变量已恢复")
                    self.load_variables()
                    self.environment_changed.emit()
                else:
                    QMessageBox.critical(self, "失败", "恢复环境变量失败")
                    

        
    def update_buttons(self):
        current_item = self.env_tree.currentItem()
        has_variable = bool(current_item and current_item.data(0, Qt.UserRole))
        
        self.edit_btn.setEnabled(has_variable)
        self.delete_btn.setEnabled(has_variable)