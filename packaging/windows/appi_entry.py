"""Frozen Windows entry. Double-click starts the background assistant."""

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

if len(sys.argv) == 1:
    sys.argv.append("serve")

from app.main import main

if __name__ == "__main__":
    main()
