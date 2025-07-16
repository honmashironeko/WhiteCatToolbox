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

    try:
        from urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    except (ImportError, AttributeError):

        try:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except (ImportError, AttributeError):
            pass
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

CURRENT_VERSION = "v0.0.6"
GITHUB_MIRRORS = [
    "https://api.github.com",
    "https://gh-api.p3terx.com",
]

FAILED_MIRRORS = set()
RAW_GITHUB_MIRRORS = [
    "https://raw.githubusercontent.com",
    "https://ghproxy.com/https://raw.githubusercontent.com",
    "https://cdn.jsdelivr.net/gh",
    "https://raw.kgithub.com",
    "https://ghps.cc/https://raw.githubusercontent.com",
]

def test_mirror_availability():
    
    print("[调试] 开始测试镜像站点可用性...")
    available_mirrors = []
    
    for mirror in GITHUB_MIRRORS:
        try:
            if REQUESTS_AVAILABLE:
                headers = {'User-Agent': 'WhiteCatToolbox/1.0'}
                response = requests.get(f"{mirror}/repos/octocat/Hello-World", 
                                      headers=headers, timeout=10, verify=False)
                if response.status_code == 200:
                    available_mirrors.append(mirror)
                    print(f"[调试] 镜像可用: {mirror}")
                else:
                    print(f"[调试] 镜像不可用: {mirror}, 状态码: {response.status_code}")
                    FAILED_MIRRORS.add(mirror)
        except Exception as e:
            print(f"[调试] 镜像测试失败: {mirror}, 错误: {e}")
            FAILED_MIRRORS.add(mirror)
    
    print(f"[调试] 可用镜像数量: {len(available_mirrors)}/{len(GITHUB_MIRRORS)}")
    return available_mirrors

def compare_versions(version1, version2):
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
        self.repo_path = "repos/honmashironeko/WhiteCatToolbox/releases/latest"
        
    def _get_repo_url(self, mirror):
        
        if "gitclone.com" in mirror:

            return f"https://gitclone.com/github.com/honmashironeko/WhiteCatToolbox/releases/latest"
        elif "github.store" in mirror:

            return f"{mirror}/honmashironeko/WhiteCatToolbox/releases/latest"
        else:

            return f"{mirror}/{self.repo_path}"
        
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
        
        headers = {
            'User-Agent': 'WhiteCatToolbox/1.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/vnd.github.v3+json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
        }
        session = requests.Session()
        session.headers.update(headers)
        session.verify = True
        if hasattr(ssl, 'create_default_context'):
            session.verify = ssl.create_default_context().check_hostname
        
        last_error = None
        
        for mirror in GITHUB_MIRRORS:

            if mirror in FAILED_MIRRORS:
                print(f"[调试] 跳过已知失败的镜像: {mirror}")
                continue
                
            try:
                repo_url = self._get_repo_url(mirror)
                print(f"[调试] 尝试镜像站点: {mirror}")
                try:
                    response = session.get(repo_url, timeout=30, verify=True)
                except requests.exceptions.SSLError:

                    print(f"[调试] SSL验证失败，尝试不验证证书: {mirror}")
                    response = session.get(repo_url, timeout=30, verify=False)
                
                print(f"[调试] HTTP状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[调试] 成功获取数据，最新版本: {data.get('tag_name', 'Unknown')}")

                    FAILED_MIRRORS.discard(mirror)
                    self._process_response_data(data)
                    return
                elif response.status_code == 403:
                    print(f"[调试] API限制，尝试下一个镜像: {mirror}")
                    continue
                else:
                    raise Exception(f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"[调试] 请求超时，尝试下一个镜像: {mirror}")
                last_error = "请求超时"
                continue
            except requests.exceptions.SSLError as e:
                print(f"[调试] SSL错误，尝试下一个镜像: {mirror}, 错误: {e}")
                last_error = f"SSL连接失败: {str(e)}"
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"[调试] 连接错误，尝试下一个镜像: {mirror}, 错误: {e}")
                last_error = f"网络连接失败: {str(e)}"
                continue
            except json.JSONDecodeError as e:
                print(f"[调试] JSON解析错误，尝试下一个镜像: {mirror}, 错误: {e}")
                last_error = "响应数据解析失败"
                continue
            except Exception as e:
                print(f"[调试] 其他错误，尝试下一个镜像: {mirror}, 错误: {e}")
                FAILED_MIRRORS.add(mirror)
                last_error = str(e)
                continue
        self.check_completed.emit(False, f"所有镜像站点都无法访问: {last_error}")
    
    def _check_with_urllib(self):
        
        headers = {
            'User-Agent': 'WhiteCatToolbox/1.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/vnd.github.v3+json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
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
        
        for mirror in GITHUB_MIRRORS:
            repo_url = self._get_repo_url(mirror)
            print(f"[调试] urllib尝试镜像: {mirror}")
            
            req = urllib.request.Request(repo_url, headers=headers)
            
            for ssl_context in ssl_contexts:
                try:
                    with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode('utf-8'))
                            print(f"[调试] urllib成功获取数据: {mirror}")
                            self._process_response_data(data)
                            return
                        elif response.status == 403:
                            print(f"[调试] urllib API限制: {mirror}")
                            break
                        else:
                            raise Exception(f"HTTP {response.status}")
                            
                except urllib.error.URLError as e:
                    print(f"[调试] urllib URL错误: {mirror}, {e}")
                    last_error = str(e)
                    continue
                except Exception as e:
                    print(f"[调试] urllib其他错误: {mirror}, {e}")
                    last_error = str(e)
                    continue
        self.check_completed.emit(False, f"所有镜像站点都无法访问: {last_error}")
    
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

        title_label.setFont(QFont(get_system_font(), s(16), QFont.Weight.Bold))
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

            release_title.setFont(QFont(get_system_font(), s(13), QFont.Weight.Medium))
            release_title.setStyleSheet(f"color: {colors['text']}; margin: {s(8)}px 0;")
            layout.addWidget(release_title)

        notes_label = QLabel(t("release_notes"))

        notes_label.setFont(QFont(get_system_font(), s(11), QFont.Weight.Medium))
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
        self.promotion_repo_path = "repos/honmashironeko/WhiteCatToolbox/contents/promotion"
        self.promotion_dir = "promotion"
        
    def _get_promotion_url(self, mirror):
        
        if "gitclone.com" in mirror:
            return f"https://gitclone.com/github.com/honmashironeko/WhiteCatToolbox/contents/promotion"
        elif "github.store" in mirror:
            return f"{mirror}/honmashironeko/WhiteCatToolbox/contents/promotion"
        else:
            return f"{mirror}/{self.promotion_repo_path}"
        
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
        
        headers = {
            'User-Agent': 'WhiteCatToolbox/1.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/vnd.github.v3+json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        session = requests.Session()
        session.headers.update(headers)
        
        last_error = None
        
        for mirror in GITHUB_MIRRORS:
            try:
                promotion_url = self._get_promotion_url(mirror)
                print(f"[调试] 推广内容尝试镜像: {mirror}")
                try:
                    response = session.get(promotion_url, timeout=30, verify=True)
                except requests.exceptions.SSLError:
                    print(f"[调试] 推广SSL验证失败，尝试不验证证书: {mirror}")
                    response = session.get(promotion_url, timeout=30, verify=False)
                
                if response.status_code == 404:
                    print(f"[调试] 推广文件夹不存在于镜像: {mirror}")
                    continue
                
                if response.status_code == 200:
                    files_info = response.json()
                    print(f"[调试] 推广成功获取文件列表: {mirror}, 文件数: {len(files_info)}")
                    self._process_promotion_files(files_info, session, mirror)
                    return
                elif response.status_code == 403:
                    print(f"[调试] 推广API限制，尝试下一个镜像: {mirror}")
                    continue
                else:
                    raise Exception(f"HTTP {response.status_code}")
                    
            except requests.exceptions.Timeout:
                print(f"[调试] 推广请求超时，尝试下一个镜像: {mirror}")
                last_error = "请求超时"
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"[调试] 推广连接错误，尝试下一个镜像: {mirror}, 错误: {e}")
                last_error = f"网络连接失败: {str(e)}"
                continue
            except json.JSONDecodeError as e:
                print(f"[调试] 推广JSON解析错误，尝试下一个镜像: {mirror}, 错误: {e}")
                last_error = "响应数据解析失败"
                continue
            except Exception as e:
                print(f"[调试] 推广其他错误，尝试下一个镜像: {mirror}, 错误: {e}")
                last_error = str(e)
                continue
        if last_error:
            self.update_completed.emit(False, f"推广内容更新失败: {last_error}")
        else:
            self.update_completed.emit(True, "推广内容已是最新")
    
    def _process_promotion_files(self, files_info, session, mirror):
        
        if not os.path.exists(self.promotion_dir):
            os.makedirs(self.promotion_dir)
        
        updated_files = []
        for file_info in files_info:
            if file_info.get('type') == 'file':
                file_name = file_info.get('name')
                download_url = file_info.get('download_url')
                remote_sha = file_info.get('sha')
                
                if file_name and download_url:

                    if self._download_and_replace_file(file_name, download_url, session, remote_sha=remote_sha):
                        updated_files.append(file_name)
        
        if updated_files:
            print(f"[调试] 推广成功更新 {len(updated_files)} 个文件: {updated_files}")
            self.update_completed.emit(True, f"推广内容已更新 ({len(updated_files)} 个文件)")
        else:
            print("[调试] 推广内容无需更新")
            self.update_completed.emit(True, "推广内容已是最新")
    
    def _download_and_replace_file(self, file_name, download_url, session, remote_sha=None):
        
        try:
            local_file_path = os.path.join(self.promotion_dir, file_name)
            if os.path.exists(local_file_path) and remote_sha:
                try:
                    with open(local_file_path, 'r', encoding='utf-8') as f:
                        local_content = f.read()
                    
                    import hashlib
                    local_blob = f"blob {len(local_content.encode('utf-8'))}\0{local_content}"
                    local_sha = hashlib.sha1(local_blob.encode('utf-8')).hexdigest()
                    
                    if local_sha == remote_sha:
                        print(f"[调试] 推广文件SHA相同，跳过下载: {file_name}")
                        return False
                except Exception as e:
                    print(f"[调试] 计算本地推广文件SHA失败: {e}")
            download_urls = []
            download_urls.append(download_url)
            if "raw.githubusercontent.com" in download_url:
                for raw_mirror in RAW_GITHUB_MIRRORS[1:]:
                    if raw_mirror == "https://cdn.jsdelivr.net/gh":

                        parts = download_url.replace("https://raw.githubusercontent.com/", "").split("/")
                        if len(parts) >= 3:
                            owner, repo, branch = parts[0], parts[1], parts[2]
                            file_path = "/".join(parts[3:])
                            jsdelivr_url = f"{raw_mirror}/{owner}/{repo}@{branch}/{file_path}"
                            download_urls.append(jsdelivr_url)
                    else:
                        mirror_url = download_url.replace("https://raw.githubusercontent.com", raw_mirror)
                        download_urls.append(mirror_url)
            for url in download_urls:
                try:
                    print(f"[调试] 尝试下载推广文件 {file_name} 从: {url}")
                    try:
                        response = session.get(url, timeout=30, verify=True)
                    except requests.exceptions.SSLError:
                        print(f"[调试] 推广下载SSL失败，尝试不验证: {url}")
                        response = session.get(url, timeout=30, verify=False)
                    
                    if response.status_code == 200:
                        new_content = response.text
                        if os.path.exists(local_file_path):
                            backup_path = f"{local_file_path}.backup"
                            shutil.copy2(local_file_path, backup_path)
                            print(f"[调试] 创建推广文件备份: {backup_path}")
                        with open(local_file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        print(f"[调试] 成功更新推广文件: {file_name}")
                        return True
                    else:
                        print(f"[调试] 推广下载失败: {file_name}, HTTP {response.status_code}")
                        continue
                        
                except Exception as e:
                    print(f"[调试] 推广下载异常 {file_name} from {url}: {e}")
                    continue
            
            print(f"[调试] 所有下载链接都失败: {file_name}")
            return False
            
        except Exception as e:
            print(f"[调试] 推广下载文件失败 {file_name}: {e}")
            return False
    
    def _update_with_urllib(self):
        
        headers = {
            'User-Agent': 'WhiteCatToolbox/1.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/vnd.github.v3+json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
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
        
        for mirror in GITHUB_MIRRORS:
            promotion_url = self._get_promotion_url(mirror)
            print(f"[调试] 推广urllib尝试镜像: {mirror}")
            
            req = urllib.request.Request(promotion_url, headers=headers)
            
            for ssl_context in ssl_contexts:
                try:
                    with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                        if response.status == 200:
                            data = json.loads(response.read().decode('utf-8'))
                            print(f"[调试] 推广urllib成功获取数据: {mirror}")
                            self._process_promotion_files_urllib(data)
                            return
                        elif response.status == 404:
                            print(f"[调试] 推广文件夹不存在: {mirror}")
                            break
                        elif response.status == 403:
                            print(f"[调试] 推广urllib API限制: {mirror}")
                            break
                except:
                    continue
        
        self.update_completed.emit(False, "无法连接到推广内容服务器")
    
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
            local_file_path = os.path.join(self.promotion_dir, file_name)
            download_urls = [download_url]
            
            if "raw.githubusercontent.com" in download_url:
                for raw_mirror in RAW_GITHUB_MIRRORS[1:]:
                    if raw_mirror != "https://cdn.jsdelivr.net/gh":
                        mirror_url = download_url.replace("https://raw.githubusercontent.com", raw_mirror)
                        download_urls.append(mirror_url)
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
            for url in download_urls:
                req = urllib.request.Request(url, headers={'User-Agent': 'WhiteCatToolbox/1.0'})
                
                for ssl_context in ssl_contexts:
                    try:
                        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
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
                                
                                print(f"[调试] urllib成功下载推广文件: {file_name}")
                                return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            print(f"[调试] urllib下载推广文件失败 {file_name}: {e}")
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
                return config.get('ads_enabled', True)
        except Exception as e:
            print(f"[调试] 读取推广配置失败: {e}")
        return True
    
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
        
