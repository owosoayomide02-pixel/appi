"""Frozen Windows entry. Double-click opens the desktop Appi window."""

from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    base = Path(sys._MEIPASS)
else:
    base = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(base / "apps" / "device-agent"))
sys.path.insert(0, str(base / "apps" / "runtime-core"))
sys.path.insert(0, str(base / "services" / "voice"))


def _run() -> None:
    # No args → desktop shell. CLI still works: Appi.exe pair|serve|install|…
    if len(sys.argv) == 1:
        from app.launcher import main as launcher_main

        launcher_main()
    else:
        from app.main import main

        main()


if __name__ == "__main__":
    _run()
