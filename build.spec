# -*- mode: python ; coding: utf-8 -*-
"""
==================================================================
 PYINSTALLER SPEC FILE
==================================================================
Builds a single-file Windows executable for the Private School
Management System.

Build command:
    pyinstaller --noconfirm build.spec

Notes:
- CustomTkinter ships its own theme JSON files and assets that
  must be bundled via collect_data_files, otherwise the UI will
  crash at runtime with "file not found" errors for the theme.
- The application's own runtime folders (database, exports,
  backups, sample_data, assets) are bundled alongside the exe so
  the app works out-of-the-box on first launch.
==================================================================
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ------------------------------------------------------------
# Collect package data (themes, assets) for libraries that need it
# ------------------------------------------------------------
datas = []
datas += collect_data_files("customtkinter")
datas += collect_data_files("reportlab")

# ------------------------------------------------------------
# Bundle application runtime folders
#
# Only add folders that actually exist and contain at least one
# file at build time (PyInstaller's Analysis.datas entry requires
# the source path to exist). Missing folders are created empty
# so the build never fails because of an absent/empty directory.
# ------------------------------------------------------------
import os as _os_check

app_datas = [
    ("database", "database"),
    ("exports", "exports"),
    ("backups", "backups"),
    ("sample_data", "sample_data"),
    ("assets", "assets"),
]

for src, dest in app_datas:
    if not _os_check.path.isdir(src):
        _os_check.makedirs(src, exist_ok=True)

    # Ensure the folder is non-empty (PyInstaller can choke on
    # truly empty directories when copying as a tree). Add a
    # placeholder file if needed.
    if not _os_check.listdir(src):
        placeholder = _os_check.path.join(src, ".gitkeep")
        with open(placeholder, "w") as f:
            f.write("")

    datas.append((src, dest))

# ------------------------------------------------------------
# Hidden imports (modules not auto-detected by PyInstaller)
# ------------------------------------------------------------
hiddenimports = []
hiddenimports += collect_submodules("matplotlib")
hiddenimports += collect_submodules("reportlab")
hiddenimports += [
    "PIL._tkinter_finder",
    "pandas._libs.tslibs.base",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

import os as _os

_icon_path = _os.path.join("assets", "icons", "app_icon.ico")
APP_ICON = _icon_path if _os.path.exists(_icon_path) else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SGS_School_Manager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=APP_ICON,
)
