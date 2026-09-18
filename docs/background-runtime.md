# Background runtime

Appi is split into:

```
APPI UI (dashboard / overlay)
+
APPI BACKGROUND RUNTIME
+
APPI VOICE SERVICE
+
APPI CLOUD CONNECTION
```

Closing or minimizing the Next.js dashboard does **not** stop the device runtime. They are separate processes.

## Commands

Foreground (existing):

```powershell
cd apps\device-agent
python -m app.main run
```

Background (reconnects, voice on by default, optional tray):

```powershell
python -m app.main serve
python -m app.main serve --no-voice
python -m app.main open
python -m app.main install
python -m app.main autostart on
python -m app.main autostart off
```

`python -m app.main install` puts **Appi** on the Desktop and Start Menu. Double-click that icon (or `scripts\Start Appi.vbs`) instead of opening PowerShell. Autostart uses a hidden VBScript so login does not flash a Command Prompt.

`serve` keeps a cloud heartbeat, listens for approved jobs, and uses `CREATE_NO_WINDOW` for local commands so tests do not steal focus.

Local IPC: `127.0.0.1:47821` (JSON line commands: `status`, `mute`, `pause`, `stop_tasks`).

Shared logic lives in `apps/runtime-core/`.

## Windows

| Feature | Status |
| --- | --- |
| User-login autostart (hidden Startup `.vbs`, no CMD) | Implemented |
| Desktop / Start Menu app shortcuts | Implemented |
| Reconnect loop independent of dashboard | Implemented |
| Local IPC | Implemented |
| System tray | Implemented when `pystray` and Pillow are installed |
| UI Automation | Planned |
| File / process monitoring beyond existing tools | Planned |

## Linux

systemd user unit / `.desktop` autostart helpers exist in `appi_runtime_core.autostart`. DBus adapters, desktop automation, and a verified tray are **Planned**.

## macOS

LaunchAgent plist helper exists. Native TCC permission prompts, Accessibility, and a Swift bridge are **Planned**.

## Idle policy

When idle: no model calls, Playwright closed unless a job needs it, heartbeat only, wake-word/hotkey if voice is on.

`serve` enables the user-activity check: foreground UI tools ask if the user was active in the last few seconds.
