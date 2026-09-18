"""Start Appi as a desktop application: native window, no CMD, no browser tab."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if sys.platform.startswith("win") else 0

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    REPO_ROOT = Path(sys._MEIPASS)
else:
    REPO_ROOT = Path(__file__).resolve().parents[3]


def _popup(title: str, text: str) -> None:
    if not sys.platform.startswith("win"):
        print(f"{title}: {text}")
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, text, title, 0x40)
    except Exception:
        print(f"{title}: {text}")


def port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def wait_for_port(port: int, seconds: float = 45.0, host: str = "127.0.0.1") -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if port_open(port, host=host):
            return True
        time.sleep(0.4)
    return False


def _hidden(cmd: list[str], cwd: Path) -> subprocess.Popen[bytes]:
    flags = CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )


def _log(message: str) -> None:
    try:
        log = Path(os.environ.get("APPDATA") or ".") / "Appi" / "desktop.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")
    except Exception:
        pass


def _python() -> str:
    python = sys.executable
    if python.lower().endswith("pythonw.exe"):
        cand = Path(python).with_name("python.exe")
        if cand.exists():
            return str(cand)
    return python


def ensure_stack() -> None:
    from app.config import settings

    api_host = settings.resolved_api_host
    api_port = settings.resolved_api_port
    web_port = settings.web_port

    api = REPO_ROOT / "services" / "api"
    web = REPO_ROOT / "apps" / "web"
    if not (api / "app").is_dir():
        if not port_open(api_port, host=api_host):
            _popup(
                "Appi",
                "This Appi shortcut needs the APPI folder on this PC.",
            )
            sys.exit(2)
        return
    if not port_open(api_port, host=api_host):
        _hidden(
            [
                _python(),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                api_host,
                "--port",
                str(api_port),
            ],
            api,
        )
        if not wait_for_port(api_port, 50, host=api_host):
            _popup("Appi", "Could not start Appi.")
            sys.exit(2)
    if not port_open(web_port):
        npm = "npm.cmd" if sys.platform.startswith("win") else "npm"
        _hidden([npm, "run", "dev"], web)
        if not wait_for_port(web_port, 90):
            _popup("Appi", "Could not start Appi. Install Node.js, then try again.")
            sys.exit(2)


def _start_agent() -> None:
    os.environ["APPI_SKIP_VAULT_PROMPT"] = "1"
    os.environ["APPI_DESKTOP"] = "1"
    from app.main import main as agent_main

    sys.argv = [sys.argv[0], "serve"]
    agent_main()


def main() -> None:
    os.chdir(REPO_ROOT / "apps" / "device-agent")
    if str(REPO_ROOT / "apps" / "runtime-core") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "apps" / "runtime-core"))
        sys.path.insert(0, str(REPO_ROOT / "services" / "voice"))

    from app.desktop.app_window import ping_existing, run_desktop, show_splash, request_quit

    _log("starting")
    existing = ping_existing()
    if existing.get("ok") and existing.get("shown"):
        _log("already running, shown existing window")
        return
    if existing.get("ok"):
        _log("runtime up, opening window")
        run_desktop()
        return

    splash = show_splash()
    try:
        ensure_stack()
    finally:
        try:
            splash.destroy()
        except Exception:
            pass
    try:
        from app.vault_prompt import prompt_if_empty

        prompt_if_empty()
    except Exception:
        pass

    def on_exit() -> None:
        import app.main as agent

        agent.STOP = True
        request_quit()

    threading.Thread(target=_start_agent, daemon=True).start()
    wait_for_port(47821, 8)
    _log("opening Appi window")
    try:
        run_desktop(on_exit=on_exit)
    except Exception as exc:
        _log(f"window failed: {exc}")
        _popup("Appi", f"Could not open the Appi window.\n{exc}")
        raise
    _log("window closed")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        _log(f"crash: {exc}")
        _popup("Appi", str(exc))
        raise
