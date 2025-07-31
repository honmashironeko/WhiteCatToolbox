import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

def setup_environment():
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

def main():
    setup_environment()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application icon
    favicon_path = Path(__file__).parent / "favicon.ico"
    if favicon_path.exists():
        app.setWindowIcon(QIcon(str(favicon_path)))
    
    from wct_modules.main_window import MainWindow
    from wct_modules.config import ConfigManager
    from wct_modules.font_scale_widget import GlobalFontScaleManager
    

    config_manager = ConfigManager()
    

    font_scale_manager = GlobalFontScaleManager(config_manager)
    font_scale_manager.initialize()
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()