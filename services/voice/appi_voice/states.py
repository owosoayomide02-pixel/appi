"""Microphone privacy states and voice response verbosity."""

from __future__ import annotations

from enum import Enum


class MicState(str, Enum):
    OFF = "OFF"
    WAKE_WORD_ONLY = "WAKE_WORD_ONLY"
    CONVERSATION = "CONVERSATION"
    RECORDING_TASK = "RECORDING_TASK"


class VoiceResponseMode(str, Enum):
    SILENT = "SILENT"
    BRIEF = "BRIEF"
    NORMAL = "NORMAL"
    VERBOSE = "VERBOSE"


DEFAULT_MIC_STATE = MicState.WAKE_WORD_ONLY
DEFAULT_WAKE_WORD = "Appi"
DEFAULT_RESPONSE_MODE = VoiceResponseMode.BRIEF


def speakable(mode: VoiceResponseMode, *, ack: str | None, result: str | None, verbose_detail: str | None = None) -> str:
    if mode == VoiceResponseMode.SILENT:
        return ""
    if mode == VoiceResponseMode.BRIEF:
        return (result or ack or "").strip()
    if mode == VoiceResponseMode.VERBOSE:
        parts = [p for p in (ack, result, verbose_detail) if p]
        return " ".join(parts)
    return " ".join(p for p in (ack, result) if p)
