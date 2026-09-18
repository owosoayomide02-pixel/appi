"""Launch the desktop Python runtime. Native Apple APIs are not implemented."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "device-agent"
sys.path.insert(0, str(ROOT))
sys.argv[0] = "appi-macos-runtime"
runpy.run_module("app.main", run_name="__main__")
