# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

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

a = Analysis(
    [str(entry)],
    pathex=[
        str(root / "apps" / "device-agent"),
        str(root / "apps" / "runtime-core"),
        str(root / "services" / "voice"),
        str(root / "packaging" / "windows"),
    ],
    binaries=[],
    datas=[(str(voice_scripts), "scripts")],
    hiddenimports=hidden + [
        "app.main",
        "appi_voice.assistant",
        "appi_voice.pipeline",
        "appi_voice.windows_sapi",
        "appi_runtime_core.autostart",
        "pystray._win32",
        "playwright",
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
    console=True,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Appi",
)
