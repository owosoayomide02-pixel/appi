"""Windows local TTS / Speech Recognition. Audio does not leave the device for wake-word."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Any

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _ps_file(script: str, extra: list[str] | None = None, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    cmd = ["powershell", "-NoProfile", "-STA", "-File", str(SCRIPTS / script)]
    if extra:
        cmd.extend(extra)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform.startswith("win") else 0,
    )


def speech_inventory() -> dict[str, Any]:
    if not sys.platform.startswith("win"):
        return {"voices": [], "recognizers": []}
    try:
        proc = _ps_file("inventory.ps1", timeout=20)
        payload = json.loads(proc.stdout or "{}")
        if isinstance(payload, dict):
            voices = payload.get("voices") or []
            recognizers = payload.get("recognizers") or []
            if isinstance(voices, dict):
                voices = [voices]
            if isinstance(recognizers, dict):
                recognizers = [recognizers]
            return {"voices": list(voices), "recognizers": list(recognizers)}
    except Exception:
        pass
    return {"voices": [], "recognizers": []}


class WindowsSapiTTS:
    name = "windows-sapi"

    def __init__(self, voice: str = "", gender: str = "") -> None:
        self.voice = voice
        self.gender = gender

    def set_voice(self, voice: str = "", gender: str = "") -> None:
        self.voice = voice
        self.gender = gender

    def speak(self, text: str) -> None:
        if not text.strip() or not sys.platform.startswith("win"):
            return
        extra = ["-Text", text]
        if self.voice:
            extra.extend(["-Voice", self.voice])
        elif self.gender:
            extra.extend(["-Gender", self.gender])
        try:
            _ps_file("speak.ps1", extra, timeout=max(8.0, len(text) / 6 + 5))
        except Exception:
            return

    def probe(self) -> dict[str, str | bool]:
        if not sys.platform.startswith("win"):
            return {"ok": False, "engine": self.name, "error": "not windows"}
        try:
            proc = _ps_file("probe_tts.ps1", timeout=20)
        except Exception as exc:
            return {"ok": False, "engine": self.name, "error": str(exc)}
        ok = "TTS_ENGINE_OK" in (proc.stdout or "")
        return {"ok": ok, "engine": self.name, "stdout": (proc.stdout or "").strip()}


class WindowsLocalSTT:
    """Uses Windows Speech Recognition if installed. Not a cloud stream."""

    name = "windows-speech-recognition"
    cloud = False

    def __init__(self, culture: str = "", min_confidence: float = 0.45) -> None:
        self.culture = culture
        self.min_confidence = min_confidence

    def set_prefs(self, *, culture: str = "", min_confidence: float | None = None) -> None:
        if culture is not None:
            self.culture = culture
        if min_confidence is not None:
            self.min_confidence = float(min_confidence)

    def recognize(self, timeout: float = 8.0) -> dict[str, Any]:
        empty = {"ok": False, "text": "", "confidence": 0.0, "source": ""}
        if not sys.platform.startswith("win"):
            return empty
        extra = ["-Seconds", str(max(3, int(timeout)))]
        if self.culture:
            extra.extend(["-Culture", self.culture])
        extra.extend(["-CommandsFile", os.environ.get("APPI_VOICE_COMMANDS") or str(SCRIPTS / "commands.txt")])
        try:
            proc = _ps_file("transcribe.ps1", extra, timeout=timeout + 12)
        except Exception:
            return empty
        raw = (proc.stdout or "").strip()
        if not raw:
            return empty
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return {
                    "ok": bool(payload.get("ok")),
                    "text": str(payload.get("text") or "").strip(),
                    "confidence": float(payload.get("confidence") or 0),
                    "source": str(payload.get("source") or ""),
                }
        except (json.JSONDecodeError, TypeError, ValueError):
            return {"ok": True, "text": raw, "confidence": 0.5, "source": "legacy"}
        return empty

    def transcribe(self, timeout: float = 8.0) -> str | None:
        result = self.recognize(timeout=timeout)
        text = (result.get("text") or "").strip()
        if not text:
            return None
        floor = 0.28 if result.get("source") == "appi-commands" else self.min_confidence
        if float(result.get("confidence") or 0) < floor:
            return None
        return text

    def probe(self) -> dict[str, str | bool]:
        if not sys.platform.startswith("win"):
            return {"ok": False, "engine": self.name, "error": "not windows"}
        try:
            proc = _ps_file("probe_sr.ps1", timeout=20)
        except Exception as exc:
            return {"ok": False, "engine": self.name, "error": str(exc)}
        out = (proc.stdout or "").strip()
        return {"ok": "SR_MIC_OK" in out, "engine": self.name, "stdout": out}


class WindowsGrammarWakeWord:
    """Persistent local grammar listener for the wake word."""

    name = "windows-grammar-wake"

    def __init__(self, wake_word: str = "Appi", culture: str = "") -> None:
        self.wake_word = wake_word
        self.culture = culture
        self._proc: subprocess.Popen[str] | None = None
        self._queue: Queue[str] = Queue()
        self._reader: threading.Thread | None = None
        self._error: str | None = None

    def probe(self) -> dict[str, str | bool]:
        if not sys.platform.startswith("win"):
            return {"ok": False, "engine": self.name, "error": "not windows"}
        try:
            proc = _ps_file("probe_grammar.ps1", timeout=20)
        except Exception as exc:
            return {"ok": False, "engine": self.name, "error": str(exc)}
        out = (proc.stdout or "").strip()
        return {"ok": "GRAMMAR_APPI_OK" in out, "engine": self.name, "stdout": out}

    def start(self) -> None:
        if not sys.platform.startswith("win") or self._proc is not None:
            return
        cmd = [
            "powershell",
            "-NoProfile",
            "-STA",
            "-File",
            str(SCRIPTS / "wake_listen.ps1"),
            "-WakeWord",
            self.wake_word,
        ]
        if self.culture:
            cmd.extend(["-Culture", self.culture])
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        def _read() -> None:
            assert self._proc and self._proc.stdout
            for line in self._proc.stdout:
                self._queue.put(line.strip())

        self._reader = threading.Thread(target=_read, daemon=True)
        self._reader.start()
        deadline = time.time() + 8
        while time.time() < deadline:
            try:
                line = self._queue.get(timeout=0.4)
            except Empty:
                if self._proc.poll() is not None:
                    err = (self._proc.stderr.read() if self._proc.stderr else "") or ""
                    self._error = err.strip() or f"exit {self._proc.returncode}"
                    return
                continue
            if line == "LISTENING":
                return
            if line.startswith("UNAVAILABLE"):
                self._error = line
                return

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except Exception:
                self._proc.kill()
        self._proc = None
        self._error = None
        while True:
            try:
                self._queue.get_nowait()
            except Empty:
                break

    def listen_once(self, timeout: float | None = 12.0) -> bool:
        if self._error:
            return False
        if self._proc is None:
            self.start()
        if self._error or self._proc is None:
            return False
        deadline = time.time() + (timeout or 12.0)
        while time.time() < deadline:
            try:
                line = self._queue.get(timeout=0.4)
            except Empty:
                if self._proc.poll() is not None:
                    return False
                continue
            if line == "WAKE":
                return True
        return False
