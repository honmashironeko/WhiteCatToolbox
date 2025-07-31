"""
终端性能优化模块
提供终端渲染和ANSI处理的性能优化功能
"""

from PySide6.QtCore import QTimer, QThread, Signal, QMutex, QMutexLocker
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor
import time
from collections import deque
from typing import List, Tuple
import threading

class PerformanceConfig:
    """性能配置类"""
    

    MAX_OUTPUT_LINES = 10000
    BATCH_SIZE = 100
    RENDER_DELAY = 50
    

    ANSI_CACHE_SIZE = 1000
    ENABLE_ANSI_CACHE = True
    

    AUTO_CLEANUP_THRESHOLD = 50000
    CLEANUP_KEEP_LINES = 5000

class OutputBuffer:
    """输出缓冲区"""
    
    def __init__(self, max_size=1000):
        self.buffer = deque(maxlen=max_size)
        self.mutex = QMutex()
        
    def add(self, text, format_info=None):
        """添加文本到缓冲区"""
        with QMutexLocker(self.mutex):
            self.buffer.append((text, format_info, time.time()))
    
    def get_all(self):
        """获取所有缓冲的文本"""
        with QMutexLocker(self.mutex):
            items = list(self.buffer)
            self.buffer.clear()
            return items
    
    def size(self):
        """获取缓冲区大小"""
        with QMutexLocker(self.mutex):
            return len(self.buffer)

class BatchRenderer(QThread):
    """批量渲染器"""
    
    render_batch = Signal(list)
    
    def __init__(self, output_buffer):
        super().__init__()
        self.output_buffer = output_buffer
        self.running = True
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self.process_buffer)
        self.render_timer.moveToThread(self)
        
    def run(self):
        """运行批量渲染器"""
        self.render_timer.start(PerformanceConfig.RENDER_DELAY)
        self.exec()
        
    def process_buffer(self):
        """处理缓冲区"""
        if self.output_buffer.size() > 0:
            items = self.output_buffer.get_all()
            if items:

                for i in range(0, len(items), PerformanceConfig.BATCH_SIZE):
                    batch = items[i:i + PerformanceConfig.BATCH_SIZE]
                    self.render_batch.emit(batch)
    
    def stop(self):
        """停止渲染器"""
        self.running = False
        if self.render_timer.isActive():
            self.render_timer.stop()
        self.quit()
        self.wait()

class ANSICache:
    """ANSI解析缓存"""
    
    def __init__(self, max_size=1000):
        self.cache = {}
        self.access_order = deque(maxlen=max_size)
        self.max_size = max_size
        self.mutex = QMutex()
    
    def get(self, text):
        """获取缓存的解析结果"""
        if not PerformanceConfig.ENABLE_ANSI_CACHE:
            return None
            
        with QMutexLocker(self.mutex):
            if text in self.cache:

                if text in self.access_order:
                    self.access_order.remove(text)
                self.access_order.append(text)
                return self.cache[text]
        return None
    
    def put(self, text, result):
        """缓存解析结果"""
        if not PerformanceConfig.ENABLE_ANSI_CACHE:
            return
            
        with QMutexLocker(self.mutex):

            if len(self.cache) >= self.max_size and text not in self.cache:
                if self.access_order:
                    oldest = self.access_order.popleft()
                    if oldest in self.cache:
                        del self.cache[oldest]
            
            self.cache[text] = result
            if text not in self.access_order:
                self.access_order.append(text)
    
    def clear(self):
        """清空缓存"""
        with QMutexLocker(self.mutex):
            self.cache.clear()
            self.access_order.clear()

class PerformanceOptimizedTextEdit(QTextEdit):
    """性能优化的文本编辑器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_count = 0
        self.last_cleanup_time = time.time()
        

        self.setUndoRedoEnabled(False)
        self.document().setMaximumBlockCount(PerformanceConfig.MAX_OUTPUT_LINES)
    
    def append_optimized(self, text, format=None):
        """优化的文本追加方法"""

        self.line_count += text.count('\n')
        
        if (self.line_count > PerformanceConfig.AUTO_CLEANUP_THRESHOLD and 
            time.time() - self.last_cleanup_time > 60):
            self.cleanup_old_content()
        

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        if format:
            cursor.setCharFormat(format)
        
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    
    def cleanup_old_content(self):
        """清理旧内容"""
        try:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            

            lines_to_delete = self.line_count - PerformanceConfig.CLEANUP_KEEP_LINES
            if lines_to_delete > 0:

                for _ in range(lines_to_delete):
                    cursor.movePosition(QTextCursor.MoveOperation.Down)
                

                cursor.setPosition(0, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                
                self.line_count = PerformanceConfig.CLEANUP_KEEP_LINES
                self.last_cleanup_time = time.time()
                
        except Exception as e:
            print(f"清理旧内容时出错: {e}")

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.render_count = 0
        self.ansi_parse_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
    
    def record_render(self):
        """记录渲染操作"""
        self.render_count += 1
    
    def record_ansi_parse(self):
        """记录ANSI解析操作"""
        self.ansi_parse_count += 1
    
    def record_cache_hit(self):
        """记录缓存命中"""
        self.cache_hit_count += 1
    
    def record_cache_miss(self):
        """记录缓存未命中"""
        self.cache_miss_count += 1
    
    def get_stats(self):
        """获取性能统计"""
        runtime = time.time() - self.start_time
        cache_hit_rate = (self.cache_hit_count / 
                         max(1, self.cache_hit_count + self.cache_miss_count) * 100)
        
        return {
            'runtime': runtime,
            'render_count': self.render_count,
            'ansi_parse_count': self.ansi_parse_count,
            'cache_hit_rate': cache_hit_rate,
            'renders_per_second': self.render_count / max(1, runtime),
            'parses_per_second': self.ansi_parse_count / max(1, runtime)
        }
    
    def print_stats(self):
        """打印性能统计"""
        stats = self.get_stats()
        print("=== 终端性能统计 ===")
        print(f"运行时间: {stats['runtime']:.2f}秒")
        print(f"渲染次数: {stats['render_count']}")
        print(f"ANSI解析次数: {stats['ansi_parse_count']}")
        print(f"缓存命中率: {stats['cache_hit_rate']:.1f}%")
        print(f"渲染速率: {stats['renders_per_second']:.1f}/秒")
        print(f"解析速率: {stats['parses_per_second']:.1f}/秒")


performance_monitor = PerformanceMonitor()

def optimize_terminal_performance():
    """优化终端性能的建议设置"""
    recommendations = [
        "1. 启用ANSI缓存以减少重复解析",
        "2. 设置合适的最大输出行数限制",
        "3. 使用批量渲染减少UI更新频率",
        "4. 定期清理旧的输出内容",
        "5. 禁用不必要的文本编辑功能",
        "6. 使用性能优化的文本控件"
    ]
    
    return recommendations

if __name__ == "__main__":

    print("终端性能优化模块测试")
    

    cache = ANSICache(100)
    test_text = "\x1b[31m红色文本\x1b[0m"
    

    result = cache.get(test_text)
    if result is None:
        print("缓存未命中，进行解析...")
        result = "解析结果"
        cache.put(test_text, result)
    

    result = cache.get(test_text)
    if result is not None:
        print("缓存命中！")
    

    print("\n性能优化建议:")
    for rec in optimize_terminal_performance():
        print(rec)