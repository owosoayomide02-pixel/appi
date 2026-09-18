from pathlib import Path

import pytest

from appi_voice.pipeline import VoicePipeline
from appi_voice.windows_sapi import WindowsGrammarWakeWord, WindowsSapiTTS


def test_voice_probes_on_windows():
    tts = WindowsSapiTTS().probe()
    wake = WindowsGrammarWakeWord().probe()
    if not tts["ok"] or not wake["ok"]:
        pytest.skip(f"Windows Speech is unavailable in this session: tts={tts} wake={wake}")
    assert tts["ok"] is True
    assert wake["ok"] is True


def test_diagnose_does_not_require_speech():
    report = VoicePipeline().diagnose(speak_ack=False)
    assert report["wake_word"] == "Appi"
    if not report["tts"].get("ok") or not report["wake"].get("ok"):
        pytest.skip("Windows Speech is unavailable in this session")
    assert report["tts"]["ok"] is True
    assert report["wake"]["ok"] is True


def test_command_grammar_includes_open_chrome():
    path = Path(__file__).resolve().parents[3] / "services" / "voice" / "scripts" / "commands.txt"
    text = path.read_text(encoding="utf-8").lower()
    assert "open chrome" in text
    assert "what can you do" in text
    script = (path.parent / "transcribe.ps1").read_text(encoding="utf-8")
    assert "appi-commands" in script
    assert "DictationGrammar" in script
    speak = (path.parent / "speak.ps1").read_text(encoding="utf-8")
    assert "SelectVoice" in speak


def test_voice_prefs_roundtrip(tmp_path, monkeypatch):
    from app import voice_prefs

    monkeypatch.setattr(voice_prefs, "prefs_path", lambda: tmp_path / "voice.json")
    saved = voice_prefs.save_voice_prefs({"tts_voice": "Microsoft Zira Desktop", "culture": "en-GB"})
    assert saved["tts_voice"] == "Microsoft Zira Desktop"
    assert saved["culture"] == "en-GB"
    loaded = voice_prefs.load_voice_prefs()
    assert loaded["tts_voice"] == "Microsoft Zira Desktop"
    assert loaded["culture"] == "en-GB"


def test_pipeline_stops_wake_before_command():
    class FakeWake:
        name = "fake"
        stopped = False

        def start(self):
            return None

        def stop(self):
            self.stopped = True

        def listen_once(self, timeout=None):
            return True

    class FakeSTT:
        name = "fake"
        cloud = False

        def recognize(self, timeout=8.0):
            return {"ok": True, "text": "open chrome", "confidence": 0.9, "source": "appi-commands"}

        def transcribe(self, timeout=8.0):
            return "open chrome"

        def probe(self):
            return {"ok": True}

    class FakeTTS:
        name = "fake"

        def speak(self, text):
            return None

        def probe(self):
            return {"ok": True}

    wake = FakeWake()
    pipeline = VoicePipeline(wake=wake, stt=FakeSTT(), tts=FakeTTS())
    assert pipeline.wait_for_wake(1) is True
    assert wake.stopped is True
    assert pipeline.capture_command(1) == "open chrome"


def test_assistant_greeting_uses_first_name():
    from appi_voice.assistant import follow_up, greeting, local_reply, sanitize_heard

    text = greeting("Ayomide")
    assert "Ayomide" in text
    assert "What can I do for you" in text
    assert "how are you" in text.lower()
    assert "Ayomide" in follow_up("Ayomide O.")
    assert local_reply("what can you do", "Ayomide")
    assert "approved folders" in local_reply("what can you do", "Ayomide")
    assert local_reply("never mind", "Ayomide")
    assert local_reply("open chrome", "Ayomide") is None
    assert sanitize_heard('{"ok":true,"text":"open chrome","confidence":0.9}') == "open chrome"

