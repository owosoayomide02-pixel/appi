# Voice

```
Microphone → wake-word engine → "Appi" → VAD/STT → Appi Brain → Guardian → act → TTS
```

Voice is an input method. It does not bypass Guardian, capability checks, or audit.

## Microphone states

| State | Meaning |
| --- | --- |
| `OFF` | No capture |
| `WAKE_WORD_ONLY` | Default. Audio stays local. Nothing is stored. Nothing is sent to the cloud until activation. |
| `CONVERSATION` | Capture the command after "Appi" / hotkey |
| `RECORDING_TASK` | Explicit recording task (not implemented) |

After a command, the runtime returns to `WAKE_WORD_ONLY` unless continuous conversation is enabled.

## Wake word

Configurable. Default: **Appi**.

Windows tries local `System.Speech` grammar first. If Speech Recognition is unavailable, **Ctrl+Shift+A** is the local fallback.

The microphone is not streamed to the cloud to detect the wake word.

**Status this milestone (Windows, live-probed):**

- TTS: **Implemented** — SAPI speaks the assistant greeting
- Microphone + `Appi` grammar: **Implemented** — `SetInputToDefaultAudioDevice` and grammar load succeeded
- Persistent local wake-word listener: wired for `serve` (audio stays on-device)
- Spoken utterance in CI: not automated; say **Appi** after `serve`

Fallback activator: **Ctrl+Shift+A**

## Speaking voice and recognition language

Windows SAPI voices and recognizers are listed from the device. Pick them in **Settings → Voice**, or:

```powershell
cd apps\device-agent
python -m app.main voice-voices
python -m app.main voice-set --voice "Microsoft Zira Desktop" --culture en-GB
python -m app.main serve
```

Restart `serve` after `voice-set` if the runtime was already running and the dashboard did not push the change.

After **Appi**, Appi greets you by name (for example “Good evening Ayomide. How are you? What can I do for you?”), then listens. Small-talk such as “what can you do” is answered locally. Real tasks still go through Guardian.

`python -m app.main serve` keeps voice on by default (`--no-voice` to disable) and can autostart at login.

Recognition is local Windows Speech Recognition. The wake-word listener releases the microphone before command capture. Short phrases such as “open Chrome” are loaded as a command grammar; free dictation is the fallback. Low-confidence guesses are discarded instead of being sent as tasks.

This is still on-device Windows SR, not cloud STT. Accents and noisy rooms will miss. Speak after the greeting, not over it.

## Response modes

`SILENT` · `BRIEF` (default) · `NORMAL` · `VERBOSE`

Example: “Starting it.” then “Your server is running.” Internal planner steps are not narrated in BRIEF.

## Authentication

Speaker verification is a stub. Voice is **not** strong authentication.

“Appi, transfer ₦500,000.” cannot execute because someone spoke. Financial actions require a connected connector **and** a strong approval (PIN / biometric / device / passkey). With no connector the result is `CONNECTOR_NOT_CONNECTED`.
