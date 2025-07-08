from PySide6.QtCore import QProcess
class ToolProcess(QProcess):
    def __init__(self, parent=None, process_tab=None):
        super().__init__(parent)
        self.process_tab = process_tab
        self.readyReadStandardOutput.connect(self.handle_stdout)
        self.readyReadStandardError.connect(self.handle_stderr)
        self.finished.connect(self.handle_finished)
    
    def handle_stdout(self):
        
        data = self.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8", errors="ignore")
        if self.process_tab and hasattr(self.process_tab, 'append_output'):
            self.process_tab.append_output(stdout)
    
    def handle_stderr(self):
        
        data = self.readAllStandardError()
        stderr = bytes(data).decode("utf-8", errors="ignore")
        if self.process_tab and hasattr(self.process_tab, 'append_output'):
            self.process_tab.append_output(f"[ERROR] {stderr}")
    
    def handle_finished(self, exit_code, exit_status):
        
        if hasattr(self.parent(), 'process_finished'):
            self.parent().process_finished(self, exit_code, exit_status) 