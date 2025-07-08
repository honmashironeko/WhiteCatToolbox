import os
import re
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QLineEdit, QComboBox, QGroupBox,
    QGridLayout, QFrame, QSpacerItem, QSizePolicy, QFileDialog,
    QSplitter, QDialog, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from .utils import build_cross_platform_command, get_system_font
from .i18n import t

from .widgets import ClickableLabel, EditableTabWidget
from .theme import colors, fonts, params
from .styles import get_modern_qtabwidget_stylesheet
from .config import ToolConfigParser
from .process import ToolProcess
from .process_tab import ProcessTab
from .parameters import ToolParameterTab, ParameterSection
from .templates import TemplateManager
from .utils import s

class ToolOperationPage(QWidget):

    def __init__(self, tool_name):
        super().__init__()
        self.tool_name = tool_name
        self.config_data = None
        self.processes = []
        self.command_history = {}  
        self.setup_ui()
        self.load_config()
        self.load_command_history()
        self.load_env_config()
    
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
        top_layout = QVBoxLayout()
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
        first_button_layout = QHBoxLayout()
        first_button_layout.setSpacing(s(8))
        first_button_layout.addStretch()

        clear_btn = QPushButton(t("buttons.clear_options"))
        clear_btn.setMinimumWidth(s(80))
        clear_btn.setMinimumHeight(s(32))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["white"]};
                border: 1px solid #ff9500;
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(12)}px;
                color: #ff9500;
                font-weight: 500;
                font-size: {s(8)}pt;
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
        first_button_layout.addWidget(clear_btn)
        
        custom_btn = QPushButton(t("buttons.custom_template"))
        custom_btn.setMinimumWidth(s(90))
        custom_btn.setMinimumHeight(s(32))
        custom_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["white"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(12)}px;
                color: {colors["secondary"]};
                font-weight: 500;
                font-size: {s(8)}pt;
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
        first_button_layout.addWidget(custom_btn)

        self.new_tab_toggle = QPushButton(t("buttons.new_tab"))
        self.new_tab_toggle.setCheckable(True)
        self.new_tab_toggle.setChecked(True)
        self.new_tab_toggle.setMinimumWidth(s(100))
        self.new_tab_toggle.setMinimumHeight(s(32))
        self.new_tab_toggle.setFont(QFont(fonts["system"], s(8), QFont.Medium))

        self.new_tab_toggle.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(12)}px;
                color: {colors["text_secondary"]};
                font-weight: 500;
                font-size: {s(8)}pt;
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
        self.new_tab_toggle.setToolTip(t("tooltips.run_mode"))
        first_button_layout.addWidget(self.new_tab_toggle)
        
        first_button_layout.addStretch()
        top_layout.addLayout(first_button_layout)
        command_widget = QWidget()
        command_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(8)}px;
            }}
        """)
        command_layout = QHBoxLayout()
        command_layout.setContentsMargins(s(8), s(4), s(8), s(4))
        command_layout.setSpacing(s(12))
        
        cmd_label = QLabel(t("labels.run_command"))
        cmd_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        cmd_label.setMinimumWidth(s(60))
        cmd_label.setStyleSheet(f"""
            QLabel {{
                color: {colors["text_secondary"]};
                background: transparent;
                border: none;
                padding: {s(4)}px 0px;
            }}
        """)
        command_layout.addWidget(cmd_label)
        
        self.command_input = QLineEdit()
        self.command_input.setMinimumHeight(s(32))
        self.command_input.setPlaceholderText(t("placeholders.command_input"))
        self.command_input.setToolTip(t("tooltips.command_input"))
        self.command_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(12)}px;
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
        command_layout.addWidget(self.command_input)
        
        run_btn = QPushButton(t("buttons.start_run"))
        run_btn.setMinimumWidth(s(100))
        run_btn.setMinimumHeight(s(32))
        run_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["secondary"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(6)}px {s(16)}px;
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
        command_layout.addWidget(run_btn)
        
        command_widget.setLayout(command_layout)
        top_layout.addWidget(command_widget)
        
        top_widget.setLayout(top_layout)
        layout.addWidget(top_widget)

        self.param_tabs = QTabWidget()
        self.param_tabs.setStyleSheet(get_modern_qtabwidget_stylesheet())

        global_search_container = self.create_global_search_bar()
        layout.addWidget(global_search_container)

        venv_env_widget = QWidget()
        venv_env_layout = QVBoxLayout()
        venv_env_layout.setContentsMargins(0, 0, 0, 0)
        venv_env_layout.setSpacing(s(4))

        venv_label = QLabel(t("labels.python_venv"))
        venv_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        venv_label.setStyleSheet(f"color: {colors['text_secondary']}; background: transparent; border: none;")
        self.venv_input = QLineEdit()
        self.venv_input.setMinimumHeight(s(28))
        self.venv_input.setPlaceholderText(t("placeholders.venv_path"))
        self.venv_input.setToolTip(t("tooltips.venv_path"))
        self.venv_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['main_background_start']};
                border: 1px solid {colors['background_gray']};
                border-radius: {params['border_radius_very_small']};
                padding: {s(4)}px {s(8)}px;
                font-size: {s(9)}pt;
                color: {colors['text_secondary']};
            }}
            QLineEdit:focus {{
                border-color: {colors['secondary']};
                background-color: {colors['white']};
            }}
            QLineEdit:hover {{
                border-color: {colors['border']};
            }}
        """)
        venv_env_layout.addWidget(venv_label)
        venv_env_layout.addWidget(self.venv_input)

        env_label = QLabel(t("labels.custom_env"))
        env_label.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        env_label.setStyleSheet(f"color: {colors['text_secondary']}; background: transparent; border: none;")
        self.env_input = QLineEdit()
        self.env_input.setMinimumHeight(s(28))
        self.env_input.setPlaceholderText(t("placeholders.env_vars"))
        self.env_input.setToolTip(t("tooltips.env_vars"))
        self.env_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['main_background_start']};
                border: 1px solid {colors['background_gray']};
                border-radius: {params['border_radius_very_small']};
                padding: {s(4)}px {s(8)}px;
                font-size: {s(9)}pt;
                color: {colors['text_secondary']};
            }}
            QLineEdit:focus {{
                border-color: {colors['secondary']};
                background-color: {colors['white']};
            }}
            QLineEdit:hover {{
                border-color: {colors['border']};
            }}
        """)
        venv_env_layout.addWidget(env_label)
        venv_env_layout.addWidget(self.env_input)

        venv_env_widget.setLayout(venv_env_layout)
        layout.addWidget(venv_env_widget)

        self.venv_input.textChanged.connect(self.save_env_config)
        self.env_input.textChanged.connect(self.save_env_config)
        
        layout.addWidget(self.param_tabs)
        
        widget.setLayout(layout)
        return widget
    
    def create_global_search_bar(self):
        
        search_container = QWidget()
        search_container.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                padding: {s(8)}px;
            }}
        """)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_icon = QLabel(t("labels.global_search"))
        search_icon.setFont(QFont(fonts["system"], s(9), QFont.Bold))
        search_icon.setStyleSheet(f"color: {colors['text_secondary']}; border: none; background: transparent;")
        search_icon.setMinimumWidth(s(90))
        
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText(t("placeholders.global_search"))
        self.global_search_input.setFont(QFont(fonts["system"], s(10)))
        self.global_search_input.setMinimumHeight(s(36))
        self.global_search_input.textChanged.connect(self.on_global_search_changed)
        self.global_search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors["main_background_start"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_very_small"]};
                padding: {s(4)}px {s(12)}px;
                font-size: {s(10)}pt;
            }}
            QLineEdit:focus {{
                border: 2px solid {colors["secondary"]};
                background-color: {colors["white"]};
            }}
        """)
        
        self.global_clear_btn = QPushButton(t("buttons.clear"))
        self.global_clear_btn.setFont(QFont(get_system_font(), s(8)))
        self.global_clear_btn.setMinimumSize(s(50), s(28))
        self.global_clear_btn.clicked.connect(self.clear_global_search)
        self.global_clear_btn.setVisible(False)  
        
        self.global_clear_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #6c757d;
                border-radius: 4px;
                background-color: #ffffff;
                color: #6c757d;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #495057;
                color: #495057;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
            }
        """)
        
        self.global_result_label = QLabel()
        self.global_result_label.setFont(QFont(get_system_font(), s(8)))
        self.global_result_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        self.global_result_label.setVisible(False)
        
        search_mode_label = QLabel(t("labels.search_mode"))
        search_mode_label.setFont(QFont(get_system_font(), s(8)))
        search_mode_label.setStyleSheet("color: #6c757d; border: none; background: transparent;")
        
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItems([t("search_modes.fuzzy"), t("search_modes.exact"), t("search_modes.regex")])
        self.search_mode_combo.setFont(QFont(get_system_font(), s(9)))
        self.search_mode_combo.setMinimumHeight(s(36))
        self.search_mode_combo.currentIndexChanged.connect(self.on_search_mode_changed)
        self.search_mode_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {colors["white"]};
                border: 1px solid {colors["border"]};
                border-radius: {s(6)}px;
                padding: {s(4)}px {s(8)}px;
                min-width: {s(60)}px;
                font-weight: 500;
                color: {colors["text"]};
                font-size: {s(9)}pt;
                height: {s(32)}px;
                text-align: center;
            }}
            QComboBox::drop-down {{
                width: 0px;
                border: none;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }}
            QComboBox:hover {{
                border-color: {colors["secondary"]};
                background-color: {colors["background_very_light"]};
            }}
            QComboBox:focus {{
                border-color: {colors["primary"]};
                outline: none;
            }}
            QComboBox:pressed {{
                background-color: {colors["background_light"]};
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors["white"]};
                border: 1px solid {colors["secondary"]};
                border-radius: {s(8)}px;
                selection-background-color: {colors["secondary"]};
                selection-color: {colors["white"]};
                padding: {s(8)}px;
                outline: none;
                font-size: {s(9)}pt;
                show-decoration-selected: 1;
                min-width: {s(100)}px;
                alternate-background-color: transparent;
                gridline-color: transparent;
            }}
            QComboBox QAbstractItemView QScrollBar {{
                border: none;
                background: transparent;
            }}
            QComboBox QFrame {{
                border: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: {s(12)}px {s(16)}px;
                border: none;
                border-radius: {s(6)}px;
                font-weight: 500;
                min-height: {s(20)}px;
                margin: {s(2)}px;
                background: transparent;
                color: {colors["text"]};
                text-align: center;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 {colors["secondary"]}, stop: 1 {colors["secondary_hover"]});
                color: {colors["white"]};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, 
                    stop: 0 {colors["primary"]}, stop: 1 {colors["primary_hover"]});
                color: {colors["white"]};
                font-weight: 600;
            }}
        """)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.global_search_input, 1)
        search_layout.addWidget(self.global_clear_btn)
        search_layout.addWidget(search_mode_label)
        search_layout.addWidget(self.search_mode_combo)
        search_layout.addWidget(self.global_result_label)
        
        search_container.setLayout(search_layout)
        return search_container
    
    def on_global_search_changed(self, text):
        
        self.global_clear_btn.setVisible(bool(text))
        
        if text.strip():
            self.perform_global_search(text.strip())
        else:
            self.clear_all_search_highlights()
    
    def clear_global_search(self):
        
        self.global_search_input.clear()
        self.clear_all_search_highlights()
    
    def on_search_mode_changed(self, mode):
        
        search_text = self.global_search_input.text().strip()
        if search_text:
            self.perform_global_search(search_text)
    
    def perform_global_search(self, search_text):
        
        total_matches = 0
        total_params = 0
        search_mode = self.search_mode_combo.currentText()

        for tab_index in range(self.param_tabs.count()):
            tab_widget = self.param_tabs.widget(tab_index)
            if isinstance(tab_widget, ToolParameterTab):
                
                for section in tab_widget.findChildren(ParameterSection):
                    section_matches = self.search_in_section(section, search_text, search_mode)
                    total_matches += section_matches
                    total_params += len(section.param_widgets)

        if total_matches == 0:
            self.global_result_label.setText(t("messages.no_matches"))
            self.global_result_label.setStyleSheet("color: #dc3545; border: none; background: transparent; font-weight: 500;")
        else:
            self.global_result_label.setText(t("messages.found_matches", total_matches, total_params))
            self.global_result_label.setStyleSheet("color: #28a745; border: none; background: transparent; font-weight: 500;")
        
        self.global_result_label.setVisible(True)

        self.system_log_tab.append_system_log(
            t("messages.global_search_result", search_text, search_mode, total_matches),
            "info"
        )
    
    def search_in_section(self, section, search_text, search_mode):
        
        matches = 0
        
        for param_widget in section.param_widgets:
            is_match = False
            
            if search_mode == t("search_modes.fuzzy"):
                is_match = self.smart_search_match(param_widget.param_info, search_text.lower())
            elif search_mode == t("search_modes.exact"):
                is_match = self.exact_search_match(param_widget.param_info, search_text)
            elif search_mode == t("search_modes.regex"):
                is_match = self.regex_search_match(param_widget.param_info, search_text)
            
            if is_match:
                param_widget.setVisible(True)
                section.highlight_search_match(param_widget, search_text.lower())
                matches += 1
            else:
                param_widget.setVisible(False)
                section.clear_highlight(param_widget)
        section.rebuild_layout_order()
        
        return matches
    
    def smart_search_match(self, param_info, search_text):

        fields_to_search = [
            param_info.get('param_name', ''),
            param_info.get('display_name', ''),
            param_info.get('description', ''),
            param_info.get('help', ''),
            str(param_info.get('default', ''))
        ]
        
        for field in fields_to_search:
            if search_text in field.lower():
                return True
        return False
    
    def exact_search_match(self, param_info, search_text):
        
        fields_to_search = [
            param_info.get('param_name', ''),
            param_info.get('display_name', ''),
            param_info.get('description', ''),
            param_info.get('help', ''),
            str(param_info.get('default', ''))
        ]
        
        for field in fields_to_search:
            if search_text == field:
                return True
        return False
    
    def regex_search_match(self, param_info, search_text):
        
        try:
            import re
            pattern = re.compile(search_text, re.IGNORECASE)
            
            fields_to_search = [
                param_info.get('param_name', ''),
                param_info.get('display_name', ''),
                param_info.get('description', ''),
                param_info.get('help', ''),
                str(param_info.get('default', ''))
            ]
            
            for field in fields_to_search:
                if pattern.search(field):
                    return True
        except re.error:
            
            return self.smart_search_match(param_info, search_text.lower())
        
        return False
    
    def clear_all_search_highlights(self):

        for tab_index in range(self.param_tabs.count()):
            tab_widget = self.param_tabs.widget(tab_index)
            if isinstance(tab_widget, ToolParameterTab):
                for section in tab_widget.findChildren(ParameterSection):
                    section.show_all_parameters()
        
        self.global_result_label.setVisible(False)
    
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
        self.process_tabs.currentChanged.connect(self.on_tab_changed)

        self.system_log_tab = ProcessTab(None, t('system.log_tab_name'), self.process_tabs)
        self.system_log_tab.terminal_output.setHtml(f"""
        <div style='color: #e2e8f0; background: transparent;'>
        🎯 <b>{t('system.log_title')}</b><br/>
        📝 {t('system.log_description')}<br/>
        💡 {t('system.log_includes')}<br/>
        ⚡ {t('system.log_realtime')}<br/>
        </div>
        """)
        self.system_log_tab.append_system_log(t('messages.terminal_init'), "success")
        system_tab_index = self.process_tabs.addTab(self.system_log_tab, "📊 " + t('system.log_tab_name'))
        self.system_log_tab.set_as_current_tab(True)

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

        if '常用参数' in self.config_data:
            common_tab = ToolParameterTab(self.config_data['常用参数'])
            self.param_tabs.addTab(common_tab, t('tabs.common_params'))

        if '全部参数' in self.config_data:
            all_tab = ToolParameterTab(self.config_data['全部参数'])
            self.param_tabs.addTab(all_tab, t('tabs.all_params'))
    
    def start_tool(self):

        current_tab = self.param_tabs.currentWidget()
        if not current_tab:
            self.system_log_tab.append_system_log("没有选择参数选项卡", "error")
            return

        is_valid, missing_params = current_tab.validate_required_params()
        if not is_valid:
            missing_list = "\n• ".join(missing_params)
            error_msg = f"以下必填参数尚未填写，请检查后重试：\n\n• {missing_list}"
            self.system_log_tab.append_system_log(f"必填参数验证失败: {', '.join(missing_params)}", "error")

            if hasattr(self, 'show_custom_message'):
                self.show_custom_message("参数验证失败", error_msg)
            else:
                
                from PySide6.QtWidgets import QMessageBox
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("参数验证失败")
                msg_box.setText(error_msg)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.exec()
            return
        
        params = current_tab.get_all_params()

        user_command = self.command_input.text().strip()
        if not user_command:
            self.system_log_tab.append_system_log("请输入工具运行命令", "error")
            return

        tool_path = os.path.join("tools", self.tool_name)
        
        try:
            command = build_cross_platform_command(tool_path, user_command, params)
        except ValueError as e:
            self.system_log_tab.append_system_log(str(e), "error")
            return
        except Exception as e:
            self.system_log_tab.append_system_log(f"构建命令时发生错误: {e}", "error")
            return
        
        self.system_log_tab.append_system_log(f"工具 {self.tool_name} 启动", "info")
        self.system_log_tab.append_system_log(f"执行命令: {' '.join(command)}", "info")

        if self.new_tab_toggle.isChecked():

            process_tab = ProcessTab(None, f"进程{len(self.processes) + 1}", self.process_tabs)
            tab_index = self.process_tabs.addTab(process_tab, f"进程{len(self.processes) + 1}")
            self.process_tabs.setCurrentIndex(tab_index)
            process_tab.set_as_current_tab(True)
        else:

            current_index = self.process_tabs.currentIndex()
            current_tab_text = self.process_tabs.tabText(current_index) if current_index >= 0 else ""

            if current_index < 0 or "系统日志" in current_tab_text:

                process_tab = ProcessTab(None, f"进程{len(self.processes) + 1}", self.process_tabs)
                tab_index = self.process_tabs.addTab(process_tab, f"进程{len(self.processes) + 1}")
                self.process_tabs.setCurrentIndex(tab_index)
                process_tab.set_as_current_tab(True)
            else:

                process_tab = self.process_tabs.widget(current_index)

                if hasattr(process_tab, 'process') and process_tab.process:
                    process_tab.stop_process()

                process_tab.clear_terminal()
                if isinstance(process_tab, ProcessTab):
                    process_tab.set_as_current_tab(True)

        process_tab.append_system_log(f"开始运行工具: {self.tool_name}", "info")
        process_tab.append_system_log(f"执行命令: {' '.join(command)}", "info")
        process_tab.append_system_log("您可以在下方输入命令与程序交互", "info")

        venv_path = self.venv_input.text().strip()
        custom_env = self.env_input.text().strip()
        env = os.environ.copy()

        if venv_path:

            if os.name == "nt":
                venv_bin = os.path.join(venv_path, "Scripts")
            else:
                venv_bin = os.path.join(venv_path, "bin")
            env["PATH"] = venv_bin + os.pathsep + env.get("PATH", "")
            env["VIRTUAL_ENV"] = venv_path

        if custom_env:
            for pair in custom_env.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    k = k.strip()
                    v = v.strip()

                    if k.upper() == "PATH":
                        if "%PATH%" in v:
                            v = v.replace("%PATH%", env.get("PATH", ""))
                        if "$PATH" in v:
                            v = v.replace("$PATH", env.get("PATH", ""))
                        env["PATH"] = v
                    else:
                        env[k] = v

        if venv_path and command[0] in ["python", "python3"]:
            if os.name == "nt":
                venv_python = os.path.join(venv_path, "Scripts", "python.exe")
            else:
                venv_python = os.path.join(venv_path, "bin", "python")
            if os.path.exists(venv_python):
                command[0] = venv_python
            else:
                self.system_log_tab.append_system_log(f"虚拟环境python未找到: {venv_python}", "warning")
        
        process = ToolProcess(self, process_tab)
        process_tab.process = process
        process.setEnvironment([f"{k}={v}" for k, v in env.items()])
        process.start(command[0], command[1:])

        process_tab.show_prompt()
        self.optimize_all_tabs_cache()
        
        self.processes.append(process)

        process.finished.connect(lambda code, status: self.process_finished(process, code, status))
    
    def process_finished(self, process, exit_code, exit_status):

        try:
            from wct_modules.main_window import MainWindow
            from PySide6.QtWidgets import QApplication, QStyle
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, MainWindow):
                    widget.set_tool_list_item_alert(self.tool_name, alert=True)

                    for i in range(self.process_tabs.count()):
                        tab_widget = self.process_tabs.widget(i)
                        if isinstance(tab_widget, ProcessTab) and tab_widget.process == process:
                            self.process_tabs.setTabIcon(i, QIcon.fromTheme('dialog-warning'))
                            break
                    break
        except Exception as e:
            print(f"[DEBUG] 设置工具列表/标签页高亮失败: {e}")
        
        if exit_code == 0:
            self.system_log_tab.append_system_log(f"进程完成，退出代码: {exit_code}", "success")
        else:
            self.system_log_tab.append_system_log(f"进程完成，退出代码: {exit_code}", "error")

        for i in range(self.process_tabs.count()):
            tab_widget = self.process_tabs.widget(i)
            if isinstance(tab_widget, ProcessTab) and tab_widget.process == process:
                tab_widget.process_finished(exit_code)
                break
    
    def close_process_tab(self, index):
        
        tab_widget = self.process_tabs.widget(index)
        if isinstance(tab_widget, ProcessTab):
            
            tab_widget.stop_process()
            self.system_log_tab.append_system_log("进程标签页关闭，进程已终止", "warning")

        self.process_tabs.removeTab(index)
    
    def save_command(self):
        
        command = self.command_input.text().strip()
        self.command_history[self.tool_name] = command
        
        try:
            import json
            with open("command_history.json", "w", encoding="utf-8") as f:
                json.dump(self.command_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存命令历史失败: {e}")
    
    def load_command_history(self):
        
        try:
            import json
            with open("command_history.json", "r", encoding="utf-8") as f:
                self.command_history = json.load(f)

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
            print(f"加载命令历史失败: {e}")
    
    def open_template_manager(self):
        
        template_manager = TemplateManager(self.tool_name, self)
        template_manager.exec()
    
    def update_tab_toggle_text(self, checked):
        
        if checked:
            self.new_tab_toggle.setText(t('messages.run_mode_new_tab'))
        else:
            self.new_tab_toggle.setText(t('messages.run_mode_current_tab'))
    
    def clear_all_params(self):

        current_tab = self.param_tabs.currentWidget()
        if not current_tab:
            self.system_log_tab.append_system_log(t('messages.no_tab_selected'), "warning")
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
        
        self.system_log_tab.append_system_log(t('messages.cleared_params', cleared_count), "info")

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
                self.system_log_tab.append_system_log(t('messages.config_backed_up', backup_path), "info")

            with open(config_path, 'w', encoding='utf-8') as f:
                
                if '常用参数' in self.config_data:
                    f.write("%常用参数\n")
                    self._write_section_to_file(f, self.config_data['常用参数'])
                    f.write("\n")

                if '全部参数' in self.config_data:
                    f.write("%全部参数\n")
                    self._write_section_to_file(f, self.config_data['全部参数'])
            
            self.system_log_tab.append_system_log(f"配置文件已保存到: {config_path}", "success")
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"保存配置文件失败: {e}", "error")
            import traceback
            self.system_log_tab.append_system_log(f"详细错误: {traceback.format_exc()}", "error")
    
    def _write_section_to_file(self, file, section_data):
        
        for subsection_name, params in section_data.items():
            if subsection_name in ['勾选项区', '输入框区']:
                if subsection_name == '勾选项区':
                    file.write("%%勾选项\n")
                elif subsection_name == '输入框区':
                    file.write("%%输入项\n")
                
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

        for section_name in ['常用参数', '全部参数']:
            if section_name in self.config_data:
                for subsection_name in ['勾选项区', '输入框区']:
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
            subsection = '勾选项区' if param_type == '1' else '输入框区'

            if (from_section in self.config_data and 
                subsection in self.config_data[from_section]):
                
                params_list = self.config_data[from_section][subsection]
                for i, param in enumerate(params_list):
                    if param['param_name'] == param_info['param_name']:
                        removed_param = params_list.pop(i)
                        break
                else:
                    self.system_log_tab.append_system_log(f"在{from_section}中未找到参数", "error")
                    return

            if to_section not in self.config_data:
                self.config_data[to_section] = {}
            if subsection not in self.config_data[to_section]:
                self.config_data[to_section][subsection] = []

            target_params = self.config_data[to_section][subsection]
            for param in target_params:
                if param['param_name'] == param_info['param_name']:
                    self.system_log_tab.append_system_log(f"目标区域已存在同名参数", "warning")
                    
                    self.config_data[from_section][subsection].append(removed_param)
                    return

            self.config_data[to_section][subsection].append(removed_param)

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"参数 '{param_info['display_name']}' 已从{from_section}移动到{to_section}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"移动参数失败: {e}", "error")
    
    def add_parameter_to_section(self, param_info, section_title):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())

            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'

            if current_tab_name in self.config_data:
                if subsection in self.config_data[current_tab_name]:
                    for existing_param in self.config_data[current_tab_name][subsection]:
                        if existing_param['param_name'] == param_info['param_name']:
                            self.system_log_tab.append_system_log(f"参数名 '{param_info['param_name']}' 已存在", "error")
                            return

            if current_tab_name not in self.config_data:
                self.config_data[current_tab_name] = {}
            if subsection not in self.config_data[current_tab_name]:
                self.config_data[current_tab_name][subsection] = []
            
            self.config_data[current_tab_name][subsection].append(param_info)

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"新参数 '{param_info['display_name']}' 已添加到{current_tab_name}", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"添加参数失败: {e}", "error")
    
    def update_parameter_in_config(self, old_param_name, new_param_info):
        
        try:
            
            param_type = new_param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'

            for section_name in ['常用参数', '全部参数']:
                if section_name in self.config_data:
                    for subsection_name in ['勾选项区', '输入框区']:
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
                f"参数 '{new_param_info['display_name']}' 信息已更新", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"更新参数信息失败: {e}", "error")
    
    def remove_parameter_from_common(self, param_info):
        
        try:
            
            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'

            if ('常用参数' in self.config_data and 
                subsection in self.config_data['常用参数']):
                
                params_list = self.config_data['常用参数'][subsection]
                for i, param in enumerate(params_list):
                    if param['param_name'] == param_info['param_name']:
                        removed_param = params_list.pop(i)
                        break
                else:
                    self.system_log_tab.append_system_log(f"在常用参数中未找到参数", "error")
                    return

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"参数 '{param_info['display_name']}' 已从常用参数中移除", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"移除参数失败: {e}", "error")
    
    def copy_parameter_to_common(self, param_info):
        
        try:
            
            param_type = param_info['type']
            subsection = '勾选项区' if param_type == '1' else '输入框区'

            if '常用参数' not in self.config_data:
                self.config_data['常用参数'] = {}
            if subsection not in self.config_data['常用参数']:
                self.config_data['常用参数'][subsection] = []

            params_list = self.config_data['常用参数'][subsection]
            for param in params_list:
                if param['param_name'] == param_info['param_name']:
                    self.system_log_tab.append_system_log(f"常用参数中已存在该参数", "warning")
                    return

            param_copy = param_info.copy()
            params_list.append(param_copy)

            self.save_and_reload_ui()

            self.system_log_tab.append_system_log(
                f"参数 '{param_info['display_name']}' 已添加到常用参数", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"添加参数到常用参数失败: {e}", "error")
    
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
        
        cancel_btn = QPushButton("取消")
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
        
        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(s(90), s(40))
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

                    for other_tab_name in ['常用参数', '全部参数']:
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
                f"已同步 {section_title} 的参数顺序到全局配置", 
                "success"
            )
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"同步参数顺序失败: {e}", "error")
    
    def remove_parameter_from_section(self, param_name, section_name):
        
        try:
            
            current_tab_name = self.param_tabs.tabText(self.param_tabs.currentIndex())

            for subsection_name in ['勾选项区', '输入框区']:
                if (current_tab_name in self.config_data and 
                    subsection_name in self.config_data[current_tab_name]):
                    
                    params_list = self.config_data[current_tab_name][subsection_name]
                    for i, param in enumerate(params_list):
                        if param['param_name'] == param_name:
                            removed_param = params_list.pop(i)
                            
                            self.system_log_tab.append_system_log(
                                f"参数 '{param['display_name']}' 已从 {section_name} 中移除", 
                                "info"
                            )
                            return removed_param
            
            return None
            
        except Exception as e:
            self.system_log_tab.append_system_log(f"移除参数失败: {e}", "error")
            return None
    
    def move_parameter_between_sections(self, param_info, from_section_title, to_section_title):
        
        current_tab = self.param_tabs.currentWidget()
        if not hasattr(current_tab, 'config_data'):
            return

        from_key = '勾选项区' if from_section_title == t('tabs.checkbox_params') else '输入框区'
        to_key = '勾选项区' if to_section_title == t('tabs.checkbox_params') else '输入框区'
        new_type = '1' if to_key == '勾选项区' else '2'

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
        dialog.setMinimumSize(s(450), s(240))
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
        icon_map = {"成功": "✅", "完成": "✅", "错误": "❌", "失败": "❌", "提示": "💡", "信息": "💡"}
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
        
        ok_btn = QPushButton("确定")
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
        dialog.setMinimumSize(s(520), s(300))
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

        cancel_btn = QPushButton("取消")
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

        ok_btn = QPushButton("确定")
        ok_btn.setMinimumSize(s(90), s(40))
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
        """
        获取当前标签页中所有参数的配置，用于保存为模板。
        """
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
        """
        将模板中的参数应用到当前界面。
        """
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
                        print(f"Error applying template for param {param_name}: {e}")

        current_tab.update_all_required_styles()
        return applied_count

    def on_process_tab_clicked(self, index):
        
        self.process_tabs.setTabIcon(index, QIcon())
        has_remaining_alerts = False
        for i in range(self.process_tabs.count()):
            if i != index:
                tab_icon = self.process_tabs.tabIcon(i)
                if not tab_icon.isNull():
                    has_remaining_alerts = True
                    break
        if not has_remaining_alerts:
            try:
                from wct_modules.main_window import MainWindow
                from PySide6.QtWidgets import QApplication
                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, MainWindow):
                        widget.set_tool_list_item_alert(self.tool_name, alert=False)
                        break
            except Exception as e:
                print(f"[DEBUG] 自动清除工具列表警示失败: {e}")
    
    def on_tab_changed(self, index):
        for i in range(self.process_tabs.count()):
            tab_widget = self.process_tabs.widget(i)
            if isinstance(tab_widget, ProcessTab):
                tab_widget.set_as_current_tab(False)
        if index >= 0:
            current_tab = self.process_tabs.widget(index)
            if isinstance(current_tab, ProcessTab):
                current_tab.set_as_current_tab(True)
                cache_status = current_tab.get_cache_status()
                if cache_status['cached_items'] > 0:
                    self.system_log_tab.append_system_log(
                        f"标签页切换：刷新了 {cache_status['cached_items']} 条缓存输出", 
                        "info"
                    )

    def get_performance_statistics(self):
        
        stats = {
            'total_tabs': self.process_tabs.count(),
            'active_tabs': 0,
            'cached_tabs': 0,
            'total_cached_items': 0,
            'cache_enabled_tabs': 0,
            'total_compressed_items': 0,
            'total_memory_saved_mb': 0,
            'average_compression_ratio': 0
        }
        
        compression_ratios = []
        total_original_size = 0
        total_compressed_size = 0
        
        for i in range(self.process_tabs.count()):
            tab_widget = self.process_tabs.widget(i)
            if isinstance(tab_widget, ProcessTab):
                cache_status = tab_widget.get_cache_status()
                
                if cache_status['is_current_tab']:
                    stats['active_tabs'] += 1
                    
                if cache_status['cached_items'] > 0:
                    stats['cached_tabs'] += 1
                    stats['total_cached_items'] += cache_status['cached_items']
                    
                if cache_status['cache_enabled']:
                    stats['cache_enabled_tabs'] += 1
                
                if cache_status.get('compressed_items', 0) > 0:
                    stats['total_compressed_items'] += cache_status['compressed_items']
                    
                    if cache_status.get('compression_ratio', 0) > 0:
                        compression_ratios.append(cache_status['compression_ratio'])
                    original_size = cache_status.get('original_size', 0)
                    compressed_size = cache_status.get('total_text_size', 0)
                    total_original_size += original_size
                    total_compressed_size += compressed_size
        if compression_ratios:
            stats['average_compression_ratio'] = round(sum(compression_ratios) / len(compression_ratios), 2)
        
        if total_original_size > 0:
            memory_saved_bytes = total_original_size - total_compressed_size
            stats['total_memory_saved_mb'] = round(memory_saved_bytes / (1024 * 1024), 2)
        
        return stats
    
    def optimize_all_tabs_cache(self):
        
        current_index = self.process_tabs.currentIndex()
        optimized_count = 0
        
        for i in range(self.process_tabs.count()):
            tab_widget = self.process_tabs.widget(i)
            if isinstance(tab_widget, ProcessTab):

                is_current = (i == current_index)
                tab_widget.set_as_current_tab(is_current)
                if not tab_widget.output_cache_enabled:
                    tab_widget.set_cache_enabled(True)
                    optimized_count += 1
        
        if optimized_count > 0:
            self.system_log_tab.append_system_log(
                f"已优化 {optimized_count} 个标签页的缓存设置", 
                "success"
            )
        stats = self.get_performance_statistics()
        self.system_log_tab.append_system_log(
            f"性能统计: {stats['active_tabs']}个活跃标签页, {stats['cached_tabs']}个缓存标签页, 共{stats['total_cached_items']}条缓存", 
            "info"
        )
        
        if stats['total_compressed_items'] > 0:
            self.system_log_tab.append_system_log(
                f"压缩统计: {stats['total_compressed_items']}条压缩数据, 平均压缩率{stats['average_compression_ratio']}%, 节省内存{stats['total_memory_saved_mb']}MB", 
                "success"
            )

    def load_env_config(self):
        
        tool_env_path = os.path.join("tools", self.tool_name, "env_config.json")
        global_env_path = "global_env_config.json"
        config = {"venv_path": "", "custom_env": ""}
        if os.path.exists(tool_env_path):
            try:
                with open(tool_env_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config.update(data)
            except Exception as e:
                print(f"[DEBUG] 读取工具独立env_config.json失败: {e}")
        elif os.path.exists(global_env_path):
            try:
                with open(global_env_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    config.update(data)
            except Exception as e:
                print(f"[DEBUG] 读取全局global_env_config.json失败: {e}")
        self.venv_input.setText(config.get("venv_path", ""))
        self.env_input.setText(config.get("custom_env", ""))

    def save_env_config(self):
        
        tool_env_path = os.path.join("tools", self.tool_name, "env_config.json")
        config = {
            "venv_path": self.venv_input.text().strip(),
            "custom_env": self.env_input.text().strip()
        }
        try:
            with open(tool_env_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[DEBUG] 保存env_config.json失败: {e}")
