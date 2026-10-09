"""One-time Windows dialog to save the local login vault. Password never goes to the model."""

from __future__ import annotations

from app.secrets_vault import save_login, status


def prompt_if_empty() -> dict:
    info = status()
    if info.get("saved"):
        return info
    try:
        import tkinter as tk
        from tkinter import messagebox
    except Exception:
        return info

    result: dict = {"saved": False}

    root = tk.Tk()
    root.title("Appi — save login for this PC")
    root.geometry("460x260")
    tk.Label(
        root,
        text=(
            "Save the email and password Appi may use to log in on this laptop.\n"
            "It is encrypted for your Windows account only.\n"
            "It is never sent to the chat or the cloud model.\n"
            "Banks, payments, and MFA stay with you."
        ),
        justify="left",
        wraplength=420,
    ).pack(padx=16, pady=12)
    tk.Label(root, text="Email").pack(anchor="w", padx=16)
    email = tk.Entry(root, width=48)
    email.pack(padx=16)
    tk.Label(root, text="Password").pack(anchor="w", padx=16)
    password = tk.Entry(root, width=48, show="*")
    password.pack(padx=16)

    def save() -> None:
        try:
            save_login(email.get(), password.get())
            result.update(status())
            root.destroy()
        except Exception as exc:
            messagebox.showerror("Appi", str(exc))

    def skip() -> None:
        root.destroy()

    bar = tk.Frame(root)
    bar.pack(pady=16)
    tk.Button(bar, text="Save on this PC", command=save).pack(side="left", padx=8)
    tk.Button(bar, text="Skip for now", command=skip).pack(side="left", padx=8)
    root.mainloop()
    return result if result.get("saved") else status()
