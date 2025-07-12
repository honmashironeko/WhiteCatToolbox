from PySide6.QtCore import QProcess
import re
class ToolProcess(QProcess):
    
    
    def __init__(self, parent=None, process_tab=None):
        super().__init__(parent)
        self.process_tab = process_tab
        self.readyReadStandardOutput.connect(self.handle_stdout)
        self.readyReadStandardError.connect(self.handle_stderr)
        self.finished.connect(self.handle_finished)
    
    def convert_ansi_to_html(self, text):
        ansi_colors = {
            '30': '#000000',
            '31': '#FF0000',
            '32': '#00FF00',
            '33': '#FFFF00',
            '34': '#0000FF',
            '35': '#FF00FF',
            '36': '#00FFFF',
            '37': '#FFFFFF',
            '90': '#808080',
            '91': '#FF6B6B',
            '92': '#4ECDC4',
            '93': '#FFE66D',
            '94': '#4D96FF',
            '95': '#FF6BCB',
            '96': '#4ECDC4',
            '97': '#FFFFFF',
        }
        
        ansi_bg_colors = {
            '40': '#000000',
            '41': '#FF0000',
            '42': '#00FF00',
            '43': '#FFFF00',
            '44': '#0000FF',
            '45': '#FF00FF',
            '46': '#00FFFF',
            '47': '#FFFFFF',
        }
        result = text
        result = re.sub(r'\x1b\[0m', '</span>', result)
        result = re.sub(r'\x1b\[m', '</span>', result)
        result = re.sub(r'\x1b\[1m', '<span style="font-weight: bold;">', result)
        for code, color in ansi_colors.items():
            pattern = r'\x1b\[' + code + r'm'
            replacement = f'<span style="color: {color};">'
            result = re.sub(pattern, replacement, result)
        for code, color in ansi_bg_colors.items():
            pattern = r'\x1b\[' + code + r'm'
            replacement = f'<span style="background-color: {color};">'
            result = re.sub(pattern, replacement, result)
        def replace_combined(match):
            codes = match.group(1).split(';')
            styles = []
            for code in codes:
                if code == '1':
                    styles.append('font-weight: bold')
                elif code in ansi_colors:
                    styles.append(f'color: {ansi_colors[code]}')
                elif code in ansi_bg_colors:
                    styles.append(f'background-color: {ansi_bg_colors[code]}')
            return f'<span style="{"; ".join(styles)};">' if styles else ''
        
        result = re.sub(r'\x1b\[([0-9;]+)m', replace_combined, result)
        result = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', result)
        
        return result
    
    def handle_stdout(self):
        
        data = self.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8", errors="ignore")
        if self.process_tab and hasattr(self.process_tab, 'append_output'):

            html_output = self.convert_ansi_to_html(stdout)
            self.process_tab.append_output_html(html_output)
    
    def handle_stderr(self):
        
        data = self.readAllStandardError()
        stderr = bytes(data).decode("utf-8", errors="ignore")
        if self.process_tab and hasattr(self.process_tab, 'append_output'):

            html_output = self.convert_ansi_to_html(stderr)
            self.process_tab.append_output_html(f"<span style='color: #FF6B6B;'>[ERROR]</span> {html_output}")
    
    def handle_finished(self, exit_code, exit_status):
        
        pass 