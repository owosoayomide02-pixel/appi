"""Launch the desktop Python runtime. Reports linux capabilities honestly."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "device-agent"
sys.path.insert(0, str(ROOT))
sys.argv[0] = "appi-linux-runtime"
runpy.run_module("app.main", run_name="__main__")
