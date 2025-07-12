from .theme import colors, fonts, params
from .utils import s

def get_cross_platform_app_stylesheet():
    
    return f"""
        
        {get_modern_combobox_style()}
        
        
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
        QMessageBox QPushButton[text="No"],
        QMessageBox QPushButton[text="否"] {{
            background-color: {colors["background_light"]};
            color: {colors["primary"]};
            border: 1px solid {colors["border_light"]};
        }}
        QMessageBox QPushButton[text="取消"]:hover,
        QMessageBox QPushButton[text="Cancel"]:hover,
        QMessageBox QPushButton[text="No"]:hover,
        QMessageBox QPushButton[text="否"]:hover {{
            background-color: {colors["border"]};
            border-color: {colors["primary"]};
        }}
        
        
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
        
        
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background-color: transparent;
        }}
        
        
        QToolTip {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["tooltip_background_start"]}, stop: 1 {colors["tooltip_background_end"]});
            color: {colors["tooltip_text"]};
            border: {s(2)}px solid {colors["tooltip_border"]};
            border-radius: {params["border_radius_small"]};
            padding: {s(6)}px {s(10)}px;
            font-size: {fonts["tooltip_size"]};
            font-family: '{fonts["system"]}', Arial, sans-serif;
            font-weight: 500;
            line-height: 1.3;
            max-width: {s(450)}px;
            word-wrap: break-word;
            white-space: pre-wrap;
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
            background-color: {colors["white"]};
            border: 1px solid {colors["border_light"]};
            border-radius: {s(8)}px;
            padding: {s(6)}px;
            color: {colors["text"]};
            font-size: {s(10)}pt;
            font-family: '{fonts["system"]}', Arial, sans-serif;
            min-width: {s(180)}px;
        }}
        QMenu::item {{
            padding: {s(10)}px {s(18)}px;
            background-color: transparent;
            border-radius: {s(6)}px;
            margin: {s(2)}px {s(4)}px;
            font-weight: 500;
            min-height: {s(24)}px;
            color: {colors["text"]};
        }}
        QMenu::item:selected {{
            background-color: {colors["secondary"]};
            color: {colors["text_on_primary"]};
            font-weight: 600;
        }}
        QMenu::item:pressed {{
            background-color: {colors["secondary_hover"]};
        }}
        QMenu::item:disabled {{
            color: {colors["text_disabled"]};
            background-color: transparent;
        }}
        QMenu::separator {{
            height: {s(1)}px;
            background-color: {colors["border_light"]};
            margin: {s(6)}px {s(12)}px;
            border: none;
        }}
        QMenu::icon {{
            padding-left: {s(8)}px;
            width: {s(16)}px;
            height: {s(16)}px;
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
            width: 8px;
            margin: 2px 0;
            border-radius: 4px;
            border: 1px solid {colors["border"]};
        }}
        QSplitter::handle:hover {{
            background-color: {colors["splitter_handle_hover"]};
            border-color: {colors["primary"]};
            width: 10px;
        }}
        QSplitter::handle:vertical {{
            height: 1px;
            margin: 0 2px;
            border-radius: 4px;
            border: 1px solid {colors["border"]};
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
                    font-weight: bold;
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
                    font-weight: bold;
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
                    font-weight: bold;
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
                    font-weight: bold;
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

def get_parameter_section_style():
    
    return f"""
        QGroupBox {{
            border: 1px solid {colors["border"]};
            border-radius: {params["border_radius_small"]};
            margin-top: {s(10)}px;
            background-color: {colors["white"]};
            padding-top: {s(10)}px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: {s(4)}px {s(10)}px;
            background-color: {colors["secondary"]};
            color: {colors["text_on_primary"]};
            border-radius: {params["border_radius_very_small"]};
            font-weight: 600;
        }}
    """

def get_parameter_search_style():
    
    return f"""
        QLineEdit {{
            border: 1px solid {colors["border_light"]};
            border-radius: {params["border_radius_very_small"]};
            padding: {s(6)}px {s(12)}px;
            background-color: {colors["background_very_light"]};
            font-size: {s(9)}pt;
            color: {colors["text"]};
        }}
        QLineEdit:focus {{
            border: 2px solid {colors["secondary"]};
            background-color: {colors["white"]};
            outline: none;
        }}
        QLineEdit:hover {{
            border-color: {colors["border"]};
            background-color: {colors["background_light"]};
        }}
    """

def get_modern_combobox_style():
    """
    通用的现代化下拉框样式 - 优化版本，移除多余边框
    Modern and elegant dropdown/combobox styling with clean borders
    """
    return f"""
        QComboBox {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["white"]}, 
                                      stop: 1 {colors["background_very_light"]});
            border: 1px solid {colors["border_light"]};
            border-radius: {params["border_radius_small"]};
            padding: {s(6)}px {s(12)}px;
            padding-right: {s(25)}px;
            color: {colors["text"]};
            font-size: {fonts["default_size"]};
            font-family: '{fonts["system"]}', Arial, sans-serif;
            font-weight: 500;
            min-height: {s(20)}px;
            selection-background-color: {colors["secondary"]};
            selection-color: {colors["text_on_primary"]};
        }}
        
        QComboBox:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["background_light"]}, 
                                      stop: 1 {colors["background_very_light"]});
            border-color: {colors["secondary"]};
        }}
        
        QComboBox:focus {{
            border: 1px solid {colors["secondary"]};
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["white"]}, 
                                      stop: 1 {colors["background_light"]});
            outline: none;
        }}
        
        QComboBox:pressed {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["background_light"]}, 
                                      stop: 1 {colors["background_gray"]});
            border-color: {colors["secondary_pressed"]};
        }}
        
        QComboBox:disabled {{
            background-color: {colors["background_gray"]};
            color: {colors["text_disabled"]};
            border-color: {colors["background_gray"]};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: {s(20)}px;
            border: none;
            border-left: 1px solid {colors["border_light"]};
            border-top-right-radius: {params["border_radius_small"]};
            border-bottom-right-radius: {params["border_radius_small"]};
            background: transparent;
        }}
        
        QComboBox::drop-down:hover {{
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 {colors["secondary"]}, 
                                      stop: 1 {colors["secondary_hover"]});
            border-left-color: {colors["secondary"]};
        }}
        
        QComboBox::down-arrow {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDdMMTEgMSIgc3Ryb2tlPSIjNmM3NTdkIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            width: {s(12)}px;
            height: {s(8)}px;
        }}
        
        QComboBox::down-arrow:hover {{
            image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw2IDdMMTEgMSIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
        }}
        
        QComboBox::down-arrow:pressed {{
            top: 1px;
            left: 1px;
        }}
        
        
        QComboBox QAbstractItemView {{
            border: 0px;
            outline: 0px;
            background: {colors["white"]};
            border-radius: {params["border_radius_small"]};
            padding: 0px;
            margin: 0px;
            color: {colors["text"]};
            selection-background-color: transparent;
            alternate-background-color: transparent;
            show-decoration-selected: 0;
            gridline-color: transparent;
        }}
        
        QComboBox QAbstractItemView::item {{
            background: transparent;
            border: none;
            border-radius: {params["border_radius_very_small"]};
            padding: {s(6)}px {s(10)}px;
            margin: {s(1)}px {s(2)}px;
            color: {colors["text"]};
            font-weight: 500;
            min-height: {s(16)}px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background: {colors["list_item_hover_background"]};
            color: {colors["list_item_hover_text"]};
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background: {colors["secondary"]};
            color: {colors["text_on_primary"]};
            font-weight: 600;
        }}
        
        
        QComboBox QAbstractItemView QScrollBar:vertical {{
            background: {colors["background_light"]};
            width: {s(6)}px;
            border-radius: {s(3)}px;
            margin: {s(1)}px;
            border: none;
        }}
        
        QComboBox QAbstractItemView QScrollBar::handle:vertical {{
            background: {colors["scrollbar_handle_start"]};
            border-radius: {s(3)}px;
            min-height: {s(15)}px;
            border: none;
        }}
        
        QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {{
            background: {colors["scrollbar_handle_hover_start"]};
        }}
    """