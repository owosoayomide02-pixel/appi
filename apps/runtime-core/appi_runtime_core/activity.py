"""User activity detector. Windows uses last-input tick; others report unknown."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass


@dataclass
class ActivitySnapshot:
    idle_seconds: float | None
    busy: bool
    source: str


def last_input_idle_seconds() -> ActivitySnapshot:
    if not sys.platform.startswith("win"):
        return ActivitySnapshot(idle_seconds=None, busy=False, source="unsupported")
    import ctypes
    from ctypes import wintypes

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return ActivitySnapshot(idle_seconds=None, busy=False, source="windows-failed")
    millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
    idle = max(millis / 1000.0, 0.0)
    return ActivitySnapshot(idle_seconds=idle, busy=idle < 2.0, source="windows")


def should_ask_before_foreground(*, idle_threshold: float = 8.0) -> bool:
    snap = last_input_idle_seconds()
    if snap.idle_seconds is None:
        return False
    return snap.idle_seconds < idle_threshold
