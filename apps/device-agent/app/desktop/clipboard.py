"""Windows clipboard. Other platforms return CAPABILITY_RESTRICTED_BY_OS until tested.

Uses the Win32 clipboard API directly. A GUI toolkit is not started for a
clipboard read or write: that is slow, needs a display, and has crashed the
runtime process on some Windows/Python builds.
"""

from __future__ import annotations

import sys
import time
from typing import Any

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002


def _err(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": message, "error_code": code, "verification_required": True}


def _ok(data: dict[str, Any]) -> dict[str, Any]:
    return {"success": True, "data": data, "verification_required": True}


def _bind():
    """Return (ctypes, user32, kernel32) with argtypes set, or None off Windows."""
    if not sys.platform.startswith("win"):
        return None
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL

    return ctypes, user32, kernel32


def _open(user32, attempts: int = 8) -> bool:
    """Another process can hold the clipboard briefly. Retry, do not block forever."""
    for _ in range(attempts):
        if user32.OpenClipboard(None):
            return True
        time.sleep(0.05)
    return False


def _read_text() -> str | None:
    bound = _bind()
    if bound is None:
        return None
    ctypes, user32, kernel32 = bound
    try:
        if not _open(user32):
            return None
        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            locked = kernel32.GlobalLock(handle)
            if not locked:
                return None
            try:
                return ctypes.wstring_at(locked)
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()
    except OSError:
        return None


def _write_text(text: str) -> bool:
    bound = _bind()
    if bound is None:
        return False
    ctypes, user32, kernel32 = bound
    try:
        if not _open(user32):
            return False
        try:
            if not user32.EmptyClipboard():
                return False
            buffer = ctypes.create_unicode_buffer(text)
            size = ctypes.sizeof(buffer)
            handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            if not handle:
                return False
            locked = kernel32.GlobalLock(handle)
            if not locked:
                kernel32.GlobalFree(handle)
                return False
            try:
                ctypes.memmove(locked, buffer, size)
            finally:
                kernel32.GlobalUnlock(handle)
            if not user32.SetClipboardData(CF_UNICODETEXT, handle):
                kernel32.GlobalFree(handle)
                return False
            return True
        finally:
            user32.CloseClipboard()
    except OSError:
        return False


def read() -> dict[str, Any]:
    if not sys.platform.startswith("win"):
        return _err("CAPABILITY_RESTRICTED_BY_OS", "Clipboard read is implemented on Windows in this milestone")
    text = _read_text()
    if text is None:
        return _err("ACTION_FAILED", "Could not read clipboard")
    return _ok({"text": text, "empty": not bool(text)})


def write(text: str) -> dict[str, Any]:
    if not sys.platform.startswith("win"):
        return _err("CAPABILITY_RESTRICTED_BY_OS", "Clipboard write is implemented on Windows in this milestone")
    data = str(text or "")
    if not _write_text(data):
        return _err("ACTION_FAILED", "Could not write clipboard")
    return _ok({"text": data, "written": True})
