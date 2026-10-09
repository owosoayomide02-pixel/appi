"""Local voice preferences: TTS voice, recognition culture, confidence floor."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def prefs_path() -> Path:
    root = Path(os.environ.get("APPDATA") or Path.home() / ".appi") / "Appi"
    root.mkdir(parents=True, exist_ok=True)
    return root / "voice.json"


DEFAULTS = {
    "tts_voice": "",
    "tts_gender": "",
    "culture": "",
    "min_confidence": 0.45,
}


def load_voice_prefs() -> dict[str, Any]:
    path = prefs_path()
    data = dict(DEFAULTS)
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update({k: loaded[k] for k in DEFAULTS if k in loaded})
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    try:
        data["min_confidence"] = float(data.get("min_confidence") or 0.45)
    except (TypeError, ValueError):
        data["min_confidence"] = 0.45
    data["tts_voice"] = str(data.get("tts_voice") or "")
    data["tts_gender"] = str(data.get("tts_gender") or "")
    data["culture"] = str(data.get("culture") or "")
    return data


def save_voice_prefs(updates: dict[str, Any]) -> dict[str, Any]:
    data = load_voice_prefs()
    if "tts_voice" in updates and updates["tts_voice"] is not None:
        data["tts_voice"] = str(updates["tts_voice"])
    if "tts_gender" in updates and updates["tts_gender"] is not None:
        data["tts_gender"] = str(updates["tts_gender"])
    if "culture" in updates and updates["culture"] is not None:
        data["culture"] = str(updates["culture"])
    if "min_confidence" in updates and updates["min_confidence"] is not None:
        data["min_confidence"] = float(updates["min_confidence"])
    prefs_path().write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
