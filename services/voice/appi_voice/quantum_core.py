"""Quantum Core — frameless cyan/iris voice visualizer (PyQt6)."""

from __future__ import annotations

import math
import threading
from enum import Enum
from typing import Any


class VizState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


_CTRL: Any = None
_THREAD: threading.Thread | None = None


class _Controller:
    def __init__(self) -> None:
        self.state = VizState.IDLE
        self.level = 0.08
        self._lock = threading.Lock()

    def set_state(self, state: VizState) -> None:
        with self._lock:
            self.state = state

    def set_level(self, value: float) -> None:
        with self._lock:
            self.level = max(0.05, min(float(value), 1.0))

    def snapshot(self) -> tuple[VizState, float]:
        with self._lock:
            return self.state, self.level


def start_quantum_core() -> bool:
    """Start overlay in a daemon thread. Returns False if PyQt6 unavailable."""
    global _CTRL, _THREAD
    if _THREAD and _THREAD.is_alive():
        return True
    try:
        from PyQt6.QtWidgets import QApplication  # noqa: F401
    except Exception:
        return False
    _CTRL = _Controller()

    def _run() -> None:
        import sys
        from PyQt6.QtCore import Qt, QTimer
        from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPen
        from PyQt6.QtWidgets import QApplication, QWidget

        class Core(QWidget):
            def __init__(self) -> None:
                super().__init__()
                self.setWindowFlags(
                    Qt.WindowType.FramelessWindowHint
                    | Qt.WindowType.WindowStaysOnTopHint
                    | Qt.WindowType.Tool
                )
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                self.resize(280, 280)
                self._phase = 0.0
                self._timer = QTimer(self)
                self._timer.timeout.connect(self._tick)
                self._timer.start(16)
                try:
                    import pyaudio
                    import numpy as np

                    self._np = np
                    self._pa = pyaudio.PyAudio()
                    self._stream = self._pa.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=512,
                    )
                except Exception:
                    self._np = None
                    self._pa = None
                    self._stream = None

            def _tick(self) -> None:
                self._phase += 0.05
                if self._stream is not None and self._np is not None and _CTRL:
                    try:
                        data = self._np.frombuffer(
                            self._stream.read(512, exception_on_overflow=False),
                            dtype=self._np.int16,
                        )
                        amp = float(self._np.linalg.norm(data) / 25000.0)
                        _CTRL.set_level(amp)
                    except Exception:
                        pass
                self.update()

            def paintEvent(self, _event) -> None:  # noqa: N802
                if not _CTRL:
                    return
                state, amp = _CTRL.snapshot()
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                cx, cy = self.width() / 2, self.height() / 2
                base = 48
                pulse = amp * (55 if state == VizState.LISTENING else 35)
                if state == VizState.THINKING:
                    pulse = 28 + 12 * abs(math.sin(self._phase * 3))
                if state == VizState.SPEAKING:
                    pulse = 20 + 18 * abs(math.sin(self._phase * 2))
                radius = base + pulse

                grad = QLinearGradient(0, 0, self.width(), self.height())
                grad.setColorAt(0.0, QColor(0, 242, 254, 200))
                grad.setColorAt(1.0, QColor(79, 70, 229, 200))
                pen = QPen()
                pen.setBrush(grad)
                pen.setWidthF(2.5 + amp * 5)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                for i in range(3):
                    r = radius + i * 14
                    painter.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))

                core = QColor(27, 27, 58, 230)
                painter.setBrush(core)
                painter.setPen(Qt.PenStyle.NoPen)
                cr = base * 0.55
                painter.drawEllipse(int(cx - cr), int(cy - cr), int(cr * 2), int(cr * 2))

            def closeEvent(self, event) -> None:  # noqa: N802
                if self._stream is not None:
                    self._stream.stop_stream()
                    self._stream.close()
                if self._pa is not None:
                    self._pa.terminate()
                event.accept()

        app = QApplication.instance() or QApplication(sys.argv)
        win = Core()
        win.move(40, 40)
        win.show()
        app.exec()

    _THREAD = threading.Thread(target=_run, name="appi-quantum-core", daemon=True)
    _THREAD.start()
    return True


def set_viz_state(state: str) -> None:
    if not _CTRL:
        return
    try:
        _CTRL.set_state(VizState(state))
    except Exception:
        _CTRL.set_state(VizState.IDLE)
