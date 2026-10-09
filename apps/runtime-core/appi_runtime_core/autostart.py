"""Install or remove a user-login autostart entry. Windows Startup folder only."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def startup_dir() -> Path | None:
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "LaunchAgents"
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "autostart"


def _pythonw() -> Path:
    exe = Path(sys.executable)
    cand = exe.with_name("pythonw.exe")
    return cand if cand.exists() else exe


def windows_startup_script(repo_root: Path) -> str:
    if getattr(sys, "frozen", False):
        exe = sys.executable
        return f'@echo off\r\nstart "" "{exe}" serve\r\n'
    pythonw = _pythonw()
    agent = repo_root / "apps" / "device-agent"
    return (
        f'@echo off\r\n'
        f'cd /d "{agent}"\r\n'
        f'start "" "{pythonw}" -m app.launcher\r\n'
    )


def windows_startup_vbs(repo_root: Path) -> str:
    def q(value: Path | str) -> str:
        return str(value).replace('"', '""')

    if getattr(sys, "frozen", False):
        run = f'sh.Run """{q(sys.executable)}"" serve", 0, False'
        cwd = ""
    else:
        run = f'sh.Run """{q(_pythonw())}"" -m app.launcher", 0, False'
        cwd = f'sh.CurrentDirectory = "{q(repo_root / "apps" / "device-agent")}"\r\n'
    return (
        "Option Explicit\r\n"
        "Dim sh\r\n"
        'Set sh = CreateObject("WScript.Shell")\r\n'
        f"{cwd}{run}\r\n"
    )


def enable_autostart(repo_root: Path) -> Path:
    folder = startup_dir()
    if folder is None:
        raise RuntimeError("Cannot locate autostart directory")
    folder.mkdir(parents=True, exist_ok=True)
    if sys.platform.startswith("win"):
        path = folder / "AppiRuntime.vbs"
        path.write_text(windows_startup_vbs(repo_root), encoding="utf-16")
        old = folder / "AppiRuntime.bat"
        if old.exists():
            old.unlink()
        return path
    if sys.platform == "darwin":
        path = folder / "dev.appi.runtime.plist"
        python = sys.executable
        agent = repo_root / "apps" / "device-agent"
        path.write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>dev.appi.runtime</string>
  <key>ProgramArguments</key><array>
    <string>{python}</string><string>-m</string><string>app.main</string><string>serve</string>
  </array>
  <key>WorkingDirectory</key><string>{agent}</string>
  <key>RunAtLoad</key><true/>
</dict></plist>
""",
            encoding="utf-8",
        )
        return path
    path = folder / "appi-runtime.desktop"
    python = sys.executable
    agent = repo_root / "apps" / "device-agent"
    path.write_text(
        f"""[Desktop Entry]
Type=Application
Name=Appi Runtime
Exec={python} -m app.main serve
Path={agent}
X-GNOME-Autostart-enabled=true
""",
        encoding="utf-8",
    )
    return path


def disable_autostart() -> None:
    folder = startup_dir()
    if folder is None:
        return
    for name in ("AppiRuntime.bat", "AppiRuntime.vbs", "Appi.lnk", "dev.appi.runtime.plist", "appi-runtime.desktop"):
        path = folder / name
        if path.exists():
            path.unlink()
