#!/usr/bin/env python3


import json
import os
from typing import Dict, List, Any
from pathlib import Path

class CategoryManager:
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir) if config_dir else Path(os.path.dirname(__file__)).parent / 'config'
        self.categories_file = self.config_dir / 'categories.json'
        self.custom_categories = {}
        self.tool_category_mapping = {}
        self.load_categories()
        
    def load_categories(self):
        """加载自定义分类配置"""
        if self.categories_file.exists():
            try:
                with open(self.categories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.custom_categories = data.get('custom_categories', {})
                    self.tool_category_mapping = data.get('tool_category_mapping', {})
            except Exception as e:
                print(f"加载分类配置失败: {e}")
                self.custom_categories = {}
                self.tool_category_mapping = {}
        else:

            self.create_default_categories()
            
    def save_categories(self):
        """保存分类配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            data = {
                'custom_categories': self.custom_categories,
                'tool_category_mapping': self.tool_category_mapping
            }
            with open(self.categories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存分类配置失败: {e}")
            
    def create_default_categories(self):
        """创建默认分类"""
        self.custom_categories = {
            '未分类': {
                'display_name': '未分类',
                'description': '未归类的工具',
                'icon': '📦'
            }
        }
        self.save_categories()
        
    def add_category(self, display_name: str, description: str = '', icon: str = '📁'):
        """添加新分类"""

        category_id = display_name
        self.custom_categories[category_id] = {
            'display_name': display_name,
            'description': description,
            'icon': icon
        }
        self.save_categories()
        
    def remove_category(self, category_id: str):
        """删除分类"""
        if category_id in self.custom_categories:
            del self.custom_categories[category_id]
            

            tools_to_remove = [tool for tool, cat in self.tool_category_mapping.items() if cat == category_id]
            for tool in tools_to_remove:
                del self.tool_category_mapping[tool]
                
            self.save_categories()
            
    def update_category(self, category_id: str, **kwargs):
        """更新分类信息"""
        if category_id in self.custom_categories:
            self.custom_categories[category_id].update(kwargs)
            self.save_categories()
            
    def set_tool_category(self, tool_name: str, category_id: str):
        """设置工具的分类"""
        if category_id in self.custom_categories:
            self.tool_category_mapping[tool_name] = category_id
            self.save_categories()
            
    def get_tool_category(self, tool_name: str, default_category: str = '未分类'):
        """获取工具的分类"""
        mapped_category = self.tool_category_mapping.get(tool_name)
        if mapped_category:
            return mapped_category
        return default_category
        
    def get_all_categories(self) -> Dict[str, Dict]:
        """获取所有分类"""
        return self.custom_categories.copy()
        
    def get_category_info(self, category_id: str) -> Dict:
        """获取分类信息"""
        return self.custom_categories.get(category_id, {})
        
    def get_tools_in_category(self, category_id: str) -> List[str]:
        """获取指定分类下的工具"""
        return [tool for tool, cat in self.tool_category_mapping.items() if cat == category_id]
        
    def get_category_display_name(self, category_id: str) -> str:
        """获取分类显示名称"""
        category_info = self.custom_categories.get(category_id, {})
        return category_info.get('display_name', category_id)
        
    def export_categories(self, file_path: str):
        """导出分类配置"""
        try:
            data = {
                'custom_categories': self.custom_categories,
                'tool_category_mapping': self.tool_category_mapping
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出分类配置失败: {e}")
            return False
            
    def import_categories(self, file_path: str):
        """导入分类配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.custom_categories.update(data.get('custom_categories', {}))
                self.tool_category_mapping.update(data.get('tool_category_mapping', {}))
                self.save_categories()
            return True
        except Exception as e:
            print(f"导入分类配置失败: {e}")
            return False