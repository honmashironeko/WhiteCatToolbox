import os
import json
import platform
import shutil
import datetime
import subprocess
import zipfile
from PySide6.QtWidgets import (
    QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QListWidget,
    QTabWidget, QLabel, QPushButton, QSplitter, QFrame, QMenu,
    QFileDialog, QMessageBox, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QBrush, QColor
from .theme import colors, fonts, params
from .styles import (
    get_main_window_style, get_splitter_style, get_panel_style,
    get_title_panel_style, get_title_label_style, get_list_panel_style,
    get_tool_list_style, get_icon_button_style
)
from .tool_operation import ToolOperationPage
from .promotion import PromotionPage
from .config import ToolConfigParser
from . import utils
from .utils import s, get_system_font
from .i18n import t, init_i18n, set_language, get_current_language, get_available_languages

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tool_pages = {}
        self.promotion_page = PromotionPage()
        self.i18n = init_i18n()
        self.setup_ui()
        self.init_tools()
    
    def setup_ui(self):
        self.setWindowTitle(t("window.title"))
        self.setGeometry(0, 0, 1200, 800)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setStyleSheet(get_main_window_style())
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.setCentralWidget(scroll_area)

        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background: transparent; }")
        scroll_area.setWidget(central_widget)
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setStyleSheet(get_splitter_style())
        left_widget = self.create_tool_list()
        main_splitter.addWidget(left_widget)
        self.right_stack = QTabWidget()
        self.right_stack.setTabsClosable(False)
        self.right_stack.tabBar().hide()  
        self.right_stack.setStyleSheet("""
            QTabWidget { background: transparent; }
            QTabWidget::pane { background: transparent; border: none; }
        """)
        self.right_stack.addTab(self.promotion_page, t("window.promotion"))
        
        main_splitter.addWidget(self.right_stack)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 5)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(int(params["main_margin"]), int(params["main_margin"]), int(params["main_margin"]), int(params["main_margin"]))
        layout.setSpacing(int(params["main_spacing"]))
        layout.addWidget(main_splitter)
        central_widget.setLayout(layout)
    
    def create_tool_list(self):
        
        widget = QWidget()
        widget.setStyleSheet(get_panel_style())
        layout = QVBoxLayout()
        layout.setContentsMargins(int(params["main_margin"]), int(params["main_margin"]), int(params["main_margin"]), int(params["main_margin"]))
        layout.setSpacing(12)
        title_widget = QWidget()
        title_widget.setStyleSheet(get_title_panel_style())
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(8, 8, 8, 8)
        title_label = QLabel(t("window.tool_list"))
        title_label.setFont(QFont(fonts["system"], s(12), QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        title_label.setStyleSheet(get_title_label_style())
        title_layout.addWidget(title_label)
        
        title_button_layout = self.create_enhanced_control_panel()

        title_layout.addLayout(title_button_layout)
        title_widget.setLayout(title_layout)
        layout.addWidget(title_widget)
        list_widget = QWidget()
        list_widget.setStyleSheet(get_list_panel_style())
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(8, 8, 8, 8)
        
        self.tool_list = QListWidget()
        self.tool_list.currentRowChanged.connect(self.on_tool_selected)
        
        self.tool_list.setSelectionMode(QListWidget.SingleSelection)
        
        self.tool_list.itemClicked.connect(self.on_item_clicked)
        
        self.tool_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tool_list.customContextMenuRequested.connect(self.show_tool_list_context_menu)
        self.tool_list.setStyleSheet(get_tool_list_style())
        
        list_layout.addWidget(self.tool_list)
        list_widget.setLayout(list_layout)
        layout.addWidget(list_widget)
        
        widget.setLayout(layout)
        return widget
    
    def create_enhanced_control_panel(self):
        
        main_layout = QHBoxLayout()
        main_layout.setSpacing(s(8))
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        home_btn = QPushButton(" 🏠 ")
        home_btn.setFixedHeight(s(32))
        home_btn.setMinimumWidth(s(50))
        home_btn.setToolTip(t("buttons.home_tooltip"))
        home_btn.setCursor(Qt.PointingHandCursor)
        home_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #4a90e2;
                border: none;
                border-radius: {s(6)}px;
                color: white;
                font-weight: 600;
                font-size: {s(12)}pt;
                padding: {s(6)}px {s(12)}px;
            }}
            QPushButton:hover {{
                background-color: #357abd;
            }}
            QPushButton:pressed {{
                background-color: #2c5aa0;
            }}
        """)
        home_btn.clicked.connect(self.clear_selection)
        main_layout.addWidget(home_btn)
        self.lang_btn = QPushButton("🌐")
        self.lang_btn.setFixedHeight(s(32))
        self.lang_btn.setMinimumWidth(s(50))
        self.lang_btn.setToolTip(t("buttons.language"))
        self.lang_btn.setCursor(Qt.PointingHandCursor)
        self.lang_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #28a745;
                border: none;
                border-radius: {s(6)}px;
                color: white;
                font-weight: 600;
                font-size: {s(12)}pt;
                padding: {s(6)}px {s(12)}px;
            }}
            QPushButton:hover {{
                background-color: #218838;
            }}
            QPushButton:pressed {{
                background-color: #1e7e34;
            }}
        """)
        self.lang_btn.clicked.connect(self.show_language_menu)
        main_layout.addWidget(self.lang_btn)
        
        main_layout.addStretch()
        
        current_scale = f"{int(utils.SCALE_FACTOR * 100)}%"
        self.scale_btn = QPushButton(f"⚡ {current_scale}")
        self.scale_btn.setFixedHeight(s(32))
        self.scale_btn.setMinimumWidth(s(80))
        self.scale_btn.setToolTip(t("buttons.scale_tooltip"))
        self.scale_btn.setCursor(Qt.PointingHandCursor)
        self.scale_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #6c757d;
                border: none;
                border-radius: {s(6)}px;
                color: white;
                font-weight: 600;
                font-size: {s(10)}pt;
                padding: {s(6)}px {s(12)}px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: #545b62;
            }}
            QPushButton:pressed {{
                background-color: #495057;
            }}
        """)
        self.scale_btn.clicked.connect(self.show_scale_menu)
        main_layout.addWidget(self.scale_btn)
        
        return main_layout
    
    def show_scale_menu(self):
        
        menu = QMenu(self)
        menu.setFont(QFont(fonts["system"], s(10)))
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: {s(8)}px;
                padding: {s(6)}px;
                font-weight: 500;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: {s(8)}px {s(16)}px;
                border-radius: {s(4)}px;
                color: #495057;
                min-width: {s(100)}px;
            }}
            QMenu::item:selected {{
                background-color: #4a90e2;
                color: white;
            }}
            QMenu::item:disabled {{
                color: #6c757d;
                background-color: #f8f9fa;
            }}
        """)
        
        scale_options = [
            ("75%", t("scale.modes.75%")),
            ("100%", t("scale.modes.100%")), 
            ("125%", t("scale.modes.125%")),
            ("150%", t("scale.modes.150%")),
            ("175%", t("scale.modes.175%")),
            ("200%", t("scale.modes.200%"))
        ]
        
        current_scale = f"{int(utils.SCALE_FACTOR * 100)}%"
        
        for scale, description in scale_options:
            action_text = f"⚡ {scale} - {description}"
            if scale == current_scale:
                action_text = f"✓ {scale} - {description} ({t('scale.current')})"
            
            action = menu.addAction(action_text)
            if scale == current_scale:
                action.setEnabled(False)
            else:
                action.triggered.connect(lambda checked, s=scale: self.on_scale_changed(s))

        button_pos = self.scale_btn.mapToGlobal(self.scale_btn.rect().bottomLeft())
        menu.exec(button_pos)
    
    def show_language_menu(self):
        
        menu = QMenu(self)
        menu.setFont(QFont(fonts["system"], s(10)))
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: {s(8)}px;
                padding: {s(6)}px;
                font-weight: 500;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: {s(8)}px {s(16)}px;
                border-radius: {s(4)}px;
                color: #495057;
                min-width: {s(100)}px;
            }}
            QMenu::item:selected {{
                background-color: #4a90e2;
                color: white;
            }}
            QMenu::item:disabled {{
                color: #6c757d;
                background-color: #f8f9fa;
            }}
        """)
        
        current_lang = get_current_language()
        zh_action = menu.addAction(t("buttons.chinese"))
        if current_lang == "zh_CN":
            zh_action.setText(f"✓ {t('buttons.chinese')}")
            zh_action.setEnabled(False)
        else:
            zh_action.triggered.connect(lambda: self.on_language_changed("zh_CN"))
        en_action = menu.addAction(t("buttons.english"))
        if current_lang == "en_US":
            en_action.setText(f"✓ {t('buttons.english')}")
            en_action.setEnabled(False)
        else:
            en_action.triggered.connect(lambda: self.on_language_changed("en_US"))
        
        button_pos = self.lang_btn.mapToGlobal(self.lang_btn.rect().bottomLeft())
        menu.exec(button_pos)
    
    def on_language_changed(self, language):
        
        set_language(language)
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(t("messages.language_changed"))
        msg_box.setInformativeText(t("messages.language_restart"))
        msg_box.setWindowTitle(t("messages.hint"))
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
    
    def init_tools(self):
        tools_dir = "tools"
        tools = []
        if os.path.exists(tools_dir):
            for item in os.listdir(tools_dir):
                item_path = os.path.join(tools_dir, item)
                if os.path.isdir(item_path):
                    
                    config_path = os.path.join(item_path, "wct_config.txt")
                    if os.path.exists(config_path):
                        tools.append(item)

        for tool in tools:
            self.tool_list.addItem(tool)
            
            item = self.tool_list.item(self.tool_list.count() - 1)
            item.setFont(QFont(get_system_font(), s(11), QFont.Bold))
            
            tool_page = ToolOperationPage(tool)
            self.tool_pages[tool] = tool_page
            self.right_stack.addTab(tool_page, "")
        self.right_stack.setCurrentIndex(0)
        self.tool_list.setCurrentRow(-1)
    
    def on_tool_selected(self, row):
        if row >= 0:
            tool_name = self.tool_list.item(row).text()
            if tool_name in self.tool_pages:
                
                page_index = list(self.tool_pages.keys()).index(tool_name) + 1
                self.right_stack.setCurrentIndex(page_index)
        else:
            
            self.right_stack.setCurrentIndex(0)
    
    def on_item_clicked(self, item):
        self.set_tool_list_item_alert(item.text(), alert=False)
    
    def clear_selection(self):
        self.tool_list.clearSelection()
        self.tool_list.setCurrentRow(-1)
        self.right_stack.setCurrentIndex(0)
    
    def show_tool_list_context_menu(self, position):
        menu = QMenu(self)
        menu.setFont(QFont(fonts["system"], s(10)))
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 4px;
                color: #495057;
            }
            QMenu::item:selected {
                background-color: #4a90e2;
                color: white;
            }
        """)
        show_ads_action = menu.addAction(t("buttons.home"))
        show_ads_action.triggered.connect(self.clear_selection)
        menu.addSeparator()
        backup_action = menu.addAction(t("buttons.backup"))
        backup_action.triggered.connect(self.backup_config)
        
        restore_action = menu.addAction(t("buttons.restore"))
        restore_action.triggered.connect(self.restore_config)
        current_item = self.tool_list.currentItem()
        if current_item:
            menu.addSeparator()
            open_folder_action = menu.addAction(t("buttons.open_folder", current_item.text()))
            open_folder_action.triggered.connect(lambda: self.open_tool_folder(current_item.text()))
        
        menu.exec(self.tool_list.mapToGlobal(position))

    def on_scale_changed(self, text):
        try:
            scale_factor = float(text.replace('%', '')) / 100.0
            utils.save_scale_factor(scale_factor)

            if hasattr(self, 'scale_btn'):
                self.scale_btn.setText(f"⚡ {text}")
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(t("messages.scale_changed"))
            msg_box.setInformativeText(t("messages.scale_restart"))
            msg_box.setWindowTitle(t("messages.hint"))
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

        except ValueError:
            pass

    def open_tool_folder(self, tool_name):
        
        try:
            tool_path = os.path.join("tools", tool_name)
            if os.path.exists(tool_path):
                
                abs_tool_path = os.path.abspath(tool_path)
                if platform.system() == "Windows":
                    
                    subprocess.run(["explorer", abs_tool_path], check=False)
                elif platform.system() == "Darwin":
                    
                    subprocess.run(["open", abs_tool_path], check=False)
                else:
                    
                    subprocess.run(["xdg-open", abs_tool_path], check=False)
            else:
                self.show_error_message(t("messages.folder_not_exist"), t("messages.folder_not_exist_msg", tool_path))
        except Exception as e:
            pass

    def backup_config(self):
        
        try:
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{t('backup.filename', timestamp)}.zip"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                t("dialog.backup_title"),
                default_filename,
                t("dialog.zip_files")
            )
            
            if not file_path:
                return
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
                templates_dir = "templates"
                if os.path.exists(templates_dir):
                    for root, dirs, files in os.walk(templates_dir):
                        for file in files:
                            full_file_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_file_path, ".")
                            backup_zip.write(full_file_path, arcname)
                promotion_dir = "promotion"
                if os.path.exists(promotion_dir):
                    for root, dirs, files in os.walk(promotion_dir):
                        for file in files:
                            full_file_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_file_path, ".")
                            backup_zip.write(full_file_path, arcname)
                if os.path.exists("promotion_config.json"):
                    backup_zip.write("promotion_config.json", "promotion_config.json")
                if os.path.exists("command_history.json"):
                    backup_zip.write("command_history.json", "command_history.json")
                tools_dir = "tools"
                if os.path.exists(tools_dir):
                    for tool_name in os.listdir(tools_dir):
                        tool_path = os.path.join(tools_dir, tool_name)
                        if os.path.isdir(tool_path):
                            config_file = os.path.join(tool_path, "wct_config.txt")
                            if os.path.exists(config_file):
                                arcname = os.path.relpath(config_file, ".")
                                backup_zip.write(config_file, arcname)
                            custom_cmd_file = os.path.join(tool_path, "custom_command.txt")
                            if os.path.exists(custom_cmd_file):
                                arcname = os.path.relpath(custom_cmd_file, ".")
                                backup_zip.write(custom_cmd_file, arcname)
                backup_info = {
                    "backup_time": datetime.datetime.now().isoformat(),
                    "version": "v0.0.4_beta",
                    "description": t("backup.description"),
                    "includes": [
                        "templates/",
                        "promotion/",
                        "promotion_config.json",
                        "command_history.json", 
                        "tools/*/wct_config.txt",
                        "tools/*/custom_command.txt"
                    ]
                }
                
                backup_zip.writestr("backup_info.json", json.dumps(backup_info, ensure_ascii=False, indent=2))
            
            self.show_success_message(t("messages.backup_success"), t("messages.backup_success_msg", file_path))
            
        except Exception as e:
            self.show_error_message(t("messages.backup_failed"), t("messages.backup_failed_msg", str(e)))

    def restore_config(self):
        
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                t("dialog.restore_title"),
                "",
                t("dialog.zip_files")
            )
            
            if not file_path:
                return
            try:
                with zipfile.ZipFile(file_path, 'r') as backup_zip:
                    file_list = backup_zip.namelist()
                    if "backup_info.json" in file_list:
                        backup_info_data = backup_zip.read("backup_info.json")
                        backup_info = json.loads(backup_info_data.decode('utf-8'))
                        info_text = t("backup.backup_time", backup_info.get('backup_time', '未知')) + "\n"
                        info_text += t("backup.version", backup_info.get('version', '未知')) + "\n"
                        info_text += t("backup.description_label", backup_info.get('description', '无')) + "\n\n"
                        info_text += t("backup.includes") + "\n"
                        for item in backup_info.get('includes', []):
                            info_text += f"- {item}\n"
                        
                        reply = QMessageBox.question(
                            self,
                            t("messages.confirm_restore"),
                            t("messages.confirm_restore_msg", info_text),
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        
                        if reply != QMessageBox.Yes:
                            return
                    else:
                        reply = QMessageBox.question(
                            self,
                            t("messages.confirm_restore"), 
                            t("messages.invalid_backup"),
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        
                        if reply != QMessageBox.Yes:
                            return
            
            except zipfile.BadZipFile:
                self.show_error_message(t("messages.file_error"), t("messages.invalid_zip"))
                return
            with zipfile.ZipFile(file_path, 'r') as backup_zip:
                extracted_files = []
                backup_files = []
                
                for file_info in backup_zip.infolist():
                    
                    if file_info.is_dir() or file_info.filename == "backup_info.json":
                        continue
                    target_path = file_info.filename
                    target_dir = os.path.dirname(target_path)
                    
                    if target_dir and not os.path.exists(target_dir):
                        os.makedirs(target_dir, exist_ok=True)
                    if os.path.exists(target_path):
                        backup_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = f"{target_path}.restore_backup_{backup_timestamp}"
                        shutil.copy2(target_path, backup_path)
                        backup_files.append(backup_path)
                    backup_zip.extract(file_info, ".")
                    extracted_files.append(target_path)
                
                success_text = t("messages.restore_success") + "！\n\n"
                success_text += t("backup.restored_files", len(extracted_files)) + "\n"
                for file in extracted_files[:8]:  
                    success_text += f"- {file}\n"
                
                if len(extracted_files) > 8:
                    success_text += t("backup.more_files", len(extracted_files) - 8) + "\n"
                
                if backup_files:
                    success_text += "\n" + t("backup.backup_files", len(backup_files)) + "\n"
                    for backup_file in backup_files[:5]:  
                        original_name = backup_file.split('.restore_backup_')[0]
                        success_text += f"- {original_name} → {os.path.basename(backup_file)}\n"
                    
                    if len(backup_files) > 5:
                        success_text += t("backup.more_backups", len(backup_files) - 5) + "\n"
                
                self.show_success_message(t("messages.restore_success"), success_text)
                
        except Exception as e:
            self.show_error_message(t("messages.restore_failed"), t("messages.restore_failed_msg", str(e)))

    def show_success_message(self, title, message):
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

    def show_error_message(self, title, message):
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

    def set_tool_list_item_alert(self, tool_name, alert=True):
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            if item.text() == tool_name:
                if alert:
                    item.setBackground(QBrush(QColor('#ffe066')))
                    item.setIcon(QIcon.fromTheme('dialog-warning'))
                else:
                    item.setBackground(QBrush())
                    item.setIcon(QIcon())
                break

