# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for EZ Key Remapper.
Bundles the app with the Interception driver installer.
"""

import os
import sys

block_cipher = None

# Get the project directory
project_dir = os.path.dirname(os.path.abspath(SPEC))

# Data files to include
datas = []

# Add the driver folder if it exists (downloaded by setup)
driver_dir = os.path.join(project_dir, 'interception_driver')
if os.path.exists(driver_dir):
    datas.append((driver_dir, 'driver'))

# Add interception.dll if it exists
dll_path = os.path.join(project_dir, 'interception.dll')
if os.path.exists(dll_path):
    datas.append((dll_path, '.'))

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='EZ Key Remapper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
    uac_admin=False,  # Don't require admin by default
)
