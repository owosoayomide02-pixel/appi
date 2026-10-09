"""Ctrl+Shift+A local activation when Speech Recognition is unavailable."""

from __future__ import annotations

import sys
import threading
import time


class HotkeyWakeWord:
    name = "hotkey-ctrl-shift-a"

    def __init__(self) -> None:
        self._hit = threading.Event()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if not sys.platform.startswith("win") or self._thread:
            return
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def listen_once(self, timeout: float | None = 12.0) -> bool:
        self.start()
        return self._hit.wait(timeout if timeout is not None else 12.0) and not self._hit.clear()

    def _loop(self) -> None:
        import ctypes

        user32 = ctypes.windll.user32
        vk_a, ctrl, shift = 0x41, 0x11, 0x10
        while not self._stop.is_set():
            if user32.GetAsyncKeyState(vk_a) & 0x8000 and user32.GetAsyncKeyState(ctrl) & 0x8000 and user32.GetAsyncKeyState(shift) & 0x8000:
                self._hit.set()
                time.sleep(0.6)
            time.sleep(0.05)
