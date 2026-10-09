"""First-run pairing dialog for the desktop Appi shell."""

from __future__ import annotations

import asyncio
import threading
from typing import Callable


def prompt_pair_code(*, device_page_url: str, on_success: Callable[[], None] | None = None) -> bool:
    """Show a Tk dialog to enter the Devices pairing code. Returns True if paired."""
    import tkinter as tk
    from tkinter import messagebox

    from app.config import settings
    from app.main import pair

    result = {"ok": False}
    root = tk.Tk()
    root.title("Pair Appi")
    root.configure(bg="#0f172a")
    root.resizable(False, False)
    root.update_idletasks()
    w, h = 460, 320
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(root, text="Connect this PC", fg="#38bdf8", bg="#0f172a", font=("Segoe UI", 20, "bold")).pack(
        pady=(28, 8)
    )
    tk.Label(
        root,
        text=f"1. Open {device_page_url}\n2. Sign in and create a pairing code\n3. Enter the code below",
        fg="#cbd5e1",
        bg="#0f172a",
        font=("Segoe UI", 10),
        justify="left",
    ).pack(padx=28, pady=4)

    code_var = tk.StringVar()
    entry = tk.Entry(root, textvariable=code_var, font=("Segoe UI", 18), justify="center", width=12)
    entry.pack(pady=16)
    entry.focus_set()

    status = tk.Label(root, text="", fg="#94a3b8", bg="#0f172a", font=("Segoe UI", 9))
    status.pack()

    def do_pair() -> None:
        code = code_var.get().strip().replace(" ", "")
        if len(code) < 6:
            status.config(text="Enter the 6-digit code from Devices.", fg="#f87171")
            return
        status.config(text="Pairing…", fg="#94a3b8")
        pair_btn.config(state="disabled")

        def worker() -> None:
            try:
                asyncio.run(pair(code))
                result["ok"] = True
                root.after(0, finish_ok)
            except Exception as exc:
                msg = str(exc) or "Pairing failed. Create a new code on Devices."
                root.after(0, lambda m=msg: finish_err(m))

        def finish_ok() -> None:
            messagebox.showinfo("Appi", f"Paired. Opening {settings.dashboard_url}")
            root.destroy()
            if on_success:
                on_success()

        def finish_err(msg: str) -> None:
            status.config(text=msg, fg="#f87171")
            pair_btn.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()

    bar = tk.Frame(root, bg="#0f172a")
    bar.pack(pady=18)
    pair_btn = tk.Button(bar, text="Pair this PC", command=do_pair, width=14)
    pair_btn.pack(side="left", padx=6)
    tk.Button(bar, text="Open Devices", command=lambda: _open_url(device_page_url), width=14).pack(
        side="left", padx=6
    )
    tk.Button(bar, text="Skip for now", command=root.destroy, width=12).pack(side="left", padx=6)

    root.bind("<Return>", lambda _e: do_pair())
    root.mainloop()
    return bool(result["ok"])


def _open_url(url: str) -> None:
    import webbrowser

    webbrowser.open(url)
