from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QScrollArea, QFrame, QLabel, QMessageBox,
    QStatusBar, QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction, QFont
import os
import json

from .floating_toolbar import FloatingToolBar
from .tool_operation import ToolOperationWidget
from .terminal_area import TerminalArea
from .tool_scanner import ToolScanner
from .config import ConfigManager
from .utils import get_system_font, get_project_root

from .search_system import SearchWidget, AdvancedSearchDialog
from .virtual_env import VirtualEnvWidget
from .system_env import SystemEnvWidget

from .update_checker import UpdateManager
from .theme_manager import ThemeManager
from .font_scale_widget import FontScaleWidget, GlobalFontScaleManager
from .promotion_widget import PromotionWidget
from .process_notification_manager import ProcessNotificationManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        

        self.theme_manager = ThemeManager(self.config_manager)
        

        self.font_scale_manager = GlobalFontScaleManager(self.config_manager)
        

        self.tool_scanner = ToolScanner()
        

        

        self.update_manager = UpdateManager("1.0.0")
        

        self.current_selected_tool = None
        

        self.promotion_widget = None
        self.promotion_shown = False
        

        self.notification_manager = None
        


        self.search_widget = None
        self.virtual_env_widget = None
        self.system_env_widget = None

        self.advanced_search_dialog = None
        
        self.init_ui()
        

        self.setup_connections()
        

        self.apply_initial_theme_and_font()
        

        self.notification_manager = ProcessNotificationManager(self)
        
        self.load_tools()
        
    def init_ui(self):
        self.setWindowTitle("White Cat Toolbox")
        self.setMinimumSize(1200, 800)
        
        # Set window icon using favicon.ico
        favicon_path = get_project_root() / "favicon.ico"
        if favicon_path.exists():
            self.setWindowIcon(QIcon(str(favicon_path)))
        self.resize(1600, 1000)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.floating_toolbar = FloatingToolBar()
        main_layout.addWidget(self.floating_toolbar)
        

        self.create_promotion_widget()
        

        self.main_tabs = QTabWidget()
        

        tool_widget = QWidget()
        tool_layout = QVBoxLayout(tool_widget)
        tool_layout.setContentsMargins(0, 0, 0, 0)
        
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        self.tool_operation = ToolOperationWidget()
        self.terminal_area = TerminalArea()
        
        content_splitter.addWidget(self.tool_operation)
        content_splitter.addWidget(self.terminal_area)
        content_splitter.setSizes([400, 800])
        
        tool_layout.addWidget(content_splitter)
        self.main_tabs.addTab(tool_widget, "工具操作")
        



        

        

        self.virtual_env_widget = VirtualEnvWidget(theme_manager=self.theme_manager)
        self.main_tabs.addTab(self.virtual_env_widget, "虚拟环境")
        

        self.system_env_widget = SystemEnvWidget(theme_manager=self.theme_manager)
        self.main_tabs.addTab(self.system_env_widget, "系统环境")
        

        

        self.font_scale_widget = FontScaleWidget(self.config_manager)
        self.main_tabs.addTab(self.font_scale_widget, "字体缩放")
        

        if self.should_show_promotion():
            main_layout.addWidget(self.promotion_widget)
            self.main_tabs.hide()
            self.promotion_shown = True
        else:
            main_layout.addWidget(self.main_tabs)
            self.promotion_shown = False
        
        self.floating_toolbar.tool_selected.connect(self.on_tool_selected)
        self.floating_toolbar.promotion_requested.connect(self.show_promotion_widget)
        

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_bar.showMessage("就绪")
        
    def setup_connections(self):

        self.tool_operation.tool_execution_requested.connect(self.execute_tool)
        

        self.terminal_area.tool_execution_started.connect(self.on_tool_execution_started)
        self.terminal_area.tool_execution_finished.connect(self.on_tool_execution_finished)
            
        if self.virtual_env_widget:
            self.virtual_env_widget.environment_activated.connect(self.on_virtual_env_activated)
            
        if self.system_env_widget:
            self.system_env_widget.environment_changed.connect(self.on_system_env_changed)
            

        

        self.connect_update_manager()
        
    def load_tools(self):
        try:
            tools_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")
            self.tool_scanner.scan_tools(tools_dir)
            

            if hasattr(self, 'floating_toolbar'):
                self.floating_toolbar.update_tools(self.tool_scanner.get_all_tools(), self.tool_scanner)
                
            self.status_bar.showMessage(f"已加载 {len(self.tool_scanner.get_all_tools())} 个工具")
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载工具时出错: {str(e)}")
            
    def execute_tool(self, tool_info, parameters):
        try:
            self.terminal_area.execute_tool(tool_info, parameters)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行工具时出错: {str(e)}")
            
    def on_tool_execution_started(self, tool_name):
        self.status_bar.showMessage(f"正在执行: {tool_name}")
        
    def on_tool_execution_finished(self, tool_name, success):
        status = "成功" if success else "失败"
        self.status_bar.showMessage(f"工具 {tool_name} 执行{status}")
        

        if self.notification_manager and success:

            process_id = None
            tab_id = None
            if hasattr(self.terminal_area, 'tool_processes'):
                process_id = self.terminal_area.tool_processes.get(tool_name)
                tab_id = process_id
            
            if process_id:
                self.notification_manager.process_completed(tool_name, process_id, tab_id)
        
        QTimer.singleShot(3000, lambda: self.status_bar.showMessage("就绪"))
        
    def on_tool_selected(self, tool_name):

        if self.promotion_shown:
            self.close_promotion_widget()
            
        tool_info = self.tool_scanner.get_tool_info(tool_name)
        if tool_info:
            self.tool_operation.load_tool(tool_info)

            self.terminal_area.filter_tabs_by_tool(tool_name)

            self.current_selected_tool = tool_name
        
    def get_terminal_area(self):
        return self.terminal_area
             
    def show_advanced_search(self):
        if not self.advanced_search_dialog:
            self.advanced_search_dialog = AdvancedSearchDialog(self)
        self.advanced_search_dialog.show()
        
    def activate_virtual_env(self):
        self.main_tabs.setCurrentWidget(self.virtual_env_widget)
        
    def refresh_system_env(self):
        if self.system_env_widget:
            self.system_env_widget.load_variables()
            
    def show_about(self):
        QMessageBox.about(self, "关于", 
                         "White Cat Toolbox v3.0\n\n"
                         "一个强大的渗透测试工具集成平台\n\n"
                         "Phase 3 功能包括:\n"
                         "- 模板管理系统\n"
                         "- 搜索功能系统\n"
                         "- 虚拟环境管理\n"
                         "- 系统环境管理")
                         
    def perform_search(self, query, search_options):

        data_sources = {
            'tools': self.tool_scanner.get_all_tools(),
            'parameters': self.get_tool_parameters(),
            'outputs': self.get_terminal_outputs()
        }
        
        if self.search_widget:
            self.search_widget.perform_search(query, search_options, data_sources)
            
    def on_search_result_selected(self, result):

        if result.type == 'tool':
            tool_info = result.metadata.get('tool_info')
            if tool_info:
                self.main_tabs.setCurrentIndex(0)
                self.tool_operation.load_tool(tool_info)
        elif result.type == 'parameter':
            tool_name = result.metadata.get('tool_name')
            param_name = result.metadata.get('param_name')
            if tool_name and param_name:
                tool_info = self.tool_scanner.get_tool_info(tool_name)
                if tool_info:
                    self.main_tabs.setCurrentIndex(0)
                    self.tool_operation.load_tool(tool_info)
                    self.tool_operation.focus_parameter(param_name)
        elif result.type == 'output':

            self.terminal_area.show_output_content(result.metadata.get('full_content', ''))
            
        self.status_bar.showMessage(f"已选择搜索结果: {result.title}")
        
    def on_virtual_env_activated(self, env_path, env_vars):

        self.terminal_area.set_environment_variables(env_vars)
        self.status_bar.showMessage(f"已激活虚拟环境: {env_path}")
        
    def on_system_env_changed(self):

        self.status_bar.showMessage("系统环境变量已更新")
        
    def get_tool_parameters(self):

        parameters = {}
        for tool_info in self.tool_scanner.get_all_tools():
            if hasattr(tool_info, 'parameters'):
                parameters[tool_info.name] = tool_info.parameters
        return parameters
        
    def get_terminal_outputs(self):

        if hasattr(self.terminal_area, 'get_output_history'):
            return self.terminal_area.get_output_history()
        return []
        

                

    

    

    def connect_update_manager(self):
        """连接更新管理器信号"""
        try:

            self.update_manager.update_available.connect(self.on_update_available)
            self.update_manager.update_check_failed.connect(self.on_update_check_failed)
            

            self.update_manager.start_auto_check()
        except Exception as e:
            print(f'连接更新管理器信号失败: {e}')
    
    def on_update_available(self, version_info):
        """有更新可用时的处理"""
        try:

            pass
        except Exception as e:
            print(f'处理更新通知失败: {e}')
    
    def on_update_check_failed(self, error_msg):
        """更新检查失败时的处理"""
        try:
            print(f'更新检查失败: {error_msg}')
        except Exception as e:
            print(f'处理更新检查失败通知失败: {e}')
    
    def check_for_updates(self):
        """手动检查更新"""
        try:
            self.update_manager.check_for_updates()
        except Exception as e:
            print(f'手动检查更新失败: {e}')
    

    def new_terminal_tab(self):
        """新建终端标签页"""
        try:
            self.terminal_area.add_terminal_tab()
            self.status_bar.showMessage("已创建新的终端标签页")
        except Exception as e:
            print(f'创建新终端标签页失败: {e}')
    
    def clear_all_terminals(self):
        """清空所有终端"""
        try:
            self.terminal_area.clear_all_terminals()
            self.status_bar.showMessage("已清空所有终端输出")
        except Exception as e:
            print(f'清空所有终端失败: {e}')
    
    def stop_all_processes(self):
        """停止所有进程"""
        try:
            self.terminal_area.stop_all_processes()
            self.status_bar.showMessage("已停止所有运行中的进程")
        except Exception as e:
            print(f'停止所有进程失败: {e}')
    
    def toggle_new_tab_mode(self):
        """切换新标签页运行模式"""
        try:
            if hasattr(self.terminal_area, 'run_in_new_tab_checkbox'):
                current_state = self.terminal_area.run_in_new_tab_checkbox.isChecked()
                self.terminal_area.run_in_new_tab_checkbox.setChecked(not current_state)
                mode = "新标签页" if not current_state else "当前标签页"
                self.status_bar.showMessage(f"命令执行模式已切换为: {mode}")
        except Exception as e:
            print(f'切换新标签页模式失败: {e}')
    

    def set_theme(self, theme_name):
        """设置主题"""
        try:
            self.theme_manager.set_theme(theme_name)
            self.status_bar.showMessage(f"已切换到{theme_name}主题")
        except Exception as e:
            print(f'切换主题失败: {e}')
            QMessageBox.warning(self, "警告", f"切换主题时出错: {str(e)}")
    
    def show_font_scale_settings(self):
        """显示字体缩放设置标签页"""
        try:

            for i in range(self.main_tabs.count()):
                if self.main_tabs.tabText(i) == "字体缩放":
                    self.main_tabs.setCurrentIndex(i)
                    break
        except Exception as e:
            print(f'显示字体缩放设置失败: {e}')
    
    def apply_initial_theme_and_font(self):
        """应用初始主题和字体设置"""
        try:

            self.theme_manager.load_theme_from_config()
            

            self.font_scale_manager.initialize()
        except Exception as e:
            print(f'应用初始主题和字体设置失败: {e}')
    
    def closeEvent(self, event):
        """应用关闭事件"""
        try:

            if hasattr(self, 'notification_manager') and self.notification_manager:
                self.notification_manager.cleanup()
                

            self.config_manager.save_app_config()
            

            if hasattr(self, 'terminal_area'):
                self.terminal_area.stop_all_processes()
            

            if hasattr(self, 'update_manager'):
                self.update_manager.stop_auto_check()
                
        except Exception as e:
            print(f"关闭应用时出错: {e}")
        
        event.accept()

    def create_promotion_widget(self):
        """创建推广界面组件"""
        self.promotion_widget = PromotionWidget(self.config_manager, self)
        self.promotion_widget.promotion_closed.connect(self.on_promotion_closed)
        
    def should_show_promotion(self):
        """判断是否应该显示推广界面"""

        try:
            return self.config_manager.app_config.get('show_promotion_on_startup', True)
        except:
            return True
            
    def on_promotion_closed(self):
        """推广界面关闭事件处理"""
        self.close_promotion_widget()
        
    def close_promotion_widget(self):
        """关闭推广界面，显示主界面"""
        if self.promotion_shown and self.promotion_widget:

            if self.promotion_widget.parent():
                self.promotion_widget.setParent(None)
            self.promotion_widget.hide()
            

            if not self.main_tabs.parent():
                self.centralWidget().layout().addWidget(self.main_tabs)
            self.main_tabs.show()
            
            self.promotion_shown = False
            


                
    def show_promotion_widget(self):
        """显示推广界面"""
        if not self.promotion_shown:

            if self.main_tabs.parent():
                self.main_tabs.setParent(None)
            self.main_tabs.hide()
            

            if not self.promotion_widget.parent():
                self.centralWidget().layout().addWidget(self.promotion_widget)
            self.promotion_widget.show()
            
            self.promotion_shown = True
            

            try:
                self.config_manager.app_config['show_promotion_on_startup'] = True
                self.config_manager.save_app_config()
            except Exception as e:
                print(f"保存配置失败: {e}")
