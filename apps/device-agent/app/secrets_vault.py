"""Local login vault. Encrypted for this Windows user. Never sent to the model."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VAULT_NAME = "login.vault"


def vault_path() -> Path:
    root = Path(os.environ.get("APPDATA") or Path.home() / ".appi") / "Appi"
    root.mkdir(parents=True, exist_ok=True)
    return root / VAULT_NAME


def _protect(raw: bytes) -> bytes:
    if not sys.platform.startswith("win"):
        raise RuntimeError("The login vault is Windows DPAPI only in this milestone")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(raw, len(raw))
    blob_in = DATA_BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(blob_in), "AppiLoginVault", None, None, None, 0, ctypes.byref(blob_out)
    ):
        raise RuntimeError("Windows could not encrypt the vault for this user")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _unprotect(raw: bytes) -> bytes:
    if not sys.platform.startswith("win"):
        raise RuntimeError("The login vault is Windows DPAPI only in this milestone")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(raw, len(raw))
    blob_in = DATA_BLOB(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        raise RuntimeError("Windows could not decrypt the vault for this user")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def save_login(email: str, password: str) -> dict[str, Any]:
    email = (email or "").strip()
    password = password or ""
    if "@" not in email or not password:
        raise ValueError("Email and password are required")
    payload = json.dumps(
        {"email": email, "password": password, "saved_at": datetime.now(UTC).isoformat(), "scope": "this-windows-user"},
        ensure_ascii=False,
    ).encode("utf-8")
    vault_path().write_bytes(_protect(payload))
    return status()


def load_login() -> dict[str, str] | None:
    path = vault_path()
    if not path.exists():
        return None
    data = json.loads(_unprotect(path.read_bytes()).decode("utf-8"))
    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "")
    if not email or not password:
        return None
    return {"email": email, "password": password}


def clear_login() -> None:
    path = vault_path()
    if path.exists():
        path.unlink()


def status() -> dict[str, Any]:
    creds = None
    try:
        creds = load_login()
    except Exception:
        return {"saved": False, "email": "", "error": "Vault exists but could not be decrypted on this Windows account"}
    if not creds:
        return {"saved": False, "email": ""}
    email = creds["email"]
    hint = email[0] + "***" + email[email.find("@") :] if "@" in email else "***"
    return {"saved": True, "email": hint, "model_can_read_password": False}


def email_hint() -> str:
    return str(status().get("email") or "")
