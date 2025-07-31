from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QComboBox, QLineEdit,
    QTextEdit, QGroupBox, QCheckBox, QProgressBar,
    QMessageBox, QFileDialog, QTabWidget, QSplitter,
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, QThread, QProcess, QTimer
from PySide6.QtGui import QFont, QIcon, QColor
import os
import sys
import json
import subprocess
import venv
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class VirtualEnvInfo:
    name: str
    path: str
    python_version: str
    created_time: str
    last_used: str
    packages: List[Dict[str, str]] = None
    is_active: bool = False
    description: str = ""
    
    def __post_init__(self):
        if self.packages is None:
            self.packages = []

class VirtualEnvManager:
    def __init__(self, base_dir: str = None):
        if base_dir is None:

            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            base_dir = os.path.join(app_dir, "config", "venvs")
        self.base_dir = base_dir
        self.config_file = os.path.join(self.base_dir, "venvs.json")
        self.ensure_base_dir()
        
    def ensure_base_dir(self):
        os.makedirs(self.base_dir, exist_ok=True)
        
    def load_environments(self) -> List[VirtualEnvInfo]:
        if not os.path.exists(self.config_file):
            return []
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [VirtualEnvInfo(**env_data) for env_data in data]
        except Exception as e:
            print(f"加载虚拟环境配置失败: {e}")
            return []
            
    def save_environments(self, environments: List[VirtualEnvInfo]):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                data = [asdict(env) for env in environments]
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存虚拟环境配置失败: {e}")
            
    def create_environment(self, name: str, python_path: str = None, 
                          description: str = "") -> tuple[bool, str]:
        env_path = os.path.join(self.base_dir, name)
        
        if os.path.exists(env_path):
            return False, f"目录 '{env_path}' 已存在"
            
        try:
            if python_path:

                result = subprocess.run([python_path, "-m", "venv", env_path], 
                                      check=True, capture_output=True, text=True)
                if result.returncode != 0:
                    return False, f"创建虚拟环境失败: {result.stderr}"
            else:

                import venv
                venv.create(env_path, with_pip=True)
                

            python_exe = self.get_python_executable(env_path)
            result = subprocess.run([python_exe, "--version"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"无法获取Python版本: {result.stderr}"
                
            python_version = result.stdout.strip()
            

            env_info = VirtualEnvInfo(
                name=name,
                path=env_path,
                python_version=python_version,
                created_time=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                description=description
            )
            

            environments = self.load_environments()
            environments.append(env_info)
            self.save_environments(environments)
            
            return True, "创建成功"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"命令执行失败: {e.stderr if e.stderr else str(e)}"
            print(f"创建虚拟环境失败: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"创建虚拟环境时发生错误: {str(e)}"
            print(f"创建虚拟环境失败: {error_msg}")
            return False, error_msg
            
    def delete_environment(self, name: str) -> bool:
        environments = self.load_environments()
        env_to_delete = None
        
        for env in environments:
            if env.name == name:
                env_to_delete = env
                break
                
        if not env_to_delete:
            return False
            
        try:

            import shutil
            if os.path.exists(env_to_delete.path):
                shutil.rmtree(env_to_delete.path)
                

            environments.remove(env_to_delete)
            self.save_environments(environments)
            
            return True
            
        except Exception as e:
            print(f"删除虚拟环境失败: {e}")
            return False
            
    def get_python_executable(self, env_path: str) -> str:
        if sys.platform == "win32":
            return os.path.join(env_path, "Scripts", "python.exe")
        else:
            return os.path.join(env_path, "bin", "python")
            
    def get_pip_executable(self, env_path: str) -> str:
        if sys.platform == "win32":
            return os.path.join(env_path, "Scripts", "pip.exe")
        else:
            return os.path.join(env_path, "bin", "pip")
            
    def activate_environment(self, env_path: str) -> Dict[str, str]:
        """返回激活虚拟环境所需的环境变量"""
        env_vars = os.environ.copy()
        
        if sys.platform == "win32":
            scripts_dir = os.path.join(env_path, "Scripts")
        else:
            scripts_dir = os.path.join(env_path, "bin")
            

        current_path = env_vars.get('PATH', '')
        env_vars['PATH'] = f"{scripts_dir}{os.pathsep}{current_path}"
        

        env_vars['VIRTUAL_ENV'] = env_path
        

        env_vars.pop('PYTHONHOME', None)
        
        return env_vars
        
    def get_installed_packages(self, env_path: str) -> List[Dict[str, str]]:
        """获取虚拟环境中已安装的包"""
        pip_exe = self.get_pip_executable(env_path)
        
        try:
            result = subprocess.run(
                [pip_exe, "list", "--format=json"],
                capture_output=True, text=True, check=True
            )
            
            packages_data = json.loads(result.stdout)
            return packages_data
            
        except Exception as e:
            print(f"获取包列表失败: {e}")
            return []

class PackageInstallWorker(QThread):
    progress_updated = Signal(str)
    installation_finished = Signal(bool, str)
    
    def __init__(self, env_path: str, packages: List[str], 
                 requirements_file: str = None):
        super().__init__()
        self.env_path = env_path
        self.packages = packages
        self.requirements_file = requirements_file
        self.manager = VirtualEnvManager()
        
    def run(self):
        try:
            pip_exe = self.manager.get_pip_executable(self.env_path)
            
            if self.requirements_file:

                self.progress_updated.emit(f"从 {self.requirements_file} 安装包...")
                result = subprocess.run(
                    [pip_exe, "install", "-r", self.requirements_file],
                    capture_output=True, text=True
                )
            else:

                for package in self.packages:
                    self.progress_updated.emit(f"安装 {package}...")
                    result = subprocess.run(
                        [pip_exe, "install", package],
                        capture_output=True, text=True
                    )
                    
                    if result.returncode != 0:
                        self.installation_finished.emit(False, result.stderr)
                        return
                        
            self.installation_finished.emit(True, "安装完成")
            
        except Exception as e:
            self.installation_finished.emit(False, str(e))

class CreateEnvDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建虚拟环境")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("环境名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        

        python_layout = QHBoxLayout()
        python_layout.addWidget(QLabel("Python版本:"))
        self.python_combo = QComboBox()
        self.python_combo.addItem("使用当前Python", "")
        self.detect_python_versions()
        python_layout.addWidget(self.python_combo)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_python)
        python_layout.addWidget(self.browse_btn)
        layout.addLayout(python_layout)
        

        layout.addWidget(QLabel("描述:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)
        

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def detect_python_versions(self):
        """检测系统中的Python版本"""
        import sys
        import platform
        import os
        

        common_paths = [
            "python", "python3", "python3.8", "python3.9", 
            "python3.10", "python3.11", "python3.12", "python3.13"
        ]
        

        if platform.system() == "Windows":

            windows_paths = [
                r"C:\Python38\python.exe",
                r"C:\Python39\python.exe",
                r"C:\Python310\python.exe",
                r"C:\Python311\python.exe",
                r"C:\Python312\python.exe",
                r"C:\Python313\python.exe"
            ]
            

            appdata = os.environ.get('LOCALAPPDATA', '')
            if appdata:
                for version in ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']:
                    launcher_path = os.path.join(appdata, 'Programs', 'Python', f'Python{version.replace(".", "")}', 'python.exe')
                    if os.path.exists(launcher_path):
                        windows_paths.append(launcher_path)
            
            common_paths.extend(windows_paths)
        

        current_python = sys.executable
        if current_python and os.path.exists(current_python):
            try:
                result = subprocess.run(
                    [current_python, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.python_combo.addItem(f"{version} (当前)", current_python)
            except:
                pass
        

        for python_cmd in common_paths:
            try:
                result = subprocess.run(
                    [python_cmd, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()

                    if python_cmd != current_python:
                        self.python_combo.addItem(f"{version} ({python_cmd})", python_cmd)
            except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
                continue
            except Exception:
                continue
                
    def browse_python(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Python可执行文件",
            "", "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                result = subprocess.run(
                    [file_path, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.python_combo.addItem(f"{version} (自定义)", file_path)
                    self.python_combo.setCurrentIndex(self.python_combo.count() - 1)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无效的Python可执行文件: {e}")
                
    def get_env_info(self) -> tuple:
        name = self.name_edit.text().strip()
        python_path = self.python_combo.currentData()
        description = self.description_edit.toPlainText().strip()
        
        return name, python_path, description

class PackageManagerWidget(QWidget):
    def __init__(self, env_info: VirtualEnvInfo, parent=None):
        super().__init__(parent)
        self.env_info = env_info
        self.manager = VirtualEnvManager()
        self.install_worker = None
        self.init_ui()
        self.load_packages()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        toolbar_layout = QHBoxLayout()
        
        self.install_edit = QLineEdit()
        self.install_edit.setPlaceholderText("输入包名 (如: requests numpy)")
        toolbar_layout.addWidget(self.install_edit)
        
        self.install_btn = QPushButton("安装")
        self.install_btn.clicked.connect(self.install_packages)
        toolbar_layout.addWidget(self.install_btn)
        
        self.requirements_btn = QPushButton("从文件安装")
        self.requirements_btn.clicked.connect(self.install_from_file)
        toolbar_layout.addWidget(self.requirements_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_packages)
        toolbar_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar_layout)
        

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        

        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        

        self.packages_tree = QTreeWidget()
        self.packages_tree.setHeaderLabels(["包名", "版本", "操作"])
        self.packages_tree.setRootIsDecorated(False)
        layout.addWidget(self.packages_tree)
        
    def load_packages(self):
        self.packages_tree.clear()
        self.status_label.setText("加载包列表...")
        
        packages = self.manager.get_installed_packages(self.env_info.path)
        
        for package in packages:
            item = QTreeWidgetItem([
                package['name'],
                package['version'],
                ""
            ])
            

            uninstall_btn = QPushButton("卸载")
            uninstall_btn.clicked.connect(
                lambda checked, pkg=package['name']: self.uninstall_package(pkg)
            )
            
            self.packages_tree.addTopLevelItem(item)
            self.packages_tree.setItemWidget(item, 2, uninstall_btn)
            
        self.status_label.setText(f"已加载 {len(packages)} 个包")
        
    def install_packages(self):
        packages_text = self.install_edit.text().strip()
        if not packages_text:
            QMessageBox.warning(self, "警告", "请输入要安装的包名")
            return
            
        packages = [pkg.strip() for pkg in packages_text.split() if pkg.strip()]
        
        self.start_installation(packages=packages)
        
    def install_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择requirements文件",
            "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.start_installation(requirements_file=file_path)
            
    def start_installation(self, packages: List[str] = None, 
                          requirements_file: str = None):
        if self.install_worker and self.install_worker.isRunning():
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.install_btn.setEnabled(False)
        self.requirements_btn.setEnabled(False)
        
        self.install_worker = PackageInstallWorker(
            self.env_info.path, packages or [], requirements_file
        )
        self.install_worker.progress_updated.connect(self.status_label.setText)
        self.install_worker.installation_finished.connect(self.installation_finished)
        self.install_worker.start()
        
    def installation_finished(self, success: bool, message: str):
        self.progress_bar.setVisible(False)
        self.install_btn.setEnabled(True)
        self.requirements_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(message)
            self.install_edit.clear()
            self.load_packages()
        else:
            self.status_label.setText(f"安装失败: {message}")
            QMessageBox.critical(self, "安装失败", message)
            
    def uninstall_package(self, package_name: str):
        reply = QMessageBox.question(
            self, "确认卸载",
            f"确定要卸载包 '{package_name}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                pip_exe = self.manager.get_pip_executable(self.env_info.path)
                result = subprocess.run(
                    [pip_exe, "uninstall", "-y", package_name],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    self.status_label.setText(f"已卸载 {package_name}")
                    self.load_packages()
                else:
                    QMessageBox.critical(self, "卸载失败", result.stderr)
                    
            except Exception as e:
                QMessageBox.critical(self, "卸载失败", str(e))

class VirtualEnvWidget(QWidget):
    environment_activated = Signal(str, dict)
    
    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.manager = VirtualEnvManager()
        self.environments = []
        self.current_env = None
        self.theme_manager = theme_manager
        self.init_ui()
        self.load_environments()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        

        toolbar_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("创建环境")
        self.create_btn.clicked.connect(self.create_environment)
        toolbar_layout.addWidget(self.create_btn)
        
        self.delete_btn = QPushButton("删除环境")
        self.delete_btn.clicked.connect(self.delete_environment)
        toolbar_layout.addWidget(self.delete_btn)
        
        self.activate_btn = QPushButton("激活环境")
        self.activate_btn.clicked.connect(self.activate_environment)
        toolbar_layout.addWidget(self.activate_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.load_environments)
        toolbar_layout.addWidget(self.refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        

        splitter = QSplitter(Qt.Horizontal)
        

        env_widget = QWidget()
        env_layout = QVBoxLayout(env_widget)
        env_layout.addWidget(QLabel("虚拟环境列表:"))
        
        self.env_list = QListWidget()
        self.env_list.currentItemChanged.connect(self.on_env_selected)
        env_layout.addWidget(self.env_list)
        
        splitter.addWidget(env_widget)
        

        self.detail_tabs = QTabWidget()
        

        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        self.detail_tabs.addTab(self.detail_widget, "环境详情")
        
        splitter.addWidget(self.detail_tabs)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
        self.update_buttons()
        
    def load_environments(self):
        self.environments = self.manager.load_environments()
        self.env_list.clear()
        
        for env in self.environments:
            item = QListWidgetItem(env.name)
            item.setData(Qt.UserRole, env)
            

            if not os.path.exists(env.path):
                item.setText(f"{env.name} (不存在)")
                if self.theme_manager:
                    error_color = QColor(self.theme_manager.get_theme_color("error"))
                    item.setForeground(error_color)
                else:
                    item.setForeground(QColor("#dc3545"))
                
            self.env_list.addItem(item)
            
    def create_environment(self):
        dialog = CreateEnvDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, python_path, description = dialog.get_env_info()
            
            if not name:
                QMessageBox.warning(self, "警告", "请输入环境名称")
                return
                

            for env in self.environments:
                if env.name == name:
                    QMessageBox.warning(self, "警告", "环境名称已存在")
                    return
                    

            success, message = self.manager.create_environment(name, python_path, description)
            
            if success:
                QMessageBox.information(self, "成功", f"虚拟环境 '{name}' 创建成功")
                self.load_environments()
            else:
                QMessageBox.critical(self, "创建失败", f"创建虚拟环境 '{name}' 失败:\n\n{message}")
                
    def delete_environment(self):
        current_item = self.env_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要删除的环境")
            return
            
        env = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除虚拟环境 '{env.name}' 吗？\n这将删除所有已安装的包。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.manager.delete_environment(env.name)
            
            if success:
                QMessageBox.information(self, "成功", f"虚拟环境 '{env.name}' 已删除")
                self.load_environments()
                self.detail_text.clear()
                self.current_env = None
                self.update_buttons()
            else:
                QMessageBox.critical(self, "失败", f"删除虚拟环境 '{env.name}' 失败")
                
    def activate_environment(self):
        current_item = self.env_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请选择要激活的环境")
            return
            
        env = current_item.data(Qt.UserRole)
        
        if not os.path.exists(env.path):
            QMessageBox.warning(self, "警告", "虚拟环境路径不存在")
            return
            

        env_vars = self.manager.activate_environment(env.path)
        

        self.environment_activated.emit(env.path, env_vars)
        

        env.last_used = datetime.now().isoformat()
        self.manager.save_environments(self.environments)
        
        QMessageBox.information(self, "成功", f"虚拟环境 '{env.name}' 已激活")
        
    def on_env_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        if not current:
            self.current_env = None
            self.detail_text.clear()
            self.update_buttons()
            return
            
        env = current.data(Qt.UserRole)
        self.current_env = env
        

        details = f"""环境名称: {env.name}
路径: {env.path}
Python版本: {env.python_version}
创建时间: {env.created_time}
最后使用: {env.last_used}
描述: {env.description}

状态: {'存在' if os.path.exists(env.path) else '不存在'}
"""
        
        self.detail_text.setText(details)
        

        if os.path.exists(env.path):

            for i in range(self.detail_tabs.count() - 1, 0, -1):
                self.detail_tabs.removeTab(i)
                

            package_widget = PackageManagerWidget(env)
            self.detail_tabs.addTab(package_widget, "包管理")
            
        self.update_buttons()
        
    def update_buttons(self):
        has_selection = self.current_env is not None
        env_exists = has_selection and os.path.exists(self.current_env.path)
        
        self.delete_btn.setEnabled(has_selection)
        self.activate_btn.setEnabled(env_exists)