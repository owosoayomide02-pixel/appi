"""Voice pipeline: local wake word → capture command → Appi brain → TTS.

Does not bypass Guardian. Voice is an input method.
Speaker verification is prepared but is NOT treated as strong auth.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from appi_voice.hotkey import HotkeyWakeWord
from appi_voice.providers import SpeechToText, TextToSpeech, WakeWordEngine
from appi_voice.states import (
    DEFAULT_MIC_STATE,
    DEFAULT_RESPONSE_MODE,
    DEFAULT_WAKE_WORD,
    MicState,
    VoiceResponseMode,
    speakable,
)
from appi_voice.windows_sapi import WindowsGrammarWakeWord, WindowsLocalSTT, WindowsSapiTTS, speech_inventory


@dataclass
class VoiceConfig:
    wake_word: str = DEFAULT_WAKE_WORD
    mic_state: MicState = DEFAULT_MIC_STATE
    response_mode: VoiceResponseMode = DEFAULT_RESPONSE_MODE
    continuous_conversation: bool = False
    ack_text: str = "Yes?"
    done_text: str = "Done."
    tts_voice: str = ""
    tts_gender: str = ""
    culture: str = ""
    min_confidence: float = 0.45


@dataclass
class VoiceStatus:
    mic_state: MicState
    wake_word: str
    wake_engine: str
    stt_engine: str
    tts_engine: str
    last_error: str | None = None
    notes: list[str] = field(default_factory=list)


class SpeakerVerifier:
    """Placeholder. Voice is not sufficient for high-risk actions."""

    name = "unconfigured"

    def verify(self) -> bool:
        return False


class VoicePipeline:
    def __init__(
        self,
        config: VoiceConfig | None = None,
        *,
        wake: WakeWordEngine | None = None,
        stt: SpeechToText | None = None,
        tts: TextToSpeech | None = None,
    ) -> None:
        self.config = config or VoiceConfig()
        self.wake = wake or WindowsGrammarWakeWord(self.config.wake_word, culture=self.config.culture)
        self.hotkey = HotkeyWakeWord()
        self.stt = stt or WindowsLocalSTT(culture=self.config.culture, min_confidence=self.config.min_confidence)
        self.tts = tts or WindowsSapiTTS(voice=self.config.tts_voice, gender=self.config.tts_gender)
        self.speaker = SpeakerVerifier()
        self.last_recognition: dict[str, Any] = {}
        self.status = VoiceStatus(
            mic_state=self.config.mic_state,
            wake_word=self.config.wake_word,
            wake_engine=getattr(self.wake, "name", "unknown"),
            stt_engine=getattr(self.stt, "name", "unknown"),
            tts_engine=getattr(self.tts, "name", "unknown"),
            notes=[
                "Wake-word audio stays on-device.",
                "Raw microphone audio is not stored.",
                "Voice is not a Guardian bypass.",
                "Ctrl+Shift+A is the fallback activator if Speech Recognition is unavailable.",
            ],
        )

    def apply_prefs(self, prefs: dict[str, Any]) -> None:
        self.config.tts_voice = str(prefs.get("tts_voice") or "")
        self.config.tts_gender = str(prefs.get("tts_gender") or "")
        self.config.culture = str(prefs.get("culture") or "")
        try:
            self.config.min_confidence = float(prefs.get("min_confidence") or 0.45)
        except (TypeError, ValueError):
            self.config.min_confidence = 0.45
        if hasattr(self.tts, "set_voice"):
            self.tts.set_voice(self.config.tts_voice, self.config.tts_gender)
        if hasattr(self.stt, "set_prefs"):
            self.stt.set_prefs(culture=self.config.culture, min_confidence=self.config.min_confidence)
        if hasattr(self.wake, "culture"):
            self.wake.culture = self.config.culture

    def set_mic(self, state: MicState) -> None:
        self.status.mic_state = state
        self.config.mic_state = state

    def wait_for_wake(self, timeout: float = 12.0) -> bool:
        if self.status.mic_state == MicState.OFF:
            time.sleep(min(timeout, 0.5))
            return False
        if self.status.mic_state not in {MicState.WAKE_WORD_ONLY, MicState.CONVERSATION}:
            return False
        if hasattr(self.wake, "start"):
            self.wake.start()
        self.hotkey.start()
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = max(0.05, min(0.4, deadline - time.time()))
            if self.wake.listen_once(timeout=remaining):
                if hasattr(self.wake, "stop"):
                    self.wake.stop()
                return True
            if getattr(self.hotkey, "_hit", None) is not None and self.hotkey._hit.is_set():
                self.hotkey._hit.clear()
                if hasattr(self.wake, "stop"):
                    self.wake.stop()
                return True
        return False

    def diagnose(self, *, speak_ack: bool = False) -> dict:
        tts_probe = self.tts.probe() if hasattr(self.tts, "probe") else {"ok": False}
        stt_probe = self.stt.probe() if hasattr(self.stt, "probe") else {"ok": False}
        wake_probe = self.wake.probe() if hasattr(self.wake, "probe") else {"ok": False}
        inventory = speech_inventory()
        if speak_ack:
            self.acknowledge()
        return {
            "wake_word": self.config.wake_word,
            "mic_state": self.status.mic_state.value,
            "tts": tts_probe,
            "stt": stt_probe,
            "wake": wake_probe,
            "prefs": {
                "tts_voice": self.config.tts_voice,
                "tts_gender": self.config.tts_gender,
                "culture": self.config.culture,
                "min_confidence": self.config.min_confidence,
            },
            "voices": inventory.get("voices") or [],
            "recognizers": inventory.get("recognizers") or [],
            "spoke_yes": speak_ack,
            "notes": self.status.notes,
        }

    def capture_command(self, timeout: float = 10.0) -> str | None:
        self.set_mic(MicState.CONVERSATION)
        time.sleep(0.35)
        if hasattr(self.stt, "recognize"):
            result = self.stt.recognize(timeout=timeout)
            self.last_recognition = result
            text = str(result.get("text") or "").strip()
            floor = 0.28 if result.get("source") == "appi-commands" else self.config.min_confidence
            if text and float(result.get("confidence") or 0) >= floor:
                if not self.config.continuous_conversation:
                    self.set_mic(MicState.WAKE_WORD_ONLY)
                return text
            if not self.config.continuous_conversation:
                self.set_mic(MicState.WAKE_WORD_ONLY)
            return None
        text = self.stt.transcribe(timeout=timeout)
        if not self.config.continuous_conversation:
            self.set_mic(MicState.WAKE_WORD_ONLY)
        return text

    def acknowledge(self) -> None:
        if self.config.response_mode != VoiceResponseMode.SILENT:
            self.tts.speak(self.config.ack_text)

    def respond(self, result: str, *, detail: str | None = None) -> None:
        phrase = speakable(self.config.response_mode, ack=None, result=result, verbose_detail=detail)
        if phrase:
            self.tts.speak(phrase)
