import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGroupBox, QFrame, QGridLayout, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QFont, QDesktopServices
from .theme import colors, fonts, params
from .utils import s
from .i18n import t

class PromotionPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_file = "promotion_config.json"
        self.ads_enabled = self.load_ads_config()
        
        QTimer.singleShot(0, self.setup_ui)
    
    def load_ads_config(self):
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('ads_enabled', True)
        except:
            pass
        return True
    
    def save_ads_config(self):
        
        try:
            config = {'ads_enabled': self.ads_enabled}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{t('save_promotion_failed')}: {e}")
    
    def setup_ui(self):
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(24), s(24), s(24), s(24))
        layout.setSpacing(s(24))

        header_widget = QWidget()
        header_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #f8f9fa);
                border: 1px solid #e9ecef;
                border-radius: {s(12)}px;
                padding: {s(4)}px;
            }}
        """)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(s(20), s(16), s(20), s(16))
        header_layout.setSpacing(s(16))

        title_text = t("white_cat_toolbox") if not self.ads_enabled else t("promotion_info")
        self.title_label = QLabel(title_text)
        self.title_label.setFont(QFont(fonts["system"], s(16), QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: #2c3e50;
                background: transparent;
                border: none;
                font-weight: 700;
            }}
        """)
        header_layout.addStretch()
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.ads_toggle_btn = QPushButton(t("close_promotion") if self.ads_enabled else t("enable_promotion"))
        self.ads_toggle_btn.setFont(QFont(fonts["system"], s(10), QFont.Bold))
        self.ads_toggle_btn.setMinimumHeight(s(36))
        self.ads_toggle_btn.setMinimumWidth(s(100))
        self.ads_toggle_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.ads_toggle_btn.setCursor(Qt.PointingHandCursor)
        
        self.update_toggle_button_style()
        self.ads_toggle_btn.clicked.connect(self.toggle_ads)
        header_layout.addWidget(self.ads_toggle_btn)
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)

        self.content_widget = QWidget()
        self.setup_content()
        layout.addWidget(self.content_widget)
        
        self.setLayout(layout)
    
    def setup_content(self):

        if self.content_widget.layout():
            old_layout = self.content_widget.layout()
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            QWidget().setLayout(old_layout)
        
        if not self.ads_enabled:

            self.setup_product_intro()
            return

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(s(20))

        left_ad = self.create_enhanced_ad_widget("promotion/xm.txt", t("project_recommendations"))
        layout.addWidget(left_ad, 1)

        sponsor_widget = self.create_enhanced_sponsor_widget("promotion/zz.txt")
        layout.addWidget(sponsor_widget, 1)

        right_ad = self.create_enhanced_ad_widget("promotion/gg.txt", t("sponsors"))
        layout.addWidget(right_ad, 1)
        
        self.content_widget.setLayout(layout)
    
    def setup_product_intro(self):
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(20), s(20), s(20), s(20))
        layout.setSpacing(s(20))

        intro_text = QLabel(f"""{t('welcome_to_toolbox')}

{t('toolbox_description')}

{t('main_features')}
{t('feature_1')}
{t('feature_2')}
{t('feature_3')}
{t('feature_4')}

{t('thank_you_using')}!""")
        
        intro_text.setFont(QFont(fonts["system"], s(12)))
        intro_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        intro_text.setWordWrap(True)
        intro_text.setStyleSheet(f"""
            QLabel {{
                color: #495057;
                background: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: {s(8)}px;
                padding: {s(20)}px;
                line-height: 1.6;
            }}
        """)
        layout.addWidget(intro_text)

        layout.addStretch()
        
        self.content_widget.setLayout(layout)

    def create_enhanced_ad_widget(self, file_path, title):
        
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafbfc);
                border: 1px solid #e1e8ed;
                border-radius: {s(12)}px;
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_header = QWidget()
        title_header.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a90e2, stop: 1 #357abd);
                border-top-left-radius: {s(12)}px;
                border-top-right-radius: {s(12)}px;
                border-bottom: 1px solid #2c5aa0;
            }}
        """)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(s(16), s(12), s(16), s(12))
        
        title_label = QLabel(title)
        title_label.setFont(QFont(fonts["system"], s(12), QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        title_header.setLayout(title_layout)
        main_layout.addWidget(title_header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        scroll_content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(s(12))
        content_layout.setContentsMargins(s(16), s(16), s(16), s(16))
        content_layout.setAlignment(Qt.AlignTop)

        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    if lines:
                        for line in lines:
                            line = line.strip()
                            if line:
                                item_widget = self.create_enhanced_promotion_item(line)
                                if item_widget:
                                    content_layout.addWidget(item_widget)
                    else:
                        content_layout.addWidget(self.create_empty_state(t("no_promotion_content")))
            else:
                content_layout.addWidget(self.create_empty_state(t("promotion_file_not_exist")))
                
        except Exception as e:
            content_layout.addWidget(self.create_empty_state(f"{t('read_failed')}: {str(e)}"))
        
        content_layout.addStretch()
        scroll_content.setLayout(content_layout)
        scroll_area.setWidget(scroll_content)
        
        main_layout.addWidget(scroll_area)
        widget.setLayout(main_layout)
        
        return widget
    
    def create_enhanced_sponsor_widget(self, file_path):
        
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #ffffff, stop: 1 #fafbfc);
                border: 1px solid #e1e8ed;
                border-radius: {s(12)}px;
            }}
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_header = QWidget()
        title_header.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #28a745, stop: 1 #218838);
                border-top-left-radius: {s(12)}px;
                border-top-right-radius: {s(12)}px;
                border-bottom: 1px solid #1e7e34;
            }}
        """)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(s(16), s(12), s(16), s(12))
        
        title_label = QLabel(t("sponsor_acknowledgments"))
        title_label.setFont(QFont(fonts["system"], s(12), QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
            }
        """)
        title_layout.addStretch()
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        title_header.setLayout(title_layout)
        main_layout.addWidget(title_header)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(s(16), s(16), s(16), s(16))
        content_layout.setSpacing(s(16))
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    sponsor_data = self.parse_sponsor_data(f.readlines())
                    
                    if sponsor_data["ranking"]:
                        ranking_widget = self.create_ranking_widget(sponsor_data["ranking"])
                        content_layout.addWidget(ranking_widget)
                    
                    if sponsor_data["history"]:
                        history_widget = self.create_history_widget(sponsor_data["history"][:10])
                        content_layout.addWidget(history_widget)
            else:
                content_layout.addWidget(self.create_empty_state(t("acknowledgment_file_not_exist")))
                
        except Exception as e:
            content_layout.addWidget(self.create_empty_state(f"{t('loading_failed')}: {e}"))
        
        content_layout.addStretch()
        main_layout.addLayout(content_layout)
        widget.setLayout(main_layout)
        
        return widget
    
    def create_enhanced_promotion_item(self, line):
        
        try:
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                name, url, description = parts[0], parts[1], parts[2]
                
                item_widget = QWidget()
                item_widget.setStyleSheet(f"""
                    QWidget {{
                        background-color: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: {s(8)}px;
                        padding: {s(2)}px;
                    }}
                    QWidget:hover {{
                        background-color: #e3f2fd;
                        border-color: #4a90e2;
                    }}
                """)
                
                layout = QVBoxLayout()
                layout.setSpacing(s(8))
                layout.setContentsMargins(s(12), s(12), s(12), s(12))

                header_layout = QHBoxLayout()
                header_layout.setSpacing(s(8))
                
                name_label = QLabel(name)
                name_label.setFont(QFont(fonts["system"], s(11), QFont.Bold))
                name_label.setWordWrap(True)
                name_label.setStyleSheet("""
                    QLabel {
                        color: #2c3e50;
                        background: transparent;
                        border: none;
                    }
                """)
                header_layout.addWidget(name_label)
                
                header_layout.addStretch()
                
                link_btn = QPushButton(t("visit"))
                link_btn.setMinimumSize(s(60), s(28))
                link_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                link_btn.setCursor(Qt.PointingHandCursor)
                link_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: {s(4)}px;
                        font-weight: 600;
                        font-size: {s(9)}pt;
                    }}
                    QPushButton:hover {{ background-color: #357abd; }}
                    QPushButton:pressed {{ background-color: #2c5aa0; }}
                """)
                link_btn.clicked.connect(lambda: self.open_url(url))
                header_layout.addWidget(link_btn)
                
                layout.addLayout(header_layout)

                if description:
                    desc_label = QLabel(description)
                    desc_label.setFont(QFont(fonts["system"], s(9)))
                    desc_label.setWordWrap(True)
                    desc_label.setStyleSheet("""
                        QLabel {
                            color: #6c757d;
                            background: transparent;
                            border: none;
                            line-height: 1.4;
                        }
                    """)
                    layout.addWidget(desc_label)
                
                item_widget.setLayout(layout)
                return item_widget
            else:
                return self.create_empty_state(f"{t('format_error')}: {line}")
                
        except Exception as e:
            return None
    
    def create_empty_state(self, message):
        
        empty_widget = QWidget()
        empty_widget.setStyleSheet(f"""
            QWidget {{
                background-color: #f8f9fa;
                border: 1px dashed #ced4da;
                border-radius: {s(8)}px;
                padding: {s(12)}px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        empty_label = QLabel(message)
        empty_label.setFont(QFont(fonts["system"], s(10)))
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(empty_label)
        
        empty_widget.setLayout(layout)
        return empty_widget
    
    def create_ad_widget(self, file_path):
        
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
            }}
        """)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        scroll_content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(s(8))
        layout.setContentsMargins(s(5), s(5), s(5), s(5))
        layout.setAlignment(Qt.AlignTop)

        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    if lines:
                        for line in lines:
                            line = line.strip()
                            if line:  
                                item_widget = self.create_promotion_item(line)
                                if item_widget:
                                    layout.addWidget(item_widget)
                    else:
                        
                        empty_label = QLabel(t("no_promotion_content"))
                        empty_label.setFont(QFont(fonts["system"], s(10)))
                        empty_label.setAlignment(Qt.AlignCenter)
                        empty_label.setStyleSheet(f"""
                            QLabel {{
                                color: {colors["text_disabled"]};
                                padding: {s(20)}px;
                            }}
                        """)
                        layout.addWidget(empty_label)
            else:
                
                error_label = QLabel(t("promotion_file_path_not_exist").format(file_path=file_path))
                error_label.setFont(QFont(fonts["system"], s(10)))
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors["danger"]};
                        padding: {s(20)}px;
                    }}
                """)
                layout.addWidget(error_label)
        
        except Exception as e:
            
            error_label = QLabel(f"{t('read_promotion_content_failed')}: {str(e)}")
            error_label.setFont(QFont(fonts["system"], s(10)))
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["danger"]};
                    padding: {s(20)}px;
                }}
            """)
            layout.addWidget(error_label)
        
        layout.addStretch()
        scroll_content.setLayout(layout)
        scroll_area.setWidget(scroll_content)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(s(15), s(15), s(15), s(15))
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll_area)
        widget.setLayout(main_layout)
        
        return widget
    
    def create_sponsor_widget(self, file_path):
        
        group_box = QGroupBox(t("sponsor_acknowledgments").replace("💎 ", ""))
        group_box.setStyleSheet(f"""
            QGroupBox {{
                background-color: {colors["white"]};
                border: 1px solid {colors["background_gray"]};
                border-radius: {params["border_radius_small"]};
                margin-top: {s(20)}px;
                font-family: "{fonts["system"]}";
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: {s(5)}px {s(15)}px;
                background-color: {colors["secondary"]};
                color: {colors["white"]};
                border-radius: {params["border_radius_very_small"]};
                font-weight: bold;
            }}
        """)

        sponsor_layout = QVBoxLayout()
        sponsor_layout.setSpacing(s(10))
        sponsor_layout.setContentsMargins(s(15), s(30), s(15), s(15))
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    sponsor_data = self.parse_sponsor_data(f.readlines())
                    
                    if sponsor_data["ranking"]:
                        ranking_widget = self.create_ranking_widget(sponsor_data["ranking"])
                        sponsor_layout.addWidget(ranking_widget)
                        
                        separator = QFrame()
                        separator.setFrameShape(QFrame.HLine)
                        separator.setFrameShadow(QFrame.Sunken)
                        separator.setFixedHeight(s(1))
                        separator.setStyleSheet(f"background-color: {colors['background_gray']};")
                        sponsor_layout.addWidget(separator)

                    if sponsor_data["history"]:
                        history_widget = self.create_history_widget(sponsor_data["history"][:8])
                        sponsor_layout.addWidget(history_widget)

            else:
                error_label = QLabel(t("acknowledgment_file_path_not_exist").format(file_path=file_path))
                error_label.setFont(QFont(fonts["system"], s(10)))
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet(f"""
                    QLabel {{
                        color: {colors["danger"]};
                        padding: {s(20)}px;
                    }}
                """)
                sponsor_layout.addWidget(error_label)
                
        except Exception as e:
            error_label = QLabel(f"{t('load_acknowledgments_failed')}: {e}")
            error_label.setFont(QFont(fonts["system"], s(10)))
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors["danger"]};
                    padding: {s(20)}px;
                }}
            """)
            sponsor_layout.addWidget(error_label)

        group_box.setLayout(sponsor_layout)
        return group_box
    
    def parse_sponsor_data(self, lines):
        
        ranking_data = []
        history_data = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith(t("ranking")):
                current_section = "ranking"
                continue
            elif line.startswith(t("sponsor_history")):
                current_section = "history"
                continue
            elif line.startswith(t("time")):
                continue  

            parts = line.split('\t')
            if len(parts) >= 3:
                if current_section == "ranking":
                    ranking_data.append({
                        'rank': parts[0],
                        'name': parts[1], 
                        'amount': parts[2]
                    })
                elif current_section == "history":
                    history_data.append({
                        'time': parts[0],
                        'name': parts[1],
                        'amount': parts[2]
                    })
        
        return {
            "ranking": ranking_data,
            "history": history_data
        }
    
    def create_ranking_widget(self, ranking_data):
        
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: {s(8)}px;
                margin: {s(4)}px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(12), s(10), s(12), s(10))
        layout.setSpacing(s(8))

        title = QLabel(t("leaderboard"))
        title.setFont(QFont(fonts["system"], s(10), QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: #495057;
                background: transparent;
                border: none;
                padding: {s(4)}px 0px;
            }}
        """)
        layout.addWidget(title)

        for item in ranking_data[:5]:  
            rank_layout = QHBoxLayout()
            rank_layout.setContentsMargins(s(4), s(2), s(4), s(2))
            rank_layout.setSpacing(s(8))

            rank_icon = QLabel()
            rank_num = item['rank']
            if rank_num == '1':
                rank_icon.setText("🥇")
            elif rank_num == '2':
                rank_icon.setText("🥈")
            elif rank_num == '3':
                rank_icon.setText("🥉")
            else:
                rank_icon.setText(f"{rank_num}.")
            rank_icon.setFixedWidth(s(32))
            rank_icon.setFont(QFont(fonts["system"], s(10), QFont.Bold))
            rank_icon.setStyleSheet("QLabel { background: transparent; border: none; }")
            rank_layout.addWidget(rank_icon)

            name_label = QLabel(item['name'])
            name_label.setFont(QFont(fonts["system"], s(10), QFont.Bold))
            name_label.setStyleSheet("QLabel { color: #495057; background: transparent; border: none; }")
            rank_layout.addWidget(name_label)
            
            rank_layout.addStretch()

            amount_label = QLabel(f"¥{item['amount']}")
            amount_label.setFont(QFont(fonts["system"], s(10), QFont.Bold))
            amount_label.setStyleSheet("QLabel { color: #28a745; background: transparent; border: none; }")
            rank_layout.addWidget(amount_label)
            
            layout.addLayout(rank_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_history_widget(self, history_data):
        
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: {s(8)}px;
                margin: {s(4)}px;
            }}
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(s(12), s(10), s(12), s(10))
        layout.setSpacing(s(8))

        title = QLabel(t("recent_sponsors"))
        title.setFont(QFont(fonts["system"], s(10), QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: #495057;
                background: transparent;
                border: none;
                padding: {s(4)}px 0px;
            }}
        """)
        layout.addWidget(title)

        for item in history_data:
            history_layout = QVBoxLayout()
            history_layout.setContentsMargins(s(4), s(2), s(4), s(2))
            history_layout.setSpacing(s(1))

            top_layout = QHBoxLayout()
            top_layout.setSpacing(s(8))
            
            name_label = QLabel(item['name'])
            name_label.setFont(QFont(fonts["system"], s(8), QFont.Bold))
            name_label.setStyleSheet("QLabel { color: #495057; background: transparent; border: none; }")
            top_layout.addWidget(name_label)
            
            top_layout.addStretch()
            
            amount_label = QLabel(f"¥{item['amount']}")
            amount_label.setFont(QFont(fonts["system"], s(8), QFont.Bold))
            amount_label.setStyleSheet("QLabel { color: #28a745; background: transparent; border: none; }")
            top_layout.addWidget(amount_label)

            time_label = QLabel(item['time'])
            time_label.setFont(QFont(fonts["system"], s(7)))
            time_label.setStyleSheet("QLabel { color: #6c757d; background: transparent; border: none; }")
            
            history_layout.addLayout(top_layout)
            history_layout.addWidget(time_label)
            
            layout.addLayout(history_layout)
        
        widget.setLayout(layout)
        return widget
    
    def create_promotion_item(self, line):
        
        try:
            parts = line.split(' ', 2)  
            if len(parts) >= 3:
                name, url, description = parts[0], parts[1], parts[2]

                item_widget = QWidget()
                item_widget.setMinimumHeight(s(70))  
                item_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                item_widget.setStyleSheet(f"""
                    QWidget {{
                        background-color: {colors["background_very_light"]};
                        border-radius: {params["border_radius_very_small"]};
                        border: 1px solid {colors["background_gray"]};
                        padding: {s(8)}px;
                    }}
                    QWidget:hover {{
                        background-color: {colors["list_item_hover_background"]};
                        border-color: {colors["secondary"]};
                    }}
                """)
                
                layout = QVBoxLayout()
                layout.setSpacing(s(8))
                layout.setContentsMargins(s(15), s(12), s(15), s(12))

                header_layout = QHBoxLayout()
                header_layout.setSpacing(s(12))

                name_label = QLabel(name)
                name_label.setFont(QFont(fonts["system"], s(10), QFont.Bold))
                name_label.setWordWrap(True)  
                name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                name_label.setStyleSheet("""
                    QLabel {
                        color: #2c3e50;
                        background: transparent;
                        border: none;
                        padding: {s(4)}px 0px;
                        line-height: 1.3;
                    }
                """)
                header_layout.addWidget(name_label)
                
                header_layout.addStretch()

                link_btn = QPushButton(t("visit"))
                link_btn.setFont(QFont(fonts["system"], s(9)))
                link_btn.setMinimumSize(s(65), s(32))
                link_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                link_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        padding: {s(6)}px {s(10)}px;
                        font-weight: 600;
                        text-align: center;
                    }
                    QPushButton:hover {
                        background-color: #357abd;
                    }
                    QPushButton:pressed {
                        background-color: #2c5aa0;
                    }
                """)
                link_btn.clicked.connect(lambda: self.open_url(url))
                header_layout.addWidget(link_btn)
                
                layout.addLayout(header_layout)

                if description:
                    desc_label = QLabel(description)
                    desc_label.setFont(QFont(fonts["system"], s(9)))
                    desc_label.setWordWrap(True)
                    desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  
                    desc_label.setStyleSheet("""
                        QLabel {
                            color: #6c757d;
                            background: transparent;
                            border: none;
                            padding: {s(4)}px 0px {s(2)}px 0px;
                            line-height: 1.5;
                        }
                    """)
                    layout.addWidget(desc_label)
                
                item_widget.setLayout(layout)
                return item_widget
            else:
                
                error_widget = QWidget()
                error_widget.setMinimumHeight(s(40))
                error_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
                error_widget.setStyleSheet("""
                    QWidget {
                        background-color: #fff3cd;
                        border: 1px solid #ffeaa7;
                        border-radius: 6px;
                        margin: 3px;
                    }
                """)
                layout = QVBoxLayout()
                layout.setContentsMargins(s(12), s(10), s(12), s(10))
                
                error_label = QLabel(f"{t('format_error')}: {line}")
                error_label.setFont(QFont(fonts["system"], s(9)))
                error_label.setStyleSheet("""
                    QLabel {
                        color: #856404;
                        background: transparent;
                        border: none;
                    }
                """)
                layout.addWidget(error_label)
                error_widget.setLayout(layout)
                return error_widget
                
        except Exception as e:
            return None
    
    def open_url(self, url):
        
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"{t('open_link_failed')}: {e}")
    
    def toggle_ads(self):
        
        self.ads_enabled = not self.ads_enabled
        self.save_ads_config()

        self.ads_toggle_btn.setText(t("close_promotion") if self.ads_enabled else t("enable_promotion"))
        self.update_toggle_button_style()

        self.update_header_title()

        self.setup_content()

    def update_header_title(self):
        
        if hasattr(self, 'title_label'):
            title_text = t("white_cat_toolbox") if not self.ads_enabled else t("promotion_info")
            self.title_label.setText(title_text)
    
    def update_toggle_button_style(self):
        if self.ads_enabled:

            style = f"""
                QPushButton {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #dc3545, stop: 1 #c82333);
                    color: white;
                    border: 1px solid #a71e2a;
                    border-radius: {s(8)}px;
                    padding: {s(8)}px {s(16)}px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #e85d6d, stop: 1 #dc3545);
                    border-color: #dc3545;
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #c82333, stop: 1 #a71e2a);
                    border-color: #721c24;
                }}
            """
        else:

            style = f"""
                QPushButton {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #28a745, stop: 1 #218838);
                    color: white;
                    border: 1px solid #1e7e34;
                    border-radius: {s(8)}px;
                    padding: {s(8)}px {s(16)}px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #34ce57, stop: 1 #28a745);
                    border-color: #28a745;
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                              stop: 0 #218838, stop: 1 #1e7e34);
                    border-color: #155724;
                }}
            """
        self.ads_toggle_btn.setStyleSheet(style)
