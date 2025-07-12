import json
import re
import os
import shutil
import tempfile
import zipfile
from PySide6.QtCore import QThread, QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl
from .i18n import t
from .theme import colors, params
from .utils import get_system_font, s

try:
    import requests

    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import urllib.request
    import urllib.error
    import ssl
    URLLIB_AVAILABLE = True
except ImportError:
    URLLIB_AVAILABLE = False


CURRENT_VERSION = "v0.0.2_beta"

def compare_versions(version1, version2):
    """
    比较两个版本号
    返回值: 1表示version1更新, -1表示version2更新, 0表示相同
    """
    def normalize_version(v):

        v = re.sub(r'^v', '', v)
        v = re.sub(r'[_-](alpha|beta|rc).*$', '', v)
        return [int(x) for x in v.split('.') if x.isdigit()]
    
    v1_parts = normalize_version(version1)
    v2_parts = normalize_version(version2)
    

    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))
    
    for i in range(max_len):
        if v1_parts[i] > v2_parts[i]:
            return 1
        elif v1_parts[i] < v2_parts[i]:
            return -1
    
    return 0

class UpdateChecker(QThread):
    
    
    update_found = Signal(dict)
    check_completed = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.repo_url = "https://api.github.com/repos/honmashironeko/WhiteCatToolbox/releases/latest"
        
    def run(self):
        
        try:
            self.check_for_updates()
        except Exception as e:
            self.check_completed.emit(False, str(e))
    
    def check_for_updates(self):
        
        

        if REQUESTS_AVAILABLE:
            return self._check_with_requests()
        elif URLLIB_AVAILABLE:
            return self._check_with_urllib()
        else:
            self.check_completed.emit(False, "网络库不可用，请安装requests模块")
            return
    
    def _check_with_requests(self):
        
        try:
            headers = {
                'User-Agent': 'WhiteCatToolbox/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            print(f"[调试] 正在检查更新: {self.repo_url}")
            

            response = requests.get(
                self.repo_url, 
                headers=headers, 
                timeout=20,
                verify=True
            )
            
            print(f"[调试] HTTP状态码: {response.status_code}")
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            data = response.json()
            print(f"[调试] 成功获取数据，最新版本: {data.get('tag_name', 'Unknown')}")
            self._process_response_data(data)
            
        except requests.exceptions.SSLError as e:
            print(f"[调试] SSL错误，尝试不验证证书: {e}")

            try:
                response = requests.get(
                    self.repo_url, 
                    headers=headers, 
                    timeout=20,
                    verify=False
                )
                
                print(f"[调试] 不验证SSL后状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[调试] 不验证SSL成功，最新版本: {data.get('tag_name', 'Unknown')}")
                    self._process_response_data(data)
                else:
                    self.check_completed.emit(False, f"HTTP错误: {response.status_code}")
                    
            except Exception as e2:
                print(f"[调试] 完全失败: {e2}")
                self.check_completed.emit(False, f"SSL连接失败: {str(e)}")
                
        except requests.exceptions.Timeout:
            print("[调试] 请求超时")
            self.check_completed.emit(False, "请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError as e:
            print(f"[调试] 连接错误: {e}")
            self.check_completed.emit(False, f"网络连接失败: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"[调试] 请求异常: {e}")
            self.check_completed.emit(False, f"请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"[调试] JSON解析错误: {e}")
            self.check_completed.emit(False, "响应数据解析失败")
        except Exception as e:
            print(f"[调试] 未知错误: {e}")
            self.check_completed.emit(False, f"检查更新失败: {str(e)}")
    
    def _check_with_urllib(self):
        
        try:

            req = urllib.request.Request(
                self.repo_url,
                headers={
                    'User-Agent': 'WhiteCatToolbox/1.0',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            

            ssl_contexts = []
            

            try:
                ssl_context1 = ssl.create_default_context()
                ssl_contexts.append(ssl_context1)
            except:
                pass
            

            try:
                ssl_context2 = ssl.create_default_context()
                ssl_context2.check_hostname = False
                ssl_context2.verify_mode = ssl.CERT_NONE
                ssl_contexts.append(ssl_context2)
            except:
                pass
            

            last_error = None
            for ssl_context in ssl_contexts:
                try:
                    with urllib.request.urlopen(req, context=ssl_context, timeout=20) as response:
                        if response.status != 200:
                            raise Exception(f"HTTP {response.status}")
                        
                        data = json.loads(response.read().decode('utf-8'))
                        self._process_response_data(data)
                        return
                        
                except urllib.error.URLError as e:
                    last_error = e
                    continue
                except Exception as e:
                    last_error = e
                    continue
            

            if last_error:
                if isinstance(last_error, urllib.error.URLError):
                    if "SSL" in str(last_error.reason):
                        self.check_completed.emit(False, f"SSL连接失败: {last_error.reason}")
                    else:
                        self.check_completed.emit(False, f"网络连接失败: {last_error.reason}")
                else:
                    self.check_completed.emit(False, f"检查更新失败: {str(last_error)}")
            else:
                self.check_completed.emit(False, "无法建立连接")
                    
        except json.JSONDecodeError:
            self.check_completed.emit(False, "响应数据解析失败")
        except Exception as e:
            self.check_completed.emit(False, f"检查更新失败: {str(e)}")
    
    def _process_response_data(self, data):
        

        latest_version = data.get('tag_name', '')
        release_name = data.get('name', '')
        release_notes = data.get('body', '')
        download_url = data.get('html_url', '')
        published_at = data.get('published_at', '')
        
        print(f"[调试] 版本比较: 最新={latest_version}, 当前={CURRENT_VERSION}")
        

        comparison_result = compare_versions(latest_version, CURRENT_VERSION)
        print(f"[调试] 比较结果: {comparison_result}")
        
        if comparison_result > 0:

            print("[调试] 发现新版本！")
            update_info = {
                'latest_version': latest_version,
                'current_version': CURRENT_VERSION,
                'release_name': release_name,
                'release_notes': release_notes,
                'download_url': download_url,
                'published_at': published_at
            }
            self.update_found.emit(update_info)
        else:

            print("[调试] 当前已是最新版本")
            self.check_completed.emit(True, "当前已是最新版本")

class UpdateNotificationDialog(QDialog):
    
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setup_ui()
        
    def setup_ui(self):
        
        self.setWindowTitle(t("update_available"))
        self.setFixedSize(s(500), s(400))
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(20), s(20), s(20), s(20))
        layout.setSpacing(s(16))
        

        title_label = QLabel("🎉 " + t("new_version_available"))
        title_label.setFont(QFont(get_system_font(), s(16), QFont.Bold))
        title_label.setStyleSheet(f"color: {colors['primary']}; margin-bottom: {s(8)}px;")
        layout.addWidget(title_label)
        

        version_layout = QHBoxLayout()
        version_layout.setSpacing(s(20))
        
        current_label = QLabel(f"{t('current_version')}: {self.update_info['current_version']}")
        current_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: {s(12)}pt;")
        
        latest_label = QLabel(f"{t('latest_version')}: {self.update_info['latest_version']}")
        latest_label.setStyleSheet(f"color: {colors['success']}; font-size: {s(12)}pt; font-weight: bold;")
        
        version_layout.addWidget(current_label)
        version_layout.addStretch()
        version_layout.addWidget(latest_label)
        layout.addLayout(version_layout)
        

        if self.update_info.get('release_name'):
            release_title = QLabel(f"📦 {self.update_info['release_name']}")
            release_title.setFont(QFont(get_system_font(), s(13), QFont.Medium))
            release_title.setStyleSheet(f"color: {colors['text']}; margin: {s(8)}px 0;")
            layout.addWidget(release_title)
        

        notes_label = QLabel(t("release_notes"))
        notes_label.setFont(QFont(get_system_font(), s(11), QFont.Medium))
        notes_label.setStyleSheet(f"color: {colors['text']}; margin-top: {s(8)}px;")
        layout.addWidget(notes_label)
        

        release_notes = QTextEdit()
        release_notes.setPlainText(self.update_info.get('release_notes', t('no_release_notes')))
        release_notes.setReadOnly(True)
        release_notes.setMaximumHeight(s(150))
        release_notes.setStyleSheet(f"""
            QTextEdit {{
                background: {colors['background_very_light']};
                border: 1px solid {colors['border_light']};
                border-radius: {params['border_radius_small']};
                padding: {s(8)}px;
                font-size: {s(9)}pt;
                color: {colors['text_secondary']};
            }}
        """)
        layout.addWidget(release_notes)
        

        button_layout = QHBoxLayout()
        button_layout.setSpacing(s(12))
        

        later_btn = QPushButton(t("remind_later"))
        later_btn.setMinimumSize(s(100), s(36))
        later_btn.setStyleSheet(f"""
            QPushButton {{
                background: {colors['background_light']};
                border: 1px solid {colors['border']};
                border-radius: {params['border_radius_small']};
                color: {colors['text_secondary']};
                font-weight: 500;
                font-size: {s(10)}pt;
                padding: {s(8)}px {s(16)}px;
            }}
            QPushButton:hover {{
                background: {colors['border']};
                border-color: {colors['secondary']};
                color: {colors['text']};
            }}
        """)
        later_btn.clicked.connect(self.reject)
        

        download_btn = QPushButton("🔽 " + t("download_update"))
        download_btn.setMinimumSize(s(120), s(36))
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 {colors['primary']}, 
                                          stop: 1 {colors['primary_hover']});
                border: none;
                border-radius: {params['border_radius_small']};
                color: {colors['text_on_primary']};
                font-weight: 600;
                font-size: {s(10)}pt;
                padding: {s(8)}px {s(16)}px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 {colors['primary_hover']}, 
                                          stop: 1 {colors['primary_pressed']});
            }}
        """)
        download_btn.clicked.connect(self.open_download_page)
        
        button_layout.addStretch()
        button_layout.addWidget(later_btn)
        button_layout.addWidget(download_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        

        self.setStyleSheet(f"""
            QDialog {{
                background: {colors['white']};
                border-radius: {params['border_radius']};
            }}
        """)
    
    def open_download_page(self):
        
        if self.update_info.get('download_url'):
            QDesktopServices.openUrl(QUrl(self.update_info['download_url']))
        self.accept()

class UpdateManager(QObject):
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.checker = None
        
    def check_for_updates(self, show_no_update_message=True):
        
        if self.checker and self.checker.isRunning():
            return
            
        self.checker = UpdateChecker()
        self.checker.update_found.connect(self.on_update_found)
        self.checker.check_completed.connect(
            lambda success, message: self.on_check_completed(success, message, show_no_update_message)
        )
        self.checker.start()
    
    def on_update_found(self, update_info):
        
        dialog = UpdateNotificationDialog(update_info, self.parent_window)
        dialog.exec()
    
    def on_check_completed(self, success, message, show_no_update_message):
        
        if not success:

            QMessageBox.warning(
                self.parent_window,
                t("update_check_failed"),
                f"{t('update_check_error')}: {message}"
            )
        elif show_no_update_message and "最新版本" in message:

            QMessageBox.information(
                self.parent_window,
                t("update_check"),
                t("already_latest_version")
            )
    
    def check_for_updates_on_startup(self):
        
        QTimer.singleShot(3000, lambda: self.check_for_updates(show_no_update_message=False))
    
class PromotionUpdateChecker(QThread):
    
    
    update_completed = Signal(bool, str)
    
    def __init__(self):
        super().__init__()

        self.promotion_repo_url = "https://api.github.com/repos/honmashironeko/WhiteCatToolbox/contents/promotion"
        self.promotion_download_base = "https://raw.githubusercontent.com/honmashironeko/WhiteCatToolbox/main/promotion/"
        self.promotion_dir = "promotion"
        
    def run(self):
        
        try:
            self.check_and_update_promotion()
        except Exception as e:
            print(f"[调试] 推广更新检查异常: {e}")
            self.update_completed.emit(False, f"推广更新检查失败: {str(e)}")
    
    def check_and_update_promotion(self):
        
        print("[调试] 开始检查推广内容更新...")
        
        if REQUESTS_AVAILABLE:
            self._update_with_requests()
        elif URLLIB_AVAILABLE:
            self._update_with_urllib()
        else:
            self.update_completed.emit(False, "网络库不可用")
    
    def _update_with_requests(self):
        
        try:
            headers = {
                'User-Agent': 'WhiteCatToolbox/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            print(f"[调试] 正在获取推广文件列表: {self.promotion_repo_url}")
            

            response = requests.get(
                self.promotion_repo_url,
                headers=headers,
                timeout=20,
                verify=True
            )
            
            if response.status_code == 404:
                print("[调试] 远程promotion文件夹不存在，跳过更新")
                self.update_completed.emit(True, "推广内容已是最新")
                return
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            files_info = response.json()
            print(f"[调试] 发现 {len(files_info)} 个推广文件")
            

            if not os.path.exists(self.promotion_dir):
                os.makedirs(self.promotion_dir)
                print(f"[调试] 创建推广文件夹: {self.promotion_dir}")
            
            updated_files = []
            

            for file_info in files_info:
                if file_info.get('type') == 'file':
                    file_name = file_info.get('name')
                    download_url = file_info.get('download_url')
                    
                    if file_name and download_url:
                        if self._download_and_replace_file(file_name, download_url, headers):
                            updated_files.append(file_name)
            
            if updated_files:
                print(f"[调试] 成功更新 {len(updated_files)} 个推广文件: {updated_files}")
                self.update_completed.emit(True, f"推广内容已更新 ({len(updated_files)} 个文件)")
            else:
                print("[调试] 推广内容无需更新")
                self.update_completed.emit(True, "推广内容已是最新")
                
        except requests.exceptions.SSLError as e:
            print(f"[调试] SSL错误，尝试不验证证书: {e}")
            try:

                response = requests.get(
                    self.promotion_repo_url,
                    headers=headers,
                    timeout=20,
                    verify=False
                )

                if response.status_code == 200:
                    files_info = response.json()
                    self._process_promotion_files(files_info, headers, verify=False)
                else:
                    self.update_completed.emit(False, f"获取推广文件列表失败: HTTP {response.status_code}")
            except Exception as e2:
                self.update_completed.emit(False, f"推广内容更新失败: {str(e)}")
                
        except Exception as e:
            print(f"[调试] 推广更新失败: {e}")
            self.update_completed.emit(False, f"推广内容更新失败: {str(e)}")
    
    def _process_promotion_files(self, files_info, headers, verify=True):
        
        if not os.path.exists(self.promotion_dir):
            os.makedirs(self.promotion_dir)
        
        updated_files = []
        for file_info in files_info:
            if file_info.get('type') == 'file':
                file_name = file_info.get('name')
                download_url = file_info.get('download_url')
                
                if file_name and download_url:
                    if self._download_and_replace_file(file_name, download_url, headers, verify):
                        updated_files.append(file_name)
        
        if updated_files:
            self.update_completed.emit(True, f"推广内容已更新 ({len(updated_files)} 个文件)")
        else:
            self.update_completed.emit(True, "推广内容已是最新")
    
    def _download_and_replace_file(self, file_name, download_url, headers, verify=True):
        
        try:
            local_file_path = os.path.join(self.promotion_dir, file_name)
            
            print(f"[调试] 正在下载推广文件: {file_name}")
            

            response = requests.get(
                download_url,
                headers=headers,
                timeout=20,
                verify=verify
            )
            
            if response.status_code != 200:
                print(f"[调试] 下载失败: {file_name}, HTTP {response.status_code}")
                return False
            
            new_content = response.text
            

            if os.path.exists(local_file_path):
                try:
                    with open(local_file_path, 'r', encoding='utf-8') as f:
                        current_content = f.read()
                    
                    if current_content == new_content:
                        print(f"[调试] 文件内容相同，跳过: {file_name}")
                        return False
                except:

                    pass
            

            if os.path.exists(local_file_path):
                backup_path = f"{local_file_path}.backup"
                shutil.copy2(local_file_path, backup_path)
                print(f"[调试] 创建备份: {backup_path}")
            

            with open(local_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"[调试] 成功更新推广文件: {file_name}")
            return True
            
        except Exception as e:
            print(f"[调试] 下载推广文件失败 {file_name}: {e}")
            return False
    
    def _update_with_urllib(self):
        
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(
                self.promotion_repo_url,
                headers={
                    'User-Agent': 'WhiteCatToolbox/1.0',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            

            ssl_contexts = []
            try:
                ssl_context1 = ssl.create_default_context()
                ssl_contexts.append(ssl_context1)
            except:
                pass
            
            try:
                ssl_context2 = ssl.create_default_context()
                ssl_context2.check_hostname = False
                ssl_context2.verify_mode = ssl.CERT_NONE
                ssl_contexts.append(ssl_context2)
            except:
                pass
            
            for ssl_context in ssl_contexts:
                try:
                    with urllib.request.urlopen(req, context=ssl_context, timeout=20) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode('utf-8'))
                            self._process_promotion_files_urllib(data)
                            return
                        elif response.status == 404:
                            self.update_completed.emit(True, "推广内容已是最新")
                            return
                except:
                    continue
            
            self.update_completed.emit(False, "无法连接到推广内容服务器")
            
        except Exception as e:
            self.update_completed.emit(False, f"推广内容更新失败: {str(e)}")
    
    def _process_promotion_files_urllib(self, files_info):
        
        if not os.path.exists(self.promotion_dir):
            os.makedirs(self.promotion_dir)
        
        updated_files = []
        for file_info in files_info:
            if file_info.get('type') == 'file':
                file_name = file_info.get('name')
                download_url = file_info.get('download_url')
                
                if file_name and download_url:
                    if self._download_file_urllib(file_name, download_url):
                        updated_files.append(file_name)
        
        if updated_files:
            self.update_completed.emit(True, f"推广内容已更新 ({len(updated_files)} 个文件)")
        else:
            self.update_completed.emit(True, "推广内容已是最新")
    
    def _download_file_urllib(self, file_name, download_url):
        
        try:
            import urllib.request
            
            local_file_path = os.path.join(self.promotion_dir, file_name)
            
            req = urllib.request.Request(
                download_url,
                headers={'User-Agent': 'WhiteCatToolbox/1.0'}
            )
            
            ssl_contexts = []
            try:
                ssl_context1 = ssl.create_default_context()
                ssl_contexts.append(ssl_context1)
            except:
                pass
            
            try:
                ssl_context2 = ssl.create_default_context()
                ssl_context2.check_hostname = False
                ssl_context2.verify_mode = ssl.CERT_NONE
                ssl_contexts.append(ssl_context2)
            except:
                pass
            
            for ssl_context in ssl_contexts:
                try:
                    with urllib.request.urlopen(req, context=ssl_context, timeout=20) as response:
                        if response.status == 200:
                            new_content = response.read().decode('utf-8')
                            

                            if os.path.exists(local_file_path):
                                try:
                                    with open(local_file_path, 'r', encoding='utf-8') as f:
                                        current_content = f.read()
                                    if current_content == new_content:
                                        return False
                                except:
                                    pass
                            

                            if os.path.exists(local_file_path):
                                backup_path = f"{local_file_path}.backup"
                                shutil.copy2(local_file_path, backup_path)
                            
                            with open(local_file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"[调试] urllib下载失败 {file_name}: {e}")
            return False


class PromotionUpdateManager(QObject):
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.checker = None
        
    def check_promotion_enabled(self):
        
        try:
            config_path = "promotion_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('ads_enabled', False)
        except Exception as e:
            print(f"[调试] 读取推广配置失败: {e}")
        return False
    
    def check_for_promotion_updates(self):
        
        if not self.check_promotion_enabled():
            print("[调试] 推广页面未开启，跳过推广内容更新检查")
            return
        
        if self.checker and self.checker.isRunning():
            print("[调试] 推广更新检查已在运行中")
            return
        
        print("[调试] 开始推广内容更新检查...")
        self.checker = PromotionUpdateChecker()
        self.checker.update_completed.connect(self.on_promotion_update_completed)
        self.checker.start()
    
    def on_promotion_update_completed(self, success, message):
        
        if success:
            print(f"[调试] 推广内容更新成功: {message}")
        else:
            print(f"[调试] 推广内容更新失败: {message}")
        
