# Appi Voice

Local-first voice pipeline used by the desktop background runtime.

```
Microphone → wake-word (local) → VAD → STT → Appi Brain → Guardian → act → TTS
```

Default microphone state: `WAKE_WORD_ONLY`.

The wake word **Appi** is configurable. Audio is not streamed to the cloud to detect it.

Windows uses System.Speech (SAPI) when Speech Recognition is installed, with **Ctrl+Shift+A** as a local fallback.

Voice is an input method. It does not bypass Guardian.
