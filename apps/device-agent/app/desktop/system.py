"""Local system information. Dangerous power actions are not executed in this milestone."""

from __future__ import annotations

import os
import platform
import socket
from typing import Any


def info() -> dict[str, Any]:
    return {
        "success": True,
        "data": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "user": os.environ.get("USERNAME") or os.environ.get("USER") or "",
        },
        "verification_required": True,
    }
