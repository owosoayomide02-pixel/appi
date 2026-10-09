"""Pluggable wake-word, VAD, STT, and TTS providers.

Wake-word audio must stay local. Do not stream the microphone to the cloud
to detect the wake word.
"""

from __future__ import annotations

from typing import Protocol


class WakeWordEngine(Protocol):
    name: str

    def listen_once(self, timeout: float | None = None) -> bool:
        """Return True when the configured wake word is detected locally."""


class VoiceActivityDetector(Protocol):
    name: str

    def speech_ended(self, silence_seconds: float = 1.2) -> bool: ...


class SpeechToText(Protocol):
    name: str
    cloud: bool

    def transcribe(self, timeout: float = 8.0) -> str | None:
        """Return recognized text, or None. Cloud STT is allowed only after wake word."""


class TextToSpeech(Protocol):
    name: str

    def speak(self, text: str) -> None: ...
