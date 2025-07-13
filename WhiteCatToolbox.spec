# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Get target architecture from environment variable or command line
target_arch = os.environ.get('TARGET_ARCH', None)
if '--target-arch' in sys.argv:
    idx = sys.argv.index('--target-arch')
    if idx + 1 < len(sys.argv):
        target_arch = sys.argv[idx + 1]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('favicon.ico', '.'),
        ('wct_modules', 'wct_modules'),
        ('sitecustomize.py', '.'),
        ('config', 'config'),
        ('promotion', 'promotion'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'sitecustomize',
        # Core Python modules that might be missing
        'bz2',
        'ssl',
        'hashlib',
        'uuid',
        'socket',
        'select',
        'threading',
        '_ssl',
        '_hashlib',
        '_bz2',
        '_socket',
        '_thread',
        'zlib',
        '_zlib',
        'lzma',
        '_lzma',
        'sqlite3',
        '_sqlite3',
        'decimal',
        '_decimal',
        'json',
        '_json',
        'urllib',
        'urllib.request',
        'urllib.parse',
        'http',
        'http.client',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_isolate_python.py'],
    excludes=[
        'setuptools',
        'pip',
        'wheel',
        'pytest',
        'numpy',
        'pandas',
        'matplotlib',
        'scipy',
        'sklearn',
        'tensorflow',
        'torch',
        'jupyter',
        'ipython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhiteCatToolbox',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico',
)