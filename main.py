#!/usr/bin/env python3
if __name__ == "__main__":
    import sys
    import os
    from wct_modules import utils
    utils.load_scale_factor()
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon

    _workspace_root = os.path.abspath(os.path.dirname(__file__))
    _existing_pythonpath = os.environ.get("PYTHONPATH", "")
    if _workspace_root not in _existing_pythonpath.split(os.pathsep):
        os.environ["PYTHONPATH"] = (
            _workspace_root + (os.pathsep + _existing_pythonpath if _existing_pythonpath else "")
        )
    try:
        import importlib
        importlib.import_module("sitecustomize")
    except Exception:
        pass
    
    try:
        from wct_modules.isatty_fix import apply_isatty_fix
        apply_isatty_fix()
    except Exception:
        pass

    from wct_modules.styles import get_cross_platform_app_stylesheet
    from wct_modules.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet(get_cross_platform_app_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec()) 