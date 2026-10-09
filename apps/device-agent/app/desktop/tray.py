"""Optional Windows system-tray status. Missing pystray is not a runtime failure."""

from __future__ import annotations

import sys
import threading
from typing import Callable


def start_tray(*, on_open: Callable[[], None], on_mute: Callable[[], None], on_pause: Callable[[], None], on_stop: Callable[[], None], on_exit: Callable[[], None]) -> bool:
    if not sys.platform.startswith("win"):
        return False
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print("System tray extra not installed. Runtime continues without a tray icon.")
        print("Install with: python -m pip install pystray pillow")
        return False

    image = Image.new("RGB", (64, 64), color=(15, 23, 42))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(56, 189, 248))

    def run() -> None:
        icon = pystray.Icon(
            "Appi",
            image,
            "Appi\nOnline\nWake word: ON\nMicrophone: Wake-word only",
            menu=pystray.Menu(
                pystray.MenuItem("Open Appi", lambda: on_open()),
                pystray.MenuItem("Mute / Unmute microphone", lambda: on_mute()),
                pystray.MenuItem("Pause / Resume agent", lambda: on_pause()),
                pystray.MenuItem("Stop All Tasks", lambda: on_stop()),
                pystray.MenuItem("Exit", lambda icon_obj, item: (on_exit(), icon_obj.stop())),
            ),
        )
        icon.run()

    threading.Thread(target=run, daemon=True).start()
    return True
