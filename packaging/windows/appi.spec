# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules, collect_all

root = Path(SPECPATH).resolve().parents[1]
sys.path[:0] = [
    str(root / "apps" / "device-agent"),
    str(root / "apps" / "runtime-core"),
    str(root / "services" / "voice"),
    str(root / "packaging" / "windows"),
]
entry = root / "packaging" / "windows" / "appi_entry.py"
voice_scripts = root / "services" / "voice" / "scripts"

hidden = []
for pkg in ("app", "appi_voice", "appi_runtime_core"):
    hidden.extend(collect_submodules(pkg))

webview_datas, webview_binaries, webview_hidden = [], [], []
try:
    webview_datas, webview_binaries, webview_hidden = collect_all("webview")
except Exception:
    pass

icon_path = root / "apps" / "web" / "public" / "brand" / "appi-logo-200.png"
if not icon_path.is_file():
    icon_path = None

a = Analysis(
    [str(entry)],
    pathex=[
        str(root / "apps" / "device-agent"),
        str(root / "apps" / "runtime-core"),
        str(root / "services" / "voice"),
        str(root / "packaging" / "windows"),
    ],
    binaries=list(webview_binaries),
    datas=[(str(voice_scripts), "scripts")] + list(webview_datas),
    hiddenimports=hidden
    + list(webview_hidden)
    + [
        "app.main",
        "app.launcher",
        "app.desktop.app_window",
        "app.desktop.pair_dialog",
        "appi_voice.assistant",
        "appi_voice.pipeline",
        "appi_voice.windows_sapi",
        "appi_runtime_core.autostart",
        "pystray._win32",
        "playwright",
        "webview",
        "webview.platforms.edgechromium",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Appi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(icon_path) if icon_path else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Appi",
)
