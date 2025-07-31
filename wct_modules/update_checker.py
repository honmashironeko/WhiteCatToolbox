
"""
White Cat Toolbox - 自动更新检查器
实现多镜像站点支持、智能容错和版本比较功能
"""

import json
import re
import ssl
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

from PySide6.QtCore import QObject, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QCheckBox, QComboBox, QMessageBox
)
from PySide6.QtGui import QFont

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

class VersionInfo:
    """版本信息类"""
    
    def __init__(self, version_string: str):
        self.version_string = version_string
        self.major, self.minor, self.patch, self.pre_release = self._parse_version(version_string)
        
    def _parse_version(self, version: str) -> Tuple[int, int, int, str]:
        """解析版本字符串"""

        version = version.lstrip('v')
        

        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:[-.]?(alpha|beta|rc|dev)(\d*))?'
        match = re.match(pattern, version, re.IGNORECASE)
        
        if not match:

            return 0, 0, 0, ''
            
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        pre_release = ''
        
        if match.group(4):
            pre_release = match.group(4).lower()
            if match.group(5):
                pre_release += match.group(5)
                
        return major, minor, patch, pre_release
        
    def __lt__(self, other):
        """版本比较：小于"""
        if not isinstance(other, VersionInfo):
            return NotImplemented
            

        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
            

        if not self.pre_release and not other.pre_release:
            return False
        if not self.pre_release and other.pre_release:
            return False
        if self.pre_release and not other.pre_release:
            return True
            

        pre_order = {'dev': 0, 'alpha': 1, 'beta': 2, 'rc': 3}
        self_pre = self.pre_release.rstrip('0123456789')
        other_pre = other.pre_release.rstrip('0123456789')
        
        if self_pre != other_pre:
            return pre_order.get(self_pre, 999) < pre_order.get(other_pre, 999)
            

        self_num = re.search(r'(\d+)$', self.pre_release)
        other_num = re.search(r'(\d+)$', other.pre_release)
        
        if self_num and other_num:
            return int(self_num.group(1)) < int(other_num.group(1))
        elif self_num:
            return False
        elif other_num:
            return True
            
        return False
        
    def __eq__(self, other):
        """版本比较：等于"""
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.pre_release) == \
               (other.major, other.minor, other.patch, other.pre_release)
               
    def __str__(self):
        return self.version_string

class UpdateChecker(QThread):
    """更新检查器线程"""
    

    update_available = Signal(dict)
    no_update = Signal()
    check_failed = Signal(str)
    progress_updated = Signal(str)
    
    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = VersionInfo(current_version)
        self.timeout = 10
        self.max_retries = 3
        

        self.mirror_sites = [
            {
                'name': 'GitHub Releases',
                'url': 'https://api.github.com/repos/whitecatx/wct/releases/latest',
                'parser': self._parse_github_response
            },
            {
                'name': 'GitLab Releases',
                'url': 'https://gitlab.com/api/v4/projects/whitecatx%2Fwct/releases',
                'parser': self._parse_gitlab_response
            },
            {
                'name': 'Gitee Releases',
                'url': 'https://gitee.com/api/v5/repos/whitecatx/wct/releases/latest',
                'parser': self._parse_gitee_response
            }
        ]
        

        self.failure_log = []
        
    def run(self):
        """执行更新检查"""
        self.progress_updated.emit("开始检查更新...")
        
        for site in self.mirror_sites:
            try:
                self.progress_updated.emit(f"正在检查 {site['name']}...")
                
                response_data = self._fetch_with_retry(site['url'])
                if response_data:
                    update_info = site['parser'](response_data)
                    if update_info:
                        latest_version = VersionInfo(update_info['version'])
                        
                        if latest_version > self.current_version:
                            self.progress_updated.emit(f"发现新版本: {latest_version}")
                            update_info['mirror_site'] = site['name']
                            self.update_available.emit(update_info)
                            return
                        else:
                            self.progress_updated.emit("当前版本已是最新")
                            self.no_update.emit()
                            return
                            
            except Exception as e:
                error_msg = f"{site['name']} 检查失败: {str(e)}"
                self.failure_log.append({
                    'site': site['name'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                self.progress_updated.emit(error_msg)
                continue
                

        self.check_failed.emit("所有镜像站点检查失败")
        
    def _fetch_with_retry(self, url: str) -> Optional[dict]:
        """带重试的网络请求"""
        for attempt in range(self.max_retries):
            try:
                if HAS_REQUESTS:
                    return self._fetch_with_requests(url)
                else:
                    return self._fetch_with_urllib(url)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(1)
                
        return None
        
    def _fetch_with_requests(self, url: str) -> dict:
        """使用 requests 库获取数据"""
        headers = {
            'User-Agent': 'White Cat Toolbox Update Checker',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
        response.raise_for_status()
        return response.json()
        
    def _fetch_with_urllib(self, url: str) -> dict:
        """使用 urllib 库获取数据"""

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'White Cat Toolbox Update Checker',
                'Accept': 'application/json'
            }
        )
        
        with urllib.request.urlopen(req, timeout=self.timeout, context=context) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
            
    def _parse_github_response(self, data: dict) -> Optional[dict]:
        """解析 GitHub API 响应"""
        try:
            return {
                'version': data['tag_name'],
                'name': data['name'],
                'description': data['body'],
                'download_url': data['html_url'],
                'published_at': data['published_at'],
                'assets': [{
                    'name': asset['name'],
                    'download_url': asset['browser_download_url'],
                    'size': asset['size']
                } for asset in data.get('assets', [])]
            }
        except KeyError as e:
            raise ValueError(f"GitHub API 响应格式错误: {e}")
            
    def _parse_gitlab_response(self, data: dict) -> Optional[dict]:
        """解析 GitLab API 响应"""
        try:
            if isinstance(data, list) and len(data) > 0:
                latest = data[0]
            else:
                latest = data
                
            return {
                'version': latest['tag_name'],
                'name': latest['name'],
                'description': latest['description'],
                'download_url': latest['_links']['self'],
                'published_at': latest['released_at'],
                'assets': []
            }
        except KeyError as e:
            raise ValueError(f"GitLab API 响应格式错误: {e}")
            
    def _parse_gitee_response(self, data: dict) -> Optional[dict]:
        """解析 Gitee API 响应"""
        try:
            return {
                'version': data['tag_name'],
                'name': data['name'],
                'description': data['body'],
                'download_url': data['html_url'],
                'published_at': data['created_at'],
                'assets': [{
                    'name': asset['name'],
                    'download_url': asset['browser_download_url']
                } for asset in data.get('assets', [])]
            }
        except KeyError as e:
            raise ValueError(f"Gitee API 响应格式错误: {e}")
            
    def get_failure_log(self) -> List[dict]:
        """获取失败记录"""
        return self.failure_log.copy()

class UpdateDialog(QDialog):
    """更新对话框"""
    
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("发现新版本")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        

        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("新版本:"))
        
        version_label = QLabel(self.update_info['version'])
        version_label.setProperty("class", "version_label")
        info_layout.addWidget(version_label)
        
        info_layout.addStretch()
        
        mirror_label = QLabel(f"来源: {self.update_info.get('mirror_site', '未知')}")
        info_layout.addWidget(mirror_label)
        
        layout.addLayout(info_layout)
        

        if 'published_at' in self.update_info:
            time_label = QLabel(f"发布时间: {self.update_info['published_at']}")
            layout.addWidget(time_label)
            

        layout.addWidget(QLabel("更新说明:"))
        
        description_text = QTextEdit()
        description_text.setReadOnly(True)
        description_text.setMaximumHeight(200)
        description_text.setPlainText(self.update_info.get('description', '暂无更新说明'))
        layout.addWidget(description_text)
        

        if self.update_info.get('assets'):
            layout.addWidget(QLabel("下载文件:"))
            
            assets_text = QTextEdit()
            assets_text.setReadOnly(True)
            assets_text.setMaximumHeight(100)
            
            assets_info = []
            for asset in self.update_info['assets']:
                size_info = f" ({asset['size']} bytes)" if 'size' in asset else ""
                assets_info.append(f"• {asset['name']}{size_info}")
                
            assets_text.setPlainText('\n'.join(assets_info))
            layout.addWidget(assets_text)
            

        self.auto_check = QCheckBox("启动时自动检查更新")
        self.auto_check.setChecked(True)
        layout.addWidget(self.auto_check)
        

        button_layout = QHBoxLayout()
        
        download_btn = QPushButton("下载更新")
        download_btn.clicked.connect(self.download_update)
        button_layout.addWidget(download_btn)
        
        later_btn = QPushButton("稍后提醒")
        later_btn.clicked.connect(self.remind_later)
        button_layout.addWidget(later_btn)
        
        ignore_btn = QPushButton("忽略此版本")
        ignore_btn.clicked.connect(self.ignore_version)
        button_layout.addWidget(ignore_btn)
        
        layout.addLayout(button_layout)
        
    def download_update(self):
        """下载更新"""
        import webbrowser
        webbrowser.open(self.update_info['download_url'])
        self.accept()
        
    def remind_later(self):
        """稍后提醒"""
        self.accept()
        
    def ignore_version(self):
        """忽略此版本"""

        self.reject()
        
    def is_auto_check_enabled(self) -> bool:
        """是否启用自动检查"""
        return self.auto_check.isChecked()

class UpdateManager(QObject):
    """更新管理器"""
    

    update_available = Signal(dict)
    update_check_failed = Signal(str)
    
    def __init__(self, current_version: str, config_manager=None, parent=None):
        super().__init__(parent)
        self.current_version = current_version
        self.config_manager = config_manager
        self.checker_thread = None
        

        self.auto_check_timer = QTimer()
        self.auto_check_timer.timeout.connect(self.check_for_updates)
        

        self.load_config()
        
    def load_config(self):
        """加载配置"""
        if self.config_manager:
            config = self.config_manager.get_config()
            self.auto_check_enabled = config.get('auto_check_updates', True)
            self.check_interval = config.get('update_check_interval', 24)
            self.ignored_versions = config.get('ignored_versions', [])
        else:
            self.auto_check_enabled = True
            self.check_interval = 24
            self.ignored_versions = []
            
    def save_config(self):
        """保存配置"""
        if self.config_manager:
            config = self.config_manager.get_config()
            config['auto_check_updates'] = self.auto_check_enabled
            config['update_check_interval'] = self.check_interval
            config['ignored_versions'] = self.ignored_versions
            self.config_manager.save_config(config)
            
    def start_auto_check(self):
        """启动自动检查"""
        if self.auto_check_enabled:

            interval_ms = self.check_interval * 60 * 60 * 1000
            self.auto_check_timer.start(interval_ms)
            
    def stop_auto_check(self):
        """停止自动检查"""
        self.auto_check_timer.stop()
        
    def check_for_updates(self, show_no_update=False):
        """检查更新"""
        if self.checker_thread and self.checker_thread.isRunning():
            return
            
        self.checker_thread = UpdateChecker(self.current_version)
        self.checker_thread.update_available.connect(
            lambda info: self._on_update_available(info, show_no_update)
        )
        self.checker_thread.no_update.connect(
            lambda: self._on_no_update(show_no_update)
        )
        self.checker_thread.check_failed.connect(self._on_check_failed)
        
        self.checker_thread.start()
        
    def _on_update_available(self, update_info: dict, show_dialog=True):
        """处理有更新可用"""
        version = update_info['version']
        

        if version in self.ignored_versions:
            return
            

        self.update_available.emit(update_info)
            
        if show_dialog:
            dialog = UpdateDialog(update_info)
            result = dialog.exec()
            

            self.auto_check_enabled = dialog.is_auto_check_enabled()
            self.save_config()
            

            if result == QDialog.Rejected:
                self.ignored_versions.append(version)
                self.save_config()
                
    def _on_no_update(self, show_message=False):
        """处理无更新"""
        if show_message:
            QMessageBox.information(
                None, "检查更新", "当前版本已是最新版本。"
            )
            
    def _on_check_failed(self, error_message: str):
        """处理检查失败"""

        self.update_check_failed.emit(error_message)
        
        QMessageBox.warning(
            None, "检查更新失败", f"无法检查更新：{error_message}"
        )
        
    def set_auto_check_enabled(self, enabled: bool):
        """设置自动检查"""
        self.auto_check_enabled = enabled
        self.save_config()
        
        if enabled:
            self.start_auto_check()
        else:
            self.stop_auto_check()
            
    def set_check_interval(self, hours: int):
        """设置检查间隔"""
        self.check_interval = hours
        self.save_config()
        
        if self.auto_check_enabled:
            self.stop_auto_check()
            self.start_auto_check()