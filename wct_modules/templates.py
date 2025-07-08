import os
import json
import zipfile
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QWidget, QFrame, QScrollArea, QComboBox,
    QLineEdit, QTextEdit, QGroupBox, QGridLayout, QSpacerItem, QSizePolicy,
    QFileDialog, QMessageBox, QInputDialog, QApplication, QMenu
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QColor
from .utils import get_system_font, get_system_font_css, s
from .i18n import t
from .widgets import ClickableLabel
from .styles import get_modern_qmenu_stylesheet
from .theme import colors

class TemplateManager(QDialog):
    def __init__(self, tool_name, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.parent_page = parent
        self.templates = self.load_templates()
        self.setup_ui()
        self.load_template_list()
        self.setup_global_styles()

    def setup_ui(self):
        self.setWindowTitle(t("templates.manager_title"))
        self.setGeometry(s(150), s(150), s(900), s(600))
        self.setModal(True)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #f5f5f7;
                font-family: '{get_system_font()}', Arial, sans-serif;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(24), s(24), s(24), s(24))
        layout.setSpacing(s(20))
        
        main_card = QWidget()
        main_card.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafbfc);
                border-radius: {s(16)}px;
                border: 1px solid #e1e8ed;
            }}
        """)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(s(24), s(24), s(24), s(24))
        card_layout.setSpacing(s(20))
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(s(16))
        
        title_label = QLabel(t("templates.manager_title"))
        title_label.setFont(QFont(get_system_font(), s(18), QFont.Bold))
        title_label.setStyleSheet(f"""
            QLabel {{
                color: #2c3e50;
                background: transparent;
                border: none;
                font-weight: 700;
                padding: {s(4)}px 0px;
            }}
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        add_btn = QPushButton(t("templates.add_template"))
        add_btn.setMinimumSize(s(110), s(38))
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4A90E2, stop: 1 #357ABD);
                border: 1px solid #2C5AA0;
                border-radius: {s(10)}px;
                padding: {s(8)}px {s(16)}px;
                color: white;
                font-weight: 600;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
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
        add_btn.clicked.connect(self.save_current_params)
        header_layout.addWidget(add_btn)
        
        card_layout.addLayout(header_layout)
        
        self.template_table = QTableWidget()
        self.template_table.setColumnCount(3)
        self.template_table.setHorizontalHeaderLabels([t("templates.template_name"), t("templates.template_remark"), t("templates.operation")])
        
        self.template_table.setStyleSheet(f"""
            QTableWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafafa);
                border: 1px solid #e1e8ed;
                border-radius: {s(12)}px;
                gridline-color: #f0f0f0;
                selection-background-color: transparent;
                font-size: {s(13)}pt;
                outline: none;
                alternate-background-color: #f9f9fa;
            }}
            QTableWidget::item {{
                padding: {s(18)}px {s(16)}px;
                border-bottom: 1px solid #f0f0f0;
                border-right: none;
                border-left: none;
                border-top: none;
                background-color: transparent;
            }}
            QTableWidget::item:hover {{
                background-color: rgba(74, 144, 226, 0.05);
            }}
            QTableWidget::item:selected {{
                background-color: rgba(74, 144, 226, 0.1);
                border-radius: {s(6)}px;
            }}
            /* Ensure button container is not affected by table style */
            QTableWidget QWidget {{
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
            QHeaderView::section {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                color: #495057;
                padding: {s(14)}px {s(16)}px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-right: 1px solid #e5e5ea;
                font-weight: 600;
                font-size: {s(12)}pt;
                text-align: center;
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: {s(12)}px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: {s(12)}px;
            }}
            QHeaderView::section:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
            }}
        """)
        
        self.template_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.template_table.setSelectionMode(QTableWidget.NoSelection)
        self.template_table.verticalHeader().setVisible(False)
        self.template_table.horizontalHeader().setStretchLastSection(False)
        self.template_table.setShowGrid(False)
        self.template_table.setSortingEnabled(False)
        
        self.template_table.verticalHeader().setDefaultSectionSize(s(76))
        
        header = self.template_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)             
        header.setSectionResizeMode(1, QHeaderView.Stretch)           
        header.setSectionResizeMode(2, QHeaderView.Fixed)             
        header.resizeSection(0, s(200))
        header.resizeSection(2, s(150))
        
        card_layout.addWidget(self.template_table)
        
        main_card.setLayout(card_layout)
        layout.addWidget(main_card)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(s(12))
        
        import_btn = QPushButton(t("templates.import_template"))
        import_btn.setMinimumSize(s(110), s(38))
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #f8f9fa, stop: 1 #e9ecef);
                border: 1px solid #ced4da;
                border-radius: {s(10)}px;
                padding: {s(8)}px {s(16)}px;
                color: #495057;
                font-weight: 600;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #e9ecef, stop: 1 #dee2e6);
                border-color: #adb5bd;
                color: #343a40;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dee2e6, stop: 1 #ced4da);
                border-color: #adb5bd;
            }}
        """)
        import_btn.clicked.connect(self.import_template)
        bottom_layout.addWidget(import_btn)

        export_btn = QPushButton(t("templates.export_template"))
        export_btn.setMinimumSize(s(110), s(38))
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(import_btn.styleSheet())
        export_btn.clicked.connect(self.export_template)
        bottom_layout.addWidget(export_btn)

        bottom_layout.addStretch()

        close_btn = QPushButton(t("buttons.close"))
        close_btn.setMinimumSize(s(80), s(38))
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                border: 1px solid #6c757d;
                border-radius: {s(10)}px;
                padding: {s(8)}px {s(16)}px;
                color: #6c757d;
                font-weight: 500;
                font-size: {s(12)}pt;
                font-family: '{get_system_font()}';
            }}
            QPushButton:hover {{
                background-color: #f8f9fa;
                border-color: #5a6268;
                color: #5a6268;
            }}
            QPushButton:pressed {{
                background-color: #e9ecef;
                border-color: #5a6268;
            }}
        """)
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

        self.template_table.itemDoubleClicked.connect(self.on_item_double_clicked)

    def load_templates(self):
        try:
            templates_dir = "templates"
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
            template_file = os.path.join(templates_dir, f"templates_{self.tool_name}.json")
            with open(template_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        except Exception as e:
            print(f"Load template failed: {e}")
            return {}

    def save_templates(self):
        try:
            templates_dir = "templates"
            os.makedirs(templates_dir, exist_ok=True)
            template_file = os.path.join(templates_dir, f"templates_{self.tool_name}.json")
            with open(template_file, "w", encoding="utf-8") as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Save template failed: {e}")
            self.parent_page.show_custom_message(t("messages.error"), t("templates.save_template_error") + f": {e}")

    def load_template_list(self):
        self.template_table.setRowCount(0)
        
        sorted_templates = sorted(self.templates.items(), key=lambda item: item[1].get('create_time', '0'), reverse=True)

        for template_id, template_data in sorted_templates:
            self.add_template_row(template_id, template_data)
    
    def add_template_row(self, template_id, template_data):
        row_position = self.template_table.rowCount()
        self.template_table.insertRow(row_position)
        
        name_text = template_data.get('name', t('labels.unnamed_template'))
        name_item = QTableWidgetItem(name_text)
        name_item.setFont(QFont(get_system_font(), s(12), QFont.Bold))
        name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        name_item.setForeground(QColor("#2c3e50"))
        name_item.setToolTip(t("tooltips.template_name"))
        name_item.setData(Qt.UserRole, template_id)
        self.template_table.setItem(row_position, 0, name_item)
        
        remark_text = template_data.get('remark', t('labels.no_remark'))
        if not remark_text.strip():
            remark_text = t('labels.no_remark')
        remark_item = QTableWidgetItem(remark_text)
        remark_item.setFont(QFont(get_system_font(), s(11), QFont.Normal))
        remark_item.setForeground(QColor("#8e8e93"))
        remark_item.setToolTip(t("tooltips.template_remark"))
        self.template_table.setItem(row_position, 1, remark_item)
        
        button_widget = self.create_button_widget(template_id)
        self.template_table.setCellWidget(row_position, 2, button_widget)

    def create_button_widget(self, template_id):
        widget = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(s(6), s(8), s(6), s(8))
        button_layout.setSpacing(s(6))
        button_layout.setAlignment(Qt.AlignCenter)

        apply_btn = QPushButton(t("templates.apply"))
        apply_btn.setMinimumSize(s(58), s(28))
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors["secondary"]};
                border-radius: {s(6)}px;
                color: white;
                font-weight: 600;
                font-size: {s(10)}pt;
            }}
            QPushButton:hover {{ background-color: {colors["secondary_hover"]}; }}
            QPushButton:pressed {{ background-color: {colors["secondary_pressed"]}; }}
        """)
        apply_btn.clicked.connect(lambda: self.apply_template_by_id(template_id))
        button_layout.addWidget(apply_btn)
        
        delete_btn = QPushButton(t("templates.delete"))
        delete_btn.setMinimumSize(s(58), s(28))
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #dc3545;
                border-radius: {s(6)}px;
                color: white;
                font-weight: 600;
                font-size: {s(10)}pt;
            }}
            QPushButton:hover {{ background-color: #c82333; }}
            QPushButton:pressed {{ background-color: #a71e2a; }}
        """)
        delete_btn.clicked.connect(lambda: self.delete_template_by_id(template_id))
        button_layout.addWidget(delete_btn)
        
        widget.setLayout(button_layout)
        return widget

    def setup_global_styles(self):
        pass

    def on_item_double_clicked(self, item):
        row = item.row()
        name_item = self.template_table.item(row, 0)
        if not name_item:
            return
            
        template_id = name_item.data(Qt.UserRole)
        if template_id not in self.templates:
            return
            
        if item.column() == 0:
            self.edit_template_name(template_id)
        elif item.column() == 1:
            self.edit_template_remark(template_id)

    def save_current_params(self):
        if not self.parent_page:
            QMessageBox.critical(self, t("messages.error"), t("templates.no_parent_reference"))
            return
        
        name, ok = self.parent_page.show_custom_input(t("templates.save_template_title"), t("templates.enter_template_name"), default_text="")
        if not ok or not name.strip():
            return
        
        remark, ok = self.parent_page.show_custom_input(t("templates.save_template_title"), t("templates.enter_template_remark"), default_text="")
        if not ok:
            remark = ""
        
        current_params = self.parent_page.get_all_params_for_template()
        
        if not current_params:
            self.parent_page.show_custom_message(t("messages.hint"), t("templates.no_params_to_save"))
            return

        template_id = f"template_{int(datetime.datetime.now().timestamp())}"
        
        self.templates[template_id] = {
            'name': name.strip(),
            'remark': remark.strip(),
            'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'params': current_params
        }
        
        self.save_templates()
        self.refresh_template_list()
        self.parent_page.show_custom_message(t("templates.template_saved"), t("templates.template_saved_msg").format(name))

    def apply_template_by_id(self, template_id):
        if template_id not in self.templates:
            self.parent_page.show_custom_message(t("messages.error"), t("templates.template_not_found"))
            return
        
        template_data = self.templates[template_id]
        if not self.parent_page.show_custom_question(t("templates.confirm_apply_template"), t("templates.confirm_apply_msg").format(template_data['name'])):
            return
        
        params = template_data.get('params', {})
        applied_count = self.parent_page.apply_params_from_template(params)

        self.templates[template_id]['last_used'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        self.save_templates()
        self.refresh_template_list()
        
        self.parent_page.show_custom_message(t("templates.template_applied"), t("templates.template_applied_msg").format(template_data['name'], applied_count))
        self.close()

    def edit_template_by_id(self, template_id):

        pass

    def edit_template_name(self, template_id):
        if template_id not in self.templates:
            return
        
        old_name = self.templates[template_id].get('name', '')
        new_name, ok = self.parent_page.show_custom_input(t("templates.edit_template_name_title"), t("templates.enter_new_template_name"), default_text=old_name)
        
        if ok and new_name.strip():
            self.templates[template_id]['name'] = new_name.strip()
            self.save_templates()
            self.refresh_template_list()
            self.parent_page.show_custom_message(t("messages.success"), t("templates.template_name_updated"))

    def edit_template_remark(self, template_id):
        if template_id not in self.templates:
            return
        
        old_remark = self.templates[template_id].get('remark', '')
        new_remark, ok = self.parent_page.show_custom_input(t("templates.edit_template_remark_title"), t("templates.enter_new_template_remark"), default_text=old_remark)
        
        if ok:
            self.templates[template_id]['remark'] = new_remark.strip()
            self.save_templates()
            self.refresh_template_list()
            self.parent_page.show_custom_message(t("messages.success"), t("templates.template_remark_updated"))

    def delete_template_by_id(self, template_id):
        if template_id not in self.templates:
            self.parent_page.show_custom_message(t("messages.error"), t("templates.template_not_found_delete"))
            return
        
        template_name = self.templates[template_id].get("name", "this")
        if self.parent_page.show_custom_question(t("templates.confirm_delete_template"), t("templates.confirm_delete_msg").format(template_name)):
            del self.templates[template_id]
            self.save_templates()
            self.refresh_template_list()
            self.parent_page.show_custom_message(t("messages.success"), t("templates.template_deleted_msg").format(template_name))

    def import_template(self):
        file_path, _ = QFileDialog.getOpenFileName(self, t("templates.import_template_title"), "", t("templates.json_files"))
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_templates = {}
            if isinstance(data, dict) and 'templates' in data and 'source_tool' in data:
                 if data['source_tool'] != self.tool_name:
                    if not self.parent_page.show_custom_question(t("templates.tool_mismatch_title"), t("templates.tool_mismatch_msg").format(data['source_tool'], self.tool_name)):
                        return
                 imported_templates = data['templates']
            elif isinstance(data, dict):
                if 'name' in data and 'params' in data:
                    imported_templates = {f"imported_{int(datetime.datetime.now().timestamp())}": data}
                else:
                    imported_templates = data

            if not imported_templates:
                self.parent_page.show_custom_message(t("templates.import_failed"), t("templates.import_failed_msg"))
                return

            merge_count = 0
            new_count = 0
            for t_id, t_data in imported_templates.items():
                if t_id in self.templates:
                    merge_count += 1
                else:
                    new_count += 1
                self.templates[t_id] = t_data

            self.save_templates()
            self.refresh_template_list()
            self.parent_page.show_custom_message(t("templates.import_success"), t("templates.import_success_msg").format(new_count, merge_count))

        except Exception as e:
            self.parent_page.show_custom_message(t("templates.import_failed"), t("templates.import_error").format(e))

    def export_template(self):
        if not self.templates:
            self.parent_page.show_custom_message(t("messages.hint"), t("templates.no_templates_to_export"))
            return

        default_filename = f"templates_{self.tool_name}_{datetime.datetime.now().strftime('%Y%m%d')}.json"
        file_path, _ = QFileDialog.getSaveFileName(self, t("templates.export_template_title"), default_filename, t("templates.json_files"))

        if not file_path:
            return

        try:
            export_data = {
                'source_tool': self.tool_name,
                'export_time': datetime.datetime.now().isoformat(),
                'templates': self.templates
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            self.parent_page.show_custom_message(t("templates.export_success"), t("templates.export_success_msg").format(file_path))
        except Exception as e:
            self.parent_page.show_custom_message(t("templates.export_failed"), t("templates.export_failed_msg").format(e))

    def refresh_template_list(self):
        self.templates = self.load_templates()
        self.load_template_list()

    def show_custom_message(self, title, message, msg_type="info"):
        self.parent_page.show_custom_message(title, message)

    def show_custom_question(self, title, message):
        return self.parent_page.show_custom_question(title, message)

    def show_custom_input(self, title, label, default_text=""):
        text, ok = QInputDialog.getText(self, title, label, QLineEdit.Normal, default_text)
        if ok and text is not None:
            return text.strip(), True
        return "", False
