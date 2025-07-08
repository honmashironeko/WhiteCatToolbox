from .theme import colors, fonts, params
from .utils import s

def get_cross_platform_app_stylesheet():
    
    return f"""
        /* 修复QMessageBox黑框问题 */
        QMessageBox {{
            background-color: {colors["white"]};
            border: 1px solid {colors["border"]};
            border-radius: {params["border_radius"]};
            font-family: '{fonts["system"]}', Arial, sans-serif;
            color: {colors["text"]};
        }}
        QMessageBox QLabel {{
            background-color: transparent;
            color: {colors["text"]};
            font-size: {fonts["default_size"]};
            padding: {params["dialog_padding"]};
            border: none;
        }}
        QMessageBox QPushButton {{
            background-color: {colors["primary"]};
            border: none;
            border-radius: {params["border_radius_small"]};
            padding: {params["button_padding"]};
            color: {colors["text_on_primary"]};
            font-weight: 500;
            font-size: {fonts["default_size"]};
            min-width: {params["button_min_width"]};
            min-height: {params["button_min_height"]};
            margin: {s(4)}px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {colors["primary_hover"]};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {colors["primary_pressed"]};
        }}
        QMessageBox QPushButton[text="取消"], 
        QMessageBox QPushButton[text="Cancel"],
        QMessageBox QPushButton[text="No"] {{
            background-color: {colors["background_light"]};
            color: {colors["primary"]};
            border: 1px solid {colors["border_light"]};
        }}
        QMessageBox QPushButton[text="取消"]:hover,
        QMessageBox QPushButton[text="Cancel"]:hover,
        QMessageBox QPushButton[text="No"]:hover {{
            background-color: {colors["border"]};
            border-color: {colors["primary"]};
        }}
        
        /* 修复QInputDialog黑框问题 */
        QInputDialog {{
            background-color: {colors["white"]};
            border: 1px solid {colors["border"]};
            border-radius: {params["border_radius"]};
            font-family: '{fonts["system"]}', Arial, sans-serif;
            color: {colors["text"]};
        }}
        QInputDialog QLabel {{
            background-color: transparent;
            color: {colors["text"]};
            font-size: {fonts["default_size"]};
            padding: {s(16)}px {s(16)}px {s(8)}px {s(16)}px;
            border: none;
        }}
        QInputDialog QLineEdit {{
            background-color: {colors["background_light"]};
            border: 1px solid {colors["border_light"]};
            border-radius: {params["border_radius_small"]};
            padding: {params["input_padding"]};
            color: {colors["text"]};
            font-size: {fonts["default_size"]};
            margin: {params["input_margin"]};
            selection-background-color: {colors["primary"]};
        }}
        QInputDialog QLineEdit:focus {{
            border-color: {colors["primary"]};
            background-color: {colors["white"]};
        }}
        QInputDialog QPushButton {{
            background-color: {colors["primary"]};
            border: none;
            border-radius: {params["border_radius_small"]};
            padding: {params["button_padding"]};
            color: {colors["text_on_primary"]};
            font-weight: 500;
            font-size: {fonts["default_size"]};
            min-width: {params["button_min_width"]};
            min-height: {params["button_min_height"]};
            margin: {s(4)}px;
        }}
        QInputDialog QPushButton:hover {{
            background-color: {colors["primary_hover"]};
        }}
        QInputDialog QPushButton:pressed {{
            background-color: {colors["primary_pressed"]};
        }}
        QInputDialog QPushButton[text="取消"],
        QInputDialog QPushButton[text="Cancel"] {{
            background-color: {colors["background_light"]};
            color: {colors["primary"]};
            border: 1px solid {colors["border_light"]};
        }}
        QInputDialog QPushButton[text="取消"]:hover,
        QInputDialog QPushButton[text="Cancel"]:hover {{
            background-color: {colors["border"]};
            border-color: {colors["primary"]};
        }}
        
        /* 修复QFileDialog黑框问题 */
        QFileDialog {{
            background-color: {colors["white"]};
            color: {colors["text"]};
            font-family: '{fonts["system"]}', Arial, sans-serif;
        }}
        QFileDialog QListView {{
            background-color: {colors["white"]};
            border: 1px solid {colors["border"]};
            border-radius: {params["border_radius_very_small"]};
            color: {colors["text"]};
        }}
        QFileDialog QTreeView {{
            background-color: {colors["white"]};
            border: 1px solid {colors["border"]};
            border-radius: {params["border_radius_very_small"]};
            color: {colors["text"]};
        }}
        QFileDialog QPushButton {{
            background-color: {colors["primary"]};
            border: none;
            border-radius: {params["border_radius_small"]};
            padding: {s(8)}px {s(16)}px;
            color: {colors["text_on_primary"]};
            font-weight: 500;
            min-height: {s(28)}px;
        }}
        QFileDialog QPushButton:hover {{
            background-color: {colors["primary_hover"]};
        }}
        QFileDialog QPushButton[text="取消"],
        QFileDialog QPushButton[text="Cancel"] {{
            background-color: {colors["background_light"]};
            color: {colors["primary"]};
            border: 1px solid {colors["border_light"]};
        }}
        
        /* 垂直滚动条样式 */
        QScrollBar:vertical {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 {colors["scrollbar_background_start"]}, stop: 1 {colors["scrollbar_background_end"]});
            width: {s(12)}px;
            border-radius: {params["border_radius_very_small"]};
            margin: {s(2)}px;
            border: 1px solid {colors["scrollbar_background_border"]};
        }}
        QScrollBar::handle:vertical {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 {colors["scrollbar_handle_start"]}, stop: 1 {colors["scrollbar_handle_end"]});
            border-radius: {s(5)}px;
            min-height: {s(30)}px;
            margin: {s(1)}px;
            border: 1px solid {colors["scrollbar_handle_border"]};
        }}
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 {colors["scrollbar_handle_hover_start"]}, stop: 1 {colors["scrollbar_handle_hover_end"]});
            border-color: {colors["scrollbar_handle_hover_border"]};
        }}
        QScrollBar::handle:vertical:pressed {{
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                      stop: 0 {colors["scrollbar_handle_pressed_start"]}, stop: 1 {colors["scrollbar_handle_pressed_end"]});
            border-color: {colors["scrollbar_handle_pressed_border"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            background: none;
        }}
        
        /* 水平滚动条样式 */
        QScrollBar:horizontal {{
            height: {s(12)}px;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["scrollbar_background_start"]}, stop: 1 {colors["scrollbar_background_end"]});
            border-radius: {params["border_radius_very_small"]};
            margin: {s(2)}px;
            border: 1px solid {colors["scrollbar_background_border"]};
        }}
        QScrollBar::handle:horizontal {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["scrollbar_handle_start"]}, stop: 1 {colors["scrollbar_handle_end"]});
            border-radius: {s(5)}px;
            min-width: {s(30)}px;
            margin: {s(1)}px;
            border: 1px solid {colors["scrollbar_handle_border"]};
        }}
        QScrollBar::handle:horizontal:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["scrollbar_handle_hover_start"]}, stop: 1 {colors["scrollbar_handle_hover_end"]});
            border-color: {colors["scrollbar_handle_hover_border"]};
        }}
        QScrollBar::handle:horizontal:pressed {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["scrollbar_handle_pressed_start"]}, stop: 1 {colors["scrollbar_handle_pressed_end"]});
            border-color: {colors["scrollbar_handle_pressed_border"]};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
            height: 0;
            background: none;
        }}
        
        /* 滚动区域样式 */
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        
        /* 工具提示样式 - 高优先级确保一致性 */
        QToolTip {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["tooltip_background_start"]}, stop: 1 {colors["tooltip_background_end"]}) !important;
            color: {colors["tooltip_text"]} !important;
            border: {s(2)}px solid {colors["tooltip_border"]} !important;
            border-radius: {params["border_radius_small"]} !important;
            padding: {s(6)}px {s(10)}px !important;
            font-size: {fonts["tooltip_size"]} !important;
            font-family: '{fonts["system"]}', Arial, sans-serif !important;
            font-weight: 500 !important;
            line-height: 1.2 !important;
            max-width: {s(400)}px !important;
        }}
        
        /* 确保所有组件的工具提示都使用统一样式 */
        * QToolTip {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["tooltip_background_start"]}, stop: 1 {colors["tooltip_background_end"]}) !important;
            color: {colors["tooltip_text"]} !important;
            border: {s(2)}px solid {colors["tooltip_border"]} !important;
            border-radius: {params["border_radius_small"]} !important;
            padding: {s(6)}px {s(10)}px !important;
            font-size: {fonts["tooltip_size"]} !important;
            font-family: '{fonts["system"]}', Arial, sans-serif !important;
            font-weight: 500 !important;
            line-height: 1.2 !important;
            max-width: {s(400)}px !important;
        }}
    """ 

def get_modern_qtabwidget_stylesheet():
    
    return f"""
        QTabWidget::pane {{
            background-color: {colors["white"]};
            border: 1px solid {colors["tab_border"]};
            border-radius: {params["border_radius_small"]};
            padding: {s(4)}px;
        }}
        QTabBar::tab {{
            background-color: {colors["tab_background"]};
            border: 1px solid {colors["tab_border"]};
            border-bottom: none;
            border-radius: {params["border_radius_very_small"]} {params["border_radius_very_small"]} 0px 0px;
            padding: {s(10)}px {s(20)}px;
            margin: 0px {s(2)}px;
            color: {colors["tab_text"]};
            font-weight: 600;
            font-size: {fonts["tab_size"]};
        }}
        QTabBar::tab:hover {{
            background-color: {colors["tab_hover_background"]};
        }}
        QTabBar::tab:selected {{
            background-color: {colors["secondary"]};
            color: {colors["tab_selected_text"]};
            border-color: {colors["secondary"]};
        }}
    """

def get_modern_qmenu_stylesheet():
    
    return f"""
        QMenu {{
            background-color: {colors["menu_background"]};
            border: 1px solid {colors["menu_border"]};
            border-radius: {params["border_radius_small"]};
            padding: {s(4)}px;
            color: {colors["text"]};
            font-size: {fonts["menu_size"]};
        }}
        QMenu::item {{
            padding: {s(8)}px {s(16)}px;
            background-color: transparent;
            border-radius: {params["border_radius_very_small"]};
        }}
        QMenu::item:selected {{
            background-color: {colors["menu_item_selected_background"]};
            color: {colors["menu_item_selected_text"]};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {colors["menu_separator"]};
            margin: {s(4)}px {s(8)}px;
        }}
    """

def get_main_window_style():
    
    return f"""
        QMainWindow {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["main_background_start"]}, stop: 1 {colors["main_background_end"]});
            color: {colors["text"]};
            font-family: '{fonts["system"]}', Arial, sans-serif;
        }}
    """

def get_splitter_style():
    
    return f"""
        QSplitter::handle {{
            background-color: {colors["splitter_handle"]};
            width: 3px;
            margin: 2px 0;
            border-radius: 1px;
            border: 1px solid {colors["border_light"]};
        }}
        QSplitter::handle:hover {{
            background-color: {colors["splitter_handle_hover"]};
            border-color: {colors["splitter_handle_hover"]};
        }}
        QSplitter::handle:vertical {{
            background-color: {colors["splitter_handle"]};
            height: 1px;
            margin: 0 2px;
            border-radius: 1px;
            border: 1px solid {colors["border_light"]};
        }}
        QSplitter::handle:vertical:hover {{
            background-color: {colors["splitter_handle_hover"]};
            border-color: {colors["splitter_handle_hover"]};
        }}
    """

def get_panel_style():
    
    return f"""
        QWidget {{
            background-color: {colors["white"]};
            border-radius: {params["border_radius_small"]};
        }}
    """

def get_title_panel_style():
    
    return f"""
        QWidget {{
            background-color: {colors["main_background_start"]};
            border: 1px solid {colors["background_gray"]};
            border-radius: {params["border_radius_small"]};
            padding: 12px;
        }}
    """

def get_title_label_style(font_size=None):
    
    style = f"""
        QLabel {{
            color: {colors["tooltip_text"]};
            background: transparent;
            border: none;
            padding: 4px 8px;
        }}
    """
    if font_size:
        size = s(font_size)
        style += f"QLabel {{ font-size: {size}pt; }}"
    return style

def get_list_panel_style():
    
    return f"""
        QWidget {{
            background-color: {colors["white"]};
            border: 1px solid {colors["background_gray"]};
            border-radius: {params["border_radius_small"]};
            padding: 8px;
        }}
    """

def get_tool_list_style():
    
    return f"""
        QListWidget {{
            background-color: transparent;
            border: none;
            border-radius: {params["border_radius_very_small"]};
            padding: {s(4)}px;
            outline: none;
        }}
        QListWidget::item {{
            background-color: {colors["main_background_start"]};
            border: 1px solid {colors["background_gray"]};
            border-radius: {params["border_radius_very_small"]};
            padding: {s(12)}px {s(16)}px;
            margin: {s(2)}px 0px;
            color: {colors["text_secondary"]};
            font-weight: 700;
            font-size: {s(11)}pt;
        }}
        QListWidget::item:hover {{
            background-color: {colors["list_item_hover_background"]};
            border-color: {colors["secondary"]};
            color: {colors["list_item_hover_text"]};
        }}
        QListWidget::item:selected {{
            background-color: {colors["list_item_selected_background"]};
            border-color: {colors["secondary"]};
            color: {colors["list_item_selected_text"]};
            font-weight: 600;
        }}
    """

def get_icon_button_style(base_color, hover_color, pressed_color):
    
    return f"""
        QPushButton {{
            background-color: {base_color};
            color: {colors["white"]};
            border: none;
            border-radius: {int(int(params["icon_button_size"][:-2]) / 2)}px;
            padding: 4px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
    """

def get_clickable_label_style(checked, is_required):
    
    if checked:
        if is_required:

            return f"""
                QLabel {{
                    background-color: {colors["success"]};
                    border: 1px solid {colors["success"]};
                    border-left: 3px solid {colors["success_dark"]};
                    border-radius: {params["border_radius_very_small"]};
                    padding: 8px 12px;
                    color: {colors["white"]};
                    font-weight: 600;
                    min-height: 20px;
                }}
                QLabel:hover {{
                    background-color: {colors["success_hover"]};
                    border-color: {colors["success_pressed"]};
                    border-left: 3px solid {colors["success_dark"]};
                }}
            """
        else:

            return f"""
                QLabel {{
                    background-color: {colors["secondary"]};
                    border: 1px solid {colors["secondary"]};
                    border-radius: {params["border_radius_very_small"]};
                    padding: 8px 12px;
                    color: {colors["white"]};
                    font-weight: 600;
                    min-height: 20px;
                }}
            """
    else:
        if is_required:

            return f"""
                QLabel {{
                    background-color: {colors["danger_very_light"]};
                    border: 2px solid {colors["danger"]};
                    border-left: 4px solid {colors["danger"]};
                    border-radius: {params["border_radius_very_small"]};
                    padding: 8px 12px;
                    color: {colors["text_on_danger"]};
                    font-weight: 600;
                    min-height: 20px;
                }}
                QLabel:hover {{
                    background-color: {colors["danger_light"]};
                    border-color: {colors["danger_hover"]};
                    border-left: 4px solid {colors["danger_hover"]};
                    color: {colors["text_on_danger_hover"]};
                }}
            """
        else:

            return f"""
                QLabel {{
                    background-color: {colors["main_background_start"]};
                    border: 1px solid {colors["background_gray"]};
                    border-radius: {params["border_radius_very_small"]};
                    padding: 8px 12px;
                    color: {colors["text_secondary"]};
                    font-weight: 500;
                    min-height: 20px;
                }}
                QLabel:hover {{
                    background-color: {colors["list_item_hover_background"]};
                    border-color: {colors["secondary"]};
                    color: {colors["list_item_hover_text"]};
                }}
            """

def get_push_button_stylesheet(base, hover, pressed, text_color="white"):
    
    return f"""
        QPushButton {{
            background-color: {base};
            color: {text_color};
            border: none;
            border-radius: {params["border_radius_very_small"]};
            padding: 8px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {pressed};
        }}
    """

def get_disabled_label_style(font_size=14):
    
    return f"""
        QLabel {{
            color: {colors["text_disabled"]};
            font-size: {s(font_size)}pt;
            padding: {s(50)}px;
            background-color: {colors["background_very_light"]};
            border: 1px dashed {colors["border_light"]};
            border-radius: {params["border_radius"]};
        }}
    """

def get_vertical_separator_style():
    
    return f"""
        QFrame {{
            background-color: {colors["border_light"]};
            width: 1px;
            max-width: 1px;
            min-width: 1px;
        }}
    """

def get_promotion_item_style():
    
    return f"""
        QWidget#promotion_item {{
            background-color: {colors["background_very_light"]};
            border-radius: {params["border_radius_very_small"]};
            border: 1px solid {colors["background_gray"]};
            padding: {s(12)}px;
        }}
        QWidget#promotion_item:hover {{
            background-color: {colors["list_item_hover_background"]};
            border-color: {colors["secondary"]};
        }}
        QLabel#promotion_text {{
            background-color: transparent;
            border: none;
            color: {colors["text_secondary"]};
            font-weight: normal;
        }}
    """

def get_sponsor_groupbox_style():
    
    return f"""
        QGroupBox {{
            background-color: {colors["white"]};
            border: 1px solid {colors["border"]};
            border-radius: {params["border_radius_small"]};
            margin-top: {s(15)}px;
            background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 {colors["white"]}, stop: 1 #fdfdfd);
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 {s(10)}px;
            margin-left: {s(10)}px;
            background-color: {colors["secondary"]};
            color: {colors["white"]};
            border-radius: {params["border_radius_very_small"]};
            font-size: {s(11)}pt;
            font-weight: 600;
        }}
    """

def get_sponsor_item_style():
    
    return f"""
        QLabel {{
            color: {colors["text_secondary"]};
            font-weight: bold;
        }}
        QLabel#sponsor_amount {{
            color: {colors["danger"]};
            font-size: {s(11)}pt;
            font-weight: bold;
        }}
        QLabel#sponsor_date {{
            color: {colors["text_disabled"]};
        }}
        QFrame#sponsor_separator {{
            background-color: {colors["background_gray"]};
        }}
    """ 