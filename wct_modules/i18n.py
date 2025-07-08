import json
import os
from typing import Dict, Any

class I18nManager:
    def __init__(self):
        self.current_language = "zh_CN"
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        
        translations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations")
        os.makedirs(translations_dir, exist_ok=True)
        zh_file = os.path.join(translations_dir, "zh_CN.json")
        if os.path.exists(zh_file):
            with open(zh_file, 'r', encoding='utf-8') as f:
                self.translations["zh_CN"] = json.load(f)
        else:
            self.translations["zh_CN"] = self.get_default_chinese_translations()
            self.save_translation_file("zh_CN")
        en_file = os.path.join(translations_dir, "en_US.json")
        if os.path.exists(en_file):
            with open(en_file, 'r', encoding='utf-8') as f:
                self.translations["en_US"] = json.load(f)
        else:
            self.translations["en_US"] = self.get_default_english_translations()
            self.save_translation_file("en_US")
    
    def save_translation_file(self, language: str):
        
        translations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "translations")
        os.makedirs(translations_dir, exist_ok=True)
        
        file_path = os.path.join(translations_dir, f"{language}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.translations[language], f, ensure_ascii=False, indent=2)
    
    def get_default_chinese_translations(self) -> Dict[str, Any]:
        
        return {
            "window": {
                "title": "白猫工具箱-v0.0.3_beta",
                "tool_list": "工具列表",
                "promotion": "推广"
            },
            "buttons": {
                "home": "🏠 返回推广页面",
                "home_tooltip": "返回推广页面",
                "scale_tooltip": "点击调整界面缩放比例",
                "backup": "💾 备份配置",
                "restore": "📁 恢复配置",
                "open_folder": "📂 打开 {} 文件夹",
                "language": "🌐 语言",
                "chinese": "中文",
                "english": "English",
                "clear_options": "清空选项",
                "custom_template": "自定义模板",
                "new_tab": "新建标签页",
                "start_run": "开始运行",
                "stop": "停止",
                "clear_screen": "清屏",
                "search": "搜索",
                "clear": "清除",
                "cancel": "取消",
                "save": "保存",
                "close": "关闭",
                "apply": "应用",
                "delete": "删除",
                "import": "📥 导入模板",
                "export": "📤 导出模板"
            },
            "labels": {
                "run_command": "运行命令:",
                "python_venv": "Python虚拟环境路径 (可选):",
                "custom_env": "自定义环境变量 (可选):",
                "global_search": "🔍 全局搜索:",
                "search_mode": "匹配模式:",
                "param_name": "参数名称:",
                "display_name": "显示名称:",
                "param_desc": "参数描述:",
                "param_type": "参数类型:",
                "required_param": "必填参数",
                "running": "运行中",
                "welcome": "欢迎使用白猫工具箱交互式终端！",
                "template_manager": "📋 模板管理",
                "template_name": "模板名称",
                "template_remark": "模板备注",
                "operation": "操作",
                "unnamed_template": "未命名模板",
                "no_remark": "暂无备注"
            },
            "placeholders": {
                "command_input": "请输入工具运行命令，如: python tool.py 或 tool.exe",
                "venv_path": "如: C:/Users/xxx/venv 或 /home/xxx/venv",
                "env_vars": "如: JAVA_HOME=/usr/lib/jvm/java-11; PATH=/usr/bin:$PATH",
                "global_search": "全局搜索参数...",
                "search_input": "输入搜索关键词...",
                "input_value": "输入值",
                "required_input": "必填 - 请输入值",
                "search_params": "搜索参数（支持参数名、显示名、介绍）..."
            },
            "tooltips": {
                "command_input": "输入完整的工具运行命令，支持任何可执行文件或脚本",
                "venv_path": "Python虚拟环境路径，如果工具需要特定Python环境，请指定虚拟环境路径。支持相对路径和绝对路径。",
                "env_vars": "自定义环境变量，格式：变量名=值; 多个变量用分号分隔。例如：JAVA_HOME=/usr/lib/jvm/java-11; PATH=/usr/bin:$PATH",
                "run_mode": "💡 运行模式切换\n\n• 新建标签页：每次运行都创建新的进程标签页\n• 当前标签页：在当前标签页中运行（会终止之前的进程）",
                "search_toggle": "切换搜索面板",
                "template_name": "双击可编辑模板名称",
                "template_remark": "双击可编辑模板备注",
                "required_param": "* 此参数为必填项",
                "drag_reorder": "💡 提示：拖拽此参数可以重新排序"
            },
            "search_modes": {
                "fuzzy": "模糊匹配",
                "exact": "精确匹配",
                "regex": "正则匹配"
            },
            "param_types": {
                "checkbox": "勾选项",
                "input": "输入项"
            },
            "tabs": {
                "common_params": "常用参数",
                "all_params": "全部参数",
                "checkbox_params": "勾选项",
                "input_params": "输入项"
            },
            "actions": {
                "add_checkbox": "添加勾选项",
                "add_input": "添加输入项"
            },
            "context_menu": {
                "edit_param": "编辑参数",
                "set_required": "设为必填",
                "unset_required": "取消必填",
                "move_to_input": "移动到输入项",
                "move_to_checkbox": "移动到勾选项",
                "copy_to_common": "复制到常用参数",
                "remove_from_common": "从常用参数中移除",
                "copy": "📋 复制",
                "paste": "📌 粘贴",
                "select_all": "🔍 全选",
                "clear_screen": "🧹 清屏"
            },
            "scale": {
                "modes": {
                    "75%": "紧凑模式",
                    "100%": "标准模式",
                    "125%": "舒适模式",
                    "150%": "大字模式", 
                    "175%": "超大模式",
                    "200%": "最大模式"
                },
                "current": "当前"
            },
            "messages": {
                "scale_changed": "界面缩放比例已更改。",
                "scale_restart": "需要重启应用以应用所有更改。",
                "backup_success": "备份成功",
                "backup_success_msg": "配置已成功备份到：\n{}",
                "backup_failed": "备份失败",
                "backup_failed_msg": "备份过程中发生错误：\n{}",
                "restore_success": "恢复成功",
                "restore_failed": "恢复失败", 
                "restore_failed_msg": "恢复过程中发生错误：\n{}",
                "file_error": "文件错误",
                "invalid_zip": "选择的文件不是有效的ZIP文件",
                "confirm_restore": "确认恢复配置",
                "confirm_restore_msg": "即将恢复以下配置：\n\n{}\n是否继续？",
                "invalid_backup": "这个备份文件可能不是白猫工具箱的配置备份，是否继续恢复？",
                "folder_not_exist": "文件夹不存在",
                "folder_not_exist_msg": "工具文件夹不存在：\n{}",
                "hint": "提示",
                "language_changed": "语言已更改",
                "language_restart": "需要重启应用以应用语言更改。",
                "warning": "警告",
                "param_name_empty": "参数名称和显示名称不能为空！",
                "no_matches": "❌ 未找到匹配的参数",
                "found_matches": "✅ 找到 {}/{} 个参数",
                "global_search_result": "全局搜索 '{}' ({}): 找到 {} 个匹配参数",
                "search_no_matches": "未找到匹配项",
                "search_found_matches": "找到 {} 个匹配项",
                "welcome_terminal": "💡 欢迎使用白猫工具箱交互式终端！",
                "terminal_features": "💡 快捷键：Ctrl+C复制 | Ctrl+V粘贴 | Ctrl+A全选 | Ctrl+L清屏",
                "terminal_control": "⚡ 进程控制：右键菜单或点击停止按钮可中断进程",
                "terminal_logs": "📝 系统日志已集成，支持彩色标签分类显示",
                "terminal_init": "[系统] 终端初始化完成",
                "terminal_cleared": "🧹 终端已清空",
                "process_not_running": "[错误] 进程未运行，无法执行命令: {}",
                "process_started": "[系统] 启动终端进程: {}",
                "parse_command_error": "无法解析运行命令",
                "no_param_config": "暂无参数配置",
                "command_sent": "[发送] {}",
                "interrupt_signal_sent": "发送中断信号到终端进程",
                "no_running_process": "没有正在运行的终端进程",
                "error_occurred": "发生错误",
                "success": "成功",
                "failed": "失败",
                "save_error": "保存失败",
                "load_error": "加载失败",
                "edit_template_name": "编辑模板名称",
                "edit_template_remark": "编辑模板备注",
                "save_template": "保存模板",
                "access": "访问",
                "loading_cache": "正在分批加载{}条缓存数据，避免界面卡顿...",
                "async_flush_error": "异步刷新缓存出错: {}",
                "async_load_complete": "异步加载完成: 处理{}条，剩余{}条",
                "no_tab_selected": "没有选择参数选项卡",
                "cleared_params": "已清空 {} 个参数选项",
                "config_backed_up": "配置文件已备份到: {}",
                "run_mode_new_tab": "新建标签页",
                "run_mode_current_tab": "当前标签页",
                "process_start_failed": "启动进程失败: {}",
                "send_interrupt_signal": "发送中断信号到终端进程",
                "no_running_terminal": "没有正在运行的终端进程",
                "send_interrupt_windows": "发送中断信号到进程 (Windows)",
                "force_terminate": "强制终止进程",
                "send_interrupt_unix": "发送中断信号到进程 (Unix)",
                "graceful_terminate": "尝试优雅终止进程",
                "no_running_process": "没有正在运行的进程",
                "search_line_format": "行 {}: {}",
                "show_search_panel": "显示搜索面板",
                "hide_search_panel": "隐藏搜索面板"
            },
            "system": {
                "log_tab_name": "系统日志",
                "log_title": "白猫工具箱系统日志",
                "log_description": "此标签页集成了所有系统日志信息",
                "log_includes": "包括工具启动、参数验证、进程管理等操作记录",
                "log_realtime": "实时显示系统运行状态和错误信息"
            },
            "system_logs": {
                "system": "[系统]",
                "error": "[错误]",
                "success": "[成功]",
                "info": "[信息]",
                "warning": "[警告]"
            },
            "dialog": {
                "backup_title": "备份配置文件",
                "restore_title": "选择配置备份文件",
                "zip_files": "ZIP文件 (*.zip)",
                "edit_param_title": "编辑参数信息",
                "template_manager_title": "模板管理"
            },
            "backup": {
                "filename": "白猫工具箱配置备份_{}",
                "description": "白猫工具箱配置备份文件",
                "backup_time": "备份时间: {}",
                "version": "版本: {}",
                "description_label": "描述: {}",
                "includes": "包含的内容:",
                "restored_files": "✅ 已恢复 {} 个文件：",
                "backup_files": "💾 已备份 {} 个原文件：",
                "more_files": "... 以及其他 {} 个文件",
                "more_backups": "... 以及其他 {} 个备份文件"
            },
            "promotion": {
                "title": "白猫工具箱",
                "promotion_info": "推广信息",
                "enable_promotion": "开启推广",
                "disable_promotion": "关闭推广",
                "project_recommendation": "项目推荐",
                "sponsor": "赞助商",
                "sponsor_thanks": "💎 赞助鸣谢",
                "no_promotion": "暂无推广内容",
                "file_not_exist": "推广文件不存在",
                "read_failed": "读取失败: {}",
                "welcome_text": "欢迎使用白猫工具箱！",
                "save_config_failed": "保存推广配置失败: {}",
                "intro_text": """欢迎使用白猫工具箱！

这是一个针对CLI工具的图形化集成平台，旨在解决CLI工具使用门槛高、操作复杂的问题。

主要特点：
• 提供所有参数的图形化配置
• 拖拽控件完成自定义参数排序
• 支持参数模板保存和管理
• 多进程多工具单独运行互不干扰
• 

感谢您的使用！"""
            },
            "terminal": {
                "welcome": "💡 欢迎使用白猫工具箱终端！",
                "ansi_support": "💡 支持完整的ANSI转义序列：进度条、颜色编码、光标控制等",
                "shortcuts": "💡 快捷键：Ctrl+C复制 | Ctrl+V粘贴 | Ctrl+A全选 | Ctrl+L清屏",
                "process_control": "⚡ 进程控制：右键菜单或点击停止按钮可中断进程",
                "new_features": "🚀 新功能：原生支持各种终端应用的显示效果"
            },
            "templates": {
                "manager_title": "模板管理",
                "add_template": "✨ 添加模板",
                "import_template": "📥 导入模板",
                "export_template": "📤 导出模板",
                "template_name": "模板名称",
                "template_remark": "模板备注",
                "operation": "操作",
                "apply": "应用",
                "delete": "删除",
                "edit_name": "编辑名称",
                "edit_remark": "编辑备注",
                "confirm_delete": "确认删除",
                "delete_confirm_msg": "确定要删除模板 '{}' 吗？",
                "template_applied": "模板已应用",
                "template_deleted": "模板已删除",
                "export_success": "模板导出成功",
                "import_success": "模板导入成功",
                "export_failed": "导出失败",
                "import_failed": "导入失败",
                "select_template_file": "选择模板文件",
                "save_template_file": "保存模板文件",
                "json_files": "JSON文件 (*.json)"
            },
            "process": {
                "running": "运行中",
                "stopped": "已停止",
                "finished": "已完成",
                "error": "错误",
                "starting": "启动中",
                "stopping": "停止中",
                "process_finished": "进程完成",
                "process_error": "进程错误",
                "process_stopped": "进程已停止",
                "exit_code": "退出代码",
                "runtime": "运行时间",
                "clear_output": "清空输出",
                "stop_process": "停止进程",
                "search_toggle": "切换搜索",
                "search_placeholder": "搜索内容...",
                "prev_match": "上一个",
                "next_match": "下一个",
                "match_case": "区分大小写",
                "whole_word": "全词匹配",
                "regex_mode": "正则表达式",
                "found_matches": "找到 {} 处匹配",
                "no_matches": "未找到匹配项",
                "process_started": "进程已启动",
                "command_executed": "命令已执行"
            },
            "config": {
                "parse_error": "配置文件解析错误: {}",
                "line_parse_warning": "警告：解析配置文件行时出错: {}, 错误: {}",
                "save_failed": "保存配置失败: {}"
            },
            "utils": {
                "parse_command_error": "无法解析运行命令",
                "scale_saved": "界面缩放设置已保存",
                "scale_loaded": "界面缩放设置已加载"
            },
            "errors": {
                "file_not_found": "文件未找到: {}",
                "permission_denied": "权限被拒绝: {}",
                "connection_failed": "连接失败",
                "timeout": "操作超时",
                "unknown_error": "未知错误: {}",
                "invalid_format": "格式无效",
                "operation_cancelled": "操作已取消"
            }
        }
    
    def get_default_english_translations(self) -> Dict[str, Any]:
        
        return {
            "window": {
                "title": "WhiteCat Toolbox-v0.0.3_beta",
                "tool_list": "Tool List",
                "promotion": "Promotion"
            },
            "buttons": {
                "home": "🏠 Back to Promotion",
                "home_tooltip": "Back to promotion page",
                "scale_tooltip": "Click to adjust interface scale",
                "backup": "💾 Backup Config",
                "restore": "📁 Restore Config",
                "open_folder": "📂 Open {} Folder",
                "language": "🌐 Language",
                "chinese": "中文",
                "english": "English",
                "clear_options": "Clear Options",
                "custom_template": "Custom Template",
                "new_tab": "New Tab",
                "start_run": "Start Run",
                "stop": "Stop",
                "clear_screen": "Clear Screen",
                "search": "Search",
                "clear": "Clear",
                "cancel": "Cancel",
                "save": "Save",
                "close": "Close",
                "apply": "Apply",
                "delete": "Delete",
                "import": "📥 Import Template",
                "export": "📤 Export Template"
            },
            "labels": {
                "run_command": "Run Command:",
                "python_venv": "Python Virtual Environment Path (Optional):",
                "custom_env": "Custom Environment Variables (Optional):",
                "global_search": "🔍 Global Search:",
                "search_mode": "Match Mode:",
                "param_name": "Parameter Name:",
                "display_name": "Display Name:",
                "param_desc": "Parameter Description:",
                "param_type": "Parameter Type:",
                "required_param": "Required Parameter",
                "running": "Running",
                "welcome": "Welcome to WhiteCat Toolbox Interactive Terminal!",
                "template_manager": "📋 Template Manager",
                "template_name": "Template Name",
                "template_remark": "Template Remark",
                "operation": "Operation",
                "unnamed_template": "Unnamed Template",
                "no_remark": "No Remark"
            },
            "placeholders": {
                "command_input": "Enter tool run command, e.g: python tool.py or tool.exe",
                "venv_path": "e.g: C:/Users/xxx/venv or /home/xxx/venv",
                "env_vars": "e.g: JAVA_HOME=/usr/lib/jvm/java-11; PATH=/usr/bin:$PATH",
                "global_search": "Global search parameters...",
                "search_input": "Enter search keywords...",
                "input_value": "Input value",
                "required_input": "Required - Please enter value",
                "search_params": "Search parameters (supports param name, display name, description)..."
            },
            "tooltips": {
                "command_input": "Enter complete tool run command, supports any executable file or script",
                "venv_path": "Python virtual environment path, if tool requires specific Python environment, please specify virtual environment path. Supports relative and absolute paths.",
                "env_vars": "Custom environment variables, format: variable=value; multiple variables separated by semicolons. Example: JAVA_HOME=/usr/lib/jvm/java-11; PATH=/usr/bin:$PATH",
                "run_mode": "💡 Run Mode Switch\n\n• New Tab: Create new process tab for each run\n• Current Tab: Run in current tab (will terminate previous process)",
                "search_toggle": "Toggle search panel",
                "template_name": "Double-click to edit template name",
                "template_remark": "Double-click to edit template remark",
                "required_param": "* This parameter is required",
                "drag_reorder": "💡 Tip: Drag this parameter to reorder"
            },
            "search_modes": {
                "fuzzy": "Fuzzy Match",
                "exact": "Exact Match",
                "regex": "Regex Match"
            },
            "param_types": {
                "checkbox": "Checkbox",
                "input": "Input"
            },
            "tabs": {
                "common_params": "Common Parameters",
                "all_params": "All Parameters",
                "checkbox_params": "Checkbox",
                "input_params": "Input"
            },
            "actions": {
                "add_checkbox": "Add Checkbox",
                "add_input": "Add Input"
            },
            "context_menu": {
                "edit_param": "Edit Parameter",
                "set_required": "Set Required",
                "unset_required": "Unset Required",
                "move_to_input": "Move to Input",
                "move_to_checkbox": "Move to Checkbox",
                "copy_to_common": "Copy to Common Parameters",
                "remove_from_common": "Remove from Common Parameters",
                "copy": "📋 Copy",
                "paste": "📌 Paste",
                "select_all": "🔍 Select All",
                "clear_screen": "🧹 Clear Screen"
            },
            "scale": {
                "modes": {
                    "75%": "Compact Mode",
                    "100%": "Standard Mode",
                    "125%": "Comfortable Mode",
                    "150%": "Large Text Mode",
                    "175%": "Extra Large Mode",
                    "200%": "Maximum Mode"
                },
                "current": "Current"
            },
            "messages": {
                "scale_changed": "Interface scale has been changed.",
                "scale_restart": "Restart the application to apply all changes.",
                "backup_success": "Backup Successful",
                "backup_success_msg": "Configuration has been successfully backed up to:\n{}",
                "backup_failed": "Backup Failed",
                "backup_failed_msg": "An error occurred during backup:\n{}",
                "restore_success": "Restore Successful",
                "restore_failed": "Restore Failed",
                "restore_failed_msg": "An error occurred during restore:\n{}",
                "file_error": "File Error",
                "invalid_zip": "The selected file is not a valid ZIP file",
                "confirm_restore": "Confirm Restore Configuration",
                "confirm_restore_msg": "About to restore the following configuration:\n\n{}\nContinue?",
                "invalid_backup": "This backup file may not be a WhiteCat Toolbox configuration backup, continue restore?",
                "folder_not_exist": "Folder does not exist",
                "folder_not_exist_msg": "Tool folder does not exist:\n{}",
                "hint": "Hint",
                "language_changed": "Language Changed",
                "language_restart": "Restart the application to apply language changes.",
                "warning": "Warning",
                "param_name_empty": "Parameter name and display name cannot be empty!",
                "no_matches": "❌ No matching parameters found",
                "found_matches": "✅ Found {}/{} parameters",
                "global_search_result": "Global search '{}' ({}): Found {} matching parameters",
                "search_no_matches": "No matches found",
                "search_found_matches": "Found {} matches",
                "welcome_terminal": "💡 Welcome to WhiteCat Toolbox Interactive Terminal!",
                "terminal_features": "💡 Shortcuts: Ctrl+C copy | Ctrl+V paste | Ctrl+A select all | Ctrl+L clear screen",
                "terminal_control": "⚡ Process Control: Right-click menu or click stop button to interrupt process",
                "terminal_logs": "📝 System logs integrated, supports color-coded tag classification display",
                "terminal_init": "[System] Terminal initialization complete",
                "terminal_cleared": "🧹 Terminal cleared",
                "process_not_running": "[Error] Process not running, unable to execute command: {}",
                "process_started": "[System] Starting terminal process: {}",
                "parse_command_error": "Unable to parse run command",
                "no_param_config": "No parameter configuration",
                "command_sent": "[Sent] {}",
                "interrupt_signal_sent": "Sending interrupt signal to terminal process",
                "no_running_process": "No running terminal process",
                "error_occurred": "An error occurred",
                "success": "Success",
                "failed": "Failed",
                "save_error": "Save failed",
                "load_error": "Load failed",
                "edit_template_name": "Edit Template Name",
                "edit_template_remark": "Edit Template Remark",
                "save_template": "Save Template",
                "access": "Access",
                "loading_cache": "Loading {} cached data in batches to avoid UI freezing...",
                "async_flush_error": "Async cache flush error: {}",
                "async_load_complete": "Async loading complete: processed {}, remaining {}",
                "no_tab_selected": "No parameter tab selected",
                "cleared_params": "Cleared {} parameter options",
                "config_backed_up": "Configuration file backed up to: {}",
                "run_mode_new_tab": "New Tab",
                "run_mode_current_tab": "Current Tab",
                "process_start_failed": "Failed to start process: {}",
                "send_interrupt_signal": "Sending interrupt signal to terminal process",
                "no_running_terminal": "No running terminal process",
                "send_interrupt_windows": "Send interrupt signal to process (Windows)",
                "force_terminate": "Force terminate process",
                "send_interrupt_unix": "Send interrupt signal to process (Unix)",
                "graceful_terminate": "Attempting graceful termination",
                "no_running_process": "No running process",
                "search_line_format": "Line {}: {}",
                "show_search_panel": "Show search panel",
                "hide_search_panel": "Hide search panel"
            },
            "system": {
                "log_tab_name": "System Log",
                "log_title": "WhiteCat Toolbox System Log",
                "log_description": "This tab integrates all system log information",
                "log_includes": "Including tool startup, parameter validation, process management and other operation records",
                "log_realtime": "Real-time display of system running status and error information"
            },
            "system_logs": {
                "system": "[System]",
                "error": "[Error]",
                "success": "[Success]",
                "info": "[Info]",
                "warning": "[Warning]"
            },
            "dialog": {
                "backup_title": "Backup Configuration File",
                "restore_title": "Select Configuration Backup File",
                "zip_files": "ZIP Files (*.zip)",
                "edit_param_title": "Edit Parameter Information",
                "template_manager_title": "Template Manager"
            },
            "backup": {
                "filename": "WhiteCatToolbox_Config_Backup_{}",
                "description": "WhiteCat Toolbox configuration backup file",
                "backup_time": "Backup Time: {}",
                "version": "Version: {}",
                "description_label": "Description: {}",
                "includes": "Includes:",
                "restored_files": "✅ Restored {} files:",
                "backup_files": "💾 Backed up {} original files:",
                "more_files": "... and {} more files",
                "more_backups": "... and {} more backup files"
            },
            "promotion": {
                "title": "WhiteCat Toolbox",
                "promotion_info": "Promotion Information",
                "enable_promotion": "Enable Promotion",
                "disable_promotion": "Disable Promotion",
                "project_recommendation": "Project Recommendation",
                "sponsor": "Sponsor",
                "sponsor_thanks": "💎 Sponsor Thanks",
                "no_promotion": "No promotion content",
                "file_not_exist": "Promotion file does not exist",
                "read_failed": "Read failed: {}",
                "welcome_text": "Welcome to WhiteCat Toolbox!",
                "save_config_failed": "Save promotion config failed: {}",
                "intro_text": """Welcome to WhiteCat Toolbox!

This is a graphical integration platform for CLI tools, designed to solve the problems of high barriers to entry and complex operations for CLI tools.

Main Features:
• Provides graphical configuration for all parameters
• Drag and drop controls for custom parameter ordering
• Support for parameter template saving and management
• Multi-process multi-tool independent operation without interference
• 

Thank you for using!"""
            },
            "terminal": {
                "welcome": "💡 Welcome to WhiteCat Toolbox Terminal!",
                "ansi_support": "💡 Full ANSI escape sequence support: progress bars, color coding, cursor control, etc.",
                "shortcuts": "💡 Shortcuts: Ctrl+C copy | Ctrl+V paste | Ctrl+A select all | Ctrl+L clear screen",
                "process_control": "⚡ Process Control: Right-click menu or click stop button to interrupt process",
                "new_features": "🚀 New Features: Native support for various terminal application display effects"
            },
            "templates": {
                "manager_title": "Template Manager",
                "add_template": "✨ Add Template",
                "import_template": "📥 Import Template",
                "export_template": "📤 Export Template",
                "template_name": "Template Name",
                "template_remark": "Template Remark",
                "operation": "Operation",
                "apply": "Apply",
                "delete": "Delete",
                "edit_name": "Edit Name",
                "edit_remark": "Edit Remark",
                "confirm_delete": "Confirm Delete",
                "delete_confirm_msg": "Are you sure you want to delete template '{}'?",
                "template_applied": "Template Applied",
                "template_deleted": "Template Deleted",
                "export_success": "Template Export Successful",
                "import_success": "Template Import Successful",
                "export_failed": "Export Failed",
                "import_failed": "Import Failed",
                "select_template_file": "Select Template File",
                "save_template_file": "Save Template File",
                "json_files": "JSON Files (*.json)"
            },
            "process": {
                "running": "Running",
                "stopped": "Stopped",
                "finished": "Finished",
                "error": "Error",
                "starting": "Starting",
                "stopping": "Stopping",
                "process_finished": "Process Finished",
                "process_error": "Process Error",
                "process_stopped": "Process Stopped",
                "exit_code": "Exit Code",
                "runtime": "Runtime",
                "clear_output": "Clear Output",
                "stop_process": "Stop Process",
                "search_toggle": "Toggle Search",
                "search_placeholder": "Search content...",
                "prev_match": "Previous",
                "next_match": "Next",
                "match_case": "Match Case",
                "whole_word": "Whole Word",
                "regex_mode": "Regex",
                "found_matches": "Found {} matches",
                "no_matches": "No matches found",
                "process_started": "Process Started",
                "command_executed": "Command Executed"
            },
            "config": {
                "parse_error": "Configuration file parse error: {}",
                "line_parse_warning": "Warning: Error parsing config file line: {}, error: {}",
                "save_failed": "Save configuration failed: {}"
            },
            "utils": {
                "parse_command_error": "Unable to parse run command",
                "scale_saved": "Interface scale setting saved",
                "scale_loaded": "Interface scale setting loaded"
            },
            "errors": {
                "file_not_found": "File not found: {}",
                "permission_denied": "Permission denied: {}",
                "connection_failed": "Connection failed",
                "timeout": "Operation timeout",
                "unknown_error": "Unknown error: {}",
                "invalid_format": "Invalid format",
                "operation_cancelled": "Operation cancelled"
            }
        }
    
    def get_text(self, key: str, *args) -> str:
        
        keys = key.split('.')
        text = self.translations.get(self.current_language, {})
        
        for k in keys:
            if isinstance(text, dict) and k in text:
                text = text[k]
            else:

                fallback_text = self.translations.get("zh_CN", {})
                for k in keys:
                    if isinstance(fallback_text, dict) and k in fallback_text:
                        fallback_text = fallback_text[k]
                    else:
                        return key
                return fallback_text.format(*args) if args else fallback_text
        
        return text.format(*args) if args else text
    
    def set_language(self, language: str):
        
        if language in self.translations:
            self.current_language = language
            self.save_language_preference()
    
    def get_current_language(self) -> str:
        
        return self.current_language
    
    def get_available_languages(self) -> list:
        
        return list(self.translations.keys())
    
    def save_language_preference(self):
        
        try:
            config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "language_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({"language": self.current_language}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def load_language_preference(self):
        
        try:
            config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "language_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_language = config.get("language", "zh_CN")
        except Exception:
            pass
_i18n_manager = I18nManager()

def get_text(key: str, *args) -> str:
    
    return _i18n_manager.get_text(key, *args)

def set_language(language: str):
    
    _i18n_manager.set_language(language)

def get_current_language() -> str:
    
    return _i18n_manager.get_current_language()

def get_available_languages() -> list:
    
    return _i18n_manager.get_available_languages()

def init_i18n():
    
    _i18n_manager.load_language_preference()
    return _i18n_manager
t = get_text