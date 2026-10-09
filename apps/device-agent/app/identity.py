from __future__ import annotations

import json
import os
import socket
from pathlib import Path

from app.config import settings


def identity_path() -> Path:
    root = Path(os.environ.get("APPDATA") or Path.home() / ".appi") / "Appi"
    root.mkdir(parents=True, exist_ok=True)
    return root / "device.json"


def load_identity() -> dict | None:
    path = identity_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_identity(data: dict) -> None:
    path = identity_path()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def default_name() -> str:
    return settings.device_name or socket.gethostname()
