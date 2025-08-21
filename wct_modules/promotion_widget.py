from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit, 
    QPushButton, QLabel, QMessageBox, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QPixmap, QPalette, QDesktopServices, QColor
import os
import json
import webbrowser
from .font_scale_widget import GlobalFontScaleManager


class PromotionWidget(QWidget):
    """推广界面组件"""
    
    promotion_closed = Signal()
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.promotion_enabled = self.load_promotion_setting()
        

        self.font_scale_manager = GlobalFontScaleManager(config_manager)
        
        self.init_ui()
        self.load_promotion_content()
    
    def get_scaled_font_size(self, base_size):
        """根据全局字体缩放获取缩放后的字体大小"""
        scale = self.font_scale_manager.get_current_scale()
        return max(6, int(base_size * scale))
    
    def create_scaled_font(self, base_size, bold=False, italic=False):
        """创建缩放后的字体对象"""
        from .utils import get_system_font
        system_font = get_system_font()
        font = QFont(system_font)
        font.setPointSize(self.get_scaled_font_size(base_size))
        font.setBold(bold)
        font.setItalic(italic)
        return font
    
    def refresh_fonts(self):
        """刷新所有字体（当字体缩放改变时调用）"""



        pass
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        

        self.three_column_widget = QWidget()
        three_column_layout = QHBoxLayout(self.three_column_widget)
        three_column_layout.setSpacing(15)
        

        self.project_column = self.create_project_column("🚀 项目推荐")
        three_column_layout.addWidget(self.project_column)
        

        self.sponsor_column = self.create_sponsor_column("💰 赞助榜单")
        three_column_layout.addWidget(self.sponsor_column)
        

        self.advertiser_column = self.create_advertiser_column("🏢 赞助企业")
        three_column_layout.addWidget(self.advertiser_column)
        
        self.content_layout.addWidget(self.three_column_widget)
        

        self.intro_widget = self.create_intro_widget()
        

        self.three_column_widget.show()
        self.intro_widget.hide()
        
        layout.addWidget(self.content_widget)
        layout.addWidget(self.intro_widget)
        

        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        self.close_btn = QPushButton("开始使用工具")
        self.close_btn.setFixedSize(140, 45)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a90e2, stop:1 #2e5bb8);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5ba0f2, stop:1 #3e6bc8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a80d2, stop:1 #1e4ba8);
            }
        """)
        self.close_btn.clicked.connect(self.close_promotion)
        
        close_layout.addWidget(self.close_btn)
        close_layout.addStretch()
        
        layout.addLayout(close_layout)
        
    def create_content_column(self, title, bg_color):
        """创建内容列"""
        column = QFrame()
        column.setFrameStyle(QFrame.Box)
        column.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(column)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 5px;
                padding: 8px;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title_label)
        

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMinimumHeight(300)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                font-size: 12px;
                line-height: 1.4;
                padding: 10px;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
        """)
        layout.addWidget(text_edit)
        
        return column
    
    def create_project_column(self, title):
        """创建项目推荐列"""
        column = QFrame()
        column.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
        """)
        

        column.setGraphicsEffect(self.create_shadow())
        
        layout = QVBoxLayout(column)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        

        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(self.create_scaled_font(18, bold=True))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 0px;
                margin: 0px;
                border: none;
                background: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_row.addStretch()
        title_row.addWidget(title_label, 0, Qt.AlignCenter)
        title_row.addStretch()
        layout.addLayout(title_row)
        

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border: none;
                height: 1px;
                margin: 5px 0px;
            }
        """)
        layout.addWidget(separator)
        

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(350)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.project_content_widget = QWidget()
        self.project_layout = QVBoxLayout(self.project_content_widget)
        self.project_layout.setContentsMargins(0, 0, 0, 0)
        self.project_layout.setSpacing(10)
        
        scroll_area.setWidget(self.project_content_widget)
        layout.addWidget(scroll_area)
        
        return column
    
    def create_shadow(self):
        """创建阴影效果"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        return shadow
    
    def create_advertiser_column(self, title):
        """创建赞助企业列"""
        column = QFrame()
        column.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
        """)
        

        column.setGraphicsEffect(self.create_shadow())
        
        layout = QVBoxLayout(column)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        

        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(self.create_scaled_font(18, bold=True))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 0px;
                margin: 0px;
                border: none;
                background: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_row.addStretch()
        title_row.addWidget(title_label, 0, Qt.AlignCenter)
        title_row.addStretch()
        layout.addLayout(title_row)
        

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border: none;
                height: 1px;
                margin: 5px 0px;
            }
        """)
        layout.addWidget(separator)
        

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(350)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.advertiser_content_widget = QWidget()
        self.advertiser_layout = QVBoxLayout(self.advertiser_content_widget)
        self.advertiser_layout.setContentsMargins(0, 0, 0, 0)
        self.advertiser_layout.setSpacing(10)
        
        scroll_area.setWidget(self.advertiser_content_widget)
        layout.addWidget(scroll_area)
        
        return column
    
    def create_sponsor_column(self, title):
        """创建赞助榜单列"""
        column = QFrame()
        column.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: none;
            }
        """)
        

        column.setGraphicsEffect(self.create_shadow())
        
        layout = QVBoxLayout(column)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        

        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(self.create_scaled_font(18, bold=True))
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 0px;
                margin: 0px;
                border: none;
                background: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        title_row.addStretch()
        title_row.addWidget(title_label, 0, Qt.AlignCenter)
        title_row.addStretch()
        layout.addLayout(title_row)
        

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border: none;
                height: 1px;
                margin: 5px 0px;
            }
        """)
        layout.addWidget(separator)
        

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setMinimumHeight(350)
        main_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 8px;
                border-radius: 4px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #95a5a6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        

        main_content = QWidget()
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(20)
        

        ranking_section = QFrame()
        ranking_section.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.7);
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px 0px 15px 0px;
            }
        """)
        ranking_section_layout = QVBoxLayout(ranking_section)
        ranking_section_layout.setContentsMargins(15, 15, 15, 15)
        ranking_section_layout.setSpacing(12)
        
        ranking_title = QLabel("🏆 排行榜")
        ranking_title.setFont(self.create_scaled_font(16, bold=True))
        ranking_title.setStyleSheet("""
            QLabel {
                color: #e67e22;
                padding: 5px 0px;
                margin: 0px;
                border: none;
                background: transparent;
            }
        """)
        ranking_section_layout.addWidget(ranking_title)
        

        self.ranking_container = QWidget()
        self.ranking_layout = QVBoxLayout(self.ranking_container)
        self.ranking_layout.setContentsMargins(0, 0, 0, 0)
        self.ranking_layout.setSpacing(8)
        ranking_section_layout.addWidget(self.ranking_container)
        
        main_content_layout.addWidget(ranking_section)
        

        history_section = QFrame()
        history_section.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.7);
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
        """)
        history_section_layout = QVBoxLayout(history_section)
        history_section_layout.setContentsMargins(15, 15, 15, 15)
        history_section_layout.setSpacing(12)
        

        history_title_row = QHBoxLayout()
        history_title = QLabel("📜 赞助历史")
        history_title.setFont(self.create_scaled_font(16, bold=True))
        history_title.setStyleSheet("""
            QLabel {
                color: #27ae60;
                padding: 5px 0px;
                margin: 0px;
                border: none;
                background: transparent;
            }
        """)
        history_title_row.addWidget(history_title)
        

        self.history_count_label = QLabel("")
        self.history_count_label.setFont(self.create_scaled_font(12))
        self.history_count_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                padding: 5px 0px;
                margin: 0px;
                border: none;
                background: transparent;
            }
        """)
        history_title_row.addStretch()
        history_title_row.addWidget(self.history_count_label)
        
        history_section_layout.addLayout(history_title_row)
        

        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.setSpacing(1)
        history_section_layout.addWidget(self.history_container)
        
        main_content_layout.addWidget(history_section)
        
        main_scroll.setWidget(main_content)
        layout.addWidget(main_scroll)
        
        return column
    
    def create_project_item(self, name, url, description):
        """创建项目项目卡片"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin: 3px 0px;
            }
            QFrame:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QVBoxLayout(item_frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        

        title_row = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(self.create_scaled_font(14, bold=True))
        name_label.setStyleSheet("color: #2c3e50; background: transparent; border: none;")
        name_label.setWordWrap(True)
        title_row.addWidget(name_label)
        

        title_row.addSpacing(15)
        

        visit_btn = QPushButton("访问")
        visit_btn.setFixedSize(55, 28)
        visit_btn.setFont(self.create_scaled_font(11, bold=True))
        visit_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 55px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        visit_btn.clicked.connect(lambda: self.open_url(url))
        title_row.addWidget(visit_btn, 0, Qt.AlignRight)
        
        layout.addLayout(title_row)
        

        desc_label = QLabel(description)
        desc_label.setFont(self.create_scaled_font(12))
        desc_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                line-height: 1.4;
                background: transparent;
                border: none;
            }
        """)
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(65)
        layout.addWidget(desc_label)
        
        return item_frame
    
    def create_advertiser_item(self, name, url, description):
        """创建赞助企业卡片"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin: 3px 0px;
            }
            QFrame:hover {
                background-color: #e9ecef;
            }
        """)
        
        layout = QVBoxLayout(item_frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        

        title_row = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(self.create_scaled_font(14, bold=True))
        name_label.setStyleSheet("color: #2c3e50; background: transparent; border: none;")
        name_label.setWordWrap(True)
        title_row.addWidget(name_label)
        

        title_row.addSpacing(15)
        

        visit_btn = QPushButton("访问")
        visit_btn.setFixedSize(55, 28)
        visit_btn.setFont(self.create_scaled_font(11, bold=True))
        visit_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 55px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        visit_btn.clicked.connect(lambda: self.open_url(url))
        title_row.addWidget(visit_btn, 0, Qt.AlignRight)
        
        layout.addLayout(title_row)
        

        desc_label = QLabel(description)
        desc_label.setFont(self.create_scaled_font(12))
        desc_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                line-height: 1.4;
                background: transparent;
                border: none;
            }
        """)
        desc_label.setWordWrap(True)
        desc_label.setMaximumHeight(65)
        layout.addWidget(desc_label)
        
        return item_frame
    
    def open_url(self, url):
        """打开URL"""
        try:
            if url and url.strip():
                QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开链接: {str(e)}")
    
    def create_ranking_item(self, rank, user_id, amount):
        """创建排行榜项目"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 3px 0px;
            }
            QFrame:hover {
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
            }
        """)
        
        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)
        

        rank_container = QWidget()
        rank_container.setFixedWidth(50)
        rank_layout = QVBoxLayout(rank_container)
        rank_layout.setContentsMargins(0, 0, 0, 0)
        rank_layout.setSpacing(0)
        
        if rank == "1":
            rank_label = QLabel("🥇")
            rank_text = QLabel("第一")
        elif rank == "2":
            rank_label = QLabel("🥈")
            rank_text = QLabel("第二")
        elif rank == "3":
            rank_label = QLabel("🥉")
            rank_text = QLabel("第三")
        else:
            rank_label = QLabel("🏅")
            rank_text = QLabel(f"第{rank}")
        
        rank_label.setFont(self.create_scaled_font(18))
        rank_label.setStyleSheet("""
            QLabel {
                color: #e67e22;
                background: transparent;
                border: none;
                text-align: center;
            }
        """)
        rank_label.setAlignment(Qt.AlignCenter)
        
        rank_text.setFont(self.create_scaled_font(10, bold=True))
        rank_text.setStyleSheet("""
            QLabel {
                color: #e67e22;
                background: transparent;
                border: none;
                text-align: center;
            }
        """)
        rank_text.setAlignment(Qt.AlignCenter)
        
        rank_layout.addWidget(rank_label)
        rank_layout.addWidget(rank_text)
        layout.addWidget(rank_container)
        

        user_container = QWidget()
        user_layout = QVBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(2)
        

        user_label = QLabel(user_id)
        user_label.setFont(self.create_scaled_font(14, bold=True))
        user_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
            }
        """)
        user_label.setWordWrap(True)
        user_layout.addWidget(user_label)
        

        contributor_label = QLabel("贡献者")
        contributor_label.setFont(self.create_scaled_font(10))
        contributor_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background: transparent;
                border: none;
            }
        """)
        user_layout.addWidget(contributor_label)
        
        layout.addWidget(user_container)
        layout.addStretch()
        

        amount_container = QWidget()
        amount_layout = QVBoxLayout(amount_container)
        amount_layout.setContentsMargins(0, 0, 0, 0)
        amount_layout.setSpacing(2)
        

        amount_label = QLabel(f"¥{amount}")
        amount_label.setFont(self.create_scaled_font(16, bold=True))
        amount_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                background: transparent;
                border: none;
                text-align: right;
            }
        """)
        amount_label.setAlignment(Qt.AlignRight)
        amount_layout.addWidget(amount_label)
        

        total_label = QLabel("总赞助")
        total_label.setFont(self.create_scaled_font(10))
        total_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                background: transparent;
                border: none;
                text-align: right;
            }
        """)
        total_label.setAlignment(Qt.AlignRight)
        amount_layout.addWidget(total_label)
        
        layout.addWidget(amount_container)
        
        return item_frame
    
    def create_history_item(self, date, user_id, amount):
        """创建历史项目"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                border-bottom: 1px solid #ecf0f1;
                padding: 0px;
                margin: 0px;
                min-height: 45px;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border-radius: 4px;
                border-bottom: 1px solid #ecf0f1;
            }
        """)
        
        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(15)
        

        date_container = QWidget()
        date_container.setFixedWidth(85)
        date_layout = QVBoxLayout(date_container)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(1)
        

        try:

            date_parts = date.split('/')
            if len(date_parts) == 3:
                month_day = f"{date_parts[1]}/{date_parts[2]}"
                year = date_parts[0]
            else:
                month_day = date
                year = ""
        except:
            month_day = date
            year = ""
        
        date_main = QLabel(month_day)
        date_main.setFont(self.create_scaled_font(12, bold=True))
        date_main.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
            }
        """)
        date_main.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(date_main)
        
        if year:
            date_year = QLabel(year)
            date_year.setFont(self.create_scaled_font(9))
            date_year.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    background: transparent;
                    border: none;
                }
            """)
            date_year.setAlignment(Qt.AlignCenter)
            date_layout.addWidget(date_year)
        
        layout.addWidget(date_container)
        

        user_container = QWidget()
        user_layout = QVBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(2)
        

        user_label = QLabel(user_id)
        user_label.setFont(self.create_scaled_font(13, bold=True))
        user_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                background: transparent;
                border: none;
            }
        """)
        user_label.setWordWrap(True)
        user_layout.addWidget(user_label)
        

        thanks_label = QLabel("感谢支持")
        thanks_label.setFont(self.create_scaled_font(10))
        thanks_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                background: transparent;
                border: none;
            }
        """)
        user_layout.addWidget(thanks_label)
        
        layout.addWidget(user_container)
        layout.addStretch()
        

        amount_container = QWidget()
        amount_layout = QVBoxLayout(amount_container)
        amount_layout.setContentsMargins(0, 0, 0, 0)
        amount_layout.setSpacing(1)
        

        amount_label = QLabel(f"¥{amount}")
        amount_label.setFont(self.create_scaled_font(13, bold=True))
        amount_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                background: transparent;
                border: none;
                text-align: right;
            }
        """)
        amount_label.setAlignment(Qt.AlignRight)
        amount_layout.addWidget(amount_label)
        

        sponsor_label = QLabel("赞助")
        sponsor_label.setFont(self.create_scaled_font(10))
        sponsor_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                background: transparent;
                border: none;
                text-align: right;
            }
        """)
        sponsor_label.setAlignment(Qt.AlignRight)
        amount_layout.addWidget(sponsor_label)
        
        layout.addWidget(amount_container)
        
        return item_frame
        
    def create_text_tab(self):
        """创建文本显示标签页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-size: 12px;
                line-height: 1.5;
                padding: 10px;
            }
        """)
        
        scroll_area.setWidget(text_edit)
        return scroll_area
        
    def create_intro_widget(self):
        """创建WCT介绍部件"""
        intro_widget = QFrame()
        intro_widget.setFrameStyle(QFrame.Box)
        intro_widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(intro_widget)
        
        title = QLabel("关于 White Cat Toolbox")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #2e86ab; margin-bottom: 10px;")
        layout.addWidget(title)
        
        intro_text = QTextEdit()
        intro_text.setReadOnly(True)
        intro_text.setMaximumHeight(200)
        intro_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                font-size: 12px;
            }
        """)
        
        intro_content = """
White Cat Toolbox 是一个功能强大的安全工具集合平台，旨在为安全研究人员和开发者提供便捷的工具管理和使用环境。

主要特性：
• 集成多种安全测试工具
• 友好的图形化界面
• 参数配置和模板管理
• 历史记录和日志管理  
• 虚拟环境支持
• 主题和字体自定义

感谢您选择使用 White Cat Toolbox！
        """
        
        intro_text.setPlainText(intro_content.strip())
        layout.addWidget(intro_text)
        
        return intro_widget
    
    def load_promotion_content(self):
        """加载推广内容"""
        promotion_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "promotion")
        

        self.load_projects(promotion_dir)
        

        self.load_advertisers(promotion_dir)
        

        self.load_sponsors(promotion_dir)
    
    def load_projects(self, promotion_dir):
        """加载项目推荐"""
        xm_file = os.path.join(promotion_dir, "xm.txt")
        

        for i in reversed(range(self.project_layout.count())):
            child = self.project_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if os.path.exists(xm_file):
            try:
                with open(xm_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                if content:
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line:

                            parts = line.split(' ', 2)
                            if len(parts) >= 3:
                                name, url, description = parts[0], parts[1], parts[2]
                                item = self.create_project_item(name, url, description)
                                self.project_layout.addWidget(item)
                            elif len(parts) == 2:
                                name, url = parts[0], parts[1]
                                item = self.create_project_item(name, url, "暂无描述")
                                self.project_layout.addWidget(item)
                else:
                    self.add_empty_message(self.project_layout, "暂无项目推荐内容")
            except Exception as e:
                self.add_empty_message(self.project_layout, f"加载项目推荐失败: {str(e)}")
        else:
            self.add_empty_message(self.project_layout, "项目推荐文件不存在")
        

        self.project_layout.addStretch()
    
    def load_advertisers(self, promotion_dir):
        """加载赞助企业"""
        gg_file = os.path.join(promotion_dir, "gg.txt")
        

        for i in reversed(range(self.advertiser_layout.count())):
            child = self.advertiser_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if os.path.exists(gg_file):
            try:
                with open(gg_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                if content:
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('赞助商名称'):

                            parts = line.split(' ', 2)
                            if len(parts) >= 3:
                                name, url, description = parts[0], parts[1], parts[2]
                                item = self.create_advertiser_item(name, url, description)
                                self.advertiser_layout.addWidget(item)
                            elif len(parts) == 2:
                                name, url = parts[0], parts[1]
                                item = self.create_advertiser_item(name, url, "暂无介绍")
                                self.advertiser_layout.addWidget(item)
                else:
                    self.add_empty_message(self.advertiser_layout, "暂无赞助企业")
            except Exception as e:
                self.add_empty_message(self.advertiser_layout, f"加载赞助企业失败: {str(e)}")
        else:
            self.add_empty_message(self.advertiser_layout, "赞助企业文件不存在")
        

        self.advertiser_layout.addStretch()
    
    def load_sponsors(self, promotion_dir):
        """加载赞助榜单"""
        zz_file = os.path.join(promotion_dir, "zz.txt")
        

        for i in reversed(range(self.ranking_layout.count())):
            child = self.ranking_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
                
        for i in reversed(range(self.history_layout.count())):
            child = self.history_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if os.path.exists(zz_file):
            try:
                with open(zz_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                if content:
                    lines = content.split('\n')
                        

                    ranking_data = []
                    history_data = []
                    
                    current_section = None
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.startswith('排名'):
                            current_section = 'ranking'
                            continue
                        elif line.startswith('赞助历史'):
                            current_section = 'history'
                            continue
                        elif line.startswith('时间'):
                            continue
                            
                        if current_section == 'ranking':
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                ranking_data.append(parts)
                        elif current_section == 'history':
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                history_data.append(parts)
                    

                    for rank, user_id, amount in ranking_data:
                        item = self.create_ranking_item(rank, user_id, amount)
                        self.ranking_layout.addWidget(item)
                    
                    if not ranking_data:
                        self.add_empty_message(self.ranking_layout, "暂无排行榜数据")
                    

                    for date, user_id, amount in history_data:
                        item = self.create_history_item(date, user_id, amount)
                        self.history_layout.addWidget(item)
                    
                    if not history_data:
                        self.add_empty_message(self.history_layout, "暂无历史数据")
                        self.history_count_label.setText("")
                    else:
                        self.history_count_label.setText(f"共 {len(history_data)} 条记录")
                    

                    self.ranking_layout.addStretch()
                    self.history_layout.addStretch()
                    
            except Exception as e:

                self.add_empty_message(self.ranking_layout, f"加载赞助榜单失败: {str(e)}")
                self.add_empty_message(self.history_layout, f"加载赞助历史失败: {str(e)}")
                self.history_count_label.setText("")
        else:

            self.add_empty_message(self.ranking_layout, "赞助榜单文件不存在")
            self.add_empty_message(self.history_layout, "赞助历史文件不存在")
            self.history_count_label.setText("")
    
    def add_empty_message(self, layout, message):
        """添加空消息标签"""
        label = QLabel(message)
        label.setFont(self.create_scaled_font(14))
        label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                padding: 30px;
                text-align: center;
                background-color: #f8f9fa;
                border: none;
                border-radius: 6px;
                margin: 10px 0px;
            }
        """)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
    
    def load_promotion_setting(self):
        """从配置文件加载推广设置"""
        try:
            return self.config_manager.app_config.get('promotion_enabled', True)
        except:
            return True
            
    def save_promotion_setting(self, enabled):
        """保存推广设置到配置文件"""
        try:
            self.config_manager.app_config['promotion_enabled'] = enabled
            self.config_manager.save_app_config()
            self.promotion_enabled = enabled
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存设置失败: {str(e)}")
            
    def close_promotion(self):
        """关闭推广界面"""
        self.promotion_closed.emit()