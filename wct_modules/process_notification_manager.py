from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
    QPushButton, QFrame, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QPalette, QColor
from datetime import datetime


class NotificationPopup(QWidget):
    """右上角悬浮通知弹窗"""
    clicked = Signal(str, str)
    
    def __init__(self, tool_name, process_id, process_name=None, parent=None):
        super().__init__(parent)
        self.tool_name = tool_name
        self.process_id = process_id
        self.process_name = process_name or f"进程"
        self.init_ui()
        self.setup_animations()
        
    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 100)
        

        main_frame = QFrame()
        main_frame.setObjectName("notification_popup")
        main_frame.setStyleSheet("""
            QFrame#notification_popup {
                background: rgba(76, 175, 80, 0.95);
                border: 2px solid #4caf50;
                border-radius: 8px;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                color: white;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        

        title_label = QLabel(f"✅ 工具执行完成")
        title_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        layout.addWidget(title_label)
        

        info_layout = QHBoxLayout()
        info_label = QLabel(f"工具: {self.tool_name}")
        info_label.setFont(QFont("Microsoft YaHei", 9))
        

        process_label = QLabel(f"进程: {self.process_name}")
        process_label.setFont(QFont("Microsoft YaHei", 9))
        

        jump_btn = QPushButton("跳转")
        jump_btn.clicked.connect(self.on_jump_clicked)
        jump_btn.setFixedSize(50, 24)
        
        info_layout.addWidget(info_label)
        info_layout.addStretch()
        info_layout.addWidget(jump_btn)
        layout.addLayout(info_layout)
        

        process_layout = QHBoxLayout()
        process_layout.addWidget(process_label)
        process_layout.addStretch()
        layout.addLayout(process_layout)
        

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_frame)
        

        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
    def setup_animations(self):

        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.InOutQuad)
        

        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(500)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_animation.finished.connect(self.hide)
        
    def show_notification(self):
        """显示通知"""

        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 60
            self.move(x, y)
        
        self.show()
        self.fade_in_animation.start()
        

        QTimer.singleShot(5000, self.fade_out)
        
    def fade_out(self):
        """淡出动画"""
        self.fade_out_animation.start()
        
    def on_jump_clicked(self):
        """跳转按钮点击"""
        self.clicked.emit(self.tool_name, self.process_id)
        self.fade_out()
        
    def mousePressEvent(self, event):
        """点击通知也可以跳转"""
        if event.button() == Qt.LeftButton:
            self.on_jump_clicked()


class ProcessNotificationManager:
    """进程状态通知管理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.completed_processes = {}
        self.tab_notifications = {}
        self.tool_notifications = {}
        self.active_popups = []
        

        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.update_ui_notifications)
        self.ui_update_timer.start(1000)
        
    def process_completed(self, tool_name, process_id, tab_id=None, process_name=None):
        """处理进程完成事件"""
        if not tool_name or not process_id:
            return
            
        completion_time = datetime.now()
        

        if tool_name not in self.completed_processes:
            self.completed_processes[tool_name] = {}
        self.completed_processes[tool_name][process_id] = {
            'completion_time': completion_time,
            'process_name': process_name or f"进程"
        }
        

        if tab_id:
            self.tab_notifications[tab_id] = completion_time
            

        self.tool_notifications[tool_name] = True
        

        self.show_popup_notification(tool_name, process_id, process_name)
        

        self.update_ui_notifications()
        
    def show_popup_notification(self, tool_name, process_id, process_name=None):
        """显示右上角弹窗通知"""
        popup = NotificationPopup(tool_name, process_id, process_name, self.main_window)
        popup.clicked.connect(self.on_popup_clicked)
        self.active_popups.append(popup)
        

        popup_index = len(self.active_popups) - 1
        if self.main_window:
            main_rect = self.main_window.geometry()
            x = main_rect.right() - popup.width() - 20
            y = main_rect.top() + 60 + (popup_index * (popup.height() + 10))
            popup.move(x, y)
        
        popup.show_notification()
        

        QTimer.singleShot(6000, lambda: self.cleanup_popup(popup))
        
    def cleanup_popup(self, popup):
        """清理弹窗引用"""
        if popup in self.active_popups:
            self.active_popups.remove(popup)
        popup.deleteLater()
        
    def on_popup_clicked(self, tool_name, process_id):
        """处理弹窗点击事件"""

        self.jump_to_process(tool_name, process_id)
        
    def jump_to_process(self, tool_name, process_id):
        """跳转到指定工具和进程页面"""
        try:

            if hasattr(self.main_window, 'floating_toolbar'):

                self.main_window.on_tool_selected(tool_name)
                

            if hasattr(self.main_window, 'terminal_area'):
                terminal_area = self.main_window.terminal_area

                for tab_id, tab in terminal_area.tabs.items():
                    if (hasattr(tab, 'tool_name') and tab.tool_name == tool_name and 
                        tab_id == process_id):

                        tab_index = terminal_area.tab_widget.indexOf(tab)
                        if tab_index >= 0:
                            terminal_area.tab_widget.setCurrentIndex(tab_index)

                            self.clear_tab_notification(tab_id)
                        break
                        
        except Exception as e:
            print(f"跳转到进程页面失败: {e}")
            
    def clear_tab_notification(self, tab_id):
        """清除标签页通知状态"""
        if tab_id in self.tab_notifications:
            del self.tab_notifications[tab_id]
            

        self.update_tab_notifications()
        

        self.update_toolbar_notifications()
        
    def clear_tool_notification(self, tool_name):
        """清除工具栏工具通知状态"""
        if tool_name in self.tool_notifications:
            del self.tool_notifications[tool_name]
            

        if tool_name in self.completed_processes:
            del self.completed_processes[tool_name]
            

        self.update_toolbar_notifications()
        
    def has_tab_notification(self, tab_id):
        """检查标签页是否有通知"""
        return tab_id in self.tab_notifications
        
    def has_tool_notification(self, tool_name):
        """检查工具是否有通知"""
        return self.tool_notifications.get(tool_name, False)
        
    def check_and_clear_tool_notification(self, tool_name):
        """检查并清除工具通知（如果所有相关进程通知都已清除）"""
        if tool_name not in self.completed_processes:
            return True
            

        all_viewed = True
        for process_id in self.completed_processes[tool_name]:
            if process_id in self.tab_notifications:
                all_viewed = False
                break
                

        if all_viewed:
            self.clear_tool_notification(tool_name)
            return True
            
        return False
        
    def check_tool_notifications_cleared(self, tool_name):
        """检查工具下的所有标签页通知是否都已清除 - 保持向后兼容"""
        return self.check_and_clear_tool_notification(tool_name)
        
    def update_ui_notifications(self):
        """更新UI通知显示"""

        self.update_tab_notifications()
        

        self.update_toolbar_notifications()
        
    def update_tab_notifications(self):
        """更新标签页通知显示 - 使用*号标记而不是红色字体"""
        if not hasattr(self.main_window, 'terminal_area'):
            return
            
        terminal_area = self.main_window.terminal_area
        for i in range(terminal_area.tab_widget.count()):
            tab = terminal_area.tab_widget.widget(i)
            if tab and hasattr(tab, 'tab_id'):
                tab_id = tab.tab_id
                has_notification = self.has_tab_notification(tab_id)
                

                current_text = terminal_area.tab_widget.tabText(i)

                original_name = current_text.rstrip('*')
                

                if has_notification:
                    if not current_text.endswith('*'):
                        display_name = f"{original_name}*"
                        terminal_area.tab_widget.setTabText(i, display_name)
                else:

                    if current_text.endswith('*'):
                        terminal_area.tab_widget.setTabText(i, original_name)
                    
    def update_toolbar_notifications(self):
        """更新工具栏通知显示 - 使用红色边框而不是红色字体"""
        if not hasattr(self.main_window, 'floating_toolbar'):
            return
            
        toolbar = self.main_window.floating_toolbar
        for button in toolbar.tool_buttons:
            tool_name = button.tool_name
            has_notification = self.has_tool_notification(tool_name)
            

            if has_notification:

                button.setStyleSheet("""
                    QPushButton {
                        border: 2px solid #ff4444;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        border: 2px solid #ff6666;
                        background-color: rgba(255, 68, 68, 0.1);
                    }
                    QPushButton:checked {
                        border: 2px solid #ff4444;
                        background-color: rgba(255, 68, 68, 0.2);
                    }
                """)
            else:

                button.setStyleSheet("")
                
    def on_tab_clicked(self, tab_id):
        """标签页被点击时调用"""
        if self.has_tab_notification(tab_id):
            self.clear_tab_notification(tab_id)
            

            if hasattr(self.main_window, 'terminal_area'):
                terminal_area = self.main_window.terminal_area
                for tab in terminal_area.tabs.values():
                    if (hasattr(tab, 'tab_id') and tab.tab_id == tab_id and
                        hasattr(tab, 'tool_name')):

                        self.check_and_clear_tool_notification(tab.tool_name)
                        break
                        
    def cleanup_old_notifications(self, max_age_hours=24):
        """清理过期的通知记录"""
        current_time = datetime.now()
        max_age = max_age_hours * 3600
        

        tools_to_remove = []
        for tool_name, processes in self.completed_processes.items():
            processes_to_remove = []
            for process_id, process_info in processes.items():

                if isinstance(process_info, dict):
                    completion_time = process_info.get('completion_time')
                else:
                    completion_time = process_info
                
                if completion_time:
                    age = (current_time - completion_time).total_seconds()
                    if age > max_age:
                        processes_to_remove.append(process_id)
                        
            for process_id in processes_to_remove:
                del processes[process_id]
                
            if not processes:
                tools_to_remove.append(tool_name)
                
        for tool_name in tools_to_remove:
            del self.completed_processes[tool_name]
            

        tabs_to_remove = []
        for tab_id, completion_time in self.tab_notifications.items():
            age = (current_time - completion_time).total_seconds()
            if age > max_age:
                tabs_to_remove.append(tab_id)
                
        for tab_id in tabs_to_remove:
            del self.tab_notifications[tab_id]
            

        self.update_ui_notifications()
        
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'ui_update_timer'):
            self.ui_update_timer.stop()
            

        for popup in self.active_popups[:]:
            popup.close()
            popup.deleteLater()
        self.active_popups.clear()