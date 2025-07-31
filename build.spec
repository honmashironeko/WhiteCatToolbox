# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# 获取项目根目录
project_root = Path('.')

# 数据文件列表
datas = [
    # 配置文件
    ('config', 'config'),
    # 图标文件
    ('favicon.ico', '.'),
    # 主题文件
    ('assets', 'assets'),
    # 工具目录
    ('tools', 'tools'),
    # 推广文件
    ('promotion', 'promotion'),
]

# 隐藏导入
hiddenimports = [
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'configparser',
    'psutil',
    'watchdog',
    'colorama',
    'pywinpty',
    'Pillow',
]

# 二进制文件
binaries = []

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WhiteCatToolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhiteCatToolbox'
)