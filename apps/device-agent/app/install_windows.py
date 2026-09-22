"""Per-user Windows install. Does not need Administrator."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def install_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "Programs" / "Appi"


def start_menu_dir() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def data_dir() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    path = Path(appdata) / "Appi"
    path.mkdir(parents=True, exist_ok=True)
    return path


def desktop_dir() -> Path:
    if sys.platform.startswith("win"):
        try:
            import ctypes

            buf = ctypes.create_unicode_buffer(260)
            ctypes.windll.shell32.SHGetFolderPathW(None, 0, None, 0, buf)
            if buf.value:
                return Path(buf.value)
        except Exception:
            pass
        profile = os.environ.get("USERPROFILE")
        if profile:
            return Path(profile) / "Desktop"
    return Path.home() / "Desktop"


def pythonw_path() -> Path:
    exe = Path(sys.executable)
    cand = exe.with_name("pythonw.exe")
    return cand if cand.exists() else exe


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def running_as_admin() -> bool:
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def frozen_source_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return None


def is_installed_copy() -> bool:
    src = frozen_source_dir()
    return bool(src and src == install_dir())


def _ps_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def write_hidden_start_script() -> Path:
    """VBScript that starts Appi with no Command Prompt."""
    pyw = pythonw_path()
    agent = repo_root() / "apps" / "device-agent"
    script = data_dir() / "Start.vbs"
    agent_s = str(agent).replace('"', '""')
    pyw_s = str(pyw).replace('"', '""')
    script.write_text(
        "Option Explicit\r\n"
        "Dim sh\r\n"
        'Set sh = CreateObject("WScript.Shell")\r\n'
        f'sh.CurrentDirectory = "{agent_s}"\r\n'
        f'sh.Run """{pyw_s}"" -m app.launcher", 0, False\r\n',
        encoding="utf-16",
    )
    return script


def _create_shortcut(target: Path, *, shortcut: Path, arguments: str = "", workdir: Path | None = None) -> Path:
    shortcut.parent.mkdir(parents=True, exist_ok=True)
    work = str(workdir or target.parent)
    cmd = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut({_ps_quote(str(shortcut))}); "
        f"$s.TargetPath = {_ps_quote(str(target))}; "
        f"$s.Arguments = {_ps_quote(arguments)}; "
        f"$s.WorkingDirectory = {_ps_quote(work)}; "
        "$s.WindowStyle = 1; "
        "$s.Description = 'Appi'; "
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return shortcut


def create_app_shortcuts() -> dict[str, str]:
    """Start Menu + Desktop shortcuts that start Appi with no CMD window."""
    starter = write_hidden_start_script()
    menu = _create_shortcut(starter, shortcut=start_menu_dir() / "Appi.lnk")
    desk = _create_shortcut(starter, shortcut=desktop_dir() / "Appi.lnk")
    return {
        "start_menu": str(menu),
        "desktop": str(desk),
        "starter": str(starter),
        "launcher": str(pythonw_path()),
    }


def install(*, enable_login_start: bool = True) -> dict[str, str]:
    """Copy this Appi folder into the current user's profile. No Administrator needed."""
    dest = install_dir()
    src = frozen_source_dir()
    if src is None:
        from appi_runtime_core.autostart import enable_autostart

        shortcuts = create_app_shortcuts()
        auto = ""
        if enable_login_start:
            auto = str(enable_autostart(repo_root()))
        return {"exe": str(pythonw_path()), **shortcuts, "autostart": auto, "mode": "app"}

    exe = dest / "Appi.exe"
    dest.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dest.resolve():
        shutil.copytree(src, dest, dirs_exist_ok=True)
        # Keep production .env next to the installed exe
        env_src = src / ".env"
        if env_src.is_file():
            shutil.copy2(env_src, dest / ".env")
    # Windowed desktop app — no CLI args (entry runs launcher)
    shortcut = _create_shortcut(exe, shortcut=start_menu_dir() / "Appi.lnk", workdir=dest)
    desk = _create_shortcut(exe, shortcut=desktop_dir() / "Appi.lnk", workdir=dest)
    auto = ""
    if enable_login_start:
        from appi_runtime_core.autostart import startup_dir

        folder = startup_dir()
        if folder is not None:
            folder.mkdir(parents=True, exist_ok=True)
            starter = folder / "AppiRuntime.vbs"
            # No "serve" arg — windowed entry opens the desktop shell (hides to tray).
            # Use serve for login autostart so we don't pop a window every boot.
            starter.write_text(
                "Option Explicit\r\n"
                "Dim sh\r\n"
                'Set sh = CreateObject("WScript.Shell")\r\n'
                f'sh.Run """{str(exe).replace(chr(34), chr(34)+chr(34))}"" serve", 0, False\r\n',
                encoding="utf-16",
            )
            old = folder / "AppiRuntime.bat"
            if old.exists():
                old.unlink()
            auto = str(starter)
    return {
        "exe": str(exe),
        "shortcut": str(shortcut),
        "desktop": str(desk),
        "autostart": auto,
        "mode": "frozen",
    }


def uninstall() -> None:
    from appi_runtime_core.autostart import disable_autostart

    disable_autostart()
    for path in (
        start_menu_dir() / "Appi.lnk",
        desktop_dir() / "Appi.lnk",
        desktop_dir() / "Start Appi.lnk",
        data_dir() / "Start.vbs",
    ):
        if path.exists():
            path.unlink()
    dest = install_dir()
    src = frozen_source_dir()
    if src and src.resolve() == dest.resolve():
        raise RuntimeError("Close Appi, then run uninstall from the original download folder.")
    if dest.exists():
        shutil.rmtree(dest)
