import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QLineEdit, QComboBox, 
    QSplitter, QDialog, QCheckBox, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from .utils import build_cross_platform_command
from .i18n import t
from .env_manager import EnvironmentManager

from .widgets import ClickableLabel, EditableTabWidget
from .theme import colors, fonts, params
from .styles import get_modern_qtabwidget_stylesheet
from .config import ToolConfigParser
from .process import ToolProcess
from .process_tab import ProcessTab
from .parameters import ToolParameterTab
from .templates import TemplateManager
from .utils import s

class ToolOperationPage(QWidget):

    def __init__(self, tool_name):
        super().__init__()
        self.tool_name = tool_name
        self.config_data = None
        self.processes = []
        self.command_history = {}  
        self.env_manager = EnvironmentManager(logger=None)
        self.setup_ui()
        self.load_config()
        self.load_command_history()
        self.load_env_config()

        if hasattr(self, 'system_log_tab'):
            self.env_manager.logger = self.system_log_tab
    
    def setup_ui(self):
        
        main_splitter = QSplitter(Qt.Horizontal)

        left_widget = self.create_parameter_page()
        main_splitter.addWidget(left_widget)

        right_widget = self.create_runtime_page()
        main_splitter.addWidget(right_widget)

        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 3)
        
        layout = QHBoxLayout()
        layout.addWidget(main_splitter)
        self.setLayout(layout)
    
    def create_parameter_page(self):
        
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["white"]};
                border-radius: {params["border_radius_small"]};
            }}
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(s(16), s(16), s(16), s(16))
        layout.setSpacing(s(12))

        top_widget = QWidget()
        top_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(12)}px;
            }}
        """)
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(s(8), s(8), s(8), s(8))
        top_layout.setSpacing(s(12))
        
        tool_label = QLabel(self.tool_name)
        tool_label.setFont(QFont(fonts["system"], s(14), QFont.Bold))
        tool_label.setAlignment(Qt.AlignCenter)
        tool_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["tooltip_text"]};
                background: transparent;
                border: none;
                padding: {s(4)}px 0px;
            }}
        """)
        top_layout.addWidget(tool_label)
        
        top_widget.setLayout(top_layout)
        layout.addWidget(top_widget)

        cmd_widget = QWidget()
        cmd_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(12)}px;
            }}
        """)
        cmd_layout = QHBoxLayout()
        cmd_layout.setContentsMargins(s(8), s(8), s(8), s(8))
        cmd_layout.setSpacing(s(12))
        
        cmd_label = QLabel(t("run_command"))
        cmd_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        cmd_label.setMinimumWidth(s(80))
        cmd_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        cmd_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["text_secondary"]};
                background: transparent;
                border: none;
                padding: {s(4)}px 0px;
            }}
        """)
        cmd_layout.addWidget(cmd_label)
        
        self.command_input = QLineEdit()
        self.command_input.setMinimumHeight(s(32))
        self.command_input.setPlaceholderText(t("command_placeholder"))
        self.command_input.setToolTip(t("command_tooltip"))
        self.command_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(8)}px {s(12)}px;
                color: {colors["text_secondary"]};
                font-size: {s(9)}pt;
                selection-background-color: {colors["secondary"]};
            }}
            QLineEdit:focus {{
                border-color: {colors["secondary"]};
                background-color: {colors["white"]};
            }}
            QLineEdit:hover {{
                border-color: #ced4da;
            }}
        """)
        self.command_input.textChanged.connect(self.save_command)
        cmd_layout.addWidget(self.command_input)
        self.new_tab_toggle = QPushButton(t("new_tab"))
        self.new_tab_toggle.setCheckable(True)
        self.new_tab_toggle.setChecked(True)
        self.new_tab_toggle.setMinimumWidth(s(100))
        self.new_tab_toggle.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.new_tab_toggle.setMinimumHeight(s(36))
        self.new_tab_toggle.setFont(QFont(fonts["system"], s(9), QFont.Medium))

        self.new_tab_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(8)}px {s(16)}px;
                color: {colors["text_secondary"]};
                font-weight: 500;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {colors["list_item_hover_background"]};
                border-color: {colors["secondary"]};
                color: {colors["list_item_hover_text"]};
            }}
            QPushButton:checked {{
                background-color: {colors["secondary"]};
                border: 1px solid {colors["secondary"]};
                color: {colors["white"]};
                font-weight: 600;
            }}
            QPushButton:checked:hover {{
                background-color: {colors["secondary_hover"]};
                border-color: {colors["secondary_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["secondary_pressed"]};
            }}
        """)

        self.new_tab_toggle.toggled.connect(self.update_tab_toggle_text)
        self.new_tab_toggle.setToolTip(t("run_mode_tooltip"))
        cmd_layout.addWidget(self.new_tab_toggle)
        
        run_btn = QPushButton(t("start_running"))
        run_btn.setMinimumWidth(s(90))
        run_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        run_btn.setMinimumHeight(s(36))
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["secondary"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(8)}px {s(16)}px;
                color: white;
                font-weight: 600;
                font-size: {s(9)}pt;
            }}
            QPushButton:hover {{
                background-color: {colors["secondary_hover"]};
                border-color: {colors["secondary_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["secondary_pressed"]};
            }}
        """)
        run_btn.clicked.connect(self.start_tool)
        cmd_layout.addWidget(run_btn)
        
        cmd_widget.setLayout(cmd_layout)
        layout.addWidget(cmd_widget)
        venv_env_widget = QWidget()
        venv_env_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(12)}px;
            }}
        """)
        venv_env_layout = QVBoxLayout()
        venv_env_layout.setContentsMargins(s(8), s(8), s(8), s(8))
        venv_env_layout.setSpacing(s(12))
        

        python_row_layout = QHBoxLayout()
        python_row_layout.setSpacing(s(12))
        
        python_label = QLabel(t("python_interpreter_path"))
        python_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        python_label.setMinimumWidth(s(100))
        python_label.setStyleSheet(f"color: {colors['text_secondary']}; background: transparent; border: none;")
        
        self.python_input = QLineEdit()
        self.python_input.setMinimumHeight(s(32))
        self.python_input.setPlaceholderText(t("python_path_placeholder"))
        self.python_input.setToolTip(t("python_path_tooltip"))
        self.python_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(10)}px;
                color: {colors["text_secondary"]};
                font-size: {s(9)}pt;
                selection-background-color: {colors["secondary"]};
            }}
            QLineEdit:focus {{
                border-color: {colors["secondary"]};
                background-color: {colors["white"]};
            }}
            QLineEdit:hover {{
                border-color: #ced4da;
            }}
        """)
        
        python_browse_btn = QPushButton(t("browse"))
        python_browse_btn.setMinimumHeight(s(32))
        python_browse_btn.setMaximumWidth(s(70))
        python_browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(12)}px;
                color: {colors["text_secondary"]};
                font-size: {s(8)}pt;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors["list_item_hover_background"]};
                border-color: {colors["secondary"]};
                color: {colors["list_item_hover_text"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["secondary_pressed"]};
            }}
        """)
        python_browse_btn.clicked.connect(self.browse_python_path)
        
        python_row_layout.addWidget(python_label)
        python_row_layout.addWidget(self.python_input, 1)
        python_row_layout.addWidget(python_browse_btn)
        
        venv_env_layout.addLayout(python_row_layout)
        

        second_row_layout = QHBoxLayout()
        second_row_layout.setSpacing(s(12))
        
        venv_column = QWidget()
        venv_column_layout = QVBoxLayout()
        venv_column_layout.setContentsMargins(0, 0, 0, 0)
        venv_column_layout.setSpacing(s(4))

        venv_label = QLabel(t("python_venv_path"))
        venv_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        venv_label.setStyleSheet(f"color: {colors['text_secondary']}; background: transparent; border: none;")
        self.venv_input = QLineEdit()
        self.venv_input.setMinimumHeight(s(32))
        self.venv_input.setPlaceholderText(t("venv_placeholder"))
        self.venv_input.setToolTip(t("venv_tooltip"))
        self.venv_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(10)}px;
                color: {colors["text_secondary"]};
                font-size: {s(9)}pt;
                selection-background-color: {colors["secondary"]};
            }}
            QLineEdit:focus {{
                border-color: {colors["secondary"]};
                background-color: {colors["white"]};
            }}
            QLineEdit:hover {{
                border-color: #ced4da;
            }}
        """)
        venv_column_layout.addWidget(venv_label)
        venv_column_layout.addWidget(self.venv_input)
        venv_column.setLayout(venv_column_layout)
        env_column = QWidget()
        env_column_layout = QVBoxLayout()
        env_column_layout.setContentsMargins(0, 0, 0, 0)
        env_column_layout.setSpacing(s(4))

        env_label = QLabel(t("custom_env_vars"))
        env_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        env_label.setStyleSheet(f"color: {colors['text_secondary']}; background: transparent; border: none;")
        self.env_input = QLineEdit()
        self.env_input.setMinimumHeight(s(32))
        self.env_input.setPlaceholderText(t("env_placeholder"))
        self.env_input.setToolTip(t("env_tooltip"))
        self.env_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(10)}px;
                color: {colors["text_secondary"]};
                font-size: {s(9)}pt;
                selection-background-color: {colors["secondary"]};
            }}
            QLineEdit:focus {{
                border-color: {colors["secondary"]};
                background-color: {colors["white"]};
            }}
            QLineEdit:hover {{
                border-color: #ced4da;
            }}
        """)
        env_column_layout.addWidget(env_label)
        env_column_layout.addWidget(self.env_input)
        env_column.setLayout(env_column_layout)
        
        second_row_layout.addWidget(venv_column)
        second_row_layout.addWidget(env_column)
        
        venv_env_layout.addLayout(second_row_layout)
        
        venv_env_widget.setLayout(venv_env_layout)
        layout.addWidget(venv_env_widget)
        
        self.python_input.textChanged.connect(self.save_env_config)
        self.venv_input.textChanged.connect(self.save_env_config)
        self.env_input.textChanged.connect(self.save_env_config)
        self.param_tabs = QTabWidget()
        self.param_tabs.setStyleSheet(get_modern_qtabwidget_stylesheet())
        corner_widget = QWidget()
        corner_layout = QHBoxLayout()
        corner_layout.setContentsMargins(s(8), 0, 0, 0)
        corner_layout.setSpacing(s(8))
        clear_btn = QPushButton(t("clear_options"))
        clear_btn.setMinimumWidth(s(90))
        clear_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        clear_btn.setMinimumHeight(s(36))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["white"]};
                border: 1px solid #ff9500;
                border-radius: {params["border_radius_very_small"]};
                padding: {s(8)}px {s(16)}px;
                color: #ff9500;
                font-weight: 500;
                font-size: {s(9)}pt;
            }}
            QPushButton:hover {{
                background-color: #fff7e6;
                border-color: #e6850e;
            }}
            QPushButton:pressed {{
                background-color: #ffe6cc;
            }}
        """)
        clear_btn.clicked.connect(self.clear_all_params)
        corner_layout.addWidget(clear_btn)
        custom_btn = QPushButton(t("custom_template"))
        custom_btn.setMinimumWidth(s(100))
        custom_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        custom_btn.setMinimumHeight(s(36))
        custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["white"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(8)}px {s(16)}px;
                color: {colors["secondary"]};
                font-weight: 500;
                font-size: {s(9)}pt;
            }}
            QPushButton:hover {{
                background-color: #f0f7ff;
                border-color: {colors["secondary_hover"]};
            }}
            QPushButton:pressed {{
                background-color: {colors["list_item_hover_background"]};
            }}
        """)
        custom_btn.clicked.connect(self.open_template_manager)
        corner_layout.addWidget(custom_btn)
        
        corner_widget.setLayout(corner_layout)

        self.param_tabs.setCornerWidget(corner_widget, Qt.TopRightCorner)

        layout.addWidget(self.param_tabs)
        
        widget.setLayout(layout)
        return widget
    
    def create_runtime_page(self):
        
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(s(16), s(16), s(16), s(16))
        layout.setSpacing(s(8))

        self.process_tabs = EditableTabWidget()
        self.process_tabs.setTabsClosable(True)
        self.process_tabs.tabCloseRequested.connect(self.close_process_tab)
        self.process_tabs.tabBar().tabBarClicked.connect(self.on_process_tab_clicked)

        self.system_log_tab = ProcessTab(None, t("system_log"), self.process_tabs)
        self.system_log_tab.terminal_output.setHtml(f"""
        <div style='color: #e2e8f0; background: transparent;'>
        {t('system_log_title')}<br/>
        {t('system_log_desc1')}<br/>
        {t('system_log_desc2')}<br/>
        {t('system_log_desc3')}<br/>
        </div>
        """)
        self.system_log_tab.append_system_log(t("system_log_init"), "success")
        system_tab_index = self.process_tabs.addTab(self.system_log_tab, t("system_log"))

        self.process_tabs.tabBar().setTabButton(system_tab_index, self.process_tabs.tabBar().ButtonPosition.RightSide, None)
        self.process_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: {s(6)}px;
                padding: {s(8)}px;
            }}
            QTabBar::tab {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-bottom: none;
                border-radius: {s(6)}px {s(6)}px 0px 0px;
                padding: {s(6)}px {s(12)}px;
                margin: 0px {s(1)}px;
                color: #6c757d;
                font-weight: 500;
                font-size: {s(8)}pt;
                min-width: {s(60)}px;
            }}
            QTabBar::tab:hover {{
                background-color: #e9ecef;
                color: #495057;
            }}
            QTabBar::tab:selected {{
                background-color: #4a90e2;
                color: white;
                font-weight: 600;
                border-color: #4a90e2;
            }}
            QTabBar::close-button {{
                background-color: rgba(108, 117, 125, 0.1);
                border: none;
                border-radius: {s(6)}px;
                width: {s(14)}px;
                height: {s(14)}px;
                margin: {s(2)}px;
                subcontrol-position: right;
            }}
            QTabBar::close-button:hover {{
                background-color: #dc3545;
                border-radius: {s(6)}px;
            }}
            QTabBar::close-button:pressed {{
                background-color: #a71e2a;
            }}
        """)
        layout.addWidget(self.process_tabs)
        
        widget.setLayout(layout)
        return widget
    
    def load_config(self):
        
        config_path = os.path.join("tools", self.tool_name, "wct_config.txt")
        self.config_data = ToolConfigParser.parse_config(config_path)

        self.param_tabs.clear()

        if "常用参数" in self.config_data:
            common_tab = ToolParameterTab(self.config_data["常用参数"])
            self.param_tabs.addTab(common_tab, t("common_params"))

        if "全部参数" in self.config_data:
            all_tab = ToolParameterTab(self.config_data["全部参数"])
            self.param_tabs.addTab(all_tab, t("all_params"))
    
    def start_tool(self):

        current_tab = self.param_tabs.currentWidget()
        if not current_tab:
            self.system_log_tab.append_system_log(t("no_param_tab_selected"), "error")
            return

        is_valid, missing_params = current_tab.validate_required_params()
        if not is_valid:
            missing_list = "\n• ".join(missing_params)
            error_msg = f"{t('required_params_missing')}\n\n• {missing_list}"
            self.system_log_tab.append_system_log(f"{t('required_param_validation_failed')}: {', '.join(missing_params)}", "error")

            if hasattr(self, 'show_custom_message'):
                self.show_custom_message(t("param_validation_failed"), error_msg)
            else:
                
                from PySide6.QtWidgets import QMessageBox
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(t("param_validation_failed"))
                msg_box.setText(error_msg)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.exec()
            return
        
        params = current_tab.get_all_params()

        user_command = self.command_input.text().strip()
        if not user_command:
            self.system_log_tab.append_system_log(t("enter_tool_command"), "error")
            return

        tool_path = os.path.join("tools", self.tool_name)
        

        if hasattr(self, 'system_log_tab') and self.env_manager.logger is None:
            self.env_manager.logger = self.system_log_tab
        
        try:

            venv_path = self.venv_input.text().strip()
            custom_env = self.env_input.text().strip()
            
            command, env_dict = self.env_manager.create_subprocess_wrapper(
                tool_path, user_command, params, venv_path, custom_env
            )
            
        except ValueError as e:
            self.system_log_tab.append_system_log(str(e), "error")
            return
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('build_command_error')}: {e}", "error")
            return
        
        self.system_log_tab.append_system_log(f"{t('tool')} {self.tool_name} {t('startup')}", "info")
        self.system_log_tab.append_system_log(f"{t('execute_command')}: {' '.join(command)}", "info")

        if self.new_tab_toggle.isChecked():

            process_tab = ProcessTab(None, f"{t('process')}{len(self.processes) + 1}", self.process_tabs)
            tab_index = self.process_tabs.addTab(process_tab, f"{t('process')}{len(self.processes) + 1}")
            self.process_tabs.setCurrentIndex(tab_index)
        else:

            current_index = self.process_tabs.currentIndex()
            current_tab_text = self.process_tabs.tabText(current_index) if current_index >= 0 else ""

            if current_index < 0 or t("system_log") in current_tab_text:

                process_tab = ProcessTab(None, f"{t('process')}{len(self.processes) + 1}", self.process_tabs)
                tab_index = self.process_tabs.addTab(process_tab, f"{t('process')}{len(self.processes) + 1}")
                self.process_tabs.setCurrentIndex(tab_index)
            else:

                process_tab = self.process_tabs.widget(current_index)

                if hasattr(process_tab, 'process') and process_tab.process:
                    process_tab.stop_process()

                process_tab.clear_terminal()

        process_tab.append_system_log(f"{t('start_tool')}: {self.tool_name}", "info")
        process_tab.append_system_log(f"{t('execute_command')}: {' '.join(command)}", "info")
        process_tab.append_system_log(t("interact_below"), "info")

        process = ToolProcess(self, process_tab)
        process_tab.process = process
        process.setEnvironment([f"{k}={v}" for k, v in env_dict.items()])
        process.start(command[0], command[1:])

        process_tab.show_prompt()
        
        self.processes.append(process)

        process.finished.connect(lambda code, status: self.process_finished(process, code, status))
    
    def process_finished(self, process, exit_code, exit_status):

        try:
            from wct_modules.main_window import MainWindow
            from PySide6.QtWidgets import QApplication, QStyle
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, MainWindow):
                    widget.set_tool_list_item_alert(self.tool_name, alert=True)

                    if self.process_tabs is not None:
                        for i in range(self.process_tabs.count()):
                            tab_widget = self.process_tabs.widget(i)
                            if isinstance(tab_widget, ProcessTab) and tab_widget.process == process:
                                self.process_tabs.setTabIcon(i, QIcon.fromTheme('dialog-warning'))
                                break
                    break
        except Exception as e:
            print(f"[DEBUG] {t('debug_failed_highlight')}: {e}")

        if self.process_tabs is not None:
            for i in range(self.process_tabs.count()):
                tab_widget = self.process_tabs.widget(i)
                if isinstance(tab_widget, ProcessTab) and tab_widget.process == process:
                    tab_widget.process_finished(exit_code)
                    break
    
    def close_process_tab(self, index):
        
        tab_widget = self.process_tabs.widget(index)
        if isinstance(tab_widget, ProcessTab):
            
            tab_widget.stop_process()
            self.system_log_tab.append_system_log(t("process_tab_closed"), "warning")

        self.process_tabs.removeTab(index)
        self.check_and_clear_tool_list_alert()
    
    def save_command(self):
        
        command = self.command_input.text().strip()
        self.command_history[self.tool_name] = command
        
        try:
            import json

            config = {}
            if os.path.exists("config/app_config.json"):
                try:
                    with open("config/app_config.json", "r", encoding="utf-8") as rf:
                        config = json.load(rf)
                except:
                    config = {}
            if "tool_history" not in config:
                config["tool_history"] = {}
            config["tool_history"][self.tool_name] = command
            os.makedirs("config", exist_ok=True)
            with open("config/app_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{t('save_command_history_failed')}: {e}")
    
    def load_command_history(self):
        
        try:
            import json
            if os.path.exists("config/app_config.json"):
                with open("config/app_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
                    tool_history = config.get("tool_history", {})
                    self.command_history = tool_history
            else:
                self.command_history = {}

            if self.tool_name in self.command_history:
                self.command_input.setText(self.command_history[self.tool_name])
            else:
                
                default_commands = {
                    "OneForAll": "python oneforall.py"
                }
                if self.tool_name in default_commands:
                    self.command_input.setText(default_commands[self.tool_name])
        except FileNotFoundError:
            
            default_commands = {
                "OneForAll": "python oneforall.py"
            }
            if self.tool_name in default_commands:
                self.command_input.setText(default_commands[self.tool_name])
        except Exception as e:
            print(f"{t('load_command_history_failed')}: {e}")
    
    def open_template_manager(self):
        
        template_manager = TemplateManager(self.tool_name, self)
        template_manager.exec()
    
    def update_tab_toggle_text(self, checked):
        
        if checked:
            self.new_tab_toggle.setText(t("new_tab"))
        else:
            self.new_tab_toggle.setText(t("current_tab"))
    
    def clear_all_params(self):

        current_tab = self.param_tabs.currentWidget()
        if not current_tab:
            self.system_log_tab.append_system_log(t("no_param_tab_selected"), "warning")
            return
        
        cleared_count = 0
        
        for section in current_tab.sections:
            for param_widget in section.param_widgets:
                if isinstance(param_widget.control, (QCheckBox, ClickableLabel)):
                    if param_widget.control.isChecked():
                        param_widget.control.setChecked(False)
                        cleared_count += 1
                elif isinstance(param_widget.control, QLineEdit):
                    if param_widget.control.text().strip():
                        param_widget.control.clear()
                        cleared_count += 1
        
        self.system_log_tab.append_system_log(f"{t('cleared')} {cleared_count} {t('param_options')}", "info")

        current_tab.update_all_required_styles()
    
    def save_and_reload_ui(self):
        
        current_index = self.param_tabs.currentIndex()
        self.save_config_to_file()
        self.reload_config()
        if current_index != -1 and current_index < self.param_tabs.count():
            self.param_tabs.setCurrentIndex(current_index)
    
    def save_config_to_file(self):
        
        try:
            config_path = os.path.join("tools", self.tool_name, "wct_config.txt")

            backup_path = config_path + ".bak"
            if os.path.exists(config_path):
                import shutil
                shutil.copy2(config_path, backup_path)
                self.system_log_tab.append_system_log(f"{t('config_backup_to')}: {backup_path}", "info")

            with open(config_path, 'w', encoding='utf-8') as f:
                
                if "常用参数" in self.config_data:
                    f.write(f"%{t('common_params')}\n")
                    self._write_section_to_file(f, self.config_data["常用参数"])
                    f.write("\n")

                if "全部参数" in self.config_data:
                    f.write(f"%{t('all_params')}\n")
                    self._write_section_to_file(f, self.config_data["全部参数"])
            
            self.system_log_tab.append_system_log(f"{t('config_saved_to')}: {config_path}", "success")
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('save_config_failed')}: {e}", "error")
            import traceback
            self.system_log_tab.append_system_log(f"{t('detailed_error')}: {traceback.format_exc()}", "error")
    
    def _write_section_to_file(self, file, section_data):
        
        for subsection_name, params in section_data.items():
            if subsection_name in ["勾选项区", "输入框区"]:
                if subsection_name == "勾选项区":
                    file.write(f"%%{t('checkbox_section_title')}\n")
                elif subsection_name == "输入框区":
                    file.write(f"%%{t('input_section_title')}\n")
                
                for param in params:
                    required_flag = '1' if param.get('required', False) else '0'
                    
                    param_name = str(param.get('param_name', '')).replace('\n', ' ').strip()
                    display_name = str(param.get('display_name', '')).replace('\n', ' ').strip()
                    description = str(param.get('description', '')).replace('\n', ' ').strip()

                    if not param_name or not display_name:
                        continue
                    
                    line = f"{param_name}={display_name}={description}={required_flag}\n"
                    file.write(line)
                file.write("\n")
    
    def reload_config(self):
        
        self.load_config()
        
        for i in range(self.param_tabs.count()):
            tab = self.param_tabs.widget(i)
            if hasattr(tab, 'update_all_required_styles'):
                tab.update_all_required_styles()
    
    def sync_required_status(self, param_name, required_status):

        for section_name in ["常用参数", "全部参数"]:
            if section_name in self.config_data:
                for subsection_name in ["勾选项区", "输入框区"]:
                    if subsection_name in self.config_data[section_name]:
                        for param in self.config_data[section_name][subsection_name]:
                            if param['param_name'] == param_name:
                                param['required'] = required_status

        for i in range(self.param_tabs.count()):
            tab_widget = self.param_tabs.widget(i)
            if hasattr(tab_widget, 'sections'):
                for section in tab_widget.sections:
                    for param_widget in section.param_widgets:
                        if param_widget.param_info['param_name'] == param_name:
                            param_widget.param_info['required'] = required_status
                            param_widget.update_ui_from_param_info()
        
        self.save_and_reload_ui()
    
    def move_parameter_between_tabs(self, param_info, from_tab, to_tab):
        
        try:
            
            from_section = from_tab
            to_section = to_tab

            param_type = param_info['type']
            subsection = "勾选项区" if param_type == '1' else "输入框区"

            if (from_section in self.config_data and 
                subsection in self.config_data[from_section]):
                
                params_list = self.config_data[from_section][subsection]
                for i, param in enumerate(params_list):
                    if param['param_name'] == param_info['param_name']:
                        removed_param = params_list.pop(i)
                        break
                else:
                    self.system_log_tab.append_system_log(f"{t('in')}{from_section}{t('param_not_found')}", "error")
                    return

            if to_section not in self.config_data:
                self.config_data[to_section] = {}
            if subsection not in self.config_data[to_section]:
                self.config_data[to_section][subsection] = []

            target_params = self.config_data[to_section][subsection]
            for param in target_params:
                if param['param_name'] == param_info['param_name']:
                    self.system_log_tab.append_system_log(t("target_area_has_same_param"), "warning")
                    
                    self.config_data[from_section][subsection].append(removed_param)
                    return

            self.config_data[to_section][subsection].append(removed_param)

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"{t('parameter')} '{param_info['display_name']}' {t('removed_from')}{from_section}{t('moved_to')}{to_section}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('move_param_failed')}: {e}", "error")
    
    def add_parameter_to_section(self, param_info, section_title):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())

            param_type = param_info['type']
            subsection = "勾选项区" if param_type == '1' else "输入框区"

            if current_tab_name in self.config_data:
                if subsection in self.config_data[current_tab_name]:
                    for existing_param in self.config_data[current_tab_name][subsection]:
                        if existing_param['param_name'] == param_info['param_name']:
                            self.system_log_tab.append_system_log(f"{t('param_name')} '{param_info['param_name']}' {t('already_exists')}", "error")
                            return

            if current_tab_name not in self.config_data:
                self.config_data[current_tab_name] = {}
            if subsection not in self.config_data[current_tab_name]:
                self.config_data[current_tab_name][subsection] = []
            
            self.config_data[current_tab_name][subsection].append(param_info)

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"{t('new_param')} '{param_info['display_name']}' {t('added_to')}{current_tab_name}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('add_param_failed')}: {e}", "error")
    
    def update_parameter_in_config(self, old_param_name, new_param_info):
        
        try:
            
            param_type = new_param_info['type']
            subsection = "勾选项区" if param_type == '1' else "输入框区"

            for section_name in ["常用参数", "全部参数"]:
                if section_name in self.config_data:
                    for subsection_name in ["勾选项区", "输入框区"]:
                        if subsection_name in self.config_data[section_name]:
                            params_list = self.config_data[section_name][subsection_name]
                            for i, param in enumerate(params_list):
                                if param['param_name'] == old_param_name:
                                    
                                    if subsection_name != subsection:
                                        
                                        removed_param = params_list.pop(i)
                                        
                                        if subsection not in self.config_data[section_name]:
                                            self.config_data[section_name][subsection] = []
                                        self.config_data[section_name][subsection].append(new_param_info.copy())
                                    else:
                                        
                                        params_list[i] = new_param_info.copy()
                                    break
            
            self.save_and_reload_ui()
            
            self.system_log_tab.append_system_log(
                f"{t('parameter')} '{new_param_info['display_name']}' {t('info_updated')}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('update_param_info_failed')}: {e}", "error")
    
    def remove_parameter_from_common(self, param_info):
        
        try:
            
            param_type = param_info['type']
            subsection = "勾选项区" if param_type == '1' else "输入框区"

            if ("常用参数" in self.config_data and 
                subsection in self.config_data["常用参数"]):
                
                params_list = self.config_data["常用参数"][subsection]
                for i, param in enumerate(params_list):
                    if param['param_name'] == param_info['param_name']:
                        removed_param = params_list.pop(i)
                        break
                else:
                    self.system_log_tab.append_system_log(f"{t('in')}常用参数{t('param_not_found')}", "error")
                    return

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"{t('parameter')} '{param_info['display_name']}' {t('removed_from_common')}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('remove_param_failed')}: {e}", "error")
    
    def copy_parameter_to_common(self, param_info):
        
        try:
            
            param_type = param_info['type']
            subsection = "勾选项区" if param_type == '1' else "输入框区"

            if "常用参数" not in self.config_data:
                self.config_data["常用参数"] = {}
            if subsection not in self.config_data["常用参数"]:
                self.config_data["常用参数"][subsection] = []

            params_list = self.config_data["常用参数"][subsection]
            for param in params_list:
                if param['param_name'] == param_info['param_name']:
                    self.system_log_tab.append_system_log(t("common_params_has_param"), "warning")
                    return

            param_copy = param_info.copy()
            params_list.append(param_copy)

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"{t('parameter')} '{param_info['display_name']}' {t('added_to_common')}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('add_param_to_common_failed')}: {e}", "error")
    
    def show_custom_question(self, title, message):
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(s(500), s(260))
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        dialog.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: {s(16)}px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(32), s(32), s(32), s(32))
        layout.setSpacing(s(20))
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", s(14), QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; background: transparent; border: none; padding: 8px; font-weight: 700;")
        layout.addWidget(title_label)
        
        msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(s(12))
        
        icon_label = QLabel("❓")
        icon_label.setFixedSize(s(32), s(32))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"font-size: {s(20)}pt; background: transparent; border: none;")
        msg_layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Microsoft YaHei", s(11)))
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setStyleSheet("color: #495057; background: transparent; border: none; padding: 8px; line-height: 1.4;")
        msg_layout.addWidget(msg_label, 1)
        
        msg_container.setLayout(msg_layout)
        layout.addWidget(msg_container)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(s(16))
        button_layout.addStretch()
        
        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setMinimumSize(s(90), s(40))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: {s(10)}px;
                color: #6c757d;
                font-weight: 500;
                font-size: {s(12)}pt;
                font-family: 'Microsoft YaHei';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #495057;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #6c757d;
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton(t("confirm"))
        ok_btn.setMinimumSize(s(100), s(40))
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: {s(10)}px;
                color: white;
                font-weight: 600;
                font-size: {s(12)}pt;
                font-family: 'Microsoft YaHei';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        return dialog.exec() == QDialog.Accepted

    def sync_parameter_order(self, section_title, new_params_order):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())

            subsection = section_title

            if current_tab_name in self.config_data:
                if subsection in self.config_data[current_tab_name]:
                    self.config_data[current_tab_name][subsection] = new_params_order.copy()

                    for other_tab_name in ["常用参数", "全部参数"]:
                        if (other_tab_name != current_tab_name and 
                            other_tab_name in self.config_data and 
                            subsection in self.config_data[other_tab_name]):

                            param_map = {param['param_name']: param for param in new_params_order}
                            other_params = self.config_data[other_tab_name][subsection]

                            reordered_other_params = []
                            remaining_params = other_params.copy()

                            for param in new_params_order:
                                param_name = param['param_name']
                                for other_param in remaining_params:
                                    if other_param['param_name'] == param_name:
                                        reordered_other_params.append(other_param)
                                        remaining_params.remove(other_param)
                                        break

                            reordered_other_params.extend(remaining_params)

                            self.config_data[other_tab_name][subsection] = reordered_other_params
            
            self.system_log_tab.append_system_log(
                f"{t('synced')} {section_title} {t('param_order_to_global')}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('sync_param_order_failed')}: {e}", "error")
    
    def remove_parameter_from_section(self, param_name, section_name):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())

            for subsection_name in ["勾选项区", "输入框区"]:
                if (current_tab_name in self.config_data and 
                    subsection_name in self.config_data[current_tab_name]):
                    
                    params_list = self.config_data[current_tab_name][subsection_name]
                    for i, param in enumerate(params_list):
                        if param['param_name'] == param_name:
                            removed_param = params_list.pop(i)
                            
                            self.system_log_tab.append_system_log(
                                f"{t('parameter')} '{param['display_name']}' {t('removed_from_section')} {section_name}", 
                                "info"
                            )
                            return removed_param
            
            return None
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"{t('remove_param_failed')}: {e}", "error")
            return None
    
    def move_parameter_between_sections(self, param_info, from_section_title, to_section_title):
        
        current_tab = self.param_tabs.currentWidget()
        if not hasattr(current_tab, 'config_data'):
            return

        from_key = "勾选项区" if from_section_title == t("checkbox_section_title") else "输入框区"
        to_key = "勾选项区" if to_section_title == t("checkbox_section_title") else "输入框区"
        new_type = '1' if to_key == "勾选项区" else '2'

        config = current_tab.config_data

        param_to_move = None
        if from_key in config and isinstance(config[from_key], list):
            for p in config[from_key]:
                if p.get('param_name') == param_info['param_name']:
                    param_to_move = p
                    break
            if param_to_move:
                config[from_key].remove(param_to_move)

                param_to_move['type'] = new_type
                if to_key not in config:
                    config[to_key] = []
                config[to_key].append(param_to_move)
        
        self.save_and_reload_ui()

    def show_custom_message(self, title, message):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(s(400), s(200))
        dialog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        dialog.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: {s(16)}px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(32), s(32), s(32), s(32))
        layout.setSpacing(s(20))
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", s(14), QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; background: transparent; border: none; padding: 8px; font-weight: 700;")
        layout.addWidget(title_label)
        
        msg_container = QWidget()
        msg_layout = QHBoxLayout()
        msg_layout.setContentsMargins(0,0,0,0)
        msg_layout.setSpacing(s(12))

        icon_label = QLabel()
        icon_label.setFixedSize(s(32), s(32))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_map = {t("success"): "✅", t("completed"): "✅", t("error"): "❌", "warning": "❌", "tip": "💡", "information": "💡"}
        icon_char = "ℹ️" 
        for keyword, icon in icon_map.items():
            if keyword in title:
                icon_char = icon
                break
        icon_label.setText(icon_char)
        icon_label.setStyleSheet(f"font-size: {s(20)}pt; background: transparent; border: none;")
        msg_layout.addWidget(icon_label)
        
        msg_label = QLabel(message)
        msg_label.setFont(QFont("Microsoft YaHei", s(11)))
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        msg_label.setStyleSheet("color: #495057; background: transparent; border: none; padding: 8px; line-height: 1.4;")
        msg_layout.addWidget(msg_label, 1)
        
        msg_container.setLayout(msg_layout)
        layout.addWidget(msg_container)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton(t("confirm"))
        ok_btn.setMinimumSize(s(100), s(40))
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: {s(10)}px;
                color: white;
                font-weight: 600;
                font-size: {s(12)}pt;
                font-family: 'Microsoft YaHei';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        dialog.exec()

    def show_custom_input(self, title, label_text, default_text=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(s(450), s(250))
        dialog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        dialog.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #e1e8ed;
                border-radius: {s(16)}px;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(32), s(32), s(32), s(32))
        layout.setSpacing(s(20))

        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", s(14), QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; background: transparent; border: none; padding: 8px; font-weight: 700;")
        layout.addWidget(title_label)

        label = QLabel(label_text)
        label.setFont(QFont("Microsoft YaHei", s(11)))
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignLeft)
        label.setStyleSheet("color: #495057; background: transparent; border: none; padding: 8px 0px; line-height: 1.4;")
        layout.addWidget(label)

        input_edit = QLineEdit()
        input_edit.setText(default_text)
        input_edit.setFont(QFont("Microsoft YaHei", s(11)))
        input_edit.setMinimumHeight(s(44))
        input_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: #f2f2f7;
                border: 1px solid #d1d1d6;
                border-radius: {s(8)}px;
                padding: {s(12)}px {s(16)}px;
                color: #2c3e50;
                font-size: {s(12)}pt;
                selection-background-color: #4A90E2;
                selection-color: white;
            }}
            QLineEdit:focus {{
                border-color: #007AFF;
                background-color: #ffffff;
            }}
        """)
        layout.addWidget(input_edit)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(s(16))
        button_layout.addStretch()

        cancel_btn = QPushButton(t("cancel"))
        cancel_btn.setMinimumSize(s(90), s(40))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: {s(10)}px;
                color: #6c757d;
                font-weight: 500;
                font-size: {s(12)}pt;
                font-family: 'Microsoft YaHei';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #495057;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #6c757d;
            }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton(t("confirm"))
        ok_btn.setMinimumSize(s(100), s(40))
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: {s(10)}px;
                color: white;
                font-weight: 600;
                font-size: {s(12)}pt;
                font-family: 'Microsoft YaHei';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #5BA0F2, stop: 1 #4A90E2);
                border-color: #4A90E2;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #357ABD, stop: 1 #2C5AA0);
                border-color: #1E3A5F;
            }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            return input_edit.text().strip(), True
        return "", False

    def get_all_params_for_template(self):
        current_params = {}
        if not hasattr(self, 'param_tabs'):
            return current_params

        current_tab = self.param_tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, 'sections'):
            return current_params

        for section in current_tab.sections:
            for param_widget in section.param_widgets:
                param_info = param_widget.param_info
                param_name = param_info['param_name']

                value = param_widget.get_value()
                if (isinstance(value, bool) and value) or (isinstance(value, str) and value.strip()):
                    current_params[param_name] = {
                        'type': param_info['type'],
                        'value': value
                    }
        return current_params

    def apply_params_from_template(self, params):
        applied_count = 0
        if not hasattr(self, 'param_tabs'):
            return applied_count

        current_tab = self.param_tabs.currentWidget()
        if not current_tab or not hasattr(current_tab, 'sections'):
            return applied_count

        for section in current_tab.sections:
            for param_widget in section.param_widgets:
                param_name = param_widget.param_info['param_name']
                if param_name in params:
                    param_data = params[param_name]
                    param_value = param_data.get('value')
                    control = param_widget.control
                    
                    try:
                        if isinstance(control, (QCheckBox, ClickableLabel)):
                            control.setChecked(bool(param_value))
                            applied_count += 1
                        elif isinstance(control, QLineEdit):
                            control.setText(str(param_value))
                            applied_count += 1
                        elif isinstance(control, QComboBox):

                            index = control.findText(str(param_value))
                            if index != -1:
                                control.setCurrentIndex(index)
                                applied_count += 1
                    except Exception as e:
                        print(f"{t('error_applying_template')} {param_name}: {e}")

        current_tab.update_all_required_styles()
        return applied_count

    def check_and_clear_tool_list_alert(self):
        try:

            has_alert = False
            for i in range(self.process_tabs.count()):

                if i == 0:
                    continue
                    
                tab_icon = self.process_tabs.tabIcon(i)
                if not tab_icon.isNull():
                    has_alert = True
                    break
            if not has_alert:
                self.clear_tool_list_alert()
        except Exception as e:
            print(f"[DEBUG] {t('debug_failed_check_alert')}: {e}")
    
    def clear_tool_list_alert(self):
        try:
            from wct_modules.main_window import MainWindow
            from PySide6.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, MainWindow):
                    widget.set_tool_list_item_alert(self.tool_name, alert=False)
                    break
        except Exception as e:
            print(f"[DEBUG] {t('debug_failed_clear_alert')}: {e}")
    
    def clear_all_process_tab_alerts(self):
        try:
            for i in range(self.process_tabs.count()):

                if i == 0:
                    continue
                self.process_tabs.setTabIcon(i, QIcon())
            self.clear_tool_list_alert()
        except Exception as e:
            print(f"[DEBUG] {t('debug_failed_clear_tab_alerts')}: {e}")

    def browse_python_path(self):
        from PySide6.QtWidgets import QFileDialog
        
        if os.name == "nt":
            filter_text = "Python Executable (python.exe);;All Files (*.*)"
            initial_path = "C:\\"
        else:
            filter_text = "Python Executable (python;python3);;All Files (*)"
            initial_path = "/usr/bin"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            t("select_python_interpreter"),
            initial_path,
            filter_text
        )
        
        if file_path:

            if self.env_manager.set_manual_python_path(file_path):
                self.python_input.setText(file_path)
                self.system_log_tab.append_system_log(
                    f"{t('python_path_set')}: {file_path}", 
                    "success"
                )
            else:
                self.system_log_tab.append_system_log(
                    f"{t('invalid_python_path')}: {file_path}", 
                    "error"
                )
                self.show_custom_message(
                    t("invalid_python_interpreter"),
                    f"{t('selected_file_not_valid_python')}\n\n{t('path')}: {file_path}"
                )

    def on_process_tab_clicked(self, index):
        
        self.process_tabs.setTabIcon(index, QIcon())
        self.check_and_clear_tool_list_alert()

    def load_env_config(self):
        
        tool_env_path = os.path.join("tools", self.tool_name, "env_config.json")
        global_env_path = "global_env_config.json"
        config = {"python_path": "", "venv_path": "", "custom_env": ""}
        
        if os.path.exists(tool_env_path):
            try:
                with open(tool_env_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config.update(data)
            except Exception as e:
                print(f"[DEBUG] {t('debug_failed_read_env_config')}: {e}")
        elif os.path.exists(global_env_path):
            try:
                with open(global_env_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config.update(data)
            except Exception as e:
                print(f"[DEBUG] {t('debug_failed_read_global_env')}: {e}")
        
        self.python_input.setText(config.get("python_path", ""))
        self.venv_input.setText(config.get("venv_path", ""))
        self.env_input.setText(config.get("custom_env", ""))
        

        python_path = config.get("python_path", "").strip()
        if python_path:
            self.env_manager.set_manual_python_path(python_path)

    def save_env_config(self):
        
        tool_env_path = os.path.join("tools", self.tool_name, "env_config.json")
        config = {
            "python_path": self.python_input.text().strip(),
            "venv_path": self.venv_input.text().strip(),
            "custom_env": self.env_input.text().strip()
        }
        

        python_path = config["python_path"]
        if python_path:
            self.env_manager.set_manual_python_path(python_path)
        
        try:
            os.makedirs(os.path.dirname(tool_env_path), exist_ok=True)
            with open(tool_env_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[DEBUG] {t('save_config_failed')} env_config.json: {e}")
