"""
ANSI转义序列解析器模块
支持完整的ANSI颜色和文本格式化功能
"""

import re
from typing import List, Tuple, Dict, Optional
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QTextCursor
from PySide6.QtCore import Qt

class ANSIColor:
    """ANSI颜色定义"""
    

    COLORS_16 = {
        0: "#000000",
        1: "#800000",
        2: "#008000",
        3: "#808000",
        4: "#000080",
        5: "#800080",
        6: "#008080",
        7: "#c0c0c0",
        8: "#808080",
        9: "#ff0000",
        10: "#00ff00",
        11: "#ffff00",
        12: "#0000ff",
        13: "#ff00ff",
        14: "#00ffff",
        15: "#ffffff",
    }
    

    @staticmethod
    def get_256_color(index: int) -> str:
        """获取256色调色板中的颜色"""
        if index < 16:
            return ANSIColor.COLORS_16.get(index, "#ffffff")
        elif index < 232:

            index -= 16
            r = (index // 36) * 51
            g = ((index % 36) // 6) * 51
            b = (index % 6) * 51
            return f"#{r:02x}{g:02x}{b:02x}"
        else:

            gray = 8 + (index - 232) * 10
            return f"#{gray:02x}{gray:02x}{gray:02x}"
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """RGB转十六进制颜色"""
        return f"#{r:02x}{g:02x}{b:02x}"

class ANSITextFormat:
    """ANSI文本格式定义"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置所有格式"""
        self.bold = False
        self.dim = False
        self.italic = False
        self.underline = False
        self.strikethrough = False
        self.blink = False
        self.reverse = False
        self.hidden = False
        self.foreground_color = None
        self.background_color = None
    
    def copy(self):
        """复制当前格式"""
        new_format = ANSITextFormat()
        new_format.bold = self.bold
        new_format.dim = self.dim
        new_format.italic = self.italic
        new_format.underline = self.underline
        new_format.strikethrough = self.strikethrough
        new_format.blink = self.blink
        new_format.reverse = self.reverse
        new_format.hidden = self.hidden
        new_format.foreground_color = self.foreground_color
        new_format.background_color = self.background_color
        return new_format
    
    def to_qt_format(self) -> QTextCharFormat:
        """转换为Qt文本格式"""
        format = QTextCharFormat()
        

        if self.bold:
            format.setFontWeight(QFont.Bold)
        if self.italic:
            format.setFontItalic(True)
        if self.underline:
            format.setFontUnderline(True)
        if self.strikethrough:
            format.setFontStrikeOut(True)
        

        if self.foreground_color:
            format.setForeground(QColor(self.foreground_color))
        if self.background_color:
            format.setBackground(QColor(self.background_color))
            

        if self.reverse and self.foreground_color and self.background_color:
            format.setForeground(QColor(self.background_color))
            format.setBackground(QColor(self.foreground_color))
        
        return format

class ANSIParser:
    """ANSI转义序列解析器"""
    


    ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    ANSI_CSI_RE = re.compile(r'\x1b\[([0-9;?]*)([A-Za-z@-~])')

    ANSI_OSC_RE = re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)')

    ANSI_ALL_RE = re.compile(r'(?:'
                            r'\x1b\[[0-?]*[ -/]*[@-~]|'
                            r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|'
                            r'\x1b[@-Z\\-_]'
                            r')')
    
    def __init__(self):
        self.current_format = ANSITextFormat()
        self.default_foreground = "#ffffff"
        self.default_background = "#000000"
    
    def parse_text(self, text: str) -> List[Tuple[str, QTextCharFormat]]:
        """
        解析包含ANSI转义序列的文本
        返回: [(文本片段, Qt格式), ...]
        """
        result = []
        last_end = 0
        

        text = self.ANSI_OSC_RE.sub('', text)
        

        for match in self.ANSI_CSI_RE.finditer(text):

            if match.start() > last_end:
                plain_text = text[last_end:match.start()]
                if plain_text:
                    result.append((plain_text, self.current_format.to_qt_format()))
            

            params = match.group(1)
            command = match.group(2)
            
            if command == 'm':
                self._process_sgr_sequence(params)
            elif command == 'K':
                pass
            elif command in 'ABCD':
                pass
            elif command in 'HfJ':
                pass
            elif command in 'hlST':
                pass
            
            last_end = match.end()
        

        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text:
                result.append((remaining_text, self.current_format.to_qt_format()))
        
        return result
    
    def _process_sgr_sequence(self, params: str):
        """处理SGR (Select Graphic Rendition) 序列"""
        if not params:
            params = "0"
        
        codes = []
        for x in params.split(';'):
            try:
                codes.append(int(x) if x else 0)
            except ValueError:

                continue
        
        i = 0
        
        while i < len(codes):
            code = codes[i]
            
            if code == 0:
                self.current_format.reset()
                self.current_format.foreground_color = self.default_foreground
                self.current_format.background_color = None
            elif code == 1:
                self.current_format.bold = True
            elif code == 2:
                self.current_format.dim = True
            elif code == 3:
                self.current_format.italic = True
            elif code == 4:
                self.current_format.underline = True
            elif code == 5:
                self.current_format.blink = True
            elif code == 7:
                self.current_format.reverse = True
            elif code == 8:
                self.current_format.hidden = True
            elif code == 9:
                self.current_format.strikethrough = True
            elif code == 22:
                self.current_format.bold = False
                self.current_format.dim = False
            elif code == 23:
                self.current_format.italic = False
            elif code == 24:
                self.current_format.underline = False
            elif code == 25:
                self.current_format.blink = False
            elif code == 27:
                self.current_format.reverse = False
            elif code == 28:
                self.current_format.hidden = False
            elif code == 29:
                self.current_format.strikethrough = False
            elif 30 <= code <= 37:
                color_index = code - 30
                self.current_format.foreground_color = ANSIColor.COLORS_16[color_index]
            elif code == 38:
                i = self._process_extended_color(codes, i, True)
                continue
            elif code == 39:
                self.current_format.foreground_color = self.default_foreground
            elif 40 <= code <= 47:
                color_index = code - 40
                self.current_format.background_color = ANSIColor.COLORS_16[color_index]
            elif code == 48:
                i = self._process_extended_color(codes, i, False)
                continue
            elif code == 49:
                self.current_format.background_color = None
            elif 90 <= code <= 97:
                color_index = code - 90 + 8
                self.current_format.foreground_color = ANSIColor.COLORS_16[color_index]
            elif 100 <= code <= 107:
                color_index = code - 100 + 8
                self.current_format.background_color = ANSIColor.COLORS_16[color_index]

            
            i += 1
    
    def _process_extended_color(self, codes: List[int], index: int, is_foreground: bool) -> int:
        """处理扩展颜色序列 (38;5;n 或 38;2;r;g;b)"""
        if index + 1 >= len(codes):
            return index
        
        color_type = codes[index + 1]
        
        if color_type == 5:
            if index + 2 < len(codes):
                color_index = codes[index + 2]
                color = ANSIColor.get_256_color(color_index)
                if is_foreground:
                    self.current_format.foreground_color = color
                else:
                    self.current_format.background_color = color
                return index + 2
        elif color_type == 2:
            if index + 4 < len(codes):
                r, g, b = codes[index + 2], codes[index + 3], codes[index + 4]
                color = ANSIColor.rgb_to_hex(r, g, b)
                if is_foreground:
                    self.current_format.foreground_color = color
                else:
                    self.current_format.background_color = color
                return index + 4
        
        return index + 1
    
    def strip_ansi(self, text: str) -> str:
        """移除文本中的ANSI转义序列"""
        return self.ANSI_ALL_RE.sub('', text)
    
    def reset_format(self):
        """重置格式状态"""
        self.current_format.reset()
        self.current_format.foreground_color = self.default_foreground
    
    def set_default_colors(self, foreground: str, background: str):
        """设置默认颜色"""
        self.default_foreground = foreground
        self.default_background = background

class ANSITextRenderer:
    """ANSI文本渲染器"""
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.parser = ANSIParser()
        

        try:
            from .terminal_performance import ANSICache, performance_monitor
            self.cache = ANSICache()
            self.performance_monitor = performance_monitor
            self.cache_enabled = True
        except ImportError:
            self.cache = None
            self.performance_monitor = None
            self.cache_enabled = False
        
    def append_ansi_text(self, text: str):
        """追加ANSI格式的文本到文本控件"""
        if not text:
            return
        
        try:

            if self.performance_monitor:
                self.performance_monitor.record_render()
                

            segments = None
            if self.cache_enabled and self.cache:
                segments = self.cache.get(text)
                if segments:
                    if self.performance_monitor:
                        self.performance_monitor.record_cache_hit()
                else:
                    if self.performance_monitor:
                        self.performance_monitor.record_cache_miss()
                        self.performance_monitor.record_ansi_parse()
            

            if segments is None:
                segments = self.parser.parse_text(text)

                if self.cache_enabled and self.cache:
                    self.cache.put(text, segments)
            

            cursor = self.text_widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            

            for text_segment, format in segments:
                if text_segment:
                    cursor.setCharFormat(format)
                    cursor.insertText(text_segment)
            

            self.text_widget.setTextCursor(cursor)
            self.text_widget.ensureCursorVisible()
            
        except Exception as e:


            clean_text = self.parser.strip_ansi(text)
            cursor = self.text_widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(clean_text)
            self.text_widget.setTextCursor(cursor)
            self.text_widget.ensureCursorVisible()
    
    def set_default_colors(self, foreground: str, background: str):
        """设置默认颜色"""
        self.parser.set_default_colors(foreground, background)
    
    def clear_and_reset(self):
        """清空文本并重置格式"""
        self.text_widget.clear()
        self.parser.reset_format()


def test_ansi_parser():
    """测试ANSI解析器功能"""
    parser = ANSIParser()
    
    test_cases = [

        "\x1b[31m红色文本\x1b[0m",
        "\x1b[1;32m粗体绿色\x1b[0m", 
        "\x1b[4;34m下划线蓝色\x1b[0m",
        

        "\x1b[38;5;196m256色红色\x1b[0m",
        "\x1b[38;5;46m256色绿色\x1b[0m",
        

        "\x1b[38;2;255;165;0mRGB橙色\x1b[0m",
        "\x1b[38;2;128;0;128mRGB紫色\x1b[0m",
        

        "\x1b[41;37m红色背景白色文字\x1b[0m",
        "\x1b[48;5;21;38;5;15m256色背景\x1b[0m",
        

        "\x1b[1;3;4;31m粗体斜体下划线红色\x1b[0m",
        

        "\x1b[2J\x1b[H清屏和光标定位\x1b[0m",
        "\x1b[10A\x1b[5C光标移动\x1b[0m",
        

        "正常文本\x1b[31m红色\x1b[1m粗体红色\x1b[32m粗体绿色\x1b[0m重置",
        

        "\x1b[999m无效颜色代码\x1b[0m",
        "\x1b[38;5;300m无效256色\x1b[0m",
        

        "\x1b]0;终端标题\x07普通文本",
        "\x1b]0;C:\\Python313\\python.EXE\x07命令输出",
        "\x1b]0;窗口标题\x1b\\后续文本",
        

        "\x1b]0;标题\x07\x1b[31m红色文本\x1b[0m",
    ]
    
    print("ANSI解析器测试开始:")
    print("=" * 60)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {repr(test_text)}")
        
        try:

            segments = parser.parse_text(test_text)
            print(f"解析结果: {len(segments)} 个片段")
            
            for j, (text, format) in enumerate(segments):
                if text.strip():
                    print(f"  片段 {j+1}: {repr(text)} -> 格式已应用")
            

            clean_text = parser.strip_ansi(test_text)
            print(f"清理后文本: {repr(clean_text)}")
            
        except Exception as e:
            print(f"解析错误: {e}")
        
        print("-" * 40)
    
    print(f"\n测试完成。解析器状态:")
    print(f"当前前景色: {parser.current_format.foreground_color}")
    print(f"当前背景色: {parser.current_format.background_color}")
    print(f"粗体: {parser.current_format.bold}")
    print(f"斜体: {parser.current_format.italic}")

if __name__ == "__main__":
    test_ansi_parser()