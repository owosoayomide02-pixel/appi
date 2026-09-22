"""Native Appi window. This is the application UI — not a browser tab, not a console."""

from __future__ import annotations

import sys
import threading
from typing import Any

WINDOW: Any = None
_lock = threading.Lock()


def _dashboard_url() -> str:
    try:
        from app.config import settings

        return settings.dashboard_url
    except Exception:
        return "http://127.0.0.1:3000/app"


def _start_url() -> str:
    try:
        from app.config import settings
        from app.identity import load_identity

        if load_identity():
            return settings.dashboard_url
        return settings.device_page_url
    except Exception:
        return _dashboard_url()


DASHBOARD_URL = _dashboard_url()


def request_show() -> bool:
    """Bring the Appi window back (tray / second click)."""
    with _lock:
        window = WINDOW
    if window is None:
        return False
    try:
        for name in ("show", "deiconify", "restore", "lift"):
            fn = getattr(window, name, None)
            if callable(fn):
                fn()
        return True
    except Exception:
        return False


def request_quit() -> None:
    with _lock:
        window = WINDOW
    if window is None:
        return
    try:
        window.destroy()
    except Exception:
        pass


def _center(root: Any, width: int, height: int) -> None:
    root.update_idletasks()
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")


def show_splash() -> Any:
    import tkinter as tk

    root = tk.Tk()
    root.title("Appi")
    root.configure(bg="#0f172a")
    root.resizable(False, False)
    _center(root, 420, 220)
    tk.Label(root, text="Appi", fg="#38bdf8", bg="#0f172a", font=("Segoe UI", 28, "bold")).pack(pady=(48, 8))
    tk.Label(root, text="Starting…", fg="#cbd5e1", bg="#0f172a", font=("Segoe UI", 12)).pack()
    root.update()
    return root


def _run_webview(url: str) -> None:
    import webview

    global WINDOW
    window = webview.create_window(
        "Appi",
        url,
        width=1280,
        height=840,
        min_size=(900, 600),
        text_select=True,
        confirm_close=False,
    )

    def on_closing() -> bool:
        window.hide()
        return False

    window.events.closing += on_closing
    with _lock:
        WINDOW = window
    try:
        webview.start(gui="edgechromium")
    except Exception:
        webview.start()
    finally:
        with _lock:
            WINDOW = None


def _run_control_panel(*, on_exit: Any) -> None:
    """Always-on Appi window if WebView2 is missing. Still an application, not a console."""
    import tkinter as tk

    root = tk.Tk()
    root.title("Appi")
    root.configure(bg="#0f172a")
    _center(root, 480, 280)
    tk.Label(root, text="Appi", fg="#38bdf8", bg="#0f172a", font=("Segoe UI", 28, "bold")).pack(pady=(36, 8))
    tk.Label(
        root,
        text="Running in the background.\nSay Appi, or press Ctrl+Shift+A.",
        fg="#cbd5e1",
        bg="#0f172a",
        font=("Segoe UI", 11),
        justify="center",
    ).pack(pady=8)

    bar = tk.Frame(root, bg="#0f172a")
    bar.pack(pady=24)
    tk.Button(bar, text="Show Appi", command=lambda: (root.deiconify(), root.lift()), width=16).pack(side="left", padx=8)
    tk.Button(bar, text="Quit Appi", command=lambda: (on_exit(), root.destroy()), width=16).pack(side="left", padx=8)
    global WINDOW
    with _lock:
        WINDOW = root
    root.protocol("WM_DELETE_WINDOW", lambda: (root.iconify()))
    root.mainloop()
    with _lock:
        WINDOW = None


def run_desktop(url: str | None = None, *, on_exit: Any = None) -> None:
    target = url or _start_url()
    try:
        import webview  # noqa: F401
    except ImportError:
        _run_control_panel(on_exit=on_exit or (lambda: None))
        return
    try:
        _run_webview(target)
    except Exception:
        _run_control_panel(on_exit=on_exit or (lambda: None))


def ping_existing() -> dict:
    """Talk to a running Appi process. Returns {} if none."""
    import json
    import socket

    try:
        with socket.create_connection(("127.0.0.1", 47821), timeout=0.4) as sock:
            sock.sendall(b'{"cmd":"open"}\n')
            raw = sock.recv(4096)
        data = json.loads(raw.decode("utf-8") or "{}")
        return data if isinstance(data, dict) else {}
    except OSError:
        return {}
    except Exception:
        return {}
