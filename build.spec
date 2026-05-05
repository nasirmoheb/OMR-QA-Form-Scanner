# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for OMR QA Form Scanner
# Run with:  pyinstaller build.spec
#
# Produces:  dist/OMR_Scanner/  (folder mode, then Inno Setup wraps it)

import sys
from pathlib import Path
import customtkinter

block_cipher = None

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT      = Path(SPECPATH)          # project root
SRC       = ROOT / "src"
ASSETS    = ROOT / "assets"
DATA_DIR  = ROOT / "data"

# CustomTkinter ships its own theme JSON files — they must travel with the exe
CTK_PATH  = Path(customtkinter.__file__).parent

# ---------------------------------------------------------------------------
# Hidden imports
# (packages whose sub-modules PyInstaller misses via static analysis)
# ---------------------------------------------------------------------------
hidden = [
    # CustomTkinter internals
    "customtkinter",
    "customtkinter.windows",
    "customtkinter.windows.widgets",
    "customtkinter.windows.widgets.appearance_mode",
    "customtkinter.windows.widgets.scaling",
    "customtkinter.windows.widgets.theme",
    # PIL / Pillow
    "PIL._tkinter_finder",
    "PIL.Image",
    "PIL.ImageTk",
    # OpenCV
    "cv2",
    # Data / analytics
    "pandas",
    "numpy",
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
    # PDF
    "reportlab",
    "reportlab.graphics",
    "reportlab.lib",
    "reportlab.pdfbase",
    "reportlab.pdfbase.ttfonts",
    "reportlab.pdfgen",
    "pikepdf",
    # QR code
    "qrcode",
    "qrcode.image.pil",
    # RTL text
    "arabic_reshaper",
    "bidi",
    "bidi.algorithm",
    # SQLite / SQLAlchemy
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    # Standard library extras
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "webbrowser",
    "threading",
    "json",
    "sqlite3",
]

# ---------------------------------------------------------------------------
# Data files to bundle
# (source, destination-inside-bundle)
# ---------------------------------------------------------------------------
datas = [
    # CustomTkinter themes and assets
    (str(CTK_PATH), "customtkinter"),
    # App assets (survey template PDF, report HTML)
    (str(ASSETS), "assets"),
    # Pre-create the data directory so SQLite can write there
    (str(DATA_DIR), "data"),
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "hypothesis",
        "matplotlib",
        "scipy",
        "IPython",
        "notebook",
        "jupyter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---------------------------------------------------------------------------
# EXE
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OMR_Scanner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico",   # uncomment once you have an .ico file
)

# ---------------------------------------------------------------------------
# COLLECT  (folder-mode distribution)
# ---------------------------------------------------------------------------
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OMR_Scanner",
)
