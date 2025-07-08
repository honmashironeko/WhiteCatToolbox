import os
from .i18n import t

class ToolConfigParser:
    @staticmethod
    def parse_config(config_path):
        config = {
            '常用参数': {
                '勾选项区': [],
                '输入框区': []
            },
            '全部参数': {
                '勾选项区': [],
                '输入框区': []
            }
        }
        
        if not os.path.exists(config_path):
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_section = None
            current_subsection = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('%') and not line.startswith('%%'):
                    section_name = line[1:]
                    if section_name in ['常用参数', 'Common Parameters']:
                        current_section = '常用参数'
                    elif section_name in ['全部参数', 'All Parameters']:
                        current_section = '全部参数'
                    else:
                        current_section = section_name
                elif line.startswith('%%'):
                    subsection_name = line[2:]
                    if subsection_name in ['勾选项', 'CheckBoxes']:
                        current_subsection = '勾选项区'
                    elif subsection_name in ['输入项', 'Inputs']:
                        current_subsection = '输入框区'
                    else:
                        current_subsection = None
                elif '=' in line and current_section and current_subsection:
                    try:
                        parts = line.split('=')
                        if len(parts) >= 3:
                            param_name = parts[0].strip()
                            display_name = parts[1].strip()
                            last_part = parts[-1].strip()
                            if last_part in ['0', '1'] and len(parts) >= 4:
                                required = last_part
                                description = '='.join(parts[2:-1]).strip()
                            else:
                                description = '='.join(parts[2:]).strip()
                                required = '0'
                            if current_subsection == '勾选项区':
                                param_type = '1'
                            elif current_subsection == '输入框区':
                                param_type = '2'
                            else:
                                continue
                            param_info = {
                                'param_name': param_name,
                                'display_name': display_name,
                                'description': description,
                                'type': param_type,
                                'required': required == '1',
                                'default': '',
                                'help': description
                            }
                            if current_section in config and current_subsection in config[current_section]:
                                config[current_section][current_subsection].append(param_info)
                    except Exception as e:
                        print(t("config.line_parse_warning", line.strip(), e))
                        continue
        except Exception as e:
            print(t("config.parse_error", e))
        
        return config